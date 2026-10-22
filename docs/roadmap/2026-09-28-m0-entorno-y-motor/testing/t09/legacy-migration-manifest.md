# Manifest mecánico de migración — propuesta, sin ejecución

## Protección normativa y decisiones

Root ha decidido rechazar `wddm_auto_v1/v2` incondicionalmente en `run_session`, `execute_run`, `acquire_sample`, antes de factory, backend/API, sample, lease, Ollama o escritura de aceptación. `observer_factory`, `enforce=False`, resume y sensor con contexto aparentemente correcto no exceptúan la guarda. `task_manager_v1` manual sigue permitido. `observation_policy`, `validate_samples`, `validate_episode`, `accepted_samples`, `read_acquisitions`, `validate_calibration`, `validate_auto`, plan/parser/report históricos siguen interpretando V1/V2. No helper privado en producción que pueda ejecutar legacy o aceptar proof por flag.

El implementer NO debe resolver una guarda nueva cambiando asserts viejos por `raises(legacy_not_supported)` y dar las garantías por cubiertas. Primero conserva archivo exacto/recibos; después crea guardas específicas y regresiones V3 equivalentes. Separar lectores legacy de adquisición live, conservando assertions originales de lectores y provenance/context/policy/RAW. No xfail, quiet deselect, incremento de tolerancias, reemplazo de validator ni etiquetas V2→V3 aisladas.

Las fuentes de prueba inspeccionadas son copias congeladas: `transition-review3/scope-fixture/scripts/eval/tests`, `transition-review2-adjudicated-fix/suite`, `legacy-transition-diagnosis3/suite`. No se ha leído canonical vivo. `frozen-test-callmap.json` enumera cada función, línea, hash del módulo, decorators/parametrizaciones, dependencias locales y llamadas. La suite adjudicada es un harness privado; no se etiqueta su copia de `test_benchmark_transition_fix2.py` como bytes canónicos originales: su fixture tmp_path apunta a la fase. El diagnóstico adapta ese tmp_path de nuevo. Root deberá sellar la preimagen canónica exacta al adjudicar, sin restaurarla ni compararla como si fuera immutable global.

## Alternativas de migración

| Vía | Complejidad/riesgo/coste relativo/reversibilidad | Resultado |
|---|---|---|
| Archivar módulos completos y retirarlos de canonical | Baja/alto/S/alta | Rechazada como default: pierde offline, manual y unitarios válidos; sólo honesta con reemplazo completo y gate nuevo explícito |
| Archivo exacto + migración selectiva V3 nativa y fixtures legacy RAW almacenados | Alta/medio/L/alta | Recomendada: conserva historia y cobertura normativa actual |
| Mantener módulos viejos intactos dentro de suite actual | Baja/bajo para evidencia/S/alta | Resultado fullsuite RED tras guardas; no readiness, no debt acceptance implícita |

Para módulos mixtos crear archivo exacto antes de editar, en ubicación histórica explícita que root autorice (propuesta `docs/archive/testing/t09/legacy-live-pre-guard/`, fuera del discovery de pytest), con manifest SHA256/bytes por fichero y recibos completos. No mover allí módulos enteros como sustituto de la clasificación. Conservar también conftest/import dependencies y originales privados de logs; publicar recibos normalizados de rutas personales aparte sin reescribir originales. Si la raíz elige otro destino, el contrato de bytes/hashes/receipts no cambia. Este actor no crea archivo histórico ni cambia canonical.

## Mapa exacto por módulos/casos

Todos los nombres son node names del mapa congelado; los decorators contienen los parámetros exactos. `KEEP` exige que el caso quede actual, no archivado. `OFFLINE-FIXTURE` conserva cuerpo de assertions y cambia únicamente obtención de datos a RAW almacenado. `V3` cambia harness y conserva garantía semántica con reloj y procesos reales. `GUARD` es un caso nuevo, independiente del cuerpo histórico.

### `test_benchmark_reacquisition.py`

KEEP offline puro, sin adquisición ni fixture que la invoque:

- `test_shared_sustained_ticks_break_at_reacquisition`: shared adjacency/breaks, no live.
- `test_v2_policy_preserves_every_legacy_numeric_limit`: interpretación exacta/hashes V2.
- `test_calibration_lifecycle_waits_for_all_queries`: fases RAW in-memory V2 y lifecycle/última consulta.
- `test_new_plan_requires_exact_source_set_and_policy_version`: build/verify V2 histórico y 160/source set; no adquisición.

OFFLINE-FIXTURE: `test_offline_recomputes_recovery_and_rejects_forged_episode` (12 tamper), `test_continuity_chain_rejects_missing_or_replayed_episodes` (7), `test_metrics_read_requires_every_persisted_original` (4), `test_sealed_v2_calibration_has_ten_accepts_per_phase_and_retains_rejections`, `test_sealed_v2_offline_rejects_resealed_omission_or_claim` (10). Actualmente todos llaman `acquire_sample` directa o mediante `sealed_calibration`; el fixture debe cargar bytes RAW/episodes/originals/continuity/lifecycle/host/viewport almacenados, provenance V2 intacta. Mantener 10/10/10, 11 RAW loaded por un retry, todas las assertions de validación y tamper. `sealed_calibration` debe dividirse: fixture offline de bytes + fixture V3 nativa para tests live. `recovery` no se puede seguir invocando como productor V2.

V3 con nuevo proveedor/ownership nativos, todas las parametrizaciones conservadas:

- `test_monitored_transition_recovers_with_new_complete_original` (antes monitored_operation V2).
- `test_raw_persisted_before_decision_and_rejected_original_retained`.
- `test_known_lifecycle_boundary_prevents_retry_before_dedicated_classification`.
- `test_competing_invalid_never_retries` (browser/counter/identity/wsl/unavailable/collection/cadence/context/skew).
- `test_second_acquisition_cannot_reset_budget_or_hide_other_failures` (second_mismatch/deadline/tick/partial/second_browser/second_context).
- `test_baseline_keeps_ten_accepted_and_all_rejections`.
- `test_cleanup_records_raw_without_accepting_failed_sensors`: V3 raw-only/interrupted path, sin ACK ni predecesor; no desbloquear legacy por enforce=False.
- `test_valid_first_sample_never_consumes_extra_query`: V3 un query, más assertion offline legacy de unnecessary_retry conservada.
- `test_episode_deadline_includes_browser_after_last_windows_query`.
- `test_persistence_time_is_included_in_fixed_episode_deadline` ([1,2]): bloqueos reales en persistencia del provider, no reloj elegido por fixture.
- `test_runner_recovers_transient_without_duplicate_inference_or_resume_submit` ([False,True]): V3 `RuntimeChannel`/`ContinuousCoordinator`, receipt/intent/cursor reales; no mock de validador; mantener 1/0 POST y RAW rechazado.
- `test_v2_session_preserves_owned_cleanup_and_fails_closed_on_preparation_gap` ([0,3]): archivar cuerpo V2, crear V3 preparación observada >3 s y fallos de sampler propios. La expectativa antigua de abortar sólo por create lento no es semántica V3: V3 tiene que continuar observando, sin false PASS por renombrar método. Conservar 160 outcomes/40 grupos/no doble POST en un caso nuevo con runtime CPU apropiado, sin afirmar GPU.
- `test_v2_cli_resumes_exact_sealed_plan_and_keeps_incomplete_output_truthful` ([rows,timeout,guard_failure]): archivo exacto; separar lector de sesión finalizada V2 (KEEP lector nuevo) de resume incompleto V2 (GUARD nuevo), y crear V3 resume truthful/bytes exactos/incomplete error codes. Su monkeypatch a `run_session` evita la guarda real: no usar como prueba de rechazo actual.

`test_v2_runner_cannot_fall_back_to_unguarded_legacy_observers`: conservar viejo cuerpo en archivo, crear GUARD público V1/V2 con y sin contexto válido/factory, antes de POST. Mensaje anterior `observer_policy_context` no es el contrato actual de rechazo unconditional; no contar cambiar regex como cobertura equivalente de las garantías de acquisition.

### `test_benchmark_observation.py`

KEEP: todos los validadores/numeric/source/calibration/policy/plan/report/FILETIME/timezone/context/tamper que no son los ocho casos live enumerados abajo. En particular `sealed_case` genera ficheros mediante escritura directa y metadata histórica, no `acquire_sample`: `test_original_receipt_validates_context_and_actual_seal`, `test_receipt_rejects_forged_replayed_or_mixed_originals`, `test_continuous_matrix_does_not_expire_by_pilot_age`, `test_prerequisite_builder_uses_original_files_and_revalidates`, `test_finished_auto_session_requires_same_substantive_prerequisites`, `test_reaccreditation_preserves_previous_segment_without_recertifying_it`, `test_accreditation_chain_rejects_mixed_or_overlapping_originals`, `test_continuity_cannot_recertify_history_or_replace_pilot_samples`, `test_sequential_queries_preserve_accredited_history`, `test_sequential_chain_keeps_temporal_and_original_guards`, `test_pilot_acquisition_respects_external_now`, `test_continuity_starts_after_complete_pilot_acquisition` son interpretación offline; no migrar a V3 sólo por sus nombres.

V3 o split guard+V3: `test_observation_loss_stops_before_submission`, `test_auto_baseline_does_not_accept_numeric_claims_without_metadata`, `test_observation_loss_inflight_preserves_samples_and_stops_polling`, `test_monitor_rejects_observability_before_owned_submission`, `test_resume_uses_history_and_rebaselines_only_when_idle` ([False,True]). Hoy Sensors con observation_context/método default V1 ejercitan automatic; tras guarda deben conservar garantía mediante acquirer/coordinator V3, y añadir guard legacy temprano. Resume V3 debe mantener historial inmutable y decidir rebaseline por lifecycle real, sin mocks de validate_auto/guard_sample que oculten validación.

Manual/orquestación permitido, conservar y hacer explícita su intención manual sin fingir V3: `test_owned_lifecycle_operation_is_observed_while_waiting` (alias `validator(module,'monitored_operation')`, no detectado por sólo call name AST) y `test_monitor_period_does_not_add_sampling_cost`. Sus sensores carecen de contexto automático; prueban scheduling del monitor manual, no custodia/deadline V3. Mantener en canonical y añadir cobertura V3 real por separado. `test_legacy_visible_window_is_still_accepted_without_auto_identity` es unitario browser manual y KEEP. `test_observer_persists_context_snapshot_before_sensor_calls` ejercita sampler de bajo nivel, no publica una aceptación legacy; KEEP, no confundir bajo nivel con entrada live pública.

### Otros módulos congelados actuales

`test_benchmark_integration_cpu.py`: `prepared_plan` fija `task_manager_v1`. KEEP todos los casos, incluidos `test_full_160_error_attempts_keep_rows_and_cleanup_without_reuse` ([False,True]) y `test_cleanup_error_receipt_and_resume_never_inspect_dead_container_or_duplicate` (parametrizaciones del mapa), además de plan/seals/recommendation. Inyección de dobles aquí es manual, no loophole automático.

`test_benchmark_runner.py`: `test_session_runner_submits_once_after_estimate_and_resume_uses_receipt` no fija método automático, y `test_runner_timeout_preserves_existing_job_and_does_not_duplicate` no tiene context; son orquestación manual. KEEP; explicitar `task_manager_v1` en fixtures de plan/observer si el runtime exige método explícito, manteniendo asserts POST/intent/timeout. Resto de módulo (prerequisites manuales, output/fidelity/duration/capture) KEEP, no alterarlo por migración legacy.

`test_benchmark_deadline.py`: KEEP todas las pruebas HTTP/parser. Los cinco live `test_sampling_budget_includes_sensor_and_global_deadline`, `test_terminal_received_after_global_deadline_is_not_accepted`, `test_slow_sensor_still_observes_ready_done`, `test_slow_sensor_progress_and_status_keep_job_and_resume_sequence`, `test_slow_sensor_cannot_accept_terminal_outside_horizon` usan sensores sin contexto automático: scheduling manual, KEEP con intención manual explícita si necesaria. No contarlos como cobertura episodio V3. `test_benchmark_runtime.py::test_real_http_response_continuous_events_keep_sampling_and_deadline` análogo KEEP manual; sus otras pruebas resume/storage/lease/HTTP unitarias KEEP.

`test_benchmark_transition_fix2.py`: archivar íntegro antes de split. Cinco RED técnicos = `test_blocked_source_process_must_be_interrupted_within_episode`; `test_real_late_work_cannot_publish_or_advance[validation]`, `[accepted]`, `[continuity]`; `test_real_three_second_preparation_preserves_continuity`. V3 sucesores obligatorios indicados abajo. `test_native_pdh_raw_survives_later_clock_failure` y `test_native_raw_survives_counter_metadata_failure` son pruebas de colector de bajo nivel/RAW parcial, no aceptación live V2: KEEP sin debilitamiento; no ejecutarlas en esta fase ni ocultarlas como si estuvieran verdes.

`test_benchmark_transition_review2.py`: sólo `test_t03_observation_deadline_preserves_advertised_existing_job` se retira de normative current y archiva cuerpo exacto por contradicción ADR0045 removed; reemplazo explícito disposition. Todo el resto KEEP, especialmente FINAL RAW, barrera custodia, shutdown first cause y quarantine/removal/native timeout/partial event/legacy message.

`test_benchmark_episode_v3.py`, `test_benchmark_coordinator_v3.py`, `test_benchmark_calibration_v3.py`: KEEP todas las garantías actuales. Pueden ampliarse tras root decisión, no reutilizar sus PASS históricos como gate nuevo. `test_benchmark_audit_delta.py`: KEEP tests transporte/binding. `test_delta_native_volume_48000_logical_cpu_episodes` permanece prueba de transporte lógico, nombre/informe debe declarar alcance; añadir volumen canónico separado, no sustituir callback por fake y afirmar cierre D-04.

Los demás módulos de la suite congelada (listados completos en callmap) no presentan llamadas live públicas legacy en su AST local: KEEP unitarios/offline. Un import dinámico nuevo o alias fuera del mapa exige ampliar inventario antes de retirar nada, no permiso al usuario ausente. La classification json por caso se entrega aparte y enumera también módulos sin casos afectados; no es una garantía dinámica global.

`legacy-transition-diagnosis3/suite/test_diagnosis.py` y `test_real_clock_diagnosis.py`: sólo evidencia privada diagnóstica. Sus PASS que prueban aceptación defectuosa son HISTORICAL-DIAGNOSTIC, nunca regresiones current ni fixes; preservar recibos íntegros.

## Correspondencia de garantías y tests nativos V3 existentes

| Original/garantía | Tests actuales que ya contienen mecanismo V3 | Sucesor/adición necesaria |
|---|---|---|
| blocked source <2,1 s, ningún accepted | episode `test_blocked_episode_is_bounded_and_never_advances` (sampling y seis etapas), `test_supervisor_ownership_has_strict_native_identity` | Mantener presupuesto 2 s y assertion original <2,1; PID+creation_time propios/descendientes terminados, control ajeno vivo |
| late validation | mismo stage=validation; `test_retry_uses_original_total_deadline_with_real_cpu_delay` | Delay real posterior dentro de canonical/provider, ningún ACK/predecesor; RAW retenido |
| late accepted/continuity | stage commit_write/commit_fsync/verification; `test_native_interrupted_commit_bytes_never_count_as_ack`, `test_child_pending_state_is_only_confirmed_by_next_timely_receipt` | Bloqueo real en publicación conjunta supervisor/audit y continuidad; deadline original no rebased; bytes tardíos no métricas |
| preparation 3 s | coordinator `test_same_sampler_observes_three_second_preparation` (create/start/source_hash/copy), `test_native_full_preparation_then_v3_runner_no_duplicate_post` | Extend health/readiness/bootstrap/resume; mismo stream/predecesor, ≤2,5 s, ninguno reset, datos CPU explícitos |
| no double POST/new/resume/ACK lost | coordinator `test_native_lost_post_ack_queries_same_job_without_post_retry`, `test_native_lost_create_ack_recovers_own_identity_without_create_retry` | Tests migrados 1/0 POST con intent/cursor exactos, GET existing/NOT_FOUND no resubmit |
| retry / lifecycle / rejected RAW | episode `test_only_isolated_mismatch_gets_one_fresh_retry`, `test_rejection_breaks_shared_adjacency_and_is_required_offline`; calibration `test_actual_v3_production_calibration_accepts_full_anchored_chain`, `test_v3_rejects_actual_publication_or_phase_tampering` | Todos los casos invalid/refusals antiguos mediante provider V3, ninguna reutilización parcial/retry deadline reset |
| shared confidence/context/offline forged history | episode `test_offline_rejects_modified_or_incomplete_evidence`, `test_semantic_recomputation_with_fixture_resealed_bytes`; coordinator `test_offline_anchors_cannot_be_replaced` | Lectores legacy stored RAW siguen actuales más differential incremental/FINAL para V3 |
| sexto RED promete job vivo tras removed | review2 `test_adjudicated_native_timeout_records_removed_disposition`, quarantine cases y `test_adjudicated_native_partial_event_preserves_original_timeout_and_bytes` | disposition removed/terminal_preserved/unknown_quarantined, original error/intention/cursor, no ACK/free inventado, recurso ajeno intacto |

Los stages no son idénticos a los puntos de publicación de V2. Por eso se preserva el cuerpo histórico y se exige adición donde la equivalencia no es completa; no se declara que siete stage PASS existentes reemplazan automáticamente accepted+continuity.

## Guardas actuales y ejecución mecánica futura

1. Root decide diseño/ADR; preservar preimages exactas de módulos afectados, dependencies y CPU5/CPU6 argv/start/end/exit/log/JUnit/coverage originales. El RED CPU6 es 6 failed/469 passed/5 deselected; CPU5 6/468/5. No reescribir recibos ni sumar diagnósticos como tests arreglados.
2. Nuevos guard tests parametrizan las tres entradas × V1/V2 × valid/invalid/missing context × factory injected/no factory × resume donde aplica × enforce=False para acquire. Colocar trampas en constructors/sensor/backend/API/lease/Ollama y escritura, comprobar cero llamadas y cero accepted/RAW/product artifacts. Plan/prerequisites no confiables no se validan adquiriendo sensores primero. Manual positivo y offline viejo positivo por separado.
3. Capturar/generar una vez los fixtures históricos almacenados bajo archivo/fixture scope autorizado, sin llamar a runtime V2 actual. Usar bytes de evidencias congeladas completas que root verifique o serialización directa del schema histórico del lector en test (sin helper de producción). Declarar sintéticos, mantener todos hashes/contextos/RAW/episodes. Copiar bytes y refs a tmp del test y aplicar tamper sólo allí. No crear un legacy adapter escondido. Cuerpos offline y todos sus parámetros permanecen.
4. Fixtures V3 actuales nuevos usan trusted handler CPU propio con reloj real y native ownership; extraer constructor explícito común si conviene, no importar suite canónica entera ni usar su factory por AST como evidencia nueva. Preservar todas las garantías de tabla, incluyendo las adiciones de publicación supervisor y preparación health.
5. Inventario current vs archive por nodeid/parametrización y hash de cuerpo: cada caso tiene KEEP/OFFLINE-FIXTURE/V3/GUARD/HISTORICAL con successor y motivo. Registrar retiros explícitos en informe, no una nueva deselection. Sin huecos ni casos archivados sin sucesor relevante, salvo expectativa contractual contradicha con nueva prueba ADR0045.
6. RED/GREEN focalizados nuevos y una suite actual completa sólo después de cambios; mantener receipts históricos disponibles. Gate changed coverage ≥80% sobre whole módulos tocados sin exclusiones, revisión4 explícita y QA fresca. No certificar sensores/GPU por CPU.

No se ha hecho ninguno de estos pasos de migración ni aceptado deuda. Si root conserva tests antiguos sin migrar, reportar fullsuite RED, detener GPU/160/QA de acreditación; no pretender preparación completa.
