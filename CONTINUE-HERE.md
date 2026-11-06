# Continuar aquí

2026-11-06 · Rama `m0/t-08-verificacion-cpu`, apilada sobre T-16 (`f7d7c39`).
Estado canónico: [M0](docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md) y [M1](docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md). M2/M3 congelados: ADR-0089.

**T-08 cerrada:** CPU48 pass/0 skip; suplemento beats CPU1 pass. Informe CPU publicado en `cd40c2b` antes de GPU, como pidió el propietario.
Batch GPU original: **4 pass/0 fail/0 skip/48 deselected**,275,83 s. ASR/alineador, CLAP y estética CUDA/BF16; beats CPU.
[CPU](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/analysis-cpu-2026-11-06.md) · [GPU](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/analysis-gpu-2026-11-06.md). A/B sin hallazgos y QA final aprobada; cierre técnico aceptado, sin cambios de producto.

**Abierto:** M0 tiene15 completadas/3 canceladas; T-09/T-13/T-16 pendientes. M1 tiene15 completadas/2 canceladas; T-16 exige ACE-Step real desde web, escucha y ritual final.
T-16 tiene captura opcional y fix Windows aceptados en CPU (437 pass/9 skip). Sus seis audios históricos no prueban identidad de códigos LM/backend; no certificar parejas.
**Siguiente:** benchmark básico T-09; capturas comparables T-16; elección del propietario T-13 y aceptación M1.
**Claude CLI:** ejecutar análisis de hallazgos sólo después del cierre real de M1; aún no invocado.

**GPU:** pruebas T-08 autorizadas y terminadas. Ollama vacío al inicio/final; contenedor QA retirado. Pico host6226MiB, poslimpieza1305MiB (root posterior1290).
Imagen Compose `engine-analysis:m0-t08-asr-cache` actualizada al producto validado3923255f; alias anterior conservado, sin arrancar servicios.
No certifica `spilled:false` ni benchmarkT09. Para otra fase GPU aplicar AGENTS§4.8 y un único modelo residente; no detener servicios ni borrar modelos.

**Demo:** http://127.0.0.1:3000/create · API8000, sólo mock CPU. Proyecto `music-studio-e2e-368b45c362fb`, tres servicios intactos.
Compose privado `.cache/dev-cycle/20261105-t16-readme/compose.demo.json`; conservar datos/imágenes previos y no resetear.
**Preservar:**71 archivos ajenos según `.cache/dev-cycle/20261106-m0-t08/initial.json`. No restaurar journals ni reactivar restos M2/almacenamiento.
No SQLite viva desde Windows ni helpers históricos GPU de `.cache/dev-cycle/t08/` o `t16/`.
**Git:** main sigue en `3dede62`; rama apilada sin integrar mientras T-16 esté abierta. Sólo stage explícito.
Evidencia actual: `.cache/dev-cycle/20261106-m0-t08/{qa,gpu/qa}/`; cuatro candidatos de conocimiento pendientes, sin promoción.
