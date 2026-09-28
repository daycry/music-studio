---
name: python-isolation
description: Never install dependencies into the machine's Python; use the project-local uv interpreter and .venv via scripts/env.ps1
metadata:
  type: feedback
---

Never install Python packages into the system/machine Python. Use the uv-managed interpreter in `.cache/uv/python/` and the project `.venv/`. Load `scripts/env.ps1` (PowerShell: `. .\scripts\env.ps1`) or `scripts/env.sh` before any Python/uv command; `uv.toml` enforces `only-managed` + `python-downloads = manual`.

**Why:** the user asked on 2026-09-28 to "crea un venv de python para no instalar dependencias en el python de la máquina", consistent with [[project-context]] (everything inside the folder).
**How to apply:** run Python tooling only through the env script / `uv run`; if uv needs a new interpreter, install it with the env loaded so it lands in `.cache/uv/python`; never `pip install` outside `.venv`. Remove any shim uv drops in `%USERPROFILE%\.local\bin`.
