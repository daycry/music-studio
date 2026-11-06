#!/usr/bin/env bash
# ADR-0069: plan sin efectos; exit 2 indica bloqueo, nunca éxito de despliegue.
set -euo pipefail
studio_storage_script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
source "$studio_storage_script_dir/env.sh"
cd -- "$studio_storage_script_dir/.."
exec uv run --no-sync "$studio_storage_script_dir/storage.py" "$@"
