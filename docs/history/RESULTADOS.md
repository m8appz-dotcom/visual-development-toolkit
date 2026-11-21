# Visual Development Toolkit — resultados

**Versión 1.1.0 instalada y habilitada en Bobi.** Su propósito es acelerar la creación y modificación de juegos y apps con elementos visuales.

## Flujo de trabajo

- Crear prototipos y modificar proyectos desde su código fuente.
- Preparar e integrar iconos, ilustraciones, sprites, texturas, materiales, modelos 3D y audio.
- Generar assets con fal cuando exista una clave y gasto autorizado.
- Ejecutar el proyecto y validar sus interacciones y resultados visuales.
- Investigar código o recursos compilados con REA, Ghidra, ILSpy y AssetStudio cuando el trabajo lo requiera.

El agente usa sus herramientas habituales de edición y build junto con los recursos del plugin. Los flujos de mods quedan como referencias opcionales, fuera de la selección automática de skills. El ID interno y las rutas conservan sus nombres anteriores para mantener compatibilidad.

## Comprobaciones de esta actualización

**17 comprobaciones aprobadas**, usando la copia instalada de la versión 1.1.0:

- Nombre, descripción, prompts y 10 skills enfocados en desarrollo visual.
- Codex confirma la instalación y que el plugin está habilitado.
- Conexiones MCP Windows, Ghidra y REA: 353 herramientas descubiertas; componentes saludables y respuesta de salud de Ghidra.
- Procesamiento real de un PNG a icono 64×64 mediante universal-modder.
- package_project creó un ZIP con un archivo HTML y su icono; se verificaron contenido e integridad.
- Se rechazaron rutas fuera del proyecto y el empaquetado de la raíz de output.
- El asset original conserva su hash; Ghidra cerró sin errores en su log.

El archivo HTML es una fixture de empaquetado, no una aplicación completa validada visualmente. Las **32 comprobaciones de componentes de la versión 1.0.4** se conservan en reports/plugin-test.json como evidencia histórica. Esta actualización no reconstruyó ni cambió los motores de Docker, ILSpy o AssetStudio. Pruebas actuales: reports/visual-development-test.json.

## Uso

Abre un chat nuevo en Codex y selecciona **Visual Development Toolkit**. Ejemplos:

> Crea un prototipo de juego 2D con los assets necesarios e intégralos en una primera escena jugable.

> Mejora mi app con iconos e ilustraciones consistentes, intégralos en sus componentes y verifica las pantallas.

> Modifica este proyecto de juego o app desde su código fuente y valida el cambio en ejecución.

Guía: D:/modding-lab/README.md. Proyecto de prueba: D:/modding-lab/projects/visual-development-test-20261007-111350. Código previo y documentación para rollback: D:/modding-lab/backups/reframe-1.0.4/.

## Herramientas y requisitos

REA se mantiene incluido. Ghidra, ILSpy y AssetStudio permiten entender artefactos existentes cuando es necesario; no son un paso obligatorio para crear una app o juego. universal-modder conserva su nombre original como dependencia de procesamiento.

Fal requiere FAL_KEY y uso de pago autorizado. Blender es necesario para render3d; ComfyUI requiere su propio servidor. Esta actualización no ejecutó generación de pago ni render 3D. AssetStudio conserva su compatibilidad original Unity 3.4–2022.1; la GUI ofrece FBX/animaciones, cuyo export no se probó. No se incluye PS5.

El contenedor de análisis conserva límites de 3 CPU y 8 GiB, la imagen modding-lab:1.0.2 y restart unless-stopped. El ZIP entrega el plugin y su guía; los runtimes permanecen instalados en Bobi. Enlace privado de Tailscale: http://100.82.79.73:18741/.
