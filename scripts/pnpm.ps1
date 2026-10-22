# Python gestionado y raíz derivada de este archivo, sin fallback de perfil.
$studioRoot = Split-Path -Parent $PSScriptRoot
$studioPython = Join-Path $studioRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $studioPython -PathType Leaf)) {
    Write-Error 'pnpm NO LISTO: falta .venv; ejecuta el bootstrap del entorno gestionado.'
    exit 1
}
# Windows PowerShell 5 altéra comillas al pasar arrays a programas nativos.
# JSON/base64 transporta cadenas tipadas sin interpolación ni evaluación de shell.
$studioArgsJson = ConvertTo-Json -InputObject @($args) -Compress
$studioArgsEncoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($studioArgsJson))
& $studioPython -I -B (Join-Path $PSScriptRoot 'pnpm.py') --studio-argv-base64 $studioArgsEncoded
exit $LASTEXITCODE
