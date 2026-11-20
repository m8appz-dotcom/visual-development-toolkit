import hashlib,json,pathlib,subprocess,tomllib
ROOT=pathlib.Path('D:/modding-lab');WORK=ROOT/'plugin-maintenance';CONTROL=ROOT/'accurig-control-mcp'
installed=json.loads((WORK/'accurig-bobi-install.json').read_text(encoding='utf-8-sig'))
PLUGIN=pathlib.Path(installed['installedPath'])
contract=json.loads((WORK/'accurig-bobi-contract.json').read_text(encoding='utf-8'))
flow=json.loads((WORK/'accurig-bobi-flow.json').read_text(encoding='utf-8'))
assert contract['passed'] and len(contract['checks']['tools'])==19
assert flow['checks']['connected']['connected'] and flow['checks']['connected']['version']=='2.1.1'
assert flow['checks']['connected']['signed_in'] is False
assert flow['checks']['final_status']['connected'] is False
running=subprocess.check_output(['tasklist','/FI','IMAGENAME eq AccuRIG.exe','/FO','CSV','/NH'],text=True)
assert '"AccuRIG.exe"' not in running
config=tomllib.loads((pathlib.Path.home()/'.codex/config.toml').read_text(encoding='utf-8-sig'))
assert config['plugins']['accurig-control@modding-lab']['enabled'] is True
assert 'accurig-control' not in config.get('mcp_servers',{})
assert config['plugins']['game-modding-toolkit@modding-lab']['enabled'] is True
assert 'accurig-control' not in json.loads((ROOT/'plugins/game-modding-toolkit/mcp.json').read_text())['mcpServers']
old=sorted((CONTROL/'data').glob('registry-before-*.json'),key=lambda p:p.stat().st_mtime)[-1]
after=WORK/'accurig-bobi-final-preferences.json'
subprocess.run([str(ROOT/'windows/venv/Scripts/python.exe'),str(CONTROL/'registry_state.py'),'backup',str(after)],check=True,capture_output=True)
assert json.loads(old.read_text())==json.loads(after.read_text()),'Preferences were not restored'
lock={'host':'bobi-almax','controller_version':'0.2.0','app_version':'2.1.1.603','node':'24.18.0','blender':'5.0.1',
      'files':{str(p.relative_to(CONTROL)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['src','scripts'] for p in (CONTROL/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts}}
(CONTROL/'runtime-lock.json').write_text(json.dumps(lock,indent=2),encoding='utf-8')
summary={'host':'bobi-almax','plugin':'accurig-control@modding-lab','version':'0.2.0','installed':str(PLUGIN),
 'source':str(ROOT/'plugins/accurig-control'),'controller':str(CONTROL),'application':'D:/Applications/Reallusion/AccuRIG/AccuRIG.exe',
 'installation_verified':True,'skill_valid':True,'automatic_selection_enabled':True,'mcp_tools':19,
 'real_application_connection_verified':True,'application_version':'2.1.1','model_inspection':flow['checks'].get('model_inspection'),
 'full_rigging_export_flow_verified':False,'blocker':'Initial Reallusion sign-in required: signed_in=false, MEMBER_AUTH_FAILED and login window; scene preparation did not complete.',
 'user_decision':'Will sign in later; do not retry or monitor automatically.',
 'owned_application_closed':True,'preferences_restored':True,'separate_from_vdt':True,
 'installer':json.loads((WORK/'accurig-full-installer.json').read_text(encoding='utf-8-sig')),
 'backup':json.loads((WORK/'accurig-bobi-deployment.json').read_text())['backup']}
(WORK/'accurig-bobi-result.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
text='''# AccuRIG en Bobi — instalado; prueba completa pendiente de inicio de sesión

Plugin independiente accurig-control@modding-lab0.2.0 instalado y habilitado en Bobi (usuario video). Fuente D:/modding-lab/plugins/accurig-control, instalado C:/Users/video/.codex/plugins/cache/modding-lab/accurig-control/0.2.0. No integrado en Visual Development Toolkit.

Controlador D:/modding-lab/accurig-control-mcp. Utiliza el Node24.18.0 existente, Python local y Blender5.0.1. Dependencias SDK MCP2.3.1/Zod copiadas con sus licencias desde el runtime existente de X, sin copiar cuentas, preferencias, datos ni historial de AccuRIG. Importaciones y rutas del controlador se adaptaron a Bobi; SDK independiente del MCP de reverse engineering y de Docker.

## Acreditado

- AccuRIG2.1.1.603 instalado desde la fuente oficial Reallusion; instalador completo firmado, estado Authenticode Valid y hash en accurig-full-installer.json. El descargador inicial no completó la instalación al acabar su sesión SSH; la instalación con espera confirmó registro y ejecutable real.
- Plugin instalado/activo por CLI y skill válida con selección automática habilitada.
- Sesión MCP real con19herramientas y respuesta de estado.
- Lanzamiento dedicado de la aplicación, conexión con Electron/interfaz, versión2.1.1 y perfil de Bobi.
- Inspección del Pete.obj original de esta instalación correcta. La carga nativa se recibió pero la escena no quedó lista para Rig Body.
- Solo la instancia propia se cerró. No quedan procesos AccuRIG; las siete preferencias respaldadas coinciden tras restaurar.

## Bloqueo real y siguiente acción

Perfil nuevo sin inicio de sesión: signed_in=false, aplicación devuelve MEMBER_AUTH_FAILED y crea su ventana de login. El primer uso requiere autenticación normal; no se copiaron tokens ni se eludió el acceso. No se certifican generación de rig, validación de poses ni exportación en Bobi.

El usuario indicó que iniciará sesión después. No se programó monitor ni repetición automática. Cuando el usuario avise: abrir AccuRIG normalmente en Bobi, iniciar sesión con su cuenta, cerrar la aplicación y volver a ejecutar el flujo MCP mediante accurig_bobi_smoke.py flow. Esa prueba abre una instancia propia, carga Pete, comprueba checkpoint/edición/restauración, genera skin, valida poses y prueba exportación normal. No alterar ni usar historiales ajenos si aparece un límite.

Documentación oficial de instalación: https://manual.reallusion.com/AccuRig-2/2.0/03-introducing-the-user-interface/installation-guide.htm . URL de descarga completa encontrada en el descargador oficial: https://file.reallusion.com/ActorCore_AccRIG/ActorCore_AccuRIG_Setup.exe .

## Evidencia y rollback

En D:/modding-lab/plugin-maintenance: accurig-bobi-contract.json, accurig-bobi-flow.json (fallo conservado), accurig-bobi-result.json, accurig-full-installer.json, accurig-bobi-deployment.json. Respaldo de marketplace/config indicado en deployment.json. runtime-lock.json del controlador registra los archivos adaptados y versiones verificadas.

Para retirar el plugin se puede usar codex plugin remove accurig-control@modding-lab. Verificar cambios posteriores antes de restaurar entradas concretas del marketplace o configuración; no sobreescribir configuraciones completas ni borrar perfiles/historiales. La aplicación instalada no se desinstala por quitar el plugin. No se crearon servicios ni se modificó el contenedor Docker.
'''
(WORK/'ACCURIG-RESULT.md').write_text(text,encoding='utf-8')
(CONTROL/'STATUS.md').write_text('Host Bobi/video. Plugin accurig-control@modding-lab0.2.0 instalado/activo, independiente de VDT. App2.1.1.603 instalada y conexion real MCP19 verificada. Skill automatica valida. Node24.18/Python local/Blender5.0.1 existentes. Prueba Pete se bloqueo: signed_in=false/MEMBER_AUTH_FAILED, escena no preparada. No rig/poses/exportacion acreditados. Usuario iniciara sesion despues; no reintentar ni monitorizar automaticamente. App propia cerrada y7preferencias restauradas. Evidencias y siguiente paso en D:/modding-lab/plugin-maintenance/ACCURIG-RESULT.md y accurig-bobi-result.json. Esperar aviso de usuario tras login y cierre de app; entonces smoke flow.',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ['installer','model_inspection']},indent=2))
