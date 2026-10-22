# Inspección FIRSTcause — intento 3

0 Critical · 0 Important · 0 Minor en el componente acotado. FC02 corregido. QA independiente pendiente; B4-02/03/04 y R09T13CLI siguen abiertos. No cierre de tarea ni transferencia ADR0059 todavía.

## Lente A

**Lente A — componente FIRSTcause, inspección 3: 0 Critical · 0 Important · 0 Minor nuevos.** FC02 corregido en el diff acotado de dos ficheros. Esto no cierra T-09 ni acredita QA independiente.

| T-09 → criterio del componente | Resultado | Evidencia fichero:línea |
|---|---|---|
| Conservar la primaria ante fallo de observación y abort/registro secundarios | ✓ | `scripts/eval/benchmark_canonical_runtime.py:1046`: guarda del registro y relanzamiento con `raise` |
| Conservar la primaria ante fallo después de `begin` real | ✓ | `scripts/eval/benchmark_canonical_runtime.py:1144`: misma protección en publicación |
| Cubrir `none`, `record`, `safe_record`, `storage` en ambas fronteras | ✓ | `scripts/eval/tests/test_benchmark_canonical_integration.py:1419`: ocho parámetros; identidad, tipo y nodo original del traceback comprobados |
| Interrupción antes del rescate y ausencia de resultado positivo | ✓ | `scripts/eval/tests/test_benchmark_canonical_integration.py:1549`: interrupción en memoria, sin recibo, publicación ni posiciones positivas |
| Conservar incertidumbre y propiedad nativa; respetar proceso ajeno | ✓ | `scripts/eval/tests/test_benchmark_canonical_integration.py:1555`: `UNKNOWN_QUARANTINED`, recursos no acreditados como devueltos y testigo extranjero intacto |
| Alcance declarado conforme al plan | ✓ | `tasks.md:401`; `improvement-plan.md:40`: ambos archivos pertenecen al soporte/pruebas de benchmark declarado en `scripts/eval/`. El diff contiene exclusivamente estos dos archivos |
| Principios explícitos de la constitución | ✓ | Sin violación nueva detectada. T-09 permanece abierta conforme a `docs/CONSTITUTION.md:33`; no se cambia el contrato generado de `docs/CONSTITUTION.md:35` |
| Verificación de una tarea cerrada | No aplica | `tasks.md:395`: **en-progreso**. La verificación de `tasks.md:402` sigue pendiente; no se ha ejecutado para suplir evidencia |
| E2/E3: exportación interop | No aplica | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar el exportador |

| T-09 → criterio de aceptación completo | Estado en esta entrega | Referencia |
|---|---|---|
| Matriz de configuraciones y duraciones | ✗ Pendiente | `tasks.md:407` |
| Comparación bind mount/copia y ADR si procede | ✗ Pendiente | `tasks.md:408` |
| Ollama descargado, VRAM previa e informe | ✗ Pendiente | `tasks.md:409` |
| Navegador abierto y observación de desbordamiento | ✗ Pendiente | `tasks.md:410` |
| Experimento opcional `torch.compile` | No acreditado; opcional | `tasks.md:412` |
| Recomendación sustentada en números | ✗ Pendiente | `tasks.md:413` |

Estos pendientes **no son gaps nuevos del componente**: el ledger no declara T-09 completada.

La evidencia original acredita dos RED funcionales anteriores al cambio: `record-observation`, **02:16:47 UTC**, y `record-begin`, **02:16:54 UTC**, ambos exit **1**, un fallo y cero errores de colección. En ambos JUnit, el fallo concreto es que `OSError` del registrador sustituyó a `PrimaryFailure`. El GREEN actual termina con exit **0**, **274 PASS y 13 deseleccionados**; los ocho casos nuevos constan individualmente en JUnit.

Cotejé el JSON oficial de cobertura con el resumen entregado: cobertura **WHOLE de líneas+ramas**, sin exclusiones, por módulo:

| Módulo | Cobertura |
|---|---:|
| `benchmark_canonical_runtime.py` — producción modificada | **85,44 %** |
| `benchmark_canonical_integration.py` | 86,94 % |
| `benchmark_coordinator.py` | 83,74 % |
| `benchmark_episode.py` | 87,08 % |
| `benchmark_process.py` | 81,78 % |
| `benchmark_runtime.py` | 80,52 % |

No es una media ni cobertura de líneas del diff. Verifiqué los hashes actuales contra el freeze y los hashes de las **300 copias RAW**. La ejecución está identificada por UUID `969e87e7-ee7a-4d2b-931b-44a182314c7f`.

**Gaps nuevos: ninguno.** Permanecen abiertos B4-02, B4-03, B4-04 y R09T13CLI, así como QA independiente y transferencia de implementación ADR-0059. Se conserva formal **4 → 5**, componente **2 → 3** y el rebate de T10.

Revisión estática y cotejo de artefactos originales; no ejecuté tests ni procesos nativos. Los fallos son inyectados sobre Jobs/procesos reales; la interrupción comprobada es en memoria, sin acreditar persistencia durable ni resolver los límites nativos declarados.

## Lente B

**Sin defectos nuevos de corrección en el diff acotado de FC02.** 0 Critical · 0 Important · 0 Minor.

| Criterio | Resultado | Fichero:línea |
|---|---|---|
| Conservación de causa primaria ante fallo de abort y registro | ✓ Guarda exterior y `raise` desnudo en ambos manejadores | `benchmark_canonical_runtime.py:1052`, `:1144` |
| Fallos del logger y almacenamiento secundario | ✓ Conservan la primaria; metadata desconocida permanece UNKNOWN | `benchmark_canonical_runtime.py:1057`, `:1149` |
| Identidad, tipo y traceback originales | ✓ Comprobados en los ocho parámetros registrados | `test_benchmark_canonical_integration.py:1424` |
| Interrupción, cierre y ausencia de publicación positiva | ✓ Aserciones antes del rescate; testigo extranjero intacto | `test_benchmark_canonical_integration.py:1557` |

Verificación propia exclusivamente de lectura: hashes actuales coinciden con el freeze; JUnit registra dos RED funcionales previos y **274 PASS**, incluidos los ocho nuevos. Cobertura oficial WHOLE de los seis módulos ≥80 %, cero exclusiones; 300 RAW cotejados byte a byte.

No ejecuté tests ni procesos nativos. Los fallos son inyectados sobre Jobs/procesos reales; la interrupción acreditada es en memoria. B4-02/03/04, R09T13CLI y las limitaciones UNKNOWN previas permanecen abiertos. Este resultado corresponde a componentinspection3, sin aceptación de T09/M0 ni sustitución de QA independiente.

## Lente C

**Sin hallazgos de seguridad.** 0 Critical · 0 Important · 0 Minor.

Alcance: `scope.diff` de `integrated-firstcause-inspection3`, dos ficheros; hashes actuales coinciden con `sources-freeze.json`. Selector C automático: `false`; revisión suplementaria por custodia nativa.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ Sin nuevos destinos de ejecución | `benchmark_canonical_runtime.py:1058`, `:1150` |
| Autenticación y sesión | ✓ El manejo secundario no modifica MAC, epoch ni binding | `benchmark_canonical_runtime.py:1058`, `:1150` |
| Secretos hardcodeados o expuestos | ✓ Registro limitado a tipo, digest y reloj; fallback con `None` | `benchmark_canonical_runtime.py:1061`, `:1153` |
| Deserialización insegura | ✓ No introducida | `benchmark_canonical_runtime.py:1058`, `:1150` |
| Path traversal y SSRF | ✓ Sin rutas ni solicitudes nuevas en producción | `benchmark_canonical_runtime.py:1066`, `:1158` |
| Permisos y autorización | ✓ El fallo de registro no concede autoridad ni publicación positiva | `benchmark_canonical_runtime.py:1053`, `:1145` |
| Custodia y causa primaria | ✓ Abort precede al registro protegido; ambos handlers conservan el `raise` original | `benchmark_canonical_runtime.py:1055`, `:1071`, `:1147`, `:1163` |
| Pruebas añadidas | ✓ Fallos controlados explícitos; comprueban cuarentena y testigo ajeno | `test_benchmark_canonical_integration.py:1419` |

Evidencia del revisor: inspección estática y lectura de artefactos existentes; **sin ejecutar tests ni procesos nativos**. Los JUnit consultados muestran dos RED funcionales y 274 PASS posteriores. Esto no constituye QA independiente, persistencia durable de la interrupción ni aceptación de T09; los gaps previos permanecen abiertos.

