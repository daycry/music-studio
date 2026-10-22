> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# QA independiente del protocolo privado T05

VERDICT: SCOPEDPASS. Baseline actual única: 110 PASS, 0 fallos/errores/skips; Popen PID 19460, wait/exit 0.
UTC 2026-10-08T21:45:51.596213+00:00 — 2026-10-08T21:46:06.027458+00:00. Módulo completo: 238/240 = 99.16666667 %, cero exclusiones.

Fuente y test actuales coinciden con adjudicación A/B/C/D y productor final-current-official; mapas declarados antes/después y copias físicas previas exactos. Los tres contratos aceptados permanecen byte-exactos. Sin afirmación de estabilidad global: docs raíz y unidad SSE pueden cambiar legítimamente fuera de estos mapas.

La lectura de assertions y la corrida verifican uint32 network, JSON UTF-8 estricto, duplicados/NaN/surrogates/objetos/claves privadas/sobre cerrado, identidad/epoch/secuencia/dirección, frame 256 KiB, total wire 4 MiB por dirección, máximo 132 frames, 64 progress y 64 take_result. Test de 131 frames válidos y límite 132 por estado no se presenta como 132 frames emitidos válidos. Entrega de frame válido antes del siguiente inválido, EOF parcial, bloqueo posterior y rechazo de prefijo antes del cuerpo quedan ejercitados.

mark_stopping recibe contexto de confianza; no mide parada física. Epoch correlaciona sin autenticar. El transporte admite deliberadamente JSON inválido para negocio; el padre requiere los contratos aceptados y autoridad de publicación. No se acredita dominio mediante validación JSON.

Cota lógica del buffer 262148 bytes; RSS/pico real no medido. B228 fue comprobación in-memory del revisor, no baseline nueva ni benchmark. No prueba pipes físicos, hijos nativos/descendientes (UNKNOWN), SQL, publicación, CPU slots, modelos, hash de archivos de negocio, cleanup de grupos ni E2E. Sólo wait del proceso pytest observado con retorno real.

No cambios a producción/tests/framework/contratos públicos/docs/Git/ledger/meter. TDD n/a: QA readonly. Sin rerun de contratos74: imports productivos sólo stdlib; init vacío de imports. Entorno privado antes de imports, intérprete .venv existente, sin instalación ni red. Originales raw coverage+JSON/JUnit/stdout/stderr/argv/UTC/PID y snapshots en baseline-current-official.

Incidente de lectura: First160 inicial de CONTINUE incluyó parcialmente Historial; no utilizado para el veredicto. Métricas modelo/tokens/EUR/horasIA NULL. Aceptación fresca corresponde al root; no cierre T05/M1.
