# music-studio

Estudio personal de generación musical con IA, estilo Suno + Sondo (canción → videoclip). Local por defecto, en una RTX 5070 de 12 GB. Ver `CLAUDE.md` y `docs/README.md` para el mapa completo de documentación.

## Requisitos

- Windows 11 con Git, [uv](https://docs.astral.sh/uv/) y Node 22.
- [pnpm](https://pnpm.io/) (vía `corepack enable`) para `apps/web`. Es opcional para el backend: `scripts/bootstrap.*` avisa y sigue si no está.
- Docker Desktop para los engines GPU (a partir de M0/T-0x).

## Primer arranque

```powershell
git clone <remoto-privado> music-studio
cd music-studio
.\scripts\bootstrap.ps1        # instala el intérprete, sincroniza .venv y (si hay pnpm) node_modules
uv run scripts/init_env.py     # crea .env desde .env.example y genera STUDIO_ENGINE_TOKEN
```

En bash/WSL: `source scripts/bootstrap.sh` (o `bash scripts/bootstrap.sh`).

## Comandos de desarrollo

Ver la sección «Comandos de desarrollo» de `CLAUDE.md`.

## Documentación

Todo vive en `docs/`. Empieza por `docs/README.md` y `docs/CONSTITUTION.md`.
