**Lente A — componente inspection5: 0 Critical / 0 Important / 0 Minor.** Sin defectos de requisitos o constitución identificados en los cuatro ficheros revisados. Este resultado no acepta T-09 completa ni sustituye su QA independiente.

| T-09 → criterio del componente | Resultado | Evidencia fichero:línea |
|---|---|---|
| Bootstrap ligado a supervisor, sensor y nacimiento canónico; autenticación antes del provider | ✓ | `benchmark_canonical_runtime.py:93,156,446,580,880`; controles en `test_benchmark_canonical_runtime.py:355,550` |
| Dos carriles acotados; ingreso prioritario entre witnesses; scheduler único | ✓ | `benchmark_canonical_runtime.py:332,436,623,838`; pruebas `test_benchmark_canonical_runtime.py:68,250,517` |
| Ingreso y publicación consumen el plazo original; commit tentativo no habilita vistas | ✓ | `benchmark_canonical_runtime.py:629,642,838,934`; controles de rechazo en `test_benchmark_canonical_runtime.py:458,615` |
| Watchdog armado antes del envío; abort del Job propio; devolución condicionada a cleanup comprobado | ✓ | `benchmark_canonical_runtime.py:227,239`; `benchmark_process.py:476,653`; pruebas `test_benchmark_canonical_runtime.py:101,405,684` |
| Status/base usan validators actuales; resolución de posición únicamente por identidad | ✓ | `benchmark_canonical_runtime.py:838,1010,1033`; pruebas `test_benchmark_canonical_runtime.py:205,714` |
| Alcance declarado corresponde al plan y a esta dependencia | ✓ | `tasks.md:401,2264`: cuatro fuentes dentro de `scripts/eval/`; sin integración de callers atribuida a esta entrega |
| Tests y cobertura actual por módulo completo | ✓ | JUnit original: **64 PASS**, exit **0**, un test PDH explícitamente deselected. Cobertura oficial: **process 81,5832 %**, **canonical_runtime 84,6330 %**, cero exclusiones |
| RED funcional previo | ✓ | Logs originales: `concurrent_call_rejected` y `original owned Job remains alive`, ambos exit **1**, anteriores al cambio. Archivo temprano de nacimiento/cleanup incompleto expresamente cualificado |
| Constitución explícita | ✓ | Sin infracción identificada; confinamiento y conservación del estado canónico contrastados con `docs/CONSTITUTION.md:25,33` |
| Verificación de tarea cerrada | N/A | `tasks.md:395`: T-09 está **en-progreso**. La verificación de `tasks.md:403` no se considera ejecutada por esta suite |
| Generados y descripciones E2/E3 | N/A | El diff no toca `commands/`, `agents/` ni `hooks/`; no procede ejecutar el exportador interop |

| T-09 → criterio de aceptación global | Resultado |
|---|---|
| Matriz de configuraciones y duraciones — `tasks.md:407` | ✗ Pendiente |
| Bind mount frente a copia — `tasks.md:408` | ✗ Pendiente |
| Preflight Ollama/VRAM — `tasks.md:409` | ✗ Pendiente de aceptación global |
| Navegador y observación de desbordamiento — `tasks.md:410` | ✗ Pendiente |
| Experimento opcional `torch.compile` — `tasks.md:412` | ✗ No acreditado |
| Recomendación numérica — `tasks.md:413` | ✗ Pendiente |

Estos criterios permanecen abiertos correctamente; no constituyen gaps de esta primera dependencia.

**Comprobaciones propias:** cuatro fuentes actuales y copias oficiales coinciden por hash; **2.900 artefactos** del inventario y **65 protegidos** sin discrepancias; **84 pares** launch/cleanup, con 73 `CLOSED_CONFIRMED` y 11 `UNKNOWN_QUARANTINED`. Leí código, pruebas y evidencias; no repetí la suite.

**Límite conservado:** el bloqueo físico del `ReadFile` de custodia sigue **UNTESTED**. Las pruebas de evento y pipe no lo acreditan. QA independiente, integración formal4, cadencia, GPU y matriz160 siguen pendientes.