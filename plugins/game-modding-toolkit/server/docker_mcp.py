"""Launch an upstream MCP through docker exec, preserving stdio and hiding windows."""
import os,pathlib,subprocess,sys
root=pathlib.Path(os.environ.get('MODDING_LAB_ROOT',r'D:\modding-lab'))
flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
state=subprocess.run(['docker','inspect','modding-lab-analysis','--format','{{.State.Running}}'],capture_output=True,text=True,creationflags=flags)
if state.stdout.strip()!='true':
    up=subprocess.run(['docker','compose','-f',str(root/'compose.yaml'),'up','-d','--no-build'],stdout=sys.stderr,stderr=sys.stderr,creationflags=flags)
    if up.returncode:sys.exit(up.returncode)
mode=sys.argv[1]
command={'ghidra':['ghidra-headless-mcp','--ghidra-install-dir','/opt/ghidra'],'rea':['rea','mcp']}[mode]
proc=subprocess.Popen(['docker','exec','-i','modding-lab-analysis',*command],stdin=sys.stdin.buffer,stdout=sys.stdout.buffer,stderr=sys.stderr.buffer,creationflags=flags)
try:sys.exit(proc.wait())
except KeyboardInterrupt:proc.terminate();sys.exit(130)
