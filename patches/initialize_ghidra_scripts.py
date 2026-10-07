"""Initialize the real Ghidra script BundleHost before PE resource auto-analysis."""
import pathlib,importlib.util
spec=importlib.util.find_spec('ghidra_headless_mcp.backend')
path=pathlib.Path(spec.origin)
source=path.read_text()
needle='            self._started = True\n'
replacement='            from jpype import JClass\n            JClass("ghidra.app.script.GhidraScriptUtil").acquireBundleHostReference()\n            self._script_host_acquired = True\n            self._started = True\n'
assert source.count(needle)==1
source=source.replace(needle,replacement)
shutdown='        self._executor.shutdown(wait=False, cancel_futures=True)\n'
assert source.count(shutdown)==1
source=source.replace(shutdown,shutdown+'        if getattr(self, "_script_host_acquired", False):\n            from jpype import JClass\n            JClass("ghidra.app.script.GhidraScriptUtil").releaseBundleHostReference()\n            self._script_host_acquired = False\n')
path.write_text(source)
print(path)
cli=path.parent/'cli.py'
content=cli.read_text()
needle='    server.serve_stdio()\n    return 0\n'
assert content.count(needle)==1
content=content.replace(needle,'    try:\n        server.serve_stdio()\n        return 0\n    finally:\n        backend.shutdown()\n')
cli.write_text(content)
