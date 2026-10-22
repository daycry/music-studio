# Desarrollar el server y sus contratos

Última actualización: 2026-10-07.

Esta guía describe implementación técnica disponible y código candidato expresamente señalado. Los estados pertenecen a los ledgers de [M0](../roadmap/2026-09-28-m0-entorno-y-motor/tasks.md) y [M1](../roadmap/2026-09-28-m1-mvp-estudio/tasks.md). Ambos hitos siguen abiertos.

## Qué módulos leer

| Fuente | Responsabilidad |
|---|---|
| [main.py](../../apps/server/app/main.py) | Factoría FastAPI, lifespan y health |
| [settings.py](../../apps/server/app/settings.py) | Configuración validada y exportación neutral |
| [security.py](../../apps/server/app/security.py) | Host, Origin y preflight |
| [errors.py](../../apps/server/app/errors.py) | Errores RFC 9457 |
| [api_models.py](../../apps/server/app/api_models.py) | DTO de health y problem; candidato T03 |
| [db.py](../../apps/server/app/db.py) | SQLite, migración, callback Session y reconstrucción FTS |
| [models](../../apps/server/app/models/__init__.py) | Tablas y relaciones SQLAlchemy |
| [snapshots.py](../../apps/server/app/snapshots.py) | Validación, publicación, reconciliación e importación |
| [backup.py](../../apps/server/app/backup.py) | Copias SQLite, restauración y scheduler |
| [lyrics.py](../../apps/server/app/lyrics.py) | Parser puro de etiquetas; candidato T03 |
| [export_contracts.py](../../scripts/export_contracts.py) | Exportación determinista code-first |
| [generate.py](../../scripts/generate.py) | Generación por CLI, separada de la futura API de negocio |
| [run.py](../../scripts/eval/run.py) · [metrics.py](../../scripts/eval/metrics.py) | Plan comparativo, transporte, anonimización y métricas |

El server usa FastAPI, Pydantic, SQLAlchemy y Alembic sin torch. Los engines aíslan inferencia y devuelven crudos. El server conserva la propiedad exclusiva de la BD, postproceso y manifiestos. Véanse [sistema](../arquitectura/sistema.md), [datos](../arquitectura/datos.md) y [constitución](../CONSTITUTION.md).

## Runtime y desarrollo

El runtime del producto usa Docker. Ollama compartido en WSL2 es la excepción de [ADR-0035](../decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md). ComfyUI conserva Docker con CUDA; no se introduce otro despliegue.

El perfil `studio` implementa server y mock CPU. Su verificación no acredita el despliegue completo, UI ni comunicación futura con Ollama. La arquitectura mantiene cola SQLite GPU 1 / CPU 2, sin Kafka ni Redis. El dispatcher todavía pertenece a T04.

El desarrollo usa uv, su intérprete y la venv del proyecto, además del Node gestionado por el entorno. Nunca instala paquetes en el Python del sistema. Modelos, datos, evaluaciones y cachés permanecen dentro del repositorio; sus contenidos privados se ignoran en Git.

Carga el entorno desde la raíz antes de ejecutar comandos:

```powershell
. ./scripts/env.ps1
```

En bash se usa `source scripts/env.sh`. La preparación del entorno está en [entorno.md](../arquitectura/entorno.md). Esta guía presupone dependencias instaladas; no reproduce scripts antiguos como instrucciones vigentes.

## Configuración y frontera HTTP

`Settings` valida `STUDIO_*` y el `.env` local. Las rutas quedan confinadas al proyecto; Docker admite los montajes exactos `/data` y `/models`. No copies secretos a contratos, logs o documentación.

`STUDIO_ALLOWED_HOSTS` contiene autoridades exactas. El parser HTTP puede devolver 400 por Host malformado o duplicado. Una autoridad válida ajena recibe 403 de aplicación, conforme a [ADR-0040](../decisiones/ADR-0040-frontera-parser-http-y-aplicacion.md).

Todo Origin explícito debe coincidir exactamente con `STUDIO_WEB_ORIGIN`. GET/HEAD ordinarios permiten ausencia de Origin; otros métodos y la protección prevista de SSE lo exigen. Proteger `/api/events` no implica que la ruta SSE exista. El preflight limita métodos y cabeceras, sin entregar el token interno al navegador.

Los errores usan `application/problem+json`. Sólo sobreviven `Allow` y `WWW-Authenticate` seguros de excepciones HTTP. La respuesta de error interno añade CORS únicamente para el Origin configurado. Los logs JSON omiten mensajes arbitrarios, letras y excepciones; rotan diariamente en UTC con retención de 14 días.

## Factoría, lifespan y health: código candidato T03

`create_app(settings)` configura la aplicación sin abrir BD, archivos de log ni tareas runtime. El lifespan posee esos recursos: configura logging, migra SQLite, crea engine, reconcilia snapshots y arranca backup. Su limpieza cancela el trabajo propio, espera su finalización, dispone el engine y cierra handlers.

La exportación usa `ContractSettings`, que conserva validaciones y admite sólo entradas explícitas del constructor. Tiene `env_file=None` y no toma fuentes del entorno ni secretos de archivo. Generar OpenAPI no arranca el lifespan ni lee `.env`.

El código declara `GET /health` con `HealthDTO`; documenta 403 y 500 mediante `ProblemDTO`. Health confirma proceso HTTP en ejecución. No certifica conexión a BD, modelo cargado ni música disponible.

Estas propiedades describen el código candidato actual de T03. Su aceptación técnica sigue pendiente de revisión y QA del orquestador. No se presentan resultados de implementación como QA aceptada.

## SQLite y migraciones verificadas

[ADR-0041](../decisiones/ADR-0041-esquema-inicial-y-snapshots-del-server.md) conserva 23 tablas de dominio en el baseline `0001`. Cada conexión activa WAL y claves foráneas. Los DAG de linaje y dependencias, propietario, ULID y borrado lógico se verifican en T02.

| Revisión | Cambio local |
|---|---|
| `0002` | Metadatos de soporte/dirty/generación, membresía de consumidores e identidad FTS estable |
| `0003` | Reloj de revisión y excepción transaccional de importación |
| `0004` | Guardas que impiden promoción ordinaria de soporte y degradación de raíces |

Estas tablas auxiliares son infraestructura local; no cambian el baseline histórico ni se exportan como contenido canónico. `job_attempt` de ADR-0043 aún no está implementada. La vista `dispatchable_job` prepara el filtrado de soporte para el futuro dispatcher.

FTS indexa sólo canciones activas y letra vigente. `rebuild_fts(engine)` reconstruye esa selección de forma transaccional. Una tabla prevista para vídeo no acredita una función de vídeo implementada.

Para una BD temporal propia, Alembic acepta:

```powershell
uv run --frozen alembic -c apps/server/alembic.ini -x database_path=.cache/prueba-desarrollo.sqlite upgrade head
```

El downgrade elimina datos. Su verificación pertenece exclusivamente a fixtures temporales; no se usa sobre la biblioteca real.

## Snapshots: raíz, soporte y recuperación

[ADR-0044](../decisiones/ADR-0044-snapshots-con-dependencias-explicitas.md) define una raíz completa y cierre dirigido de soporte. `dependencies.rows/provenance` es una extensión opcional de v1. Incluye referencias globales sin expandir todos los hijos de otros proyectos.

Los triggers invalidan consumidores ante ORM, SQL, Core, bulk y movimientos OLD/NEW. El callback Session publica después del commit. SQL/Core deja reparación durable para reconciliación. Publicar el JSON atómicamente no crea una transacción conjunta con SQLite.

El publicador captura revisión y generación. Después del reemplazo comprueba su vigencia con CAS; una carrera conserva `dirty`. Un fallo registra `snapshot.failed` y el arranque puede reparar el derivado.

`restore(engine, document, data_dir)` valida formato, pertenencia, procedencia, rutas, selecciones, raíces y DAG. Adquiere el escritor antes de leer colisiones, consulta identidades en lotes de hasta 400 y revierte la transacción ante conflicto.

Las canciones importadas como soporte no se publican como proyectos ni entran en FTS. Sólo una importación completa compatible promueve la raíz correspondiente. Una edición ordinaria no puede promover soporte ni degradar una raíz.

`restore_new` inicializa un destino nuevo con el propietario original. Una BD poblada con otro usuario declara conflicto. Los medios ausentes siguen ausentes; los presentes deben coincidir con su SHA-256. JSON restaura estructura, no inventa audio.

## Backup y restauración de BD

`backup` usa la API nativa `sqlite3.Connection.backup()`, no una copia directa del archivo vivo. Valida integridad, FK y FTS antes de publicar. La rotación elimina sólo copias propias de más de 14 días.

`DailyBackup` comprueba al arrancar y cada hora si la última copia válida tiene al menos 24 horas. Trabaja fuera del event loop sin solapamientos. Si el backend estuvo parado, aplaza el trabajo al arranque siguiente.

Un fallo del origen mantiene la copia válida anterior. La parada cancela mediante el callback de progreso y espera el hilo propio. `restore_backup(source, target)` exige backend parado y destino nuevo, sin BD, WAL ni SHM existentes. El backup contiene la BD; no contiene medios.

## Contratos code-first y tipos TypeScript: candidato T03

Los modelos Python son la fuente de los contratos de [ADR-0019](../decisiones/ADR-0019-contratos-code-first.md).

`export_contracts.py` procesa tanto `engine-v1.json` como `openapi.json`. En modo check no termina prematuramente después del primer desajuste. La comprobación conserva los bytes del contrato engine preexistente; no lo reescribe para comprobarlo.

Los DTO Pydantic generan el esquema; no se usa una construcción sin validación ni un esquema manual que sustituya la fuente. `pnpm gen` ejecuta el script real de web con `openapi-typescript` fijado en 7.13.0 y escribe `apps/web/lib/generated/api.d.ts`.

```powershell
uv run --frozen --all-packages scripts/export_contracts.py --check
pnpm gen
pnpm --filter web typecheck
pnpm --filter web test
```

`pnpm gen` escribe el derivado TypeScript. Para actualizar contratos se ejecuta el exportador sin `--check`, y se revisan juntos código y derivados. Estos comandos describen tooling existente; no acreditan rutas de negocio ni UI.

## Letras y CLI

El parser candidato devuelve `original`, metadatos de alias y rangos UTF-16. No reescribe la letra ni el prompt. Los casos compartidos de [lyrics-cases.json](../../packages/contracts/lyrics-cases.json) sirven para contrastar Python y TypeScript. T03 mantiene pendiente su revisión y QA.

La CLI conserva prompts, letras y etiquetas Markdown como `**[...]**` literalmente. Sólo `--strip-tag-markdown` solicita retirar ese marcado. No se aplica como limpieza silenciosa. Consulta opciones reales sin generar audio:

```powershell
uv run --frozen --all-packages scripts/generate.py --help
uv run --frozen --all-packages scripts/eval/run.py --help
```

La generación real por CLI ya está implementada, pero ninguna herramienta CPU aprueba por sí sola un modelo musical. Una evaluación bloqueada por prerrequisitos no debe sustituirse por corpus, derechos, suelo WER o puntuaciones inventados.

## Qué verificaciones respaldan esta guía

| Unidad | Evidencia pública y alcance |
|---|---|
| T01 | [QA técnica](../roadmap/2026-09-28-m1-mvp-estudio/testing/t01/qa-report.md): 86 pruebas CPU, dos skips Windows complementados por sondas Linux; Docker CPU, token y frontera HTTP |
| T02 | [Revisión4](../roadmap/2026-09-28-m1-mvp-estudio/testing/t02/review4-report.md) y [QA4](../roadmap/2026-09-28-m1-mvp-estudio/testing/t02/qa4-report.md): 327 pass, tres skips Windows; los mismos tres casos pasan en Linux |
| T11 CPU | [Revisión3](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t11/review3-report.md) y [QA CPU3](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t11/qa-cpu3-report.md): 130 casos distintos, cuatro sondas extra y un skip de symlink por privilegios Windows |

QA4 de T02 verifica revisión `0004`, 18 operaciones CLI de migración, 28 recursos del wheel, reinicio persistente, backups y FTS. Su baseline de 32 fuentes es histórico de esa unidad; los cambios posteriores de T03 no forman parte de aquel freeze. La puerta de unidad da exit 0; la puerta global M1 da exit 1 por falta de E2E.

QA CPU3 de T11 mide módulos enteros: run 90,89 % y metrics 98,42 %, sin exclusiones; Ruff y formato dan exit 0. El pipeline mock de 30 generaciones y 90 métricas usa 120 IDs de unidad: no son 30 canciones reales. El dry-run planifica 30 posiciones; el comando completo bloqueado da exit 2 antes de HTTP.

R11-06 Minor sigue pendiente: verificación FFmpeg repetida por fila. No se declara corregido. GPU real, calibración de sensores, suelo WER cantado, derechos, corpus, escucha, ganador humano y uso real siguen pendientes en sus tareas. Los resultados CPU no certifican cero spill.

Para cambios futuros, selecciona las pruebas de los módulos afectados; no repitas sondas exclusivas históricas. Las suites disponibles se ejecutan con el entorno gestionado:

```powershell
uv run --frozen --all-packages pytest apps/server/tests -m "not gpu" -q
uv run --frozen --all-packages pytest scripts/eval/tests -m "not gpu" -q
```

La revisión documental no vuelve a ejecutar esas suites. Sus resultados aceptados se consultan en los informes enlazados. Continúa por [convenciones](../arquitectura/convenciones.md), [contrato engines](../arquitectura/contrato-engines.md) y los ledgers canónicos.
