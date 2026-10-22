# `docs/knowledge/journal/` — bitácora de sesión (memoria episódica)

Una entrada por sesión, **generada** por `agent-kits/shared/journal.py` (hook `SessionEnd`; la
última se reinyecta al arrancar/retomar). Cronológica y **no curada**: lo que merezca doctrina
se promueve a `adr/`, `gotchas/` o `lessons/` con el umbral de `knowledge-write.md`. **Excluida de
Confluence** (`docs/knowledge/journal/**`). Nombre: `AAAA-MM-DD-<iniciativa activa | sesion>.md` (sufijo `-2`
si otra sesión del día ya lo usó). **Las entradas se versionan** (memoria del proyecto, como ADR y lecciones);
quien no quiera versionarlas añade `docs/knowledge/journal/*.md` (no este README) a su `.gitignore`.
Este índice lo regenera `journal.py index`; no lo edites.

**Campos de frontmatter de cada entrada** (`agent-kits/shared/journal.py:render`):

| Campo | Valores | Qué significa |
|---|---|---|
| `cierre` | `materializado` · `recuperado_sin_cierre` | Con qué garantía se cerró la sesión: envelope de `SessionEnd` verificado, o recuperada del log de prompts sin cierre observado |
| `fuente` | `hook` · `recover` · `manual` | Quién generó la entrada: `replay` del envelope del hook, `recover` sobre una sesión huérfana, o `--enrich` a mano |
| `reason` | motivo del envelope (`clear`, `resume`, `logout`, `prompt_input_exit`, `other`) o `orphan_recovery` | Motivo de cierre; `orphan_recovery` = nunca hubo envelope |
| `derivados_en` | `replay` | `ficheros_tocados`/`tareas_cambiadas` se calculan con git al materializar (también para huérfanas), nunca en el teardown de `SessionEnd` (CA-01) |
| `materializado_en` | timestamp ISO UTC | Cuándo se escribió la entrada final; la `fecha` es la del cierre (`captured_at`) |

| Fecha | Iniciativa | Resumen | Fuente |
|---|---|---|---|
| [2026-10-12](2026-10-12-m0-entorno-y-motor.md) | m0-entorno-y-motor | Sesión sobre m0-entorno-y-motor | hook |
| [2026-10-11](2026-10-11-m0-entorno-y-motor-2.md) | m0-entorno-y-motor | Sesión sobre m0-entorno-y-motor | hook |
| [2026-10-11](2026-10-11-m0-entorno-y-motor.md) | m0-entorno-y-motor | Sesión sobre m0-entorno-y-motor | hook |
| [2026-10-09](2026-10-05-m0-entorno-y-motor-4.md) | m0-entorno-y-motor | continua con dev-cycle | hook |
| [2026-10-08](2026-10-08-m0-entorno-y-motor-2.md) | m0-entorno-y-motor | Sesión sobre m0-entorno-y-motor | hook |
| [2026-10-08](2026-10-08-m0-entorno-y-motor.md) | m0-entorno-y-motor | Sesión sobre m0-entorno-y-motor | hook |
| [2026-10-07](2026-10-07-m0-entorno-y-motor.md) | m0-entorno-y-motor | Sesión sobre m0-entorno-y-motor | hook |
| [2026-10-06](2026-10-06-m0-entorno-y-motor-3.md) | m0-entorno-y-motor | Sesión sobre m0-entorno-y-motor | hook |
| [2026-10-06](2026-10-06-m0-entorno-y-motor-2.md) | m0-entorno-y-motor | Sesión sobre m0-entorno-y-motor | hook |
| [2026-10-06](2026-10-06-m0-entorno-y-motor.md) | m0-entorno-y-motor | Sesión sobre m0-entorno-y-motor | hook |
| [2026-10-05](2026-10-05-m0-entorno-y-motor-6.md) | m0-entorno-y-motor | continua con dev-cycle de custom-agents | hook |
| [2026-10-05](2026-10-05-m0-entorno-y-motor-5.md) | m0-entorno-y-motor | continua con dev-cycle | hook |
| [2026-10-05](2026-10-05-m0-entorno-y-motor-3.md) | m0-entorno-y-motor | continua con dev-cycle | hook |
| [2026-10-05](2026-10-05-m0-entorno-y-motor-2.md) | m0-entorno-y-motor | Sesión sobre m0-entorno-y-motor | hook |
| [2026-10-05](2026-10-05-m0-entorno-y-motor.md) | m0-entorno-y-motor | Sesión sobre m0-entorno-y-motor | hook |
| [2026-09-28](2026-09-28-m0-entorno-y-motor.md) | m0-entorno-y-motor | /custom-agents:setup | hook |
