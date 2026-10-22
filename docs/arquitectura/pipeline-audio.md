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

La adaptación portable de [ADR-0053](../decisiones/ADR-0053-postproceso-cpu-portable-en-el-server.md) tiene aceptación técnica acotada tras revisión y QA: límite de datos explícito opcional y esquema incluido en el paquete, byte idéntico al canónico, con pruebas de wheel y sdist. El [recibo](../roadmap/2026-09-28-m1-mvp-estudio/testing/t05/portable-audio-post-qa1-root-acceptance.json) conserva los límites Windows/Linux y de custodia. El worker ejecutará el cómputo en un hijo propio del server; el padre conservará publicación y SQLite. La portabilidad del paquete no acredita todavía ese worker ni su despliegue.

## 2. API Python disponible

| Función pública | Entrada y resultado | Fuente |
|---|---|---|
| `validate_audio(samples, sample_rate, expected_duration_s)` | Valida forma, tasa entera positiva, duración, NaN/Inf, silencio y clipping; devuelve metadatos | [__init__.py](../../packages/audio-post/audio_post/__init__.py) |
| `make_peaks(samples, count=2000)` | Devuelve versión, canales, longitud en muestras y pares min/max por canal; hasta 2.000 bloques | [__init__.py](../../packages/audio-post/audio_post/__init__.py) |
| `measure_audio(path, *, ffmpeg)` | Mide LUFS y true peak; devuelve `lufs` y `true_peak_dbtp` | [pipeline.py](../../packages/audio-post/audio_post/pipeline.py) |
| `process_audio(source, destination, *, expected_duration_s, ffmpeg, root=None)` | Valida el límite de datos y crea master, escucha y peaks; devuelve `outputs` y `post`. El server proporcionará su raíz de datos explícita | [pipeline.py](../../packages/audio-post/audio_post/pipeline.py) |
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

Guarda la letra en un fichero UTF-8 dentro del proyecto y declara su autoría antes de encolar. El estilo se pasa como texto. Los límites administrativos actuales son 16384 caracteres de estilo y 32768 de letra; el preflight operativo comprueba además los presupuestos nativos de tokens antes de generar. La letra se conserva por defecto; la limpieza explícita de tags se describe en el apartado de preparación. Para un engine local ya arrancado:

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

La entrada completa de Libre ya usaba un caption adaptado y cabeceras simplificadas antes de llegar a la CLI. Los versos se conservan. Se ha preparado un candidato privado que recupera indicaciones de las nueve cabeceras, sin generar una toma. T-18 añade preparación y procedencia; T-19 aporta el preflight y el idioma estructurado del LM. La presencia de instrucciones en tokens no garantiza cumplimiento musical. La comparación de T-16 requiere estos controles antes de generar.

Las tomas anteriores al transporte corregido conservan su valor histórico, pero no son controles emparejados de una configuración nueva. [ADR-0027](../decisiones/ADR-0027-controles-de-inferencia-sft.md) exige producir Turbo y SFT con el mismo texto/metadata efectiva y recibos actuales, manteniendo intactos los audios anteriores. La comparación cambia checkpoint y pasos/CFG declarados; no permite atribuir diferencias al checkpoint aislado.

Los controles opcionales del CLI son `--inference-steps` y `--guidance-scale`, en entrada directa y briefs. El checkpoint del engine decide el rango: Turbo1–8/default8; SFT1–200/default50 y CFG1–20/default7. CFG explícito se admite únicamente para SFT. El pedido conserva los valores explícitos; el perfil y las capturas validan los defaults usados. Progreso y cancelación siguen el número efectivo de pasos. La captura DiT acredita argumentos a la entrada: Turbo fuerza CFG interno1 después de esa frontera, aunque GenerationParams conserve7. No se describe ese7 como CFG aplicado por Turbo.

### Preparación local antes de generar — T-18

La [decisión ADR-0028](../decisiones/ADR-0028-preparacion-fiel-de-instrucciones.md) conserva el material de origen y la petición efectiva en un recibo privado. `--style` sigue siendo texto. `--source-style-file` declara un archivo con el estilo original cuando el texto de `--style` es una adaptación manual; se guardan ambos y sus diferencias, sin afirmar equivalencia semántica automática.

```powershell
. .\scripts\env.ps1
uv run --frozen --all-packages scripts/generate.py --lyrics data/inputs/mi-cancion/lyrics.md --style "Hip hop luminoso, orquesta y piano en mayor" --source-style-file data/inputs/mi-cancion/style-original.txt --duration 255 --language es --bpm 94 --lyrics-declaration own --strip-tag-markdown --prepare-only
```

`--prepare-only` funciona offline: no consulta el catálogo ni el engine, no carga modelos, no encola audio y no necesita FFmpeg. Devuelve una referencia al recibo en `data/preparations/`. Sus textos y diffs se revisan localmente; no se imprimen las letras ni el prompt en la consola. Un recibo idéntico se reutiliza por hash sin sobrescribirlo. Al generar audio se utiliza la misma preparación y se vincula su procedencia a los manifiestos nuevos; los antiguos permanecen válidos.

`--strip-tag-markdown` retira exclusivamente el envoltorio `**` de una línea de cabecera como `**[Verse - male rap, beat enters]**`. Conserva literalmente el interior, el orden, los versos y los asteriscos que formen parte del resto de la letra. Omitir el flag mantiene identidad. No traduce las cabeceras ni resume sus instrucciones; tampoco extrae automáticamente letra de un documento que incluya notas creativas.

`--key` y `--time-signature` permiten declarar tonalidad y compás. Sus omisiones conservan los valores vacíos upstream: «en mayor» dentro del prompt no inventa una tónica y no se asume `4/4`. Los campos de un brief siguen siendo su fuente cuando se usa `--brief`; los conflictos directos se rechazan. El compás externo `time_signature` se transmite como `timesignature` al motor.

Los cambios de descriptor/adaptador requieren actualizar la imagen del engine para usarlos en Docker. T-18 verifica su código en CPU; la imagen anterior de T-14 no se ha reconstruido en este tramo. La integración de estos controles con el runtime corresponde a T-19; no se presenta la imagen anterior como si incorporase el compás nuevo.

El recibo distingue bytes de origen de texto efectivo, conserva las transformaciones y lleva hashes verificables. Preparar no valida aún los presupuestos del motor: `engine_budget=pending` señala el trabajo pendiente de T-19. Tampoco acredita obediencia ni naturalidad; esas conclusiones siguen en las tareas de evaluación musical.

Al generar, un recibo nuevo añade `execution` con la base de semilla resuelta y el número de salidas. La preparación original permanece intacta; su `seed: null`, si lo había, sigue conservado. Cada manifiesto lleva `request.variant_index`, con semilla exactamente igual a base más índice. El verificador cruza esa correspondencia y el hash declarado de letra con sus bytes originales, incluidos BOM y finales de línea.

### Presupuesto operativo — T-19 en integración

[ADR-0029](../decisiones/ADR-0029-presupuesto-operativo-de-texto-acestep.md) fija un preflight offline con código y tokenizadores locales verificados. El padre HTTP sigue sin torch/CUDA; el contador utiliza un proceso CPU aislado. `estimate` y `jobs` deben rechazar antes de cargar o encolar cualquier entrada que se perdería, y el adaptador directo aplica el mismo control. Un fallo de hash, configuración o timeout no autoriza a generar.

Se cuenta la plantilla completa del DiT: descripción más instrucciones y metadata ≤256 tokens, letra más cabeceras e idioma ≤2048. La política operativa del LM `pt` es entrada más reserva de salida ≤4096; el valor de 131072 del tokenizer no constituye su ventana operativa. En la ruta actual con CoT desactivado, la reserva completa de códigos es `int(duration_s * 5) + 10`. El perfil incluye también la rama unconditional que activa CFG, sin reducir la reserva para encajar.

El upstream del tier 4 fija **480 s con LM**. Una duración superior se rechaza en vez de aceptar el descriptor antiguo de 600 s y limitarla después. La metadata de duración upstream usa segundos enteros; se distingue de la duración de audio solicitada en float. Estas conversiones deben quedar visibles en el recibo, sin presentar ambas como idénticas.

El idioma se transmite al LM como `language` en el YAML entrenado y al DiT como idioma vocal; los tags y versos siguen siendo texto independiente. Tonalidad y compás explícitos se transportan en su formato admitido, sin deducirlos del estilo ni inventarlos al omitirlos. Las funciones CoT de reescritura permanecen desactivadas. Una extracción automática del caption SFT que altere el texto se bloquea.

Los recibos `planned` describen la comprobación previa; los `captured`, las fronteras realmente alcanzadas durante la ejecución. La captura CPU con inferencia sustituida se identifica como probe y no como audio generado. Textos y diffs permanecen privados; la documentación pública usa conteos y hashes. La presencia íntegra de las instrucciones en los tokens no garantiza que el modelo las cumpla musicalmente. Los detalles de interfaz y el recibo de integración se fijan al terminar T-19; su estado está en el ledger.

`/v1/estimate` puede devolver `input_budget`: resumen planned con hashes y conteos, sin textos. Tras una ejecución, el engine puede devolver `result.input_receipts` por variante. El CLI valida su estructura, hash, petición, flags y fronteras capturadas antes de publicar; los conserva en `data/preparations/native-<sha256>.json`. Los manifiestos nuevos añaden referencias opcionales `input_receipts` con SHA-256 e índice de salida; `verify_manifest.py` comprueba esas referencias y su correspondencia con la variante. Los recibos de preparación T-18 y los recibos nativos tienen funciones distintas y ambos permanecen privados. Los engines legados que no devuelvan recibos y los manifiestos anteriores mantienen compatibilidad.

La publicación de recibos usa un temporal confinado y enlace atómico sin sobrescribir. Un fallo de escritura no deja un archivo parcial con el nombre del hash final. El verificador lee cada payload una vez y contrasta el contenido nativo con el efectivo de la preparación privada. Los manifiestos nuevos omiten también `negative_prompt`, además de estilo y letra; ese texto se conserva y compara en privado. Los manifiestos anteriores pueden seguir conteniendo sus campos originales y se validan sin reescribirlos.

El límite administrativo ampliado de ACE-Step es 16384 caracteres de estilo y 32768 de letra; evita limitar por 512 caracteres un texto que sí cabe. Estos máximos no sustituyen los presupuestos de tokens. El preflight operativo debe estar conectado y aceptar la entrada completa antes de generar. La configuración del checkpoint DiT se comprueba contra el lock; un perfil SFT-stems que active `is_lego_sft` no se presenta como canción compatible hasta contar con su adaptador y plantilla correspondientes.

### Resolución nativa del condicionamiento DiT

[ADR-0032](../decisiones/ADR-0032-condicionamiento-dit-segun-rama-nativa.md) define la corrección de integración: el plan debe medir las instrucciones posibles con y sin códigos LM, y la captura debe validar la instrucción resuelta y sus tokens exactos. El cambio interno `text2music` a `cover` no habilita una operación pública nueva. Conservar caption, letra, metadata y reserva LM, y rechazar cualquier rama o instrucción no planificada. Los recibos nuevos declaran candidatos y rama activa; los históricos se preservan. Implementación y validación pendientes en T-16; no se presenta la decisión como soporte ya probado en GPU.


## Publicación durable pendiente de integración

[ADR-0055](../decisiones/ADR-0055-ejecucion-cpu-y-publicacion-durable-por-toma.md) conserva el post lógico agregado y confirma cada toma independientemente. Un fallo de validación no pierde las variantes válidas. El padre prepara un paquete cerrado en staging del mismo filesystem, con manifiesto inmutable que ya declara las rutas finales y un mapping privado para validarlo antes de publicar. Rename no-clobber, intención CAS y confirmación SQLite permiten recuperar las ventanas de fallo sin sobrescribir destinos ajenos ni regenerar una toma ya lista.

La primera unidad implementará el contrato, la migración y los snapshots; el hijo, la publicación, la cancelación, el análisis real y Docker se verifican después. La portabilidad del paquete U1 tiene aceptación técnica acotada registrada en el ledger, pero no acredita el worker integrado. No habilitar un take ni declarar T-05 completa sólo por pruebas de contrato.


## Custodia e IPC del futuro hijo CPU

[ADR-0057](../decisiones/ADR-0057-custodia-propia-y-protocolo-json-del-worker-cpu.md) selecciona módulos stdlib del server sin importar autoridad del benchmark ni engine_common/torch. Windows nace suspendido dentro de Job propio antes de ResumeThread; Linux usa supervisor con subreaper y liveness separado. Sólo cierre completo comprobado libera slots/staging; UNKNOWN conserva custodia. El transporte usa frames JSON UTF-8 acotados y resultados por toma antes del resumen final, sin pickle ni acceso del hijo a SQLite.

Primero se implementa el protocolo puro; después custodia nativa, hijo audio y cola/publicación. Fuente primaria consultada no sustituye pruebas de procesos/grandchildren, ni un decoder prueba recursos devueltos. Estos componentes siguen pendientes de implementación y gates.

## Almacenamiento operativo

[ADR-0089](../decisiones/ADR-0089-reencauce-tras-codex.md) aparca el VHDX ext4 y el journal Windows de ADR-0069/0075. Los datos viven en `data/`, montado en los contenedores. Cada take se publica así:

1. Se escribe en un directorio de staging.
2. Se mueve con `rename` normal a `data/songs/<song_id>/<take_ulid>/`. El id es único, así que no hay colisión y no hace falta `NOREPLACE`.
3. Se confirma la fila en SQLite. Esa fila es la autoridad: un directorio sin fila es huérfano y se limpia al arrancar.

## Contexto privado del ganador (ADR-0070)

[ADR-0070](../decisiones/ADR-0070-contexto-privado-de-request-y-linaje-en-publicacion-audio.md)
conserva request y linaje exactos en `data/private-contexts/<sha256>.json`,
parent-owned, sellado y privado. Manifest v1 añade referencia opcional por
SHA; params públicos son proyección segura sin letra/estilo privados.
El verificador común debe comprobar recibo, sujeto, proyección y linaje,
sin confundirlo con preparación ACE ni controles efectivos del modelo.
Sin referencia nueva se mantienen reglas legacy. No se exportan recibos
privados automáticamente como metadatos públicos. Implementación/QA pendientes.


## Edición CPU autónoma (M2): autoridad y manifiesto v2

[ADR-0074](../decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md) distingue el post de una generación real de una edición autónoma. El post M1 mantiene su ganador, modelo/semilla, PostPlan/PreparedPackage y manifiesto v1. Recortar, aplicar fades/crossfade o preparar A/B desde masters posee plan, ejecución, resultado y recibo CPU propios, sin engine/modelo/semilla ficticios; se implementará con variantes tipadas antes de su RED.

El Publisher final sólo acepta autoridad propia vigente y conserva CAS, custodia comprobada, paquete exacto, rename no-clobber y commit atómico. UNKNOWN bloquea publicación, serving, limpieza y liberación de recursos. El edit crea una Take hija sin cambiar el maestro. Padres y sus modelos son antecedentes; herramientas/pins reales y derechos determinan procedencia y commercial_use.

Edits y previews CPU usan manifiesto v2; inferencia conserva v1 inmutable. A/B no crea Take ni asset job inválido: su preview temporal se sirve desde el recibo privado autorizado, con hashes/derechos/contexto revalidados y límites/lectores vigentes. Lectores despachan versiones y export/import conserva cierre CPU en song v2. Los contratos y verificación integrada siguen pendientes en M2, sin alterar el pipeline histórico validado.


## Medición y perfiles de producción M3

La ruta histórica M0 usa su pyloudnorm/post.limiter y evidencia existentes. M3 adopta sólo perfiles ratificados propios; este apéndice no cambia código ni manifiestos M0. La música sigue local, engines devuelven raw y el server mide/postprocesa/publica. Toda nueva función conserva RED-GREEN-REFACTOR: primer RED acredita ausencia o no conformidad, implementación mínima y gates verdes preceden a liberación.

Se mide audio seleccionado por bytes/SHA y stream explícito. Decoder FFmpeg fijado produce PCM f64le completo N frames/FsHz/C1mono o2L,R, dominio inicial32/44,1/48k. No ReplayGain, canales/tasa implícitos ni clipping al decode. SHA PCM cubre subnormales originales; sólo análisis declara flush0 y contadores. RMS y samplepeak por canal/agregado conservan unidades dBFS y estados de cero; no sustituyen LUFS/dBTP. Clipping nuevo normalizado exige counts de abs≥1/abs>1 iguales0 y TP conforme. Silencio administrativo≤0,001RMS no es generación musical conforme.

Loudness integrado utiliza BS.1770-5/ebur128 fijado: H=Fs/10,B=4H; bloques[jH,jH+B), j0..floor((N−B)/H) sólo si N≥B; K/pesos/gates−70 y relativo−10, igualdad excluida. Última cola no se convierte en bloque con padding; RMS/peak/TP cubren todo N, incluido flushing TP demostrado. N<B con decode completo produce indeterminate/INSUFFICIENT_FRAMES e I insufficient_frames/NULL; con N≥B silencio probado SILENT, gates vacíos acreditados NO_GATED_BLOCKS. Ese orden prevalece sobre su sentinel raw−70, no blanket failed/missing; TP no calculado unavailable y mediciones reales conservadas. Log−70 solo no acredita sentinel: ambigüedad parser/precisión indeterminate/PRECISION_UNPROVEN, con raw completo; fallo real TOOL_FAILED/CANCELLED separado según §10.7, no target aparente. Presets propios streaming−14±0,5LU y podcast−16±0,5; broadcast−23±0,2QC basado en [EBU R128-2023](https://tech.ebu.ch/docs/r/r128.pdf).

Techo TP≤−1dBTP sin tolerancia oculta. Los límites observados incluyen incertidumbre de impresión y algoritmo independientemente calibrados para pin/plataforma/tasas/canales/señales/EOF; ayudan interfaces no prueban precisión. Aceptar únicamente I.lower≥T−t, I.upper≤T+t y TP.upper≤−1, más gates de PCM/formato/rights. Cota ausente o frontera cruzada=indeterminate/PRECISION_UNPROVEN; TP mostrado−1,1 no certifica. Metadata en amplitud lineal se convierte desde intervalo acreditado en amplitud antes evaluar dB; no asignar quantum lineal como dB. [BS.1770-5 oficial](https://www.itu.int/dms_pubrec/itu-r/rec/bs/R-REC-BS.1770-5-202311-I!!PDF-E.pdf), [FFmpeg ebur128](https://ffmpeg.org/ffmpeg-filters.html#ebur128-1).

Separación conserva exactamente4roles vocals/drums/bass/other, Fs/C/N/origen comunes y lag residual0; suma amplitudes originales sin normalización. Error de energía respecto al master padre: Q.upper<1e−3 (<−30dB) en agregado, canal, cada ventana[kFs,min((k+1)Fs,N)) y ventana/canal audible RMS>0,001. RMS referencia≤0,001 usa únicamente residualRMS.upper≤1e−6 y ratioNULL, incluso denominador0. Igualdad energética del límite falla si acreditada; cruce por incertidumbre impide conformidad. Escucha del modelo/pin real sigue requerida, suma adecuada no demuestra aislamiento.

Mixer usa MixRevision sellada y cuatro gains finitas≥0; mute domina, any_solo incluye solos muteados, canales identidad. Oracle materializado=sum(g_eff*stem) sin división/limiter/pan/ducking. Captura digital completa comparte transporte/origen y tasa; lag por prueba aperiódica identificable y canales mismos δ, |δ|≤1. δpositivo significa retraso capture; Oδ=[max(0,−δ),min(N,N−δ)); se compara capture[n+δ] con oracle[n]. N iguales antes shift; todos los bordes descartados con índices/counts y RMS/peak.upper≤1e−6 por lado/canal. Correlación ambigua no demuestra δ0.

Mixer audible exige Q.upper<1e−6 (<−60dB) en todas celdas de overlap; celda silenciosa usa residual absoluto≤1e−6 y ratioNULL. Mute intencional acreditado por los cuatro g_eff0 admite silencio como operación, capturepeak.upper≤1e−6 y lagNULL, sin loudness fabricado. Preview float32/resample necesita conformidad propia contra oracle binary64 antes liberar; escucha/saltos/seek/exports reales son gates independientes.

Export M3 aplica sólo ganancia constante, soxr explícito cuando perfil lo exige y codec estático; limiter disabled. Perfil constant_gain_two_attempts_v1 fija max2 antes efectos: d1=T−I_input observado; si primera salida medible no cumple I, segunda d2=d1+(T−I_final1) sobre entrada original, mismo codec/resample, sólo si predicción TP conservadora permite ensayo. Cada intento final se decodifica y mide completo; no medir el comando/tag ni cascada de MP3. Máximo2 y gates finales de §9; si no caben target/TP, captura AUDIO_TARGET_UNREACHABLE, receipt D-02 PRODUCTION_NOT_CONFORMANT y mostrar no conforme. Sin fallback dinámico ni retry que cambie parámetros silenciosamente.

ZIP stems conserva cuatro roles a48k WAV/FLAC PCM24, gain1, offset0 y N común real. Oracle usa la misma conversión soxr/configuración/flushing; ties-even signed24 q=round_even(x/2^−23) y x∈[−1,1−2^−23], ningún clamp/dither/normalización, comparación≤1LSB acreditada. Ganancia/pico/energía/conversión se registran; no afirmar amplitud matemática idéntica después de resample. Formato/codec/bitrate/delay/padding/tags y letra/cover históricos pedidos se leen independientemente antes publicar. Ayuda/exit0 no acredita tags ni transporte de canción completa.

Original conserva bytes/SHA exactos y no inserta tags nuevos; metadata/letra/cover van a sidecar solicitado D-04. Embedded obligatorio incompatible se rechaza antes efectos. Evidencia production.audio_measurement/1 tiene seis ramas métricas/perfiles cerradas (loudness,stem_sum,mix_equivalence,stems_export,final_export,original), cuatro estados y errors exactos de contrato§10. Original tiene siempre cuatro Metric/Precision/Gate not_requested y decode/PCMNULL, aun global failed SOURCE_MISMATCH/RIGHTS_REQUIRED antes decode o fallo de copia/sidecar; conserva errores y NULLs observados honestos, sin métricas unavailable ni gate indeterminate de magnitudes no pedidas. Las cinco ramas PCM conservan Metric unavailable y gates indeterminate antes cálculo, luego precedencia exhaustiva método/fase de §10.7, sin refs/fases ficticias. rights_ref usa RightsSnapshotRef D-05 cerrado exactamente family rights/reader production.rights/version1/sha256 del snapshot D-03 sellado real; CapturedRef D-02 distinto/intacto, no retagging ni NULL de snapshot genuino consumido. M.omit omite transporte/embedding con M.metadata_refNULL; metadata histórica externa D-04/dependencies y Tags.metadata_ref real se conservan sin igualdad forzada ni texto/cover omitido enviado. Fallos parciales no fabrican N/Fs/hash/Analysis succeeded ni salida completa. Binding efectivo enlaza el mismo archivo final/PCM/N/Fs/C a timing/features/TimelineV2/SceneN01 por campos ya fijados, sin master fantasma ni nuevos DTO. Derechos/linaje/historia originales íntegros, commercial_use conjuntivo; raw privado y resumen sin letra/audio/secreto/path/PID.

Los perfiles no están liberados por esta prosa. Su batería mínima AV01–AV22, calibración independiente, audio real/canción completa, decoder/medidor independientes, escucha, preview/export, codecs/tags y publicación durable se ejecutan en sus tareas. Este apéndice aporta contrato normativo, funciones/audio ejecutados0.
