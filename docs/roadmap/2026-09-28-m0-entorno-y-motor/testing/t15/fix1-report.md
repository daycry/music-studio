# T-15 · correcciones de revisión B, intento 1

Los dos gaps Important se comprobaron contra el arnés y eran correctos. Corregidos exclusivamente en orquestación privada, sin generar música ni modificar producto, ledger, Git, modelos o `.env`. Se conservan las seis tomas planificadas y los parámetros.

## Parada supervisada durante la tanda

`cli-controlled-job.py` reserva el job ULID creado por el padre: sustituye solo el primer `generate.ulid()` del proceso CLI y conserva la función original para los identificadores restantes. La prueba AST confirma que ese primer ULID corresponde a `job_id` y que `read_request`/`environment` no lo consumen. Antes de Popen se persiste el ID propio con caption y preflight.

El padre consulta `/v1/health` cada dos segundos, con timeout de cinco segundos. Si el crecimiento agregado `total_mb - free_mb - baseline_used` alcanza el 95 % del cap positivo, cancela únicamente `/v1/jobs/<ID reservado>`. El motivo es `consumed_budget_conservative`, no una afirmación de spill: otras aplicaciones pueden provocar crecimiento agregado. Dato GPU inválido, fallo de lectura o job ajeno invalidan la generación; nunca se cancela un ID ajeno. La parada deja evidencia privada antes de cancelar; se concede al CLI su limpieza de hasta 300s y se comprueba idle, sin job y sin modelo cargado. Si no puede acreditarse, no se sigue ni se declara éxito. El recibo público elimina también el ID reservado.

## Recuperación de escuchas

Cada MP3 se codifica en un temporal exclusivo del directorio derivado. Antes de publicarlo se comprueban ffprobe (90s ±0,15s por padding MP3, 48kHz, dos canales), loudness y pico. Se guarda atómicamente la procedencia: hash del MP3 completo, hash del master, ganancia y ruta temporal. Solo entonces se renombra a `listen.mp3`; en Windows el rename falla si ya existe destino. Los manifiestos siguen sin sobrescribirse.

La recuperación acepta una copia existente únicamente si tiene checkpoint, hashes/procedencia/ganancia válidos y duración/layout reales correctos. Si hubo caída entre checkpoint y rename puede recuperar el temporal probado. Un archivo parcial, hash cambiado o copia sin prueba previa se rechaza. La referencia Suno ahora usa escritura exclusiva y, cuando existe, exige su hash original en lugar de sobreescribir.

## Evidencia CPU real

```text
. ./scripts/env.ps1
uv run --no-sync --all-packages python .cache/dev-cycle/t15/fix1-cpu-probe.py
CPU scenario1: 95% aggregate budget cancels only reserved job before group completion; idle/unloaded confirmed
CPU monitor failure: generation invalidated, own cancellation requested, no blind continuation
CPU foreign job: never cancelled foreign ID; unload not falsely confirmed
CPU scenario2: real10s MP3 rejected despite correct hash/provenance and safe true peak
CPU90s stereo48k valid; missing checkpoint and hash mismatch rejected
AST3.11 four files OK; first generate.ulid is job_id; read_request/environment do not consume reserved ULID
ALL_FIX1_CPU_CHECKS_PASSED; GPU not executed
exit 0
```

El escenario de recuperación usa MP3 reales de 10s y 90s creados con FFmpeg CPU, sin inputs de usuario. El de supervisión ejecuta las funciones reales extraídas por AST con cliente/proceso simulados; no ejecuta el top-level GPU. La cadencia de dos segundos no garantiza observar picos entre muestras; el cap/stop del engine sigue activo. Revisión fresca y QA pendientes del orquestador; no se declara terminada T-15 ni aprobada la calidad musical.
