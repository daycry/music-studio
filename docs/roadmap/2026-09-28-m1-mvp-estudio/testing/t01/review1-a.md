**Dictamen de lente A: ✗ conformidad pendiente. Un gap Important: el rechazo HTTP de Host/Origin no cumple CA-14 de la spec vigente.** Revisión estática exclusivamente del paquete inline; sin herramientas, ejecución propia ni comprobación live de hashes.

| T-01 → criterio de aceptación | Resultado | Evidencia y contraste |
|---|---|---|
| Configuración `pydantic-settings`, variables `STUDIO_*` y mapa familia→URL | ✓ | `settings.py:23–36,47–74` implementa configuración y mapa; `test_settings.py:12–37,53–96` comprueba entorno, validación y persistencia de lectura. Variables de convenciones §4 aplicables a esta base presentes; proveedores opcionales no constituyen funcionalidad pendiente de T-01. |
| Host cerrado, Origin exacto para métodos salvo GET/HEAD y SSE, CORS cerrado | ✓ respecto al ledger; **✗ respecto a spec CA-14** | `security.py:18–29` compara autoridades y Origin antes del routing; `46–81` limita preflight. Cumple la formulación de `tasks.md:85`, pero devuelve **400** para Host inválido y permite GET ordinario con Origin ajeno. Véase A-01. |
| Errores RFC 9457 con código estable | ✓ | `errors.py:5–29` define cuerpo y media type; `main.py:31–52` evita publicar valores de validación y excepciones. Tests de 404, 422, 500 y 405 en `test_security_errors.py:51–83,211–230`. La discrepancia de status Host se incluye en A-01. |
| Logs JSON en `data/logs/server.log` con rotación | ✓ | `logging.py:18–39,42–64`: campos JSON, redacción, confinamiento y rotación diaria UTC con 14 copias. `test_logging_token.py:9–26,75–96` comprueba contenido y configuración; `test_logging_paths.py:12–23` cubre ambos sinks symlink. RED/GREEN Linux aportados; skips Windows identificados. |
| Token persistente en `.env` y cabecera interna | ✓ | `settings.py:24–34,87–95`, `engine_client.py:19–26`; `test_token_persistence.py:8–24` comprueba generación única mediante el mecanismo existente. `test_logging_token.py:29–72` comprueba cabecera, destino y ausencia de seguimiento automático de redirecciones. |
| Imagen sin torch, Compose, persistencia y URLs internas | ✓ con evidencia aportada | `Dockerfile:27–30`, `docker-compose.yml:2–38`: instalación del paquete server, publicación loopback, montajes y DNS interno del mock. `runtime-receipt-final.json:141–158,245–290` aporta ausencia de torch, token incorrecto 401 y montajes; `image-source-parity.json:2–11` declara coincidencia de siete fuentes. No equivale a QA independiente. |

**A-01 — Important — Contrato de rechazo Host/Origin distinto de la spec.**

- **Requisito:** `docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md:66` exige **403** para Host distinto **o** Origin ajeno.
- **Delta:** `apps/server/app/errors.py:6` fija `INVALID_HOST` en **400**; `security.py:20–21` lo devuelve. `security.py:28` permite GET/HEAD ordinarios con Origin ajeno.
- **Escenarios concretos:** GET `/health` con `Host: evil.test:8000` devuelve **400**, confirmado por `runtime-receipt-final.json:25–38`; GET `/health` con Origin ajeno devuelve **200**, expresamente exigido por `test_security_errors.py:203–207`.
- **Test discordante:** `test_security_errors.py:16–19,112–113,133–140` consolida 400 para Host inválido. Sus verdes no acreditan CA-14.
- **Contradicción documental:** `tasks.md:85` exceptúa GET/HEAD; `convenciones.md:49` exceptúa únicamente GET; la spec CA-14 no declara esas excepciones. ADR-0035 conserva Host/Origin (`:21`) y ADR-0037 conserva criterios (`:6,20`). No resuelvo la contradicción por preferencia ni considero que los tests modifiquen el requisito aprobado.

| Comprobación transversal de la lente | Resultado |
|---|---|
| (1) Tareas marcadas hechas | ✓ Sin cierre anticipado: T-01 sigue `en-progreso`, criterios abiertos (`tasks.md:71,84–90`). |
| (2) Alcance y `Archivos` | ✓ Los veinte archivos del delta corresponden a `apps/server/`, Compose, lock, licencias y tests declarados en `tasks.md:77`. Scope aportado: veinte dentro, cero fuera (`scope-original.json:5–28`). Engines M0 fuera del delta revisado. |
| (3) Tests y cobertura | ✓ Tests de comportamiento leídos; cobertura aportada **196/197 = 99,49 %**, siete módulos completos y cero exclusiones. Apoya la revisión; no corrige A-01 ni acredita cobertura de ramas. |
| (4) Constitución explícita | ✓ Sin otra violación identificada: server sin torch (`CONSTITUTION.md:17`), confinamiento (`:25`), publicación loopback y controles (`:41`), secretos (`:42`) y ejecución offline (`:44`). La constitución no fija el status de rechazo. |
| (5) Verificación declarada | ✓ Consta en la nota del ledger (`tasks.md:90`): **59 passed / 8 deselected** y Origin ajeno **403**. Recibo aporta argv, UTC y exit 0 (`receipt.json:1176–1216`). No ejecutada por este revisor. |
| (6) Interop generado y documentación | No aplica exportador interop: el delta no toca `commands/`, `agents/` ni `hooks/`. README describe la base implementada; permanece la contradicción documental de A-01. |
| Contrato OpenAPI condicional | Omitido: ninguna spec OpenAPI modificada en el delta. |

**TDD:** los RED HTTP preliminares por ausencia de factoría no cuentan como evidencia de comportamiento. El informe declara repetición contra FastAPI mínimo con fallos de status/contenido (`report.md:23–39`); los tests finales contienen esas aserciones. Los recibos aportan ejecuciones y tiempos, pero no snapshots cronológicos de implementación suficientes para demostrar por sí solos código antes de RED o certificar toda la secuencia. No identifico una infracción TDD demostrada con este paquete.

**Gaps:** Critical **0** · Important **1** · Minor **0**. Lentes C/D no emitidas aquí. QA independiente, M0/T-13 y gates finales/manuales de M1 continúan pendientes; las funcionalidades de tareas futuras no son gaps de T-01.