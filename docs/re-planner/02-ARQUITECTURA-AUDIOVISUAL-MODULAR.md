# Arquitectura audiovisual modular

## Objetivo arquitectónico

Separar dominio creativo, gestión de modelos y ejecución GPU para que:

- una canción pueda elegir modelo sin conocer hardware;
- un modelo pueda actualizarse sin migrar proyectos;
- una GPU pueda sustituirse o añadirse sin alterar workspaces;
- música y vídeo compartan jobs, assets, manifests y políticas;
- la RTX 5070 sea baseline, no dependencia estructural.

## Vista de contexto

```mermaid
C4Context
    title Contexto del estudio audiovisual local-first
    Person(user, "Creador", "Crea canciones y videoclips")
    System(studio, "Suno/Sondo Clone", "Estudio audiovisual por workspaces")
    System_Ext(hf, "Repositorios de modelos", "Hugging Face/GitHub, solo modo actualización")
    System_Ext(workers, "Workers RTX", "RTX 5070 local y RTX superiores")
    Rel(user, studio, "Usa", "HTTPS/loopback")
    Rel(studio, hf, "Descarga revisiones fijadas", "egress controlado")
    Rel(studio, workers, "Envía jobs y recibe artefactos", "protocolo autenticado")
```

## Vista de contenedores

```mermaid
flowchart TB
    subgraph Client[Cliente]
      WEB[Next.js Web]
    end

    subgraph Control[Control plane]
      API[FastAPI]
      DOMAIN[Domain Services]
      RESOLVER[Model Resolver]
      SCHED[Scheduler]
      POLICY[Policy Engine]
      MM[Model Manager]
      DB[(PostgreSQL)]
      CAS[(CAS Assets)]
    end

    subgraph WorkerLocal[Worker local RTX-12]
      AGENT[Worker Agent]
      HOST[Adapter Host]
      GPU[RTX 5070 / CUDA]
      CACHE[Model Cache RO]
    end

    subgraph WorkerRemote[Workers opcionales]
      AGENT2[Worker Agent]
      HOST2[Adapter Host]
      GPU2[RTX-16/24/32+]
    end

    WEB --> API
    API --> DOMAIN
    DOMAIN --> DB
    DOMAIN --> CAS
    DOMAIN --> RESOLVER
    RESOLVER --> POLICY
    RESOLVER --> MM
    RESOLVER --> SCHED
    SCHED --> DB
    MM --> DB
    MM --> CACHE
    SCHED --> AGENT
    SCHED --> AGENT2
    AGENT --> HOST
    HOST --> GPU
    HOST --> CACHE
    AGENT2 --> HOST2
    HOST2 --> GPU2
```

## Capas y dependencias

```mermaid
flowchart TD
    UI[Presentation] --> APP[Application Use Cases]
    APP --> DOMAIN[Domain]
    APP --> PORTS[Ports]
    ADAPTERS[Infrastructure Adapters] --> PORTS
    ADAPTERS --> UPSTREAM[Model Upstreams]
    WORKERS[Worker Runtime] --> ADAPTERS
    DOMAIN -. no depende .-> UPSTREAM
    DOMAIN -. no depende .-> WORKERS
```

Regla: el dominio no importa librerías de ACE-Step, Diffusers, ComfyUI, LTX, PyTorch o CUDA.

## Componentes

### Web / Next.js

Responsabilidades:

- navegación por workspace;
- creación y versionado musical;
- selector de `ModelProfile`;
- edición de letras y parámetros normalizados;
- brief, visual bible, storyboard y shots;
- revisión y aprobación de variantes;
- timeline básico;
- estados y errores explicables;
- reproducción y exportación.

No debe:

- construir comandos de inferencia;
- escoger un worker/GPU;
- leer rutas físicas;
- descargar pesos;
- deducir capacidades por el nombre del modelo.

### API / Application layer

Responsabilidades:

- autenticar contexto local cuando corresponda;
- validar `workspace_id`;
- aplicar casos de uso y transacciones;
- crear versiones inmutables;
- calcular selección efectiva;
- solicitar resolución de modelo;
- crear DAGs de jobs;
- exponer eventos y progreso;
- autorizar lectura/escritura de assets.

### Domain layer

Agregados principales:

```mermaid
classDiagram
    Workspace "1" --> "*" Song
    Workspace "1" --> "*" VideoProject
    Workspace "1" --> "*" Asset
    Song "1" --> "*" SongVersion
    SongVersion "1" --> "*" VideoProject : fuente fija
    VideoProject "1" --> "*" StoryboardVersion
    StoryboardVersion "1" --> "*" Shot
    Shot "1" --> "*" ShotVariant
    VideoProject "1" --> "*" TimelineVersion
    TimelineVersion "1" --> "*" VideoVersion
```

### Model Resolver

Convierte una solicitud creativa en un `ResolvedModelPlan`:

- aplica defaults y overrides;
- filtra por capability;
- comprueba canal, licencia y territorio;
- aplica compatibilidad con versión origen;
- selecciona release y perfiles de ejecución;
- no selecciona worker.

### Scheduler

Convierte un `ResolvedModelPlan` en una `PlacementDecision`:

- workers saludables;
- VRAM y RAM disponibles;
- runtime y compute capability;
- modelo instalado/cacheado;
- afinidad de assets;
- cola, temperatura y retención;
- límites de concurrencia;
- override administrativo explícito.

### Model Manager

- descubre candidatos;
- registra Model Packages;
- revisa política/licencias;
- descarga a staging;
- verifica hashes y formatos;
- ejecuta smoke y benchmark;
- publica perfiles y release sets;
- distribuye instalaciones a workers;
- promociona, depreca y revierte.

### PostgreSQL

Inicialmente contiene:

- dominio de producto;
- jobs, pasos, leases y eventos;
- model profiles, releases y políticas;
- worker registry y snapshots;
- referencias CAS;
- manifests y auditoría;
- decisiones de resolver y scheduler.

Redis se incorpora únicamente si una medición demuestra que la cola SQL o el bus de eventos no cumplen.

### Content-addressed storage

```mermaid
flowchart LR
    B[Blob
hash + bytes] --> A1[Asset ref
workspace A]
    B --> A2[Asset ref
workspace B]
    A1 --> L1[Lineage A]
    A2 --> L2[Lineage B]
```

El blob puede deduplicarse, pero la autorización se comprueba sobre `Asset`, no sobre el hash.

Clases:

```text
models/      pesos y runtimes globales, no pertenecen a workspaces
masters/     WAV/FLAC, imágenes y vídeo originales
approved/    versiones aprobadas y renders
proxies/     previews y thumbnails
rejected/    variantes descartadas con retención configurable
temporary/   staging y artefactos reconstruibles
manifests/   evidencia JSON, hashes y firmas opcionales
```

### Worker Agent

Máquina de estados:

```mermaid
stateDiagram-v2
    [*] --> registering
    registering --> idle: preflight válido
    registering --> quarantined: preflight inválido
    idle --> reserving: claim
    reserving --> preparing
    preparing --> loading
    loading --> running
    running --> persisting
    persisting --> unloading
    unloading --> idle
    running --> degraded: error recuperable
    running --> quarantined: CUDA/contexto corrupto
    idle --> draining: mantenimiento
    draining --> offline
```

Cada claim utiliza lease y heartbeat. Un archivo parcial no completa un paso.

### Adapter Host

Proceso o contenedor supervisado por familia/runtime. Recibe:

- solicitud normalizada;
- inputs temporales autorizados;
- model release read-only;
- execution profile;
- run context y cancel token.

No recibe:

- acceso directo a PostgreSQL;
- credenciales de repositorios;
- acceso global al CAS;
- egress durante inferencia.

## Flujo de generación musical

```mermaid
sequenceDiagram
    participant UI
    participant API
    participant Resolver
    participant Scheduler
    participant Worker
    participant Adapter
    participant CAS
    UI->>API: POST SongVersion generation
    API->>Resolver: capability + selection policy
    Resolver-->>API: ResolvedModelPlan
    API->>Scheduler: crear job/placement
    Scheduler->>Worker: claim con lease
    Worker->>Adapter: load + run
    Adapter-->>Worker: audio + metadata
    Worker->>CAS: staging, validate, promote
    Worker-->>API: ModelRun + hashes + metrics
    API-->>UI: SongVersion disponible
```

## DAG audiovisual

```mermaid
flowchart TD
    IA[INGEST_AUDIO] --> AA[ANALYZE_AUDIO]
    IA --> AL[ALIGN_LYRICS]
    AA --> VP[BUILD_VISUAL_PLAN]
    AL --> VP
    VP --> KF[GENERATE_KEYFRAMES x N]
    KF --> CL[GENERATE_CLIPS x N]
    CL --> LS[APPLY_LIPSYNC selectivo]
    CL --> PR[BUILD_PREVIEW]
    LS --> PR
    PR --> AP{Aprobación}
    AP -->|regenerar shot| KF
    AP -->|aprobar| RF[RENDER_FINAL]
    RF --> EX[EXPORT_DERIVATIVES]
```

Cada `JobStep` declara:

- inputs por hash;
- capability y contract version;
- `ResolvedModelPlan` o runtime determinista;
- requisitos hardware;
- idempotency key;
- outputs esperados;
- dependencias;
- retry y cancelación;
- invalidez descendente.

## Residencia de modelos en RTX-12

```mermaid
sequenceDiagram
    participant Worker
    participant Music
    participant Image
    participant Video
    participant LipSync
    Worker->>Music: cargar y generar audio
    Music-->>Worker: descargar VRAM
    Worker->>Image: cargar y generar keyframes
    Image-->>Worker: descargar VRAM
    Worker->>Video: cargar y generar clips
    Video-->>Worker: descargar VRAM
    Worker->>LipSync: cargar y procesar planos
    LipSync-->>Worker: descargar VRAM
```

No se asume que dos modelos pesados caben simultáneamente.

## Seguridad de red

### Instalación local

```mermaid
flowchart LR
    USER[Browser] -->|loopback/LAN explícita| WEB[Web/API]
    WEB --> DB[(PostgreSQL interno)]
    WEB --> WORKER[Worker interno]
    UPDATE[Update mode] --> INTERNET[Repos oficiales]
    WORKER -. egress denegado .-> INTERNET
```

- servicios internos no se publican salvo necesidad;
- modo actualización separado del modo inferencia;
- descargas fijadas y verificadas;
- modelos montados read-only;
- secretos fuera de logs y manifests públicos.

### Multiworker

- enrolment explícito;
- mTLS o túnel autenticado equivalente;
- identidad revocable;
- worker inicia conexión cuando sea viable;
- transferencia por hashes y scopes de job;
- CAS local/cache remota sin acceso global indiscriminado.

## Recuperación e idempotencia

```mermaid
flowchart TD
    CLAIM[Claim con lease] --> RUN[Ejecutar paso]
    RUN --> STAGE[Persistir en staging]
    STAGE --> VAL[Validar formato/hash]
    VAL --> PROMOTE[Promoción atómica]
    PROMOTE --> COMPLETE[Marcar JobStep completado]
    RUN -->|crash| EXPIRE[Expira lease]
    EXPIRE --> RECON[Reconciliar]
    RECON --> RETRY[Reintentar idempotentemente]
```

- uploads y outputs usan staging;
- pasos completados son inmutables;
- restart reconstruye DAG desde PostgreSQL;
- un adapter roto provoca reciclaje del proceso;
- el render final no sobrescribe masters;
- los jobs persistentes conservan selección solicitada, plan resuelto y placement.

## Despliegue inicial

```mermaid
flowchart TB
    subgraph Compose[Docker Compose]
      WEB[web]
      API[api]
      DB[postgres]
      MM[model-manager]
      WORKER[worker-local]
    end
    V1[(db volume)] --> DB
    V2[(asset CAS)] --> API
    V3[(model cache)] --> MM
    V3 --> WORKER
```

Windows hospeda el driver NVIDIA; WSL2/Docker ejecuta runtimes fijados. Los árboles I/O intensivos pueden residir en filesystem Linux/volumen dedicado si el benchmark muestra penalización en `/mnt/c`.

## Evolución

### Añadir modelo

```mermaid
flowchart LR
    PKG[Model Package] --> AD[Adapter Release]
    AD --> PROFILE[ModelProfile]
    PROFILE --> BENCH[Benchmark profile]
    BENCH --> CAND[candidate]
    CAND --> STABLE[stable]
```

No cambia el dominio.

### Añadir o sustituir GPU

```mermaid
flowchart LR
    NEW[GPU nueva] --> PF[Preflight]
    PF --> WS[WorkerSnapshot]
    WS --> BM[Benchmark]
    BM --> REG[Registry]
    REG --> SCHED[Placements nuevos]
```

No cambia ningún workspace, Song o VideoProject.
