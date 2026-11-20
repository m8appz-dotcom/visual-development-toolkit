import ast,hashlib,importlib.util,json,pathlib,subprocess,tomllib
ROOT=pathlib.Path('D:/modding-lab');WORK=ROOT/'plugin-maintenance'
INSTALLED=pathlib.Path(json.loads((WORK/'install.json').read_text(encoding='utf-8-sig'))['installedPath'])
SOURCE=ROOT/'plugins/game-modding-toolkit'
for folder in [SOURCE,INSTALLED]:
    for relative in ['.codex-plugin/plugin.json','plugin.json']:
        p=folder/relative;manifest=json.loads(p.read_text(encoding='utf-8'))
        interface=manifest['interface'] if 'interface' in manifest else manifest['extensions']['com.openai']['interface']
        interface['longDescription']='Analiza aplicaciones y paquetes con REA, Ghidra, ILSpy y extracción Unity. Consulta grafos JavaScript y conserva evidencia verificable. Esta instalación utiliza los analizadores existentes de Bobi mediante Docker.'
        p.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    doc=folder/'skills/visual-development-agents/references/local-runtime.md'
    text=doc.read_text(encoding='utf-8')
    text+='''
## Envoltura de evidencia comprobada

analyze_javascript_application devuelve contenido estructurado con result (grafo y estadísticas), evidence_id y evidence (el registro Evidence completo). Usa result.semantic_graph para inspeccionar nodos y pasa evidence como application a trace_javascript_semantics. No confundas esta envoltura con la respuesta contract_version/ok/result de la capa agent_* de X. La prueba local encontró dos funciones reales y trazó desde un node_id obtenido de ese resultado, sin transcribir IDs.
'''
    doc.write_text(text,encoding='utf-8')
def tree(folder):
    return {str(p.relative_to(folder)):hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
assert tree(SOURCE)==tree(INSTALLED)
spec=importlib.util.spec_from_file_location('v',WORK/'quick_validate.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
for p in (INSTALLED/'skills').iterdir():
    if p.is_dir():assert v.validate_skill(p)[0]
for p in INSTALLED.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
report=json.loads((WORK/'verification.json').read_text(encoding='utf-8'))
assert report['passed'] and not report['failures']
before=report['checks']['gateway']['status']['container']['data']
after=json.loads(subprocess.check_output(['docker','inspect','modding-lab-analysis','--format','{{json .State}}'],text=True))
assert before['StartedAt']==after['StartedAt'] and after['Running']
report['checks']['container_preserved']={'same_started_at':True,'running':True,'healthy':after['Health']['Status']=='healthy'}
report['checks']['final_files']={'source_installed_identical':True,'skills_valid':6,'python_syntax_valid':True,
    'bytes':sum(p.stat().st_size for p in INSTALLED.rglob('*') if p.is_file() and '__pycache__' not in p.parts)}
catalog=json.loads((WORK/'catalog.json').read_text(encoding='utf-8-sig'))
plugin=next(p for p in catalog['installed'] if p['name']=='game-modding-toolkit')
assert plugin['installed'] and plugin['enabled'] and plugin['version']=='1.3.0'
report['checks']['installed_catalog']={'pluginId':plugin['pluginId'],'enabled':True,'version':'1.3.0'}
report['limits']=['Bobi REA125 has no agent_* extension; native X persistence/export capabilities were not installed or claimed.',
    'Six skills validated and representative MCP routes exercised; no independent model response quality evaluation.']
(WORK/'verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
receipt=json.loads((WORK/'deployment.json').read_text())
summary='''# Visual Development Toolkit 1.3.0 en Bobi

Actualización completada en bobi-almax, usuario video. Fuente activa D:/modding-lab/plugins/game-modding-toolkit; instalada en C:/Users/video/.codex/plugins/cache/modding-lab/game-modding-toolkit/1.3.0. La copia D:/visual-development-toolkit no se usó como instalación activa.

Se conservó el mcp.json de Bobi con gateway Windows y Ghidra/REA Docker; no se copiaron rutas nativas de X. El contenedor modding-lab-analysis no se reinició y sigue saludable. Modelos/proveedores existentes conservados. La versión anterior1.1.1 y la configuración están respaldadas.

## Pruebas reales

- Gateway:12 herramientas; rechazo de run_um retirado; creación de proyecto aislado, lectura/listado, reconocimiento y estado de componentes correctos.
- Ghidra:212 herramientas; importación de /bin/true a un proyecto nuevo, análisis, listado de185 funciones, decompilación real de una función y cierre de la sesión propia.
- REA:125 herramientas y catálogo/fingerprint coincidente; análisis de una muestra JavaScript con dos funciones y trazado semántico mediante el helper de la skill en una sola sesión MCP Docker.
- Seis skills pasan quick_validate y el helper empaquetado funciona con el mcp.json de esta instalación. Metadatos permiten selección automática.
- Fuente y archivos instalados coinciden por SHA256, excluyendo caches de bytecode.

## Diferencia importante con X

Bobi no tiene las15 herramientas agent_* ni export_javascript_application_graph del runtime parcheado de X. La skill lo expresa y usa la API JavaScript disponible, sin simular IDs/trabajos persistentes. La extensión avanzada no se instaló en el contenedor compartido. No se afirma igualdad de capacidades entre ambos hosts ni evaluación de respuestas de un modelo independiente.

Los primeros fallos fueron de interpretación del verificador (envoltura de REA y selección del offset de paginación como dirección Ghidra), no fallos del motor. Se conservaron en verification-initial-failed.json y se corrigieron; los recorridos afectados pasaron después. No se repitieron los checks ya correctos del gateway.

## Recuperación

Backup: '''+receipt['backup']+'''

Para revertir, con las sesiones propias detenidas y verificando que no haya cambios posteriores, apartar el paquete nuevo y restaurar plugin-before en la ruta fuente; reinstalar esa versión con codex plugin add game-modding-toolkit@modding-lab. No restaurar ciegamente toda la configuración si hubo cambios posteriores. No reiniciar Docker ni cerrar apps ajenas.

Evidencia: verification.json, deployment.json, install.json, catalog.json y logs en D:/modding-lab/plugin-maintenance. Refrescar plugin/chat para que la sesión de Codex cargue1.3.0; no se reinició la aplicación.
'''
(WORK/'RESULT.md').write_text(summary,encoding='utf-8')
(WORK/'STATUS.md').write_text('Completado: VDT1.3.0 instalado/activo en Bobi. Objetivo/rutas/backup/pruebas y limites en RESULT.md. Gateway12/Ghidra212/REA125,6skills validas,JS2funciones+traza y decompilacion Ghidra reales. Runtime Docker preservado sin reinicio. agent_* no esta instalado y no se simula; skill adaptada a capacidades disponibles. Siguiente: refrescar catalogo de sesion. Evidencia verification.json.',encoding='utf-8')
print(json.dumps({'passed':True,'host':'bobi-almax','version':'1.3.0','skills':6,'tools':{'gateway':12,'ghidra':212,'rea':125},'bytes':report['checks']['final_files']['bytes'],'container_healthy_without_restart':True},indent=2))
