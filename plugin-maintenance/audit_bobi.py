import asyncio,json,os,pathlib,socket
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=pathlib.Path('D:/modding-lab');PLUGIN=ROOT/'plugins/game-modding-toolkit';OUT=ROOT/'plugin-maintenance'
async def inspect(name,cfg):
    with (OUT/(name+'-baseline.log')).open('w',encoding='utf-8') as log:
        async with stdio_client(StdioServerParameters(command=cfg['command'],args=[s.replace('${PLUGIN_ROOT}',str(PLUGIN)) for s in cfg['args']],env={**os.environ,**cfg.get('env',{})}),errlog=log) as streams:
            async with ClientSession(*streams,read_timeout_seconds=timedelta(seconds=40)) as session:
                init=await session.initialize();page=await session.list_tools();tools=list(page.tools)
                while page.nextCursor:page=await session.list_tools(cursor=page.nextCursor);tools.extend(page.tools)
                result={'server':init.serverInfo.model_dump(mode='json'),'tools':[t.model_dump(mode='json') for t in tools]}
                if name=='modding-lab':result['status']=(await session.call_tool('component_status',{})).model_dump(mode='json')
                return name,result
async def main():
    OUT.mkdir(exist_ok=True)
    cfg=json.loads((PLUGIN/'mcp.json').read_text())['mcpServers']
    pairs=await asyncio.gather(*(asyncio.wait_for(inspect(n,c),timeout=100) for n,c in cfg.items()),return_exceptions=True)
    servers={}
    for name,pair in zip(cfg,pairs):servers[name]={'error':repr(pair)} if isinstance(pair,BaseException) else pair[1]
    result={'host':socket.gethostname(),'root':str(ROOT),'manifest':json.loads((PLUGIN/'.codex-plugin/plugin.json').read_text()),'mcp_config':cfg,'servers':servers}
    (OUT/'baseline.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'host':socket.gethostname(),'servers':{n:{'tools':len(v.get('tools',[])),'agents':[t['name'] for t in v.get('tools',[]) if t['name'].startswith('agent_')],'error':v.get('error'),'status':v.get('status')} for n,v in servers.items()}},indent=2))
asyncio.run(main())
