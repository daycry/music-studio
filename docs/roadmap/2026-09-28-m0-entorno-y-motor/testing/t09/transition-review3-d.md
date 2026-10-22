**Lente D — intento 3/3 FINALREGULAR: ✗. Critical: 0 · Important: 1 · Minor: 0.** Contador sin reiniciar; veredictos anteriores conservados. Revisión estática exclusivamente INLINE, sin herramientas ni pruebas propias.

| Criterio de rendimiento | Resultado | Evidencia |
|---|---|---|
| Runtime V3: adquisición, publicación y verificación con deadline original | ✓ | `benchmark_episode.py:548–620`; el trabajo bloqueante reside en el hijo. Los resultados CPU aportados no acreditan sensores GPU actuales. |
| Runtime V3: preparación prolongada con el mismo sampler | ✓ | `benchmark.py:63`, `benchmark_coordinator.py:129`; readiness y operaciones largas permiten muestreo independiente. |
| R09-T07: transporte incremental sin retransmitir el historial verificado | ✓ | `benchmark_coordinator.py:443–501`, `benchmark_audit.py:166–177`. Segmentos nuevos, vista sin copia del prefijo y consulta acotada cuando no cambia. |
| Validación incremental compatible con el volumen previsto | ✗ | D-04: cada segmento vuelve a validar todos los originales del prefijo. |
| Esperas seleccionadas por `sleep-bloqueante` | ✓ | No identifico un defecto adicional de rendimiento en la ruta V3: la espera de readiness no detiene el sampler. |
| Fronteras legacy V1/V2 | ✗ | Persisten los escenarios históricos D-01/D-02 en entradas Python inyectadas; la CLI automática normal los bloquea en `benchmark.py:671–675`. |

| ID | Gravedad | Fichero:línea | Escenario concreto y orden de magnitud |
|---|---|---|---|
| **D-04 — Revalidación completa repetida por cada segmento nuevo** | **Important** | `scripts/eval/benchmark_runtime.py:685`; `scripts/eval/benchmark_audit.py:173`; `scripts/eval/benchmark_coordinator.py:465` | Una matriz permitida de **160 jobs de 300 s de pared**, con cadencia nominal de 1 s, acumula aproximadamente **48.000 episodios**, sin contar preparación ni auditorías. Los segmentos contienen como máximo **32 intentos** y cada commit invoca `read_publications` sobre **todo el prefijo**. Incluso agrupando óptimamente, son 1.500 validaciones de tamaños 32, 64…48.000: **36.024.000 visitas a episodios**, unas **750,5 veces** una lectura completa final. Cada visita relee request, commit, prepared, RAW y todos sus progresos, además de reconstruir y validar relojes/contexto. Con un RAW y un progreso por episodio son ya **≥216 millones de lecturas JSON**, frente a ≥288.000 para una pasada. Segmentos menores aumentan la repetición. |

El efecto es trabajo CPU/disco acumulativo evitable durante una sesión cuyo historial sigue creciendo. Además, `refresh_accreditation` vuelve a recorrerlo mediante `validate_auto` (`benchmark_runtime.py:1063`), y cada fila lo hace mediante `accepted_samples` (`benchmark_runner.py:394`). Estas pasadas refuerzan el mismo hallazgo; no las cuento como defectos separados.

**No afirmo un timeout demostrado:** cada commit dispone de 3.600 s y el sampler continúa independientemente. El deadline de 2 s pertenece al episodio; aislar la auditoría preserva esa frontera, pero no elimina su coste ni acredita que la validación creciente termine dentro de su propio plazo. Los **18,89 s** aportados usan un validador sintético que inspecciona únicamente el segmento (`test_benchmark_audit_delta.py:318–323`); no miden este recorrido canónico.

La corrección debe reducir las revalidaciones repetidas conservando la comprobación de bytes originales, contexto, ownership y anclas independientes, con invalidación ante cambios; la lectura canónica completa final debe mantenerse. Una aprobación cacheada sin esas garantías no resuelve el hallazgo.

R09-T03–T06 no presentan un hallazgo adicional de rendimiento identificado; su aceptación funcional corresponde a A/B. R09-T07 corrige el defecto histórico de **transporte**, pero deja D-04 en **validación**. Los cinco RED técnicos V2 siguen siendo defectos reales alcanzables por inyección Python, sin convertirlos en fallos del runtime V3 ni borrarlos del historial.

CPU6 permanece **469 PASS / 6 FAIL / 5 exclusiones explícitas**. El finisher con exit 0 no certifica el CLI original ni su limpieza histórica. Esta revisión no acepta QA, calibración, matriz GPU160 ni cierre de T-09/M0.