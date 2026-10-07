---
name: game-recon
description: "Inspect an existing game or visual app project and identify its engine, framework, assets and build route. Use for project onboarding or compiled-artifact investigation; prefer available source."
---

# Inspect a game or visual app
Start with source files, manifests, lockfiles and build scripts. Record target platform, engine/framework version, entry points, scenes/screens, asset formats, import conventions and existing checks in PROJECT_NOTES.md. For an existing product, locate the requested behavior and its dependencies before editing.

Use recon_game only when an installed Windows game is the actual target and engine detection is useful. For a source project, inspect its own configuration instead. For compiled apps, use REA or managed/native analysis only as needed. Identify uncertainties and verify them from files/runtime; choose a route toward the requested feature, not a mod loader by default.
