# Informe de QA — M0 · Fase 2 (T-03 y T-04)

| | |
|---|---|
| **Fecha** | 2026-10-05 |
| **Estado** | Pruebas sin GPU verificadas; QA de UI no aplica por declaración del plan |
| **Alcance** | T-03 contrato `/v1`, engine común y mock; T-04 audio-post y manifiesto |
| **Revisión** | Intento 3 A+B+D sin gaps pendientes, registrado en el ledger |
| **Plan** | [improvement-plan.md](../improvement-plan.md) |
| **Ledger** | [tasks.md](../tasks.md) |
| **Base git al verificar** | `1f30b1f66f4f7a469dbb4f2ece4e723b82f99677`; cambios de trabajo sin comitear |

ℹ️ sin UI por diseño (`test-plan: n/a (sin UI)`): `ledger-lint` exit 0, 0 incoherencias y 9 avisos; `coverage-check` exit 0 acepta la declaración y **no ejecuta la puerta de cobertura de UI**.

## Veredicto (qa-gate)

`qa-gate.py` no aplica: no hay Playwright, `results.json` E2E ni porcentaje E2E. No se fabrica un resultado de este gate ni se declara un verde E2E. No se ha abierto URL ni probado host alguno. La excepción sin UI del agente QA permite terminar con exit 0 tras documentar las puertas y verificaciones; no es el cierre completo del hito.

## Resumen y verificaciones

| Comando | Resultado | Evidencia |
|---|---|---|
| `uv run pytest -m "not gpu" -q` | exit 0 · **125 passed in 13.15s** | [pytest.txt](raw/pytest.txt) |
| `uv run ruff check .` | exit 0 · All checks passed! | [ruff-check.txt](raw/ruff-check.txt) |
| `uv run ruff format --check <Python cambiados>` | exit 0 · 23 files already formatted | [ruff-format-changed.txt](raw/ruff-format-changed.txt), [lista y códigos](raw/test-exitcodes.json) |
| `uv run scripts/export_contracts.py --check` | exit 0 · engine-v1.json up to date | [contracts-check.txt](raw/contracts-check.txt) |
| `uv run scripts/verify_manifest.py packages/contracts/examples/` | exit 0 · all valid (4 manifests) | [manifest-check.txt](raw/manifest-check.txt) |

Todos los comandos Python se ejecutaron después de `. ./scripts/env.ps1`, con Python 3.12.14 gestionado dentro del proyecto. No se instaló ninguna dependencia.

## Puertas del ledger y cobertura de UI

[ledger-lint.txt](raw/ledger-lint.txt): 0 incoherencias, 9 avisos por falta de campo Changelog en T-05, T-06, T-07, T-08, T-09, T-10, T-11, T-12 y T-13. Son tareas futuras; el aviso no es un error duro. [Códigos de salida](raw/entry-gates.json).

[coverage-check.txt](raw/coverage-check.txt) acepta el marcador canónico. Lista `eximidos`: **T-00, T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10, T-11, T-12, T-13**; `eximidos_exigidos=false`. Son tareas listadas para revisión; el script no detecta criterios rastreables `[GWT]` en la spec y no exigía cobertura automática de estas tareas.

Aviso `rutas_ui_degradado`: el diff contra `merge-base main…HEAD (1f30b1f6)` no aporta ficheros porque no hay commits propios. La comprobación solo mira el alcance declarado y cambios sin comitear, y no incluye lo que scope-check excluye. `rutas_ui=[]` no demuestra haber inspeccionado todo el diff histórico. `marcador_no_canonico=null`.

Salida JSON de coverage-check, tal cual:

```json
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": "el diff contra la base «merge-base main…HEAD (1f30b1f6)» no aporta ningún fichero: solo se han mirado los cambios sin comitear"}
```

## Cobertura unitaria del alcance

Se conserva el [recibo del gate oficial](raw/coverage-gate.json) ejecutado por el orquestador, sin repetirlo: exit 0, **93,62 %** en modo `changed-only`, mínimo **80 %**; global **72,81 %**. El global incluye scripts históricos fuera del alcance y no sustituye la medición del diff. Aviso: `conftest.py` carece de datos de cobertura y queda excluido de la media. El recibo muestra porcentajes por fichero; no implica que cada fichero individual alcance el 80 %.

## Trazabilidad y límites

| Tarea | Evidencia | Límite |
|---|---|---|
| T-03 | Suite conjunta verde, esquema exportado al día; ledger registra 40 tests de contrato/common/mock y 8 AST | GPU/NVML reales, Docker y montaje real no comprobados aquí; las pruebas usan simulación donde corresponde |
| T-04 | Suite conjunta con ffmpeg real, 53 pruebas registradas en ledger y 4 ejemplos válidos | No acredita una canción ACE-Step real ni CLI completo, pendientes de T-05 en adelante |
| T-02 | Suite de pesos incluida en las 125 pruebas; rechazo fail-closed de STACK_GLOBAL revisado en intento 2 | Layout ACE-Step contra upstream queda para T-06 |

La revisión del intento 3 conservó verdes anteriores y reevaluó D2: 0 Critical, 0 Important y 0 Minor pendientes. A tuvo contexto fresco; B y D reutilizaron contextos de revisión por límite de hilos, con revisores independientes del autor de D2. El TDD original del código heredado no es verificable; los RED/GREEN de las correcciones sí están documentados en el ledger.

El orquestador informa de Docker/WSL bloqueados por permisos denegados y de pre-commit bloqueado por `WinError 5` al crear un directorio con permisos 0700. No se presentan como comprobaciones completas. Python 3.11 real no está instalado; la comprobación de gramática AST 3.11 no sustituye una ejecución con ese intérprete. Ruff directo pasó; el formato se comprobó solo sobre los 23 Python cambiados. Los 14 ficheros históricos fuera de alcance que el formato global señalaría no se modificaron.

## Checklist pendiente

- [ ] Verificar ejecución real con Python 3.11 cuando el intérprete del engine esté disponible.
- [ ] Ejecutar integración Docker/WSL y comprobaciones GPU en el entorno autorizado; GPU compartida conforme ADR-0022.
- [ ] Repetir pre-commit completo cuando se resuelva el bloqueo de permisos del entorno.
- [ ] Continuar T-05 y siguientes: imagen, ACE-Step, generación por CLI, medición y escucha siguen fuera de este informe.

No hay checklist visual ni capturas porque M0 no tiene UI. PDF no generado: se aplica la salida sin UI y no se instala un renderer. El informe es solo local; no se publica en Confluence ni Jira. El orquestador es el único que actualiza estados: este agente no modifica ledger, spec, plan ni código; M0 permanece abierto.

Integración Git pendiente: este perfil permite lectura de .git, pero no escritura. Este informe acredita la verificación técnica del árbol de trabajo; no acredita commit, fast-forward ni publicación de la rama. La documentación de uso y reanudación se actualizará después mediante el orquestador.
