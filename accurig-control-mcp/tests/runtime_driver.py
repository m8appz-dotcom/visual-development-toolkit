"""Keep one real MCP client session alive for the authorized end-to-end test."""
import asyncio,json,pathlib,time,sys,re
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=pathlib.Path(__file__).resolve().parents[1]
TAG=sys.argv[1] if len(sys.argv)>1 else ''
assert re.fullmatch(r'[a-zA-Z0-9-]*',TAG)
async def main():
 commands=ROOT/('reports/commands'+TAG+'.jsonl');commands.touch(exist_ok=True)
 params=StdioServerParameters(command='D:/visual-development-toolkit/windows/node/node-v24.19.0-win-x64/node.exe',args=[str(ROOT/'src/server.mjs')])
 with (ROOT/('reports/mcp-server'+TAG+'.log')).open('a',encoding='utf8') as log:
  async with stdio_client(params,errlog=log) as streams:
   async with ClientSession(*streams,read_timeout_seconds=timedelta(minutes=4)) as session:
    await session.initialize();tools=await session.list_tools();(ROOT/'reports/live-tools.json').write_text(json.dumps([t.model_dump(mode='json') for t in tools.tools],indent=2));print('MCP connected: '+','.join(t.name for t in tools.tools),flush=True)
    with commands.open(encoding='utf8') as queue,(ROOT/('reports/responses'+TAG+'.jsonl')).open('a',encoding='utf8') as output:
     deadline=time.monotonic()+14400
     while time.monotonic()<deadline:
      line=queue.readline()
      if not line:await asyncio.sleep(.2);continue
      r=json.loads(line)
      if r['tool']=='__stop':break
      started=time.monotonic()
      result=await session.call_tool(r['tool'],r.get('arguments',{}))
      value={'id':r['id'],'tool':r['tool'],'is_error':bool(result.isError),'elapsed_ms':round((time.monotonic()-started)*1000,2),'data':result.structuredContent,'content':[x.model_dump(mode='json') for x in result.content] if not result.structuredContent else None}
      output.write(json.dumps(value)+'\n');output.flush();print(json.dumps({'id':r['id'],'tool':r['tool'],'is_error':bool(result.isError)}),flush=True)
asyncio.run(main())
