"""Real MCP: recover the completed Nico receipt in a new controller, no native replay."""
import asyncio,json,pathlib
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
root=pathlib.Path(__file__).resolve().parents[1]
async def main():
 record={'passed':False,'steps':[]}
 params=StdioServerParameters(command='D:/visual-development-toolkit/windows/node/node-v24.19.0-win-x64/node.exe',args=[str(root/'src/server.mjs')])
 async with stdio_client(params) as streams:
  async with ClientSession(*streams) as session:
   await session.initialize()
   for name,args in [('accurig_reconcile_session',{'recovery_job_id':'16e56003518f4a57b8208d2150b91d39'}),('accurig_status',{}),('accurig_export_fbx',{'output_path':str(root/'outputs/must-not-export-offline.fbx')})]:
    result=await session.call_tool(name,args);data=result.structuredContent
    record['steps'].append({'tool':name,'data':data})
    if name=='accurig_reconcile_session':assert data['ok'] and data['result']['recovered']
    elif name=='accurig_status':assert data['ok'] and data['result']['rigged'] and not data['result']['connected']
    else:assert not data['ok'] and 'NOT_CONNECTED' in data['error']['message']
   record['passed']=True
 (root/'reports/recovery-reconnect-nico.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
 print(json.dumps({'passed':record['passed'],'real_mcp_checks':len(record['steps'])}))
asyncio.run(main())
