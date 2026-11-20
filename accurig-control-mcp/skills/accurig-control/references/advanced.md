# Calibración y recuperación

## Calibración de pose

Usa `accurig_calibrate_pose` cuando el objetivo requiera offsets de pose y exista una generación válida: `coordinate_space:"accurig_native_angles"`, `offsets:[{bone_name,rotation:{x,y,z}}]`. Lee nombres reales y confirma la convención nativa antes de elegir ángulos. No traslades radianes ni quaternions del visor por suposición.

La herramienta utiliza captura y exportación originales de AccuRIG, guarda el iAvatar y produce un GLB calibrado nuevo. Cambia `generation_id` e invalida la validación: vuelve a validar y revisar ese GLB. Exporta con `avatar:"calibrated"` si ese es el artefacto requerido. No reutilices un avatar antiguo para aparentar calibración.

La aceptación histórica ejercitó offsets neutros; no demuestra corrección anatómica mediante ángulos no nulos. `blender` con `MeshOnly` es el preset probado. Valida otros destinos cuando el pedido los requiera.

## Historial de ensayo propio

El límite nativo es seis historiales. Antes de archivar identifica el ensayo propio y comprueba que está dentro del alcance autorizado; no elijas contenido del usuario para liberar espacio.

`accurig_archive_generation({generation_id})` exige una generación completada por este MCP, correspondencia de actor y GLB, y que el historial no sea el activo. Conserva archivos, fila de base de datos y recibo de restauración antes de retirar la entrada mediante la aplicación. Verifica y conserva ese recibo. No eludas un fallo de pertenencia mediante borrado manual.

Restaura solo siguiendo el recibo real, con AccuRIG cerrado e identificador y carpeta libres. No sobrescribas historiales ni ejecutes un comando de un ensayo anterior sin verificar sus destinos actuales. El checkpoint de articulaciones no sustituye este respaldo.

## Operaciones inciertas

Con `uncertain` o `interrupted`, conserva ID, error, estado de proceso y última generación confirmada en el registro. Consulta estado y reconciliación sin repetir la mutación. Timeout no significa cancelación nativa. Sin evidencia nueva para recuperar, detén las mutaciones dependientes e informa del bloqueo concreto.

## Contrato0.3
La espera prolongada no certifica calidad. El recibo automático vincula fuente/actor/hashes/eventos. Reanexar requiere que el controlador anterior haya terminado y que proceso, ejecutable, fecha, puertos loopback, nonce y lease coincidan. No se repite la operación. Offline nunca permite exportación nativa.

El archivo conserva todos los archivos (no sólo FBX/GLB) y la fila de historial, con manifiesto verificado. La eliminación permanente es otra herramienta y exige autorización explícita del usuario sobre esa generación; IDs dobles no sustituyen esa autorización.

No existe exportación excepcional para omitir revisión visual. Aceptación exige todas las poses y vistas del informe actual. Un rechazo puede detenerse en el primer defecto y registrar sólo lo observado, sin inventar cobertura. Cambios en fuente, geometría, avatar, calibración, revisión o informe invalidan la aceptación.
