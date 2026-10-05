# Informe de QA — M0 / T-06: adapter ACE-Step

| | |
|---|---|
| **Fecha** | 2026-10-05 |
| **Estado** | Verificación técnica CPU/GPU conforme; gate unitario exit 0. Sin veredicto E2E por diseño. El orquestador decide el estado de T-06; M0 continúa abierto |
| **URL auditada** | No aplica: tarea CLI/backend sin UI; no se ejecutó tráfico E2E ni acceso a terceros |
| **Plan y ledger** | [Plan](../../improvement-plan.md) · [Tareas](../../tasks.md) · [Spec](../../spec.md) |

## Veredicto E2E

ℹ️ sin UI por diseño (`test-plan: n/a (sin UI)`). `ledger-lint` exit 0: **0 incoherencias, 8 avisos**; `coverage-check` exit 0 por declaración sin UI, **puerta de cobertura E2E no ejecutada**. No se ejecutó `qa-gate.py`, no hay `results.json` E2E, capturas ni porcentaje E2E. No se atribuye un verde E2E a esta exención.

## Resumen y trazabilidad

| Capa / tarea | Resultado | Evidencia |
|---|---|---|
| T-06, CPU host ampliada con todos los testpaths raíz y adapter | **179 passed, 5 skipped, 1 deselected**, 1 warning; exit 0, 30,01 s, Python 3.12.14 | [Salida](raw/qa-cpu-tests.log), [comando exacto anonimizado](raw/qa-cpu-command.json), [runner](raw/qa-cpu-runner.py) |
| T-06, cobertura del diff frente a `main` | **94,58 %**, mínimo 80 %, exit 0; cinco ficheros de producción medidos, ninguno excluido | [Gate real](raw/qa-coverage-gate.json), [coverage.py JSON real](raw/qa-coverage.json) |
| T-06, CPU contenedor final, evidencia previa conservada | **58 passed, 1 deselected**, exit 0; Python 3.11.14. Cobertura agregada adapter/patches/descriptor/factoría **92,96 %** | [Recibo fix2](fix2-report.md), [CPU](raw/fix2/container-cpu-final.log), [cobertura](raw/fix2/container-coverage-final.log) |
| Ledger del hito | Exit 0, 0 incoherencias; 8 avisos de Changelog ausente en T-06…T-13 | [Salida](raw/qa-ledger-lint.log) |
| Exportador contractual | Exit 0: `engine-v1.json up to date` | [Salida](raw/qa-contracts.log) |
| Ruff global | Exit 0: `All checks passed!` | [Salida](raw/qa-ruff.log) |
| `git diff --check` | Exit 0, sin salida | [Salida](raw/qa-diff-check.log) |
| T-06, GPU real 30 s, WAV y unload | **1 passed, 58 deselected**, 1 warning, exit 0; 144,74 s. Recibo del orquestador; QA no repite GPU | [Salida](raw/gpu-30s.log), [recibo de herramienta](raw/gpu-30s-tool-receipt.json) |

La suite host incluye expresamente `apps/engines/acestep/tests`: el `pytest.ini` raíz no lo incluye. CUDA se oculta en el runner, no se cargan pesos ni se ejecutan builds. Las cinco omisiones son de entorno/contenedor, coherentes con la suite host del fix2; la prueba GPU se deselecciona mediante `-m "not gpu"`. El aviso host es `PytestCacheWarning` por ACL Windows al guardar `nodeids`; no es un fallo de aserción. Los paths normales y los repr con barras duplicadas se anonimizan en los recibos.

## Cobertura declarada de escenarios

Salida JSON de `coverage-check.py`, tal como se obtuvo:

```json
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": "el diff contra la base «merge-base main…HEAD (19ab2395)» no aporta ningún fichero: solo se han mirado los cambios sin comitear"}
```

La spec no aporta criterios rastreables a esta puerta. La lista de 14 tareas se presenta para revisión; la puerta no exigía su cobertura (sí exigiría criterios `[GWT]`). No se han detectado rutas de interfaz, pero la comprobación degradó porque no existen commits propios frente al merge-base: miró el alcance declarado y los cambios sin comitear; no acredita haber examinado un diff de commits completo. [Salida completa y límites](raw/qa-coverage-check.log). El marcador es canónico.

## Gate unitario y pirámide

E2E: no aplica, sin porcentaje. Unitario/integración CPU: **94,58 % de media por fichero del diff**. El global **26,29 %** de `--cov=.` comprende todo el árbol y no es la métrica configurada de cierre; no se usa para otorgar el gate del diff. Los datos de producción son adapter **89,29 %**, descriptor **100 %**, factoría **100 %**, patches **84,62 %**, contrato **99 %**. La única exclusión automática sin datos es el propio runner de recibos QA; se declara y no afecta a producción. La cobertura de contenedor previa usa un ámbito diferente y no sustituye esta medida del diff.

Comando de gate ejecutado después de `. ./scripts/env.ps1`:

```powershell
uv run --no-sync python <plugin>/skills/unit-tests/scripts/coverage-gate.py . --changed-only --base main --min 80 --json --runner '.venv/Scripts/python.exe docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/t06/raw/qa-cpu-runner.py'
```

`<plugin>` corresponde al paquete custom-agents 1.21.1 de Codex; se omite la ruta personal. El runner conserva argv oficial de pytest, variables de cobertura y exit reales. Las caches y basetemp están dentro de `.cache/`; no se instaló ninguna herramienta. [Salida JSON completa del gate](raw/qa-coverage-gate.json).

## Verificación GPU recibida del orquestador

Comando efectivo: `docker compose run --rm engine-acestep python /data/tmp/t06-gpu/run_test.py`. El wrapper ejecuta `pytest.main` con `-m gpu -q -s` y muestrea RAM; equivale al escenario GPU canónico con instrumentación adicional. Imagen `sha256:ecae5c354e3ec7350e1a6a6fc0118c8f3faf5ff4dc976a83e1444e82f3cd95b3`. El propietario autorizó esta prueba excepcional de 30 s; Ollama estaba vacío y no hubo modelo que descargar ni restaurar. Esta evidencia no amplía esa autorización a pruebas futuras.

La prueba acredita carga real y WAV float32 estéreo de **30 s, 48 kHz, 1.440.000 muestras**, sin NaN ni silencio (RMS **0,17382145**), con 31 eventos. Telemetría BF16: `load_s=122.86637192699709`, `run_s=142.50300859300114`, `rtf=null`, `spilled=false`, pico VRAM **7.806,80 MiB**, cap **8.810,31 MiB**. `run_s` incluye la carga: no se suma a `load_s` ni se declara RTF. La diferencia derivada entre ambos es aproximadamente 19,64 s y no constituye una medición separada del rendimiento de generación.

El assert de unload acredita terminación del proceso hijo y estado `loaded=null`; VRAM libre antes **9.322,31 MiB**, después **10.512,50 MiB**. El escritorio liberó memoria durante el test: esa diferencia no es el tamaño del modelo. Lectura posterior del orquestador: **1.338 / 12.227 MiB** usados. La revisión de QA se limita al recibo, sin nueva ejecución GPU.

Muestreo RAM cada **0,5 s**, 291 muestras: pico usado de la VM WSL excluyendo `MemAvailable` **4.567,90 MiB**, máximo RSS hijo **5.651,64 MiB**, pico swap **1,293 MiB**, cache final **16.121,92 MiB**. Son métricas con alcances distintos; no representan RAM física Windows ni VRAM, y no deben sumarse entre sí. Un aviso de deprecación Starlette no afecta a los asserts. [Recibo completo](raw/gpu-30s.log).

## Checklist manual y pendientes

- [x] Revisar el recibo GPU del orquestador: carga real, 30 s, WAV 48 kHz estéreo float32 sin NaN ni silencio, telemetría y unload. Conforme; no repetido por QA.
- [ ] Escucha y aceptación musical humana pertenecen al cierre posterior del hito; CPU no acredita calidad musical, T-07 ni T-10.
- [ ] PDF del informe pendiente: Node v22.23.2 disponible, `markdown-it`, `mammoth` y `puppeteer` no preparados en las caches comprobadas. Se aplicó `custom-agents:to-pdf` hasta la comprobación de dependencias; no se instalaron ni escribieron herramientas fuera del repositorio, ni se generó un PDF ficticio.

No existen bloques `M-xx`, `API-xx` ni `A11Y-xx` porque el plan declara sin UI. Estos pendientes expresan verificaciones humanas/técnicas restantes, no escenarios inventados del test-plan. La revisión A+B+C intento 3 figura sin gaps en el ledger y la prueba GPU ya está acreditada por separado. QA no modifica código de producción, ledger, spec, plan ni Git. Entrega resultado técnico conforme al orquestador para el cierre de T-06; no cierra M0 ni acredita T-07/T-10. PDF pendiente y escucha humana del hito permanecen declarados.
