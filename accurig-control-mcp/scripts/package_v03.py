"""Update only this plugin's documentation and manifest; preserve historical reports."""
from pathlib import Path
import json, hashlib, shutil
ROOT=Path(__file__).resolve().parents[1]
PLUGIN=Path('D:/visual-development-toolkit/plugins/accurig-control')
skill='''---
name: accurig-control
description: Controlar AccuRIG con su MCP para importar OBJ/FBX, revisar y corregir articulaciones, generar skin, validar deformaciones y exportar rigs con revisión visual vinculada al archivo exacto.
---

# Control de AccuRIG 0.3

Usa el MCP `accurig-control` para todas las operaciones que cubre. Consulta `accurig_status` y los esquemas reales; no lo sustituyas por IPC directo, CLI ni clics. Lee [references/runtime.md](references/runtime.md) para conexión y rutas. No confundas una prueba anterior con aceptación del modelo actual.

1. Verifica la fuente original, su identidad, el alcance autorizado y el destino. `accurig_inspect_model` inspecciona OBJ; FBX requiere carga nativa. No alteres malla, textura o proporciones para silenciar avisos.
2. `accurig_connect` inicia una instancia propia sin foco. `APP_IN_USE` no autoriza cerrar otra. La sesión nueva borra modelo, revisión visual, calibración y privilegios heredados. Si existe una sesión propia cuyo controlador terminó, `resume_owned_session:true` verifica proceso, nonce y lease antes de reanexar; no hereda un modelo aceptado.
3. Si `FBX_TEMP_PROTECTION` bloquea la importación, usa `accurig_prepare_import_workspace` sólo en sesión vacía: respalda todos los archivos con manifiesto verificado antes de aislar temporales. No borres temporales ajenos. Carga con `accurig_load_model` y espera completed.
4. Detecta cuerpo/manos según anatomía real con `accurig_detect_joints`. `body:false` conserva el cuerpo. Elige dedos y simetría explícitamente; no impongas simetría ni cinco dedos.
5. Lee `accurig_inspect_rig`, guarda checkpoint y revisa marcadores delante, ambos lados, espalda y manos. Los errores anatómicos duros bloquean skin. Corrige únicamente lo observado con `accurig_edit_joints`, revisión actual y espacio `accurig_native_model`. El controlador verifica posición, quaternion y máscara y verifica también un rollback. Si no puede verificarlo, bloquea la sesión.
6. Registra la revisión real con `accurig_review_joints`, hash exacto, expected_revision, vistas y observaciones. Aceptar articulaciones no aprueba pesos. `accurig_build_skin` conserva las correcciones; no redetectes después. La operación de compatibilidad `accurig_generate_rig` no evita esta revisión obligatoria.
7. Espera la generación mediante `accurig_job_status`. El build admite 90 minutos y observa progreso y CPU sin repetir ni cancelar por timeout. CPU activa no prueba que haya terminado. Ante uncertain/interrupted usa `accurig_reconcile_session`, opcional recovery_job_id; nunca repitas la generación sin comprobar su resultado.
8. Ejecuta `accurig_validate_rig`: estructura, deformación y visual son estados separados. Comprueba todas las mallas, pesos, matrices, piezas estáticas, dedos y 20 movimientos con tres grados de flexión. Un fallo estructural o de deformación bloquea exportación. needs_review necesita inspección concreta; no equivale a aprobación.
9. Revisa el GLB real en HTML interactivo: frente, perfiles, espalda, ambas manos y todos los movimientos del informe, también durante la transición. Compara rostro, ropa y proporciones con el original. Sigue las referencias visuales del usuario. Registra sólo lo observado mediante `accurig_record_visual_review`, generación/hash exactos, todas las poses y defectos abiertos. Rechazo, revisión pendiente o cambios posteriores bloquean exportación. No existe bypass allow_needs_review.
10. Exporta a ruta nueva con `accurig_export_fbx`, target, mode y avatar explícitos. El MCP comprueba fuente, actor, avatar y revisión, exporta a staging, reimporta y valida el FBX antes de publicar FBX/GLB/recibo exclusivos. Un staging rechazado no es una entrega. MeshOnly/Blender es el preset ejercitado; otros destinos requieren su propia aceptación.
11. Entrega siempre el HTML con el modelo real, giro y zoom verificados en navegador; identifica un ensayo rechazado. No sustituyas el visor por capturas ni ZIP. `accurig_close_session` solicita salida, desconecta CDP, verifica PID y restaura preferencias. Si el SDK deja un proceso residual, sólo termina su PID propio revalidado y sin build pendiente. `recover_owned_session:true` permite completar ese cierre tras terminar su controlador anterior; nunca cierra una app ajena.

## Recuperación y límites

Comprueba `ok:false` y estado final: transporte exitoso y job_id no significan éxito. Una revisión distinta exige releer el estado, no cambiar sólo el número. Fuente, revisión, actor, GLB, avatar e informe están vinculados; cualquier cambio invalida aceptación.

El recibo de finalización se escribe automáticamente. La recuperación verifica fuente, eventos, actor, historial y hashes sin regenerar. Tras cerrar la app, recuperación offline sólo autoriza preview/validación, nunca exportación nativa. Sin prueba de procedencia permanece bloqueado. El lease rechaza controladores concurrentes. El lanzamiento independiente de Windows permite conservar un cálculo aunque cierre el cliente; comprueba siempre el proceso real.

Archivar requiere respaldo completo verificado. Borrar requiere una orden explícita sobre la generación exacta: `accurig_delete_generation` confirma dos veces el ID y verifica todas las copias; conserva fuentes e historiales ajenos. Lee [references/advanced.md](references/advanced.md). No toques un ZIP protegido por el usuario.

Los umbrales son filtros de ingeniería, no una certificación anatómica. Conserva observaciones, límites y evidencia del archivo concreto. No inventes revisión humana ni transfieras aprobación entre modelos o generaciones.
'''
(ROOT/'skills/accurig-control/SKILL.md').write_text(skill,encoding='utf-8')
runtime='''# Runtime y evidencia local

Plugin independiente `accurig-control@modding-lab`, versión0.3.0, 23 herramientas; no forma parte de Visual Development Toolkit. Namespace `mcp__accurig_control`. Los esquemas conectados son la autoridad.

Fuente del plugin: D:/visual-development-toolkit/plugins/accurig-control.
Controlador: D:/visual-development-toolkit/accurig-control-mcp/src/server.mjs.
Node: D:/visual-development-toolkit/windows/node/node-v24.19.0-win-x64/node.exe.
AccuRIG2.1.1 / Electron14.2.9, Blender5.2.1, dependencias existentes. Comprueba host, ejecutables y copias activas antes de operar.

Lee FIXES15-STATE.md para la tarea actual y reports/ para evidencia; STATUS.md incluye antecedentes que no acreditan aceptación vigente. Contrato actual: AGENT-WORKFLOW.md. Los clientes ya cargados requieren reconexión para tomar esquemas nuevos, sin reiniciar una app ajena ni repetir operaciones activas.

Rollback de código: backups/fixes15-20261021. Conservar outputs/reports, recibos y fuentes. No restaurar config.toml completo ni otros plugins sobre cambios posteriores. El rollback de código no revierte una eliminación explícita de historial.
'''
(ROOT/'skills/accurig-control/references/runtime.md').write_text(runtime,encoding='utf-8')
advanced=(ROOT/'skills/accurig-control/references/advanced.md').read_text(encoding='utf-8')
advanced=advanced.split('\n## Contrato0.3',1)[0].rstrip()+'\n'
advanced+='''
## Contrato0.3
La espera prolongada no certifica calidad. El recibo automático vincula fuente/actor/hashes/eventos. Reanexar requiere que el controlador anterior haya terminado y que proceso, ejecutable, fecha, puertos loopback, nonce y lease coincidan. No se repite la operación. Offline nunca permite exportación nativa.

El archivo conserva todos los archivos (no sólo FBX/GLB) y la fila de historial, con manifiesto verificado. La eliminación permanente es otra herramienta y exige autorización explícita del usuario sobre esa generación; IDs dobles no sustituyen esa autorización.

No existe exportación excepcional para omitir revisión visual. Aceptación exige todas las poses y vistas del informe actual. Un rechazo puede detenerse en el primer defecto y registrar sólo lo observado, sin inventar cobertura. Cambios en fuente, geometría, avatar, calibración, revisión o informe invalidan la aceptación.
'''
(ROOT/'skills/accurig-control/references/advanced.md').write_text(advanced,encoding='utf-8')
(ROOT/'AGENT-WORKFLOW.md').write_text('# Contrato operativo 0.3\n\n'+skill.split('# Control de AccuRIG 0.3',1)[1],encoding='utf-8')
(ROOT/'README.md').write_text('''# AccuRIG Control MCP 0.3.0

Control local de AccuRIG2.1.1 mediante23 herramientas MCP. Usa los canales y convertidor originales; no modifica EXE/ASAR/DLL, cuentas, licencias ni controles de seguridad.

Plugin independiente `accurig-control@modding-lab`. Su mcp.json apunta a Node24.19.0 y src/server.mjs de este repositorio. No hay una entrada global duplicada ni dependencia del plugin Visual Development Toolkit. Los clientes en memoria deben reconectarse para cargar nuevos esquemas.

Flujo obligatorio: fuente original → importación nativa → detección → inspección/corrección y revisión multivista de articulaciones → skin → validación de todas las mallas y20 movimientos progresivos → revisión visual vinculada al GLB exacto → exportación en staging y reimportación → HTML verificado. No hay bypass de revisión pendiente, rechazo o defectos abiertos.

Contrato completo: [AGENT-WORKFLOW.md](AGENT-WORKFLOW.md). Skill: skills/accurig-control/SKILL.md. Prueba actual y fuentes: FIXES15-STATE.md. Evidencia histórica en reports/; una prueba previa no aprueba otro modelo.

Pruebas: Node `--test tests/workflow.test.mjs tests/build-recovery.test.mjs tests/hardening-v03.test.mjs tests/glb-v03.test.mjs tests/recovery-v03.test.mjs tests/export-v03.test.mjs tests/visual-v03.test.mjs tests/shutdown-v03.test.mjs`; Python tests/validator_contract.py y tests/plugin_contract.py. Los tests unitarios no sustituyen la prueba nativa ni inspección visual. Resultado actual y límites: reports/fixes15-final.json.

Módulos0.3: workflow-v03 (gates y ciclo de vida), joints-quality (anatomía), glb-quality (GLB estricto), integrity (persistencia/manifiestos/publicación), lease (exclusión), build-recovery/session-recovery (recuperación), scripts/validate_poses_v03.py (deformación), scripts/launch_detached.py (Windows independiente).

El build observa progreso/CPU hasta90min sin replay. El recibo de finalización permite recuperación comprobada; offline sólo revisión/validación. Archivar respalda todo; borrar es permanente y requiere una orden explícita para la generación exacta. Las fuentes no se modifican.

Rollback de código: backups/fixes15-20261021. Conservar fuentes, outputs, reports y cambios ajenos. No restaurar preferencias/configuraciones generales sobre cambios posteriores.
''',encoding='utf-8')
manifest=PLUGIN/'.codex-plugin/plugin.json'
m=json.loads(manifest.read_text(encoding='utf-8'));m['version']='0.3.0';manifest.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
shutil.copytree(ROOT/'skills/accurig-control',PLUGIN/'skills/accurig-control',dirs_exist_ok=True)
lock=json.loads((ROOT/'runtime-lock.json').read_text(encoding='utf-8'))
files=list((ROOT/'src').glob('*.mjs'))+list((ROOT/'scripts').glob('*.py'))+[ROOT/'registry_state.py']
lock['control_sources']={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
lock.update(control_version='0.3.0',tools=23)
(ROOT/'runtime-lock.json').write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8')
print('Canonical plugin0.3/docs/hash lock updated; no installed client restarted.')
