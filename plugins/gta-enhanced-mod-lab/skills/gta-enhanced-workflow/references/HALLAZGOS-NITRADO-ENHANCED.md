# FiveM Enhanced: montaje, personajes y aceptación

Caso privado del 15 de octubre de 2026, FXServer Enhanced b169 Linux y cliente build 3788. Los archivos, recibos y capturas permanecen en el proyecto autorizado. Esta nota no incluye archivos del juego, mods de terceros ni credenciales.

## Disco, índice servido y sesión son tres comprobaciones diferentes

Un paquete Star Fox tenía sus 105 archivos correctos por SHA256/tamaño en el servidor, pero el índice de streaming publicado conservaba solo 69 entradas y omitía los nombres nuevos. Iniciar el recurso después de sustituir una carpeta no bastó. Se detuvieron únicamente los cuatro paquetes modificados, se ejecutó `refresh`, se iniciaron y se comprobó el `cache/<recurso>/files.json` real. El índice regenerado incluyó las 105 entradas. La siguiente conexión fría cargó los reemplazos correctos.

No borrar cachés globales para resolver este caso. Conservar el índice anterior, verificar nombres/hashes del índice nuevo y registrar la sesión efectiva. Una transferencia de navegador encolada no equivale a un archivo completo: mantener su pestaña durante la subida y verificar después desde otra superficie. Reenviar solo los fallos estables; no reiniciar un paquete completo sin evidencia.

## Un reemplazo debe concordar con el formato gráfico del ped base

En una selección de 49 personajes, 17 bases tenían `IsStreamedGfx=true` mientras los YDD de origen eran paquetes completos con ese indicador falso. Esos 17 mostraron piezas de la base, mallas ausentes o deformaciones, aunque los nativos confirmaban modelo válido, visible y movimiento. Se consultó el `peds.ymt` del juego instalado mediante el lector normal de CodeWalker; no se modificó el juego.

Un piloto de metadatos sobre dos bases existentes no corrigió el resultado y se revirtió. Se eligieron 17 bases compatibles con `IsStreamedGfx=false`, género apropiado y cápsula correspondiente, conservando exactamente los payloads convertidos. Tras comprobar índice y conexión fría, los 17 pasaron carga, marcha, ragdoll/limpieza y revisión de capturas originales de frente/espalda. Los otros 32 conservaron sus resultados previos. Esto respalda esa corrección concreta, no una regla universal para todo ped.

No copiar esqueletos ni normalizar escalas por compartir tags. Un reemplazo también cambia el aspecto de cualquier NPC que use ese identificador. Guardar la relación nombre lógico/base, procedencia, hashes y rollback. La selección de personajes debe resolver el nombre lógico a la base realmente cargada.

## La prueba funcional no decide el encaje visual

Los 32 vehículos seleccionados cargaron, admitieron conductor, se desplazaron/condujeron o volaron y limpiaron sus entidades en un cliente real. Eso no prueba armas, personalización, todas las colisiones, todos los LOD ni replicación con otro cliente.

Mario y Luigi pasaron selección del jugador, creación del kart, asiento, conducción, salida y retirada mediante los comandos de juego. Las capturas frontales revelaron un asiento demasiado bajo respecto al volante. Mantener esa combinación pendiente de ajuste visual aunque la conducción pase. Medir huesos del ped y del vehículo antes de editar: en un control Mario, cabeza/manos quedaron más bajas que con el conductor base. Un piloto separado cambia solo el punto de asiento; requiere lectura binaria, comparación de contenido, montaje y nueva comprobación visual. No presentar un ajuste en preparación como aceptado.

Research Base pasó puntos fijos de exterior y dormitorio, marcha/colisión y lectura visual. Dos cortinas también se crearon y capturaron por separado. Son muestras concretas; no certificar todos los interiores ni afirmar que una cortina apareció en una zona que no la instancia. Una sesión antigua no registró los arquetipos; la sesión fría sí lo hizo.

## Los nueve poderes siguen siendo otro runtime

Batman, DBZ, Hulk, Iron Man, Spider-Man, Superman, Thanos, Flash y Thor tienen scripts principales que referencian `GTA.Script` y NIB de Story Mode; DBZ usa `NIBSHDotNet` y los principales Enhanced inspeccionados usan `NIBScriptHookVDotNet2`. No hay implementación CitizenFX correspondiente dentro de esa selección. La conversión Gen9 de recursos no porta esos poderes ni justifica cargar ASI/ENdll/ndll como recursos FiveM.

Conservar hashes y referencias de cada binario. Para avanzar hacen falta una implementación FiveM compatible con las funciones originales y las licencias del autor, y sus pruebas reales. No alterar autenticación/licencias, renombrar DLL para simular un port ni llamar completo al mod por añadir vuelo genérico. El autor mantiene como requisitos Script Hook V y NIBShDotNet: https://www.patreon.com/JulioNIB/posts/julionib-mods-34679963.

## Evidencia y límites

Guardar fallos anteriores junto a los resultados nuevos; no reemplazarlos por un booleano de aprobación. Distinguir archivo convertido, integridad remota, índice publicado, conexión efectiva, comportamiento, revisión visual y dos clientes. La revisión Gemini fue dispensada expresamente por el usuario para esta sesión; no transferir esa dispensa a otros proyectos o sesiones. Ninguno de estos resultados garantiza ausencia general de crashes.

## Resultado del piloto de asiento: revertido

La copia de Mario Kart 7 elevó únicamente el hueso de asiento 0,25 m. Las dos versiones YFT conservaron generación 171; la comparación XML binaria de vuelta mantuvo los otros contenidos salvo requantización de colisión máxima de 0,000036 m. La auditoría nativa de ambos archivos no detectó errores ni avisos. El servidor publicó el hash nuevo, pero un reinicio caliente conservó el prototipo anterior en el cliente; solo una conexión fría reflejó la nueva altura.

La vista frontal fría mostró la cabeza correctamente por encima del volante, pero también los pies demasiado altos. Un ensayo delimitado de objetivos IK para las piernas no corrigió esa pose de conducción, tampoco con el modo 2 aplicado exclusivamente al NPC de prueba. No generalizar ese resultado a todas las tareas o peds. Se retiraron el código experimental y los YFT del piloto y se restauraron los originales previamente probados. La conducción sigue pasando; el encaje Mario/Luigi en esos karts requiere una pose de conducción o retarget específico. Conservar esa limitación y los resultados fallidos; no promover una corrección que solo mueve el problema a otra parte del cuerpo.