# Crear mods propios para GTA V Enhanced

Revisión del 14 de octubre de 2026 con Visual Development Toolkit. Evidencia local en `reports/`; fuentes primarias enlazadas junto a cada tema. Esta revisión acredita inspección y pruebas de archivos, no estabilidad ni apariencia dentro del juego.

## Lo que encontramos en esta PC

- Host: BOBI-ALMAX. Juego: `D:\Downloads\GTAVEnhanced\GTA5_Enhanced.exe`, versión de archivo **1.0.1158.16**.
- Script Hook V ya instalado: **3889.0.1158.13**. El log existente registra inicialización correcta como `VER_EN_1_0_1158_13` y carga de EnhancedNativeTrainer. Es evidencia histórica de ese trainer, no de los mods nuevos; no tratamos la diferencia entre versión del EXE y clasificación interna como incompatibilidad automática.
- Los 14 paquetes descargados conservan sus SHA-256 originales. Se inspeccionaron **15 instaladores OIV** y se leyeron **366 archivos nativos/ensamblados**, incluyendo **332 recursos**, mediante CodeWalker y metadatos .NET. Entre ellos hay 167 diccionarios YCD de animación y tres recursos YPT de partículas. Leer sus estructuras no prueba todavía su aplicación a cada personaje.
- Se identificaron **36 recursos de skins Gen8**: 11 YDD, 11 YFT y 14 YTD. El paquete de Iron Man contiene varias variantes y el de Spider-Man incluye texturas alternativas. Los scripts ya traen numerosos props y texturas Gen9.
- Los scripts de los cinco héroes referencian **NIBScriptHookVDotNet2 2.11.6.0**. El paquete de NIB también incluye API 3.9.0.0 y el menú 3.2.1.4. No son intercambiables automáticamente con DLL de otro runtime.
- Hay **tres copias de ObjectSpawnUnlockNbuild.asi** dentro de paquetes de Thanos y Thor. El autor menciona ese nombre entre los plugins desactualizados que pueden cerrar Enhanced. No se han instalado ni ejecutado. Hay que revisar el plan de cada OIV y la procedencia de ese binario, aunque el ZIP se llame Enhanced. [Advertencia del autor](https://www.patreon.com/JulioNIB/posts/gta-5-enhanced-147079939).

## Cómo funcionan

Hay dos cadenas que se encuentran durante el juego:

```
Lógica: GTA -> cargador ASI -> Script Hook V -> runtime .NET -> script del poder
Arte:   GTA -> OpenRPF -> archivos de mods -> modelo, texturas, animaciones y física
```

Script Hook V permite llamar las funciones nativas de GTA desde plugins. Un runtime como SHVDNE añade una API administrada para C#/VB.NET. En los paquetes de JulioNIB, los archivos `.ENdll` son ensamblados .NET que usan su runtime NIB, audio, entidades, modelos, raycasts, cámaras y funciones nativas. Spider-Man referencia también `GTA.Rope`; esa referencia permite identificar una dependencia, pero no reconstruye por sí sola el algoritmo de sus telarañas. [Script Hook V](https://www.dev-c.com/gtav/scripthookv/), [SHVDNE](https://github.com/Chiheb-Bacha/ScriptHookVDotNetEnhanced).

Un OIV es un paquete con archivos y un plan `assembly.xml`: puede instalar scripts, reemplazar recursos y modificar metadatos dentro de RPF. No es solamente una skin. Inspeccionamos su contenido sin ejecutar el instalador.

OpenRPF carga archivos modificados desde `mods`; **no convierte Gen8 a Gen9**. Además, `OpenIV.asi` puede ser el antiguo plugin o una copia de OpenRPF renombrada para un flujo de instalación. Hay que identificar el contenido y su hash. [OpenRPF](https://www.gta5-mods.com/tools/openrpf-openiv-asi-for-gta-v-enhanced), [instrucciones de JulioNIB](https://www.patreon.com/JulioNIB/posts/issues-and-159303765).

## Cómo escribiremos la lógica propia

Estas son decisiones de ingeniería para nuestro código; deberán medirse en runtime:

1. Fijar versión del juego, runtime, API, compilador y dependencias por hash. Para un mod C# independiente, empezar con SHVDNE y su API 3; el SDK .NET usado para construir nuestras herramientas de análisis no es el runtime que ejecuta GTA.
2. Usar funciones nativas y APIs documentadas. Evitar direcciones fijas y patrones de memoria propios al comenzar: las releases de SHVDNE documentan cierres por cambios en pools y punteros, además de un parche que accedía a estructuras de Online ausentes en Historia. [Casos del mantenedor](https://github.com/Chiheb-Bacha/ScriptHookVDotNetEnhanced/releases).
3. Implementar cada poder como estados: desactivado, solicitando recursos, preparado, activo y liberando. La carga necesita un plazo máximo y cancelación; nunca un bucle infinito esperando un modelo.
4. Comprobar que modelos y animaciones existen y terminaron de cargar antes de crear entidades. Verificar que una entidad sigue existiendo antes de operar sobre ella. Tratar muerte, cambio de personaje, carga de partida y descarga del script como salidas normales.
5. Mantener las llamadas al juego dentro del contexto admitido por el runtime. Workers externos pueden procesar datos propios, pero no manipular GTA directamente. El README de SHVDNE documenta restricciones de hilo.
6. Limitar entidades, partículas, cuerdas y sonidos activos; reutilizar cuando corresponda, registrar sus propietarios y liberar solo lo creado por nuestro mod. Restaurar únicamente los estados que el mod cambió.
7. Registrar acción, estado, versión, modelo y excepción. Capturar excepciones administradas ayuda a diagnosticar el script; no evita una violación de acceso nativa. Medir tiempo por Tick, FPS y memoria; aún no tenemos un presupuesto medido en esta PC.

## Cómo construiremos personajes sin deformarlos

| Archivo | Qué contiene | Qué debemos comprobar |
|---|---|---|
| YDD | Componentes visibles y skinning | Geometría, LOD, índices, pesos y paletas de huesos |
| YFT | Esqueleto/fragmento y datos asociados | Tags, jerarquía, pose de referencia y física |
| YTD | Diccionario de texturas | Nombres, shaders, formato, mipmaps y datos completos |
| YMT | Variaciones del ped | Componentes y variantes que realmente existen |
| YLD | Simulación de tela | Correspondencia con la capa y comportamiento en movimiento |
| YCD | Clips de animación | Diccionario/clip, tags y relación con el esqueleto |

Los esqueletos leídos incluyen **98 huesos** en Hulk, Iron Man, Spider-Man y Thor, y **103 en Thanos**. Eso no significa que todos sus huesos, proporciones o poses sean idénticos. Algunos componentes heredan el esqueleto y no lo almacenan nuevamente. Thor tiene un YLD con un elemento de tela: no aplicamos las reglas de pesos ordinarios a todas las referencias de cloth como si fueran huesos del cuerpo.

Para crear una skin, partir de un esqueleto GTA adecuado al tipo de ped, ajustar la malla a su pose de referencia y conservar tags/jerarquía. En Blender, los grupos de vértices deben corresponder al armature correcto. Revisar influencias de hombros, codos, cadera, rodillas, muñecas y dedos; quitar pesos sobrantes y normalizar antes de exportar. Nuestro auditor comprueba pesos byte y paletas de los layouts ordinarios que reconoce. La tela necesita pruebas adicionales. [Rigging con Sollumz](https://docs.sollumz.org/documentation/drawables.ydr/rigging).

No comparar solo nombres literales: en Spider-Man encontramos huesos faciales con el sufijo `_000` en YFT y sin él en YDD, conservando sus tags. Tampoco arreglar una malla moviendo el esqueleto a ciegas: el problema puede ser la pose de referencia, el modificador, la paleta o los pesos.

Separar fallos de rigging de fallos visuales de material. Colores de vértice, normales, shader y canales de textura pueden producir superficies negras, brillo o movimiento por viento. Un único mip no siempre es incorrecto —HUD y render targets pueden requerirlo—, pero las superficies de personajes necesitan revisión. En Thor hay 18 de 37 texturas con un único nivel; esto es una observación para revisar, no prueba de un crash. [Guía y problemas de materiales de Sollumz](https://docs.sollumz.org/tutorials/basic-clothes-editing).

## Conversión comprobada y un problema real del lector

Convertimos una copia del Spider-Man Civil War: YDD **165 -> 159**, YFT **162 -> 171**, YTD **13 -> 5**. El YMT se conserva separado porque no pertenece a esa conversión. Usamos CodeWalker, con una copia aislada de sus bibliotecas; repo de referencia en commit `485d56bec00262ed7fa472261cce7bbc6202b96e`. [Conversión de formatos](https://github.com/Sollumz/wiki/blob/main/tutorials/asset-conversion-for-gtav-enhanced.md), [implementación de CodeWalker](https://github.com/dexyfex/CodeWalker/blob/master/CodeWalker.Core/Utils/Gen9Converter.cs).

Una comparación estricta detectó que el lector Gen8 de CodeWalker calcula algunos mipmaps mediante divisiones sucesivas del tamaño. En una textura BC1 de esta muestra omitía bytes de los niveles más pequeños, mientras el lector Gen9 calcula el tamaño por bloques. Nuestro adaptador relee el rango completo desde el recurso original usando `CalcDataSize` y `DataPointer`, sin inventar píxeles ni modificar el paquete original. Esto se verificó contra la implementación local `TextureData.Read` y mediante hashes antes/después.

La copia corregida conserva las firmas del esqueleto, pesos/índices/paletas y datos de las seis texturas en la lectura de vuelta. También probamos tres archivos negativos: el auditor detectó pesos nulos, un índice de skin inválido y un índice de triángulo fuera de rango. Informes: `test-results.json`, `spiderman-gen9-readback.json` y `negative-fixture-audit.json`. Son pruebas estructurales, no una inspección visual del personaje.

## Prueba necesaria dentro del juego

Nuestra secuencia de aceptación será: juego base -> cargadores mínimos -> una skin sin poderes -> un solo poder -> efectos/audio -> combinación con otros mods. Cada paso conserva un respaldo y permite retirar solo el cambio de ese paso. No cambiar `gameconfig.xml` ni retirar packs arbitrariamente: diagnosticar primero el límite, el conflicto y la build real.

Comprobar idle, caminar, correr, saltar, apuntar, puños, agacharse, entrar/salir de vehículos, caída/ragdoll, muerte, respawn y cambio de ped. Revisar manos, boca, ojos y capa desde varias distancias/LOD. Repetir carga de partida y recarga admitida del script, y una sesión prolongada con el poder activo; conservar logs, tiempos y capturas de esa misma build.

Si falla, reducir a un caso reproducible: retirar por grupos los cambios de nuestra copia de prueba, comparar contra la base y volver a introducir el responsable. La prueba inicial usará un ped del juego para separar un fallo del poder de un fallo de la skin. Una build aprobada se invalida cuando cambian EXE, runtime o assets relevantes.

**Estado actual:** no instalamos los mods ni lanzamos una sesión con ellos. La estabilidad, deformaciones animadas, materiales y física de tela permanecen pendientes. Podemos construir y detectar clases concretas de fallos; ninguna revisión de archivos permite prometer cero crashes en todas las combinaciones.

## Repetir nuestras comprobaciones

Desde PowerShell:

```powershell
& 'D:\modding-lab\projects\gta-enhanced-marvel-lab\run_checks.ps1'
python 'D:\modding-lab\projects\gta-enhanced-marvel-lab\preflight.py' --enforce
```

El primer comando recompila y vuelve a leer nuestros archivos de prueba, valida resultados y genera el informe del juego. El segundo es de solo lectura y devuelve código 2 si los paquetes originales aún presentan bloqueos para instalarse. Ninguno instala plugins ni altera la carpeta de GTA.

La muestra está en `samples/spiderman/gen9`; las entradas, en `inputs`; las copias intencionalmente dañadas, en `tests/negative-fixtures` y nunca deben instalarse. El próximo mod propio necesita una mecánica concreta; la primera implementación debe añadir un único comportamiento medible y pasar esta secuencia de aceptación.
