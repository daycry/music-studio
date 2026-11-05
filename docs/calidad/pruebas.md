---
documento: pruebas
titulo: Estrategia de pruebas
estado: vigente
fecha: 2026-09-28
actualizado: 2026-11-05
---

# Estrategia de pruebas

**Regla de oro:** las pruebas automáticas validan **contratos observables** (estados, duración, formato, loudness, manifiesto, linaje), nunca la calidad musical. La calidad se decide escuchando ([evaluacion-escucha.md](./evaluacion-escucha.md)).

| Nivel | Qué | Herramienta | Cuándo |
|---|---|---|---|
| Unitarias server | Validación de peticiones, parser de etiquetas de letra, resolución por capacidades, transiciones de estado, linaje, manifiesto y su verificador | pytest | Siempre, sin GPU |
| Unitarias engines y `packages/weights` | Auditor de pickle (rechaza opcodes no tensoriales, convierte a safetensors), verificación SHA-256 y sello, cálculo del tope de VRAM, supervisor de proceso hijo (load/unload), cancelación, prohibición de `torch.load`/`pickle.load` (búsqueda en `apps/` y `packages/`) | pytest | Siempre, sin GPU |
| Unitarias audio-post | Normalización a ±0,5 LU del objetivo, true peak ≤ −1 dBTP (medido con ffmpeg `ebur128=peak=true`), duración ±5 %, detección de silencio, NaN y clipping, picos | pytest con audio sintético + ffmpeg LGPL | Siempre |
| Unitarias web | Parser de etiquetas (mismos casos que el server, en `packages/contracts/lyrics-cases.json`), componentes clave | vitest | Siempre |
| **Contrato** | `openapi.json` versionado = generado; `engine-v1.json` = generado desde `packages/engine-contract`; manifiesto, timeline y song.json validan contra sus JSON Schema; parsers de letra Py y TS pasan `lyrics-cases.json` | pytest + vitest | Siempre |
| **E2E** | Crear → cola → progreso → take en la canción → reproducir → descargar; errores; cancelación; recuperación tras reinicio | Playwright contra `engine-mock` | Siempre (CI local) |
| **Conformidad de adapter** | Con GPU real, por tarea del descriptor: duración, sample rate, canales, sin silencio ni NaN, telemetría completa (`load_s`, `run_s`, `vram_peak_mb`, `vram_cap_mb`, `spilled`), VRAM pico bajo el tope, liberación real tras `unload` | pytest marcado `gpu` | Al añadir o actualizar un modelo |
| **Escucha** | Batería de 10 briefs | `scripts/eval/` + oído | M0 y cada cambio de modelo |

## engine-mock

Ver [`../arquitectura/contrato-engines.md`](../arquitectura/contrato-engines.md) §7: implementa el contrato `/v1` sin GPU para todas las tareas (audio, texto en streaming, imagen, vídeo, análisis), con retardos y fallos inyectables. Es el engine por defecto en desarrollo de UI y en los E2E. Cada hito con UI tiene su `test-plan.md` (bloques E2E-xx y M-xx) en la carpeta del hito, que ejecuta el agente `qa` del plugin.

## Desarrollar y probar la web en Windows sin WSL ni GPU

Este perfil comprueba la UI con datos sintéticos. El producto conserva el despliegue Docker de la [constitución](../CONSTITUTION.md#2-arquitectura-fijada--vetada). No necesita arrancar Docker, Ollama ni engines. Prepara las dependencias con `scripts/bootstrap.ps1`: incluye la descarga y verificación de Node/pnpm portátiles mediante `fetch_web_tools.py`, sin recurrir a versiones globales. Para las pruebas de navegador, instala después Chromium dentro de las cachés del proyecto:

```powershell
. ./scripts/env.ps1
& ./scripts/pnpm.ps1 --filter ./apps/web exec playwright '--' install chromium
```

Desde la raíz, carga el entorno en cada terminal. Usa el wrapper [scripts/pnpm.ps1](../../scripts/pnpm.ps1), que ejecuta el Node gestionado y valida argumentos mediante [pnpm.py](../../scripts/pnpm.py):

```powershell
. ./scripts/env.ps1
& ./scripts/pnpm.ps1 --filter ./apps/web test
& ./scripts/pnpm.ps1 --filter ./apps/web lint
& ./scripts/pnpm.ps1 --filter ./apps/web typecheck
& ./scripts/pnpm.ps1 --filter ./apps/web build
uv run --frozen --no-sync scripts/export_contracts.py --check
```

La cobertura se activa con `exec vitest '--' run --coverage`; los umbrales y archivos medidos están en [vitest.config.ts](../../apps/web/vitest.config.ts). El recibo de una fase puede usar una configuración más específica: hay que conservarla junto con su informe y no presentar su porcentaje como cobertura de todo el repositorio. Mantén entre comillas el primer `'--'` de transporte en PowerShell; el wrapper sólo retira ese separador y conserva los posteriores.

En otra terminal inicia la web con `& ./scripts/pnpm.ps1 --filter ./apps/web dev`. El script de [package.json](../../apps/web/package.json) usa Webpack y escucha en `127.0.0.1:3000`, igual que el build usa Webpack. No sustituyas el comando por un Node del sistema.

### Preparar exclusivamente el servidor HTTP temporal

Los dos smokes de API necesitan un HTTP real en `127.0.0.1:8000`. No apuntes a la biblioteca habitual ni al stack vivo. Este ejemplo ejecutado desde la raíz crea una carpeta nueva bajo `.cache/qa-cpu/`, omite `.env`, desactiva engines y usa un token efímero. Si el puerto está ocupado, no detengas el servicio ajeno: aplaza estos dos smokes.

En una terminal con el entorno cargado:

```powershell
@'
from pathlib import Path
import secrets
import sys
import uvicorn

root = Path.cwd().resolve()
assert (root / "apps/server/app/main.py").is_file()
sys.path.insert(0, str(root / "apps/server"))
from app.main import create_app
from app.settings import Settings

data = root / ".cache/qa-cpu" / secrets.token_hex(8)
settings = Settings(
    _env_file=None, engine_token=secrets.token_urlsafe(32),
    data_dir=data, engines={}, storage_uuid=None,
)
uvicorn.run(create_app(settings), host="127.0.0.1", port=8000)
'@ | uv run --frozen --no-sync python -
```

La factoría [create_app](../../apps/server/app/main.py) conserva migración y ciclo de vida reales sobre esa BD temporal. `engines={}` impide usarla para generar canciones. Cierra únicamente estos dos procesos de prueba con `Ctrl+C` al terminar; sus datos temporales no pertenecen a la biblioteca del usuario.

### Ejecutar e interpretar Playwright CPU

Con ambos procesos anteriores disponibles:

```powershell
& ./scripts/pnpm.ps1 --filter ./apps/web exec playwright '--' test --config=playwright.cpu.config.ts
```

[playwright.cpu.config.ts](../../apps/web/playwright.cpu.config.ts) no arranca servicios: usa un worker, Chromium con `--disable-gpu` y excluye recuperación, análisis y colecciones. Guarda JSON, HTML, trazas y capturas en `.cache/playwright-ui/`. Para ejecutar sólo UI sin el HTTP temporal, añade `'--grep-invert=API-'` al mismo comando.

| Evidencia | Qué demuestra | Qué queda fuera |
|---|---|---|
| Tests UI con [fixtures](../../apps/web/e2e/fixtures.ts) | Formulario, eventos, estados, errores, biblioteca y reproducción ante respuestas controladas; una ruta API no declarada devuelve 404 | Engine, persistencia y SSE reales; audio y VRAM son sintéticos |
| [API-01/02](../../apps/web/e2e/api-smoke.spec.ts) | Rechazo de Origin ajeno y contrato OpenAPI del servidor temporal | Generación, reintento y publicación de audio |
| Unitarias y build | Comportamiento de módulos y compilación | Calidad musical, integración Docker y aceptación manual |

El [informe QA CPU de M1](../roadmap/2026-09-28-m1-mvp-estudio/testing/cpu-ui-2026-11-03.md) conserva los resultados observados y sus límites. Los E2E con engine-mock, FFmpeg, recuperación y medios reales siguen siendo una verificación distinta en el [plan canónico](../roadmap/2026-09-28-m1-mvp-estudio/test-plan.md). No se sustituyen por este perfil ni por repetirlo tres veces.

## Integración Docker con HTTP, SSE y medios reales

El perfil [playwright.integration.config.ts](../../apps/web/playwright.integration.config.ts) ejecuta los casos de [e2e/integration](../../apps/web/e2e/integration/) contra servicios ya levantados. Usa un worker, sin reintentos de Playwright ni interceptación HTTP. Chromium lleva `--disable-gpu`; el audio procede del mock CPU y pasa por el postproceso real del server.

El ámbito debe quedar preparado antes de ejecutar o descubrir pruebas. Estas siete variables son obligatorias:

| Variable | Valor requerido |
|---|---|
| `E2E_PROJECT_NAME` | Proyecto Compose exclusivo `music-studio-e2e` o `music-studio-e2e-<nombre>` |
| `E2E_COMPOSE_FILE` | Archivo Compose existente dentro de `.cache/` del repositorio |
| `E2E_ENV_FILE` | Archivo de entorno privado existente dentro de `.cache/` |
| `STUDIO_DATA_ROOT` | Directorio de datos de prueba dentro de `.cache/`, separado de la biblioteca habitual |
| `E2E_ARTIFACT_ROOT` | Directorio de resultados dentro de `.cache/`; usa uno distinto por corrida |
| `E2E_API_ORIGIN` | Origen HTTP local del API; en este stack, `http://127.0.0.1:8000` |
| `E2E_WEB_ORIGIN` | Origen HTTP local de la web; en este stack, `http://127.0.0.1:3000` |

La configuración valida confinamiento de rutas y orígenes locales. Si se adapta [docker-compose.yml](../../docker-compose.yml) a una ubicación bajo `.cache/`, hay que resolver sus contextos de build y montajes relativos. Copiarlo sin más cambia la resolución de esas rutas.

[e2e_stack.py](../../scripts/e2e_stack.py) acepta el proyecto, Compose, entorno y datos seleccionados. `up` levanta web/server/mock y siembra por API; `smoke` levanta sin sembrar; `down` detiene ese proyecto. El helper usa los puertos 8000/3000. No ejecutes dos suites sobre ese stack ni sustituyas sus datos durante una corrida.

### Preparar el ámbito privado y ejecutar la suite

La receta presupone Docker Desktop disponible y las herramientas gestionadas instaladas mediante `scripts/bootstrap.ps1` en Windows. Antes de `up`, prepara FFmpeg Linux con el descargador fijado: el Dockerfile del server necesita el archivo `tools/ffmpeg-linux/.../.archive.tar.xz` para su `COPY`. No requiere descargar pesos ni usar GPU:

```powershell
. ./scripts/env.ps1
uv run --frozen --no-sync scripts/fetch_ffmpeg_linux.py --download
```

Reserva los puertos 3000/8000 antes de usar la receta. Si hay otro stack o una QA en curso, espera a que termine; estos comandos no identifican ni detienen servicios ajenos.

Desde la raíz del repositorio, crea un ámbito nuevo y un token exclusivo de prueba. El comando `config` resuelve rutas con la raíz como directorio del proyecto. Guarda el resultado JSON, válido como entrada de Compose, dentro del ámbito privado:

```powershell
. ./scripts/env.ps1
$repo = (Get-Location).Path
$suffix = [Guid]::NewGuid().ToString('N').Substring(0, 12)
$scope = Join-Path $repo ".cache/e2e-runs/$suffix"
New-Item -ItemType Directory -Path $scope | Out-Null

$env:E2E_PROJECT_NAME = "music-studio-e2e-$suffix"
$env:E2E_COMPOSE_FILE = Join-Path $scope 'compose.resolved.json'
$env:E2E_ENV_FILE = Join-Path $scope 'stack.env'
$env:STUDIO_DATA_ROOT = Join-Path $scope 'data'
$env:E2E_ARTIFACT_ROOT = Join-Path $scope 'run-1'
$env:E2E_API_ORIGIN = 'http://127.0.0.1:8000'
$env:E2E_WEB_ORIGIN = 'http://127.0.0.1:3000'
$env:MOCK_STAGE_DELAY_MS = '5000'
$env:E2E_RECOVERY = '1'

$bytes = New-Object byte[] 32
$rng = [Security.Cryptography.RandomNumberGenerator]::Create()
try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
$token = [Convert]::ToBase64String($bytes)
$utf8 = [Text.UTF8Encoding]::new($false)
[IO.File]::WriteAllText($env:E2E_ENV_FILE, "STUDIO_ENGINE_TOKEN=$token`n", $utf8)

$previousToken = [Environment]::GetEnvironmentVariable('STUDIO_ENGINE_TOKEN', 'Process')
try {
  $env:STUDIO_ENGINE_TOKEN = $token
  $resolved = & docker compose --project-directory $repo `
    --project-name $env:E2E_PROJECT_NAME --profile studio `
    --env-file $env:E2E_ENV_FILE --file docker-compose.yml config --format json
  if ($LASTEXITCODE -ne 0) { throw 'No se pudo resolver el Compose de pruebas' }
} finally {
  [Environment]::SetEnvironmentVariable('STUDIO_ENGINE_TOKEN', $previousToken, 'Process')
  $token = $null
  $previousToken = $null
}
[IO.File]::WriteAllText($env:E2E_COMPOSE_FILE, ($resolved -join "`n"), $utf8)
$resolved = $null
```

`stack.env` y `compose.resolved.json` contienen el token. Mantén ambos en `.cache/`; no imprimas su contenido ni los publiques. La receta no modifica `.env`. La resolución del Compose verifica configuración; todavía no arranca servicios ni demuestra un arranque desde cero.

Conserva esta terminal y sus variables para el arranque y las pruebas:

```powershell
uv run --frozen --no-sync scripts/e2e_stack.py up
```

Con la aplicación arrancada, prepara el navegador antes de la suite. Esta descarga sólo se necesita para las pruebas: el wrapper fija `PLAYWRIGHT_BROWSERS_PATH` y el entorno de caché dentro del proyecto.

```powershell
& ./scripts/pnpm.ps1 --filter ./apps/web exec playwright '--' install chromium
& ./scripts/pnpm.ps1 --filter ./apps/web exec playwright '--' test --config=playwright.integration.config.ts
```

El helper arranca sólo `web`, `server` y `engine-mock`, del perfil `studio`. Sus dependencias quedan entre esos tres servicios; no solicitan GPU. La resolución técnica de este Compose se comprobó sin arrancarlo. Una ejecución satisfactoria requiere además que build, health, siembra y suite terminen correctamente.

Para otra corrida, cambia `E2E_ARTIFACT_ROOT` a `Join-Path $scope 'run-2'` y vuelve a ejecutar Playwright. Al terminar, `uv run --frozen --no-sync scripts/e2e_stack.py down` detiene sólo el proyecto seleccionado y conserva los archivos de prueba. No uses `--reset-data` sobre evidencia que quieras conservar.

La prueba de recuperación exige que el mock arranque con `MOCK_STAGE_DELAY_MS=5000`, como en la receta. El Compose general tiene otro valor por defecto. Sin `E2E_RECOVERY=1`, Playwright omite recuperación: una corrida con ese skip no acredita los 14 casos. Los flags E2E no sustituyen la selección explícita de proyecto, archivos y datos.

El [wrapper pnpm](../../scripts/pnpm.py) transporta sólo los controles E2E validados. Para recuperación resuelve el ejecutable Compose autónomo y un endpoint Docker exclusivamente local. Si no están en la ubicación esperada, admite `E2E_COMPOSE_CLI`, `E2E_DOCKER_CLI` y `E2E_DOCKER_HOST` explícitos y validados. Conserva el HOME aislado del proceso de pruebas sin copiar credenciales del usuario.

### Qué acredita cada prueba integrada

| Fuente | Contrato observable |
|---|---|
| [core.spec.ts](../../apps/web/e2e/integration/core.spec.ts) | Letra y autoría; uno por defecto y dos outputs con capacidad CPU verificada y estimación válida; estados reales, publicación, onda, reproducción, Range, descargas MP3/FLAC, maestro, búsqueda y preescucha |
| `core.spec.ts`: errores y cancelación | Fallos persistentes, reintento explícito, cancelación terminal y liberación de cola ante `VRAM_EXCEEDED` imposible en CPU |
| [recovery.spec.ts](../../apps/web/e2e/integration/recovery.spec.ts) | SIGKILL y arranque del server dedicado; reconexión SSE, mismo take/canción/semilla y una sola tarjeta hasta `ready` |
| [api-smoke.spec.ts](../../apps/web/e2e/integration/api-smoke.spec.ts) | Rechazo de Host/Origin ajenos y contrato OpenAPI por HTTP real |
| [layout.spec.ts](../../apps/web/e2e/integration/layout.spec.ts) | Biblioteca en cuadrícula y lista a 1440, 768 y 390 px |

Una capacidad CPU verificada puede declarar VRAM cero. Esto permite probar dos outputs del mock; no acredita que dos variantes de ACE-Step quepan en la GPU.

Las sondas privadas de recuperación runtime distinguen caída durante generación, reinicio del engine y caída durante FFmpeg. Comprueban, respectivamente, continuidad del attempt y cursor; nuevo attempt del engine; y misma ejecución/plan CPU con nueva lease hasta publicar. Se ejecutaron sobre una imagen anterior al fix final. Complementan la prueba del navegador; no sustituyen las tres corridas independientes de QA ni verifican por sí solas la imagen final.

JSON, HTML, trazas y capturas quedan bajo `E2E_ARTIFACT_ROOT`. Para evaluar un resultado, conserva también la identidad de las imágenes y fuentes desplegadas. Una suite sobre una imagen anterior no valida automáticamente un fix posterior. Los resultados y las puertas de aceptación pertenecen al [ledger M1](../roadmap/2026-09-28-m1-mvp-estudio/tasks.md) y sus informes de testing.

La revisión documental describe el procedimiento; no certifica un arranque desde cero ni da por terminada una QA en curso. M1 conserva la aceptación con ACE-Step real y escucha del propietario, según el [recorte aprobado](../roadmap/2026-09-28-m1-mvp-estudio/spec.md#recorte-del-2026-10-22-adr-0089). T-15/T-16 siguen sujetos a sus verificaciones; M2/M3 permanecen congelados por [ADR-0089](../decisiones/ADR-0089-reencauce-tras-codex.md).

Última actualización: 2026-11-05.
