# Hallazgos reutilizables: mapas, interiores, objetos, vehículos y misiones

Investigación y análisis local del 14 de octubre de 2026 con Visual Development Toolkit, ILSpy y CodeWalker. Versiones de GTA: Enhanced 1158.16 en esta PC. No se instalaron estos mods en el juego ni se probaron sus escenas o misiones. El contenido de los autores y los dumps decompilados quedan en carpetas privadas, fuera del plugin.

## Evidencia y selección correcta

Se descargaron ocho paquetes originales, 611075356 bytes, con SHA256 e integridad ZIP/RAR comprobados: Kush Park1.6 Enhanced, Remastered6.0-SP, Burgershot2.1 Enhanced, Island Research Base1.0.1, Scene Lights1.7, Jesko Attack1.0, Citation X1.1 Enhanced y Mini Heists1.1. SP Festive Surprise2.9 muestra «file is no longer available» en su descarga oficial. LSPDFR Enhanced1158.16 bloqueó el acceso HTTP403; no se sustituyó por mirrors ni se analizó un binario ausente.

Las etiquetas de la página y el archivo predeterminado no bastan: Burgershot, Kush Park y Citation X ofrecen una descarga Enhanced distinta de la marcada current. Scene Lights, Remastered, Research Base y Jesko incluyen ramas alternativas en un mismo archivo. Elegir solo una rama y no combinar identidades duplicadas de esas variantes.

Se inspeccionaron 2259 entradas dentro de RPF, incluyendo variantes Legacy y Enhanced, y 786 recursos mediante el auditor nativo. Resultado: cero errores de lectura/estructura en esos controles; 210 archivos emitieron advertencias. Estas cantidades incluyen variantes y no son un conteo de assets únicos. No acreditan ausencia de crashes, buen rendimiento ni calidad visual.

Evidencia privada: `D:\modding-lab\projects\gta-enhanced-marvel-lab\category-expansion\reports\evidence-summary.json`, `rpf-graph-v2.json`, `native-expanded-audit.json`, `mini-heists-pe.json`; manifiesto de originales: `category-expansion\downloads-manifest.json`.

## RPF y generaciones: una extracción puede producir falsos errores

`RpfFile.ExtractFile` de CodeWalker devuelve el payload ya descomprimido de los recursos, sin el contenedor RSC7 autónomo. Para leerlo con `YmapFile.Load(byte[])` o exportarlo como recurso independiente, reconstruir RSC7 con `ResourceBuilder.Compress(payload)` y `AddResourceHeader(entry, compressed)` conservando SystemFlags/GraphicsFlags/version de la entrada. Verificar que descomprimir devuelve el payload idéntico. También se puede usar el overload `Load(payload, entry)` apropiado para análisis en memoria.

Nuestro primer wrapper trató el payload como un archivo autónomo y generó falsos errores de compresión. Se corrigió el wrapper; no los mods. La segunda lectura de las 2259 entradas pasó. Mantener el informe inicial como evidencia del fallo de herramienta, no como prueba de un asset corrupto.

Versiones observadas en las ramas Enhanced: YDR/YDD159, YFT171 y YTD5. YMAP/YTYP2 y YBN43 aparecen en los mapas Enhanced correctos: no bloquearlos por un supuesto número Gen9 universal. Detectar versión por tipo. No reconvertir archivos que ya sean Gen9 ni imponer reglas de esqueletos humanoides a fragments de vehículos/props.

## Mapas y edificios: referencias, colisión y portales

El DLC usa `setup2.xml`/`content.xml` para montar archivos. YMAP coloca entidades y sus referencias a archetypes; YTYP define modelos y, en los MLO, habitaciones/portales; YBN contiene colisión. Colisión también puede estar embebida en drawables/fragments, por lo que ausencia de un YBN independiente no demuestra ausencia de colisión.

Burgershot contiene 404 entidades, 69 archetypes, 8 habitaciones MLO y 15 portales en la rama SP inspeccionada. Kush Park tiene 2727 entidades, 301 archetypes y 11 YBN; también registra 3 habitaciones y 7 portales. Esto permite comprobar integridad y referencias antes de probar puertas, colisiones, iluminación y streaming dentro del juego.

Los hashes de entidades no definidos en el paquete pueden pertenecer al juego base u otros DLC. Reportarlos como dependencias externas pendientes; no declararlos automáticamente errores. Las identidades duplicadas entre Legacy/Enhanced tampoco prueban un conflicto si se instala solo una variante.

Research Base declara edificios con interiores, pero las definiciones inspeccionadas no tienen habitaciones ni portales MLO. No deducir aislamiento de luz, audio u occlusión MLO a partir de «interior» en el anuncio. Su FiveM incluye otro recurso para props médicos; su equivalente/dependencias en Story Mode requiere una revisión separada.

El cliente Lua de Burgershot FiveM oculta una puerta vanilla con `CreateModelHide` y declara TIMECYCLEMOD_FILE y SCALEFORM_DLC_FILE. Copiar solo los meshes no reproduce ese comportamiento. Un paquete FiveM no equivale a un DLC SP ni a una garantía de soporte FiveM Enhanced.

## Reflexiones y rendimiento: advertencias concretas

El README de Remastered Enhanced advierte, a fecha abril2025, que sus modelos dedicados de reflexión pueden producir rectángulos alrededor de vegetación cuando el juego usa la ruta de reflejos sin el ajuste indicado de ray tracing. Describe que RT y Ray Traced Reflections en Very High/Ultra evitan esa ruta. No aplicar esos ajustes a ciegas: comprobar la versión actual, medir rendimiento y capturar ambas rutas antes de atribuir el artefacto a una textura rota.

Scene Lights Enhanced registra 90 drawables y 90 archetypes de luces. Revisar intensidad, luces volumétricas, sombras y coste según cantidad visible; no hay un umbral de FPS medido en esta investigación.

La descripción de Jesko anuncia texturas4K/8K; el YTD Enhanced descargado contiene 59 texturas y la dimensión máxima medida es2048. El archivo real prevalece sobre el anuncio. Su drawable principal tiene67 huesos, 271260 vértices y solo un modelo High en la estructura observada, tanto en base como `_hi`. Es una señal para revisar LOD y coste; el resumen del drawable no constituye una auditoría exhaustiva de todos los hijos del fragment.

Citation X tiene73 huesos en los fragments principales; el `_hi` registra318434 vértices. Sus dos YTD incluyen dimensiones8192; hay17 texturas de un solo mip entre ambos diccionarios. Revisar uso/material antes de generar mips: algunos targets/UI pueden necesitar un solo nivel. Ninguna de estas cifras prueba un crash por sí sola.

## Vehículos: el rig no es un personaje

`vehicles.meta` conecta modelName, txdName y handlingId; `handling.meta` define física; carvariations y layouts añaden configuración. Deben coincidir con las identidades de YFT/YTD y los registros content.xml. Pruebas dentro del juego: spawn, ruedas/tren de aterrizaje, asientos, puertas, cristales, luces, daños, cambio de LOD y despawn. La integridad de índices/pesos no verifica estas interacciones ni handling.

El content.xml de Jesko marca archivos con `disabled=true` y después los activa en `filesToEnable` del change set `kja24_AUTOGEN`, seleccionado por `GROUP_STARTUP` en setup2.xml. No concluir que el DLC está deshabilitado leyendo un solo atributo; seguir el grupo y el change set que se ejecutan al cargar. Respetar namespaces dlc_kja24 y rutas %PLATFORM% al comprobar referencias.

Fuentes: https://www.gta5-mods.com/vehicles/koenigsegg-jesko-attack-add-on-legacy-enhanced y https://www.gta5-mods.com/vehicles/cessna-750-citation-x-add-on-sounds-legacy-enhanced . Verificar aparte los complementos opcionales ELS/VehFuncsV; no extender la compatibilidad del modelo a esos scripts.

## Mini Heists: lógica recuperada y riesgos acotados

El ZIP contiene `DrugMeetups2.dll`/`.ini`, no `MiniHeists.dll`. PE metadata confirma referencia a ScriptHookVDotNet2 versión2.11.6.0. El autor indica SHVDN Enhanced para esta edición; no confundir esa dependencia con NIBScriptHookVDotNet2 de JulioNIB.

ILSpy recuperó C# de una copia importada con hashes. Falta resolver referencias en el proyecto decompilado y aparecen anotaciones de tipos desconocidos: se usa como evidencia del flujo, no como fuente original recompilable ni decompilación perfecta.

El constructor suscribe Tick y Aborted. OnShutdown intenta limpiar entidades, props y blips. El mod usa ubicaciones/estados, natives de GTA, modelos y animaciones ya disponibles; no requiere un mapa nuevo para aportar nuevas misiones.

En `spawnproptolistrdr`, después de `Model.Request(10000)` hay `while(!IsLoaded)` con Wait50 pero sin deadline visible, y otra espera sin límite por la entidad. `spawnpedtolist` y `spawnvehicle` también esperan indefinidamente si no aparece el handle. Inferencia: una falla de carga/creación puede dejar suspendido el flujo del script; no afirmamos haber observado un crash. Para nuestros scripts: estados de carga/creación, timeout total, cancelación, fallo explícito y cleanup, sin repetir efectos tras un fallo incierto.

La lectura INI solo aplica el fallback si hay excepción; un valor vacío puede llegar a `int.Parse`. Inferencia: una configuración vacía/inválida puede lanzar FormatException. Para nuestros scripts: TryParse, defaults y rangos. P/Invoke a kernel32 sirve para el INI: su presencia no prueba manipulación de memoria del motor. El ajuste LodDistance8000 requiere medición, no copiarlo como estándar.

Fuente autor: https://www.gta5-mods.com/scripts/mini-heists . El autor anuncia32misiones; este análisis no ejecutó ni verificó las32.

## Herramientas nuevas y límites

- `inspect_mod_package`: lee RPF anidados en una carpeta ya extraída, exporta una copia con flags preservados y reporta generaciones, entidades/archetypes, habitaciones/portales y metadata vehicular. Mantiene los originales. Los archivos sueltos YMAP/YTYP/YBN se cuentan pero esta herramienta no los interpreta como entradas RPF. No convierte ni instala DLC.
- `review_mod_script_source`: señala patrones C#/Lua con archivo/línea. Son heurísticas para revisión, no bugs confirmados ni certificado de seguridad. Necesita fuente original o decompilada autorizada; no ejecuta el código ni decompila por sí sola.
- `read_mod_field_notes`: devuelve estos hallazgos y su hash.

Se conservan el alcance de instalación staging, el registro de rollback y el lease del coordinador QA. No cambiar recursos ajenos para hacer pasar una prueba. La actualización del plugin no instala estos paquetes en GTA.
