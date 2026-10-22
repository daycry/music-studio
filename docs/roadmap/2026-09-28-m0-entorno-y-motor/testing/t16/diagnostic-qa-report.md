# QA independiente — T-16, diagnóstico fix1

**Resultado: conforme para el arnés CPU acotado; 4/4 pruebas pasan, cero fallos.** T-16 sigue en-progreso: CA1/2 conservan sus evidencias previas y CA3/4 permanecen abiertas. M0 no se cierra. No hay validación GPU, musical ni de la causa real del fallo.

ℹ️ Sin UI por diseño (`test-plan: n/a (sin UI)`). `qa-gate.py`: n/a, no se ejecuta ni se fabrica results.json E2E. La puerta de cobertura no se ha ejecutado: el marcador se acepta y se listan las tareas para revisión. No se declara un porcentaje de cobertura del producto para esta corrección efímera.

## Evidencia independiente

Entorno gestionado mediante `. ./scripts/env.ps1`: Python 3.12.14; AST compatible con 3.11. Todas las salidas de esta ejecución viven en `.cache/dev-cycle/t16/diagnostic-qa/`, ignorada por Git; el recibo público conserva sus SHA-256. No se alteran las fuentes auditadas, el producto, el arnés de seis fuentes, la imagen, el servicio 8101 ni los journals ajenos.

| Comprobación | Resultado | Evidencia privada |
|---|---|---|
| Integridad antes/después: 29 archivos originales y 12 del candidato | Exit 0; hashes idénticos | integrity-before.json, integrity-after.json y sus logs |
| Recibo público de fix1 frente al privado | Idénticos; fuentes vinculadas congeladas | integrity-before.json |
| Delta respecto del original | Solo condición final y SystemExit(1); AST 3.11 válido | verify.py, integrity-after.log |
| Cuatro escenarios del bloque real con dobles CPU | 4 passed, exit 0, 0,06 s | tests-clean.log, tests-clean.xml |
| Candidato real sin `--execute` | Exit 0, prepared_not_executed, una toma de 30 s | prepare-only.log |
| Preparación con subprocess/HTTP bloqueados | Exit 0; subprocess=0, HTTP=0, host_torch=false | prepare-guard.py, prepare-guard.log |
| Ledger | Exit 0; 0 incoherencias, 7 avisos Changelog | ledger.log |
| Cobertura del plan | Exit 0; applies=false, sin rutas UI ni degradación | coverage.log |

SHA original: `bc7980091dd325528f2a8c081096dde2f1005122f311626fcd73c79ce214f81e`. SHA candidato: `e6fd237e2b035154822455a83e0b1adfbc82260570abf76c54da3f28257df82c`. Ambos se verificaron antes y después.

## Escenarios CPU

| CLI | Motivo de parada | Unload | Exit esperado y observado |
|---|---|---|---|
| 1 | Ninguno | true | 1 |
| 1 | Guarda de presupuesto | true | 1 |
| 0 | Ninguno | false | 1 |
| 0 | Ninguno | true | 0 |

Cada prueba ejecuta el AST real del candidato con dobles: comprueba una única llamada de limpieza y la persistencia de `exit_code`/`unload_confirmed` en group.json. El bloque finally permanece intacto y se ejecuta antes del exit final. Estos escenarios usan rutas temporales exclusivas y entradas sintéticas; no generan audio ni escriben sobre inputs, pesos o archivos privados existentes.

Primera pasada: 4 passed en 0,11 s y un aviso `Unknown config option: cache_dir` provocado por desactivar cacheprovider; tests.log/tests.xml se preservan. Segunda pasada con caché propia: 4 passed en 0,06 s y un aviso `PytestCacheWarning` por WinError 5 al crear la caché. Ambos exit 0; no se oculta ni se interpreta el aviso como fallo de prueba. No se repite la suite completa por esta incidencia ambiental.

La evidencia RED previa acredita 3 failed/1 passed, seguida de GREEN 4 passed. Los intentos de fixture con KeyError/NameError no se contabilizan como RED de producto. Se preservan por hash; no se vuelven a generar ni modificar.

## Puerta sin UI

```json
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14", "T-15", "T-16", "T-17", "T-18", "T-19"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": null}
```

La lista es informativa: la spec no aporta criterios rastreables y la puerta no exigía cobertura de esos IDs. Los avisos del ledger corresponden a T-08–T-13 y T-16 sin campo Changelog; no son incoherencias duras.

## Límites y pendientes

La evidencia IPC anterior se leyó, sin repetirla: HTTP 202, terminal error, hijo en otro proceso, parent_torch_imported=false, tmp fallido eliminado y trazas privadas preservadas fuera de tmp. Sus archivos y las factorías/child actuales coinciden con el recibo congelado. Es un antecedente CPU con cómputo simulado, no una ejecución nueva ni una demostración de la causa T-16.

- [ ] Ejecutar y evaluar la toma diagnóstica GPU únicamente tras la aceptación del orquestador; esta QA no la ejecuta ni la autoriza.
- [ ] Determinar la causa real y valorar audio/calidad; un resultado de 30 s no reproduce ni refuta el fallo de 90 s.
- [ ] Completar CA3/4 y las verificaciones canónicas restantes de T-16 antes de cerrarla.
- [ ] PDF pendiente por herramientas ausentes; no se instala ni se escribe fuera del proyecto.

Sin API/A11Y/E2E de UI ni checklist M-xx: el plan declara sin UI. Sin Docker/GPU, descarga de pesos, instalación, torch host, build o suite general. No se publica en Confluence ni Jira, no hay handoff documental de cierre. Consumo real desconocido, sin medición o atribución individual: esta QA pertenece al lote concurrente T-08 GPU/T-16 revisión 2.
