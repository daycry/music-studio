# Benchmark básico de ACE-Step en la RTX 5070 — M0/T-09

Fecha: 2026-11-06. Las tres generaciones terminaron con CLI exit 0. El estado pertenece al [ledger canónico](../tasks.md).

## Qué se ejecuta

Tres jobs independientes de 120 segundos, con semillas 1, 2 y 3 y una salida por job. Cada job vuelve a cargar el proceso del modelo. No se vacían las cachés de archivos del sistema operativo.

El engine usa ACE-Step 1.5 Turbo, LM 0.6B, BF16, backend PT y tier 4 explícito. Turbo utiliza ocho pasos y shift efectivo 1; la solicitud no añade CFG. Se desactivan las reescrituras CoT de caption, idioma y metadatos.

La CLI existente `scripts/generate.py` recibe la letra y el estilo privados de «Libre», español, BPM 94 y declaración de autoría `own`. La duración técnica es 120 segundos, no la canción completa. Se conservan originales, preparación efectiva y recibos nativos; este benchmark no valida calidad musical ni parejas SFT/Turbo.

La letra tiene SHA-256 `421a2aaa97998b38b71db4aa939f468e4f6fb54a0b3d0c895d93fbae7ad5e635`. El estilo efectivo tiene SHA-256 `22471b4c4326638c937d5ac12347ca84ddc3b90407a590f3d5abcdc071e1757b`. No se publica su contenido.

## Tiempos y memoria observados

| Semilla | Audio real (s) | CLI completa (s) | Inferencia sincronizada (s) | Pico host (`nvidia-smi`, MiB) | `spilled` terminal |
|---|---:|---:|---:|---:|---|
| 1 | 120,00 | 229,56 | 30,69 | 9.376 | `false` |
| 2 | 120,00 | 185,49 | 33,74 | 9.394 | `false` |
| 3 | 120,00 | 182,51 | 37,28 | 9.394 | `false` |

La CLI completa incluye comprobaciones previas, carga del proceso y posprocesado CPU. La inferencia sincronizada mide sólo `upstream_generate_music`, según el evento real. No se suman `load_s` y `run_s` para reconstruir un tiempo total.

La mediana fue 185,49 segundos por ejecución completa y 33,74 segundos de inferencia para 120 segundos de audio. Son tres cargas de proceso independientes; no estiman el rendimiento de un servicio con el modelo ya cargado.

| Semilla | Carga informada (s) | Pico allocator (MiB) | Presupuesto allocator (MiB) | Muestras host |
|---|---:|---:|---:|---:|
| 1 | 135,42 | 7.809,74 | 10.191,91 | 902 |
| 2 | 111,14 | 7.809,74 | 10.212,71 | 733 |
| 3 | 105,34 | 7.809,74 | 10.194,96 | 716 |

El muestreo host usa `nvidia-smi` cada 250 ms. Ese pico incluye otros consumidores y puede omitir picos entre muestras. La primera captura conserva hora local; la columna original `utc` del CSV está mal rotulada y no acredita UTC.

`spilled:false` procede literalmente de `done.data.telemetry` del NDJSON original. El guard compara el pico del allocator de PyTorch con su presupuesto, calculado desde VRAM libre menos margen. **No mide directamente la memoria compartida de WSL ni certifica ausencia absoluta de paginación.**

## De dónde salen los resultados

La imagen `music-studio/engine-acestep:t09-20261106` se construyó desde el Dockerfile y el lock actuales: `sha256:761384424101a4b7c24994d124bed352594c230f6a50bec59327a3ef6916de56`. El upstream está fijado en `dce621408bee8c31b4fcf4811682eb9359e1bc94`.

QA verificó 26 archivos de modelos contra el lock antes y después. Coinciden las 68 fuentes seleccionadas y los 71 archivos ajenos preservados; 53 fuentes copiadas de la imagen coinciden con el checkout. No hubo cambios de producto.

El contenedor aislado publica sólo `127.0.0.1:18109`, usa autenticación privada, modelos de lectura y modo offline. La CLI M0 gestiona el posprocesado fuera del engine; no se consulta SQLite. `STUDIO_ALLOW_UNVERIFIED=1` permite la prueba del descriptor aún no aceptado por el propietario; mantiene los controles de pesos y memoria.

El [resumen privado](../../../../.cache/dev-cycle/20261106-m0-t09/qa/summary.json) y las carpetas por semilla conservan comandos sin texto privado, NDJSON, manifests, audio y CSV. Los recibos crudos y el audio quedan fuera de Git.

El primer job terminó con CLI exit 0. Después falló el extractor QA al buscar `telemetry` en la raíz del evento. El campo real está en `data.telemetry`. Se conserva el fallo del harness; la lectura del NDJSON original acredita la fila sin repetir esa generación.

## Archivos y limpieza verificados

`verify_manifest` pasó para los tres resultados. FFprobe confirmó 120 segundos, 48 kHz y estéreo en los masters; los MP3 de escucha también son válidos. Los tres recibos capturados contienen backend observado `pt` y huella de los códigos reales. Las huellas difieren entre semillas, como queda registrado; no se compara aquí ningún par SFT/Turbo.

Después de cada job, el engine quedó `idle`, sin modelo cargado ni proceso hijo. El [recibo de limpieza](../../../../.cache/dev-cycle/20261106-m0-t09/qa/cleanup.json) acredita contenedor propio retirado y tres servicios demo conservados. Ollama permaneció vacío, como al inicio; GPU final 1.228 MiB ocupados. Los audios permanecen privados para la escucha posterior.

QA ejecutó `ledger-lint.py`: salida 0, cero incoherencias y 25 avisos históricos. `coverage-check.py` devolvió salida 0 y `applies:false`, por `test-plan: n/a (sin UI)`. No hay código cambiado que medir; ese resultado no acredita un porcentaje de cobertura. [Informe QA](../../../../.cache/dev-cycle/20261106-m0-t09/qa/report.md).

## Revisión del cierre

Revisión A/B, intento 1: sin hallazgos. Las dos lentes contrastaron NDJSON, CSV, manifests, audios y límites de la medición. Scope: salida 0, sin exclusiones ni avisos; el selector no activó C ni D. [Veredictos](../../../../.cache/dev-cycle/20261106-m0-t09/review-1/verdicts.md).

QA final `PASS_T09_FINAL_DOCS_EVIDENCE`: 37 comprobaciones conformes, cero gaps; 12 hashes raw, 68 fuentes, 71 archivos ajenos y 18 enlaces contrastados. [Comprobación documental](../../../../.cache/dev-cycle/20261106-m0-t09/qa/final-docs/report.md). No se repitieron generaciones ni suites por el cierre documental.

El orquestador acepta el cierre técnico de T-09. M0 y M1 siguen abiertos; este benchmark no elige modelo ni acepta musicalmente el producto. La rama permanece apilada sobre T-16, pendiente de completar esa tarea.
