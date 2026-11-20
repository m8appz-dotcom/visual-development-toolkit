# Revisión del MCP para calidad de rigs — 2026-10-21

## Conclusión

Ampliar el MCP existente. El puente hacia AccuRIG ya permite el recorrido real; falta un contrato de estado sólido y un ciclo de inspección, corrección y validación. Rehacer el motor de rigging no se justifica con la evidencia disponible.

Esta entrega es un análisis. No cambia el controlador, su configuración ni la aplicación. Se consultó `accurig_status` por el MCP instalado: sesión desconectada, sin trabajo activo. No se abrió AccuRIG. Se reutilizó por MCP el trabajo REA existente y se comprobaron los hashes de background.js, 2.js y preload.js contra runtime-lock.json: coinciden. Las capacidades adicionales descritas abajo están comprobadas en código; todavía no están probadas como herramientas de control.

## Defectos que deben preceder a nuevas funciones

| Prioridad | Evidencia actual | Mejora y criterio de aceptación |
|---|---|---|
| Alta | src/accurig.mjs:54–62: un segundo rig del mismo actor puede encontrar su GLB anterior inmediatamente. La lectura valida estructura, pero no que pertenezca a la nueva generación. | Identificar cada generación y exigir su finalización nativa y un artefacto asociado. No basta exigir un hash distinto: un rig idéntico puede ser determinista. Probar dos generaciones del mismo actor y fallo de la segunda. |
| Alta | `rigged` es un booleano; no se invalida al empezar otra generación. `close` tampoco limpia modelo/rigged. Una importación fallida puede conservar el modelo anterior en memoria. | Revisiones de modelo, articulaciones, skin y exportación. Invalidar resultados antes de mutar; limpiar estado al cerrar. Un fallo nunca debe habilitar exportar un resultado anterior como nuevo. |
| Alta | export comprueba que no existe el FBX, pero copyPreview usa copyFile sobre el GLB hermano sin esa comprobación. Solo comprueba tamaño mínimo del FBX; registra su cabecera sin validarla. | Reservar todos los destinos; rechazar colisiones del FBX y del GLB. Validar formato y reimportar el FBX. Probar un GLB previo sin FBX, conservando su hash. |
| Alta | Timeout de Runtime.evaluate no cancela necesariamente el SDK nativo. El trabajo puede quedar failed y liberar active mientras AccuRIG continúa. Los trabajos en disco no reconstruyen por sí solos una sesión. | Estado de operación incierta, reconciliación con proceso/actor/fase nativa y bloqueo de nuevas mutaciones hasta resolverla. No reintentar a ciegas ni prometer cancelación instantánea. |
| Media | load depende del texto inglés `Rig Body` y processTitle 2; se registran versiones/hashes, pero no se exige compatibilidad al conectar. | Adaptador explícito para AccuRIG 2.1.1, comprobación de contratos/capacidades y transiciones independientes del idioma. |

## Funciones originales aprovechables

Fuentes: preload.js expone los canales, 2.js implementa sus handlers y background.js contiene los wrappers del SDK. El grafo REA también localizó setJointPosition y convertRotationActorCoreToAutoRig en background.js. Esto acredita los wrappers JavaScript, no una implementación nativa recuperada completamente.

| Capacidad | Código original | Uso recomendado para agentes |
|---|---|---|
| Ajustar articulaciones | setJointPositions, setJointRotation, setJointsInfo, resetJoints, getJointInfo | Ediciones pequeñas con nombres válidos, unidades y marco de coordenadas explícitos; lectura posterior y rollback. |
| Simetría y centro | bodyDetect acepta parámetro; renderer ofrece centro de columna y simetría; getJointsInfo(true) modifica dedos | Separar consultar de aplicar simetría. No imponer simetría a anatomías deliberadamente asimétricas. |
| Manos diferentes | setFingerNum, canSetJointMask, setJointMask, isJointMasked; fingerDetect admite Both/Left/Right | Configuración anatómica explícita, máscaras válidas y detección por mano. Verificar enums y semántica antes de exponerlas. |
| Guardar correcciones | saveJointAsINI, loadIniFromCheck, loadINIJoint | Checkpoints con hash del modelo, transformaciones, configuración de dedos y datos de articulaciones. Un INI de otro modelo no debe aplicarse silenciosamente. |
| Calibrar | setMotionOffset, saveOffsetData, exportOffsetAvatar | Separar calibración de colocación de joints. Conservar el avatar calibrado y validar su exportación. |
| Exportar para destino | setTarget, setMeshMotionMode, setEmbedPose, setImageSize, setFPS, isCompatibleWithExportOption | Presets explícitos para Blender/Unity/Unreal, con opciones compatibles y comprobación independiente del archivo. |

Trampas de contrato verificadas: getJointsInfo(true) escribe articulaciones; setJointMask devuelve el estado masked (false puede ser un éxito al quitar máscara); setJointsInfo puede devolver undefined al completar correctamente. Por tanto, no generalizar «truthy = éxito». Hay conversiones de rotación ActorCore/AutoRig: no enviar coordenadas del visor al SDK sin verificar el espacio y las unidades.

La interfaz de exportación de app.282cb366.js prefiere selectedActor.offsetIAvatar cuando existe. El MCP actual selecciona siempre iAvatar. Al añadir calibración debe cambiar también esa selección; de lo contrario podría exportar el avatar sin las correcciones.

## Contrato propuesto

Mantener las herramientas actuales por compatibilidad y añadir operaciones delimitadas, evitando una herramienta de JavaScript arbitrario:

1. `inspect_model`: geometría, materiales, escala/orientación observadas y problemas de entrada; no reparar geometría silenciosamente.
2. `detect_joints`: detección separada de skinning; cuerpo/manos configurables.
3. `inspect_rig`: informe compacto y detalle bajo demanda de joints, simetría, máscaras y distribución de pesos.
4. `edit_joints`: cambios por lote, precondición de revisión, coordenadas explícitas, snapshot y lectura posterior. Invalidar skin/exportación.
5. `save_checkpoint` / `restore_checkpoint`: restauración vinculada al modelo y contrato de AccuRIG.
6. `build_skin`: caracteriza las articulaciones actuales sin redetectarlas ni borrar las correcciones.
7. `validate_rig`: inspección estructural, batería de poses y evidencias visuales.
8. `export_rig`: destino, formato soportado, avatar calibrado y validación del archivo exportado.

Un agente debería seguir inspeccionar → detectar → revisar → corregir → generar skin → probar poses → exportar. Si falla una validación, corregir únicamente la región afectada, con límite de intentos y comparación contra el checkpoint anterior. No volver a ejecutar toda la detección automáticamente.

## Qué debe significar calidad

La prueba anterior de Pete confirmó importación/exportación, pesos positivos en 31.134 vértices y movimiento de un brazo. El test de Blender solo exige que algún vértice muestre desplazamiento mayor que un mínimo. Eso no mide corrección anatómica, suavidad, conservación de volumen ni calidad de todas las regiones.

La aceptación futura debe combinar:

- Integridad: jerarquía coherente, transformaciones finitas, matrices de bind válidas, pesos no negativos y normalizados, índices válidos y cobertura de vértices según las mallas que deban deformarse.
- Anatomía: articulaciones y longitudes plausibles respecto del tamaño del modelo; simetría solo cuando corresponda, dedos separados y máscaras acordes a la anatomía.
- Deformación: ambos hombros/codos, caderas/rodillas, torsión de torso, muñecas y cierre de dedos; detectar colapsos, estiramientos anómalos y movimiento de regiones ajenas. Algunas intersecciones son contactos válidos: requieren contexto y revisión.
- Inspección visual: modelo real desde frente, perfil y espalda, detalle de manos y poses; visor interactivo. Un valor numérico no sustituye esta revisión.
- Exportación: reimportar el archivo final y comprobar escala, orientación, materiales, jerarquía y deformación, también después de calibrar.

Devolver `passed`, `needs_review` o `failed` por comprobación, con medidas, región, evidencia y siguiente acción. Calibrar umbrales contra modelos aceptados; no inventar una puntuación global de «calidad 95%».

## Orden recomendado y pruebas

Primero corregir generación obsoleta, revisiones/invalidación, colisiones de archivos y timeouts inciertos. Después integrar inspect_rig y validate_rig. Luego exponer corrección/checkpoints y separar detección de skinning. Finalmente añadir calibración y presets de exportación.

Usar Pete, Bianca y Craig existentes para comparación, más casos autorizados que representen asimetrías, manos distintas y geometría difícil. Añadir pruebas de segunda generación del mismo actor, importación fallida tras éxito, cierre/reconexión, interrupción nativa, colisión del GLB y exportación de avatar calibrado. Medir falsos éxitos, intervenciones necesarias, deformación y reproducibilidad. No dar por validado todo AccuRIG por tres modelos ni por un único brazo.

El SDK nativo sigue siendo una frontera: la decompilación JavaScript acredita controles disponibles, pero no demuestra que permita corregir pesos por vértice. No prometer una herramienta de pintura de pesos nativos sin verificar una API real para ello.
