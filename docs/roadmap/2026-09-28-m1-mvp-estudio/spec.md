---
spec: m1-mvp-estudio
descripcion: MVP del estudio web: crear canciones como proyecto, ver la generación en vivo, escuchar variantes, elegir maestro y descargar
estado: aprobada          # borrador | aprobada | implementada | obsoleta
aprobada: 2026-09-28
creado: 2026-09-28
actualizado: 2026-09-28
evaluacion: n/a (proyecto personal — ADR-0001; esfuerzo orientativo en tasks.md)
design: n/a (la arquitectura está en docs/arquitectura/ y docs/decisiones/)
plan: improvement-plan.md
depende-de: m0-entorno-y-motor
---

# Spec · M1 — MVP del estudio web

## 1. Objetivo

Usar el estudio a diario desde el navegador:

1. Escribir la letra y el estilo.
2. Ver cómo se genera.
3. Escuchar las variantes A/B.
4. Trabajar cada canción como un proyecto: takes, take maestro y versiones de la letra.
5. Descargar.

**Esquema completo desde la primera migración.** El modelo de datos se crea entero en la primera migración ([datos.md](../../arquitectura/datos.md)): canción = proyecto, linaje con varios padres, `job` con carriles y dependencias, `asset`, `upload`, `analysis`, y las tablas de artwork, vídeo, personajes y ajustes vacías. M2–M5 añaden funcionalidad **sin migraciones rompedoras**.

## 2. Alcance

**Dentro:**
- Canción = proyecto: F-01 a F-05.
- Crear audio: F-10 a F-15.
- Descarga en MP3/FLAC (F-32).
- Análisis básico de BPM y beats (F-33).
- Biblioteca y reproductor: F-60 a F-63.
- Modelos en la UI (F-80), cola (F-81), manifiesto (F-82) y sistema (F-83).
- Backup diario de la BD.

Ver [funcionalidades.md](../../producto/funcionalidades.md).

**Fuera:**

| Hito | Qué queda fuera de M1 |
|---|---|
| M2 | Operaciones derivadas (retake, extender, regenerar sección, cover), asistente de letras, modo simple, ajustes de proveedores |
| M3 | Stems, exportación por destino, WAV 48 kHz, portada, vídeo con letra, subidas, presets |
| M4 | Vídeo musical |

## 3. Criterios de aceptación

| # | Criterio |
|---|---|
| CA-01 | **Arranque.** `docker compose --profile engines up -d` + server y web en nativo levantan la app en `http://127.0.0.1:3000`. Con `STUDIO_ENGINES=mock=…` funciona sin GPU. **Precondición:** M0 cerrado, con `music.song` y `music.instrumental` verificadas en el descriptor de ACE-Step. |
| CA-02 | **Crear en modo personalizado.** Letra con etiquetas validadas en vivo (el mismo parser que el server, con `lyrics-cases.json`), estilo, chips, estilos a excluir, **autoría obligatoria**, opciones avanzadas según el `params_schema` de la tarea y de 1 a 4 variantes. Sin autoría, el botón queda deshabilitado con el motivo visible y el server responde `422 LYRICS_DECLARATION_REQUIRED`. |
| CA-03 | **Generación en vivo.** La tarjeta muestra las etapas reales por SSE, tal como las emite el engine: cola, modelo, generando % y post-proceso. Usa la visualización de [ux.md](../../producto/ux.md) §4.2 y, al terminar, se convierte en la forma de onda real. |
| CA-04 | **Variantes.** Las variantes de una petición aparecen agrupadas (A/B) y `⏭` en el reproductor salta a la pareja. Generar sin una canción abierta crea una **canción borrador** con título provisional. |
| CA-05 | **Instrumental.** Produce un take sin voz (`music.instrumental`), **sin exigir** declaración de autoría. En la UI, la letra y la voz se pliegan sin perder lo escrito. |
| CA-06 | **Biblioteca de canciones.** Grid y lista; búsqueda FTS por título, letra y estilo; filtros por colección, estado, fecha, modelo, favoritas y etiquetas; preescucha del maestro; papelera de 30 días con restaurar y purgar. |
| CA-07 | **Vista de canción** (pestañas Audio y Letra, [ux.md](../../producto/ux.md) §4.4):<br>- Takes con valoración y etiqueta; **marcar maestro**.<br>- Onda con seek y zoom, con los beats marcados (análisis `audio.beats`).<br>- Versiones de la letra y qué take cantó cada una.<br>- Panel de procedencia, exportable a JSON.<br>- Descarga en MP3/FLAC.<br>- Título, artista, estado y etiquetas. |
| CA-08 | **Reproductor persistente** con cola; sobrevive a la navegación. Atajos de [ux.md](../../producto/ux.md) §5. |
| CA-09 | **Cola:**<br>- Cancelar un trabajo deja el take en `cancelled` y limpia `data/tmp/`.<br>- Si el server se reinicia a mitad de un trabajo, el job pasa a `interrupted` y se reencola (tiene semilla fija).<br>- Un error `retryable` se reintenta hasta 2 veces.<br>- El análisis depende del take y queda `blocked` hasta que el take está listo. |
| CA-10 | **Errores.** Validación, `VRAM_EXCEEDED`, fallo del modelo y engine caído se muestran en la tarjeta con el `code`, el `job_id` y un botón de reintentar. Nunca en un toast que desaparece. La API responde en formato `problem+json` ([convenciones.md](../../arquitectura/convenciones.md) §3). |
| CA-11 | **Página Sistema.** GPU, VRAM (total, libre y tope), RAM, estado de cada engine, modelos instalados con sus tareas verificadas, licencia y hash ✓, cola y disco. Botón para descargar el modelo de la VRAM. |
| CA-12 | **Datos:**<br>- La primera migración crea el esquema completo de datos.md.<br>- Todo take `ready` tiene assets y `manifest.json` válido (`verify_manifest.py data/songs/` en verde).<br>- `song.json` se regenera al cambiar la canción.<br>- `data/backups/` recibe un `.backup` diario con rotación de 14 días. |
| CA-13 | **Colecciones.** Crear, renombrar y mover canciones entre colecciones. |
| CA-14 | **Seguridad local** ([ADR-0020](../../decisiones/ADR-0020-seguridad-local.md)):<br>- Una petición con `Host` distinto o con `Origin` ajeno recibe `403`.<br>- Los puertos de los engines están en `127.0.0.1`.<br>- Los engines rechazan peticiones sin token. |
| CA-15 | **Interfaz.** UI en castellano con `next-intl`, sin cadenas hardcodeadas. Temas oscuro y claro. Contraste AA en los tokens. |
| CA-16 | **Tests en verde:**<br>- Unitarios del server y de la web.<br>- Contrato: `openapi.json` coincide con el generado y `engine-v1.json` también.<br>- E2E de [`test-plan.md`](test-plan.md) contra `engine-mock`. |

## 4. Restricciones

[CONSTITUTION](../../CONSTITUTION.md) · [ADR-0002](../../decisiones/ADR-0002-personal-local-first.md) · [ADR-0004](../../decisiones/ADR-0004-sqlite-y-cola-propia.md) · [ADR-0008](../../decisiones/ADR-0008-procedencia-y-linaje.md) · [ADR-0013](../../decisiones/ADR-0013-cancion-como-proyecto.md) · [ADR-0017](../../decisiones/ADR-0017-postproceso-y-manifiesto-en-el-server.md) · [ADR-0018](../../decisiones/ADR-0018-cola-de-jobs.md) · [ADR-0019](../../decisiones/ADR-0019-contratos-code-first.md) · [ADR-0020](../../decisiones/ADR-0020-seguridad-local.md).

## 5. Incógnitas

| # | Incógnita | Se resuelve en |
|---|---|---|
| I-01 | ¿Genera el modelo elegido en M0 N variantes en un solo batch dentro de la VRAM, o hay que hacerlas en serie? | T-04 (según el benchmark de M0) |
| I-02 | ¿Qué parámetros avanzados expone de verdad el descriptor de la tarea (BPM, tonalidad, idioma, fuerza del estilo, prompt negativo)? | T-09 (a partir del `params_schema`) |
