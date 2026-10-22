---
agente: qa
tier: medium
fecha: 2026-10-10
estado: verificado-linux
alcance: componente-tecnico-test-only
tokens: null
coste: null
---

# QA actual Linux: portabilidad de audio

Verificación independiente del checkout posterior al CAS ROOT 22:01:07 UTC: **180 PASS / 5 SKIP / 0 FAIL / 0 ERROR**, 185 casos. Pytest/uv exit 0; contenedor exit 0, PID 0. El resultado cubre exclusivamente `packages/audio-post/tests` en Linux. M1 y T-05 siguen abiertos; Windows mantiene 169 PASS / 9 SKIP / 7 FAIL / 16 ERROR y no se repitió.

La preparación inicial omitió `engine_mock`, requerido transitivamente por `test_generate_preparation`: 156 PASS / 5 SKIP / 24 FAIL (ModuleNotFoundError), conservados en [JUnit intento de infraestructura 1](../../../../../.cache/dev-cycle/m1/audio-post-portability-20261010/qa-linux/attempt1/results/suite.xml). Se completó el snapshot privado con fuentes actuales common/mock y locks; ningún test ni runtime se editó. El intento 2 es la evidencia vigente.

| Módulo completo | Líneas cubiertas / total | Cobertura | Gate oficial >=80 % | Exclusiones |
|---|---:|---:|---:|---:|
| `manifest.py` | 215 / 255 | 84.31 % | exit 0 | 0 |
| `pipeline.py` | 128 / 133 | 96.24 % | exit 0 | 0 |

Medición oficial por cada módulo completo, sin omit ni exclusiones. Gate de runtime cambiado n/a: el CAS solo integra cuatro ficheros de tests. No se usó porcentaje global para sustituir los dos gates.

Snapshot actual: 237 fuentes/recursos/locks, 19 imports del snapshot privados verificados por SHA; delta antes/después: 0. La venv de dependencias procede de la imagen fijada y no se sincronizó ni instaló nada. FFmpeg real SHA `953632dece404bb1461a4a2285f0191a6105d72c81f9da577eb54326a7fad49a`, procedencia binario instalado desde imagen/receta sellada, copia privada verificada; sin alias ni reparación de `tools` canónico. Las cuatro fuentes coinciden exactamente con integration-receipt.

Contenedor `037cc6e250bf92d24884d6fcc89587a7882849560161649c72875d3f16b87633`, imagen `sha256:7c65be72cf35ef0989407f280405f49c41662d01caa32a4c75bf4eec4d55ee25`. UID/GID 10001, cap-drop ALL, NoNewPrivs 1, red none, sin GPU; bind de fuentes privadas readonly, cache uv propia escribible, temporales Linux tmpfs `/studio/.cache` y `/tmp`, results modo1777. Export TAR antes de liberar el contenedor; copia actual persistida en QA. Estado final detenido, PID0. Sin control de WSL, Ollama, modelos, bindings o servicios ajenos.

Skips legítimos de plataforma:

- `test_real_link_rejected[junction-root]`: Windows directory junctions only
- `test_real_link_rejected[junction-ancestor]`: Windows directory junctions only
- `test_real_link_rejected[junction-source]`: Windows directory junctions only
- `test_real_link_rejected[junction-destination]`: Windows directory junctions only
- `test_windows_stat_ctime_domains_preserve_each_api_identity`: Windows stat API domains

Evidencias: [JUnit](../../../../../.cache/dev-cycle/m1/audio-post-portability-20261010/qa-linux/results/suite.xml), [terminal pytest/uv](../../../../../.cache/dev-cycle/m1/audio-post-portability-20261010/qa-linux/results/pytest-terminal.json), [coverage JSON](../../../../../.cache/dev-cycle/m1/audio-post-portability-20261010/qa-linux/results/coverage.json), [gate manifest](../../../../../.cache/dev-cycle/m1/audio-post-portability-20261010/qa-linux/results/manifest-gate.json), [gate pipeline](../../../../../.cache/dev-cycle/m1/audio-post-portability-20261010/qa-linux/results/pipeline-gate.json), [comandos Docker](../../../../../.cache/dev-cycle/m1/audio-post-portability-20261010/qa-linux/create.terminal.json), [estado final](../../../../../.cache/dev-cycle/m1/audio-post-portability-20261010/qa-linux/inspect-stopped.log), [entorno runtime](../../../../../.cache/dev-cycle/m1/audio-post-portability-20261010/qa-linux/results/environment.json), [imports](../../../../../.cache/dev-cycle/m1/audio-post-portability-20261010/qa-linux/imports-verified.json), [fuentes antes](../../../../../.cache/dev-cycle/m1/audio-post-portability-20261010/qa-linux/source-before.json), [fuentes después/delta](../../../../../.cache/dev-cycle/m1/audio-post-portability-20261010/qa-linux/source-after.json), [Ruff](../../../../../.cache/dev-cycle/m1/audio-post-portability-20261010/qa-linux/ruff-terminal.json), [resumen determinista](../../../../../.cache/dev-cycle/m1/audio-post-portability-20261010/qa-linux/summary.json).

Ruff check y format --check pasan para los cuatro tests actuales en `.venv` gestionada con `scripts/env.ps1`, sin instalaciones. QA Playwright/qa-gate n/a por alcance técnico sin UI; no se fabricó resultado E2E. PDF omitido: no se adquirieron dependencias de render. TDD preservado: no hay edición de producto; RED/GREEN anteriores quedan como historial del implementador, esta ejecución es QA actual independiente.

Pendientes fuera de alcance: corrección y QA nativo Windows, E2E ext4 persistente, generación/escucha GPU, pruebas manuales del plan y cierre formal T-05/M1. No se actualizan ledger, checkpoint, Git ni estados; aceptación del componente reservada a ROOT.
