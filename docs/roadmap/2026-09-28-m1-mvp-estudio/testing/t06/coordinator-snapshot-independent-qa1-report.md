> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

QA independiente U2c B01: PASS. Una ejecución fresca: 246 PASS, 0 failures/errors/skips; originales 239 presentes y 7 casos B01 añadidos. Siete archivos completos, tests byteexact, sin filtros ni exclusiones. TDD n/a: QA independiente sin cambios de producto.

Cobertura oficial WHOLE de una única traza RAW y JSON (líneas+ramas, cero líneas excluidas):
- `apps/server/app/publication.py`: 90.322581% (69 líneas y 15 ramas cubiertas).
- `apps/server/app/event_snapshot.py`: 93.750000% (40 líneas y 20 ramas cubiertas).
- `apps/server/app/sse.py`: 95.226730% (279 líneas y 120 ramas cubiertas).
- `apps/server/app/queue/events.py`: 94.516129% (220 líneas y 73 ramas cubiertas).

Ruff check y format --check --no-cache sobre cuatro runtime y dos tests nuevos; salidas originales y waits directos archivados. Fuentes y protegidos conservados. Fixture B01 preservada antes de adaptación; único añadido privado: observador atexit de módulos cargados. DB SQLite real, EventBus real, barrera de dos hilos y orden commit/publicación ejercidos por los tests originales. B01 rechazo stage/certificado/shutdown conserva DB durable y devuelve false; sink válido true; None/False/1 rechazados. confirmed_count mide aceptaciones reales, no retención tras gap. Batch vacío e invalidate-only cuentan cero; semántica legacy y default consumer intacta.

Snapshot 1064/17 chunks de hasta64 jobs, límite64KiB, DTO cerrado, H común e id SSE sólo al final ejercidos; no salida parcial ante preflight inválido. TrustedScope max64 y feed certificado owner/song/type y binding immutable, sin metadatos privados/delta/system; límites ring256/pending64/subscribers32 y notify/overflow mantienen suite original.

Evidencia fresh BEFORE física de intérprete gestionado/base/stdlib/sitepackages y fuentes, aliases resueltos 3.12→3.12.14. No retrocaptura de productor: depsbefore histórico UNKNOWN. Inventario endloaded limitado; imports transitorios y censo kernel/DLL UNKNOWN. Cambios disjuntos en scripts/eval no implican propiedad ni congelación. Sin claims de exclusividad o rendimiento.

Historias originales239, QA2 fallida, B01 RED3 y fixture inicial None permanecen en sus paquetes originales sin waiver. FullSource/WAL/register/H/replay/allwriters/runtime/HTTP/no-store/sessionlifecycle/heartbeat/client/E2E siguen pendientes; no ejecución315,801,453, GPU/nativo/UI ni certificado seguridad global. Aceptación sólo Root. Modelo/tokens/EUR/horas null por ausencia de originales del proveedor.

Historia privada: intento inicial exit2 durante collection, cero casos ejecutados; faltaba test_dispatcher_recovery en el bootstrap. Artefactos originales conservados y receta reparada copiando las dependencias *.py igual que productor. Una sola baseline funcional246, sin retries funcionales ni RED causal atribuido al error.

BEFORE actual: 8126 archivos físicos tools, 264 fuentes/harness. Drift de cierre: [].

Historia privada: intento inicial exit2 durante collection, cero casos ejecutados; faltaba test_dispatcher_recovery en el bootstrap. Artefactos originales conservados y receta reparada copiando las dependencias *.py igual que productor. Una sola baseline funcional246, sin retries funcionales ni RED causal atribuido al error.

BEFORE actual: 8126 archivos físicos tools, 264 fuentes/harness. Drift de cierre: [].
