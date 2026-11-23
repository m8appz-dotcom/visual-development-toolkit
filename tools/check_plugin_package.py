"""Verify a source plugin ZIP and discover/call its MCP server in an isolated workspace."""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def unwrap(result):
    if result.isError:
        raise RuntimeError("Packaged MCP operation failed")
    return result.structuredContent if result.structuredContent is not None else json.loads(next(c.text for c in result.content if c.type == "text"))


async def check(package: Path, work: Path):
    work = work.resolve()
    if work.exists():
        raise ValueError("Choose a new isolated workspace or inspect the previous receipt")
    work.mkdir(parents=True)
    plugin = work / "plugin"
    with zipfile.ZipFile(package) as archive:
        for item in archive.infolist():
            destination = (plugin / item.filename).resolve()
            if not destination.is_relative_to(plugin.resolve()) or item.is_dir() or ((item.external_attr >> 16) & 0o170000) == 0o120000:
                raise ValueError("Unexpected archive member")
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(archive.read(item))
    manifest = json.loads((plugin / ".codex-plugin/plugin.json").read_text())
    for key in ("skills", "mcpServers"):
        destination = (plugin / manifest[key]).resolve()
        if not destination.is_relative_to(plugin.resolve()) or not destination.exists():
            raise ValueError("Missing or unsafe plugin reference")
    config = json.loads((plugin / manifest["mcpServers"]).read_text())
    entry = config["mcpServers"]["modding-lab"]
    args = [s.replace("${PLUGIN_ROOT}", str(plugin)) for s in entry["args"]]
    runtime = work / "runtime"
    runtime.mkdir()
    original = work / "owned-fixture.txt"
    content = b"Application capability exposed through a packaged MCP tool.\n"
    original.write_bytes(content)
    env = {**os.environ, "MODDING_LAB_ROOT": str(runtime), "MODDING_LAB_MODE": "portable", "PYTHONDONTWRITEBYTECODE": "1"}
    async with contextlib.AsyncExitStack() as stack:
        read, write = await stack.enter_async_context(stdio_client(StdioServerParameters(command=sys.executable, args=args, env=env)))
        client = await stack.enter_async_context(ClientSession(read, write))
        await client.initialize()
        tools = await client.list_tools()
        names = [t.name for t in tools.tools]
        required = {"inspect_unity_assets", "export_unity_assets", "decompile_dotnet", "create_project", "verify_originals"}
        if not required.issubset(names):
            raise ValueError("The packaged server lost expected application tool contracts")
        unwrap(await client.call_tool("create_project", {"name": "plugin-smoke"}))
        unwrap(await client.call_tool("import_target", {"project_name": "plugin-smoke", "source_path": str(original)}))
        intact = unwrap(await client.call_tool("verify_originals", {"project_name": "plugin-smoke"}))
        if not intact.get("ok") or original.read_bytes() != content:
            raise ValueError("Packaged server did not preserve the original")
        rejected = await client.call_tool("read_project_text", {"project_name": "plugin-smoke", "file_path": "../outside.txt"})
        if not rejected.isError:
            raise ValueError("Packaged server accepted an outside-project path")
    receipt = {"version": 1, "plugin": manifest["name"], "pluginVersion": manifest["version"],
               "manifestReferencesValid": True, "skill": "app-to-mcp", "mcpDiscoveryPassed": True,
               "tools": names, "toolCount": len(names), "fixtureRoundTripPassed": True,
               "outsidePathRejected": True, "inputUnchanged": True,
               "packageSha256": hashlib.sha256(package.read_bytes()).hexdigest(),
               "scope": "Packaged source discovery and portable operation; native app behavior has its own recorded run. Fresh-client installation is not claimed."}
    (work / "plugin-checks.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(check(args.package, args.work))
