# Continuar aquí

> Reanudación actualizada el **2026-10-05**. El estado detallado vive **solo** en el [ledger de M0](docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md).

## Dónde estamos

M0 sigue abierto. La Fase 2 está completada técnicamente: contrato /v1, engine común y mock (T-03), audio-post y manifiesto (T-04). La spec está aprobada y el plan existe; dev-cycle retoma implementación sin evaluar ni planificar de nuevo. M1 espera al cierre de M0.

- Fase 2: revisión adversarial, tercer intento A+B+D sin gaps pendientes; tablas en el ledger.
- QA sin UI por diseño: **125 tests sin GPU** verdes, ruff global y formato de los 23 Python cambiados verdes. Cobertura del diff: **93,62 %**, mínimo 80 %; media por fichero con exclusión declarada de conftest.py sin datos.
- [Informe de QA de Fase 2](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/report.md) y sus evidencias. Ese tramo no declara pruebas E2E ni GPU reales; la matmul GPU de T-05 está acreditada por separado.
- T-03 (`af181de`) y T-04 (`9da20f0`) integradas con commits separados y fast-forward a `main` el 2026-10-05; recibo final `6b371e9`. Los tres commits están publicados en `origin/main`. Se han conservado los journals existentes.
- T-05 integrada y publicada en `main` con commit `19ab239`; rama actual **m0/t-06-acestep-adapter**. `.git` requiere escalación de permisos en este perfil; las integraciones se realizan mediante scripts revisables de `.cache/dev-cycle/`.

**T-05: imagen engine-acestep completada**, con cuatro pruebas CPU del contenedor y 125 adicionales del workspace (Python 3.11.14, torch 2.10.0+cu128 y FFmpeg 7 LGPL shared). La importación CPU de `acestep.handler` también pasa. `uv pip check` informa una incompatibilidad: `nano-vllm` requiere el `flash-attn` excluido expresamente para SDPA/backend `pt`; el revisor B la descarta como defecto para pt, pero no se declara ese check verde. **BF16/sm_120 real verificado:** el propietario autorizó la matmul 64×64 con baseline 2.950 MiB; assert sm_120 y resultado 262144.0, exit 0. Ollama estaba vacío, sin modelo que restaurar. Esa excepción no cubre carga de modelos ni benchmarks posteriores. Revisión A+B+C y [QA sin UI](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t05/report.md) acreditadas; PDF pendiente por herramientas ausentes. La siguiente tarea es **T-06: adaptador ACE-Step**, aún sin generación acreditada.

**T-06 completada técnicamente; integración Git preparada:** adaptador y factoría `/v1` implementados con modos explícitos, loaders locales safetensors y parches auditados. Tras corregir con TDD la precisión de semillas grandes y la clasificación de errores de VRAM, la tercera revisión A+B+C quedó sin gaps pendientes. QA independiente: **179 tests CPU verdes**, cinco skips y uno excluido; cobertura de lo cambiado **94,58 %**, superior al 80 % requerido. La imagen final acredita además **58 tests CPU** con Python 3.11.14. [Informe de QA y evidencias](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t06/report.md).

**Generación GPU real verificada:** una prueba sintética de **30 s**, autorizada expresamente por el propietario con la ocupación de GPU existente, produjo WAV FLOAT a 48 kHz estéreo. Pico VRAM **7.806,80 MiB**, tope **8.810,31 MiB**, `spilled: false`; `unload` terminó el hijo y liberó la carga. El test pasó en 144,74 s. `run_s` incluye la carga: no se suman sus tiempos ni se declara un RTF. Ollama estaba vacío y no hubo modelo que restaurar. Después de la prueba, la GPU registró 1.338 MiB. Las capacidades siguen sin verificarse para producto hasta T-10; esta prueba no acredita calidad musical ni «Libre».

M0 lleva **7/14 tareas completadas**. La siguiente tarea es **T-07: CLI y primera canción**. El propietario ha elegido y escrito el perfil global de WSL: **16 GB de RAM, 8 GB de swap y `autoMemoryReclaim=dropCache`**. A petición suya se ejecutó `wsl --shutdown`, exit 0. Tras arrancar Ubuntu, `/proc/meminfo` mostró 16.375.452 kB totales (15,62 GiB utilizables) y `/proc/swaps` 8.388.608 KiB, sin uso; Docker volvió a responder. [ADR-0025](docs/decisiones/ADR-0025-limite-de-memoria-wsl.md) registra el cambio. La prueba de audio de 30 s se ejecutó con el límite anterior de 24 GB; no acredita todavía el nuevo perfil con una canción completa.

## Cómo retomar

1. Carga el entorno: . ./scripts/env.ps1. Usa uv y el Python gestionado dentro de la carpeta; nunca instales en el Python de la máquina.
2. Lee el ledger y comprueba git status y git log --oneline -5. Conserva los cambios existentes; no añadas todos los ficheros indiscriminadamente. La integración debe respetar ramas y commits por tarea conforme [convenciones](docs/arquitectura/convenciones.md).
3. Docker y WSL funcionan **fuera del aislamiento**, con escalación: Docker Desktop 4.92.0 / Engine 29.8.0. Dentro del aislamiento siguen denegando acceso. Al retomar T-05, `ollama ps` no mostraba modelos cargados y `nvidia-smi` registró 1.400 / 12.227 MiB. No se ha parado ningún servicio ni cambiado ningún modelo de Ollama.
   Para las lecturas CPU de T-06, el prefijo ya autorizado es `docker compose run --rm engine-acestep`. Oculta CUDA dentro del comando (`sh -c "CUDA_VISIBLE_DEVICES= python …"`); añadir `-e` antes del servicio cambia el prefijo y dejó una llamada esperando permiso. La imagen no incluye `rg`: usa AST/pathlib o `grep`. Ejecuta Docker directamente y conserva después la salida, sin envolverlo en pipelines de PowerShell que cambien la autorización.
4. Antes de cualquier nueva carga de modelos en GPU, descarga **solo el modelo** que muestre Ollama, sin parar el servicio ni borrarlo:

       wsl -d Ubuntu -e ollama ps
       wsl -d Ubuntu -e ollama stop mimo:9b-q5  # usa el nombre que indique ps
       nvidia-smi --query-gpu=memory.used --format=csv  # ≲ 1,6 GB

   Al terminar, recarga ese modelo: `wsl -d Ubuntu -e ollama run <modelo>` ([ADR-0022](docs/decisiones/ADR-0022-memoria-tecnica-kwipu-graphiti.md)).
5. Comprueba la integración de T-06 y retoma T-07 con brief determinista, subagente fresco y TDD según .claude/dev.json:

       /custom-agents:dev-cycle docs/roadmap/2026-09-28-m0-entorno-y-motor

   Lee los recibos CPU y GPU existentes. No repitas el build, la matmul ni la prueba de 30 s salvo cambios o fallos nuevos. Continúa con T-07, forzando backend `pt`; antes de una nueva generación comprueba la condición de VRAM y la declaración de autoría de su letra.

## Verificación local disponible

    . ./scripts/env.ps1
    uv run --frozen --all-packages pytest -m "not gpu" -q
    uv run --frozen scripts/export_contracts.py --check
    uv run --frozen scripts/verify_manifest.py packages/contracts/examples/
    uv run --frozen ruff check .

Pre-commit completo quedó sin ejecutar por WinError 5 al crear su entorno con permisos 0700. El lint directo y el formato del alcance pasaron. El formato global señala 14 ficheros históricos fuera de alcance; no se modificaron. T-03/T-04 se verificaron con Python 3.12.14 local y gramática AST 3.11; T-05 verifica Python 3.11.14 real dentro del contenedor.

## Pendientes conocidos

- T-02: STACK_GLOBAL se rechaza siempre de forma fail-closed; la revisión confirmó ese comportamiento.
- T-06: integración real de checkpoints, lectura segura de silence_latent y generación GPU de 30 s acreditadas; completar integración Git y conservar las evidencias.
- T-07: scripts/generate.py y la primera canción por CLI siguen pendientes, junto con la letra propia B-02 y la escucha del propietario.
- No cerrar M0 ni iniciar M1 con estos resultados: faltan primera canción completa, mediciones, capacidades, batería y escucha. El ritual de changelog/retro/cierre corresponde al hito completo.

## Mapa rápido

- [Documentación](docs/README.md) · [constitución](docs/CONSTITUTION.md) · [decisiones](docs/decisiones/README.md).
- [Contrato de engines](docs/arquitectura/contrato-engines.md) · [pipeline de audio](docs/arquitectura/pipeline-audio.md) · [datos](docs/arquitectura/datos.md) · [entorno](docs/arquitectura/entorno.md).
- [Memoria del proyecto](docs/memory/MEMORY.md), dentro del repositorio.
