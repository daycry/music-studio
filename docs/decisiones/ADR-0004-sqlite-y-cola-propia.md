# ADR-0004 · SQLite y cola de trabajos propia

- **Estado:** aceptada · **Fecha:** 2026-09-28 · El detalle de la cola está en [ADR-0018](ADR-0018-cola-de-jobs.md)

## Decisión
- Base de datos **SQLite** en modo WAL, en `data/db/studio.sqlite`. Solo la escribe el proceso **server**.
- La **cola** es la tabla `job`, con dependencias en `job_dependency`, y la gestiona un dispatcher `asyncio` dentro del server, con carriles `gpu` (1 trabajo a la vez), `cpu` y `remote`. No se usa Redis ni Celery.
- Los engines no acceden a la base de datos: reciben el trabajo por HTTP y devuelven los eventos como NDJSON.
- **Copia de seguridad diaria** con `sqlite3 .backup` en `data/backups/`, con rotación de 14 días, desde M1. La base de datos viva **no** se sincroniza con Synology; los backups sí ([`../arquitectura/entorno.md`](../arquitectura/entorno.md) §4).

## Motivo
- Con un usuario y una GPU no hace falta nada más.
- Postgres con los datos en un bind-mount de Windows da problemas de permisos (el directorio debe tener 0700 y el propietario correcto) y de rendimiento.
- Un volumen Docker con nombre dejaría los datos fuera de la carpeta del proyecto, lo que incumple [ADR-0005](ADR-0005-todo-en-la-carpeta.md).

## Salida
Si llega el multiusuario (hito futuro, con su propio ADR):
- SQLAlchemy y Alembic permiten migrar a Postgres;
- la cola se puede sustituir por arq o Redis.
