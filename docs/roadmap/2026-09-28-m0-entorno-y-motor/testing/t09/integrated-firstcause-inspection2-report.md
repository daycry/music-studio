# Inspección FIRSTcause — intento 2

**0 Critical · 1 Important · 0 Minor.** FC01 del episodio está corregido. FC02 permanece dentro de la ingesta canónica, líneas 1059 y 1142. Se amplía la siguiente unidad a esa frontera; no se declara resuelto R09-T09 ni se sustituye QA.

## Lente A

**Lente A: 0 Critical · 1 Important · 0 Minor.** FC01 está corregido en `EpisodeAcquirer`, pero permanece un residuo de FIRSTcause dentro de la ingesta canónica. No procede declarar corregido todo B4-01/R09-T09.

| T-09 → criterio del componente | Resultado | Evidencia fichero:línea |
|---|---|---|
| Preservar primaria ante fallo de cierre y de registro en el manejador del episodio | ✓ | `scripts/eval/benchmark_episode.py:695`: fallback tipado, registrador seguro y guarda exterior; relanzamiento mediante `raise` en `:735`. |
| Conservar identidad, tipo y traceback; intentar cerrar sensor y registrar interrupción | ✓ | `scripts/eval/tests/test_benchmark_canonical_integration.py:1377`: comprobaciones anteriores al rescate, para `none`, `record` y `safe_record`. |
| Invalidar head/recibos y conservar incertidumbre del recurso | ✓ | `test_benchmark_canonical_integration.py:1390`: ausencia de aceptación, posiciones vacías y `UNKNOWN_QUARANTINED`, aunque el proceso haya terminado. |
| Preservar primera causa también cuando falla **dentro** de la ingesta canónica | ✗ Important | `scripts/eval/benchmark_canonical_runtime.py:1059` y `:1142`: registro secundario sin guarda. Los nuevos casos lanzan la primaria **después** de que la ingesta original termine (`test_benchmark_canonical_integration.py:1315`). |
| Preservar pruebas anteriores y fuentes protegidas | ✓ | 29 funciones anteriores de integración conservadas por AST; 13 archivos protegidos sin discrepancias de hash. |
| Cierre fallido sin primaria sigue siendo fallo | ✓ | El diff no modifica las rutas normales de cierre; conserva las comprobaciones anteriores. |

| Control de conformidad | Resultado | Evidencia |
|---|---|---|
| Plan y `Archivos` | ✓ | Los dos archivos del diff pertenecen a módulos/pruebas de `scripts/eval/`, declarado en `tasks.md:401`. Scope: dos dentro, cero fuera. |
| Tests y TDD | ✓ para FC01 acotado | RED original: `red-record/stdout.txt` muestra `OSError` sustituyendo `PrimaryFailure`, exit 1, iniciado `2026-10-09T01:13:18.855032Z`. Es fallo funcional, no de colección. |
| Ejecución entregada | ✓ | `final01/stdout.txt:5`: **266 passed, 13 deselected**; JUnit: cero failures/errors/skips; exit 0. No repetí la suite. |
| Cobertura vigente | ✓ | WHOLE oficial, líneas+ramas, cada módulo ≥80 %, cero exclusiones; cifras abajo. No sustituye la lectura de los tests. |
| Constitución explícita | ✓ | No observo infracción introducida por este diff. T-09 permanece abierta conforme a `docs/CONSTITUTION.md:33`; no cambia contratos públicos ni decisiones documentadas (`:35`, `:37`). |
| Verificación de tarea cerrada | N/A | T-09 está `en-progreso` (`tasks.md:395`). El benchmark completo declarado en `:403` sigue sin acreditarse; estos tests no lo sustituyen. |
| E2/E3 interop | N/A | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar el exportador. |

Cobertura comprobada directamente en `final01/coverage-official.json`: integration **86,940299 %**, canonical runtime **84,279919 %**, coordinator **83,741648 %**, episode **87,078652 %**, process **81,777778 %**, runtime **80,516899 %**. Verifiqué las **276 trazas RAW y sus copias** sin discrepancias, y los dos archivos actuales contra el freeze. Ejecución identificada por UUID `2698d906-44f5-4722-8246-06c20dd0e1c7`.

**Important — residuo de FIRSTcause en la ingesta real.** En `benchmark_canonical_runtime.py:1059`, si `_ingest_latest()` falla, `abort_owned()` también falla y `cleanup_error_record()` lanza, el registrador sustituye la primaria antes de llegar a la nueva guarda del episodio. El mismo patrón existe en `:1142`.

Comprobé el primer escenario ejecutando los métodos extraídos del **AST actual**, con dependencias controladas exclusivamente en memoria: `primary_preserved=False`, excepción final `OSError`, llamadas `ingest → abort → record`, ningún cierre del sensor y ningún intento interrumpido. `EpisodeAcquirer.acquire()` no captura ese `OSError` (`benchmark_episode.py:667`). **Es prueba estática ejecutada, no evidencia nativa.** Los nuevos tests cubren una primaria lanzada después de una ingesta exitosa y no detectan esta frontera interior.

| T-09 → criterio de aceptación completo | Estado |
|---|---|
| Matriz de configuraciones y duraciones — `tasks.md:407` | ✗ Pendiente |
| Bind mount frente a copia — `:408` | ✗ Pendiente |
| Ollama descargado y VRAM de reposo acreditada — `:409` | ✗ Pendiente |
| Navegador visible y desbordamiento — `:410` | ✗ Pendiente |
| Experimento opcional `torch.compile` — `:412` | ✗ No acreditado; opcional |
| Recomendación con números — `:413` | ✗ Pendiente |

Estos pendientes no son nuevos gaps de cierre: la tarea sigue abierta. Se conservan B4-02/B4-03/B4-04 y R09-T13, formal4→5 y el rebate de T-10. No se acredita QA independiente, GPU160, cadencia, calibración, CLI, FINAL ni aceptación de T-09/M0.

## Lente B

**Sin defectos en el alcance FC01/componentinspection2. 0 Critical · 0 Important · 0 Minor. FC01 corregido.**

| Criterio | Resultado | Fichero:línea |
|---|---|---|
| Ingesta primaria + cierre canónico fallido + registrador fallido conserva la primaria | ✓ | `scripts/eval/benchmark_episode.py:695` |
| Fallo del propio registrador seguro conserva evidencia tipada con digest/reloj UNKNOWN | ✓ | `scripts/eval/benchmark_episode.py:699` |
| Se registra interrupción en memoria y se intenta cerrar el sensor | ✓ | `scripts/eval/benchmark_episode.py:709`, `:725` |
| Se conserva identidad, tipo y traceback de la primaria | ✓ | `scripts/eval/benchmark_episode.py:735` |
| Cierre sin primaria continúa propagando errores | ✓ | `scripts/eval/benchmark_episode.py:739` |
| Regresión controla los tres modos y comprueba estados antes del rescate | ✓ | `scripts/eval/tests/test_benchmark_canonical_integration.py:1284` |

Contrastados los dos RED funcionales originales, argv/UTC/JUnit y el baseline **266 PASS, 13 deseleccionados, cero failures/errors/skips**. Verificados freeze, fuentes protegidas, AST previo y 276 copias RAW. Cobertura oficial WHOLE de cada uno de los seis módulos ≥80 %, cero exclusiones.

Revisión estática y comprobaciones de lectura; **no ejecuté pruebas nativas**. La evidencia entregada usa recursos nativos con fallos controlados; la interrupción inmediata acredita memoria, no persistencia en disco.

B4-02/03/04 y R09T13 permanecen abiertos; contador formal4→5 intacto. No implica aceptación de T09/M0 ni sustituye QA independiente.

## Lente C

**Sin hallazgos de seguridad introducidos o reabiertos: 0 Critical · 0 Important · 0 Minor.**

Revisado el diff completo de dos archivos de `integrated-firstcause-inspection2/scope.diff`, las fuentes actuales y el contexto protegido. Los hashes actuales coinciden con el freeze. Selector C: `false`, sin motivos automáticos; revisión suplementaria por custodia de procesos/Jobs y excepciones.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ No añade destinos de ejecución ni interpolación de entradas | `scripts/eval/benchmark_episode.py:697` |
| Autenticación, sesión y autorización | ✓ No altera permisos ni habilita aceptación tras el fallo | `scripts/eval/benchmark_episode.py:709` |
| Secretos y exposición de errores | ✓ Registro secundario acotado; digest o `None`, sin publicar el mensaje | `scripts/eval/benchmark_episode.py:699`; `scripts/eval/benchmark_coordinator.py:23` |
| Deserialización insegura | ✓ No incorpora deserializadores ejecutables | `scripts/eval/benchmark_episode.py:705` |
| Path traversal y SSRF | ✓ No introduce rutas ni destinos de red derivados del error | `scripts/eval/benchmark_episode.py:699` |
| Custodia y primera causa — FC01 | ✓ El fallo del logger queda protegido; continúa la interrupción y el intento de cierre del sensor; relanza la primaria | `scripts/eval/benchmark_episode.py:707`, `:709`, `:725`, `:735` |
| Aislamiento de recursos propios | ✓ Regresión comprueba identidad extranjera intacta antes del rescate | `scripts/eval/tests/test_benchmark_canonical_integration.py:1404` |

**FC01 corregido en la frontera delimitada.** No implica que todas las rutas de primera causa del proyecto estén corregidas.

Evidencia archivada contrastada: dos RED funcionales por `OSError` sustituyendo `PrimaryFailure`; `final01` con **266 PASS, 0 fallos/errores/skips y 13 deseleccionados**. Cobertura oficial WHOLE de los seis módulos: **86,9403 / 84,2799 / 83,7416 / 87,0787 / 81,7778 / 80,5169 %**, cada uno con cero exclusiones.

Mi verificación fue estática y de lectura; no ejecuté suites ni procesos nativos. Las pruebas entregadas utilizan recursos Windows reales con fallos controlados y sensor simulado. La interrupción inmediata se conserva en memoria; no acredita persistencia durable ni cierre universal de lectores.

B4-02/03/04 y R09T13 permanecen abiertos; formal4→5 y los límites UNKNOWN siguen intactos. Sin aceptación de componente, T09 o M0.

