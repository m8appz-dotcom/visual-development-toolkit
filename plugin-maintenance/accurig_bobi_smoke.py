import asyncio,importlib.util,json,os,pathlib,socket,sys,time,traceback
from datetime import timedelta
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
import yaml
ROOT=pathlib.Path('D:/modding-lab');WORK=ROOT/'plugin-maintenance';CONTROL=ROOT/'accurig-control-mcp'
PLUGIN=pathlib.Path(json.loads((WORK/'accurig-bobi-install.json').read_text(encoding='utf-8-sig'))['installedPath'])
cfg=json.loads((PLUGIN/'mcp.json').read_text())['mcpServers']['accurig-control']
phase=sys.argv[1] if len(sys.argv)>1 else 'contract'
report={'host':socket.gethostname(),'phase':phase,'plugin':str(PLUGIN),'controller':str(CONTROL),'checks':{}}
def save():
    (WORK/('accurig-bobi-'+phase+'.json')).write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
async def main():
    spec=importlib.util.spec_from_file_location('validate',WORK/'quick_validate.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
    assert v.validate_skill(PLUGIN/'skills/accurig-control')[0]
    meta=yaml.safe_load((PLUGIN/'skills/accurig-control/agents/openai.yaml').read_text(encoding='utf-8'))
    assert meta['policy']['allow_implicit_invocation'] and meta['dependencies']['tools'][0]['value']=='accurig-control'
    report['checks']['skill_valid_and_automatic']=True
    params=StdioServerParameters(command=cfg['command'],args=cfg['args'],env={**os.environ,**cfg['env']})
    with (WORK/('accurig-bobi-'+phase+'-stderr.log')).open('w',encoding='utf-8') as log:
        async with stdio_client(params,errlog=log) as streams:
            async with ClientSession(*streams,read_timeout_seconds=timedelta(seconds=45)) as session:
                init=await session.initialize();page=await session.list_tools();tools=page.tools
                assert len(tools)==19
                report['checks']['server']=init.serverInfo.model_dump(mode='json')
                report['checks']['tools']=[t.model_dump(mode='json') for t in tools]
                async def call(name,args=None):
                    r=await session.call_tool(name,args or {})
                    value=r.structuredContent
                    assert not r.isError and value['ok'],(name,value)
                    return value['result']
                async def job(value):
                    start=time.monotonic();last=0
                    while value['state']=='working':
                        if time.monotonic()-last>20:
                            print(value['type']+': '+str(value.get('phase')),flush=True);last=time.monotonic()
                        assert time.monotonic()-start<480,'MCP operation did not reach a final state within test budget; no replay'
                        await asyncio.sleep(2);value=await call('accurig_job_status',{'job_id':value['id']})
                    assert value['state']=='completed',value
                    report['checks']['last_job']=value;save()
                    return value['result']
                report['checks']['status_before']=await call('accurig_status');save()
                if phase=='contract':
                    report['passed']=True;save();print('AccuRIG plugin: skill validates, automatic selection enabled, MCP19 connects and status responds',flush=True);return
                try:
                    report['checks']['connected']=await call('accurig_connect');save()
                    sample=pathlib.Path(cfg['env']['ACCURIG_INSTALL_DIR'])/'Sample Character/Pete.obj'
                    inspected=await call('accurig_inspect_model',{'input_path':str(sample)})
                    assert inspected['verdict']=='passed';report['checks']['model_inspection']=inspected
                    report['checks']['load']=await job(await call('accurig_load_model',{'input_path':str(sample)}));save()
                    joints=await call('accurig_inspect_rig');report['checks']['joint_inspection']=joints
                    elbow=next(j for j in joints['data']['bodyJoints'] if j['name'].endswith('L_Forearm'))
                    checkpoint=await call('accurig_save_checkpoint');report['checks']['checkpoint']=checkpoint
                    edited=await job(await call('accurig_edit_joints',{'expected_revision':joints['revision'],'coordinate_space':'accurig_native_model','changes':[{'name':elbow['name'],'position':elbow['position']}]}))
                    report['checks']['joint_edit_same_position']=edited
                    now=await call('accurig_inspect_rig');report['checks']['restored']=await job(await call('accurig_restore_checkpoint',{'checkpoint_id':checkpoint['id'],'expected_revision':now['revision']}));save()
                    report['checks']['build']=await job(await call('accurig_build_skin'));save()
                    report['checks']['quality']=await job(await call('accurig_validate_rig'));save()
                    assert report['checks']['quality']['verdict']=='passed',report['checks']['quality']
                    target=CONTROL/'outputs'/('Pete-Bobi-'+str(time.time_ns())+'.fbx')
                    export=await session.call_tool('accurig_export_fbx',{'output_path':str(target),'target':'blender','mode':'MeshOnly'})
                    if export.isError:
                        error=export.structuredContent
                        if 'AUTH_REQUIRED' in json.dumps(error):report['checks']['export_auth_required']=error
                        else:raise AssertionError(error)
                    else:
                        attempt=export.structuredContent['result']
                        try:report['checks']['export']=await job(attempt)
                        except AssertionError as error:
                            if 'AUTH_REQUIRED' in str(error):report['checks']['export_auth_required']=str(error)
                            else:raise
                    report['passed']=True;save()
                finally:
                    state=await call('accurig_status')
                    report['checks']['status_after']=state
                    if not state.get('active_job') and not state.get('uncertain'):
                        report['checks']['closed']=await call('accurig_close_session');report['checks']['final_status']=await call('accurig_status')
                    save()
    print(json.dumps({'passed':report.get('passed',False),'checks':list(report['checks']),'export_auth_required':'export_auth_required' in report['checks']},indent=2),flush=True)
try:asyncio.run(main())
except BaseException as e:
    report['passed']=False;report['error']=str(e);report['traceback']=''.join(traceback.format_exception(e));save();print(report['traceback'],flush=True);sys.exit(1)
