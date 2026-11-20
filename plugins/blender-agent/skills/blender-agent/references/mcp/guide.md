# Guía breve para el agente de Blender

Objetivo: producir el resultado solicitado con pocas operaciones innecesarias y revisar su apariencia real. Respeta el brief, las referencias y las instrucciones del usuario. Estas pautas no autorizan otros proveedores, compras, cambios de seguridad ni procesamiento adicional de imágenes.

## Antes de construir

1. Define sujeto, uso, estilo, referencias, escala, formato, resolución/aspecto y criterio de entrega. Pregunta sólo si falta una decisión que cambie materialmente el resultado; no pidas aprobación por cada preview.
2. Consulta get_blender_capabilities y get_objects_summary. Confirma sesión, archivo y versión. Usa sesión aislada si la tarea no requiere editar la escena actual; no cierres sesiones ajenas.
3. Lee la receta pertinente y verifica sólo la API que vas a usar. Obtén la referencia rápida con get_blender_workflow_docs(topic="quick_api"). Si cambia el build o falla una firma, consulta get_python_api_docs o search_api_docs. No cargues el volcado completo de funciones/API.

## Ejecutar con menos idas y vueltas

- Prefiere la herramienta específica que cubra el trabajo. Agrupa consultas independientes y, cuando haga falta Python, reúne cambios coherentes en un bloque con comprobaciones finales; devuelve conteos, bounds, nombres y rutas, no todos los vértices.
- Usa operadores para acciones estándar; para geometría procedural o creación masiva explícita, bpy.data/Mesh.from_pydata/BMesh evitan depender de selección repetidamente. En Edit Mode usa BMesh y actualiza su malla. Conserva referencias reales: los nombres pueden recibir sufijos .001.
- Un Object y su Mesh son datos distintos. Reutiliza datos/grupos/materiales cuando deban ser idénticos; comprueba users y crea copias antes de modificar algo compartido que deba diferenciarse.
- Separa escribir de evaluar: agrupa cambios compatibles y actualiza el depsgraph antes de leer geometría/matrices evaluadas. No fuerces update dentro de cada iteración sin una dependencia real. Libera los resultados temporales de to_mesh con to_mesh_clear.
- Controla objeto activo, selección, modo y área. Usa run_blender_operator cuando corresponda. Para archivos existentes, execute_blender_transaction trabaja sobre una copia y publica un archivo nuevo sólo al pasar sus asserts.
- Conserva una sesión para iteraciones; evita iniciar un Blender por cada consulta. Para renders/bakes/lotes largos usa start_blender_job, mcp_progress y checkpoints en límites útiles; consulta estado según el trabajo, sin bucles de polling constantes. Reiniciar desde un checkpoint vuelve a comenzar el código y requiere que éste distinga el trabajo ya hecho.

## Orden visual de trabajo

1. **Forma y cámara:** comprueba proporciones, silueta y encuadre con geometría sencilla. Evita cortes accidentales y tangencias. Ajusta distancia y focal según la referencia; no impongas una focal universal.
2. **Iluminación:** busca separación entre sujeto y fondo y sombras que expliquen el volumen. Para producto, una luz de área puede servir como punto de partida; no es una obligación para escenas estilizadas u otros briefs.
3. **Materiales y detalle:** distingue superficies por sus propiedades físicas y por la referencia. Añade bevels sólo donde correspondan a aristas reales y a escala razonable. Revisa normales, escala, UV y texturas faltantes antes de añadir más subdivisiones. No hagas todo brillante para aparentar calidad.
4. **Color:** elige gestión de color para el destino; AgX es una opción para alto rango dinámico, no una garantía de fidelidad cromática o de apariencia. Revisa reflejos quemados, negros sin detalle y separación de tonos. Conserva la intención estilística.
5. **Preview y acabado:** fija un presupuesto explícito al usar Cycles; no heredes miles de muestras por accidente. Una preview de 512–768 px y 16–32 muestras es sólo un punto de partida propuesto, ajustable a escena/equipo. Activa adaptive sampling/denoising sólo cuando sean adecuados y comprueba que no borren detalles. El final usa la resolución solicitada y un presupuesto decidido al ver ruido y detalles reales; no hay un número universal de muestras.

## Comprobar antes de entregar

- Renderiza y observa la imagen. El helper render_thumbnail_to_path está limitado a 320 px y sirve para previews; render_viewport_to_path hace un render de cámara, no una captura del viewport. Un thumbnail o un test técnico no acreditan el acabado final.
- Revisa silueta/proporciones, encuadre, iluminación, materiales, ruido, bordes y detalles al tamaño de entrega. En personajes/animación añade deformaciones, contactos e interpenetraciones y revisa el movimiento completo con su audio si existe. Corrige lo observado en la escena y vuelve a revisar el artefacto final.
- Separa defectos verificables, decisiones de estilo e incertidumbres. Usa el bloque común y el módulo pertinente del catálogo local review-prompts.md. No atribuyas una revisión a otro evaluador ni inventes un dictamen.
- Reabre el .blend y verifica recursos. Exporta según el destino y prueba el archivo resultante en su consumidor; un import que no falla no demuestra fidelidad visual. Entrega modelos en HTML interactivo con giro/zoom y verifica el modelo real en navegador, según las instrucciones vigentes.
- Guarda estado breve, fuente, versión, artefactos y comprobaciones. Conserva originales y usa rutas nuevas. Los checkpoints no revierten efectos externos y restaurarlos cambia el filepath; no prometas rollback universal.

Esta guía mejora el proceso; no certifica de antemano la calidad de una creación ni que todo Blender esté probado.


## Dispositivo de render

Antes de heredar CPU, enumera los dispositivos reales de Cycles en una sesión aislada y mide un trabajo representativo con los mismos ajustes. Carga get_blender_workflow_docs(topic="render") para la receta. En la prueba de lámpara de X, OptiX en RTX3060 tardó16.72s frente a82.32s CPU con1200×900 y64muestras; es una medición de esa escena, no una garantía universal. Conserva CPU como alternativa comprobada si la GPU falla o no tiene memoria, sin cambiar preferencias globales ni guardar userpref.


## Preservación de identidad y guardia de artefactos

Para reparaciones de personajes con parecido que conservar, leer identity_preservation. Fijar base preferida y originales con create_asset_preservation_guard; declarar ROI por atributos/vértices y píxeles. Proteger también opacidad, mirada y silueta; no sustituir rasgos por genéricos para limpiar artefactos. Comparar original/base/candidato. validate_asset_preservation sólo acredita integridad técnica. La entrega controlada usa record_asset_identity_review y export_asset_with_preservation_guard; revisión regresiva/incierta o hash cambiado bloquea esa ruta. No afirmar protección frente a Python arbitrario ni juicio automático de semejanza.
