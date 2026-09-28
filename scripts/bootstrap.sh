#!/usr/bin/env bash
# Reconstruye el entorno completo desde los ficheros versionados (ADR-0005).
# Uso (desde la raíz del proyecto):  source scripts/bootstrap.sh   (o bash scripts/bootstrap.sh)
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

# shellcheck source=./env.sh
source "$root/scripts/env.sh"

echo "== uv python install (lee .python-version) =="
uv python install

echo "== uv sync --frozen =="
uv sync --frozen

if command -v pnpm >/dev/null 2>&1; then
    if [ -f "$root/pnpm-lock.yaml" ]; then
        echo "== pnpm install --frozen-lockfile =="
        pnpm install --frozen-lockfile
    else
        echo "AVISO: no existe pnpm-lock.yaml todavía: omito 'pnpm install'. Genera el lockfile una vez con 'pnpm install' cuando pnpm esté disponible." >&2
    fi
else
    echo "AVISO: pnpm no está instalado en esta máquina: omito la instalación de apps/web. Instala pnpm (por ejemplo 'corepack enable') para completar el bootstrap del front." >&2
fi

echo "music-studio: bootstrap completo."
