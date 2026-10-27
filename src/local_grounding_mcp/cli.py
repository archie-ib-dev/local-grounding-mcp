"""CLI utilities for Local Grounding MCP."""
import json, os, sys, urllib.request
from importlib.metadata import version
from pathlib import Path
HOST=os.environ.get('GROUNDING_HOST','127.0.0.1')
PORT=int(os.environ.get('GROUNDING_PORT','8765'))
BASE=f'http://{HOST}:{PORT}'
def _request(method,path,payload=None,timeout=5):
    data=json.dumps(payload).encode() if payload is not None else None
    request=urllib.request.Request(BASE+path,data=data,method=method,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=timeout) as response:
        return json.loads(response.read().decode())
def service_main():
    from .service import main
    main()
def adapter_main():
    from .mcp_adapter import mcp
    mcp.run(transport='stdio')
def doctor_main():
    import torch
    model=Path(os.environ.get('GROUNDING_MODEL_PATH',str(Path.home()/'Models'/'UGround-V1-2B'))).expanduser()
    checks=[('Python',sys.version.split()[0],True),('Apple MPS',str(torch.backends.mps.is_available()),torch.backends.mps.is_available()),('Model path',str(model),model.exists()),('Host',HOST,HOST=='127.0.0.1'),('Package',version('local-grounding-mcp'),True)]
    for name,value,ok in checks:
        print(f"{'OK' if ok else 'FAIL':4}  {name}: {value}")
    raise SystemExit(0 if all(row[2] for row in checks) else 1)
def status_main():
    try: print(json.dumps(_request('GET','/health'),indent=2))
    except Exception: print('Shared grounding service: STOPPED')
def stop_main():
    try: print(json.dumps(_request('POST','/shutdown',{},10),indent=2))
    except Exception: print('Shared grounding service is not running.')
def metrics_main():
    path=Path(os.environ.get('GROUNDING_LOG_DIR',str(Path.home()/'.local'/'state'/'local-grounding')))/'requests.jsonl'
    if not path.exists():
        print('No metrics yet.'); return
    rows=[]
    for line in path.read_text().splitlines():
        try: rows.append(json.loads(line))
        except Exception: pass
    located=[row for row in rows if row.get('operation')=='locate_target' and row.get('success')]
    print(f'records_total: {len(rows)}')
    print(f'locate_success: {len(located)}')
    for key in ('visual_tokens','input_tokens','generated_tokens','preprocess_seconds','inference_seconds','total_grounding_seconds'):
        values=[float(row[key]) for row in located if row.get(key) is not None]
        if values: print(f'{key}: avg={sum(values)/len(values):.3f} total={sum(values):.3f}')
