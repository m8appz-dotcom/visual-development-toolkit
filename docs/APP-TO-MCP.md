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

The native case runner holds machine paths and full traces only in its private output. The builder selects public fixture evidence and adapter source; it excludes installed binaries and private configuration. The ZIP is a focused source package: manifest, MCP connections, authored server adapters and the app-to-mcp skill. Configure the private copy as shown below. Codex does not forward arbitrary caller variables into the plugin automatically. The bootstrap does not install engines or silently start a stopped Docker service. The legacy plugin ID stays stable for compatibility.

Use the existing setup helper on a private source or installed copy; the source-only ZIP includes the same helper as `configure_runtime.py`. Keep its machine-specific output private.

```sh
python configure_runtime.py --plugin-root PATH_TO_PRIVATE_PLUGIN --runtime-root PATH_TO_EXISTING_RUNTIME --python PATH_TO_EXISTING_PYTHON --mode portable
```

For native adapters choose `--mode native` and an existing native runtime. The helper uses a bare executable name and a private interpreter PATH, as required by the portable plugin format. `--dry-run` inspects the change without writing it. Do not overwrite another installed plugin or its configuration to test this source package. This repository's public snapshot and a locally evolved installation can have different versions and purposes.

## What the public demo does

**View recorded MCP run** opens the saved native result. It does not execute a visitor's desktop app. File inspection and SHA-256 checks read the actual included files. **Download Codex plugin** downloads the source package; **Export selection** packages the selected artifact bytes in the browser. These browser actions do not impersonate the native MCP run.

The local workspace retains its existing passkey-protected copies and live engine adapter. Its holder registration, login and recovery acceptance remain separate from machine-only MCP checks; this delivery claims no new human authentication acceptance.

## Coverage

The native fixture validates the TextAsset path, not every AssetStudio format or GUI feature. The runtime scope artifact distinguishes actual operations from connection/version checks and unverified engines. REA's managed identity query succeeded; later member-level requests failed MCP transport and are not presented as passed. No paid generation, desktop input, third-party sample-image transformation or Spark service change occurred.

## Fresh Codex client validation

On 23 November 2026, an isolated Codex CLI 0.163.0 home installed plugin1.2.2 from a local marketplace. Codex discovered the app-to-mcp skill and16 MCP tools. Through the actual Codex client, create_project, import_target, verify_originals and package_project completed; independent ZIP read-back matched the owned fixture and an outside-project path was rejected. No model inference or native engine startup was required. This validates the portable gateway, not all optional native engines or a human passkey ceremony.

The test caught and fixed a stale canonical root manifest and an absolute-executable setup incompatibility. Canonical and compatibility identity now match; regression tests cover both and the downloadable package. See tools/check_codex_client.py to repeat the installed-client check with an isolated home and explicitly configured runtime.
