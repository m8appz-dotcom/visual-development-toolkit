"""Prepare host-adapted VDT1.3.0; preserve Bobi's proven MCP launch definitions."""
import hashlib,json,pathlib,shutil,tarfile,re
ROOT=pathlib.Path('D:/visual-development-toolkit');WORK=ROOT/'plugin-maintenance'
STAGE=WORK/'bobi-vdt-1.3.0'
assert not STAGE.exists()
shutil.copytree(ROOT/'plugins/game-modding-toolkit',STAGE)
baseline=json.loads((WORK/'bobi-baseline.json').read_text(encoding='utf-8'))
cfg={'$schema':'https://agent-plugins.org/schemas/1.0.0/mcp.schema.json','mcpServers':baseline['mcp_config']}
(STAGE/'mcp.json').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
# The same engine version has different locally installed extensions. Record the real catalog.
tools=sorted(baseline['servers']['rea']['tools'],key=lambda t:t['name'])
digest=hashlib.sha256(json.dumps(tools,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
skill=STAGE/'skills/reverse-engineer-anything/SKILL.md'
text=skill.read_text(encoding='utf-8').replace('tool_count: 141','tool_count: 125').replace('X / REA 4.1.0 snapshot','Bobi / REA 4.1.0 Docker snapshot')
text=re.sub(r'catalog_digest: "[a-f0-9]+"','catalog_digest: "'+digest+'"',text,count=1)
text=text.replace('The native-only agent helper and its limits are described in','The MCP helper and host-specific limits are described in')
skill.write_text(text,encoding='utf-8')
(STAGE/'skills/reverse-engineer-anything/references/tool-catalog.json').write_text(json.dumps({
 'host':'bobi-almax','engine':'REA 4.1.0','tool_count':len(tools),'catalog_digest':digest,
 'digest_algorithm':'SHA256 of UTF-8 JSON sorted by tool name, sorted object keys, compact separators, ensure_ascii=false; full tools/list descriptors',
 'tools':[t['name'] for t in tools]},indent=2)+'\n',encoding='utf-8')
helper=STAGE/'skills/visual-development-agents/scripts/rea_mcp.py'
text=helper.read_text(encoding='utf-8')
start=text.index('@asynccontextmanager\nasync def connect(')
end=text.index('\ndef input_json():',start)
text=text[:start]+'''# Core fallback is deliberately limited to static JavaScript queries on this REA server.
CORE_JS={'analyze_javascript_application','trace_javascript_semantics','trace_application_feature',
         'compare_application_versions','compare_source_to_bundle','compare_javascript_export_shapes'}
@asynccontextmanager
async def connect(lab_root=None):
 from mcp import ClientSession,StdioServerParameters
 from mcp.client.stdio import stdio_client
 plugin=pathlib.Path(__file__).resolve().parents[3]
 config=json.loads((plugin/'mcp.json').read_text(encoding='utf-8-sig'))['mcpServers']['rea']
 configured=config.get('env',{}).get('MODDING_LAB_ROOT')
 if lab_root is not None and pathlib.Path(lab_root).resolve()!=pathlib.Path(configured).resolve():
  raise ValueError('lab-root differs from this installed plugin; use the correct host plugin.')
 root=pathlib.Path(configured).resolve(strict=True)
 env={**os.environ,**config.get('env',{})}
 args=[a.replace('${PLUGIN_ROOT}',str(plugin)) for a in config['args']]
 log=root/'plugin-maintenance/skill-mcp.log';log.parent.mkdir(parents=True,exist_ok=True)
 with log.open('a',encoding='utf-8') as errlog:
  async with stdio_client(StdioServerParameters(command=config['command'],args=args,env=env),errlog=errlog) as streams:
   async with ClientSession(*streams,read_timeout_seconds=timedelta(seconds=90)) as session:
    await session.initialize();advertised=[];cursor=None
    while True:
     page=await session.list_tools(cursor=cursor);advertised.extend(page.tools);cursor=page.nextCursor
     if not cursor:break
    tools=[t for t in advertised if t.name.startswith('agent_') or t.name in CORE_JS]
    yield AgentConnection(session,tools)
''' +text[end:]
text=text.replace("default=os.environ.get('MODDING_LAB_ROOT','D:/visual-development-toolkit')","default=os.environ.get('MODDING_LAB_ROOT')")
helper.write_text(text,encoding='utf-8')
entry=STAGE/'skills/visual-development-agents/SKILL.md'
text=entry.read_text(encoding='utf-8')
heading='## Disponibilidad por instalación\n\n'
heading+='En Bobi, REA 4.1.0 Docker anuncia 125 herramientas y no incluye la extensión `agent_*` de X. Usa `analyze_javascript_application` y consultas semánticas que anuncie el servidor para análisis estático. Conserva la evidencia retornada; no simules IDs de trabajo persistente, paginación o fragmentos de la capa ausente. El helper del paquete conecta por el mcp.json local, descubre el subconjunto JavaScript disponible y rechaza herramientas ausentes. En X, la capa 0.2 añade 15 herramientas: las secciones sobre trabajos/grafos persistentes solo aplican cuando se anuncien.\n\n'
text=text.replace('## Elegir la operación',heading+'## Elegir la operación',1)
entry.write_text(text,encoding='utf-8')
doc=STAGE/'skills/visual-development-agents/references/local-runtime.md'
doc.write_text('''# Instalación de Bobi y conexión MCP

Host verificado: bobi-almax, usuario video. Raíz activa D:/modding-lab, plugin game-modding-toolkit@modding-lab, runtime Docker en el contenedor existente modding-lab-analysis. D:/visual-development-toolkit es una copia distinta y no determina la instalación activa de Codex.

El mcp.json local conserva sus lanzadores Python existentes: gateway con server/lab_mcp.py, Ghidra y REA con server/docker_mcp.py. No copies los comandos nativos de X ni reinicies el contenedor compartido para una consulta. La versión de REA es4.1.0, pero carece de las15 herramientas agent_ y de export_javascript_application_graph de X.

## Operaciones disponibles

Primero usa las herramientas MCP directas. En esta instalación usa analyze_javascript_application para el árbol seleccionado y trace_javascript_semantics sobre su evidencia si el esquema lo permite. No intentes agent_job_start ni atribuyas persistencia/reanudación de la capa0.2 a este servidor. El catálogo del skill REA es una instantánea de Bobi; las herramientas anunciadas prevalecen.

Si el host no expone REA, scripts/rea_mcp.py abre una conexión MCP stdio real usando el mcp.json de ESTA copia de plugin, incluyendo el transporte Docker existente. No descarga dependencias ni cambia proveedor. Expone las agent_* si existen y un subconjunto de operaciones estáticas JavaScript anunciadas. El modo list permite descubrirlas. Una operación ausente devuelve TOOL_UNAVAILABLE sin ejecutarse.

Con el Python existente D:/modding-lab/windows/venv/Scripts/python.exe ejecuta <skill>/scripts/rea_mcp.py list, session, batch o call <herramienta>. Envía argumentos JSON por stdin, sin TTY ni interpolación de shell. Reutiliza una conexión para operaciones dependientes. batch admite1–32 peticiones {id,tool,arguments}; session usa NDJSON con esos campos y hasta64 peticiones, rechazando IDs duplicados. Conserva meta.session_id para comprobar reutilización. El registro stderr está en D:/modding-lab/plugin-maintenance/skill-mcp.log.

Para un runner Python importa connect de esta carpeta scripts y usa async with connect() as connection. connection.tools es una lista de descriptores, no un diccionario. Comprueba ok/is_error y el contenido estructurado antes de usar evidence_id, conteos o nodos. Guarda la evidencia real para consultas posteriores; no confundas autoridad estática con ejecución.

Las instrucciones de references/graph-workflow.md son condicionales a la presencia de agent_* y no son aplicables a la capa ausente en Bobi. No recrees esa API ni inventes resultados. El control de AccuRIG corresponde a su plugin independiente.
''',encoding='utf-8')
# Prevent an unrelated fallback from automatically starting shared infrastructure.
launcher=STAGE/'server/docker_mcp.py'
text=launcher.read_text(encoding='utf-8')
start=text.index("if state.stdout.strip()!='true':")
end=text.index('mode=sys.argv[1]',start)
text=text[:start]+'''if state.returncode or state.stdout.strip()!='true':
    print('Configured analysis container is not running; no automatic restart performed.',file=sys.stderr)
    sys.exit(2)
'''+text[end:]
launcher.write_text(text,encoding='utf-8')
archive=WORK/'bobi-vdt-1.3.0.tar.gz'
with tarfile.open(archive,'w:gz') as tar:tar.add(STAGE,arcname='game-modding-toolkit')
receipt={'archive':str(archive),'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'version':'1.3.0',
 'root':'D:/modding-lab','rea_tools':125,'agent_extension_available':False,'runtime_config_preserved':True}
(WORK/'bobi-package.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
