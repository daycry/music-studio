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

if [ ! -f "$root/pnpm-lock.yaml" ]; then
    echo 'Bootstrap incompleto: falta pnpm-lock.yaml revisado.' >&2
    exit 1
fi
echo '== pnpm install --frozen-lockfile --ignore-scripts =='
bash "$root/scripts/pnpm.sh" install --frozen-lockfile --ignore-scripts
echo "music-studio: bootstrap completo."
