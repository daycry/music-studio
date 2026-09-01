# Tests del runner (Fase 0)

Suite pytest que corre **sin GPU y sin torch** (biblioteca estándar + pytest): cubre la
puerta anti-RCE de D-14 (`assert_safetensors`), el presupuesto D-17, la validación de
peticiones, `_slug`, las estadísticas e informes atómicos de `_timing.py`, la protección C1
de `vram_profile.py` y el contrato M-3 de `gpu_seconds`. Ejecución, desde la raíz del repo:
`python -m pytest apps/runner/tests -q` (instala pytest con `pip install pytest` si falta).
