---
name: modding-lab
description: "Coordinar ingeniería inversa de aplicaciones y artefactos con los MCP REA, Ghidra, ILSpy y extracción Unity del REA. Usar para analizar paquetes distribuidos y recuperar evidencia; no para crear productos ni generar assets."
---

# REA: ingeniería inversa

Identifica el artefacto y la pregunta. Usa un proyecto aislado y copias verificadas cuando haga falta importar material. Prefiere el código fuente disponible para preguntas que no requieren decompilación.

Consulta `component_status` solo al necesitar comprobar conexión, host o entorno. El plugin existe en X y Bobi; no deduzcas rutas, Docker o versiones de otra máquina. Lee [references/environments.md](references/environments.md) si el entorno no está establecido.

- Para JavaScript/Electron y consultas persistentes con evidencia, usa `visual-development-agents`.
- Para decidir la ruta REA nativa, administrada, Android, firmware o navegador, usa `reverse-engineer-anything` y sus referencias pertinentes. La existencia de una herramienta no acredita que todos sus proveedores funcionen en este host.
- Usa Ghidra para análisis nativo, ILSpy para ensamblados .NET administrados y AssetStudio para inventario/extracción Unity soportada. ILSpy no recupera código fuente de IL2CPP.
- `recon_game` identifica motores de una carpeta seleccionada sin lanzar el juego. `create_project`, `import_target`, `list_project_files`, `read_project_text` y `verify_originals` conservan entradas, resultados y trazabilidad.
- Prefiere las operaciones del MCP específico a `rea_command`. Este último se mantiene como ruta limitada para operaciones que el MCP específico no cubra.

No presenta generación de assets, automatización genérica, creación de apps ni empaquetado de producto. No edites ejecutables ni reconstruyas un producto por una solicitud de revisión. Distingue evidencia estática, runtime observado, hipótesis e incertidumbres y registra errores por función/artefacto.
