"""Real MCP acceptance via the installed plugin entrypoint, preserving the target scene."""
import argparse,asyncio,hashlib,json,os,socket,sys,time
from datetime import timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def unpack(v):
    assert not v.isError,v
    return v.structuredContent or json.loads(next(c.text for c in v.content if c.type=='text'))
async def main():
    p=argparse.ArgumentParser();p.add_argument('--fixture',required=True);p.add_argument('--output',required=True);p.add_argument('--render');a=p.parse_args()
    from mcp import ClientSession,StdioServerParameters
    from mcp.client.stdio import stdio_client
    settings=json.loads((Path(os.environ['LOCALAPPDATA'])/'BlenderAgent/settings.json').read_text(encoding='utf-8'))
    fixture=Path(a.fixture).resolve(strict=True);before=sha(fixture)
    cfg=json.loads((ROOT/'mcp.json').read_text(encoding='utf-8'))['mcpServers']['blender']
    args=[x.replace('${PLUGIN_ROOT}',str(ROOT)) for x in cfg['args']]
    evidence={'host':socket.gethostname(),'plugin_root':str(ROOT),'settings':settings}
    async with stdio_client(StdioServerParameters(command=cfg['command'],args=args,env={**os.environ,**cfg['env']})) as (r,w):
        async with ClientSession(r,w,read_timeout_seconds=timedelta(seconds=240)) as s:
            await s.initialize();tools=await s.list_tools()
            names={t.name for t in tools.tools}
            required={'get_blender_capabilities','get_blender_workflow_docs','execute_blender_code_for_cli',
                      'get_retopology_capabilities','begin_retopology','inspect_retopology','add_retopology_patch',
                      'build_retopology_bone_strip','select_retopology_tool','relax_retopology','undo_retopology',
                      'finish_retopology','transfer_retopology_weights','validate_retopology_poses','save_retopology_result'}
            assert required <= names,('Missing required tools',sorted(required-names))
            evidence['tools']=[t.name for t in tools.tools]
            initial=unpack(await s.call_tool('get_blender_capabilities',{}));assert initial['session']['build']=='9e2066aef7ef'
            evidence['session_before']=initial['session']
            evidence['topics']={}
            for topic in ('overview','guide','quick_api','geometry','nodes','rig_animation','render','export','delivery'):
                evidence['topics'][topic]=unpack(await s.call_tool('get_blender_workflow_docs',{'topic':topic}))
            recipe=evidence['topics']['geometry']['recipe']
            evidence['geometry']=unpack(await s.call_tool('execute_blender_code_for_cli',{'blend_file':str(fixture),'code':recipe['code']}))
            error=await s.call_tool('execute_blender_code_for_cli',{'blend_file':str(fixture),'code':'raise ValueError("plugin_acceptance_expected_error")'})
            assert error.isError;evidence['typed_error_received']=True
            if a.render:
                output=Path(a.render).resolve();assert not output.exists();output.parent.mkdir(parents=True,exist_ok=True)
                code=evidence['topics']['render']['recipe']['configure_optix_code']
                code+='\nimport time\ns=bpy.context.scene\ns.render.resolution_x=1200;s.render.resolution_y=900;s.render.resolution_percentage=100\ns.render.engine="CYCLES";s.cycles.samples=64;s.cycles.seed=27\ns.render.image_settings.file_format="PNG";s.render.filepath='+repr(str(output))+'\nt0=time.monotonic();bpy.ops.render.render(write_still=True)\nresult={"render_seconds":time.monotonic()-t0,"output":s.render.filepath,"devices":[d.name for d in prefs.devices if d.use],"resolution":[s.render.resolution_x,s.render.resolution_y],"samples":s.cycles.samples}\n'
                evidence['render']=unpack(await s.call_tool('execute_blender_code_for_cli',{'blend_file':str(fixture),'code':code}))
                assert output.is_file() and output.stat().st_size>10000
                evidence['render_sha256']=sha(output)
            final=unpack(await s.call_tool('get_blender_capabilities',{}));assert final['session']==initial['session']
    assert sha(fixture)==before
    evidence['source_and_session_preserved']=True;evidence['passed']=True
    Path(a.output).write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    print(json.dumps({'passed':True,'host':evidence['host'],'tools':len(evidence['tools']),'render':evidence.get('render'),'session_preserved':True}))
asyncio.run(main())
