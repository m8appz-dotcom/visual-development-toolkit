"""Exercise actual MCP servers from the installed plugin manifest; save every result."""
import asyncio,contextlib,datetime,json,pathlib,sys,traceback,subprocess
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=pathlib.Path(__file__).parent
REPORT=ROOT/'reports/plugin-test.json'
RESULT={'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':[]}

def payload(result):
    value=result.model_dump(mode='json')
    if value.get('isError'):raise RuntimeError(json.dumps(value)[:2500])
    if value.get('structuredContent') is not None:return value['structuredContent']
    for item in value.get('content',[]):
        if item.get('type')=='text':
            try:return json.loads(item['text'])
            except ValueError:return {'text':item['text']}
    return value

async def call(session,name,args,check=None):
    result=await session.call_tool(name,args,read_timeout_seconds=timedelta(seconds=300))
    data=payload(result)
    if check:check(data)
    RESULT['checks'].append({'tool':name,'arguments':args,'ok':True,'result':data})
    REPORT.write_text(json.dumps(RESULT,indent=2),encoding='utf-8')
    print('PASS',name,flush=True)
    return data

async def connect(stack,plugin,name):
    config=json.loads((plugin/'mcp.json').read_text())['mcpServers'][name]
    args=[arg.replace('${PLUGIN_ROOT}',str(plugin)) for arg in config['args']]
    log=(ROOT/'logs'/f'test-{name}.log').open('w',encoding='utf-8');stack.callback(log.close)
    read,write=await stack.enter_async_context(stdio_client(StdioServerParameters(command=config['command'],args=args,env=config.get('env')),errlog=log))
    session=await stack.enter_async_context(ClientSession(read,write,read_timeout_seconds=timedelta(seconds=300)))
    await session.initialize()
    tools=await session.list_tools()
    RESULT.setdefault('servers',{})[name]={'tools':len(tools.tools),'names':[t.name for t in tools.tools]}
    print('CONNECTED',name,len(tools.tools),flush=True)
    return session,tools.tools

def require_ok(data):
    if not data.get('ok'):raise AssertionError(json.dumps(data)[:2500])

async def main():
    install=json.loads((ROOT/'logs/plugin-install.json').read_text(encoding='utf-8-sig'))
    # The caller passes the installed cache path reported by Codex, never a manually edited cache.
    plugin=pathlib.Path(sys.argv[1])
    RESULT['installed_plugin']=str(plugin)
    name='toolkit-test-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    async with contextlib.AsyncExitStack() as stack:
        lab,_=await connect(stack,plugin,'modding-lab')
        status=await call(lab,'component_status',{})
        require_ok(status['analysis'])
        await call(lab,'create_project',{'name':name})
        base=ROOT/'projects'/name
        for source in [ROOT/'fixtures/native/game_logic',ROOT/'fixtures/managed/bin/Release/net8.0/GameLogic.dll',ROOT/'windows/AssetBridge/publish/AssetBridge.exe',ROOT/'fixtures/unity/lab.assets',ROOT/'fixtures/unity/texture.assets',ROOT/'fixtures/electron']:
            await call(lab,'import_target',{'project_name':name,'source_path':str(source)})
        def check_cs(data):
            require_ok(data)
            sources=list((base/'output').rglob('*.cs'))
            assert any('CalculateDamage' in p.read_text() and 'Math.Max' in p.read_text() for p in sources)
        await call(lab,'decompile_dotnet',{'project_name':name,'input_file':'input/GameLogic.dll'},check_cs)
        await call(lab,'inspect_unity_assets',{'project_name':name,'input_path':'input/lab.assets'},require_ok)
        def check_asset(data):
            require_ok(data)
            saved=next(i['saved'] for i in data['data']['items'] if i['type']=='TextAsset')
            assert pathlib.Path(saved).read_bytes()==(ROOT/'fixtures/unity/expected.txt').read_bytes()
        await call(lab,'export_unity_assets',{'project_name':name,'input_path':'input/lab.assets','asset_type':'TextAsset'},check_asset)
        def check_texture(data):
            from PIL import Image
            require_ok(data)
            saved=next(i['saved'] for i in data['data']['items'] if i['type']=='Texture2D')
            with Image.open(saved) as image:assert image.size==(4,4) and image.convert('RGBA').getpixel((0,0))==(255,0,0,255)
        texture=await call(lab,'export_unity_assets',{'project_name':name,'input_path':'input/texture.assets','asset_type':'Texture2D'},check_texture)
        saved=next(i['saved'] for i in texture['data']['items'] if i['type']=='Texture2D')
        await call(lab,'run_um',{'project_name':name,'args':['sprite','fit',str(pathlib.Path(saved).relative_to(base)),'output/sprite-32.png','--size','32x32']},require_ok)
        from PIL import Image
        with Image.open(base/'output/sprite-32.png') as image:assert image.size==(32,32)
        await call(lab,'run_um',{'project_name':name,'args':['sprite','--help']},require_ok)
        await call(lab,'run_um',{'project_name':name,'args':['kb','search','Terraria'],'platform':'windows'},require_ok)
        await call(lab,'rea_command',{'project_name':name,'args':['analyze-javascript-application',f'/lab/projects/{name}/input/electron','--json']},require_ok)
        ghidra,ghidra_tools=await connect(stack,plugin,'ghidra')
        (ROOT/'reports/ghidra-tool-schemas.json').write_text(json.dumps([t.model_dump(mode='json') for t in ghidra_tools],indent=2))
        opened=await call(ghidra,'program.open',{'path':f'/lab/projects/{name}/input/game_logic'})
        sid=opened.get('session_id') or opened.get('result',{}).get('session_id')
        if not sid:raise AssertionError('No Ghidra session_id: '+json.dumps(opened)[:1500])
        await call(ghidra,'program.report',{'session_id':sid})
        functions=await call(ghidra,'function.list',{'session_id':sid,'limit':100})
        found=await call(ghidra,'function.by_name',{'session_id':sid,'name':'CalculateDamage','exact':True})
        assert found['total']==1
        dossier=await call(ghidra,'function.report',{'session_id':sid,'function_start':found['items'][0]['entry_point']})
        assert dossier['decompile_completed'] and 'CalculateDamage' in dossier['c'] and '-' in dossier['c']
        (base/'reports/ghidra-damage.c').write_text(dossier['c'])
        RESULT['ghidra_session_id']=sid
        await call(ghidra,'program.close',{'session_id':sid})
        pe=await call(ghidra,'program.open',{'path':f'/lab/projects/{name}/input/AssetBridge.exe'})
        await call(ghidra,'program.summary',{'session_id':pe['session_id']})
        await call(ghidra,'program.close',{'session_id':pe['session_id']})
        rea,rea_tools=await connect(stack,plugin,'rea')
        (ROOT/'reports/rea-tool-schemas.json').write_text(json.dumps([t.model_dump(mode='json') for t in rea_tools],indent=2))
        await call(rea,'open_binary',{'path':f'/lab/projects/{name}/input/game_logic','provider_id':'ghidra'})
        await call(rea,'binary_overview',{})
        await call(rea,'close_binary',{})
        # Native analysis CLI is independently checked even if the upstream MCP schema changes.
        await call(lab,'rea_command',{'project_name':name,'args':['function',f'/lab/projects/{name}/input/game_logic','CalculateDamage','--provider','ghidra','--json']},require_ok)
        await call(lab,'verify_originals',{'project_name':name},require_ok)
        denied=await lab.call_tool('read_project_text',{'project_name':name,'file_path':'../../README.md'})
        assert denied.isError
        RESULT['checks'].append({'tool':'path_traversal_guard','ok':True,'result':'Rejected a path outside the project.'})
    await asyncio.sleep(3)
    process_list=subprocess.check_output(['docker','exec','modding-lab-analysis','ps','-eo','pid,comm'],text=True,timeout=20,creationflags=subprocess.CREATE_NO_WINDOW)
    assert not any(name in process_list for name in ['java','ghidra-headless','demangler','node']),process_list
    RESULT['checks'].append({'tool':'session_process_cleanup','ok':True,'result':process_list})
    RESULT['ok']=True;RESULT['project']=name

if __name__=='__main__':
    try:asyncio.run(main())
    except BaseException as e:
        RESULT['ok']=False;RESULT['error']=str(e);RESULT['traceback']=traceback.format_exc();print(RESULT['traceback'],flush=True)
    finally:
        RESULT['finished']=datetime.datetime.now(datetime.timezone.utc).isoformat();REPORT.write_text(json.dumps(RESULT,indent=2),encoding='utf-8')
    sys.exit(0 if RESULT.get('ok') else 1)
