# Dragon Ball, Street Fighter, Star Wars, DC, Mario, Mario Kart y Star Fox

Inspección local del 14 de octubre de 2026. Las observaciones siguientes proceden de archivos descargados de los autores, hashes, metadatos PE, recursos nativos, manifiestos OIV y decompilación con Visual Development Toolkit / ILSpy. No se ejecutaron estos mods en GTA. No hay aprobación visual, de rendimiento ni de ausencia de crashes.

## Evidencia y límites

Trabajo privado: `D:/modding-lab/projects/gta-enhanced-marvel-lab/franchise-expansion`.
Consultar `downloads-manifest.json`, `reports/asset-package-analysis.json`, `reports/evidence-summary.json`, `reports/oiv-actions.json`, `reports/rig-comparison.json` y `reports/toolkit-decompilation.json`. El proyecto aislado del Toolkit es `D:/modding-lab/projects/gta-enhanced-franchise-analysis`. Las copias importadas se verifican con `verify_originals`.

Los números de vértices suman componentes/LODs del recurso inspeccionado; no son automáticamente el coste visible simultáneo. Los recuentos de archivos pueden incluir instaladores, desinstaladores, backups y alternativas. Contar solo la variante elegida al preparar una instalación.

No distribuir archivos originales, recursos extraídos ni decompilados dentro del plugin. Los enlaces de descarga pueden cambiar; conservar origen, nombre del archivo, versión/edición y SHA256. La presencia de un archivo en un ZIP no demuestra que su instalador lo active.

## 1. La extensión no determina el formato

`pedpersonality.ymt` del instalador y desinstalador Star Fox empieza por `PSIN`: es PSO binario, no un recurso `RSC7` comprimido. El auditor antiguo daba un falso error de compresión al invocar siempre `YmtFile.Load(byte[])`. El auditor 0.3.0 distingue la cabecera y usa la ruta de entrada binaria para PSO/RBF. Ambas muestras PSO se leen correctamente después de la corrección.

Nunca concluir que el mod está dañado por un error de descompresión sin comprobar cabecera y contexto. Mantener rechazo de metadatos truncados o sin formato reconocido. YMT2, YMAP2 y YBN43 no indican por sí solos una incompatibilidad con Enhanced.

`.ENdll` y `.ndll` también pueden contener ensamblados PE/.NET. El auditor incluye ambas extensiones y lee referencias sin ejecutar el código. Renombrar un `.ndll` a `.dll` o `.ENdll` no convierte sus llamadas, runtime, carga o licencia.

## 2. Dragon Ball: componentes y runtime separado

Goku All in 1 1.1 contiene un ped `rare_dragonb_goku` con YDD165, YFT162, YTD13 y YMT2: los recursos de dibujo/texturas requieren conversión para Enhanced. Su YFT tiene 98 huesos; el YDD contiene 22 drawables y suma 141031 vértices, con High y sin Med/Low/VLow en esos drawables. El YTD contiene 66 texturas, dimensión máxima 2048. No confundir todas las variantes de ropa/cabello con geometría visible a la vez.

Las seis configuraciones incluidas apuntan al mismo modelo y seleccionan componentes/variaciones/texturas. `transformation_level`, `max_transformation_level`, salud y coeficientes son datos para el script DBZ, no nuevas mallas completas ni lógica de combate dentro del YDD. Validar rangos y disponibilidad del componente en el YMT antes de aplicar una transformación.

El archivo descargado `DBZ mod R2d - GTA 5 Legacy.zip` instala `DBZ-NibStyle.ndll`. La referencia de ensamblado encontrada es **NIBSHDotNet 0.0.0.0**. No es `NIBScriptHookVDotNet2` de los paquetes Enhanced DC. Convertir Goku a Gen9 no porta este script a Enhanced. Mantener pendiente un build Enhanced del autor o un script propio con APIs verificadas.

Fuente: https://www.gta5-mods.com/player/goku-from-dragon-ball-saga-all-in-1-add-on-replace y https://www.patreon.com/posts/17186450.

## 3. Los rigs no son intercambiables

Goku, los seis personajes Mario y Darth Vader tienen 98 huesos, pero sus firmas completas no coinciden. Usando tags para comparar contra Goku, cambian las traslaciones locales de 55 huesos en Mario/Luigi, 59 en Baby Mario/Baby Luigi/Wario/Waluigi y 44 en Vader. Compartir 98 tags no garantiza iguales índices, padres, offsets, pose de reposo o escala.

Street Fighter Pack contiene Ryu, Ken, Guile y Cammy. Los tres primeros resuelven 104 huesos y Cammy 101; todos comparten 98 tags con Goku, con offsets distintos. No copiar un esqueleto de 98 huesos sobre ellos descartando los extras. El paquete son cuatro peds con recursos Gen8, texturas y variantes; no contiene un sistema de combate Street Fighter.

Los cuatro peds Street Fighter, los seis Mario, Goku y Vader pasan las comprobaciones estructurales de pesos, índices y jerarquía. Eso **no** demuestra ausencia de deformación. El autor Mario informa problemas al conducir y en bicicletas. La conversión de formato conserva el rig; no corrige por sí sola esos problemas.

Para un rig propio: comparar tags, padres, índices, matrices/transformaciones de reposo, paletas por geometría, pesos y componentes. Probar locomoción, agachado, apuntado, manos, cara, ragdoll, subir/bajar vehículos y contacto con asiento/pedales/volante. Resolver IK y proporciones con el modelo y el asiento elegidos, sin normalizar todas las figuras al rig de un humano alto.

Fuentes: https://www.gta5-mods.com/player/street-fighter-pack-add-on y https://www.gta5-mods.com/player/super-mario-plumbers-add-on-ped-mariobabyluigi.

## 4. DC Enhanced: script, animación, props y configuración

Se descargaron los adjuntos **Batman - GTA Enhanced.zip**, **Superman V2.2 - GTA 5 Enhanced.zip** y **TheFlash - GTA 5 Enhanced.zip**. Sus scripts principales son `Batman.ENdll`, `Superman V2.ENdll` y `TFlash.ENdll`. Los tres referencian **NIBScriptHookVDotNet2 2.11.6.0**, además de bibliotecas .NET/audio. No sustituir este runtime por el SHVDN clásico solo por compartir un número de versión.

ILSpy produce C# con nombres y flujo ofuscados y referencias sin resolver. La salida permite inspeccionar metadatos y algunos puntos de integración; no reconstruye automáticamente una implementación clara de todos los poderes. No quitar ni alterar licencias, autenticación o protecciones. Preferir código propio para nuestras mecánicas.

Batman contiene props Gen9 YDR159/YTD5/YPT71 y 22 archivos YCD46. Flash contiene un prop YDR159 y YTD5. Superman incluye recursos Gen9, animaciones compartidas, configuraciones de trajes y complementos opcionales. El script coordina el comportamiento; YCD aporta animaciones, props/partículas aportan efectos y los INI seleccionan modelos/ajustes.

El paquete Superman conserva materiales de empaquetado anidados: un `Superman V2.ndll` antiguo referencia NIBSHDotNet y hay ASI dentro de ese contenido. Sin embargo, el manifiesto principal apunta a `Scripts/Superman V2.ENdll`, no a ese `.ndll` antiguo. Seguir las acciones del manifiesto; no copiar recursivamente todo el contenido al juego. Tampoco contar 369 YCD de la extracción como 369 movimientos únicos: existen copias y ramas internas.

Los instaladores DC escriben las mismas rutas `Scripts/NAudio.dll` y `Scripts/DirectShowLib-2005.dll`; Superman las repite desde varias ramas. Comparar hash y versión por destino antes de fusionar. Instalar poderes de uno en uno y verificar convivencia y cleanup; restaurar la copia previa del usuario, no una DLL genérica de otro ZIP.

Fuentes: https://www.patreon.com/posts/55602231, https://www.patreon.com/posts/100507185 y https://www.patreon.com/posts/14610884.

## 5. Mario Kart: vehículo, pista y reglas son partes distintas

El DLC karts 0.2 declara tres modelos/handling IDs: `mariokart7`, `luigiskart7`, `mariokart8`. Contiene seis YFT162 y tres YTD13. Las geometrías principales inspeccionadas son High; algunos karts superan 100000 vértices por recurso y se repiten en base/hi. Los YTD incluyen texturas de un solo mip; medir su uso antes de considerarlas un defecto o cambiarlas todas.

Luigi Circuit 0.3 contiene una entidad YMAP, un archetype YTYP, un drawable YDR165, una YTD13 y una colisión YBN43. Es una pista dibujada como un recurso, no un conjunto de checkpoints ni reglas de carrera. No tiene MLO rooms/portals. Los ZIP examinados no traen scripts de ítems, boost, vueltas, clasificación o multijugador.

Para nuestro modo Kart: separar assets, colisión, handling/vehículo, cámara/asiento, checkpoints/validación de vuelta, respawn, ítems y autoridad de carrera. Comprobar las deformaciones Mario en el kart concreto. No inferir que una pista y un skin de Mario ya producen Mario Kart completo.

Fuentes: https://www.gta5-mods.com/vehicles/mario-kart-7-karts-add-on y https://www.gta5-mods.com/maps/mario-kart-wii-luigi-circuit.

## 6. Star Wars y Star Fox: variantes y cambios compartidos

Vader trae texturas máximas 4096 y LODs High/Med/Low/VLow en sus dos drawables YDD; no trae un YLD separado. Su aspecto, capa y poderes requieren pruebas específicas. Arwing separa Add-on, Replace y Backup Copy. El add-on declara model/handling `arwing`; su rig tiene 46 huesos y las copias de respaldo Lazer 50. No tratar backups como variantes listas para instalar. Arwing es un avión/handling dentro de GTA, no una campaña Star Fox.

El Mega Star Wars Vehicle Pack Enhanced de Nexus no se pudo descargar: el sitio respondió HTTP403. Su descripción no equivale a una inspección de sus 35 vehículos. No atribuirle checks de recursos, rigs o rendimiento que no se realizaron.

Star Fox 1.1 distribuye armas, voces y metadatos en OIV; el DLC de personajes es una descarga adicional. El enlace a los modelos se recuperó del ZIP oficial 1.0 y se descargó el archivo público del autor. No afirmar que esa procedencia acredita la revisión 1.1 de las texturas: comprobar los archivos del DLC por separado. El enlace manual de 1.1 solo contiene armas/voces/metadatos, no los peds.

El DLC separado se inspeccionó: 107 entradas, 26 YDD165, 26 YFT162, 26 YMT2 y 26 YTD13; los 104 recursos nativos pasan la lectura estructural. Los rigs resuelven 98 o 104 huesos y hay texturas de hasta 4096. Necesita conversión de los recursos Gen8; sus nombres/paletas no validan facial animation ni poses dentro de Enhanced.

El ZIP de modelos ocupa 237026095 bytes, pero el `dlc.rpf` se expande a 5800542720 bytes. La extracción de sus entradas seleccionadas produjo 246223405 bytes. Esto mide el contenedor y el output de análisis, no VRAM ni memoria requerida en juego. Para analizarlo se extrajo por streaming ese archivo concreto verificado y se ejecutó el auditor de paquetes con sus límites de entradas/payload intactos. El MCP conserva su límite normal de input de 3 GB; no se amplió para todos los paquetes.

El manifiesto OIV 1.1 tiene 120 acciones registradas y el desinstalador 99. Reemplaza armas/voces y metadatos compartidos: `relationships.dat`, `game.dat151.rel`, `pedpersonality.ymt`, loadouts, pickups y entradas de armas de DLCs. Es más amplio que un simple Add-on Ped. Sus directorios con nombres `.rpf` son rutas de destino del instalador, no necesariamente contenedores RPF reales.

No ejecutar el OIV ni su desinstalador para investigar. Fusionar las entradas necesarias contra el build Enhanced actual y usar backups propios por archivo/destino. Restaurar un archivo vanilla incluido en el desinstalador puede borrar cambios de otros mods o usar una versión de otra build. Los ajustes de heap/gameconfig Legacy enlazados en un README no quedan aprobados para Enhanced por ese enlace.

Fuentes: https://www.gta5-mods.com/player/darth-vader-star-wars-battlefront-2-4ktextures-add-on, https://www.gta5-mods.com/vehicles/star-fox-arwing, https://www.gta5-mods.com/player/star-fox-addon-pack-add-on-ped-wolffire23309 y https://www.nexusmods.com/gta5enhanced/mods/1279.

## Procedimiento reutilizable

1. Inventariar ZIP/RAR/OIV y sus dependencias adicionales. Separar revisiones, edición y alternativas. Extraer OIV como ZIP; inspeccionar `assembly.xml` sin ejecutar instaladores.
2. Recorrer las acciones reales, incluyendo archive chains, reemplazos, borrados y destinos compartidos. Calcular hashes por destino. Conservar el contenido original del usuario para rollback.
3. Detectar formato por cabecera/entrada, no solo por extensión. Auditar recursos y ensamblados sin ejecutar. Tratar salidas ofuscadas como evidencia parcial.
4. Convertir solo assets elegidos a un nuevo directorio. Comparar firmas de rigs/pesos/índices y datos de texturas antes/después. La conversión no porta scripts ni valida poses.
5. Diseñar lógica propia con límites de carga, timeout/cancelación y cleanup. Probar primero una mecánica y después rig, efectos, vehículos y convivencia. Reservar el veredicto de estabilidad y apariencia para pruebas reales.

Los inputs excesivamente grandes se inspeccionan explícitamente y con límites de extracción documentados. No ampliar de forma general los límites de todos los MCP ni retirar sus controles para aceptar un paquete.
