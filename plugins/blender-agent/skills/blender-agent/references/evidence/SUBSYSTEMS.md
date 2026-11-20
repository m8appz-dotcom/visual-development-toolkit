# Blender 5.2.1: render, GPU, animación, simulación y medios

Fecha de análisis: 2026-10-20. Host comprobado: **X**. Fuente examinada: `D:/visual-development-toolkit/projects/blender-521-20261020/source`; commit `9e2066aef7ef7e20c142ad7bd3303138a4304c93`. `git status --short` no mostró cambios al iniciar. La cabecera de versión declara `502`, parche `1`, ciclo `release`, sufijo `LTS`: BKE_blender_version.h:26 (ruta histórica en el informe original).

Este informe documenta análisis estático de fuente, con lecturas dirigidas de implementaciones y comprobación de símbolos y líneas. No acredita compilación, render ejecutado, calidad visual, disponibilidad de dispositivos, compatibilidad de archivos ni equivalencia binaria con una instalación. No modifica la fuente, instalaciones, escenas ni proyectos Ghidra. Es una parte del análisis completo de Blender: no significa que cada algoritmo o línea del programa esté revisado.

## 1. Cómo se conectan estos subsistemas

El estado evaluado de la escena alimenta varios consumidores. Cycles lo convierte a su propia escena y ejecuta integración de luz; EEVEE y Workbench sincronizan objetos con el sistema de dibujo; compositor y sequencer consumen resultados de imagen, datos de escena y medios. Animación, constraints, deformaciones y simulación producen parte del estado que esos consumidores reciben.

Una distinción esencial: **motor de render** y **backend GPU** son elecciones diferentes. Cycles tiene su abstracción `Device`, con CPU/CUDA/OptiX/HIP/Metal/oneAPI; el dibujo de Blender tiene otra abstracción `GPUBackend`, con OpenGL/Vulkan/Metal/Dummy. Por tanto, que un viewport use un backend gráfico no determina por sí mismo el dispositivo de Cycles. Las dos factorías están en device.cpp:101 (ruta histórica en el informe original) y gpu_context.cc:548 (ruta histórica en el informe original). Sus ramas están condicionadas por opciones de compilación; la presencia de código no prueba que una distribución las incluya o el hardware las soporte.

## 2. Entrada común al render de imágenes y animaciones

`RE_RenderFrame` entra en el pipeline de render después de preparar su contexto: pipeline.cc:1925 (ruta histórica en el informe original). La animación usa el mismo pipeline por fotograma desde RE_RenderAnim:2318 (ruta histórica en el informe original).

`do_render_full_pipeline` distingue tres rutas: un motor externo puede asumir todo el procesamiento; si el sequencer está activo, se produce su salida; en otro caso se ejecuta la ruta de escena/compositor. Después agrega metadatos y, cuando corresponde, estampado. Esto explica por qué el botón de render no siempre equivale a invocar directamente el motor de iluminación: pipeline.cc:1480 (ruta histórica en el informe original).

Dentro de la ruta de escena, `do_render_engine` obtiene y valida la cámara, configura el plano de vista y llama a `RE_engine_render`; si no hay cámara informa un error y cancela esa ruta. Luego procesa el posible render por borde: pipeline.cc:1055 (ruta histórica en el informe original). El compositor puede requerir renderizar otras escenas utilizadas por sus nodos: pipeline.cc:1170 (ruta histórica en el informe original).

Recorrido concreto comprobado: `RE_RenderFrame` → `do_render_full_pipeline` → decisión sequencer/compositor/motor → `do_render_engine` → `RE_engine_render` → resultados y metadatos. Este recorrido describe llamadas presentes en la fuente, no una traza capturada en ejecución.

## 3. Cycles: adaptación de escena, planificación y transporte de luz

### 3.1 Frontera Blender–Cycles

`BlenderSession::render` recibe el depsgraph, instala un `BlenderOutputDriver`, obtiene la capa evaluada y calcula parámetros de sesión/buffers. Durante cada vista sincroniza la escena con `sync_data`; puede liberar datos de Blender después de esa conversión para reducir memoria; finalmente arranca y espera la sesión. Véanse session.cpp:338 (ruta histórica en el informe original), sincronización:397 (ruta histórica en el informe original) y start/wait:450 (ruta histórica en el informe original).

Esto crea una frontera útil para diagnóstico: un objeto puede existir en Blender y aun así requerir inspeccionar su conversión a Cycles; las estructuras que procesa el integrador no son simplemente punteros arbitrarios a toda la interfaz de Blender.

### 3.2 Sesión y trabajo progresivo

`Session::run_main_render_loop` pide una unidad `RenderWork`, trata cancelación y errores de dispositivo, bloquea los buffers mientras procesa la iteración y llama a `path_trace_->render`. Al terminar libera la oportunidad de dibujar o reiniciar entre iteraciones: session.cpp:163 (ruta histórica en el informe original).

La preparación de la siguiente iteración coordina:

- Reinicio diferido de escena y buffers, bajo mutex de escena.
- Configuración del denoiser, muestreo adaptativo y guiding.
- Presupuesto de muestras/tiempo y elección del siguiente tile.
- Evicción periódica de tiles de imágenes no usados.
- Cambio de resolución de cámara para render progresivo.
- Carga de kernels y memoria de trabajo, y espera explícita a compilaciones de dispositivo.

Todo está concentrado en run_update_for_next_iteration:311 (ruta histórica en el informe original). Un detalle de concurrencia relevante: libera el mutex de escena antes de cargar kernels del denoiser, porque la interoperabilidad gráfica puede bloquearse si el mutex permanece tomado; está explicado en el propio código en la línea 417. `update_scene` actualiza muestras/pases y llama a `scene->update`: session.cpp:706 (ruta histórica en el informe original).

`PathTrace::render_pipeline` separa inicialización, redistribución de carga, trazado, entrenamiento de guiding, muestreo adaptativo y postprocesado Cryptomatte; el resto de la clase contiene las etapas de denoise, display y escritura: path_trace.cpp:184 (ruta histórica en el informe original), denoise:618 (ruta histórica en el informe original), display:741 (ruta histórica en el informe original). Tener un denoiser configurado no implica que se ejecute en cada iteración: `RenderWork` habilita sus etapas.

### 3.3 CPU y GPU ejecutan la máquina de estados de manera distinta

En CPU, `PathTraceWorkCPU` inicializa un camino desde cámara o bake y ejecuta el megakernel; contempla caminos adicionales del shadow catcher: path_trace_work_cpu.cpp:119 (ruta histórica en el informe original). El megakernel lee el siguiente estado y despacha intersección, fondo, superficie, volumen, sombra y otros pasos. No consiste en una sola fórmula de color: megakernel.h:22 (ruta histórica en el informe original).

En GPU, `PathTraceWorkGPU::render_samples` alimenta trabajo y llama a `enqueue_path_iteration`; el despachador selecciona kernels según cantidades de caminos pendientes, agrupa trabajo y trata por separado caminos de sombra y sombreado. Las ramas concretas incluyen intersección cercana/sombra/subsurface/volumen y sombreado de superficie/fondo/luz/volumen: path_trace_work_gpu.cpp:348 (ruta histórica en el informe original), selección:459 (ruta histórica en el informe original), despacho:519 (ruta histórica en el informe original). La interpretación arquitectónica es una ejecución por colas de etapas, frente al bucle por camino visible en CPU. No se midió cuál resulta más rápida en esta máquina.

### 3.4 Materiales de Cycles

`BlenderSync::sync_materials` construye un `ShaderGraph` y lo asigna al shader de Cycles; también existen rutas separadas para world y luces: shader.cpp:1640 (ruta histórica en el informe original). `ShaderManager::create` elige un gestor OSL cuando la compilación/configuración lo permite; en el otro caso utiliza SVM: shader.cpp:464 (ruta histórica en el informe original).

SVM compila tipos de shader y escribe sus nodos en una representación para el dispositivo: svm.cpp:1036 (ruta histórica en el informe original), compile:1174 (ruta histórica en el informe original). OSL tiene otro compilador y grupos de shaders: osl.cpp:1486 (ruta histórica en el informe original). No se deduce que OSL esté disponible en cualquier dispositivo, ni que todos los nodos se reduzcan a la misma representación que EEVEE.

## 4. EEVEE: sincronización modular y muestras GPU

`eevee::Instance` concentra módulos de mundo, materiales, velocidad, luces, sombras, volúmenes, probes, pipelines, film, ray tracing y efectos. `begin_sync` sincroniza esos módulos, considera las restricciones de la capa y reinicia muestras al detectar movimiento de cámara en el viewport: eevee_instance.cc:348 (ruta histórica en el informe original). Los objetos pasan por `object_sync`, que constituye la entrada a los módulos de geometría: eevee_instance.cc:394 (ruta histórica en el informe original).

`render_sample` hace avanzar el muestreo, actualiza tablas/uniformes, renderiza mundo y probes, ejecuta la vista principal y después avanza motion blur. En render final puede resincronizar y esperar a que terminen shaders/texturas; no trata una compilación pendiente como material definitivo: eevee_instance.cc:536 (ruta histórica en el informe original).

El render de un frame repite muestras hasta completar el presupuesto. Para Metal y Vulkan vacía trabajo entre muestras por gestión de recursos/memoria de comandos; los comentarios advierten del riesgo de acumular un command buffer enorme: eevee_instance.cc:659 (ruta histórica en el informe original).

El viewport reutiliza el mismo `render_sample`, pero presenta resultado por actualización, intercambia datos de velocidad, escribe pases para el compositor cuando está habilitado y solicita nuevos repintados mientras quedan muestras. Durante playback evita pedir repintados adicionales para conservar la relación con el ritmo de animación y TAA: eevee_instance.cc:724 (ruta histórica en el informe original).

Materiales: `MaterialModule::material_sync` resuelve variantes por objeto/geometría y pases: eevee_material.cc:313 (ruta histórica en el informe original). `ShaderModule::material_shader_get` llama a `GPU_material_from_nodetree`, con callback que adapta el código generado al pipeline EEVEE: eevee_shader.cc:1544 (ruta histórica en el informe original), adaptación:937 (ruta histórica en el informe original). Sus grafos generan fragmentos de superficie/volumen/desplazamiento y dependencias del shader. Es una compilación específica del motor; compartir el árbol de material de Blender no significa compartir el evaluador de Cycles.

## 5. Workbench: representación de trabajo del modelo

Workbench deriva de `DrawEngine` y organiza pases opacos, transparentes, profundidad transparente, sombras, volumen, contornos, profundidad de campo y antialiasing: workbench_engine.cc:48 (ruta histórica en el informe original).

La selección de color puede proceder del objeto, un color aleatorio, color único, atributo de vértice, textura o color de material. La ruta de material está implementada por `get_material`: workbench_engine.cc:134 (ruta histórica en el informe original). Hay un arreglo de punteros `GPUMaterial` ficticios expresamente para consultar geometría de superficie; el comentario aclara que esos punteros no se usan como materiales efectivos. Esto respalda que el sombreado de trabajo no evalúa automáticamente toda la red de nodos de un material físico.

La etapa de dibujo prepara los attachments de color/profundidad/ID de objeto, limpia buffers y ejecuta los pases en orden; conserva profundidad de elementos “in front” para overlays y puede volver a mostrar el resultado ya acumulado: workbench_engine.cc:449 (ruta histórica en el informe original).

## 6. Viewport, extracción de geometría y comandos GPU

En este checkout la orquestación principal está en **`draw_context.cc`**, mientras `draw_manager.cc` implementa el gestor de recursos, visibilidad y comandos. Conviene evitar diagramas de versiones anteriores que coloquen todo dentro de `draw_manager.cc`.

`DRWContext::engines_init_and_sync` inicializa engines habilitados, inicia sincronización del manager, llama a `begin_sync`, sincroniza objetos y termina con `end_sync` de engines y manager. `DRWContext::sync` usa un grafo de extracción, procesa duplicados y geometría diferida, espera su trabajo y actualiza curvas: draw_context.cc:1056 (ruta histórica en el informe original). `engines_draw_scene` invoca después `instance.draw` de cada motor: draw_context.cc:1097 (ruta histórica en el informe original).

`Manager::end_sync` sube recursos y despacha un compute shader de finalización de matrices/bounds/info seguido de una barrera de memoria: draw_manager.cc:114 (ruta histórica en el informe original). Al enviar un pase, el manager comprueba huellas de manager/vista para recalcular visibilidad o generar comandos sólo cuando corresponde: draw_manager.cc:310 (ruta histórica en el informe original). Esto explica la separación entre evaluar una escena, extraer sus buffers y volver a dibujarla: son operaciones relacionadas, pero distintas.

`GPU_context_create` crea el contexto de recursos de Blender sobre el contexto de plataforma: gpu_context.cc:193 (ruta histórica en el informe original). La selección detecta backends admitidos y puede caer a otra opción: gpu_context.cc:475 (ruta histórica en el informe original). No se comprobó el backend activo de una sesión gráfica.

Los shaders se describen con `ShaderCreateInfo`. `GPU_shader_create_from_info` envía la descripción al compilador y `ShaderCompiler::compile` finaliza la información, genera fuentes e inicializa/finaliza el shader concreto: gpu_shader.cc:226 (ruta histórica en el informe original), compile:787 (ruta histórica en el informe original). Existen rutas de compilación asíncrona y recogida del resultado: gpu_shader.cc:332 (ruta histórica en el informe original). Revisar esta capa y el backend concreto es necesario ante un fallo de compilación GPU; un shader Cycles CUDA y un shader de viewport no recorren necesariamente este mismo camino.

## 7. Animación: propiedades, acciones, NLA y drivers

`BKE_animsys_evaluate_animdata` convierte el ID animado a `PointerRNA`; procesa NLA si existe y está habilitado, o evalúa la acción activa si NLA no produjo evaluación; después puede evaluar drivers y aplica overrides de edición. El código señala expresamente que la acción activa forma parte del stack NLA cuando esa ruta se usa: anim_sys.cc:4004 (ruta histórica en el informe original).

Las acciones actuales pasan por `animrig::evaluate_and_apply_action` con un `slot_handle`; las curvas se agrupan en channelbags del slot y se evalúan con tiempo ajustado: evaluation.cc:79 (ruta histórica en el informe original), channelbags/FCurves:149 (ruta histórica en el informe original). La evaluación y la aplicación del resultado son operaciones separadas. El informe no reduce por ello todas las acciones a una lista global antigua de FCurves.

Lectura operacional: el canal describe una propiedad RNA y su índice, la curva produce un valor al tiempo solicitado, y el sistema aplica ese valor al ID evaluado. Una pose finalmente visible requiere además las fases de restricciones y transformación del rig. La implementación puede evaluarse por componentes del depsgraph; el orden local descrito de `BKE_animsys_evaluate_animdata` no sustituye el análisis completo de dependencias entre distintos objetos o drivers.

## 8. Rigging, constraints, IK y deformación

`BKE_pose_eval_init_ik` inicializa los árboles IK; `BKE_pose_eval_bone` calcula el hueso ordinario o usa su matriz de reposo, y aparta huesos pertenecientes a árboles IK/spline IK. `BKE_pose_constraints_evaluate` vuelve a separar esos casos: armature_update.cc:853 (ruta histórica en el informe original), bone:870 (ruta histórica en el informe original), constraints:906 (ruta histórica en el informe original).

El cierre de un hueso multiplica la matriz de pose por la inversa de la matriz de reposo y prepara su dual quaternion de deformación. El resultado puede volcarse al canal original si el depsgraph es el activo: BKE_pose_bone_done:953 (ruta histórica en el informe original). Es importante para interpretar matrices: matriz de pose y matriz correctiva de deformación no son intercambiables.

`BIK_*` es una capa de plugins que despacha según `pose->iksolver`, con compilación condicional del solver estándar y iTaSC: ikplugin_api.cc:27 (ruta histórica en el informe original). `BKE_pose_iktree_evaluate` ejecuta el árbol a través de esa API y posteriormente existe liberación de los datos temporales: armature_update.cc:1001 (ruta histórica en el informe original).

En el solver estándar el adaptador convierte huesos a segmentos, establece parentesco, transformaciones, límites, rigidez, estiramiento, objetivos de posición/orientación y pole vector; finalmente llama a `IK_Solve` con el límite de iteraciones del árbol: iksolver_plugin.cc:336 (ruta histórica en el informe original), objetivos/solve:509 (ruta histórica en el informe original). La implementación numérica construye Jacobianos y actualiza ángulos: IK_QJacobianSolver.cpp:295 (ruta histórica en el informe original). Tiene inversión SDLS, que amortigua valores singulares individualmente, y otra implementación DLS: IK_QJacobian.cpp:190 (ruta histórica en el informe original), DLS:312 (ruta histórica en el informe original).

La deformación final de geometría está separada de resolver la pose: `armature_deform.cc` contiene acumuladores lineales y de dual quaternions, y APIs para malla/curvas/editmesh: armature_deform.cc:111 (ruta histórica en el informe original), API mesh:660 (ruta histórica en el informe original). Resolver correctamente la cadena de huesos no demuestra por sí mismo que pesos, espacios de transformación y opción de deformación produzcan la malla esperada.

## 9. Simulación: varias familias de solver y caché temporal

### Cloth

`clothModifier_do` vincula el modifier a su point cache y determina rango de tiempo. Antes de calcular intenta recuperar estado exacto, interpolado o antiguo; sólo permite simular el siguiente frame secuencial cuando la caché no está bakeada. Al recuperar caché actualiza posiciones y geometría; al avanzar ejecuta `do_step_cloth` y escribe caché: cloth.cc:326 (ruta histórica en el informe original), política temporal:382 (ruta histórica en el informe original), paso:257 (ruta histórica en el informe original). El solver está implementado en el módulo de simulación mass-spring: SIM_mass_spring.cc:1258 (ruta histórica en el informe original).

Consecuencia comprobable en el control de flujo: saltar a un frame no siempre ejecuta la misma trayectoria que reproducir desde el inicio; depende del estado y tipo de caché. No se evaluó estabilidad ni precisión numérica.

### Rigid body

`BKE_rigidbody_do_simulation` consulta point cache, requiere avance temporal válido, subdivide el intervalo y llama a `RB_dworld_step_simulation`, actualizando objetos y cacheando el resultado: rigidbody.cc:2216 (ruta histórica en el informe original). La envoltura `intern/rigidbody` construye `btDiscreteDynamicsWorld` y delega a `stepSimulation` de Bullet: rb_bullet_api.cpp:143 (ruta histórica en el informe original), step:202 (ruta histórica en el informe original). Existen implementaciones vacías bajo condiciones de compilación sin Bullet; no debe inferirse disponibilidad por el nombre de la API únicamente.

### Fluidos y Mantaflow

`BKE_fluid_modifier_do` protege el dominio con mutex de lectura/escritura para evitar que un render de preview lea mientras se modifica la simulación. Decide además cuándo actualizar la vista durante bake, replay o dominio adaptativo: fluid.cc:4062 (ruta histórica en el informe original).

`manta_step` actualiza transformaciones/dominio y avanza subpasos hasta cubrir la duración del frame: fluid.cc:3478 (ruta histórica en el informe original). El procesamiento trata cachés de configuración, datos, ruido, malla, partículas y guiding de forma distinta; escribe datos principales sólo si el paso concluye con éxito y genera productos derivados según flags: fluid.cc:3997 (ruta histórica en el informe original). La frontera C/C++ hacia MANTA expone operaciones de bake y timestep: manta_fluid_API.cpp:86 (ruta histórica en el informe original). `MANTA_main.cpp` integra las plantillas de scripts del solver y sus llamadas: MANTA_main.cpp:300 (ruta histórica en el informe original). No se auditó el solver completo de presión, advección o líquido.

### Zonas de simulación de Geometry Nodes

Las zonas de simulación constituyen otra vía. Sus nodos usan `LazyFunction` y reciben comportamiento desde `simulation_params`. La salida distingue lectura de un estado, lectura interpolada entre dos estados, pass-through y almacenamiento de un estado nuevo: node_geo_simulation.cc:383 (ruta histórica en el informe original), selección:468 (ruta histórica en el informe original). Esto permite expresar evolución temporal mediante un grafo; no implica que cualquier zona ejecute automáticamente Cloth, Bullet o Mantaflow. Queda pendiente seguir en detalle quién prepara `SimulationZoneBehavior` desde la caché del modifier.

## 10. Compositor: planificación por salidas, fusión y ejecución CPU/GPU

El compositor observado no usa un hipotético `intern/evaluator.cc`. Su entrada de render construye un contexto y una `NodeGroupOperation`. Ese contexto decide GPU sólo si el dispositivo está soportado y la configuración de render selecciona compositor GPU: compositor.cc:140 (ruta histórica en el informe original). Mapea interfaces y pases de imagen a resultados: compositor.cc:594 (ruta histórica en el informe original).

`NodeGroupOperation::execute` calcula un schedule según salidas necesarias; recorre nodos, comprueba cancelación, acumula nodos de píxel en unidades de compilación y evalúa los demás como operaciones independientes: node_group_operation.cc:87 (ruta histórica en el informe original).

Para las unidades de píxel, selecciona `MultiFunctionProcedureOperation` si ejecuta en CPU o si la unidad produce un valor único; usa `ShaderOperation` para la otra ruta GPU. Por tanto, compositor GPU no significa que toda operación se convierta obligatoriamente a shader: node_group_operation.cc:213 (ruta histórica en el informe original).

El scheduler empieza desde salidas pertinentes —incluidos viewer/file output según contexto— y calcula una heurística de buffers intermedios. El comentario reconoce que es una estimación, no una medida exacta del máximo de memoria: scheduler.cc:86 (ruta histórica en el informe original), heurística:310 (ruta histórica en el informe original), compute_schedule:502 (ruta histórica en el informe original).

Cada operación evalúa procesadores de entrada, ejecuta, realiza postprocesado y libera referencias de entradas; el mapeo de dominios y conversiones no se reduce a conectar punteros de texturas: operation.cc:26 (ruta histórica en el informe original), input processors:91 (ruta histórica en el informe original). El contenedor de render conserva cachés y puede recrearse si cambia dispositivo o precisión: compositor.cc:732 (ruta histórica en el informe original), recreación:794 (ruta histórica en el informe original).

## 11. Sequencer: evaluación temporal de strips y composición

`render_give_ibuf` es una entrada de imagen para un tiempo de timeline. Consulta caché de imagen final y, si hace falta, renderiza el stack de strips: render.cc:1968 (ruta histórica en el informe original).

`seq_render_strip` consulta caché intraframe y de fuente, produce datos sin caché cuando corresponde, aplica preprocesamiento y guarda el resultado: render.cc:1732 (ruta histórica en el informe original). Hay rutas para imágenes, movies/proxies, clips, máscaras y escenas, además de meta-strips y efectos: imagen:954 (ruta histórica en el informe original), movie:1096 (ruta histórica en el informe original), scene strip:1346 (ruta histórica en el informe original), despachador:1655 (ruta histórica en el informe original).

El stack combina resultados con reglas de blend, early-outs y cachés de composición; no renderiza necesariamente todas las capas inferiores si una ruta opaca vuelve innecesario su resultado: render.cc:1842 (ruta histórica en el informe original). El archivo examinado explica la imagen del sequencer; no se siguió aquí la mezcla ni reproducción de audio, sincronización de reloj o codificación final de video. Esas rutas requieren revisar también el sistema de sonido y movie I/O.

## 12. Importación, exportación y formatos

Los formatos no comparten un único importador universal. `source/blender/io/CMakeLists.txt` agrega módulos propios para OBJ, PLY, STL, Grease Pencil, FBX, Alembic y USD, según opciones de build: CMakeLists.txt:6 (ruta histórica en el informe original). Los operadores del editor traducen parámetros de interfaz/RNA a APIs de formato.

**FBX:** en esta fuente, la importación ya tiene operador C++ nativo: prepara `FBXImportParams` y llama a `FBX_import`: io_fbx_ops.cc:66 (ruta histórica en el informe original). `importer_main` abre el archivo, configura ufbx, carga su escena y reconstruye datos Blender; la secuencia incluye materiales/geometría/armatures, cámaras, luces, empties, animación y jerarquía: fbx_import.cc:336 (ruta histórica en el informe original), cierre de importación:426 (ruta histórica en el informe original). El file handler declara expresamente exportación con el add-on Python `export_scene.fbx`: io_fbx_ops.cc:254 (ruta histórica en el informe original). No debe describirse toda operación FBX como un único plugin ni como enteramente nativa.

**USD:** `USD_export` crea un job o ejecuta de forma síncrona; `export_to_stage` crea un stage y usa `USDHierarchyIterator` para recorrer datos evaluados: usd_capi_export.cc:811 (ruta histórica en el informe original), stage:508 (ruta histórica en el informe original), iterator:569 (ruta histórica en el informe original). USDZ tiene limpieza/conversión final específica; un comentario explica por qué una operación que cambia directorio debe quedar fuera del callback worker: usd_capi_export.cc:748 (ruta histórica en el informe original).

El paquete `scripts/addons_core/io_scene_gltf2` existe en el árbol; se localizó su punto de entrada Python, pero no se auditó el recorrido glTF completo ni se probó round-trip. OBJ/PLY/STL/Alembic se inventariaron en el build; sus parsers y conversión de coordenadas no se revisaron exhaustivamente. La preservación real de materiales, morphs, constraints, unidades o animación sólo puede aceptarse por formato y caso de prueba.

## 13. Assets y bibliotecas

`AssetLibraryService` mantiene bibliotecas y selecciona entre archivo actual, bibliotecas de disco, essentials, agregadas y configuraciones remotas: asset_library_service.cc:74 (ruta histórica en el informe original), remotas:148 (ruta histórica en el informe original). Estas ramas acreditan soporte en fuente; no que una biblioteca remota concreta esté configurada, accesible o descargada.

Al traer un asset al archivo, `asset_import.cc` obtiene su ruta de biblioteca y decide método. El predeterminado es append con reutilización, salvo un método explícito del llamador o asset. Las ramas enlazan, empaquetan, anexan recursivamente o anexan reutilizando IDs locales. La importación termina en `WM_file_link_datablock` o `WM_file_append_datablock`, con flags diferentes: asset_import.cc:33 (ruta histórica en el informe original), dispatch:55 (ruta histórica en el informe original).

Interpretación: la identidad/persistencia del asset y su instancia local tienen responsabilidades distintas. Un catálogo o una miniatura no prueba que el datablock ya forme parte del archivo; su disponibilidad real depende de resolver y efectuar la importación. No se realizaron descargas, cambios de biblioteca ni inserciones de assets.

## 14. Dependencias externas y frontera de integración

La fuente incluye adaptadores propios en `intern/` para motores o bibliotecas de terceros; el CMake agrega condicionalmente Cycles, solver IK, iTaSC, Bullet, Mantaflow y otros componentes: intern/CMakeLists.txt:23 (ruta histórica en el informe original). Los adaptadores no equivalen a una reimplementación completa de las bibliotecas.

El manifiesto de dependencias fija las siguientes versiones para **este checkout**. Son versiones del entorno de compilación prescrito, no resultados de inspección de DLLs cargadas ni garantía de cómo fue construido un ejecutable concreto.

| Componente | Valor en la fuente | Función que orienta su inspección | Referencia |
|---|---|---|---|
| Alembic | 1.8.3 | Cachés e intercambio de escenas | versions.cmake:217 (ruta histórica en el informe original) |
| OpenSubdiv | v3_7_0 | Subdivisión | versions.cmake:232 (ruta histórica en el informe original) |
| OpenColorIO | 2.5.0 | Gestión de color | versions.cmake:263 (ruta histórica en el informe original) |
| LLVM | 20.1.8 | Infraestructura de compilación usada por dependencias | versions.cmake:287 (ruta histórica en el informe original) |
| OpenImageIO | v3.1.13.1 | Imágenes y texturas | versions.cmake:298 (ruta histórica en el informe original) |
| OSL | 1.15.3.0 | Shaders OSL | versions.cmake:344 (ruta histórica en el informe original) |
| Python | 3.13.13 | Scripting/add-ons y puente de APIs | versions.cmake:381 (ruta histórica en el informe original) |
| TBB | v2022.3.0 | Paralelismo de tareas | versions.cmake:410 (ruta histórica en el informe original) |
| OpenVDB | 13.0.0 | Datos volumétricos | versions.cmake:430 (ruta histórica en el informe original) |
| FFmpeg | 8.1 | Medios audiovisuales | versions.cmake:646 (ruta histórica en el informe original) |
| Embree | 4.4.1 | Kernels de ray tracing | versions.cmake:842 (ruta histórica en el informe original) |
| USD | 26.03 | Escenas USD | versions.cmake:851 (ruta histórica en el informe original) |
| OpenImageDenoise | 2.5.0 | Denoising | versions.cmake:879 (ruta histórica en el informe original) |

No se descargaron ni recompilaron esas dependencias. No se revisó su código completo ni se atribuye cobertura de sus implementaciones internas a este análisis de Blender.

## 15. Registro de cobertura y límites

| Área | Cobertura realizada | Pendiente para análisis exhaustivo |
|---|---|---|
| Pipeline render | Entrada frame/animación, elección de rutas, cámara, motor, resultados | Todas las rutas de escritura, multivista y errores |
| Cycles | Sesión, adaptador Blender, RenderWork, CPU/GPU, selección Device, grafos SVM/OSL | Todos los BSDF, muestreadores, BVH, kernels y backends por dispositivo |
| EEVEE | Sincronización modular, frame/viewport, muestras, compilación de material | Algoritmos completos de sombras/probes/ray tracing/volumen |
| Workbench | Recursos, color de material y orden de pases | Implementación de cada pase/shader |
| GPU y viewport | DRWContext, extracción, Manager, backend y compilación | Comandos nativos de Vulkan/Metal/OpenGL, drivers, medición GPU |
| Animación | RNA, acción/NLA/drivers, slots/channelbags y aplicación | Interpolación completa, todos los modos NLA y drivers entre IDs |
| Rig/IK | Fases de pose, constraints, plugins, segmentos/objetivos/Jacobiano, deformación | Auditoría numérica exhaustiva, iTaSC, spline IK y todos los constraints |
| Física | Control temporal/cache de Cloth, Bullet y Mantaflow; comportamiento de zonas GN | Solvers internos completos, colisiones, soft-body, partículas, rigidbody nodes y bake multiframe |
| Compositor | Schedule, operaciones, unidades pixel CPU/GPU, cachés y contexto | Todos los nodos, conversiones, resultados y ejecución GPU real |
| Sequencer | Imagen por frame, strips, fuentes/proxies y composición/cache | Audio, reloj, codificación y todos los efectos |
| I/O | Estructura CMake, FBX nativo/Python y export USD; localización glTF | Round-trips, parsers completos y matriz de fidelidad por formato |
| Assets | Servicio de bibliotecas y modos de importación | Catálogos/índices remotos, transferencia y persistencia completas |
| Dependencias | Opciones de integración y versiones prescritas | Binarios efectivamente cargados, código de terceros y reproducibilidad del build |

Los recorridos de mayor rendimiento explicativo para continuar son: un material concreto desde árbol Blender hasta kernel/shader del motor; un rig pequeño desde slot/FCurve hasta vértice deformado; una zona de simulación desde cache del modifier hasta `StoreNewState`; y un frame con compositor/sequencer hasta su archivo final. Cada recorrido debe acompañarse de una prueba runtime específica si se pretende afirmar funcionamiento de la instalación, fidelidad de exportación o equivalencia con el binario analizado. Este documento sólo acredita la parte estática descrita.
