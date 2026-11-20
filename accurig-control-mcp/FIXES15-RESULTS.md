# AccuRIG0.3 — matriz de correcciones

Prueba vigente: Nico original FBX, importación nueva del21oct2026. El rig anterior se eliminó por orden explícita; su evidencia histórica no aprueba éste. Estado nativo y visual actual en FIXES15-STATE.md. No se ha hecho retarget ni Unreal.

| # | Corrección implementada | Evidencia de verificación |
|---|---|---|
|1|Revisión anatómica obligatoria antes de skin; dedos colapsados o mal proporcionados bloquean build.|Nico recién importado fue rechazado con JOINT_ANATOMY_FAILED;40 posiciones medidas del original, editadas y leídas de vuelta; revisión ligada al hash.|
|2|Rechazar articulaciones vacías, incompletas, duplicadas o no finitas.|Tests hardening-v03/joints-quality.|
|3|Separar estructura, deformación y revisión visual; no exportar por un passed técnico aislado.|Gates de generación/hash/informe, pruebas de revisión pendiente y rechazo.|
|4|Validar todas las mallas con ejes anatómicos, handedness y FK compuesto;20 movimientos,60 muestras, continuidad y penetración.|Blender aislado real sobre fixturePete y rechazo de pieza extra sin pesos. Nico requiere su propio informe/revisión.|
|5|Vincular fuente, revisión, actor, GLB, avatar, validación y aceptación.|Pruebas de fuente/preview cambiado, otro actor y avatar sustituido.|
|6|Nueva sesión sin modelo, calibración, revisión ni privilegios offline heredados.|Test reset; carga nueva y SHA del original.|
|7|Recibo automático al completar, recuperación verificada sin invalidar arbitrariamente un resultado ni regenerarlo.|Tests recovery-v03 del recibo automático y actor cambiado. Recibo automático real de Nico comprobado; reconexión durante cálculo, tras completar y recuperación offline sin regenerar verificadas.|
|8|Lanzamiento Windows independiente, windir correcto y reconexión de proceso propio.|ClienteR3 cerró; app35252 sobrevivió;R4/R5 reanexaron mismo proceso/nonce/fecha sin heredar aceptación.|
|9|Lease exclusivo, control del propietario y reserva de mutaciones; finalizador viejo no libera trabajo nuevo.|Tests lease y reserva; reconexión real del propietario terminado.|
|10|Persistencia atómica y errores visibles; fallo inicial no deja BUSY falso; fallo tras mutación queda uncertain.|Tests de serialización, disco, reserva y estado incierto.|
|11|Comprobar posición, máscara y quaternion equivalente; rollback leído y verificado.|Tests readback/q/-q/rollback;40 correcciones de dedos reales verificadas.|
|12|Cierre comprobado del PID propio y restauración verificada de preferencias.|Test de error de quit; Cierre real comprobado: salida nativa dejó un proceso residual; fallback sólo del PID propio revalidado, preferencias restauradas y verificadas. Se corrigió también la desconexión del inspector antes de esperar.|
|13|Espera90min observando progreso y CPU; estancamiento observable sin replay ni cancelación supuesta.|Trabajo nuevo mantiene progreso/actividad; tests de completionevents y observación sin actividad.|
|14|GLB estricto: accessors, índices, jerarquía, matrices, pesos; archivo completo con manifiesto.|7tests GLB/lease; backup de temporales real entre volúmenes verificado antes de aislar.|
|15|Exportación a staging, reimportación, correspondencia de huesos/triángulos, publicación exclusiva y pruebas de fallo.|Tests export-v03: FBX inválido nunca publicado, colisión sin entrega parcial; Exportación real de Nico bloqueada por revisión rechazada. No se ejecutó ni se atribuye un roundtrip FBX positivo a este candidato fallido.|

54 testsNode y2 testsPython pasaron. Plugin0.3 instalado y probado con cliente MCP real:23 herramientas, skill empaquetada, export sin bypass y borrado marcado destructivo. Esto no sustituye el recorrido nativo ni la revisión visual final del rig Nico.

Fuentes intactas; ZIP Nico no consultado ni modificado. Recibo de eliminación exacta: reports/deleted-16e56003518f4a57b8208d2150b91d39.json,267858030bytes liberados.

Rollback de código: backups/fixes15-20261021, conservando fuentes, informes, salidas y cambios ajenos. La eliminación solicitada no es reversible mediante este respaldo de código.

## Resultado real del piloto

Importación nueva desde el FBX original,40 posiciones de dedos corregidas y verificadas antes de skin, generación nueva con100 articulaciones y216647 vértices ponderados,403606 triángulos. Estructura pasada;20 movimientos/60 muestras completados; deformación fallida en ambos puños. Codex observó frente, ambas manos, puños y hombros, y comparó mano derecha con referencia del FBX sin rig: hay pliegues y separaciones en el resultado nativo, incluso en reposo. Revisión detenida ante defectos; no se certifican otras vistas ni poses.

El MCP registró requires_corrections y bloqueó exportación. El piloto no es un rig aprobado. La implementación del controlador sí quedó probada, incluidos rechazos reales, recuperación de resultado y cierre. HTML conserva la referencia y la prueba nueva con textura original cargada; giro y zoom se verifican en el navegador. No se reparó el rig viejo ni se avanzó a Unreal.

El primer cierre mostró un proceso nativo residual después de destruir el contexto JavaScript; no basta desconectar el inspector. Se añadió salida acotada y terminación exclusivamente del PID propio después de revalidar ejecutable/fecha/lease y ausencia de build pendiente. Recuperación de cierre sólo tras terminar el controlador anterior. Pruebas y cierre real verificados; no se cerraron apps ajenas.

Informe completo: reports/fixes15-final.json. Artefacto rechazado conservado para revisión, fuentes y ZIP intactos.
