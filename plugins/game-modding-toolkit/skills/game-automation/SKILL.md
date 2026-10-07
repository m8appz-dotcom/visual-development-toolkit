---
name: game-automation
description: "Run and validate a game or visual app after changing code or assets. Use appropriate source build, browser, engine or Windows runtime tools; visible interactions obey the user's host permissions."
---

# Verify the actual game or app
Read the project's own build/run commands and existing tests. Build the affected target, run the changed interaction, and inspect the real output at relevant screen sizes or engine settings. Verify asset loading, transparency, scaling, pivots, animations, audio behavior and error recovery where applicable.

For Windows games use windows_game_tool only for supported CLI operations and authorized visible interaction. For web/native/mobile apps use the available platform-specific tooling; this plugin does not install an emulator or universal app driver. Do not close unrelated windows/processes. Save concise evidence and distinguish technical checks from perceptual audiovisual approval. Follow the user's Gemini rules for video/audio reviews.
