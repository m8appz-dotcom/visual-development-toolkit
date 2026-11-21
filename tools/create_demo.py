"""Run the actual stdio gateway and publish a portable packaging walkthrough."""
from __future__ import annotations
import asyncio
import contextlib
import hashlib
import html
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '<!doctype html><html lang="en"><meta charset="utf-8"><title>Authored source example</title><h1>Source packaged through MCP</h1><p>This authored file is the input and output of the integrity walkthrough.</p></html>\n'

def payload(result):
    if result.isError:
        raise RuntimeError(next(c.text for c in result.content if c.type == 'text'))
    return result.structuredContent if result.structuredContent is not None else json.loads(next(c.text for c in result.content if c.type == 'text'))

async def main():
    target = ROOT / 'docs/examples'
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='toolkit-demo-') as temp:
        work = Path(temp); lab = work / 'lab'; original = work / 'authored.html'
        original.write_text(SOURCE, encoding='utf-8')
        before = hashlib.sha256(original.read_bytes()).hexdigest()
        env = {**os.environ, 'MODDING_LAB_ROOT':str(lab), 'MODDING_LAB_MODE':'docker'}
        operations = []
        async with contextlib.AsyncExitStack() as stack:
            read, write = await stack.enter_async_context(stdio_client(StdioServerParameters(command=sys.executable, args=[str(ROOT/'plugins/game-modding-toolkit/server/lab_mcp.py')], env=env)))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            async def call(tool, **arguments):
                data = payload(await session.call_tool(tool, arguments))
                operations.append(tool)
                return data
            await call('create_project', name='portfolio-demo')
            imported = await call('import_target', project_name='portfolio-demo', source_path=str(original))
            folder = lab / 'projects/portfolio-demo/output/source'
            folder.mkdir()
            shutil.copy2(original, folder / 'index.html')
            packaged = await call('package_project', project_name='portfolio-demo', output_folder='output/source')
            integrity = await call('verify_originals', project_name='portfolio-demo')
            rejected = await session.call_tool('package_project', {'project_name':'portfolio-demo','output_folder':'../outside'})
            operations.append('reject_outside_project')
            with zipfile.ZipFile(packaged['archive']) as archive:
                names = archive.namelist()
                content = archive.read('index.html')
            assert imported['files']==1 and packaged['files']==1 and names==['index.html']
            assert integrity['ok'] and rejected.isError
            assert hashlib.sha256(content).hexdigest()==before==hashlib.sha256(original.read_bytes()).hexdigest()
        example = target / 'packaged-project'; example.mkdir(exist_ok=True)
        (example/'index.html').write_bytes(content)
        evidence = {'transport':'actual_mcp_stdio', 'operations':operations, 'filesPackaged':1, 'originalUnchanged':True, 'archiveContentMatchesOriginal':True, 'outsidePathRejected':True, 'sourceSha256':before, 'externalEnginesStarted':False, 'paidProviderCalls':0}
        (target/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
        rows=''.join('<tr><td>'+html.escape(name)+'</td><td>Verified</td></tr>' for name in operations)
        report='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Portable MCP walkthrough</title><style>body{margin:0;background:#f5f7fa;color:#172033;font:17px/1.6 system-ui,sans-serif}main{max-width:960px;margin:52px auto;padding:32px}h1{font-size:42px;line-height:1.1;letter-spacing:-1px}p{max-width:780px}.panel{background:white;border:1px solid #dce2e9;border-radius:12px;padding:24px;margin:26px 0}.stats{display:flex;gap:48px;flex-wrap:wrap}b{display:block;font-size:30px}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:14px;border-bottom:1px solid #e4e8ef}.muted{color:#526174}</style><main><p class="muted">Visual Development Toolkit · Actual stdio MCP run</p><h1>From authored source to a verified package</h1><p>The gateway created an isolated project, imported one authored file, packaged its output, verified the original, and rejected a path outside the project.</p><section class="panel stats"><div><b>1</b>source file packaged</div><div><b>Verified</b>original preserved</div><div><b>Rejected</b>outside path</div></section><section class="panel"><h2>Observed tool calls</h2><table><thead><tr><th>Operation</th><th>Result</th></tr></thead><tbody>'''+rows+'''</tbody></table></section><p class="muted">This portable example runs the actual MCP gateway. It does not start Docker, Ghidra, REA, native applications, or paid generation providers.</p></main></html>'''
        (target/'walkthrough.html').write_text(report,encoding='utf-8')
    print(json.dumps(evidence))

if __name__ == '__main__':
    asyncio.run(main())
