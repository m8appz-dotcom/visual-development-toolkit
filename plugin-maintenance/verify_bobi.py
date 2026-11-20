import asyncio,hashlib,importlib.util,json,os,pathlib,re,socket,subprocess,sys,time,tomllib,traceback
from contextlib import asynccontextmanager
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=pathlib.Path('D:/modding-lab');WORK=ROOT/'plugin-maintenance'
install=json.loads((WORK/'install.json').read_text(encoding='utf-8-sig'))
PLUGIN=pathlib.Path(install['installedPath'])
CONFIG=json.loads((PLUGIN/'mcp.json').read_text())['mcpServers']
REPORT={'host':socket.gethostname(),'version':'1.3.0','installed':str(PLUGIN),'checks':{},'failures':{}}
def save():
    (WORK/'verification.json').write_text(json.dumps(REPORT,indent=2,ensure_ascii=False),encoding='utf-8')
def data(response):
    if response.structuredContent is not None:return response.structuredContent
    parts=[c.text for c in response.content if hasattr(c,'text')]
    try:return json.loads('\n'.join(parts))
    except ValueError:return {'text':'\n'.join(parts)}
def find_key(value,key):
    if isinstance(value,dict):
        if key in value:return value[key]
        for v in value.values():
            found=find_key(v,key)
            if found is not None:return found
    elif isinstance(value,list):
        for v in value:
            found=find_key(v,key)
            if found is not None:return found
    return None
@asynccontextmanager
async def connect(name):
    cfg=CONFIG[name]
    with (WORK/(name+'-acceptance.log')).open('w',encoding='utf-8') as log:
        async with stdio_client(StdioServerParameters(command=cfg['command'],args=[a.replace('${PLUGIN_ROOT}',str(PLUGIN)) for a in cfg['args']],env={**os.environ,**cfg.get('env',{})}),errlog=log) as streams:
            async with ClientSession(*streams,read_timeout_seconds=timedelta(seconds=120)) as c:
                await c.initialize();yield c
async def call(c,name,args=None):
    response=await c.call_tool(name,args or {})
    assert not response.isError,(name,data(response))
    value=data(response)
    assert not isinstance(value,dict) or value.get('ok') is not False,(name,value)
    return value
async def inventory(c):
    page=await c.list_tools();tools=list(page.tools)
    while page.nextCursor:page=await c.list_tools(cursor=page.nextCursor);tools.extend(page.tools)
    return [t.model_dump(mode='json') for t in tools]
async def gateway():
    async with connect('modding-lab') as c:
        tools=await inventory(c);assert len(tools)==12
        assert not {'run_um','windows_game_tool','package_mod','package_project'}&{t['name'] for t in tools}
        assert (await c.call_tool('run_um',{'project_name':'unused','args':['fal']})).isError
        name='vdt-plugin-test-'+str(time.time_ns())
        project=await call(c,'create_project',{'name':name})
        base=ROOT/'projects'/name
        assert base.resolve().parent==(ROOT/'projects').resolve() and base.is_dir()
        fixtures=base/'input/js';fixtures.mkdir()
        (fixtures/'package.json').write_text(json.dumps({'name':'vdt-validation-fixture','version':'1.0.0','main':'main.js'}))
        (fixtures/'main.js').write_text('function double(value){return value*2;}\nfunction run(){return double(21);}\nmodule.exports={run};\n')
        text=await call(c,'read_project_text',{'project_name':name,'file_path':'input/js/main.js','max_chars':500})
        assert 'double' in json.dumps(text)
        listing=await call(c,'list_project_files',{'project_name':name,'folder':'input'})
        scan=await call(c,'recon_game',{'game_path':str(base/'input')})
        assert scan.get('ok') is True
        status=await call(c,'component_status')
        REPORT['checks']['gateway']={'tools':tools,'project':project,'source_read':text,'listing':listing,'recognition':scan,'status':status,'removed_tool_rejected':True,'fixture_project':name}
        save();print('Gateway: 12 tools, project/read/list/recon and status passed',flush=True)
        return name
async def javascript(name):
    script=PLUGIN/'skills/visual-development-agents/scripts/rea_mcp.py'
    spec=importlib.util.spec_from_file_location('rea_helper_bobi',script);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    async with m.connect() as conn:
        advertised=[t.name for t in conn.tools]
        assert 'analyze_javascript_application' in advertised and 'agent_job_start' not in advertised
        missing=await conn.call('agent_capabilities',{});assert not missing['ok'] and missing['error']['code']=='TOOL_UNAVAILABLE'
        analyzed=await conn.call('analyze_javascript_application',{'input_path':'/lab/projects/'+name+'/input/js','format':'directory'})
        assert analyzed['ok'],analyzed
        (WORK/'javascript-analysis.json').write_text(json.dumps(analyzed,indent=2),encoding='utf-8')
        evidence=analyzed.get('structured_content')
        if evidence is None:
            evidence=json.loads('\n'.join(x['text'] for x in analyzed['content'] if x['type']=='text'))
        envelope=evidence
        evidence=envelope.get('evidence',envelope)
        normalized=envelope.get('result',evidence.get('normalized_result',{}))
        graph=normalized.get('semantic_graph',{})
        nodes=graph.get('nodes',[])
        functions=[n for n in nodes if n.get('kind')=='function']
        assert len(functions)>=2,{'normalized_keys':list(normalized),'graph_keys':list(graph),'functions':len(functions)}
        seed=functions[0]['node_id']
        traced=await conn.call('trace_javascript_semantics',{'application':evidence,'query':{'seed':{'kind':'semantic-node','node_id':seed},'direction':'forward-influence'}})
        assert traced['ok'],traced
        assert analyzed['meta']['session_id']==traced['meta']['session_id']
        REPORT['checks']['javascript']={'helper_tools':advertised,'agent_extension_unavailable_explicit':True,'functions':len(functions),
            'semantic_nodes':len(nodes),'analysis':analyzed,'trace':traced,'single_session':True}
        save();print('REA/helper: real JS analysis and semantic trace passed in one Docker MCP session',flush=True)
    async with connect('rea') as c:
        tools=await inventory(c)
        ordered=sorted(tools,key=lambda t:t['name'])
        digest=hashlib.sha256(json.dumps(ordered,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
        meta=json.loads((PLUGIN/'skills/reverse-engineer-anything/references/tool-catalog.json').read_text())
        assert len(tools)==125 and meta['catalog_digest']==digest
        REPORT['checks']['rea_catalog']={'tools':len(tools),'digest_verified':True}
        save()
async def ghidra(name):
    async with connect('ghidra') as c:
        tools=await inventory(c);assert len(tools)==212
        ping=await call(c,'health.ping')
        opened=await call(c,'program.open',{'path':'/bin/true','project_location':'/lab/projects/'+name+'/output/ghidra',
              'project_name':'vdt-smoke-'+str(time.time_ns()),'program_name':'coreutils-true-readonly-input','update_analysis':True})
        REPORT['checks']['ghidra_open']={'response':opened};save()
        sid=find_key(opened,'session_id');assert sid,opened
        try:
            analysis=await call(c,'analysis.update_and_wait',{'session_id':sid})
            functions=await call(c,'function.list',{'session_id':sid,'limit':5})
            REPORT['checks']['ghidra_functions']=functions;save()
            # Recover the first function address from the actual function records.
            def address(v):
                if isinstance(v,dict):
                    for k in ['entry','entry_point','entryPoint','address','start','offset']:
                        if isinstance(v.get(k),(str,int)):return v[k]
                    for child in v.values():
                        found=address(child)
                        if found is not None:return found
                elif isinstance(v,list):
                    for child in v:
                        found=address(child)
                        if found is not None:return found
            items=functions.get('items',[])
            entry=items[0]['entry_point'] if items else None
            assert entry is not None,functions
            entry=int(entry,16) if isinstance(entry,str) else entry
            decompiled=await call(c,'decomp.function',{'session_id':sid,'function_start':entry,'timeout_secs':30})
            assert any(key in json.dumps(decompiled).lower() for key in ['return','void','int ','undefined']),decompiled
            REPORT['checks']['ghidra']={'tools':len(tools),'health':ping,'analysis':analysis,'functions':functions,'decompiled':decompiled}
            save();print('Ghidra: actual import, analysis, function listing and decompilation passed',flush=True)
        finally:
            REPORT['checks']['ghidra_close']=await call(c,'program.close',{'session_id':sid});save()
async def main():
    if '--retry' in sys.argv:
        global REPORT
        REPORT=json.loads((WORK/'verification.json').read_text(encoding='utf-8'))
        (WORK/'verification-initial-failed.json').write_text(json.dumps(REPORT,indent=2),encoding='utf-8')
        REPORT['failures']={}
        name=REPORT['checks']['gateway']['fixture_project']
        tasks=await asyncio.gather(asyncio.wait_for(javascript(name),timeout=100),asyncio.wait_for(ghidra(name),timeout=180),return_exceptions=True)
        for key,result in zip(['javascript','ghidra'],tasks):
            if isinstance(result,BaseException):REPORT['failures'][key]={'error':str(result),'traceback':''.join(traceback.format_exception(result))}
        REPORT['passed']=not REPORT['failures'];save()
        print(json.dumps({'passed':REPORT['passed'],'failures':REPORT['failures']},indent=2),flush=True)
        if REPORT['failures']:sys.exit(1)
        return
    spec=importlib.util.spec_from_file_location('validator',WORK/'quick_validate.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    skills={}
    for folder in (PLUGIN/'skills').iterdir():
        if not folder.is_dir():continue
        ok,reason=v.validate_skill(folder);assert ok,(folder,reason)
        skills[folder.name]=reason
    assert len(skills)==6
    REPORT['checks']['skills']=skills
    before=json.loads((WORK/'backups'/pathlib.Path(json.loads((WORK/'deployment.json').read_text())['backup']).name/'config.toml').read_text()) if False else None
    cfg=tomllib.loads((pathlib.Path.home()/'.codex/config.toml').read_text(encoding='utf-8-sig'))
    oldcfg=tomllib.loads((pathlib.Path(json.loads((WORK/'deployment.json').read_text())['backup'])/'config.toml').read_text(encoding='utf-8-sig'))
    for key in ['model','model_reasoning_effort','model_provider']:assert cfg.get(key)==oldcfg.get(key)
    assert cfg['plugins']['game-modding-toolkit@modding-lab']['enabled'] is True
    REPORT['checks']['configuration']={'plugin_enabled':True,'model_provider_preserved':True,'mcp_launch_definitions_preserved':CONFIG==json.loads((WORK/'baseline.json').read_text())['mcp_config']}
    save()
    name=await gateway()
    tasks=await asyncio.gather(asyncio.wait_for(javascript(name),timeout=100),asyncio.wait_for(ghidra(name),timeout=180),return_exceptions=True)
    for key,result in zip(['javascript','ghidra'],tasks):
        if isinstance(result,BaseException):REPORT['failures'][key]={'error':str(result),'traceback':''.join(traceback.format_exception(result))}
    status=REPORT['checks']['gateway']['status']['container']['data']
    after=json.loads(subprocess.check_output(['docker','inspect','modding-lab-analysis','--format','{{json .State}}'],text=True))
    REPORT['checks']['container_preserved']={'same_started_at':status['StartedAt']==after['StartedAt'],'running':after['Running']}
    assert status['StartedAt']==after['StartedAt'] and after['Running']
    REPORT['passed']=not REPORT['failures'];save()
    print(json.dumps({'passed':REPORT['passed'],'skills':len(skills),'failures':REPORT['failures'],'container_preserved':REPORT['checks']['container_preserved']},indent=2),flush=True)
    if REPORT['failures']:sys.exit(1)
if __name__=='__main__':asyncio.run(main())
