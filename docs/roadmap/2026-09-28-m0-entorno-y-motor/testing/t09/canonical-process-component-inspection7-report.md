# Revisión independiente del componente canónico — intento 7

Las cuatro lentes terminaron sin hallazgos. QA independiente actual en curso; no aceptación del benchmark completo.

## Lente A

**Lente A · component-inspection7: 0 Critical / 0 Important / 0 Minor en el delta revisado.** Resultado limitado a `native-protocol-cleanup-fix1`; no acepta T-09 ni sustituye la revisión integrada formal siguiente4.

| Criterio de revisión | Resultado | Evidencia y límite |
|---|---|---|
| 1. Tareas hechas realmente implementadas | ✓ | T-09 continúa `en-progreso`, con sus criterios abiertos: `tasks.md:395,407–413`. El delta no declara completada otra tarea. |
| 2. Alcance y `Archivos` | ✓ | Los dos módulos y el test nuevo pertenecen a `scripts/eval/`, declarado en `tasks.md:401`; autorización causal concreta en `tasks.md:2308`. `scope.json` registra tres archivos dentro del alcance y ninguno fuera. |
| 3. Tests y cobertura vigente | ✓ limitado | Lectura de las aserciones nuevas y del fixture protegido. JUnit original: **253 PASS, 13 deseleccionadas**, exit0. WHOLE oficial por módulo cambiado: runtime **84,38134 %**, process **81,90184 %**, cero exclusiones. |
| 4. Constitución explícita | ✓ | No encuentro una infracción introducida por este delta. Se conserva el estado abierto y no se ejecuta un cierre sin verificación, conforme a `docs/CONSTITUTION.md:33`. No cambia `/v1`, pesos, BD ni infraestructura. |
| 5. Verificación declarada ejecutada | N/A para cierre | La verificación completa de T-09 sigue pendiente (`tasks.md:402–404`). Al no estar cerrada, no corresponde «verificación declarada sin evidencia». No la ejecuté para completar evidencia. |
| 6. Generados y documentación E2/E3 | N/A | El delta no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar el exportador interop. |

**T-09 → criterios de la corrección causal**

| Criterio | Resultado | Fichero:línea |
|---|---|---|
| Admitir únicamente un error autenticado y revocar antes de despertar consumidores | ✓ | [benchmark_canonical_runtime.py:249](<repositorio>/scripts/eval/benchmark_canonical_runtime.py:249); test de estado previo a publicación: `test_benchmark_native_error_cleanup.py:98,157`. |
| Rechazar resultados y progresos posteriores sin reemplazar el error original | ✓ | `benchmark_canonical_runtime.py:253,266`; aserciones de error, progreso y terminales: `test_benchmark_native_error_cleanup.py:127–142`. |
| Separar rechazo lógico de EOF físico | ✓ | [benchmark_process.py:334](<repositorio>/scripts/eval/benchmark_process.py:334). `reader_eof` se establece por lectura vacía; el observador del test delega en la tubería real y comprueba `b""`: `test_benchmark_native_error_cleanup.py:151`. |
| Acotar el drain y conservar el presupuesto original | ✓ por lectura | `benchmark_process.py:339–344`; `benchmark_canonical_runtime.py:268`. Topes de frames/bytes y deadline mínimo; la lectura bloqueante concreta no queda acreditada por estas pruebas. |
| Preservar error, progreso y un único recibo ante cierre concurrente/repetido | ✓ | `benchmark_process.py:533,617,682`; test parametrizado y aserciones de identidad del recibo: `test_benchmark_native_error_cleanup.py:56,158–165`. |
| Mantener negativos preterminales en `UNKNOWN_QUARANTINED` | ✓ | `test_benchmark_native_error_cleanup.py:175–209`: malformed, MAC, replay, cuota, binding y lane; Job vacío no basta para acreditar recursos devueltos. |
| Mantener tests protegidos y RED funcional anterior al código | ✓ | Test original byte exacto SHA `ec70abec…1032c1`; preimagen process `d1d05569…42e8631`. RED original y nuevo: exit1, UTC y argv registrados, fallos de aserción funcionales antes del cambio. |

**T-09 → aceptación completa del plan**

| Criterio del ledger | Resultado |
|---|---|
| Matriz de modelos y duraciones — `tasks.md:407` | ✗ Pendiente; no acreditada por esta unidad |
| Comparación bind mount/copia — `tasks.md:408` | ✗ Pendiente |
| Ollama descargado y VRAM de reposo — `tasks.md:409` | ✗ No acreditado aquí |
| Navegador abierto y observación de spill — `tasks.md:410–411` | ✗ Pendiente |
| Experimento opcional `torch.compile` — `tasks.md:412` | ✗ No acreditado aquí; opcional |
| Recomendación con números — `tasks.md:413` | ✗ Pendiente |

Estas pendientes **no son gaps nuevos del componente**: permanecen abiertas y no se reclama su cumplimiento.

Comprobaciones propias ejecutadas: hashes/tamaños actuales contra freeze, preimágenes archivadas, JUnit y JSON oficial de cobertura; **254 bases —padre y 253 UUID— con SHA exacto, todas de final-baseline3**. No repetí suites. Las ejecuciones anteriores no se combinaron.

Límites conservados: cobertura individual de los dos casos de startup **UNKNOWN**; cierre desde el propio lector y `physicalReadFile_zero_bytes_BLOCKED` **UNTESTED**. Los procesos, Jobs y eventos son nativos; payloads y alteraciones de protocolo son fixtures sintéticos, y los fixtures externos no acreditan hardware.

La expresión «aceptación anterior de cinco fuentes» de `report.md:36` y `receipt.json:114` es **incorrecta como autoridad de aceptación**: `tasks.md:2315` registra expresamente **no aceptación**. Esa cobertura es histórica, y canonicalruntime cambió después. No la he utilizado para conceder aceptación actual.

## Lente B

**Sin defectos de corrección identificados.** Critical: 0 · Important: 0 · Minor: 0.

| Criterio | Fichero:línea | Resultado |
|---|---|---|
| Revocación antes de despertar consumidores; rechazo de respuestas posteriores | `benchmark_canonical_runtime.py:249` | Sin defectos |
| Conservación del error original y progreso | `benchmark_canonical_runtime.py:374` | Sin defectos |
| Drenaje acotado y observación física de EOF | `benchmark_process.py:334` | Sin defectos |
| Cierre concurrente y acreditación conservadora de recursos | `benchmark_process.py:535`, `:682` | Sin defectos |

Revisión estática y cotejo de originales, sin ejecutar suites. Verificados: hashes actuales, test protegido `ec70…`, RED funcional, JUnit final de 253 pruebas y 254 trazas sin discrepancias de hash. Cobertura oficial completa: runtime **84,38 %**, process **81,90 %**, cero exclusiones.

Se mantienen UNKNOWN los dos arranques sin cobertura individual persistida y UNTESTED el cierre desde el lector y `ReadFile` bloqueado. Este resultado corresponde únicamente a **inspection7**; no acepta la integración completa ni cierra T09.

## Lente C

**Sin hallazgos de seguridad en el delta de tres archivos.** Critical: 0 · Important: 0 · Minor: 0.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| Autenticación, sesión y replay | ✓ MAC, binding, secuencia y tipo se validan antes de autorizar el drenaje. | `benchmark_canonical_runtime.py:93`, `:127`, `:249` |
| Revocación y autorización | ✓ Revocación bajo lock antes de despertar consumidores; las respuestas posteriores se rechazan. | `benchmark_canonical_runtime.py:266` |
| Recursos y cierre | ✓ Drenaje limitado; EOF procede de lectura vacía real. Confirmación exige ownership, procesos terminados y lector/writers unidos. | `benchmark_process.py:334`, `:682` |
| Deserialización insegura | ✓ Se mantiene JSON acotado; el diff no incorpora pickle ni ejecución de contenido recibido. | `benchmark_process.py:60`, `:354` |
| Inyección, secretos, traversal y SSRF | ✓ El delta no añade secretos, destinos, rutas ni intérpretes controlados por entradas. | `benchmark_canonical_runtime.py:266`, `benchmark_process.py:334` |

Las tres fuentes actuales coinciden con el freeze; el test protegido conserva SHA `ec70ab…`. Evidencia archivada: RED funcional anterior al cambio y final-baseline3 **253 PASS/13 deselected**, cobertura WHOLE **84,38134 % / 81,90184 %**, cero exclusiones.

Revisión estática y lectura de evidencias; **no ejecuté pruebas**. Permanecen UNKNOWN las dos coberturas individuales de startup y UNTESTED el cierre desde el lector y ReadFile bloqueado. La redacción «accepted five» del recibo no acredita aceptación root. Este resultado no acepta la integración completa ni cierra T-09.

## Lente D

**Sin hallazgos de rendimiento.** Critical: 0 · Important: 0 · Minor: 0.

Alcance: delta de tres archivos de `canonical-process-component-inspection7`, cotejado con las fuentes actuales y sus SHA.

| Criterio | Fichero:línea | Resultado |
|---|---|---|
| N+1 | `benchmark_canonical_runtime.py:273` | Sin consultas; revocación sobre un máximo de dos slots simultáneos. |
| Bloqueos síncronos | `benchmark_process.py:345,537,621,646` | Lectura en hilo dedicado. El `sleep(0.001)` que activó la lente ya existía; el cambio evita esperas y unión del lector consigo mismo. |
| Trabajo repetido | `benchmark_canonical_runtime.py:267` | Serialización adicional una vez por error terminal, sin repetición creciente por historial. |
| Complejidad con volumen | `benchmark_process.py:339` | Drenaje limitado a 66 frames y 17.301.570 bytes; no crece con los 160 jobs de la matriz. |

Evidencia del revisor: inspección estática y lectura de artefactos, sin ejecutar suites. Cobertura oficial archivada: runtime **84,38 %**, process **81,90 %**, cero exclusiones.

El plazo comprobado entre lecturas no acredita interrupción de un `ReadFile` bloqueado; esa trayectoria continúa **UNTESTED**. Este resultado no acepta la integración completa ni cierra T09.