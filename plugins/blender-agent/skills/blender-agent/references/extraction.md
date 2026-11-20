# Hallazgos útiles y procedencia

Referencia local verificada el 21 de octubre de 2026 en X: Blender 5.2.1 LTS, build 9e2066aef7ef. Fuente oficial analizada: commit 9e2066aef7ef7e20c142ad7bd3303138a4304c93, D:/visual-development-toolkit/projects/blender-521-20261020/source. No asumas estas firmas en otro build; consulta RNA actual con el MCP cuando cambie la versión.

## Consecuencias prácticas del código analizado

- Object y Mesh son datablocks distintos. La malla puede tener varios usuarios: reutiliza si deben permanecer idénticos y copia antes de una edición independiente. Inspecciona `users`, no deduzcas propiedad por nombre.
- RNA puede invalidar datos sin evaluarlos inmediatamente. Agrupa escrituras compatibles, actualiza antes de leer resultados dependientes y evita forzar una evaluación por iteración sin necesidad.
- Distingue geometría fuente de la evaluada con modificadores/Geometry Nodes. Usa depsgraph y `evaluated_get` al comprobar el resultado; libera `to_mesh()` con `to_mesh_clear()` en `finally`. En Edit Mode usa la malla BMesh apropiada y actualízala.
- El contexto de un operador incluye objeto activo, selección, modo y área. Un `poll` correcto no garantiza que la ejecución termine bien. Usa la herramienta de contexto o un override verificado cuando sea pertinente; no intentes reparar todo seleccionando objetos por nombres supuestos.
- El orden de modificadores cambia el resultado. No apliques destructivamente toda la pila para inspeccionarla. Guarda/exporta según el consumidor y comprueba atributos y materiales relevantes.
- El render tiene preparación y evaluación además del muestreo. Agrupar llamadas y elegir GPU puede reducir tiempos distintos; mide cada tramo y revisa ruido/detalle en el resultado real.

Fundamento detallado: [CORE](evidence/CORE.md) (datablocks, RNA, contexto, depsgraph y modificadores) y [SUBSYSTEMS](evidence/SUBSYSTEMS.md) (render y otros subsistemas). Consulta secciones pertinentes, no el catálogo completo.

## Evidencia y límites

El análisis nativo identificó 215.319 funciones y recuperó pseudocódigo de 215.303, con 16 huecos y advertencias. Esto no es recuperación semántica completa ni validación de todas las funciones. [Límites nativos](evidence/NATIVE-LIMITS.md).

La referencia rápida contiene nueve operadores y diez tipos seleccionados, contrastados con runtime. Las seis recetas son ejemplos acotados; un keyframe simple no certifica rigs completos ni deformaciones de personajes.

La prueba real de lámpara comparó seis construcciones equivalentes: mediana de tres rondas 10 llamadas/0,346 s frente a 1 llamada/0,141 s. El tramo mide construcción MCP, no razonamiento del agente. Un render CPU de 82,32 s y uno OptiX RTX3060 de 16,72 s usaron 1200×900 y 64 muestras; no prueban una aceleración universal. Codex inspeccionó renders originales y el modelo interactivo; hubo una corrección del visor móvil.

[Informe y evidencias](evidence/AGENT-INTEGRATION.md). Esa aprobación corresponde a esos artefactos, no a futuras creaciones.

## Integración local histórica (X)

Servidor configurado: `blender`; launcher D:/CodexTools/blender-mcp/launcher.py; overlay hardening-v2. Las conexiones nuevas verificadas exponen 42 herramientas. Una conexión previa puede seguir anunciando 41 hasta reconectar. No cambies configuración ni cierres sesiones ajenas para consultar documentación.

El manifiesto de references/mcp conserva versión y hashes del conocimiento instalado. El contenido actual servido por el MCP prevalece si se actualiza; ante discrepancias registra versión y revisa la receta contra el runtime antes de ejecutar. Los detalles operativos de esta referencia son internos, no material para un evaluador visual externo.


## Plugin portable

En instalaciones nuevas consulta settings.json bajo %LOCALAPPDATA%/BlenderAgent para runtime e integration_home reales. Las rutas de X anteriores son procedencia, no instrucciones para Bobi. El paquete incluye el mismo MCP con BUNDLE configurable, sin dependencia de Claude.
