# Filtro del modelo base antes de AccuRIG

Obligatorio antes de importar, detectar o generar skin. La imagen aprobada y una malla cerrada no acreditan aptitud para animación. Esta fase usa Blender MCP para medir y el HTML del modelo real para revisión visual. No cambia el cuerpo ni genera imágenes por iniciativa propia.

## Tres resultados

- **Descarte total — pide realizar cambios** (`discard`): identidad o anatomía incorrectas, dedos fusionados/sin separación suficiente, pose que impide colocar articulaciones, defectos que requieren reconstrucción, o evidencia incompleta. Bloquea AccuRIG. Entrega defectos concretos, zona y criterio para el siguiente intento; no pide una confirmación redundante si regenerar ya está autorizado.
- **Pasa con advertencia** (`pass_warning`): sólo defectos no bloqueantes, con motivo, impacto y mitigación escritos. No admite fallos conocidos de deformación, identidad, separación de dedos o recursos imprescindibles como simples advertencias. El aviso acompaña la importación; no equivale a aprobación final del rig.
- **Pasa total** (`pass_total`): todas las comprobaciones pasaron con evidencia suficiente, sin advertencias. Significa aptitud de la base; los pesos y animaciones deben aprobar sus propias pruebas después.

## Evaluación real

Preserva la fuente 3D y referencias originales. Blender MCP lee coordenadas finitas, mallas, componentes, caras degeneradas, bordes abiertos/no manifold, UV y recursos. Inspecciona pose A/T, zona de axilas, volumen de hombros, dedos separados, pulgar, pivotes colocables y distribución de geometría donde doblará. Una malla de triángulos puede ser válida: ni un número de polígonos ni ausencia de agujeros aprueban topología de deformación.

Revisión visual real de frente, ambos lados, espalda y ambas manos, con zoom; documenta qué no pudo observarse. `hands` debe acreditar ambas manos mediante imágenes adicionales o una vista que las muestre realmente. Evalúa identidad, proporciones, hombros, manos, separación de dedos y materiales contra originales, considerando luz/cámara. Rechazo puede terminar al hallar un defecto; el resto se registra `unverified`, nunca `passed`. Para pasar, todos los controles y las vistas deben estar completos. Usa los prompts de revisión vigentes y respeta la elección del evaluador del usuario; no impongas Gemini si fue excluido.

## Rehacer en Meshy: delegación y límite

Tras descarte, el coordinador encarga a **otro agente** un intento concreto en Meshy. Esta skill autoriza esa delegación; un trabajador de generación y un auditor se usan secuencialmente, sin delegación anidada. El trabajador no aprueba su salida. Antes de cada envío reserva el intento en el mismo caso, con ID real del agente y brief autosuficiente: originales autorizados, cuenta/proveedor/modelo vigentes, identidad a preservar, defectos observados y criterios de aceptación. Comprueba documentación oficial vigente antes de llamar a Meshy. Usa su MCP si existe; si no cubre la operación, documenta el límite y usa la sesión del navegador autorizada según reglas locales.

Máximo **tres regeneraciones**, además de la base inicial. Reserva antes de enviar para que una desconexión no produzca duplicados. Conserva ID real del trabajo Meshy, archivo original descargado y dictamen de cada intento. Evalúa cada salida antes de otra. No reinicies el contador cambiando nombre, chat, carpeta o fase; reutiliza el caso y su historial. Un intento reservado o fallido también consume cupo de forma conservadora. No vuelvas a enviar uno pendiente sin reconciliar el trabajo real. No se autoriza cambiar proveedor, modelo elegido, comprar créditos ni superar cuotas.

Si un intento pasa, se detiene la regeneración y se usa ese archivo. Si las tres fallan, **no hay cuarto intento automático**.

## Después de tres fallos: viabilidad en Blender

El agente auditor evalúa si una corrección local puede dar un buen resultado conservando identidad, proporciones, UV y texturas. Propone operaciones concretas: separar/reconstruir dedos, retopología local de articulaciones, corregir intersecciones, etc. Distingue reparar base de pintar pesos, que aún no existen. Registra `feasible`, motivo, operaciones y preservación de identidad para el hash concreto.

Si es viable, el implementador corrige una **copia nueva mediante Blender MCP**, conserva rollback y vuelve a pasar el filtro completo sobre esa copia. La viabilidad no permite entrar directamente a AccuRIG. Si no es viable, bloquea y presenta los cambios necesarios o la decisión material pendiente; no sustituye silenciosamente el cuerpo por otro personaje.

## Control ejecutable

`scripts/base_gate.py` conserva caso, tres reservas, salidas, informes y hashes. No es un evaluador de visión ni ejecuta Meshy automáticamente; el coordinador debe realizar la delegación y recibir el resultado real. Sus comandos son:

```text
base_gate.py init --case CASO.json --input ORIGINAL.fbx --reference REFERENCIA.png --builder ID_COORDINADOR
base_gate.py review --case CASO.json --input CANDIDATO.fbx --technical TECNICO.json --visual VISUAL.json
base_gate.py reserve-meshy --case CASO.json --worker ID_AGENTE --brief BRIEF.md
base_gate.py finish-meshy --case CASO.json --attempt ID_RESERVA --provider-job ID_MESHY --output NUEVO.fbx
base_gate.py finish-meshy --case CASO.json --attempt ID_RESERVA --provider-job ID_ERROR_REAL --error DESCRIPCION
base_gate.py blender --case CASO.json --report VIABILIDAD.json
base_gate.py blender --case CASO.json --report VIABILIDAD.json --output CORREGIDO.fbx
base_gate.py assert --receipt RECIBO.json --input CANDIDATO.fbx
base_gate.py status --case CASO.json
```

Rutas absolutas; no ZIP como fuente/evidencia. Fuente, referencias y archivos de evidencia deben conservar sus hashes. `init` sobre el mismo caso no reinicia intentos. Guarda el caso en el estado breve del proyecto y no lo recrees. No inventes IDs, inspección ni dictámenes. El auditor técnico debe ser distinto del coordinador/constructor.

Ambos informes llevan `source_sha256`, `reviewer_id` y `checks`, un objeto por control con `status` (`passed`, `warning`, `failed`, `unverified`) y `observation` concreta. Una advertencia necesita `rig_blocking` booleano y `mitigation`. Controles técnicos: `geometry`, `pose`, `shoulders`, `hands`, `finger_separation`, `deformation_topology`, `uv_textures`; métricas técnicas `vertices`, `triangles`, `finite_positions`; `dependencies` inventaría todos los archivos externos observados (vacío sólo para recursos autocontenidos). Controles visuales: `identity`, `proportions`, `shoulders`, `hands`, `finger_separation`, `materials`; `evidence` asigna `front`, `left`, `right`, `back`, `hands` a imágenes reales y distintas. Añade evidencia para cada mano cuando haga falta. No rellenes valores sin inspección.

Para iniciar las fases existentes, `gate.py init` exige además `--base-receipt` y `--base-input`. Toda comprobación de fase vuelve a verificar ese recibo. En AccuRIG MCP usa `accurig_set_base_gate(receipt_path=...)` antes de `accurig_load_model`. La carga y `accurig_build_skin` verifican fuente, dictamen y evidencia de nuevo; ni `accurig_generate_rig` evita el filtro. Reconectar no hereda aceptación de otra base.

Un control de archivos no autentica por sí solo que un agente miró el modelo: las observaciones y sesiones reales siguen siendo obligatorias. No transfieras la aceptación del original a una regeneración o reparación.

## Recibo v2: tercero y usuario obligatorios

Aplica [revisión externa](external-visual-review.md). Para pasar, el informe visual
incluye `external_review_path` y `user_approval_path`, rutas a JSON internos, nunca
texto de aprobación fabricado. Consulta `scripts/external_review.py` para el contrato.
El informe externo `gemini-browser-review/1` conserva provider Gemini, transport browser,
source_sha256, reviewer_id externo, account_verified, model_selection (selected,
available_flash_models, latest_available_verified), session_url real de conversación,
selector_evidence, response_evidence, prompt_path, raw_response_path, reviewed_images
(ruta:sha256), status, findings y limitations. No inventes nombres futuros de modelo.
`passed` requiere cero hallazgos y ninguna limitación de cobertura; hallazgos exigen una
nueva revisión, no marcar el informe anterior como resuelto. La aprobación del usuario
incluye source_sha256, actor user, status approved, message_reference, approval_text y
evidence_path. Guarda evidencias del mensaje real; el agente no puede concederla.

Se añade control técnico y visual `wrist_transition`. Evidencias obligatorias: front,
left, right, back, hands y left_wrist_front/profile/palm/back y right_wrist_front/profile/palm/back
(cada clave expandida individualmente), siempre con antebrazo visible. El reporte de
muñecas debe indicar mediciones realmente ejecutadas; una observación de malla cerrada
no aprueba anatomía. El controlador verifica recibo v2 y hashes antes de cargar/detectar/
generar. Los recibos v1 pasan a revisión pendiente; nunca se convierten solos a v2.
La ausencia del tercero no impide registrar un descarte temprano; sí impide un pase.


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
