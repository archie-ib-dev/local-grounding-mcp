import fcntl,json,os,subprocess,sys,time,urllib.error,urllib.request
from pathlib import Path
from typing import Any
from mcp.server.fastmcp import FastMCP
HOST = os.environ.get("GROUNDING_HOST", "127.0.0.1")
PORT = int(os.environ.get("GROUNDING_PORT", "8765"))
BASE = f"http://{HOST}:{PORT}"

SERVICE = Path(
    os.environ.get(
        "GROUNDING_SERVICE_SCRIPT",
        str(Path(__file__).with_name("service.py")),
    )
).expanduser()

LOG = Path(
    os.environ.get(
        "GROUNDING_SERVICE_LOG",
        str(
            Path.home()
            / ".local"
            / "state"
            / "local-grounding"
            / "service.log"
        ),
    )
).expanduser()

LOCK = Path(
    os.environ.get(
        "GROUNDING_START_LOCK",
        "/tmp/local-grounding-start.lock",
    )
)

CLIENT = os.environ.get(
    "GROUNDING_CLIENT",
    "unknown",
)
mcp=FastMCP("Shared Local Visual Grounding",instructions="Visual fallback only. Inspect Playwright DOM/accessibility first and use a reliable ref whenever available.")
def call(method,path,payload=None,timeout=30):
    data=json.dumps(payload).encode() if payload is not None else None; req=urllib.request.Request(BASE+path,data=data,method=method,headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e: raise RuntimeError(e.read().decode(errors="replace")) from e
def ready():
    try: return bool(call("GET","/health",timeout=.75).get("ok"))
    except: return False
def ensure():
    if ready(): return
    LOG.parent.mkdir(parents=True,exist_ok=True)
    with LOCK.open("a+") as f:
        fcntl.flock(f.fileno(),fcntl.LOCK_EX)
        if ready(): return
        h=LOG.open("a"); subprocess.Popen([sys.executable,str(SERVICE)],stdin=subprocess.DEVNULL,stdout=h,stderr=h,start_new_session=True,close_fds=True)
        end=time.time()+20
        while time.time()<end:
            if ready(): return
            time.sleep(.25)
        raise RuntimeError(f"Shared service failed to start; inspect {LOG}")
@mcp.tool()
def grounding_health()->dict[str,Any]:
    """Return shared backend status without loading the model."""; ensure(); return call("GET","/health")
@mcp.tool()
def load_grounding_model()->dict[str,Any]:
    """Load the one shared model; simultaneous calls queue."""; ensure(); return call("POST","/load",{"client":CLIENT},180)
@mcp.tool()
def locate_target(image_path:str,target:str,viewport_css_width:int|None=None,viewport_css_height:int|None=None,delete_after_read:bool=True)->dict[str,Any]:
    """Visual fallback only. First inspect Playwright DOM/accessibility. Claude and Antigravity share one queued model."""
    ensure(); return call("POST","/locate",{"client":CLIENT,"image_path":image_path,"target":target,"viewport_css_width":viewport_css_width,"viewport_css_height":viewport_css_height,"delete_after_read":delete_after_read},360)
@mcp.tool()
def cleanup_grounding_screenshots(max_age_minutes:int=60)->dict[str,Any]:
    """Delete orphan screenshots."""; ensure(); return call("POST","/cleanup",{"max_age_minutes":max_age_minutes})
if __name__=="__main__": mcp.run(transport="stdio")
