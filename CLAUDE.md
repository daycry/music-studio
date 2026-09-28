# music-studio

El contexto del proyecto, las reglas, el flujo de trabajo y los comandos están en **`AGENTS.md`**, que se importa aquí. Esa es la fuente única: no dupliques su contenido en este fichero.

@AGENTS.md

## Específico de Claude Code

- **Usa siempre el plugin `custom-agents`.** Invoca sus comandos (`/custom-agents:dev-cycle`, `/custom-agents:pm-cycle`…), sus agentes por nombre (`implementer`, `reviewer`, `qa`…) y sus skills (`quick-implement`, `adversarial-review`, `tdd`…). Consulta la tabla de `AGENTS.md` §2.
- **Memoria:** usa `docs/memory/` y nunca `~/.claude/projects/.../memory/`. El índice se carga aquí:

@docs/memory/MEMORY.md
