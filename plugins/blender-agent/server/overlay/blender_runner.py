"""Runs inside an isolated Blender child, never in the MCP server process."""
import json
import os
from pathlib import Path
import sys
import time
import traceback
import uuid

spec = json.loads(Path(SPEC_PATH).read_text(encoding='utf-8'))
root = Path(spec['state_dir'])
sys.path.insert(0, spec['addon_root'])
from blender_mcp_addon.weak_sandbox import WeakSandboxForLLM


def atomic(path, value):
    temp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(value, default=repr), encoding='utf-8')
    for attempt in range(20):
        try:
            os.replace(temp, path)
            return
        except PermissionError:
            if attempt == 19:
                raise
            time.sleep(.025)


def progress(value):
    atomic(Path(spec['progress_path']), {'value': value, 'updated': time.time()})


def checkpoint():
    import bpy
    path = root / ('checkpoint-' + uuid.uuid4().hex + '.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(path), copy=True)
    atomic(root / 'checkpoint.json', {'path': str(path), 'updated': time.time()})
    return str(path)


namespace = {'result': {}, 'mcp_progress': progress, 'mcp_checkpoint': checkpoint, '__name__': '__mcp_job__'}
try:
    with WeakSandboxForLLM():
        exec(compile(spec['code'], '<blender-mcp>', 'exec'), namespace)
    result = namespace['result']
    if not isinstance(result, dict):
        raise TypeError('Assign a JSON-serializable dict to result')
    # Strict JSON prevents repr() from masquerading as real structured data.
    json.dumps(result, allow_nan=False)
    response = {'status': 'ok', 'result': result}
except BaseException as ex:
    response = {'status': 'error', 'error': {'code': 'BLENDER_PYTHON_ERROR', 'message': str(ex),
                'exception_type': type(ex).__name__, 'traceback': traceback.format_exc()}}
atomic(Path(spec['result_path']), response)
if response['status'] != 'ok':
    raise RuntimeError(response['error']['message'])
