# RetopoFlow tools

The Blender MCP now exposes typed retopology operations. They require an explicit
owned interactive session; start_blender_session(background=False) creates one
hidden without changing existing windows. Pass the session_id to every call.

1. get_retopology_capabilities: adapter requirements and truthful limits.
2. begin_retopology: append an explicit mesh and its source rig/actions from a
   .blend into a fresh owned session. Supply the actual RetopoFlow package folder
   and a NEW output .blend path. Source files are read only and hashed.
3. inspect_retopology: wait until ready=true. Read actual native tool names and
   topology. No headless registration claims: RetopoFlow skips its initialization
   when Blender is running in background mode.
4. add_retopology_patch: explicit vertices/faces, source-local coordinates,
   projected with native RetopoFlow. Invalid input/projection fails before editing;
   patch exceptions restore the target BMesh.
5. build_retopology_bone_strip: directed ring layout around existing bones. Every
   ring is {bone: string, t: number from 0 to 1}. Missing/overlong rays are rejected
   before target mutation. This is not anatomy inference or whole-character auto
   retopology. Extents and layout must be chosen for the actual source.
6. select_retopology_tool: activate the actual named native tool; does not simulate
   mouse gestures or claim to exercise its brush strokes.
7. relax_retopology: adapter Laplacian smoothing followed by native RetopoFlow
   surface projection. Preserves boundary by default. This is NOT the native
   RetopoFlow Relax brush; the response reports the actual algorithm.
8. finish_retopology: request native commit/cancel, then inspect until modal exit.
9. transfer_retopology_weights: interpolate existing source skin weights using
   source triangles. Keeps the existing rig. Refuses existing target groups.
10. validate_retopology_poses: evaluate bounded existing action/frame samples on
    both meshes; restores frame, action slot, matrices, pose mode and NLA mutes.
    Reports finite coordinates and sampled one-way distance. It does not establish
    visual quality, better deformation, full-motion coverage or performance.
11. save_retopology_result: verify original source hash and atomically publish
    the reserved new output file. Existing output paths are not overwritten.
12. undo_retopology: native RetopoFlow undo/redo for target edits and adapter
    relaxation. Useful for trying an additional patch without keeping it.

The add-on is loaded only in the selected test process. No user preferences are
saved, no default provider is changed and no original mesh file is saved in place.
Inputs are plain data; these tools accept no caller-supplied Python. Mutating tools
reject non-owned sessions and background sessions. They do not modify existing
rigs or rebind the source character in production.

Tested scope: RetopoFlow 3.4.10 / Blender 5.2.1 LTS / Windows X. Other package
versions require a runtime test. Package import, geometry operations and the
interactive consumer are distinct checks; never substitute one for another.
