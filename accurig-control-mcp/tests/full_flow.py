"""Exercise the actual MCP session owned by runtime_driver.py; no simulated calls."""
import json,pathlib,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
TAG=sys.argv[1]
commands=ROOT/('reports/commands'+TAG+'.jsonl')
responses=ROOT/('reports/responses'+TAG+'.jsonl')
record={'tag':TAG,'steps':[],'complete':False}
def response(identifier,timeout=40):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  if responses.exists():
   for line in responses.read_text(encoding='utf8').splitlines():
    try:item=json.loads(line)
    except json.JSONDecodeError:continue
    if item['id']==identifier:return item
  time.sleep(.3)
 raise TimeoutError(identifier)
counter=0
def call(tool,arguments=None):
 global counter
 counter+=1;identifier='flow-'+str(counter)
 with commands.open('a',encoding='utf8') as f:f.write(json.dumps({'id':identifier,'tool':tool,'arguments':arguments or {}})+'\n')
 return response(identifier)
def require(item):
 if item['is_error']:raise RuntimeError(json.dumps(item['data']))
 return item['data']['result']
def wait_job(item):
 job=require(item);end=time.monotonic()+420
 while job['state']=='working' and time.monotonic()<end:
  time.sleep(4);job=require(call('accurig_job_status',{'job_id':job['id']}))
 if job['state']!='completed':raise RuntimeError(json.dumps(job))
 record['steps'].append(job);print(job['type']+' completed',flush=True)
 return job
try:
 record['connect']=require(response('connect'))
 wait_job(response('load-pete'))
 wait_job(call('accurig_generate_rig',{'detect_fingers':True}))
 output=str(ROOT/'outputs'/('Pete-rigged-'+TAG+'.fbx'))
 wait_job(call('accurig_export_fbx',{'output_path':output}))
 exists=call('accurig_export_fbx',{'output_path':output})
 assert exists['is_error'] and 'already exists' in exists['data']['error']['message']
 record['overwrite_protection']=exists['data']
 record['final_status']=require(call('accurig_status'))
 record['complete']=True
except Exception as error:record['error']=str(error);print('FAILED: '+str(error),flush=True)
finally:
 (ROOT/('reports/full-flow-'+TAG+'.json')).write_text(json.dumps(record,indent=2),encoding='utf8')
 print(json.dumps({'complete':record['complete'],'steps':len(record['steps'])}),flush=True)
