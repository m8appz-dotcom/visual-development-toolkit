# Visual Development Toolkit

Create and modify games and apps with visual elements. Start from source code, prepare assets, integrate them into working features and validate the actual result.

Private local plugin installed on **BOBI-ALMAX**, Windows, with a Linux Docker backend. It includes universal-modder, REA, Ghidra 12.1.4 with mrphrazer's headless MCP, ILSpy and the original AssetStudio. Both referenced Ghidra MCP repositories are downloaded; only the selected headless connector is active to avoid duplicate analysis sessions. No PS5 project is included.

## Locations

- Runtime, downloads, sources and Docker Compose: `D:\modding-lab`
- Plugin source: `D:\modding-lab\plugins\game-modding-toolkit`
- Installed copy: see `logs/plugin-install.json`; update source, then reinstall through Codex. Never edit the cache directly.
- Isolated projects and persistent reports: `projects/`
- Windows ILSpy GUI: `windows/ILSpy/ILSpy.exe`
- Windows AssetStudio GUI: `windows/AssetStudio/AssetStudioGUI.exe`
- Console AssetStudio adapter: `windows/AssetBridge/publish/AssetBridge.exe`
- Repository revisions, official package hashes: `reports/downloads.json`

Private Tailscale delivery: **http://100.82.79.73:18741/**. It serves only the results, this guide and the plugin ZIP, bound to Bobi's Tailscale address. `modding-lab-delivery` is a separate small, read-only container with health checks and restart unless-stopped. The ZIP contains the plugin package; the installed runtimes/images remain on Bobi and are not duplicated inside that ZIP. Verification of the HTTP routes and ZIP SHA-256 is recorded in `reports/delivery-verification.json`.

## Use in Codex

The local marketplace is `modding-lab`; the plugin is `game-modding-toolkit@modding-lab`. A new conversation loads its skills and three MCP connections: `modding-lab`, `ghidra`, `rea`. Example request:

> Use Visual Development Toolkit to improve my game or visual app source project. Build the requested feature, prepare and integrate its icons, sprites or textures, then run it and verify the result.

The gateway creates a project and copies explicitly selected input. The Windows path `D:\modding-lab\projects\my-project\input\game.exe` becomes `/lab/projects/my-project/input/game.exe` inside Docker. A Docker backend on another machine cannot directly read a client's Windows path; transfer the selected files first.

Prefer existing source code and ordinary build tools. Use asset-pipeline and fal-assets for game/app visuals, then integrate them into the consuming components/scenes. Only when compiled artifacts need investigation, use ILSpy for managed .NET code, Ghidra or REA with the Ghidra provider for native code, and AssetStudio for Unity resources. The plugin does not automatically recover a complete game's original source or guarantee compatibility with every engine/version.

## Start, recover and update

```powershell
docker compose -f D:\modding-lab\compose.yaml up -d --no-build
docker inspect modding-lab-analysis --format '{{json .State}}'
docker logs --tail 50 modding-lab-analysis
```

The container has `restart: unless-stopped`, a health check, 3 CPU and 8 GB memory limits. The MCP launchers start only this container if stopped. It resumes after Docker Engine starts; it does not alter Docker Desktop's existing sign-in/autostart policy. No shared Docker socket is mounted into the analysis container and no analysis TCP port is published.

The deployed image is `modding-lab:1.0.2`. Its small repair layer installs Debian `procps` (needed for REA's verified process cleanup) and initializes/releases Ghidra's script BundleHost. It also closes the upstream headless backend on MCP stdin EOF. The unmodified downloaded repository and the explicit local patch are retained separately. `Dockerfile` builds the base `1.0.0`; `Dockerfile.fix` builds the deployed image. Current dependency versions are recorded in `reports/docker-python-lock.txt` and `reports/windows-python-lock.txt`.

Docker Desktop DNS was already failing during installation. `build_image.py` resolves required package hosts from Windows and passes task-local build host entries. It does not change system DNS, restart Docker or touch existing services. These build IPs are recorded for diagnosis, not hardcoded as permanent production configuration. Rebuild with:

```powershell
python D:\modding-lab\build_image.py
docker compose -f D:\modding-lab\compose.yaml up -d --no-build
codex plugin add game-modding-toolkit@modding-lab --json
```

Before replacing an existing image, keep its image ID/tag in the deployment log. Do not prune shared Docker storage. Stop only this backend for maintenance. User projects are bind-mounted separately and remain after container recreation.

## Actual capabilities and boundaries

- Ghidra and REA connect to the real engines, not fake backends. REA is installed at version 4.1.0 and uses Ghidra/Java; no paid IDA or Hopper dependency is required for the installed workflow.
- ILSpyCmd decompiles managed assemblies in Docker; ILSpy's Windows GUI is also installed.
- AssetStudio's Windows adapter exposes asset inventory, text, texture/sprite PNG, audio and mesh OBJ export. Other objects require a type tree for a readable dump; unsupported cases return errors. FBX/animation export remains in the original installed GUI. Upstream declares Unity 3.4â€“2022.1; newer or encrypted formats may fail.
- universal-modder is installed in Docker and a separate Windows virtual environment. Upstream knowledge/examples and original workflow references are bundled. Active skills now prioritize visual development; legacy modding workflows are optional references outside automatic skill routing. File/sprite processing runs through `run_um`; Windows game control runs through `windows_game_tool`.
- External asset generation requires a user-provided `FAL_KEY` and authorized charges. Blender is required for its 3D-to-sprite rendering workflow. Neither is silently substituted or presented as tested when unavailable.
- Ghidra raw scripting and REA runtime operations are powerful. Restrict imported projects to intended data; the container mount is the working project area, not the entire game library. Authorizations for visible game interaction, changes to real saves and publication remain separate from toolkit installation.

## Source and asset bundles

Use package_project for an authored subfolder under a lab project output directory. It packages game/app source and visual assets without a mod-specific loader or publishing requirement. It does not compile an app, create a platform installer or publish a release. Use the source project's actual build tools for those deliverables.

## Tests and rollback

The repeatable test runner connects using the **installed** `mcp.json` and calls actual MCP tools on authored native, .NET, JavaScript and Unity fixtures. See `reports/plugin-test.json` and the final test summary. It verifies recovered logic, exported bytes, tool discovery, original-file integrity and error handling. It does not prove compatibility with every game/app. The 1.0.4 component tests remain historical evidence; reports/visual-development-test.json records the targeted 1.1.0 update checks.

The final test also confirms that both MCP sessions and native provider processes close cleanly. A separate read-only Codex app-server probe confirms that the plugin is installed/enabled and declares its MCP connections. That probe creates no chat/model turn; tools are exercised by the MCP test runner, not inferred from a catalog entry. Start a new chat to load the newly installed tools in Codex.

```powershell
D:\modding-lab\windows\venv\Scripts\python.exe D:\modding-lab\test_plugin.py <installed-plugin-path>
```

To disable/remove only this installation:

```powershell
codex plugin remove game-modding-toolkit@modding-lab
docker compose -f D:\modding-lab\compose.yaml stop
```

Update 1.1.0 preserves the internal ID and runtime paths to keep existing projects working. The pre-update source and documentation are saved in backups/reframe-1.0.4/. Restore the owning source from that archive and reinstall with codex plugin add for rollback; do not overwrite current project data.

Keep `projects/`, `reports/` and sources for rollback. No cleanup command in this guide deletes project data or shared images/volumes. Run no system restart while other containers are active; follow the host's orderly Docker shutdown rules if a restart is explicitly requested.

## Attribution

Upstream projects and their original licenses are recorded in `reports/downloads.json` and the plugin's `licenses/` folder. The Windows AssetStudio console adapter and local gateway are authored for this installation; they are not official upstream features. Runtime SDK/JDK package evidence is in the runtime download logs. No game binaries, dumps or proprietary game assets are distributed by the plugin package.
