"""Verify a second MCP cannot take over the application under test."""
import asyncio,json,pathlib
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client
ROOT=pathlib.Path(__file__).resolve().parents[1]
async def main():
 params=StdioServerParameters(command='D:/visual-development-toolkit/windows/node/node-v24.19.0-win-x64/node.exe',args=[str(ROOT/'src/server.mjs')])
 with (ROOT/'reports/second-client.log').open('a') as log:
  async with stdio_client(params,errlog=log) as streams:
   async with ClientSession(*streams) as client:
    await client.initialize();r=await client.call_tool('accurig_connect',{})
    value=r.structuredContent
    assert r.isError and 'APP_IN_USE' in value['error']['message']
    (ROOT/'reports/in-use-protection.json').write_text(json.dumps(value,indent=2))
    print('PASS: unrelated instance takeover refused')
asyncio.run(main())
