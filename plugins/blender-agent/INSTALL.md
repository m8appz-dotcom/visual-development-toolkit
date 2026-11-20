# Blender Agent para Windows

Incluye el servidor MCP mejorado, la skill y documentación por tema. El runtime Blender se instala íntegro en paralelo o se reutiliza sólo tras verificar versión/build. No requiere Claude.

Desde un Python3.12 o superior existente:

```
python install.py --archive RUTA_AL_ZIP_OFICIAL
```

Sin --archive, descarga el ZIP fijado en runtime/blender-lock.json desde el servidor oficial y comprueba SHA256. Con --blender RUTA_A_BLENDER_EXE reutiliza sólo5.2.1LTS/build9e2066aef7ef. --python-runtime permite reutilizar un Python con las versiones exactas del lock; si se omite crea un venv propio. --integration-home permite conservar la integración existente y su estado, sin sustituir addons diferentes.

El lanzador portable utiliza `python` del PATH para leer %LOCALAPPDATA%/BlenderAgent/settings.json y ejecutar el intérprete configurado. Si falta configuración o runtime falla claramente; no instala ni descarga durante llamadas MCP. Todo se ejecuta bajo demanda, sin servicios de arranque ni cambios a preferencias globales.

Registrar este directorio como plugin de un marketplace local y usar `codex plugin add blender-agent@NOMBRE_DEL_MARKETPLACE --json`. Consultar primero `codex plugin --help` en el host. No editar caches manualmente. Tras verificar el plugin, desactivar sólo la entrada MCP standalone equivalente si existe y archivar la skill standalone para no duplicarla; conservar backups antes de esos ajustes.

Verificación real desde el intérprete configurado:

```
python verify.py --fixture RUTA_A_UNA_COPIA_BLEND --output RUTA_NUEVA_JSON
```

Descubre42 herramientas, lee nueve temas y ejecuta una receta CLI real; conserva el archivo de entrada y la sesión. --render RUTA_NUEVA_PNG prueba OptiX detectado en una copia del fixture con cámara/luz; falla si no hay dispositivo compatible. Esa prueba opcional no representa todos los motores ni tarjetas. Inspeccionar perceptivamente el PNG original antes de aprobar apariencia.

La skill exige un visorHTML para entregas de modelos. Este plugin no promete convertir automáticamente cualquier escena en una entrega visual aprobada.

Rollback: desinstalar sólo blender-agent mediante el CLI soportado, restaurar únicamente el bloque MCP anterior y mover la skill archivada a su ruta si falta. Conservar runtime y estado con trabajo sin guardar; nunca cerrar Blender ajeno. Consultar el recibo de despliegue del host para backups exactos.
