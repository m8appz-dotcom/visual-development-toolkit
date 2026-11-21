"""Exercise the real stdio MCP gateway without Docker or native engines."""
import asyncio
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zipfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / 'plugins/game-modding-toolkit/server/lab_mcp.py'

def content(result):
    if result.isError:
        raise RuntimeError(next((c.text for c in result.content if c.type == 'text'), 'MCP tool error'))
    if result.structuredContent is not None:
        return result.structuredContent
    return json.loads(next(c.text for c in result.content if c.type == 'text'))

class PortableGatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='toolkit-portable-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.lab = self.root / 'lab'
    @contextlib.asynccontextmanager
    async def connected(self):
        env = {**os.environ, 'MODDING_LAB_ROOT': str(self.lab), 'MODDING_LAB_MODE': 'docker'}
        async with contextlib.AsyncExitStack() as stack:
            read, write = await stack.enter_async_context(stdio_client(StdioServerParameters(command=sys.executable, args=[str(SERVER)], env=env)))
            self.session = await stack.enter_async_context(ClientSession(read, write))
            await self.session.initialize()
            yield self.session

    async def call(self, tool_name, **args):
        return content(await self.session.call_tool(tool_name, args))

    def test_import_package_and_integrity_through_real_mcp(self):
        async def scenario():
            async with self.connected():
                await self.import_package_and_integrity()
        asyncio.run(scenario())

    async def import_package_and_integrity(self):
        tools = await self.session.list_tools()
        self.assertIn('package_project', [t.name for t in tools.tools])
        await self.call('create_project', name='portfolio-example')
        original = self.root / 'authored.html'
        original.write_text('<!doctype html><title>Authored example</title><h1>MCP fixture</h1>', encoding='utf-8')
        digest = hashlib.sha256(original.read_bytes()).hexdigest()
        imported = await self.call('import_target', project_name='portfolio-example', source_path=str(original))
        self.assertEqual(imported['files'], 1)
        output = self.lab / 'projects/portfolio-example/output/source'
        output.mkdir()
        shutil.copy2(original, output / 'index.html')
        packaged = await self.call('package_project', project_name='portfolio-example', output_folder='output/source')
        self.assertTrue(packaged['ok'])
        with zipfile.ZipFile(packaged['archive']) as archive:
            self.assertEqual(archive.namelist(), ['index.html'])
            self.assertEqual(hashlib.sha256(archive.read('index.html')).hexdigest(), digest)
        self.assertTrue((await self.call('verify_originals', project_name='portfolio-example'))['ok'])
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(), digest)

    def test_escape_and_output_root_are_rejected(self):
        async def scenario():
            async with self.connected():
                await self.escape_and_output_root()
        asyncio.run(scenario())

    async def escape_and_output_root(self):
        await self.call('create_project', name='bounded-example')
        for folder in ('output', '../outside', 'output/../../outside'):
            with self.subTest(folder=folder):
                result = await self.session.call_tool('package_project', {'project_name':'bounded-example','output_folder':folder})
                self.assertTrue(result.isError)

    def test_invalid_project_and_duplicate_do_not_overwrite(self):
        async def scenario():
            async with self.connected():
                await self.invalid_project_and_duplicate()
        asyncio.run(scenario())

    async def invalid_project_and_duplicate(self):
        self.assertTrue((await self.session.call_tool('create_project', {'name':'../escape'})).isError)
        await self.call('create_project', name='existing-project')
        marker = self.lab / 'projects/existing-project/project.json'
        before = marker.read_bytes()
        self.assertTrue((await self.session.call_tool('create_project', {'name':'existing-project'})).isError)
        self.assertEqual(marker.read_bytes(), before)

if __name__ == '__main__':
    unittest.main()
