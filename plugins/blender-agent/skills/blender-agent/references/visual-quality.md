# Revisión visual y entrega

Antes de evaluar, lee %USERPROFILE%/.codex/references/global-workflows/review-prompts.md y selecciona bloque común + módulo del material (imagen estática para render; audiovisual para animación con sonido). Para video/audio lee también audiovisual-review.md. Usa sólo las referencias originales autorizadas. No crees versiones procesadas de imágenes para facilitar la revisión sin autorización.

## Qué observar

- Forma y cámara: proporciones respecto al brief, silueta reconocible, encuadre, tangencias, perspectiva y cortes accidentales.
- Luz y materiales: volumen legible, reflejos y sombras coherentes, negros y altas luces con el detalle esperado, materiales distinguibles y consistentes con referencias.
- Superficie: normales, facetas inesperadas, interpenetraciones, contactos, texturas/UV faltantes y detalle visible al tamaño final.
- Render: ruido, artefactos del denoising, bordes, transparencia y gestión de color según el destino. No uses brillo, subdivisión o muestras altas como sustituto de una composición correcta.
- Animación cuando aplique: movimiento completo, deformaciones, contactos, ritmo, cámaras y sonido real. Un fotograma o un hueso probado no valida el clip.

Da al evaluador sólo objetivo, material real y referencias pertinentes. Guarda hashes/rutas/logs internamente; no envíes aprobaciones anteriores ni defectos esperados en una primera revisión. Identifica al evaluador real y qué observó. Distingue defecto confirmado, preferencia estética e incertidumbre. Corrige lo observado en Blender y vuelve a mirar el artefacto final cuando cambie materialmente.

## Consumidor real

Reabre o reimporta la salida para verificar datos, recursos, escala y materiales. Además, observa el archivo final en el visor/motor destino. Para modelos: HTML con geometría real, giro y zoom; comprueba carga, cámara, materiales, controles y consola, y móvil si es parte de la entrega. No sustituyas el visor por una captura o ZIP. Verifica la URL Tailscale y declara diferencias de iluminación/materiales respecto al render.

Registra internamente artefacto, objetivo, resultado técnico, evaluación perceptiva, correcciones, límites y enlace verificado. No declares calidad comprobada si sólo hubo metadatos o el evaluador no pudo abrir el material. Reutiliza una comprobación anterior si no cambió el artefacto ni el entorno y no hay fallo nuevo; identifica su alcance histórico con claridad.

Si falta el catálogo local, usa la copia versionada [review-prompts.md](review-prompts.md), bloque común y módulo pertinente; no omitas la inspección real. Para animación sin la referencia audiovisual local, declara el límite y realiza revisión perceptiva completa por Codex sin atribuirla a otro proveedor.

Para personajes y encajes anatómicos aplica además [validación externa obligatoria](external-visual-review.md), incluidas ambas muñecas con el antebrazo visible. No uses capturas de manos aisladas para aprobar la unión.


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
