# Memoria del proyecto

Índice de la memoria persistente. Una línea por memoria; el contenido vive en cada fichero.

- [Project context](project-context.md) — personal Suno-like app, restart from zero on RTX 5070 12 GB, all inside project folder
- [Memory location](memory-location.md) — all memory lives in docs/memory/, never in ~/.claude
- [Local by default](local-by-default.md) — every feature defaults to a local model; APIs only opt-in alternatives
- [Python isolation](python-isolation.md) — never install into machine Python; project-local uv interpreter + .venv via scripts/env.ps1
