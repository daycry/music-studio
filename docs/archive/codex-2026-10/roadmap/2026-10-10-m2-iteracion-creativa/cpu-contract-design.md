---
design: m2-t01-cpu-contract
titulo: "Procedencia CPU duradera en Take y contratos históricos"
estado: aprobado
creado: "2026-10-10"
actualizado: "2026-10-11"
spec: spec.md
evaluacion: n/a
plan: improvement-plan.md
diseno_padre: design.md
adr: ../../decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md
opcion_elegida: O1
validada: "2026-10-10"
autoridad: "elección del orquestador bajo delegación autónoma del propietario"
generacion:
  fuente: estimado
  tokens_reales: null
  eur: null
  nota: "El medidor no dispone de transcripción atribuible a este agente; no hay medida real de tokens ni coste."
---

# Diseño — Procedencia CPU duradera en Take

> **Spec:** [spec.md](spec.md), aprobada · **Plan:** [improvement-plan.md](improvement-plan.md) · **Diseño padre:** [O2](design.md) · **ADR:** [ADR-0074](../../decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md), aceptada por el orquestador tras revisión 2 y QA documental 16/16.

| Campo | Valor |
|---|---|
| Estado | Aprobado; segunda pasada orquestada de M2/T-01 |
| Opción elegida | O1 — Take discriminado y contratos CPU versionados |
| Validación | `elegida: O1`, orquestador el 2026-10-10 bajo delegación autónoma del propietario |
| Alcance ejecutado | Diseño, ADR propuesta y verificación documental; TDD n/a: prosa |

## 1. Contexto y restricciones

M2 necesita registrar recortes, fades y crossfades como nuevos `Take` de la misma canción. El resultado conserva aristas, raíz canónica y assets. No cambia el maestro automáticamente. Esta decisión concreta la frontera CPU de O2; no reemplaza el diseño general.

El texto de CA-29 leído durante el diseño exige manifiesto v1 y compatibilidad M1. CA-32 exige evidencia y puertas independientes. El orquestador eligió O1 y la adaptación explícita de CA-29 para CPU v2, preservando los demás requisitos. La aceptación del ADR y la sincronización de Constitución, datos, pipeline, spec y plan preceden a la implementación. Son responsabilidad del orquestador; esta segunda pasada no modifica esos documentos.

**Fronteras verificadas en el repositorio**

| Frontera | Evidencia vigente | Consecuencia |
|---|---|---|
| Identidad de toma | `apps/server/app/models/__init__.py:149`; SQL baseline `apps/server/app/migrations/versions/0001_schema.sql:111` | `model_id`, `model_version` y `seed` son NOT NULL. No existe columna engine en Take. |
| Codificación de semilla | `apps/server/app/models/__init__.py:30`; SQL baseline `:143` | Seed se almacena como texto decimal y se expone como entero. `0` es una semilla válida, no un marcador de ausencia. |
| Plan y paquete | `apps/server/app/worker/contracts.py:389`, `:464`, `:538` | PostPlan v1 exige procedencia de engine, generación y autoridad con intento ganador/semilla. PreparedPackage incorpora esa autoridad. |
| Ejecución CPU M1 | `apps/server/app/models/__init__.py:535`; `apps/server/app/migrations/cpu_publication_invariants.py:95` | Su cómputo es CPU, pero su autoridad fuente sigue siendo una inferencia. El nombre de tabla no acredita un edit autónomo. |
| Intención durable | `apps/server/app/models/__init__.py:556`, `:571` | La raíz exige seed; la revisión exige generación, ganador, ordinal, seq, SHA terminal y seed. |
| Guardas SQL/ORM | `apps/server/app/migrations/cpu_publication_invariants.py:433`, `:513`, `:570`, `:609`, `:746` | Las guardas relacionan esos valores con engine, post, toma e historial. Nullable aislado dejaría esas guardas incoherentes. |
| Publicador | `apps/server/app/worker/publications.py:64`, `:115`, `:394`, `:455` | Captura y revalidación consultan JobAttempt. Su fase de commit/replay utiliza intención, paquete y CAS. |
| Manifiesto v1 | `packages/contracts/manifest-v1.schema.json:177`, `:243`, `:252` | `pipeline.engine_id/engine_version` son strings requeridos; `request.seed` es entero requerido. `models` permite lista vacía. |
| Emisión/verificación | `apps/server/app/worker/packages.py:154`; `packages/audio-post/audio_post/manifest.py:77` | El emisor fija v1 y un generator; el verificador carga solamente su schema v1. |
| Snapshot | `packages/contracts/song-v1.schema.json:477`; `apps/server/app/snapshots.py:33`, `:255`, `:453` | El snapshot v1 exige modelo/versión string y seed integer. La validación y emisión fijan versión 1. |
| API y UI | `apps/server/app/domain_routes.py:145`, `:214`; `apps/web/components/ProvenancePanel.tsx:12` | El DTO ya admite null para versión/seed, pero no para model_id. La UI muestra model_id como modelo. |

La Constitución §2 exige migraciones aditivas y crecimiento v1 únicamente mediante campos opcionales. ADR-0041 fija DAG, raíz mínima entre originales y snapshots derivados. ADR-0055 fija autoridad y custodia durable M1. Este diseño no reabre su comportamiento histórico; propone excepciones acotadas para el origen nuevo.

Las migraciones 0001–0006, los manifiestos emitidos y los recibos M1 quedan intactos. Las extensiones se aplicarán después del head real que encuentre el implementador. El orquestador reservó ADR-0074; esta pasada no reserva un número de migración.

## 2. Opciones (2)

### O1 — Take discriminado y contratos CPU versionados, elegida

La BD conserva un único Take. Añade `origin_kind` con valores `inference` y `cpu_edit`, y una referencia verificable a procedencia CPU. Relaja los tres campos únicamente bajo la rama CPU. La inferencia histórica y nueva sigue exigiéndolos.

La autoridad privada CPU utiliza plan/paquete tipados nuevos. Los lectores despachan por versión/handler y conservan PostPlan v1. El Publisher comparte su fase final tras validar cada autoridad. No convierte un edit en un intento de engine.

Los manifiestos de resultados CPU autónomos usan versión 2, incluidos edits y previews sin nueva toma. Su procedencia declara ejecución del server, receta y herramientas; no contiene modelo ejecutado ni semilla de inferencia. Los lectores aceptan v1 histórico y v2 CPU. Las canciones cuyo cierre portable contiene CPU usan `song.json` versión 2; las demás conservan proyección v1. El post M1 de una inferencia conserva autoridad y manifiesto v1, aunque el post-proceso corra en CPU.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: migración condicionada, autoridad nueva y lectores multiversión; un único dominio Take y publicador final compartido. |
| Riesgo | Migración y export/import multiversión. Los lectores antiguos rechazan el nuevo CPU mediante una versión desconocida explícita. |
| Coste relativo | L: schemas/copies v2 y distribución coordinada de lectores. No incluye horas ni presupuesto. |
| Reversibilidad | Media: retirar capacidad CPU es posible; downgrade sin pérdida se rechaza si existen tomas CPU. Los históricos permanecen utilizables. |

**Excepciones necesarias:** relajación SQL delimitada; CA-29 pasa a permitir v2 para origen CPU conservando v1 histórico. No cambia la regla de crecimiento de v1.

### O2 — Take discriminado y ampliación condicional de v1, descartada

La BD y la autoridad privada utilizan la misma discriminación honesta que O1. El manifiesto conserva versión 1 y añade `origin_kind` y procedencia CPU opcionales. Amplía los tipos de `request.seed` y `pipeline.engine_id/engine_version` para permitir null solamente en la rama CPU.

Sin discriminador, el lector aplica la rama histórica: seed entero y campos engine string. En CPU exige seed/engine null, modelos ejecutados vacíos y procedencia propia válida. Los antecedentes permanecen en inputs/lineage identificados; nunca rellenan los campos de ejecución.

El snapshot v1 amplía condicionalmente Take y las autoridades privadas. Su lector nuevo acepta datos M1. Un lector v1 antiguo rechaza la nueva rama aunque el número de versión sea conocido. Las extensiones opcionales por sí solas no logran esta representación.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: mantiene un schema de salida, pero añade condiciones históricas/CPU y selección privada de autoridades. |
| Riesgo | Mismo número de versión con tipos diferentes. Un consumidor puede asumir capacidades que su schema no admite. |
| Coste relativo | M: menos schemas nuevos; exige actualizar igualmente DTOs, imports, verificadores y lectores. |
| Reversibilidad | Baja: volver al schema v1 anterior deja manifiestos CPU v1 emitidos que ya no acepta. No pueden reescribirse. |

**Excepciones necesarias:** relajación SQL delimitada y excepción explícita a «v1 sólo crece con campos opcionales». Hay compatibilidad de datos antiguos hacia lector nuevo, no compatibilidad completa entre todos los lectores v1.

**Alternativas eliminadas antes de comparar:** almacenar `0`, string vacío o identidades CPU como modelo/engine; copiar la semilla/modelo del padre como ejecución; crear `cpu_take` paralelo. Las primeras falsean procedencia. La última rompe el Take común y sus relaciones.

## 3. Criterios de decisión

1. La ejecución declarada coincide con la ejecución real. CPU no tiene intento ganador de engine, modelo musical ni semilla ejecutada.
2. El lector nuevo acepta historias M1 sin backfill, cambio de hashes ni modificación de planes/manifiestos emitidos.
3. SQL, ORM, DTO, snapshot, paquete y manifiesto aplican la misma rama; no basta comprobar solamente el JSON final.
4. Se conserva una toma, sus múltiples padres, la pertenencia y la promoción explícita a maestro.
5. Una incompatibilidad nueva se declara y detecta. La reducción de cambios no justifica reutilizar una versión con significado distinto.
6. La excepción autoriza sólo la frontera CPU. No permite relajar las exigencias de inferencia ni reconstruir tablas arbitrarias.

### Matriz de compatibilidad

O1 es la opción elegida. La columna O2 conserva la comparación de la alternativa descartada; no constituye autorización para ampliar los tipos v1.

| Caso | O1 | O2 | Evidencia/límite |
|---|---|---|---|
| Take histórico con tres valores | Sin transformación de valores | Sin transformación de valores | NOT NULL actual comprobado; equivalencia de migración aún pendiente. |
| Inferencia sin cualquiera de los tres | Rechazo obligatorio SQL/ORM/DTO/import | Igual | CHECK debe usar `IS NOT NULL`; no depender del resultado UNKNOWN. |
| CPU con modelo/versión/seed null | Rama SQL/DTO CPU; snapshot v2 | Rama SQL/DTO CPU; snapshot v1 ampliado | ADD origin aislado sigue fallando `take.model_id`. |
| PostPlan/paquete M1 | Lector v1 original | Lector v1 original | Versionado privado nuevo no reserializa ni recalcula hashes M1. |
| Intención de inferencia histórica | Conserva ganador, semilla y causalidad | Igual | Guardas equivalentes obligatorias antes/después. |
| Intención CPU nueva | Sin campos engine; autoridad propia | Igual | Requiere relajar también raíz/revisión y reemplazar condiciones, no sólo Take. |
| Manifiesto M1 leído por lector nuevo | Despacho v1 intacto | Rama histórica preservada | Fixture v1: 0 errores con schema actual; rama O2 experimental también acepta. |
| CPU leído por lector v1 antiguo | Versión no soportada, rechazo explícito | Versión conocida, schema incompatible | Sonda O2 rechaza seed/engine null en schema original. No prometer compatibilidad descendente. |
| CPU sin seed en schema v1 actual | No se utiliza para CPU | No válido | `'seed' is a required property`, reproducido. |
| CPU seed null en schema v1 actual | No se utiliza para CPU | Requiere ampliación condicional | `None is not of type 'integer'`, reproducido. |
| Preview A/B CPU sin nueva Take | Manifiesto v2 con sujeto job autorizado; sin identidad inferida | Exigiría la misma relajación v1 descartada | No fabricar Take, JobAttempt ni intención por toma para encajar el temporal. |
| Post CPU M1 de generación real | Conserva autoridad de inferencia y manifiesto v1 | Igual | El dispositivo de post no cambia el origen musical. |
| Inferencia seed null en schema O2 candidato | n/a | Sigue rechazada | Sonda sólo de identidad; no valida autoridad/custodia completas. |
| Song histórica v1 | Lector v1; se omiten nuevas columnas por defecto al proyectar | Igual | No añadir origin por defecto a JSON histórico ni cambiar digest de filas. |
| Song con CPU y antecesores M1 | Snapshot v2 con ambas ramas | Snapshot v1 ampliado | El cierre incluye padres, assets y nuevas autoridades; no elimina historia para hacerla importable. |
| API M1, toma de inferencia | DTO/operación originales intactos | Igual | `_OPENAPI_TAKE.model_id` sigue string. |
| API M1, toma CPU o listado que la incluye | 409 CONFLICT explícito; no devuelve DTO incompatible | Igual | Comprobar antes de efectos en PATCH/restore. No omitir CPU del listado. |
| API nueva, historia mixta | Operaciones aditivas `/api/v2/...`, DTO discriminado | Igual | Sonda OpenAPI: tres paths/cuatro operaciones nuevos, 0 rompedores. |
| Downgrade con CPU durable | Rechazo previo sin efectos | Rechazo previo sin efectos | Recuperación mediante backup/lector compatible; nunca borrar tomas para permitir downgrade. |
| Engine `/v1` | Sin cambios por esta frontera | Igual | La receta CPU es privada del server, no un engine sintético. |

## 4. Recomendación · opción elegida y por qué

**Recomendación del arquitecto: O1.** La versión nueva expresa una ejecución nueva sin redefinir v1. Conserva sus validadores históricos y permite rechazar incompatibilidad antes de interpretar identidades. Su mayor coste relativo responde a una frontera real.

**Opción elegida: O1, por el orquestador el 2026-10-10 bajo delegación autónoma del propietario.** El orquestador revisó el diseño, la matriz y las sondas SQLite/API. La elección prioriza identidad real, historia M1 intacta y versionado explícito. No se atribuye al propietario lectura ni elección personal de O1.

**Descartada: O2.** Conserva menos schemas, pero exige cambiar tipos requeridos manteniendo el número de versión. Su menor coste relativo no compensa esa excepción adicional. La sonda sólo demuestra compatibilidad histórica de su rama experimental de identidad; el lector v1 anterior sigue rechazando CPU.

### Contrato elegido de O1

Las ramas y reglas siguientes forman parte de la elección. Los nombres de tipos, handler y campos privados nuevos se concretarán antes del RED respectivo. No son símbolos ya implementados.

| Elemento | Inferencia, incluida historia M1 | CPU edit |
|---|---|---|
| `Take.origin_kind` | `inference`; default SQL, omitible en proyección histórica | `cpu_edit`, obligatorio explícito |
| `Take.model_id/model_version/seed` | Tres valores obligatorios; formato y límites existentes | Tres NULL; rechazar valores heredados o sentinelas |
| `Take.job_id` | Job de generación histórico | Job CPU que crea la toma; task privada propuesta `audio.edit` |
| `Take.derivation/root_id/song_id` | Semántica vigente | `edit`, misma song; raíz mínima entre originales alcanzables |
| Antecedentes | Aristas originales | Una arista `source` o dos `crossfade_a/crossfade_b`; mapas efectivos ligados a cada arista |
| Procedencia CPU | No requerida retroactivamente | Recipe version/hash, padre+asset+hash, derechos, herramientas/pins y referencias de ejecución/resultados |
| `cpu_execution.plan` | PostPlan v1; hash y serialización originales | Plan CPU versionado, handler explícito; validación y cierre de hijo propios |
| `publication_intent.seed` | Entero obligatorio | NULL |
| `revision.generation_job_id/winning_attempt_id/winning_ordinal/terminal_seq/terminal_sha256/seed` | Obligatorios y ligados al ganador histórico | NULL; ningún FK a un JobAttempt inventado |
| `revision.cpu_execution_id/post_job_id/take_id` | Valores actuales | Valores propios comprobados; el nombre histórico post_job_id no convierte el trabajo en inferencia |
| SHA de autoridad | Procedencia congelada M1 | Procedencia CPU congelada; conserva recipe/result SHA como hechos distintos |
| Fuente de post | Salida cruda ganadora | Salida realmente renderizada y hash verificado; puede coincidir con el SHA de un padre |
| Publicación | Intención CAS, no-clobber, paquete exacto y assets/ready/committed | Mismas garantías finales, después de comprobar autoridad CPU |
| Maestro | Cambio explícito | Nunca cambia por confirmación de edit |

La BD añade discriminación equivalente en raíz/revisión. Las ramas exigen coherencia entre sí, ejecución y Take. La unicidad histórica `(intent_id,generation_job_id,winning_attempt_id,output_index)` sigue protegida para inferencia. CPU necesita unicidad propia por intención, ejecución y salida; los NULL no deben permitir duplicados.

La receta se captura antes de ejecutar. Su hash no prueba terminación. Un resultado CPU sellado vincula execution, receta, fuentes y salida. La custodia `UNKNOWN` bloquea publicación, limpieza y liberación del slot. Los padres pueden ser CPU o inferencia; su cadena histórica no sustituye esta autoridad. Cada edit conserva nueva ejecución, Take y asset con IDs propios y custodia comprobada. La salida puede tener el mismo SHA que un padre; esa igualdad no sustituye la autoridad propia.

O1 mantiene manifests v1 de inferencia. El v2 CPU declara provider local, executor del server y herramientas reales; no incluye generator ni controles de inferencia. Los inputs referencian padres con sus hashes/declaraciones. `commercial_use` combina entradas y herramientas sin inferir derechos por `models=[]`.

La alternativa descartada O2 habría usado NULL para engine/seed dentro de v1. O1 no realiza esa ampliación: emite CPU con versión 2 y conserva v1.

### Resultados CPU sin nueva Take

Las previews A/B son resultados CPU del job de comparación, no nuevas versiones musicales. Utilizan manifiesto versión 2, sujeto job autorizado y referencias de ambos masters/hashes/derechos. Registran receta, política de nivel, herramientas/pins, mediciones y resultado propio. No incluyen modelo, engine o semilla ejecutados.

No crean `take`, no promueven maestro y no modifican manifests de los padres. `publication_intent` y `publication_intent_revision` exigen Take: el preview no crea una fila ficticia para satisfacerlas. El contrato tipado de ejecución/resultado temporal debe validar autoridad job/ejecución, CAS, custodia y cierre antes de servir.

`asset.subject_type` no acepta `job` en el schema actual (`apps/server/app/models/__init__.py:210`). O1 no amplía esa tabla ni introduce un asset con sujeto inválido. El temporal se resuelve desde el contexto/recibo privado del job y su manifiesto, con pertenencia, hashes e invalidación de acceso. Si una implementación quisiera persistir assets job, necesitaría una decisión adicional fuera de la excepción de estas tres tablas.

La versión final del plan/recibo temporal y su publicación se fija antes del RED de previews. Debe impedir servir un resultado parcial y conservar el slot/staging mientras la custodia sea UNKNOWN. No hereda de un padre la prueba de ejecución. Un cierre portable que incluya autoridad CPU usa snapshot v2; un temporal no inserta datos artificiales en `song.json` para aparentar una Take.

Esta regla también distingue el post M1 de generación real. Ese post tiene un ganador musical válido: conserva PostPlan v1, recibos, intento ganador, modelo/semilla y manifiesto v1. La ejecución CPU de su post no lo transforma en `cpu_edit`.

### API server compatible mediante operaciones aditivas

O1 mantiene el DTO M1 y las operaciones existentes. Cambiar `model_id` de string a nullable en la misma respuesta constituye un cambio rompedor; el lint lo reproduce. El versionado del manifiesto no resuelve por sí solo esta incompatibilidad.

La elección añade tres paths nuevos con cuatro operaciones durante implementación. Comparten autorización, selección de filas y reglas de negocio, pero usan un DTO nuevo discriminado. La web M2 consume estas operaciones para cualquier toma; no intenta una conversión silenciosa al DTO M1.

| Operación propuesta, todavía no implementada | Contrato |
|---|---|
| `GET /api/v2/takes/{take_id}` | TakeV2: origin inference conserva tres valores; origin CPU exige los tres NULL y su procedencia verificable. |
| `GET /api/v2/songs/{song_id}/takes` | Listado íntegro de inferencia y CPU autorizadas, con el orden vigente y ambos tipos. |
| `PATCH /api/v2/takes/{take_id}` | Misma edición de metadatos y ownership; respuesta TakeV2. No altera audio ni la autoridad congelada. |
| `POST /api/v2/takes/{take_id}/restore` | Misma restauración autorizada; respuesta TakeV2, sin inventar modelo. |

Las operaciones M1 de detalle, listado, PATCH y restore conservan sus respuestas exitosas para inferencia. Ante una toma CPU devuelven el 409 y `code: CONFLICT` que ya declara `_responses()` en `domain_routes.py:260`. El detalle explica la necesidad de API v2 y puede incluir `Link` hacia la operación equivalente. No introduce un código desconocido obligatorio en ProblemDTO.

El listado M1 rechaza la solicitud completa si su selección autorizada contiene una toma CPU. No devuelve una lista aparentemente íntegra después de eliminarla. Las comprobaciones se realizan tras autorización y antes de serialización. PATCH y restore rechazan antes de cualquier cambio, incluso antes de entrar en su flujo de actualización efectivo.

Los endpoints de audio/master, borrado y promoción a maestro pueden mantener su contrato cuando la respuesta no incorpora Take. Conservan ownership, derechos, estado y semántica vigentes. No se versionan por analogía. Una futura operación que emita Take debe elegir explícitamente DTO M1 o TakeV2 y aplicar el mismo rechazo.

`packages/contracts/openapi.json` conserva todos los paths/DTO M1 y añade los nuevos. El contrato `/v1` de engines queda intacto. `apps/web/lib/api.ts:26` define manualmente `Take.model_id:string`; también debe mantener ese tipo M1 y añadir TakeV2. Regenerar `api.d.ts` sin adaptar este consumidor manual no basta.

La selección de API nueva no equivale a negociación heurística: el path es la versión. Cliente M1 que solicite contenido CPU recibe rechazo explícito; cliente M2 usa v2. No se exige actualizar un cliente antiguo para seguir leyendo canciones puramente M1.

### Excepción SQL delimitada de ADR-0074

El alcance elegido abarca `take.model_id/model_version/seed`, `publication_intent.seed` y `publication_intent_revision.generation_job_id/winning_attempt_id/winning_ordinal/terminal_seq/terminal_sha256/seed`. Permite relajarlos sólo con origen CPU explícito y nuevas guardas equivalentes. Conserva nombres, datos, IDs y checks históricos de inferencia. ADR-0074 queda aceptada por el orquestador tras revisión 2 y QA documental 16/16.

La migración agrega discriminadores y metadatos CPU mediante columnas nuevas. Si el SQLite fijado del producto necesita reconstrucción para quitar NOT NULL, el ADR autoriza exclusivamente esas tres tablas. Conserva índices, FK diferidas, triggers, referencias entrantes, unicidades e invalidación de snapshots. No modifica el baseline ni borra datos históricos.

El intérprete gestionado observado enlaza SQLite 3.53.1. Una sonda en memoria quitó NOT NULL con ALTER COLUMN. Esa capacidad aparece desde 3.53.0 según la [documentación oficial de SQLite](https://www.sqlite.org/lang_altertable.html).

El orquestador aportó una [sonda de contenedor](../../../.cache/dev-cycle/m2/sqlite-container-probe.json) sobre Python base con el mismo pin que el server. SQLite 3.40.1 rechazó ALTER COLUMN cerca de `ALTER` y conservó la fila histórica. La imagen de la sonda es `sha256:1c18c0ef8ed31d824452f8f3d449f93700c1f26fabd90c4ca0c7c69190df719d`. Es evidencia recibida del orquestador, no una ejecución Docker de este agente. No acredita la futura imagen server integrada.

El implementador debe verificar la imagen fijada y probar una estrategia determinista soportada. Para reconstrucción, sigue la secuencia segura crear/copy/drop/rename, conserva objetos asociados y verifica FK antes del commit. Evita renombrar primero la tabla vieja. SQLite documenta esas operaciones; [Alembic batch](https://alembic.sqlalchemy.org/en/latest/batch.html) ofrece el mecanismo de copia, pero requiere tratar checks, triggers y FK explícitamente.

La migración requiere acceso exclusivo, backup verificado y rollback completo ante error. Restaura `foreign_keys=ON` antes del runtime. La prueba usa datos temporales poblados, referencias entrantes y ciclos diferidos. Downgrade no destruye datos CPU: rechaza con un motivo antes de alterar schema.

### Invariantes y condiciones previas a la implementación

| Invariante elegido | Evidencia requerida en su unidad de implementación |
|---|---|
| Inferencia conserva los tres campos y causalidad ganadora | Negativos ORM/SQL/import para cada NULL; checks explícitos y regresiones M1. |
| CPU no declara una ejecución de engine | Negativos para modelo/seed/ganador heredados, sentinelas y referencias de intento ficticias. |
| Una Take por resultado musical, múltiples padres reales | Pertenencia, ciclos, crossfade de dos raíces, mapas por arista y raíz canónica sin perder padres. |
| Publicación por toma con historial y CAS | Duplicados CPU, retry sólo fallido, ready inmutable, no-clobber y replay de ventanas archivos/BD. |
| UNKNOWN no autoriza efectos | Probar bloqueo de publicación, serving, limpieza y liberación del slot/staging hasta cierre comprobado del grupo propio. |
| Reconstrucción limitada a tres tablas | Inventario de FK entrantes/diferidas, checks, índices, triggers e invalidación; equivalencia antes/después sobre BD poblada. |
| Backup previo íntegro y restaurable | Backup SQLite consistente con WAL, comprobación de integridad/FK y restauración real en destino temporal propio. |
| Migración exclusiva y reversible ante fallo | Sin workers/leases activos; rollback de cada ventana; FK ON antes de runtime; downtime explícito. |
| Downgrade no pierde CPU | Rechazo sin efectos si existen tomas/autoridades CPU no representables; recuperación por backup compatible. |
| Contratos históricos estables | Bytes/hashes de planes/recibos/manifest v1 intactos, snapshots inferencia equivalentes, v2 mixto exportable/importable. |
| API no cambia DTO M1 ni oculta filas | Lectura M1 de inferencia igual, CPU 409 explícito; PATCH/restore sin efecto antes de rechazo; listado v2 íntegro. |

Son gates futuros, no pruebas ejecutadas en esta pasada. Los contratos tipados se fijan antes del RED de cada unidad. Las preguntas de implementación no reabren ni bloquean la selección de O1.

## 5. Impacto en módulos y ficheros

| Ruta real | Cambio elegido para O1, pendiente de implementación | Alcance |
|---|---|---|
| `apps/server/app/models/__init__.py` | Discriminación Take/intenciones; nullable sólo CPU; tipos de plan/paquete y seed coherentes | Modificado |
| `apps/server/app/migrations/versions/` | Migración posterior al head real; preservar 0001–0006 | Fichero nuevo |
| `apps/server/app/migrations/cpu_publication_invariants.py` | Ramas ORM/SQL, autoridad, unicidad CPU, inmutabilidad y CAS | Modificado |
| `apps/server/app/migrations/initial_invariants.py` | Referencia para preservar linaje, raíces y pertenencia durante migración; no rehacer baseline | Lectura; cualquier extensión posterior exige alcance propio |
| `apps/server/app/migrations/env.py` | Acceso exclusivo y estrategia FK/transacción si la reconstrucción lo necesita | Cambio condicional |
| `apps/server/app/worker/contracts.py` | Conservar PostPlan v1; nuevas variantes CPU y resultados/paquetes discriminados | Modificado |
| `apps/server/app/worker/planning.py` | Planificación CPU independiente de un terminal de engine; receta y referencias selladas | Modificado |
| `apps/server/app/worker/publications.py` | Captura/revalidación por origen; reutilizar fase de publicación durable sin saltarse autoridad | Modificado |
| `apps/server/app/worker/packages.py` | Emisión CPU honesta y verificaciones de autoridad; conservar emisor M1 | Modificado |
| `packages/audio-post/audio_post/manifest.py` | Dispatch v1/v2; derechos, privacidad y hashes de ambas versiones | Modificado |
| `packages/audio-post/audio_post/private_context.py` | Lector del recibo CPU y despacho; preservar recibos M1 sin volver a sellarlos | Modificado |
| `packages/contracts/manifest-v1.schema.json` y `packages/audio-post/audio_post/manifest-v1.schema.json` | Conservar copias v1; distribuir v2 como schema nuevo | Intactos |
| `packages/contracts/song-v1.schema.json` y `apps/server/app/models/song-v1.schema.json` | Conservar copias v1; distribuir v2 como schema nuevo | Intactos |
| `apps/server/app/snapshots.py` | Dispatch, proyección, hash, cierre e importación de ambas autoridades; omitir defaults nuevos históricos | Modificado |
| `apps/server/app/domain_routes.py` | DTO/operaciones M1 intactos; añadir operaciones v2 y DTO discriminado; rechazo 409 de CPU antes de efectos M1 | Modificado |
| `packages/contracts/openapi.json` y `apps/web/lib/generated/api.d.ts` | Regenerar desde código; comprobar delta contractual | Generados |
| `apps/web/lib/api.ts` | Conservar Take M1; añadir TakeV2 y llamadas de la web M2 a paths v2 | Modificado |
| `apps/web/components/ProvenancePanel.tsx` | Presentar edición CPU y antecedentes por separado; no mostrar modelo ejecutado inexistente | Modificado |
| `scripts/verify_manifest.py` | Aceptar versiones soportadas mediante verificador; rechazo claro a versión desconocida | Modificado/validado |
| `apps/server/tests/test_worker_snapshots.py` y `apps/server/tests/test_snapshot_synthetic_provenance.py` | Conservar regresiones M1; extender con historias mixtas y hashes estables | Tests posteriores |
| `docs/arquitectura/datos.md`, `docs/arquitectura/pipeline-audio.md`, `docs/CONSTITUTION.md` | Documentar campos y excepciones; O1 además adapta CA-29 en spec/plan por orquestador | Fuera del ownership de esta pasada |

O1 añadirá schemas v2 en los mismos directorios de distribución de cada v1 y sus lectores. Las rutas nuevas todavía no existen. Se declaran como artefactos nuevos, no como evidencia del repo.

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Excepción constitucional implícita | Alta si se implementa directamente | Alto | ADR aceptado y documentos afectados actualizados antes de escribir producto. |
| SQLite host distinto del Docker fijado | Alta | Alto | Registrar ambas versiones; probar migración en imagen real sin sustituir herramientas ni asumir capacidades. |
| CHECK con NULL permite inferencia incompleta | Alta | Alto | Predicados con IS NOT NULL y negativos por ORM, SQL directo e import. |
| NULL elimina unicidad causal CPU | Media | Alto | Restricción/índice específico de rama CPU y pruebas de duplicados/retry. |
| Guardas/triggers se pierden al reconstruir | Media | Alto | Inventario previo y comparación posterior; tests SQL de linaje, snapshots, ready e historia. |
| Rehash/backfill transforma M1 | Media | Alto | Omitir defaults históricos al proyectar; fixtures bytes/hash, planes y recibos write-once intactos. |
| Modelo/seed del padre aparece como ejecución | Alta si se reutiliza contexto M1 | Alto | Rama CPU rechaza esos valores y UI distingue antecedentes identificados. |
| API M1 recibe model_id null o pierde filas CPU | Alta sin separación de DTO | Alto | Operaciones v2 aditivas; M1 rechaza CPU explícitamente sin filtrar ni mutar primero. |
| Snapshot mixto pierde un padre o authority | Media | Alto | Crossfade de dos raíces, padre CPU e inferencia y export/import de cierre completo. |
| Resultado CPU se publica sólo por estar presente | Media | Alto | Receta/resultado propio, CAS vigente y cierre de custodia antes del publicador final. |
| Cambio de versiones excede alcance evaluado | Media | Medio | Evaluación propia no disponible en esta carpeta; orquestador valida impacto antes de ejecución. No se inventan horas. |

### Evidencia ejecutada y alcance de verificación

Con `scripts/env.ps1` cargado se ejecutó `python .cache/dev-cycle/m2/t01-cpu-contract-20261010/architect/contract_probe.py`. Exit 0. El [recibo](../../../.cache/dev-cycle/m2/t01-cpu-contract-20261010/architect/contract-probe.json) conserva once hashes de fuente, versión SQLite y resultados. La sonda usa exclusivamente SQLite en memoria y validación JSON Schema.

| Comprobación | Salida real |
|---|---|
| NOT NULL Take | `model_id=true, model_version=true, seed=true` |
| Insert CPU baseline / tras ADD origin | Ambos: `NOT NULL constraint failed: take.model_id` |
| ALTER COLUMN host | `supported on current managed SQLite`; NOT NULL de model_id pasa a false en memoria |
| ALTER COLUMN base Docker, recibo del orquestador | SQLite `3.40.1`; `OperationalError: near "ALTER": syntax error`; fila anterior intacta |
| Fixture v1 histórica | `historical_fixture_schema_errors=[]` |
| Seed CPU ausente / null | Rechazos required/type del schema v1 |
| Rama O2 experimental de identidad | Histórico aceptado, CPU null aceptado, legacy null rechazado y lector original rechaza CPU |
| Copias schemas actuales | `manifest_schema_copies_equal=true; song_schema_copies_equal=true` |
| OpenAPI candidato aditivo | Estructura exit 0; diff exit 0, `rompedores=0`; operaciones históricas exactamente iguales |
| model_id nullable en operación M1 | Diff exit 1, `rompedores=1`: `tipo cambiado en campo model_id` |

La [sonda API](../../../.cache/dev-cycle/m2/t01-cpu-contract-20261010/architect/api-candidate-probe.json) usa `custom-agents:api-contract` sobre candidatos privados. Agrega tres paths/cuatro operaciones y un DTO experimental; conserva los paths históricos exactamente iguales. Se ejecutó con el intérprete gestionado y exit 0 del controlador. El negativo rompedor produjo exit 1 del lint, como esperaba la sonda. El candidato verifica estructura y delta; su procedencia CPU aún no contiene el contrato completo y no sustituye la regeneración code-first posterior.

La rama O2 experimental amplía seed y los dos campos engine; no prueba el contrato CPU completo. No se ejecutó migración propuesta, publicación, render, custodia, integración Docker ni aceptación audiovisual. No se realizaron accesos GPU, WSL, descargas o cambios de datos.

`model-tier.py architect` resolvió `model=opus effort=high`; es metadata del plugin, no una afirmación de modelo ejecutado. `knowledge-find.py --tipo adr --contexto ...` terminó sin aciertos; se aplicaron las decisiones referenciadas en el brief. `usage-meter` degradó a estimado por falta de transcripción propia; tokens/coste reales permanecen null.

La elección O1 queda registrada en esta segunda pasada. El orquestador completó la verificación propia de T-01: matriz contrastada con fuentes y sondas, documentos compartidos integrados, ADR aceptada, revisión A/B intento 2 y QA documental independiente 16/16. El ledger registra el cierre contractual de T-01. No acredita migración, render, API o compatibilidad de producto implementados.

La segunda pasada verifica sólo documentación y fuentes actuales. Su [acta](../../../.cache/dev-cycle/m2/t01-cpu-contract-20261010/architect/second-pass/acta.md) registra la elección recibida y su alcance. El [recibo documental](../../../.cache/dev-cycle/m2/t01-cpu-contract-20261010/architect/second-pass/document-verification.json) registra hashes, enlaces, ausencia de placeholders y estabilidad de 22 fuentes protegidas. No se repiten sondas, tests de producto ni ejecuciones Docker.

## 7. Preguntas abiertas

La elección O1 está cerrada. Las preguntas siguientes concretan implementación antes del RED respectivo; no son nuevas puertas de selección T-01.

- ¿La futura imagen server confirma SQLite 3.40.1 del mismo Python base? La sonda del orquestador descarta ALTER COLUMN como solución portable sobre ese pin. Debe probarse la reconstrucción integral con sus FK/triggers, no sólo una tabla mínima.
- ¿El nombre de task/handler CPU será `audio.edit`? Es una propuesta privada; no existe una autorización para anunciarlo en engines `/v1`.
- ¿Qué versión y forma final tendrán CpuEditPlan, autoridad, paquete y recibo? Deben fijarse antes del RED de implementación, sin perder lector M1.
- ¿Dónde se almacenará la referencia CPU de Take y su SHA? Debe acreditar la ejecución durable y ser portable sin filtrar leases/PIDs.
- ¿Qué plan/recibo tipado y CAS publicarán previews job sin Take ni asset job? Se fijan antes de su RED; deben conservar serving, privacidad, temporal y custodia UNKNOWN.
- ¿Qué pruebas de upgrade con WAL, rollback, downgrade rechazado y restauración de backup acreditarán la excepción antes de integrar T-05/T-07?

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-10-10 | Primera pasada en borrador: dos opciones reales, fronteras reproducidas, recomendación O1 y elección pendiente. |
| 2026-10-10 | Segunda pasada: O1 elegida por el orquestador bajo delegación; diseño aprobado, ADR-0074 propuesta y previews CPU v2 explícitas. |


## Concreción privada de receta — T-02

El [contrato de receta](recipe-contract-design.md) y [ADR-0077](../../decisiones/ADR-0077-envelope-privado-de-recetas-creativas.md) concretan el envelope, los DTO y los lectores históricos. El contrato detallado está ratificado tras revisión A+B intento2 y QA documental18/18; no acredita implementación ni autoridad de publicación CPU. Los planes y recibos de ejecución conservan sus propias puertas antes del RED.


## Seam de composición T03 — propuesta compatible

[CompositionPlanV1](composition-contract-design.md) es un artefacto privado ligado al SHA de CapturedRecipe; no reemplaza CpuEditPlan, autoridad durable ni lectores históricos. Sus mapas resueltos todavía no acreditan audio efectivo. T04/T07 deberán concretar la proyección de convert; T08 ejecutará conversión, render y contraste medido. O1 elegida por ROOT espera revisión documental y QA antes de implementación.
