# QA independiente — T-09 observabilidad autónoma / piloto privado y T-20 documental

**QA_CPU_DOCUMENTAL_PASS**. Producto: 173/173; ejecutor privado: 32/32; total CPU: 205/205. Sin fallos, skips, reintentos ni pruebas Playwright. Cobertura oficial `coverage.py` mediante `pytest-cov`: **1188/1439 líneas = 82,55733148 %**, sobre siete módulos completos; sin exclusiones ni filtro de líneas cambiadas. Cada módulo y cada caso quedan en `coverage-summary.json`, `product-coverage.json` y `junit-records.json`.

Esta ejecución independiente usa las diez suites canónicas completas del recibo de implementación y la suite privada completa `autonomous-pilot-fix2/test_pilot.py`. La fixture privada bloquea procesos y red reales; modelos/recursos/errores de IO y limpieza se prueban con mocks. No se ejecutan `prepare`/`run` reales. Los resultados dirigidos históricos no se suman. Los comandos, UTC, exits y stdout/stderr originales UTF-8 están en `receipt.json`; los dos JUnit originales se conservan.

Veredicto determinista del script real `qa-gate.py`, con conversión explícita de JUnit CPU a stats compatibles; no constituye E2E:

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 205,
    "failed": 0,
    "flaky": 0,
    "skipped": 0,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}
```

ℹ️ sin UI por diseño (`test-plan: n/a (sin UI)`); `ledger-lint.py`: exit0, 0 incoherencias y 7 avisos Changelog de tareas abiertas. `coverage-check.py`: exit0; **la puerta de cobertura E2E no se ha ejecutado**. Listado completo del script:

```json
{
  "applies": false,
  "gwt_sin_id": 0,
  "test_plan_na": true,
  "marcador_no_canonico": null,
  "eximidos": [
    "T-00",
    "T-01",
    "T-02",
    "T-03",
    "T-04",
    "T-05",
    "T-06",
    "T-07",
    "T-08",
    "T-09",
    "T-10",
    "T-11",
    "T-12",
    "T-13",
    "T-14",
    "T-15",
    "T-16",
    "T-17",
    "T-18",
    "T-19",
    "T-20"
  ],
  "eximidos_exigidos": false,
  "rutas_ui": [],
  "rutas_ui_origen": {},
  "rutas_ui_degradado": null
}
```

No hay rutas UI detectadas, comprobación degradada ni marcador no canónico. Los 21 IDs se listan para revisar su Verificación; `eximidos_exigidos=false` y no son criterios GWT eximidos.

T-20: **12 documentos / 156 enlaces locales / 0 errores**, verificados por checker independiente. Destinos contenidos en el repositorio y existentes, fences cerrados; no hay enlaces con fragmento o dentro de fences en esta tanda. `document-links.json` registra cada origen, línea, destino y resultado. `document-coherence.json` enlaza la evidencia de Docker producto, Ollama WSL compartido no poseído por el estudio, server como único escritor SQLite, job/job_dependency GPU1/CPU2 sin Kafka/Redis, y despliegues M1–M4/ComfyUI CUDA pendientes. Las filas de licencias se contrastaron documentalmente, sin instalar ni certificar software futuro.

Custodia: **160 archivos protegidos intactos** antes y después, incluidos 64 fuentes, 12 documentos, ejecutor privado y `.coverage` raíz, más originales privados y recibos/informes previos aceptados. `protected-before.json`, `protected-after.json` y `custody.json` contienen tamaños/SHA-256. `.coverage` raíz conserva `153490fc264e69bcc7573506ab68a41a109bbdd7bcf6583d0915bdcd84c5d32d`; piloto privado conserva `cbe68de959572642e5f311860f8052070b1db343e42e1b1dcabcea39bed3bb2d`.

| Tarea | Resultado acreditado | Pendiente |
|---|---|---|
| T-09 subfase ADR-0036 | Regresión CPU y custodia conformes | Piloto real nuevo, navegador visible, acreditación WDDM/carga/unload y matriz160 |
| Ejecutor privado T-09 | 32 casos CPU conformes sobre fuente final sellada | Recuperación y cleanup bajo procesos/hardware reales |
| T-20 | Enlaces y coherencia documental conformes | Root acepta/publica el cierre documental; despliegue se valida en M1–M4 |

No se requieren nuevas lecturas manuales del propietario por esta QA. No existe checklist M-xx de M0 por el marcador sin UI. Las comprobaciones operativas anteriores siguen pendientes y no se transfieren falsamente a manual ni se dan por hechas. No se acredita calidad musical, spill causal, memoria compartida calibrada independientemente ni rendimiento GPU. T-09/M0 permanecen abiertos. Root conserva ownership de ledger/Git/documentación y acepta esta QA antes del piloto.

PDF no generado: la skill `custom-agents:to-pdf` requiere dependencias ausentes; la instalación está prohibida en el encargo. Informe Markdown y evidencias completas disponibles. No hubo instalaciones ni ejecución de navegador.
