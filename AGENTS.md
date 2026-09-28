# AGENTS.md — contexto inicial para agentes de IA

> Contexto base para cualquier agente que trabaje en este repositorio (Claude Code, Codex, Copilot…). `CLAUDE.md` lo importa. **Al retomar el trabajo, lee primero [`CONTINUE-HERE.md`](CONTINUE-HERE.md)**: dice dónde se paró y cómo seguir.

## 1. El proyecto

**music-studio** es un estudio personal de generación musical con IA al estilo Suno + Sondo: letra y estilo → canción → videoclip. Corre **en local**, en una RTX 5070 de 12 GB (Windows 11, Docker Desktop sobre WSL2).

- **Stack:** Next.js (`apps/web`) → FastAPI sin torch (`apps/server`, fuente de verdad en SQLite) → engines GPU en Docker con el contrato `/v1` (`apps/engines/*`).
- **Motor musical:** ACE-Step 1.5.
- **Imagen y vídeo:** ComfyUI headless.
- **Letras:** LLM local.
- **Idiomas:** documentación, UI y commits en **castellano**; identificadores de código, API, BD y JSON en **inglés**.
- **Estado actual:** hito **M0** (entorno, motor por CLI y elección de modelo). El progreso está en el ledger del hito.

## 2. Flujo de trabajo: SIEMPRE con el plugin `custom-agents`

Todo trabajo de producto o de código pasa por el plugin **custom-agents** (comandos `/custom-agents:*`, agentes y skills). **No se implementa «por libre» fuera del plugin**, ni siquiera un cambio pequeño: para eso está su vía rápida.

| Si hay que… | Usa |
|---|---|
| Implementar un hito ya planificado (M0, M1…) | **`/custom-agents:dev-cycle docs/roadmap/<fecha>-<slug>`**. Si la spec está `aprobada` y ya existen `improvement-plan.md` y `tasks.md`, se saltan las fases de evaluar y planificar y se va directo a implementar |
| Hacer un cambio pequeño y bien definido (1–2 frases, pocos ficheros) | Skill **`custom-agents:quick-implement`** (vía rápida de `dev-cycle`: `tasks.md` ligero, revisión de dos lentes y `qa`) |
| Definir una idea nueva o un hito futuro (M2+) | **`/custom-agents:pm-cycle`**, o el agente **`analyst`** si la idea está verde. El agente **`architect`** si hay opciones de diseño que comparar |
| Revisar un diff o una rama | Skill **`custom-agents:adversarial-review`** (lentes A/B, más C de seguridad y D de rendimiento cuando aplican) |
| Un fallo que no se resuelve a la primera | Skill **`custom-agents:debug-root-cause`** |
| Escribir tests primero | Skill **`custom-agents:tdd`**, activa por defecto en este proyecto |
| Auditar la seguridad | Agente **`nemesis`** o skill **`custom-agents:cybersecurity`** |
| Validar o comparar contratos OpenAPI | Skill **`custom-agents:api-contract`** |
| Ver el estado o las métricas | `/custom-agents:roadmap-status` · `/custom-agents:roadmap-metrics` · `/custom-agents:doctor` |
| Cerrar un hito | Ritual de cierre de `dev-cycle`: `changelog-sync`, `/custom-agents:retro` y el agente `documenter` |
| Proponer o curar conocimiento técnico | `documenter` propone y **`knowledge-curator`** aprueba (`docs/knowledge/`) |

**Configuración del plugin** (`.claude/`, versionada; se cambia con `/custom-agents:setup`):
- `dev.json`: **TDD** y **subagentes de contexto fresco** activos, cobertura mínima del **80 %** sobre lo que cambia cada fase, lentes de seguridad y rendimiento en `auto`, guardarraíles activos.
- `rates.json`: tarifa 0 €/h (proyecto personal), con el precio de tokens verificado.
- Jira y Confluence: desactivados.
- `knowledge-services/taxonomy.json`: Kwipu (exportación) y Graphiti (`shadow`), ambos como MCP locales.

Scripts del plugin que se usan a menudo, en `<plugin>/agent-kits/shared/`:
- `ledger-lint.py <tasks.md>` → debe dar `0 incoherencias`;
- `task-brief.py <iniciativa> T-XX` → brief determinista para el subagente;
- `model-tier.py <agente>`.

> **Agentes sin el plugin** (Codex, Copilot…): seguid las mismas reglas a mano. El estado solo en `tasks.md`, cada tarea se cierra ejecutando su **Verificación** y se respeta la constitución. No uséis ledgers paralelos.

## 3. Documentación y fuentes de verdad

- **Mapa:** [`docs/README.md`](docs/README.md).
- **Principios permanentes:** [`docs/CONSTITUTION.md`](docs/CONSTITUTION.md). Cambiarlos exige un ADR, y la revisión adversarial los hace cumplir.
- **Fuente de verdad:** todo `docs/` salvo `docs/archive/`, que es histórico y no vigente.
- **Antes de tocar contratos o datos:** [`contrato-engines.md`](docs/arquitectura/contrato-engines.md), [`datos.md`](docs/arquitectura/datos.md) y [`convenciones.md`](docs/arquitectura/convenciones.md).
- **Estado de las tareas:** **solo** en el `tasks.md` del hito (`docs/roadmap/<fecha>-<slug>/`).
  - Estados válidos: `borrador · en-progreso · en-revision · completado · cancelado`.
  - Cada tarea se cierra ejecutando su **Verificación** y pegando la salida.
  - El orquestador es quien actualiza el ledger; los subagentes no lo tocan.
- **Decisiones:** toda decisión que cambie algo documentado va a un ADR nuevo en [`docs/decisiones/`](docs/decisiones/README.md), y se actualiza el documento afectado.

## 4. Reglas clave

1. **Local por defecto en todo** (música, letras, imagen, vídeo). APIs y suscripciones solo como alternativa opcional desactivada de fábrica (ADR-0014). **La música es siempre local.**
2. **La canción es el proyecto** (ADR-0013): takes, letra, portada, vídeo y exportaciones cuelgan de `song`. Nunca se sobrescribe un take: cada edición crea un take hijo con linaje.
3. **Todo dentro de esta carpeta**: código, pesos (`models/`), herramientas (`tools/`), datos (`data/`), evaluaciones (`eval/`), cachés (`.cache/`) y memoria (`docs/memory/`). Nada en otras unidades ni en `%USERPROFILE%`.
4. **Nunca instales nada en el Python de la máquina.** Usa el intérprete gestionado por uv y `.venv` a través de `scripts/env.ps1` / `env.sh`.
5. **Pesos seguros** (ADR-0006):
   - en runtime solo `safetensors`, `gguf` u `onnx`;
   - **nunca** `torch.load` ni `pickle.load`: los pickle oficiales se convierten con el auditor de `packages/weights`;
   - todo fijado por revisión y verificado por SHA-256 contra `models/models.lock.json`;
   - el `trust_remote_code` va fijado por hash.
6. **Engines sin estado:** devuelven salida cruda en `data/tmp/<job_id>/`. El post-proceso, los manifiestos y el render los hace el server, que es el único que escribe en la BD (ADR-0017).
7. **Un modelo en VRAM a la vez** (ADR-0007):
   - el modelo corre en un proceso hijo y `unload` termina ese proceso;
   - BF16 por defecto;
   - el tope se calcula a partir de la VRAM **libre** menos un margen;
   - en WSL2, si se desborda, la GPU tira de RAM sin avisar;
   - la 5070 cae en el tier 4 de ACE-Step: los modos se fuerzan de forma explícita.
8. **La GPU se comparte con el Ollama del stack `knowledge-graphs`**, cuyo modelo cargado ocupa de 7 a 9 GB. Antes de cualquier trabajo con GPU:
   - mira qué hay cargado: `wsl -d Ubuntu -e ollama ps`;
   - descárgalo: `wsl -d Ubuntu -e ollama stop <modelo>`, hoy `mimo:9b-q5`;
   - comprueba que `nvidia-smi` marca ≲ 1,6 GB.

   Al terminar, vuélvelo a cargar con `wsl -d Ubuntu -e ollama run <modelo>`. **No pares el servicio ni borres modelos** (ADR-0022).
9. **Licencias:** ningún modelo ni herramienta entra en el código sin su fila en [`docs/legal/licencias.md`](docs/legal/licencias.md). Los modelos no comerciales solo se usan para comparar, nunca como motor por defecto.
10. **Repositorio público** (`github.com/daycry/music-studio`, todos los derechos reservados; ADR-0021):
    - nunca se commitea nada de `.env`, `data/`, `models/` (salvo los locks), ni rutas personales;
    - una rama por tarea (`m0/t-03-…`), con merge fast-forward a `main` al cerrarla, sin PR;
    - commits en Conventional Commits en castellano, terminados en `[M0/T-XX]`;
    - git se autentica con `gh`.
11. **UX derivada de Suno y Sondo, sin copiar su identidad visual** (ADR-0010).

## 5. Comandos de desarrollo

Carga siempre el entorno antes de usar `uv` o `python`:

```powershell
. .\scripts\env.ps1     # PowerShell
```
```bash
source scripts/env.sh   # bash / WSL
```

| Qué | Comando |
|---|---|
| Reconstruir desde cero (intérprete, `.venv`, `node_modules`) | `.\scripts\bootstrap.ps1` (o `scripts/bootstrap.sh`) |
| Crear o completar `.env` (genera `STUDIO_ENGINE_TOKEN` una sola vez) | `uv run scripts/init_env.py` |
| Dependencias Python según los locks | `uv sync --frozen` · añadir: `uv add --package <miembro> <paquete>` |
| Descargar o verificar modelos y herramientas | `uv run scripts/fetch_models.py --model <id> [--check]` · `uv run scripts/fetch_tools.py [--check]` |
| Tests Python sin GPU | `uv run pytest -m "not gpu"` |
| Tests de un engine con GPU (dentro de su contenedor) | `docker compose run --rm <engine> uv run pytest -m gpu` |
| Lint y formato Python | `uv run ruff check .` · `uv run ruff format .` |
| Hooks de pre-commit | `uv run pre-commit run --all-files` |
| Web (desde M1) | `pnpm install --frozen-lockfile` · `pnpm lint` · `pnpm test` · `pnpm gen` |

## 6. Memoria del proyecto

La memoria persistente vive **en el repositorio**, en [`docs/memory/`](docs/memory/MEMORY.md), **nunca** en directorios de usuario del agente.
- Índice: `docs/memory/MEMORY.md`, una línea por memoria.
- Cada memoria es un fichero con frontmatter (`name`, `description`, `metadata.type`: user | feedback | project | reference) y enlaza otras con `[[name]]`.
- Antes de crear una memoria, comprueba si ya existe y, en ese caso, actualízala.
