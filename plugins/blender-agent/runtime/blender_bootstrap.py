"""Start the official Blender Lab bridge in an isolated background session."""
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
log = (BASE / 'blender.log').open('a', encoding='utf-8', buffering=1)
sys.stdout = log
sys.stderr = log
sys.path.insert(0, str(BASE / 'official-addon'))
import bpy
from blender_mcp_addon.cli import cli_execute

bpy.app.driver_namespace['codex_mcp_session'] = {
    'owner': 'Codex', 'pid': os.getpid(), 'mode': 'background',
}
print('Codex Blender MCP: isolated background session', flush=True)
cli_execute(['--host', '127.0.0.1', '--port', '9877'])
