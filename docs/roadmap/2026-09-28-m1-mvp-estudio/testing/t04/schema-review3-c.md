**Lente C: sin hallazgos de seguridad introducidos o reabiertos** en las diez fuentes del diff INLINE.

Activación: `lente_c: true`, patrón `sql-fstring` en `apps/server/app/migrations/job_attempt_invariants.py:307`.

| Criterio C | ✓/✗ | Evidencia estática |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ | Interpolaciones desde constantes y esquemas internos; literales escapados en `job_attempt_invariants.py:158`. El payload importado no se interpola como SQL. |
| Autenticación y sesión | ✓ | No cambia endpoints, autenticación ni sesiones. |
| Secretos hardcodeados o persistidos | ✓ | Rechazo recursivo en `job_attempt_invariants.py:58` y JSON1 en `:316`. Los valores de prueba son sintéticos. |
| Deserialización insegura | ✓ | JSON y validación Pydantic estricta en `job_attempt_invariants.py:51`; no incorpora pickle ni ejecución de contenido. |
| Path traversal | ✓ | Validadores contractuales heredados y guardas SQL en `job_attempt_invariants.py:243`; salida ligada al intento en `:317`. No añade operaciones de filesystem sobre rutas del terminal. |
| SSRF | ✓ | No introduce llamadas de red ni destinos externos. |
| Permisos y propiedad | ✓ | Propietario del intento ligado al job en `job_attempt_invariants.py:319`, guarda del padre en `:344` y validación del snapshot en `snapshots.py:265`. |
| Soporte e importación | ✓ | Guardas en `job_attempt_invariants.py:354`; validación y colisiones preceden la excepción transaccional de importación en `snapshots.py:562` y `:593`. |
| Correcciones R04-S01 y R04-B02 | ✓ | Timestamp explícito y UTC; comprobación estricta de calendario, hora y fracción en `job_attempt_invariants.py:162`, aplicada al terminal y Common. Sin regresión de seguridad identificada. |

**Gaps: Critical: 0 · Important: 0 · Minor: 0.**

Revisión exclusivamente estática del paquete INLINE completo, con criterio propio; sin herramientas, referencias externas ni ejecución de tests. Los ✓ indican ausencia de vulnerabilidades identificadas. Esta tabla corresponde a **C**, sin emitir conformidad A ni aceptación técnica. T04 sigue `en-progreso`, con ocho CA abiertos; QA independiente y wheel/Docker permanecen pendientes.