# Continuar aquí

> Reanudación actualizada el **2026-10-05**. El estado detallado vive **solo** en el [ledger de M0](docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md).

## Dónde estamos

M0 sigue abierto. La Fase 2 está completada técnicamente: contrato /v1, engine común y mock (T-03), audio-post y manifiesto (T-04). La spec está aprobada y el plan existe; dev-cycle retoma implementación sin evaluar ni planificar de nuevo. M1 espera al cierre de M0.

- Fase 2: revisión adversarial, tercer intento A+B+D sin gaps pendientes; tablas en el ledger.
- QA sin UI por diseño: **125 tests sin GPU** verdes, ruff global y formato de los 23 Python cambiados verdes. Cobertura del diff: **93,62 %**, mínimo 80 %; media por fichero con exclusión declarada de conftest.py sin datos.
- [Informe de QA de Fase 2](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/report.md) y sus evidencias. Ese tramo no declara pruebas E2E ni GPU reales; la matmul GPU de T-05 está acreditada por separado.
- T-03 (`af181de`) y T-04 (`9da20f0`) integradas con commits separados y fast-forward a `main` el 2026-10-05; recibo final `6b371e9`. Los tres commits están publicados en `origin/main`. Se han conservado los journals existentes.
- T-05 integrada y publicada en `main` con commit `19ab239`; T-07 publicada como cd9b79d; T-14 integrada por fast-forward a **main**. `.git` requiere escalación de permisos en este perfil; las integraciones se realizan mediante scripts revisables de `.cache/dev-cycle/`.

**T-05: imagen engine-acestep completada**, con cuatro pruebas CPU del contenedor y 125 adicionales del workspace (Python 3.11.14, torch 2.10.0+cu128 y FFmpeg 7 LGPL shared). La importación CPU de `acestep.handler` también pasa. `uv pip check` informa una incompatibilidad: `nano-vllm` requiere el `flash-attn` excluido expresamente para SDPA/backend `pt`; el revisor B la descarta como defecto para pt, pero no se declara ese check verde. **BF16/sm_120 real verificado:** el propietario autorizó la matmul 64×64 con baseline 2.950 MiB; assert sm_120 y resultado 262144.0, exit 0. Ollama estaba vacío, sin modelo que restaurar. Esa excepción no cubre carga de modelos ni benchmarks posteriores. Revisión A+B+C y [QA sin UI](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t05/report.md) acreditadas; PDF pendiente por herramientas ausentes. La generación real y el cierre de T-06 se acreditan a continuación.

**T-06 completada e integrada en `main` (`11c1884`, publicada en `origin`):** adaptador y factoría `/v1` implementados con modos explícitos, loaders locales safetensors y parches auditados. Tras corregir con TDD la precisión de semillas grandes y la clasificación de errores de VRAM, la tercera revisión A+B+C quedó sin gaps pendientes. QA independiente: **179 tests CPU verdes**, cinco skips y uno excluido; cobertura de lo cambiado **94,58 %**, superior al 80 % requerido. La imagen final acredita además **58 tests CPU** con Python 3.11.14. [Informe de QA y evidencias](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t06/report.md).

**Generación GPU real verificada:** una prueba sintética de **30 s**, autorizada expresamente por el propietario con la ocupación de GPU existente, produjo WAV FLOAT a 48 kHz estéreo. Pico VRAM **7.806,80 MiB**, tope **8.810,31 MiB**, `spilled: false`; `unload` terminó el hijo y liberó la carga. El test pasó en 144,74 s. `run_s` incluye la carga: no se suman sus tiempos ni se declara un RTF. Ollama estaba vacío y no hubo modelo que restaurar. Después de la prueba, la GPU registró 1.338 MiB. Las capacidades siguen sin verificarse para producto hasta T-10; esta prueba no acredita calidad musical ni «Libre».

M0 lleva **10/16 tareas completadas**; T-14 se añadió con autorización del propietario. T-07 está cerrada técnicamente; la siguiente fase es **Medición y elección (T-08–T-13)**. La calidad musical de «Libre» sigue sin aprobarse. El propietario ha elegido y escrito el perfil global de WSL: **16 GB de RAM, 8 GB de swap y `autoMemoryReclaim=dropCache`**. A petición suya se ejecutó `wsl --shutdown`, exit 0. Tras arrancar Ubuntu, `/proc/meminfo` mostró 16.375.452 kB totales (15,62 GiB utilizables) y `/proc/swaps` 8.388.608 KiB, sin uso; Docker volvió a responder. [ADR-0025](docs/decisiones/ADR-0025-limite-de-memoria-wsl.md) registra el cambio. La prueba de audio de 30 s se ejecutó con el límite anterior de 24 GB; la canción completa de T-07 verifica después el nuevo perfil sin uso de swap.

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
5. Retoma la fase de medición con brief determinista, subagente fresco y TDD según .claude/dev.json:

       /custom-agents:dev-cycle docs/roadmap/2026-09-28-m0-entorno-y-motor

   Lee los recibos CPU y GPU existentes. No repitas el build, la matmul ni la prueba de 30 s salvo cambios o fallos nuevos. T-07 ya tiene canción completa, revisión A+B+D y QA verdes. Conserva backend `pt`; antes de una nueva generación comprueba la condición de VRAM y la declaración de autoría de su letra.

## Verificación local disponible

    . ./scripts/env.ps1
    uv run --frozen --all-packages pytest -m "not gpu" -q
    uv run --frozen scripts/export_contracts.py --check
    uv run --frozen scripts/verify_manifest.py packages/contracts/examples/
    uv run --frozen ruff check .

Pre-commit completo quedó sin ejecutar por WinError 5 al crear su entorno con permisos 0700. El lint directo y el formato del alcance pasaron. El formato global señala 14 ficheros históricos fuera de alcance; no se modificaron. T-03/T-04 se verificaron con Python 3.12.14 local y gramática AST 3.11; T-05 verifica Python 3.11.14 real dentro del contenedor.

## Pendientes conocidos

- T-02: STACK_GLOBAL se rechaza siempre de forma fail-closed; la revisión confirmó ese comportamiento.
- T-06: completada, integrada y publicada en `main` (`11c1884`); generación GPU de 30 s y unload acreditados.
- T-07: completada técnicamente en la rama `m0/t-07-cli-first-song`, con integración por fast-forward a main. CLI real exit 0, dos tomas privadas preservadas, manifiestos válidos; revisión A+B+D intento 3 sin gaps y QA 243 tests CPU verdes, cobertura 93,98 %. El propietario escuchó la primera toma y percibe problemas de ritmo/encaje, afinación y carácter de voz. Calidad no aprobada. [Diagnóstico y comparación propuesta](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t07/prompt-model-diagnosis.md): shift actual 1 frente a recomendado 3 para Turbo, hipótesis aún sin A/B. Referencias Suno en copias privadas; originales intactos. [ADR-0023](docs/decisiones/ADR-0023-primera-cancion-con-material-privado.md) mantiene B-02 separada y fija.
- No cerrar M0 ni iniciar M1 con estos resultados: faltan mediciones, capacidades, batería y selección final por escucha (T-08–T-13). El ritual de changelog/retro/cierre corresponde al hito completo.

## Mapa rápido

- [Documentación](docs/README.md) · [constitución](docs/CONSTITUTION.md) · [decisiones](docs/decisiones/README.md).
- [Contrato de engines](docs/arquitectura/contrato-engines.md) · [pipeline de audio](docs/arquitectura/pipeline-audio.md) · [datos](docs/arquitectura/datos.md) · [entorno](docs/arquitectura/entorno.md).
- [Memoria del proyecto](docs/memory/MEMORY.md), dentro del repositorio.

## Reanudación tras T-14 — escucha pendiente

T-14 completada técnicamente e integrada por fast-forward a `main`. `shift` opcional entre 1 y 5 conserva el valor anterior cuando se omite. Revisión A+B, intento 2, sin gaps; **282 pruebas CPU** y cobertura **94,57 %** conformes. Imagen final: 75 pruebas CPU, digest `ca67e3d…`. Seis tomas reales de 90 s: semillas 1/2/3 por shift 1/3, sin desbordamiento, con descarga del proceso confirmada y swap WSL pico de 0,4375 MiB. [QA y recibo](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t14/report.md). Ollama vacío, sin modelo que restaurar.

Escucha privada lista: `data/eval/libre-shift/01M46K3MT0JNZB0DYC0F4DZADQ/listen.html`; `.cache/dev-cycle/t14/latest-session.json` señala la sesión. No regenerar ni consultar el mapa antes de valorar. Página con referencia Suno original y seis copias a nivel comparable por ganancia lineal; secciones de Suno sin sincronizar. Valorar ritmo, afinación y carácter de voz por par (A/B/empate/ninguna). **Calidad y ganador pendientes**: no elegir parámetros ni generar una canción completa por suposición. T-08–T-13 y M0 siguen abiertos. Journals ajenos preservados; sin candidatos nuevos de este tramo.


## T-15 completada técnicamente — escucha de naturalidad pendiente

El propietario ha valorado T-14: B/B/B, equivalentes a shift1 en dos pares y shift3 en uno; sigue faltando naturalidad de voces, ritmos e instrumentos. No hay ganador consistente ni calidad aprobada. Autoriza continuar la comparación de captions y revisar alternativas locales. Se mantiene modelo/letra/configuración fijos durante la prueba de prompts; la revisión primaria de candidatos está terminada; falta elegir y ejecutar la prueba de modelo. No volver a generar T-14. Rama m0/t-15-libre-prompt-ab, ledger T-15, privados data/inputs/libre/prompt-ab y data/eval/libre-prompt. El preflight de la ejecución registró 1.327 MiB y Ollama vacío en ambas tandas; límite ≤1.600 MiB respetado, sin reutilizar la excepción de T-14.


**Resultado T-15:** seis tomas nuevas de 90 s con solo caption variable, tres pares privados a ciegas, referencia original de Suno conservada. Revisión A+B intento 2 y QA técnico conformes; 14 manifiestos CLI y 6 derivados válidos. [Informe](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t15/report.md), [investigación de modelos y licencias](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t15/model-review.md). Sesión privada `data/eval/libre-prompt/01M46QBFERQBK6XCH2Z4QQP9B1/listen.html`; servidor local separado http://127.0.0.1:8767/listen.html (se conserva el anterior de T-14, sin recargar valoraciones). GPU pico 7891.26 MiB, sin spill; unload confirmado. No hay ganador ni calidad aprobada. No repetir estas seis tomas por un fallo de empaquetado: `--pack-session 01M46QBFERQBK6XCH2Z4QQP9B1` es recuperación solo CPU. Pesos/producto/contratos sin cambios; TDD/cobertura n/a.

Siguiente paso: recoger escucha de voces, instrumentos y ritmo, y elegir la prueba de modelo. SFT 2B/LM 0,6B primero y HeartMuLa 3B después son recomendaciones, aún sin benchmark local propio. SFT necesita pasos/CFG correctos, no basta cambiar checkpoint con los 8 pasos actuales. Incorporar candidatos conserva T-09/T-12/T-13, licencias/lock/conformidad y cap dinámico. M0 abierto con 10/16 tareas; no iniciar M1 ni ejecutar ritual de cierre.
