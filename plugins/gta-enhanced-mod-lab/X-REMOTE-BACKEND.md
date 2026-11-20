# Instalación en X con backend en Bobi

Paquete GTA Enhanced Mod Lab 0.4.4 copiado del plugin instalado y habilitado en Bobi el 15/10/2026. Los scripts y referencias conservan su contenido. Solo `mcp.json` se adapta al transporte SSH existente de X a Bobi.

El MCP ejecuta el servidor del plugin en Bobi con su Python, configuración, auditores y límites de instalación existentes. Las rutas de archivos recibidas por las herramientas son rutas de **Bobi**, no de X. No copiar ni ampliar `runtime.json` para intentar operar sobre otra instalación.

Instalar o conectar este plugin no inicia FiveM, no conecta jugadores y no instala un mod en GTA ni en Nitrado. El MCP independiente `fivem-enhanced-qa` permanece en Bobi. Las pruebas posteriores deben respetar su coordinador, sesiones y lease compartido.

Procedencia, hashes y respaldo del transporte original en `D:\visual-development-toolkit\reports\gta-plugin-install-x-20261015`. Para desinstalar solo de X: `codex plugin remove gta-enhanced-mod-lab@modding-lab`. La desinstalación no afecta al plugin de Bobi.
