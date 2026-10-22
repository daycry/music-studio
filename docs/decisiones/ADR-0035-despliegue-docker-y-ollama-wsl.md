# ADR-0035 · Despliegue Docker Compose y Ollama compartido en WSL2

- **Estado:** aceptada por el propietario · **Fecha:** 2026-10-06 · **Implementación:** pendiente
- **Validez:** sustituye la ejecución nativa de web/server de [ADR-0003](ADR-0003-stack.md) y el backend llama.cpp propio de [ADR-0012](ADR-0012-llm-de-letras.md). Conserva sus contratos y el alcance funcional de los hitos.

## Contexto

El propietario elige que el producto se despliegue en Docker, con una excepción: Ollama permanece en Ubuntu WSL2 porque también sirve a otras aplicaciones. music-studio es cliente de ese servicio compartido y no su propietario. Esta decisión registra el despliegue objetivo; no acredita contenedores, conectividad ni ejecución GPU completados.

Docker Desktop utiliza su backend WSL2: ComfyUI en un contenedor Linux también corre sobre WSL2 y puede acceder a la RTX mediante CUDA. No requiere instalar otro ComfyUI nativo en Ubuntu. [Documentación oficial de Docker](https://docs.docker.com/desktop/features/gpu/).

## Decisión

- **Docker Compose:** web Next.js, server FastAPI y los engines. El server sigue sin torch y contiene el dispatcher y el worker CPU para FFmpeg, post-proceso, manifiestos, render y backups. SQLite WAL permanece en almacenamiento persistente dentro del proyecto; solo el server escribe en la BD.
- **Engines locales:** música y análisis mantienen sus contenedores por familia. ComfyUI headless corre en su contenedor con CUDA y acceso a la RTX 5070, conforme a [ADR-0016](ADR-0016-comfyui-como-motor-de-imagen-y-video.md). Su integración y validación GPU siguen pendientes en sus hitos.
- **Letras y guion:** `engine-llm` es un adaptador Docker del contrato `/v1` hacia el Ollama existente en Ubuntu WSL2. No hace inferencia propia ni posee un proceso CUDA o almacén de modelos adicional. Ollama realiza la inferencia. La elección y validación del modelo de letras se resuelve en M2; esta decisión no elige un modelo nuevo.
- **Cola:** se conserva [ADR-0018](ADR-0018-cola-de-jobs.md): tablas `job` y `job_dependency` en SQLite, carril `gpu` con concurrencia 1 y `cpu` con concurrencia 2. `remote` sigue siendo opcional y desactivado por defecto. No se añaden Kafka ni Redis. El vídeo mantiene un job por plano.
- **Residencia GPU:** un solo modelo residente, también al usar Ollama. Los engines con inferencia propia mantienen el proceso hijo y `POST /v1/unload`. En el adaptador LLM, `unload` descarga el modelo en Ollama y comprueba su ausencia y la recuperación de VRAM; no termina el servicio externo. Antes de un trabajo GPU se observa qué modelos están cargados y se descargan los que impiden el turno. Al terminar solo se restauran los modelos observados previamente y descargados por esta operación. Si Ollama estaba vacío, permanece vacío. Nunca se para su servicio ni se borran modelos ([ADR-0022](ADR-0022-memoria-tecnica-kwipu-graphiti.md)).
- **Convivencia:** no se presume exclusión implementada con aplicaciones ajenas. Antes de cargar y durante el trabajo se comprueban los controles de residencia y VRAM disponibles. Si otro consumidor vuelve a ocupar la GPU, se espera o se devuelve un error observable; un bloqueo local del estudio no bloquea globalmente Ollama.
- **Red local:** los puertos publicados al host se limitan a `127.0.0.1`. Entre contenedores se usan nombres de servicio y puertos internos. La comunicación del adaptador a Ollama es una llamada local autorizada, no descarga de pesos ni acceso cloud. El destino privado Docker→WSL2 y sus controles se validan en M2 sin exponer Ollama a la LAN; no se da por probado un endpoint concreto.
- **Seguridad y datos:** se conservan `/v1`, token de engines, `Host`/`Origin`, rutas y pesos verificados, ejecución sin descargas y el server como único escritor de BD y manifiestos. La excepción a «todo dentro del proyecto» se limita al servicio Ollama preexistente y compartido; no autoriza trasladar datos del estudio ni crear otro almacén de pesos fuera de la carpeta. Los modelos que use el estudio siguen sujetos a fijación, hash y licencia de [ADR-0006](ADR-0006-seguridad-de-pesos.md).

## Alternativas descartadas

| Alternativa | Motivo |
|---|---|
| Web y server nativos, engines Docker | El propietario elige Docker para el despliegue del producto. |
| Dockerizar otro Ollama o ejecutar llama.cpp dentro de `engine-llm` | Duplica la inferencia y no conserva el servicio compartido elegido. |
| Kafka o Redis para la cola | La cola local existente cubre carriles, dependencias y recuperación sin nueva infraestructura. |

## Consecuencias y validación pendiente

- M1 debe empaquetar web/server, ejecutar migraciones y persistir SQLite en Compose; incorporar FFmpeg LGPL Linux fijado y resolver nombres internos, hosts permitidos, CORS, SSE y `Range`.
- Los E2E de M1 usan `engine-mock` en Docker y no requieren GPU ni Ollama. El navegador conserva URLs de host en `127.0.0.1`; el server usa direcciones internas de Compose.
- M2 debe validar conectividad privada a Ollama, `text.generate`, cancelación, eventos, descarga y convivencia real sin gestionar el servicio ajeno.
- M3–M4 validan ComfyUI CUDA y sus workflows. La decisión no acredita calidad, rendimiento ni capacidad de VRAM.
- Los comandos nativos pueden seguir como herramientas de desarrollo; ya no constituyen el criterio de despliegue del producto.

## Documentos afectados

[Constitución](../CONSTITUTION.md) · [Sistema](../arquitectura/sistema.md) · [Diagramas](../arquitectura/diagramas.md) · [Entorno](../arquitectura/entorno.md) · [Spec M1](../roadmap/2026-09-28-m1-mvp-estudio/spec.md) · [Plan M1](../roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md) · [Pruebas M1](../roadmap/2026-09-28-m1-mvp-estudio/test-plan.md)
