import importlib.util
from pathlib import Path
import tempfile
import unittest
import runpy
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("plugin_bootstrap", ROOT / "plugins/game-modding-toolkit/server/bootstrap_mcp.py")
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)


class PluginBootstrapTests(unittest.TestCase):
    def test_docker_worker_does_not_restart_a_container_stopped_after_bootstrap(self):
        with patch.dict(bootstrap.os.environ, {"MODDING_LAB_ROOT": str(ROOT)}):
            with patch.object(sys, "argv", ["docker_mcp.py", "ghidra"]):
                with patch.object(bootstrap.subprocess, "run", return_value=bootstrap.subprocess.CompletedProcess([], 0, "false\n", "")) as run:
                    with patch.object(bootstrap.subprocess, "Popen") as popen:
                        with self.assertRaises(SystemExit) as stopped:
                            runpy.run_path(str(ROOT / "plugins/game-modding-toolkit/server/docker_mcp.py"), run_name="__main__")
                        self.assertEqual(stopped.exception.code, 2)
                        self.assertEqual(run.call_count, 1)
                        self.assertEqual(run.call_args.args[0][:2], ["docker", "inspect"])
                        popen.assert_not_called()

    def test_missing_runtime_never_installs_or_launches_an_engine(self):
        with patch.object(bootstrap.subprocess, "run") as run:
            with self.assertRaisesRegex(ValueError, "MODDING_LAB_ROOT"):
                bootstrap.command("gateway", {})
            run.assert_not_called()

    def test_portable_gateway_uses_the_callers_interpreter_and_explicit_root(self):
        with tempfile.TemporaryDirectory() as folder:
            args, env = bootstrap.command("gateway", {"MODDING_LAB_ROOT": folder, "MODDING_LAB_MODE": "portable"}, "configured-python")
            self.assertEqual(args[0], "configured-python")
            self.assertTrue(args[-1].endswith("lab_mcp.py"))
            self.assertEqual(env["MODDING_LAB_ROOT"], str(Path(folder).resolve()))
            with self.assertRaisesRegex(ValueError, "Portable"):
                bootstrap.command("rea", env)

    def test_stopped_docker_is_reported_without_starting_it(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(bootstrap.subprocess, "run", return_value=bootstrap.subprocess.CompletedProcess([], 0, "false\n", "")) as run:
                with self.assertRaisesRegex(ValueError, "not running"):
                    bootstrap.command("gateway", {"MODDING_LAB_ROOT": folder, "MODDING_LAB_MODE": "docker"})
                self.assertEqual(run.call_count, 1)
                self.assertEqual(run.call_args.args[0][:2], ["docker", "inspect"])
