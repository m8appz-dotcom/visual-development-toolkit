# GTA Enhanced Mod Lab

Local Codex plugin for this Windows PC. Includes the researched GTA Enhanced guide, an executable test runner and an installation journal with verified backups and rollback.

Version 0.2.0 adds evidence from eight downloaded map/interior/prop/vehicle/mission packages, nested RPF inspection and conservative C#/Lua source review. `read_mod_field_notes` reads the findings; `inspect_mod_package` inspects an already extracted DLC folder into a fresh report/output; `review_mod_script_source` flags patterns for manual review. Sources and third-party assets remain outside the plugin. The full findings are in `skills/gta-enhanced-workflow/references/HALLAZGOS-PAQUETES.md`.

Version 0.3.0 adds inspected Dragon Ball, Street Fighter, Star Wars, DC, Mario/Kart and Star Fox findings in `HALLAZGOS-FRANQUICIAS.md`. `read_mod_field_notes` now returns `franchise_notes` and its SHA256. The native auditor recognizes binary PSO/RBF YMT and managed `.ndll` assemblies, avoiding false compression errors and exposing actual loader references. Downloaded assets and decompiled code stay outside this plugin. Large DLC inspection remains explicitly bounded; MCP read/install roots and normal size limits are unchanged.

Version 0.4.0 adds the inspected kjb33 Star Wars MEGA PACK conversion and `rebuild_mod_package`: rebuild fresh DLC containers from converted resources, read them back, preserve untouched member payloads, and compare full fragment geometry/rig/collision structures. Collision positions may requantize within their own per-axis precision; the report measures this instead of claiming byte identity. `read_mod_field_notes` also returns `starwars_notes`. The new authored wrapper depends on the existing CodeWalker runtime and Gen9 shader conversion data; its source is included under `tools/rpf-rebuild/`.

Version 0.4.1 checks a changed collision's saved quantum against its unchanged bounding box; converted data cannot widen its own allowed tolerance. Exact unchanged bounds remain accepted. Five negative comparator cases cover excessive drift, topology/materials, mesh, bones and inflated quantum.

Version 0.4.2 adds the scoped Enhanced rig/animation and QA case note in `HALLAZGOS-RIG-ANIMACION-Y-QA.md`. `read_mod_field_notes` returns `rig_qa_notes` and its SHA256 alongside unchanged existing fields. It documents paired YFT/YDD translation flags, retarget scale/shear, controlled A/B measurement and QA transfer boundaries. This is a documentation/retrieval update: it adds no automatic repair, YCD-to-skeleton diagnostic, gameplay barrier or new runtime case. Project-specific evidence stays in its owning project.

## Installed command-line tools

```powershell
& 'D:\modding-lab\windows\gta-enhanced-mod-lab-venv\Scripts\gta-enhanced-test-runner.exe' static
& 'D:\modding-lab\windows\gta-enhanced-mod-lab-venv\Scripts\gta-mod-install-ledger.exe' list
```

The runner reads actual assets, checks conversion preservation and rejects known negative fixtures. `runtime-preflight` inspects the existing local FiveM QA service. `stock-smoke` runs only when that service verifies an exact ready client, a clean baseline and an available shared lease. It does not launch/connect a game or alter another project's QA resources.

The ledger provides `plan`, `apply`, `rollback` and `list`. Plans include hashes and exact paths. Apply requires the plan digest and rechecks source/target state. Rollback restores original files or removes the plan's unchanged additions; it refuses independent edits. Backups and the SQLite journal survive process restarts.

## MCP tools

- `mod_lab_status`, `read_modding_guide`
- `read_mod_field_notes`, `inspect_mod_package`, `review_mod_script_source`
- `rebuild_mod_package`
- `audit_mod_assets`, `convert_mod_assets`, `run_static_mod_tests`
- `runtime_test_preflight`, `run_runtime_stock_test`, `reconcile_runtime_test`
- `plan_mod_install`, `apply_mod_install`, `rollback_mod_install`, `list_mod_install_plans`

Static results do not certify gameplay, visual deformation, cloth or material appearance. The stock QA cases do not test JulioNIB powers in Story Mode. The conversion tool writes converted resource types to a new run folder; it does not assemble/install a complete ped package or automatically copy YMT/YLD metadata.

## Scope and prerequisites

`runtime.json` points to this PC's installed .NET SDK, native auditor, lab fixtures and existing QA connector. It initially permits installation only under:

`D:\modding-lab\state\gta-enhanced-mod-lab\staging`

The test does not authorize installing into the actual GTA folder. Expanding installation roots requires an explicitly approved scope and a reviewed local configuration. Symlinks/junctions, path traversal, executable installers, Gen8 resource types and the identified obsolete unlocker are rejected. No arbitrary command or security-setting tool is exposed.

The native CodeWalker-based auditor remains in the existing local lab, with its own dependencies. Its authored source is included under `tools/native-audit/`; third-party Marvel assets and binaries are excluded from this plugin archive.

## Local installation and recovery

The separate Python environment uses MCP 1.30.0. Package metadata version is `gta-enhanced-mod-tools==0.4.4`; the plugin MCP runs its source entrypoint from `mcp.json`. Install the plugin through the configured `modding-lab` marketplace:

```powershell
codex plugin add gta-enhanced-mod-lab@modding-lab --json
```

Edit the source here; reinstall after a version bump. Do not manually edit Codex's version cache. The MCP server starts on demand and uses stdio; it does not expose a network listener.

To resolve a partially applied file plan, inspect its journal and call rollback. To resolve an uncertain live test, call `reconcile_runtime_test` with its recorded operation ID; do not repeat the action. The shared QA lease is retained when the coordinator cannot yet release it.

Version 0.4.3 adds Nitrado/FiveM Enhanced field notes: served streaming indexes, packed/streamed ped replacement compatibility, real runtime and visual evidence, driver seat fit, and the separate NIB Story Mode powers. read_mod_field_notes adds nitrado_notes with its SHA256; it does not add automatic repair or retarget the existing local QA MCP.

Version 0.4.4 records the rejected and reverted kart seat/IK pilot, including binary readback and the cold-session requirement. No experimental pose or third-party game assets are packaged.
