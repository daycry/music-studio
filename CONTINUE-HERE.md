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

M0 lleva **13/20 tareas completadas**; T-14–T-17 recogen continuaciones autorizadas por el propietario. T-07 está cerrada técnicamente; la siguiente fase es **Medición y elección (T-08–T-13)**. La calidad musical de «Libre» sigue sin aprobarse. El propietario ha elegido y escrito el perfil global de WSL: **16 GB de RAM, 8 GB de swap y `autoMemoryReclaim=dropCache`**. A petición suya se ejecutó `wsl --shutdown`, exit 0. Tras arrancar Ubuntu, `/proc/meminfo` mostró 16.375.452 kB totales (15,62 GiB utilizables) y `/proc/swaps` 8.388.608 KiB, sin uso; Docker volvió a responder. [ADR-0025](docs/decisiones/ADR-0025-limite-de-memoria-wsl.md) registra el cambio. La prueba de audio de 30 s se ejecutó con el límite anterior de 24 GB; la canción completa de T-07 verifica después el nuevo perfil sin uso de swap.

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

Prioridad actual: auditar y corregir fidelidad de prompts/tags antes de elegir la prueba de modelo (T-17). La preparación de SFT (T-16) vuelve a borrador. SFT 2B/LM 0,6B primero y HeartMuLa 3B después son recomendaciones, aún sin benchmark local propio. SFT necesita pasos/CFG correctos, no basta cambiar checkpoint con los 8 pasos actuales. Incorporar candidatos conserva T-09/T-12/T-13, licencias/lock/conformidad y cap dinámico. M0 abierto con 11/18 tareas; no iniciar M1 ni ejecutar ritual de cierre.


## Prioridad T-17 — fidelidad antes de cambiar modelos

La auditoría CPU ya mide el recorrido instalado hasta las fronteras del LM musical y del DiT, con inferencia sustituida por capturas y tokenizadores fijados. [Informe y recibos](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t17/audit-report.md): 16 casos, nueve de diez prompts originales rechazados por el límite local de 512 caracteres, cuatro superarían los 256 tokens de la plantilla DiT. Las adaptaciones actuales caben; la letra cantada de Libre conserva 72 líneas, pero varias indicaciones de sus nueve tags se habían simplificado. Candidato privado nuevo en data/inputs/libre/prompt-faithful, sin audio. No se han modificado modelos ni producto, ni repetido generaciones. T-17 completada técnicamente: revisión A+B intento 2 sin gaps y QA CPU/documental conforme. El estado vive en el ledger; controles de producto y calidad musical siguen pendientes.

Siguiente trabajo: controles de preparación, presupuestos de tokens y metadata/procedencia; no atribuir naturalidad al modelo antes de revisar esas entradas. Las ideas de los estudios enlazados se registran como propuestas compatibles. La aportación sobre clips independientes y modelos de vídeo queda contrastada para M4 en [video.md §9](docs/arquitectura/video.md); no adelanta ese hito. Conserva los journals ajenos de docs/knowledge/.


## Corrección en curso — T-18/T-19

El objetivo persistente es implementar el roadmap completo y elegir las mejores alternativas. T-18 implementa preparación determinista privada (original/efectivo, diff, hashes, limpieza opt-in de tags Markdown, metadata opcional y prepare-only offline). T-19 sigue con presupuesto nativo y metadata LM, antes de modelos nuevos o comparaciones. El ledger tiene 20 tareas; M0 sigue abierto con 12 completadas. Rama de trabajo m0/t-18-preparacion-prompts. No hay audio nuevo ni calidad aprobada. Journals ajenos preservados.

El perfil actual permite comandos locales sin solicitar escalación; las notas históricas sobre sandbox y prefijos Docker describen el perfil anterior. Las restricciones del proyecto sobre GPU, licencias, pesos y procesos permanecen vigentes.

## T-18 conforme — siguiente T-19

Preparación fiel implementada: original/efectivo privados, diff y hashes, tags Markdown opt-in, metadata opcional y prepare-only offline. [QA independiente](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t18/report.md): 185 tests declarados y 309 tests completos CPU verdes; cobertura añadida 93,60 %, mínimo por archivo 88,14 %. Probe 72 versos, nueve tags y 32 hashes preservados. Revisión 2 sin gaps, reutilización de contextos y fix principal por límite de threads declarados. Sin audio nuevo ni aprobación artística. La imagen T-14 aún no incorpora este código; T-19 verificará integración runtime y presupuestos nativos. El estado canónico y el cierre de integración viven en el ledger. Sigue T-19 antes de SFT y nuevas comparaciones.

## T-19 conforme — siguiente T-16

T-18 publicada en `83fc652`. T-19 integrada y publicada por fast-forward en main y su rama (`ef66a36`): [QA](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t19/report.md) independiente con 146 tests declarados y 381 completos verdes, cobertura añadida 92,84 % (mínimo 87,50 %), revisión A+B+C intento 2 fresca sin gaps. Presupuesto LM/DiT nativo, idioma/metadata y recibos planned/captured privados verificados; diez capturas válidas intactas y contradicciones rechazadas. Imagen reconstruida incorpora T-18/T-19, health idle descargado; los 133 tests CPU de imagen y 16 casos nativos son antecedentes de integración. No repetir builds/probes salvo cambios o fallos nuevos. Sin audio nuevo ni aprobación artística; sin nuevos pesos, herramientas, locks ni dependencias. PDF QA pendiente por herramientas ausentes; sin UI por diseño.

M0 sigue abierto con 13/20 tareas. Retomar T-16 con brief fresco y TDD: controles SFT50/CFG7 y perfiles/recibos coherentes, antes de las tres tomas comparativas. Mantener captions/letra de control y referencias anteriores; controles de GPU/Ollama/VRAM se comprueban antes de cualquier carga nueva. T-08–T-13 y los siguientes hitos siguen pendientes. Journals ajenos preservados; no se promueven ni se añaden a Git.

## T-16 retomada tras integrar T-19

Rama actual `m0/t-16-libre-sft`, actualizada por fast-forward a `ef66a36`. T-16 en-progreso: implementer fresco con TDD prepara controles y coherencia de perfiles/recibos SFT50/CFG7, sin pesos nuevos, instalaciones ni GPU en esta implementación. Root conserva documentación, ledger y posterior comparación. Antes de generar se comprobarán Ollama, VRAM libre y límites actuales; las tomas previas y valoraciones se preservan. M0 abierto con 13/20 completadas.

La comparación se corrige mediante [ADR-0027](docs/decisiones/ADR-0027-controles-de-inferencia-sft.md): seis nuevas tomas emparejadas (tres Turbo y tres SFT). El idioma LM llega ahora como metadata; los Turbo antiguos no recibían ese campo y quedan como referencia histórica separada. No se sustituye la escucha ni se sobrescribe ninguna toma; consumo adicional aún sin medir. Parte CPU del brief original sin cambios, ajuste GPU notificado al implementer.

## T-16 — puerta CPU conforme; comparación GPU pendiente

Implementación y revisión fresca A+B conformes; C/D=false por selector. [QA CPU independiente](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t16/cpu-qa-report.md): 41 pruebas declaradas y430 completas verdes, cinco skips/una excluida/seis avisos, cobertura añadida93,65 % y mínimo86,36 %. Trece recibos intactos, siete contradicciones rechazadas,32 hashes históricos preservados. Imagen nueva `music-studio/engine-acestep:m0-t16-controls` ID9e4fc86:156 pruebas CPU y19 casos nativos previos; HTTP aislado Turbo/SFT con CpuGpu sintético conforme. Servicio8101 conserva imagen anterior13326c0, idle/descargado. No repetir suites/builds/probes sin cambios o fallo nuevo.

CA1/2 acreditados, CA3/4 y T-16 aún en-progreso; M0 sigue13/20, sin ganador ni aprobación artística. Comparación preparada con control T-15 idéntico y siete pesos locales verificados, sin descargas. Runner privado `.cache/dev-cycle/t16/run-comparison.py --prepare-only` conforme CPU; completar revisión de guardas/paquete de escucha antes de generar. Registros del arnés y datos privados no se publican como evidencia de GPU.

Consulta de GPU pendiente: última lectura Ollama vacío y2706MiB ocupados (9238libres de12227total). AGENTS§4.8 exige≤1600MiB; se ha solicitado liberar GPU o excepción expresa para estas seis nuevas tomas, cap libre−512MiB y parada conservadora. Esperar respuesta o baseline conforme; no reinterpretar autorizaciones T-14/30s como permiso de esta comparación. No cargar modelo mientras falta esa condición. Objetivo completo vigente; T-08–T-13 y M1–M5 siguen pendientes. Journals ajenos intactos.

## T-16 — arnés corregido y QA CPU conforme

Revisión fresca del arnés detectó cuatro Important: cleanup omitido ante timeouts, copia parcial de referencia irrecuperable, math ausente y stop indirecto de job ajeno. Root corrigió la orquestación privada con siete regresiones rojas previas; ampliación final12verdes. Segunda revisión A+B fresca y [QA independiente](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t16/harness-qa-report.md) conformes:12passed/sinavisos, fuentes/históricos y seis fuentes de producto intactos. Snapshot, SHA y límites en recibos públicos separados; no sobrescribir guards/packer anteriores para aparentar nueva evidencia. No volver a ejecutar los scripts one-shot record/verify sin destinos nuevos.

Runner/packer actuales en .cache/dev-cycle/t16, ya revisados CPU: label e imagen propias, cleanup por ID ante fallos, diferido si aparece job ajeno, referencia publicada atómicamente sin sustituir destinos, math presente. La descarga/limpieza Docker real y fullpack siguen sin verificar; no hay seis audios nuevos ni calidad aprobada. Imagen producto existente9e4fc86 y servicio anterior8101 no modificados; no rebuild/suite430 sin motivo nuevo. T-16 sigue en-progreso, CA3/4 abiertas; entrega en rama m0/t-16-libre-sft, sin FF a main.

Lectura GPU posterior: Ollama vacío,2676MiB usados/9268libres de12227. La consulta específica sigue pendiente; el runner todavía exige1600 y NO admite excepción automática. Si llega autorización, registrar alcance y condición aparte sin modificar el plan inmutable ni reutilizar permisos anteriores; revisar cualquier cambio del arnés antes de GPU. No volver a preguntar por lo ya pendiente.

Mientras tanto se comprobaron prerrequisitos CPU de T-08 en .cache/dev-cycle/t08/prerequisitos-2026-10-06.md: los cinco modelos auxiliares locales pasan fetch_models --check, sin descarga; manifiesto Docker base2.14cuda13 existe. Qwen requiere separar ASR/alineación para obtener tiempos sin dos modelos residentes; beat_this convertido no conserva hyper_parameters/config.json; CLAP local tiene arquitectura HFClapModel, preferible investigar loader local a defaults del hook remoto. Son hallazgos previos, no implementación ni decisiones de producto. T-08 aún borrador; preparar rama/brief fresco TDD con deps/contrato/licencias seguros. No adelantar M1–M5 ni cerrar el objetivo completo.
