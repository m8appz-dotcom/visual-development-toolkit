# Reparación local con conservación de identidad

Aplicar cuando un personaje debe seguir pareciéndose a las fotos originales o a una base preferida por el usuario. No imponer parecido realista a un encargo estilizado distinto. La prioridad es conservar la identidad buscada mientras se repara el defecto; menos artefactos no compensa otro rostro.

## Antes de editar

1. Fijar la base preferida exacta y los originales reales. Conservar ambas fuentes. Declarar defecto, región permitida y rasgos protegidos. Ojos, cejas, bigote, labios, contorno y silueta pueden aportar identidad tanto por geometría como por textura, opacidad y material.
2. Para una corrección local, una causa por variante. No cambiar simultáneamente proyección global, ojos, color y peinado para reparar una marca nasal. No revelar ojos genéricos bajo una foto como atajo de limpieza. Una selección por altura no demuestra que sólo incluya cabello.
3. Consultar `get_asset_preservation_capabilities`. Para GLB de topología estable, crear `create_asset_preservation_guard` ANTES de la edición. Las herramientas sólo leen GLB/fotos; no acceden a la escena de Blender. Los recibos se guardan en el estado del MCP.

## Contrato ejecutable

`create_asset_preservation_guard` requiere:
- `baseline_glb`: base preferida; el hash se fija y vuelve a comprobar.
- `reference_images`: rutas de fotos originales, cuyo hash también se fija. No se suben a terceros.
- `objective`: defecto concreto y propósito de conservación.
- `edit_regions`: lista de `{mesh, primitive, vertices, attributes}`. Índices de vértice del GLB, no índices de loop ni del .blend previo a exportación. Ejemplo: `{mesh:0, primitive:0, vertices:[10,11,12], attributes:["POSITION"]}`. Sólo esos atributos/vértices pueden cambiar. Pesos/huesos permanecen protegidos.
- `protected_features`: lista de `{name, mesh, primitive, vertices}`. No puede solaparse con una región editable. Compara atributos, incluida opacidad; en imágenes editables protege el rectángulo UV de cada rasgo con margen de dos píxeles.
- `image_edits`: lista de `{image, rectangles:[[x,y,width,height]]}` para texturas que deban cambiar. Coordenadas enteras con origen ARRIBA-IZQUIERDA, coherentes con glTF. Si la imagen cambia, exige igualdad de píxeles fuera de esos rectángulos. No es una operación de edición ni autoriza procesamiento de imágenes.

Los materiales globales, estructura, topología, rig/bind/weights y muestras de animación deben conservarse. Omitir una región no permite cambios: los bloquea. Decodificación de cambios de textura: sólo PNG RGB/RGBA8 no entrelazado de hasta 16 megapíxeles; imágenes idénticas no se decodifican. JPEG modificado, sparse accessors, compresión requerida, transformaciones UV de rasgos o formatos no cubiertos producen error o rechazo, nunca un pase silencioso. Para retopología u otros cambios de alcance usar el flujo pertinente y declarar que esta guardia no los cubre.

## Validación y entrega

- `validate_asset_preservation` lee base/candidato y devuelve `technical_pass`, causas y cambios. Una validación que falla no debe publicarse por otra vía para eludir el control.
- Revisar original + base + candidato, con misma cámara/luz/pose entre modelos. Ver cara completa además del defecto, de frente, tres cuartos y ambos perfiles. Diferencias de perspectiva de la foto limitan inferencias anatómicas; no inventar puntuaciones de parecido.
- Registrar hallazgos: resuelto, parcial, persistente, regresión o no comprobado. Si pierde parecido, conservar la base y rechazar la candidata aunque pase técnicamente. Si hay duda, indicarla; no inventar aprobación ni pedir de nuevo una ya otorgada.
- `record_asset_identity_review` registra una declaración del evaluador `codex` o `external`, resultado `preserved/regressed/uncertain`, observaciones y cuatro vistas `{view, baseline_image, candidate_image}` (`front`, `three_quarter`, `profile_left`, `profile_right`). Las imágenes deben ser evidencia realmente observada; una comparación A/B completa puede servir para ambos roles. El servidor fija hashes, pero no prueba que alguien miró las imágenes, no verifica identidad automáticamente y no convierte esta declaración en aprobación humana.
- `export_asset_with_preservation_guard` es la ruta de entrega controlada: sólo copia a un GLB NUEVO si pasa lo técnico y la revisión declarada es `preserved` para el mismo hash. Revisa de nuevo base, originales y evidencia; rechaza revisión ausente, incierta, regresiva o caducada y nunca sobrescribe archivos. Después probar GLB real en HTML con materiales, giro, zoom y animación cuando aplique.

## Límites de protección

El parecido sigue requiriendo juicio perceptivo. La guardia sólo controla su propia ruta de entrega y no intercepta Python arbitrario, otros exportadores ni cambios externos a los archivos examinados. Un agente debe seguir el flujo; no afirmar protección universal. No declarar una fuente «original» por su nombre o por estar aprobada previamente. Los controles técnicos y la revisión visual son dos resultados distintos.

Caso motivador: se conservaron rig/UV/geometría facial, pero la opacidad retiró la foto de los ojos y apareció la textura ocular genérica; además se cambiaron proyección, mezcla y silueta. La integridad técnica no protegió el parecido.

Referencia de formato: [glTF 2.0, Khronos](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html). No trasladar sin conversión la orientación UV de la interfaz de Blender a los píxeles del archivo glTF.
