FIXTURE-OWNER01 corregido para revisión fresca y QA independiente.

Causa probada: las validaciones de entradas/padres no revalidaban el token de custodia; el marcador final rechazaba la limpieza cuando el payload ya había desaparecido. Tres RED nativos con aserción real de payload retenido, previa al cambio de producción: entrada en scandir, salida tras colección y entre dos unlinks. Los primeros tres RED por recuento también se conservan; no son fallos de colección/import/API.

Cambio mínimo: check_owner antes de cada borrado de hoja/directorio y antes de retirar el marcador; conserva guardas inicial/final, tipo regular, nlink=1, token, UUID/registro y comprobaciones de reparse/padres/root identity. Tras retirar el marcador, antes de rmdir raíz, valida identidad/registro; recuperación exclusiva x tras rmdir fallido permanece, sin remint ajeno. No chmod ni seguimiento de destinos de childlinks.

Prueba: intercalación controlada sobre Workspace/UUID y filesystem kernel Windows real; wrapper de scandir sólo altera el marcador propio. Entre entradas, wrapper ejecuta unlink real y altera el mismo marcador tras el primer borrado. No prueba un adversario OS plenamente concurrente. Existe ventana TOCTOU entre check y unlink/rmdir frente a mutación maliciosa por el mismo usuario; no se promete atomicidad.

GREEN dirigido 3 PASS. Final final-frozen 106 PASS/5 skips (fixture completo, portable completo y vecino audio-post symlink). Junctions foreign/cycle/broken, hardlinks, file handles y directory handle noShareDelete con recuperación del marcador pasan. Cinco skips Windows de privilegio symlink; prueba Linux childlink anterior conserva sólo su alcance/bytes anteriores, sin rerun Docker ni atribución a bytes nuevos.

Cobertura oficial nueva .coverage + coverage.json: módulo completo 119/126=94,444444%, cero líneas excluidas; mismo helper y tests congelados antes/después de ejecución. No unión con trazas anteriores. Ruff check y format --check exit0. Primer format --check exit1, corregido sólo formato; corrida y cobertura anteriores preservadas y final repetida sobre bytes actuales.

Todos los tests/asserts fixture previos AST exactos; módulo portable byte exacto al predecessor, por tanto original67 preservados. Fuentes congeladas actuales y snapshots por comando; protegidos/payloads before=after; fixtures privadas vacías tras cleanup propio. No GPU/red/install/frontend/Git/ledger/docs/global acceptance.

Guías aplicadas: custom-agents:tdd y debug-root-cause 1.22.0. Gotcha sólo se propone aquí por ownership exclusivo root docs: comprobar custodia antes de cada efecto, documentando TOCTOU. No escritura de conocimiento autorizada en esta fase.

Advertencias: pytest cacheprovider desactivado produce aviso preexistente de cache_dir; ZIP duplicado intencional produce warning. Los scripts privados se ejecutan por Python .venv gestionado tras env.ps1, caches/TEMP/coverage/fixture configurados antes. No telemetría de modelo/tokens/coste/horas real: NULL.

RED: tests/test_fixture_confinement.py::test_cleanup_revalidates_owner_before_each_delete[entry] falló con AssertionError: Payload borrado después de perder custodia · 2026-10-08T00:16:44.545715+00:00

RED: tests/test_fixture_confinement.py::test_cleanup_revalidates_owner_before_each_delete[collected] falló con AssertionError: Payload borrado después de perder custodia · 2026-10-08T00:16:45.495298+00:00

RED: tests/test_fixture_confinement.py::test_cleanup_revalidates_owner_before_each_delete[between] falló con AssertionError: Payload borrado después de perder custodia · 2026-10-08T00:16:46.471775+00:00

2933 payloads Node/pnpm y sus dos metadatos de origen exactos. Ningún drift concurrente en el helper observado hasta el cierre de este recibo; cli-metadata terminal corresponde al orquestador tras finalizar esta entrega.
