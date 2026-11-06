# Continuar aquí

2026-11-06 · Entrega T-16: `m0/t-16-tomas-comparables`, CPU `b642b58`, sobre T-09 `fc7f0ed` y software `f7d7c39`.
Estado canónico: [M0](docs/roadmap/2026-09-28-m0-entorno-y-motor/tasks.md) y [M1](docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md). M2/M3 congelados: ADR-0089.

**T-16 cerrada técnicamente.** Fix CPU `b642b58`: A/B sin hallazgos, QA478 pass/10 skip, delta15/15=100 %; QA final62/62 sin gaps.
GPU posterior: seis tomas90 s válidas, **3/3 parejas con códigos LM efectivos iguales** y60 checks conformes. Turbo8/SFT50/CFG7, LM0.6B BF16/PT; sin ganador musical.
Raw `.cache/dev-cycle/20261106-m0-t16/gpu-pairs/qa-seeded/`; hoja nueva `listening/listen.html`. Ensayo previo0/3 intacto en `qa/`; diagnóstico yfix preservados.
Software T-16 aceptado en CPU: 437 pass/9 skip. No recertificar audios históricos sin observaciones; validar los recibos nuevos con índice 0/1/2.
**GPU:** T-16 terminó con Ollama vacío/GPU 1.298 MiB, inicio1.297. Imagen `86e0e7aa` validada y alias Compose `engine-acestep:m0-t05` actualizado; QA retirado/demo intacta.

**T-09 cerrada y subida:** `fc7f0ed`; tres jobs reales de120 s, `spilled:false`, máximo host 9.394 MiB; A/B y QA aprobadas.
[Benchmark](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/benchmark-basico-2026-11-06.md). El guard no certifica ausencia absoluta de paginación WSL.
**T-08 cerrada:** CPU 48+1 pass, GPU 4 pass/0 skip; A/B y QA aprobadas, sin cambios de producto.
**Abierto:** M0 tiene17 completadas/3 canceladas; sólo T-13 pendiente. M1 tiene15 completadas/2 canceladas; T-16 depende de T-13, capacidad verificada y canción real desde web/escucha.
**T-13 en curso:** el propietario ya escuchó y rechaza las seis tomas por falta de sincronía voz/música y distancia con Suno; sin modelo aceptado. [Búsqueda ampliada: 18 opciones](docs/roadmap/2026-09-28-m0-entorno-y-motor/testing/modelos-locales-t13-2026-11-06.md): viabilidad Music3/HeartMuLa, ACE LM mayor/XL como controles; sin pesos nuevos ni GPU. Separar generación libre de cover. No repetir la petición de esa escucha. Claude CLI sólo tras cierre real de M1.

**Demo:** http://127.0.0.1:3000/create · API8000, sólo mock CPU. Proyecto `music-studio-e2e-368b45c362fb`, tres servicios intactos.
Compose privado `.cache/dev-cycle/20261105-t16-readme/compose.demo.json`; conservar datos e imágenes previos.
**Preservar:** 71 archivos ajenos y68 fuentes según `.cache/dev-cycle/20261106-m0-t16/gpu-pairs/initial.json`; no restaurar journals ni reactivar M2/almacenamiento.
No SQLite viva desde Windows ni ejecutar/importar helpers históricos GPU de `.cache/`.
**Git:** investigación actual en `m0/t-13-escucha-y-modelo`; T-13 abierta, sin merge a `main`. Entrega T-16 previa en `main`, SHA y push en `.cache/dev-cycle/20261106-m0-t16/gpu-pairs/final-validation.json`. Sólo stage explícito.
Limpieza: 55 contenedores,30 referencias antiguas de imágenes,6 copias de revisión (128 MB) y214 temporales pytest (1,47 GB) retirados; motor sustituido eliminado. Recibos `.cache/cleanup/20261106/`; copia adicional T-16 retenida por bloqueo automático.
Modelos: 65,50 GB con caché; el propietario solicita borrarlos. La revisión automática rechazó el borrado («blocked by policy»); siguen presentes. Conservar lock; Ollama fuera del alcance.
