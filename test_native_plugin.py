"""Exercise the installed native MCP connections on authored Windows fixtures."""
import asyncio,contextlib,datetime,json,os,pathlib,subprocess,traceback,zipfile
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image
ROOT=pathlib.Path(__file__).resolve().parent
RESULT={'host':os.environ.get('COMPUTERNAME'),'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':[],'servers':{}}
def check(name,valid,data):
    assert valid,name+': '+str(data)[:1200]
    RESULT['checks'].append({'name':name,'ok':True,'evidence':data});print('PASS',name,flush=True)
def payload(result):
    assert not result.isError,str(result)[:2000]
    if result.structuredContent is not None:return result.structuredContent
    texts=[p.text for p in result.content if p.type=='text']
    try:return json.loads(texts[0])
    except (ValueError,IndexError):return {'text':'\n'.join(texts)}
async def main():
    installed=json.loads((ROOT/'logs/plugin-install.json').read_text(encoding='utf-8-sig'));plugin=pathlib.Path(installed['installedPath'])
    RESULT['plugin']=installed
    config=json.loads((plugin/'mcp.json').read_text())['mcpServers']
    native=json.loads((ROOT/'native-runtime.json').read_text())
    environment=os.environ.copy();environment.update(DOTNET_ROOT=str(ROOT/'windows/dotnet-sdk'),TEMP=str(ROOT/'temp'),TMP=str(ROOT/'temp'),DOTNET_CLI_DO_NOT_USE_MSBUILD_SERVER='1',MSBUILDDISABLENODEREUSE='1',DOTNET_CLI_HOME=str(ROOT/'temp/dotnet'),NUGET_PACKAGES=str(ROOT/'temp/nuget'),DOTNET_CLI_TELEMETRY_OPTOUT='1')
    project_source=ROOT/'fixtures/managed/GameLogic.csproj';native_project=project_source.with_name('GameLogic.Native.csproj')
    native_project.write_text(project_source.read_text().replace('<TargetFramework>net8.0</TargetFramework>','<TargetFramework>net10.0</TargetFramework><AssemblyName>GameLogic</AssemblyName>'),encoding='utf-8')
    subprocess.run([str(ROOT/'windows/dotnet-sdk/dotnet.exe'),'build',str(native_project),'-c','Release','-p:UseSharedCompilation=false'],cwd=ROOT,env=environment,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
    subprocess.run([str(ROOT/'windows/venv/Scripts/python.exe'),'fixtures/create_unity_fixture.py'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW)
    async with contextlib.AsyncExitStack() as stack:
        sessions={}
        for name,entry in config.items():
            log=(ROOT/'logs'/f'native-test-{name}.log').open('w',encoding='utf-8');stack.callback(log.close)
            streams=await stack.enter_async_context(stdio_client(StdioServerParameters(command=entry['command'],args=[arg.replace('${PLUGIN_ROOT}',str(plugin)) for arg in entry['args']],env=entry['env']),errlog=log))
            session=await stack.enter_async_context(ClientSession(*streams,read_timeout_seconds=timedelta(seconds=420)))
            await session.initialize();catalog=await session.list_tools();sessions[name]=session
            RESULT['servers'][name]={'tools':len(catalog.tools)}
            check(name+' MCP discovery',len(catalog.tools)>0,RESULT['servers'][name])
        lab=sessions['modding-lab']
        async def call(name,args):return payload(await lab.call_tool(name,args,read_timeout_seconds=timedelta(seconds=420)))
        status=await call('component_status',{});check('Native components',status['mode']=='native' and all(status['analysis']['versions'][n]['ok'] for n in ['rea','ilspycmd','java']),status)
        name='native-test-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S');base=ROOT/'projects'/name;RESULT['project']=name
        created=await call('create_project',{'name':name});check('Project isolation',(base/'input').is_dir(),created)
        for source in [ROOT/'fixtures/managed/bin/Release/net10.0/GameLogic.dll',ROOT/'windows/AssetBridge/publish/AssetBridge.exe',ROOT/'fixtures/unity/lab.assets',ROOT/'fixtures/unity/texture.assets',ROOT/'fixtures/electron']:
            imported=await call('import_target',{'project_name':name,'source_path':str(source)});check('Import '+source.name,imported['files']>0,imported)
        decompiled=await call('decompile_dotnet',{'project_name':name,'input_file':'input/GameLogic.dll'})
        recovered=any('CalculateDamage' in p.read_text() for p in (base/'output').rglob('*.cs'))
        check('ILSpy recovered C#',decompiled['ok'] and recovered,decompiled)
        exported=await call('export_unity_assets',{'project_name':name,'input_path':'input/lab.assets','asset_type':'TextAsset'})
        saved=next(p['saved'] for p in exported['data']['items'] if p['type']=='TextAsset')
        check('Unity text exact bytes',exported['ok'] and pathlib.Path(saved).read_bytes()==(ROOT/'fixtures/unity/expected.txt').read_bytes(),exported)
        texture=await call('export_unity_assets',{'project_name':name,'input_path':'input/texture.assets','asset_type':'Texture2D'})
        saved=pathlib.Path(next(p['saved'] for p in texture['data']['items'] if p['type']=='Texture2D'))
        with Image.open(saved) as image:valid=image.size==(4,4) and image.convert('RGBA').getpixel((0,0))==(255,0,0,255)
        check('Unity DXT1 texture',texture['ok'] and valid,texture)
        authored=base/'output/authored';authored.mkdir()
        sprite=await call('run_um',{'project_name':name,'args':['sprite','fit',str(saved.relative_to(base)),'output/authored/icon.png','--size','64x64']})
        with Image.open(authored/'icon.png') as image:valid=image.size==(64,64)
        check('Native sprite processing',sprite['ok'] and valid,sprite)
        javascript=await call('rea_command',{'project_name':name,'args':['analyze-javascript-application',str(base/'input/electron'),'--json']})
        check('REA JavaScript',javascript['ok'],javascript)
        ping=payload(await sessions['ghidra'].call_tool('health.ping',{}));check('Ghidra health',bool(ping),ping)
        opened=payload(await sessions['ghidra'].call_tool('program.open',{'path':str(base/'input/AssetBridge.exe')},read_timeout_seconds=timedelta(seconds=420)))
        sid=opened['session_id'];summary=payload(await sessions['ghidra'].call_tool('program.summary',{'session_id':sid}))
        check('Ghidra Windows PE',bool(summary),summary)
        payload(await sessions['ghidra'].call_tool('program.close',{'session_id':sid}));check('Ghidra closes session',True,{'session_id':sid})
        rea=sessions['rea']
        doctor=await call('rea_command',{'project_name':name,'args':['doctor','--json']})
        check('REA doctor responds','ghidra' in json.dumps(doctor).lower(),doctor)
        opened=payload(await rea.call_tool('open_binary',{'path':str(base/'input/AssetBridge.exe'),'provider_id':'ghidra'},read_timeout_seconds=timedelta(seconds=420)))
        overview=payload(await rea.call_tool('binary_overview',{},read_timeout_seconds=timedelta(seconds=420)))
        check('REA Windows native P0',bool(overview),overview)
        payload(await rea.call_tool('close_binary',{}));check('REA closes session',True,opened)
        package=await call('package_project',{'project_name':name,'output_folder':'output/authored'})
        with zipfile.ZipFile(package['archive']) as z:valid=z.testzip() is None and z.namelist()==['icon.png']
        check('Source/asset ZIP',package['ok'] and valid,package)
        originals=await call('verify_originals',{'project_name':name});check('Original hashes intact',originals['ok'],originals)
        outside=await lab.call_tool('read_project_text',{'project_name':name,'file_path':'../../README.md'})
        check('Traversal rejected',outside.isError,{'rejected':outside.isError})
    RESULT.update(ok=True,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (ROOT/'reports/native-plugin-test.json').write_text(json.dumps(RESULT,indent=2),encoding='utf-8')
    print(json.dumps({'ok':True,'host':RESULT['host'],'checks':len(RESULT['checks']),'servers':RESULT['servers']},indent=2),flush=True)
if __name__=='__main__':
    try:asyncio.run(main())
    except Exception as error:
        RESULT.update(ok=False,error=str(error));(ROOT/'reports/native-plugin-test-failed.json').write_text(json.dumps(RESULT,indent=2),encoding='utf-8');traceback.print_exc();raise SystemExit(1)
