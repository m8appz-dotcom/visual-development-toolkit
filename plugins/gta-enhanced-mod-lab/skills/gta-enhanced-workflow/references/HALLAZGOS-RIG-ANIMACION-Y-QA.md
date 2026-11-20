# Rig, animación y separación de telemetría: caso Enhanced

Nota de campo, 2026-10-15. Evidencia local de Capitán en FiveM Enhanced, juego build 3788. No es una regla universal de reparación ni una aprobación visual. No incluye assets, código de terceros ni rutas privadas del proyecto.

## Contrato entre animación y esqueleto

Un YCD puede contener canales BonePosition que el esqueleto efectivo no aplica. En este caso, pelvis y Spine_Root no habilitaban TransX/Y/Z en los dos contenedores con esqueleto, YFT y YDD. La comparación A/B cambió únicamente esos flags en ambos archivos; conservó reposo, malla, skin y YCD. La pelvis pasó de coincidir con el origen del root a seguir el desplazamiento animado. En 95 muestras reproducidas, sin ragdoll y posteriores a 100 ms, el error máximo de posición de pelvis frente a la referencia fue 0.164 mm.

Ese límite corresponde a pelvis: no demuestra precisión del cuerpo entero, contacto de armas, locomoción o apariencia. El ensayo tampoco corrigió la inclinación al correr. Una comparación de nombres o cantidad de huesos habría omitido el problema.

Procedimiento reutilizable:

1. Identificar qué archivos contienen los esqueletos realmente cargados y qué clips se ejecutan. Comparar tags, jerarquía, reposo y flags, incluidos YFT y YDD cuando ambos correspondan al ped.
2. Contrastar canales animados de posición/escala con las capacidades de los huesos destino. Una diferencia es un punto de revisión; puede ser intencional o depender del rig/runtime.
3. Cambiar una variable en copias aisladas, conservar controles y leer de vuelta el binario compilado. Medir pose con fase real, espacio local del actor y referencia explícita, sin alinear artificialmente los resultados.
4. Separar transformación interna pelvis/root de movimiento de la entidad en mundo; comparar cada muestra con su fase, sin emparejar a ciegas tiempos de ejecuciones diferentes.

No activar TransXYZ en todos los huesos como reparación automática. La herramienta actual `audit_mod_assets` no realiza todavía este cruce YCD↔flags YFT/YDD.

## Retarget y ejes

Aplicar la inversa affine de un rebind por frame había introducido escala no uniforme/shear en este retarget. Una solución específica usó FK rígido con longitudes del destino, conservando la rotación anatómica del rebind y el desplazamiento fuente de pelvis. Las ramas de pelvis y torso necesitaron deltas coherentes. Esto no autoriza eliminar escalas intencionales en otros rigs.

La conversión de eje debe demostrarse contra fuente y runtime. En este caso ya se había convertido combate +X a frente local +Y; otra rotación global de 90° no estaba respaldada por las medidas. No ajustar yaw, reposo o poses sólo para mejorar una captura.

Cuando la fuente tiene ramas de ataque/cancelación y fases de contacto, conservar su semántica: concatenarlas puede alterar movimiento y duración. Las posiciones óseas no equivalen por sí solas a superficies de contacto. La lectura estática y los errores numéricos no sustituyen video real ni evaluación perceptiva del corte final.

## Telemetría y pruebas de combate

Un retraso observado separó 612 ms del reloj de red de 118 ms del reloj de juego dentro de una espera. Había transferencias voluminosas pendientes. Se añadió, sólo al fixture de QA, una barrera entre movimientos y antes de verificar resultados. Dos ejecuciones frías posteriores, una por variante de ped con el mismo paquete, pasaron sus comprobaciones funcionales. Esto demuestra utilidad local del aislamiento; no identifica la transferencia como causa exclusiva ni garantiza estabilidad general.

El ejecutor debe distinguir reloj de juego, red y captura; registrar fase/tarea/ACK; exigir confirmación de escritura; vincular ACK a emisor, generación, duelo, captureId, filas y bytes; abortar ante timeout/cancelación; y comprobar archivos reales, rutas únicas y hashes antes de declarar evidencia completa. Un array vacío o metadatos sin readback no son éxito.

Implementación: mantener estos controles en el MCP/ejecutor de FiveM, responsable de sesiones, cancelación y transferencia. La barrera es opcional de QA, no una espera que deba añadirse al combate normal. No ampliar ventanas de contacto, daño o tolerancias para esconder retrasos. El runner stock de Mod Lab no pasa a ejecutar combate personalizado por esta nota.

## Promoción y límites

Siguiente fase propuesta: diagnóstico de solo lectura de canales animados frente a flags de cada esqueleto, con avisos por diferencias entre YFT/YDD y escala no uniforme. Requiere fixtures compatibles, incompatibles y casos intencionales/no soportados. Debe informar alcance y cobertura; nunca reparar automáticamente ni certificar gameplay.

Las recetas exactas por hueso, calibraciones, fuentes, recibos, hashes, clips y videos permanecen en el proyecto. Los modelos usados son trazabilidad, no una clasificación de eficacia: no hubo comparación controlada entre modelos. La corrección A/B del rig precedió a la orden de seguir la nueva ruta de Mod Lab; no atribuir su éxito exclusivamente al plugin.

Los dos videos finales de este caso seguían pendientes de revisión Gemini4Argon, y la prueba con dos humanos y la aceptación completa de Thor también estaban pendientes al registrar esta nota. Mantener separadas aprobación estructural, funcional, perceptiva y multijugador.
