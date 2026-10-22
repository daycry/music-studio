# ADR-0068 · Descartar identidad obsoleta antes de construir procedencia

- **Estado:** aceptada bajo delegación del propietario; implementación, revisión y QA pendientes.
- **Fecha:** 2026-10-09.
- **Relacionadas:** [ADR-0062](ADR-0062-evidencia-sintetica-explicita-con-binding-del-server.md), [ADR-0063](ADR-0063-procedencia-en-resolucion-completa-tras-routing.md) y [ADR-0067](ADR-0067-verificacion-vigente-del-esquema-sql-con-suite-completa.md).

## Contexto y evidencia

SQL QA3 completa terminó con1026PASS,27FAIL y3SKIP. Dos revisiones
independientes aislaron incompatibilidades de composición de fixtures y el
caso de cambio de identidad entre routing y resolución fresca. Los focales
privados posteriores confirmaron registro compartido y ACK/residencia de
las fixtures positivas, sin modificar las aserciones originales.

Con composición positiva correcta, `test_selected_health_revalidated_after_screen[identity]`
observó exactamente dos Health: versión `1` y después `changed`. La
construcción de procedencia lanzó `ResolutionError` antes del cotejo de
identidad que el dispatcher ya ejecutaba después de `resolve`. No hubo
lease autorizado para `changed`. Ese rechazo de autoridad es correcto;
su clasificación como petición inválida impide el aborto transitorio
previsto por la prueba y por el control existente del dispatcher.

Evidencia privada: `t05-qa3-causal-probes1/root-scanning-probes-verification.json`
y auditoría `t05-identity-drift-contract-review1/report.md`, ambas bajo
`.cache/dev-cycle/m1/`. El primer prototipo `scanning-A` tuvo un error de
wiring y se conserva sin usarlo para probar causalidad; el contraste válido
es `scanning-A-fix1` frente a `scanning-B`.

## Decisión

La resolución completa del dispatch recibe el contexto de la ruta elegida
y coteja su identidad con **la misma observación fresca** utilizada para
resolver, antes de construir procedencia o conceder una lease. Un cambio
acreditado de backend/identidad se comunica como estado obsoleto específico;
el dispatcher invalida la observación y descarta ese candidato sin reservar,
cargar ni enviar, tanto en selección explícita como automática.

El contexto sólo restringe la selección; nunca concede autoridad. Se
mantienen la validación del registro sintético, el binding exacto de
descriptor/backend/origen/build y la captura posterior a load. No se
autoriza `changed`, no se aprende confianza del catálogo y no se añade una
tercera lectura de Health para desplazar la carrera.

La restricción de selección **no omite las observaciones frescas de otros
backends** que el recorrido de resolución completa ya realizaba. Los
controles originales de observación positiva se conservan; un backend
observado distinto del seleccionado no puede conceder procedencia ni ser
retargeteado. La medición posterior al primer fix detectó la omisión en los
parámetros200/400 y exige corregirla, sin cambiar aserciones o plazos.

La pertenencia del backend seleccionado al mapping vigente debe mantenerse
después de las suspensiones que preceden a seleccionar procedencia. El
chequeo inicial no basta si un callback de otro catálogo sustituye el objeto
seleccionado durante ese await. Se conserva el descarte específico e
invalidación, incluso para jobs explícitos, sin retargetear al reemplazo ni
convertir cualquier error de entrada en drift. La revisión B1 del primer
intento exige reproducción funcional antes de corregir ese caso.

Los errores de entradas inválidas o de binding inicialmente inválido
conservan su propagación para un job explícito. No se captura cualquier
`ResolutionError` como estado transitorio ni se compara el texto del error.
Resolver invocado fuera del dispatch conserva su comportamiento sin contexto
de routing. El control posterior y el preflight fresco siguen vigentes.

## Implementación y verificación

Ownership inicial: resolver/dispatcher, dos fixtures de scanning y reintento
manual, y pruebas nuevas específicas de drift. Las fixtures declaran recetas
antes del catálogo y comparten el registro exacto; sus positivos devuelven
ACK y residencia coherentes. El caso de reintento conserva `prepared`,
procedencia NULL, terminal None y sus cuatro aserciones.

Reproducción RED funcional antes de cambiar runtime; controles de identidad
estable, drift y errores explícitos, sin load/submit/lease/attempt para drift.
Se conservan parámetros, aserciones, plazos y límites de consultas anteriores.
Después: revisión adversarial y QA independiente vigente. ADR-0067 sigue
exigiendo las suites completas y el suplemento Linux; ningún focal las sustituye.

El recurso `scripts/init_env.py` que faltaba en el espejo se declara y sella
en la nueva preparación de QA. No se modifica su código ni el test, y nunca
se usa el `.env` real como fixture. Este arreglo de preparación no cuenta
como un RED funcional del generador de tokens.
