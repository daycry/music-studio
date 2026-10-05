# Informe de QA — M0 / T-05: imagen engine-acestep

| | |
|---|---|
| **Fecha** | 2026-10-05 |
| **Estado** | Verificaciones de T-05 satisfechas; QA sin UI. Sin veredicto E2E. M0 sigue abierto. |
| **Alcance** | Imagen, entorno, dependencias y arranque; no adapter funcional, HTTP ni generación (T-06). |
| **URL auditada** | No aplica: no se ejecutó UI, Playwright ni tráfico contra hosts. |
| **Plan y ledger** | [Plan](../../improvement-plan.md) · [Tareas](../../tasks.md) · [Spec](../../spec.md) |

## Veredicto y resumen

ℹ️ Sin UI por diseño (`test-plan: n/a (sin UI)`): `ledger-lint` exit 0, 0 incoherencias y 9 avisos; `coverage-check` exit 0 acepta la declaración y **no ejecuta la puerta de cobertura E2E**.

`qa-gate.py` no ejecutado: no hay escenarios E2E ni `results.json` de Playwright. No se ha fabricado un JSON E2E ni declarado un verde de ese gate. Capturas y trazas de navegador no aplican.

Las cuatro verificaciones canónicas de T-05 tienen evidencia real: build, 4 tests CPU en contenedor, CUDA/sm_120 con matmul BF16 y comprobación FFmpeg. La suite CPU adicional del workspace pasa **125/125** (exit 0). `uv pip check` permanece **fallido, exit 1**, con una incompatibilidad conocida y rebatida para backend `pt`; no se presenta como consistencia completa de dependencias.

Este informe no modifica el ledger, no cierra M0 y no hace handoff a `documenter`. La decisión de integración/cierre de T-05 corresponde al orquestador.

## Puertas deterministas

| Comprobación | Resultado | Evidencia |
|---|---|---|
| `ledger-lint.py tasks.md` | Exit 0: 0 incoherencias, 9 avisos de Changelog para T-05…T-13 | [Salida](raw/ledger-lint.log) |
| `coverage-check.py tasks.md test-plan.md spec.md` | Exit 0: declaración sin UI; cobertura E2E no ejecutada | [Salida](raw/coverage-check.log) |
| `git diff --check` | Exit 0 | [Recibo](raw/diff-check.log) |
| `ruff check apps/engines/acestep/tests/test_environment.py` | Exit 0: All checks passed | [Salida](raw/ruff-check.log) |
| Gate unitario oficial, `--changed-only --base main --min 80` | Exit 0; ningún fichero de Python de producción medible en el diff. No hay porcentaje aplicable ni 80 % acreditado | [JSON](raw/coverage-gate.json) · [Salida](raw/coverage-gate.log) |

### Cobertura declarada de escenarios

Salida JSON completa de `coverage-check`:

```json
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": "el diff contra la base «merge-base main…HEAD (6b371e9f)» no aporta ningún fichero: solo se han mirado los cambios sin comitear"}
```

La lista `eximidos` incluye las 14 tareas del ledger; `eximidos_exigidos: false` indica que su cobertura no era exigida por esta puerta (la spec no aporta criterios rastreables `[GWT]`). Sus evidencias siguen siendo las verificaciones del ledger. No hay aviso de marcador no canónico.

**Limitación de rutas de interfaz:** la búsqueda no ha inspeccionado un diff de commits propios contra `main`; solo el alcance declarado y los cambios sin comitear. `rutas_ui: []` no acredita una inspección de todo el historial de la iniciativa.

### Gate de cobertura Python

Salida JSON del gate oficial:

```json
{
  "ok": true,
  "exit": 0,
  "stack": "pytest",
  "detalle": {
    "stack": "pytest",
    "informe": "docs\\roadmap\\2026-09-28-m0-entorno-y-motor\\testing\\t05\\raw\\coverage-run\\coverage.json",
    "global": 25.51,
    "modo": "changed-only",
    "base": "main",
    "ficheros": {}
  },
  "avisos": [
    "sin ficheros de código en el diff: nada que evaluar"
  ]
}
```

Pirámide medida: **E2E no aplica; cobertura Python del diff no aplica** (sin código de producción Python cambiado). El 25,51 % global procede de `--cov` sobre todo el árbol local y no es la métrica del cambio. El gate de Python no mide `Dockerfile`, `entrypoint.sh`, Compose ni la lógica upstream de ACE-Step. Las aserciones del nuevo test y las pruebas reales del contenedor aportan evidencia funcional de esas piezas, sin inventar cobertura de shell.

Para respetar el directorio de escritura de QA, [el driver](raw/coverage-run/gate-driver.txt) importa el script oficial y reubica únicamente `COV_FILE['pytest']` a [datos completos](raw/coverage-data.json). No modifica selección, cálculo, umbral ni veredicto. [El runner](raw/coverage-run/runner.txt) usa el intérprete gestionado del proyecto, pytest/pytest-cov existentes, `-m "not gpu"` y el directorio raíz. No se instalaron paquetes. Los textos de evidencia se guardan en UTF-8 con rutas del workspace sanitizadas.

## Resultados reales de T-05

| Verificación / criterio | Resultado | Evidencia |
|---|---|---|
| Build exacto de `engine-acestep` | Exit 0, imagen construida; CUDA 12.8.1 fijada por digest, Python 3.11.14 y upstream por commit | [Build](raw/build-fixed-cache.log) · [Recibos](raw/receipts.json) |
| Pytest exacto dentro del contenedor | Exit 0, **4 passed in 7.01s**; entorno real, versiones, imports, usuario/mounts y log SDPA | [Pytest](raw/pytest-final.log) |
| `sm_120` y matmul CUDA BF16 de 64×64 | Exit 0, **262144.0** | [BF16](raw/bf16-final.log) |
| FFmpeg, ausencia `enable-gpl` y `enable-nonfree` | Stdout **0**, exit **1 esperado** de `grep -c` sin coincidencias; tests acreditan LGPL shared, lame/soxr/opus y torchcodec | [FFmpeg](raw/ffmpeg-final.log) |
| Importación CPU `acestep.handler`, CUDA oculta | Exit 0; sin modelos cargados. Matplotlib usa caché temporal y bitsandbytes ausente usa AdamW estándar | [Importación](raw/handler-import-cpu.log) |
| `uv pip check` del entorno de ACE-Step | **Exit 1**, 152 paquetes, 1 incompatibilidad: nano-vllm requiere flash-attn no instalado | [Pip check](raw/pip-check-combined.log) |
| Suite CPU del workspace con cobertura | Exit 0, **125 passed, 1 warning in 19.62s** | [Suite final](raw/pytest-coverage.log) |

La excepción GPU fue autorizada expresamente por el propietario («autorizo esa prueba»), exclusivamente para la matmul BF16 con baseline de 2.950 MiB; no cubre modelos ni benchmarks. Ollama estaba vacío antes: no hubo modelo que descargar o restaurar. QA reutiliza el recibo ejecutado por el orquestador, sin repetir Docker ni GPU.

El fallo de `pip check` es real. La revisión A/B/C intento 1 del [ledger](../../tasks.md) descartó que la ausencia de flash-attn impida el backend `pt`: el upstream fijado usa `_load_pytorch_model` en `acestep/llm_inference.py:706–707` y reserva la importación de nano-vllm a la rama `vllm` (línea 734). **T-06 debe forzar `pt`**, porque el argumento upstream por defecto es `vllm`. Esta revisión no demuestra carga ni generación musical.

## Instrumentación y advertencias

La primera ejecución de cobertura desde `raw/coverage-run` obtuvo **123 passed, 2 failed**, exit 1. Ambos fallos fueron `FileNotFoundError` de rutas relativas a `packages/contracts/engine-v1.json` y `scripts/export_contracts.py`: el runner había usado un cwd distinto de la raíz. Se conserva [la salida fallida](raw/pytest-coverage-cwd-failed.log) y [su gate](raw/coverage-gate-cwd-failed.log). El gate exit 0 de aquel intento no se usó para acreditar pruebas: el gate de cobertura no valida el exit de pytest.

Se corrigió únicamente el cwd del runner de QA y se repitió la medición, con 125 tests pasando. No se repitió otra suite tras ese resultado. La ejecución final tiene una advertencia `Unknown config option: cache_dir`: se desactivó `cacheprovider` para evitar el error ACL de su caché temporal en este sandbox. No implica fallo del producto.

Los fixtures de tests existentes crean sus temporales bajo `.cache/` del proyecto; el runner no cambia esos fixtures. No se modificaron fuentes, contratos, ledger ni evidencias anteriores de T-03/T-04.

## Checklist pendiente y trazabilidad

No existen bloques `M-xx`, `API-xx` ni `A11Y-xx`: el plan declara ausencia de UI.

- [ ] **T-06:** factoría HTTP, adapter funcional, backend `pt` forzado, carga segura, generación, eventos y cancelación reales.
- [ ] **M0:** primera canción, benchmarks, capacidades, evaluación y escucha del propietario; se validarán en sus tareas correspondientes.
- [ ] **Documento PDF:** generar cuando existan dependencias `to-pdf` permitidas dentro del workspace. Este informe Markdown está disponible.

| Tarea | Evidencia de este informe | Límite |
|---|---|---|
| T-05 | Cuatro verificaciones canónicas reales + revisión A/B/C + lint y suite CPU | Pip check completo sigue fallido; integración Git corresponde al orquestador |
| T-06 | No ejecutada | HTTP, modelos y generación no acreditados |
| T-07…T-13 | No ejecutadas | M0 no cerrado |

## Artefactos y PDF

[Recibos del entorno](raw/receipts.json), [comprobaciones QA](raw/qa-checks.json), logs enlazados y cobertura cruda local. E2E, screenshots y trazas de Playwright no aplican.

**PDF no generado.** Se revisó la skill `custom-agents:to-pdf`; Node v22.23.2 existe, pero faltan `markdown-it`, `mammoth` y `puppeteer` en los directorios comprobados. La tarea prohíbe instalar y escribir fuera del workspace; no se descargó Chromium. [Comprobación de requisitos](raw/pdf-prerequisites.log). El informe es solo local: no se publica en Confluence.
