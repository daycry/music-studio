# QA CPU T-10 — intento 1

**QA_CPU_PASS.** Agente independiente de contexto fresco, después de la revisión A+B limpia. Root verificó 59 fuentes, 318 artefactos privados, 6 artefactos de laboratorio, los JUnit y el JSON oficial de cobertura. [Recibo](cpu-qa1-receipt.json).

Una suite dirigida: **79 pruebas pasan en 7,60 s**; JUnit sin fallos, errores ni omisiones. Cinco pruebas del descriptor pasan, 164 quedan deseleccionadas. Ruff check y formato conformes en los 14 archivos Python de T-10. CLI plan/report reales producen dos sesiones nuevas de 522 filas, 13 casos, dos superficies y tres perfiles, todas con `verified=false` y veredicto null. No se ejecutó inferencia.

La media aritmética de los seis módulos de producción es **89.8051 %**, superior al 80 %. La fuente es pytest-cov; no son líneas del diff ni un mínimo del 80 % por archivo.

| Archivo | Cobertura oficial |
|---|---:|
| `scripts/eval/capabilities.py` | 72.2689 % |
| `scripts/eval/capabilities_evidence.py` | 100.0000 % |
| `scripts/eval/capabilities_metrics.py` | 100.0000 % |
| `scripts/eval/capabilities_native.py` | 87.9765 % |
| `scripts/eval/capabilities_plan.py` | 95.9184 % |
| `scripts/eval/capabilities_runtime.py` | 82.6667 % |

ℹ️ Sin UI por diseño: el frontmatter declara `test-plan: n/a (sin UI)`. `ledger-lint` devuelve 0: cero incoherencias y seis avisos de Changelog en tareas abiertas. `coverage-check` devuelve 0 con `applies=false`: acepta la declaración sin UI, no mide cobertura E2E. La puerta Playwright no aplica y no se declara como ejecutada.

Las siete evidencias RED previas y sus 13 regresiones se cotejaron por hash; ahora pasan. Las 14 fuentes T-10, 45 ajenas, corpus original, lock y `.coverage` raíz permanecen intactos durante QA. Fixtures y cachés se aislaron con un plugin privado en memoria, sin editar conftest. Root autorizó exclusivamente la nueva sesión UUID del test CLI original; se conservaron sus argumentos, transporte y aserciones sin redirección. Ninguna sesión anterior se modificó.

Comandos con entorno gestionado: pytest dirigido con cobertura/JUnit, pytest del descriptor, Ruff check y format --check, `python -m scripts.eval.capabilities plan/report`, y los dos gates oficiales del plugin. Los comandos exactos y sus logs sellados están en el recibo privado; no se repitió la suite tras pasar.

**T-10 sigue en progreso.** Faltan recursos aprobados, pruebas GPU, música y escucha, bitexact real de repaint, ground truth y LoRA auditado. QA CPU no habilita capacidades ni acredita la puerta de M1. No hubo GPU, Docker, WSL, modelos, audio de T-16, UI, red ni instalaciones por el agente.
