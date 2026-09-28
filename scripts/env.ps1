# Entorno de desarrollo de music-studio. Uso (desde la raíz del proyecto):  . .\scripts\env.ps1
# Mantiene intérpretes, cachés y venv dentro de la carpeta (ADR-0005); no toca el Python de la máquina.
$root = Split-Path -Parent $PSScriptRoot
$env:UV_CACHE_DIR          = Join-Path $root ".cache\uv"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $root ".cache\uv\python"
$env:UV_PYTHON_INSTALL_BIN = "0"      # sin accesos directos python3.x.exe en %USERPROFILE%\.local\bin
$env:UV_PROJECT_ENVIRONMENT = Join-Path $root ".venv"
$env:HF_HOME               = Join-Path $root "models\.hf-cache"
$env:TORCH_HOME            = Join-Path $root "models\.torch"
$env:PNPM_STORE_DIR        = Join-Path $root ".cache\pnpm"

$activate = Join-Path $root ".venv\Scripts\Activate.ps1"
if (Test-Path $activate) {
    & $activate
    Write-Host "music-studio: entorno listo ($(python --version))"
} else {
    Write-Host "music-studio: variables de entorno listas (.venv aún no existe; ejecuta scripts\bootstrap.ps1)"
}
