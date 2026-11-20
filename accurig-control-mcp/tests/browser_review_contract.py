"""Real packaged MCP enforcement, using SYNTHETIC evidence only; no native app."""
import asyncio, json, sys
from pathlib import Path
from datetime import timedelta
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,'D:/visual-development-toolkit/kenneth-character-pipeline/tests')
from test_base_gate import BaseGateTests, g

async def main():
 fixture=BaseGateTests();fixture.setUp()
 try:
  receipt=fixture.review();path=receipt['receipt_path']
  cfg=json.loads(Path('C:/Users/kenny/.codex/plugins/cache/modding-lab/accurig-control/0.4.0/mcp.json').read_text())['mcpServers']['accurig-control']
  async with stdio_client(StdioServerParameters(command=cfg['command'],args=cfg['args'])) as streams:
   async with ClientSession(*streams,read_timeout_seconds=timedelta(seconds=30)) as session:
    await session.initialize()
    ok=await session.call_tool('accurig_set_base_gate',{'receipt_path':path})
    assert not ok.isError,ok
    # Preserve the positive receipt while attempting a legacy pass without Gemini.
    legacy=g.read(path);legacy['schema']='base-gate/1';legacy.pop('external_review')
    c=g.read(fixture.case);c['reviews'][g.sha(fixture.source)]=legacy;g.save(fixture.case,c);g.save(path,legacy)
    blocked=await session.call_tool('accurig_set_base_gate',{'receipt_path':path})
    assert blocked.isError and 'GEMINI_BROWSER_REVIEW_REQUIRED' in str(blocked),blocked
    # A closed synthetic mesh with a recorded wrist defect must also be rejected.
    a,b=fixture.reports();v=g.read(b);ext=g.read(v['external_review_path'])
    ext['findings']=[{'location':'wrist','observation':'Synthetic narrow wrist despite closed mesh','status':'open'}]
    g.save(v['external_review_path'],ext)
    rejected=g.review(fixture.case,fixture.source,a,b)
    defect=await session.call_tool('accurig_set_base_gate',{'receipt_path':rejected['receipt_path']})
    assert defect.isError and 'BASE_MODEL_REJECTED' in str(defect),defect
    status=await session.call_tool('accurig_status',{})
    assert not status.isError and status.structuredContent['result']['connected'] is False
    report={'passed':True,'synthetic_only':True,'native_app_started':False,
            'positive_receipt_accepted':True,'legacy_without_external_blocked':True,'wrist_defect_blocked':True}
    (ROOT/'reports/browser-review-contract.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report))
 finally:fixture.tearDown()

asyncio.run(main())
