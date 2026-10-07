"""Targeted checks of installed 1.1.0 instructions, connections and asset bundling."""
import asyncio,contextlib,datetime,hashlib,json,pathlib,subprocess,zipfile
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
from PIL import Image
ROOT=pathlib.Path(__file__).parent
RESULT={'started':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':[],'servers':{}}
def check(label,condition,evidence):
    assert condition,label
    RESULT['checks'].append({'name':label,'ok':True,'evidence':evidence})
    print('PASS',label,flush=True)
def payload(result):
    assert not result.isError,str(result)[:1500]
    if result.structuredContent is not None:return result.structuredContent
    return json.loads(next(i.text for i in result.content if i.type=='text'))
async def main():
    installed=json.loads((ROOT/'logs/plugin-install.json').read_text(encoding='utf-8-sig'))
    plugin=pathlib.Path(installed['installedPath']);RESULT['installed_plugin']=str(plugin)
    manifest=json.loads((plugin/'plugin.json').read_text())
    compat=json.loads((plugin/'.codex-plugin/plugin.json').read_text())
    interface=manifest['extensions']['com.openai']['interface']
    check('Installed identity and presentation',manifest['version']=='1.1.0' and interface['displayName']=='Visual Development Toolkit' and compat['interface']==interface and compat['version']=='1.1.0',interface)
    skill_paths=list((plugin/'skills').glob('*/SKILL.md'))
    check('Development skills and optional references',len(skill_paths)==10 and not any((plugin/'skills'/n).exists() for n in ['mod-any-game','mashup-mods','publish-mod']) and (plugin/'references/optional-modding/mod-any-game/SKILL.md').is_file(),[str(p.relative_to(plugin)) for p in skill_paths])
    primary=(plugin/'skills/modding-lab/SKILL.md').read_text()
    check('Source creation and integration workflow','new project' in primary and 'Integrate actual files' in primary and 'package_project' in primary and 'visual app' in (plugin/'skills/fal-assets/SKILL.md').read_text(),str(plugin/'skills/modding-lab/SKILL.md'))
    host=json.loads((ROOT/'reports/codex-host-plugin-list.json').read_text())['plugins'][0]
    check('Codex host installed and enabled',host['installed'] and host['enabled'] and host['localVersion']=='1.1.0' and host['interface']['displayName']==interface['displayName'],host['id'])
    config=json.loads((plugin/'mcp.json').read_text())['mcpServers']
    async with contextlib.AsyncExitStack() as stack:
        sessions={}
        for name,entry in config.items():
            log=(ROOT/'logs'/f'visual-test-{name}.log').open('w',encoding='utf-8');stack.callback(log.close)
            params=StdioServerParameters(command=entry['command'],args=[a.replace('${PLUGIN_ROOT}',str(plugin)) for a in entry['args']],env=entry.get('env'))
            read,write=await stack.enter_async_context(stdio_client(params,errlog=log))
            session=await stack.enter_async_context(ClientSession(read,write,read_timeout_seconds=timedelta(seconds=240)))
            initialized=await session.initialize();catalog=await session.list_tools();sessions[name]=session
            RESULT['servers'][name]={'tools':len(catalog.tools),'server':initialized.serverInfo.model_dump(mode='json')}
            check(name+' MCP connection',len(catalog.tools)>0,RESULT['servers'][name])
        lab=sessions['modding-lab']
        async def call(name,args):return payload(await lab.call_tool(name,args))
        status=await call('component_status',{})
        check('Installed components healthy',status['analysis']['ok'] and status['container']['data']['Health']['Status']=='healthy',status)
        ping=payload(await sessions['ghidra'].call_tool('health.ping',{}))
        check('Ghidra health call',bool(ping),ping)
        name='visual-development-test-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S');RESULT['project']=name
        created=await call('create_project',{'name':name});base=ROOT/'projects'/name
        check('Isolated game/app asset project',(base/'output').is_dir(),created)
        fixture=ROOT/'fixtures/texture-export/sprite-32.png'
        imported=await call('import_target',{'project_name':name,'source_path':str(fixture)})
        check('Asset imported without changing original',imported['files']==1,imported)
        authored=base/'output/visual-app';authored.mkdir();(authored/'assets').mkdir()
        (authored/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><title>Asset fixture</title><img src="assets/icon.png" width="64" height="64" alt="Red square"></html>',encoding='utf-8')
        fit=await call('run_um',{'project_name':name,'args':['sprite','fit','input/sprite-32.png','output/visual-app/assets/icon.png','--size','64x64']})
        with Image.open(authored/'assets/icon.png') as image:valid=image.size==(64,64) and image.convert('RGBA').getpixel((32,32))==(255,0,0,255)
        check('App visual asset processing',fit['ok'] and valid,fit)
        bundle=await call('package_project',{'project_name':name,'output_folder':'output/visual-app'})
        with zipfile.ZipFile(bundle['archive']) as archive:
            valid=archive.testzip() is None and set(archive.namelist())=={'index.html','assets/icon.png'} and archive.read('assets/icon.png')==(authored/'assets/icon.png').read_bytes()
        check('Game/app source and asset ZIP',bundle['ok'] and bundle['files']==2 and valid,bundle)
        outside=await lab.call_tool('package_project',{'project_name':name,'output_folder':'../../README.md'})
        check('Out-of-project packaging rejected',outside.isError,str(outside)[:1000])
        root=await lab.call_tool('package_project',{'project_name':name,'output_folder':'output'})
        check('Output root self-packaging rejected',root.isError,str(root)[:1000])
        original=await call('verify_originals',{'project_name':name})
        check('Original asset integrity',original['ok'],original)
    check('Clean Ghidra session log',not (ROOT/'logs/visual-test-ghidra.log').read_text().strip(),str(ROOT/'logs/visual-test-ghidra.log'))
    RESULT.update(ok=True,finished=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (ROOT/'reports/visual-development-test.json').write_text(json.dumps(RESULT,indent=2),encoding='utf-8')
    print(json.dumps({'ok':True,'checks':len(RESULT['checks']),'servers':RESULT['servers'],'project':RESULT['project']},indent=2))
if __name__=='__main__':
    try:asyncio.run(main())
    except Exception as error:
        RESULT.update(ok=False,error=str(error));(ROOT/'reports/visual-development-test-failed.json').write_text(json.dumps(RESULT,indent=2));raise
