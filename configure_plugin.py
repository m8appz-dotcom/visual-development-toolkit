"""Configure a private plugin copy for an existing runtime; never install engines."""
import argparse,json,os,pathlib
ROOT=pathlib.Path(__file__).parent

def configure(runtime,write=True,*,plugin_root=None,python=None,mode='native'):
    runtime=pathlib.Path(runtime).resolve()
    # Keep venv executable symlinks: dereferencing them selects the base Python.
    interpreter=pathlib.Path(os.path.abspath(os.path.expanduser(str(python)))) if python else runtime/'windows/venv/Scripts/python.exe'
    if mode not in {'native','portable','docker'}:
        raise ValueError('Choose native, portable or docker mode.')
    if write and (not runtime.is_dir() or not interpreter.is_file()):
        raise ValueError('Choose an existing runtime and Python interpreter first.')
    path=pathlib.Path(plugin_root).resolve()/'mcp.json' if plugin_root else ROOT/'plugins/game-modding-toolkit/mcp.json'
    config=json.loads(path.read_text(encoding='utf-8'))
    for entry in config['mcpServers'].values():
        # Portable plugins require a bare executable. PATH remains private.
        entry['command']=interpreter.name
        entry['env'].update(MODDING_LAB_ROOT=str(runtime),MODDING_LAB_MODE=mode,
                            PATH=str(interpreter.parent)+os.pathsep+os.environ.get('PATH',''))
    if write:path.write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    return config

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-root',default=str(ROOT))
    parser.add_argument('--plugin-root',type=pathlib.Path)
    parser.add_argument('--python',type=pathlib.Path)
    parser.add_argument('--mode',choices=['native','portable','docker'],default='native')
    parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args()
    config=configure(args.runtime_root,not args.dry_run,plugin_root=args.plugin_root,python=args.python,mode=args.mode)
    print(json.dumps({'servers':list(config['mcpServers']),'written':not args.dry_run,'mode':args.mode}))

