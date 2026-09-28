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

$pnpm = Get-Command pnpm -ErrorAction SilentlyContinue
if ($pnpm) {
    if (Test-Path (Join-Path $root "pnpm-lock.yaml")) {
        Write-Host "== pnpm install --frozen-lockfile =="
        pnpm install --frozen-lockfile
        if ($LASTEXITCODE -ne 0) { throw "pnpm install --frozen-lockfile falló (exit $LASTEXITCODE)" }
    } else {
        Write-Warning "No existe pnpm-lock.yaml todavía: omito 'pnpm install'. Genera el lockfile una vez con 'pnpm install' cuando pnpm esté disponible."
    }
} else {
    Write-Warning "pnpm no está instalado en esta máquina: omito la instalación de apps/web. Instala pnpm (por ejemplo 'corepack enable') para completar el bootstrap del front."
}

Write-Host "music-studio: bootstrap completo."
