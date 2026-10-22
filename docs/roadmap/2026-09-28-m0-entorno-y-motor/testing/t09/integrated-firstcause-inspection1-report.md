# Inspección FIRSTcause — intento 1 del componente

**0 Critical · 1 Important · 0 Minor**. Las tres fronteras originales están corregidas; persiste FC-01: error al registrar cleanup canónico sustituye la primera causa y omite cierre del sensor. Formal4/5 y los demás gaps se conservan. No QA/aceptación.

## Lente A

**Lente A: 0 gaps nuevos — 0 Critical, 0 Important, 0 Minor.** B4-01/R09-T09 queda corregido en las **tres fronteras acotadas** revisadas. Esto no cierra T-09 ni constituye QA independiente.

Revisado el diff completo de seis archivos y comprobada su identidad SHA-256 frente al freeze y las copias anteriores a final03.

| Tarea → criterio del componente | Resultado | Evidencia fichero:línea |
|---|---|---|
| T-09 → conservar primera causa durante startup y cleanup | ✓ | `scripts/eval/benchmark_process.py:330`; identidad y tipo comprobados en `scripts/eval/tests/test_benchmark_process.py:417` |
| T-09 → conservar primera causa de proof al cerrar sensor | ✓ | `scripts/eval/benchmark_episode.py:716`; prueba en `scripts/eval/tests/test_benchmark_episode_v3.py:22` |
| T-09 → conservar excepción del cuerpo al cerrar contexto | ✓ | `scripts/eval/benchmark_coordinator.py:100`; prueba en `scripts/eval/tests/test_benchmark_coordinator_v3.py:20` |
| T-09 → fallo del registro secundario no sustituye primaria | ✓ | Guardas en las tres fronteras; variantes `recording_fault=True`. Registro acotado en `scripts/eval/benchmark_coordinator.py:23` |
| T-09 → conservar recurso incompleto si falla adjuntar referencia | ✓ | Referencia explícita y fallback mediante traceback: `scripts/eval/benchmark_process.py:337`; prueba del setter fallido en `scripts/eval/tests/test_benchmark_process.py:486` |
| T-09 → error de cleanup sin causa previa sigue propagándose | ✓ | Pruebas en `test_benchmark_process.py:463`, `test_benchmark_episode_v3.py:68` y `test_benchmark_coordinator_v3.py:64` |
| T-09 → no declarar recursos devueltos sin prueba | ✓ | `scripts/eval/benchmark_process.py:348` y `:701`; se conserva `UNKNOWN_QUARANTINED`, sin deducir cierre únicamente de Job vacío |

| Control solicitado | Resultado | Evidencia |
|---|---|---|
| Implementación frente a plan y `Archivos` | ✓ | Los tres módulos y tres tests pertenecen a `scripts/eval/`, declarado en `tasks.md:401`. Scope capturado: seis archivos en alcance, cero fuera, cero excluidos |
| Tests y TDD reales | ✓ | JUnit/logs: seis RED iniciales por sustitución de excepción y un RED adicional por setter; todos funcionales. Los tres casos sin primaria son preservación, no RED causal |
| GREEN actual | ✓ | `final03/stdout.txt:5`: **263 passed, 13 deselected**; JUnit: cero failures/errors/skips; exit **0** |
| Cobertura actual | ✓ | WHOLE oficial, líneas+ramas: coordinator **83,741648 %**, episode **86,311787 %**, process **82,666667 %**. Los otros tres módulos: **86,194030 / 84,584178 / 80,516899 %**. Cero exclusiones en los seis |
| Procedencia de cobertura | ✓ | UUID `9ad4ae34-66d7-436e-8ac4-d2f00039d0f9`; **267 RAW** con hashes y copias previas a combine comprobados. Sin unión histórica |
| Constitución explícita | ✓ | No se observa infracción del diff. Estado y cierre conforme a `docs/CONSTITUTION.md:33`; secretos conforme a `:42`; contratos públicos sin modificación, conforme a `:35` |
| Verificación de tarea cerrada | N/A | T-09 continúa **en-progreso** (`tasks.md:395`). La verificación completa de `tasks.md:403` no se acredita con estos tests; no se ejecutó para suplir evidencia |
| E2 / E3 interop | N/A | El diff no toca `commands/`, `agents/` ni `hooks/`; no procede ejecutar exportador |

Los criterios de aceptación completos permanecen correctamente abiertos:

| T-09 → criterio del ledger | Estado |
|---|---|
| Matriz de configuraciones y duraciones (`tasks.md:408`) | ✗ Pendiente |
| Bind mount frente a copia (`tasks.md:409`) | ✗ Pendiente |
| Preflight Ollama/VRAM acreditado para medición (`tasks.md:410`) | ✗ Pendiente |
| Navegador visible y desbordamiento (`tasks.md:411`) | ✗ Pendiente |
| Experimento opcional `torch.compile` (`tasks.md:413`) | ✗ No acreditado; opcional |
| Recomendación con números (`tasks.md:414`) | ✗ Pendiente |

**Gaps anteriores conservados:** B4-02, B4-03, B4-04 y R09-T13 siguen Important; ADR-0059 adoptado no demuestra implementación. Se mantiene formal4→5 y el rebate de T-10.

La evidencia nativa corresponde a procesos/Jobs/lectores reales con fallos controlados y sensores simulados. Conserva sus límites: **268 nacimientos, 235 CLOSED_CONFIRMED y 33 UNKNOWN**; bloqueo físico ReadFile, cierre universal del lector y dos capturas startup siguen sin acreditar. Mi ejecución se limitó a comprobaciones de lectura; no repetí suites ni modifiqué archivos.

## Lente B

**0 Critical · 1 Important · 0 Minor.** El defecto encontrado es un residuo de B4-01/R09-T09, no una regresión introducida.

| Criterio | Resultado | Fichero:línea |
|---|---|---|
| Startup conserva identidad y tipo del error primario, incluso si falla adjuntar la referencia | ✓ | `scripts/eval/benchmark_process.py:330` |
| Error del cuerpo conservado ante cierre y registro fallidos | ✓ | `scripts/eval/benchmark_coordinator.py:100` |
| Error de proof conservado ante cierre fallido del sensor | ✓ | `scripts/eval/benchmark_episode.py:716` |
| Registro secundario nunca sustituye la primera causa en la ruta canónica del episodio | ✗ Important | `scripts/eval/benchmark_episode.py:698` |
| Cierre fallido sin error previo sigue propagándose | ✓ | Tres comprobaciones GREEN de preservación |

**Important — registro canónico sin protección.** Si `canonical.ingest_latest()` falla, `canonical.close()` también falla y `cleanup_error_record()` lanza, este último error sustituye la excepción primaria. Además, no se alcanza el registro de interrupción ni `self.worker.close()`. La ruta todavía llama al registrador sin el guard usado en el cierre del sensor.

Reproducido con el AST actual de `acquire` y dependencias controladas, exclusivamente en memoria: `primary_identity_preserved=false`, `recording_replaced_primary=true`, cero llamadas al cierre del sensor y cero intentos interrumpidos. **No constituye prueba nativa.**

Contrastados argv, UTC y JUnit de los siete RED causales y los GREEN; `final03` acredita 263 PASS. Los seis WHOLE oficiales actuales superan el 80 %, con cero exclusiones; las seis fuentes coinciden con el freeze. No ejecuté suites ni modifiqué archivos.

**B4-01/R09-T09:** corregidas las tres llamadas directas señaladas anteriormente; permanece Important por este fallo de registro previo al cierre del sensor. Los demás gaps de formal4 y el contador formal4→5 permanecen intactos.

## Lente C

**Sin hallazgos de seguridad introducidos o reabiertos.** Nuevos gaps: **0 Critical / 0 Important / 0 Minor**.

Alcance: diff congelado de seis archivos en `integrated-firstcause-inspection1/scope.diff`; hashes y tamaños actuales coinciden con el freeze. Selector C automático: `false`, sin motivos; revisión suplementaria por custodia de recursos nativos.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ Sin nuevos destinos de ejecución con datos externos | `scripts/eval/benchmark_process.py:330` |
| Autenticación, sesión y autorización | ✓ No introduce cambios en credenciales, permisos ni aceptación del protocolo | `scripts/eval/benchmark_episode.py:717` |
| Secretos y exposición de errores | ✓ Registro secundario con tipo limitado a 128 caracteres y digest del primer argumento string, limitado a 4096; no invoca `__str__` | `scripts/eval/benchmark_coordinator.py:23` |
| Deserialización insegura | ✓ No añade deserializadores ni objetos ejecutables recibidos por RPC | `scripts/eval/benchmark_coordinator.py:37` |
| Path traversal y SSRF | ✓ No añade rutas ni destinos de red derivados del error | `scripts/eval/benchmark_episode.py:722` |
| Custodia nativa y cierre | ✓ Conserva referencia al objeto incompleto o mediante traceback; no declara recursos devueltos ante incertidumbre | `scripts/eval/benchmark_process.py:338`, `:349` |
| Preservación de primera causa | ✓ Protege las tres fronteras; sin excepción primaria, el fallo de cierre sigue propagándose | `scripts/eval/benchmark_process.py:330`; `benchmark_episode.py:717`; `benchmark_coordinator.py:100` |

**B4-01 / R09-T09:** corrección respaldada para las tres fronteras delimitadas, pendiente de aceptación del root. No se cierran B4-02/03/04 ni R09-T13, ni se modifica el contador formal.

Evidencia archivada comprobada: siete RED funcionales por sustitución de la excepción primaria; `final03` con **263 PASS**, cero fallos/errores/skips y 13 deseleccionados. Cobertura oficial WHOLE actual de los seis módulos: **80,5169–86,3118 %**, cada uno con cero exclusiones; 267 trazas del run final.

Revisión estática y lectura de evidencias existentes; no ejecuté pruebas nativas. Los fallos son controlados sobre Job/lector reales. `ReadFile` bloqueado, cierre universal del lector y las 33 disposiciones `UNKNOWN` mantienen sus límites declarados.

## Lente D

**Sin hallazgos de rendimiento nuevos: 0 Critical / 0 Important / 0 Minor.**

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| N+1 | ✓ Sin consultas añadidas ni E/S por elemento. | `benchmark_episode.py:716`, `benchmark_process.py:330` |
| Bloqueos síncronos | ✓ Los cambios mantienen una llamada de cierre por frontera; no añaden esperas ni reintentos. El `sleep(0.001)` que activó el selector es preexistente. | `benchmark_process.py:669`, `benchmark_coordinator.py:100` |
| Trabajo repetido evitable | ✓ Un registro por fallo secundario, con mensaje limitado a 4096 caracteres y tipo a 128; no invoca `__str__` arbitrario. | `benchmark_coordinator.py:23`, `benchmark_coordinator.py:37` |
| Complejidad con volumen | ✓ Ningún recorrido nuevo del historial de muestras, recibos o trabajos. El coste añadido por fallo no crece con esos historiales. | `benchmark_episode.py:722`, `benchmark_process.py:344`, `benchmark_coordinator.py:109` |

Se verificó la coincidencia SHA-256/tamaño de las seis fuentes congeladas. Evidencia original examinada: siete RED causales, GREEN dirigido de diez casos y `final03` con **263 PASS**, 13 deseleccionados; cobertura oficial WHOLE de los seis módulos ≥80 %, cero exclusiones.

**B4-01/R09T09:** las tres fronteras delimitadas preservan la primera causa según el código y las pruebas entregadas. Recursos Windows reales con fallos controlados; esta revisión no ejecutó procesos ni pruebas nativas. B4-02/03/04 y R09T13 permanecen pendientes; no se declara aceptación completa de T09.

