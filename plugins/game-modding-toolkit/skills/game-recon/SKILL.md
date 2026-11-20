---
name: game-recon
description: "Identificar formato, motor y dependencias de una aplicación o juego distribuido antes de su ingeniería inversa. Usar para reconocer el artefacto y elegir analizador; no para crear juegos o generar assets."
---

# Reconocimiento del artefacto

Identifica plataforma, formato, motor, arquitectura y versiones mediante archivos y metadatos. Usa `recon_game` solo para una carpeta de juego Windows seleccionada por el usuario; no lanza el juego. Prefiere las fuentes disponibles cuando basten para la pregunta.

Elige REA para los formatos que soporte el proveedor actual, Ghidra para nativos, ILSpy para .NET administrado y AssetStudio para recursos Unity. Registra ruta, hash y límites; reconoce incertidumbres sin adivinar un motor por nombres de archivo. No conviertas reconocimiento en modificación ni instalación.
