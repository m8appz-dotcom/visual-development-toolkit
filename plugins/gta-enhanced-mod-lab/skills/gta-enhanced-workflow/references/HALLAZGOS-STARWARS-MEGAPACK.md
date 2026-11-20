# Conversión del MEGA PACK de kjb33 a recursos Enhanced

Evidencia local del 14 de octubre de 2026. Descarga oficial: https://www.gta5-mods.com/vehicles/star-wars-mega-pack-add-on, versión 1.0, download ID 113372. RAR de 209156777 bytes, SHA256 `a03581dc27d615143b6b1590eba4f8c13711effb654def9c6bc9d46738322b3d`; integridad comprobada con UnRAR. Original `dlc.rpf`: 342022656 bytes. Archivos privados y reports en `D:/modding-lab/projects/gta-enhanced-marvel-lab/starwars-megapack`. El plugin no incluye los assets.

## Composición real y nombres

El DLC declara **26 modelos y 26 handling IDs**. El README contiene 25 nombres y omite `v19`; también dice `Spawn name - starwarspack`, aunque ese es el nombre del pack. Usar `vehicles.meta` como fuente de los nombres de spawn, no el nombre del DLC:

`arc170`, `awing`, `bwing`, `cloudcar`, `hansfalcon`, `jedintercept`, `jedinterceptx2`, `kylotie`, `lambda`, `naboosf`, `razorcrest`, `slave`, `snowspeeder`, `speederbike`, `tieadvanced`, `tiefighterx`, `tieintercept`, `tiephantom`, `tiestriker`, `uwing`, `v19`, `venator`, `vwing`, `xwing2`, `xwingsf`, `ywing`.

La inspección de tipos seleccionados obtiene 85 entradas; el recorrido completo de miembros hoja encuentra **97**. No confundir el subconjunto que extrae `inspect_mod_package` con todos los archivos de un RPF. Hay **52 YFT162** (base/hi de 26 vehículos) y **26 YTD13**, sin scripts externos en el RAR. Sus equivalentes Enhanced son YFT171 y YTD5. Metadatos, layouts y archivos auxiliares se conservan; cambiar la versión de la cabecera por sí solo no convierte modelos, buffers y shaders.

El aviso del autor sobre dual burners se refiere a scripts instalados aparte. La conversión de assets no porta ni crea esos scripts. Los recursos de alas, tren de aterrizaje, asiento, puertas, colisión y fragmentos físicos siguen dependiendo de huesos, tags, animaciones/layout del vehículo y llamadas del motor GTA.

## Calidad, LOD y texturas: datos medidos, no FPS

Los rigs principales tienen entre 24 y 45 huesos. Los 26 modelos base incluyen High; **25 no tienen Med**, y ningún base contiene Low/VLow en el drawable principal inspeccionado. A-wing sí tiene Med. Esto no es una auditoría de todas las variantes físicas ni un benchmark de streaming.

Ejemplos de vértices del drawable principal base: Razorcrest 457318, Falcon 325782, V-wing 292230, Jedi Interceptor 268976. No sumar base/hi/fragmentos/LODs como geometría visible simultánea. La conversión mantiene estos meshes; no crea LODs ni vuelve a modelarlos.

Los 26 YTD contienen **517 texturas**, **234 con un mip**. Hay dimensiones no potencia de dos: 700, 1920, 3000 y hasta **4356** en Snowspeeder. Conservar dimensiones, niveles y hashes de payload durante una conversión de formato. No imponer que todo sea 1024/2048 ni fabricar mipmaps como parte implícita de convertir; una futura optimización requiere medir uso, tamaño/VRAM, transparencia y calidad real.

La Razorcrest y Falcon de este pack de 2021 no equivalen automáticamente a las descargas individuales actualizadas con interior de años posteriores. Registrar versión y hash del recurso seleccionado.

## Reconstrucción y preservación de archivos

`convert_mod_assets` produce recursos sueltos; no recompone un DLC. La herramienta nueva **`rebuild_mod_package(folder, converted_resources)`** copia el RPF a una carpeta nueva, cambia solo los recursos convertibles seleccionados y reconstruye de los archivos internos hacia el contenedor exterior. Conserva metadatos y recursos auxiliares originales. Rechaza versiones incorrectas, recursos faltantes/huérfanos, inputs fuera de alcance, errores de lectura y cambios de miembros.

CodeWalker devuelve payload descomprimido al extraer recursos; reconstruir un `RSC7` con flags de la entrada antes de leerlo/converterlo. Verificar hash del payload reextraído del RPF generado contra el recurso convertido; el hash de bytes comprimidos puede cambiar por defragmentación/compresión sin un cambio lógico. Para miembros no convertidos, comparar payload y versión exactos. Excluir los contenedores RPF anidados de esa comparación de miembros hoja: sus bytes necesariamente cambian cuando cambian sus hijos.

El rebuild de este pack cambió **78 recursos** y conservó el conjunto de **97 miembros hoja**. Se comprueban los **52 fragmentos**, incluyendo **518 drawables** y **466 children físicos** contados entre base/hi y LODs físicos. Los recuentos incluyen referencias/variantes; no son 518 naves ni 466 objetos únicos visibles. Las firmas de geometría visible, índices, pesos, paletas, huesos y transformaciones se comparan exactamente; también se comprueban masas/tags físicos y metadatos de colisión.

El resultado local reconstruido ocupa **289473024 bytes** frente a 342022656 del original. La reducción proviene del empaquetado/defragmentación; no demuestra menor VRAM, menor coste de dibujo ni mayor FPS.

## Cuantización de colisiones: una diferencia esperada y acotada

Una comparación exacta de todos los XML de colisión rechazó inicialmente Jedi Interceptor. La causa comprobada en el código de CodeWalker es `BoundGeometry.CalculateQuantum()` / `BuildVertices()`: al guardar se recalcula Quantum y se codifican posiciones como enteros de 16 bits. El decode posterior puede variar una unidad de esa cuantización, aun conservando topología y dimensiones.

El verificador no ignora las colisiones: conserva exactos los polígonos, materiales, transforms y restantes metadatos; permite cambios de posiciones decodificadas como máximo **un quantum por eje más cuatro ULPs de float32**. Aplica la precisión propia de cada geometría y revisa tanto vertices como vertices shrunk. Valores no finitos y diferencias mayores bloquean el rebuild. Los tests aceptan una muestra dentro de su quantum y rechazan cambios que exceden la precisión, alteraciones de material/topología, mesh y huesos.

La versión 0.4.1 comprueba además que el quantum de una colisión modificada corresponda al cálculo desde su bounding box conservado, `(BoxMax-BoxMin)*0.5/32767`, con tolerancia de cuatro ULPs. No permite inflar Quantum para aceptar un desplazamiento arbitrario. La quinta muestra negativa prueba expresamente ese caso; una colisión exactamente igual al original no necesita requantización.

En los 52 YFT se observaron coordenadas requantizadas; la mayor diferencia medida es **0.00324 unidades de escena**, en Venator. No afirmar que las colisiones quedaron idénticas bit a bit. No repetir conversiones sucesivas sobre copias ya guardadas: comenzar desde el original verificado, porque la cuantización puede acumular deriva.

Otro fallo inicial del wrapper fue omitir `ShadersGen9Conversion.xml` junto al nuevo ejecutable. El readback Gen9 lo necesita incluso si el rebuild recibe archivos ya convertidos. La dependencia se copia desde el runtime existente mediante el `.csproj`; no atribuir ese error al mod.

## Uso y validación pendiente

1. `inspect_mod_package` sobre una copia extraída del pack; comprobar modelos, handling IDs y dependencias.
2. `audit_mod_assets` y `convert_mod_assets` sobre `resource_output`, manteniendo el original.
3. Comparar firmas de rigs/skinning y especificaciones/payload de YTD antes/después.
4. `rebuild_mod_package` con el directorio original que contiene el DLC y el `gen9_output` de la conversión. Se genera otra carpeta; no instala ni ejecuta scripts.
5. Reabrir el RPF generado, comprobar versiones, miembros/metadatos, y auditar los recursos extraídos. Usar la lista real de spawn. Evitar montar simultáneamente este DLC y las versiones individuales con los mismos modelos.

La lectura, conversión y rebuild **no certifican comportamiento ni apariencia dentro de GTA Enhanced**. Quedan pendientes materiales/iluminación, alas/tren/puertas, armas, burn effects, entrada/salida, asiento/cámara, choque/daño, colisión y presupuesto de streaming. Los casos stock del QA existente no prueban estas 26 naves. No ampliar la instalación fuera de staging ni lanzar un juego del usuario por haber convertido archivos.
