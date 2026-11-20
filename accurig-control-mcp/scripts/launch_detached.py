"""Launch the installed owned app outside the MCP's Windows kill-on-close job."""
import sys,json,subprocess,os,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
exe=pathlib.Path('D:/Applications/Reallusion/AccuRIG/AccuRIG.exe')
main,renderer=map(int,sys.argv[1:])
if not(1024<main<65536 and 1024<renderer<65536):raise ValueError('Ports invalid')
args=[str(exe),f'--inspect-brk=127.0.0.1:{main}',f'--remote-debugging-port={renderer}','--remote-debugging-address=127.0.0.1','--disable-background-timer-throttling','--disable-renderer-backgrounding','--disable-backgrounding-occluded-windows']
env=dict(os.environ);env.pop('ELECTRON_RUN_AS_NODE',None)
log=open(root/'reports/application.log','ab')
# Create outside the tracked descendant tree, not merely outside the nearest job.
# No service, scheduled task, account or security setting is created/changed.
cmd=subprocess.list2cmdline(args)
script="$r=Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine='"+cmd.replace("'","''")+"';CurrentDirectory='"+str(exe.parent).replace("'","''")+"'}; if($r.ReturnValue -ne 0){throw ('WMI launch failed '+$r.ReturnValue)}; $p=Get-CimInstance Win32_Process -Filter ('ProcessId='+$r.ProcessId); $owner=Invoke-CimMethod -InputObject $p -MethodName GetOwner; if($owner.User -ne $env:USERNAME){throw 'Unexpected application account'}; @{pid=$r.ProcessId;launch_mode='wmi_independent';owned=$true}|ConvertTo-Json -Compress"
print(subprocess.check_output(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],text=True,creationflags=subprocess.CREATE_NO_WINDOW).strip())
