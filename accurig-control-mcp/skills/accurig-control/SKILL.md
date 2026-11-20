---
name: accurig-control
description: Controlar AccuRIG con su MCP para importar OBJ/FBX, revisar y corregir articulaciones, generar skin, validar deformaciones y exportar rigs con revisión visual vinculada al archivo exacto.
---

# Control de AccuRIG 0.4

Usa el MCP `accurig-control` para todas las operaciones que cubre. Consulta `accurig_status` y los esquemas reales; no lo sustituyas por IPC directo, CLI ni clics. Lee [references/runtime.md](references/runtime.md) para conexión y rutas. No confundas una prueba anterior con aceptación del modelo actual.

0. Antes de cargar o detectar, aplica el filtro del modelo base del plugin 3d · Rig y movimiento y lee [filtro base](references/base-model-filter.md). Registra el recibo exacto mediante `accurig_set_base_gate`. Descarte o evidencia pendiente bloquean AccuRIG; pasa con advertencia conserva el aviso. Fuente o informes cambiados invalidan el recibo. La base debe tener aptitud real de deformación, no sólo estar cerrada.

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

## Validación externa obligatoria

Antes de aceptar una adaptación anatómica o pasarla a AccuRIG aplica [revisión externa](references/external-visual-review.md): Gemini Flash más reciente disponible verificado, sólo navegador, prompt sencillo y evidencia real. Revisión pendiente, defectos abiertos o aprobación de usuario ausente bloquean el siguiente paso. No confundir malla cerrada con encaje correcto.


## Precedencia explícita del usuario — 24 octubre 2026

La aprobación explícita del usuario para continuar con el modelo exacto prevalece
sobre todos los dictámenes técnicos y visuales del agente o terceros, incluidos
Gemini, advertencias, rechazos y revisiones pendientes. No vuelvas a pedirla ni
inicies otra revisión sólo para cambiar su decisión. Esta sección prevalece sobre
las instrucciones anteriores que bloquean por dictámenes de revisores.

Registra la decisión real ligada al SHA256 de la base y a su alcance:
`actor:user`, `status:approved`, `scope:base_model_accurig`,
`decision_authority:supersedes_reviewer_verdicts`, `message_reference`,
`approval_text`, `evidence_path`, `source_sha256`.
Conserva los informes existentes íntegros y sus observaciones como advertencias;
no los marques resueltos ni inventes una aprobación del tercero. El nuevo recibo
se distingue como `base-gate/user-authority/1`, autoridad `user`, `pass_warning`.

Usa el control ejecutable y después el MCP normal:
`base_gate.py approve-user --input BASE.fbx --approval APROBACION.json --receipt RECIBO.json --retain-report INFORME.json`
`accurig_set_base_gate(receipt_path=RECIBO.json)`

La autorización sólo vale para ese archivo y fase. Cambiar la base o evidencias
invalida el recibo. No permite ignorar errores reales de ejecución, archivos
corruptos, restricciones del proveedor, cambiar identidades ni ampliar el alcance.
La decisión de pasar la base no declara correcto un rig que aún no se ha generado.
