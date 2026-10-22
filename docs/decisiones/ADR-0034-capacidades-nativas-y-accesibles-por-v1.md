# ADR-0034 — Capacidades nativas y accesibles por /v1

- **Estado:** aceptada; implementación y mediciones pendientes
- **Fecha:** 2026-10-06
- **Decisor:** orquestador, con autorización del propietario para elegir las mejores alternativas del roadmap
- **Ámbito:** M0/T-10; complementa ADR-0006, ADR-0007, ADR-0017 y ADR-0033

## Contexto y alternativas

T-10 exige medir ocho operaciones, cinco features de canción y la conservación del audio fuera de la región de repaint. El adaptador actual sólo expone canción e instrumental. Un rechazo de esa superficie no demuestra incapacidad nativa del checkpoint; un éxito del modelo fuera del adaptador tampoco acredita una capacidad del producto.

| Opción | Ventaja | Coste o riesgo |
|---|---|---|
| O1: /v1 real y laboratorio nativo seguro, con evidencia separada | Evalúa el alcance completo sin integrar prematuramente edición | Harness de investigación y custodia de dos superficies |
| O2: ampliar /v1 antes de medir | Una superficie integrada | Adelanta piezas de M2/M3/M5 antes de conocer su funcionamiento |
| O3: sólo /v1 actual | Resultado inicial barato | Deja sin respuesta capacidades nativas y repaint; insuficiente para cerrar T-10 |

## Decisión

Elegir **O1**. La matriz mantiene `music.song`, `music.instrumental`, `music.retake`, `music.extend`, `music.repaint`, `music.cover`, `music.complete` y `audio.stems`, junto a `negative_prompt`, `bpm`, `key`, `timbre_ref` y `lora`. Cada caso conserva checkpoint, modo, comando, estado de ejecución y veredicto por superficie. Una operación compuesta se identifica como tal, sin prometer una API nativa inexistente.

El laboratorio usa el código fijado y loaders seguros, hijo propio, un residente GPU, cap dinámico, cancelación/unload y crudos en `data/tmp/<job_id>/`. Reutilizar el preflight de canción no acredita los límites de edición ni la seguridad de PEFT/LoRA: esas rutas se auditan antes de cargarlas. No ejecutar una CLI upstream sin estas garantías. Planes, fuentes, audio, recibos y mapas se custodian en las carpetas privadas de evaluación; el llamante realiza copias y post-proceso.

`verified=true` requiere funcionamiento real en la superficie de producción, en el checkpoint/modo documentados y con evidencia sellada. Rechazo, no-op, resultado degradado, prerequisito pendiente o éxito exclusivo del laboratorio conservan `false`. El transporte de un prompt se distingue de su cumplimiento musical. Un recurso ausente se registra pendiente, sin inventar fallo inferencial, audio o puntuación.

Para repaint, comparar PCM por patrón de bits fuera de la región, antes/después del splice y contra fuente original/procesada. No usar MP3/PCM24 normalizado como ground truth. Si la salida requiere empalme, documentarlo; un empalme experimental del llamante no convierte la operación en capacidad accesible de /v1.

Los materiales pueden ser un corpus propio/autorizado o componentes generados por separado y mezclados con coeficientes, alineación y hashes conocidos. La separación estimada no es ground truth real. LoRA exige archivo compatible/licenciado, configuración y auditoría de loader; no se inicia entrenamiento M5 implícito para forzar M0. La tonalidad y la escucha necesitan evaluadores acreditados, sin confundir métricas automáticas con naturalidad.

## Consecuencias y verificación

Primero termina el freeze/revisión/QA de T-09, que comparte archivos. Después se asigna ownership de T-10, con TDD y gates del dev-cycle. La implementación de transporte de edición del producto conserva su lugar en el roadmap; no se amplía silenciosamente /v1 por este diseño.

El [diseño](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t10/capabilities-design.md) concreta casos, controles, prerequisitos y repaint. El [ledger](../roadmap/2026-09-28-m0-entorno-y-motor/tasks.md) conserva el estado y las mediciones: la preparación no cierra T-10 ni habilita M1. Se publicará `eval/results/capacidades-acestep.md` tras verificación y escucha. El motor inicial no cambia por esta decisión.
