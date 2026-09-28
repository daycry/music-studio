# music-studio

Estudio personal de generación musical con IA, estilo Suno + Sondo (canción → videoclip). Se ejecuta en local en una RTX 5070 de 12 GB. Stack: Next.js + FastAPI (sin torch) + engines GPU en Docker con contrato `/v1`. Documentación, UI y commits en castellano; **identificadores de código, API, BD y JSON en inglés**.

## Documentación

- **Al retomar el trabajo, lee primero `CONTINUE-HERE.md`** (dónde se paró y cómo seguir).
- Empieza por `docs/README.md` (mapa) y respeta **`docs/CONSTITUTION.md`** (principios permanentes; cambiarlos exige ADR). Fuente de verdad: todo `docs/` salvo `docs/archive/`, que es histórico y no vigente.
- Antes de tocar contratos o datos: `docs/arquitectura/contrato-engines.md`, `datos.md` y `convenciones.md`.
- Estado de las tareas: **solo** en el `tasks.md` del hito, en `docs/roadmap/<fecha>-<slug>/` (estados `borrador · en-progreso · en-revision · completado · cancelado`; validar con `ledger-lint`). Cada tarea se cierra ejecutando su **Verificación**. Hito actual: **M0**. Cómo implementar: `docs/roadmap/README.md`.
- Toda decisión que cambie algo ya documentado va a un ADR nuevo en `docs/decisiones/`, y se actualiza el documento afectado.

## Reglas clave

- **Local por defecto en todo** (música, letras, imagen, vídeo). APIs y suscripciones solo como alternativa opcional, desactivada de fábrica (ADR-0014). La música es siempre local.
- **La canción es el proyecto** (ADR-0013): takes, letra, portada, vídeo y exportaciones cuelgan de `song`.
- **Todo dentro de esta carpeta.** Código, pesos (`models/`), datos (`data/`), evaluaciones (`eval/`) y memoria (`docs/memory/`). Nada en otras unidades.
- **Pesos seguros.** Solo `safetensors`/`gguf`/`onnx` en runtime; nunca `torch.load` ni `pickle.load` (los pickle oficiales se convierten con el auditor). Fijados por revisión y verificados con SHA-256 contra `models/models.lock.json`; el código `trust_remote_code` va fijado por hash.
- **Engines sin estado**: devuelven salida cruda en `data/tmp/`; post-proceso, manifiesto y render los hace el server. Solo el server escribe en la BD.
- **Un modelo en VRAM a la vez**, en proceso hijo (unload = terminar el proceso), BF16 por defecto y tope calculado de la VRAM **libre**: en WSL2, si se desborda, la GPU tira de RAM sin avisar. La 5070 es tier 4 de ACE-Step: forzar modos explícitos.
- **Licencias:** ningún modelo ni herramienta entra en el código sin su fila en `docs/legal/licencias.md`. Los modelos no comerciales solo se usan para comparar, nunca como motor por defecto.
- **UX derivada de Suno, sin copiar su identidad visual.**

## Comandos de desarrollo

Carga siempre el entorno antes de usar `uv`/`python` (nunca instales nada en el Python de la máquina):

```powershell
. .\scripts\env.ps1     # PowerShell
```
```bash
source scripts/env.sh   # bash / WSL
```

| Qué | Comando |
|---|---|
| Reconstruir todo desde cero (intérprete, `.venv`, `node_modules`) | `.\scripts\bootstrap.ps1` (o `scripts/bootstrap.sh`) |
| Crear/completar `.env` (genera `STUDIO_ENGINE_TOKEN` una sola vez) | `uv run scripts/init_env.py` |
| Instalar/actualizar dependencias Python según los locks | `uv sync --frozen` |
| Añadir o actualizar una dependencia Python | `uv add <paquete>` (regenera `uv.lock`) |
| Tests Python (excluye los que necesitan GPU) | `uv run pytest -m "not gpu"` |
| Lint + formato Python | `uv run ruff check .` · `uv run ruff format .` |
| Hooks de pre-commit | `uv run pre-commit run --all-files` |
| Instalar dependencias de `apps/web` | `pnpm install --frozen-lockfile` |
| Lint / tests de `apps/web` | `pnpm lint` · `pnpm test` |
| Generar tipos TS desde `openapi.json` (M1) | `pnpm gen` |

## Memoria

La memoria persistente del proyecto vive **dentro del repositorio**, en `docs/memory/`. No uses el directorio de memoria de usuario (`~/.claude/projects/.../memory/`).

- Índice: `docs/memory/MEMORY.md`, una línea por memoria.
- Cada memoria es un fichero con frontmatter (`name`, `description`, `metadata.type`: user | feedback | project | reference). Enlaza otras con `[[name]]`.
- Antes de crear una memoria, comprueba si ya existe y, en ese caso, actualízala.

@docs/memory/MEMORY.md
