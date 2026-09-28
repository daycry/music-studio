# Entorno de desarrollo de music-studio para bash/WSL. Uso:  source scripts/env.sh
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export UV_CACHE_DIR="$root/.cache/uv" UV_PYTHON_INSTALL_DIR="$root/.cache/uv/python" UV_PYTHON_INSTALL_BIN=0
export UV_PROJECT_ENVIRONMENT="$root/.venv" HF_HOME="$root/models/.hf-cache" TORCH_HOME="$root/models/.torch" PNPM_STORE_DIR="$root/.cache/pnpm"
