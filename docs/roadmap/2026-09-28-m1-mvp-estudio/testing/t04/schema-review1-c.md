**Lente C: sin hallazgos de seguridad introducidos o reabiertos** en las ocho fuentes del diff proporcionado.

Activación: `lente_c: true`, patrón `sql-fstring` en `apps/server/app/migrations/job_attempt_invariants.py:278`.

| Criterio de seguridad | Resultado | Evidencia estática |
|---|---|---|
| Inyección SQL/comando/plantilla | ✓ | Las interpolaciones generan SQL desde tipos y constantes internos; los literales se escapan en `job_attempt_invariants.py:149`. No se identifica entrada del snapshot interpolada como SQL. |
| Autenticación y sesión | ✓ | El diff no modifica autenticación, sesiones ni endpoints. |
| Secretos hardcodeados o persistidos | ✓ | Rechazo recursivo de campos sensibles en `job_attempt_invariants.py:56` y mediante JSON1 en `:279`; las credenciales de los tests son sintéticas. |
| Deserialización insegura | ✓ | JSON y validación Pydantic estricta en `job_attempt_invariants.py:51`; no introduce pickle ni ejecución de contenido. |
| Path traversal | ✓ | Validadores contractuales heredados y guardas SQL en `job_attempt_invariants.py:212`; directorio de salida ligado al intento en `:280`. No añade operaciones sobre archivos desde las rutas del terminal. |
| SSRF | ✓ | No introduce solicitudes de red ni resolución de destinos externos. |
| Permisos y propiedad | ✓ | Coincidencia con el propietario del job en `job_attempt_invariants.py:282`, guarda del padre en `:307` y validación de propietarios del snapshot en `snapshots.py:265`. |
| Protección del soporte e importación | ✓ | Guardas de soporte en `job_attempt_invariants.py:317`; validación y colisiones preceden la excepción transaccional de importación en `snapshots.py:562` y `:593`. |

**Gaps:** Critical: ninguno. Important: ninguno. Minor: ninguno.

Revisión exclusivamente estática del paquete INLINE, con criterio propio y sin consultar referencias externas ni ejecutar herramientas o tests. Los ✓ significan ausencia de un defecto identificable en este diff. No emito conformidad de Lente A ni aceptación técnica: T04 mantiene sus ocho CA abiertas y la QA de wheel/Docker sigue pendiente.