---
documento: pipeline-audio
titulo: Pipeline de audio — post-proceso, formatos y exportación
estado: vigente
fecha: 2026-09-28
actualizado: 2026-10-05
---

# Pipeline de audio

El paquete [`audio_post`](../../packages/audio-post/audio_post/__init__.py) procesa la salida cruda del engine sin torch ni acceso a la BD. T-04 implementa sus funciones y el manifiesto v1. El **worker CPU del server** lo integrará en M1 ([ADR-0017](../decisiones/ADR-0017-postproceso-y-manifiesto-en-el-server.md)). El [CLI de T-07](../../scripts/generate.py) conecta el engine local con este postproceso; su revisión, QA y escucha se registran en el [ledger](../roadmap/2026-09-28-m0-entorno-y-motor/tasks.md).

## 1. Etapas tras la inferencia

```
salida cruda del engine (WAV/FLAC, sr nativo; mock = WAV PCM16, 48 kHz estéreo)
  → validación: duración ±5 % de la pedida, sin NaN/Inf, no silencio (RMS > −60 dBFS),
                sin clipping sostenido (> 0,5 % de muestras a ±1,0)
  → medición: loudness integrado (pyloudnorm, BS.1770-4) y true peak (ffmpeg ebur128=peak=true)
  → master.flac : 24 bit, sr nativo, SIN normalizar
  → listen.mp3  : 320 kbps CBR, objetivo −14 ±0,5 LUFS y true peak ≤ −1 dBTP
                  medidos después de codificar; alimiter si hace falta (post.limiter)
  → peaks.json  : ~2.000 pares min/max por canal (formato compatible con wavesurfer.js)
```

- **Ganancia lineal**, nunca `loudnorm` dinámico: `loudnorm` puede pasar a modo dinámico sin avisar y cambiar la mezcla.
- **Remuestreo** con soxr (`aresample=resampler=soxr`): la escucha conserva 32, 44,1 o 48 kHz; otras tasas pasan a 48 kHz. El master conserva la tasa nativa.
- La lectura y escritura propias usan **soundfile** y **ffmpeg**, nunca torchaudio (ver [entorno.md](./entorno.md), E-07).

[`process_audio`](../../packages/audio-post/audio_post/pipeline.py) corrige la ganancia y, si hace falta, el techo del limitador durante un máximo de 16 intentos. Cada intento mide el MP3 decodificado. Si no consigue ambos objetivos, falla con `AUDIO_TARGET_UNREACHABLE`. `post` registra la ganancia aplicada, la limitación y las mediciones finales.

## 2. API Python disponible

| Función pública | Entrada y resultado | Fuente |
|---|---|---|
| `validate_audio(samples, sample_rate, expected_duration_s)` | Valida forma, tasa entera positiva, duración, NaN/Inf, silencio y clipping; devuelve metadatos | [__init__.py](../../packages/audio-post/audio_post/__init__.py) |
| `make_peaks(samples, count=2000)` | Devuelve versión, canales, longitud en muestras y pares min/max por canal; hasta 2.000 bloques | [__init__.py](../../packages/audio-post/audio_post/__init__.py) |
| `measure_audio(path, *, ffmpeg)` | Mide LUFS y true peak; devuelve `lufs` y `true_peak_dbtp` | [pipeline.py](../../packages/audio-post/audio_post/pipeline.py) |
| `process_audio(source, destination, *, expected_duration_s, ffmpeg)` | Crea master, escucha y peaks; devuelve `outputs` y `post` | [pipeline.py](../../packages/audio-post/audio_post/pipeline.py) |
| `write_manifest(path, manifest)` | Valida procedencia y salidas, calcula `commercial_use` y crea un fichero nuevo | [manifest.py](../../packages/audio-post/audio_post/manifest.py) |
| `verify_manifest(manifest, base_dir)` | Acepta un diccionario o fichero; valida esquema y hashes; devuelve `valid` y número de `outputs` | [manifest.py](../../packages/audio-post/audio_post/manifest.py) |

`process_audio` requiere fuente y destino dentro del proyecto y rechaza enlaces simbólicos y junctions. El destino debe ser nuevo: reutilizarlo produce `FileExistsError`. La función prepara los tres ficheros en un directorio temporal dentro del destino. Si falla, limpia su salida; no publica un conjunto parcial. No escribe el manifiesto automáticamente.

### Procesar una salida del mock

Primero genera el WAV de tres segundos con el [ejemplo del contrato](./contrato-engines.md#arrancar-el-mock-en-local). Después ejecuta desde la raíz:

```powershell
. .\scripts\env.ps1
@'
from pathlib import Path
from audio_post import process_audio, measure_audio

root = Path.cwd()
ffmpeg = next((root / "tools/ffmpeg").glob("*/bin/ffmpeg.exe"))
raw = root / "data/tmp/01ARZ3NDEKTSV4RRFFQ69G5FAV/output-0.wav"
destination = root / "data/tmp/01ARZ3NDEKTSV4RRFFQ69G5FAV/post-example"
result = process_audio(raw, destination, expected_duration_s=3, ffmpeg=ffmpeg)
print(result["post"])
print(measure_audio(destination / "listen.mp3", ffmpeg=ffmpeg))
'@ | uv run --frozen --package audio-post python -
```

Usa un destino nuevo al repetirlo. `outputs` contiene `role`, ruta relativa al destino, MIME, SHA-256, bytes y metadatos. El master mantiene las amplitudes dentro de la precisión de PCM24. `peaks.json` usa los samples originales; sus pares min/max no son la señal normalizada de escucha.

### Escribir y verificar procedencia v1

El esquema vigente es [manifest-v1.schema.json](../../packages/contracts/manifest-v1.schema.json). Los [ejemplos](../../packages/contracts/examples/) muestran `audio_take`, `cli_run` y variantes de procedencia. Son fixtures de prueba, no canciones reales ni resultados de ACE-Step.

El llamante reúne el contexto de modelo, herramientas, petición, derechos y linaje. Después añade `outputs` y `post` devueltos por el proceso y llama a `write_manifest(destination / "manifest.json", manifest)`. La función verifica los ficheros respecto a `destination`; no acepta reutilizar un manifiesto existente.

`write_manifest` recalcula `commercial_use`: cada dependencia de `models`, `tools` e `inputs` debe declarar `true`. Una declaración ausente impide marcar la salida comercial. `verify_manifest` admite declaraciones opcionales ausentes en v1, pero rechaza contradicciones demostrables. No exportes letra literal ni fotografías: se usan hashes y declaraciones, y el escritor rechaza esos contenidos privados.

[`verify_manifest.py`](../../scripts/verify_manifest.py) acepta un fichero o directorio. Busca manifiestos recursivamente y omite JSON auxiliares como `peaks.json`; comprueba esquema, rutas seguras, SHA-256 y bytes cuando se declaran. Devuelve exit 0 si todos son válidos y exit 1 si faltan manifiestos o falla alguno.

```powershell
. .\scripts\env.ps1
uv run --frozen --all-packages scripts/verify_manifest.py packages/contracts/examples/
uv run --frozen --all-packages pytest packages/audio-post/tests -q
```

La [suite](../../packages/audio-post/tests/test_audio_post.py) usa ffmpeg real para master, MP3, limitador y remuestreo. Prueba también manifiestos inmutables y detección de alteraciones. El [informe de QA](../roadmap/2026-09-28-m0-entorno-y-motor/testing/report.md) conserva las salidas de T-04. La primera canción ACE-Step tiene su [recibo técnico separado](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t07/first-song-technical-receipt.json); sus mediciones no sustituyen la escucha del propietario.

### Generar una canción con el CLI de M0

Guarda la letra en un fichero UTF-8 dentro del proyecto y declara su autoría antes de encolar. El estilo se pasa como texto; el descriptor de ACE-Step limita este caption a 512 caracteres. Es un límite local, distinto de los presupuestos nativos de tokens. La CLI transmite los tags y cualquier Markdown presentes, sin normalizarlos. Para un engine local ya arrancado:

```powershell
. .\scripts\env.ps1
uv run --frozen --all-packages scripts/generate.py --lyrics data/inputs/mi-cancion/lyrics.txt --style "Hip hop luminoso, orquesta y piano en mayor" --duration 255 --language es --bpm 94 --seed 1 --lyrics-declaration own --engine http://127.0.0.1:8101
uv run --frozen --all-packages scripts/verify_manifest.py data/cli/
```

`--lyrics-declaration` admite `own`, `assistant`, `public_domain` o `licensed`. Una licencia externa no basta para marcar automáticamente uso comercial. Para una pieza instrumental, usa `--task music.instrumental` y omite letra y declaración. `--variants N` admite de 1 a 64 salidas; cada variante recibe una carpeta nueva. Sin `--engine`, se elige la primera entrada de `STUDIO_ENGINES` en `.env`. El token sale del entorno o de ese fichero y no se imprime.

La otra entrada es `--brief B-02`: lee [briefs.yaml](../../eval/briefs/briefs.yaml) y `eval/briefs/B-02.txt`. El catálogo fija estilo, duración, idioma y BPM; la letra de B-02 aún requiere aportación del propietario. No se sustituye por la letra privada de «Libre» ([ADR-0023](../decisiones/ADR-0023-primera-cancion-con-material-privado.md)).

ACE-Step admite el parámetro opcional `--shift <1–5>`, numérico finito, tanto con entrada directa como junto a `--brief`. Se transmite al modelo y se registra en `request.params.shift` del manifiesto. Omitirlo conserva el comportamiento anterior (upstream 1); no se introduce un nuevo default. La prueba privada de 1 frente a 3 se documenta en [ADR-0026](../decisiones/ADR-0026-comparacion-controlada-shift.md).

El CLI muestra etapas y progreso, descarga el modelo antes de procesar audio y publica `master.flac`, `listen.mp3`, `peaks.json` y `manifest.json` en `data/cli/<fecha UTC>/<run_id>/`. El manifiesto `cli_run` guarda procedencia, parámetros, declaración y hash de letra; el contenido literal de la letra queda fuera. Los datos y el estilo del manifiesto son privados y no se versionan. Una salida anterior nunca se sobrescribe. Los bloqueos transitorios Windows 5/32 se reintentan como máximo cinco veces; un fallo persistente retira solo las carpetas nuevas de ese intento.

Ctrl+C solicita cancelar y espera el terminal del trabajo propio antes de descargar. Se realiza una sola limpieza por ejecución, con un plazo máximo de 300 s, peticiones HTTP de hasta 5 s y confirmación de `loaded: null`; puede esperar a que termine una carga ya iniciada. La interrupción conserva exit 130. Si no se acredita la descarga, imprime `ENGINE_CLEANUP_UNCONFIRMED` y conserva el error original; revisa el estado del engine antes de cargar otro modelo. Nunca cancela ni descarga un trabajo ajeno.

Hasta T-10, ACE-Step mantiene sus capacidades `verified: false`. Una evaluación explícita requiere `STUDIO_ALLOW_UNVERIFIED=1` tanto en el CLI como en el engine; no es el valor de fábrica. Antes de cada carga se aplica la comprobación de Ollama y VRAM del [entorno](./entorno.md).

## 3. Exportación a demanda (M3)

Estas exportaciones son el diseño aprobado para M3; no forman parte de la API implementada en T-04.

| Destino | Formato | Loudness | Notas |
|---|---|---|---|
| **Streaming / web** | MP3 320 o FLAC | −14 LUFS, ≤ −1 dBTP | Opción por defecto |
| **Vídeo / broadcast** | WAV 48 kHz, 24 bit | −23 LUFS (EBU R128), ≤ −1 dBTP | Para Premiere, DaVinci o Avid |
| **Podcast** | WAV 48 kHz o MP3 | −16 LUFS, ≤ −1 dBTP | |
| **Stems** | WAV/FLAC 48 kHz por pista, en un zip | Sin normalizar | Alineados sample a sample con la mezcla |
| **Original** | `master.flac` tal cual | Sin tocar | |

Metadatos que se escriben al exportar:

- título, artista y año;
- comentario con el `take_id`;
- letra embebida (ID3 `USLT` o Vorbis `LYRICS`), si se pide;
- portada, si existe (M3).

## 4. ffmpeg

- **Server (Windows):** build BtbN `win64-lgpl` en `tools/ffmpeg/`, fijada en `tools/tools.lock.json`.
- **Engines (Linux):** build BtbN `linux64-lgpl-shared`, porque torchcodec necesita las `.so`.
- **Comprobación en build o arranque:**
  - `-buildconf` **contiene** `--enable-libmp3lame`, `--enable-libsoxr` y `--enable-libopus`;
  - **no contiene** `--enable-gpl` ni `--enable-nonfree`.

## 5. Stems (M3)

Hay dos vías, según [modelos.md](./modelos.md) §4:

- la tarea `audio.stems` del generador (el extract de ACE-Step, que requiere el checkpoint base);
- un separador dedicado, que se carga después de descargar el generador de la VRAM.

Los stems se guardan como `asset` del take (`role=stem:vocals`, etc.); no generan un take nuevo. **Prueba de conformidad:** la suma de los stems se compara con la mezcla y el error debe quedar por debajo de −30 dB.

## 6. Fidelidad de instrucciones — auditoría T-17

La [auditoría CPU de T-17](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t17/audit-report.md) distingue original, adaptación y entrada efectiva. El código instalado limita la plantilla completa de descripción del DiT a 256 tokens y la letra a 2048; estos presupuestos son distintos del límite local de 512 caracteres. Los originales rechazados solo se reprodujeron en CPU para medir tokens, sin generar audio.

La entrada completa de Libre ya usaba un caption adaptado y cabeceras simplificadas antes de llegar a la CLI. Los versos se conservan. Se ha preparado un candidato privado que recupera indicaciones de las nueve cabeceras, sin generar una toma. Sigue pendiente implementar preflight, procedencia de la adaptación y controles de metadata; presencia de instrucciones en tokens no garantiza cumplimiento musical. T-16 permanece en borrador hasta atender esta prioridad.
