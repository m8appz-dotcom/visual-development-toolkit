# AccuRIG Control MCP 0.4.0

Filtro base obligatorio: `accurig_set_base_gate` vincula dictamen y hashes; carga, detección y skin rechazan bases descartadas o no revisadas. Tres regeneraciones Meshy coordinadas por el plugin 3d, después viabilidad Blender y nueva revisión. Ver skills/accurig-control/references/base-model-filter.md. 24 herramientas; clientes abiertos requieren reconexión.

# Histórico del controlador previo

Control local de AccuRIG2.1.1 mediante24 herramientas MCP. Usa los canales y convertidor originales; no modifica EXE/ASAR/DLL, cuentas, licencias ni controles de seguridad.

Plugin independiente `accurig-control@modding-lab`. Su mcp.json apunta a Node24.19.0 y src/server.mjs de este repositorio. No hay una entrada global duplicada ni dependencia del plugin Visual Development Toolkit. Los clientes en memoria deben reconectarse para cargar nuevos esquemas.

Flujo obligatorio: fuente original → importación nativa → detección → inspección/corrección y revisión multivista de articulaciones → skin → validación de todas las mallas y20 movimientos progresivos → revisión visual vinculada al GLB exacto → exportación en staging y reimportación → HTML verificado. No hay bypass de revisión pendiente, rechazo o defectos abiertos.

Contrato completo: [AGENT-WORKFLOW.md](AGENT-WORKFLOW.md). Skill: skills/accurig-control/SKILL.md. Prueba actual y fuentes: FIXES15-STATE.md. Evidencia histórica en reports/; una prueba previa no aprueba otro modelo.

Pruebas: Node `--test tests/workflow.test.mjs tests/build-recovery.test.mjs tests/hardening-v03.test.mjs tests/glb-v03.test.mjs tests/recovery-v03.test.mjs tests/export-v03.test.mjs tests/visual-v03.test.mjs tests/shutdown-v03.test.mjs`; Python tests/validator_contract.py y tests/plugin_contract.py. Los tests unitarios no sustituyen la prueba nativa ni inspección visual. Resultado actual y límites: reports/fixes15-final.json.

Módulos0.3: workflow-v03 (gates y ciclo de vida), joints-quality (anatomía), glb-quality (GLB estricto), integrity (persistencia/manifiestos/publicación), lease (exclusión), build-recovery/session-recovery (recuperación), scripts/validate_poses_v03.py (deformación), scripts/launch_detached.py (Windows independiente).

El build observa progreso/CPU hasta90min sin replay. El recibo de finalización permite recuperación comprobada; offline sólo revisión/validación. Archivar respalda todo; borrar es permanente y requiere una orden explícita para la generación exacta. Las fuentes no se modifican.

Rollback de código: backups/fixes15-20261021. Conservar fuentes, outputs, reports y cambios ajenos. No restaurar preferencias/configuraciones generales sobre cambios posteriores.
