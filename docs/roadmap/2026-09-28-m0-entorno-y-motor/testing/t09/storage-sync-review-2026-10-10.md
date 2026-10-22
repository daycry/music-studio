# T-09 — Revisión del delta de sincronización por bloque

Segunda entrega de la copia de ADR-0072, después del fallo nativo de la
limitación de flujo por sí sola. Tres revisores de contexto fresco leyeron
el diff completo de los dos archivos: `benchmark_storage.py` y
`test_benchmark_storage_pacing.py`. Esta revisión cubre el delta de
sincronización, no el hito ni la matriz GPU.

| Criterio del delta | A | B | D | Evidencia |
|---|---|---|---|---|
| Cada bloque se escribe, vacía y sincroniza antes del siguiente | ✓ | ✓ | ✓ | Producto: líneas 127–129; regresión incluye lock y colas cortas |
| Fallos de vaciado/sincronización se propagan | ✓ | ✓ | ✓ | Seis casos parametrizados; no retorno de recibo válido |
| Coste real y política v2 | ✓ | ✓ | ✓ | `monotonic_bounded_sync_v2`; sincronización lenta incluida en `copy_s` |
| Ritmo global sin crédito acumulado, hashes y bind preservados | ✓ | ✓ | ✓ | Tests focales y cuatro vecinos; bind sin escritura, espera ni sync |
| TDD y cobertura | ✓ | ✓ | ✓ | Nueve RED antes de GREEN; 95/113 líneas = 84,0708 %, cero exclusiones |
| Preparación compatible con presupuesto | ✓ | ✓ | ✓ | CPU en entrypoint antes de uvicorn; readiness 3.600 s |
| Reproducción directa del producto con sensores | pendiente | pendiente | pendiente | Siguiente gate; el experimento privado no la sustituye |

**Veredicto del delta:** 0 Critical, 0 Important y 0 Minor. A y B repitieron
19 pruebas CPU, con 41 deseleccionadas ajenas al almacenamiento; D repitió
las 15 focales. Todos terminaron exit 0. A y B comprobaron los 93 artefactos,
las fuentes actuales y congeladas, las preimágenes y los dos tests vecinos,
sin discrepancias. El orquestador también verificó 93/93 artefactos y
cuatro fuentes/vecinos, sin discrepancias.

El último RED terminó a las 17:45:01,763487 UTC; el primer GREEN empezó a
las 17:45:21,535174 UTC. Los JUnit RED tienen un fallo asertivo, cero errores
y terminal 1; los nueve GREEN terminan con un test pasado y terminal 0.
Ruff y format-check de la entrega terminaron exit 0.

El selector oficial no activa C y activa D por la espera bloqueante del
pacing. El clasificador oficial del delta devuelve cinco paths en alcance,
cero fuera, cero excluidos y cero avisos. El checkout compartido completo
mantiene 459 paths preexistentes fuera del ledger M0, incluido M1: su gate
global sigue sin verde. No se revierten ni se ocultan para revisar este
componente.

Evidencia privada: `.cache/dev-cycle/t09/storage-sync-20261010/` y
`progress-persistence-diagnosis-20261010/sync-root-verification.json`.
SHA de producto:
`792c780abc79521653374c3e6acc36f41ac033f7f2bd3571db851cfcca3c39a7`;
SHA de test:
`1a6877dd2e6a95e61775f88d2cc0d28785ef2452158493ad3b57cfa9f4f98814`.

La primera entrega y su revisión permanecen en
[storage-pacing-review1-2026-10-10.md](storage-pacing-review1-2026-10-10.md).
La reproducción y los resultados negativos se conservan en
[storage-contention-diagnosis-2026-10-10.md](storage-contention-diagnosis-2026-10-10.md).
T-09 sigue en progreso; QA del componente, reproducción directa y matriz
GPU pendientes. TDD n/a para este informe.

## QA CPU independiente

Después de la revisión, un agente QA de contexto fresco ejecutó el componente
sin UI: **19/19**, cero fallos, errores u omitidos; 41 deseleccionados ajenos
al almacenamiento. Exit real 0. Cobertura oficial del módulo completo
95/113 = 84,0708 %, con cero líneas excluidas. Verificó los SHA de las dos
fuentes y dos vecinos antes y después, sin cambios.

Evidencia privada: `.cache/dev-cycle/t09/storage-sync-qa-20261010/`, con
`verdict.json`, `report.md`, JUnit, cobertura, comando, UTC, terminal e
inventario de 39 archivos. Playwright y su qa-gate no aplican a este
componente CLI; no se fabrica una salida UI. La reproducción directa en
Docker está en curso. Este PASS CPU no cierra T-09.
