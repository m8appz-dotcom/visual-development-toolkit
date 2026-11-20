# Consultas JavaScript/Electron

Los nombres de esta referencia corresponden a la capa 0.2 sobre REA 4.1.0. Consulta el esquema real: los prefijos que muestra el host pueden variar.

## Trabajo persistente

`agent_job_start({input_path,format})` admite `auto`, `asar` y `directory`. Para importar una exportación verificada existente, añade `artifact_directory` con `plugin-result.json`, `analysis.json` y los grafos; actualmente esa importación requiere fuente archivo/ASAR. No pases un JSON arbitrario como exportación verificada.

Guarda `result.job.id` y consulta `agent_job_status({job_id})` respetando `poll_interval_ms`. No uses sondeo continuo ni generes otro trabajo cuando el anterior ya está activo. `agent_job_cancel` conserva checkpoints; `agent_job_resume` exige la misma fuente y motor. Tras reiniciar Windows la reanudación es explícita. La API utiliza herramientas ordinarias, no la extensión Tasks nativa.

`agent_job_result` devuelve rutas, hashes y contadores cuando termina. Los fallos de herramienta usan `isError` y la envoltura `{contract_version:"1",ok:false,error:{code,message,retryable}}`; no interpretes un error como una página vacía. `SOURCE_CHANGED`, `ARTIFACT_MISMATCH` e `INVALID_CURSOR` exigen corregir la causa, no reintentar idénticamente.

## Pregunta → consulta

| Necesidad | Herramienta y criterio |
|---|---|
| Localizar un símbolo | `agent_graph_search({job_id,query,kind:"function",module})`; `module` es ruta exacta, la búsqueda textual usa prefijos de tokens, no significado |
| Explicar una función | `agent_graph_function_context({job_id,node_id,source_root,limit})` |
| Leer código original | `agent_graph_source_excerpt({job_id,node_id,source_root,max_chars})`; verifica SHA256 del módulo y columnas UTF-16, conserva CRLF |
| Ver relaciones | `agent_graph_neighbors({job_id,node_id,direction,relation,resolution,limit,cursor})` |
| Conectar dos nodos | `agent_graph_trace` o `agent_graph_flow_context`; especifica origen y destino y, si procede, `resolution:"resolved"` |
| Conocer incertidumbres | `agent_graph_coverage_report({job_id,function_id})`, o `module` o `node_id`; no combines selectores |
| Leer un nodo | `agent_graph_node({job_id,node_id,include_evidence:true})` |
| Recuperar un registro grande | `agent_graph_evidence_fragment({job_id,record_id,record_type,chunk_chars,cursor})` |

Un contexto de función incluye miembros directos y ejemplos de sus llamadas. `member_count`, `context_truncated` y los cursores de vecinos indican omisiones. La cobertura de función incluye todos sus miembros directos; las funciones anidadas tienen pertenencia independiente. Sin `source_root`, el contexto no contiene código original: no lo completes de memoria. La fuente debe proceder del árbol original, no de un bundle reformateado que cambie su hash.

`flow_context` aporta evidencia de nodos y conserva pasos candidatos. `trace` permite además filtrar `relation`. Empieza con el subconjunto que responda la pregunta; un resultado vacío tras filtrar relaciones no demuestra ausencia en el grafo completo.

## Límites y fragmentos

- Páginas: 1–100 elementos; contextos de función: 1–20 por sección. Sigue los cursores con los mismos filtros. No los modifiques ni los reutilices en otro trabajo.
- Recorridos: profundidad máxima 12, 2.000 nodos, 20.000 relaciones y cinco segundos de exploración. Consulta `limits_reached`, `budget_reached` y `negative_result`. Aumenta un presupuesto solo si resuelve la pregunta y dentro de los límites anunciados.
- Respuesta lógica: hasta 64 KiB. El transporte puede incluir la misma respuesta como texto y contenido estructurado; no sumes ambas copias como contexto independiente.
- Si `detail_omitted` es verdadero, usa fragmentos de registro. Admite tipos `node`, `edge` y `unknown`, con 256–8.000 caracteres por fragmento.

Para reconstruir un registro, concatena `text` sin separadores siguiendo `next_cursor`, comprueba SHA256 de la concatenación UTF-8 y después parsea el JSON. El cursor queda vinculado al trabajo, registro y hash. El hash corresponde a esa serialización del registro, no al archivo de fuente.

La cobertura informa conteos de evidencia estática y motivos de incertidumbre; no mide cobertura de ejecución ni probabilidad de acierto. Para afirmar comportamiento observado se necesitan pruebas de runtime separadas y autorizadas.
