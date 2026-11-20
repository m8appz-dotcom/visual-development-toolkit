# Source reconciliation — 2026-11-19

Base main: 516091074b28bb057fb56d05150705d361b92c67. Preserved source recovery: codex/x-toolkit-recovery-20261119. Reversion point: codex/pre-reconcile-main-20261119.

This candidate overlays the selected X source on the existing published tree, preserving existing files not selected in the export. It brings the AccuRig 0.4.0, Blender agent 1.0.0, REA/game-modding-toolkit 1.3.1 and GTA Enhanced Mod Lab 0.4.5 source packages and marketplace metadata together. Installed caches, downloaded runtimes, user projects and private runtime data remain outside version control. Generated build/lib duplicates were not integrated.

Two fresh-checkout issues were corrected in this candidate: build completion now creates its output directory before copying a verified preview; the collapsed-finger regression uses a synthetic fixture and a non-collapsed control instead of requiring a private runtime checkpoint. No real model or private checkpoint was copied or opened.

Validation in the isolated worktree: 59 existing Node lifecycle/security tests,19 synthetic asset-preservation tests and14 user-authority tests pass (92 total); Python source syntax passes. These checks use synthetic temporary files and mocked native operations. No installed plugin, native UI, live model/provider, user asset or active service was exercised or modified. Native application/install smoke acceptance remains separate from these unit results.

Main remains unchanged in this preparation phase. Review this branch and run the necessary Windows installation/runtime smoke check in a suitable maintenance/test environment before using it to replace an installed source/runtime.
