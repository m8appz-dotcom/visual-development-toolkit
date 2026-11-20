"""Connect to the existing local REA via MCP; never install or change configuration."""
import argparse,asyncio,json,os,pathlib,sys,time,uuid
from contextlib import asynccontextmanager
from datetime import timedelta

MAX_LINE=65536
class AgentConnection:
 def __init__(self,session,tools):
  self.session=session;self.tools=tools;self.session_id=uuid.uuid4().hex;self.request_count=0
 async def call(self,tool,arguments=None):
  arguments={} if arguments is None else arguments
  if not isinstance(arguments,dict):raise ValueError('Tool arguments must be a JSON object.')
  if self.request_count>=64:raise ValueError('Session is limited to 64 tool requests.')
  self.request_count+=1;start=time.perf_counter()
  if tool not in {t.name for t in self.tools}:
   value={'ok':False,'error':{'code':'TOOL_UNAVAILABLE','message':'Requested agent tool is not advertised by this REA connection.'}}
  else:
   response=await self.session.call_tool(tool,arguments)
   value={'ok':not response.isError,'is_error':bool(response.isError),'structured_content':response.structuredContent,'content':[c.model_dump(mode='json') for c in response.content]}
  value['meta']={'session_id':self.session_id,'request_index':self.request_count,'elapsed_ms':round((time.perf_counter()-start)*1000,3)}
  return value

@asynccontextmanager
async def connect(lab_root='D:/visual-development-toolkit'):
 """One owned MCP session for adaptive queries; EOF/context exit closes its process."""
 from mcp import ClientSession,StdioServerParameters
 from mcp.client.stdio import stdio_client
 root=pathlib.Path(lab_root).resolve(strict=True)
 cfg=json.loads((root/'native-runtime.json').read_text(encoding='utf-8-sig'))
 provider=os.environ.get('REA_ANALYSIS_PROVIDER','ghidra')
 if provider!='ghidra':raise ValueError('This local helper requires the configured Ghidra installation; use the direct MCP for another provider.')
 command=pathlib.Path(cfg['node']);entry=root/'windows/rea/node_modules/rea-agents/scripts/rea.mjs'
 for p in (command,entry,pathlib.Path(cfg['java']),pathlib.Path(cfg['ghidra'])):
  if not p.exists():raise FileNotFoundError('Configured runtime path is unavailable: '+str(p))
 env={**os.environ,'MODDING_LAB_ROOT':str(root),'MODDING_LAB_MODE':'native','REA_ANALYSIS_PROVIDER':provider,'GHIDRA_INSTALL_DIR':cfg['ghidra'],'JAVA_HOME':cfg['java'],'PYTHONIOENCODING':'utf-8'}
 log=root/'agent-layer/reports/skill-mcp.log';log.parent.mkdir(parents=True,exist_ok=True)
 with log.open('a',encoding='utf-8') as errlog:
  async with stdio_client(StdioServerParameters(command=str(command),args=[str(entry),'mcp'],env=env),errlog=errlog) as streams:
   async with ClientSession(*streams,read_timeout_seconds=timedelta(seconds=90)) as session:
    await session.initialize();tools=[];cursor=None
    while True:
     page=await session.list_tools(cursor=cursor);tools.extend(t for t in page.tools if t.name.startswith('agent_'));cursor=page.nextCursor
     if not cursor:break
    yield AgentConnection(session,tools)

def input_json():
 raw=sys.stdin.read(1024*1024+1)
 if len(raw)>1024*1024:raise ValueError('Input exceeds 1 MiB.')
 return json.loads(raw or '{}')

def request(value):
 if not isinstance(value,dict) or set(value)-{'id','tool','arguments'}:raise ValueError('Use id, tool and arguments fields.')
 if not isinstance(value.get('id'),str) or not 1<=len(value['id'])<=64:raise ValueError('Request id must have 1–64 characters.')
 if not isinstance(value.get('tool'),str) or not isinstance(value.get('arguments',{}),dict):raise ValueError('Use a tool string and arguments object.')
 return value

def emit(value):print(json.dumps(value,ensure_ascii=True),flush=True)

async def execute(args):
 if args.action=='batch':
  requests=input_json()
  if not isinstance(requests,list) or not 1<=len(requests)<=32:raise ValueError('Batch requires 1–32 requests.')
  requests=[request(v) for v in requests]
  if len({v['id'] for v in requests})!=len(requests):raise ValueError('Batch ids must be unique.')
 elif args.action=='call':
  arguments={} if sys.stdin.isatty() else input_json()
  if not isinstance(arguments,dict):raise ValueError('Tool arguments must be a JSON object.')
 async with connect(args.lab_root) as connection:
  if args.action=='list':return {'ok':True,'tools':[t.model_dump(mode='json') for t in connection.tools]}
  if args.action=='call':return await connection.call(args.tool,arguments)
  if args.action=='batch':
   values=[]
   for r in requests:values.append({'id':r['id'],**await connection.call(r['tool'],r.get('arguments',{}))})
   return {'ok':all(v['ok'] for v in values),'session_id':connection.session_id,'results':values}
  # NDJSON supports adaptive requests while the same SDK session stays alive.
  emit({'event':'ready','ok':True,'session_id':connection.session_id,'tools':[t.name for t in connection.tools]})
  seen=set()
  for _ in range(64):
   line=await asyncio.to_thread(sys.stdin.readline,MAX_LINE+1)
   if not line:return None
   if len(line)>MAX_LINE:
    emit({'id':None,'ok':False,'error':{'code':'REQUEST_TOO_LARGE','message':'Session request exceeds 64 KiB; connection closed.'}});return None
   try:
    r=request(json.loads(line))
    if r['id'] in seen:raise ValueError('Duplicate id; request was not repeated.')
    seen.add(r['id']);value=await connection.call(r['tool'],r.get('arguments',{}))
   except (ValueError,TypeError,json.JSONDecodeError):
    emit({'id':None,'ok':False,'error':{'code':'INVALID_REQUEST','message':'Invalid request or duplicate id; no tool call performed.'}});continue
   emit({'id':r['id'],**value})
  emit({'event':'closed','ok':True,'reason':'Session request limit reached.'})
 return None

def main():
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--lab-root',default=os.environ.get('MODDING_LAB_ROOT','D:/visual-development-toolkit'))
 sub=parser.add_subparsers(dest='action',required=True);sub.add_parser('list');sub.add_parser('batch');sub.add_parser('session');invoke=sub.add_parser('call');invoke.add_argument('tool');args=parser.parse_args()
 try:value=asyncio.run(execute(args))
 except Exception as error:value={'ok':False,'error':{'code':'MCP_CONNECTION_OR_ARGUMENT_ERROR','type':type(error).__name__,'message':'Check the runtime paths, JSON arguments and agent-layer/reports/skill-mcp.log.'}}
 if value is None:return 0
 emit(value);return 0 if value['ok'] else 1
if __name__=='__main__':sys.exit(main())
