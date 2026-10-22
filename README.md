# music-studio

Estudio local de generacion musical con IA, con flujo de cancion a videoclip. La aplicacion usa Next.js, FastAPI y engines en Docker; Ollama permanece en WSL2 para poder reutilizarlo fuera del estudio. La documentacion vigente esta en `docs/README.md`.

## Requisitos

- Windows 11, Docker Desktop con backend WSL2 y una cuenta con permisos de administrador para montar el VHDX persistente.
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

## Almacenamiento persistente en WSL2

El despliegue persistente exige un VHDX ext4 acreditado. El override `docker-compose.storage.yml` falla cerrado si faltan `STUDIO_STORAGE_ROOT` o `STUDIO_STORAGE_UUID`; `create_host_path: false` evita que Docker cree un directorio vacio fingiendo que es el volumen.

1. Ejecuta la preparacion offline y la publicacion Windows desde la raiz del proyecto. El primer comando deja un recibo en `.cache/dev-cycle/storage-<operation_id>/receipt.json` y no monta nada:

```powershell
. .\scripts\env.ps1
.venv\Scripts\python.exe scripts\storage_offline.py --project . --size-bytes 67108864 --uuid 12345678-1234-5678-1234-567812345678 --operation-id 01ARZ3NDEKTSV4RRFFQ69G5FAV --image music-studio-storage-tools-t05-runtime1:private --execute
```

2. Publica el VHDX verificado en `data/_storage/studio-data.vhdx` con custodia Windows. La publicacion es write-once y actualiza el recibo a `published`:

```powershell
.venv\Scripts\python.exe -c "from scripts.storage_publish import publish_verified_vhdx; publish_verified_vhdx('.', '.cache/dev-cycle/storage-01ARZ3NDEKTSV4RRFFQ69G5FAV/receipt.json')"
```

3. Abre PowerShell como administrador y adjunta el VHDX al WSL. El operador compara los bloques antes y despues, exige el UUID ext4 y valida `findmnt` y `blkid`; si falla, revierte el mount y el attach:

```powershell
.venv\Scripts\python.exe scripts\storage_attach.py --project . --receipt .cache/dev-cycle/storage-01ARZ3NDEKTSV4RRFFQ69G5FAV/receipt.json --distro Ubuntu --mountpoint /mnt/studio-data --execute
```

La secuencia usa `wsl.exe --mount <vhdx> --vhd --bare` y despues monta el dispositivo ext4 dentro de la distribucion. Consulta la [documentacion oficial de montaje de discos en WSL](https://learn.microsoft.com/en-us/windows/wsl/wsl2-mount-disk). No se debe sustituir este paso por un bind a una carpeta vacia ni por un `mkdir` automatico.

4. Arranca el perfil persistente desde el contexto que ve `/mnt/studio-data`, pasando el UUID que figura en el recibo:

```powershell
$env:STUDIO_STORAGE_ROOT = '/mnt/studio-data'
$env:STUDIO_STORAGE_UUID = '12345678-1234-5678-1234-567812345678'
docker compose --profile studio -f docker-compose.yml -f docker-compose.storage.yml config -q
docker compose --profile studio -f docker-compose.yml -f docker-compose.storage.yml up -d web server engine-mock
```

Para ACE-Step o el analisis se sustituyen los servicios mock por los engines correspondientes. El server es el unico proceso que escribe en la base de datos y los engines devuelven sus salidas en `data/tmp/<job_id>`.

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
- `docs/roadmap/2026-09-28-m1-mvp-estudio/`: spec, plan, ledger y evidencias del MVP.
- `.claude/`: configuracion versionada del flujo `custom-agents`.

Para lint y tests Python, carga primero `scripts/env.ps1` y usa `uv run`. Los tests GPU se ejecutan dentro del contenedor del engine; los tests CPU se pueden ejecutar con `uv run pytest -m "not gpu"`.
