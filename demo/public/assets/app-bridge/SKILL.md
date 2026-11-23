---
name: app-to-mcp
description: Build MCP integrations that expose an existing application's capabilities, then package the server, tool contracts and reusable workflows as a Codex plugin. Use for application adapters and plugin engineering, rather than ordinary feature work inside an app.
---

# Application capabilities to Codex tools

Start from the action the user needs to perform in the application. Reuse its supported API, SDK, CLI or libraries when these cover the action. Inspect shipped artifacts with REA, ILSpy or Ghidra only when the integration depends on behavior or interfaces the available documentation/source does not establish.

## Establish the boundary

- Distinguish the original application, an authored adapter, the MCP transport and the skill that guides use. A successful call through one adapter does not demonstrate every feature of the app.
- Match inspection to the target: managed metadata/C# for .NET, native analysis for machine code, and application graphs for JavaScript/Electron. Preserve the target and any active analysis belonging to another task.
- Record a small capability map: user action, native entry point, proposed MCP tool, input/output contract and a fixture that can prove the mapping. Keep uncertain capabilities explicitly unverified.

## Expose a useful capability

Implement narrow, typed tools around native operations. Prefer meaningful verbs and structured results over a general shell, arbitrary script execution or a button that merely launches the app. Constrain file operations to the selected project, return actionable failures, and preserve native behavior and formats.

Test tool discovery, a real native operation and a rejected invalid request. Use an owned or authorized fixture and compare the actual output with an independently known result. Keep source hashes, runtime paths and full traces in private run evidence; publish only intentionally selected, non-sensitive fixtures and results.

The repository's reproducible example is `tools/run_app_bridge_case.py`: it calls the real gateway to inspect and export an authored Unity TextAsset with AssetStudio/AssetBridge, inspect the authored adapter with ILSpy, verify originals and read back the result from a package. It requires an existing configured runtime and a separate output directory; it does not install or restart engines.

## Package the integration

Keep the plugin's stable identity. Bundle its manifest, MCP server configuration, adapter source and the skills needed to use the tools. Tools are exposed by the MCP server; the skill explains when and how to use them. Refer to separately installed application engines without embedding machine-specific paths, credentials or runtime binaries.

Validate every manifest reference and skill path, discover tools from the packaged server, and run the fixture through that package. Report package/transport acceptance separately from human authentication, native UI acceptance and feature coverage. Do not create credentials, register an authenticator or claim a real holder login from machine-only tests.
