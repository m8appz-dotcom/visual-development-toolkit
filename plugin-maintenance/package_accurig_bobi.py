"""Copy only the AccuRIG controller and its skill; adapt paths for Bobi."""
import hashlib,json,pathlib,shutil,tarfile
LAB=pathlib.Path('D:/visual-development-toolkit');WORK=LAB/'plugin-maintenance'
STAGE=WORK/'accurig-bobi-package';assert not STAGE.exists();STAGE.mkdir()
CONTROL=STAGE/'accurig-control-mcp';CONTROL.mkdir()
ORIGINAL=LAB/'accurig-control-mcp'
for rel in ['src','scripts/validate_poses.py','scripts/history_checkpoint.py','registry_state.py','AGENT-WORKFLOW.md','SOURCE-CONTRACT.md','README.md']:
    source=ORIGINAL/rel;dest=CONTROL/rel;dest.parent.mkdir(parents=True,exist_ok=True)
    if source.is_dir():shutil.copytree(source,dest)
    else:shutil.copy2(source,dest)
deps=LAB/'windows/rea/node_modules'
for name in ['@modelcontextprotocol/server','@modelcontextprotocol/core','zod']:
    source=deps/name;dest=CONTROL/'node_modules'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(source,dest)
server=CONTROL/'src/server.mjs';text=server.read_text(encoding='utf-8')
text=text.replace("'file:///D:/visual-development-toolkit/windows/rea/node_modules/@modelcontextprotocol/server/dist/index.mjs'","'@modelcontextprotocol/server'")
text=text.replace("'file:///D:/visual-development-toolkit/windows/rea/node_modules/@modelcontextprotocol/server/dist/stdio.mjs'","'@modelcontextprotocol/server/stdio'")
text=text.replace("'file:///D:/visual-development-toolkit/windows/rea/node_modules/zod/index.js'","'zod'")
server.write_text(text,encoding='utf-8')
for name in ['accurig.mjs','workflow.mjs']:
    p=CONTROL/'src'/name;text=p.read_text(encoding='utf-8')
    text=text.replace("const INSTALL='D:/Applications/Reallusion/AccuRIG';","const INSTALL=process.env.ACCURIG_INSTALL_DIR??'D:/Applications/Reallusion/AccuRIG';")
    text=text.replace("'D:/visual-development-toolkit/windows/venv/Scripts/python.exe'","(process.env.ACCURIG_PYTHON??'D:/modding-lab/windows/venv/Scripts/python.exe')")
    text=text.replace("'D:/CodexTools/Blender/5.2.1-S04/runtime/blender-5.2.1-windows-x64/blender.exe'","(process.env.ACCURIG_BLENDER??'C:/Program Files/Blender Foundation/Blender 5.0/blender.exe')")
    text=text.replace("'C:/Users/kenny/AppData/Local'","'C:/Users/video/AppData/Local'")
    p.write_text(text,encoding='utf-8')
p=CONTROL/'scripts/history_checkpoint.py';text=p.read_text(encoding='utf-8')
text=text.replace('import sqlite3,pathlib,json,sys,shutil,subprocess','import sqlite3,pathlib,json,sys,shutil,subprocess,os')
text=text.replace("root=pathlib.Path('C:/Users/kenny/AppData/Local/Reallusion/ActorCore AccuRIG')","root=pathlib.Path(os.environ['LOCALAPPDATA'])/'Reallusion/ActorCore AccuRIG'")
p.write_text(text,encoding='utf-8')
plugin=STAGE/'accurig-control';shutil.copytree(LAB/'plugins/accurig-control',plugin)
env={'ACCURIG_INSTALL_DIR':'D:/Applications/Reallusion/AccuRIG','ACCURIG_PYTHON':'D:/modding-lab/windows/venv/Scripts/python.exe',
 'ACCURIG_BLENDER':'C:/Program Files/Blender Foundation/Blender 5.0/blender.exe',
 'LOCALAPPDATA':'C:/Users/video/AppData/Local','APPDATA':'C:/Users/video/AppData/Roaming','USERPROFILE':'C:/Users/video','SystemRoot':'C:/Windows'}
cfg={'mcpServers':{'accurig-control':{'type':'stdio','command':'C:/Program Files/nodejs/node.exe',
 'args':['D:/modding-lab/accurig-control-mcp/src/server.mjs'],'env':env}}}
(plugin/'mcp.json').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
(plugin/'skills/accurig-control/references/runtime.md').write_text('''# Runtime de AccuRIG en Bobi

Plugin independiente accurig-control@modding-lab, con selección automática de su skill. Fuente D:/modding-lab/plugins/accurig-control; controlador D:/modding-lab/accurig-control-mcp. Verifica el catálogo local para la copia instalada.

El mcp.json del plugin declara las rutas locales de Node, Python, Blender y AccuRIG. No copies rutas de X. El controlador conserva su propia copia de dependencias MCP2.3.1 y Zod existentes, sin depender del plugin de reverse engineering ni de su contenedor Docker. El bloqueo de versión exige AccuRIG2.1.1. No cambies esa comprobación para una versión no aceptada.

Usa accurig_status y accurig_connect para acreditar el control de la aplicación, no solo el registro del plugin. No cierres una instancia ajena ante APP_IN_USE. El perfil de Bobi es C:/Users/video; nunca copies datos de cuenta, historiales o preferencias de X. La aplicación puede requerir inicio de sesión normal para exportar: informa AUTH_REQUIRED y no eludas ese control.

El modelo de prueba, si la instalación lo incluye, está en D:/Applications/Reallusion/AccuRIG/Sample Character/Pete.obj. No atribuyas a Bobi la aceptación previa de X. Valida las poses con el Blender instalado en Bobi y conserva su resultado real.

El estado y la evidencia de instalación quedan en D:/modding-lab/plugin-maintenance/accurig-bobi-*.json y el estado de trabajo del controlador. Antes de reutilizar un visor verifica su URL y que sirve el GLB final de esta ejecución. Un visor anterior de X no verifica un modelo de Bobi.
''',encoding='utf-8')
license_files=[]
for name in ['@modelcontextprotocol/server','@modelcontextprotocol/core','zod']:
    pkg=json.loads((CONTROL/'node_modules'/name/'package.json').read_text())
    license_files.append({'name':name,'version':pkg['version'],'license':pkg.get('license')})
archive=WORK/'accurig-bobi-package.tar.gz'
with tarfile.open(archive,'w:gz') as tar:
    for p in STAGE.iterdir():tar.add(p,arcname=p.name)
receipt={'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'bytes':archive.stat().st_size,'dependencies':license_files,
 'controller_version':'0.2.0','plugin':'accurig-control@modding-lab','source_host':'X','target_host':'bobi-almax','node_existing':'24.18.0','blender_existing':'5.0.1'}
(WORK/'accurig-bobi-package.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
