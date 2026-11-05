# Plan de pruebas — M1 · MVP del estudio web

| | |
|---|---|
| **Estado** | borrador |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) |
| **URL local** | http://127.0.0.1:3000 (API en http://127.0.0.1:8000; server en Compose con `STUDIO_ENGINES=mock=http://engine-mock:8199`) |

Regla general: se validan contratos observables (estados, duración, formatos, manifiesto, linaje). La calidad musical queda fuera de estas pruebas ([calidad/pruebas.md](../../calidad/pruebas.md)).

## Ejecución en Windows sin WSL ni GPU (2026-11-03)

La suite `playwright.cpu.config.ts` usa Chromium real con `--disable-gpu`, sin arrancar servicios ni ejecutar recuperación de Docker. Su comando, desde PowerShell con el entorno cargado, es `pnpm --filter ./apps/web exec playwright '--' test --config=playwright.cpu.config.ts`.

Las pruebas de interfaz interceptan la API con fixtures sintéticos identificados. Comprueban el comportamiento del navegador; no prueban el dispatcher, el post-proceso ni la persistencia. API-01 y API-02 no interceptan peticiones: necesitan un server HTTP aislado en `127.0.0.1:8000`, sin engines y con datos temporales dentro de `.cache/`. La web de desarrollo escucha en `127.0.0.1:3000`. Nunca se utiliza la base de datos del usuario para esta suite.

| Área CPU | Comprobaciones | Tareas |
|---|---|---|
| Crear | Autoría, instrumental, duración vacía, sistema no disponible y variantes condicionadas por la estimación del fixture | T-09 |
| Generación | Etapas SSE sintéticas, espera del take `ready`, cancelación confirmada por evento y errores de acciones | T-06, T-10 |
| Biblioteca | Enter, búsqueda conservada y preescucha de la última toma lista si falta maestro | T-11 |
| Canción | Valoración y borrado con `null`, maestro solo listo, onda y descarga | T-12 |
| Reproductor | Blob autenticado y conservación de la pista al navegar | T-13 |
| API HTTP | Rechazo de Origin ajeno y publicación del OpenAPI | T-01, T-03 |

Los informes HTML, JSON, trazas y capturas se guardan en `.cache/playwright-ui/`. La suite CPU excluye `recovery.spec.ts`, `analysis.spec.ts` y `collections.spec.ts`: la recuperación necesita el despliegue real y beats/colecciones están aplazados por ADR-0089. Sus escenarios históricos se conservan debajo para el despliegue; no forman parte del camino mínimo actual.

El verde de la suite CPU no cierra T-04, T-05, T-07, T-15 completa ni M1. M-01, M-02 y M-03 conservan su validación separada. La fase CPU anterior no ejecutó WSL, Docker, Ollama ni inferencia GPU.

## Ejecución integrada en Docker (2026-11-05)

`playwright.integration.config.ts` descubre sólo `e2e/integration/`: navegador, HTTP, SSE, SQLite y FFmpeg reales sobre web/server/engine-mock CPU. No importa los fixtures que interceptan la API. El orquestador levanta un proyecto Compose dedicado y datos privados bajo `.cache/`; no se resetean datos del usuario. Cada corrida exige `E2E_PROJECT_NAME`, `E2E_COMPOSE_FILE`, `E2E_ENV_FILE`, `STUDIO_DATA_ROOT`, `E2E_ARTIFACT_ROOT`, `E2E_API_ORIGIN` y `E2E_WEB_ORIGIN` explícitos. Proyecto, rutas privadas y orígenes HTTP loopback se validan antes de descubrir las pruebas. Comando: `pnpm --filter ./apps/web exec playwright '--' test --config=playwright.integration.config.ts`.

`E2E_RECOVERY=1` habilita la caída del servidor de pruebas; requiere el mock con `MOCK_STAGE_DELAY_MS=5000`. Sin esa variable el caso queda omitido explícitamente y la corrida no acredita recuperación. El helper de Compose espera cada operación y restaura el server de pruebas incluso si el escenario falla. Deben conservarse recibos de identidad y estado antes/después, además de las trazas del navegador.

Pendientes: tres corridas integradas consecutivas verdes, pruebas de caída durante generación y post-proceso, revisión independiente y `qa-gate`. Los resultados de desarrollo y las correcciones se registran en el ledger; no se marcan las casillas de aceptación antes de QA. La música del mock es sintética: no acredita ACE-Step ni calidad musical.

## Automáticos (E2E — los ejecuta `qa` con Playwright)

### Despliegue — CA-01

Entorno objetivo: web, server y `engine-mock` en Docker Compose, sin GPU ni Ollama. El nombre interno `engine-mock` coincide con el servicio del despliegue privado ([ADR-0035](../../decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md)).

- [ ] Arrancar web/server/mock con Compose y ejecutar migraciones dentro del server; abrir web/API por puertos del host en `127.0.0.1`.
- [ ] Confirmar resolución server→mock por nombre de servicio, sin usar localhost entre contenedores.
- [ ] Crear canción/job, recrear el contenedor server y comprobar persistencia de SQLite WAL y assets, sin borrar los datos.
- [ ] Verificar FFmpeg LGPL Linux fijado y procesar audio sintético real hasta assets/manifiesto válidos.
- [ ] Verificar Host/Origin permitidos y rechazos ajenos; puertos sin exposición LAN.
- [ ] Verificar SSE y reproducción Range entre navegador y API publicada.

Este bloque valida el despliegue de M1 sin inferencia GPU. La conexión a Ollama y su descarga/restauración se validan en M2; ComfyUI CUDA, en sus hitos.

### E2E-01 — Crear canción con dos variantes y escucharla
- **Objetivo**: comprobar el flujo principal completo, desde crear hasta descargar.
- **Precondiciones**: app levantada con `engine-mock` (`MOCK_STAGE_DELAY_MS=300`); datos privados. Cada escenario crea su canción y un marcador de búsqueda único.
- **Pasos**:
  1. Abrir Crear, escribir una letra con `[verse]` y `[chorus]`, un estilo y la autoría «Propia».
  2. Elegir 2 variantes y pulsar Crear.
  3. Esperar a que terminen las dos tarjetas.
  4. Abrir la canción, seleccionar una toma y reproducirla; desplazar la posición del audio.
  5. Descargar el MP3 y el FLAC.
- **Aserciones**:
  - [ ] Aparece una canción borrador con 2 takes independientes. La agrupación A/B y el salto de par quedan aplazados por ADR-0089.
  - [ ] Las etapas se muestran en orden: cola → generando → post-proceso → listo.
  - [ ] El reproductor avanza, permite seek y conserva el blob autenticado al navegar a la biblioteca.
  - [ ] Las descargas tienen el content-type, los bytes y el nombre esperados (`<titulo>-<take_id>.mp3` y `.flac`). `Content-Disposition` es visible por CORS al navegador.
  - [ ] HTTP Range devuelve 206 y los bytes solicitados desde Node y desde el navegador.
  - [ ] Hay eventos SSE reales de generación. Tras EOF/invalidez de epoch, el observador reconecta con el cursor confirmado y acepta el terminal del post sólo en un snapshot completo begin/chunk/end (ADR-0056).
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
  1. Crear con el estilo `synthwave <marcador> @mock:fail_once=PROVIDER_ERROR`, sin la directiva `retryable`.
  2. Pulsar Reintentar.
- **Aserciones**:
  - [ ] La tarjeta muestra el `code` `PROVIDER_ERROR` y el `job_id`; no aparece un toast; no hubo reintento automático (no es `retryable`).
  - [ ] Reintentar (`POST /api/jobs/{id}/retry`) crea un job nuevo que reutiliza el take sin publicar y termina `ready`; conserva su semilla e índice.
  - [ ] Un escenario independiente con `@mock:fail=INTERNAL` confirma tarjeta y toma fallidas, sin assets ni recuperación inventada. `INTERNAL` descarga el proceso y reinicia el estado en memoria del mock: `fail_once=INTERNAL` no simula un fallo transitorio entre cargas.
  - [ ] `@mock:fail=VRAM_EXCEEDED @mock:retryable` con el mock CPU sin offload termina en error visible y toma fallida sin assets; la cola deja de tener jobs bloqueados, en espera o en ejecución. La falta temporal de recursos conserva su espera; el rechazo estructural cierra sólo el presupuesto operativo, sin inventar attempts ni cambiar historia.
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
  - [ ] El job termina `ready` conservando canción, toma y semilla. Se conserva evidencia del estado realmente observado; no se deduce una transición `interrupted` sólo del éxito final.
  - [ ] El recibo del servidor distingue continuar el mismo attempt de reintentar con ordinal nuevo; conserva solicitudes congeladas y cursores sin regresión.
  - [ ] La UI restablece SSE; se verifica por separado recuperación con `Last-Event-ID` sin sustituirla por una recarga sin cursor.
- **Capturas esperadas**: tarjeta completada tras el reinicio.
- **Cubre tareas**: T-04, T-06

### E2E-07 — Vista de canción: take maestro, valoración y letra
- **Objetivo**: trabajar la canción como proyecto.
- **Precondiciones**: una canción con 2 takes (seed).
- **Pasos**:
  1. Abrir la canción.
  2. Valorar B con ★★★★ y marcarla como maestro.
  3. Quitar la valoración y abrir la letra de la toma.
- **Aserciones**:
  - [ ] La canción apunta a B como maestro y la biblioteca previsualiza B.
  - [ ] Quitar la valoración guarda `null` y la letra de la toma permanece visible.
  - La edición de versiones y el panel de procedencia quedan aplazados por ADR-0089.
- **Capturas esperadas**: vista de canción con el maestro marcado.
- **Cubre tareas**: T-07, T-12

### E2E-08 — Biblioteca: búsqueda y preescucha
- **Objetivo**: encontrar y escuchar canciones.
- **Precondiciones**: canción creada en el escenario con un marcador único en su estilo.
- **Pasos**:
  1. Buscar el marcador con Enter.
  2. Preescuchar el maestro marcado en E2E-07.
- **Aserciones**:
  - [ ] La búsqueda FTS devuelve solo la canción esperada.
  - [ ] La preescucha reproduce el audio del maestro.
  - Colecciones, filtros y papelera quedan aplazados por ADR-0089.
- **Capturas esperadas**: resultados de búsqueda y preescucha.
- **Cubre tareas**: T-07, T-11

### E2E-09 — Beats en la onda (análisis dependiente)
**Aplazado por ADR-0089.** El bloque siguiente conserva la intención histórica y no es una puerta del M1 recortado.
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
**Aplazado por ADR-0089.** El bloque siguiente conserva la intención histórica y no es una puerta del M1 recortado.
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
- **Qué revisar**: tema oscuro, contraste, foco visible, reproductor manejado sólo con teclado y `prefers-reduced-motion`. El tema claro está aplazado por ADR-0089.
- **Por qué no se automatiza**: requiere juicio visual.
- **Criterio de aceptación**:
  - [ ] No hay texto ilegible y el reproductor se puede usar solo con el teclado.
- **Cubre tareas**: T-08, T-13

### M-03 — Backup y restauración
- **Qué revisar**: copiar el conjunto privado de pruebas, forzar el backup diario y restaurarlo en otro directorio privado; nunca borrar ni abrir desde Windows la BD del usuario. La copia SQLite no incluye ficheros: conservar también `songs/` y los recibos inmutables de `private-contexts/`; sin éstos la validación devuelve `PRIVATE_CONTEXT_INVALID` aunque estén presentes los medios.
- **Por qué se revisa por separado**: requiere comprobar que la restauración contiene todos los assets y manifiestos, además de las filas de SQLite.
- **Criterio de aceptación**:
  - [ ] La biblioteca vuelve completa y `verify_manifest.py data/songs/` pasa en verde.
- **Cubre tareas**: T-02, T-16

## Cobertura (tarea → escenarios)

Esta tabla conserva el mapa histórico. Para el alcance recortado mandan los campos «Cubre (tests)» del ledger: E2E-09 (beats) y E2E-10 (Sistema) están aplazados y no bloquean M1. Declarar cobertura no significa haber ejecutado o aprobado el escenario de despliegue.

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


## Ámbitos de evidencia — ADR-0037

[ADR-0037](../../decisiones/ADR-0037-avance-tecnico-condicionado.md) permite apertura técnica contra mock tras revisión/QA documental. Unitarios CPU, E2E mock, Docker real sin GPU, integración GPU y escucha son evidencias separadas. M-01 se conserva para aceptación final en T-16 con cobertura compartida de T-04/T-05; no se sustituye por un mock. M-02/M-03 y la resolución I-01 de T-04 permanecen obligatorias. M0/T-13 y descriptores reales verificados siguen siendo precondiciones de aceptación final.

### DOC-00 — Coherencia de secuenciación

- **Cubre tareas**: T-00.
- **Verificación**: enlaces locales de los documentos afectados y ledgers sin incoherencias; revisión A/B del diff documental. Prosa, sin UI: no se presenta como E2E.
- **Resultado requerido**: opción elegida por el orquestador bajo delegación, aperturas y aceptación explícitas, fuentes selladas intactas y ningún cierre de tarea por anticipado.

### Contrato negativo — capacidades sin verificar

Al implementar T-06/T-07/T-09, probar un descriptor con tarea y feature `verified:false`: el resolver rechaza su uso y la UI las deshabilita con motivo. El mock sintético con capacidades verificadas no transfiere esa verificación al engine real ni elude autoría/derechos. No usar excepciones de laboratorio como gate de producto.

## Almacenamiento operativo

[ADR-0089](../../decisiones/ADR-0089-reencauce-tras-codex.md) aparca el VHDX ext4 y el journal Windows de ADR-0069/0075. Los datos viven en `data/`, montado en los contenedores. Cada take se publica así:

1. Se escribe en un directorio de staging.
2. Se mueve con `rename` normal a `data/songs/<song_id>/<take_ulid>/`. El id es único, así que no hay colisión y no hace falta `NOREPLACE`.
3. Se confirma la fila en SQLite. Esa fila es la autoridad: un directorio sin fila es huérfano y se limpia al arrancar.
