# QA independiente de T-14 — comparación shift

2026-10-05. Alcance: parámetro opcional `shift`, descriptor, adaptador y CLI; preparación de la comparación privada. **CPU conforme; GPU conforme**, sin veredicto musical. El orquestador actualiza el estado técnico de T-14; M0 permanece abierto. Calidad y ganador pendientes del propietario. No se modifica el ledger desde este agente.

ℹ️ sin UI por diseño (`test-plan: n/a (sin UI)`). `coverage-check.py` acepta la declaración, exit 0: **la puerta de cobertura E2E no se ejecutó**. No se ejecutaron Playwright ni `qa-gate.py`, no hay porcentaje ni resultados E2E fabricados. No hubo instalación ni acceso a hosts públicos.

## Ejecución independiente CPU

El [runner retenido](raw/qa-cpu-runner.py) ejecutó pytest oficial una vez desde el entorno gestionado del proyecto, con CUDA oculto (`CUDA_VISIBLE_DEVICES=""`), cobertura oficial y temporales dentro de `.cache/`. Paths explícitos: `packages/weights/tests`, `packages/engine-contract/tests`, `packages/audio-post/tests`, `apps/engines/common/tests`, `apps/engines/mock/tests`, `tests`, `apps/engines/acestep/tests`; `-m "not gpu" -q --tb=short --cov=. --cov-report=json`. [Comando sanitizado](raw/qa-cpu-command.json).

**282 passed, 5 skipped, 1 deselected, 5 warnings in 25.80s; exit 0.** [Log completo](raw/qa-cpu-tests.log). Los cinco avisos son deprecaciones Starlette/TestClient; los skips son escenarios no disponibles en este entorno y no se presentan como aprobados. La prueba GPU quedó excluida. El recibo JSON real contiene 169 archivos, timestamp `2026-10-05T19:38:38.816590`; no se utilizó un informe vacío o antiguo. [Cobertura oficial](raw/qa-coverage.json).

Gate ejecutado con `--changed-only --base main --min 80 --json --runner "<workspace>/.venv/Scripts/python.exe <workspace>/docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t14/raw/qa-cpu-runner.py"`, usando barras `/` en el comando real. **Exit 0; media por archivo 94,57 %**, mínimo 80 %. La cobertura global de todo lo observado es 27,70 % y no es la métrica del gate de este cambio.

| Producción cambiada | Statements cubiertos/total | Cobertura |
|---|---:|---:|
| `apps/engines/acestep/adapter.py` | 155/173 | 89,60 % |
| `apps/engines/acestep/descriptor.py` | 30/30 | 100,00 % |
| `scripts/generate.py` | 319/339 | 94,10 % |

Salida íntegra del [gate](raw/qa-coverage-gate.json):

```json
{
  "ok": true,
  "exit": 0,
  "stack": "pytest",
  "detalle": {
    "stack": "pytest",
    "informe": "coverage.json",
    "global": 27.7,
    "modo": "changed-only",
    "base": "main",
    "ficheros": {
      "apps/engines/acestep/adapter.py": 89.6,
      "apps/engines/acestep/descriptor.py": 100.0,
      "scripts/generate.py": 94.1
    },
    "porcentaje": 94.57,
    "minimo": 80.0
  },
  "avisos": [
    "sin datos de cobertura para: docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t14/raw/qa-cpu-runner.py (excluidos de la media)"
  ]
}
```

Única exclusión automática de la media: el runner de QA, que ejecuta fuera de la instrumentación y no es producto. Se declara explícitamente; ningún archivo de producción del cambio fue excluido. No se altera entrada ni umbral para obtener verde.

## Puertas y trazabilidad

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Ruff global | All checks passed | [Log](raw/qa-ruff.log) |
| Formato cinco archivos de producto/tests y runner | 6 files already formatted | [Log](raw/qa-format.log) |
| Exportación contratos `--check` | engine-v1.json up to date | [Log](raw/qa-contracts.log) |
| Manifiestos anteriores `data/cli/` | all valid (2 manifests) | [Log](raw/qa-cli-manifests.log) |
| Ledger | 0 incoherencias, 7 avisos Changelog T-08–T-14 | [Log](raw/qa-ledger.log) |
| Cobertura criterios/E2E | Excepción canónica sin UI; no puerta ejecutada | [Log y JSON](raw/qa-plan-coverage.log) |
| Revisión A+B, intento 2 | 0 Critical / 0 Important / 0 Minor | [Revisión](review-attempt2.md) |
| Imagen final, recibo del orquestador | 75 passed CPU, exit 0; no GPU | [Recibo](image-final-cpu-receipt.json) |

El formato del runner recién creado originó un panic de Ruff por el BOM/CRLF. Se normalizó únicamente ese artefacto de QA a UTF-8 sin BOM/LF y la comprobación de seis archivos pasó; no se cambió producto ni se repitió la suite.

`coverage-check` lista `eximidos` T-00, T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10, T-11, T-12, T-13, T-14; `eximidos_exigidos=false`: sin criterios rastreables en la spec, la puerta solo exigiría los `[GWT]`. `rutas_ui=[]`, sin marcador no canónico. **Inspección del diff degradada:** la base merge-base main…HEAD (cd9b79d6) no aporta cambios propios; el script miró cambios sin comitear y alcance declarado. Esto no acredita haber inspeccionado un diff histórico completo.

T-14 criterio de parámetro: validación de finitud/tipo/rango, enteros enormes, compatibilidad de omisión, descriptor, propagación y manifiesto cubiertos por tests y revisión. [RED/GREEN inicial](cpu-implementation-report.md) y [fix1](fix1-report.md) aportan el TDD previo; no se inventa RED desde QA. Los criterios de seis audios, igualación, códigos privados, eventos y descarga GPU se acreditan técnicamente mediante el recibo del orquestador y los validadores siguientes. Este agente no leyó letra, prompts, mapas privados, `.env` ni contenido de los manifiestos; solo ejecutó su validador. La página y los reproductores corresponden a la comprobación del orquestador.

## Generación GPU y manifiestos finales

**GPU conforme.** El [recibo público numérico](generation-receipt.json) declara `technical_status=passed`: seis tomas nuevas de 90 s, tres semillas 1/2/3 por shift 1/3, autoría `own`, hashes de entradas/configuración, mismas palabras y caption, BPM 94, español, BF16, Turbo/LM0.6B. Dos grupos terminaron con exit 0; ambos partieron idle/loaded:null y Ollama vacío, con la imagen final ya probada en CPU. `unload_confirmed=true` en ambos: descarga entre grupos y al finalizar. El recibo no acredita una audición del agente.

QA comprobó la coherencia numérica del recibo: seis telemetrías de 90 s, todas `spilled=false`, pico inferior al cap en cada grupo, cero regeneraciones GPU y ganador/calidad pendientes. [Comprobación independiente](raw/qa-gpu-receipt-check.json). Pico registrado **7.889,16 MiB**, caps **9.057,69 y 10.052,19 MiB**. La muestra WSL comprende 205 mediciones, pico de RAM utilizada sin disponible 4.695,57 MiB y **pico de swap 0,4375 MiB**; no se declara swap cero.

Tiempo de pared total **512,77 s**, incluido carga, post-proceso y recuperación de empaquetado. Los `run_s` compartidos por grupo son 203,80 y 177,54 s, con cargas 149,98 y 124,58 s: **no se suman por toma ni se calcula RTF** a partir de esas cifras; el recibo deja `rtf=null`.

La primera fase de empaquetado encontró una semilla nullable incompatible con el manifiesto derivado, que exige entero. Se corrigió únicamente ese derivado lineal no estocástico usando sentinel `seed=0`. El recibo registra **0 tomas GPU regeneradas**, sin rerender GPU; el tiempo total incluye la recuperación. La igualación por ganancia lineal apunta a −16,47 LUFS, sin compresor; la referencia original permanece intacta y solo tiene ganancia de reproducción −3,28 dB. La referencia es objetivo artístico, no condicionamiento enviado al engine ni control causal entre motores.

Validación final independiente, sin leer el contenido privado:

| Comando | Resultado | Evidencia |
|---|---|---|
| `scripts/verify_manifest.py data/cli/` | all valid (8 manifests) | [Log](raw/qa-cli-final-manifests.log) |
| `scripts/verify_manifest.py data/eval/libre-shift/01M46K3MT0JNZB0DYC0F4DZADQ` | all valid (6 manifests) | [Log](raw/qa-listening-manifests.log) |

Son ocho manifiestos CLI: dos anteriores y seis nuevos; seis derivados de escucha. QA no repitió CPU, no generó audio ni cargó GPU para esta ampliación.

## Pendientes y límites

- [x] Recibo público de seis generaciones incorporado y manifiestos originales/derivados validados; QA no generó ni cargó modelos.
- [ ] Escucha del propietario: ritmo, afinación, carácter de voz y preferencia en la hoja privada con volumen comparable. **Calidad no aprobada y ganador pendiente**; no se infiere con tests CPU ni se genera canción completa por suposición.
- [ ] PDF pendiente: herramientas no instaladas; no se instala ni escribe fuera del proyecto en esta auditoría.

No hay bloques M-xx porque no hay test-plan de UI. Las comprobaciones humanas anteriores corresponden al alcance musical de T-14. La autorización de seis tomas con baseline 2.613 MiB está [registrada](gpu-authorization.json); no se solicitó otra vez. M0 conserva T-08–T-13 pendientes y este informe no sustituye su batería ni selección final.
