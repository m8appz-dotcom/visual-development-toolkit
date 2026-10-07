---
name: modding-lab
description: Use the installed Windows/Docker toolkit to inspect a user-owned game, analyze native or managed code, extract Unity assets, or build and verify a mod. Includes universal-modder, REA, Ghidra, ILSpy and AssetStudio; excludes PS5.
---

# Game Modding Toolkit

The plugin connects three real MCP servers: modding-lab (Windows gateway), ghidra (Docker headless), and rea (Docker). Use the actual connected tool schemas. Runtime is D:/modding-lab on Bobi. The Docker project root is /lab/projects; paths on Windows and Linux are different.

Create an isolated project with create_project, then import_target for explicitly selected files/folders. Original files are copied and hashed; never analyze or overwrite the installation directly. Use recon_game for a read-only engine scan of the actual Windows game folder. Consult the bundled knowledge and universal-modder engine playbooks.

Native: open the copied /lab/projects/PROJECT/input/... target with ghidra program.open, then report/list/decompile functions. Or use REA open_binary with provider_id ghidra and its evidence tools. Follow the connected schemas, close sessions and save reports. Ghidra decompiler output is pseudocode, not recovered original source. Keep analysis databases inside project output.

.NET: decompile_dotnet uses the real ILSpyCmd. REA can inspect managed artifacts too. Unity Mono and IL2CPP need different routes; never claim ILSpy recovers IL2CPP source.

Unity resources: inspect_unity_assets/export_unity_assets execute the original AssetStudio 0.16.47 libraries through a Windows console adapter. Text, PNG texture/sprite, audio and OBJ mesh conversion are exposed. FBX/animation export is available in the installed native AssetStudio GUI, not in the adapter. Unsupported Unity versions, encryption, missing type trees or failed codecs must be reported. Do not silently represent a raw object dump as a converted asset.

universal-modder: run_um passes project-relative arguments to the original um CLI. Use --help before an unfamiliar group. platform docker handles asset/file processing; platform windows handles local CLI tasks. windows_game_tool exposes native game launch, capture, recording and input. Before visible interaction on X, obtain explicit user authorization for that action; a boolean is a record of authorization, not a substitute for it. Do not kill unrelated processes or change registry settings.

Fal generation needs FAL_KEY and authorized spending; Blender needs a configured installation; neither is required for the verified analysis and sprite workflow. Do not invent generated outputs if either prerequisite is unavailable. Do not upload game binaries or decompiled files to cloud services. Use user's provided authorization to proceed with reversible installation, mod building and checking; do not ask again for already-authorized steps.

Test the actual target and validate originals with verify_originals. Report exact tool/version, evidence paths, results and limitations. Self-authored fixtures test the toolkit and do not establish that a commercial game or mod runs correctly. No anti-cheat/DRM bypasses or unauthorized multiplayer modifications. Package only authored mod code/assets, never game files or decompiled dumps. Publication or external messaging requires explicit authorization.

Start persistent backend: docker compose -f D:/modding-lab/compose.yaml up -d --no-build. It has restart unless-stopped and resource limits; do not restart Docker Desktop or existing containers to repair this plugin. Logs and test reports live in D:/modding-lab/logs and reports. Use the operator README for install, recovery and rollback.
