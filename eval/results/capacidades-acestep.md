---
estado: en-progreso
actualizado: 2026-10-07
verified: false
---

# Capacidades de ACE-Step — informe parcial

La matriz mantiene las 522 filas originales: tres checkpoints, dos superficies, ocho operaciones y cinco features, semillas y controles. Este informe registra únicamente evidencia inspeccionada; no declara cerrada T-10 ni sustituye la escucha.

Hay ocho ejecuciones técnicas aceptadas de 60 s: dos nativas y seis por /v1. Todas usan Turbo; /v1 cubre canción e instrumental con semillas101/102/103. Faltan otros checkpoints, controles, operaciones y aceptación musical. `funciona`, `degradada` o `no funciona` se asignarán al reunir la evidencia correspondiente. Un requisito ausente no equivale a fallo del modelo.

| Checkpoint | Operación o feature | /v1 | Laboratorio nativo | Veredicto musical |
|---|---|---|---|---|
| acestep-v15-turbo | `music.song` | [Audio seed101](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KY4PDQ96RTWYWEMJZ/output-0.wav); [Audio seed102](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KDDC5C1YA0JPMQ5FK/output-0.wav); [Audio seed103](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KW7CE93GGAHGZ4FSV/output-0.wav); técnico aceptado, escucha pendiente | [Audio seed101](../capabilities/t10-native-song60-second-128a0c4629474126982f1cd657b52835/01M49GF1NMKYKKNE0KMS6QJS10/output-0.wav); técnico aceptado, escucha pendiente | Pendiente |
| acestep-v15-turbo | `music.instrumental` | [Audio seed101](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KYKERDBMJV71WX34S/output-0.wav); [Audio seed102](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83K78ZHWA7RNZASW3J1/output-0.wav); [Audio seed103](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KJVDNBMDZ5E04NXZP/output-0.wav); técnico aceptado, escucha pendiente | [Audio seed101](../capabilities/t10-native-instrumental60-839a483c9fef4ab3b8db11e1ef3838c2/01M49HZQ7K5WFE9PA1N3WDN92K/output-0.wav); técnico aceptado, escucha pendiente | Pendiente |
| acestep-v15-turbo | `music.retake` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-turbo | `music.extend` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-turbo | `music.repaint` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-turbo | `music.cover` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-turbo | `music.complete` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-turbo | `audio.stems` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-turbo | `negative_prompt` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-turbo | `bpm` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-turbo | `key` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-turbo | `timbre_ref` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-turbo | `lora` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-sft | `music.song` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-sft | `music.instrumental` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-sft | `music.retake` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-sft | `music.extend` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-sft | `music.repaint` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-sft | `music.cover` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-sft | `music.complete` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-sft | `audio.stems` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-sft | `negative_prompt` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-sft | `bpm` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-sft | `key` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-sft | `timbre_ref` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-sft | `lora` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-base | `music.song` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-base | `music.instrumental` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-base | `music.retake` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-base | `music.extend` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-base | `music.repaint` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-base | `music.cover` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-base | `music.complete` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-base | `audio.stems` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-base | `negative_prompt` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-base | `bpm` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-base | `key` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-base | `timbre_ref` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |
| acestep-v15-base | `lora` | Pendiente de evidencia | Pendiente de evidencia | Pendiente |

## Ejecuciones aceptadas

Los comandos siguientes son las invocaciones reales de los runners privados. El campo `command` heredado en result.json es el comando CLI planificado; no se presenta como CLI realmente ejecutado.

### native_lab · music.song · Turbo · seed101

`uv run --frozen --no-sync --all-packages python -B .cache/dev-cycle/t10/run-native-song60-second.py`

[WAV crudo](../capabilities/t10-native-song60-second-128a0c4629474126982f1cd657b52835/01M49GF1NMKYKKNE0KMS6QJS10/output-0.wav) · [Resultado](../capabilities/t10-native-song60-second-128a0c4629474126982f1cd657b52835/01M49GF1NMKYKKNE0KMS6QJS10/result.json) · [Entrada capturada](../capabilities/t10-native-song60-second-128a0c4629474126982f1cd657b52835/01M49GF1NMKYKKNE0KMS6QJS10/native-receipt.json).
SHA WAV `312ec507da990e81c5eacd5f4c11973bab618b547b6d7a8d88d6be84e06bf57d`; 23040088 bytes. QA: `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t10/native-song60-second-report.md`.

### native_lab · music.instrumental · Turbo · seed101

`uv run --frozen --no-sync --all-packages python -B .cache/dev-cycle/t10/run-native-instrumental60.py`

[WAV crudo](../capabilities/t10-native-instrumental60-839a483c9fef4ab3b8db11e1ef3838c2/01M49HZQ7K5WFE9PA1N3WDN92K/output-0.wav) · [Resultado](../capabilities/t10-native-instrumental60-839a483c9fef4ab3b8db11e1ef3838c2/01M49HZQ7K5WFE9PA1N3WDN92K/result.json) · [Entrada capturada](../capabilities/t10-native-instrumental60-839a483c9fef4ab3b8db11e1ef3838c2/01M49HZQ7K5WFE9PA1N3WDN92K/native-receipt.json).
SHA WAV `8d5d0f9f08819fd5ca89b7f1960ed168d249151706c3e832aa0ac7fa5b32c083`; 23040088 bytes. QA: `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t10/native-instrumental60-report.md`.

### v1 · music.song · Turbo · seed101

`uv run --frozen --no-sync --all-packages python -B .cache/dev-cycle/t10/v1-song60-runner-fix1/run.py`

[WAV crudo](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KY4PDQ96RTWYWEMJZ/output-0.wav) · [Resultado](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KY4PDQ96RTWYWEMJZ/result.json) · [Entrada capturada](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KY4PDQ96RTWYWEMJZ/input-receipt-0.json).
SHA WAV `682ed551843aabb7c4bb8ad2b638cc726b63dca5267c7f5dbeb9cea72376d379`; 23040088 bytes. QA: `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t10/v1-song60-audio-qa-report.md`.

## Prerrequisitos y límites abiertos

- Complete/extract: voces aisladas y mezcla multipista conocida con derechos, alineación y coeficientes reales. Los stems estimados no se convierten en ground truth por sus nombres.
- LoRA: artefacto compatible con licencia y consentimiento, pesos safetensors sellados y loader sin fallback inseguro.
- Key: evaluador tonal autorizado y revisión musical; transportar keyscale no demuestra tonalidad audible.
- Timbre/edit: entradas propias source60/refA30/refB30 preparadas en data/inputs/t10-capabilities/own-audio-v1; su preparación no prueba efecto del modelo.
- Repaint: medir diferencias de PCM y conservación exterior sobre audio real para cada modo; sigue pendiente.
- Naturalidad, inteligibilidad, ausencia vocal instrumental y fidelidad acústica requieren escucha con timestamps. Ningún recibo planned/captured las acredita.
- T-09: calibración con Administrador de tareas pendiente. No se certifica spill cero por NVML ni se construye un ranking con una inferencia.

Los WAV FLOAT originales son la autoridad para preservación exacta. Audiciones MP3/master PCM24 son derivados; las comparaciones usarán el protocolo de ganancia lineal a −16 LUFS.

## Nuevas ejecuciones default aceptadas

### /v1 · music.song · Turbo · seed102

`uv run --frozen --no-sync --all-packages python -B .cache/dev-cycle/t10/v1-defaults-batch/01M49JY83KDDC5C1YA0JPMQ5FK/run.py`

[WAV crudo](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KDDC5C1YA0JPMQ5FK/output-0.wav) · [Resultado](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KDDC5C1YA0JPMQ5FK/result.json) · [Entrada capturada](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KDDC5C1YA0JPMQ5FK/input-receipt-0.json).

SHA WAV `8001cffd2407b53b81f7c6584f79e80f5e7b208b9a398097e810101aa15b260e`; 23040088 bytes. QA: `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t10/v1-defaults-audio-qa-report.md`.

### /v1 · music.song · Turbo · seed103

`uv run --frozen --no-sync --all-packages python -B .cache/dev-cycle/t10/v1-defaults-batch/01M49JY83KW7CE93GGAHGZ4FSV/run.py`

[WAV crudo](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KW7CE93GGAHGZ4FSV/output-0.wav) · [Resultado](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KW7CE93GGAHGZ4FSV/result.json) · [Entrada capturada](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KW7CE93GGAHGZ4FSV/input-receipt-0.json).

SHA WAV `6d9f22d8b80d67c6bb13adf94fbba994bc44199920d195246a49d221e766c3bd`; 23040088 bytes. QA: `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t10/v1-defaults-audio-qa-report.md`.

### /v1 · music.instrumental · Turbo · seed101

`uv run --frozen --no-sync --all-packages python -B .cache/dev-cycle/t10/v1-defaults-batch/01M49JY83KYKERDBMJV71WX34S/run.py`

[WAV crudo](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KYKERDBMJV71WX34S/output-0.wav) · [Resultado](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KYKERDBMJV71WX34S/result.json) · [Entrada capturada](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KYKERDBMJV71WX34S/input-receipt-0.json).

SHA WAV `ed496972b7cb2abadae7d502ba89ec01fd301289b0bf29a1bab376191b26f449`; 23040088 bytes. QA: `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t10/v1-defaults-audio-qa-report.md`.

### /v1 · music.instrumental · Turbo · seed102

`uv run --frozen --no-sync --all-packages python -B .cache/dev-cycle/t10/v1-defaults-batch/01M49JY83K78ZHWA7RNZASW3J1/run.py`

[WAV crudo](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83K78ZHWA7RNZASW3J1/output-0.wav) · [Resultado](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83K78ZHWA7RNZASW3J1/result.json) · [Entrada capturada](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83K78ZHWA7RNZASW3J1/input-receipt-0.json).

SHA WAV `62779620ae28a8f236b77e14bc4a86966ae626bf321ba6ec1fb1e09ff0224ff9`; 23040088 bytes. QA: `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t10/v1-defaults-audio-qa-report.md`.

### /v1 · music.instrumental · Turbo · seed103

`uv run --frozen --no-sync --all-packages python -B .cache/dev-cycle/t10/v1-defaults-batch/01M49JY83KJVDNBMDZ5E04NXZP/run.py`

[WAV crudo](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KJVDNBMDZ5E04NXZP/output-0.wav) · [Resultado](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KJVDNBMDZ5E04NXZP/result.json) · [Entrada capturada](../capabilities/t10-v1-song60-preflight-7215a482a7484c128900d1e65a1ddffa/01M49JY83KJVDNBMDZ5E04NXZP/input-receipt-0.json).

SHA WAV `62cbb8bfd8e0d1311ea30b7108cd7c43674a6a983d24cf5bdf55f961590124a7`; 23040088 bytes. QA: `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t10/v1-defaults-audio-qa-report.md`.
