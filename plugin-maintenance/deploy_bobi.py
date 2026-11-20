import ast,hashlib,json,pathlib,shutil,socket,tarfile,time
ROOT=pathlib.Path('D:/modding-lab');WORK=ROOT/'plugin-maintenance';TARGET=ROOT/'plugins/game-modding-toolkit'
assert socket.gethostname().lower()=='bobi-almax'
assert TARGET.resolve().parent==(ROOT/'plugins').resolve()
receipt=json.loads((WORK/'bobi-package.json').read_text())
archive=WORK/'bobi-vdt-1.3.0.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==receipt['sha256']
baseline=json.loads((WORK/'baseline.json').read_text())
assert json.loads((TARGET/'mcp.json').read_text())['mcpServers']==baseline['mcp_config'],'Runtime changed since probe'
old=json.loads((TARGET/'.codex-plugin/plugin.json').read_text());assert old['version']=='1.1.1'
backup=WORK/'backups'/str(time.time_ns());backup.mkdir(parents=True)
config=pathlib.Path.home()/'.codex/config.toml';shutil.copy2(config,backup/'config.toml')
stage=WORK/('incoming-'+str(time.time_ns()));stage.mkdir()
with tarfile.open(archive,'r:gz') as tar:
    for m in tar.getmembers():
        assert not m.issym() and not m.islnk()
        assert (stage/m.name).resolve().is_relative_to(stage.resolve())
    tar.extractall(stage,filter='data')
incoming=stage/'game-modding-toolkit'
assert json.loads((incoming/'mcp.json').read_text())['mcpServers']==baseline['mcp_config']
assert json.loads((incoming/'.codex-plugin/plugin.json').read_text())['version']=='1.3.0'
for p in incoming.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
shutil.move(str(TARGET),str(backup/'plugin-before'))
try:shutil.move(str(incoming),str(TARGET))
except BaseException:
    shutil.move(str(backup/'plugin-before'),str(TARGET));raise
out={'host':socket.gethostname(),'version':'1.3.0','source':str(TARGET),'backup':str(backup),
     'previous_version':old['version'],'mcp_config_preserved':True,'container_restarted':False}
(WORK/'deployment.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
