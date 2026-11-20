# Guía integrada y prueba real de Blender

La guía está instalada en el MCP configurado de X. Una conexión nueva al launcher devuelve **42 herramientas** y anuncia get_blender_workflow_docs en sus instrucciones de inicio. Sus temas permiten cargar la guía, nueve firmas verificadas y recetas de geometría, nodos, animación, render, exportación y entrega, sin leer los300MB de la API completa.

El resultado de la prueba se puede ver en el [visor interactivo por Tailscale](http://100.124.193.10:18834/). Incluye el render original aceptado, el modelo giratorio con zoom y las descargas reales del GLB y del .blend. El servidor estático es local y bajo demanda, limitado a la IP Tailscale; no se instaló un servicio de arranque ni se modificaron otros servidores.

## Qué se midió

Encargo concreto: lámpara de escritorio original color salvia, columna y detalles de metal cálido, difusor marfil y presentación de producto sobre pedestal. No se proporcionaron referencias externas ni se añadió branding.

| Tramo | Antes | Con el flujo guiado | Alcance |
|---|---:|---:|---|
| Llamadas para construir y comprobar la escena |10|1|Mismas funciones/partes en llamadas separadas frente a un bloque coherente |
| Construcción, mediana de3 rondas |0,346s|0,141s|2,45× en ese tramo; no incluye razonamiento, generación de código, arranque o render |
| Render de cámara CPU frente a OptiX |82,32s CPU|16,72s RTX3060/OptiX|4,92× en esta escena;1200×900,64muestras,misma semilla y resto de ajustes |
| Trabajo aislado completo del render |83,85s|17,89s|Incluye ejecución del proceso hijo según supervisor, no el razonamiento del agente |

La mejora grande procede de **elegir y comprobar el dispositivo real** antes de heredar CPU. La receta de render ahora incluye enumeración de dispositivos, configuración OptiX aislada y este ejemplo medido. No guarda preferencias globales. CPU sigue siendo una alternativa si la GPU no está disponible, falla o no tiene memoria; el rendimiento debe verificarse para cada escena/equipo.

## Comparación controlada y límites de la medición

Los dos flujos de construcción ejecutaron las mismas definiciones de producto, cámara, luces, materiales, resolución y semilla. Se alternó el orden entre rondas y se reinició la escena de prueba. Las seis ejecuciones produjeron la misma huella de escena:8componentes de producto,18304vértices y14objetos contando el estudio.

Los dos renders CPU de esos archivos tienen **píxeles idénticos**; sus metadatos y tiempos son diferentes. Por tanto, el ahorro de llamadas no se obtuvo reduciendo la escena o su calidad. OptiX produce pequeñas diferencias numéricas respecto a CPU: diferencia absoluta media por canal de aproximadamente0,003 sobre255. Esas estadísticas son evidencia complementaria; también se observaron las imágenes originales.

Se trata de una prueba de flujo real realizada por el agente actual mediante MCP, no de un ensayo aleatorio de agentes autónomos o modelos distintos. La parte repetida es un benchmark reproducible de construcción por componentes frente a agrupación. La comparación de dispositivos tiene una ejecución final por dispositivo y no es un estudio estadístico. No permite afirmar que todos los encargos o el razonamiento completo del agente sean2,45× o4,92× más rápidos. Los dos efectos se separan en la tabla para no atribuir al prompt la mejora propia del hardware.

## Aceptación visual y del archivo

Codex inspeccionó los PNG originales de CPU y GPU a1200×900 con el bloque común y los módulos de imagen y comparación del catálogo local. Se observó una silueta continua, encuadre completo del producto, reflejos suaves, materiales diferenciados y sombras de contacto; no se observó un defecto visual material en el resultado OptiX frente a CPU. Dictamen: adecuado para esta prueba de producto de estudio, sin certificar la calidad artística de otros trabajos.

El GLB se reimportó en un Blender aislado: aparecieron8meshes y los límites espaciales coincidieron con el original, aproximadamente±0,831m enX/Y y0–2,520m enZ. El visor carga la geometría evaluada exportada del mismo producto, sin usar geometría de reemplazo, y se verificó en el navegador:8componentes, giro por arrastre, zoom, giro automático y español persistente al recargar. Su iluminación de tiempo real es aproximada y puede verse distinta del render de estudio.

En móvil se detectó que los controles envolvían sobre la base del modelo. Se corrigió el diseño y se volvió a observar: el canvas mide320px de alto y los controles quedan debajo, sin desbordamiento horizontal en390px. La captura completa de la herramienta falló de forma transitoria tras cambiar el viewport; se restauró el tamaño y se usó la captura nativa documentada. Se guardaron las evidencias finales.

!Visor verificado (ruta histórica en el informe original)

## Instalación, conservación y rollback

- Integración activa: D:/CodexTools/blender-mcp/launcher.py apunta a hardening-v2. El directorio hardening-v1 y el paquete upstream se conservan.
- El backup anterior a esta integración figura en deployment.json (ruta histórica en el informe original). config.toml no cambió y la escena previa permaneció limpia, sin archivo y enPID29084.
- Sólo se cerraron sesiones aisladas creadas para las pruebas, después de guardar sus archivos. Los renders no se retocaron, recortaron, remuestrearon ni procesaron para mejorar su apariencia; se compararon leyendo sus datos.
- rollback.ps1 (ruta histórica en el informe original) restaura únicamente el launcher previo tras comprobar su hash. Conserva modelos, renders, logs, trabajos y preferencias. No se ejecutó rollback.
- La conexión antigua del chat conserva su catálogo hasta que el cliente la renueve; la instalación y el nuevo catálogo se comprobaron mediante una conexión nueva al mismo launcher configurado. No se reinició Codex ni el Blender existente.

## Evidencia reproducible

- Aceptación del MCP instalado (ruta histórica en el informe original):42herramientas, guía de inicio, todos los temas, errores y CLI.
- Recetas ejecutadas (ruta histórica en el informe original):geometría,nodos,animación,inspección de render y exportación en una escena aislada.
- Benchmark del trabajo (ruta histórica en el informe original) y script reproducible (ruta histórica en el informe original).
- Render CPU (ruta histórica en el informe original), render OptiX (ruta histórica en el informe original) y comparación numérica sin alterar los originales (ruta histórica en el informe original).
- Aceptación de navegador (ruta histórica en el informe original), dictamen visual (ruta histórica en el informe original) y captura móvil final (ruta histórica en el informe original).

El aprendizaje práctico incorporado es: cargar sólo conocimiento pertinente, agrupar cambios coherentes, verificar los dispositivos reales, medir con ajustes comparables y observar el resultado final. Las pruebas previas de descompilación siguen conservando sus límites; esta integración no los convierte en una certificación exhaustiva de Blender.
