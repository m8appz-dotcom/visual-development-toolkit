# Blender 5.2.1: arquitectura central observada en la fuente

## Procedencia y alcance

Análisis estático de la copia `D:/visual-development-toolkit/projects/blender-521-20261020/source`, realizado en el host **X**. Se verificaron ruta, host, commit `9e2066aef7ef7e20c142ad7bd3303138a4304c93` y árbol de trabajo limpio. El commit tiene fecha 2026-08-17 y asunto «Cycles: Bump minimum driver version in UI from 570 to 575». La propia fuente declara `BLENDER_VERSION 502`, parche `1`, ciclo `release` y sufijo `LTS` en BKE_blender_version.h (ruta histórica en el informe original).

Este informe explica los contratos y recorridos centrales que se pudieron seguir en el código. No representa una descompilación exhaustiva de todas las funciones ni una auditoría de todos los algoritmos. No se modificaron la fuente, la instalación, escenas ni bases de Ghidra. No se ejecutó Blender para validar estos recorridos; la coincidencia entre esta fuente y un ejecutable instalado queda fuera de lo demostrado aquí.

**Convenciones:** «Observado» significa definición, llamada o condición encontrada en el código citado; «interpretación» describe su consecuencia arquitectónica. Los enlaces apuntan a líneas de esta copia y commit, no a posiciones garantizadas de otras versiones.

## 1. Arranque: construir los registros antes de aceptar trabajo

**Observado:** main (ruta histórica en el informe original) prepara varias capas antes de entrar al bucle gráfico. En las líneas 486–503 inicializa ruta del ejecutable, hilos, SDNA actual, globales, tipos C++, funciones comunes, tipos ID, modificadores, shader effects, volúmenes y tipos de nodos del depsgraph. Más adelante inicializa directorios, planificador de tareas, imágenes, RNA, motores de render y sistema de nodos; véase secuencia de inicialización (ruta histórica en el informe original).

Los argumentos se procesan por pasadas: entorno primero, configuración después y opciones de interfaz solamente cuando corresponde. Esto importa: las variables de entorno afectan las rutas y el modo background evita subsistemas gráficos. `WITH_PYTHON_MODULE` y `WITH_HEADLESS` fuerzan background en creator.cc (ruta histórica en el informe original). Las ramas de compilación describen posibilidades; no prueban cuáles se usaron en un binario concreto.

`main` llama a WM_init (ruta histórica en el informe original), que incluye registro de tipos de editor, lectura inicial y arranque de Python. Hay lectura de homefile en la línea 283, `BPY_python_start` en la 331 y procesamiento posterior de homefile en la 372. El código no permite reducir el arranque a «crear una ventana y cargar una escena»: también establece registros, estado de usuario, contexto y puente con scripts.

**Interpretación:** muchos subsistemas se conectan mediante tablas de tipos y callbacks. Un objeto, operador o modificador no necesita contener toda su implementación: conserva un identificador de tipo y el sistema encuentra el comportamiento registrado correspondiente.

## 2. Base de datos: Main, ID, Object y Mesh

Main (ruta histórica en el informe original) agrupa la base de datos de un archivo: ruta, versiones, estado de lectura/undo, bibliotecas y listas por tipo. Las listas explícitas de escenas, objetos, mallas, materiales e imágenes están en BKE_main.hh:365 (ruta histórica en el informe original). No equivale a una escena ni a una base SQL; puede contener varias escenas y datos que ninguna escena use actualmente.

ID (ruta histórica en el informe original) es la cabecera compartida de los datablocks. Incluye enlaces de lista, biblioteca, nombre, flags persistentes, tags de runtime y contador de usuarios. Los dos primeros bytes del nombre codifican el tipo. Más adelante aparecen flags de recálculo, `session_uid` estable durante la sesión y propiedades personalizadas. El contador de usuarios es contabilidad de referencias; no se observó una garantía de que actúe por sí solo como un recolector de basura universal.

Object (ruta histórica en el informe original) comienza con `ID`, tiene relaciones de parentesco, datos y lista de modificadores, además de ubicación y otras transformaciones. Mesh (ruta histórica en el informe original) es otro datablock, también con su propio `ID`. Separar ambos permite que varias instancias de objeto apunten a geometría compartida y mantengan transformaciones distintas. Esta consecuencia se deriva de la estructura de referencias; no se comprobó aquí un caso interactivo de duplicación enlazada.

Main también puede dividirse durante lectura o enlace: su campo `split_mains` documenta un Main por biblioteca y conservación de orden para undo. Por ello «un único Main» describe el estado principal habitual, no todos los estados intermedios del cargador.

## 3. DNA y RNA: almacenamiento y acceso semántico

**DNA/SDNA.** Las estructuras `DNA_*` describen disposición y campos de datos. El programa de construcción makesdna (ruta histórica en el informe original) genera la descripción SDNA. En ejecución, DNA_sdna_current_init (ruta histórica en el informe original) interpreta `DNAstr`/`DNAlen`; el mismo módulo contiene DNA_struct_reconstruct (ruta histórica en el informe original), para reconstrucción de estructuras según información de correspondencia. Esto ayuda a cargar formatos con disposiciones diferentes; no sustituye las migraciones semánticas de versión.

**RNA.** Es la capa que describe propiedades, tipos, funciones y cómo acceder a ellos. Un ejemplo concreto es Object.location (ruta histórica en el informe original): se declara una propiedad de traslación, se enlaza al campo DNA `loc`, se define editabilidad, texto y rango, y se registra un callback y notificación. RNA no es una segunda copia completa de todos los datos: puede acceder a campos SDNA o a funciones específicas.

La función rna_property_update (ruta histórica en el informe original) ejecuta callbacks, añade notificaciones, publica en el message bus y etiqueta sincronización/parámetros en el depsgraph cuando procede. Tiene condiciones para flags, contexto, tipos ID y propiedades personalizadas. **No toda escritura de memoria provoca por sí misma una actualización.** El propio comentario de las líneas 2533–2544 explica excepciones al editar propiedades ID desde Python y la necesidad de `update_tag` en ciertos casos.

Recorrido concreto observado de `location`:

1. RNA asocia `location` a `Object.loc`.
2. El callback rna_Object_internal_update (ruta histórica en el informe original) etiqueta `ID_RECALC_TRANSFORM`.
3. La actualización genérica de RNA puede añadir sincronización/parámetros y notificaciones.
4. Una evaluación posterior del depsgraph actualiza los resultados dependientes.

La escritura y la evaluación son pasos distintos; el paso 4 no debe presentarse como una llamada inmediata e incondicional por cada asignación.

## 4. Contexto, eventos y operadores

bContext (ruta histórica en el informe original) guarda el entorno de la operación: gestor de ventanas, ventana, workspace, pantalla, área, región, almacén de contexto y datos como Main y escena. Es el vínculo entre una acción y el lugar donde ocurre. No es el propietario de toda la geometría. El mismo operador puede encontrar datos o permisos distintos dependiendo del contexto.

wmOperatorType (ruta histórica en el informe original) define identificador, descripción, callbacks, propiedades RNA y flags. Sus contratos distinguen:

- `poll`: comprueba si se permite intentar la operación en el contexto; aun pasando puede fallar al ejecutar.
- `exec`: ejecución con parámetros, sin depender de interacción inmediata.
- `invoke`: entrada interactiva con un evento; puede preparar o iniciar una operación modal.
- `modal`: recibe eventos posteriores mientras devuelve `OPERATOR_RUNNING_MODAL`.
- `cancel`: limpieza al cancelar; `check` y callbacks de UI atienden propiedades y presentación.

wm_operator_invoke (ruta histórica en el informe original) hace poll, crea la instancia, inicializa propiedades anteriores cuando corresponde y llama a `invoke` si existe y hay evento; en otro caso puede llamar a `exec`. También controla profundidad de undo para llamadas anidadas y procesa informes/resultados. wm_operator_finished (ruta histórica en el informe original) conecta la finalización con `ED_undo_push_op` según las condiciones de registro y undo. No todos los operadores producen un paso de undo.

El bucle WM_main (ruta histórica en el informe original) primero refresca WM y depsgraph; después repite: recibir eventos de GHOST y colas de ventana, ejecutar handlers, procesar notificaciones y actualizar dibujo. El comentario inicial exige evaluar antes de permitir operadores. **Interpretación:** entrada, modificación, invalidación y dibujo están coordinados, pero son responsabilidades separadas. Un notifier no es por sí mismo el cálculo geométrico.

## 5. Depsgraph: invalidar, propagar y evaluar

La API DEG_id_tag_update (ruta histórica en el informe original) recibe un ID y flags de recálculo. Etiquetar indica trabajo pendiente; no significa que ya se reconstruyó la malla.

deg_flush_updates_and_refresh (ruta histórica en el informe original) actualiza tiempo, etiqueta visibilidad, propaga cambios y evalúa. Tiene una aserción de que las relaciones no estén pendientes de reconstrucción. Después ejecuta callbacks de escritura de vuelta sólo si el modo lo permite y el grafo es activo. DEG_evaluate_on_framechange (ruta histórica en el informe original) etiqueta la fuente temporal, fija frame/tiempo y usa ese recorrido.

El planificador observado en deg_evaluate_on_refresh (ruta histórica en el informe original):

1. Sale si no hay tags de entrada.
2. Incrementa un contador global atómico de actualización y prepara ejecución.
3. Ejecuta `COPY_ON_EVAL`, asegurando datablocks expandidos válidos incluso ante ciclos.
4. Si hace falta, calcula visibilidad dinámica antes de evaluación pesada.
5. Ejecuta operaciones que admiten paralelismo.
6. Completa en un pase de un hilo aquellas operaciones que lo requieren.

El comentario menciona metaballs como ejemplo de operación que limita el paso paralelo. No se deduce de esto que Blender completo sea monohilo o que cualquier grafo pueda paralelizarse íntegramente. El código libera el GIL al entrar en esta evaluación cuando se compila con Python, para permitir drivers Python.

La API distingue IDs evaluados y originales (ruta histórica en el informe original). Esta separación explica la edición no destructiva: el dato fuente y el resultado usado para visualizar/renderizar pueden diferir. Hay mecanismos explícitos de escritura de vuelta; sería incorrecto afirmar que nunca se comunica ningún resultado al original. No se auditó aquí la corrección de todas las relaciones, ciclos o políticas de caché.

## 6. Modificadores: una pila sobre resultados evaluados

mesh_calc_modifiers (ruta histórica en el informe original) prepara contexto, lista de modificadores —incluidos virtuales— y requisitos de atributos/capas. La evaluación considera modos, visibilidad, necesidad de correspondencia con la geometría original y restricciones de sculpt. No es sólo aplicar una lista de matrices.

La bifurcación de mesh_data_update.cc:457 (ruta histórica en el informe original) distingue deformación pura (`OnlyDeform`) de modificaciones constructivas. Las primeras alteran posiciones mediante `BKE_modifier_deform_verts`; las otras pueden producir una malla nueva mediante modifier_modify_mesh_and_geometry_set (ruta histórica en el informe original). Se administran copias de evaluación y vida de resultados anteriores.

Las máscaras de datos indican qué capas necesita el resto de la pila. `CD_ORIGINDEX` permite conservar correspondencias para selección/mapeo cuando se solicitan; no garantiza que toda topología nueva tenga una correspondencia inequívoca. El orden de pila importa porque cada paso recibe el resultado anterior y algunos exigen datos originales. El código registra un error de mala posición cuando un modificador requiere originales y la pila ya no cumple esa condición.

## 7. Modelado: Mesh y BMesh no son la misma representación

BMesh (ruta histórica en el informe original) usa vértices, aristas, loops y caras. Cada vértice referencia una arista incidente; cada arista conecta dos vértices y participa en ciclos alrededor de cada extremo. Los loops enlazan vértice, arista y cara, recorren el perímetro de una cara y forman ciclos radiales alrededor de una arista. Véanse BMEdge (ruta histórica en el informe original) y BMLoop (ruta histórica en el informe original).

**Interpretación:** esas conexiones facilitan cambios topológicos locales y admiten más de dos caras alrededor de una arista. La estructura no impone que toda malla sea manifold. El winding de cara lo determina su ciclo de loops; invertir el orden radial no equivale a invertir una cara.

Existen conversiones expresas Mesh → BMesh (ruta histórica en el informe original), BMesh → Mesh (ruta histórica en el informe original) y conversión para evaluación (ruta histórica en el informe original). No debe extrapolarse que todo procesamiento de geometría pasa por BMesh: las mallas evaluadas y muchos algoritmos trabajan en otras estructuras.

Ejemplo concreto: MESH_OT_extrude_region (ruta histórica en el informe original) registra `edbm_extrude_region_exec`, exige contexto editmesh y permite registro/undo. Su ejecución (ruta histórica en el informe original) reúne objetos en modo edición con datos únicos, obtiene BMEditMesh, omite selecciones vacías, realiza extrusión y llama a `EDBM_update` pidiendo triángulos, normales y actualización destructiva. El algoritmo topológico inferior está en bmo_extrude_face_region_exec (ruta histórica en el informe original). Se localizó su implementación, sin verificar cada caso de degeneración, selección o manifold.

## 8. Geometry Nodes: otro grafo dentro de la evaluación geométrica

El modificador Nodes implementa modify_geometry_set (ruta histórica en el informe original), que delega en `modifyGeometry`. En MOD_nodes.cc:1781 (ruta histórica en el informe original) se verifica salida de grupo y primer socket de geometría, se obtiene un grafo de funciones perezosas y se prepara información del depsgraph, objeto, simulación, bake, logs, efectos laterales y contexto de cálculo.

execute_geometry_nodes_on_geometry (ruta histórica en el informe original) prepara entradas y salidas, lee propiedades RNA de sockets, introduce la geometría en la primera entrada geométrica, asigna memoria y ejecuta `lazy_function.execute`. Después extrae la geometría de salida. El constructor del grafo vive en geometry_nodes_lazy_function.cc (ruta histórica en el informe original), y utiliza ejecutores de grafo para grupos y zonas.

**Interpretación:** el depsgraph coordina dependencias de escena/objetos y Geometry Nodes resuelve el cálculo interno del árbol. Son grafos con niveles de responsabilidad distintos. «Perezoso» permite que la demanda y el uso de valores guíen cálculo; no prueba que todo nodo no conectado quede siempre sin ejecutar, porque hay efectos laterales explícitos, viewers, simulaciones y bake. Tampoco implica que todo se ejecute en GPU. No se inspeccionaron todos los nodos, fields, dominios de atributos o zonas.

## 9. Guardar y cargar: bloques tipados, referencias y migraciones

write_file_handle (ruta histórica en el informe original) sincroniza view layers, prepara IDs de bloque estables y escribe cabecera, información de render, miniatura y globales. Reúne IDs locales, escribe cada ID con `write_id`, bibliotecas y preferencias cuando corresponde. Termina con el bloque `DNA1` y `ENDB`. BLO_write_file (ruta histórica en el informe original) elige envoltorio comprimido zstd o crudo según flags; BLO_write_file_mem (ruta histórica en el informe original) reutiliza la infraestructura para memoria.

La lectura empieza interpretando DNA en read_file_dna (ruta histórica en el informe original). El recorrido mayor es blo_read_file_internal (ruta histórica en el informe original). Se observan migraciones `do_versions`, lectura de bibliotecas, unión de Main, resolución de enlaces, recálculo de usuarios y migraciones posteriores al enlace en readfile.cc:4383 (ruta histórica en el informe original).

**Interpretación:** el archivo conserva estructuras y relaciones; cargar exige reconstruir referencias válidas en el proceso actual y traducir significados antiguos. No basta con copiar bytes del archivo a sus direcciones originales. Guardado y undo comparten parte del serializador, pero tienen condiciones diferentes: el cargador evita determinadas migraciones/recuentos en undo y conserva/reutiliza algunos IDs. No se probó aquí recuperación ante archivos dañados ni compatibilidad exhaustiva entre versiones.

## 10. Undo y redo: tipos de pasos, no simplemente comandos inversos

undo_system.cc (ruta histórica en el informe original) gestiona la pila y el tipo de paso; BKE_undosys_step_load_data_ex (ruta histórica en el informe original) carga estados objetivo. El tipo memfile registra callbacks `poll`, `step_encode`, `step_decode` y `step_free` en ED_memfile_undosys_type (ruta histórica en el informe original).

BKE_memfile_undo_encode (ruta histórica en el informe original) escribe el estado a memfile comparándolo con el anterior. BKE_memfile_undo_decode (ruta histórica en el informe original) lo lee, prepara el nuevo estado de undo y vuelve a obtener Main del contexto porque pudo reasignarse. Conserva la ruta y etiqueta actualización visible. Esto explica por qué referencias crudas a datos no deben asumirse estables tras undo.

No todos los modos usan únicamente ese formato: el sistema admite diferentes tipos de pasos y la infraestructura de edición puede conservar estados especializados. Este análisis trazó memfile y el despachador; no auditó individualmente todos los tipos de undo de sculpt, pintura, edición o texto. Tampoco se midieron consumo de memoria ni velocidad de deduplicación.

## 11. Python: integración con RNA y operadores

BPY_python_start (ruta histórica en el informe original) prepara Python embebido y llama a `Py_InitializeFromConfig` en la línea 585 cuando corresponde. Hay una modalidad de módulo Python distinta de la aplicación normal; sus ramas no prueban que esa modalidad esté activa en la instalación.

El acceso a atributos RNA pasa por pyrna_struct_getattro (ruta histórica en el informe original): busca propiedades o funciones del tipo RNA y construye el acceso Python correspondiente. Las escrituras emplean funciones RNA y actualizaciones cuando proceden; véase bpy_rna.cc:2240 (ruta histórica en el informe original). Esto conecta scripts, propiedades y notificaciones sin exigir que cada propiedad tenga una implementación Python independiente.

Las llamadas Python a operadores llegan a WM_operator_call_py (ruta histórica en el informe original). Por ello `bpy.ops` conserva requisitos de contexto, poll, estados e integración de operadores. El acceso a datos por RNA y la ejecución de un operador son recorridos distintos: cambiar una propiedad no equivale a simular una pulsación ni garantiza el mismo undo. El puente contiene manejo de errores/reportes y liberación/recuperación del GIL para la llamada.

## 12. Recorrido integrado y límites de cobertura

El recorrido arquitectónico sostenido por estos enlaces es: **entrada → contexto/operador o escritura RNA → cambio de datos originales → tags/notificaciones → evaluación de dependencias → geometría y estado evaluados → dibujo**. Guardado serializa datos y relaciones; undo recupera estados a través de sus tipos de paso. Python entra por los mismos sistemas de propiedades y operadores, con diferencias importantes entre ambas API.

| Área | Cobertura estática completada | Pendiente para afirmaciones más amplias |
|---|---|---|
| Arranque | main, registros, background, WM/Python | Trazar un binario real con sus opciones de build |
| Main/ID/DNA/RNA | Estructuras, metadatos, acceso y ejemplo location | Todos los tipos ID y callbacks de propiedades |
| Eventos/contexto | Bucle WM, callbacks y despacho de operadores | Entrada real por plataforma, keymaps y todas las rutas modales |
| Depsgraph | Tags, propagación, fases, original/evaluado | Todos los builders, relaciones, ciclos y escenarios de invalidación |
| Modificadores | Pila de malla, deformación/construcción, máscaras | Algoritmo y casos extremos de cada modificador |
| BMesh | Topología, conversiones y extrusión como ejemplo | Todos los operadores y robustez geométrica |
| Geometry Nodes | Puente del modificador y ejecución del grafo | Cada nodo, fields, inferencia, simulación y bake completos |
| Archivo/undo | Escritor/lector, DNA, versioning y memfile | Archivos reales, corrupción, migraciones y tipos de undo restantes |
| Python | Inicio, atributos RNA y llamadas a operadores | Extensiones, drivers, handlers y seguridad de cada flujo |

**No verificado en runtime:** arranque de la instalación, interacción visual, exactitud numérica, comportamiento de escenas, render, compatibilidad con GPU/controladores, rendimiento o correspondencia binaria con el commit. La existencia de implementaciones en la fuente demuestra disponibilidad del código, no que todas estén compiladas o activas en el equipo.
