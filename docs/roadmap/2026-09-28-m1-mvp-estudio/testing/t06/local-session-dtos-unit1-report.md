> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Unidad pura de sesiones locales y DTOs · informe de implementación

Estado: código concreto entregado; revisión fresca A/B/C, D auto y QA independientes pendientes del root. T06 sigue abierta.

## Resultado actual

Se crearon únicamente los cuatro ficheros de ownership. Owner ULID fijado por caller interno; ninguna resolución ficticia de User DB. Sesiones públicas aleatorias, TTL absoluto8h, capacidad32 sin expulsión, purga, padding64 y compare_digest de todos los registros acotados. Revoke idempotente sólo sobre binding genuino; close/epoch, foreign binding y referencias copiadas fallan cerradas. Revalidación retorna deadline absoluto para stream futuro idle. Locks con adquisición máxima2s, sin await, threads de producto ni callbacks retenidos. RNG/reloj internos de test deben ser funciones finitas de confianza; no se promete interrumpir un callback malicioso inyectado.

DTOs strict/extra forbid/frozen/finite; null preservado, ULID vigente, etiquetas ASCII64, discriminador phase, H positivo seguro, timestamp UTC milisegundos. Sólo end emite wire id epoch:H; helper propio preserva phase/jobs y revalida hijos antes de serializar. La allowlist no detecta secretos disfrazados de etiquetas públicas. Model_dump/exportación de SessionCredentialDTO incluye deliberadamente la credencial para futuro bootstrap autorizado, repr la oculta.

## Verificación real

```text
........................................................................ [ 57%]
.....................................................                    [100%]
125 passed in 0.24s
```

Coverage.py oficial7.16.2, fresh singletrace final-baseline/.coverage, sin combine ni exclusiones:

- apps\server\app\event_dtos.py: 78/79 (98.734177 %), excluidas0.
- apps\server\app\local_sessions.py: 163/164 (99.390244 %), excluidas0.

Worst-case de forma: frame real 21597bytes, 64 DTOs con ULIDs26/etiquetas64/attempt/statuslargo/float exponencial/Hsafe máximo, headers incluidos. Artefactos exactos .sse/.json en final-baseline/test-root. ceil1064/64=17; empty begin/end probado. No mide RSS/capacidad física ni ensambla snapshot SQL o coherencia completa entre17chunks.

Carrera real de40hilos con barrera:32 emisiones únicas/8 SESSION_LIMIT; carrera validate/revoke, join de cada thread con assert de terminación. child lifecycle final before/after no nuevos threads vivos. Es concurrencia stdlib del registro, no custodia Windows/CPU2 o rendimiento nativo. Reloj inyectado es prueba funcional, no espera real8h. Token por defecto sólo forma43URL-safe comprobada, sin afirmación estadística de entropía.

Ruff check --verbose --no-cache y format --check --no-cache: exit0 para los4ficheros, fuentes previas y comandos archivados. No config global alterada. Dos anotaciones locales BLE001 documentan sanitización deliberada de fallos arbitrarios de clock/RNG; no excluyen cobertura. Primer Ruff9findings conservado; import sort/fecha timezone/dict literales corregidos sin debilitar aserciones.

## TDD y custodia

Tests originales escritos antes de baselines compilables. REDs conductuales antes del código que resuelve cada grupo; cada corrida tiene sources-before/copias2prod2tests+runner+child+config+protected, argv/UTC/PID/exit/stdout/stderr/JUnit y .coverage/JSON. causal-red-receipts.json reúne22corridas. No se afirma RED individual de125parametrizaciones. Null/formas/status válidos ya satisfechos por baseline permisiva se verifican, sin llamarlos causal RED. Clock-exception/código desconocido son pruebas suplementarias posteriores, no features nuevas ni RED propio.

- RED: `apps/server/tests/test_local_sessions.py::test_real_defaults_and_fixed_owner` · exit1 · 2026-10-08T22:43:45.091637+00:00 · originales `red-registry-causal/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_event_dtos.py::test_private_extra_fields_rejected[engine_token]` · exit1 · 2026-10-08T22:43:47.141740+00:00 · originales `red-dto-privacy-causal/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_event_dtos.py::test_strict_job_bounds[progress-True]` · exit1 · 2026-10-08T22:43:49.142692+00:00 · originales `red-dto-finite-causal/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_event_dtos.py::test_controls_frame_phase_and_wire_commit[end]` · exit1 · 2026-10-08T22:43:51.143404+00:00 · originales `red-frame-causal/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_event_dtos.py::test_credential_exact_schema` · exit1 · 2026-10-08T22:44:00.166139+00:00 · originales `red-credential/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_event_dtos.py::test_control_data_bounds[begin-active_count-1001]` · exit1 · 2026-10-08T22:44:02.200866+00:00 · originales `red-control-shape/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_event_dtos.py::test_control_data_bounds[end-cursor-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:2]` · exit1 · 2026-10-08T22:44:04.215403+00:00 · originales `red-control-cursor/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_event_dtos.py::test_control_envelope_bounds[id-True]` · exit1 · 2026-10-08T22:44:06.230864+00:00 · originales `red-envelope/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_event_dtos.py::test_control_closed_discriminator_and_schema` · exit1 · 2026-10-08T22:44:08.235244+00:00 · originales `red-discriminator/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_local_sessions.py::test_expiry_idle_deadline_and_no_sliding` · exit1 · 2026-10-08T22:45:26.480213+00:00 · originales `red-expiry/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_local_sessions.py::test_absolute_expiry_and_purge_without_eviction` · exit1 · 2026-10-08T22:45:28.518538+00:00 · originales `red-capacity/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_local_sessions.py::test_revoke_close_restart_and_foreign_binding` · exit1 · 2026-10-08T22:45:30.545386+00:00 · originales `red-binding/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_local_sessions.py::test_duplicate_rng_finite_no_overwrite` · exit1 · 2026-10-08T22:45:32.596501+00:00 · originales `red-collision/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_local_sessions.py::test_invalid_clock[True]` · exit1 · 2026-10-08T22:45:34.665601+00:00 · originales `red-clock/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_local_sessions.py::test_invalid_controls[controls0]` · exit1 · 2026-10-08T22:45:36.731672+00:00 · originales `red-controls/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_local_sessions.py::test_constant_time_bounded_scan` · exit1 · 2026-10-08T22:45:38.784763+00:00 · originales `red-scan/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_local_sessions.py::test_thread_capacity_and_revoke_race` · exit1 · 2026-10-08T22:45:40.863278+00:00 · originales `red-threads/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_local_sessions.py::test_wrong_owner_cannot_issue` · exit1 · 2026-10-08T22:46:01.673581+00:00 · originales `red-owner-causal/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_local_sessions.py::test_revocation_invalidates_and_is_idempotent` · exit1 · 2026-10-08T22:46:03.692263+00:00 · originales `red-revoke/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_local_sessions.py::test_close_invalidates_all` · exit1 · 2026-10-08T22:46:05.717552+00:00 · originales `red-close/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_local_sessions.py::test_rng_retry_and_private_exception` · exit1 · 2026-10-08T22:46:07.795456+00:00 · originales `red-rng-private/stdout.txt` y JUnit.
- RED: `apps/server/tests/test_local_sessions.py::test_invalid_clock` · exit1 · 2026-10-08T22:47:39.763499+00:00 · originales `red-huge-clock-causal/stdout.txt` y JUnit.

Incidentes no causales separados: primer runner parents5 erróneo (4intentos antes proceso, originales sólo conversación y copia runner); PYTHONPATH app provocó shadow de stdliblogging (4runs con stderr retenido); red-owner falló por resta float exacta y se corrigió la aserción a deadline=issued+TTL, sin etiquetar ese fallo de owner; selectorhugeclock exit4, luego RED causal OverflowError y GREEN6. Son historia conservada, nunca RED por import/colección. Lecturas iniciales de contexto no tuvieron sellado anterior/argvPIDstdout separado; copias tardías context-source-copies no afirman primera custodia. Baselines de cada corrida sí capturan antes del proceso real.

## Scope y límites

current_sources cuatro exactos cotejados con inputs de la corrida final;30protected root definidos estables (bus/framing/tests, queue/main/security/API/locks/etc). No se congelan modelos/snapshot/migraciónCPU ni custodia nativa de otros actores. Ningún oldtest alterado. No imports ORM/settings/security/main/.env, dependencias nuevas, rutas HTTP/OpenAPIJSON/Next/SQLite/engines. No suites históricas453/66/31 ni GPU/Docker/red/UI. No ledger/docs/ADR/Git/medidor/metas ni aceptación final tocados.

No acredita HTTP/CORS/auth/UserDB/feed/replay/WAL/barrier/builder/cliente/E2E/SWC/CPU2 o aceptación completaT06. Siguiente actor root: revisión fresca y QA independiente antes HTTPunit. Contabilidad de proveedor/modelo/tokens/EUR/horasIA NULL; originales CLI reservados no tocados. Inventario NONCLI completo excluye sólo4reservados top y el propio inventory.json.

Límite de locality: format-own4 no fijó RUFF_CACHE_DIR ni --no-cache. El directorio preexistente .ruff_cache/0.16.9 muestra LastWriteTimeUtc22:48:02, concordante con esa ejecución; mutación exacta de entradas UNKNOWN por ausencia de sellado previo. No se borra caché compartida. Las siguientes corridas tienen cache privada y las comprobaciones finales --no-cache. Recibo/informe/contabilidad previos al descubrimiento conservados .before-cache-disclosure.
