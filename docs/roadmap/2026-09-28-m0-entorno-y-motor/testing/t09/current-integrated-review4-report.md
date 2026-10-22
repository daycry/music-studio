# Revisión integrada — intento 4

**0 Critical · 5 Important · 0 Minor**, fusionados sin duplicar A/B/D. Cuatro defectos del corte actual; R09-T13 permanece en la CLI anterior y se resolverá con su migración. Rebate T10 y contador formal3 conservados. No aceptación de T09/M0.

C es suplementaria por instrucción raíz sobre custodia, capabilities y fuentes; el selector automático C=false se conserva. Su frase «petición explícita» se refiere al prompt raíz, no a una solicitud directa del propietario de esa lente.

## Lente A

**Lente A — revisión integrada, intento 4: ✗. 0 Critical · 2 Important · 0 Minor.** Se conserva la revisión formal 3 y el rebate de R09-T10. Uno de los Important afecta al corte actual; el otro permanece en la ruta legacy pendiente de migración.

Revisión estática, sin ejecutar tests, procesos de producto ni probes. Leídos los seis módulos completos y los siete tests originales; comprobado en memoria que `scope.diff` reproduce exactamente esos seis archivos contra el HEAD explícito `8663287…`. Cotejo de las 80 entradas fuente/contexto con sus copias archivadas: **0 discrepancias**. No se modificaron archivos ni ledger.

| T-09 → criterio de aceptación del ledger | ✓/✗ | Resultado |
|---|---|---|
| Matriz de configuraciones y duraciones | ✗ pendiente | Se conserva la planificación de 160 jobs; esta evidencia CPU no demuestra su ejecución completa. |
| Comparación bind/copia y ADR si diferencia >30 s | ✗ pendiente | Existen preparación y pruebas CPU; faltan los números reales de la comparación. |
| Ollama descargado y VRAM en reposo ≤~1,6 GB antes de medir | ✗ pendiente | Los dobles CPU no acreditan este preflight actual. |
| Navegador abierto y registro de desbordamiento | ✗ pendiente | La integración conserva validadores y confianza limitada; no acredita observación GPU actual. |
| Experimento opcional `torch.compile` | N/A | No exigible para aceptar este corte. |
| Recomendación argumentada con números | ✗ pendiente | No acreditada por esta medición. |

Estos pendientes están declarados honestamente: **no son gaps nuevos del alcance parcial ni tareas cerradas indebidamente**.

| T-09 → criterio del corte integrado | ✓/✗ | Código y test leído |
|---|---|---|
| Un sampler ingresa la finalización real sin pasar por el worker largo | ✓ | `benchmark_episode.py:593`; `test_benchmark_canonical_integration.py:141,1151`: status independiente y noveno ingreso durante ocho witnesses. |
| Captura/transición/commit exclusivamente canónicos; arrays del supervisor como evidencia | ✓ | `benchmark_canonical_runtime.py:805`; ancla privada derivada de `_last_completion`, antes de captura. Test `:55` exige confirmación previa a aceptación. |
| Accepted/rejected/interrupted distintos y revocación del head positivo | ✓ | `benchmark_episode.py:577,701`; tests `:75,311,342,1251` comprueban rechazo, interrupción, EOF y conservación de RAW. |
| Status/base tipados, identidad privada, consumidor y solicitud propios | ✓ | `benchmark_canonical_integration.py:272,295`; test `:182` rechaza copia, consumidor ajeno y reutilización. |
| Acreditación fresca y autoridad del snapshot seleccionado | ✓ | `benchmark_canonical_runtime.py:953`; `CanonicalState.finish_accredit` vuelve a validar con reloj actual. Los tests permiten snapshot cursor8 mientras ingresa cursor9; no lo presentan como head9. |
| Consumidores no migrados cerrados antes de efectos | ✓ | Guards del runtime/provider; test `:254` recorre acciones directas y `args_begin/fragment/execute`. Constructor integrado descarta bootstrap legacy (`:593`). |
| Contexto, epoch, ownership y fuentes ligados a objetos propios | ✓ acotado | `create_session:116`, `canonical_for_runtime:227`; tests `:864,1087` revocan ante configuración cambiada y sustitución de worker. `expected_sources` procede del supervisor confiado; un hash JSON no instala la asociación privada. |
| Deadline original del episodio y lectura con presupuesto independiente | ✓ acotado | Ingreso conserva `start+2s`; mux arma watchdog antes del envío. Los tests de bloqueos CPU/eventos nativos no prueban bloqueo físico de `ReadFile`. |
| Primera causa conservada en todas las fronteras | ✗ | Residuo R09-T09 detallado abajo. |
| Delta sin revalidación semántica completa del prefijo | ✓ canónico / ✗ legacy | `CanonicalState.propose` valida el episodio nuevo; los witnesses siguen siendo O(historia), permitido por ADR-0050. `BenchmarkOperationProvider.validate_delta` todavía relee todo el prefijo. |
| Alcance declarado en `Archivos` | ✓ | Los seis módulos y tests pertenecen a `scripts/eval/`, declarado en `tasks.md:400`. Scope capturado: sin archivos fuera de alcance, avisos ni exclusiones de usuario. Ownership del productor sigue siendo `[]`. |
| Constitución explícita | ✓ | No identifico infracción constitucional introducida. Los gaps siguientes se fundamentan en requisitos de recuperación/integración, no en principios inventados. |
| Verificación de tareas cerradas | ✓ | T-09 sigue `en-progreso` (`tasks.md:394`). No se afirma ejecutada su verificación final; no la ejecuté para suplir evidencia. |
| Generados E2/interop y descripciones E3 | N/A / ✓ acotado | El diff no toca `commands/`, `agents/` ni `hooks/`: no corresponde ejecutar exportador. ADR-0050 y el handoff describen explícitamente el corte opt-in y la CLI pendiente. |

La evidencia del productor es **253 PASS, 13 deseleccionados declarados, exit0**, UUID único `52335119-ae2b-43fc-be99-231fdc9a8cf3`, 254 trazas crudas. Cobertura WHOLE oficial de líneas+ramas, cero exclusiones:

| Módulo | Cobertura |
|---|---:|
| canonical_integration | 86,1940 % |
| canonical_runtime | 84,3813 % |
| coordinator | 82,8306 % |
| episode | 86,5125 % |
| process | 81,9018 % |
| runtime | 80,5169 % |

**Cumple el gate de los seis módulos.** No es un resultado nuevo de `coverage-gate --changed-only`, ni sustituye la lectura de los tests, ni constituye QA independiente.

| Gap previo | Estado CURRENT | Evidencia y límite |
|---|---|---|
| R09-T08 — frontera Python legacy | **Corregido estáticamente** | `benchmark.py:734` y `benchmark_observation.py:1300` rechazan V1/V2 antes de usar proveedores inyectados. No reabro los RED históricos como defectos actuales. |
| R09-T09 — FIRSTcause | **Sigue Important** | `run_owned:225` protege el cleanup, pero persisten otras fronteras sin esa protección. |
| R09-T10 — overflow de renovación | **Rebatido, preservado** | [Prueba de crecimiento](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/growth-functional-probe-report.md): historial323.202 bytes, dos renovaciones21.138/prerequisites21.694. Sin evidencia nueva que autorice reabrirlo. |
| R09-T11 — cleanup de inicialización | **Corregido para el escenario previo** | Binding escrito dentro del `try`, `benchmark.py:303,309`; constructor del coordinador protegido. Test de nacimiento parcial `test_benchmark_canonical_integration.py:827`. No equivale a limpieza universal confirmada. |
| R09-T12 — ACK de lease | **Corregido estáticamente, evidencia CPU acotada** | Intent antes del RPC (`benchmark.py:328`); lease nace en cuarentena (`benchmark_runtime.py:823`); recuperación distingue absent/foreign/identity/owned (`:1231`). Test `:1007` conserva reserva propia y no toca ajena. |
| R09-T13 — coste de validar historial | **Corregido en canónico; sigue Important en legacy** | `CanonicalState.propose` sólo valida delta; `benchmark_runtime.py:722` aún llama `read_publications` con el prefijo completo. La CLI actual sigue montando ese provider (`benchmark.py:319`). |

| ID | Gravedad | Fichero:línea | Trigger concreto → impacto |
|---|---|---|---|
| **R09-T09, residuo integrado** | **Important** | `scripts/eval/benchmark_episode.py:716`; `scripts/eval/benchmark_process.py:331`; `scripts/eval/benchmark_coordinator.py:85` | Una verificación de proof falla mientras el sensor sigue vivo y su cierre también lanza: `worker.close` sustituye `failure` antes de `raise failure`. Igualmente, un error de startup seguido de cleanup fallido o un error del cuerpo seguido de cierre fallido pierde la excepción primaria. Incumple conservación del error original de **ADR-0045:10** y el cierre preservando causa del handoff. Los tests de cleanup del mux no cubren estas fronteras. |
| **R09-T13, obligación previa pendiente** | **Important** | `scripts/eval/benchmark_runtime.py:722`; `scripts/eval/benchmark_audit.py:173` | Cada segmento legacy nuevo valida `snapshot["receipts"]` completo mediante `read_publications`: vuelve a abrir originales anteriores. El crecimiento mantiene el coste acumulativo probado anteriormente; no afirmo timeout nuevo. El corte canónico evita esa ruta, pero la CLI aún la utiliza. **No es un defecto nuevo del corte opt-in ni exige activar ahora la CLI; impide cerrar globalmente este gap previo.** |

Custodia: **255 nacimientos, 232 CLOSED_CONFIRMED y 23 UNKNOWN_QUARANTINED**. Dos startups carecen de traza individual persistida; stderr de hijos DEVNULL y RPC completo permanecen UNKNOWN. El incidente del helper de entrega es metadata privado, sin repetición de suite ni RED causal. No infiero `finally` tras muerte ni devolución de recursos a partir de Job vacío solamente.

**No se acepta globalmente T-09/M0.** Permanecen pendientes QA integrada independiente, migración CLI, FINAL/packs/restore, calibración, GPU160 y cadencia13h.

## Lente B

**Lente B — revisión integrada, intento 4: ✗. 0 Critical · 4 Important · 0 Minor.** Contador formal 3 y rebate de R09-T10 conservados.

Revisión estática, sin pruebas ejecutadas ni probes. Leídas las seis fuentes completas, los siete tests originales y el contexto transitivo pertinente del archivo de medición. Comprobado en memoria que los seis bloques completos de `scope.diff` coinciden con las fuentes actuales y sus SHA congelados.

| Criterio | Resultado | Evidencia |
|---|---|---|
| Provider/coordinador reales; consumidores pendientes cerrados antes de efectos | ✓ | `benchmark_canonical_integration.py:333,350,373`; `benchmark_runtime.py:743` |
| Accepted/rejected/interrupted; publicación tras confirmación y deadline original | ✓ | `benchmark_episode.py:563,604`; `benchmark_canonical_runtime.py:1047,1070` |
| Revocación terminal, identidad/epoch, acreditación fresca y snapshot seleccionado | ✓ | `benchmark_canonical_runtime.py:248,936`; contexto transitivo `benchmark_canonical.py:669,774,803` |
| Preservación de primera causa en toda la integración | ✗ | B4-01 |
| Plazo completo de lectura independiente | ✗ | B4-02 |
| Presupuesto total de bootstrap compartido | ✗ | B4-03 |
| Contexto canónico ligado al plan del worker operativo | ✗ | B4-04 |
| Custodia UNKNOWN distinguida de cierre confirmado | ✓ | `benchmark_process.py:694`; las 23 disposiciones UNKNOWN permanecen desconocidas |

| Gap | Gravedad | Fichero:línea | Trigger concreto e impacto |
|---|---|---|---|
| **B4-01 — Cleanup del sensor sustituye la primera causa** | **Important** | `scripts/eval/benchmark_episode.py:716` | El sensor devuelve correctamente; después falla captura/publicación canónica o verificación del padre. El bloque conserva `failure`, pero llama sin protección a `self.worker.close(graceful=False)`. Si ese cierre lanza, por ejemplo por enumeración de miembros o lector no unido, nunca alcanza `raise failure`: el coordinador recibe el error secundario como causa primaria. El registro de interrupción conserva parte de la evidencia, pero la propagación y recuperación identifican la causa equivocada. |
| **B4-02 — Las comprobaciones de fuentes quedan fuera del plazo de lectura** | **Important** | `scripts/eval/benchmark_canonical_integration.py:273,282,284` | `session.read(timeout_s=…)` relee y calcula hashes mediante `canonical_for_runtime` **antes** de crear el deadline. Después del RPC vuelve a realizar esas lecturas sin comprobar el plazo original. Una lectura lenta de fuentes/configuración puede consumir el presupuesto entero y aun así devolver éxito posteriormente; si bloquea, el watchdog del RPC no cubre ese trabajo del supervisor. |
| **B4-03 — El arranque canónico recibe un presupuesto nuevo de cinco segundos** | **Important** | `scripts/eval/benchmark_canonical_integration.py:172–176`; `scripts/eval/benchmark_canonical_runtime.py:1030` | Con `startup_timeout_s=1` y el sensor ya arrancado, `remaining()` comprueba el restante, pero su valor no se transmite a `CanonicalChannel`. Este crea su `OwnedProcess` con el default de cinco segundos. Si el bootstrap canónico tarda tres segundos, la factoría sólo detecta el vencimiento después de ese arranque. Falla cerrado finalmente, pero incumple la cota total declarada. `coordinator.__enter__()` también usa su plazo independiente de 2,5 segundos. |
| **B4-04 — Se admite una sesión con contexto A y plan operativo B** | **Important** | `scripts/eval/benchmark_canonical_integration.py:148–154,181,204` | Proporcionar un contexto válido de sesión A y un `operation_config` con plan/owner coherentes de sesión B supera el montaje: se congelan los tres ficheros, pero nunca se comparan sus identidades. El provider sólo compara owner con su plan (`benchmark_runtime.py:663`); el integrado elimina el antiguo audit binding. Así, el mismo `RuntimeChannel` devuelve status/base acreditados de A mientras sus operaciones permitidas actúan con B. Los tests usan configuraciones mínimas independientes y no verifican el rechazo de esta combinación. |

| Gap formal previo | Estado CURRENT | Evidencia y escenario |
|---|---|---|
| **R09-T08 — Python legacy** | **Corregido** | `benchmark.py:719`: V1/V2 se rechazan también con `observer_factory`, antes de backend/API. |
| **R09-T09 — FIRST cause** | **Still Important** | El escenario original de `run_owned` está corregido en `benchmark_coordinator.py:244`; B4-01 demuestra otra frontera actual que todavía sustituye la primera causa. |
| **R09-T10 — Renovación/256 KiB** | **Rebatido** | Se conserva `growth-functional-probe-report.md`: historial de 323.202 bytes, respuestas/referencias acotadas y dos renovaciones reales. Sin evidencia nueva para reabrirlo. |
| **R09-T11 — Init cleanup** | **Corregido** | `benchmark.py:295`: escritura del binding dentro del `try/finally`. `create_session:194` recoge fallos parciales y conserva la causa original. B4-03 es un defecto distinto de presupuesto. |
| **R09-T12 — ACK lease/cuarentena** | **Corregido, escenario acotado** | `benchmark.py:332`; `benchmark_runtime.py:828,1230`: intención previa, reserva inicialmente quarantined y reconciliación del ACK incierto sin replay. No implica custodia confirmada de los nacimientos UNKNOWN. |
| **R09-T13 — Validación histórica** | **Corregido en ingreso integrado; Still Important en ruta legacy vigente** | El ingreso integrado aplica transición al delta; la acreditación conserva witnesses O(historia) de cero payload conforme a ADR-0050. `benchmark_runtime.py:722` sigue revalidando el prefijo completo en legacy. Se preserva el hallazgo previo de D; no infiero un timeout nuevo ni lo cuento entre los cuatro defectos B. |

La medición **253 PASS, 13 deseleccionados y seis WHOLE ≥80 %, cero exclusiones**, acredita ese gate de cobertura, no aceptación integrada. Conserva **255 nacimientos: 232 CLOSED_CONFIRMED y 23 UNKNOWN_QUARANTINED**, dos startups sin traza individual, stderr DEVNULL y RPC completo no archivado. Los incidentes del helper no son RED de producto.

CLI integrado, tickets materiales, FINAL/packs, restore, bloqueo físico de ReadFile, reader-close, GPU160, calibración, cadencia13h y cierre T09/M0 siguen pendientes declarados; no los convierto en defectos de este corte.

## Lente C

**Lente C — revisión formal integrada, intento 4: sin hallazgos de seguridad.** Critical **0**, Important **0**, Minor **0** de esta lente. Esto **no acepta la integración completa** ni cierra los gaps funcionales anteriores.

Revisados los seis ficheros productivos completos, su diff acumulativo contra `8663287cf9f3fb0d4f06263fa4a6fc0d18bdec77`, los siete tests originales archivados y el contexto transitivo pertinente. Las seis fuentes coinciden con el freeze; el diff reproduce íntegramente sus contenidos y los siete tests coinciden byteexactamente con los actuales. Ownership de la medición: `[]`.

El selector registra `lente_c=false`, `motivos=[]`; C se ejecuta por tu petición explícita. Contador anterior preservado.

| Criterio de seguridad | Resultado y evidencia |
|---|---|
| Inyección SQL/comando/plantilla | ✓ No identifico una ruta explotable introducida. Los comandos usan listas de argumentos; no aparecen SQL concatenado, plantillas ejecutables ni `shell=True`. |
| Secretos | ✓ Token obtenido de configuración/`.env`, sin secreto hardcodeado; Docker recibe el token mediante entorno, no argv (`benchmark_runtime.py:215`). La clave IPC se genera por sesión. |
| Autenticación y replay IPC | ✓ MAC, epoch, binding, carril, secuencia y cuota preceden a admisión (`benchmark_canonical_runtime.py:93`, `:250`). |
| Revocación terminal | ✓ El error autenticado revoca antes de despertar al consumidor; el tail posterior queda rechazado (`benchmark_canonical_runtime.py:266`). Revocación lógica y EOF físico permanecen separados. |
| Fuente confiada frente a hash del caller | ✓ El inventario se contrasta con configuración confiada del supervisor (`benchmark_canonical_integration.py:17`, `:43`); la factoría canónica ejecuta los bytes sellados (`benchmark_canonical_runtime.py:60`). Un hash RPC no concede autoridad. |
| Procedencia, contexto y publicación | ✓ El ingreso parte de `_last_completion` privado real; captura, commit y publicación conservan el deadline original (`benchmark_canonical_runtime.py:1064`). La aceptación del acquirer sucede después de confirmación (`benchmark_episode.py:607`). |
| Capabilities y acreditación fresca | ✓ Se comprueba identidad privada, request y consumidor; consumir solicita acreditación nueva (`benchmark_canonical_integration.py:295`). Los witnesses y la validación de frescura pertenecen al snapshot seleccionado (`benchmark_canonical_runtime.py:953`). |
| Consumidores pendientes | ✓ Las rutas de auditoría/certificación no migradas quedan bloqueadas antes de progreso o efectos, también mediante argumentos fragmentados (`benchmark_canonical_integration.py:344`, `:354`). |
| Path traversal y deserialización | ✓ Rutas confinadas, nombres originales cerrados y custodia nativa; JSON acotado, sin pickle ni selección de código mediante RPC (`benchmark_episode.py:51`; `benchmark_canonical_runtime.py:900`; `benchmark_process.py:60`). |
| SSRF y autorización de recursos | ✓ HTTP conecta a loopback; limpieza exige ID y labels propios (`benchmark_runtime.py:75`, `:628`). No identifico bypass introducido. |

No hay escenario de explotación sustentado que justifique asignar un CWE.

El arrastre de **formal3** queda así; sus grados funcionales no se cuentan como hallazgos C:

| Gap previo | Estado actual | Escenario y evidencia |
|---|---|---|
| **R09-T08** — frontera Python legacy | **Corregido, estáticamente** | `run_session` rechaza V1/V2 incluso con `observer_factory` (`benchmark.py:734`); `acquire_sample` también los bloquea (`benchmark_observation.py:1294`). Se cierra la entrada inyectada anterior. |
| **R09-T09** — FIRSTcause | **StillImportant en inicialización; escenario original corregido** | `run_owned` conserva el error primario y registra cleanup aparte (`benchmark_coordinator.py:227`). Pero si startup falla y su cierre también lanza, el constructor sustituye la excepción original mediante `self.close()` (`benchmark_process.py:330`). La factoría integrada recibe esa segunda causa. Es arrastre de robustez, sin explotación de seguridad demostrada. |
| **R09-T10** — supuesto overflow de renovación | **Descartado — rebatido** | Se conserva [la contraprueba de crecimiento](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/growth-functional-probe-report.md): historial de 323.202 bytes, renovaciones válidas e interfaces acotadas. Sin evidencia nueva para reabrirlo. |
| **R09-T11** — cleanup de inicialización | **Corregido en el escenario anterior y montaje acotado; devolución completa UNKNOWN** | La escritura del binding está dentro del `try` (`benchmark.py:303`); el montaje integrado cierra recursos nacidos ante fallo parcial (`benchmark_canonical_integration.py:164`, `:194`). Esto no convierte cierres desconocidos en confirmados. |
| **R09-T12** — ACK lease/cuarentena | **Corregido en la ruta acotada; prueba completa UNKNOWN** | La intención precede a adquisición; el hijo reserva cuarentena y recuperación distingue identidad propia, ajena o desconocida sin replay (`benchmark_runtime.py:815`, `:1231`). No infiero reconciliación física completa del daemon. |
| **R09-T13** — revalidación del historial | **StillImportant en CLI legacy; corregido para ingreso canónico opt-in** | `validate_delta` todavía recorre el prefijo completo (`benchmark_runtime.py:722`). El modo integrado valida el delta mediante transición común; la acreditación mantiene witnesses O(historia) de cero payload. La activación del CLI sigue pendiente explícitamente. |

**Límites conservados:** productor 253 PASS, 13 deseleccionados, seis WHOLE ≥80 %, cero exclusiones y 254 trazas del mismo UUID; no es QA independiente. Los 255 nacimientos incluyen **232 CLOSED_CONFIRMED y 23 UNKNOWN_QUARANTINED**. Dos trazas de startup, stderr hijo DEVNULL y RPC completo siguen UNKNOWN. Los incidentes privados de entrega no constituyen RED de producto.

Sólo lectura estática y comprobaciones en memoria de texto, SHA-256 e inventarios. Sin pruebas nuevas, procesos de producto, escrituras ni mutaciones Git. No se acredita bloqueo físico de ReadFile, reader-close, CLI, GPU, 160 jobs, calibración, cadencia de 13 h, FINAL/packs, restore, audio ni cierre T09/M0.

## Lente D

**Lente D — revisión integrada, intento 4: ✗. 0 Critical · 1 Important pendiente · 0 Minor.** No identifico nuevos defectos de rendimiento en la integración canónica acotada. **R09-T13 sigue alcanzable en la ruta live utilizada por la CLI.**

Revisión estática de los seis módulos completos, el diff acumulativo contra la referencia explícita, los siete tests originales archivados y su contexto transitivo pertinente. Conservé los veredictos anteriores y el rebate de T10. No ejecuté tests ni modifiqué archivos; las comprobaciones adicionales fueron comparaciones de bytes, hashes y contenido en memoria.

| Criterio | Resultado | Evidencia |
|---|---|---|
| Transporte incremental con referencias acotadas | ✓ | No aparece nueva evidencia que reabra T10. |
| Ingesta canónica sin revalidar el payload histórico | ✓ | `benchmark_canonical_runtime.py:953`: lectura mediante witnesses; la validación del episodio nuevo permanece separada. |
| Coste del prefijo canónico | ✓ | Recorrido de identidad **O(historial)** declarado por ADR-0050. No lo confundo con releer todos los originales. |
| Esperas y E/S aisladas del sampler | ✓ | No identifico un bloqueo adicional con escenario de carga demostrable. |
| Validación delta en la ruta live existente | ✗ | `benchmark_runtime.py:722` entrega el prefijo completo a `read_publications` en cada commit. |
| Evidencia suficiente para aceptación integral | UNKNOWN | La cobertura acredita ejecución CPU; no acredita carga prolongada, limpieza universal ni los gates funcionales pendientes. |

| Hallazgo | Gravedad | Fichero:línea | Carga concreta e impacto |
|---|---|---|---|
| **R09-T13 — revalidación histórica repetida por segmento** | **Important** | `scripts/eval/benchmark_runtime.py:699`, especialmente **`:722`**; `scripts/eval/benchmark_coordinator.py:530`; `scripts/eval/benchmark_audit.py:173` | Con **160 jobs de 300 s**, muestreo nominal de **1 Hz**, se acumulan aproximadamente **48.000 episodios**. Con segmentos de hasta **32 intentos**, cada commit revalida tamaños 32, 64…48.000: **36.024.000 visitas**, frente a 48.000 en una pasada, **750,5 veces**. Repite lectura y validación de originales ya comprobados. |

La accesibilidad es actual: `benchmark.py:320` sigue seleccionando `BenchmarkOperationProvider`; el test archivado `test_real_legacy_runtime_delta_and_integrated_internal_reads` ejercita esa ruta real. La fábrica canónica optativa mejora su propia frontera, pero todavía no sustituye la ruta CLI. Esto mantiene un defecto previo alcanzable; no convierte los demás trabajos declarados pendientes en defectos de una entrega parcial.

El probe histórico conserva evidencia de crecimiento: añadir un episodio provocaba **70/140 lecturas históricas** con prefijos de 10/20. No lo presento como una medición nueva. Tampoco afirmo un timeout demostrado. Corrijo la estimación anterior de lecturas JSON: el orden de magnitud sustentado aquí es el de **visitas a episodios**, sin reutilizar la cifra previa de 216 millones.

| Gap previo | Estado actual | Escenario y evidencia |
|---|---|---|
| **R09-T08 — frontera Python legacy** | **Corregido en el escenario previo** | Una llamada Python V1/V2 inyectada encuentra rechazo explícito en `benchmark.py:735`, `benchmark_observation.py:1295` y `benchmark_runner.py:106`. No reabro código histórico situado después del rechazo. |
| **R09-T09 — FIRST cause** | **Corregido en el escenario previo** | Si falla el trabajo y también su limpieza, `benchmark_coordinator.py:230` registra el error secundario conservando la excepción primaria; la integración aplica la misma protección en `benchmark_canonical_integration.py:198`. No equivale a aceptar todas las rutas funcionales de limpieza. |
| **R09-T10 — overflow de renovación** | **Rebatido; rebate conservado** | La renovación utiliza referencias acotadas. No hay prueba nueva concreta de overflow ni fundamento para inventar un RED. |
| **R09-T11 — limpieza de inicialización** | **Corregido en el escenario previo; cierre universal UNKNOWN** | La construcción del binding está dentro del `try` desde `benchmark.py:303`. La fábrica protege sus nacimientos en `benchmark_canonical_integration.py:194`. Esto no demuestra cierre de los nacimientos archivados UNKNOWN. |
| **R09-T12 — ACK de lease / cuarentena** | **Corregido en el escenario previo; custodia completa UNKNOWN** | Ante pérdida del ACK, se persiste intención antes de adquirir (`benchmark.py:336`); el runtime establece `lease_ack_unknown` y cuarentena (`benchmark_runtime.py:829`), y recuperación consulta la intención (`:1231`). No infiero liberación o cierre confirmado a partir de esos estados. |
| **R09-T13 — coste de validación histórica** | **Sigue Important** | Corregido para el payload histórico de la frontera canónica acotada; pendiente en la ruta live descrita arriba. |

La medición archivada acredita **253 PASS, 13 deselecciones CPU declaradas**, cobertura oficial superior al 80 % en cada módulo completo y cero líneas excluidas. Es evidencia del productor, **no QA final**.

Los nacimientos registrados son **255: 232 CLOSED_CONFIRMED y 23 UNKNOWN_QUARANTINED**. Las dos startups de cobertura, stderr del hijo y ausencia del RPC completo mantienen sus límites de observabilidad. No doy por probados `finally` después de muerte, cierre del reader, bloqueo físico de `ReadFile`, matriz GPU160, sesión de 13 horas ni cierre de T09/M0.

