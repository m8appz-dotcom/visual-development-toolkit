# From an application capability to a Codex plugin

Toolkit's purpose is to help build MCP integrations that use existing applications well, then distribute those tools with reusable skills in Codex plugins. The application, adapter, MCP server and skill each have a separate job.

[Open the integration showcase](https://kennethyepez.com/work/visual-development-toolkit/index.html)

## A recorded native example

The example starts with an authored Unity TextAsset fixture. The real MCP gateway invokes AssetStudio through the authored Windows AssetBridge adapter to identify the resource and extract its text. An independent byte comparison checks the extraction against the known original. ILSpy inspects the authored adapter's compiled assembly; no external application's recovered code is published. The run checks imported originals and reads the extracted result back from a package.

The public gallery includes the capability map, adapter source, actual MCP tool contracts, server implementation, plugin manifest, skill, selected fixture and recorded results. It makes the integration inspectable without exposing a private native application service.

| Layer | What this case demonstrates |
| --- | --- |
| Application | AssetStudio's real Unity resource reader |
| Authored adapter | AssetBridge maps native library calls to structured results |
| MCP | Typed tool contracts expose inspection, extraction and supporting operations |
| Codex plugin | A manifest bundles server connections and an app-to-mcp skill |
| Verification | Native extraction, adapter decompilation, original preservation and package read-back |

## Reproduce with an existing runtime

Use the runtime's Python environment with its maintained MCP dependency. Choose a new output directory outside the installed runtime. These commands do not install engines, start Docker or alter an active application project:

```sh
python tools/run_app_bridge_case.py --runtime-root PATH_TO_EXISTING_RUNTIME --output PATH_TO_NEW_RUN
python tools/build_plugin_showcase.py --run PATH_TO_NEW_RUN
python tools/check_plugin_package.py --package demo/public/assets/app-bridge/toolkit-codex-plugin.zip --work PATH_TO_NEW_PACKAGE_CHECK
```

The native case runner holds machine paths and full traces only in its private output. The builder selects public fixture evidence and adapter source; it excludes installed binaries and private configuration. The ZIP is a focused source package: manifest, MCP connections, authored server adapters and the app-to-mcp skill. Set `MODDING_LAB_ROOT` privately to an existing runtime before invoking its servers. The bootstrap does not install engines or silently start a stopped Docker service. The legacy plugin ID stays stable for compatibility.

The existing `configure_plugin.py --runtime-root ... --dry-run` can inspect local registration changes. Do not overwrite another installed plugin or its configuration to test this source package. This repository's public snapshot and a locally evolved installation can have different versions and purposes.

## What the public demo does

**View recorded MCP run** opens the saved native result. It does not execute a visitor's desktop app. File inspection and SHA-256 checks read the actual included files. **Download Codex plugin** downloads the source package; **Export selection** packages the selected artifact bytes in the browser. These browser actions do not impersonate the native MCP run.

The local workspace retains its existing passkey-protected copies and live engine adapter. Its holder registration, login and recovery acceptance remain separate from machine-only MCP checks; this delivery claims no new human authentication acceptance.

## Coverage

The native fixture validates the TextAsset path, not every AssetStudio format or GUI feature. The runtime scope artifact distinguishes actual operations from connection/version checks and unverified engines. REA's managed identity query succeeded; later member-level requests failed MCP transport and are not presented as passed. No paid generation, desktop input, third-party sample-image transformation or Spark service change occurred.
