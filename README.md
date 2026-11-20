# REA

Create and modify games and apps with visual elements. This Codex plugin combines source-development workflows with asset generation/conversion and optional compiled-code analysis. Version **1.1.0** includes REA, Ghidra, ILSpy, AssetStudio and universal-modder. PS5 projects are excluded.

Work from source code when available: implement the feature, prepare its visuals, integrate the actual files, then build/run the project and verify the result. Use the analysis tools only when existing compiled artifacts need investigation. Legacy mod workflows remain optional references.

Version **1.2.0** adds a [native Windows runtime](docs/NATIVE-WINDOWS.md) for on-demand installation on X and Titan. The earlier 1.1.0 evidence and Bobi handoff remain historical records; the existing Bobi Docker runtime is preserved.

## Contents

| Path | Purpose |
|---|---|
| `plugins/game-modding-toolkit/` | Complete plugin package: manifests, 10 active skills, MCP launchers, knowledge, examples and licenses |
| `.agents/plugins/marketplace.json` | Local Codex marketplace |
| `windows/AssetBridge/` | Source for the Windows AssetStudio console adapter |
| `Dockerfile`, `Dockerfile.fix`, `compose.yaml` | Resource-limited analysis backend and documented Ghidra/REA repairs |
| `upstream-lock.json` | Seven upstream commits and SHA-256 hashes of official runtime/tool downloads |
| `setup_runtime.py` | Windows runtime preparation, optional Docker build and installation |
| `configure_plugin.py` | Connect the source plugin to an existing runtime |
| `fixtures/`, `test_*.py` | Authored fixtures and actual MCP checks |
| `docs/INSTALL-WINDOWS.md` | Setup, recovery and rollback |
| `docs/USO-ES.md` | Spanish usage and setup guidance |
| `docs/RESULTADOS.md` | Verified 1.1.0 results and limitations |
| `docs/BOBI-OPERATOR.md` | Operator handoff for the existing Bobi installation |

The internal package ID remains `game-modding-toolkit@modding-lab` for compatibility. Its visible name is **REA**. The repository preserves the complete plugin source; large third-party installations are fetched from the official URLs and revisions in the lock file. User projects, credentials, generated logs and runtime binaries are excluded.

## Existing Bobi installation

The verified runtime is `D:\modding-lab`; the owning installed source remains there. This repository is its versioned source export, not a second running service. Open a new Codex chat and select **REA**.

```text
Create a playable 2D prototype, prepare and integrate its sprites, and verify the first scene.
Improve this app with consistent icons and illustrations, integrate them into its components, and check the screens.
Modify this source project and validate the changed behavior in its real runtime.
```

## Another Windows machine

Read [Windows setup](docs/INSTALL-WINDOWS.md) before preparing a new runtime. Dependencies: Windows x64, Python 3.12+, Git, .NET 8 Desktop Runtime, Codex and Docker Desktop in Linux-container mode. FFmpeg is needed on Windows for native capture/recording. Allow enough space for the SDKs, archives, source checkouts and Docker images: the original lab used about 4.7 GiB of files plus a 4.7 GiB image; builds/caches need additional space.

From a clone of this repository, preview the steps first:

```powershell
python setup_runtime.py --plan --build --install
# Downloads/installs dependencies, builds Docker and installs the plugin:
python setup_runtime.py --build --install
```

The 1.1.0 plugin and existing Bobi components have runtime evidence: **17 targeted update checks**, plus **32 earlier component checks**. The repository's new setup orchestration was checked for syntax/configuration; a full fresh-machine rebuild has not been executed. Package registries and upstream availability can change even with pinned versions.

## Optional generation and rendering

Fal runs in the cloud, requires `FAL_KEY`, and charges per model/use. Configure the key in the local environment; never commit it. No paid generation was performed in the recorded checks. Blender must be configured for 3D-to-sprite rendering; ComfyUI requires its own available server. These requirements do not prevent ordinary source development or local sprite processing.

REA 4.1.0 and Ghidra 12.1.4 are connected through separate MCP servers. ILSpy recovers managed .NET code, not IL2CPP source. AssetStudio's original support range is Unity 3.4–2022.1; PNG/text/audio/OBJ export uses the included adapter, while FBX/animation remains in the original GUI and was not exercised in these checks. Decompilation is evidence about compiled behavior, not recovery of the original repository.

## Licenses and provenance

See [third-party notices](THIRD_PARTY.md), `upstream-lock.json` and the preserved licenses under the plugin. This repository contains local integration code and adapted workflows alongside upstream material. The third-party licenses apply to their respective files; this export does not assign a new blanket license to the user's integration code.


## Source reconciliation

See [the reconciliation and validation record](docs/RECONCILIATION-20261119.md) for the current source candidate and its acceptance scope.
