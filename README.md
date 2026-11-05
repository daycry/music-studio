# music-studio

Estudio local de generacion musical con IA, con flujo de cancion a videoclip. La aplicacion usa Next.js, FastAPI y engines en Docker; Ollama permanece en WSL2 para poder reutilizarlo fuera del estudio. La documentacion vigente esta en `docs/README.md`.

## Requisitos

- Windows 11, Docker Desktop con backend WSL2.
- Git, `uv`, Node 22 y `pnpm` (se puede activar con `corepack enable`).
- RTX NVIDIA para ACE-Step y ComfyUI. El recorrido mock no necesita GPU.
- WSL2 con la distribucion Ubuntu. Ollama se instala y mantiene en WSL2, nunca dentro de este Compose.

## Primer arranque

```powershell
git clone https://github.com/daycry/music-studio.git music-studio
cd music-studio
. .\scripts\env.ps1
.\scripts\bootstrap.ps1
.venv\Scripts\python.exe scripts\init_env.py
```

`bootstrap.ps1` instala el interprete fijado por `.python-version`, sincroniza las dependencias Python y prepara `node_modules` con el lockfile. No instala paquetes en el Python global.

Las herramientas de arranque son `scripts/bootstrap.ps1`, `scripts/init_env.py` y `scripts/e2e_stack.py`. La guía de pruebas explica cómo preparar el ámbito privado antes de ejecutar `up` y `down`.

En bash/WSL se puede usar `source scripts/env.sh` y `bash scripts/bootstrap.sh`.

## MVP reproducible con datos mock

El recorrido técnico levanta solo `web`, `server` y `engine-mock`, publica en localhost y no necesita ACE-Step, Ollama ni una GPU libre. Comprueba integración y medios reales con audio sintético; la aceptación de M1 conserva ACE-Step real y escucha del propietario.

Sigue primero la [receta de preparación del ámbito privado](docs/calidad/pruebas.md#preparar-el-ámbito-privado-y-ejecutar-la-suite). Genera un token de prueba y un Compose resuelto bajo `.cache/`, con contextos y montajes absolutos. Configura las siete variables obligatorias: `E2E_PROJECT_NAME`, `E2E_COMPOSE_FILE`, `E2E_ENV_FILE`, `STUDIO_DATA_ROOT`, `E2E_ARTIFACT_ROOT`, `E2E_API_ORIGIN` y `E2E_WEB_ORIGIN`.

Conserva la terminal de esa receta. Con los puertos 3000/8000 libres y sin otra QA sobre el stack, ejecuta:

```powershell
. .\scripts\env.ps1
uv run --frozen --no-sync scripts/e2e_stack.py up
# abrir http://127.0.0.1:3000/create
& ./scripts/pnpm.ps1 --filter ./apps/web exec playwright '--' test --config=playwright.integration.config.ts
uv run --frozen --no-sync scripts/e2e_stack.py down
```

Para reiniciar unicamente el server durante una prueba de recuperacion:

```powershell
uv run --frozen --no-sync scripts/e2e_stack.py restart-server
```

La receta activa `E2E_RECOVERY=1` y arranca el mock con `MOCK_STAGE_DELAY_MS=5000`. Sin esa coordinación, recuperación se omite. El aislamiento depende de los destinos privados explícitos y del proyecto Compose exclusivo; los flags E2E no los sustituyen. Playwright guarda los informes bajo `E2E_ARTIFACT_ROOT`.

## Datos

Los datos viven en `data/` (o en `STUDIO_DATA_ROOT`), montado en los contenedores. La publicación de takes es sencilla: directorio por id único, `rename` dentro de `data/` y SQLite como autoridad ([ADR-0089](docs/decisiones/ADR-0089-reencauce-tras-codex.md)). El server es el único proceso que escribe en la base de datos, y los engines devuelven sus salidas en `data/tmp/<job_id>`. Para ACE-Step o el análisis se sustituyen los servicios mock por los engines correspondientes.

**Aviso:** no abras `data/db/studio.sqlite` (ni con Python ni con DB Browser) desde Windows mientras el stack corre. SQLite en modo WAL sobre el bind de Docker Desktop no comparte bloqueos con el host, y al cerrar esa conexión se borran `-wal` y `-shm` en uso, con pérdida de escrituras. Consulta por la API o con `docker compose exec server`.

## GPU y Ollama

Antes de cargar un engine GPU, comprueba el modelo compartido y libera solo el modelo, sin detener el servicio ni borrar pesos:

```powershell
wsl -d Ubuntu -e ollama ps
wsl -d Ubuntu -e ollama stop mimo:9b-q5
nvidia-smi
```

El arranque de ACE-Step requiere que `nvidia-smi` este aproximadamente por debajo de 1,6 GB antes de cargar el modelo. Al terminar el trabajo, vuelve a cargarlo con `wsl -d Ubuntu -e ollama run mimo:9b-q5`. La politica es un modelo en VRAM a la vez y esta descrita en `docs/arquitectura/entorno.md`.

## Desarrollo y documentacion

- `docs/CONSTITUTION.md`: reglas permanentes del proyecto.
- `docs/arquitectura/contrato-engines.md`: contrato `/v1` de los engines.
- `docs/roadmap/2026-09-28-m1-mvp-estudio/`: spec, plan y ledger del MVP.
- `CONTINUE-HERE.md`: dónde se paró y cuál es el siguiente paso.
- `.claude/`: configuracion versionada del flujo `custom-agents`.

Para lint y tests Python, carga primero `scripts/env.ps1` y usa `uv run`. Los tests GPU se ejecutan dentro del contenedor del engine; los tests CPU se pueden ejecutar con `uv run pytest -m "not gpu"`.
