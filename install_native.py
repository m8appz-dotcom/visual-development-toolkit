"""Install a private Windows native runtime from the verified deployment payload."""
import argparse,datetime,hashlib,json,os,pathlib,shutil,subprocess,sys,zipfile
ROOT=pathlib.Path(__file__).resolve().parent
FLAGS=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS
ENV=os.environ.copy()
for folder in ['temp','logs','reports','projects']:(ROOT/folder).mkdir(exist_ok=True)
ENV.update(TEMP=str(ROOT/'temp'),TMP=str(ROOT/'temp'),PIP_CACHE_DIR=str(ROOT/'temp/pip-cache'),npm_config_cache=str(ROOT/'temp/npm-cache'),DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER='1',MSBUILDDISABLENODEREUSE='1',DOTNET_CLI_HOME=str(ROOT/'temp/dotnet'),NUGET_PACKAGES=str(ROOT/'temp/nuget'),DOTNET_CLI_TELEMETRY_OPTOUT='1')
def run(args,label,timeout=1200):
    executable=args
    if str(args[0]).endswith(('.cmd','.bat')):executable=[ENV.get('COMSPEC','cmd.exe'),'/d','/c',*args]
    with (ROOT/'logs'/f'native-install-{label}.log').open('w',encoding='utf-8') as log:
        result=subprocess.run(executable,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,env=ENV,creationflags=FLAGS,timeout=timeout)
    if result.returncode:raise RuntimeError(f'{label} failed: see logs/native-install-{label}.log')
    print('READY',label,flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--payload',default=str(ROOT/'payload'));args=parser.parse_args()
    if sys.version_info[:2]!=(3,12):raise RuntimeError('Use the private Python 3.12 interpreter; PyGhidra 3.1 pins JPype 1.5.2.')
    payload=pathlib.Path(args.payload)
    records=json.loads((ROOT/'payload-lock.json').read_text())
    for record in records:
        archive=payload/record['name']
        with archive.open('rb') as stream:sha=hashlib.file_digest(stream,'sha256').hexdigest()
        if sha!=record['sha256']:raise RuntimeError('Payload checksum mismatch: '+record['name'])
        dest=ROOT/record['extract_to'];dest.mkdir(parents=True,exist_ok=True)
        marker=dest/('.prepared-'+sha)
        if not marker.exists():
            with zipfile.ZipFile(archive) as z:
                for member in z.namelist():
                    if not (dest/member).resolve().is_relative_to(dest.resolve()):raise RuntimeError('Unsafe archive member')
                z.extractall(dest)
            marker.touch()
        print('READY',record['name'],flush=True)
    python=ROOT/'windows/venv/Scripts/python.exe'
    cfg=ROOT/'windows/venv/pyvenv.cfg'
    if cfg.exists() and 'version = 3.12' not in cfg.read_text() and 'version_info = 3.12' not in cfg.read_text():
        source=(ROOT/'windows/venv').resolve();backup=(ROOT/'backups'/('venv-before-python312-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))).resolve()
        assert source.is_relative_to(ROOT) and backup.is_relative_to(ROOT)
        backup.parent.mkdir(exist_ok=True);source.rename(backup)
    if not python.exists():run([sys.executable,'-m','venv',str(ROOT/'windows/venv')],'venv')
    wheel_paths=[str(p) for p in (ROOT/'wheels').glob('*.whl')]
    run([str(python),'-m','pip','install','--no-cache-dir','--only-binary=:all:','mcp==1.30.0','pyghidra==3.1.0','JPype1==1.5.2','pywin32','python-dotenv',*wheel_paths],'python')
    java=next(p for p in (ROOT/'windows/jdk21').iterdir() if (p/'bin/java.exe').exists())
    node=next((ROOT/'windows/node').rglob('node.exe'))
    ghidra=ROOT/'downloads/ghidra/ghidra_12.1.4_PUBLIC'
    dotnet=ROOT/'windows/dotnet-sdk/dotnet.exe'
    ENV.update(JAVA_HOME=str(java),GHIDRA_INSTALL_DIR=str(ghidra),DOTNET_ROOT=str(dotnet.parent),REA_ANALYSIS_PROVIDER='ghidra',_JAVA_OPTIONS='-Xmx2048m')
    ENV['PATH']=str(node.parent)+os.pathsep+str(java/'bin')+os.pathsep+str(dotnet.parent)+os.pathsep+ENV['PATH']
    if not (ROOT/'windows/rea/node_modules/rea-agents/scripts/rea.mjs').exists():
        run([str(node.parent/'npm.cmd'),'install','--prefix',str(ROOT/'windows/rea'),'--no-audit','--no-fund','rea-agents@4.1.0'],'rea')
    if not list((ROOT/'windows/ilspy-tools').rglob('ilspycmd.dll')):
        run([str(dotnet),'tool','install','--tool-path',str(ROOT/'windows/ilspy-tools'),'ilspycmd','--version','11.1.0.9782'],'ilspy')
    project_source=ROOT/'windows/AssetBridge/AssetBridge.csproj'
    native_project=project_source.with_name('AssetBridge.Native.csproj')
    xml=project_source.read_text().replace('<TargetFramework>net8.0</TargetFramework>','<TargetFramework>net10.0</TargetFramework><AssemblyName>AssetBridge</AssemblyName>')
    native_project.write_text(xml,encoding='utf-8')
    run([str(dotnet),'publish',str(native_project),'-c','Release','-p:UseSharedCompilation=false','-o','windows/AssetBridge/publish','--self-contained','false'],'assetbridge')
    marker=ROOT/'windows/venv/.ghidra-script-host-patched'
    if not marker.exists():run([str(python),'patches/initialize_ghidra_scripts.py'],'ghidra-patch');marker.touch()
    config={'mode':'native','node':str(node),'java':str(java),'ghidra':str(ghidra),'dotnet':str(dotnet)}
    (ROOT/'native-runtime.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
    plugin=ROOT/'plugins/game-modding-toolkit';mcp=json.loads((plugin/'mcp.json').read_text())
    for name,entry in mcp['mcpServers'].items():
        entry.update(command=str(python),args=['${PLUGIN_ROOT}/server/native_mcp.py',{'modding-lab':'gateway','ghidra':'ghidra','rea':'rea'}[name]],env={'MODDING_LAB_ROOT':str(ROOT),'MODDING_LAB_MODE':'native','PYTHONIOENCODING':'utf-8'})
    (plugin/'mcp.json').write_text(json.dumps(mcp,indent=2)+'\n',encoding='utf-8')
    central=plugin/'skills/modding-lab/SKILL.md';text=central.read_text()
    text+='\n## Native Windows installation\nThis host uses MODDING_LAB_MODE=native. component_status.runtime_root is authoritative; local project paths stay on Windows. run_um uses native installed tools even with the historical platform=docker argument. Ghidra and REA run on demand, hidden, at below-normal priority; Java is limited to 2 GiB. Do not start Docker or persistent services for this mode. Windows REA native analysis is its experimental read-only x64 PE P0 boundary; use separate Ghidra MCP for other formats and report provider limitations. On X, keep visible interactions explicitly authorized and use Bobi/Spark for prolonged heavy work.\n'
    if '## Native Windows installation' not in central.read_text():central.write_text(text,encoding='utf-8')
    codex=shutil.which('codex.cmd') or shutil.which('codex.exe') or shutil.which('codex')
    if not codex:raise RuntimeError('Codex CLI not found')
    run([codex,'plugin','marketplace','add',str(ROOT),'--json'],'marketplace',120)
    run([codex,'plugin','add','game-modding-toolkit@modding-lab','--json'],'plugin',120)
    install=json.loads((ROOT/'logs/native-install-plugin.log').read_text(encoding='utf-8-sig'))
    (ROOT/'logs/plugin-install.json').write_text(json.dumps(install,indent=2),encoding='utf-8')
    print(json.dumps({'host':os.environ['COMPUTERNAME'],'runtime':str(ROOT),'plugin':install,'mode':'native'},indent=2),flush=True)
