# T-11 · Papelera de canciones

## Alcance

La biblioteca incorpora un modo de papelera respaldado por la API. El borrado sigue siendo lógico para conservar el proyecto y su linaje. La restauración reactiva la canción y sus índices FTS; la purga física sólo se permite después de 30 días y cuando no existen tomas, trabajos, letras, artwork, vídeo ni publicaciones durables asociadas.

## Cambios

- `GET /api/songs/trash` devuelve canciones propias borradas, `deleted_at` y `purge_after`, con cursor.
- `POST /api/songs/{song_id}/restore` restaura la canción y conserva las tomas.
- `POST /api/songs/{song_id}/purge` aplica retención y devuelve `PURGE_PROTECTED` ante historial durable.
- La UI de Biblioteca permite abrir la papelera y ejecutar Restaurar/Purgar.
- `MasterPreview` espera 400 ms al pasar el cursor o enfocar, carga el take maestro autenticado, limita la escucha a 10 s, libera el Blob URL y puede desactivarse.
- Las canciones en `in_progress` muestran `GenerativeViz` como miniatura de generación.
- El contrato OpenAPI se regeneró y quedó sincronizado.

## Verificación

- RED inicial: 2 fallos por rutas inexistentes.
- Server: `16 passed` en `test_domain_routes.py`.
- Web: `240 passed`.
- Playwright Compose: `15 passed, 1 skipped` (E2E-06 condicionado).
- ESLint, TypeScript, Ruff y `scripts/export_contracts.py --check`: verdes.

## Pendiente de T-11

La implementación funcional está completa; la tarea permanece abierta hasta la revisión adversarial y la QA de cierre.

## Actualizacion de filtros y carga incremental

La biblioteca ya aplica filtros de estado, modelo, favorita, etiqueta y rango de fechas; el contrato OpenAPI publica esos parametros y el cliente los genera. El sentinel IntersectionObserver activa la siguiente pagina con una guardia de concurrencia y mantiene el boton de respaldo. La miniatura de generacion no inventa porcentaje: usa progress=null hasta disponer del progreso real.

Verificacion adicional: server 17 passed; web 240 passed; Compose 15 passed, 1 skipped; build, lint, TypeScript, Ruff y contrato OpenAPI verdes.
