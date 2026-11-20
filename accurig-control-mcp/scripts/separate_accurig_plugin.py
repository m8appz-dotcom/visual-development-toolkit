"""Undo only the previous VDT addition and prepare a separate local AccuRIG plugin."""
import hashlib, json, pathlib, shutil, socket, time

ROOT = pathlib.Path('D:/visual-development-toolkit/accurig-control-mcp')
LAB = ROOT.parent
TARGET = LAB/'plugins/accurig-control'

def main():
    assert socket.gethostname().lower() == 'x'
    receipt = json.loads((ROOT/'reports/plugin-skill-integration.json').read_text())
    original_backup = pathlib.Path(receipt['backup'])
    assert not TARGET.exists(), 'Separate plugin already exists; inspect first'
    marketplace = LAB/'.agents/plugins/marketplace.json'
    catalog = json.loads(marketplace.read_text(encoding='utf-8-sig'))
    assert not any(p['name']=='accurig-control' for p in catalog['plugins'])
    # Compare original content plus our exact previous changes before restoring it.
    restoration = []
    for index, entry in enumerate(receipt['plugins']):
        plugin = pathlib.Path(entry['plugin']).resolve(strict=True)
        assert plugin.name == '1.2.0' or plugin.name == 'game-modding-toolkit'
        skill = plugin/'skills/accurig-control'
        assert skill.resolve().parent == (plugin/'skills').resolve()
        actual_files = {str(p.relative_to(skill)) for p in skill.rglob('*') if p.is_file()}
        assert actual_files == {f['file'] for f in receipt['files']}
        for file in receipt['files']:
            assert hashlib.sha256((skill/file['file']).read_bytes()).hexdigest() == file['sha256']
        for rel in ['mcp.json','.codex-plugin/plugin.json']:
            old = original_backup/str(index)/rel
            original = json.loads(old.read_text(encoding='utf-8-sig'))
            current = json.loads((plugin/rel).read_text(encoding='utf-8-sig'))
            if rel == 'mcp.json':
                assert 'accurig-control' in current['mcpServers']
                current['mcpServers'].pop('accurig-control')
            else:
                suffix = ' Includes AccuRIG control, joint correction, pose validation and rig export through MCP.'
                assert current['interface']['longDescription'].endswith(suffix)
                current['interface']['longDescription'] = current['interface']['longDescription'][:-len(suffix)]
            assert current == original, 'Other edits exist; preserve them instead of blanket restore'
            restoration.append((old,plugin/rel))
    backup = ROOT/'backups'/('separate-plugin-'+str(time.time_ns()))
    backup.mkdir(parents=True)
    shutil.copy2(marketplace,backup/'marketplace.json')
    shutil.copy2(pathlib.Path('C:/Users/kenny/.codex/config.toml'),backup/'config.toml')
    for index, entry in enumerate(receipt['plugins']):
        plugin = pathlib.Path(entry['plugin'])
        for rel in ['mcp.json','.codex-plugin/plugin.json']:
            dest = backup/str(index)/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(plugin/rel,dest)
        shutil.move(str(plugin/'skills/accurig-control'),str(backup/('removed-vdt-skill-'+str(index))))
    for old,destination in restoration:
        shutil.copy2(old,destination)
    (TARGET/'.codex-plugin').mkdir(parents=True)
    manifest = {'name':'accurig-control','version':'0.2.0',
                'description':'Control AccuRIG through MCP: load models, correct joints, generate rigs, validate poses and export.',
                'skills':'./skills/','mcpServers':'./mcp.json',
                'interface':{'displayName':'AccuRIG','shortDescription':'Rigging y validación de personajes',
                             'longDescription':'Controla AccuRIG mediante su MCP: carga modelos, corrige articulaciones, genera el rig, valida poses y exporta. Incluye la skill accurig-control con selección automática.',
                             'category':'Developer Tools','capabilities':['Read','Write'],
                             'defaultPrompt':['Carga mi modelo en AccuRIG, revisa las articulaciones, valida el rig y expórtalo.']}}
    (TARGET/'.codex-plugin/plugin.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    mcp = {'$schema':'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json','mcpServers':{'accurig-control':{
        'type':'stdio','command':'D:/visual-development-toolkit/windows/node/node-v24.19.0-win-x64/node.exe',
        'args':[str(ROOT/'src/server.mjs')]}}}
    (TARGET/'mcp.json').write_text(json.dumps(mcp,indent=2)+'\n',encoding='utf-8')
    (TARGET/'skills').mkdir()
    shutil.copytree(ROOT/'skills/accurig-control',TARGET/'skills/accurig-control')
    catalog['plugins'].append({'name':'accurig-control','source':{'source':'local','path':'./plugins/accurig-control'},
                               'policy':{'installation':'AVAILABLE','authentication':'ON_INSTALL'},'category':'Developer Tools'})
    marketplace.write_text(json.dumps(catalog,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    # Retire the mistaken integrator so it cannot accidentally be run again.
    obsolete = ROOT/'scripts/integrate_plugin_skill.py'
    if obsolete.exists():
        shutil.move(str(obsolete),str(backup/obsolete.name))
    result = {'plugin':'accurig-control@modding-lab','source':str(TARGET),'backup':str(backup),
              'vdt_original_manifests_restored':True,'vdt_added_skills_removed':True,'standalone_install_pending':True}
    (ROOT/'reports/separate-plugin.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    main()
