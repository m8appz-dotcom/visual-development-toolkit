import hashlib,json,pathlib,shutil,socket,subprocess,tarfile,time
ROOT=pathlib.Path('D:/modding-lab');WORK=ROOT/'plugin-maintenance';assert socket.gethostname().lower()=='bobi-almax'
receipt=json.loads((WORK/'accurig-bobi-package.json').read_text())
archive=WORK/'accurig-bobi-package.tar.gz'
assert hashlib.sha256(archive.read_bytes()).hexdigest()==receipt['sha256']
targets=[ROOT/'accurig-control-mcp',ROOT/'plugins/accurig-control']
assert all(not p.exists() for p in targets),'Target exists; inspect before replacing'
market=ROOT/'.agents/plugins/marketplace.json';catalog=json.loads(market.read_text())
assert not any(p['name']=='accurig-control' for p in catalog['plugins'])
backup=WORK/'accurig-backups'/str(time.time_ns());backup.mkdir(parents=True)
shutil.copy2(market,backup/'marketplace.json');shutil.copy2(pathlib.Path.home()/'.codex/config.toml',backup/'config.toml')
stage=WORK/('accurig-incoming-'+str(time.time_ns()));stage.mkdir()
with tarfile.open(archive,'r:gz') as tar:
    for m in tar.getmembers():
        assert not m.issym() and not m.islnk() and (stage/m.name).resolve().is_relative_to(stage.resolve())
    tar.extractall(stage,filter='data')
shutil.move(str(stage/'accurig-control-mcp'),str(targets[0]));shutil.move(str(stage/'accurig-control'),str(targets[1]))
catalog['plugins'].append({'name':'accurig-control','source':{'source':'local','path':'./plugins/accurig-control'},
 'policy':{'installation':'AVAILABLE','authentication':'ON_INSTALL'},'category':'Developer Tools'})
market.write_text(json.dumps(catalog,indent=2)+'\n',encoding='utf-8')
out={'host':socket.gethostname(),'plugin':'accurig-control@modding-lab','controller':str(targets[0]),'source':str(targets[1]),'backup':str(backup)}
(WORK/'accurig-bobi-deployment.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
(targets[0]/'STATUS.md').write_text('Instalacion en Bobi: plugin independiente accurig-control, rutas locales Node24.18/Python/Blender5.0.1. Pendiente probar app AccuRIG2.1.1, MCP19 y skill. No copiar cuenta ni historiales de X. Backup y registro en D:/modding-lab/plugin-maintenance/accurig-bobi-*.json.',encoding='utf-8')
print(json.dumps(out,indent=2))
