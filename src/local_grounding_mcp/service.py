import atexit, json, os, re, sys, threading, time, traceback, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
import torch
from PIL import Image
from qwen_vl_utils import process_vision_info
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

HOST = os.environ.get("GROUNDING_HOST", "127.0.0.1")
PORT = int(os.environ.get("GROUNDING_PORT", "8765"))
IDLE_SECONDS = int(
    os.environ.get("GROUNDING_IDLE_SECONDS", "900")
)
HOME = Path.home()
MODEL_PATH = Path(
    os.environ.get(
        "GROUNDING_MODEL_PATH",
        str(HOME / "Models" / "UGround-V1-2B"),
    )
).expanduser()
SCREENSHOT_DIR = Path(
    os.environ.get(
        "GROUNDING_SCREENSHOT_DIR",
        str(HOME / ".local" / "share" / "local-grounding" / "screenshots"),
    )
).expanduser()
CACHE_DIR = Path(
    os.environ.get(
        "GROUNDING_CACHE_DIR",
        str(HOME / ".cache" / "local-grounding"),
    )
).expanduser()
LOG_DIR = Path(
    os.environ.get(
        "GROUNDING_LOG_DIR",
        str(HOME / ".local" / "state" / "local-grounding"),
    )
).expanduser()
PID_FILE, METRICS_FILE = CACHE_DIR / "service.pid", LOG_DIR / "requests.jsonl"
BACKEND_NAME, DEVICE, DTYPE = "uground-baseline-fp32", "mps", torch.float32
_model = _processor = None
_model_loaded_at = None
_model_load_count = 0
_started_at = _last_activity = time.time()
_shutdown_requested = False
inference_lock, state_lock, metrics_lock = threading.Lock(), threading.Lock(), threading.Lock()
queue_depth, active_request_id = 0, None

def log(msg):
    print(f"[{time.strftime('%F %T')}] [shared-grounding] {msg}", file=sys.stderr, flush=True)
def now_iso(): return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
def metric(row):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with metrics_lock, METRICS_FILE.open("a", encoding="utf-8") as f: f.write(json.dumps(row, ensure_ascii=False)+"\n")
def state():
    with state_lock: return {"queue_depth":queue_depth,"active_request_id":active_request_id,"last_activity":_last_activity}
def cleanup(age=3600):
    deleted=failed=0; now=time.time()
    if not SCREENSHOT_DIR.exists(): return {"deleted":0,"failed":0}
    for p in SCREENSHOT_DIR.iterdir():
        if not p.is_file() or p.suffix.lower() not in {".png",".jpg",".jpeg",".webp"}: continue
        try:
            if now-p.stat().st_mtime >= age: p.unlink(); deleted+=1
        except OSError: failed+=1
    return {"deleted":deleted,"failed":failed}
def ensure_model():
    global _model,_processor,_model_loaded_at,_model_load_count
    if _model is not None: return _model,_processor,0.0
    if not torch.backends.mps.is_available(): raise RuntimeError("Apple MPS unavailable")
    t=time.perf_counter(); log(f"Loading {BACKEND_NAME}")
    _processor=AutoProcessor.from_pretrained(str(MODEL_PATH))
    _model=Qwen2VLForConditionalGeneration.from_pretrained(str(MODEL_PATH),torch_dtype=DTYPE,attn_implementation="eager",low_cpu_mem_usage=True).to(DEVICE)
    _model.eval(); elapsed=time.perf_counter()-t; _model_loaded_at=time.time(); _model_load_count+=1
    log(f"Model loaded in {elapsed:.3f}s"); return _model,_processor,elapsed
def point(text):
    m=re.search(r"[\(\[]\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*[\)\]]",text)
    if not m: raise RuntimeError(f"No coordinate pair: {text!r}")
    x,y=float(m.group(1)),float(m.group(2))
    if not (0<=x<=1000 and 0<=y<=1000): raise RuntimeError("Coordinate outside 0-1000")
    return x,y
def health():
    s=state(); return {"ok":True,"backend":BACKEND_NAME,"service_mode":"shared-http","host":HOST,"port":PORT,"pid":os.getpid(),"service_uptime_seconds":round(time.time()-_started_at,3),"idle_timeout_seconds":IDLE_SECONDS,"model_path":str(MODEL_PATH),"device":DEVICE,"precision":"float32","model_loaded":_model is not None,"model_loaded_at":_model_loaded_at,"model_load_count":_model_load_count,"mps_available":torch.backends.mps.is_available(),"queue_depth":s["queue_depth"],"active_request_id":s["active_request_id"],"seconds_since_activity":round(time.time()-s["last_activity"],3),"metrics_file":str(METRICS_FILE)}
def queued(op,client,fn:Callable):
    global queue_depth,active_request_id,_last_activity
    rid=str(uuid.uuid4()); qtime=time.perf_counter()
    with state_lock: queue_depth+=1; position=queue_depth
    try:
        with inference_lock:
            wait=time.perf_counter()-qtime
            with state_lock: queue_depth-=1; active_request_id=rid; _last_activity=time.time()
            t=time.perf_counter(); result=fn(); run=time.perf_counter()-t
            result.update({"request_id":rid,"client":client,"queue_position_on_arrival":position,"queue_wait_seconds":round(wait,3),"service_execution_seconds":round(run,3),"shared_service_pid":os.getpid()})
            return result
    finally:
        with state_lock: active_request_id=None; _last_activity=time.time()
def visual_tokens(inputs,processor):
    grid=inputs.get("image_grid_thw")
    if grid is None: return None
    merge=int(getattr(getattr(processor,"image_processor",None),"merge_size",2))
    return sum((int(t)*int(h)*int(w))//(merge*merge) for t,h,w in grid.detach().cpu().tolist())
def load_op(payload):
    client=str(payload.get("client","unknown"))
    def run():
        _,_,seconds=ensure_model(); metric({"timestamp":now_iso(),"operation":"load_model","client":client,"service_pid":os.getpid(),"load_seconds":round(seconds,3),"success":True})
        return {"ok":True,"backend":BACKEND_NAME,"load_seconds":round(seconds,3)}
    return queued("load-model",client,run)
def locate_op(payload):
    client=str(payload.get("client","unknown")); path=Path(str(payload.get("image_path",""))).expanduser().resolve(); target=str(payload.get("target","")).strip()
    cw,ch=payload.get("viewport_css_width"),payload.get("viewport_css_height"); delete=bool(payload.get("delete_after_read",True))
    if not path.exists(): raise FileNotFoundError(path)
    if not target: raise ValueError("target required")
    def run():
        total=time.perf_counter(); model,processor,load_seconds=ensure_model(); prep=time.perf_counter()
        with Image.open(path) as src: image=src.convert("RGB"); image.load()
        width,height=image.size
        prompt=("Your task is to identify the precise coordinates (x, y) of one UI element. "
                "Return only a single coordinate pair (x, y) in the 0-1000 grid. Description: "+target+" Answer:")
        messages=[{"role":"user","content":[{"type":"image","image":str(path)},{"type":"text","text":prompt}]}]
        rendered=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
        image_inputs,video_inputs=process_vision_info(messages)
        inputs=processor(text=[rendered],images=image_inputs,videos=video_inputs,padding=True,return_tensors="pt")
        deleted=False; delete_error=None
        if delete:
            try: path.unlink(missing_ok=True); deleted=True
            except OSError as e: delete_error=str(e)
        input_tokens=int(inputs["input_ids"].shape[-1]); vtokens=visual_tokens(inputs,processor); pixels=int(inputs["pixel_values"].shape[0]) if "pixel_values" in inputs else None
        prep_seconds=time.perf_counter()-prep; inputs={k:(v.to(DEVICE) if hasattr(v,"to") else v) for k,v in inputs.items()}
        it=time.perf_counter()
        with torch.inference_mode(): output=model.generate(**inputs,max_new_tokens=20,do_sample=False,use_cache=True)
        infer=time.perf_counter()-it; generated=output[:,inputs["input_ids"].shape[-1]:]; gen_tokens=int(generated.shape[-1])
        raw=processor.batch_decode(generated,skip_special_tokens=True,clean_up_tokenization_spaces=False)[0].strip(); gx,gy=point(raw); total_seconds=time.perf_counter()-total
        result={"ok":True,"backend":BACKEND_NAME,"raw_response":raw,"grid_point_0_1000":[gx,gy],"image_size":[width,height],"input_tokens":input_tokens,"visual_tokens":vtokens,"pixel_tensor_rows":pixels,"generated_tokens":gen_tokens,"model_load_seconds":round(load_seconds,3),"preprocess_seconds":round(prep_seconds,3),"inference_seconds":round(infer,3),"total_grounding_seconds":round(total_seconds,3),"screenshot_deleted":deleted,"screenshot_delete_error":delete_error}
        if cw is not None and ch is not None: result["viewport_css_point"]=[round(gx/1000*int(cw)),round(gy/1000*int(ch))]; result["viewport_css_size"]=[int(cw),int(ch)]
        metric({"timestamp":now_iso(),"operation":"locate_target","client":client,"service_pid":os.getpid(),"image_width":width,"image_height":height,"input_tokens":input_tokens,"visual_tokens":vtokens,"pixel_tensor_rows":pixels,"generated_tokens":gen_tokens,"model_load_seconds":round(load_seconds,3),"preprocess_seconds":round(prep_seconds,3),"inference_seconds":round(infer,3),"total_grounding_seconds":round(total_seconds,3),"screenshot_deleted":deleted,"success":True})
        return result
    return queued("locate-target",client,run)
def queue_test(payload):
    client=str(payload.get("client","test")); seconds=min(max(float(payload.get("seconds",1)),.1),5)
    return queued("queue-test",client,lambda:(time.sleep(seconds) or {"ok":True,"slept_seconds":seconds}))
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def reply(self,code,obj):
        body=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(code); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(body))); self.end_headers(); self.wfile.write(body)
    def payload(self):
        n=int(self.headers.get("Content-Length","0")); return json.loads(self.rfile.read(n).decode()) if n else {}
    def do_GET(self): self.reply(200,health()) if self.path=="/health" else self.reply(404,{"ok":False})
    def do_POST(self):
        global _shutdown_requested
        try:
            p=self.payload()
            if self.path=="/load": r=load_op(p)
            elif self.path=="/locate": r=locate_op(p)
            elif self.path=="/queue-test": r=queue_test(p)
            elif self.path=="/cleanup": r=cleanup(int(p.get("max_age_minutes",60))*60); r["ok"]=r["failed"]==0
            elif self.path=="/shutdown": _shutdown_requested=True; r={"ok":True,"pid":os.getpid()}; threading.Thread(target=self.server.shutdown,daemon=True).start()
            else: self.reply(404,{"ok":False,"error":"not_found"}); return
            self.reply(200,r)
        except FileNotFoundError as e: self.reply(404,{"ok":False,"error":"file_not_found","message":str(e)})
        except (ValueError,TypeError) as e: self.reply(400,{"ok":False,"error":"bad_request","message":str(e)})
        except Exception as e: log(traceback.format_exc()); self.reply(500,{"ok":False,"error":"internal_error","message":str(e)})
def monitor(server):
    while not _shutdown_requested:
        time.sleep(10); s=state()
        if time.time()-s["last_activity"]>=IDLE_SECONDS and s["active_request_id"] is None and s["queue_depth"]==0 and not inference_lock.locked(): log("Idle timeout; stopping"); server.shutdown(); return
def remove_pid():
    try:
        if PID_FILE.exists() and PID_FILE.read_text().strip()==str(os.getpid()): PID_FILE.unlink()
    except OSError: pass
def main():
    CACHE_DIR.mkdir(parents=True,exist_ok=True); LOG_DIR.mkdir(parents=True,exist_ok=True); SCREENSHOT_DIR.mkdir(parents=True,exist_ok=True); PID_FILE.write_text(str(os.getpid())); atexit.register(remove_pid); cleanup()
    server=ThreadingHTTPServer((HOST,PORT),Handler); threading.Thread(target=monitor,args=(server,),daemon=True).start(); log(f"Listening on {HOST}:{PORT}")
    try: server.serve_forever(.5)
    finally: server.server_close(); remove_pid(); log("Stopped")
if __name__=="__main__": main()
