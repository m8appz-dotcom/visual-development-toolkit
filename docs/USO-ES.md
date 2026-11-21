# Uso e instalación

**Visual Development Toolkit acelera la creación y modificación de juegos y apps con elementos visuales.** Trabaja desde el código fuente cuando está disponible, prepara los assets, intégralos en la app o escena y valida el resultado en ejecución.

## Bobi

La versión **1.1.0** ya está instalada. Abre un chat nuevo de Codex y selecciona el plugin. Ejemplos:

> Crea un prototipo de juego 2D con una primera escena jugable y prepara e integra sus sprites.

> Mejora mi app con iconos e ilustraciones consistentes, intégralos en sus componentes y verifica las pantallas.

> Modifica este proyecto desde su código fuente y prueba el comportamiento que cambió.

La instalación activa permanece en `D:\modding-lab`. El nombre interno `game-modding-toolkit@modding-lab` se conserva por compatibilidad.

## Otro Windows

Necesitas Windows x64, Python 3.12+, Git, .NET 8 Desktop Runtime, Codex y Docker Desktop funcionando con contenedores Linux. FFmpeg permite la captura/grabación local; Blender y ComfyUI son opciones separadas.

Clona el repositorio privado y entra en su carpeta. Primero revisa los pasos; después prepara el entorno:

```powershell
python setup_runtime.py --plan --build --install
python setup_runtime.py --build --install
```

El instalador descarga los siete repositorios y las herramientas desde sus fuentes oficiales con versiones y hashes fijados, prepara Python, compila el adaptador de AssetStudio, construye Docker e instala el plugin. Los detalles de recuperación y rollback están en [INSTALL-WINDOWS.md](INSTALL-WINDOWS.md). La reconstrucción completa en un Windows nuevo todavía no se ha probado; la evidencia entregada corresponde al runtime real de Bobi.

## Qué aporta cada componente

| Componente | Uso |
|---|---|
| universal-modder | Preparar sprites, imágenes, texturas y otros assets con sus pipelines |
| fal | Generar/editar imágenes, audio, video y modelos 3D mediante los modelos disponibles |
| REA y Ghidra | Entender artefactos compilados cuando lo requiere el trabajo |
| ILSpy | Recuperar C# aproximado desde assemblies .NET compatibles |
| AssetStudio | Inspeccionar y extraer recursos Unity compatibles |
| Agente de Codex | Crear y modificar el código, integrar los assets y ejecutar los checks del proyecto |

Fal requiere tu `FAL_KEY` y cobra por uso. No se hicieron generaciones pagadas en las pruebas. Renderizar 3D a sprites necesita Blender. Las instrucciones y herramientas específicas de mods quedan como referencias opcionales.

`package_project` crea un ZIP con los archivos que hayas escrito en una subcarpeta de `output/`; el ZIP puede contener código y assets. Usa el build propio del proyecto para producir una app, juego o instalador ejecutable.

## Evidencia

[RESULTADOS.md](history/RESULTADOS.md) registra **17 comprobaciones de la actualización** y **32 comprobaciones previas de componentes**. Se verificaron conexiones MCP, procesamiento de un icono, empaquetado e integridad de originales. Los archivos de prueba son propios; no acreditan compatibilidad con cualquier juego/app ni sustituyen la revisión de tu proyecto real.

