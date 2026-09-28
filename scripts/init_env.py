"""Crea `.env` a partir de `.env.example` y genera `STUDIO_ENGINE_TOKEN` una sola vez.

Uso:  uv run scripts/init_env.py

Idempotente: si `.env` ya existe y ya tiene un valor para `STUDIO_ENGINE_TOKEN`,
no lo regenera (ese token es persistente y lo comparten el CLI, el server y los
engines vía la cabecera `X-Studio-Engine-Token`; ver
docs/arquitectura/convenciones.md §5).
"""

from __future__ import annotations

import re
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_EXAMPLE = ROOT / ".env.example"
ENV_FILE = ROOT / ".env"

TOKEN_VAR = "STUDIO_ENGINE_TOKEN"
TOKEN_RE = re.compile(rf"^{TOKEN_VAR}=(.*)$")


def _existing_token(lines: list[str]) -> str | None:
    for line in lines:
        match = TOKEN_RE.match(line)
        if match and match.group(1).strip():
            return match.group(1).strip()
    return None


def main() -> None:
    if not ENV_EXAMPLE.exists():
        raise SystemExit(f"No existe {ENV_EXAMPLE}: nada de lo que partir.")

    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
        if _existing_token(lines):
            print(f"{ENV_FILE.name} ya existe y {TOKEN_VAR} ya está fijado: no se toca nada.")
            return
        print(f"{ENV_FILE.name} ya existe pero sin {TOKEN_VAR}: lo añado.")
    else:
        lines = ENV_EXAMPLE.read_text(encoding="utf-8").splitlines()
        print(f"Creo {ENV_FILE.name} a partir de {ENV_EXAMPLE.name}.")

    new_token = secrets.token_hex(32)
    found = False
    out_lines: list[str] = []
    for line in lines:
        if line.startswith(f"{TOKEN_VAR}="):
            out_lines.append(f"{TOKEN_VAR}={new_token}")
            found = True
        else:
            out_lines.append(line)
    if not found:
        out_lines.append(f"{TOKEN_VAR}={new_token}")

    ENV_FILE.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"{TOKEN_VAR} generado y guardado en {ENV_FILE.name} (persistente: no se regenera en futuras ejecuciones).")


if __name__ == "__main__":
    main()
