# Instalación local y recuperación de conexión

Estas rutas identifican la instalación verificada en X, perfil `C:/Users/kenny`. Compruébalas antes de usarlas desde otra máquina. El directorio de trabajo del chat puede pertenecer a otro repositorio.

- Toolkit: `D:/visual-development-toolkit`.
- **Repositorio Git de la capa:** `D:/visual-development-toolkit/agent-layer`; rama comprobada `codex/agent-layer`. La raíz del toolkit no es ese repositorio. Para cambios en la capa, verifica Git con `git -C D:/visual-development-toolkit/agent-layer ...`; no deduzcas ausencia de repositorio consultando su directorio padre. En investigaciones de solo lectura no hace falta consultar Git si no afecta a la pregunta.
- Fuentes del plugin: `plugins/game-modding-toolkit`; `mcp.json` declara los servidores `modding-lab`, `ghidra` y `rea`.
- Estado de la capa para agentes: `agent-layer/STATUS.md`; contratos reales guardados: `agent-layer/contracts/mcp-tools-v1.json`.
- Configuración de runtimes: `native-runtime.json` (Node, Java y Ghidra existentes).
- Python: `windows/venv/Scripts/python.exe`.
- REA: `windows/rea/node_modules/rea-agents/scripts/rea.mjs`.

El plugin instalado se llama internamente `game-modding-toolkit@modding-lab`, con nombre visible REA. Su caché instalada y su código fuente son copias distintas. No edites la caché para cambiar esta skill ni reemplaces el paquete REA reparado con una descarga nueva.

Si el servidor está desactivado, usa la configuración o gestión MCP disponible para habilitarlo dentro de la tarea y verificar la conexión. No cambies modelos, cuentas ni proveedores. Si el registro es correcto pero faltan herramientas en la sesión, intenta una conexión MCP nueva; no reinicies aplicaciones en uso.

## Helper MCP nativo cuando el host no expone REA

Este helper requiere native-runtime.json y la instalación nativa. No es un adaptador Docker de Bobi. En Bobi usa su MCP registrado y verifica primero su modo; no transfieras la configuración nativa de X.

Usa primero las herramientas MCP directas. Si el host no las ofrece, explica esa limitación y usa `scripts/rea_mcp.py` con el Python existente. Abre una conexión **MCP stdio real**, descubre herramientas y limita las llamadas a la capa `agent_*`; no usa la CLI de análisis ni instala dependencias. No es un proxy de otros servidores.

```text
D:/visual-development-toolkit/windows/venv/Scripts/python.exe <skill>/scripts/rea_mcp.py list
D:/visual-development-toolkit/windows/venv/Scripts/python.exe <skill>/scripts/rea_mcp.py call agent_capabilities
D:/visual-development-toolkit/windows/venv/Scripts/python.exe <skill>/scripts/rea_mcp.py batch
D:/visual-development-toolkit/windows/venv/Scripts/python.exe <skill>/scripts/rea_mcp.py session
```

Para argumentos, envía un objeto JSON por stdin. Por ejemplo, para estado: `{"job_id":"<identificador existente>"}`. No construyas argumentos con interpolación de shell. `--lab-root` permite indicar otra instalación que hayas verificado explícitamente; no busca equipos ni cambia de host. El helper usa los runtimes configurados y el proveedor Ghidra ya seleccionado en esta instalación para inicializar REA; si la configuración indica otro proveedor, se detiene en vez de sustituirlo. Conserva stderr del servidor en `agent-layer/reports/skill-mcp.log`, sin volcar variables de entorno ni credenciales.

Para varias consultas, **reutiliza una conexión** en vez de lanzar `call` por cada petición:

Prefiere la API Python `connect` para runners. Si usas el modo NDJSON, conecta stdin/stdout mediante pipes **sin PTY/TTY**: el eco y los controles de terminal alteran la presentación del JSON y dificultan capturarlo. Guarda el resultado estructurado antes de imprimir resúmenes; no uses la transcripción de una terminal como sustituto del registro JSON.

- `batch` recibe un array JSON de 1–32 objetos `{"id":"estado","tool":"agent_job_status","arguments":{...}}`. Los ejecuta secuencialmente en una conexión. Un error de herramienta permanece en su resultado y no obliga a repetir los anteriores. Los IDs deben ser únicos. No uses batch para operaciones dependientes de IDs que aún no conoces.
- `session` mantiene una conexión adaptativa por stdin/stdout NDJSON. Lee primero el evento `ready`; envía un objeto con `id`, `tool`, `arguments` por línea y lee una respuesta por línea. Puedes usar un ID obtenido en una respuesta para construir la siguiente petición. Cada respuesta correcta incluye `meta.session_id`, `request_index` y tiempo de consulta. IDs repetidos se rechazan sin volver a ejecutar. Cierra stdin al terminar y espera la salida del proceso. La sesión termina también tras 64 mensajes; no crea servicio ni puerto.
- Para un runner Python, importa `connect` del helper y usa una sola instancia:

```python
import asyncio, sys
sys.path.insert(0, "<directorio-real-de-esta-skill>/scripts")
from rea_mcp import connect

async def main():
    async with connect("D:/visual-development-toolkit") as connection:
        first = await connection.call("agent_capabilities", {})
        # Más consultas adaptativas dentro de este mismo bloque.
        print(first["structured_content"])

asyncio.run(main())
```

Conserva `meta` en el registro de evaluación: permite acreditar reutilización y medir consultas por separado del arranque. No reintentes automáticamente una operación mutante si se pierde la conexión; consulta su trabajo antes de decidir. `call` y `list` siguen disponibles para operaciones aisladas. Los errores de transporte cierran la conexión; no se hace replay.

Antes de agrupar consultas verifica los parámetros en `connection.tools` y sus `inputSchema`. En la capa 0.2, `agent_graph_source_excerpt.max_chars` admite **256–8.000**, con 4.000 por defecto; no admite 10.000. Si un parámetro se rechaza, corrígelo antes de repetirlo en otras peticiones. Este límite de código fuente es independiente de `chunk_chars` para evidencia fragmentada.

Transfiere los IDs desde los resultados estructurados a las consultas dependientes como variables; no transcribas hashes largos desde la terminal. Por ejemplo, dentro de la misma conexión:

```python
async def function_context(connection, job_id, name, module, source_root):
    page = await connection.call("agent_graph_search", {
        "job_id": job_id, "query": name, "kind": "function", "module": module
    })
    if not page["ok"]:
        return page
    matches = [n for n in page["structured_content"]["result"]["items"]
               if n["label"] == name]
    if len(matches) != 1:
        raise ValueError("Inspecciona candidatos y paginación antes de elegir")
    return await connection.call("agent_graph_function_context", {
        "job_id": job_id, "node_id": matches[0]["id"], "source_root": source_root
    })
```

Si `agent_capabilities` no aparece, el helper devuelve `TOOL_UNAVAILABLE`; no basta con que el servidor responda para acreditar la capa 0.2. Revisa registro y errores una vez; no repitas instalación ni análisis a ciegas. La skill no registra por sí sola un servidor MCP.

## Reutilizar un proyecto previo

Lee el estado del proyecto concreto y verifica fuente e identidad del trabajo antes de reutilizar su grafo. No elijas una aplicación predeterminada. El control operativo de AccuRIG corresponde a su plugin independiente; esta skill solo analiza artefactos.
