---
name: blender-agent
description: "Crear, editar, renderizar y exportar escenas de Blender mediante el MCP blender, con recetas verificadas, consulta selectiva de API y revisión visual del resultado. Usar en trabajos reales de Blender y diagnóstico de sus flujos."
---

# Blender con MCP y revisión visual

Usa el MCP existente `blender`. Empieza con `get_blender_workflow_docs(topic="overview")`, `get_blender_capabilities` y la inspección del archivo/sesión objetivo. Confirma runtime y contexto antes de editar. No inicies otra instancia si la tarea exige trabajar en la escena actual; para pruebas independientes usa una sesión aislada y conserva las ajenas.

Lee `topic="guide"` y sólo las recetas pertinentes:

Para retopología consulta primero `get_retopology_capabilities`. Usa las tools específicas
`begin_retopology`, `inspect_retopology`, `add_retopology_patch`, `build_retopology_bone_strip`,
`select_retopology_tool`, `relax_retopology`, `undo_retopology`, `finish_retopology`,
`transfer_retopology_weights`, `validate_retopology_poses` y `save_retopology_result`.
Requieren `session_id` explícito de una sesión GUI propia, que puede iniciarse oculta con
`start_blender_session(background=False)`. Espera `ready=true` antes de editar y salida modal
antes de transferir/guardar. Usa rutas nuevas y preserva fuentes. El trazado de anillos es
dirigido; Relax del adaptador no es el pincel nativo y seleccionar una herramienta no prueba
sus strokes. No presentes distancias de poses muestreadas como aprobación visual.
El contrato y límites están en `RETOPOLOGY.md` en la raíz del plugin.

| Trabajo | topic |
|---|---|
| Firmas seleccionadas de API | `quick_api` |
| Malla explícita y modificador evaluado | `geometry` |
| Interfaz de Geometry Nodes | `nodes` |
| Keyframes y evaluación temporal | `rig_animation` |
| Dispositivos, presupuesto y render | `render` |
| Selección, GLB y reimportación | `export` |
| Modelo en HTML interactivo | `delivery` |

Si la conexión del chat no anuncia la herramienta nueva, comprueba el catálogo de una conexión nueva al servidor configurado. No crees otro MCP ni reinicies apps en uso. Si sigue ausente, declara ese límite y consulta las [copias versionadas](references/mcp/manifest.json); conserva el MCP para las operaciones disponibles. Las copias son documentación, no un sustituto del runtime ni permiso para ejecutar ejemplos sin adaptar sus precondiciones.

## Construir y medir

Define sujeto, referencias originales, uso, escala, estilo y formato con lo que pidió el usuario. Decide primero silueta y cámara; después luz, materiales y detalles. No impongas un estilo de producto a otros encargos.

Usa herramientas específicas antes de Python general. Agrupa cambios coherentes y devuelve un resumen con comprobaciones. Para geometría procedural usa datos explícitos/BMesh cuando evite selección repetitiva. Consulta [hallazgos de la extracción](references/extraction.md) cuando intervengan datos compartidos, operadores o geometría evaluada. No cargues los catálogos completos de pseudocódigo/API.

Con archivos existentes, usa transacciones sobre copia y rutas nuevas según el objetivo. Los checkpoints no revierten archivos externos; reiniciar un job reejecuta código. Usa jobs durables para renders/bakes largos y lee errores reales antes de continuar. No declares éxito por la mera existencia de una ruta.

Para render, enumera dispositivos reales antes de elegir CPU/GPU, mide con ajustes equivalentes y no guardes preferencias globales. Ajusta muestras y resolución al objetivo y al ruido observado. Las cifras históricas de una lámpara no garantizan el rendimiento de otra escena.

## Aceptar por apariencia y por uso

Cuando haya que conservar identidad o parecido durante una reparación, lee [preservación de identidad](references/identity-preservation.md) o `get_blender_workflow_docs(topic="identity_preservation")`. Fija la base preferida y originales; una causa/región por candidata; protege también textura, opacidad, mirada y silueta. No sustituir rasgos por otros genéricos para limpiar artefactos. Usa la guardia MCP y su exportación controlada cuando el GLB esté cubierto; un pase técnico no aprueba parecido. Compara original/base/candidato y no promuevas una regresión. Declara los límites si la guardia no cubre el formato o la operación.

Aplica [revisión visual](references/visual-quality.md) antes de dar por terminado un trabajo visual. Mira el render original final al tamaño solicitado. Un thumbnail, script exitoso, conteo de polígonos o reimportación técnica no acreditan calidad visual.

Entrega modelos en HTML interactivo y prueba el modelo real en navegador: giro, zoom, materiales y animación si aplica. Verifica la URL Tailscale antes de entregarla. Si el visor aproxima los materiales del render, explica el límite. No transfieras una aprobación de otro artefacto.

Preserva brief, fuentes originales, elección de herramientas/proveedor/modelo y autorización del usuario. Esta skill no autoriza procesamiento de imágenes, cambios de marca, compras, publicación o mensajes externos adicionales.

## Referencias bajo demanda

- [Guía de respaldo](references/mcp/guide.md): sólo cuando la guía del MCP no esté disponible o al comparar versiones.
- [Procedencia y evidencias](references/extraction.md): build, hallazgos y límites de la extracción y pruebas.
- [Calidad visual](references/visual-quality.md): evaluación y entrega en el consumidor.
- Recetas de respaldo: [geometría](references/mcp/geometry.json), [nodos](references/mcp/nodes.json), [animación](references/mcp/rig_animation.json), [render](references/mcp/render.json), [exportación](references/mcp/export.json), [entrega](references/mcp/delivery.json), [API breve](references/mcp/quick-api.json). Lee sólo la necesaria.

## Runtime del plugin

Este paquete proporciona el MCP `blender`. Consulta la configuración local %LOCALAPPDATA%/BlenderAgent/settings.json. Si falta, ejecuta el instalador del plugin siguiendo INSTALL.md; no uses rutas históricas de X en otro equipo. El servidor no descarga ni instala dependencias automáticamente durante una llamada MCP.

## Validación externa obligatoria

Antes de aceptar una adaptación anatómica o pasarla a AccuRIG aplica [revisión externa](references/external-visual-review.md): Gemini Flash más reciente disponible verificado, sólo navegador, prompt sencillo y evidencia real. Revisión pendiente, defectos abiertos o aprobación de usuario ausente bloquean el siguiente paso. No confundir malla cerrada con encaje correcto.
