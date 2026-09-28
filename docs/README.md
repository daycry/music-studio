# Documentación — music-studio

Estudio personal de generación musical con IA, estilo Suno + Sondo (canción → videoclip), que corre en local en una RTX 5070 de 12 GB. Cada canción es un proyecto. **Estado (2026-09-28): documentación reorganizada; el desarrollo empieza de cero en el hito M0.**

## Mapa

| Carpeta | Qué contiene | Empieza por |
|---|---|---|
| [`CONSTITUTION.md`](./CONSTITUTION.md) | **Principios permanentes** (arquitectura fijada/vetada, convenciones, seguridad). La lee la revisión adversarial del plugin | — |
| [`producto/`](./producto/) | Qué se construye y por qué | [`vision.md`](./producto/vision.md) → [`funcionalidades.md`](./producto/funcionalidades.md) → [`ux.md`](./producto/ux.md) |
| [`arquitectura/`](./arquitectura/) | Cómo se construye | [`diagramas.md`](./arquitectura/diagramas.md) · [`sistema.md`](./arquitectura/sistema.md) · [`contrato-engines.md`](./arquitectura/contrato-engines.md) · [`convenciones.md`](./arquitectura/convenciones.md) · [`modelos.md`](./arquitectura/modelos.md) · [`video.md`](./arquitectura/video.md) · [`datos.md`](./arquitectura/datos.md) · [`pipeline-audio.md`](./arquitectura/pipeline-audio.md) · [`entorno.md`](./arquitectura/entorno.md) |
| [`decisiones/`](./decisiones/) | ADR: decisiones cortas, con fecha y motivo | [`README.md`](./decisiones/README.md) |
| [`roadmap/`](./roadmap/) | Hitos. Cada hito es una iniciativa con `spec.md` + `tasks.md`, en el formato del plugin `custom-agents` (`/dev-cycle`) | [`README.md`](./roadmap/README.md) |
| [`calidad/`](./calidad/) | Cómo se decide si un modelo suena bien y estrategia de pruebas | [`evaluacion-escucha.md`](./calidad/evaluacion-escucha.md) · [`pruebas.md`](./calidad/pruebas.md) |
| [`legal/`](./legal/) | Licencias de modelos y herramientas; qué hacer antes de comercializar | [`licencias.md`](./legal/licencias.md) · [`comercializacion.md`](./legal/comercializacion.md) |
| [`memory/`](./memory/) | Memoria persistente del proyecto para las sesiones con Claude | [`MEMORY.md`](./memory/MEMORY.md) |
| [`archive/`](./archive/) | Documentación anterior (julio–septiembre 2026). **Histórica, no vigente** | — |

## Reglas

1. **Fuente de verdad:** lo que está fuera de `archive/`. Si algo contradice al archivo, gana lo vigente.
2. **Toda decisión que cambie algo ya documentado pasa por un ADR** (`decisiones/ADR-XXXX-*.md`) y actualiza el documento afectado.
3. **El estado de las tareas vive solo en el `tasks.md` de su hito.** No se duplica en otros sitios.
4. **Todo vive dentro de esta carpeta**: código, modelos, datos y memoria ([ADR-0005](./decisiones/ADR-0005-todo-en-la-carpeta.md)).
5. **Documentación breve.** Si un documento pasa de ~300 líneas, probablemente mezcla dos temas.
