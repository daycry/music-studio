# ADR-0069: plan sin efectos. Exit 2 = provisión/preflight aún bloqueados.
# No ejecuta WSL, Hyper-V, diskpart, formato, servicios ni Docker.
$ErrorActionPreference = 'Stop'
$studioStorageRoot = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot 'env.ps1')
Push-Location -LiteralPath $studioStorageRoot
try {
    & uv run --no-sync (Join-Path $PSScriptRoot 'storage.py') @args
    $studioStorageExit = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $studioStorageExit
