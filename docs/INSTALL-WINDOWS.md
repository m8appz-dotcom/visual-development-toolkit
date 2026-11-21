# Optional Docker runtime on Windows

The [portable quickstart](../README.md#portable-quickstart) does not require this runtime. Choose Docker only when the intended engine/format needs it. Requirements: Windows x64, Python 3.12+, Git, .NET 8 Desktop Runtime, Codex, and Docker Desktop using Linux containers. Reserve space for source, downloads, images, and build caches; the earlier installation used roughly 4.7 GiB of files and a 4.7 GiB image.

From your own source checkout, inspect the plan first:

```powershell
python setup_runtime.py --plan --build --install
```

The following command downloads and installs dependencies, builds an image, and registers the plugin. Run it only for a deliberately chosen new runtime:

```powershell
python setup_runtime.py --build --install
```

The orchestration is distinct from the portable CI checks. A full fresh-machine Docker rebuild has not been established by this portfolio walkthrough. Check pinned upstream URLs and runtime requirements before installation. The source plugin lives in `plugins/game-modding-toolkit`; configure the owning source with `configure_plugin.py`, not an installed cache. `MODDING_LAB_ROOT` and the configured MCP launchers identify your runtime root; verify it with `component_status` rather than copying a historical host path.

## Operate only the intended backend

```powershell
docker compose -f compose.yaml up -d --no-build analysis
docker inspect modding-lab-analysis --format '{{json .State}}'
docker logs --tail 50 modding-lab-analysis
docker compose -f compose.yaml stop -t 30 analysis
```

The backend declares 3 CPUs, 8 GiB RAM, and `restart: unless-stopped`. This does not change Docker Desktop startup preferences. Preserve bind-mounted `projects/` and do not restart other services to repair this runtime.

## Recovery and rollback

Keep the previous owning-source commit, runtime image, projects, and reports. Update through the owning source and validate the affected engine with authorized fixtures. Roll back with a separate checkout configured to the preserved runtime; do not discard work or edit the installed cache. Removing the plugin with `codex plugin remove game-modding-toolkit@modding-lab` disconnects it without deleting runtime data.

[Historical component checks and host-specific notes](history/README.md) remain available, with their original scope and limitations.
