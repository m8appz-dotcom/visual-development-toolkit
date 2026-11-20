# Funciones dificiles: estado final, fuente y limites

Se intentaron todas las entradas del inventario. Esta tabla sigue los 22 casos que persistieron tras los reintentos iniciales y muestra su estado despues de la pasada extendida. Los registros RNA generados se vinculan con su generador y con la declaracion del tipo; no se presentan como funciones escritas literalmente en el checkout.

| Direccion | Funcion | Estado final | Fuente o generador |
|---|---|---|---|
| 1407e7a50 | `?register_struct_WindowManager@blender@@YAXAEAUBlenderRNA@1@@Z` | pseudocodigo recuperado | generador del registro RNA (ruta histórica en el informe original); definicion WindowManager (ruta histórica en el informe original) |
| 140a20ba0 | `blender::bke::create_implicit_conversions` | sin pseudocodigo del motor | definicion de conversiones implicitas (ruta histórica en el informe original) |
| 140b51df0 | `?BLI_noise_mg_variable_lacunarity@blender@@YAMMMMMHH@Z` | sin pseudocodigo del motor | definicion de ruido con dominio distorsionado (ruta histórica en el informe original) |
| 140c0caa0 | `blender::ui::but_event_property_operator_string` | sin pseudocodigo del motor | definicion en la interfaz (ruta histórica en el informe original) |
| 140de8160 | `?rna_blender_rna_create@blender@@YA?AUBlenderRNA@1@XZ` | sin pseudocodigo del motor | generador de creacion de BlenderRNA (ruta histórica en el informe original) |
| 140e50460 | `?register_struct_UILayout@blender@@YAXAEAUBlenderRNA@1@@Z` | sin pseudocodigo del motor | generador del registro RNA (ruta histórica en el informe original); definicion UILayout (ruta histórica en el informe original) |
| 140f62110 | `?blo_do_versions_450@blender@@YAXPEAUFileData@1@PEAULibrary@1@PEAUMain@1@@Z` | sin pseudocodigo del motor | migraciones de archivos anteriores (ruta histórica en el informe original) |
| 14103cad0 | `?register_struct_Object@blender@@YAXAEAUBlenderRNA@1@@Z` | sin pseudocodigo del motor | generador del registro RNA (ruta histórica en el informe original); definicion Object (ruta histórica en el informe original) |
| 14129b110 | `?compute@MaterialXNodeParser@node_shader_bsdf_principled_cc@nodes@blender@@UEAA?AVNodeItem@materialx@34@XZ` | pseudocodigo recuperado | cuerpo MaterialX de Principled BSDF (ruta histórica en el informe original); macro que define el parser (ruta histórica en el informe original) |
| 141580210 | `?manta_update_pointers@blender@@YAXPEAUMANTA@1@PEAUFluidModifierData@1@_N@Z` | pseudocodigo recuperado | puente C de Mantaflow (ruta histórica en el informe original) |
| 141a124b0 | `blender::init_compositor_infos` | sin pseudocodigo del motor | registro de descriptores del compositor (ruta histórica en el informe original) |
| 141a377c0 | `blender::init_draw_infos` | sin pseudocodigo del motor | registro de descriptores de dibujo (ruta histórica en el informe original); generacion de la lista de descriptores (ruta histórica en el informe original) |
| 141ad9bd0 | `blender::init_gpu_infos` | pseudocodigo recuperado | registro de descriptores GPU (ruta histórica en el informe original) |
| 141aef300 | `?gpu_shader_dependency_init@blender@@YAXXZ` | sin pseudocodigo del motor | dependencias de fuentes shader (ruta histórica en el informe original) |
| 142238b20 | `?register_struct_RenderEngine@blender@@YAXAEAUBlenderRNA@1@@Z` | pseudocodigo recuperado | generador del registro RNA (ruta histórica en el informe original); definicion RenderEngine (ruta histórica en el informe original) |
| 14280de80 | `?initializeRNAMap@MANTA@blender@@AEAAXPEAUFluidModifierData@2@@Z` | sin pseudocodigo del motor | mapa RNA de Mantaflow (ruta histórica en el informe original) |
| 142835730 | `?updatePointers@MANTA@blender@@QEAAXPEAUFluidModifierData@2@_N@Z` | pseudocodigo recuperado | actualizacion de punteros de Mantaflow (ruta histórica en el informe original) |
| 1436ee200 | `?set_id_props_from_prim@usd@io@blender@@YAXPEAUID@3@AEBVUsdPrim@pxrBlender_v26_03__pxrReserved__@@W4PropertyImportMode@123@VUsdTimeCode@6@@Z` | sin pseudocodigo del motor | propiedades ID desde primitivos USD (ruta histórica en el informe original) |
| 1448fb5a0 | `??$ConvertData@GC@v12@AbcCoreOgawa@Alembic@@YAXPEADPEAX_K@Z` | sin pseudocodigo del motor | [plantilla de Alembic 1.8.3 (version fijada por el build)](https://github.com/alembic/alembic/blob/1.8.3/lib/Alembic/AbcCoreOgawa/ReadUtil.cpp#L169) |
| 1448fb490 | `??$ConvertData@GE@v12@AbcCoreOgawa@Alembic@@YAXPEADPEAX_K@Z` | sin pseudocodigo del motor | [plantilla de Alembic 1.8.3 (version fijada por el build)](https://github.com/alembic/alembic/blob/1.8.3/lib/Alembic/AbcCoreOgawa/ReadUtil.cpp#L169) |
| 1448fb6f0 | `??$ConvertData@FE@v12@AbcCoreOgawa@Alembic@@YAXPEADPEAX_K@Z` | sin pseudocodigo del motor | [plantilla de Alembic 1.8.3 (version fijada por el build)](https://github.com/alembic/alembic/blob/1.8.3/lib/Alembic/AbcCoreOgawa/ReadUtil.cpp#L169) |
| 1448fb800 | `??$ConvertData@FC@v12@AbcCoreOgawa@Alembic@@YAXPEADPEAX_K@Z` | sin pseudocodigo del motor | [plantilla de Alembic 1.8.3 (version fijada por el build)](https://github.com/alembic/alembic/blob/1.8.3/lib/Alembic/AbcCoreOgawa/ReadUtil.cpp#L169) |

## Ruido: error de normalizacion de saltos

BLI_noise_mg_variable_lacunarity conserva el error Backward normalization not implemented con las opciones estandar y conservadoras. El origen del mensaje esta en JumpBasic2::findUnnormalized (ruta histórica en el informe original), con el lanzamiento de la excepcion en la linea 1767.

La fuente exacta de Blender permite seguir el algoritmo: dos selectores eligen funciones de ruido; la primera calcula tres desplazamientos escalados por distortion, usando posiciones con offsets +13.5, 0 y -13.5; la segunda evalua el punto desplazado. Esto es lectura de la fuente, no una recuperacion nativa exitosa ni una prueba de ejecucion de todos sus casos. definicion de ruido con dominio distorsionado (ruta histórica en el informe original).

## Registro de shaders de dibujo

init_draw_infos contiene 89.387 instrucciones en el cuerpo que Ghidra identifico. El proceso del decompilador termino inesperadamente tanto en modo estandar (46,781 s) como conservador (26 s). No se determino la causa de esa terminacion.

La fuente incluye glsl_draw_infos_list.hh dentro del registro de ShaderCreateInfo; CMake genera esa lista de inclusiones. El codigo tambien contiene un ajuste de buffer condicionado por GPU_stencil_clasify_buffer_workaround. Las macros crean descriptores y los agregan al diccionario; este recorrido explica la funcion sin afirmar que cada instruccion haya sido reconstruida. registro de descriptores de dibujo (ruta histórica en el informe original); generacion de la lista de descriptores (ruta histórica en el informe original).

## Cuatro conversiones de Alembic

Las cuatro instancias ConvertData hicieron terminar el proceso del decompilador en las dos configuraciones. Se conserva su ensamblador y se reviso su cola escalar. Todas reducen el contador con un desplazamiento de un bit, leen elementos de dos bytes y escriben uno. Las comparaciones y limites observados dan este resumen de la ruta escalar:

| Direccion | Interpretacion de entrada observada | Intervalo aplicado antes de guardar el byte | Instrucciones inventariadas |
|---|---|---|---:|
| 1448fb490 (ruta histórica en el informe original) | 16 bits sin signo | 0 a 255 | 69 |
| 1448fb5a0 (ruta histórica en el informe original) | 16 bits sin signo | 0 a 127 | 81 |
| 1448fb6f0 (ruta histórica en el informe original) | 16 bits con signo | 0 a 255 | 70 |
| 1448fb800 (ruta histórica en el informe original) | 16 bits con signo | -128 a 127 | 85 |

Pseudocodigo analitico de esa ruta escalar, sin contabilizarlo como salida recuperada por Ghidra:

```text
n = cantidad_de_bytes >> 1
para i desde 0 hasta n - 1:
    destino[i] = convertir_a_byte(limitar(origen16[i], minimo, maximo))
```

Tambien hay rutas SIMD con empaquetado y comprobaciones de solapamiento. No se ejecutaron estas funciones ni se demostro aqui equivalencia completa de esas rutas vectoriales; el resumen anterior tiene alcance escalar. La [plantilla oficial de Alembic 1.8.3](https://github.com/alembic/alembic/blob/1.8.3/lib/Alembic/AbcCoreOgawa/ReadUtil.cpp#L169) ofrece la referencia de conversion con limites. Esa es la version fijada por el build de Blender en versions.cmake (ruta histórica en el informe original); no se verifico identidad binaria de esa dependencia contra una compilacion propia.

## Ensamblador y errores pendientes

Los casos sin pseudocodigo conservan cada intento, sus tiempos y su archivo .asm en unresolved-functions.json (ruta histórica en el informe original). El inventario y el catalogo mantienen esas direcciones como no recuperadas. Ghidra es el proveedor de decompilacion comprobado disponible en este host; Hopper no admite Windows e IDA no tiene registro MCP configurado.

Estado final de estos 22 casos: 6 recuperados y 16 sin pseudocodigo del motor. Sus referencias de fuente siguen disponibles en la tabla.

## Comprobacion estatica de la aritmetica SIMD

Un modelo de las instrucciones registradas confronto los 65.536 patrones posibles de entrada de 16 bits en cada variante, en ambos bloques desenrollados y durante dos iteraciones. Los 1.048.576 resultados por carril coincidieron con la saturacion escalar de la tabla; se comprobo tambien que cada salida depende de su propia entrada. Las constantes se leyeron de la imagen de programa mediante Ghidra MCP. Evidencia y alcance (ruta histórica en el informe original).

La interpretacion del empaquetado y comparaciones sigue las [definiciones de intrinsecos SSE2 de LLVM/Clang](https://clang.llvm.org/doxygen/emmintrin_8h.html), las operaciones logicas siguen [SSE](https://clang.llvm.org/doxygen/xmmintrin_8h.html) y los minimos/maximos sin signo siguen [SSE4.1](https://clang.llvm.org/doxygen/smmintrin_8h.html). Es un contraste de aritmetica por carril; no ejecuta las funciones del binario ni valida accesos, punteros o solapamiento real de memoria. Las cuatro siguen marcadas como fallos del motor.

## Tabla de saltos de MaterialX en una copia aislada

El cuerpo inicial de MaterialXNodeParser::compute tenia 136 bytes y 31 instrucciones: terminaba en un salto calculado y no incluia cuatro entradas de su tabla. Se decodificaron seis offsets de 32 bits con signo desde la direccion que usa el propio codigo; el limite de indice aparece en su comparacion con 5. En una copia de la base se registraron esos destinos y se recalculo el cuerpo: 35.760 bytes, con las seis entradas incluidas. Las regiones de instrucciones y la tabla comprobadas conservaron sus bytes.

Se usaron las APIs oficiales [JumpTable](https://ghidra.re/ghidra_docs/api/ghidra/program/model/pcode/JumpTable.html) y [CreateFunctionCmd](https://ghidra.re/ghidra_docs/api/ghidra/app/cmd/function/CreateFunctionCmd.html). La base principal y el ejecutable permanecieron intactos. Registro del contexto (ruta histórica en el informe original); resultado con el mismo limite de 300 segundos (ruta histórica en el informe original).

El intento aislado produjo pseudocodigo y se incorporo al catalogo conservando su contexto separado, el cuerpo original y el historial de intentos. El resultado mantiene tipos inferidos y advertencias. Este caso demuestra que el inventario original puede omitir ramas indirectas.
