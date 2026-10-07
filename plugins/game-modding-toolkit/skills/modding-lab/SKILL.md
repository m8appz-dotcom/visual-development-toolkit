---
name: modding-lab
description: "Create and modify games and apps with visual elements using the installed Windows/Docker tools. Coordinate source changes, generated assets, asset conversion, integration and actual validation. Use for prototypes, UI visuals, sprites, textures, 3D assets or changes to an existing app/game. REA and decompilers are optional when source is unavailable."
---

# Visual Development Toolkit

## Purpose and default workflow
Accelerate creation and modification of games and apps with visual elements. The user may be building a new product or changing an existing source project. Start from their intended behavior, project, platform and visual style. Work with the existing source repository when available; do not turn normal development into a game-installation scan, loader project, pass-through bridge or mod workflow.

1. Inspect the selected source, framework/engine, existing visual system and build commands. Preserve unrelated changes. For a new project, choose a stack appropriate to its target platform and scope. Use the coding agent's normal file, terminal and source-editing tools; this MCP does not supply a universal project generator or app builder.
2. Implement a useful first slice: a playable mechanic, working screen or interaction. Reuse existing assets where suitable. Specify asset dimensions, alpha, palette/style, animation frames, formats, and 3D scale/axes from the consuming code.
3. Generate new visuals/audio with fal-assets when the user has a key and authorizes the cost. Convert assets with asset-pipeline. Integrate actual files into the source project, components, engine imports and build; an exported image by itself is not a completed game/app feature.
4. Build and run the actual project. Test the changed behavior and inspect real rendered screens or game scenes. Match evidence to claims: tool discovery does not prove a feature works; a build does not establish visual quality. Follow the user's required Gemini workflow for perceptual video/audio QA.
5. Deliver source changes and authored assets with relevant checks and recovery steps. Use package_project for an authored output folder when a ZIP is useful. Its ZIP is a source/asset bundle, not a platform installer or proof of a successful build.

## Installed tools and paths
Three real MCP servers connect: modding-lab (Windows gateway), ghidra and rea (Docker). Runtime: D:/modding-lab on Bobi. Windows projects map from D:/modding-lab/projects/PROJECT to /lab/projects/PROJECT inside Docker. Infrastructure names and the internal plugin ID remain for compatibility; they do not define the product's purpose.

Use create_project for isolated asset/analysis work and import_target for selected inputs; copies are hashed. Read/write the user's authorized source repository with the coding agent's usual tools. run_um exposes sprite, video, fal, comfy, render3d and other CLI processing; inspect --help for exact flags. Docker processes assets/files; Windows handles local CLI tasks. The bundled upstream knowledge/examples are technical references, not instructions to build a mod by default.

When source is unavailable and the task requires understanding an existing artifact, use REA for native, managed or JavaScript applications; Ghidra for native binaries; ILSpy for managed .NET code. Decompiler output is not the original source. Unity Mono and IL2CPP need different routes; ILSpy does not recover IL2CPP source. Close analysis sessions and save evidence in reports.

AssetStudio's Windows adapter inventories and exports Unity text, texture/sprite PNG, audio and OBJ mesh. The original GUI retains FBX/animation export; those paths were not tested. Upstream support is Unity 3.4–2022.1; report unsupported versions, missing type trees, encryption or codecs. Asset extraction is useful only when the actual task needs existing compiled resources.

## Execution and delivery
Fal generation runs in the cloud and requires FAL_KEY and authorized spending. Blender must be configured for render3d; ComfyUI needs a separately available server. Do not claim any optional service is available or tested without checking it. Keep credentials out of assets/source packages and do not upload binaries or decompiled files to cloud generation.

windows_game_tool can launch/capture/drive a Windows target where its CLI supports that target; it does not guarantee control of every app or mobile device. Use the appropriate platform/browser/native testing tool for the actual product. Respect the user's host-specific visible-interaction permissions; do not kill unrelated processes or change registry settings.

Verify imported originals with verify_originals when imports were used. Package only intended authored files. A request to create or modify a game/app does not authorize external publication, messaging or paid generation. Optional legacy modding instructions under references/optional-modding apply only when the human explicitly requests a mod.

Start/recover: docker compose -f D:/modding-lab/compose.yaml up -d --no-build. Existing container resource limits and restart policy remain. Do not restart unrelated Docker services to repair this plugin. Operation/rollback: D:/modding-lab/README.md. The installed component fixtures establish tool behavior, not compatibility with every game/app.
