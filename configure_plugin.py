"""Point the source plugin at an existing runtime without changing its identity."""
import argparse,json,pathlib
ROOT=pathlib.Path(__file__).parent
def configure(runtime,write=True):
    runtime=pathlib.Path(runtime).resolve();python=runtime/'windows/venv/Scripts/python.exe'
    if write and not python.is_file():raise ValueError('Prepare the runtime or choose its existing directory first.')
    path=ROOT/'plugins/game-modding-toolkit/mcp.json';config=json.loads(path.read_text())
    for entry in config['mcpServers'].values():
        entry['command']=str(python);entry['env']['MODDING_LAB_ROOT']=str(runtime)
    if write:path.write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    return config
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--runtime-root',default=str(ROOT));parser.add_argument('--dry-run',action='store_true');args=parser.parse_args()
    config=configure(args.runtime_root,not args.dry_run)
    print(json.dumps({'runtime_root':args.runtime_root,'servers':list(config['mcpServers']),'written':not args.dry_run},indent=2))

