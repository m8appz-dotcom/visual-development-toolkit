# Native Windows runtime

Version 1.2.0 supports on-demand native Windows engines alongside Docker mode. Choose an isolated runtime root; existing installations are not automatically migrated.

The native launcher configures local Ghidra 12.1.4, a full JDK 21, a private Node 24 for REA 4.1.0, ILSpyCmd 11.1 and the AssetStudio adapter compiled for the included .NET 10 runtime. It hides child windows, uses below-normal priority and limits Java to 2 GiB. It starts engines only when an MCP connection or analysis request needs them. Visible GUI/game interaction requires separate authorization; keep routine checks in the background.

REA's Windows Ghidra provider is its experimental read-only x64 native PE P0 boundary, with 25 supported native inventory/function operations. That provider does not offer the same target-format and mutation support as Linux. REA's separate JavaScript/managed-artifact tools and the direct Ghidra MCP remain available according to their own capabilities. Report unsupported operations rather than implying full cross-platform parity.

The native installation is prepared from checksum-verified official archives and wheels built from the pinned upstream source. `install_native.py --payload <archive-folder>` expects `payload-lock.json`, the source plugin and the prepared wheels in the runtime root. A deployer must first prepare/transfer that payload; this command is not an independent public internet downloader.

For a fresh clone on Windows, install `uv` from https://docs.astral.sh/uv/getting-started/installation/ and run `python setup_native_runtime.py`. This prepares a private Python 3.12.10 without adding registry entries or executable shortcuts, downloads the pinned Windows packages, builds the pure Python wheels and calls the native installer. The private Python is needed because PyGhidra 3.1 pins JPype 1.5.2. No existing Python or Node installation is upgraded. The fresh-clone downloader itself has not been run end to end in this delivery; the deployed payload and engines are recorded separately in the host-specific history.

The actual runtime is recorded in `native-runtime.json`; `component_status` reports it. The installed `mcp.json` points all three connections at `server/native_mcp.py` with the runtime root. Source project paths stay on Windows. The gateway's historical `platform=docker` argument routes to native tools in this mode for backward compatibility. It creates no TCP service, scheduled task, SSH authorization or Docker instance.

`test_native_plugin.py` exercises the installed manifest using authored fixtures: MCP discovery, .NET decompilation, Unity text/DXT1 export, sprite processing, JavaScript analysis, Ghidra PE analysis, REA native P0, ZIP packaging and imported-file integrity. See each host's `reports/native-plugin-test.json` for actual results; this document does not itself establish a passing test.

Remove the plugin with `codex plugin remove game-modding-toolkit@modding-lab`. Preserve the runtime source, imported projects and reports for recovery. Update/reinstall through the owning source; never edit the installed cache directly.

Host-specific cache and installation records are preserved in [history](history/README.md).
