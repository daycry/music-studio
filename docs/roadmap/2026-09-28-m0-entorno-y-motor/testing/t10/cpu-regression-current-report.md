# Regresion CPU de evaluacion M0

Fecha: 2026-10-10

Comando ejecutado con el interprete del proyecto:

```powershell
.venv\Scripts\python.exe -m pytest scripts/eval/tests/test_evaluation_cpu.py scripts/eval/tests/test_evaluation_guards.py scripts/eval/tests/test_evaluation_fix1.py scripts/eval/tests/test_evaluation_stream_silence.py scripts/eval/tests/test_capabilities_plan.py scripts/eval/tests/test_capabilities_runtime.py scripts/eval/tests/test_capabilities_metrics.py scripts/eval/tests/test_capabilities_evidence.py scripts/eval/tests/test_capabilities_cli.py scripts/eval/tests/test_capabilities_checks.py scripts/eval/tests/test_capabilities_fix1.py -q --basetemp=.cache/pytest/m0-eval-current2
```

Resultado: **219 passed en 28,07 s**, exit 0. El bloque verifica el plan, runtime, metricas, evidencia, CLI y guards sin inferencia GPU. No acredita las ejecuciones reales de T-09/T-10, el WER cantado, las 30 tomas de T-11 ni la escucha de T-13.
