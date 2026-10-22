> Adjudicación de entrega raíz: los JUnit actuales son 32 Linux + 36 Windows = 68. Los seis casos añadidos son cuatro errores de selector y dos casos auxiliares; la expresión inicial «26 + 4» del informe no incluye los dos auxiliares. Esto no constituye aceptación ni QA independiente.

> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# B03 Linux â€” entrega para review3 y QA de root

Corregido Ãºnicamente el escape del cleanup por errores del selector auxiliar. Se preservan lÃ­der propio no reaped/WNOWAIT/pidfd, autoridad PGID y candidatos ajenos sin autoridad. Fallar el selector marca UNKNOWN y continÃºa SIGKILL, fallback pidfd, waits y final notify; no crea un nuevo FD para recuperarse.

RED: test_grace_selector_enfile_after_actual_term_contains_owned_tree[create] fallÃ³ con ambos descendientes reales vivos tras TERM real + ENFILE controlado Â· 2026-10-09; runs/red-b03-create.
RED: variantes register/select/close fallaron por la misma assertion conductual Â· 2026-10-09; runs/red-b03-other. Supervisor original exacto; fuente/test/fixture/runner/toolchain precopiados antes de ejecuciÃ³n, argv/PID/UTC/exits/stdout/stderr/JUnit originales. Rescate pidfd propio sÃ³lo DESPUÃ‰S de assertions; testigo ajeno vivo antes del rescate.

GREEN focal: 4PASS. Primer GREEN fallÃ³ por seam privado buscando refs en la nueva closure; original y fuente conservados, reparaciÃ³n fija sin cambiar assertions. No se cuenta como RED conductual. Fixture Linux byte exacta; todas las funciones originales Linux conservan AST/asserts/decoradores/params. Linux backend/fachada/Windows backend/tests/fixture byte exactos.

FINAL05: Linux32 (original26 + 4) + Windows36 = 68PASS, 0FAIL/ERROR/SKIP. UUID a186ab8b-5f11-4525-8886-5704d9395260. WHOLE oficial lÃ­neas+ramas, cero exclusiones, RAW actuales de ambas OS e hijos nativos precopiados antes de combine --keep. No uniÃ³n histÃ³rica, extracciÃ³n, promedio ni gate separado de ramas80.
- apps/server/app/worker/custody.py: 258/293 = 88.05460750853243 %.
- apps/server/app/worker/custody_linux.py: 279/333 = 83.78378378378379 %.
- apps/server/app/worker/custody_linux_supervisor.py: 264/327 = 80.73394495412845 %.

CIDs propios exactos: 16, todos inspect/remove/Gone acreditados. Imagen fija preexistente --pull never, usuario65532, no red/GPU, capdropALL/no-new-privileges/read-only/pids128/mem1g/cpus2/tmpfs128m/binds privados; sin pull/build/install/descargas/cambios daemon ajenos. Herramientas privadas bytecopiadas del preflight autorizado. Host .venv gestionada tras env.ps1 con UV/TEMP/TMP/pycache/coverage privadas antes de imports.

actor-command-accounting.json preserva comandos originales y sus exits. current_sources.json contiene SOLO OWNED3; protegido separado; case-proof-map.json enlaza casos a artefactos y deja UNKNOWN donde falta prueba individual. Sourcecopies BEFORE RED/final y RAWsources BEFORE combine; inventario Ã­ntegro excluye sÃ³lo cuatro CLI top reservados y sÃ­ mismo. Tokens/EUR/horas IA reales NULL. TDD n/a: prosa/metadata/config/seam estÃ¡tico; comportamiento sÃ­ tiene RED real.

Historial sellado intacto y lÃ­mites originales conservados. No metadata retrospectiva; UTC observada no implica instante exacto de birth kernel. No checkpoints fingidos tras muerte. Windows conserva warning cache_dir del runner con cacheprovider desactivado. No fullT05/audio/FS/SQL/CPU2/FFmpeg/E2E/GPU aceptaciÃ³n, ni revisiÃ³n/QA independiente del productor. Root realiza review3 fresca+QA; no reset.


RED secundario: test_secondary_final_notify_error_retains_unknown_after_native_waits falló con exit nativo120 por ValueError final, después de TERM/KILL/waits reales · 2026-10-09. Se retiró primero la defensa notify para reproducir el manejo anterior, conservando el arreglo de gracia; no se afirma supervisor completo original en este RED auxiliar. Restauración mínima tras RED: GREEN 1PASS, sin final recibido y UNKNOWN. Primer intento auxiliar falló por seam privado interpretando el ACK binario; es NO causal y se conserva.

Historia FINAL01 y FINAL02: ambas66PASS pero gates supervisor77,7778 y79,7546 FALLIDOS, sin redondear79,7546 a80. FINAL03 añade el caso secundario con RED/GREEN real y fuentes de test/instrumentación nuevas; no reutiliza ninguna traza anterior. El snapshot de notify-fault es anterior al error controlado; su confirmed previo no autoriza devolución de recursos sin evento final y supervisor/FD/thread proof.

Incidentes estáticos adicionales: lector PowerShell de JSON coverage rechazó clave vacía (sin mutation); apply_patch privado inicialmente no encontró una línea de reporte inexistente (sin mutation). No son RED conductuales ni justifican repetir suites.

FINAL03: 67PASS pero WHOLE supervisor79,7546 FAIL; histórico intacto. RED query-point-repair: error EIO al consultar PGID en finally dejó ambos descendientes reales vivos con el manejo anterior. RED query-unknown: captura amplia contuvo y esperó ambos, pero confirmed=true violó UNKNOWN. Corrección mínima uncertain=true tras RED; GREEN1PASS, fallback pidfd exclusivo de referencias propias, waits SIGKILL reales, testigo ajeno vivo y final confirmed=false. Ningún SIGTERM/SIGKILL de grupo se autoriza con query fallida. FINAL04 exige nuevo UUID y pareja actual; sin unión de trazas previas.

Primer intento query fue NO causal: leyó leader_retained_before_signals antes de su asignación. Se conserva test/seam originales y se registra retained real en el punto de query, sin fabricar checkpoints. Primer deliver falló leyendo JUnit histórico con ruta final03 inexistente; repair privado, sin repetir tests/combine por ese fallo.

FINAL04: 68PASS y tres WHOLE>=80, pero Ruff format devolvió1 por EOL mezclados. La primera entrega privada no exigió ese exit en el archiver; auditoría final lo detectó. Fuente anterior y salida original conservadas; Ruff normaliza EOL sin cambiar AST. FINAL05 vuelve a ejecutar los mismos68 casos con SHA/UUID nuevos; no se reutilizan RAW de FINAL04. Verificación final exige combine/JSON/lint/format exit0. No es RED conductual ni excepción de gate.

DONE_WITH_CONCERNS: unidad concreta entregada; root debe realizar review3 fresca y QA independiente, sin reset ni cierre T05.
