---
design: t09-benchmark-5070
titulo: "Diseño de implementación del benchmark T-09 existente"
estado: aprobado
creado: "2026-10-06"
actualizado: "2026-10-06"
spec: ../../spec.md
evaluacion: n/a
plan: ../../improvement-plan.md
adr: ../../../../decisiones/ADR-0033-perfiles-y-medicion-directa-del-benchmark.md
opcion_elegida: O1
validada: "2026-10-06; elegida O1 por root bajo autorización vigente del propietario"
generacion:
  fuente: estimado
  ventana: lote-combinado-root
  tokens: null
  coste: null
  horas_ia: null
---

# Diseño — cómo medir T-09 en la RTX 5070

Este documento privado desarrolla T-09 del M0 aprobado. No crea una iniciativa, un ledger ni una elección musical.
Root eligió O1 el 2026-10-06 conforme a la autorización vigente del propietario para elegir las mejores decisiones.

| Campo | Valor |
|---|---|
| Estado | aprobado por root bajo autorización del propietario |
| Recomendación | O1 — harness aislado sobre `/v1`, perfiles explícitos y telemetría aditiva |
| Opción elegida | O1 |
| Evidencia producida | diseño, fuentes oficiales fijadas, SHA y recibo; ninguna medición GPU |

## 1. Contexto y restricciones

El brief íntegro e inmutable es `task-brief.md`. La preparación es `testing/t09/preparation-report.md` y `.cache/dev-cycle/t09/preparation/research.md`.
La investigación anterior distingue pesos disponibles de soporte runtime. Se reutiliza su inventario sin hashear pesos grandes otra vez.

La factoría `apps/engines/acestep/engine_acestep.py` selecciona checkpoint y LM por entorno. Descriptor, adapter y preflight comparten esos valores.
`scripts/generate.py` selecciona BF16 y no ofrece checkpoint, LM o modo. Su tiempo incluye preparación y publicación.
`apps/engines/common/engine_common/server.py` mide `run_s` desde antes de cargar. Restar `load_s` no acredita inferencia medida.
`packages/engine-contract/engine_contract/__init__.py` ya contiene `Telemetry.rtf`, `Telemetry.extra`, modos libres y `DoneData.result` opcional.

Base y XL reciben hoy la identidad Turbo. `input_profile.inference_controls` solamente distingue `sft=True/False`.
El soporte de INT8 todavía no se expone. El upstream fijado sí tiene una implementación oficial y dependencia bloqueada.
XL está fijado en `models/models.lock.json`, pero falta en disco. Su disponibilidad sigue siendo prerrequisito de ejecución.

La matriz obligatoria mantiene cinco configuraciones y cuatro duraciones. T-16 y sus tomas no son evidencia de T-09.
Los pesos, audio, entradas y recibos permanecen privados dentro del repositorio. No se publican letras ni materiales de Suno o Libre.

Antes de GPU, root vuelve a comprobar T-16, otras cargas, Ollama y baseline. Este agente no ejecuta Docker, GPU, modelos, instalación ni audio.
No se leyó `docs/knowledge/`, memoria ni MCP de conocimiento. No se abre otra ventana de consumo.

## 2. Opciones

### O1 — medir el producto mediante `/v1` en contenedores propios

Un harness local crea un contenedor aislado para cada identidad/LM/almacenamiento. Usa estimación, jobs, eventos y unload del contrato vigente.
El adapter aporta un reloj directo y sus opciones efectivas. Windows aporta un colector independiente de memoria compartida.
Los perfiles nuevos entran de forma explícita, conservando Turbo/SFT y recibos v2. La CLI musical general queda intacta.

| Criterio | Valoración |
|---|---|
| Complejidad | Media-alta: integrar perfiles, modo INT8, observadores y recuperación de sesiones |
| Riesgo | Cambios compartidos de adapter; se integran después del freeze T-16 y se verifican con sus regresiones |
| Coste relativo | M: reutiliza protocolo, preflight, verificación de pesos, hijo y eventos |
| Reversibilidad | Alta: contenedores propios, flags explícitos y módulos nuevos; se conserva el default Turbo/BF16 |

### O2 — medir upstream directamente con worker de benchmark independiente

Un worker privado llama al código upstream fijado, sin pasar por `/v1`. Implementa sus propios perfiles, tiempos y recibos.
El harness ejecuta ese worker en contenedores propios y mantiene la misma observación Windows y comparación de almacenamiento.
Sirve para caracterizar el proveedor, pero exige después repetir conformidad de los perfiles en el engine del producto.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: worker independiente, más validación duplicada de entrada, pesos, cap y cancelación |
| Riesgo | Alto: cuantización, offload o entrada pueden diferir del adapter que usará el estudio |
| Coste relativo | L: duplicación de validadores y repetición posterior para recomendar defaults del producto |
| Reversibilidad | Alta: artefactos aislados; retirar el worker no altera la API |

### O3 — ampliar la CLI musical y medir el flujo publicado completo

`scripts/generate.py` incorpora selectores explícitos de modelo, LM y modo. El benchmark consume esa CLI y publica takes/manifiestos.
Necesita igualmente el reloj del adapter: el tiempo de CLI representa experiencia total y no sustituye la inferencia.
La ampliación obliga a actualizar preparación, recibos, linaje y publicación de todos los perfiles.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: mayor superficie CLI/server/publicación y pruebas de compatibilidad |
| Riesgo | Alto: acopla T-09 a flujos musicales y a archivos compartidos de T-16 |
| Coste relativo | L: amplía producto para una medición que `/v1` ya permite ejecutar |
| Reversibilidad | Media: retirar flags exige conservar compatibilidad de preparaciones y manifiestos emitidos |

## 3. Criterios de decisión

1. Medir el mismo adapter, preflight y contrato que utilizará el producto.
2. Conservar toda la matriz y medir relojes directamente, con evidencia inmutable.
3. Distinguir memoria compartida Windows, VRAM CUDA/NVML, RAM WSL y offload voluntario.
4. Garantizar identidad propia de base/XL y comprobar que INT8 quedó realmente aplicado.
5. Aislar ejecución, almacenamiento y recuperación sin tocar cargas ajenas o T-16.
6. Mantener `/v1` y manifiesto v1 compatibles; cambios opcionales y exportación code-first si corresponde.
7. Recomendar rendimiento solamente con filas reales. La calidad artística y el cierre de M0 pertenecen a otras tareas.

## 4. Recomendación, elección y alcance de la decisión

**Recomendada: O1.** Usa las interfaces vigentes y evita reproducir un engine alternativo.
El coste principal es resolver soporte real de perfiles, tiempos y observación. Las tres opciones necesitan esos controles.

**Elección: O1, validada por root el 2026-10-06.** O2 pierde equivalencia con el producto; O3 amplía publicación y CLI sin necesidad para T-09.
Root registrará ADR-0033 y pasará un brief íntegro al implementer. Conserva `Telemetry.extra` y copia efímera en el contenedor propio.

La decisión supera el umbral de ADR: afecta perfiles, adapter, server común y benchmark.
Root redactará un ADR en `docs/decisiones/` con alternativas descartadas y actualizará documentos afectados.
El número depende del índice vigente que root gestione; este agente no reserva un número ni consulta conocimiento.

ADR propuesto: «Perfiles explícitos y medición directa para el benchmark local M0».
Define IDs base/XL, matriz, modos, relojes, evidencia y política de spill. No cambia principios de la constitución.
Un segundo ADR depende del resultado: diferencia bind/copia superior a 30 s, con condiciones, delta, dispersión y costes de copia.
No se anticipa ese resultado ni se decide migrar pesos por una hipótesis.

## 5. Impacto, interfaces y secuencia de integración

### 5.1 Rutas concretas

| Ruta | Cambio previsto en O1 | Estado / coordinación |
|---|---|---|
| `scripts/eval/benchmark.py` | CLI obligatoria y orquestación de sesiones; sin importación de torch | Nuevo; ruta canónica T-09 |
| `scripts/eval/benchmark_plan.py` | Matriz, configuración y plan determinista privado | Nuevo propuesto |
| `scripts/eval/benchmark_evidence.py` | Validación de hashes, recibos, eventos, estado y reporte | Nuevo propuesto |
| `scripts/eval/benchmark_runtime.py` | API, Docker aislado, brazos de almacenamiento y cleanup propio | Nuevo propuesto |
| `scripts/eval/benchmark_observers.py` | NVML externo, WSL RAM/swap y observación Windows | Nuevo propuesto |
| `scripts/eval/windows_gpu_memory.ps1` | Contadores WDDM agregados y estado visible del navegador | Nuevo propuesto |
| `scripts/eval/tests/test_benchmark_*.py` | TDD de matriz, relojes, sensores, reanudación, informe y ownership | Nuevos propuestos |
| `apps/engines/acestep/benchmark_profiles.py` | Registro estricto de checkpoint, identidad, defaults y modos | Nuevo propuesto; mantiene wrapper de APIs previas |
| `apps/engines/acestep/engine_acestep.py` | Propagar `resource_root` explícito a descriptor/adapter/preflight | Modificación aditiva; raíz actual por defecto |
| `apps/engines/acestep/descriptor.py` | Resolver perfiles sin alias; modos INT8 explícitos | Modificado después del freeze compartido |
| `apps/engines/acestep/input_profile.py` | Controles por perfil, nuevos SHA upstream necesarios | Modificado después del freeze; conservar interfaz `sft=` compatible |
| `apps/engines/acestep/adapter.py` | Registro por perfil, load efectivo, reloj sincronizado, resultado aditivo | Modificado después del freeze; ningún parche informal en sesión viva |
| `apps/engines/acestep/preflight.py` | Comprobar identidad/config y propagar perfil/LM/modo opcionales | Modificado después del freeze; recibos v2 históricos intactos |
| `apps/engines/acestep/patches.py` | Añadir verificaciones SHA de rutas INT8 oficiales si necesitan helper | Cambio mínimo; preservar parche safetensors auditado |
| `apps/engines/common/engine_common/server.py` | Propagar reloj a `rtf` y `extra`; no reinterpretar `run_s` | Modificado después del freeze |
| `apps/engines/common/engine_common/runtime.py` | Solo si se necesita propagar datos de guardas; cap y heurística vigentes | Evitar cambio si harness puede hacerlo; añadir pruebas si cambia |
| `apps/engines/common/engine_common/worker.py` | IPC ya transporta `result`; no requiere cambio de esquema por principio | Reutilizado |
| `packages/engine-contract/engine_contract/__init__.py` | Tipos `InferenceTiming` opcionales únicamente si root decide tiparlos | Reutilizar `extra` primero; ninguna obligación nueva |
| `packages/contracts/engine-v1.json` | Regenerar solo si cambia schema code-first | Reutilizado o aditivo; ejecutar exportación `--check` |
| `apps/server/app/__init__.py` | No necesario para orquestar benchmark crudo | Sin cambio en O1 |
| `scripts/generate.py` | Reusar validadores puros; no medir por tiempo de CLI ni cambiar flags | Sin modificación en O1 |
| `models/models.lock.json` | Misma revisión/hash; verificar XL antes de ejecutar | No reescribir por benchmark |
| `scripts/fetch_models.py` | Ruta existente de preparación separada del runtime | Reutilizado |
| `apps/engines/acestep/Dockerfile`, `apps/engines/acestep/uv.lock` | Verificar upstream torchao bloqueado en imagen nueva; no actualizar por suposición | Evitar cambio si build congelado ya resuelve dependencia |
| `docker-compose.yml` | No requerido: contenedores de sesión independientes | Sin modificación |
| `eval/results/benchmark-5070.md` | Reporte público redactado, sin entradas privadas | Nuevo; publicación final del harness |
| `docs/decisiones/`, `docs/arquitectura/contrato-engines.md`, `docs/arquitectura/modelos.md`, `docs/legal/licencias.md` | ADR, semántica de tiempos/perfiles y fila torchao | Solo root; propuesta, no escritura por este agente |

El server de M1 sigue como esqueleto. En M0 `scripts/generate.py` hace sus funciones de publicación.
O1 evita modificar ambos: produce salida cruda y evidencia del benchmark, sin crear takes ni escribir en la BD.

### 5.2 Matriz completa y perfiles

Cada fila cruza **30, 60, 180 y 300 s**, semilla 1, `n_outputs=1`, lote 1 y backend LM PT.
La entrada nueva tiene autoría declarada, hash y presupuestos nativos válidos para 300 s. No reutiliza tokens/audio de comparaciones históricas.
Si las cuatro duraciones requieren letras diferentes, se fijan cuatro fixtures antes de correr. Cada duración usa idéntico fixture entre candidatos y brazos.

| `config_id` | `model_id` | Checkpoint / LM | Default de pasos y CFG | Modo primario |
|---|---|---|---|---|
| `turbo-lm06` | `ace-step-1.5-turbo` | `acestep-v15-turbo` / `acestep-5Hz-lm-0.6B` | 8; CFG DiT no expuesto | `bf16` |
| `turbo-lm17` | `ace-step-1.5-turbo` | `acestep-v15-turbo` / `acestep-5Hz-lm-1.7B` | 8; CFG DiT no expuesto | `bf16` |
| `sft-lm06` | `ace-step-1.5-sft` | `acestep-v15-sft` / `acestep-5Hz-lm-0.6B` | 50 / 7 | `bf16` |
| `base-lm06` | `ace-step-1.5-base` | `acestep-v15-base` / `acestep-5Hz-lm-0.6B` | 32 / 7 | `bf16` |
| `xl-turbo-lm06-int8` | `ace-step-1.5-xl-turbo` | `acestep-v15-xl-turbo` / `acestep-5Hz-lm-0.6B` | 8; CFG DiT no expuesto | `offload-int8` |

Base y SFT aceptan pasos1–200 y CFG1–20. Turbo/XL conservan el límite operativo1–8 actual; no se amplía a20 por la UI upstream.
El registro usa coincidencia exacta de checkpoint; un desconocido devuelve `MODEL_NOT_FOUND`, nunca Turbo.
Los dos Turbo tienen el mismo DiT, pero `config_id`, revisiónLM y huella de ejecución los separan inequívocamente.

`shift=1`, CFG LM2, `thinking=true`, metadatos explícitos, CoT caption/language/metas desactivados y contexto LM4096 son políticas del benchmark.
No se etiquetan como defaults oficiales. La UI upstream fijada utiliza shift3 y desactiva inicioLM automático para base puro.
Aquí base utiliza LM0.6 explícito para conservar comparabilidad. El recibo registra ese override y la rama nativa real de DiT.
El modo base sin LM puede estudiarse después, como experimento adicional; no sustituye una de las20 filas.

Fuente de pasos: `acestep/ui/gradio/events/generation/model_config.py` fijado, base32/SFT50/Turbo8.
CFG7 procede de `GenerationParams` de `inference.py` ya fijado por `SOURCE_HASHES`.
XL-turbo obtiene default8 por su perfil turbo oficial, pero conserva su ID y configuración XL propia.

Todos los perfiles conservan `verified=false` hasta su conformidad. Un benchmark exitoso no valida automáticamente todas las capacidades.
No se rebautiza un peso como otro ni se concede calidad por default.

### 5.3 INT8: implementación factible y prueba de aplicación

El Dockerfile fija ACE-Step `dce621408bee8c31b4fcf4811682eb9359e1bc94` y `uv sync --frozen`.
El lock oficial fija Linux x86_64 `torch==2.10.0+cu128` y `torchao==0.16.0`.
El wheel Linux torchao tiene SHA `2d6293a0c57c9dd505efb025a7189459d154965fbed000efd638cf299f9362dd`.
Esto describe dependencias previstas; no acredita su importación efectiva en la imagen futura. [Lock oficial fijado](https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/dce621408bee8c31b4fcf4811682eb9359e1bc94/uv.lock).

Modo nuevo `offload-int8`: BF16 de activaciones, PT/SDPA, compilefalse, offloadCPU y offloadDiTCPU true, `quantization="int8_weight_only"`.
LM permanece BF16/PT con offload. No se anuncia un LM INT8 ni activaciones INT8.
La implementación oficial aplica `Int8WeightOnlyConfig` mediante `quantize_` a lineales del decoder DiT; excluye tokenizer/detokenizer.
Se aprovecha ese código fijado, sin bitsandbytes ni cuantización propia. [Loader oficial fijado](https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/dce621408bee8c31b4fcf4811682eb9359e1bc94/acestep/core/generation/handler/init_service_loader.py).

La carga verifica safetensors/remote_code contra el lock. `install_safe_loader()` sigue sustituyendo exclusivamente `silence_latent.pt` por safetensors.
No guarda tensors cuantizados serializados ni introduce `torch.load` o pickle. La cuantización sucede en memoria sobre pesos seguros verificados.

El upstream puede degradar a `quantization=None` cuando falla torchao. El adapter rechaza esa degradación para `offload-int8`.
Después de carga exige `runtime.dit.quantization == "int8_weight_only"`, versiones esperadas y conteo positivo de lineales efectivamente cuantizadas.
La comprobación usa tipos torchao de la versión fijada y guarda clase/layout/conteo, nunca contenidos de tensors.
Además, la prueba real verifica transferenciaCPU↔CUDA, forward y retornoCPU en sm_120 bajo cap; un import exitoso no basta.
[Orquestador oficial fijado](https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/dce621408bee8c31b4fcf4811682eb9359e1bc94/acestep/core/generation/handler/init_service_orchestrator.py).

CPU offload ya tiene tratamiento upstream para `AffineQuantizedTensor`. Ese soporte es teórico hasta probar la combinación concreta en5070.
No se corrige una incompatibilidad cambiando flags silenciosamente. Se guarda error tipado y opción efectiva, manteniendo fila pendiente o no factible.
[Transferencia oficial fijada](https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/dce621408bee8c31b4fcf4811682eb9359e1bc94/acestep/core/generation/handler/init_service_memory_transfer.py).

XL faltante se prepara fuera del runtime: `uv run scripts/fetch_models.py --model ace-step-1.5 --include-optional`, después `--check` con el mismo selector.
Root comprueba espacio para shards, caché de descarga y copia del conjunto seleccionado antes de descargar. Todo queda bajo el proyecto.
El benchmark nunca descarga y conserva `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1` y revisión/source SHA en la imagen.
No marca «no cabe» porque falten pesos: `missing_weights` implica ejecución incompleta y salida distinta de0.
«Si cabe» admite `hardware_not_feasible` solamente con prueba real fallida bajo cap o incompatibilidad runtime documentada de INT8/offload.
Las cuatro filas XL permanecen explícitas con motivo y evidencia. No se sustituye XL por un Turbo pequeño ni se reduce duración.

### 5.4 Interfaces privadas tipadas

Los siguientes tipos usan JSON con nombres ingleses. Son interfaces de diseño, no código implementado.

| Tipo | Campos y validación |
|---|---|
| `CheckpointProfile` | `checkpoint:str`, `model_id:str`, `family_variant:Literal[turbo,sft,base,xl_turbo]`, `default_steps:int`, `max_steps:int`, `cfg_supported:bool`, `default_cfg:float`, `modes:tuple[str,...]`; lookup exacto |
| `BenchmarkPlan` | `schema_version=1`, `session_id:ULID`, `matrix="default"`, `durations_s:[30,60,180,300]`, `configs:list[BenchmarkConfig]`, `fixtures_by_duration`, `source_hashes`, `lock_sha256`, `image_id`, `seed:int`, `repeat_policy`, `observer_policy`, `timeouts`, `plan_sha256` |
| `BenchmarkConfig` | `config_id`, `model_id`, `checkpoint`, `lm`, `mode`, `params`, `storage:Literal[bind,container_copy]`, revisiones/hash seleccionados; sin alias |
| `RunKey` | `config_id`, `duration_s`, `storage`, `phase:Literal[process_cold,warm]`, `repetition:int`; `run_id` y `job_id` nuevos |
| `InferenceTiming` | `version=1`, `clock="perf_counter_ns_cuda_synchronized"`, `infer_start_ns:int`, `infer_end_ns:int`, `inference_s:float`, `audio_duration_s:float`, `rtf:float`, `scope`, `cuda_sync:bool`; fin≥inicio, cifras finitas |
| `RuntimeEffective` | `checkpoint`, `lm`, revisiones, `mode`, `dtype`, `lm_backend`, `attention_backend`, `quantization_requested`, `quantization_effective`, `quantized_linear_count`, `compile_effective`, offloads, `profile_sha256` |
| `ObservationSample` | `seq:int`, `ts_utc`, `host_monotonic_ns`, `sensor`, `gpu_identity`, valor/unidad, `status`, `run_id?`; gaps explícitos, nunca rellenados con0 |
| `RunReceipt` | `run_key`, `job_id`, `request_sha256`, `planned/captured` refs, `effective`, `timing`, `load_s`, `run_s`, `copy_s`, `verification_s`, `http_s`, `postprocess_s`, `unload_s`, VRAM/cap, `spilled_engine`, `spill_assessment`, hashes de eventos/WAV/sensores y terminal |
| `SpillAssessment` | `engine_heuristic:bool?`, `rtf_ratio:float?`, `reference_run_ids:list`, `shared_gpu_observed:bool?`, `shared_gpu_delta_mb:float?`, `sensor_coverage`, `verdict:Literal[observed_possible_spill,no_indicator_observed,unknown]`, motivos |
| `SessionReceipt` | identidad/owner, plan/image/code/lock/fixtures SHA, archivos/hash/tamaño, estados de cada RunKey, cleanup/restauración Ollama, completitud y `report_sha256` |

No se añaden campos obligatorios a `JobRequest`, `LoadRequest`, eventos ni manifiestos.
El adapter devuelve `inference_timing` y `runtime_effective` dentro de `result`, junto a `input_receipts` existentes.
El worker ya transmite el resultado. El server propaga `rtf` y `extra.inference_timing`/`extra.runtime_effective` sin modificar `run_s`.
Si se tipa `inference_s` en `Telemetry`, será opcional `float|None`, defaultnull; schema regenerado en el mismo cambio.
No se reescribe un manifiesto v1 emitido. Los metadatos nuevos quedan en evidencia privada y campo opcional si se publican después.

No se añaden hashes de dependencia a `SOURCE_HASHES` indiscriminadamente. Se incluyen solo fuentes que controlen el perfil y nuevas rutas INT8 ejecutadas.
Los controles base/XL y sus fuentes forman una huella nueva explícita. Recibos previos v1/v2 conservan su propia huella y validación histórica.

### 5.5 Relojes directamente medidos

La inferencia abarca `runtime.generate_music`: LM, DiT, VAE y transferencias del modo elegido. Excluye preflight y escrituraWAV.
El adapter ejecuta `torch.cuda.synchronize()` justo antes de `perf_counter_ns()` inicial y antes del reloj final.
El segundo reloj se toma después de la sincronización final. Se registra su método; el cronómetro vive en el hijo.
No se deriva `inference_s` restando tiempos. Si la generación falla, guarda intervalo fallido con estado, sin producir RTF exitoso.

| Métrica | Frontera y lugar |
|---|---|
| `copy_s` | copiaCPU de componentes seleccionados al almacenamiento interior; solo brazo copia |
| `verification_s` | verificaciónSHA separada antes de medir y dentro de carga auditada cuando aplica |
| `load_s` | reloj real `ProcessSupervisor.load_s`: creación/importación del hijo y carga verificada; misma semántica en ambos brazos |
| `inference_s` | relojes directos sincronizados alrededor de llamada upstream; incluye offload propio del modo |
| `audio_duration_s` | número real de framesWAV/sample_rate; validar duración frente a la solicitada |
| `rtf` | `inference_s/audio_duration_s`; más bajo es más rápido; no audio_s/inference_s |
| `run_s` | duración job ya vigente, carga incluida; permanece con ese nombre/semántica |
| `request_wall_s` | harness: envíoAPI a terminal; red/eventos/control, distinto de inferencia |
| `write_audio_s` | escritura y hashWAV en adapter después de inferencia; opcional directamente medido |
| `postprocess_s` | fuera de medición primaria; O1 no publica takes, por tanto null/noejecutado |
| `unload_s` | solicitud a confirmaciónhijo terminado/healthidle; solo dueño |

Cada celda tiene un job `process_cold` que arranca desde unload y mide carga+inferencia separadas.
Después ejecuta tres jobswarm nuevos con el mismo modelo residente, sin reutilizar audio/códigosLM ni terminales anteriores.
El plan completo tiene20 celdas × 2 brazos × 4 ejecuciones=160 jobs, salvo fallos reales acreditados o XL no factible condicionado.
Las inferencias cold se informan separadas: calentamiento CUDA/kernel afecta su rendimiento.
`load_s=0` en warm indica ninguna carga del job, no «carga instantánea».

### 5.6 Bind frente a copia interior equivalente

Ambos brazos usan la misma imagen por ID, código, revisión, dtype, modo, cap, variables, límites CPU/RAM y componentes por SHA.
Bind monta `models` RO en `/models`. Copia usa el filesystem del contenedor propio efímero, en `/studio/.cache/benchmark/<session>/models`.
Este almacenamiento Docker ya está autorizado para engines. No crea volúmenes persistentes ni migra el data-root global compartido.
La caché vive en el espacio lógico del proyecto dentro del guest. Desaparece al retirar exclusivamente ese contenedor por ID y labels.
Los pesos y fuentes permanentes siguen en `models/` del repositorio. Una segunda carpeta Windows bind no es una copia interior válida.
El layout conserva `models.lock.json`, `ace-step-1.5/checkpoints` y componentes con hashes idénticos.
Se parametriza explícitamente `resource_root` desde la factoría hacia descriptor, adapter y preflight; ninguno puede seguir leyendo el bind por accidente.
Para copia, `resource_root` es la raíz guest anterior; para bind, `/models`. El recibo guarda la ruta efectiva y su almacenamiento.

La preparación CPU del contenedor copia solo checkpoint, LM, VAE, embedding y lock desde un bind de origen RO. No crea contexto CUDA.
Conserva layout y metadata necesarias. Verifica bytes contra el lock en origen/destino y genera un recibo; las mismas verificaciones se aplican al bind.
El runtime posterior vuelve a verificar los componentes como siempre. No se elimina la comprobación de un brazo para acelerarlo.
La copia inicial se mide una vez por conjunto; se informa coste único y amortización descriptiva por carga, sin mezclarlo con `load_s`.

Se alterna orden AB/BA determinista por duración/config para minimizar sesgo. Cada cold job usa hijo nuevo.
No se vacía caché global, reinicia WSL o modifica T16. `process_cold` no significa caché de disco fría.
Se declara `filesystem_cache="uncontrolled"` salvo prueba de control local válida. Warmreload puede medir efecto observado de caché por brazo.
Si se añade warm reload, unload/load equivalentes y coste separado: no reemplaza los tres warm jobs de inferencia.

El reporte calcula `load_bind_s-load_copy_s`, absoluto, por parejas bajo condiciones comparables.
Si cualquiera supera 30 s, root abre ADR con evidencia y límites; no se migra automáticamente todo `models/`.
Un delta contaminado por recursos distintos o datos faltantes es inconcluso y exige repetir la pareja, preservando la tentativa inicial.

### 5.7 Windows sharedGPU, RAM WSL y referencia RTF

El colectorWindows obtiene memoria agregada del adaptador con contadoresWDDM, no sumando procesos.
Descubre nombres localizados con `Get-Counter -ListSet` y registra ruta resuelta, instancia LUID, driver y GPU física.
La rutaEnglish candidata es `GPU Adapter Memory(*)/Shared Usage`, junto a `Dedicated Usage`; se valida contra el adaptador5070.
Muestrea cada 1 s antes de cargar, durante carga/generación y después de unload. Conserva timestamps, statusPDH y muestrascrudas.
Los nombres localizados y las restricciones ACL están documentados por [Get-Counter](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.diagnostics/get-counter?view=powershell-7.5).

Root conservó `.cache/dev-cycle/t09/windows-counter-probe.json`, observado el 2026-10-06T04:58:24.2239114Z.
Sus 46 muestras con status 0 acreditan disponibilidad del proveedor, sin modelo cargado. Aparecen dos instancias de adaptador.
No se asigna ninguna instancia a la 5070 por consumo, nombre `phys_0`, suma decontadores o coincidencia aproximada deVRAM.
El helper deberá enumerar adapters DXGI y obtener Description, VendorId, DeviceId y AdapterLuid. Unirá LUID exacto con la instancia PDH.
La implementación preferida usa `ctypes` de la biblioteca estándar: `CreateDXGIFactory1`, `EnumAdapters1` y `GetDesc1`.
Registra también DedicatedVideoMemory y usa la pareja de32bits del AdapterLuid, sin instalar herramientas ni operar UI nativa.
Si solo existe un adaptador RTX/NVIDIA inequívoco, puede asociarlo explícitamente con la5070/NVML; varias coincidencias rechazan el mapeo.
La identificación5070 exige descripción/vendor y correlación con inventario físicoGPU; si existe ambigüedad queda `gpu_mapping_status=unresolved`.
Como fallback verificable, root registra la pestaña Rendimiento seleccionando explícitamente RTX 5070 y correlación temporal; no renombra el contador ambiguo.
El sensor agregado tiene ámbitoRTX 5070, no propiedad exclusiva del job. La atribución WSL/container a PID Windows puede ser desconocida.
Registrar PID contenedor/hijo, proceso WSL y PIDs Windows identificables permite correlación, sin inventar equivalencia uno-a-uno ni sumarGPU Process Memory.

ADR-0036 añade la acreditación automática `wddm_auto_v1` como alternativa explícita al contraste manual `task_manager_v1`. El [diseño autónomo aprobado](autonomous-observability-design.md) fija identidad, estados, unidades, timestamps/frescura, piloto baseline/carga/unload y confianza shared limitada antes de nueva GPU.
El contraste dedicado NVML no calibra shared Windows de forma independiente. Las capturas/lecturas previas se conservan con su discrepancia y límites; no se exige nueva intervención del propietario ni se inventa una captura o simultaneidad. Un método inválido produce diagnóstico parcial.
La pestaña Rendimiento muestra memoria compartida agregada; por proceso pueden existir duplicaciones y valores incorrectos.
[Semántica Microsoft](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/), [limitación documentada de contadores por proceso](https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/gpu-process-memory-counters-report-wrong-value).

NVML registra VRAMtotal/free/usada agregada y CUDA registra picoalloc/reserved del hijo. Ninguno mide sharedGPU Windows.
WSL aporta `MemAvailable`, `SwapTotal`, `SwapFree` y RSS del proceso propio si observable. Son campos separados con ámbito/distro.
NVML tiene consultas limitadas enWSL; guardar errores y camposnull resulta obligatorio.
[GuíaNVIDIAWSL](https://docs.nvidia.com/cuda/wsl-user-guide/index.html).

El navegador permanece abierto durante todo el benchmark, con una ventana visible deChrome/Edge/Firefox identificada porPID/HWND y capturainicial.
No se termina, minimiza ni cambia su contenido. Se registra heartbeat durante el lote, baseline GPU con ese navegador y pérdida deobservabilidad.
Un proceso sin ventana no acredita por sí solo el criterio. Si desaparece la ventana, la celda queda invalidada y no alimenta recomendación.

El plan fija el ruido de sharedGPU debaseline: 10 muestras antes de cargar; tolerancia=max(32MiB,3×desviaciónbaseline), declarada como criterio experimental.
`shared_gpu_observed=true` significa aumento agregado sostenido en dos muestras sobrebaseline+tolerancia, no prueba causal de spill exclusivo del hijo.
Offload puede aumentar memoria host/pinned legítimamente. Se informa separado y no se concluye que todo aumento constituye desbordamiento accidental.

`reference_rtf` es mediana de tres warm runs nuevos de la MISMAconfiguración/duración/modo/brazo/entrada y condicionesCPU/GPU.
Solo participan referencias con sensores válidos, cap cumplido, ventana abierta y sin aumento sharedGPU detectado bajo el criterio declarado.
Los tres IDs y susRTF quedan en el recibo. No se usa referenciaTurbo parabase, ni30s para300s, ni un número oficialteórico.
Si faltan tres referencias elegibles, `reference_rtf=null`, `rtf_ratio=null` y veredictodesconocido; jamás se fuerza referencia0.
El harness compara los runs elegibles/inferencias cold explícitamente con esa referenciawarm y anota que cold incluye calentamiento.
Un ratio>1.5 indica caída de rendimiento compatible con spill; no demuestra causalidad. No mezcla comparación de carga conRTF.

`spilled_engine` conserva la heurísticaactual95%cap. El informe añade sharedobservado,ratio y `spill_assessment` ternario.
`spilled=false` o ausencia de datosNVML nunca se traduce en sharedGPUcero. Todos los ámbitos y gaps permanecen visibles.
Si el collector agregado es inaccesible, esa ejecución es parcial; reporte de diagnóstico sí, recomendación completa deT09 no.

### 5.8 Preflight, recursos, ownership y recuperación

Antes del lote root comprueba estado actual de T16/T08 y de 8101. Ninguna inferencia concurrente es admisible.
Un lock deGPU propio delrepositorio coordina sesiones; un lock ya existente no se fuerza ni se borra por antigüedad sin comprobar dueño.
Se registra `ollama ps`, se descarga cada modelo que estuviese cargado por `ollama stop <modelo>`, sin parar servicio ni borrar pesos.
Root conserva lista/modelos/opciones para restaurar el estado previo al final, incluso con cancelación controlada.
Si Ollama ya estaba vacío no se carga un modelo por rutina; restaurar significa volver al estado anterior.

Baseline `nvidia-smi used<=1600MiB`, navegador abierto, GPU UUID y disponibilidad son puertas reales antes de cargar.
El cap se recalcula desde VRAMlibre actual−margen512MiB, manteniendo la lógica vigente. No fracciónfija de12GB ni capcopiado deT16.
El plan registra memlimitCPU/swap delcontenedor, perfilWSL16GB/8GB observado, espacio libre y posibilidad de picoRAM deXL.
No modifica `.wslconfig`, reinicia servicios o amplíaRAM automáticamente.

Los contenedoresusan nombres `music-studio-t09-<session>-<arm>`, labelsowner/session/plan, puerto loopback reservado y token no impreso.
El puerto 8101 y servicios existentes quedan intactos. Root revisa disponibilidad delpuerto elegido; no mata quien lo ocupe.
Cada job tieneULID nuevo y `output_dir="tmp/<job_id>"`; engine solo crudo. El harness escribe evidencia, nunca BD/takes.

Persistir plan+ownerreceipt antes de crear recursos. Después de cada acción material, escribir recibo nuevo exclusivo y eventos append-only.
Timeout plan explícito por fase; JobRequest permite plazo de carga/inferencia prolongado. `/v1/load` tiene deadline actual 60 s: no asumir que mide cargasXL largas.
O1 mide carga dentro de cold job con timeout explícito de 3600 s por job, revisable antes de ejecutar según root; un timeout no es éxito.
El harness heartbeat permite seguimiento: conservar handle/session y no relanzar por silencio de herramienta.

En interrupción: consultar health job propio, pedir cancel de esejob si sigueactivo, esperar terminal, unload y comprobarloaded null/idle/hijo muerto.
Solo después retirar el contenedor efímero por ID y labels coincidentes. Su caché interior desaparece con él.
`docker system prune`, restart WSL y kill global quedan prohibidos.
Si ownership/identidad no coincide, conservar recurso y registrar conflicto; nunca limpiarpor prefijo de nombre solamente.
La restauración Ollama ocurre después de liberar GPU. Si falla, registrar bloqueo real y comando de restauración exacto, no ocultarlo.

`--resume <session>` exige mismo plan SHA/image ID/source SHA/lock SHA/fixtures SHA y receipt íntegro.
No vuelve a medir una fila terminada. Para filas pendientes interroga el job ID existente antes de crear una tentativa nueva con ULID distinto.
La reanudación conserva evidencia vieja, distingue intento/fecha y repite baseline. Un changement de configuración exige sesión nueva.
`--matrix default` crea sesión nueva por defecto; no descubre automáticamente carpetas históricas ni devuelve un informe almacenado.

### 5.9 Evidencia y verificación final

Raízprivada: `.cache/dev-cycle/t09/runtime/<session>/`, restringida alproyecto. No usar carpetasT16.
Guardar `plan.json`, source/image/lock/fixtures SHA, requests/planned/captured, eventsNDJSON, observersNDJSON, outputsSHA y recibos.
Los eventos guardanseq originales y terminal único. La correspondencia run ID/job ID/request SHA/effective SHA se valida antes de resumir.
La procedencia exige `thinking=true` real y códigos audio recién generados. Rechazar referencias/códigosLM/audio deejecuciones anteriores.
El contenido de inputs privados no llega aDocker logs o Markdown público. El reporte usaIDs ciegos para fixtures/candidatos y un índice privado de procedencia.

Cada archivo de evidencia usa creación exclusiva, hash y tamaño. Ningún WAV, recibo, plan o terminal se reescribe.
La tabla pública incluye config/duración/brazo/fase, VRAMpico/cap, carga,inferencia,RTF,sharedGPU,RAM WSL,ratio y spilled con evidencia referenciada.
Medianas y dispersión se calculan desde recibos válidos, sin ocultar fallos/OOM o rows sin medir. `null` conserva su motivo.

`uv run scripts/eval/benchmark.py --matrix default` ejecuta y escribe `eval/results/benchmark-5070.md` desde la sesión real actual.
`--prepare-only` puede validarplan/CPU, pero no satisface la verificacióncanónica. Tampoco lo hacen160 jobs simulados.
Salida0 significa matriz evaluada con evidencia y cleanup válidos, admitiendo XLhardware_not_feasible acreditado según su condición explícita.
Pesos faltantes, sensores sin observabilidad, filas omitidas, browser cerrado, fuente alterada o cleanup fallido producen reporte parcial y salida no cero.
Los otros cuatro perfiles deben tener medicionesreales por duración. Un OOM es un intento medido, pero no una recomendación viable.
Root decide si esos fallos requieren el brazooffload adicional; cualquier fallback crea config_id distinto y no reemplaza la primaria.

La recomendación dedefault/alta calidad operacional cita números deRTF,carga,pico yspill; no afirma superioridad musical por50 pasos.
La etiqueta «alta calidad» identifica un modo/candidato operativo pendiente de escucha; la selección artística sigue separada.
No se elige ganador sin datos. No se cierra T09 ni M0 desde este diseño.

### 5.10 Secuencia sin pisar T-16

Root informó QA del fullpack T-16 conforme con113 pruebas y freeze61 cerrado. Ya puede integrar fuentes comunes tras elección/ADR/revisión de este diseño.
Primero implementar módulos nuevos del harness y pruebas CPU con transporte/sensor inyectables. No se cambia ningún artefacto privado T-16.
En paralelo secuencial alfreeze, preparar brief de perfiles/INT8 y documentación deinterfaces; sin tocar fuentes compartidas.
Cuando root libere freeze, releer/hasear los archivos actuales y aplicar el cambio aditivo mínimo a perfiles/descriptor/preflight/adapter/server.
Usar TDD real de cada comportamiento; conservar pruebas T16 decontroles/rama nativa/recibos, y coberturachanged-only≥80%.
Revisión fresca A+B+C+D y QA independiente deben aprobar identidad, seguridad de peso/copia/ownership y medidas antes de ejecución GPU.
Root prepara XL fuera runtime y valida imagen offline/dependencias/código, sensor Windows/browser y equivalencia de la copia efímera.
Luego ejecuta la matriz canónica, conservahandle/session, termina y acredita unload/restauración. PublicaMarkdown y evidencia validada.
Root registra ADR si delta>30s y el estado exclusivamente en tasks.md después de verificación real. Aquí TDD n/a: prosa de diseño.

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Aliasbase/XL comoTurbo | Confirmado hoy | Matriz inválida | Registroexacto, IDs propios y prueba de concordanciadescriptor/request/preflight/captured |
| INT8 declarado pero desactivado | Conocido por upstream | Medición falsa | Rechazo de downgrade, cuantización efectiva y conteo de capas, prueba real CPU↔CUDA |
| XL no cabe en 12 GB o 16 GB WSL | Desconocida | Fila no viable | Offload+INT8 oficial, cap desde libre, monitoreo RAM y error real; no convertir estimación de pesos en soporte |
| Inferencia basada enresta | Confirmado en implementaciónactual | RTF sesgado | Reloj directo sincronizado en adapter; carga/copiapostproceso separados |
| Memoria compartida sin sensor | Confirmado hasta instrumentar | CAspill abierto | WDDMagregado+TaskManager y gapsnull; NVML/WSL no sustituyen observación |
| ReferenciaRTF contaminada | Media | Spillmal clasificado | Mediana de3warm runs elegibles pormismacelda/brazo; ausencia dejaunknown |
| Caché filesystem desigual | Alta sin control | Delta bind/copiainconcluso | Alternar AB/BA, declarar uncontrolled, mismos SHA/recursos/verificación; no reiniciar WSL |
| Copia sigue usando bind accidentalmente | Media | Comparación inválida | Propagar `resource_root` a descriptor/adapter/preflight y comprobar rutas efectivas, hashes y almacenamiento en el recibo |
| Regresión deT16 | Alta siparalelo | QAinvalidada | Freeze, módulos nuevosprimero, rereadSHAantes editar y revisión deconformidad |
| Cleanup ajeno o duplicación de resume | Media | Pérdida de evidencia/interferencia | IDs+labels+plan SHA, consultar job existente y acciones idempotentes exclusivas |
| Modelo/documento no autorizado | Baja bajo locks | Licencia/constitución | ACE-Step MIT fijado y fila torchao/licencias root; APIs musicales exteriores vetadas |

El soporte hardware verificado deT16 solo acredita ese perfil/duración de aquella prueba. No extiende evidenciaaLM1.7/base/XL/300s.
El registro upstream estima pesos XL~9 GB BF16 y memoria LM adicional; son estimaciones arquitectónicas, nunca resultados de 5070.
No hay soporte INT8 sm_120 acreditado por este diseño, pese a la implementación oficial disponible.

## 7. Preguntas abiertas, fuentes y recibo

Quedan dos prerrequisitos de ejecución, no decisiones de perfil: sensor Windows con mapping verificable y factibilidad XL real.
La copia efímera usa el almacenamiento Docker existente autorizado; no abre un gate de migración del disco global.
El implementer puede empezar CPU con O1 elegido; no iniciar GPU hasta acreditar esos prerrequisitos y el freeze T16 liberado.
Root decidió conservar `Telemetry.extra` existente. No se añade obligatoriedad ni cambia el schema público.
Root registra el ADR y el alcance aditivo antes de modificar fuentes compartidas; las rutas propuestas amplían los dos ficheros canónicos para cumplir CA vigentes.

Las fuentes web se limitaron a proveedores oficiales. No se usa contenido de resultados secundarios de búsquedas.
Los bytes del upstream fijado y su SHA se conservan en `sources/` y `source-provenance.json`.
`receipt.json` contiene SHA del diseño, fuentes locales leídas, archivos propios y validación de 7 secciones/placeholders.
Una fuente leída por fragmentos figura como `read_scope=sampled`; su SHA refleja el archivo actual completo, no una auditoría exhaustiva.

| Fuente | Uso |
|---|---|
| [pyproject upstream fijado](https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/dce621408bee8c31b4fcf4811682eb9359e1bc94/pyproject.toml) | DependenciasLinux y condición torchao; archivo propioconSHA |
| [uv.lock upstream fijado](https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/dce621408bee8c31b4fcf4811682eb9359e1bc94/uv.lock) | Versiones exactas y hasheswheel; consulta focalizada, no auditoría completa supply chain |
| [Loader INT8 fijado](https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/dce621408bee8c31b4fcf4811682eb9359e1bc94/acestep/core/generation/handler/init_service_loader.py) | Configuración oficial, filtro decoder y carga que conserva parche seguro |
| [Setup fijado](https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/dce621408bee8c31b4fcf4811682eb9359e1bc94/acestep/core/generation/handler/init_service_setup.py) | Prerrequisitos de importación y normalización de opciones |
| [Orquestador fijado](https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/dce621408bee8c31b4fcf4811682eb9359e1bc94/acestep/core/generation/handler/init_service_orchestrator.py) | Downgrade INT8 y campos efectivos |
| [Transferencia fijada](https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/dce621408bee8c31b4fcf4811682eb9359e1bc94/acestep/core/generation/handler/init_service_memory_transfer.py) | Tratamiento de tensores cuantizadosCPU/GPU |
| [Controles fijados](https://raw.githubusercontent.com/ace-step/ACE-Step-1.5/dce621408bee8c31b4fcf4811682eb9359e1bc94/acestep/ui/gradio/events/generation/model_config.py) | Defaultsbase32/SFT50/Turbo8 y separación de política shift1 |
| [Microsoft GPU](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/) | Semántica agregada de memorias Windows |
| [Microsoft limitación contadores](https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/gpu-process-memory-counters-report-wrong-value) | No usar suma/detalles por proceso como verdad agregada |
| [PowerShell Get-Counter](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.diagnostics/get-counter?view=powershell-7.5) | Muestreo, nombreslocalizados y ACL |
| [NVIDIA CUDA WSL](https://docs.nvidia.com/cuda/wsl-user-guide/index.html) | Limitaciones NVML y memoria host; no sensorWindows |

No se ejecutó `--matrix default`: pertenece a la implementación y benchmark futuros. No hay números de rendimiento inventados.
No se abrió medidor individual; generación estimada y consumo null dentro de la ventana combinada de root.

| Fecha | Cambio |
|---|---|
| 2026-10-06 | Diseño privado T09 aprobado: root elige O1; telemetría en `extra`, copia efímera y tres warm runs; fuentes T16 intactas |
