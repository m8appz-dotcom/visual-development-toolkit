"""Register this local stdio server without changing other Codex settings."""
import json,pathlib,shutil,time,tomllib
ROOT=pathlib.Path(__file__).resolve().parent
config=pathlib.Path('C:/Users/kenny/.codex/config.toml')
before=config.read_text(encoding='utf-8')
parsed=tomllib.loads(before)
entry={'command':'D:/visual-development-toolkit/windows/node/node-v24.19.0-win-x64/node.exe','args':[str(ROOT/'src/server.mjs')],'enabled':True}
existing=parsed.get('mcp_servers',{}).get('accurig-control')
if existing:
 if existing!=entry:raise SystemExit('Existing accurig-control differs; no settings changed')
 print('Already registered');raise SystemExit(0)
backup=ROOT/'data'/('codex-config-before-'+str(time.time_ns())+'.toml')
backup.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(config,backup)
addition='\n[mcp_servers.accurig-control]\ncommand = '+json.dumps(entry['command'])+'\nargs = '+json.dumps(entry['args'])+'\nenabled = true\n'
after=before+addition
updated=tomllib.loads(after)
assert updated['mcp_servers'].pop('accurig-control')==entry
assert updated==parsed
temporary=config.with_suffix('.accurig-control.tmp');temporary.write_text(after,encoding='utf-8');temporary.replace(config)
print(json.dumps({'registered':'accurig-control','config':str(config),'backup':str(backup)}))
