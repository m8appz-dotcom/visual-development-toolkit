"""Typed RetopoFlow operations; all mutations require an owned interactive session."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Literal
import uuid


def register(mcp, *, rpc, session_info, state_dir):
    runtime = Path(__file__).with_name('retopology_runtime.py').resolve(strict=True)
    state_dir = Path(state_dir) / 'retopology'
    state_dir.mkdir(exist_ok=True)

    def owned(session_id):
        info = session_info(session_id)
        if not info.get('owned') or info.get('background'):
            raise ValueError('Retopology requires an owned interactive Blender session. Create one with start_blender_session(background=False).')
        return info

    def call(session_id, operation, **options):
        info = owned(session_id)
        request = {'operation': operation, **options}
        code = ('import runpy\nresult=runpy.run_path(' + repr(str(runtime)) +
                ',init_globals={"OPTIONS":' + repr(request) + '})["result"]')
        return rpc(code, port=info['port'], timeout=120)

    def points(value):
        if not 1 <= len(value) <= 10000:
            raise ValueError('Expected 1–10000 vertices')
        if any(len(p) != 3 or any(not math.isfinite(c) for c in p) for p in value):
            raise ValueError('Every vertex must have three finite coordinates')

    @mcp.tool()
    def get_retopology_capabilities(session_id: str = '') -> dict:
        """Describe the actual RetopoFlow adapter and limits; optionally inspect an owned GUI session."""
        description = {
            'status': 'ok', 'adapter_version': '1.0.0',
            'requirements': ['RetopoFlow package directory supplied explicitly', 'owned interactive Blender session', 'new output .blend path'],
            'operations': ['inspect', 'begin', 'add_patch', 'bone_strip', 'select_native_tool', 'projected_laplacian_relax', 'native_undo_redo', 'finish', 'transfer_weights', 'validate_sampled_poses', 'save'],
            'limits': ['No automatic anatomy inference or whole-character retopology',
                       'Native tool selection is supported; mouse-driven strokes are not simulated',
                       'Relax is adapter Laplacian smoothing with native RetopoFlow surface projection, not the native Relax brush',
                       'Pose validation is sampled one-way surface distance, not visual approval or continuous animation validation',
                       'Tested package: RetopoFlow 3.4.10; other versions require runtime verification'],
        }
        if session_id:
            description['runtime'] = call(session_id, 'inspect')
        return description

    @mcp.tool()
    def begin_retopology(session_id: str, source_blend: str, source_object: str,
                         addon_directory: str, output_path: str) -> dict:
        """Append a reference into a clean owned GUI session and start RetopoFlow on a new target. Never opens or saves the original in place."""
        info = owned(session_id)
        if info.get('dirty') or info.get('filepath'):
            raise ValueError('Begin requires a fresh clean owned session with no loaded .blend')
        source = Path(source_blend).resolve(strict=True)
        addon = Path(addon_directory).resolve(strict=True)
        output = Path(output_path).resolve()
        if source.suffix.lower() != '.blend' or output.suffix.lower() != '.blend':
            raise ValueError('Source and output must be .blend files')
        if output.exists() or output == source:
            raise ValueError('Output must be a new path, distinct from the source')
        if addon.name != 'retopoflow' or not (addon / '__init__.py').is_file():
            raise ValueError('addon_directory must name the actual retopoflow package, not a ZIP or parent directory')
        project = state_dir / uuid.uuid4().hex
        project.mkdir()
        return call(session_id, 'begin', source=str(source), source_object=source_object,
                    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), addon=str(addon),
                    output=str(output), stage=str(project / 'working.blend'))

    @mcp.tool()
    def inspect_retopology(session_id: str) -> dict:
        """Read real modal readiness, source/target topology, available native tools and current file."""
        return call(session_id, 'inspect')

    @mcp.tool()
    def add_retopology_patch(session_id: str, vertices: list[list[float]], faces: list[list[int]],
                            max_projection_distance: float = 0.003) -> dict:
        """Append explicit triangles/quads in source-local coordinates, snapped through RetopoFlow. Validates all input before mutation and rolls back patch errors."""
        points(vertices)
        if not faces or len(faces) > 20000:
            raise ValueError('Expected 1–20000 faces')
        if any(len(f) not in (3, 4) or len(set(f)) != len(f) or
               any(isinstance(i, bool) or not 0 <= i < len(vertices) for i in f) for f in faces):
            raise ValueError('Faces must have 3 or 4 distinct valid vertex indices')
        if not math.isfinite(max_projection_distance) or max_projection_distance <= 0:
            raise ValueError('Projection tolerance must be finite and positive, in source-local units')
        return call(session_id, 'add_patch', vertices=vertices, faces=faces,
                    max_projection_distance=max_projection_distance)

    @mcp.tool()
    def build_retopology_bone_strip(session_id: str, rig_object: str, rings: list[dict],
                                    sides: int = 16, max_radius: float = 0.02) -> dict:
        """Build a directed open quad strip around existing bone centers using actual source intersections and RetopoFlow projection/mesh creation. Rings are {bone: name, t: 0..1}; rejects missed or overlong rays before editing."""
        if not 2 <= len(rings) <= 128 or not 4 <= sides <= 64:
            raise ValueError('Expected 2–128 rings and 4–64 sides')
        if len(rings) * sides > 10000 or not math.isfinite(max_radius) or max_radius <= 0:
            raise ValueError('Invalid size or maximum radius')
        for ring in rings:
            if set(ring) != {'bone', 't'} or not isinstance(ring['bone'], str) or not ring['bone']:
                raise ValueError('Each ring must contain only bone (name) and t (0..1)')
            if isinstance(ring['t'], bool) or not isinstance(ring['t'], (int, float)) or not math.isfinite(ring['t']) or not 0 <= ring['t'] <= 1:
                raise ValueError('Ring t must be a finite number from 0 to 1')
        return call(session_id, 'bone_strip', rig=rig_object, rings=rings, sides=sides, max_radius=max_radius)

    @mcp.tool()
    def select_retopology_tool(session_id: str, tool: str) -> dict:
        """Activate one native RetopoFlow tool by its actual displayed name. Does not simulate mouse strokes."""
        return call(session_id, 'select_tool', tool=tool)

    @mcp.tool()
    def relax_retopology(session_id: str, iterations: int = 2, strength: float = 0.2,
                         preserve_boundary: bool = True) -> dict:
        """Laplacian relaxation of the whole target, reprojected through RetopoFlow each pass. This adapter operation is not the native brush; rolls back on failure."""
        if not 1 <= iterations <= 20 or not math.isfinite(strength) or not 0 < strength <= 1:
            raise ValueError('Expected 1–20 iterations and strength in (0,1]')
        return call(session_id, 'relax', iterations=iterations, strength=strength, preserve_boundary=preserve_boundary)

    @mcp.tool()
    def finish_retopology(session_id: str, cancel: bool = False) -> dict:
        """Request native RetopoFlow commit/cancel; poll inspect_retopology until modal_active is false before transfer, validation or save."""
        return call(session_id, 'finish', cancel=cancel)

    @mcp.tool()
    def undo_retopology(session_id: str, redo: bool = False) -> dict:
        """Use native RetopoFlow undo/redo for adapter patches and relaxation while its modal session is active."""
        return call(session_id, 'undo', redo=redo)

    @mcp.tool()
    def transfer_retopology_weights(session_id: str, rig_object: str) -> dict:
        """Transfer the reference's existing vertex weights by nearest-triangle barycentric interpolation to the new target; retains the same rig."""
        return call(session_id, 'transfer_weights', rig=rig_object)

    @mcp.tool()
    def validate_retopology_poses(session_id: str, rig_object: str, poses: list[dict],
                                  sample_limit: int = 2000) -> dict:
        """Evaluate identical existing-rig action/frame samples on source and target. Restores rig/action/frame state. Returns bounded one-way surface-distance and finite checks, not a claim of better animation."""
        if not 1 <= len(poses) <= 32 or not 10 <= sample_limit <= 10000:
            raise ValueError('Expected 1–32 poses and 10–10000 probes')
        for pose in poses:
            if set(pose) != {'action', 'frame'} or not isinstance(pose['action'], str) or not isinstance(pose['frame'], int) or isinstance(pose['frame'], bool):
                raise ValueError('Each pose must contain action (existing name or empty for rest) and integer frame')
        return call(session_id, 'validate_poses', rig=rig_object, poses=poses, sample_limit=sample_limit)

    @mcp.tool()
    def save_retopology_result(session_id: str) -> dict:
        """Publish once to the new .blend path reserved by begin_retopology; verify source SHA256 unchanged. Existing output files are never overwritten."""
        return call(session_id, 'save')
