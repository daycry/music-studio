---
id: ADR-0074
titulo: Procedencia CPU y contratos versionados
estado: aceptada
fecha: 2026-10-10
iniciativa: m2-iteracion-creativa
design: ../roadmap/2026-10-10-m2-iteracion-creativa/cpu-contract-design.md
autoridad: elección del orquestador bajo delegación autónoma del propietario
---

# ADR-0074 · Procedencia CPU y contratos versionados

## Contexto

Take exige modelo, versión y semilla. La publicación M1 exige además generación, intento ganador y terminal de engine. Un edit CPU autónomo no posee esas identidades. El manifiesto v1 exige seed entero y campos engine string; su snapshot también exige los tres campos de Take.

[ADR-0073](ADR-0073-recetas-privadas-y-escucha-ab-de-iteracion-creativa.md) exige autoridad CPU honesta, pero todavía prescribe v1 para las previews A/B. Constitución §2 exige migraciones aditivas y artefactos con v1. La ampliación sólo mediante campos opcionales no puede representar las ausencias reales.

El [diseño comparado](../roadmap/2026-10-10-m2-iteracion-creativa/cpu-contract-design.md) presenta dos opciones. El orquestador eligió O1 el 2026-10-10 bajo delegación autónoma del propietario, tras revisar matriz y sondas SQLite/API. No se atribuye al propietario lectura o aprobación personal de este ADR. El diseño queda aprobado; este ADR queda aceptado por el orquestador tras revisión A/B intento 2 y QA documental independiente 16/16.

## Decisión

Se conserva una única Take y se añade origen `inference` o `cpu_edit`. CPU almacena NULL en modelo, versión y semilla; inferencia conserva los tres campos obligatorios. Resultados CPU autónomos utilizan manifiesto versión 2, snapshots CPU versión 2 y API server aditiva v2. Los históricos v1 conservan valores, bytes y significado.

### Excepción SQL precisa

Las tablas reales son `take`, `publication_intent`, `publication_intent_revision` y `cpu_execution`, declaradas en `apps/server/app/models/__init__.py`. La excepción de relajación/reconstrucción alcanza solamente las tres primeras:

| Tabla | Campos cuya ausencia se permite exclusivamente en CPU |
|---|---|
| `take` | `model_id`, `model_version`, `seed` |
| `publication_intent` | `seed` |
| `publication_intent_revision` | `generation_job_id`, `winning_attempt_id`, `winning_ordinal`, `terminal_seq`, `terminal_sha256`, `seed` |

Los discriminadores y metadatos CPU nuevos se añaden aditivamente. Las guardas SQL/ORM/import exigen coherencia entre Take, intención, revisión y ejecución. La rama inferencia sigue exigiendo cada campo y su ganador válido. Las comparaciones usan NULL explícito; no dependen del resultado UNKNOWN de un CHECK.

CPU no inserta un JobAttempt inventado, semilla 0, modelo vacío ni valores de un padre como ejecución. Los padres son antecedentes identificados por aristas y hashes. La autoridad propia vincula propietario, canción, job, ejecución, toma destino cuando existe, receta/hash, fuentes, derechos, herramientas/pins y resultado comprobado. Un SHA de receta no acredita terminación.

La unicidad histórica de revisiones sigue protegiendo la inferencia. CPU requiere unicidad propia por intención/ejecución/salida y retry compatible; los NULL no pueden habilitar duplicados. Las revisiones de contenido y tomas listas permanecen inmutables.

La migración se aplica después del head real, sin modificar 0001–0006. Si el SQLite fijado exige reconstrucción, ésta se limita a las tres tablas indicadas. Conserva datos, IDs, índices, checks, FK diferidas/entrantes, triggers, linaje e invalidación de snapshots. No autoriza reconstruir `cpu_execution`, `asset` ni otras tablas.

Antes de migrar se exige exclusividad sin workers/leases activos y backup SQLite íntegro/restaurable, incluidos datos confirmados en WAL. La implementación prueba BD vacía/poblada, integridad/FK, restauración en destino temporal y rollback ante cada fallo. Restaura `foreign_keys=ON` antes de runtime. Downgrade con contenido CPU no representable se rechaza antes de efectos; nunca elimina tomas para permitirlo.

### Autoridad y publicación

Los lectores privados conservan PostPlan/PreparedPackage v1 y sus hashes. Nuevas variantes tipadas CPU comparten la fase final de publicación después de validar su autoridad. El Publisher conserva CAS, revalidación, paquete exacto, rename no-clobber, assets/ready/committed en transacción y replay de ventanas archivos/BD.

Una edición crea Take hija de la misma canción con `derivation: edit`, padres reales, mapas efectivos y raíz canónica de ADR-0041. Crossfade conserva ambas aristas. El maestro sólo cambia por su acción explícita vigente.

La custodia `UNKNOWN` bloquea publicación, serving de resultados, limpieza y liberación de slot/staging. Sólo el cierre comprobado del grupo propio permite continuar. Archivos presentes, un PID o un terminal ajeno no acreditan éxito.

El post M1 de una generación real conserva autoridad original, ganador, modelo/semilla, recibos y manifiesto v1. Ejecutar su post en CPU no cambia el origen musical ni lo convierte en edit autónomo.

### Manifiestos, snapshots y previews

La inferencia conserva manifiestos v1 inmutables y sus validadores. El manifiesto CPU versión 2 declara executor del server, receta y herramientas reales. No declara engine, modelo o semilla de inferencia ejecutados. Los inputs/lineage identifican antecedentes; `commercial_use` combina derechos de entradas y herramientas, sin inferir permisos por una lista de modelos vacía.

Los lectores nuevos aceptan v1 y v2 mediante despacho explícito. Una versión no soportada se rechaza con motivo. Las canciones cuyo cierre portable incluya autoridad CPU usan snapshot versión 2; las demás conservan proyección v1 y hashes históricos. Export/import conserva padres, causalidad y referencias, excluyendo leases/PIDs/custodia operativa. Restaurar no reactiva procesos y exige reconciliación.

Las previews A/B sin nueva Take también usan manifiesto versión 2 con sujeto job autorizado. Su receta, fuentes/hashes, política, herramientas, mediciones y resultado pertenecen a una ejecución CPU propia. No inventan semilla/engine ni crean Take, maestro o publicación por toma ficticios. No modifican manifiestos de los padres.

El schema actual de `asset.subject_type` excluye job. La preview temporal se resuelve desde contexto/recibo privado del job, con manifiesto y serving autorizado; no inserta un asset job inválido. El plan/recibo tipado y su CAS se fijan antes del RED de previews, conservando privacidad, invalidez por cambios de contexto y bloqueo UNKNOWN. Persistir assets job exigiría otra decisión fuera de esta excepción.

### API server aditiva

El DTO M1 conserva `model_id:string` y sus operaciones. Abrirlo a null en la misma respuesta es rompedor. Se añaden cuatro operaciones con DTO TakeV2 discriminado:

- `GET /api/v2/takes/{take_id}`.
- `GET /api/v2/songs/{song_id}/takes`.
- `PATCH /api/v2/takes/{take_id}`.
- `POST /api/v2/takes/{take_id}/restore`.

Comparten autorización y negocio existentes; la web M2 consume v2 para historia mixta. Los clientes M1 siguen leyendo inferencia con su contrato original. Detalle, listado, PATCH o restore M1 que incluyan CPU devuelven 409 `CONFLICT` explícito y motivo de API requerida, antes de efectos. El listado no oculta filas CPU. El rechazo se aplica tras autorización, sin filtrar datos ajenos.

Audio/master y operaciones sin respuesta Take conservan su contrato cuando no hay cambio de forma o significado. El OpenAPI mantiene paths/DTOs M1 y añade v2; el tipo manual de `apps/web/lib/api.ts` requiere TakeV2 además de regenerar `api.d.ts`. Engine `/v1` permanece intacto.

## Alternativas descartadas

- **O2, relajación condicional dentro de v1.** Acepta datos históricos en el lector nuevo, pero modifica tipos requeridos manteniendo la misma versión. Exige una excepción adicional y sigue siendo incompatible con lectores v1 antiguos. Su menor coste relativo no compensa esa ambigüedad.
- **Sentinelas o identidad del padre como ejecución.** Falsean modelo/engine/semilla del edit o preview. No resuelven derechos ni autoridad.
- **Take CPU paralela.** Rompe la entidad común y sus relaciones de linaje, raíz, canción y maestro.

## Consecuencias

Esta decisión complementa ADR-0041/0055 y delimita la representación pendiente de ADR-0073. Su regla de preview v2 sustituye únicamente la prescripción de preview v1 de ADR-0073 una vez aceptado este ADR. No cambia sus criterios de audio, custodia o derechos.

El orquestador ha actualizado Constitución, datos, pipeline, spec/CA-29, plan e índice antes de producto. La modificación permite formatos CPU v2 y la excepción SQL delimitada; conserva todos los gates y requisitos restantes. O1 no amplía los tipos de v1 ni autoriza una relajación genérica del schema.

Los nombres finales de handlers, planes, recibos, paquetes y referencias privadas se fijan antes del RED de cada unidad. Esas concreciones no bloquean la selección T-01. Revisión/QA de documentos, migración probada, contratos regenerados, cobertura y aceptación musical real permanecen como puertas independientes.

## Estado

`aceptada` — decisión O1 y documentos aceptados por el orquestador bajo delegación el 2026-10-10. Revisión A/B intento 2 sin gaps y QA documental 16/16; T-01 contractual cerrada. Migración, render, publicación, APIs v2 y aceptación funcional permanecen pendientes en sus tareas. No acredita implementación o release de producto.

**Evidencia de decisión:** las [sondas locales](../../.cache/dev-cycle/m2/t01-cpu-contract-20261010/architect/contract-probe.json) reproducen NOT NULL y rechazo v1 de seed ausente/null. La [sonda SQLite del orquestador](../../.cache/dev-cycle/m2/sqlite-container-probe.json) registra 3.40.1 y rechazo de ALTER COLUMN sobre Python base con el pin server; no acredita migración integral. La [sonda OpenAPI](../../.cache/dev-cycle/m2/t01-cpu-contract-20261010/architect/api-candidate-probe.json) da estructura/diff aditivos exit 0 y negativo de nullable M1 exit 1. Son sondas de fronteras/candidatos, no pruebas de producto ni migración.
