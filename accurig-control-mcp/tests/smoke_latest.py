import asyncio,json,pathlib
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
P=pathlib.Path(__file__).resolve().parents[1]
async def main():
 with (P/'reports/smoke-latest-stderr.log').open('w') as log:
  async with stdio_client(StdioServerParameters(command='D:/visual-development-toolkit/windows/node/node-v24.19.0-win-x64/node.exe',args=[str(P/'src/server.mjs')]),errlog=log) as streams:
   async with ClientSession(*streams) as c:
    async def call(name,args=None):
     r=await c.call_tool(name,args or {});assert not r.isError,r;return r.structuredContent['result']
    async def finish(j):
     while j['state']=='working':await asyncio.sleep(2);j=await call('accurig_job_status',{'job_id':j['id']})
     assert j['state']=='completed',j
     return j['result']
    await c.initialize();ts=await c.list_tools();connected=await call('accurig_connect');assert connected['model'] is None and not connected['rigged']
    model=await call('accurig_inspect_model',{'input_path':'D:/Applications/Reallusion/AccuRIG/Sample Character/Pete.obj'})
    load=await call('accurig_load_model',{'input_path':model['path']})
    busy=await c.call_tool('accurig_detect_joints',{'body':False,'fingers':'None'});assert busy.isError
    await finish(load);j=await call('accurig_inspect_rig');elbow=next(x for x in j['data']['bodyJoints'] if x['name'].endswith('L_Forearm'))
    edited=await finish(await call('accurig_edit_joints',{'expected_revision':j['revision'],'coordinate_space':'accurig_native_model','changes':[{'name':elbow['name'],'position':elbow['position']}]}))
    closed=await call('accurig_close_session');status=await call('accurig_status');assert status['model'] is None and status['generation'] is None
    result={'passed':True,'tools':len(ts.tools),'connect':connected,'inspect_model':model,'busy_rejected':bool(busy.isError),'native_edit_readback':edited,'close':closed,'final_status':status}
    (P/'reports/smoke-latest.json').write_text(json.dumps(result,indent=2));print(str(len(ts.tools))+' tools: real load/edit, BUSY rejection and state reset passed')
asyncio.run(main())
