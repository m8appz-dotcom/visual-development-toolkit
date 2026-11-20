# Procedencia y licencias

Blender Lab MCP y add-on: GPL-3.0-or-later, Blender Authors, repositorio https://projects.blender.org/lab/blender_mcp . Add-on fijado al commit 5181fa06d5c601e910eb680a0012d20d1203b8d5; servidor proveniente de la extensión instalada v1.0.1/pyproject1.0.0. Sus fuentes Python/documentación y cabeceras originales se incluyen en server/upstream y runtime/official-addon.

Overlay local modificado: CLI, errores, sesiones, jobs, transacciones, render y guía; fuentes completas en server/overlay. Cambio portable: ruta BUNDLE configurable mediante entorno. Lanzador e instalador en este paquete. Distribuidos bajo GPL-3.0-or-later; texto en LICENSE.txt.

Blender es un runtime externo íntegro, no se incrusta ni modifica el binario dentro del plugin. El instalador usa el ZIP oficial fijado por SHA256 o reutiliza el runtime compatible verificado. Conserva sus licencias. Fuente oficial correspondiente: https://projects.blender.org/blender/blender/src/tag/v5.2.1 y https://download.blender.org/source/ . Runtime lock: runtime/blender-lock.json. No se incluye credencial, .venv ni estado de usuario.
