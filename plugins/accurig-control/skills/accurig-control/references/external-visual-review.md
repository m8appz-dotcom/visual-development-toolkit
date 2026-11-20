# Revisión externa y encaje anatómico

La revisión externa obligatoria utiliza Gemini Flash, el más reciente disponible
en la cuenta autorizada **verificado en el selector al ejecutar**, exclusivamente
por navegador. No CLI, API, Auto ni sustitución silenciosa. La selección del usuario
prevalece. Si falta acceso, cuota, modelo o capacidad de adjuntos, registra pendiente
y bloquea la siguiente fase; no lo sustituyas por la autoevaluación de Codex.

Lee browser-access.md, gemini-browser.md y review-prompts.md locales antes de usar
el navegador. Abre conversación nueva para la revisión final independiente, conserva
cuenta y sesión. IAB primero; Chrome sólo ante límite comprobado. No envíes logs,
hashes, rutas, dictámenes previos ni defectos esperados al evaluador.

Prompt sencillo:

> Revisa este modelo 3D para detectar errores visuales de anatomía, proporciones, uniones y superficie. Indica dónde ves cada defecto y qué se observa. Si alguna zona no se puede evaluar, dilo.

Adjunta capturas reales sin procesar del modelo final en HTML: frente, ambos lados,
espalda, y ambas manos con muñeca y antebrazo visibles desde frente, perfil, palma y
dorso. No uses una mano aislada ni un cuerpo distante como prueba de su integración.
Una captura parcial sirve para rechazar un defecto; no para aprobar el cuerpo completo.
En animación adjunta el clip completo y revisa también las transiciones; una aprobación
estática no valida deformación. No envíes un enlace privado como si Gemini hubiera
podido abrirlo: verifica recepción real de los adjuntos y respuesta terminada.

Antes de unir piezas en Blender MCP, compara escala, ejes, longitud, sección y volumen
con el cuerpo. Mide varias secciones del antebrazo, muñeca y palma en la misma unidad;
registra ubicación, ancho, profundidad y cambios entre secciones. Un mínimo brusco,
intersección o salto de silueta debe investigarse; no impongas un umbral anatómico
universal ni apruebes por estar cerrada la malla. Conserva fuentes, cara y rollback.

Después del encaje, inspecciona las mismas vistas con luz neutra y compara el archivo
exportado y reimportado, no sólo Blender. Registra también límites del diagnóstico.
No declares automatizada esta medición si no se ejecutó sobre la geometría real.

Guarda respuesta original íntegra, conversación, cuenta verificada, selector de modelos,
capturas de navegador, archivos realmente enviados y sus hashes en el registro interno.
Los controles técnicos, el dictamen perceptivo y la aprobación del usuario son separados.
Gemini no reemplaza al usuario ni certifica topología o skinning. Cualquier defecto abierto,
zona requerida no observada, respuesta pendiente o archivo cambiado bloquea AccuRIG.
Un defecto corregido exige nueva revisión del resultado; no cambies su estado a resuelto
en el recibo viejo para habilitarlo. Toda aprobación debe corresponder al archivo exacto.

El control ejecutable es scripts/base_gate.py junto a external_review.py del pipeline
3d · Rig y movimiento y del controlador AccuRIG. No es una firma del proveedor ni puede
probar que un recibo escrito por el agente sea veraz: conserva las evidencias originales.
La ejecución general de Blender sigue permitiendo trabajo en progreso y diagnósticos;
la barrera se aplica a la aceptación y al paso a AccuRIG, no a guardar un borrador.

Si el usuario autoriza expresamente otro modelo de la familia Flash para esta revisión,
registra esa excepción para el archivo exacto; nunca conviertas una cuota en permiso
para cambiarlo automáticamente. `model_selection.user_authorization_path` referencia
un recibo user-model-choice/1 con source_sha256, selected, actor user, status authorized,
message_reference, authorization_text y evidence_path del mensaje real. Esta decisión
no aprueba el modelo 3D ni cambia el modelo predeterminado de las próximas tareas.


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
