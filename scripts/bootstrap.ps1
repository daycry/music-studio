# Reconstruye el entorno completo desde los ficheros versionados (ADR-0005).
# Uso (desde la raíz del proyecto):  .\scripts\bootstrap.ps1
# Falla ruidoso y pronto: cualquier paso que falle detiene el script.
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

. (Join-Path $root "scripts\env.ps1")

Write-Host "== uv python install (lee .python-version) =="
uv python install
if ($LASTEXITCODE -ne 0) { throw "uv python install falló (exit $LASTEXITCODE)" }

Write-Host "== uv sync --frozen =="
uv sync --frozen
if ($LASTEXITCODE -ne 0) { throw "uv sync --frozen falló (exit $LASTEXITCODE)" }

if (-not (Test-Path -LiteralPath (Join-Path $root 'pnpm-lock.yaml'))) { throw 'Bootstrap incompleto: falta pnpm-lock.yaml revisado.' }
Write-Host '== pnpm install --frozen-lockfile --ignore-scripts =='
& (Join-Path $PSScriptRoot 'pnpm.ps1') install --frozen-lockfile --ignore-scripts
if ($LASTEXITCODE -ne 0) { throw "Bootstrap incompleto: pnpm falló (exit $LASTEXITCODE)." }
Write-Host "music-studio: bootstrap completo."
