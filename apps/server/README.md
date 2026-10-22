# Server

Guía técnica: [server y contratos](../../docs/desarrollo/server-y-contratos.md).
Última actualización: 2026-10-07.

Base FastAPI sin torch. `/health` confirma que el proceso HTTP está ejecutándose;
no acredita BD, engines ni disponibilidad musical. Las rutas de negocio y SSE
se implementan en tareas posteriores; la protección de `/api/events` ya exige Origin.

El entorno usa `STUDIO_*` y `.env` del proyecto. `STUDIO_ENGINES` acepta
`mock=http://engine-mock:8199,acestep=http://engine-acestep:8101`.
`STUDIO_ALLOWED_HOSTS` es una lista separada por comas de autoridades exactas
(`127.0.0.1:8000,localhost:8000,server:8000,server`); no admite comodines ni LAN.
El parser HTTP rechaza Host malformado o duplicado con 400; una autoridad válida
ajena recibe 403 (ADR-0040). Todo Origin explícito debe coincidir exactamente con
`STUDIO_WEB_ORIGIN`, también en GET/HEAD; duplicados y valores malformados reciben
403. Solo GET/HEAD ordinarios permiten ausencia de Origin; SSE y los demás métodos
exigen Origin válido. Preflight limita métodos y cabeceras sin permitir el token
de engines al navegador. Las rutas se resuelven dentro del proyecto; Docker admite
los montajes exactos `/data` y `/models`.

Generar el token persistente una sola vez con el mecanismo existente:

```powershell
. ./scripts/env.ps1
uv run --frozen scripts/init_env.py
docker compose --profile studio up --build server engine-mock
```

El perfil `studio` arranca server y mock CPU; no depende de engines GPU. El server
publica solo `127.0.0.1:8000`; el mock se accede por DNS interno con token. Las
dependencias del runtime se instalan desde el lock con `uv --package server`,
sin dependencias dev ni paquetes GPU. No hay descargas de pesos en ejecución.

Logs JSON en `data/logs/server.log`, rotación diaria UTC, retención 14 días.
Solo se conservan nombres de eventos propios y IDs: los mensajes arbitrarios,
argumentos, excepciones, letras y campos adicionales se omiten o redactan.
Uvicorn no registra URLs de peticiones. El cliente mínimo hacia engines limita
el destino al origen configurado, no sigue redirecciones ni proxies del entorno.

Los errores mantienen `application/problem+json`. De las cabeceras de una
excepción HTTP solo se conservan `Allow` y `WWW-Authenticate` con valores ASCII
imprimibles; se descartan controles, valores no textuales y otras cabeceras.

## Persistencia (M1/T-02)

El lifespan migra `data/db/studio.sqlite`, habilita WAL y claves foráneas por
conexión y reconcilia `data/songs/<song_id>/song.json`. Las 23 entidades conservan
propietario, ULID y borrado lógico. El linaje y las dependencias son DAG; los
triggers mantienen FTS exclusivamente sobre canciones activas y letra vigente.
`rebuild_fts(engine)` reconstruye esa misma selección de forma transaccional.

`create_db_engine(path, data_dir=...)` publica snapshots tras los commits de
SQLAlchemy Session, incluidas modificaciones de filas hijas. SQLite se confirma
antes de reemplazar el JSON; un fallo de publicación registra `snapshot.failed`
y se repara al arrancar. `snapshots.restore` valida formato, cierre, rutas y
colisiones, y reconstruye filas sin reemplazar contenido ajeno. No restaura los
medios ausentes. Los contratos y recursos Alembic se incluyen en el wheel.

La copia nativa se comprueba al arrancar y cada hora para ejecutar la siguiente
copia al cumplir 24 horas. El backend parado aplaza el trabajo al siguiente
arranque. La tarea corre fuera del event loop, sin solapamientos, y la parada
interrumpe el backup por su callback de progreso y espera al hilo propio.
Sólo se publican copias validadas; la rotación elimina copias propias de más de
14 días. Los backups no contienen los medios. `backup.restore_backup(source,
target)` restaura a un destino nuevo sin BD/WAL/SHM existentes; se utiliza con el
backend parado y no sobrescribe una BD viva.

La revisión inicial admite `upgrade head` repetido. Su `downgrade base` borra
las filas antes de retirar el esquema y es **destructivo**: sólo se verifica en
una BD temporal privada, nunca en la biblioteca real. Ejemplo desde la raíz:

```powershell
uv run alembic -c apps/server/alembic.ini -x database_path=.cache/prueba-t02.sqlite upgrade head
uv run alembic -c apps/server/alembic.ini -x database_path=.cache/prueba-t02.sqlite downgrade base
uv run alembic -c apps/server/alembic.ini -x database_path=.cache/prueba-t02.sqlite upgrade head
```

La revisión aditiva `0002` conserva intacta `0001`. Añade metadatos locales
`song.is_dependency_only`, `snapshot_dirty` y `snapshot_generation`, y dos
tablas de infraestructura: `snapshot_member` registra los consumidores de
cada identidad y `song_fts_identity` asigna rowids enteros estables, sin
convertir ni truncar ULIDs. Estos metadatos no forman parte de `song.json`.

La extensión opcional `dependencies` de v1 contiene un cierre dirigido de
soporte y hashes canónicos de filas. Mantiene una raíz completa y conserva
referencias legales a recursos globales de otras canciones, sin incluir sus
hijos ajenos. Los archivos v1 anteriores siguen siendo legibles. La importación
valida la unión, procedencia, pertenencia, selecciones, DAG, raíces y timelines;
las colisiones abortan la transacción. `restore_new` inicializa un destino nuevo
con el usuario original antes de sembrarlo. Una BD poblada con otro usuario
declara conflicto. JSON restaura estructura; los medios ausentes siguen ausentes.
Si existe un medio en la ruta declarada, se comprueba su SHA-256 real.

Las canciones de soporte no se publican como proyectos ni entran en FTS.
Su promoción exige importar el proyecto completo con filas compatibles; la
edición ordinaria de la fila de canción se rechaza hasta esa promoción.
La vista `dispatchable_job` excluye jobs de soporte: la futura integración del
dispatcher debe consultarla y la biblioteca debe filtrar `is_dependency_only=0`.
No implementa aquí la cola ni la migración de intentos de T04.

Los triggers invalidan de forma durable consumidores ante ORM, Core, SQL y
movimientos OLD/NEW. El callback sólo publica raíces pendientes. Las consultas
de cierre usan IDs y relaciones indexadas; el arranque audita los archivos y
repara individualmente los ausentes, inválidos u obsoletos. El publicador sólo
limpia `dirty` si la generación capturada sigue vigente. Un fallo mantiene la
reparación pendiente y registra `snapshot.failed` en el logger configurado.
La publicación atómica de cada archivo no equivale a atomicidad BD/filesystem.

La revisión `0003` añade reloj y excepción transaccional de importación; `0004`
impide promover soporte o degradar raíces mediante edición ordinaria. Restore
adquiere el escritor antes de leer colisiones y consulta lotes de hasta 400 IDs
en la misma transacción. Los conflictos revierten toda la importación.

La [QA4 de T02](../../docs/roadmap/2026-09-28-m1-mvp-estudio/testing/t02/qa4-report.md)
verifica esa revisión, wheel, migraciones, reinicio persistente y backup/FTS.
La aceptación técnica no cierra M1 ni acredita E2E. Un fallo del origen de backup
conserva la copia válida anterior; los backups incluyen BD, no medios.

T03 sigue como código candidato pendiente de revisión y QA. `GET /health` usa
`HealthDTO` y documenta problemas 403/500 con `ProblemDTO`. `create_app` configura
sin abrir recursos runtime; el lifespan posee logging, BD, backup y limpieza.
La exportación usa `ContractSettings` validado, sólo entradas explícitas y
`env_file=None`, sin leer `.env` ni arrancar el lifespan. No implementa rutas de
negocio, dispatcher ni `job_attempt`.
