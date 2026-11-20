import json
import os
from pathlib import Path
import sys

spec = json.loads(Path(SPEC_PATH).read_text(encoding='utf-8'))
log = open(spec['log'], 'a', encoding='utf-8', buffering=1)
sys.stdout = log
sys.stderr = log
sys.path.insert(0, spec['addon_root'])
import bpy
from blender_mcp_addon import mcp_to_blender_server, execute_interactive, execute_blocking

bpy.app.driver_namespace['codex_mcp_session'] = {'owner': 'Codex', 'pid': os.getpid(), 'session_id': spec['session_id'], 'mode': 'background' if bpy.app.background else 'interactive'}
mcp_to_blender_server.start('127.0.0.1', spec['port'])
if bpy.app.background:
    execute_blocking.run()
else:
    mcp_to_blender_server.timer_internal_vars_calc(active=.05, idle=.1, idle_delay=5)
    bpy.app.timers.register(execute_interactive.run, first_interval=.05, persistent=True)
