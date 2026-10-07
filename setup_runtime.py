"""Prepare a Windows x64 checkout; optional Docker build and Codex installation."""
import argparse,json,os,pathlib,shutil,subprocess,sys
ROOT=pathlib.Path(__file__).parent
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)
def commands(build=False,install=False):
    python=ROOT/'windows/venv/Scripts/python.exe';dotnet=ROOT/'windows/dotnet-sdk/dotnet.exe'
    rows=[
        [sys.executable,'bootstrap.py'],[sys.executable,'download_runtimes.py'],[sys.executable,'download_procps.py'],
        [sys.executable,'-m','venv',str(ROOT/'windows/venv')],
        [str(python),'-m','pip','install','-c','requirements/windows-constraints.txt','mcp==1.30.0','Pillow','PyYAML',str(ROOT/'sources/universal-modder')],
        [str(dotnet),'tool','install','--tool-path',str(ROOT/'downloads/ilspy-tools'),'ilspycmd','--version','11.1.0.9782'],
        [str(dotnet),'publish','windows/AssetBridge/AssetBridge.csproj','-c','Release','-o','windows/AssetBridge/publish','--self-contained','false'],
        [sys.executable,'configure_plugin.py','--runtime-root',str(ROOT)],
    ]
    if build:rows += [[sys.executable,'build_image.py'],['docker','compose','-f','compose.yaml','up','-d','--no-build','analysis']]
    if install:rows += [['codex','plugin','marketplace','add',str(ROOT),'--json'],['codex','plugin','add','game-modding-toolkit@modding-lab','--json']]
    return rows
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--plan',action='store_true');parser.add_argument('--build',action='store_true');parser.add_argument('--install',action='store_true');args=parser.parse_args()
    rows=commands(args.build,args.install)
    if args.plan:print(json.dumps(rows,indent=2));raise SystemExit(0)
    if os.name!='nt' or sys.version_info<(3,12):raise RuntimeError('Use Windows x64 with Python 3.12 or later.')
    for folder in ['logs','reports','projects']:(ROOT/folder).mkdir(exist_ok=True)
    # NuGet tool install is already complete if its DLL exists.
    for index,row in enumerate(rows):
        if 'tool' in row and 'install' in row and list((ROOT/'downloads/ilspy-tools').rglob('ilspycmd.dll')):continue
        executable=row
        if row[0]=='codex':
            resolved=shutil.which('codex')
            if not resolved:raise RuntimeError('Codex CLI is missing from PATH.')
            executable=[resolved,*row[1:]]
            if pathlib.Path(resolved).suffix.lower() in ['.cmd','.bat']:
                executable=[os.environ.get('COMSPEC','cmd.exe'),'/d','/c',*executable]
        with (ROOT/'logs'/f'setup-{index:02d}.log').open('w',encoding='utf-8') as log:
            result=subprocess.run(executable,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,creationflags=FLAGS)
        if result.returncode:raise RuntimeError(f'Setup step {index} failed. See logs/setup-{index:02d}.log; correct the cause and rerun.')
        if row[:3]==['codex','plugin','add']:
            text=(ROOT/'logs'/f'setup-{index:02d}.log').read_text();json.loads(text)
            (ROOT/'logs/plugin-install.json').write_text(text,encoding='utf-8')
    print('Runtime prepared. Start a new Codex chat after installation.')

