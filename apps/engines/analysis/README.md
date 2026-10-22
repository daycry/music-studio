# Engine de análisis local

Implementación del contrato `/v1` para M0/T-08, publicada exclusivamente en
`127.0.0.1:8130`. El padre HTTP permanece sin torch/CUDA; el supervisor ejecuta
los modelos en un proceso hijo y `/v1/unload` termina ese proceso. Todas las
capacidades mantienen `verified: false` hasta su validación de producto.

| Tarea | Modelo local | Dispositivo | Pruebas reales |
|---|---|---|---|
| `audio.transcribe` | Qwen3-ASR-1.7B seguido de ForcedAligner-0.6B | GPU, BF16 | Pendientes |
| `audio.align_lyrics` | Qwen3-ForcedAligner-0.6B | GPU, BF16 | Preparada para M3, pendiente |
| `audio.clap` | LAION larger_clap_music, arquitectura Transformers | GPU, BF16 | Pendientes |
| `audio.aesthetics` | Audiobox Aesthetics, ejes CE/CU/PC/PQ | GPU, BF16 | Pendientes |
| `audio.beats` | beat_this final0 | CPU | Clic de 120 BPM comprobado sin CUDA |

La transcripción admite hasta 600 s y reconoce fragmentos contiguos de hasta
180 s sin usar la letra esperada. Conserva texto, idioma e intervalo real de
cada fragmento; agrega el texto y los idiomas siguiendo Qwen. Después libera
ASR una vez, vuelve a medir la VRAM libre y carga el alineador una vez con
**el texto reconocido de cada fragmento**. Alinea esos mismos intervalos y suma
su offset a los tiempos locales. Los fragmentos silenciosos conservan su
intervalo sin pedir tiempos de palabras inexistentes.
Los tiempos son del modelo; un resultado ausente o inválido produce un error.
La siguiente transcripción libera el alineador y vuelve a cargar ASR. El
descriptor del pipeline declara ambos pesos y el JSON crudo identifica etapas,
modelos y revisiones. `loaded.model_id` identifica el pipeline solicitado,
no la etapa interna residente.

La alineación independiente admite como máximo 180 s hasta M3: una letra
aportada no incluye la asociación entre texto y fragmentos que genera ASR.
No se reparte esa letra por heurísticas. Los idiomas de entrada son los nombres
canónicos declarados por Qwen; un idioma inválido o un audio no decodificable
produce `INVALID_PARAMS`, conservando los errores internos y de VRAM.

Cada petición recibe exactamente una entrada `audio` y devuelve un JSON crudo
en `data/tmp/<job_id>/analysis.json`. El engine no escribe la BD ni manifiestos
de canción. CLAP rechaza textos que excedan su presupuesto y conserva
información de su ventana de audio; su puntuación no acredita por sí sola
fidelidad ni naturalidad musical.

CLAP respeta la estrategia configurada por el extractor del checkpoint:
el modelo local no fusionado utiliza `rand_trunc` y un canal de entrada.
Su ventana efectiva es de 10 s: los audios largos se recortan aleatoriamente
a esa ventana y los cortos se rellenan por repetición. La duración original
y la ventana se declaran por separado; no se atribuye un timestamp al recorte
ni cobertura de toda la canción.

## Dependencias y recursos

`pyproject.toml` y `uv.lock` son independientes del workspace raíz. La base
PyTorch 2.14/CUDA 13 está fijada por digest; proporciona torch 2.14.0+cu130,
torchaudio 2.11.0+cu130 y torchvision 0.29.0+cu130. Estos paquetes se excluyen
del resolver uv para conservar la ABI de la base. El entorno Docker utiliza
`--system-site-packages`; no se instala torch en el host. Los paquetes apt
explícitos, los commits upstream y las restantes dependencias están fijados.

Los cinco directorios de modelos se montan en `/models:ro`. Recursos y pesos
se comprueban contra `models/models.lock.json`; solo se cargan safetensors.
CLAP y beat_this utilizan los pesos convertidos existentes. La arquitectura de
beats se conserva en `engine_analysis/resources/beat_this.json`, con la
procedencia del checkpoint auditado. No hay loaders pickle ni descargas runtime:
`HF_HUB_OFFLINE=1` y `TRANSFORMERS_OFFLINE=1` son obligatorios.

El runtime se ejecuta como `engine` (UID 10001). Triton escribe sus compilaciones
en `TRITON_CACHE_DIR=/studio/.cache/triton`, creado con propietario `engine` y
permisos 0755. No necesita escribir en el home `/studio` ni ejecutar como root.
La regresión CPU comprueba escritura y lectura con el FileCacheManager real,
el usuario y la configuración por defecto de la imagen, sin cargar modelos.

Compose reutiliza el token interno y los montajes de ACE-Step: `models:ro`,
`data:ro` y `data/tmp:rw`. Las salidas son datos privados y no se versionan.
El progreso canónico pertenece al [ledger M0](../../../docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md).

## Verificación CPU

Desde la raíz, en PowerShell:

```powershell
docker compose --profile engines build engine-analysis
$projectRoot = (Get-Location).Path
docker run --rm --network none -e CUDA_VISIBLE_DEVICES= -e STUDIO_ENGINE_TOKEN=prueba-cpu `
  -v "${projectRoot}/models:/models:ro" music-studio/engine-analysis:m0-t08-asr-cache `
  uv run pytest tests -m "not gpu" --cov=engine_analysis --cov-report=term-missing -q
```

La prueba real de beats utiliza CPU, genera un clic temporal y exige BPM entre
118 y 122. También comprueba el proceso hijo y su descarga:

```powershell
docker run --rm --network none -e CUDA_VISIBLE_DEVICES= -e STUDIO_ENGINE_TOKEN=prueba-cpu `
  -v "${projectRoot}/models:/models:ro" -v "${projectRoot}/data:/data:ro" `
  -v "${projectRoot}/data/tmp:/data/tmp" music-studio/engine-analysis:m0-t08-asr-cache `
  uv run pytest tests/test_gpu.py -m gpu -k beats -q -s
```

El marcador `gpu` agrupa las pruebas reales del hito, incluida beats CPU.
Ejecutar únicamente beats no verifica las otras tareas GPU ni cierra T-08.

## Verificación GPU pendiente

Antes de cargar modelos, aplica las reglas de GPU compartida de
[AGENTS.md](../../../AGENTS.md) y comprueba la VRAM libre. Prepara un WAV local
con voz reconocible y derechos de uso dentro de `data/tmp/`; el engine no lo
descarga ni sintetiza para simular una transcripción.

```powershell
$env:STUDIO_ANALYSIS_TEST_AUDIO = "tmp/audio-prueba.wav"
docker compose run --rm engine-analysis uv run pytest -m gpu -q
```

Ese comando debe acreditar texto y tiempos reales, CLAP, los cuatro ejes de
Audiobox y el clic de beats. Estas pruebas GPU **no han pasado todavía**.
La alineación independiente sigue pendiente de M3. La residencia secuencial
está definida en [ADR-0030](../../../docs/decisiones/ADR-0030-analisis-local-y-alineacion-secuencial.md).
