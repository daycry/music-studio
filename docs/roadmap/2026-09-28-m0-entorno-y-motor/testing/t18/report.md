# Informe de QA — T-18: preparación fiel y procedencia

| | |
|---|---|
| Fecha | 2026-10-05 |
| Estado | **CONFORME CPU — sin UI por diseño** (`passed_cpu_no_ui`) |
| URL | Sin UI; probe offline con engine local inaccesible, `http://127.0.0.1:1` |
| Plan | [Plan](../../improvement-plan.md) · [Ledger canónico](../../tasks.md) |
| Recibo | [qa-receipt.json](qa-receipt.json) |

## Veredicto y límites

ℹ️ sin UI por diseño (`test-plan: n/a (sin UI)`): ledger-lint exit 0, cero incoherencias y nueve avisos de Changelog; coverage-check exit 0, `applies=false`. La puerta de cobertura E2E no se ejecutó: no se presenta como «cobertura OK».

`qa-gate.py` no aplica y no se ejecuta sin resultados Playwright. No hay E2E, screenshots ni porcentajes E2E ficticios. El resultado CPU procede de las ejecuciones independientes que siguen y del gate de cobertura de producción cambiada ≥80 %.

## Resumen independiente

- Verificación exacta de los seis módulos T-18: **185 passed, 1 skipped, 5 warnings**, exit 0, 8,91 s; ejecutada con cobertura oficial pytest-cov por directorios, sin imports forzados.
- Suite configurada del workspace: **236 passed**, exit 0. Su `pytest.ini` omite ACE-Step; se ejecutó también el workspace completo explícito `tests packages apps/engines`: **309 passed, 5 skipped, 1 deselected, 5 warnings**, exit 0, 18,89 s.
- Los cinco warnings son Starlette TestClient timeout existentes. La primera suite configurada añade un warning WinError 5 al guardar la caché; no es un fallo de prueba. La suite completa con caché precreada no presenta ese aviso.
- Exportador de contrato: `engine-v1.json up to date`, exit 0. Manifiestos legados: `all valid (4 manifests)`, exit 0. Ruff del alcance: `All checks passed!`, exit 0. CLI `--help` real: exit 0.
- Probe CLI real offline: **72 versos, nueve tags completos y 32 registros de hashes preservados**. Repetición con mismo payload, SHA-256 y mtime. Engine inaccesible; sin catálogo/load/jobs/FFmpeg, modelos ni audio en prepare-only.

## Cobertura de producción

Cruce independiente del diff contra `08d6d82` con `executed_lines`/`missing_lines` oficiales. Se cuentan únicamente statements añadidos; en el módulo nuevo se cuentan todos. El descriptor modifica un literal sin statement nuevo separado: el fichero completo ejecuta 30/30 statements y las aserciones comprueban metadata/compatibilidad. No se mide branch coverage.

| Archivo | Statements cambiados | Archivo completo |
|---|---|---|
| `scripts/input_preparation.py` | 92/95 = 96.84 % | 92/95 = 96.84 % |
| `scripts/generate.py` | 44/47 = 93.62 % | 362/384 = 94.27 % |
| `apps/engines/acestep/adapter.py` | 2/2 = 100.00 % | 137/175 = 78.29 % |
| `apps/engines/acestep/descriptor.py` | Literal; sin statement nuevo separado | 30/30 = 100.00 % |
| `packages/audio-post/audio_post/manifest.py` | 52/59 = 88.14 % | 123/132 = 93.18 % |

**Gate ≥80 %: conforme en cada archivo medible.** Agregado cambiado: 190/203 = 93,60 %. El agregado histórico de los directorios es 1237/1667 = 74,21 %, incluye código previo fuera de este cambio. El adapter completo tiene 78,29 %, pero sus dos statements añadidos están cubiertos; estos alcances no se confunden.

## Coverage-check: salida literal

```json
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14", "T-15", "T-16", "T-17", "T-18", "T-19"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": "el diff contra la base «merge-base main…HEAD (08d6d82d)» no aporta ningún fichero: solo se han mirado los cambios sin comitear"}
```

`eximidos` lista T-00–T-19 para revisión; `eximidos_exigidos=false`: la spec no aporta criterios rastreables y no son exenciones de [GWT] exigidos. Ninguna ruta UI detectada. **Lectura del diff degradada:** el merge-base main…HEAD coincide con `08d6d82d` y no aporta commits propios; el script mira alcance declarado y cambios sin comitear, no acredita haber examinado el diff completo. Marcador canónico, sin aviso de escritura del marcador.

## Trazabilidad de T-18

| Criterio | Resultado y evidencia |
|---|---|
| Original/efectivo, diff/hashes, no overwrite | Tests de preparación/publicación e integridad; probe de 32 hashes y repetición inmutable |
| Default intacto; limpieza opt-in conserva versos/tags | Tests BOM/CRLF/asteriscos/default; probe CLI 72/9. Original privado ya carecía de Markdown: derivación explícita existente para probar limpieza |
| Key/compás opcionales, omisión/conflictos/autoría | Tests CLI, descriptor y adapter; schema legado de key preservado, metadata upstream comprobada sin inferencia |
| Prepare-only offline y recibo privado inmutable | Subprocess real a endpoint inaccesible; tests de cero HTTP/catalog/load/jobs/FFmpeg; presupuesto del motor `pending` |
| Reutilización, atomicidad, confinamiento y privacidad | Tests fallos de publicación/manifiestos, referencias y seed/variant binding; cuatro ejemplos legados válidos |
| RED/GREEN, revisión y QA ≥80 %, sin cumplimiento artístico | RED leídos en implementación/fix; revisión 2 sin gaps; esta QA independiente y cobertura oficial del diff |

La revisión 1 detectó tres gaps; la revisión 2 acredita sus correcciones. **Degradación de revisión declarada:** por límite de threads reutilizó contextos A/B anteriores, independientes de la implementación del fix; no fueron dos contextos recién creados. Esta QA sí se despachó con contexto fresco. No se oculta esa limitación ni se convierte QA en aprobación musical.

## Publicación y enlaces

Examen de los archivos públicos T-18 y documentación/producción listadas: sin versos largos originales, secretos reales de `.env` ni rutas personales absolutas detectados; enlaces locales resueltos. Es un examen acotado y determinista, sin consultar URLs externas ni prometer escaneo integral de secretos. El recibo público contiene conteos, hashes y resultados; las salidas crudas permanecen en caché local ignorada.

## Checklist manual pendiente

No existe test-plan UI ni bloques M-xx que automatizar. Quedan controles humanos de producto:

- [ ] Valorar por escucha pronunciación, reparto vocal/rap, ritmo, instrumentos, arco y outro con la [rúbrica](preparation-report.md); calidad artística todavía no aprobada.
- [ ] Ejecutar T-19 para presupuesto real de tokens, idioma estructurado al LM y fronteras del motor antes de atribuir naturalidad al modelo.
- [ ] Completar T-08/T-12/T-13 y elección por escucha: este resultado no cierra M0.

## Evidencias y entrega

Recibo público: [qa-receipt.json](qa-receipt.json). Evidencia local privada: `.cache/dev-cycle/t18/qa/` (`targeted.txt`, `workspace.txt`, `full-workspace.txt`, `coverage.json`, `changed-coverage.json`, `ledger-lint.txt`, `coverage-check.txt`, `contracts.txt`, `manifests.txt`, `cli-help.txt`, `probe.txt`, `preparation-receipt.json`, `public-scan.json`, `ruff.txt` y scripts de reproducción).

Entorno `scripts/env.ps1`, Python gestionado 3.12.14, `uv run --frozen --all-packages`, temporales/cachés dentro del repositorio. Sin instalaciones, GPU/build/descargas ni cambios de código, Git, ledger o journals ajenos por QA. Copia del probe redirige solo su recibo a la carpeta QA y exige que la derivación privada ya exista.

**PDF pendiente:** dependencias de `to-pdf` ausentes; no se instalaron. Handoff al orquestador para decisión/ledger canónico; QA no cierra estados. Medición gestionada por root, ventana parcial desde 21:40:08Z posterior al despacho; horas IA, tokens y coste reales desconocidos, no inferidos del reloj.
