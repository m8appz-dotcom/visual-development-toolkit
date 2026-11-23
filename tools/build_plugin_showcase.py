"""Build the approved gallery from actual MCP/plugin source and a selected native run."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/game-modding-toolkit"


def source_bytes(path: Path) -> bytes:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n").encode("utf-8")


def plugin_package(destination: Path) -> list[str]:
    """Source-only focused package; no installed engines or third-party sample assets."""
    files = [".codex-plugin/plugin.json", "mcp.json", "server/bootstrap_mcp.py",
             "server/lab_mcp.py", "server/native_mcp.py", "server/docker_mcp.py",
             "skills/app-to-mcp/SKILL.md", "skills/app-to-mcp/agents/openai.yaml"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            info = zipfile.ZipInfo(name, date_time=(2026, 11, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, source_bytes(PLUGIN / name))
        setup = zipfile.ZipInfo("SETUP.md", date_time=(2026, 11, 23, 0, 0, 0))
        setup.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(setup, "# Toolkit application bridge\n\nThis source-only Codex plugin packages the gateway, MCP connections and the app-to-mcp skill. It requires an existing configured Toolkit runtime. Set MODDING_LAB_ROOT privately before invoking it. Native mode uses that runtime's interpreter; no engines are installed or started automatically. For portable gateway testing, set MODDING_LAB_MODE=portable and install the repository's pinned MCP development dependency in your interpreter. The legacy plugin name is retained for compatibility.\n")
    return files


def build(run: Path):
    run = run.resolve(strict=True)
    evidence = json.loads((run / "bridge-evidence.json").read_text(encoding="utf-8"))
    if not evidence.get("checks") or any(c["status"] != "passed" for c in evidence["checks"]):
        raise ValueError("Choose a completed native run with no failed checks")
    # A private runtime path or trace is never a public gallery input.
    public = ROOT / "demo/public"
    target = public / "assets/app-bridge"
    target.mkdir(parents=True, exist_ok=True)
    manifest = []

    def add(name: str, label: str, category: str, data: bytes, kind="document", mime="text/plain", preview=None):
        (target / name).write_bytes(data)
        item = {"id": len(manifest), "group": category, "category": category,
                "project": "Application → MCP → Codex plugin", "path": "app-bridge/" + name,
                "name": name, "label": label, "type": kind, "mime": mime,
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
        if preview is not None:
            item["preview"] = preview
        manifest.append(item)

    def data(name, label, category, value):
        add(name, label, category, (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode("utf-8"), "data", "application/json")

    data("capability-map.json", "Application capabilities", "app", {
        "application": "AssetStudio", "adapter": "Authored Windows AssetBridge",
        "inspect_unity_assets": {"nativeEntryPoint": "AssetsManager.LoadFiles / LoadFolder", "observed": "LabReadme · TextAsset"},
        "export_unity_assets": {"nativeEntryPoint": "TextAsset.m_Script", "observed": "Extracted text matches the authored fixture"},
        "coverage": "TextAsset fixture path only; other export types were not exercised by this run",
    })
    add("AssetBridge.cs", "Native application adapter", "app", source_bytes(ROOT / "windows/AssetBridge/Program.cs"))
    schemas = json.loads((run / "tool-schemas.json").read_text(encoding="utf-8"))
    data("tool-contracts.json", "MCP tool contracts", "mcp", schemas)
    add("lab_mcp.py", "MCP server implementation", "mcp", source_bytes(PLUGIN / "server/lab_mcp.py"))
    add("mcp.json", "Bundled MCP connections", "mcp", source_bytes(PLUGIN / "mcp.json"), "data", "application/json")
    add("plugin.json", "Codex plugin manifest", "plugin", source_bytes(PLUGIN / ".codex-plugin/plugin.json"), "data", "application/json")
    add("SKILL.md", "Reusable app-to-MCP workflow", "skill", source_bytes(PLUGIN / "skills/app-to-mcp/SKILL.md"))
    add("openai.yaml", "Skill invocation metadata", "skill", source_bytes(PLUGIN / "skills/app-to-mcp/agents/openai.yaml"))
    data("bridge-evidence.json", "Recorded native MCP run", "evidence", evidence)
    add("lab.assets", "Original Unity input fixture", "evidence", (ROOT / "fixtures/unity/lab.assets").read_bytes(), "binary", "application/octet-stream",
        ["Unity TextAsset fixture", "Object: LabReadme", "Open the capability map for the native inventory."])
    add("extracted-text.txt", "Native extraction result", "evidence", (run / "extracted-text.txt").read_bytes())
    package = target / "toolkit-codex-plugin.zip"
    files = plugin_package(package)
    add(package.name, "Downloadable Codex plugin", "plugin", package.read_bytes(), "package", "application/zip", files[:7])
    data("runtime-checks.json", "Integration verification scope", "evidence", {
        "AssetStudio / AssetBridge": "Native fixture inspection and TextAsset export passed through MCP",
        "ILSpy": "Authored adapter decompilation passed through MCP",
        "REA": "Managed assembly identity inspection completed; later member calls failed MCP transport and remain unverified",
        "Ghidra": "MCP program-session query responded; no native target analysis claimed by this case",
        "universal-modder": "CLI help responds; generation and application modification not exercised here",
        "Blender": "Installed binary reports version 5.2.2 LTS; no scene or render operation claimed here",
        "fal / ComfyUI": "Generation not exercised; no paid calls were made",
        "Codex package": "Source manifest, MCP configuration and skill included; fresh-client installation acceptance is separate",
    })
    (public / "assets/collection.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return manifest


def static_copy(destination: Path):
    public = ROOT / "demo/public"
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("app.js", "base.css", "products.css", "ui.css", "core.js", "engine-client.js",
                 "portable-package.js", "file-preview.js", "zip.js"):
        (destination / name).write_bytes(source_bytes(public / name))
    index = (public / "index.html").read_text(encoding="utf-8").replace(
        '<html lang="en">', '<html lang="en" data-packaging-mode="portable">', 1)
    (destination / "index.html").write_text(index, encoding="utf-8", newline="\n")
    (destination / "assets/app-bridge").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(public / "assets/collection.json", destination / "assets/collection.json")
    for item in json.loads((public / "assets/collection.json").read_text(encoding="utf-8")):
        shutil.copyfile(public / "assets" / item["path"], destination / "assets" / item["path"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--static-output", type=Path)
    args = parser.parse_args()
    manifest = build(args.run)
    if args.static_output:
        static_copy(args.static_output)
    print(json.dumps({"artifacts": len(manifest), "application": "AssetStudio", "package": "source-only Codex plugin"}))
