---
name: reverse-engineering
description: "Understand compiled game or app behavior or asset formats when source is unavailable. Route .NET to ILSpy, native binaries to Ghidra/REA, and Unity resources to AssetStudio; skip decompilation for normal source development."
---

# Analyze compiled behavior only when needed
Prefer the user's source repository. If the requested change requires an existing compiled artifact, import a selected copy into an isolated project and record its hashes. Use decompile_dotnet for managed .NET, Ghidra or REA for native code, REA for JavaScript artifacts and AssetStudio for supported Unity resources. Consult reverse-engineer-anything for REA's actual schemas.

Save evidence, function/format hypotheses and limitations; validate claims with a fixture or runtime observation when possible. Ghidra yields pseudocode, not original source. ILSpy does not recover IL2CPP source. Close sessions. Keep extracted proprietary resources and decompiled dumps out of deliverable bundles unless distribution is explicitly authorized and appropriate.
