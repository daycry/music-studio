**Lente C: sin hallazgos de seguridad introducidos o reabiertos** en las nueve fuentes del diff INLINE.

Activación: `lente_c: true`, patrón `sql-fstring` en `apps/server/app/migrations/job_attempt_invariants.py:290`.

| Criterio C | ✓/✗ | Evidencia estática |
|---|---|---|
| Inyección SQL, comando o plantilla | ✓ | SQL generado desde constantes y esquemas internos; literales escapados en `job_attempt_invariants.py:158`. Los payloads importados no se interpolan como SQL. |
| Autenticación y sesión | ✓ | No modifica endpoints, autenticación ni sesiones. |
| Secretos hardcodeados o persistidos | ✓ | Rechazo recursivo en `job_attempt_invariants.py:58` y JSON1 en `:291`. Valores de prueba sintéticos. |
| Deserialización insegura | ✓ | JSON y validación Pydantic estricta en `job_attempt_invariants.py:51`; ninguna carga pickle ni ejecución de contenido. |
| Path traversal | ✓ | Validadores contractuales heredados, guardas SQL en `job_attempt_invariants.py:221` y salida ligada al intento en `:292`. No incorpora operaciones de filesystem sobre rutas del terminal. |
| SSRF | ✓ | No añade llamadas de red ni destinos externos. |
| Permisos y propiedad | ✓ | Guarda de propietario en `job_attempt_invariants.py:294`, protección del padre en `:319` y propietario común del snapshot en `snapshots.py:265`. |
| Soporte e importación | ✓ | Guardas en `job_attempt_invariants.py:329`; validación y colisiones antes de abrir la excepción de importación en `snapshots.py:562` y `:593`. |
| Corrección R04-S01 | ✓ | Timestamp explícito y UTC en helper (`job_attempt_invariants.py:54`, `:78`) y SQL (`:255`, `:219`); ambas copias del snapshot requieren `ts`. Sin regresión de seguridad identificada. |

**Gaps:** Critical: 0 · Important: 0 · Minor: 0.

Revisión exclusivamente estática del paquete INLINE, con criterio propio, sin consultar referencias externas ni ejecutar herramientas o pruebas. Los ✓ indican ausencia de vulnerabilidades identificadas en este diff; no constituyen un veredicto de Lente A ni aceptación técnica. T04 conserva sus ocho CA abiertos; QA independiente y wheel/Docker permanecen pendientes.