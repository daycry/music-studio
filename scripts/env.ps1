# Entorno de desarrollo de music-studio. Uso (desde la raíz del proyecto):  . .\scripts\env.ps1
# Mantiene intérpretes, cachés y venv dentro de la carpeta (ADR-0005); no toca el Python de la máquina.
$root = Split-Path -Parent $PSScriptRoot
$env:UV_CACHE_DIR          = Join-Path $root ".cache\uv"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $root ".cache\uv\python"
$env:UV_PYTHON_INSTALL_BIN = "0"      # sin accesos directos python3.x.exe en %USERPROFILE%\.local\bin
$env:UV_PROJECT_ENVIRONMENT = Join-Path $root ".venv"
$env:HF_HOME               = Join-Path $root "models\.hf-cache"
$env:TORCH_HOME            = Join-Path $root "models\.torch"
$env:npm_config_store_dir = Join-Path $root ".cache\pnpm"   # pnpm lee npm_config_store_dir (no PNPM_STORE_DIR)
# pnpm standalone vive en %PNPM_HOME%\bin; en sesiones abiertas antes de instalarlo no está en PATH.
if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    $pnpmHome = [Environment]::GetEnvironmentVariable('PNPM_HOME', 'User')
    if ($pnpmHome -and (Test-Path (Join-Path $pnpmHome 'bin\pnpm.cmd'))) { $env:Path = (Join-Path $pnpmHome 'bin') + ';' + $env:Path }
}

$activate = Join-Path $root ".venv\Scripts\Activate.ps1"
if (Test-Path $activate) {
    & $activate
    Write-Host "music-studio: entorno listo ($(python --version))"
} else {
    Write-Host "music-studio: variables de entorno listas (.venv aún no existe; ejecuta scripts\bootstrap.ps1)"
}
