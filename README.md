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

Las rutas reproducibles equivalentes son `scripts/bootstrap.ps1`, `scripts/init_env.py`, `scripts/e2e_stack.py up` y `scripts/e2e_stack.py down`; en los bloques PowerShell se escriben con barra inversa.

En bash/WSL se puede usar `source scripts/env.sh` y `bash scripts/bootstrap.sh`.

## MVP reproducible con datos mock

Este es el camino diario para desarrollar la UI y el API. Levanta solo `web`, `server` y `engine-mock`, publica en localhost y no necesita ACE-Step, Ollama ni una GPU libre.

```powershell
. .\scripts\env.ps1
.venv\Scripts\python.exe scripts\e2e_stack.py up
# abrir http://127.0.0.1:3000/create
pnpm --filter ./apps/web exec playwright -- test
.venv\Scripts\python.exe scripts\e2e_stack.py down
```

Para reiniciar unicamente el server durante una prueba de recuperacion:

```powershell
.venv\Scripts\python.exe scripts\e2e_stack.py restart-server
```

`E2E_ISOLATED=1` o `E2E_RECOVERY=1` hace que la prueba use `.cache/e2e-data` y no toque los datos persistentes del proyecto.

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
