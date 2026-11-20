"""Validate the installed RE-focused plugin using real, read-only MCP operations."""
import asyncio,ast,hashlib,importlib.util,json,os,pathlib,re,shutil,sys,tomllib
from datetime import timedelta
import yaml
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

LAB=pathlib.Path('D:/visual-development-toolkit');WORK=LAB/'plugin-maintenance'
SOURCE=LAB/'plugins/game-modding-toolkit'
INSTALLED=pathlib.Path('C:/Users/kenny/.codex/plugins/cache/modding-lab/game-modding-toolkit/1.3.0')
MIRROR=LAB/'codex-plugin-cache/modding-lab/game-modding-toolkit/1.3.0'
REMOVED={'run_um','windows_game_tool','package_mod','package_project'}

def tree(folder):
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}

async def inspect(name,config):
    params=StdioServerParameters(command=config['command'],args=[a.replace('${PLUGIN_ROOT}',str(INSTALLED)) for a in config['args']],env={**os.environ,**config.get('env',{})})
    with (WORK/(name+'-verify.log')).open('w',encoding='utf-8') as log:
        async with stdio_client(params,errlog=log) as streams:
            async with ClientSession(*streams,read_timeout_seconds=timedelta(seconds=45)) as session:
                init=await session.initialize();page=await session.list_tools();tools=list(page.tools)
                while page.nextCursor:
                    page=await session.list_tools(cursor=page.nextCursor);tools.extend(page.tools)
                descriptors=[t.model_dump(mode='json') for t in tools]
                result={'connected':True,'server':init.serverInfo.model_dump(mode='json'),'count':len(tools),'tools':descriptors}
                if name=='modding-lab':
                    assert len(tools)==12 and not REMOVED&{t.name for t in tools}
                    invalid=await session.call_tool('run_um',{'project_name':'unused','args':['fal']})
                    assert invalid.isError, 'Removed tool still callable'
                    result['removed_tool_rejected']=True
                    status=await session.call_tool('component_status',{});assert not status.isError
                    result['status']=status.model_dump(mode='json')
                    files=await session.call_tool('list_project_files',{'project_name':'accurig-extraction-20261020','folder':'reports'})
                    assert not files.isError
                    result['read_only_project_listing']=True
                elif name=='ghidra':
                    health=await session.call_tool('health.ping',{});assert not health.isError
                    result['health']=health.model_dump(mode='json')
                else:
                    ordered=sorted(descriptors,key=lambda t:t['name'])
                    digest=hashlib.sha256(json.dumps(ordered,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
                    catalog=json.loads((INSTALLED/'skills/reverse-engineer-anything/references/tool-catalog.json').read_text())
                    assert catalog['tool_count']==len(tools) and catalog['catalog_digest']==digest
                    result['catalog_digest_verified']=True
                return name,result

async def helper_test():
    script=INSTALLED/'skills/visual-development-agents/scripts/rea_mcp.py'
    spec=importlib.util.spec_from_file_location('reviewed_rea_helper',script);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    results={}
    async with module.connect(str(LAB)) as connection:
        assert len(connection.tools)==15
        results['capabilities']=await connection.call('agent_capabilities',{})
        job='0ea8a45617a64e99bca87db5cecf4c45'
        results['job']=await connection.call('agent_job_status',{'job_id':job})
        results['search']=await connection.call('agent_graph_search',{'job_id':job,'query':'setMotionOffset','kind':'function','limit':1})
        for r in results.values():assert r['ok'] and r['structured_content']['ok'],r
        items=results['search']['structured_content']['result']['items']
        if not items:
            results['search']=await connection.call('agent_graph_search',{'job_id':job,'query':'','kind':'function','limit':1})
            assert results['search']['ok']
            items=results['search']['structured_content']['result']['items']
        assert items
        results['context']=await connection.call('agent_graph_function_context',{
            'job_id':job,'node_id':items[0]['id'],'limit':2,
            'source_root':str(LAB/'projects/accurig-extraction-20261020/output/application')})
        assert results['context']['ok'] and results['context']['structured_content']['ok'],results['context']
        original=results['context']['structured_content']['result']['source']
        assert original['available'] and not original['truncated'] and original['text']
        sessions={r['meta']['session_id'] for r in results.values()}
        assert len(sessions)==1
        return {'tools':len(connection.tools),'single_session':True,'existing_job_reused':True,'responses':results}

async def main():
    assert tree(SOURCE)==tree(INSTALLED),'Source/install mismatch'
    if MIRROR.exists():assert tree(MIRROR)==tree(INSTALLED)
    else:
        assert MIRROR.resolve().parent==(LAB/'codex-plugin-cache/modding-lab/game-modding-toolkit').resolve()
        shutil.copytree(INSTALLED,MIRROR)
    assert tree(MIRROR)==tree(INSTALLED)
    cfg=tomllib.loads(pathlib.Path('C:/Users/kenny/.codex/config.toml').read_text(encoding='utf-8-sig'))
    assert cfg['plugins']['game-modding-toolkit@modding-lab']['enabled']
    assert cfg['plugins']['accurig-control@modding-lab']['enabled']
    skill_paths=list((INSTALLED/'skills').glob('*/SKILL.md'));assert len(skill_paths)==6
    skill_validation={}
    validator_path=pathlib.Path('C:/Users/kenny/.codex/skills/.system/skill-creator/scripts/quick_validate.py')
    spec=importlib.util.spec_from_file_location('skill_validator',validator_path);validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator)
    for p in skill_paths:
        ok,detail=validator.validate_skill(p.parent);assert ok,(p,detail)
        skill_validation[p.parent.name]=detail
    receipt=json.loads((WORK/'change-receipt.json').read_text())
    preserved_asset=pathlib.Path(receipt['backup'])/'excluded/skills/asset-pipeline'
    assert validator.validate_skill(preserved_asset)[0]
    for p in (INSTALLED/'server').glob('*.py'):ast.parse(p.read_text())
    # All local markdown resource links in retained skills must remain resolvable.
    broken=[]
    for p in (INSTALLED/'skills').rglob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
            if re.match(r'^(https?:|#|mailto:)',link) or '<' in link:continue
            dest=link.split('#')[0]
            if dest and not (p.parent/dest).exists():broken.append({'file':str(p),'link':link})
    assert not broken,broken
    configs=json.loads((INSTALLED/'mcp.json').read_text())['mcpServers']
    assert set(configs)=={'modding-lab','ghidra','rea'}
    pairs=await asyncio.gather(*(asyncio.wait_for(inspect(n,c),timeout=110) for n,c in configs.items()))
    servers=dict(pairs)
    helper=await asyncio.wait_for(helper_test(),timeout=90)
    result={'passed':True,'host':'X','version':'1.3.0','source':str(SOURCE),'installed':str(INSTALLED),'desktop_cache':str(MIRROR),
        'source_install_cache_identical':True,'skills':skill_validation,'archived_asset_yaml_valid':True,
        'broken_resource_links':broken,'servers':servers,'helper':helper,
        'before_bytes':receipt['original_source_bytes'],'after_bytes':sum(p.stat().st_size for p in INSTALLED.rglob('*') if p.is_file() and '__pycache__' not in p.parts),
        'bobi_modified':False,'limits':'No remote Bobi runtime check, new decompilation, model inference or independent agent behavior evaluation.'}
    (WORK/'verification.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['servers','helper']},indent=2))
    print('MCP tools: '+str({n:s['count'] for n,s in servers.items()}))
    print('Agent helper: capabilities, existing job, graph search and function context passed in one session')

asyncio.run(main())
