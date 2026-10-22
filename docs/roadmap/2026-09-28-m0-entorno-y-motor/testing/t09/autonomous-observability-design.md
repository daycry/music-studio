---
design: t09-autonomous-observability
titulo: Acreditación automática de observabilidad GPU
estado: aprobado
creado: "2026-10-07"
actualizado: "2026-10-07"
spec: ../../../../../docs/roadmap/2026-09-28-m0-entorno-y-motor/spec.md
evaluacion: n/a
plan: ../../../../../docs/roadmap/2026-09-28-m0-entorno-y-motor/improvement-plan.md
adr: docs/decisiones/ADR-0036-observabilidad-wddm-autonoma.md
opcion_elegida: O1
recomendada: O1
generacion:
  fuente: estimado
  tokens: null
  coste_eur: null
  horas_ia: null
  medidor: ventana-unica-del-orquestador
---

# Diseño — Acreditación automática de observabilidad GPU

Spec M0 aprobada; subfase de T-09. No reemplaza su plan ni acredita su verificación GPU. El orquestador conserva la elección y publicación bajo la autorización delegada del propietario. Este agente entrega opciones; no fija una elegida ni escribe un ADR.

## 1. Contexto y restricciones

El propietario ha delegado la continuación de M0–M5 y no podrá aportar más lecturas. ADR-0033 conserva observación verificable de Task Manager como puerta previa al benchmark. `benchmark_runner.validate_prerequisites` exige actualmente parejas baseline/representative manuales. Es necesario cambiar esa puerta explícitamente; aceptar JSON de aspecto correcto o renombrar datos históricos no resuelve el problema.

| Evidencia existente | Qué acredita | Límite |
|---|---|---|
| `testing/t09/gpu-baseline-capture-{report.md,receipt.json}` | RTX 5070; pantalla 1,3/12 GB y 0,1/15,8 GB | PDH posterior, no simultáneo; redondeo/escala no exactos |
| `testing/t09/browser-baseline-capture-{report.md,receipt.json}` | Viewport about:blank y correlación posterior PID6932/HWND8062574 | Identidad histórica, ahora ausente |
| `.cache/dev-cycle/t09/representative-capture-instrumental60-20261006/` | Captura21:32:15,356–,609 UTC y sensor próximo21:32:15,569992 UTC | Pantalla1,3 GB frente NVML8904/PDH8918,34 MiB; discrepancia real; causa no probada |
| `.cache/dev-cycle/t09/autonomous-baseline-20261007/` | Diez muestras22:56:24–33 UTC, NVML1264 MiB; PDH1277,89 dedicada/131,65 compartida, status0, LUID0:BFF3 | Sin navegador vivo, sin modelo/carga, sin metadatos/raw/timestamps por sensor requeridos por este diseño |
| `.cache/dev-cycle/t09/owner-peak-and-autonomy-20261007.json` | Autonomía explícita y lectura9,5 dedicada máxima/0,2 compartida | Hora/escala desconocidas; compartida no declarada máxima; sin simultaneidad |
| `.cache/dev-cycle/t09/autonomous-browser-20261007/root-receipt.json` | Root aporta nueva pestaña propia2032699582/about:blank, viewport y DOMvisible; heartbeatPID17152/HWND1314188/msedge visible | No binding directo tab→HWND; persistencia efímera, requiere latidos durante el lote |

Se conserva la matriz nominal de160 jobs: cinco perfiles × cuatro duraciones × dos brazos × cold+3warm. No se cambian `/v1`, pesos, locks, duración, modelo, BF16, VRAM libre−512 MiB, reposo≤1600 MiB, unload por hijo ni restauración del estado previo de Ollama. El navegador debe estar abierto y visible durante la medición. Una pestaña propia en blanco y una ventana de navegador visible acreditan sus respectivas condiciones observadas; no acreditan consumo de la futura UI de M1 ni su vinculación entre sí si no está probada.

La semántica publicada de Task Manager procede de VidMm/VidSch, y la memoria compartida es memoria del sistema usada por GPU. [Microsoft](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/). La incidencia documentada de memoria **por proceso** no explica nuestro panel Rendimiento. [Incidencia oficial](https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/gpu-process-memory-counters-report-wrong-value). NVML en WSL dispone de consultas limitadas; una consulta ausente sigue desconocida. [NVIDIA](https://docs.nvidia.com/cuda/wsl-user-guide/index.html).

## 2. Opciones

### O1 — PDH agregado acreditado por API, con contraste dedicado separado

Mantener `GPU Adapter Memory` dedicado/compartido como medición Windows primaria. Unir instancia a DXGI por LUID exacto y a inventario físico inequívoco. Acreditar estado, tipo/unidad/escala, timestamp nativo, frescura y respuesta dedicada ante carga/unload. Contrastar dedicada con NVML y guardar CUDA del hijo por separado. Sustituir la obligación de captura Task Manager por una política automática versionada, mediante ADR nuevo que complemente ADR-0033. La compartida queda observada por el proveedor agregado Windows; **no queda calibrada de forma independiente por NVML/CUDA**.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: ampliar observador, política, validador y recibos existentes |
| Riesgo | Medio: errores o retraso del proveedor compartido no detectables por NVML; confianza declarada y datos incompletos inválidos |
| Coste relativo | M: no instalaciones ni grabación global, reutiliza interfaces reales |
| Reversibilidad | Alta: nuevo modo discriminado; conserva validador y evidencia histórica GUI |

### O2 — PDH primario más extracción ETW/WPR/WPA comprobada

Añadir a O1 una grabación acotada de calibración con WPR y exportación automática de tablas VidMm, si herramientas ya disponibles y permisos/ownership efectivos lo permiten. Validar adaptador, ámbito agregado, memoria local/no local, unidad y reloj de cada tabla antes de compararla. Es una segunda ruta de adquisición; puede compartir origen VidMm y no demuestra independencia física ni ausencia causal de spill.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: perfil, ETL, tabla/exportación real, alineación temporal, sesiones y overhead |
| Riesgo | Alto: WPR disponible no implica exporter ni tabla adecuada; captura global puede interferir con sesiones ajenas |
| Coste relativo | L: extracción y validación adicional; no admite instalar SDK/ADK en esta fase |
| Reversibilidad | Media: puede retirarse el contraste; conservar ETL/CSV/recibos propios |

WPR.exe y perfil GPU están inventariados, pero no hay una extracción validada. Microsoft documenta exportación CLI de un ETL con `.wpaProfile`; no promete que cualquier ETL GPU contenga una tabla de sharedGPU apta. [WPA Exporter](https://learn.microsoft.com/en-us/windows-hardware/test/wpt/exporter). O2 solo es elegible tras inventario RO del exporter, versión/hash, perfil real, tabla con datos y mapeo/unidades comprobados. Verificar sesión ajena antes de empezar; no usar cancelación global, reiniciar servicios ni elevar para sortear bloqueos. Salidas/temporales bajo el proyecto. Esta entrega no inicia WPR.

### O3 — Conservar puerta GUI y publicar diagnóstico parcial

Mantener ADR-0033 y validador manual. Conservar medidas automáticas como diagnóstico sin recomendación completa ni salida0 canónica. Preserva la puerta existente, pero no permite finalizar autónomamente T-09 mientras no exista una nueva pareja GUI verificable; no se pedirán más lecturas al propietario.

| Criterio | Valoración |
|---|---|
| Complejidad | Baja: no cambia código ni semántica de aceptación |
| Riesgo | Bajo para la honestidad; alto de bloqueo indefinido del objetivo |
| Coste relativo | S en implementación; dependencia externa sin resolución autónoma |
| Reversibilidad | Alta: se conserva como fallback diagnóstico de O1/O2 |

No se ofrece D3DKMT como cuarta alternativa ejecutable. La estructura candidata `D3DKMT_QUERYSTATISTICS_SEGMENT_INFORMATION` está reservada para uso del sistema, con ABI dependiente de versión. [Documentación oficial](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/d3dkmthk/ns-d3dkmthk-d3dkmt_querystatistics_segment_information). Tampoco sirve `IDXGIAdapter3::QueryVideoMemoryInfo` como sustituto: consulta uso/presupuesto del proceso llamante. [DXGI](https://learn.microsoft.com/en-us/windows/win32/api/dxgi1_4/nf-dxgi1_4-idxgiadapter3-queryvideomemoryinfo).

## 3. Criterios de decisión

1. Medición real agregada de memoria compartida del adaptador exacto antes que apariencia de calibración GUI.
2. Autonomía autorizada sin ampliar acceso a aplicaciones ajenas,8768 o pantallas del propietario.
3. Ausencia de datos/estado inválido implica desconocido y reporte parcial; no convierte `spilled_engine=false` en sharedGPU0.
4. Criterios sellados antes de nueva GPU; sin ajustar umbrales tras ver resultados ni reciclar muestras históricas como acreditación nueva.
5. Misma matriz, relojes de inferencia, baseline por grupo y tres warm nuevos por celda/brazo/entrada. Sin equivalencia CPU→GPU ni rendimiento→calidad musical.
6. Cambio aditivo con cadena de procedencia y posibilidad de conservar O3; O2 solo cuando pueda comprobarse de extremo a extremo.

## 4. Recomendación · opción elegida y por qué

**Elegida: O1 por el orquestador bajo la delegación explícita del propietario.** Es la única opción ahora implementable con APIs públicas y herramientas existentes que elimina la dependencia de lecturas manuales conservando sharedGPU Windows. O2 queda contraste futuro opcional, condicionado a extracción probada; O3 será la salida diagnóstica si falla la acreditación automática.

La aceptación O1 permite recomendar **rendimiento operativo medido con observación WDDM agregada**, con `shared_validation_level=provider_verified` y `shared_independent_validation=false`. No afirma calibración Task Manager, independencia de shared ni cero spill causal. La discrepancia anterior permanece documentada como `task_manager_contrast=conflicting_historical`, no se resuelve por cambiar la puerta.

### Política previa a GPU, versionada y sellada

| Condición | Criterio propuesto antes de cualquier nueva carga |
|---|---|
| Identidad | Enumeración DXGI completa, RTX5070/vendor0x10DE inequívoco, LUID32+32 exacto en ambos contadores; NVML UUID+nombre inequívocos; driver/buildWindows capturados. Nunca mapear por consumo o `phys_0` |
| Unidades | Guardar tipoPDH y escala; exigir contador de uso absoluto validado como bytes, formato sin escala (`PDH_FMT_NOSCALE`) y conversión `bytes/2**20`; conservar raw/formatted y ruta. Tipo/escala incompatible: rechazo, no inferencia |
| Estados | Retorno collect/raw/format0, raw y formatted CStatus0 o1; valores finitos≥0. CStatus0 significa válido aunque el valor no cambie; no exigir CStatus1. Errores/null conservados |
| Tiempo | UTC y monotónico inicio/fin por operación; timestamp de colección y rawPDH conservados; reloj monotónico ascendente, timestamp de colección nuevo en cada tick; duración colección≤2s, hueco entre ticks≤2,5s; no usar timestamp general anterior a todas las llamadas como simultaneidad |
| Pareja dedicada | Contrastar solo parejas cuya diferencia de puntos medios≤1s y bracket de cada consulta≤2s. No exigir total=used+free, dado que pueden existir reservas NVML |
| Baseline | Diez muestras nuevas, cadencia objetivo1s, antes de cargar cada grupo, con navegador visible acreditado; todos estados, frescura, identidad y navegador válidos; NVML≤1600MiB; margen512 y free fresco |
| Contraste representativo | Diez parejas nuevas en baseline y diez en meseta tras evento real de carga terminada antes de unload; todas cumplen `abs(PDHded-NVMLused) <= max(128MiB,0.02*NVMLused)`. Meseta definida por ese estado de fase, sin buscar un tramo favorable después. Detectar crecimiento dedicado de al menos512MiB respecto baseline en ambos; tras unload diez muestras nuevas acreditan recuperación NVML≤1600MiB y descenso dedicado≥512MiB |
| Alcance contraste | Es comprobación experimental de plausibilidad/identidad/respuesta de dedicada, no igualdad contractual entre APIs. CUDAalloc/reserved/pico del hijo son coherencia separada con su cap y reloj; no se suman a PDH ni calibran compartida |
| Shared | Raw/status/tipo/unidad/tiempo exactos de `Shared Usage` válidos; diez baseline; tolerancia vigente `max(32MiB,3*population_stdev(baseline))`; aumento sostenido en dos ticks consecutivos. Valores constantes son válidos si consultas/timestamps avanzan |
| Vigencia | Acreditación representativa de la misma sesión, source/image/lock/policy hashes y driver/build/adaptador; inicio matriz≤15min tras recuperación. Antes de cada grupo/resume nuevo baseline; cambio identidad/driver/policy o hueco de sesión>15min obliga re-acreditación. No validar por hash solo |
| Navegador | Pestaña propia about:blank por API soportada y ventana de navegador identificada con PID+creationTime+exe+HWND+rectángulo no vacío+IsWindowVisible+no IsIconic. Evidencia inicial fechada/hash del viewport propio y su tab/browser ID. Registrar bindingtab→HWND como probado/no probado, sin inferirlo por unicidad. Latido nativo de la ventana en cada muestra, sin leer pestañas ajenas; cambio/reutilización PID/HWND requiere nueva identidad. Si se crea ventana/perfil nuevo, perfil bajo `.cache`; no es obligatorio crear otro si existe ventana válida |

Los números128MiB/2%,512MiB,1s/2s/2,5s y15min son **criterios experimentales propuestos**, no garantías oficiales de API ni derivados de la captura discrepante. Deben quedar en plan y recibo antes del piloto. Si son inviables, registrar fallo y proponer política nueva antes de repetir; no recalificar un intento previo. El contraste no obliga aumento compartido: producirlo artificialmente no es necesario ni aconsejable para certificar una muestra válida.

Un piloto representativo nuevo bajo preflight puede usar TurboLM0.6/instrumental60 con carga/estados reales, separado del benchmark. No se cuentan sus jobs ni las tomas T10 anteriores entre los160 nominales. El piloto se ejecuta solo por root después de TDD/revisión/QA; esta entrega no lo ejecuta.

### Validator de prerrequisitos y recomendación

`observation.method` discrimina `task_manager_v1` y `wddm_auto_v1`; no se acepta presencia de uno para satisfacer el otro. Validar esquema estricto, policy hash, seals/rutas contenidas/tamaños, timestamps reales no futuros, sesión/driver/adaptador/browser, source/image/lock coincidentes y arrays NDJSON originales. Una acreditación nueva no debe declarar `task_manager.baseline/representative` ni `calibration_pass=true` para capturas previas. Validador histórico sigue disponible con su propia política.

Comprobar baseline y sensores durante **toda** carga/generación/unload, no solo en prerequisites. Un error, cambio de LUID/UUID, muestra caducada o navegador ausente invalida la fila; no interpolar, rellenar ceros ni continuar nuevas submissions con observabilidad perdida. Recuperación/cancelación de job propio conserva la lógica y evidencia existentes.

`reference_rtf` mantiene exactamente tres warm distintos, nuevos y elegibles de la misma config/duración/modo/brazo/fixture; sin aumento shared detectado, cap y observabilidad válidos. Falta cualquiera: referencia/ratio null y `spill_assessment=unknown`. Ratio>1,5 junto con aumento shared es compatible con presión/spill; ningún patrón prueba atribución al hijo. Incluso `not_detected` se presenta como «sin indicio bajo esta política y cadencia», nunca «sin spill» absoluto.

Recomendación completa exige cobertura nominal160 (salvedad XLhardware_not_feasible con evidencia vigente), recibos/WAV/entrada/relojes/terminales/cleanup válidos, sensores acreditados y tres warm por grupo; no ocultar filas fallidas/OOM. Comparación default/alta calidad usa cifras reales, dispersión y la confianza arriba. El candidato artístico y CAs humanos siguen pendientes de escucha; no inferirlos de autonomía.

## 5. Impacto en módulos y ficheros

| Ruta real o nueva propuesta | Cambio de O1 | Tipo / dueño siguiente |
|---|---|---|
| `scripts/eval/benchmark_windows.py` | Persistir inventarioDXGI, metadatosPDH, raw/format/timestamp nativo; latido no minimizado y creationTime | Modificado / implementer |
| `scripts/eval/benchmark_observers.py` | Brackets por sensor, validación tipada/frescura/unidades y contraste dedicado; conservar errores y ámbitos | Modificado / implementer |
| `scripts/eval/benchmark_runner.py` | Discriminador de prerequisites y validador estructural+sustantivo; resumen rechaza status/tiempo/identidad inválidos también en baseline | Modificado / implementer |
| `scripts/eval/benchmark_plan.py` | Nueva política versionada con umbrales y fingerprint; hash incluido en plan; no cambiar matrix_runs | Modificado / implementer |
| `scripts/eval/benchmark.py` | Baseline/resume/finalización aplican misma política; referencia a calibración nueva; conservación del lease y cleanup | Modificado / implementer |
| `scripts/eval/benchmark_evidence.py` | Provenance/confianza en recibos/report; evitar texto de cero spill; criterios existentes de treswarm y matriz intactos | Modificado / implementer |
| `scripts/eval/benchmark_runtime.py` | Reusar APIs/lease/unload/ownership actuales; cambio solo si integración requiere transportar receipt, no relajar guardas | Lectura/reuso / implementer |
| `scripts/eval/tests/test_benchmark_{windows_cpu,observers,runner,plan,cli,evidence,integration_cpu}.py` | RED de discriminador, statusválido/estadoinválido, rawunidades, datoidénticofresco, replay, skew, PID/HWNDreuse, baseline sinbrowser, sharedunknown y treswarm | Modificados / implementer TDD |
| `.cache/dev-cycle/t09/runtime/<session>/observation/` | Policy, source/image/driver/inventory seals, muestras y brackets, calibración baseline/load/unload, viewport propio y recibo | Nueva evidencia / root |
| `docs/decisiones/ADR-NNNN-observabilidad-wddm-autonoma.md` | Complementar/cambiar puerta expresa de ADR0033; registrar O1/O2/O3, confianza limitada, sin equivalencia shared↔NVML | Nuevo / root; número libre comprobado por root |
| `docs/decisiones/README.md` | Índice del ADR nuevo | Modificado / root |
| `docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/benchmark-design.md` §§5.7–5.9 | Sustituir calibración GUI obligatoria por modos explícitos, provenance/confianza/validez; histórico preservado | Modificado / root |
| `docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md`, `CONTINUE-HERE.md` | Trazar decisión/fase y evidencias; criterio original se conserva con callout de mecanismo equivalente aceptado por ADR | Modificados / root; no cerrarT09 |
| `eval/results/benchmark-5070.md` | Solo verificación canónica real futura; confianza y referencias al receipt | Generado / root trasGPU |

Provenance mínimo: `schema_version,method,session_id,run_id,job_id,plan_sha256,policy_sha256,source_hashes,image_id,lock_sha256,driver_version,windows_build,nvml_uuid,dxgi_inventory,adapter_luid,counter_paths,counter_type,raw_unit,format_flags,scale,conversion,pdh_status,query_filetime,raw_counter,started_utc,finished_utc,started_monotonic_ns,finished_monotonic_ns,browser_identity,browser_heartbeat,evidence_sha256,evidence_bytes,validation_results,shared_validation_level,shared_independent_validation,task_manager_contrast,limitations`. CUDA/WSL conservan sus ámbitos; identificación del hijo no implica PID Windows uno-a-uno. No contenidos privados de entradas/token ni rutas personales en informe público.

O2 añadiría módulo/pruebas de extracción ETW y evidencia propia solo después de probar su prerequisito. O3 no altera producto. No se añade dependencia, servicio, instalación ni cambio de engine para obtener acreditación de host.

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Shared agregado atribuido al hijo o NVML usado para validarlo | Alta sin lenguaje explícito | Falso cero spill | Fuente y confianza separadas; causalidadunknown; sharedindependentfalse |
| Histórico válido por hash pero caducado | Confirmado en navegador | Benchmark con puerta falsa | Freshness y sesión/identidad/driver; ventana propia nueva; baseline fresco |
| Counter exitoso con CStatus inválido / valor fijo tratado como stale | Medio | Falsa aceptación/rechazo | Retornos y CStatus separados; timestamps nuevos; valor idéntico no inválido por sí mismo. [PDH](https://learn.microsoft.com/en-us/windows/win32/api/pdh/nf-pdh-pdhgetrawcountervalue) |
| Formateo/escala ambiguos | Medio | Error de MiB/GB | Raw+tipo+scale y NOSCALE; divisiones explícitas; rechazo tipo no probado. [Propiedades PDH](https://learn.microsoft.com/en-us/windows/win32/api/pdh/ns-pdh-pdh_counter_info_w) |
| Timestamp general implica simultaneidad falsa | Confirmado en muestra secuencial actual | Contraste inválido | Brackets por llamada y timestamp query. [PdhCollectQueryDataWithTime](https://learn.microsoft.com/en-us/windows/win32/api/pdh/nf-pdh-pdhcollectquerydatawithtime) |
| Umbral dedicado no válido para esta combinación driver/API | Medio | Piloto rechazado | Política previa, sin afirmar garantía; fallo conserva datos; cambio futuro exige nueva versión/intento |
| Coste extra sensor altera cadencia/HTTPdeadline | Medio | RegresiónR09-04/08 | APIsCPU fake con retrasos y regresiones deadline; no nueva instalación; budgetes independiente |
| ETL sin shared utilizable o conflicto WPRglobal | Alto hasta prueba | Calibración falsa/interferencia | O2 opcional; exporter/perfil/tabla/ownership requeridos; ETL por existir no es calibración |
| Blankbrowser carga diferente a UI futura | Cierto | Generalización excesiva | Declarar about:blank, perfil/viewport/condición del experimento; no alegar benchmarkUI-M1 |
| Calidad humana no disponible | Cierto | CAs musicales no cerrables automáticamente | Publicar resultado operacional y dejar evaluación artística pendiente |

## 7. Preguntas abiertas

No se requieren respuestas ni nuevas lecturas del propietario para preparar O1. El orquestador ha elegido O1 y publicado ADR-0036; la política se versiona y sella antes de la nueva ejecución GPU. La estructura D3DKMT propuesta no es una dependencia admisible; O2 permanece pendiente de extractor real, no bloquea O1.

Pendientes verificables en ejecución: metadatos/tipo/unidad reales de PDH en este host; brackets/cadencia efectivos; frescura/continuidad de la nueva identidad y viewport aportados por root; piloto dedicado/load/unload de sesión nueva; los160 jobs y salida canónica; factibilidadXL y evaluación humana. El binding directo tab→HWND actual no está probado; la ventana visible y el viewport propio son evidencias separadas, y no se inventará esa unión. Su ausencia impide declarar esos resultados, pero no impide la implementación CPU.

Esta entrega solo contiene diseño y recibos propios. TDD n/a: prosa de arquitectura; los tests RED/GREEN pertenecen al siguiente implementer. No se ejecutó verificación canónica, GPU, WPR, UI, instalación, servicio, Git, ni escritura de docs/ledger/memoria. Meter único ya abierto por root; no se abre/cierra otro ni se estima trabajo IA por reloj.

La propuesta y sus fuentes selladas originales se conservan en `.cache/dev-cycle/t09/autonomous-observability-design/`. [Recibo publicado](autonomous-observability-design-receipt.json). O1 elegida y ADR-0036 publicado; implementación y medición real pendientes.


## Decisión del orquestador

O1 aprobada el2026-10-07 bajo la autorización de continuar autónomamente todo el roadmap y escoger las mejores alternativas. [ADR-0036](../../../../decisiones/ADR-0036-observabilidad-wddm-autonoma.md) fija el cambio de puerta; las fuentes y la propuesta originales quedan intactas en el laboratorio privado. Implementación, revisión, QA y acreditación real pendientes; ningún resultado GPU nuevo se deriva de esta decisión.
