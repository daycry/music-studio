# Decisiones (ADR)

Formato: `ADR-XXXX-slug.md` con **Estado** (propuesta · aceptada · sustituida por ADR-YYYY), **Fecha**, **Contexto**, **Decisión**, **Motivo / Consecuencias**. Cortas: una pantalla.

| ADR | Decisión | Estado |
|---|---|---|
| [0001](ADR-0001-reinicio-desde-cero.md) | Reinicio desde cero; la documentación anterior se archiva | aceptada |
| [0002](ADR-0002-personal-local-first.md) | Uso personal, local-first, un solo usuario, sin auth; cloud solo como alternativa opcional (ADR-0014) | aceptada |
| [0003](ADR-0003-stack.md) | Next.js + FastAPI (sin torch) + un engine GPU en contenedor por familia de modelo | aceptada |
| [0004](ADR-0004-sqlite-y-cola-propia.md) | SQLite (WAL, backup diario) y cola propia en el server | aceptada |
| [0005](ADR-0005-todo-en-la-carpeta.md) | Todo dentro de la carpeta (incluidas cachés); qué se sincroniza con Synology y qué no | aceptada |
| [0006](ADR-0006-seguridad-de-pesos.md) | Pesos: safetensors/GGUF/ONNX; pickle solo convertido con auditor; código remoto fijado; revisión y SHA-256 | aceptada |
| [0007](ADR-0007-gpu-local-12gb.md) | GPU 12 GB: un modelo en VRAM, proceso hijo para liberar, tope desde VRAM libre, ACE-Step tier 4 (LM 0.6B) | aceptada |
| [0008](ADR-0008-procedencia-y-linaje.md) | Manifiesto v1 por artefacto y linaje multi-padre desde la primera migración | aceptada |
| [0009](ADR-0009-formatos-y-loudness.md) | FLAC + MP3; WAV 48 kHz a demanda; loudness por destino; true peak con ffmpeg | aceptada |
| [0010](ADR-0010-ux-derivada-de-suno.md) | UX derivada de Suno y Sondo, identidad propia | aceptada |
| [0011](ADR-0011-seleccion-de-modelos.md) | ACE-Step 1.5 (2B turbo + LM 0.6B) principal; HeartMuLa alternativa (M5); no comerciales solo en laboratorio | aceptada (a confirmar en M0) |
| [0012](ADR-0012-llm-de-letras.md) | Asistente de letras: Gemma 4 12B local por defecto; Claude API opcional | aceptada |
| [0013](ADR-0013-cancion-como-proyecto.md) | La canción es el proyecto: takes, letra, portada, vídeo y exportaciones dentro de ella | aceptada |
| [0014](ADR-0014-local-por-defecto.md) | Local por defecto en todo; APIs/suscripciones solo como alternativa opcional, visible y registrada | aceptada |
| [0015](ADR-0015-video-musical-por-niveles.md) | Vídeo musical por niveles N0–N3 (letra/visualizador → guion gráfico → planos protagonistas → todo generativo) | aceptada (a validar) |
| [0016](ADR-0016-comfyui-como-motor-de-imagen-y-video.md) | ComfyUI headless como motor de imagen y vídeo, workflows versionados | aceptada (a validar) |
| [0017](ADR-0017-postproceso-y-manifiesto-en-el-server.md) | Engines devuelven salida cruda; post-proceso, manifiesto y render en el server (worker CPU) | aceptada |
| [0018](ADR-0018-cola-de-jobs.md) | Cola de jobs: carriles gpu/cpu/remote, prioridades, dependencias, reintentos, recuperación | aceptada |
| [0019](ADR-0019-contratos-code-first.md) | Contratos code-first: OpenAPI generado, `engine-contract` Pydantic, esquemas JSON versionados | aceptada |
| [0020](ADR-0020-seguridad-local.md) | Seguridad local: Host/Origin, puertos en 127.0.0.1, token de engines, subidas validadas | aceptada |
| [0021](ADR-0021-repositorio-publico.md) | Remoto público `daycry/music-studio` (todos los derechos reservados); código anterior en `archive/legacy-main`; auth con `gh`; merge ff a `main` por tarea | aceptada |
| [0022](ADR-0022-memoria-tecnica-kwipu-graphiti.md) | Memoria técnica en Kwipu (export) y Graphiti (`shadow`, grupo `music-studio`) como MCP locales; liberar la VRAM de Ollama antes de trabajar con GPU | aceptada |
| [0023](ADR-0023-primera-cancion-con-material-privado.md) | Primera canción de M0 con «Libre» como entrada privada; B-02 mantiene su definición en la evaluación | aceptada |
| [0024](ADR-0024-hashes-de-codigo-remoto-en-descriptores.md) | Campo opcional remote_code en el descriptor, con rutas relativas y SHA-256; ampliación compatible de /v1 | aceptada |
| [0025](ADR-0025-limite-de-memoria-wsl.md) | WSL con límite de 16 GB, swap de 8 GB y recuperación de caché dropCache; perfil elegido por el propietario y aplicado | aceptada |
| [0026](ADR-0026-comparacion-controlada-shift.md) | Comparación privada shift 1/3; parámetro opcional y default anterior conservado | aceptada |
| [0028](ADR-0028-preparacion-fiel-de-instrucciones.md) | Preparación determinista original/efectiva, limpieza explícita de Markdown en tags y recibo privado inmutable | aceptada |
| [0029](ADR-0029-presupuesto-operativo-de-texto-acestep.md) | Preflight offline con plantillas/tokenizadores fijados, política LM y reserva completa, metadata entrenada y captura privada de fronteras | aceptada |

## Decisiones heredadas de la documentación archivada

Las decisiones D-01…D-30 de [`../archive/…/spec.md`](../archive/roadmap-2026-07-27/2026-07-27-plataforma-musical-ia/spec.md) §2 **no están vigentes** salvo las recogidas explícitamente en un ADR de esta tabla («Hereda D-xx»).
