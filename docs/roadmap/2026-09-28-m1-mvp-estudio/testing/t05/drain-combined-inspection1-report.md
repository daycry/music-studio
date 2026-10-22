# Drenaje del worker: revisión del componente

A/B/C/D: 0 Critical, 0 Important, 0 Minor. La revisión estática no sustituye la QA independiente ni cierra T-05. Se conservan los fallos y límites de procedencia anteriores.

## Lente A

**Lente A: sin gaps nuevos — 0 Critical / 0 Important / 0 Minor**, para el diff compuesto de cuatro archivos. **No acredita el cierre de T-05.**

Revisión estática de solo lectura: diff completo contrastado con sus cuatro preimágenes reales; fuentes actuales y copias entregadas coinciden con el freeze por SHA-256.

| Tarea → criterio | Resultado | Evidencia y alcance |
|---|---|---|
| T-05 → ejecutar audio-post/FFmpeg Linux, traslado atómico, assets y manifiesto | ✗ Pendiente de aceptación completa | `docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md:211`. Sigue abierto; esta entrega revisa custodia/drain, no demuestra este CA completo. |
| T-05 → take ready, song.json y análisis beats dependiente | ✗ Pendiente de aceptación completa | `tasks.md:212`. No se declara cumplido mediante estas pruebas nativas. |
| T-05 → limpieza exclusiva del intento acreditado y failed/code | ✗ Pendiente de aceptación completa | `tasks.md:213`. El componente conserva custodia ante transporte inválido; no acredita toda la publicación/limpieza. |
| T-05 → alcance de la unidad | ✓ | `improvement-plan.md:64` contempla custodia nativa; `tasks.md:204` declara worker y tests. Los cuatro archivos corresponden a esa unidad. `scope.json:353`: sin exclusiones de usuario ni avisos. |
| T-05 → validar durante drain sin efectos tardíos | ✓ | `apps/server/app/worker/custody.py:188`: consume el decoder también con `parsing=False`; `_message` queda condicionado por parsing y stop. EOF y errores mantienen el gate cerrado. |
| T-05 → tests del comportamiento modificado | ✓ | `test_worker_native_linux_custody.py:887` y `:1057`; `test_worker_native_custody.py:841` y `:1007`: bytes truncados/schema, frame válido seguido de inválido, cuota, terminal, longitud y ausencia de efectos. Leídos línea a línea. |
| T-05 → backpressure realmente observado | ✓ | `test_worker_native_linux_custody.py:1135`: wrapper delega al `Queue.put` original. Recibo actual: **4 Full reales**, cola **4/4**, `UNKNOWN_QUARANTINED`, release false y owner retenido. Fixture `worker_custody_linux_child.py:148`: cambia exclusivamente el payload; conserva 20 mensajes. |
| T-05 → cobertura actual completa | ✓ | `final/coverage.json`: **custody.py 87,84 %**, cero exclusiones. Backends intactos: Linux **85,89 %**, supervisor **81,65 %**, Windows **88,19 %**. Son métricas oficiales de módulos completos de la pareja actual, sin promedio ni unión histórica. |
| T-05 → TDD del cambio productivo | ✓ Con límite documental | `tasks.md:1658` y `proof-red/junit.xml:1`: RED funcional por `CLOSED_CONFIRMED` frente a `UNKNOWN_QUARANTINED`. La copia productiva RED coincide con la preimagen anterior al fix. Metadata original argv/UTC parcialmente sobrescrita: **no certifico su integridad completa**. Fixture-data declara TDD n/a en `tasks.md:1742`. |
| T-05 → constitución explícita | ✓ | No observo violación de `docs/CONSTITUTION.md:18–20`, `:33` o `:35`: no añade autoridad SQL/publicación, altera contratos públicos ni cierra la tarea sin verificación. |
| T-05 → Verificación de tarea cerrada | ✓ Estado honesto | `tasks.md:198`: **en-progreso**. Las verificaciones de `:207–208` siguen pendientes de cierre; el resultado parcial de 88 casos no las sustituye. No existe aquí una tarea completada sin evidencia que señalar. |
| T-05 → generado/descriptivo E2/E3 | N/a | El diff no toca `commands/`, `agents/` ni `hooks/`; no procede ejecutar `export-interop.py --check`. |

**Evidencia entregada comprobada:** JUnit Linux **42 PASS** y Windows **46 PASS**, sin failures/errors/skips; 87 RAW con hashes y copias previas al combine coincidentes, UUID `266e08e1-cbfa-4cd2-9ee5-d195d3c0cf41`. Los AST de las funciones originales de ambas suites permanecen iguales.

**Comprobaciones ejecutadas por esta lente:** lectura, hashes, comparación íntegra del diff, AST y análisis de artefactos en memoria; exit **0**. No ejecuté suites ni procesos nativos.

**Gaps:** ninguno nuevo. Se conservan el fallo histórico 86/1 y los límites declarados de procedencia/cleanup. La QA dual OS independiente y la aceptación completa de T-05 siguen pendientes (`tasks.md:1772`).

## Lente B

**Sin defectos de corrección identificados en el diff de cuatro ficheros.**

| Criterio | Fichero:línea | Resultado |
|---|---|---|
| Validación durante drenaje, incluidos errores posteriores a un frame válido | `apps/server/app/worker/custody.py:188` | ✓ |
| Supresión de efectos al parar | `apps/server/app/worker/custody.py:192` | ✓ |
| Error persistente y bloqueo de liberación | `apps/server/app/worker/custody.py:271` | ✓ |
| Fronteras del decoder mediante pipes físicos | `apps/server/tests/test_worker_native_linux_custody.py:1051`, `apps/server/tests/test_worker_native_custody.py:1015` | ✓ |
| Saturación observada mediante excepciones `Full` reales | `apps/server/tests/test_worker_native_linux_custody.py:1143` | ✓ |
| Estímulo compacto conserva mensajes y secuencia | `apps/server/tests/fixtures/worker_custody_linux_child.py:148` | ✓ |

Critical: **0** · Important: **0** · Minor: **0**.

Revisión estática de solo lectura; hashes actuales coinciden con el freeze. Evidencia entregada contrastada: Linux **42 PASS**, Windows **46 PASS**, **4 Full** reales y cobertura WHOLE oficial de los cuatro módulos **≥80 %**, con cero exclusiones. Las pruebas de entrega retenida usan intervención controlada sobre bytes de pipes reales.

El RED funcional conservado muestra `CLOSED_CONFIRMED` ante bytes truncados; su metadata original de comandos sigue parcial. No ejecuté tests ni probes nativos. Esta revisión no acredita QA independiente ni cierre de T-05.

## Lente C

**Sin hallazgos.** 0 Critical · 0 Important · 0 Minor en los cuatro archivos de `scope.diff`.

| Criterio | Resultado |
|---|---|
| Inyección, secretos, SSRF y path traversal | ✓ Sin vías introducidas |
| Deserialización de IPC | ✓ JSON acotado; conserva validación de esquema, secuencia, cuotas y EOF |
| Autorización y efectos tardíos | ✓ El drenaje valida sin ejecutar `_message` tras parada |
| Custodia y liberación | ✓ Los errores permanecen impeditivos; `closed` recibido no acredita liberación |

Revisión estática READONLY; los cuatro SHA-256 coinciden con `sources-freeze.json`. No ejecuté código ni pruebas. El resultado se limita al diff congelado y no certifica limpieza nativa ni aceptación de T-05.

## Lente D

**Sin hallazgos de rendimiento.** 0 Critical · 0 Important · 0 Minor.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| N+1 | ✓ El diff no introduce consultas ni accesos repetidos a BD. | `apps/server/app/worker/custody.py:189` |
| Bloqueos síncronos | ✓ El drenaje permanece en el hilo finalizador; después de parar no ejecuta `_message` ni espera capacidad de cola. | `apps/server/app/worker/custody.py:192` |
| Trabajo repetido evitable | ✓ Cada frame drenado se valida mediante el decoder existente; no se introduce reserialización ni reprocesamiento acumulativo. | `apps/server/app/worker/custody.py:189` |
| Crecimiento con volumen | ✓ Validación acotada por sesión: 4 MiB totales, 132 frames y 256 KiB por frame. La fixture conserva 20 mensajes y reduce su payload. | `apps/server/app/worker/pipe_protocol.py:23`; `apps/server/tests/fixtures/worker_custody_linux_child.py:147` |

Alcance: diff compuesto entregado de cuatro ficheros, con los cuatro hashes actuales coincidentes con `sources-freeze.json`. Lente activada por las rutas `worker` de esos ficheros.

Evidencia exclusivamente estática y lectura de artefactos; no ejecuté tests, cargas ni benchmarks. Este resultado no acredita la aceptación completa de T-05.

