# Documentación — music-studio

Estudio personal de generación musical con IA, estilo Suno + Sondo (canción → videoclip), que corre en local en una RTX 5070 de 12 GB. Cada canción es un proyecto.

La documentación combina arquitectura aprobada e implementación disponible. Los ledgers de [M0](./roadmap/2026-09-28-m0-entorno-y-motor/tasks.md) y [M1](./roadmap/2026-09-28-m1-mvp-estudio/tasks.md) son la única fuente de estados. La generación local por CLI y los componentes web ya tienen implementación; su existencia no acredita la aceptación musical ni la integración completa del producto.

## Implementación y verificaciones técnicas

El [contrato `/v1`](./arquitectura/contrato-engines.md#8-uso-de-la-implementación-python) documenta los modelos Pydantic, el servidor común y el mock sin GPU. El [pipeline de audio](./arquitectura/pipeline-audio.md#2-api-python-disponible) explica las funciones de postproceso y el manifiesto v1.

La [guía del server y los contratos](./desarrollo/server-y-contratos.md) explica el backend técnico, módulos, ciclo de vida, comandos y límites. Conserva contexto histórico de sus primeras verificaciones; consulta las verificaciones vigentes de cada tarea en los ledgers de M0 y M1. Las pruebas de módulos no aceptan el modelo musical ni sustituyen escucha, uso real o E2E del producto.

Para trabajar sin ocupar WSL ni GPU, consulta el [perfil Windows CPU de la web](./calidad/pruebas.md#desarrollar-y-probar-la-web-en-windows-sin-wsl-ni-gpu): herramientas gestionadas, API temporal aislada, Playwright y límites de los datos sintéticos. La [QA CPU de la UI](./roadmap/2026-09-28-m1-mvp-estudio/testing/cpu-ui-2026-11-03.md) conserva evidencia independiente; no acredita el despliegue Docker completo.

La [integración Docker](./calidad/pruebas.md#integración-docker-con-http-sse-y-medios-reales) explica el ámbito privado de T-15, sus siete variables obligatorias y las pruebas con HTTP, SSE, medios y recuperación reales. La [guía de restauración](./desarrollo/server-y-contratos.md#qué-conservar-junto-con-la-copia-sqlite) aclara qué guardar junto a SQLite. Estos procedimientos usan mock CPU; la aceptación de M1 exige ACE-Step real y escucha, según [ADR-0089](./decisiones/ADR-0089-reencauce-tras-codex.md).

Desde la raíz, con el entorno local instalado:

```powershell
. .\scripts\env.ps1
uv run --frozen --all-packages scripts/export_contracts.py --check
uv run --frozen --all-packages scripts/verify_manifest.py packages/contracts/examples/
uv run --frozen --all-packages pytest -m "not gpu" -q
```

Fuentes de estos comandos: [export_contracts.py](../scripts/export_contracts.py), [verify_manifest.py](../scripts/verify_manifest.py) y [configuración de pruebas](../pytest.ini).

## Mapa

| Carpeta | Qué contiene | Empieza por |
|---|---|---|
| [`CONSTITUTION.md`](./CONSTITUTION.md) | **Principios permanentes** (arquitectura fijada/vetada, convenciones, seguridad). La lee la revisión adversarial del plugin | — |
| [`producto/`](./producto/) | Qué se construye y por qué | [`vision.md`](./producto/vision.md) → [`funcionalidades.md`](./producto/funcionalidades.md) → [`ux.md`](./producto/ux.md) |
| [`arquitectura/`](./arquitectura/) | Cómo se construye | [`diagramas.md`](./arquitectura/diagramas.md) · [`sistema.md`](./arquitectura/sistema.md) · [`contrato-engines.md`](./arquitectura/contrato-engines.md) · [`convenciones.md`](./arquitectura/convenciones.md) · [`modelos.md`](./arquitectura/modelos.md) · [`video.md`](./arquitectura/video.md) · [`datos.md`](./arquitectura/datos.md) · [`pipeline-audio.md`](./arquitectura/pipeline-audio.md) · [`entorno.md`](./arquitectura/entorno.md) |
| [`decisiones/`](./decisiones/) | ADR: decisiones cortas, con fecha y motivo | [`README.md`](./decisiones/README.md) |
| [`desarrollo/`](./desarrollo/) | Módulos, contratos y verificación del backend | [`server-y-contratos.md`](./desarrollo/server-y-contratos.md) |
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

Última actualización: 2026-11-05.
