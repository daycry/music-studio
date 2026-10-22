> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Fix Linux B-01/B-02 — entrega para review2

Ownership EXACTO4. Fachada, backend/tests/fixture Windows y contexto protegido byte exactos. Ningún ledger/docs/ADR/Git/aceptación/medidor modificado.

RED: test_construction_emfile_after_native_popen_contains_tree falló con supervisor/líder/nieto reales vivos después de EMFILE · 2026-10-09; runs/red-b01.
RED: test_journal_fault_after_native_registration_still_reaps[ENOSPC] falló con nieto real vivo tras salida del supervisor · 2026-10-09; runs/red-b02.
RED: test_journal_fault_after_native_registration_still_reaps[EIO] falló con descendientes reales vivos · 2026-10-09; runs/red-b02-eio.

Los tres RED tienen fuente/runner/instrumentación/herramientas copiadas antes de start, argv/PID/UTC/exit/stdout/stderr/JUnit y referencias nativas previas al fallo. Testigo ajeno sobrevivió; cleanup exacto observado. No son errores de colección ni mocks de procesos. Se inyectan únicamente os.dup y journal dentro del proceso nativo propio.

B-01: boundary después de Popen, cierre de liveness y extremos privados, wait acotado del supervisor; los duplicados parciales se retienen inmediatamente. La excepción original se propaga y el grupo parcial continúa retenido UNKNOWN. B-02: finally desde el fork, journal con error conservador, PGID acreditado con líder propio no reaped/espera WNOWAIT y pidfd cuando existe, TERM/KILL, waits hasta ECHILD y final notify independiente del journal. Candidatos extranjeros no reciben autoridad.

GREEN focal: B-01 1PASS y B-02 2PASS. FINAL02 UUID df4f514d-b858-4db3-963a-8ffb373db800: Linux26PASS/Windows36PASS, 0FAIL/ERROR/SKIP. Se conserva AST de todas las funciones/clases/asserts/decoradores/parametrizaciones originales Linux23; Windows36 byte exactos. La primera pareja también pasó; se conserva y NO entra en el combinado actual. Nueva pareja justificada por recibos contemporáneos adicionales de waits y testigo.

Cobertura WHOLE oficial coverage.py --keep, cero exclusiones, ramas reales activas, solo raw actuales precopiados antes de combinar:
- apps/server/app/worker/custody.py: 258/293 = 88.05460750853243 %. Líneas 90.49773755656109 %, ramas 80.55555555555556 %.
- apps/server/app/worker/custody_linux.py: 285/333 = 85.58558558558559 %. Líneas 89.10505836575875 %, ramas 73.6842105263158 %.
- apps/server/app/worker/custody_linux_supervisor.py: 255/318 = 80.18867924528301 %. Líneas 82.3529411764706 %, ramas 73.75 %.

Docker: imagen pinned preexistente, sólo 7 CIDs propios; create --pull never, nonroot65532, no red/GPU, capdropALL/no-new-privileges, rootfsreadonly, pids128/mem1g/cpus2/tmpfs128m, binds privados. Inspect/removal/gone originales demuestran todos los CIDs eliminados. Sin build/pull/install/download/image mutation. Host únicamente .venv gestionada tras env.ps1; caches/TEMP/TMP/pycache privados antes de imports. Herramientas existentes bytecopiadas pre-run.

Comandos/originales: runs/*, windows-*, official-final02/*; recipe-original es copia readonly del último recipe FINAL06. current_sources SOLO OWNED4; protegido aparte en protected-context.json. Inventario completo excluye únicamente los cuatro nombres CLI top reservados y su propio fichero. TDD n/a para prosa/recibos/config e instrumentación de metadatos.

Límites: sin review2/QA independiente ni fullT05/audio/SQL/CPU2/FFmpeg/E2E/GPU. Límites históricos FINAL06 intactos; no metadata retrospectiva. Early host shell metadata detallada UNKNOWN fuera del historial CLI original de root. UTC nativo observado tras lanzamiento no equivale al instante kernel de nacimiento. Recursos parciales desconocidos retenidos conservadoramente. Ramas individuales Linux <80; métrica requerida WHOLE oficial líneas+ramas supera80 en cada uno. Tokens/EUR/horas IA reales NULL.

DONE_WITH_CONCERNS: unidad técnica concreta entregada; root debe realizar review2 fresca y QA independiente, sin reset de review1 ni cierre T05.

Incidente privado: deliver_current antes de case-repair comparó No such object con mayúscula; Docker emitió no such object. Fuente original preservada; reparación sólo del lector, sin repetir tests/combine. Los RED iniciales conservan birth/group/pidfds y runner reales, pero no argv/UTC individual de cada Popen interno; instrumentación posterior sólo acredita sus ejecuciones contemporáneas, sin retrocaptura.
