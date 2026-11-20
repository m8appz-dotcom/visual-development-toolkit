"""Narrow the local VDT plugin to reverse engineering, preserving excluded sources."""
import ast,hashlib,json,pathlib,re,shutil,socket,time,yaml

LAB=pathlib.Path('D:/visual-development-toolkit')
PLUGIN=LAB/'plugins/game-modding-toolkit'
WORK=LAB/'plugin-maintenance'

def write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(text,encoding='utf-8')

def main():
    assert socket.gethostname().lower()=='x'
    manifest_path=PLUGIN/'.codex-plugin/plugin.json'
    assert json.loads(manifest_path.read_text())['version']=='1.2.0'
    backup=WORK/'backups'/str(time.time_ns())
    backup.mkdir(parents=True)
    shutil.copytree(PLUGIN,backup/'source-1.2.0')
    shutil.copy2(pathlib.Path('C:/Users/kenny/.codex/config.toml'),backup/'config.toml')
    original_bytes=sum(p.stat().st_size for p in PLUGIN.rglob('*') if p.is_file())
    # Fix the invalid description even though this workflow is being retired.
    asset=PLUGIN/'skills/asset-pipeline/SKILL.md'
    text=asset.read_text(encoding='utf-8')
    text=re.sub(r'^description: (.*)$',lambda m:'description: '+json.dumps(m[1],ensure_ascii=False),text,count=1,flags=re.M)
    yaml.safe_load(text.split('---',2)[1]);write(asset,text)
    fixed_asset_digest=hashlib.sha256(asset.read_bytes()).hexdigest()
    excluded=['skills/asset-pipeline','skills/fal-assets','skills/game-automation',
              'skills/game-research-websearch','skills/showcase-video','examples','references']
    for relative in excluded:
        item=(PLUGIN/relative).resolve(strict=True)
        assert item.is_relative_to(PLUGIN.resolve()) and item!=PLUGIN.resolve()
        destination=backup/'excluded'/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.move(str(item),str(destination))
    # Remove the callable functions, not just their descriptions or routing.
    gateway=PLUGIN/'server/lab_mcp.py'
    code=gateway.read_text(encoding='utf-8')
    nodes=ast.parse(code);lines=code.splitlines(keepends=True)
    remove={'run_um','windows_game_tool','package_mod','package_project'}
    spans=[]
    for n in nodes.body:
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in remove:
            spans.append((min([n.lineno]+[d.lineno for d in n.decorator_list])-1,n.end_lineno))
    assert len(spans)==4
    for start,end in sorted(spans,reverse=True):del lines[start:end]
    code=''.join(lines).replace('Local Windows MCP gateway. Analysis runs in the dedicated Docker container.',
        'Reverse-engineering MCP gateway; uses the configured native or Docker runtime.')
    code=code.replace('Check the actual Docker engine and all installed analysis and Windows components.',
        'Inspect this host and its configured native or Docker analysis components.')
    code=code.replace('Run REA analysis commands inside Docker. Paths refer to /lab/projects/PROJECT. Full REA MCP tools are also connected separately.',
        'Run allowed REA analysis commands in the configured native or Docker runtime. Prefer the separate REA MCP for supported operations.')
    # Resource generation prerequisites are no longer part of the status contract.
    code=code.replace("'fal_key_available':bool(os.environ.get('FAL_KEY')),'blender_available':bool(shutil.which('blender')),",'')
    ast.parse(code);write(gateway,code)
    # Scope and presentation; preserve the ID and existing attribution fields.
    description='Reverse engineer applications, binaries and packages with REA, Ghidra, ILSpy and Unity asset inspection.'
    interface={'displayName':'Visual Development Toolkit','shortDescription':'Reverse engineering con evidencia',
      'longDescription':'Analiza aplicaciones y paquetes con REA, Ghidra, ILSpy y extracción Unity. Incluye trabajos persistentes, grafos JavaScript/Electron y evidencia verificable. Detecta el runtime local nativo o Docker antes de operar.',
      'defaultPrompt':['Analiza esta aplicación y explica sus funciones con evidencia.','Decompila este artefacto e identifica sus límites de recuperación.','Consulta el grafo JavaScript para seguir una función y sus dependencias.']}
    for path in [manifest_path,PLUGIN/'plugin.json']:
        data=json.loads(path.read_text())
        data['version']='1.3.0';data['description']=description
        target=data['interface'] if 'interface' in data else data['extensions']['com.openai']['interface']
        target.update(interface)
        write(path,json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    write(PLUGIN/'skills/modding-lab/SKILL.md','''---
name: modding-lab
description: "Coordinar ingeniería inversa de aplicaciones y artefactos con los MCP REA, Ghidra, ILSpy y extracción Unity del Visual Development Toolkit. Usar para analizar paquetes distribuidos y recuperar evidencia; no para crear productos ni generar assets."
---

# Visual Development Toolkit: ingeniería inversa

Identifica el artefacto y la pregunta. Usa un proyecto aislado y copias verificadas cuando haga falta importar material. Prefiere el código fuente disponible para preguntas que no requieren decompilación.

Consulta `component_status` solo al necesitar comprobar conexión, host o entorno. El plugin existe en X y Bobi; no deduzcas rutas, Docker o versiones de otra máquina. Lee [references/environments.md](references/environments.md) si el entorno no está establecido.

- Para JavaScript/Electron y consultas persistentes con evidencia, usa `visual-development-agents`.
- Para decidir la ruta REA nativa, administrada, Android, firmware o navegador, usa `reverse-engineer-anything` y sus referencias pertinentes. La existencia de una herramienta no acredita que todos sus proveedores funcionen en este host.
- Usa Ghidra para análisis nativo, ILSpy para ensamblados .NET administrados y AssetStudio para inventario/extracción Unity soportada. ILSpy no recupera código fuente de IL2CPP.
- `recon_game` identifica motores de una carpeta seleccionada sin lanzar el juego. `create_project`, `import_target`, `list_project_files`, `read_project_text` y `verify_originals` conservan entradas, resultados y trazabilidad.
- Prefiere las operaciones del MCP específico a `rea_command`. Este último se mantiene como ruta limitada para operaciones que el MCP específico no cubra.

No presenta generación de assets, automatización genérica, creación de apps ni empaquetado de producto. No edites ejecutables ni reconstruyas un producto por una solicitud de revisión. Distingue evidencia estática, runtime observado, hipótesis e incertidumbres y registra errores por función/artefacto.
''')
    write(PLUGIN/'skills/modding-lab/references/environments.md','''# Entornos de instalación

El plugin está instalado en X y Bobi según el usuario. Eso no hace intercambiables las rutas ni acredita versiones iguales.

- X: comprobado en esta revisión, raíz `D:/visual-development-toolkit`, modo nativo, configuración `native-runtime.json`. El manifiesto local usa `server/native_mcp.py` con Node/Java/Ghidra existentes.
- Bobi: instalación confirmada por el usuario. Documentación previa referencia `D:/modding-lab` y contenedor `modding-lab-analysis`; son antecedentes. Verifica sus `mcp.json`, configuración local y `component_status` antes de aplicar esas rutas o asegurar que Docker siga siendo el modo activo.

Usa primero los MCP expuestos por la instalación actual. No copies el mcp.json de X sobre Bobi: contiene rutas específicas de X. Para una operación en Docker usa las rutas que informe ese runtime, no las rutas nativas del otro equipo. No cambies proveedores, reinstales REA ni descargues latest para resolver descriptores ausentes. Revisa registro y conexión y conserva las reparaciones locales.
''')
    write(PLUGIN/'skills/game-recon/SKILL.md','''---
name: game-recon
description: "Identificar formato, motor y dependencias de una aplicación o juego distribuido antes de su ingeniería inversa. Usar para reconocer el artefacto y elegir analizador; no para crear juegos o generar assets."
---

# Reconocimiento del artefacto

Identifica plataforma, formato, motor, arquitectura y versiones mediante archivos y metadatos. Usa `recon_game` solo para una carpeta de juego Windows seleccionada por el usuario; no lanza el juego. Prefiere las fuentes disponibles cuando basten para la pregunta.

Elige REA para los formatos que soporte el proveedor actual, Ghidra para nativos, ILSpy para .NET administrado y AssetStudio para recursos Unity. Registra ruta, hash y límites; reconoce incertidumbres sin adivinar un motor por nombres de archivo. No conviertas reconocimiento en modificación ni instalación.
''')
    write(PLUGIN/'skills/share-field-notes/SKILL.md','''---
name: share-field-notes
description: "Registrar localmente hallazgos de ingeniería inversa con versiones, fuente, evidencia y límites. Usar para continuidad de una investigación; compartir fuera requiere una solicitud explícita."
---

# Notas de investigación

Usa el estado o notas existentes del proyecto. Registra host y rutas verificadas, versión del artefacto/analizador, hashes, IDs de trabajo, hallazgos sustentados, errores, incógnitas y siguiente paso. Distingue análisis estático de observación de runtime. No envíes dumps, subas contenido ni abras PRs de la base de conocimiento por iniciativa propia.
''')
    # Adapt upstream registration advice to this patched, multi-host installation.
    rea=PLUGIN/'skills/reverse-engineer-anything/SKILL.md';text=rea.read_text(encoding='utf-8')
    start=text.index('When tools are absent or registration is stale:')
    end=text.index('A concrete CLI fallback',start)
    text=text[:start]+'''When tools are absent or registration is stale, inspect this plugin's actual
mcp.json and host-specific runtime first. X and Bobi are separate installations;
read the environment reference in the modding-lab skill before using saved paths.
Preserve the existing patched REA and selected provider. Do not invoke npx latest
or replace the runtime to repair a connection. Reconnect the affected MCP and
check its advertised schemas. A client without tools is distinct from a missing
analysis provider. The native-only agent helper and its limits are described in
visual-development-agents/references/local-runtime.md.

Use the MCP for supported operations. A CLI fallback is conditional on a verified
missing MCP operation or connection failure; the examples below are not authority
to install packages, switch provider, or override user permissions.

'''+text[end:]
    catalog=json.loads((LAB/'reports/vdt-audit-20261021/audit.json').read_text(encoding='utf-8'))['servers']['rea']['tools']
    ordered=sorted(catalog,key=lambda t:t['name'])
    digest=hashlib.sha256(json.dumps(ordered,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    text=text.replace('tool_count: 133','tool_count: '+str(len(catalog)))
    text=re.sub(r'catalog_digest: "[a-f0-9]+"','catalog_digest: "'+digest+'"',text,count=1)
    text=text.replace('  version: "27"','  version: "27"\n  catalog_scope: "X / REA 4.1.0 snapshot; discover schemas per host"')
    write(rea,text)
    write(PLUGIN/'skills/reverse-engineer-anything/references/tool-catalog.json',json.dumps({
        'host':'X','engine':'REA 4.1.0','tool_count':len(catalog),'catalog_digest':digest,
        'digest_algorithm':'SHA256 of UTF-8 JSON sorted by tool name, sorted object keys, compact separators, ensure_ascii=false; full tools/list descriptors',
        'tools':[t['name'] for t in ordered]},indent=2)+'\n')
    # Remove misleading standalone-skill path and isolate historical app context.
    local=PLUGIN/'skills/visual-development-agents/references/local-runtime.md'
    text=local.read_text(encoding='utf-8')
    text=text.replace('sys.path.insert(0, "C:/Users/kenny/.codex/skills/visual-development-agents/scripts")','sys.path.insert(0, "<directorio-real-de-esta-skill>/scripts")')
    text=text.replace('## Helper MCP cuando el host no expone REA','## Helper MCP nativo cuando el host no expone REA\n\nEste helper requiere native-runtime.json y la instalación nativa. No es un adaptador Docker de Bobi. En Bobi usa su MCP registrado y verifica primero su modo; no transfieras la configuración nativa de X.')
    if '## Caso AccuRIG:' in text:text=text[:text.index('## Caso AccuRIG:')]+'''## Reutilizar un proyecto previo

Lee el estado del proyecto concreto y verifica fuente e identidad del trabajo antes de reutilizar su grafo. No elijas una aplicación predeterminada. El control operativo de AccuRIG corresponde a su plugin independiente; esta skill solo analiza artefactos.
'''
    write(local,text)
    write(PLUGIN/'skills/visual-development-agents/agents/openai.yaml','''interface:
  display_name: "Visual Development Agents"
  short_description: "Analiza apps con REA y evidencia verificable"
  default_prompt: "Usa $visual-development-agents para analizar esta aplicación y explicar los hallazgos con evidencia verificable."
dependencies:
  tools:
    - type: "mcp"
      value: "rea"
      description: "Análisis REA y consultas persistentes de grafos"
policy:
  allow_implicit_invocation: true
''')
    report={'host':'X','source':str(PLUGIN),'version':'1.3.0','backup':str(backup),
      'original_source_bytes':original_bytes,'new_source_bytes':sum(p.stat().st_size for p in PLUGIN.rglob('*') if p.is_file()),
      'excluded':excluded,'removed_tools':sorted(remove),'fixed_asset_sha256':fixed_asset_digest,
      'rea_tools':len(catalog),'catalog_digest':digest,'bobi_modified':False}
    write(WORK/'change-receipt.json',json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
