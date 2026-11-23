"""Run the repository MCP gateway with task-only projects and an existing runtime."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]
projects = Path(os.environ["TOOLKIT_DEMO_PROJECTS"]).resolve()
projects.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location(
    "toolkit_case_gateway", SOURCE / "plugins/game-modding-toolkit/server/lab_mcp.py"
)
gateway = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)
# Only this isolated process changes its project root. Installed runtime files remain read-only.
gateway.PROJECTS = projects
gateway.MCP.run()
