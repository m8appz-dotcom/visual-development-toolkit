# Windows setup and operation

## Use the existing runtime

On Bobi, the runtime and active source remain in `D:\modding-lab`. Creating this repository did not recreate containers or move project data. To point this checkout at an already prepared runtime:

```powershell
python configure_plugin.py --runtime-root D:\modding-lab --dry-run
python configure_plugin.py --runtime-root D:\modding-lab
codex plugin marketplace add . --json
codex plugin add game-modding-toolkit@modding-lab --json
```

Do this only when you intend the checkout to become the owning plugin source. It registers the same plugin/marketplace identity, not a second plugin. Keep the previous owning source for rollback. Manifest versions must be incremented for later edits before reinstalling; never edit the installed cache directly.

## Prepare a new runtime

1. Install Windows x64 Python 3.12+, Git, .NET 8 Desktop Runtime, Codex and Docker Desktop. Start Docker in Linux-container mode. Install Windows FFmpeg if native video capture is needed. Optional Blender/ComfyUI/Fal are separate.
2. Clone the private repository into a short local path. Run `python setup_runtime.py --plan --build --install` to see its commands.
3. Run `python setup_runtime.py --build --install`. The checkout becomes the runtime root; large generated directories are ignored by Git. The installer fetches exact upstream commits and checksum-verified archives, prepares the Windows venv, restores ILSpyCmd, compiles AssetBridge, builds the two Docker layers and installs the plugin.
4. Inspect `logs/` if a step fails. Correct the cause and rerun. Existing upstream checkouts with a different commit are rejected instead of overwritten. A NuGet tool already present is reused. Do not reset Docker or delete volumes to solve a setup error.
5. Open a new Codex chat. Call `component_status` and verify the tools are available before working on a project.

The Windows SDK downloaded by the installer is .NET 10.0.401; the authored AssetBridge targets .NET 8 and needs the separately installed .NET 8 runtime. Linux ILSpyCmd targets .NET 10. Ghidra uses the pinned full JDK 21.

The Compose file exposes only the analysis service. It does not publish a network port, mount the Docker socket, or start the Bobi-specific Tailscale delivery service. It retains the original container name, so do not run a second copy on a host already using `modding-lab-analysis` without planning separate names and data mounts.

## Source and asset work

Use the source project's normal build tools to implement games/apps. The MCP gateway prepares isolated asset/analysis projects; it is not a universal app compiler. `package_project` packages authored source/assets from an output subfolder into a ZIP; it does not build a platform installer or publish a release.

MCP configuration uses `${PLUGIN_ROOT}` for launcher files and `MODDING_LAB_ROOT` for the runtime root. `configure_plugin.py` rewrites only the runtime paths in `mcp.json`. The central skill includes the historical Bobi path as a reference; the actual configured environment and `component_status.runtime_root` are authoritative on another machine.

## Checks

The existing installation's evidence is recorded in `RESULTADOS.md`. To regenerate authored fixtures on a newly prepared runtime:

```powershell
python prepare_fixtures.py
windows\venv\Scripts\python.exe test_plugin.py <installed-plugin-path>
```

The first runner connects to installed MCP configuration and performs the earlier component checks. It writes logs/reports locally. The targeted update runner additionally expects a Codex host inventory in `reports/codex-host-plugin-list.json`, so its recorded 17-check result is delivered as historical evidence for Bobi; do not imply that file exists on an untouched clone. These fixture tests do not prove compatibility with every real game or app.

## Start, recover and stop

```powershell
docker compose -f compose.yaml up -d --no-build analysis
docker inspect modding-lab-analysis --format '{{json .State}}'
docker logs --tail 50 modding-lab-analysis
docker compose -f compose.yaml stop -t 30 analysis
```

The backend uses 3 CPUs, 8 GiB of RAM and `restart: unless-stopped`. It resumes after Docker Engine starts; this repository does not alter Docker Desktop's sign-in policy. Do not restart the engine or other services to repair this plugin. Project data is bind-mounted in `projects/` and must be preserved.

## Updates and rollback

Commit owning-source changes, increment both plugin manifests to the same version, reinstall, then test affected behavior. Preserve the previous commit and runtime image. For rollback, use a separate checkout of the known-good commit, configure it to the preserved runtime, then register/reinstall that source. This avoids discarding uncommitted work. Do not roll back by editing the cache or deleting `projects/`.

To remove only the plugin connection:

```powershell
codex plugin remove game-modding-toolkit@modding-lab
```

Removing the plugin does not delete runtime directories or projects. Keep data/backups unless the human expressly asks to remove them.

