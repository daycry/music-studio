# ADR-0026 — Comparar shift sin cambiar el valor por defecto

- **Estado:** aceptada
- **Fecha:** 2026-10-05
- **Decisor:** propietario; autorización «adelante» a la prueba de tres pares
- **Ámbito:** M0/T-14, ACE-Step y CLI

## Contexto

El propietario percibe desajustes de ritmo, afinación y carácter de voz en la primera toma de «Libre» y aporta su material Suno como referencia privada. El adaptador dejaba el parámetro shift al default upstream 1. La documentación oficial recomienda 3 para Turbo, pero no demuestra que ese cambio resuelva los problemas percibidos. [Inferencia oficial](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INFERENCE.md).

## Decisión

Se incorpora `shift` como parámetro opcional numérico finito entre 1 y 5 en el descriptor de ACE-Step y `--shift` en la CLI, también como override explícito de un brief. Se transmite sin cambiar los demás parámetros y se registra en el manifiesto. Su omisión conserva el comportamiento anterior: el upstream usa 1. La API genérica /v1 no cambia y ningún indicador `verified` se activa por esta incorporación.

T-14 prepara tres pares de 90 s con las semillas 1, 2 y 3, misma entrada privada (primer verso y primer estribillo), mismos parámetros y modelo; solo varía shift 1/3. Se conservan originales y generaciones anteriores. El orden de escucha se oculta mediante códigos, el mapa queda privado y la igualación usa únicamente ganancia lineal, reduciendo el objetivo común si los picos lo requieren. El audio Suno es una referencia artística, no una entrada al modelo ni un control causal entre motores.

La prueba no cambia la letra, no entrena modelos, no elige un ganador sin escucha del propietario y no sustituye la batería fija ni el cierre de M0. Una preferencia en fragmentos no acredita la estructura ni el final de una canción completa. Las semillas fijadas no se presentan como garantía de determinismo bit a bit.

## Consecuencias

Permite investigar una variable concreta sin imponer un nuevo default. TDD/revisión/QA verifican validación y propagación; GPU/manifiestos/telemetría acreditan ejecución. La evaluación musical corresponde a la escucha humana. La siguiente comparación de prompts o de modelos se decide a partir de esa evidencia y se mantiene separada.

## Referencias

- [Ledger M0, T-14](../roadmap/2026-09-28-m0-entorno-y-motor/tasks.md).
- [Diagnóstico inicial T-07](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t07/prompt-model-diagnosis.md).
- [Pipeline y CLI](../arquitectura/pipeline-audio.md).
