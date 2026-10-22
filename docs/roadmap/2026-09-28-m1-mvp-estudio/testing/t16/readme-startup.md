# T-16 ? recetas reproducibles de arranque

Fecha: 2026-10-10

Se sustituyo la receta generica del README por instrucciones reproducibles y cerradas: clon publico, bootstrap gestionado por uv, stack mock de M1, almacenamiento persistente mediante recibo/VHDX/attach WSL2, override Compose con UUID y convivencia con Ollama fuera de Docker. El README enlaza la documentacion oficial de montaje VHDX en WSL2 y deja explicitamente que el operador requiere administrador.

## Evidencia

- RED: `tests/test_readme_startup.py` fallo porque faltaban el remoto publico y la receta persistente.
- GREEN: `.venv\Scripts\python.exe -m pytest tests/test_readme_startup.py -q --basetemp=.cache/pytest/t16-readme-green` -> **1 passed**.
- `git diff --check -- README.md tests/test_readme_startup.py` -> limpio.

Esto cubre la documentacion de arranque; T-16 sigue abierta por M-01 GPU real, M-03 backup/restauracion y el cierre formal de M0/T-13.
