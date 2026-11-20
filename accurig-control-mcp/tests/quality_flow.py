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
 r=read('load-pete');assert not r['is_error'];job(r['data']['result'])
 job(call('accurig_detect_joints',{'body':False,'fingers':'Both'}))
 initial=call('accurig_inspect_rig');checkpoint=call('accurig_save_checkpoint');record['checkpoint']=checkpoint['id']
 elbow=next(j for j in initial['data']['bodyJoints'] if j['name'].endswith('L_Forearm'))
 changed={**elbow['position'],'z':elbow['position']['z']+1.0}
 edited=job(call('accurig_edit_joints',{'expected_revision':initial['revision'],'coordinate_space':'accurig_native_model','changes':[{'name':elbow['name'],'position':changed}]}))
 record['revision_conflict']=call('accurig_edit_joints',{'expected_revision':initial['revision'],'coordinate_space':'accurig_native_model','changes':[{'name':elbow['name'],'position':changed}]},error=True)
 restored=job(call('accurig_restore_checkpoint',{'checkpoint_id':checkpoint['id'],'expected_revision':edited['revision']}))
 current=call('accurig_inspect_rig');got=next(j for j in current['data']['bodyJoints'] if j['name']==elbow['name'])
 assert all(abs(got['position'][k]-v)<.001 for k,v in elbow['position'].items())
 record['correction']={'joint':elbow['name'],'baseline':elbow['position'],'controlled_perturbation':changed,'corrected_readback':got['position'],'note':'Perturbation and restoration test; no anatomical improvement claimed from an arbitrary offset.'}
 first=job(call('accurig_build_skin'));second=job(call('accurig_build_skin'))
 assert first['generation_id']!=second['generation_id'];record['fresh_generation_test']={'first':first['generation_id'],'second':second['generation_id']}
 for j in current['data']['bodyJoints']:
  after=next(x for x in second['joints_before']['bodyJoints'] if x['name']==j['name'])
  assert all(abs(after['position'][k]-v)<.001 for k,v in j['position'].items())
 record['corrections_preserved_before_skin']=True
 quality=job(call('accurig_validate_rig'));record['quality']=quality
 assert quality['verdict']!='failed'
 output=str(ROOT/'outputs'/('Pete-corrected-'+TAG+'.fbx'))
 exported=job(call('accurig_export_fbx',{'output_path':output,'target':'blender','mode':'MeshOnly'}));record['export']=exported
 collision=ROOT/'outputs'/('collision-'+TAG+'.glb');collision.write_bytes(b'preserve-existing-glb')
 record['sidecar_collision']=call('accurig_export_fbx',{'output_path':str(collision.with_suffix('.fbx'))},error=True)
 assert collision.read_bytes()==b'preserve-existing-glb'
 record['invalid_import']=call('accurig_load_model',{'input_path':str(ROOT/'does-not-exist.obj')},error=True)
 state=call('accurig_status');assert state['model'] is None and not state['rigged'] and state['generation'] is None
 record['export_after_failed_import']=call('accurig_export_fbx',{'output_path':str(ROOT/'outputs/rejected.fbx')},error=True)
 record['closed']=call('accurig_close_session');record['passed']=True
except Exception as error:record['error']=str(error);print('FAILED: '+str(error),flush=True)
finally:
 (ROOT/('reports/quality-flow-'+TAG+'.json')).write_text(json.dumps(record,indent=2),encoding='utf8');print(json.dumps({'passed':record['passed'],'steps':len(record['steps'])}),flush=True)
