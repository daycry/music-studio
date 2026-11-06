# Continuar aquí

2026-11-06 · Rama `m0/t-16-tomas-comparables`, sobre T-09 (`fc7f0ed`), T-08 y software T-16 (`f7d7c39`).
Estado canónico: [M0](docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md) y [M1](docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md). M2/M3 congelados: ADR-0089.

**T-16: fix CPU aceptado; GPU pendiente.** Seis tomas previas de90 s válidas, Turbo8 y SFT50/CFG7; **0/3 parejas certificadas**.
Prompts/argumentos LM iguales, códigos efectivos no vacíos pero hashes distintos. Prueba CPU AST/mock demuestra que la ruta PT individual no aplica la semilla al muestreo.
Raw `.cache/dev-cycle/20261106-m0-t16/gpu-pairs/qa/`; diagnóstico `diagnosis-seeding/`, fix `seed-fix/`: A/B sin hallazgos, QA CPU478 pass/10 skip, delta15/15=100 %.
Software T-16 aceptado en CPU: 437 pass/9 skip. No recertificar audios históricos sin observaciones; validar los recibos nuevos con índice 0/1/2.
**GPU:** T-16 terminó con Ollama vacío/GPU 1.227 MiB. Contenedores propios retirados y demo intacta. Diagnóstico actual sólo CPU/lectura; no repetir GPU a ciegas.

**T-09 cerrada y subida:** `fc7f0ed`; tres jobs reales de120 s, `spilled:false`, máximo host 9.394 MiB; A/B y QA aprobadas.
[Benchmark](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/benchmark-basico-2026-11-06.md). El guard no certifica ausencia absoluta de paginación WSL.
**T-08 cerrada:** CPU 48+1 pass, GPU 4 pass/0 skip; A/B y QA aprobadas, sin cambios de producto.
**Abierto:** M0 tiene16 completadas/3 canceladas; T-13/T-16 pendientes. M1 tiene15 completadas/2 canceladas; T-16 exige ACE-Step real desde web y escucha.
**Después:** elección del propietario T-13 y aceptación M1. Claude CLI sólo tras cierre real de M1; aún no invocado.

**Demo:** http://127.0.0.1:3000/create · API8000, sólo mock CPU. Proyecto `music-studio-e2e-368b45c362fb`, tres servicios intactos.
Compose privado `.cache/dev-cycle/20261105-t16-readme/compose.demo.json`; conservar datos e imágenes previos.
**Preservar:** 71 archivos ajenos y68 fuentes según `.cache/dev-cycle/20261106-m0-t16/gpu-pairs/initial.json`; no restaurar journals ni reactivar M2/almacenamiento.
No SQLite viva desde Windows ni ejecutar/importar helpers históricos GPU de `.cache/`.
**Git:** main sigue en `3dede62`; ramas apiladas sin integrar mientras T-16 esté abierta. Sólo stage explícito.
Limpieza: 55 contenedores,29 referencias de imágenes,6 copias de revisión (128 MB) y214 temporales pytest antiguos (1,47 GB) retirados. Recibos `.cache/cleanup/20261106/`; repetir al cerrar fase.
