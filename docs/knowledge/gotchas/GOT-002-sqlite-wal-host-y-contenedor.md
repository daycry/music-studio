---
id: GOT-002
tipo: gotcha
area: almacenamiento
estado: propuesta
fecha: 2026-10-22
fuente: docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md (T-05, hallazgo H4)
---

# SQLite en WAL compartido entre Windows y el contenedor por el bind 9p

## Síntoma

Durante la verificación de M1/T-05 se abrió `data/db/studio.sqlite` con el Python de Windows mientras el server lo usaba dentro del contenedor. Al terminar:

- desaparecieron `studio.sqlite-wal` y `studio.sqlite-shm`;
- el server siguió funcionando con descriptores abiertos a unos ficheros que ya no existían;
- se perdieron escrituras confirmadas: un take `ready` quedó sin fila en la base de datos;
- el contenedor ya no podía volver a abrir la base de datos (`unable to open database file`).

## Causa raíz

El bind de Docker Desktop (9p/DrvFS) no comparte los bloqueos de SQLite entre el host y el contenedor. La conexión de Windows creyó que era la única. Al cerrarse, hizo checkpoint y borró el `-wal` y el `-shm`, que el contenedor seguía usando.

## Cómo evitarlo

- Con el stack en marcha, no abras la base de datos desde Windows con ninguna herramienta (Python, DB Browser…).
- Para consultarla, usa la API o `docker compose exec server python …`.
- Para inspeccionarla desde el host, para antes el stack.
- El aviso está en el `README.md`, sección «Datos».

## Efecto en el diseño

La limpieza de arranque de T-05 (ADR-0089 §2) movió el directorio del take sin fila a `data/trash/orphans/` en vez de borrarlo, y así no se perdieron ficheros. Por eso el principio es «sin fila → papelera, nunca borrar».
