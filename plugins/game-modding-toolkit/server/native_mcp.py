"""Run native Windows MCP engines on demand, hidden and at below-normal priority."""
import ctypes,json,os,pathlib,runpy,subprocess,sys
root=pathlib.Path(os.environ['MODDING_LAB_ROOT']).resolve()
config=json.loads((root/'native-runtime.json').read_text())
java_home=root/'temp/java-home';java_home.mkdir(parents=True,exist_ok=True)
os.environ.update(MODDING_LAB_MODE='native',JAVA_HOME=config['java'],GHIDRA_INSTALL_DIR=config['ghidra'],REA_ANALYSIS_PROVIDER='ghidra',DOTNET_ROOT=str(root/'windows/dotnet-sdk'),UM_KB=str(root/'plugins/game-modding-toolkit/knowledge'),TEMP=str(root/'temp'),TMP=str(root/'temp'),_JAVA_OPTIONS='-Xmx2048m -Duser.home='+str(java_home),DOTNET_CLI_HOME=str(root/'temp/dotnet'),DOTNET_CLI_TELEMETRY_OPTOUT='1')
os.environ['PATH']=str(pathlib.Path(config['java'])/'bin')+os.pathsep+str(pathlib.Path(config['node']).parent)+os.pathsep+str(root/'windows/dotnet-sdk')+os.pathsep+os.environ.get('PATH','')
if os.name=='nt':ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(),0x4000)
mode=sys.argv[1]
if mode=='gateway':runpy.run_path(str(pathlib.Path(__file__).parent/'lab_mcp.py'),run_name='__main__')
elif mode=='ghidra':
    from ghidra_headless_mcp.cli import main
    raise SystemExit(main(['--ghidra-install-dir',config['ghidra']]))
elif mode=='rea':
    flags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS
    proc=subprocess.Popen([config['node'],str(root/'windows/rea/node_modules/rea-agents/scripts/rea.mjs'),'mcp'],stdin=sys.stdin.buffer,stdout=sys.stdout.buffer,stderr=sys.stderr.buffer,creationflags=flags)
    try:raise SystemExit(proc.wait())
    except KeyboardInterrupt:proc.terminate();raise SystemExit(130)
else:raise ValueError('Choose gateway, ghidra or rea.')
