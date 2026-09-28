# ADR-0011 · Selección de modelos y política de licencias

- **Estado:** aceptada (pendiente de confirmar con la medición y la escucha de M0) · **Fecha:** 2026-09-28

## Contexto
Revisión del catálogo abierto de septiembre de 2026 para una RTX 5070 de 12 GB ([`../arquitectura/modelos.md`](../arquitectura/modelos.md)):
- **LeVo 2 y YuE2:** según terceros, son los de mejor calidad abierta, pero sus pesos no permiten uso comercial.
- **MiniMax-Music3:** es el único abierto que aparece en una arena independiente. Su licencia es propia y tiene condiciones.
- **ACE-Step 1.5:** pesos MIT, soporte oficial para 12 GB y operaciones de edición (repaint, cover, extract y LoRA). El extract solo está en el checkpoint base.

## Decisión
1. **Motor principal: ACE-Step 1.5**, con DiT 2B turbo y LM 0.6B en BF16. Es la configuración del tier 4, que es donde ACE-Step coloca los 11,94 GiB de la 5070 ([ADR-0007](ADR-0007-gpu-local-12gb.md)).
   - El LM 1.7B y el XL-turbo se prueban en el benchmark de M0. Solo pasan a ser opción («alta calidad», F-18) si caben con margen y mejoran la escucha.
2. **Motor alternativo: HeartMuLa-oss-3B en 4 bits**, por su castellano. Se evalúa en M0 como tarea opcional y entraría en **M5** (F-74).
3. **Laboratorio** (solo evaluación, opcional): MiniMax-Music3 y, si se quiere comparar, YuE2.
4. **Política de licencias:**
   - El pipeline por defecto solo usa pesos con uso comercial ✅, o ⚠️ con la condición documentada.
   - Un modelo no comercial nunca es el motor por defecto. Sus artefactos llevan `commercial_use: false` en el manifiesto y una marca visible en la biblioteca.
5. **Auxiliares:**
   - Evaluación: Qwen3-ASR-1.7B (WER y tiempos), Qwen3-ForcedAligner-0.6B (LRC), LAION CLAP (convertido desde `.bin`) y Audiobox Aesthetics.
   - Análisis: beat_this.
   - Stems: primero el extract de ACE-Step; después RoFormer vía MSST.
   - Audio: FFmpeg LGPL.

## Motivo
Mantiene abierta la comercialización sin reescribir nada, y ACE-Step es el que más se parece a Suno como producto. Aun así, la arena independiente lo sitúa por debajo de Suno v5. Por eso la decisión se confirma con la escucha de M0 ([`../calidad/evaluacion-escucha.md`](../calidad/evaluacion-escucha.md)) y no antes.

## Revisión
Esta decisión se reabre si ocurre alguna de estas cosas:
- M0 no aprueba a ningún candidato;
- aparece un modelo abierto con pesos comerciales que mejora claramente en la arena;
- se abandona la intención de comercializar.
