# Contrato de control observado

Fuente: AccuRIG 2.1.1 instalado en `D:/Applications/Reallusion/AccuRIG`. Análisis previo con Visual Development Toolkit/REA; fuentes extraídas en `projects/accurig-extraction-20261020/output/application`.

| Operación | Evidencia decompilada | Prueba exigida |
|---|---|---|
| Arranque | background.js; Electron main app ready | PID propio, contexto y versión real |
| Importar | preload.js `api.send`, 2.js `loadFile` → importModel | `fileOnload` posterior al trabajo |
| Preparar | renderer Check → Rig Body → getAutorigObjQuaternion → autorigRotateOnAxis | getModelHeightOffset posterior a importación |
| Detectar | 2.js `bodyDetect`, `fingerDetect` | retorno nativo 1 y articulaciones reales |
| Caracterizar | 2.js `characterize` → autoRigAll → nativeCharacterize → exportIAvatar | GLB del actor actual con skins, joints y pesos |
| Exportar | preload.js converter → EXPORT_FBX → exportWithDecryptedData | FBX no vacío en ruta nueva, reimportación independiente |
| Identificar salida | GET_RIGGING_ACTOR_ID + getAvatarHistories | coincidencia exacta cid, rutas devueltas por aplicación |

La llamada `characterize` devuelve antes de completar la conversión; no constituye aceptación. Los callbacks del convertidor tampoco sustituyen el archivo final.

El acceso directo a `ipcMain._invokeHandlers` no reproduce el contrato de Electron: los handlers guardados son envoltorios que requieren un evento con callbacks internos. La implementación final usa el preload original para consultar el actor y lee el archivo por la ruta devuelta; no usa ese acceso directo.

La ventana de AccuRIG se abre fuera de pantalla y sin foco. La instrumentación está limitada a la instancia creada por este servidor, captura progreso sin buffers ni credenciales y redirige únicamente el diálogo de guardar `Export FBX` a la ruta solicitada. Se restaura el diálogo en `finally`.

El historial de AccuRIG conserva seis carpetas y puede borrar huérfanos automáticamente. El servidor comprueba capacidad y coherencia antes de caracterizar. No aumenta el límite ni borra historiales del usuario.
