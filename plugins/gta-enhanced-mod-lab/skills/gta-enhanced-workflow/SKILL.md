---
name: gta-enhanced-workflow
description: Inspect, create, test and prepare GTA V Enhanced mods using the local auditor, repeatable test runner and journaled installation/rollback tools. Use for compatibility, rigging, Gen9 conversion, scripts, crashes or scoped mod installation.
---

# GTA Enhanced Mod Lab

Read `references/GUIA-GTA-ENHANCED.md` for the researched guide. Prefer our tools to manual edits. Local tools require this PC's configured lab/runtime; a plugin installation does not imply that a mod is installed in GTA.

For FiveM Enhanced server streaming, packed versus streamed ped replacements, browser upload integrity, seat fit or actual Nitrado acceptance, read `references/HALLAZGOS-NITRADO-ENHANCED.md` or `nitrado_notes` from `read_mod_field_notes`. Check the served streaming index as well as disk hashes after file-name changes, then validate the effective session. Numerical visibility/movement does not prove correct meshes or driver fit. Keep the nine NIB Story Mode powers separate from converted skins and vehicles.

For ped deformation, retargeting or animation timing, read `references/HALLAZGOS-RIG-ANIMACION-Y-QA.md` or `rig_qa_notes` from `read_mod_field_notes`. Compare actual YCD channels against both YFT/YDD skeletons and flags; the current auditor does not automate that cross-check. Do not apply universal translation, scale or yaw fixes. Keep telemetry barriers in the FiveM QA executor, with real write ACKs, file readback and explicit timeout failure; never infer visual approval or exclusive crash/stall causation from a functional pass.

For Dragon Ball, Street Fighter, Star Wars, DC, Mario/Kart and Star Fox, read `references/HALLAZGOS-FRANQUICIAS.md` or the `franchise_notes` returned by `read_mod_field_notes`. It records actual script runtime references, differing bind poses, supplemental model downloads and OIV replacement scope. Detect PSO/RBF YMT by content; do not treat every YMT as compressed RSC7. Review real installer actions instead of recursively copying all extracted files. Legacy .ndll and Enhanced .ENdll are managed assemblies with different dependencies, not interchangeable filename variants.

For complete DLC conversion, read `references/HALLAZGOS-STARWARS-MEGAPACK.md` or `starwars_notes`. After `convert_mod_assets`, use `rebuild_mod_package` with the original DLC folder and `gen9_output`. It rebuilds fresh archive copies and verifies all leaf payloads and fragment geometry/rig/collision preservation, allowing only measured collision requantization within each geometry's precision. It does not install files or port optional scripts. Start from originals to avoid cumulative quantization.

For maps, MLO interiors, props, vehicles and mission packages, call `read_mod_field_notes` or read `references/HALLAZGOS-PAQUETES.md`. Use `inspect_mod_package` on the extracted folder to inspect DLC containers and generation variants. Use `review_mod_script_source` on scoped original/decompiled C# or Lua copies to identify review points; heuristics are not runtime findings. Select one Enhanced branch before preparing an install plan. YMAP/YTYP2 and YBN43 are not automatically Legacy blockers. Unresolved local archetypes can be external game/DLC dependencies.

1. Call `mod_lab_status` to verify actual paths and dependencies. Use `read_modding_guide` for the guide. Preserve unrelated game files and processes.
2. Inspect assets with `audit_mod_assets`; use `convert_mod_assets` only into its new output directory. Treat errors as blockers; distinguish warnings, unsupported cloth/pose checks and actual defects. Never equate bone counts or names alone with a correct rig.
3. Run `run_static_mod_tests`. This checks actual files and known negative fixtures and preserves fresh reports. It never certifies gameplay or visual appearance.
4. For live checks call `runtime_test_preflight`, then `run_runtime_stock_test` only when the existing coordinator confirms a fresh, clean Enhanced baseline. The tool supports its stock NPC cases, not arbitrary hero models or NIB powers. Respect the shared QA lease; never change the coordinator or bypass its rejection. Do not launch, connect or restart a user's game/server as an implied part of installing this plugin.
5. For user-authorized file installation call `plan_mod_install`, show its concrete file scope, then `apply_mod_install` with that plan's digest. Existing authorization can cover the action; do not add redundant approval. Default installation roots are the staging sandbox. Installing into the real game requires explicit scope and a reviewed local runtime configuration; do not widen roots autonomously merely to get a test passing.
6. Use `rollback_mod_install` to restore only unchanged files owned by that plan. It refuses to overwrite independent changes. `list_mod_install_plans` shows durable journal state. Do not manually delete backups to resolve a conflict.

Do not weaken security, bypass author licensing, install obsolete plugins, execute arbitrary shell commands, submit data to third parties, or declare zero crashes. Test one behavior with a stock ped first, then the custom skin, then effects and interactions. Record build, hashes, logs, timings and actual captures. Use the user's required Gemini workflow for perceptual video/audio QA.

Keep authored code/notes separate from extracted third-party assets. Do not redistribute the downloaded Marvel packages as part of this plugin. Report runtime failures and visual validation honestly; `blocked` or `pending` is not a pass.
