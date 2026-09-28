# Plan de pruebas — M1 · MVP del estudio web

| | |
|---|---|
| **Estado** | borrador |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) |
| **URL local** | http://127.0.0.1:3000 (API en http://127.0.0.1:8000, `STUDIO_ENGINES=mock=http://127.0.0.1:8199`) |

Regla general: se validan contratos observables (estados, duración, formatos, manifiesto, linaje). La calidad musical queda fuera de estas pruebas ([calidad/pruebas.md](../../calidad/pruebas.md)).

## Automáticos (E2E — los ejecuta `qa` con Playwright)

### E2E-01 — Crear canción con dos variantes y escucharla
- **Objetivo**: comprobar el flujo principal completo, desde crear hasta descargar.
- **Precondiciones**: app levantada con `engine-mock` (`MOCK_STAGE_DELAY_MS=300`); BD vacía.
- **Pasos**:
  1. Abrir Crear, escribir una letra con `[verse]` y `[chorus]`, un estilo y la autoría «Propia».
  2. Elegir 2 variantes y pulsar Crear.
  3. Esperar a que terminen las dos tarjetas.
  4. Pulsar ▶ en la variante A y luego `⏭`.
  5. Descargar el MP3 y el FLAC.
- **Aserciones**:
  - [ ] Aparece una canción borrador con 2 takes agrupados (A/B).
  - [ ] Las etapas se muestran en orden: cola → generando → post-proceso → listo.
  - [ ] El reproductor salta de A a B con `⏭`.
  - [ ] Las descargas tienen el content-type y el nombre esperados (`<titulo>-A.mp3`).
- **Capturas esperadas**: tarjeta generando; par A/B listo.
- **Cubre tareas**: T-04, T-05, T-06, T-07, T-09, T-10, T-13

### E2E-02 — La autoría de la letra es obligatoria
- **Objetivo**: comprobar que no se puede generar sin declarar la autoría.
- **Precondiciones**: app levantada.
- **Pasos**:
  1. Escribir la letra y el estilo sin marcar la autoría.
  2. Intentar crear.
  3. Llamar a `POST /api/generations` sin `lyrics_declaration`.
- **Aserciones**:
  - [ ] El botón está deshabilitado y el motivo es visible.
  - [ ] La API responde `422` con `code: LYRICS_DECLARATION_REQUIRED`.
- **Capturas esperadas**: botón deshabilitado con el motivo.
- **Cubre tareas**: T-07, T-09

### E2E-03 — Validación de etiquetas de la letra
- **Objetivo**: el editor marca las etiquetas inválidas con el mismo parser que el server.
- **Precondiciones**: app levantada.
- **Pasos**:
  1. Escribir `[verso]` (alias válido) y `[chrous` (malformada).
- **Aserciones**:
  - [ ] `[verso]` se pinta como píldora válida.
  - [ ] `[chrous` aparece subrayada como aviso, con un mensaje.
- **Capturas esperadas**: editor con la etiqueta en aviso.
- **Cubre tareas**: T-03, T-09

### E2E-04 — Error del engine y reintento
- **Objetivo**: los errores se muestran en la tarjeta y se pueden reintentar.
- **Precondiciones**: app levantada.
- **Pasos**:
  1. Crear con el estilo `synthwave @mock:fail_once=INTERNAL` (directiva del mock, contrato §7).
  2. Pulsar Reintentar.
- **Aserciones**:
  - [ ] La tarjeta muestra el `code` `INTERNAL` y el `job_id`; no aparece un toast; no hubo reintento automático (no es `retryable`).
  - [ ] Reintentar (`POST /api/jobs/{id}/retry`) crea un job nuevo que reutiliza el take y termina `ready`.
- **Capturas esperadas**: tarjeta en error.
- **Cubre tareas**: T-04, T-10

### E2E-05 — Cancelar
- **Objetivo**: la cancelación deja el take en `cancelled` y limpia los temporales.
- **Precondiciones**: app levantada con `MOCK_STAGE_DELAY_MS=3000`.
- **Pasos**:
  1. Crear.
  2. Cancelar desde la tarjeta durante «generando».
- **Aserciones**:
  - [ ] El take queda en `cancelled`.
  - [ ] `data/tmp/<job_id>/` no existe.
- **Capturas esperadas**: tarjeta cancelada.
- **Cubre tareas**: T-04, T-10

### E2E-06 — Recuperación tras reiniciar el server
- **Objetivo**: un job en curso sobrevive a un reinicio del server.
- **Precondiciones**: app levantada con `MOCK_STAGE_DELAY_MS=5000`.
- **Pasos**:
  1. Crear.
  2. Reiniciar el server a mitad de la generación (lo hace `scripts/e2e_stack.py restart-server`).
  3. Recargar la web.
- **Aserciones**:
  - [ ] El job pasa a `interrupted`, se reencola y termina `ready`.
  - [ ] La UI se reconecta al SSE (`Last-Event-ID`).
- **Capturas esperadas**: tarjeta completada tras el reinicio.
- **Cubre tareas**: T-04, T-06

### E2E-07 — Vista de canción: take maestro, valoración y versiones de letra
- **Objetivo**: trabajar la canción como proyecto.
- **Precondiciones**: una canción con 2 takes (seed).
- **Pasos**:
  1. Abrir la canción.
  2. Valorar B con ★★★★ y marcarla como maestro.
  3. Editar la letra y guardar una versión nueva.
  4. Generar otra vez.
- **Aserciones**:
  - [ ] La canción apunta a B como maestro y la biblioteca previsualiza B.
  - [ ] Existen 2 versiones de letra; el take nuevo referencia la v2 y los anteriores la v1.
  - [ ] El panel de procedencia muestra el modelo, la licencia, el hash, la semilla y la autoría.
- **Capturas esperadas**: vista de canción con el maestro marcado.
- **Cubre tareas**: T-07, T-12

### E2E-08 — Biblioteca: búsqueda, filtros y papelera
- **Objetivo**: encontrar y recuperar canciones.
- **Precondiciones**: 3 canciones con títulos, letras y colecciones distintos (seed).
- **Pasos**:
  1. Buscar una palabra de la letra.
  2. Filtrar por colección.
  3. Borrar una canción, abrir la papelera y restaurarla.
- **Aserciones**:
  - [ ] La búsqueda FTS devuelve solo la canción esperada.
  - [ ] El filtro de colección funciona.
  - [ ] La canción restaurada conserva sus takes.
- **Capturas esperadas**: resultados de búsqueda; papelera.
- **Cubre tareas**: T-07, T-11, T-14

### E2E-09 — Beats en la onda (análisis dependiente)
- **Objetivo**: el análisis se ejecuta después del take y se muestra en la onda.
- **Precondiciones**: app levantada; `engine-mock` con `audio.beats`.
- **Pasos**:
  1. Crear una canción.
  2. Abrir la vista de canción.
- **Aserciones**:
  - [ ] El job de análisis estuvo `blocked` hasta que el take quedó `ready` y después terminó `succeeded`.
  - [ ] La onda muestra las marcas de beat y el BPM.
- **Capturas esperadas**: onda con los beats marcados.
- **Cubre tareas**: T-04, T-05, T-12

### E2E-10 — Página Sistema
- **Objetivo**: el estado del sistema es visible.
- **Precondiciones**: app levantada.
- **Pasos**:
  1. Abrir Sistema.
- **Aserciones**:
  - [ ] Se ven la VRAM (total/libre/tope), la RAM, los engines y su estado, los modelos con sus tareas verificadas, la licencia, el hash ✓ y el disco.
- **Capturas esperadas**: página Sistema.
- **Cubre tareas**: T-07, T-14

### E2E-11 — Instrumental sin declaración de autoría
- **Objetivo**: el instrumental no exige autoría de la letra y conserva lo escrito.
- **Precondiciones**: app levantada.
- **Pasos**:
  1. Escribir una letra, activar Instrumental (sin marcar autoría).
  2. Crear.
  3. Desactivar Instrumental.
- **Aserciones**:
  - [ ] El botón Crear está habilitado con Instrumental activo y el take termina `ready` con `task: music.instrumental`.
  - [ ] Al desactivar Instrumental, la letra sigue ahí y vuelve a exigirse la autoría.
- **Capturas esperadas**: panel con Instrumental activo.
- **Cubre tareas**: T-07, T-09

## API (smoke con curl)

### API-01 — Seguridad local: Host y Origin
- **Método y ruta**: `POST /api/songs` con `Origin: http://evil.test`
- **Status esperado**: 403
- **Aserción sobre el body**: `"code":"FORBIDDEN_ORIGIN"`
- **Cubre tareas**: T-01

### API-02 — OpenAPI
- **Método y ruta**: `GET /openapi.json`
- **Status esperado**: 200
- **Aserción sobre el body**: `"/api/generations"`
- **Cubre tareas**: T-03

## Manuales (M — los realiza una persona)

### M-01 — Generación real con GPU
- **Qué revisar**: con `engine-acestep` real, repetir E2E-01 y escuchar el resultado.
- **Por qué no se automatiza**: requiere la GPU y el oído.
- **Criterio de aceptación**:
  - [ ] La canción se genera y suena; la telemetría muestra `spilled: false`.
- **Cubre tareas**: T-04, T-05, T-16

### M-02 — Revisión visual y de accesibilidad básica
- **Qué revisar**: los temas oscuro y claro, el contraste, el foco visible, el reproductor manejado solo con teclado y `prefers-reduced-motion`.
- **Por qué no se automatiza**: requiere juicio visual.
- **Criterio de aceptación**:
  - [ ] No hay texto ilegible y el reproductor se puede usar solo con el teclado.
- **Cubre tareas**: T-08, T-13

### M-03 — Backup y restauración
- **Qué revisar**: forzar el backup diario, borrar `studio.sqlite` y restaurar desde `data/backups/`.
- **Por qué no se automatiza**: es destructivo sobre datos reales.
- **Criterio de aceptación**:
  - [ ] La biblioteca vuelve completa y `verify_manifest.py data/songs/` pasa en verde.
- **Cubre tareas**: T-02, T-16

## Cobertura (tarea → escenarios)

| Tarea | Escenarios |
|---|---|
| T-01 | API-01 |
| T-02 | M-03 |
| T-03 | E2E-03, API-02 |
| T-04 | E2E-01, E2E-04, E2E-05, E2E-06, E2E-09, M-01 |
| T-05 | E2E-01, E2E-09, M-01 |
| T-06 | E2E-01, E2E-06 |
| T-07 | E2E-01, E2E-02, E2E-07, E2E-08, E2E-10, E2E-11 |
| T-08 | M-02, (infra E2E) |
| T-09 | E2E-01, E2E-02, E2E-03, E2E-11 |
| T-10 | E2E-01, E2E-04, E2E-05 |
| T-11 | E2E-08 |
| T-12 | E2E-07, E2E-09 |
| T-13 | E2E-01, M-02 |
| T-14 | E2E-08, E2E-10 |
| T-15 | todos los E2E-xx |
| T-16 | M-01, M-03 |
