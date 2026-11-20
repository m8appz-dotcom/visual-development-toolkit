"""Read-only smoke using the packaged plugin's actual MCP definition."""
import asyncio, json, pathlib, tomllib, sys, tempfile, hashlib
from datetime import timedelta
import yaml
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN = pathlib.Path(sys.argv[1] if len(sys.argv)>1 else 'C:/Users/kenny/.codex/plugins/cache/modding-lab/accurig-control/0.4.0')

async def main():
    manifest = json.loads((PLUGIN/'.codex-plugin/plugin.json').read_text(encoding='utf-8'))
    skill = PLUGIN / manifest['skills'] / 'accurig-control'
    metadata = yaml.safe_load((skill/'agents/openai.yaml').read_text(encoding='utf-8'))
    assert metadata['policy']['allow_implicit_invocation'] is True
    assert metadata['dependencies']['tools'][0]['value'] == 'accurig-control'
    text = (skill/'SKILL.md').read_text(encoding='utf-8')
    frontmatter = yaml.safe_load(text.split('---',2)[1])
    assert frontmatter['name'] == 'accurig-control'
    config = tomllib.loads(pathlib.Path('C:/Users/kenny/.codex/config.toml').read_text(encoding='utf-8-sig'))
    assert manifest['name'] == 'accurig-control'
    assert manifest['version'] == '0.4.0'
    assert config['plugins']['accurig-control@modding-lab']['enabled'] is True
    assert 'accurig-control' not in config.get('mcp_servers',{})
    assert not pathlib.Path('C:/Users/kenny/.codex/skills/accurig-control').exists()
    for vdt in [pathlib.Path('D:/visual-development-toolkit/plugins/game-modding-toolkit')]:
        assert 'accurig-control' not in json.loads((vdt/'mcp.json').read_text())['mcpServers']
        assert not (vdt/'skills/accurig-control').exists()
    definition = json.loads((PLUGIN/manifest['mcpServers']).read_text())['mcpServers']['accurig-control']
    with (ROOT/'reports/plugin-contract-stderr.log').open('w') as errlog:
        async with stdio_client(StdioServerParameters(command=definition['command'],args=definition['args']),errlog=errlog) as streams:
            async with ClientSession(*streams,read_timeout_seconds=timedelta(seconds=30)) as session:
                initialized = await session.initialize()
                tool_list = await session.list_tools()
                names = {t.name for t in tool_list.tools}
                assert initialized.serverInfo.version == '0.4.0'
                assert len(names) == 24 and {'accurig_status','accurig_build_skin','accurig_export_fbx','accurig_review_joints','accurig_record_visual_review','accurig_delete_generation','accurig_prepare_import_workspace','accurig_set_base_gate'} <= names
                export_tool=next(t for t in tool_list.tools if t.name=='accurig_export_fbx')
                assert 'allow_needs_review' not in export_tool.inputSchema['properties']
                assert next(t for t in tool_list.tools if t.name=='accurig_delete_generation').annotations.destructiveHint is True
                status = await session.call_tool('accurig_status',{})
                assert not status.isError and status.structuredContent['ok']
                assert status.structuredContent['result']['active_job'] is None
                inspect = await session.call_tool('accurig_inspect_model',{'input_path':'D:/Applications/Reallusion/AccuRIG/Sample Character/Pete.obj'})
                assert not inspect.isError and inspect.structuredContent['result']['verdict'] == 'passed'
                # Synthetic rejected receipt exercises the new tool over real stdio;
                # it is explicitly not a character-quality assessment.
                with tempfile.TemporaryDirectory(prefix='base-gate-contract-') as td:
                    folder=pathlib.Path(td);source=folder/'fixture.obj';source.write_text('v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n')
                    model={'path':str(source.resolve()),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
                    case=folder/'case.json';receipt=folder/'receipt.json'
                    r={'schema':'base-gate/1','case':str(case),'model':model,'verdict':'discard','files':{},'warnings':[]}
                    case.write_text(json.dumps({'source':model,'references':{},'reviews':{model['sha256']:r}}))
                    receipt.write_text(json.dumps(r))
                    blocked=await session.call_tool('accurig_set_base_gate',{'receipt_path':str(receipt)})
                    assert blocked.isError and 'BASE_MODEL_REJECTED' in blocked.structuredContent['error']['message']
                    after=await session.call_tool('accurig_status',{})
                    assert after.structuredContent['result']['base_gate_receipt'] is None
                report = {'passed':True,'plugin':manifest['name'],'version':manifest['version'],
                          'server':initialized.serverInfo.model_dump(mode='json'),'tools':sorted(names),
                          'skill':frontmatter,'implicit_invocation':True,'global_duplicates':False,
                          'status':status.structuredContent,'inspect':inspect.structuredContent,'rejected_base_blocked':blocked.structuredContent,
                          'scope':'Real packaged stdio MCP and skill metadata; no rig generation or agent selection trial'}
                (ROOT/'reports/plugin-contract.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
                print('Plugin0.4 skill and packaged MCP:24 tools, strict export schema, destructive annotation, status and Pete inspection passed')

asyncio.run(main())
