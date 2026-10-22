> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

U2b1 entregada para revisión; NEEDS_CONTEXT. No aceptación de unidad, T05 ni M1.

Pruebas propias actuales: 51 casos, exit 0. Baseline apropiada original: {'cases': 1029, 'passed': 804, 'failed': 8, 'errors': 214, 'skipped': 3}, exit 1; 32 ficheros seleccionados, sin excluir performance801 ni historia job_attempt.

La baseline no es verde: cuatro expectativas HEAD0005 en tres ficheros no asignados requieren autorización/asignación de root. Véase needs-context.json y baseline-failures-original.json. No se modificaron ni eludieron.

Implementación: migración0006 con DDL propio congelado, tres tablas opcionales, contratos privados aceptados reutilizados, CAS/invariantes SQL+ORM, revisión de contenido y paquete inmutables, historial de retry, error/procedencia legacy opcionales, proyección0005 por capacidades, snapshots sin campos operativos y restauración activa interrupted/unknown. Backup SQLite conserva privados. Sin AnalysisImport ni columnas Analysis nuevas.

Copias/input causal exactos: True. Delta protegido: []. Tres reemplazos legacy byte exactos: True; demás funciones/decoradores/asserts/params AST idénticos. Schemas espejo byte idénticos: True.

La cobertura siguiente procede exclusivamente de la traza actual de baseline fallida; no acredita QA ni aceptación. Se conserva primera traza de unidad separada y nunca se une con trazas antiguas.

WHOLE apps/server/app/migrations/cpu_publication_invariants.py: 279/303=92.07920792%; excluidas 0.

WHOLE apps/server/app/migrations/versions/0006_cpu_publication.py: 27/27=100.00000000%; excluidas 0.

WHOLE apps/server/app/models/__init__.py: 418/420=99.52380952%; excluidas 0.

WHOLE apps/server/app/snapshots.py: 379/405=93.58024691%; excluidas 0.

RED: test_sql_cas_stale_illegal_and_immutable falló con AssertionError: assert 1 == 2
 +  where 1 = <function cas at 0x00000211138FBD80>(<sqlalchemy.engine.base.Connection object at 0x0000021113EFFC20>, 'cpu_execution', '01K70000000000000000000006', 1, 'running') · 2026-10-08T22:45:49.107302+00:00 · red-cas/junit-original.xml

RED: test_committed_requires_exact_assets falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:56:37.979396+00:00 · red-committed-assets/junit-original.xml

RED: test_cpu_rejects_engine_lane_sql falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:42:00.413823+00:00 · red-cpu-authority/junit-original.xml

RED: test_cpu_unknown_custody_cannot_finish_or_resume falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:52:24.554414+00:00 · red-custody-state/junit-original.xml

RED: test_orm_plan_rechecks_real_winner_terminal_digest falló con Failed: DID NOT RAISE any of (ValueError, StatementError, IntegrityError) · 2026-10-08T22:59:40.663824+00:00 · red-orm-winner-sha/junit-original.xml

RED: test_sql_outcome_is_closed_and_finite falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:54:29.427864+00:00 · red-outcome/junit-original.xml

RED: test_prepared_package_sql_rejects_contradictions[foreign_seed] falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:52:30.247454+00:00 · red-package-authority/junit-original.xml

RED: test_cpu_orm_contract_invalid[digest] falló con Failed: DID NOT RAISE any of (ValueError, StatementError, IntegrityError) · 2026-10-08T22:42:15.911575+00:00 · red-plan-digest/junit-original.xml

RED: test_ready_assets_history_and_terminal_outcome_are_preserved falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:56:41.008635+00:00 · red-ready-immutable/junit-original.xml

RED: test_legacy_ready_take_cannot_acquire_new_intent falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:52:27.463579+00:00 · red-ready-preservation/junit-original.xml

RED: test_revision_crossrow_fraud_sql[output_index-1] falló con Failed: DID NOT RAISE IntegrityError · 2026-10-08T22:42:13.098288+00:00 · red-revision-authority/junit-original.xml

RED: test_snapshot_causal_closure_private_roundtrip falló con AssertionError: assert [] == ['01K70000000000000000000006']
  
  Right contains one more item: '01K70000000000000000000006'
  Use -v to get more diff · 2026-10-08T22:46:12.079953+00:00 · red-snapshot-closure/junit-original.xml

RED: test_portable_row_drops_operational_identity falló con AssertionError: assert {'cleanup_sta...shed_at', ...} == {'contract_ve...handler', ...}
  
  Extra items in the left set:
  'cleanup_state'
  'process_identity'
  'lease_token'
  'supervisor_epoch'
  Use -v to get more diff · 2026-10-08T22:41:54.127281+00:00 · red-snapshot-privacy/junit-original.xml

Coste SQL real por propósito: 29+3*pages frente a26+3*pages, exactamente tres lecturas adicionales de extensiones; lectura de capacidades sustituye la anterior comprobación de job_attempt. Conserva pages+1 para job_attempt y casos20/200/405. Receipts SQL en los directorios green-unit-current y final-current.

TDD n/a: esquemas estáticos, DDL congelado como configuración y helpers/informes privados. Esqueleto compilable mínimo previo a RED de comportamiento, sin dobles de producción. Ruff check y format --check registrados exit0 sobre seis ficheros propios; test_job_attempt_schema no formateado.

Custodia/cleanup nativo UNKNOWN; grupo/slot/FFmpeg/audio/media/publicación filesystem/dispatcher/E2E/Docker/GPU no acreditados. Modelos/terminal/descriptores de fixtures explícitamente sintéticos; SQLite/ORM y backup reales.

Baseline completa fallida; cuatro expectativas HEAD fuera de ownership exigen decisión y asignación de root. Sin waiver, selección fuera ni cambios de esos tests.

SQL compara referencias/identidades/digests congelados; SHA canónico de payload se calcula y revalida en ORM/snapshots, no mediante SHA256 nativo en SQLite.

Los primeros RED archivaron código/tests/runner/fixtures/config, pero el archivo causal inicial no incluía JSON de migrations/initial_relations. La baseline final sí los copia.

Primeros comandos pytest no fijaron cache_dir privado; podían usar cacheprovider de pytest del checkout. Final y últimos RED sí fijan cache_dir propio. No se borró ni alteró esa historia.

Normalización de fixture terminal y longitud ULID reparadas con historia original conservada; esos incidentes no se cuentan como RED conductuales.

CLI del padre y uso real del proveedor reservados a root; no se fabrican exit/modelo/tokens/EUR/horas.

Baseline: caso performance801 TimeoutError, causa UNKNOWN. Error FileNotFoundError del archivo privado scripts/init_env.py corregido en harness-token-repair1 (1 PASS); baseline original exit1 conservada, sin reemplazarla por esa prueba aislada.

Tokens, EUR y horas IA NULL. Root es único ledger/docs/ADR/Git/aceptación/medidor. No se ha actualizado ninguno.

NEEDS_CONTEXT: autorizar y asignar las cuatro expectativas HEAD0005→0006 en los tres ficheros exactos de needs-context.json; después baseline completa fresca y revisión/QA raíz.

Delta de entradas vivas posterior a baseline: [".cache/dev-cycle/m1/t05-durable-sql-unit2b1/actor_runner.py"]. Copias originales preservadas; cambio privado del runner para archivar init_env.py y ejecutar el caso aislado. Timeout performance801 UNKNOWN; requiere diagnóstico y coordinación de root, sin ampliar timeout ni excluir el caso.
