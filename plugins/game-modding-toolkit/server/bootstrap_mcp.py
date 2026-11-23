"""Portable plugin entry point; use an existing, explicitly selected runtime."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


def command(service: str, env: dict, interpreter: str = sys.executable) -> tuple[list[str], dict]:
    if service not in {"gateway", "ghidra", "rea"}:
        raise ValueError("Choose gateway, ghidra or rea")
    configured = env.get("MODDING_LAB_ROOT")
    if not configured:
        raise ValueError("Set MODDING_LAB_ROOT to an existing Toolkit runtime; no engines are installed automatically")
    runtime = Path(configured).resolve(strict=True)
    if not runtime.is_dir():
        raise ValueError("The selected runtime must be a directory")
    mode = env.get("MODDING_LAB_MODE") or ("native" if (runtime / "native-runtime.json").is_file() else "docker")
    child_env = {**env, "MODDING_LAB_ROOT": str(runtime), "MODDING_LAB_MODE": mode}
    server = Path(__file__).resolve().parent
    if mode == "native":
        executable = runtime / "windows/venv/Scripts/python.exe"
        if not executable.is_file() or not (runtime / "native-runtime.json").is_file():
            raise ValueError("The selected native runtime is incomplete; preserve it and check its setup")
        return [str(executable), "-B", str(server / "native_mcp.py"), service], child_env
    if mode == "portable" and service == "gateway":
        return [interpreter, "-B", str(server / "lab_mcp.py")], child_env
    if mode != "docker":
        raise ValueError("Portable mode supports only the project gateway")
    # Do not start or recreate services as a side effect of connecting a plugin.
    state = subprocess.run(["docker", "inspect", "modding-lab-analysis", "--format", "{{.State.Running}}"],
                           capture_output=True, text=True, timeout=15,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
    if state.returncode or state.stdout.strip() != "true":
        raise ValueError("The configured Docker runtime is not running; start it deliberately before connecting")
    if service == "gateway":
        return [interpreter, "-B", str(server / "lab_mcp.py")], child_env
    return [interpreter, "-B", str(server / "docker_mcp.py"), service], child_env


if __name__ == "__main__":
    try:
        argv, environment = command(sys.argv[1] if len(sys.argv) == 2 else "", dict(os.environ))
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        child = subprocess.Popen(argv, env=environment, stdin=sys.stdin.buffer,
                                 stdout=sys.stdout.buffer, stderr=sys.stderr.buffer, creationflags=flags)
        try:
            raise SystemExit(child.wait())
        except KeyboardInterrupt:
            child.terminate()
            raise SystemExit(child.wait())
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print("Toolkit MCP: " + str(exc), file=sys.stderr)
        raise SystemExit(2)
