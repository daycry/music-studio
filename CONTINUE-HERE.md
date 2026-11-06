# Continuar aquí

2026-11-06 · Rama `m0/t-09-benchmark-basico`, sobre T-08 (`420052a`) y T-16 (`f7d7c39`).
Estado canónico: [M0](docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md) y [M1](docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md). M2/M3 congelados: ADR-0089.

**T-09 cerrada.** Tres jobs de 120 s válidos, Turbo BF16/PT, semillas 1/2/3; `spilled:false` literal en todos. A/B y QA final aprobadas, sin cambios de producto.
CLI 229,56/185,49/182,51 s; inferencia 30,69/33,74/37,28 s; máximo host 9.394 MiB. [Informe](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/benchmark-basico-2026-11-06.md).
Raw privado `.cache/dev-cycle/20261106-m0-t09/qa/`: NDJSON terminal original, manifests, recibos nativos y CSV host por job.
`spilled:false` del guard es una heurística del allocator; no certifica ausencia absoluta de paging/shared WSL.
**GPU:** inicio/final Ollama vacío y GPU 1.228 MiB. Contenedor propio retirado; imagen `engine-acestep:t09-20261106` (`76138442`) conservada.

**T-08 cerrada:** CPU 48+suplemento 1 pass; GPU 4 pass/0 skip, 275,83 s; A/B y QA aceptadas, sin cambios de producto.
[CPU](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/analysis-cpu-2026-11-06.md) · [GPU](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/analysis-gpu-2026-11-06.md).
**Abierto:** M0 tiene 16 completadas/3 canceladas; T-13/T-16 pendientes. M1 tiene 15 completadas/2 canceladas; T-16 exige ACE-Step real desde web, escucha y ritual final.
T-16: captura opcional y fix Windows aceptados CPU 437 pass/9 skip; seis audios históricos no certifican códigos LM/backend iguales por par.
**Después:** capturas comparables T-16; elección del propietario T-13 y aceptación M1. Claude CLI sólo tras cierre real de M1; aún no invocado.

**Demo:** http://127.0.0.1:3000/create · API 8000, sólo mock CPU. Proyecto `music-studio-e2e-368b45c362fb`, tres servicios intactos.
Compose privado `.cache/dev-cycle/20261105-t16-readme/compose.demo.json`; conservar datos e imágenes previos.
**Preservar:** 71 archivos ajenos según `.cache/dev-cycle/20261106-m0-t09/initial.json`; no restaurar journals ni reactivar M2/almacenamiento.
No SQLite viva desde Windows ni helpers históricos GPU de `.cache/dev-cycle/t08/` o `t16/`.
**Git:** main sigue en `3dede62`; rama apilada sin integrar mientras T-16 esté abierta. Sólo stage explícito.
Cuatro candidatos de conocimiento pendientes; no promover sin curator.
