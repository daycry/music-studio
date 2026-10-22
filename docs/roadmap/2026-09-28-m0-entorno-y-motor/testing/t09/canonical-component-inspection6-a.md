**Lente A · inspection6: 0 Critical / 0 Important / 0 Minor.** Sin defectos de requisitos o constitución identificados en el diff aislado B5-01/B5-02. Este resultado no acepta T-09 completa.

| T-09 → criterio del componente | Resultado | Evidencia fichero:línea |
|---|---|---|
| B5-01: admitir 64 progresos legales aunque el collector esté detenido | ✓ | `scripts/eval/benchmark_canonical_runtime.py:118`: cuota por secuencia, terminal y fallo reservados. Test `scripts/eval/tests/test_benchmark_canonical_runtime.py:83`: recibe los 64 progresos y terminal antes de liberar collector; ingest concurrente completa. |
| Mantener admisión acotada y validar mensajes antes de encolarlos | ✓ | `benchmark_canonical_runtime.py:127,245,268`: índice, tipo, carril, autenticación y límite de bytes; una petición por carril. Controles en `test_benchmark_canonical_runtime.py:217,260`. |
| B5-02: conservar deadline/fallo original después de progreso MUX | ✓ | `benchmark_canonical_runtime.py:145,352`: adaptación interna `payload → value`; conserva `error.progress` original y `partial_raw`. Test parametrizado `test_benchmark_canonical_runtime.py:162`. |
| Error de cleanup secundario no sustituye al primario | ✓ | `benchmark_canonical_runtime.py:345`: captura separada de cleanup. Test `test_benchmark_canonical_runtime.py:191`. |
| Preservar plazo original, watchdog y aborto del Job propio | ✓ | `benchmark_canonical_runtime.py:266,278,333`; controles anteriores conservados en `test_benchmark_canonical_runtime.py:423,727`. No se renueva el presupuesto. |
| Alcance declarado corresponde a la tarea | ✓ | `docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md:401,2269`: módulos/pruebas de evaluación y corrección aislada autorizada. El diff completo contiene únicamente runtime y su test; `benchmark_process.py` permanece idéntico. |
| Tests y cobertura vigente ≥80 %, sin exclusiones | ✓ | `canonical-process-review5-fix1/official-frozen/stdout.txt:3`: **76 PASS, 1 PDH deselected**, exit 0. JSON oficial: runtime **85,3392 %**, process intacto **81,5832 %**, cero exclusiones; medición completa con líneas y branches, padre e hijos de esta ejecución. |
| RED funcional anterior al cambio | ✓, con reservas conservadas | `canonical-process-review5-fix1/report.md:9,11,13`: logs originales confirman `Full()` y `KeyError('value')` tras deadline/fallo reales, exit 1. El archivo temprano incompleto de imports y UTC de nacimiento sigue expresamente cualificado. |
| Constitución explícita | ✓ | Sin infracción identificada de `docs/CONSTITUTION.md:25,33,35,37`: confinamiento, ledger, contratos y decisiones. |
| Verificación declarada de tarea cerrada | N/A | `tasks.md:395`: T-09 continúa **en-progreso**, sin criterios globales marcados hechos. La suite CPU no acredita la Verificación de `tasks.md:403`. |
| Generados y descripciones E2/E3 | N/A | El diff no toca `commands/`, `agents/` ni `hooks/`; no procede ejecutar el exportador interop. |

| T-09 → criterio de aceptación global | Resultado |
|---|---|
| Matriz de configuraciones y duraciones — `tasks.md:407` | ✗ Pendiente |
| Bind mount frente a copia — `tasks.md:408` | ✗ Pendiente |
| Preflight Ollama/VRAM — `tasks.md:409` | ✗ Pendiente de aceptación global |
| Navegador y observación de desbordamiento — `tasks.md:410` | ✗ Pendiente |
| Experimento opcional `torch.compile` — `tasks.md:412` | ✗ No acreditado |
| Recomendación numérica — `tasks.md:413` | ✗ Pendiente |

Estos pendientes están declarados y no constituyen gaps de la corrección aislada.

**Comprobaciones propias ejecutadas, solo lectura:** 3/3 hashes del freeze coincidentes; 67 protegidos sin diferencias; 16 funciones anteriores del test con AST idéntico; 8.542 copias fuente verificadas; 108 pares launch/cleanup, con 91 `CLOSED_CONFIRMED` y 17 `UNKNOWN_QUARANTINED`. Leí el diff, código, tests y evidencias originales; no repetí suites ni lancé hijos nativos.

El bloqueo físico zero-byte de `CustodyStore.ReadFile` permanece **UNTESTED**. QA independiente, integración formal4, cadencia, matriz160, GPU/calibración y calidad siguen pendientes; se conserva el contador de revisión.