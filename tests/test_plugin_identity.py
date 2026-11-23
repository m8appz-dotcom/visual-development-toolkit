"""Regressions found by installing the plugin in a fresh real Codex client."""
import importlib.util,json,os,pathlib,subprocess,sys,tempfile,unittest,venv,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('configure_plugin',ROOT/'configure_plugin.py')
configure=importlib.util.module_from_spec(spec);spec.loader.exec_module(configure)

class PluginIdentityTests(unittest.TestCase):
    def test_canonical_and_compatibility_identity_match(self):
        p=ROOT/'plugins/game-modding-toolkit'
        canonical=json.loads((p/'plugin.json').read_text())
        legacy=json.loads((p/'.codex-plugin/plugin.json').read_text())
        for key in ('name','version','description','author'):
            self.assertEqual(canonical[key],legacy[key])
        self.assertEqual(canonical['extensions']['com.openai']['interface'],legacy['interface'])

    def test_private_setup_keeps_portable_command_and_binds_existing_interpreter(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory); plugin=root/'plugin';plugin.mkdir()
            path=plugin/'mcp.json'
            path.write_bytes((ROOT/'plugins/game-modding-toolkit/mcp.json').read_bytes())
            result=configure.configure(root,plugin_root=plugin,python=sys.executable,mode='portable')
            for server in result['mcpServers'].values():
                self.assertEqual(server['command'],pathlib.Path(sys.executable).absolute().name)
                self.assertFalse(pathlib.Path(server['command']).is_absolute())
                self.assertEqual(server['env']['MODDING_LAB_MODE'],'portable')
                self.assertTrue(server['env']['PATH'].startswith(str(pathlib.Path(sys.executable).absolute().parent)))

    @unittest.skipIf(os.name=='nt','Symlink venv acceptance runs on Linux CI')
    def test_selected_symlinked_venv_really_runs_inside_that_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root=pathlib.Path(directory);environment=root/'selected-venv'
            venv.EnvBuilder(with_pip=False,symlinks=True).create(environment)
            selected=environment/'bin/python'
            self.assertTrue(selected.is_symlink())
            plugin=root/'plugin';plugin.mkdir()
            (plugin/'mcp.json').write_bytes((ROOT/'plugins/game-modding-toolkit/mcp.json').read_bytes())
            server=configure.configure(root,plugin_root=plugin,python=selected,mode='portable')['mcpServers']['modding-lab']
            check=subprocess.run([server['command'],'-c','import sys;print(sys.prefix)'],env={**os.environ,**server['env']},check=True,capture_output=True,text=True)
            self.assertEqual(pathlib.Path(check.stdout.strip()),environment)

    def test_download_package_includes_canonical_manifest_and_runtime_setup(self):
        with zipfile.ZipFile(ROOT/'demo/public/assets/app-bridge/toolkit-codex-plugin.zip') as package:
            canonical=json.loads(package.read('plugin.json'))
            legacy=json.loads(package.read('.codex-plugin/plugin.json'))
            self.assertEqual(canonical['version'],legacy['version'])
            self.assertIn('configure_runtime.py',package.namelist())
