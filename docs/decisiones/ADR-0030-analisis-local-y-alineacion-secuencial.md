---
id: ADR-0030
titulo: Análisis local y alineación secuencial de la transcripción
estado: aceptada
fecha: 2026-10-06
---

# ADR-0030 — Análisis local y alineación secuencial

## Contexto

M0/T-08 requiere transcripción con texto y tiempos, CLAP, estética y beats. La residencia de modelos y la descarga por proceso hijo siguen [ADR-0007](ADR-0007-gpu-local-12gb.md) y el [contrato /v1](../arquitectura/contrato-engines.md). Los cinco pesos auxiliares existentes se conservan con sus revisiones y SHA del lock. No se sustituyen por los checkpoints Qwen nuevos `-hf`.

El [código Qwen fijado](https://github.com/QwenLM/Qwen3-ASR/tree/7c6daf77a2421100f5fb066495372c00129d39ff) usa ForcedAligner para obtener tiempos. Su ejemplo de carga conjunta no respeta nuestra residencia única. El [loader oficial beat_this](https://github.com/CPJKU/beat_this/blob/b95c8ab0c58c2d9fcfd40508ae8dffbc05ac4f5c/beat_this/inference.py) reconstruye la arquitectura desde `hyper_parameters` y usa pickle; el peso convertido local conserva los tensores pero no esos metadatos.

## Alternativas

| Opción | Ventaja | Coste o limitación |
|---|---|---|
| Qwen ASR y alineador cargados juntos | Receta upstream directa | Incumple residencia única y suma VRAM; descartada |
| Transcripción con ventanas temporales aproximadas | Evita la segunda carga | No proporciona los tiempos por palabra que necesita el pipeline; no se usa como sustituto |
| ASR seguido de alineación, con descarga intermedia | Tiempos calculados por el modelo y una sola carga residente | Mayor latencia y recarga al alternar etapas; elegida |

## Decisión

`audio.transcribe` usa ASR para producir texto; libera sus referencias, realiza la descarga necesaria y después carga ForcedAligner para alinear **ese texto reconocido**. Nunca se usa la letra esperada como entrada de ASR ni para fabricar una transcripción correcta. La etapa, procedencia y revisión de ambos modelos se conservan en el JSON crudo. Un fallo o resultado de tiempos inválido produce error explícito, sin repartir palabras uniformemente ni presentar ventanas aproximadas como tiempos del modelo. El tope dinámico se aplica antes de cada carga GPU; el padre permanece sin torch/CUDA y `/v1/unload` termina el hijo. La prueba de integración deberá acreditar esta secuencia y su memoria; esta decisión no declara que ya esté verificada.

La capacidad independiente `audio.align_lyrics`, con texto aportado por el usuario, queda preparada y `verified: false` hasta su validación en M3. Alinear la transcripción en T-08 no acredita la fidelidad de una letra cantada, ni convierte CLAP/estética en aprobación musical.

La segmentación y recomposición de tiempos para transcripción hasta600s se concretan en [ADR-0031](ADR-0031-transcripcion-segmentada-con-tiempos-globales.md), que mantiene esta residencia secuencial y hace explícito el límite temporal de la alineación independiente preparada.

El descriptor de transcripción incluye los pesos de ASR y la dependencia de alineación. El `model_id` de `loaded` identifica ese pipeline solicitado, no afirma qué etapa ocupa VRAM en cada instante. Eventos y JSON crudo identifican las etapas y revisiones reales; una petición posterior vuelve a cargar ASR después de liberar el alineador. No se recarga ASR al terminar únicamente para mantener una apariencia de residencia. Los demás modelos de análisis siguen separados y el cambio de pipeline termina el hijo conforme al contrato.

beat_this se ejecuta en CPU. Su arquitectura se reconstruye con configuración JSON derivada del checkpoint oficial, comprobado contra SHA `8c328b45f59d8dd3dff219253ff6a8d6482be57d0133a29140e2febbf8eb8331`, mediante el auditor restringido de `packages/weights`, sin torch ni ejecución de globals del proveedor. Se conserva únicamente la configuración necesaria y su procedencia; runtime carga safetensors y exige correspondencia estricta de tensores. No se llama al loader pickle ni a su descarga automática.

CLAP usa la arquitectura Transformers `ClapModel` declarada por el config local; procesador y tokenizer se cargan desde las rutas fijadas, offline. Audiobox usa su peso safetensors y código fijado. Los loaders fallan ante pesos/configuración/tokenizadores ausentes o distintos del lock; no descargan ni sustituyen modelos en runtime.

## Consecuencias y verificación pendiente

El engine conserva tareas genéricas `/v1`, salidas crudas en `data/tmp/<job_id>/` y proceso hijo exclusivo. No escribe BD, manifiestos de canción ni postproceso. Su proyecto uv y lock son independientes; torch se instala solo en Docker. Base aprobada PyTorch 2.14/CUDA 13 fijada por digest, imports reales y build deben comprobarse antes de GPU.

La base observada contiene Python 3.12.3, torch 2.14.0+cu130, torchaudio 2.11.0+cu130 y torchvision 0.29.0+cu130. Para conservar ese conjunto se crea un venv de contenedor con acceso a system-site-packages: el lock independiente excluye explícitamente esos tres paquetes mediante [exclude-dependencies de uv](https://docs.astral.sh/uv/reference/settings/#exclude-dependencies), y el build comprueba sus versiones/imports contra la base fijada. No se simula una plataforma imposible en los marcadores de dependencias ni se declara que los wheels PyPI puedan sustituir el conjunto. Imports CPU conformes no acreditan inferencia, ABI de todas las operaciones ni soporte GPU; esas pruebas siguen pendientes.

T-08 no se cierra con dobles CPU: requiere su build y pruebas de análisis declaradas sobre audio, tiempos, puntuaciones y clic de 120 BPM. La condición GPU vigente se comprueba antes de cargar modelos; las excepciones de pruebas musicales previas no se extienden a este engine. Estado y pruebas ejecutadas viven únicamente en el [ledger M0](../roadmap/2026-09-28-m0-entorno-y-motor/tasks.md).
