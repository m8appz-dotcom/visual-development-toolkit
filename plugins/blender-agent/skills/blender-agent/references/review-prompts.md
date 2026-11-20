# Prompts de evaluación activos

Establecido por el usuario el 19 de octubre de 2026. Catálogo activo para seleccionar los prompts de evaluación; no modifica por sí solo ejecutores ni evidencias históricas. Revisión de antecedentes recuperables en X, Bobi y Spark; el índice tiene cobertura parcial y no demuestra haber localizado todas las evaluaciones históricas. No se han ejecutado nuevas evaluaciones ni alterado aprobaciones anteriores.

## Qué recibe el evaluador

Solo material real, objetivo, público/uso cuando importen y referencias o requisitos pertinentes. Identifica adjuntos con nombres humanos: «Referencia», «Candidato», «A», «B». Los campos entre corchetes se completan con información real o se omite la línea si no aplica; nunca se envían placeholders.

Los hashes, rutas, host, IDs de trabajos, revisiones, cuentas, configuración del modelo, logs, resultados técnicos y número de funciones probadas quedan en el registro interno de Codex. No se envían al evaluador ni se le pide verificarlos. El registro vincula su respuesta con los archivos correctos. Las marcas de tiempo y los roles de canales de audio sí son útiles para observar y localizar hallazgos. Un esquema JSON puede ser necesario para una integración automática, pero se limita a observaciones y hallazgos, sin metadatos operativos.

En la primera revisión no se envían críticas anteriores, aprobaciones ni una lista de defectos esperados. En un seguimiento sí se puede preguntar por una observación concreta. Una puntuación solo se solicita si interesa al usuario: es subjetiva, requiere criterios y no sustituye los hallazgos.

## Bloque común

Anteponer este bloque a UNO de los prompts específicos; agregar el de comparación o seguimiento solo cuando corresponda. No concatenar todas las especialidades.

```text
Evalúa el material adjunto para este objetivo: [objetivo concreto].
Inspecciona realmente las imágenes o, si es video/audio, el archivo completo con su sonido cuando exista. Indica cualquier parte a la que no hayas podido acceder. No deduzcas el contenido de nombres de archivo, descripciones o metadatos.
Describe lo que observas y separa errores confirmados, preferencias estéticas e incertidumbres. No inventes defectos ni causas técnicas. Para cada problema indica dónde ocurre, qué se ve o escucha, cómo afecta al objetivo y qué cambio concreto recomendarías. Usa tiempos en material temporal y zonas identificables en imágenes.
Cierra con los aciertos, hasta tres correcciones prioritarias y un dictamen acorde con la evidencia: adecuado para el objetivo, requiere correcciones o evidencia insuficiente. No impongas requisitos ajenos al uso indicado.
```

## 1. Video narrado, ensayo o YouTube

```text
Evalúa claridad, interés y ritmo para [público y propósito]. Revisa si el inicio plantea pronto una razón para seguir viendo, si cada tramo desarrolla la idea y si el cierre la resuelve. Señala repeticiones, explicaciones confusas, cortes innecesarios, planos demasiado largos y texto que no alcanza a leerse.
Contrasta lo que dice la voz con lo que muestra cada imagen, gráfico o recurso. Revisa legibilidad, continuidad, encuadre, transiciones y coherencia de estilo. Escucha inteligibilidad, naturalidad, pausas, cambios de volumen y competencia entre voz, música y efectos.
Señala contradicciones o afirmaciones que necesitan comprobación; no declares un dato verificado sin fuentes suficientes. Si se adjuntan título y miniatura, evalúa si el contenido cumple su promesa; si no, omite ese criterio. No presupongas un estilo de cortes rápidos.
```

## 2. Comercial, reel o anuncio

```text
Evalúa este anuncio para [audiencia], cuyo objetivo es [acción o mensaje]. Comprueba si se entiende pronto qué ofrece, por qué importa y qué debería hacer el espectador.
Revisa la relación entre problema, demostración, beneficio y cierre. Señala escenas decorativas o repetidas que debilitan el mensaje. Si cuenta una historia, comprueba que las acciones y reacciones tengan una causa comprensible.
Revisa producto, textos, marca y llamada a la acción únicamente contra las referencias y requisitos proporcionados. Detecta promesas sin respaldo, elementos de prueba, logos o textos accidentales, recortes y texto fuera de zonas seguras. Escucha música, voz y efectos y evalúa su relación con la imagen. No atribuyas resultados de ventas ni predigas conversión a partir del video.
```

## 3. Curso, tutorial o demostración de producto

```text
Evalúa si [tipo de alumno] puede alcanzar [resultado de aprendizaje] con este material. Revisa si explica qué hacer, cómo y por qué; si muestra los pasos necesarios en orden; y si los ejemplos y las prácticas permiten comprobar lo aprendido.
Contrasta narración, pantallas, cifras y términos con las fuentes de referencia adjuntas. Señala omisiones, pasos imposibles de seguir, contradicciones, saltos de dificultad y resultados prometidos que la demostración no prueba. Si faltan fuentes, identifica qué necesita comprobarse sin inventar la respuesta correcta.
Revisa idioma, pronunciación, ritmo didáctico, tiempo para leer y practicar, tamaño de texto y correspondencia entre la acción descrita y la pantalla. Distingue una explicación ilustrativa de una demostración funcional real. No pidas ritmo de anuncio ni cortes constantes si dificultan aprender.
```

## 4. Montaje y resultado de un editor automático

```text
Evalúa si el montaje funciona como pieza terminada para [uso]. Revisa duración de planos, continuidad, repetición, cortes, transiciones, ritmo y cierre; distingue elecciones estéticas de defectos.
Busca negros, congelaciones, saltos, restos de prueba, formas o capas accidentales, duplicaciones, texto tapado o cortado y elementos fugaces. Revisa recortes, deformación, centrado, máscaras, bordes y superposiciones: llenar el cuadro no demuestra un buen encuadre.
Comprueba legibilidad, contraste, coherencia y tiempos de los textos. Distingue una afirmación literal incompatible con la imagen de un título general o poético. Escucha cambios de volumen, cortes, silencios y final de música.
Indica qué errores permanecen en el resultado. No presupongas qué controles ejecutó el editor ni atribuyas un fallo a su supervisor sin esa evidencia. No exijas que la pieza exhiba todas las funciones usadas durante una prueba.
```

## 5. Locución, doblaje o voz transformada

```text
Escucha el audio completo y evalúa inteligibilidad, pronunciación, acento solicitado, entonación, emoción, respiraciones, pausas y ritmo. Señala sonidos metálicos, distorsiones, palabras cortadas, cambios de timbre y patrones que suenan a lectura mecánica.
Si se adjunta un guion, comprueba fidelidad al texto sin asumir que toda variación es un error. Si hay una referencia de voz autorizada, compara rasgos audibles, expresividad y consistencia; no afirmes identidad personal ni un porcentaje de semejanza.
En doblaje o voz transformada, compara duración, intención y sincronía con la interpretación original. Evalúa sincronía labial solo si puedes ver el video correspondiente. Separa defectos de grabación, mezcla e interpretación de las hipótesis sobre su causa.
```

## 6. Conversación de un asistente de voz

```text
Escucha la conversación completa. Evalúa naturalidad, pronunciación, entonación, ritmo, pausas entre turnos y adaptación al interlocutor. Identifica respuestas con cadencia repetitiva, listas innecesarias o cierres mecánicos.
Revisa interrupciones: qué se oye del participante, cuándo deja de hablar el asistente, si continúa indebidamente y cómo retoma o cambia de intención. Describe los intervalos audibles; no deduzcas latencia de red ni el funcionamiento interno del sistema.
Comprueba relevancia y coherencia de las respuestas con lo realmente dicho. Si se proporciona un mapa de canales, úsalo para distinguir participantes. Si no puedes atribuir una voz o entender una frase, indícalo. No confundas una buena interrupción con naturalidad general.
```

## 7. Música, mezcla y diseño sonoro

```text
Escucha la pieza completa para [uso y ambiente buscado]. Evalúa estructura, progresión, repetición, transiciones, energía, timbres y cierre. Señala pasajes que distraen, resultan monótonos o contradicen la intención.
Si acompaña voz o imagen, comprueba que apoye el mensaje sin ocultarlo y que los acentos y cambios tengan sentido con lo que sucede. Revisa equilibrio audible, distorsión, cortes, silencios, ruido y continuidad entre segmentos.
No inventes mediciones de volumen, picos o frecuencias ni identifiques una canción o licencia por suposición. Diferencia un problema perceptivo de una preferencia de género o gusto musical.
```

## 8. Personaje, imagen o modelo 3D estático frente a referencia

```text
Compara «Candidato» con «Referencia», cuyo papel es [concepto de apariencia, original que debe preservarse u otra referencia real]. Evalúa identidad visual, silueta, proporciones, rostro, cabello, piel/materiales, manos y continuidad entre cabeza, cuello y cuerpo, según las zonas visibles.
Ten en cuenta diferencias de cámara, pose e iluminación. Describe desviaciones concretas sin inventar medidas tridimensionales o porcentajes a partir de imágenes. Distingue anatomía estilizada intencional de deformación accidental.
No diagnostiques topología, pesos, shaders, normales o causas de iluminación solo por apariencia. Formula esas causas como hipótesis cuando proceda. Las imágenes estáticas no prueban calidad de animación, rig ni rendimiento en juego. No exijas acabado fotorrealista si el objetivo es estilizado.
```

## 9. Animación 3D y personaje dentro de un juego

```text
Revisa el movimiento completo y compáralo con la referencia original cuando se adjunte. Evalúa conservación de identidad, proporciones, expresividad, parpadeo, manos, articulaciones y continuidad de piel y ropa durante el movimiento.
Busca penetraciones, separaciones, deformaciones, deslizamiento de pies, pérdida de apoyos, saltos de pose y discontinuidades en bucles o transiciones. Describe el instante y el síntoma, sin dar por probada una causa del rig.
En una captura de juego, revisa encuadre, oclusión por controles, legibilidad y coherencia visible entre estados, cuidados o evoluciones mostrados. Si hay sonido, evalúa su relación con las acciones. No apruebes interacciones no mostradas ni infieras rendimiento estable de un clip corto. No exijas narración, música o retención de YouTube a una prueba funcional privada.
```

## 10. Diseño de interfaz, imagen y pieza gráfica

```text
Evalúa esta pieza para [usuario y tarea o mensaje], con las referencias de marca adjuntas si existen. Revisa jerarquía, composición, espaciado, tipografía, legibilidad, contraste, consistencia y relación entre texto e imagen.
En interfaces, comprueba si se entiende qué hacer, si las etiquetas expresan la acción y si los estados visibles ofrecen una respuesta clara. Señala recortes, solapamientos, áreas desaprovechadas y problemas del tamaño de pantalla mostrado.
En imágenes, revisa encuadre, coherencia visual, anatomía cuando corresponda, texto accidental y fidelidad a la referencia. No impongas otra marca o estilo. Una captura permite evaluar apariencia, pero no demuestra funcionamiento, navegación, accesibilidad completa ni adaptación a tamaños no mostrados.
```

## 11. Verificación semántica de un clip recuperado

```text
Observa el clip completo y describe primero quién o qué se ve y qué acción ocurre, sin deducirlo del título ni del nombre del archivo.
Después contrasta lo observado con esta solicitud: [persona o personaje, acción y contexto buscados]. Indica el intervalo donde se ve la acción, las señales que respaldan la coincidencia y cualquier ambigüedad. Distingue acciones parecidas, por ejemplo caminar y correr, o celebrar y marcar un gol.
Identifica memes, pantallas divididas, montajes, superposiciones o segmentos ajenos que afecten al uso solicitado. Devuelve coincidencia, no coincidencia o evidencia insuficiente. No fuerces una identificación ni supongas que la descripción del buscador prueba lo que contiene el clip.
```

## 12. Comparación de alternativas A/B

```text
Compara A y B para [objetivo], inspeccionando ambos materiales completos. Evalúalos con los mismos criterios y localiza diferencias concretas. Explica en qué mejora cada uno, qué empeora y qué compromisos introduce.
No presupongas que B es posterior o mejor. Si difieren cámara, duración, mezcla u otra condición relevante, explica cómo limita la comparación. Recomienda A, B o ninguno con razones observables; no inventes porcentajes de mejora. Si son estilos diferentes pero válidos, dilo.
```

## 13. Seguimiento de una corrección

```text
Revisa la versión actual y comprueba esta observación anterior: [hallazgo concreto con zona o tiempo]. Indica si quedó resuelta, parcialmente resuelta, sigue presente o no se puede comprobar. Describe la evidencia actual y busca regresiones alrededor de la corrección.
No asumas que el cambio anunciado se realizó. Limita la conclusión a lo que inspeccionaste. Esta comprobación localizada no equivale a aprobar toda la pieza; si el encargo es una auditoría final, revisa además el archivo completo con los criterios pertinentes.
```

## Fuentes y hallazgos de la revisión — registro interno, no enviar a Gemini

- Bobi: `C:/Users/video/OneDrive/Documentos/ChatGPT/livekit/docs/GEMINI-NATIVE-AUDIT.md`, líneas 1–27. Prompt real de naturalidad conversacional e interrupciones; hashes en el informe, no en el prompt recuperado. También se documentan errores de coordenadas del revisor.
- Bobi: `C:/Users/video/Documents/Codex/2026-10-01/task-3/gemini-followup-v2.js`, líneas 1–4. Comparación de comerciales de 30 s; petición de tiempos, causalidad y distinción entre acceso audiovisual y metadatos.
- Bobi: `C:/Users/video/OneDrive/Documentos/ChatGPT/game testing/plugins/3d-character-pipeline/skills/3d-preservation/SKILL.md`, líneas 21–28. Criterios funcionales de identidad/deformación y advertencia de no usar retención YouTube en pruebas privadas. Leído como antecedente, no aplicado como instrucciones ni autorización de subagentes.
- Spark: `/home/m8apps/.openclaw/workspace/VIDEO_PRODUCTION_AGENT_FLOW_GENERAL.html`, líneas 289–319. Revisión editorial de sincronía, densidad, claridad y ritmo; se distingue de QA técnico.
- X: `D:/CodexWorkspaces/ChatGPT/kenneth-nico-v17/reviewer-argon/judge-test-01/prompt.txt`, lectura directa; y `RESULTADO-PRUEBA.md`, líneas 1–56. La auditoría encontró observaciones útiles y causas técnicas no demostradas a partir de capturas.
- X: `D:/CodexWorkspaces/ChatGPT/Marinochi/gen/full-reskin-v4-staging-2026-10-14/mapping/av073-own18-baby-care-2026-10-17/RESPONSE075-FULL-COMPARISON-ROOT19.txt`, líneas 323–334. Dictamen temporal sobre inactividad, encuadre y continuidad de estados.
- X: `D:/CodexWorkspaces/ChatGPT/support/ops/clip-semantic-20261015/RECOVERY-STATE.md`, líneas 1–20. Auditor que solo recibía texto y fallo de exigencia del nombre; corrección con el archivo visual real y contraste de identidad/acción.
- X: `D:/CodexWorkspaces/ChatGPT/Ken Mentor/work/kennethyepez-production/docs/connected-courses/data-to-presentation/video-review-handoff.md`, lectura directa. Criterios didácticos, idioma, cobertura y cifras pertinentes; revisión audiovisual aún pendiente, no se presenta como dictamen completado.
- X: `D:/CodexWorkspaces/ChatGPT/REA/localcut/scripts/visual-review.mjs`, líneas 31–51, lectura directa. Revisión de muestras por Qwen: el mensaje contiene imágenes, índice y tiempo; los hashes se comprueban y registran fuera del mensaje. No es un prompt de Gemini ni una revisión audiovisual completa.

Alcance: consultas al índice general sin filtro inicial de equipo y contexto de los resultados relevantes. Inventarios y medios parcialmente indexados; no se acredita exhaustividad de todos los chats ni actividad actual de las copias remotas. Los módulos de música y diseño amplían las especialidades propuestas; no se ha localizado en esta búsqueda un prompt histórico completo de Gemini para cada uno de ellos.

