"""Drive the live MCP, including real native edits, rollback and two generations."""
import json,pathlib,time,sys
ROOT=pathlib.Path(__file__).resolve().parents[1];TAG=sys.argv[1];counter=0
commands=ROOT/('reports/commands'+TAG+'.jsonl');responses=ROOT/('reports/responses'+TAG+'.jsonl')
record={'tag':TAG,'passed':False,'steps':[]}
def read(identifier,timeout=240):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if responses.exists():
   for line in responses.read_text(encoding='utf8').splitlines():
    try:r=json.loads(line)
    except json.JSONDecodeError:continue
    if r['id']==identifier:return r
  time.sleep(.5)
 raise TimeoutError(identifier)
def call(tool,arguments=None,error=False):
 global counter
 counter+=1;identifier='qa-'+str(counter)
 with commands.open('a',encoding='utf8') as f:f.write(json.dumps({'id':identifier,'tool':tool,'arguments':arguments or {}})+'\n')
 r=read(identifier)
 if bool(r['is_error'])!=error:raise RuntimeError(str(r))
 return r['data']['error'] if error else r['data']['result']
def job(value):
 end=time.monotonic()+600
 while value['state']=='working' and time.monotonic()<end:
  time.sleep(3);value=call('accurig_job_status',{'job_id':value['id']})
 if value['state']!='completed':raise RuntimeError(str(value))
 record['steps'].append(value);print(value['type']+' completed',flush=True)
 return value['result']
try:
 record['archive']=read('archive');assert not record['archive']['is_error']
 r=read('load-pete');assert not r['is_error'];job(r['data']['result'])
 job(call('accurig_detect_joints',{'body':False,'fingers':'Both'}))
 built=job(call('accurig_build_skin'));record['build']=built
 calibrated=job(call('accurig_calibrate_pose',{'coordinate_space':'accurig_native_angles','offsets':[{'bone_name':'CC_Base_Hip','rotation':{'x':0,'y':0,'z':0}}]}));record['calibration']=calibrated
 quality=job(call('accurig_validate_rig'));assert quality['verdict']!='failed';record['quality']=quality
 exported=job(call('accurig_export_fbx',{'output_path':str(ROOT/'outputs/Pete-calibrated-cal21.fbx'),'avatar':'calibrated','target':'blender'}));record['export']=exported;record['closed']=call('accurig_close_session');record['passed']=True
except Exception as error:record['error']=str(error);print('FAILED: '+str(error),flush=True)
finally:
 (ROOT/('reports/calibration-flow-'+TAG+'.json')).write_text(json.dumps(record,indent=2),encoding='utf8');print(json.dumps({'passed':record['passed'],'steps':len(record['steps'])}),flush=True)
