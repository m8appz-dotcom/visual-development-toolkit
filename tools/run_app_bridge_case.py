"""Exercise existing application engines through real MCP; never modify the runtime."""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import zipfile

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


def unwrap(response):
    if response.isError:
        raise RuntimeError(next((c.text for c in response.content if c.type == "text"), "MCP operation failed"))
    return response.structuredContent if response.structuredContent is not None else json.loads(
        next(c.text for c in response.content if c.type == "text")
    )


async def run(runtime: Path, work: Path):
    runtime = runtime.resolve(strict=True)
    work = work.resolve()
    if work == runtime or work.is_relative_to(runtime):
        raise ValueError("Use a dedicated output directory outside the installed runtime")
    work.mkdir(parents=True, exist_ok=True)
    receipt = work / "private-run.json"
    if receipt.exists():
        raise ValueError("This run already exists; inspect its receipt instead of repeating it")
    env = {**os.environ, "MODDING_LAB_ROOT": str(runtime), "MODDING_LAB_MODE": "native",
           "TOOLKIT_DEMO_PROJECTS": str(work / "projects"), "PYTHONDONTWRITEBYTECODE": "1"}
    operations = []
    private = {"runtime": str(runtime), "operations": operations}
    public = {"version": 1, "case": "AssetStudio application to MCP", "transport": "actual MCP stdio",
              "fixture": "Repository-authored Unity TextAsset", "nativeApplication": "AssetStudio via AssetBridge",
              "paidCalls": 0, "desktopInput": False, "checks": []}

    def save():
        receipt.write_text(json.dumps(private, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    async with contextlib.AsyncExitStack() as stack:
        read, write = await stack.enter_async_context(stdio_client(StdioServerParameters(
            command=sys.executable, args=["-B", str(ROOT / "tools/isolated_app_gateway.py")], env=env,
        )))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        tools = await session.list_tools()
        public["toolNames"] = [t.name for t in tools.tools]
        (work / "tool-schemas.json").write_text(
            json.dumps([{"name": t.name, "description": t.description, "inputSchema": t.inputSchema} for t in tools.tools], indent=2) + "\n",
            encoding="utf-8",
        )

        async def call(tool_name, **kwargs):
            print("Running " + tool_name, flush=True)
            try:
                result = unwrap(await session.call_tool(tool_name, kwargs))
                operations.append({"tool": tool_name, "result": result})
                save()
                return result
            except Exception as exc:
                operations.append({"tool": tool_name, "error": str(exc)})
                save()
                raise

        project = "assetstudio-app-bridge"
        await call("create_project", name=project)
        await call("import_target", project_name=project, source_path=str(ROOT / "fixtures/unity/lab.assets"))
        inventory = await call("inspect_unity_assets", project_name=project, input_path="input/lab.assets")
        if not inventory.get("ok"):
            raise RuntimeError("Native Unity inventory did not succeed; see private receipt")
        items = inventory.get("data", {}).get("items", [])
        if not any(i.get("type") == "TextAsset" and i.get("name") == "LabReadme" for i in items):
            raise RuntimeError("The native engine did not identify the expected TextAsset")
        public["checks"].append({"name": "Native Unity inventory", "status": "passed", "observed": "LabReadme · TextAsset"})

        exported = await call("export_unity_assets", project_name=project, input_path="input/lab.assets", asset_type="TextAsset")
        if not exported.get("ok"):
            raise RuntimeError("Native Unity export failed; see private receipt")
        outputs = list(Path(exported["output_path"]).glob("*.txt"))
        expected = (ROOT / "fixtures/unity/expected.txt").read_bytes()
        if len(outputs) != 1 or outputs[0].read_bytes() != expected:
            raise RuntimeError("Extracted text differs from the authored expected result")
        public["checks"].append({"name": "Native TextAsset export", "status": "passed", "bytes": len(expected),
                                 "sha256": hashlib.sha256(expected).hexdigest(), "matchesOriginal": True})
        (work / "extracted-text.txt").write_bytes(expected)

        # Inspect the authored adapter with ILSpy; do not decompile or redistribute an external application.
        for filename in ("AssetBridge.dll", "AssetStudio.dll", "AssetStudioUtility.dll", "SixLabors.ImageSharp.dll"):
            await call("import_target", project_name=project, source_path=str(runtime / "windows/AssetBridge/publish" / filename))
        decompiled = await call("decompile_dotnet", project_name=project, input_file="input/AssetBridge.dll", type_name="Program")
        source_files = list(Path(decompiled["output_path"]).rglob("*.cs"))
        source_text = "\n".join(p.read_text(encoding="utf-8-sig") for p in source_files)
        decompile_ok = bool(decompiled.get("ok") and source_files and "AssetsManager" in source_text)
        public["checks"].append({"name": "ILSpy adapter inspection", "status": "passed" if decompile_ok else "failed",
                                 "scope": "Authored AssetBridge adapter; external application code is not published"})

        intact = await call("verify_originals", project_name=project)
        if not intact.get("ok"):
            raise RuntimeError("An imported original changed")
        public["checks"].append({"name": "Original integrity", "status": "passed"})
        public["operations"] = [o["tool"] for o in operations]
        public["limitations"] = ["A native TextAsset fixture validates this adapter path, not every AssetStudio export format.",
                                  "No real holder passkey enrollment or recovery is asserted by this machine-only MCP run."]
        clean = work / "projects" / project / "output/verified-example"
        clean.mkdir()
        (clean / "extracted-text.txt").write_bytes(expected)
        (clean / "bridge-evidence.json").write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8", newline="\n")
        package = await call("package_project", project_name=project, output_folder="output/verified-example")
        with zipfile.ZipFile(package["archive"]) as archive:
            if archive.read("extracted-text.txt") != expected:
                raise RuntimeError("The packaged extraction differs")
        public["checks"].append({"name": "Package read-back", "status": "passed", "originalBytesPreserved": True})
        (work / "bridge-evidence.json").write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8", newline="\n")
        shutil.copyfile(package["archive"], work / "verified-bridge-example.zip")
        print(json.dumps({"checks": public["checks"], "tools": len(tools.tools)}, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(run(args.runtime_root, args.output))
