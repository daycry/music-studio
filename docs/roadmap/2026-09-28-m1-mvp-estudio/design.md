---
design: m1-technical-sequencing
titulo: Avance técnico condicionado sin sustituir la aceptación musical
estado: aprobado
creado: 2026-10-07
actualizado: 2026-10-07
spec: spec.md
evaluacion: n/a
plan: improvement-plan.md
adr: ../../decisiones/ADR-0037-avance-tecnico-condicionado.md
opcion_elegida: O2
generacion:
  fuente: estimado
  tokens: null
  model: unknown
  cost_eur: null
---

# Diseño — Avance técnico condicionado

| Campo | Valor |
|---|---|
| Estado | Aprobado por el orquestador bajo delegación previa |
| Opción elegida | O2 — decisión del orquestador bajo delegación previa |
| Validación | O2 elegida por el orquestador bajo delegación previa; revisión y QA documental conformes |

## 1. Contexto y restricciones

M1 tiene spec aprobada y dieciséis tareas todavía en borrador. CA-01, el plan y T-01 bloquean actualmente su inicio hasta cerrar M0/T-13. M0 sigue abierto: 13/21 completadas, T-09/T-10 en progreso y T-08/T-16/T-20 en revisión. T-09 conserva su matriz activa de 160 ejecuciones y 28 fuentes selladas. Piloto GPU5 de 60 s y calibración de 30 observaciones son evidencia técnica; no eligen un ganador musical ni autorizan `verified:true`.

El server es un scaffold: `apps/server/app/__init__.py` no tiene app funcional; su pyproject solo depende de engine-contract. Compose contiene engines de análisis y ACE-Step, todavía no web/server/mock. ADR-0035 fija Docker, FastAPI sin torch, SQLite WAL y FFmpeg LGPL Linux; Ollama compartido en WSL2 es una excepción acotada. No Kafka/Redis ni otro backend de inferencia LLM. ComfyUI CUDA se valida en sus hitos.

La constitución conserva autoría, derechos, linaje, manifiestos inmutables y honestidad de capacidades. M0/T-13 requiere escucha humana y elección: ninguna automatización lo sustituye. El contrato ya permite probar todas las tareas con un mock sintético; su `verified:true` no se transfiere a ACE-Step. No se usa `STUDIO_ALLOW_UNVERIFIED` como vía de aceptación del producto.

## 2. Opciones (2–3)

### O1 — Conservar el bloqueo absoluto

Esperar a M0 completo antes de implementar M1 o abrir los siguientes hitos según roadmap vigente.

| Criterio | Valoración |
|---|---|
| Complejidad | Baja: ninguna separación documental nueva |
| Riesgo | Bajo de falsa aceptación; alto de inmovilizar trabajo independiente por escucha ausente |
| Coste relativo | S de cambio; oportunidad perdida durante la espera |
| Reversibilidad | Alta: desbloquear después exige la misma decisión documental |

### O2 — Implementación y QA técnicas contra mock, aceptación real condicionada

Permitir trabajo contract-first de M1 y piezas técnicamente independientes de otros hitos, con dependencias explícitas. Conservar gates de modelo, calidad, rendimiento, descriptores y release. Validar CPU, mock E2E y despliegue Docker sin GPU como evidencias diferentes; ninguna equivale a integración musical real.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: distinguir dependencias de construcción y aceptación en los documentos existentes |
| Riesgo | Medio: mock demasiado permisivo o cierre de tarea con criterio real pendiente |
| Coste relativo | M: ajuste acotado de gates y pruebas de capacidades negativas |
| Reversibilidad | Alta: contratos genéricos, esquema completo y descriptores evitan fijar candidato |

### O3 — Producto real provisional antes de cerrar M0

Conectar anticipadamente un candidato musical real y avanzar uso del producto mientras calidad y rendimiento siguen abiertos. El contrato contempla una excepción de desarrollo para tareas no verificadas, pero extenderla al producto chocaría con la honestidad de capacidades.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: configuración provisional, cambios de candidato y coexistencia GPU |
| Riesgo | Alto: competir con matriz activa, habilitar tareas no verificadas y confundir uso con aceptación |
| Coste relativo | L: integración y posible retrabajo antes de datos concluyentes |
| Reversibilidad | Media: el código es reversible, los artefactos y decisiones de uso ya emitidos no se borran |

## 3. Criterios de decisión

1. Preservar evidencia, matriz activa y aceptación humana por encima de avance aparente.
2. Obtener utilidad autónoma con contratos y datos independientes del candidato.
3. Mantener trazabilidad de lo realmente ejecutado: implementación, CPU QA, mock E2E, Docker real sin GPU, integración GPU y escucha son ámbitos distintos.
4. Cambiar el mínimo documental; conservar los criterios existentes y evitar infraestructura o alcance M2 nuevos.

## 4. Opción elegida y por qué

**Opción elegida: O2, por decisión del orquestador bajo delegación previa.** Permite progreso útil y reversible sin competir con GPU160 ni falsificar el cierre musical. O1 conserva coherencia pero bloquea seguridad, persistencia y UI que no necesitan un ganador. O3 no se recomienda durante la matriz activa; una excepción de laboratorio no hace elegible una capacidad para el producto.

Separación propuesta: implementación y CPU QA pueden avanzar contra mock; mock E2E prueba flujos; Docker real web/server/mock acredita despliegue, resolución interna, persistencia, FFmpeg Linux, SSE y Range. Release y aceptación musical conservan M0 cerrado, tareas `music.song`/`music.instrumental` realmente verificadas y M-01. M-02 y M-03 conservan su evidencia propia; no se dan por hechas mediante tests unitarios.

| Tareas M1 | Cierre honesto antes de M0 |
|---|---|
| T-01 | Sí, al cumplir todos sus CA y verificaciones, incluido arranque/configuración Compose real sin GPU y revisión de seguridad; código o mocks unitarios solos no bastan |
| T-02 | Sí: esquema completo, WAL/FTS/linaje, migraciones, song.json y backup/restauración probados en datos de prueba; M-03 real queda separado para aceptación del hito, sin borrado de biblioteca privada |
| T-03 | Sí al ejecutar contratos/parser/TS; API-02 exige `/api/generations`, así que la dependencia efectiva de esa evidencia llega con T-07; no cerrar por exportar un scaffold |
| T-04 | Implementable y verificable contra mock; cierre completo condicionado a I-01 (batch/serie según benchmark M0). No inventar rendimiento ni fijar un candidato |
| T-05 | CA técnicos cerrables con audio sintético y FFmpeg Linux real; M-01 compartida sigue pendiente en aceptación del hito, no sustituida por el mock |
| T-06, T-07 | Cerrables con sus verificaciones completas y capacidades negativas probadas; T-07 conserva dependencias T-04/T-05, no se elimina el bloqueo transitivo por una afirmación técnica |
| T-08, T-13 | Desarrollo y mock QA posibles; cierre requiere también M-02 según la cobertura y verificación existentes |
| T-09 | Cierre técnico posible con schemas/features del descriptor y rechazo de no verificadas; I-02 solo se resuelve para el descriptor realmente probado, no declara parámetros de ACE-Step acreditados |
| T-10, T-11, T-12, T-14 | Cierre técnico posible con dependencias y E2E cumplidos; eventos, onda, beats y telemetría proceden del mock identificado, sin atribuirlos al engine real |
| T-15 | Sí, suite existente 11 E2E y tres ejecuciones seguidas con mock; no certifica calidad, GPU ni release |
| T-16 | No: documentación preparable, pero cierre conserva M0/T-13, descriptores reales, M-01/M-03 y todos los CA de la spec |

Estas posibilidades no conceden cierres por adelantado. Si una tarea mezcla evidencia técnica con una evidencia real pendiente, el orquestador conserva el CA abierto y la tarea en progreso/revisión; no añade estados nuevos ni ledger alternativo. M-01 queda documentada como aceptación del hito en T-16, con cobertura compartida de T-04/T-05.

Para M2–M5, O2 permite definir y construir únicamente unidades con contrato aprobado y dependencias técnicas satisfechas. El roadmap hoy exige cierre previo, ≥30 generaciones reales para M2 y ≥100/una canción usada para M5. Esos requisitos se conservan para aceptación/release, y root debe explicitar la excepción de apertura técnica antes de abrir iniciativas. No autoriza implementar ahora funcionalidades sin spec ni declarar independientes las operaciones musicales, ComfyUI CUDA, LoRA o conectividad Ollama real. No se propone su descomposición ni presupuesto.

## 5. Impacto en módulos y ficheros

Los documentos de secuenciación se han publicado por el orquestador; cuentan con revisión y QA conformes para iniciar código. La implementación indicada en la tabla es futura.

| Ruta real | Cambio mínimo recomendado | Tipo |
|---|---|---|
| `docs/decisiones/ADR-0037-avance-tecnico-condicionado.md` | Registrar O2 si root la elige, autoría de decisión del orquestador bajo delegación previa; 0037 no ocupado en listado observado, revalidar al publicar | Nuevo propuesto |
| `docs/decisiones/README.md` | Enlazar ADR | Modificado propuesto |
| `docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md` | CA-01: separar arranque técnico mock de aceptación final con M0 cerrado y capacidades verificadas; enlace al diseño/ADR, mantener dependencia de aceptación | Modificado propuesto |
| `docs/roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md` | Sustituir bloqueo de inicio por gate técnico y gate de release; mantener fases y requisitos | Modificado propuesto |
| `docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md` | Cabecera y T-01: dependencia de contratos/mock disponibles más ADR de secuenciación aceptado por root; T-04 I-01 y T-16 gates reales explícitos, sin cierres ahora | Modificado propuesto |
| `docs/roadmap/2026-09-28-m1-mvp-estudio/test-plan.md` | Etiquetar ámbito de evidencia, preservar M-01/02/03; casos negativos de tarea/feature no verificada, sin nueva plataforma QA | Modificado propuesto |
| `docs/roadmap/README.md` | Distinguir apertura técnica de aceptación secuencial conservando umbrales de uso real | Modificado propuesto |
| `docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md` | Root armoniza únicamente frase T-10 «M1 no puede empezar» como gate de aceptación real; no toca criterios de T-13 ni estado M0 | Modificado propuesto |
| `apps/server/app/`, `apps/server/pyproject.toml`, `apps/server/Dockerfile`, `docker-compose.yml` | Handoff T-01: app/settings/security/errors/logging y servicio server sin torch, sin cambiar engines activos; scaffold usa paquete `app`, respetarlo | Implementación futura |
| `apps/server/models/`, `apps/server/alembic/`, `apps/server/backup.py`, `packages/contracts/song-v1.schema.json` | T-02, esquema íntegro ya requerido; no seleccionar motor | Implementación futura |

Dependencias: T-01 → T-02/T-03; T-02 → T-04 → T-05/T-06 → T-07; T-03 → T-08; T-07/T-08 → flujos web; T-15 → T-16, con gates reales adicionales de aceptación. No confundir el paralelismo descrito por el plan con una autorización para ignorar dependencias del ledger.

**Handoff de código T-01, solo después de resolución de root:** implementar requisitos existentes de settings `STUDIO_*`, mapa engines, Host/Origin/CORS cerrados incluido SSE, problem+json, logs JSON rotados sin secretos ni letras, token persistente generado una sola vez y enviado internamente, imagen y Compose sin torch con rutas persistentes y nombres internos. TDD y revisión A/B, Nemesis/lente C por seguridad; cobertura vigente del proyecto. No añadir settings/proveedores de M2, scheduler nuevo, nuevas capacidades ni gestión de Ollama. Verificaciones exactas de T-01 y evidencia Docker pendientes de ejecución por los agentes autorizados.

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Mock verifica todas las tareas, ocultando indisponibilidad real | Alta | Alto | Fixture con tarea/feature false: resolver rechaza y UI deshabilita con motivo; no alterar descriptor ACE-Step |
| QA CPU presentada como Docker acreditado | Media | Alto | Evidencia separada de build/arranque Compose real sin GPU; no cierre T-01/T-08 por lectura del YAML |
| CA compartidos M-01 o I-01 perdidos al cerrar tareas | Media | Alto | Anotar ámbito de aceptación en canónicos antes del cierre; conservar lo pendiente en T-16 y T-04 respectivamente |
| Cambios Compose o carga CPU perturban GPU160 | Media | Alto | No recrear servicios engines activos, no cambios sellados; root coordina ejecución posterior y limita carga si altera observación |
| Primer esquema incompleto obliga migración rompedora | Media | Alto | T-02 toma todas las tablas de datos.md, incluso vacías de hitos posteriores |
| Contradicciones documentales heredadas | Alta | Medio | ADR-0035 prevalece: contrato §6 aún cita llama.cpp, ADR-0017 cita FFmpeg Windows y scaffold cita M0/T-06; root corrige lo necesario en su ownership sin reabrir la decisión |
| Uso sintético contado como ≥30/≥100 generaciones reales | Media | Alto | Conservar umbrales de uso y aceptación del roadmap; no sumar mocks como evidencia musical |

## 7. Preguntas abiertas

La decisión de secuenciación está resuelta: O2 y ADR-0037, elegidas por el orquestador bajo delegación previa. Revisión A/B y QA documental conformes; la implementación conserva sus gates propios. No se atribuye al propietario una elección específica de O2.

Siguen abiertas I-01, las capacidades reales de T-10, la elección/escucha T-13 y las validaciones Docker/GPU/UI/backup que todavía no se han ejecutado. No impiden redactar o construir unidades independientes una vez conforme la revisión documental, pero sí sus cierres que incluyan tales criterios. No se estima esfuerzo ni se aprueban funcionalidades nuevas mediante esta decisión.

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-10-07 | Tres secuenciaciones comparadas; O2 elegida por el orquestador bajo delegación, ADR-0037 y gates publicados |


## Resolución del orquestador — 2026-10-07

O2 elegida bajo delegación previa. [ADR-0037](../../decisiones/ADR-0037-avance-tecnico-condicionado.md) y gates canónicos publicados; revisión y QA documental conformes antes de iniciar código. La propuesta histórica y sus originales se conservan privados; no se afirma una elección específica del propietario.


## Ampliación decidida del postproceso CPU

[ADR-0055](../../decisiones/ADR-0055-ejecucion-cpu-y-publicacion-durable-por-toma.md) adopta P1: un post agregado con resultados durables/publicación por toma. Sustituye cualquier interpretación all-or-nothing anterior. La ejecución local tiene contrato y autoridad propios, historial inmutable de publicación y reconciliación FS/SQLite; el análisis depende de la toma confirmada y de su causa real. Primero se implementan contrato/migración/snapshots, después runtime, procedencia, publicación, beats y Docker. Esta decisión no cierra ningún criterio de T-05.


## Ampliación decidida del stream SSE

[ADR-0056](../../decisiones/ADR-0056-sse-con-buffer-y-recuperacion-de-estado.md) adopta O1: bus existente con ring y recuperación del estado, manteniendo terminales/seq de engine y el API interno publish/buffer. U1 limitada a bus y framing; integración posterior con barrera de writers, autorización, contrato API, snapshots y cliente. Un bus aislado no acredita GET/api/events ni reconexión tras reinicio. No tabla outbox ni broker adicional.
