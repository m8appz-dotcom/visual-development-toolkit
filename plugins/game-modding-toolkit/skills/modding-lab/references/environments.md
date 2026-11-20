# Entornos de instalación

El plugin está instalado en X y Bobi según el usuario. Eso no hace intercambiables las rutas ni acredita versiones iguales.

- X: comprobado en esta revisión, raíz `D:/visual-development-toolkit`, modo nativo, configuración `native-runtime.json`. El manifiesto local usa `server/native_mcp.py` con Node/Java/Ghidra existentes.
- Bobi: instalación confirmada por el usuario. Documentación previa referencia `D:/modding-lab` y contenedor `modding-lab-analysis`; son antecedentes. Verifica sus `mcp.json`, configuración local y `component_status` antes de aplicar esas rutas o asegurar que Docker siga siendo el modo activo.

Usa primero los MCP expuestos por la instalación actual. No copies el mcp.json de X sobre Bobi: contiene rutas específicas de X. Para una operación en Docker usa las rutas que informe ese runtime, no las rutas nativas del otro equipo. No cambies proveedores, reinstales REA ni descargues latest para resolver descriptores ausentes. Revisa registro y conexión y conserva las reparaciones locales.
