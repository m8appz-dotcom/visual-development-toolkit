"""Portable stdio entrypoint; runtime installation is explicit, never automatic."""
import json,msvcrt,os,socket,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
SETTINGS=Path(os.environ['LOCALAPPDATA'])/'BlenderAgent/settings.json'
if not SETTINGS.is_file():
    raise SystemExit('Blender Agent is not configured; run the plugin install.py first (see INSTALL.md).')
cfg=json.loads(SETTINGS.read_text(encoding='utf-8'))
python=Path(cfg['python']).resolve(strict=True)
if Path(sys.executable).resolve()!=python:
    os.execv(str(python),[str(python),str(Path(__file__).resolve()),*sys.argv[1:]])
os.environ['CODEX_BLENDER_HOME']=cfg['integration_home']
os.environ['BLENDER_PATH']=cfg['blender']
os.environ['BLENDER_MCP_BUNDLE']=str(ROOT/'server/upstream')
sys.path.insert(0,str(ROOT/'server/overlay'))
from hardened_mcp import BASE,BLENDER,STATE,atomic,build_server,launch_detached,registry,registry_guard,rpc,PROBE

def ensure_default():
    with (BASE/'launch.lock').open('a+b') as lock:
        lock.seek(0)
        if not lock.read(1):
            lock.write(b'0');lock.flush()
        lock.seek(0)
        msvcrt.locking(lock.fileno(),msvcrt.LK_LOCK,1)
        try:
            with socket.socket() as sock:
                occupied=sock.connect_ex(('127.0.0.1',9877))==0
            if not occupied:
                launch_detached([str(BLENDER),'--background','--factory-startup','--disable-autoexec','--threads','2','--python',str(BASE/'blender_bootstrap.py')])
            value=None
            deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                try:
                    value=rpc(PROBE,9877,timeout=2)
                    break
                except (OSError,ValueError):
                    if occupied:
                        raise RuntimeError('Port 9877 is occupied but identity validation failed; no additional Blender was started')
                    time.sleep(.2)
            if not value or value.get('status')!='ok':
                raise RuntimeError('Default Blender bridge did not become ready')
            info=value['result']
            if os.path.normcase(os.path.realpath(info['binary']))!=os.path.normcase(str(BLENDER)) or (info.get('owner') or {}).get('owner')!='Codex':
                raise RuntimeError('Default port does not belong to the expected Codex Blender session')
            with registry_guard():
                items=registry()
                previous=items.get('background-default',{})
                if occupied and previous.get('pid') and previous['pid']!=info['pid']:
                    raise RuntimeError('Default session identity changed; explicit registration is required')
                items['background-default']={'port':9877,'pid':info['pid'],'owned':False}
                atomic(STATE/'sessions.json',items)
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)



if __name__=='__main__':
    ensure_default()
    build_server().run(transport='stdio')
