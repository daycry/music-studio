# Continuar aquí

> Reanudación actualizada el **2026-10-05**. El estado detallado vive **solo** en el [ledger de M0](docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md).

## Dónde estamos

M0 sigue abierto. La Fase 2 está completada técnicamente: contrato /v1, engine común y mock (T-03), audio-post y manifiesto (T-04). La spec está aprobada y el plan existe; dev-cycle retoma implementación sin evaluar ni planificar de nuevo. M1 espera al cierre de M0.

- Revisión adversarial: tercer intento A+B+D sin gaps pendientes; tablas en el ledger.
- QA sin UI por diseño: **125 tests sin GPU** verdes, ruff global y formato de los 23 Python cambiados verdes. Cobertura del diff: **93,62 %**, mínimo 80 %; media por fichero con exclusión declarada de conftest.py sin datos.
- [Informe de QA](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/report.md) y sus evidencias. No se han declarado pruebas E2E ni GPU reales.
- Rama actual: **m0/t-03-engine-contract**, con cambios **sin commit, fast-forward ni publicación**. .git es de solo lectura en este perfil. Antes de continuar ramas de producto, hay que integrar por tarea en un entorno con escritura Git, preservando el árbol y los journals ajenos.

La siguiente tarea del ledger es **T-05: imagen engine-acestep**. Está en borrador; todavía no existe Dockerfile ni imagen verificable. Su brief determinista está preparado en .cache/dev-cycle/T-05-brief.md (se puede regenerar con task-brief.py).

## Cómo retomar

1. Carga el entorno: . ./scripts/env.ps1. Usa uv y el Python gestionado dentro de la carpeta; nunca instales en el Python de la máquina.
2. Lee el ledger y comprueba git status y git log --oneline -5. Conserva los cambios existentes; no añadas todos los ficheros indiscriminadamente. La integración debe respetar ramas y commits por tarea conforme [convenciones](docs/arquitectura/convenciones.md).
3. Confirma acceso real a Docker y WSL. En esta sesión, docker version devolvió acceso denegado al pipe dockerDesktopLinuxEngine y wsl -d Ubuntu -e ollama ps devolvió Wsl/Service/E_ACCESSDENIED. No se ha hecho trabajo GPU ni modificado Ollama.
4. Antes de T-05 con GPU, descarga **solo el modelo** que muestre Ollama, sin parar el servicio ni borrarlo:

       wsl -d Ubuntu -e ollama ps
       wsl -d Ubuntu -e ollama stop mimo:9b-q5  # usa el nombre que indique ps
       nvidia-smi --query-gpu=memory.used --format=csv  # ≲ 1,6 GB

   Al terminar, recarga ese modelo: `wsl -d Ubuntu -e ollama run <modelo>` ([ADR-0022](docs/decisiones/ADR-0022-memoria-tecnica-kwipu-graphiti.md)).
5. Retoma el ciclo con el brief T-05, subagente fresco y TDD según .claude/dev.json:

       /custom-agents:dev-cycle docs/roadmap/2026-09-28-m0-entorno-y-motor

   Construye y ejecuta **todas las verificaciones Docker/GPU de T-05**. Una simulación no acredita la imagen ni sm_120.

## Verificación local disponible

    . ./scripts/env.ps1
    uv run --frozen --all-packages pytest -m "not gpu" -q
    uv run --frozen scripts/export_contracts.py --check
    uv run --frozen scripts/verify_manifest.py packages/contracts/examples/
    uv run --frozen ruff check .

Pre-commit completo quedó sin ejecutar por WinError 5 al crear su entorno con permisos 0700. El lint directo y el formato del alcance pasaron. El formato global señala 14 ficheros históricos fuera de alcance; no se modificaron. El intérprete Python 3.11 real se verificará en el contenedor; ahora se ejecutó 3.12 y se comprobó la gramática AST 3.11.

## Pendientes conocidos

- T-02: STACK_GLOBAL se rechaza siempre de forma fail-closed; la revisión confirmó ese comportamiento.
- T-06: comprobar el layout de checkpoints contra la carga real de ACE-Step y parchear la lectura segura de silence_latent. Mock y fixtures no acreditan esa integración.
- T-07: scripts/generate.py y la primera canción por CLI siguen pendientes, junto con la letra propia B-02 y la escucha del propietario.
- No cerrar M0 ni iniciar M1 con estos resultados: faltan motor real, mediciones, capacidades, batería y escucha. El ritual de changelog/retro/cierre corresponde al hito completo.

## Mapa rápido

- [Documentación](docs/README.md) · [constitución](docs/CONSTITUTION.md) · [decisiones](docs/decisiones/README.md).
- [Contrato de engines](docs/arquitectura/contrato-engines.md) · [pipeline de audio](docs/arquitectura/pipeline-audio.md) · [datos](docs/arquitectura/datos.md) · [entorno](docs/arquitectura/entorno.md).
- [Memoria del proyecto](docs/memory/MEMORY.md), dentro del repositorio.
