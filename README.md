# Visual Development Toolkit

Build MCP integrations that expose real application capabilities, then package the tools, server connections and reusable skills as Codex plugins. Use supported application interfaces first; inspect shipped artifacts with REA, Ghidra or ILSpy when the integration needs evidence unavailable from documentation or source.

## Explore the application-to-MCP case

[Open the integration showcase](https://kennethyepez.com/work/visual-development-toolkit/index.html) · [Reproduce the native case](docs/APP-TO-MCP.md) · [Plugin source](plugins/game-modding-toolkit/.codex-plugin/plugin.json) · [App-to-MCP skill](plugins/game-modding-toolkit/skills/app-to-mcp/SKILL.md)

An actual MCP run inspected and extracted an authored Unity TextAsset using AssetStudio/AssetBridge, inspected the authored adapter with ILSpy, preserved its originals and verified the packaged output. The gallery exposes the capability map, source, tool contracts, recorded results and a source-only Codex plugin package. Browser file verification and exports are separate from the recorded native execution.

A fresh isolated Codex client installed version1.2.2, discovered the skill and16 tools, and completed import, verification and packaging with byte-checked ZIP read-back. It also rejected an outside-project path. [Client validation and setup](docs/APP-TO-MCP.md#fresh-codex-client-validation).

The existing visual-asset and application-analysis integrations remain available. Their installation, configuration and coverage differ; a successful fixture does not establish compatibility with every application or every export format.


![Application-to-MCP showcase on desktop](docs/images/workflow-covers-desktop.jpg)

<details><summary>Phone view</summary>

![Application-to-MCP showcase on a phone](docs/images/workflow-covers-mobile.jpg)

</details>

## Why these tools are combined

- **REA, Ghidra and ILSpy** help establish application capabilities and callable boundaries when source or supported interfaces do not answer the integration question.
- **Application libraries and authored adapters** perform the native operation. The AssetStudio/AssetBridge case demonstrates this layer without recreating the application UI.
- **MCP** exposes typed operations to an agent; **Codex plugins** distribute server connections and the skills that guide their use.
- The existing generation, conversion and visual-asset tools remain optional capabilities of the broader toolkit. They are not required to understand or run the focused application-bridge example.

## Project direction and use

[Kenneth Yepez](https://github.com/kennethyepez) directs the requirements, architecture, integration, and validation of this toolkit's integration layer. AI coding agents implement code under his direction. Integrated engines retain their upstream authorship and licenses.

See [use and licensing](LICENSE.md), [contributing](CONTRIBUTING.md), and [security reporting](SECURITY.md).

## Portable gateway quickstart

Review the source and exercise the portable MCP gateway before installing any native engine. Requires Python 3.13; the walkthrough does not start Docker, Ghidra, or REA and does not call a paid provider.

```bash
python -m venv .venv
# Activate .venv using your shell, then:
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python tools/create_demo.py
python -m http.server 8000 --bind 127.0.0.1 --directory docs/examples
```

Open `http://127.0.0.1:8000/walkthrough.html`. The example uses actual MCP stdio requests to create an isolated project, import an authored HTML file, package it, verify byte integrity, and reject a path outside the project. It does not establish native engine compatibility.

## Architecture and review

```mermaid
flowchart LR
  A[Codex plugin and skills] --> B[MCP adapters]
  B --> C[Portable project gateway]
  B --> D[Optional native engines]
  B --> E[Optional Docker engines]
```

Start with [lab_mcp.py](plugins/game-modding-toolkit/server/lab_mcp.py), [native_mcp.py](plugins/game-modding-toolkit/server/native_mcp.py), and the [portable integration tests](tests/test_portable_gateway.py). The [plugin manifest](plugins/game-modding-toolkit/.codex-plugin/plugin.json) and [marketplace](.agents/plugins/marketplace.json) preserve the internal package ID `game-modding-toolkit@modding-lab` for compatibility.

## Optional engines

Choose the [Docker setup guide](docs/INSTALL-WINDOWS.md) or [native Windows guide](docs/NATIVE-WINDOWS.md) only when the target needs those engines. Inspect the Docker plan with `python setup_runtime.py --plan --build --install` before authorizing installation. The native downloader performs installation; it has no plan-only mode. Neither installer is required for the portable example.

REA's Windows native PE provider is experimental and read-only; support differs from Linux. Fal and other generation providers require separately configured credentials and can incur charges. Source publication does not authorize paid calls or work on third-party binaries.

## Provenance and historical evidence

[THIRD_PARTY.md](THIRD_PARTY.md), [upstream-lock.json](upstream-lock.json), and [native-tool-lock.json](native-tool-lock.json) identify upstream engines and pinned downloads. Their underlying capabilities and authorship are separate from this integration layer.

Machine-specific operator notes and earlier runtime checks are preserved in [docs/history](docs/history/README.md). Those records do not prove a fresh-machine installation. User projects, credentials, runtime binaries, and generated caches are excluded.

## Reviewed delivery

See the [delivery workflow](docs/DELIVERY.md) for acceptance criteria, commit boundaries, identified AI/human review, protected integration, and source provenance.
