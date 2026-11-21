# Visual Development Toolkit — X and Titan

Verified installation on **2026-10-09**. Both hosts run plugin **1.2.0** with native Windows engines, on demand.

| Host | Runtime | MCP tools discovered | Checks passed | Codex |
|---|---|---:|---:|---|
| X | `D:\visual-development-toolkit` | 353 | 24 | Installed and enabled |
| TITAN-WIN | `C:\visual-development-toolkit` | 353 | 24 | Installed and enabled |

The 24 checks on each machine connect through the installed `mcp.json`: three MCP discoveries; actual component versions; isolated project/imports; .NET C# recovery with ILSpy; exact Unity TextAsset bytes and DXT1 PNG conversion; sprite processing; REA JavaScript analysis; Ghidra Windows PE import/summary/close; REA doctor and Windows native P0 open/overview/close; ZIP packaging; original-file hashes and traversal rejection. All test inputs were authored fixtures, including the locally built .NET apphost. No commercial game/app compatibility claim is made.

The Codex app-server probe confirms installation and enabled state without creating a chat/model turn. Processes were checked after the test clients closed: no toolkit Java, Python, Node or .NET process remained.

X uses D: for the runtime and a verified junction for only the `modding-lab` Codex cache. Titan uses C:. Python 3.12 and Node 24 are private dependencies; existing interpreters were not upgraded. Java runs below normal priority with a 2 GiB heap limit; child windows remain hidden. No Docker, TCP service, scheduled task or SSH permission was created for these installations.

REA's Windows native Ghidra provider remains its experimental read-only x64 PE P0 boundary. Separate JavaScript/managed tools and direct Ghidra MCP follow their own capabilities. Fal requires a key and authorized payment; Blender is needed for its render workflow. Neither paid generation nor GUI FBX export was tested.

Open a new Codex chat to load Visual Development Toolkit. See NATIVE-WINDOWS.md for setup/recovery. Bobi's existing Docker deployment and its 1.1.0 evidence remain separate; it was not restarted or migrated during this installation. The fresh-clone native downloader is source/syntax checked, while these runtime tests used the deployed verified payload.

Local full evidence: D:/modding-lab/reports/native-clients/. Per-machine full evidence: <runtime>/reports/native-plugin-test.json and native-codex-host-plugin.json. Keep project data, dependency archives and the owning source for rollback. Remove only the plugin connection with `codex plugin remove game-modding-toolkit@modding-lab`; do not remove X's cache target while its junction is in use.
