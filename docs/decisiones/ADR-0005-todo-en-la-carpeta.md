# ADR-0005 · Todo dentro de la carpeta del proyecto

- **Estado:** aceptada · **Fecha:** 2026-09-28 · Revisada el mismo día: se afina qué se sincroniza y se añaden las cachés

## Decisión

- **Todo dentro de `music-studio/`.** Código, pesos (`models/`), herramientas descargadas (`tools/`), datos (`data/`), evaluaciones (`eval/`), cachés (`.cache/`, `models/.hf-cache`) y la memoria del proyecto (`docs/memory/`). Nada va a otras unidades ni a `%USERPROFILE%`: las variables de caché (`HF_HOME`, `UV_CACHE_DIR`, `npm_config_store_dir`, `TORCH_HOME`) apuntan dentro de la carpeta ([`../arquitectura/convenciones.md`](../arquitectura/convenciones.md) §4).
- **`.gitignore`** excluye:
  - `models/*`, salvo `models/models.lock.json`;
  - `tools/*`, salvo `tools/tools.lock.json`;
  - `data/`, `.cache/`, `node_modules/`, `.venv/`, `.next/` y `.env`;
  - `eval/*`, salvo `eval/briefs/` y `eval/results/*.md`. Patrón exacto: `eval/*` · `!eval/briefs/` · `!eval/results/` · `eval/results/*` · `!eval/results/*.md` (git no reincluye ficheros dentro de un directorio excluido).

  Los `.gitkeep` de las carpetas ignoradas se añaden con `git add -f`.
- **Reconstruir desde cero.** Se versionan (y sincronizan) las *recetas*, nunca los resultados: `.python-version`, `uv.toml`, `uv.lock`, `pnpm-lock.yaml`, `models.lock.json` y `tools.lock.json`. Con ellas, `scripts/bootstrap.ps1` reconstruye intérprete, `.venv/` y `node_modules/` (`uv python install` · `uv sync --frozen` · `pnpm install --frozen-lockfile`), y `scripts/fetch_models.py` / `fetch_tools.py` reconstruyen `models/` y `tools/`. `.venv/` no se sincroniza también porque no es portable (rutas absolutas y binarios de esta máquina).

## Sincronización con Synology Drive

Synology Drive sincroniza la carpeta (existe `.SynologyWorkingDirectory`). En el filtro de sincronización:

| Ruta | ¿Se sincroniza? | Motivo |
|---|---|---|
| Código, `docs/`, `eval/briefs`, `eval/results` | **Sí** | Copia del trabajo |
| `data/songs/`, `data/characters/`, `data/uploads/`, `data/backups/` | **Sí** | Es la biblioteca: sin esto, no tendría copia |
| `data/db/` | **No** | SQLite abierto en modo WAL: sincronizarlo a medio escribir lo corrompe. La copia va en `data/backups/` |
| `data/tmp/`, `data/cli/`, `data/logs/`, `data/trash/` | No | Temporales |
| `models/`, `tools/`, `.cache/`, `node_modules/`, `.venv/`, `.next/`, `eval/takes/`, `eval/capabilities/` | No | Se reconstruyen desde los locks; ocupan decenas de GB |

Esta configuración es una **acción manual del propietario** (M0 T-00), antes de crear cualquiera de esas carpetas.

## Rendimiento

Leer una carpeta de Windows desde un contenedor de Docker Desktop (WSL2) es más lento que desde un disco Linux nativo. Se mide en M0 T-09. Si la carga de pesos supera los 30 s, se valorará una caché dentro del contenedor, sin dejar de tratar `models/` como fuente de verdad.
