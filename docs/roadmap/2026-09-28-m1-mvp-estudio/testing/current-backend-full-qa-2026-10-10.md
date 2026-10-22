# QA backend completa actual — M1 · 10 de octubre de 2026

**Backend: NO-VERDE. M1 integral: NO-VERDE.** Esta ejecución mide el checkout posterior a las correcciones CPU/API aceptadas; conserva los originales y no convierte los 88 fallos anteriores en 88 defectos. Sin cambios de producto, dependencias, ledger o Git por QA.

## Ejecución y resultados reales

Suite principal server + engine-contract + audio-post + storage-guard: **2185 PASS, 81 FAIL, 0 ERROR, 11 SKIP**, sobre 2277 nodos JUnit. **Pytest exit 1; contenedor exit 1; wrapper docker start exit 1; terminal PID 0.** Los resultados de terminal se conservan en suite.log; un caso con llamada pasada y teardown fallido puede diferir del contador de nodos JUnit.

Primer intento: setup-only, exit 2 antes de pytest por PermissionDenied en caché UV heredada de la imagen. No hubo tests ni JUnit; se preservan recibos y contenedor detenido. Reintento nuevo: UV_CACHE_DIR propia, `uv run --frozen --no-sync --all-packages`, imagen CPU fijada `sha256:7c65be72cf35ef0989407f280405f49c41662d01caa32a4c75bf4eec4d55ee25`. UID/GID 10001, cap-drop ALL, no-new-privileges, red none, sin GPU ni Ollama. Fuentes montadas RO. Caché temporal Linux en capa propia y `/proof` tmpfs exclusivamente para tests nativos/cross-device; no acredita almacenamiento de producto ni sustituye ext4. FFmpeg Linux real fijado y su SHA están en environment.json.

Selección principal completa de los cuatro directorios anteriores con `-m "not gpu"`, salvo **test_worker_native_custody.py**, archivo exclusivo de KernelGroup Windows sin marcas de plataforma y con parent.py externo. No se cuenta como skip pytest: 20 funciones de test sin ejecutar en esta selección (parametrización puede ampliar casos). Lista exacta en summary.json. Los marks propios restantes se conservan; no se fabrican skips.

## Pruebas nativas de credenciales, separadas del runtime

| Entrada | PASS | FAIL | ERROR | SKIP |
|---|---:|---:|---:|---:|
| custody-current-recorded | 21 | 0 | 0 | 0 |
| ipc-recorded | 84 | 1 | 0 | 0 |
| ipc-idempotent-focal-recorded | 0 | 1 | 0 | 0 |

La entrada custody histórica usa un auxiliar antiguo: fallan las nuevas respuestas de credenciales y source-mutation. Se conserva sin atribuir sus siete fallos al producto. custody-current usa el arnés real vigente, con UID19000 helper y rival UID10001, NoNewPrivs y Cap*=0 comprobados por las pruebas, y pasa 21/21. IPC y su focal conservan el fallo de `test_native_second_instance_and_idempotent_close`: `OSError(9, Bad file descriptor)` al segundo `Server.close()`. La fuente helper.py:160–178 conserva lock/control tras cerrar; el `finally` puede cerrar de nuevo un descriptor invalidado o reutilizado. Bug reproducido con fixtures reales, notificado al orquestador; QA no lo corrige.

Estos contenedores usan UID0 sólo para preparar propietarios y cambiar credenciales reales, con SETUID/SETGID/CHOWN/DAC_OVERRIDE/FOWNER explícitas; sin privileged/SYS_ADMIN/GPU/red/WSL. Tmpfs `/scratch` y `/out` son auxiliares unitarios. No representan ni reemplazan server/worker UID10001 o persistencia de consumer. Los arneses originales y sus hashes, adaptaciones limitadas a rutas/selección, JUnit y metadatos se conservan.

Las primeras entradas nativas usaban `/out` tmpfs y perdieron su JUnit al detenerse; sus logs y terminales reales permanecen, sin atribuirles un JUnit conservado. Las tres entradas `*-recorded` repiten sólo esos subconjuntos en contenedores nuevos con `/out` en capa Linux propia y conservan JUnit oficiales. Sus resultados son los conteos formales de la tabla. `/scratch` permanece tmpfs unitario.

## Fallos de la suite principal

| Caso | Clasificación de evidencia |
|---|---|
| apps.server.tests.test_domain_routes::test_generation_forwards_style_and_defaults_seed | fixture resolver SimpleNamespace incompleta tras captura de engine_id; dos stubs en test_domain_routes.py:193/296 |
| apps.server.tests.test_domain_routes::test_generation_creates_song_chain_after_authority_checks | fixture resolver SimpleNamespace incompleta tras captura de engine_id; dos stubs en test_domain_routes.py:193/296 |
| apps.server.tests.test_worker_actual_execution::test_real_wav_is_transcoded_and_published_once | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_actual_execution::test_manifest_keeps_winning_params_and_actual_take_lineage | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_actual_execution::test_private_params_require_generic_receipt_before_manifest_publication[actual0] | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_native_linux_custody::test_owner_deadline_and_normal[normal] | pendiente de adjudicación; resultado rojo real conservado |
| apps.server.tests.test_worker_native_linux_custody::test_invalid_transport_retains_owner[eof] | pendiente de adjudicación; resultado rojo real conservado |
| apps.server.tests.test_worker_native_linux_custody::test_journal_fault_after_native_registration_still_reaps[ENOSPC] | hooks privados de fault injection ausentes; no defecto de producto acreditado |
| apps.server.tests.test_worker_native_linux_custody::test_journal_fault_after_native_registration_still_reaps[EIO] | hooks privados de fault injection ausentes; no defecto de producto acreditado |
| apps.server.tests.test_worker_native_linux_custody::test_grace_selector_enfile_after_actual_term_contains_owned_tree[create] | hooks privados de fault injection ausentes; no defecto de producto acreditado |
| apps.server.tests.test_worker_native_linux_custody::test_grace_selector_enfile_after_actual_term_contains_owned_tree[register] | hooks privados de fault injection ausentes; no defecto de producto acreditado |
| apps.server.tests.test_worker_native_linux_custody::test_grace_selector_enfile_after_actual_term_contains_owned_tree[select] | hooks privados de fault injection ausentes; no defecto de producto acreditado |
| apps.server.tests.test_worker_native_linux_custody::test_grace_selector_enfile_after_actual_term_contains_owned_tree[close] | hooks privados de fault injection ausentes; no defecto de producto acreditado |
| apps.server.tests.test_worker_native_linux_custody::test_secondary_final_notify_error_retains_unknown_after_native_waits | hooks privados de fault injection ausentes; no defecto de producto acreditado |
| apps.server.tests.test_worker_native_linux_custody::test_final_group_query_error_uses_owned_pidfds_and_retains_unknown | hooks privados de fault injection ausentes; no defecto de producto acreditado |
| apps.server.tests.test_worker_native_linux_custody::test_backpressure_fixture_really_saturates_queue | pendiente de adjudicación; resultado rojo real conservado |
| apps.server.tests.test_worker_private_context_integration::test_song_private_receipt_uses_sql_author_not_param_claim | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_sql_lyrics_proof_is_checked_before_copy_or_spawn[UPDATE take SET lyrics_version_id=NULL-PROVENANCE_MISSING] | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_sql_lyrics_proof_is_checked_before_copy_or_spawn[UPDATE lyrics_version SET deleted_at='2026-10-09T00:00:00Z'-PROVENANCE_MISSING] | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_sql_lyrics_proof_is_checked_before_copy_or_spawn[UPDATE lyrics_version SET text='Different text'-PROVENANCE_MISMATCH] | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_sql_lyrics_proof_is_checked_before_copy_or_spawn[UPDATE lyrics_version SET sha256='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'-PROVENANCE_MISMATCH] | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_sql_lyrics_proof_is_checked_before_copy_or_spawn[UPDATE take SET seed='18'-PROVENANCE_MISMATCH] | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_total_plan_and_private_context_budget_precedes_copy | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_lyrics_authority_drift_before_commit_cannot_publish | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_replay_uses_historical_receipt_and_rejects_new_declaration | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_real_sparse_output_keeps_engine_index_and_seed[3] | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_raw_source_custody_rejects_aliases_and_changed_bytes[hardlink] | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_raw_source_custody_rejects_aliases_and_changed_bytes[symlink] | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_raw_source_custody_rejects_aliases_and_changed_bytes[fifo] | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_raw_source_custody_rejects_aliases_and_changed_bytes[tamper] | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_actual_ffmpeg_failure_is_durable_and_has_no_assets[song_actual0] | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| apps.server.tests.test_worker_private_context_integration::test_cancel_at_publication_barrier_preserves_no_assets_and_joins | omisión del arnés QA: recibo FFmpeg real ausente; ver focal reparado |
| packages.audio-post.tests.test_audio_post::test_master_and_listen | dependencia/ruta exclusiva Windows |
| packages.audio-post.tests.test_audio_post::test_limiter_and_resampling | dependencia/ruta exclusiva Windows |
| packages.audio-post.tests.test_portable_audio_post::test_explicit_root_real_audio | dependencia/ruta exclusiva Windows |
| packages.audio-post.tests.test_portable_audio_post::test_real_link_rejected[junction-root] | pendiente de adjudicación; resultado rojo real conservado |
| packages.audio-post.tests.test_portable_audio_post::test_real_link_rejected[junction-ancestor] | pendiente de adjudicación; resultado rojo real conservado |
| packages.audio-post.tests.test_portable_audio_post::test_real_link_rejected[junction-source] | pendiente de adjudicación; resultado rojo real conservado |
| packages.audio-post.tests.test_portable_audio_post::test_real_link_rejected[junction-destination] | pendiente de adjudicación; resultado rojo real conservado |
| packages.audio-post.tests.test_portable_audio_post::test_failure_preserves_source_and_cleans_own_output[transcode] | pendiente de adjudicación; resultado rojo real conservado |
| packages.audio-post.tests.test_portable_audio_post::test_replaced_owned_directory_is_preserved[transcode] | pendiente de adjudicación; resultado rojo real conservado |
| packages.audio-post.tests.test_wheel_resources::test_installed_manifest_without_checkout | pendiente de adjudicación; resultado rojo real conservado |
| packages.storage-guard.tests.test_client::test_native_client_real_credentials_and_domain_cleanup | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_protected_domain_runs_noreplace_and_cleans | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_anonymous_consumer_rw_has_no_named_witness | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_domain_rejects_unaccredited_policy[nosticky] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_domain_rejects_unaccredited_policy[wrongowner] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_domain_rejects_unaccredited_policy[privatewide] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_domain_rejects_unaccredited_policy[acl] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_rival_cannot_reach_protected_names_at_boundaries[delete-file] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_rival_cannot_reach_protected_names_at_boundaries[delete-directory] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_rival_cannot_reach_protected_names_at_boundaries[creator-close] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_rival_cannot_reach_protected_names_at_boundaries[mkdir-open] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_unknown_residue_is_preserved_and_blocks_reopen | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_constructor_duplicate_failure_closes_already_owned_fd | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_consumer_uid10001_anonymous_rw_and_helper_runtime_rejection | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_acl_query_error_fails_closed | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_custody::test_source_modified_after_creation_is_preserved | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_helper::test_native_wrong_peer_fails_before_probe | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_helper::test_native_helper_authenticated_exchange[success] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_helper::test_native_helper_authenticated_exchange[extra-fd] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_helper::test_native_helper_authenticated_exchange[wrong-root] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_helper::test_native_helper_authenticated_exchange[deadline] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_helper::test_native_helper_authenticated_exchange[disconnect] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_helper::test_native_endpoint_rejects_before_socket_creation[busy-lock] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_helper::test_native_endpoint_rejects_before_socket_creation[wide-control] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_helper::test_native_authority_constructor_rejects_invalid_config[wrong-uid] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_helper::test_native_authority_constructor_rejects_invalid_config[uuid-authority] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_helper::test_native_endpoint_preserves_unknown_replacement | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_helper::test_native_second_instance_and_idempotent_close | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_native_probe::test_native_noreplace_preserves_all_witnesses_and_cleans | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_native_probe::test_probe_does_not_remove_substituted_marker | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_native_probe::test_probe_preserves_file_modified_in_place | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_protocol::test_native_one_fd_cloexec_and_tail_rejection | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_protocol::test_native_invalid_frame_has_no_descriptor_leak[extra] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_protocol::test_native_invalid_frame_has_no_descriptor_leak[control-truncated] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_protocol::test_native_invalid_frame_has_no_descriptor_leak[data-truncated] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_protocol::test_native_invalid_frame_has_no_descriptor_leak[tail-fd] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_protocol::test_native_invalid_frame_has_no_descriptor_leak[response-fd] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_protocol::test_native_invalid_frame_has_no_descriptor_leak[malformed] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |
| packages.storage-guard.tests.test_protocol::test_native_invalid_frame_has_no_descriptor_leak[disconnect] | credenciales/fixtures nativas no suministradas en principal UID10001; ver subejecuciones |

Mensajes y trazas completos: [failures.json](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/failures.json). Los hooks privados ausentes se conservan como fallos no ejecutables; no se inyectan señales falsas. Las fixtures que fijan ffmpeg.exe Windows no reciben un alias Linux. Un rojo de preparación no prueba un fallo de producto, y tampoco se presenta como verde.

Desglose disjunto de los 81 FAIL: **39** credenciales/fixtures storage no suministradas en principal; **19** omisión de recibo FFmpeg por QA; **2** stubs resolver sin engine_id en test_domain_routes.py:193/296; **8** hooks privados inexistentes; **10** fixtures audio/plataforma (incluye wheel con Lib/site-packages Windows); **3** nativos de custodia sin adjudicar (`owner_deadline_and_normal[normal]`, `invalid_transport_retains_owner[eof]`, `backpressure_fixture_really_saturates_queue`). Los tres últimos siguen rojos reales, sin calificarlos de flaky ni inventar causa. El bug close se reproduce en el arnés IPC con autoridad real separado.

Focal reparado de los 19 casos bloqueados por el recibo: **19 PASS, 0 FAIL, 0 ERROR, 0 SKIP**, pytest exit 0. No se repite la suite completa ni se borran sus fallos. Se extrae READONLY el recibo real de la imagen CPU fijada; archive SHA 2d41cbea… y FFmpeg SHA 953632de… coinciden con pin y binario snapshot. Un intento de montaje sobre directorio RO falló antes de pytest y se preserva separado. El focal válido monta un kit privado completo RO con el recibo real. [Selección y prueba de recibo](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/ffmpeg-receipt-focal2/selection.json), [JUnit focal](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/ffmpeg-receipt-focal2/results/suite.xml), [terminal focal](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/ffmpeg-receipt-focal2/results/pytest-terminal.json).

Los artefactos de `/proof` se copiaron en vivo durante la suite, antes de detener el contenedor: [recibo de captura](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/attempt2/proof-live-capture.receipt.json). El sufijo de la carpeta es sólo una etiqueta; la UTC real consta en el recibo. La tmpfs desaparece al detenerse y no se promete una conservación posterior de su contenido original. Los JSON copiados se sellan en el inventario final.

## Cobertura oficial whole

Pytest-cov recoge todos los archivos de los cuatro módulos de producto; JSON oficial conservado. No se recortan rangos ni se rebaja el umbral. Scope de correcciones y audio post completo:

| Archivo | Líneas | % | Exclusiones |
|---|---:|---:|---:|
| apps/server/app/db.py | 60/64 | 93.7500 | 0 |
| apps/server/app/domain_routes.py | 655/755 | 86.7550 | 0 |
| apps/server/app/migrations/job_attempt_invariants.py | 191/202 | 94.5545 | 0 |
| apps/server/app/migrations/versions/0007_job_attempt_json_guard.py | 15/15 | 100.0000 | 0 |
| apps/server/app/queue/chains.py | 84/86 | 97.6744 | 0 |
| packages/audio-post/audio_post/manifest.py | 169/255 | 66.2745 | 0 |
| packages/audio-post/audio_post/pipeline.py | 100/133 | 75.1880 | 0 |

Hay 12 archivos medidos por debajo del 80 % whole; lista completa y todos los módulos en cobertura oficial y summary.json. La suma global no sustituye cada scope. No se declara cumplimiento whole del backend completo ni una cobertura de fixtures nativas no ejecutadas.

Combinación oficial de las bases originales de cobertura principal y focal (misma fuente, sin rerun): `coverage combine --keep` y `coverage json`, con SHA/bytes de entradas y terminales 0 preservados. [JSON combinado](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/combined-coverage/results/coverage.json). Manifest continúa **169/255 = 66,27 %**, pipeline **100/133 = 75,19 %**, por debajo del 80 %. Publications alcanza **229/262 = 87,40 %**. Audio_child aparece **0/170** porque esta medición pytest-cov no instrumenta su proceso hijo; los 19 casos funcionales pasan, pero no se atribuye cobertura no medida. Sin exclusiones en esos scopes. La falta de umbral se mantiene explícita y no se sustituye por el número de casos.

## Puertas y custodia

Ledger-lint exit 0: cero incoherencias, un aviso de lectura UTF-8. Coverage-check exit 0: cero referencias rotas; T-00 documental sin cobertura declarada. No se ejecuta qa-gate como veredicto pytest: esta entrada es backend CPU, no Playwright; no se fabrica results.json ni se reutiliza un gate HTTP histórico como actual.

Snapshot: 1767 fuentes/locks/auxiliares sellados antes y después. Input_profile.py ACE CPU, server/app, conftest, scripts/test_workspace y recursos wheel incluidos. Delta documental autorizado del orquestador: docs/roadmap/2026-09-28-m1-mvp-estudio/testing/current-validation-2026-10-10.md, CONTINUE-HERE.md, docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md. No hay delta de producto. Se registran SHA y bytes de artefactos regulares; entradas nativas/special se describen sin afirmar contenido verificado. Contenedores propios detenidos para forense, terminal PID0; no se reutilizan los originales anteriores ni se toca ACE incumbente. Sin datos canónicos, Git, servicios ajenos o instalación.

Evidencia: [JUnit principal](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/attempt2/results/suite.xml), [terminal pytest](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/attempt2/results/pytest-terminal.json), [log principal](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/attempt2/results/suite.log), [cobertura oficial](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/attempt2/results/coverage.json), [terminal contenedor](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/attempt2/terminal-inspect.json), [resumen](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/summary.json), [sello inicial](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/source-before.json), [sello final](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/source-after.json), [inventario](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/artifact-inventory.json), [cierre de custodia](../../../../.cache/dev-cycle/m1/validation-20261010/backend-current/SOURCE_SEAL_FINISHED.json). PDF fuera de ownership de esta entrada; renderer gestionado no instalado, no instalación. Tokens/coste reales desconocidos (`null`), sin markers propios ni mediciones inventadas.

## Puertas integrales pendientes

- [ ] Ext4/VHDX autorizado, publicación/recovery, assets y Range persistentes.
- [ ] M-01 generación GPU real, escucha y cierre M0/T-13.
- [ ] M-02 revisión visual/manual/accesibilidad.
- [ ] M-03 backup/restauración de biblioteca real.
- [ ] Correcciones/revisión/QA de fallos pendientes e integración Git por orquestador.

No se cierran estados ni se hace handoff de documentación final.
