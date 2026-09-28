# Continuar aquí

> Estado al **2026-09-28**. Este fichero dice dónde se paró y cómo retomar. El estado detallado de cada tarea vive **solo** en el ledger: [`docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md`](docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md).

## Dónde estamos

| | |
|---|---|
| **Hito** | **M0**: entorno, motor por CLI y elección de modelo. Spec `aprobada` y plan `en-progreso`. M1 también está aprobada, pero no empieza hasta cerrar M0 |
| **Progreso** | **3 de 14 tareas**: Fase 1 completada (T-00, T-01) y Fase 2 con 1 de 3 (T-02) |
| **Rama** | `main`, actualizada y subida a `github.com/daycry/music-studio` (público; el código antiguo está en `archive/legacy-main`) |
| **Siguiente tarea** | **T-03**: `packages/engine-contract` + `apps/engines/common` + `engine-mock`. Congela el contrato `/v1` |

### Qué hay hecho

- **T-00 (máquina lista):**
  - la GPU RTX 5070 se ve desde Docker;
  - WSL tiene 24 GB (`.wslconfig`);
  - Node 22, pnpm 9.12, uv y git instalados;
  - filtro de Synology configurado.
- **T-01 (esqueleto del monorepo):**
  - workspace uv sin torch y pnpm;
  - `uv.toml`, `.python-version`, `scripts/env.ps1|sh`, `bootstrap.ps1|sh` e `init_env.py`;
  - `LICENSE` con todos los derechos reservados.
- **T-02 (pesos seguros):**
  - `packages/weights`: lock, SHA-256 con sello, auditor y conversor de pickle sin torch;
  - `scripts/fetch_models.py` y `fetch_tools.py`;
  - **27 GB de modelos ya descargados y verificados** en `models/`: ACE-Step 1.5 turbo/sft/base, LM 0.6B/1.7B, VAE, Qwen3-Embedding, Qwen3-ASR, ForcedAligner, CLAP, Audiobox y beat_this;
  - ffmpeg LGPL en `tools/`.
- **Configuración del plugin** (`/setup`):
  - TDD y subagentes frescos activados;
  - cobertura mínima del 80 %;
  - lentes de seguridad y rendimiento en `auto`;
  - statusline;
  - Kwipu y Graphiti (`shadow`) activados y registrados como MCP locales.

## Cómo retomar

1. **Prepara la GPU.** El Ollama del stack `knowledge-graphs` ocupa de 7 a 9 GB de VRAM cuando tiene un modelo cargado. Desde T-05 hay que descargarlo, sin parar el servicio ni borrar el modelo:
   ```powershell
   wsl -d Ubuntu -e ollama ps                  # qué modelo hay cargado
   wsl -d Ubuntu -e ollama stop mimo:9b-q5     # descargarlo (usa el nombre que salga en ps)
   nvidia-smi --query-gpu=memory.used --format=csv   # debe marcar ≲ 1,6 GB
   ```
   Al terminar el trabajo con GPU: `wsl -d Ubuntu -e ollama run <modelo>`.
2. **Carga el entorno:** `. .\scripts\env.ps1` en PowerShell. Si faltan `.venv` o `node_modules`, ejecuta `.\scripts\bootstrap.ps1`.
3. **Comprueba el estado:**
   ```powershell
   git status; git log --oneline -5
   uv run scripts/fetch_models.py --model ace-step-1.5 --check     # modelos intactos
   uv run pytest -m "not gpu" -q
   ```
4. **Sigue con el ciclo:** `/custom-agents:dev-cycle` sobre `docs/roadmap/2026-09-28-m0-entorno-y-motor`. Las fases 1 y 2 del ciclo ya están hechas (spec y plan), así que se va directo a implementar. La siguiente es **T-03**:
   - rama `m0/t-03-engine-contract`;
   - brief con `task-brief.py`;
   - subagente `implementer` **con TDD**, porque ahora está activo.

## Pendiente conocido

- **Revisión de dos lentes de la Fase 2** (al cerrar T-04). T-02 deja dos puntos que hay que mirar:
  - el auditor rechaza siempre `STACK_GLOBAL` (protocolo 4+);
  - el bundle de ACE-Step se reparte en 4 subdirectorios de `checkpoints/`, pendiente de confirmar contra lo que espera upstream en T-06.
- `pnpm install` no instala nada todavía: `apps/web` aún no tiene dependencias (llegan en M1).
- **Barra de estado:** la ruta del script incluye la versión del plugin (`1.22.0`). Si actualizas el plugin, vuelve a lanzar `/setup` para corregirla.

## Mapa rápido

- Documentación: [`docs/README.md`](docs/README.md) · principios: [`docs/CONSTITUTION.md`](docs/CONSTITUTION.md) · decisiones: [`docs/decisiones/`](docs/decisiones/README.md)
- Contrato de engines: [`docs/arquitectura/contrato-engines.md`](docs/arquitectura/contrato-engines.md) · datos: [`docs/arquitectura/datos.md`](docs/arquitectura/datos.md) · entorno: [`docs/arquitectura/entorno.md`](docs/arquitectura/entorno.md)
- Memoria del proyecto (para Claude): [`docs/memory/MEMORY.md`](docs/memory/MEMORY.md)
