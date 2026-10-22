# T09 R09-O7 — continuidad de operaciones CPU

DONE_CPU_WITH_CONCERNS. Dos llamadas pasan ahora por monitored_operation existente: estimate y GET de reanudación, sólo wddm_auto_v1.

1. Reproducción mínima: dos RED individuales con sensores sintéticos explícitos y validador real reprodujeron observability_lost_auto_replayed_or_paused_sample tras 15 segundos sintéticos sin muestreo. argv/UTC/exits y stdout/stderr originales en red-estimate y red-resume.
2. Aislamiento: pre-submit se valida; estimate síncrono avanza15s; siguiente initial del envío falla antes del POSTjobs. Consulta de reanudación avanza15s y primer sample de observe_job falla. El transporte del envío ya monitorizado, relojes/PDH, baseline y serialización local no son la causa reproducida.
3. Hipótesis probada: las llamadas HTTP bloqueantes fuera del monitor provocan pérdida de continuidad. Ambas reproducciones hacen fallar la guarda real manteniendo timestamps/monotónicos y política.
4. Fix mínimo y GREEN2. Controles14 comprueban continuidad, sólo un POSTjobs, no reenvío en resume, NOT_FOUND/transport/error, no intent tras pérdida/error estimate, custodia request/terminal, identidad/estado y rama manual. Hilos reales; fake clock sólo del módulo observation y sensores sintéticos.

RED: test_slow_estimate_preserves_continuity_before_single_submission falló observability_lost_auto_replayed_or_paused_sample · 2026-10-07T01:27:10 UTC.
RED: test_slow_resume_query_preserves_continuity_without_resubmission falló observability_lost_auto_replayed_or_paused_sample · 2026-10-07T01:27:14 UTC.

Suite inicial224PASS; cobertura197/265 conservada. Suite final229PASS; cobertura228/265=86.037736%; private32PASS con hashes intactos. Ruff y format finalexit0. Recibo conserva todos los argv/exits. Dos errores de fixture now string no se declaran TDD y quedaron corregidos a datetime.

Custodia: baseline66→67; un cambio existente y un test nuevo;65 fuentes ajenas intactas;66 preimágenes intactas;12documentos y originalesGPU3 intactos. Artefactos anteriores protegidos y .coverage raíz cotejados. Delta aislado y sellos en este directorio.

## Límites

- Existing monitored_operation joins owned thread on guard failure, so error/cleanup waits for transport completion or existing transport deadline (default70s). Test covers joined completion/error, not cancellation of an indefinitely hung injected operation.
- Other execute_run local JSON/hash/fsync operations remain synchronous; no CPU evidence of them exceeding cadence. No unproven blanket wrappers or timestamps changed.
- No GPU, Docker, WSL, UI, network, model, install, ledger, document, Git or knowledge writes; CPU does not certify a successful new pilot or matrix160.
- debug-root-cause knowledge handoff belongs to root; explicit ownership forbids this worker from writing knowledge.
