# REA 4.1.0: cadenas literales vacías

Parche local del runtime usado por Visual Development Toolkit 1.2.0 en X. No cambia validadores ni configuración. Mantiene literales exactos en propiedades, usa null para etiquetas vacías y escapa identidades vacías o del prefijo reservado sin colisiones. Identidades ordinarias conservadas.

Reproducción, regresiones, respaldo y rollback: D:/visual-development-toolkit/projects/rea-semantic-fix-20261020.

El respaldo previo se conserva en backups/ con hashes. Rollback: ejecutar rollback.py en ese proyecto; rechaza sobrescribir archivos modificados posteriormente.

runtime.patch documenta las cuatro modificaciones. apply_fix.py reproduce las sustituciones sobre REA 4.1.0 original y crea un respaldo al lado del script; no ejecutar de nuevo sobre el runtime ya corregido. Una reinstalación de REA puede reemplazar el parche: verificar la versión y los hashes antes de reaplicarlo. No modifica la caché instalada del plugin.

Se añadió un quinto archivo de runtime: JavaScriptSemanticGraphProjection.js. Sustituye búsquedas lineales repetidas por índices de rangos sobre IR inmutable; conserva orden, empates y resultados. apply_performance.py y range-index-replacement.js reproducen esa mejora después del arreglo de literales. Prueba medida: 6.003 consultas equivalentes, siete grafos con IDs idénticos antes/después y 1.500 consultas adicionales con rangos superpuestos, columnas, empates y nodos ausentes. performance.patch conserva la modificación. El manifiesto y rollback incluyen los cinco archivos persistentes.

Exportación grande: apply_export.py añade export_javascript_application_graph al MCP real. Son siete archivos persistentes en total, incluido un módulo nuevo. Usa el mismo reconstructJavaScriptArtifact y validadores originales, pero serializa los grafos a disco por elementos y devuelve rutas, hashes y contadores. Evita Invalid string length al devolver grafos enormes. Prueba real del MCP: reports/export-mcp-regression.json. No altera analyze_javascript_application ni debilita esquemas. El rollback elimina únicamente el módulo nuevo y restaura los demás archivos después de verificar hashes.
