# Perfiles RTX, scheduler y multiworker

## Baseline

La referencia inicial es **GeForce RTX 5070 desktop con 12 GB GDDR7**, arquitectura Blackwell, compute capability 12.0, Tensor Cores de quinta generación y NVENC de novena generación. El producto la trata como baseline medido `RTX-12`, no como requisito de identidad para canciones o workspaces.

```mermaid
flowchart LR
    PRODUCT[Producto] --> PROFILES[Perfiles de modelo]
    PROFILES --> SCHED[Scheduler]
    SCHED --> RTX12[RTX-12 baseline]
    SCHED --> RTX16[RTX-16]
    SCHED --> RTX24[RTX-24]
    SCHED --> RTX32[RTX-32+]
```

## Principio de clasificación

Los perfiles se asignan por capacidad medida:

- VRAM utilizable;
- compute capability;
- dtypes y kernels soportados;
- driver/runtime;
- RAM y disco;
- temperatura y potencia;
- benchmark de cada execution profile.

No basta con `gpu_name`.

## Perfiles iniciales

### RTX-12

Referencia: RTX 5070 desktop 12 GB.

- una tarea GPU pesada simultánea;
- un modelo pesado residente cada vez;
- preview antes de final;
- offloading y cuantización solo si están aprobados;
- música completa;
- keyframes ligeros;
- vídeo por planos cortos;
- lip-sync ligero;
- render NVENC.

### RTX-16

- modelos de imagen/vídeo con menos offload;
- rutas audiovisuales mayores si pasan benchmark;
- una tarea pesada por defecto;
- mayor resolución o duración de preview.

### RTX-24

- modelos musicales y de vídeo mayores;
- menor dependencia de offloading;
- lip-sync avanzado;
- posible concurrencia controlada si se mide.

### RTX-32+

- modelos audiovisuales grandes;
- batch y calidad superior;
- concurrency policy basada en benchmark;
- no implica que cualquier modelo esté autorizado.

## WorkerSnapshot

```yaml
worker_id: studio-pc-01
hostname: studio-pc-01
status: idle
gpu:
  name: NVIDIA GeForce RTX 5070
  uuid: GPU-...
  compute_capability: "12.0"
  vram_total_mb: 12288
  vram_free_mb: 11720
runtime:
  driver_version: ...
  cuda_runtime: ...
  pytorch_version: ...
  supports_fp16: true
  supports_bf16: true
  supports_tf32: true
health:
  temperature_c: 45
  disk_free_gb: 620
  heartbeat_at: ...
capacity:
  worker_profile: RTX-12
  max_heavy_gpu_jobs: 1
installed_releases: []
```

El snapshot es temporal. No se copia a `Song`; se referencia desde `PlacementDecision`/`ModelRun`.

## Registro del worker

```mermaid
sequenceDiagram
    participant Worker
    participant Control as Control Plane
    participant Registry
    participant Scheduler
    Worker->>Worker: preflight
    Worker->>Control: enrolment + identity proof
    Control->>Registry: registrar Worker
    Worker->>Control: WorkerSnapshot + heartbeat
    Control->>Scheduler: actualizar disponibilidad
    Scheduler-->>Worker: claims compatibles
```

## Requisitos de un job

```yaml
job_requirements:
  capability: video.generate.image_to_video
  resolved_model_release_id: video.ltxvideo.2b...
  allowed_execution_profiles:
    - ltxv2b-fp8-rtx12
    - ltxv2b-bf16-rtx16
  minimum_vram_free_mb: 10500
  disk_required_mb: 25000
  expected_duration_seconds: 420
  asset_hashes: []
  heavy_gpu_slots: 1
```

No contiene una GPU concreta salvo override administrativo.

## Placement

```mermaid
flowchart TD
    J[JobRequirements] --> W[Workers healthy]
    W --> P[Profile compatible]
    P --> R[Runtime/driver compatible]
    R --> M[Model installed o installable]
    M --> V[VRAM/RAM/disk guardas]
    V --> T[Temperatura y slots]
    T --> A[Afinidad de assets/modelo caliente]
    A --> Q[Longitud de cola]
    Q --> D[PlacementDecision explicable]
```

### Ejemplo de decisión

```yaml
placement_decision:
  worker_id: studio-pc-02
  reasons:
    - execution_profile_validated
    - model_already_cached
    - lower_queue_time
  rejected_workers:
    - worker_id: studio-pc-01
      reasons: [insufficient_free_vram_for_requested_profile]
```

## Afinidad sin acoplamiento

El scheduler puede preferir:

- worker con modelo ya cargado;
- worker con assets cacheados;
- worker local;
- worker más rápido;
- worker con mejor benchmark.

Preferir no significa fijar. La preferencia no se persiste en `Song`.

## Sustitución de GPU

```mermaid
stateDiagram-v2
    idle --> draining: iniciar cambio
    draining --> offline
    offline --> hardware_changed
    hardware_changed --> registering: reiniciar worker
    registering --> benchmarking
    benchmarking --> idle: perfiles aprobados
    benchmarking --> quarantined: fallo
```

Proceso:

1. drenar jobs;
2. apagar worker;
3. sustituir GPU/driver;
4. ejecutar preflight;
5. crear nuevo hardware snapshot;
6. invalidar benchmarks hardware-bound anteriores;
7. ejecutar smoke/benchmark de release sets;
8. publicar capabilities;
9. reabrir claims.

No se modifican workspaces ni versiones.

## Multiworker

```mermaid
flowchart TB
    CP[Control Plane] --> DB[(PostgreSQL)]
    CP --> CAS[(CAS central o federado)]
    CP --> S[Scheduler]
    S --> W1[PC 1 RTX-12]
    S --> W2[PC 2 RTX-16]
    S --> W3[PC 3 RTX-24/32]
    W1 <-->|hashes/artefactos| CAS
    W2 <-->|hashes/artefactos| CAS
    W3 <-->|hashes/artefactos| CAS
```

### Protocolo

- enrolment explícito;
- identidad de dispositivo;
- mTLS;
- heartbeat;
- leases;
- transferencias resumibles;
- verificación SHA-256;
- scopes por job;
- revocación;
- caché local de modelos/assets.

## Transferencia de assets

```mermaid
sequenceDiagram
    participant Scheduler
    participant Worker
    participant CAS
    Scheduler->>Worker: claim con hashes requeridos
    Worker->>CAS: HEAD por hash
    CAS-->>Worker: disponibilidad/tamaño
    Worker->>CAS: GET resumible faltantes
    Worker->>Worker: verificar SHA-256
    Worker-->>Scheduler: ready
```

Nunca se confía en el nombre del archivo como identidad.

## Precisión y Tensor Cores

La RTX soporta hardware moderno, pero el uso efectivo depende de adapter/modelo/runtime.

Política:

- BF16 cuando esté soportado y validado;
- FP16 como alternativa;
- TF32 solo para operaciones FP32 compatibles y medido;
- FP8/NVFP4 solo con ruta oficial/validada;
- INT8/INT4 solo si la degradación y compatibilidad son aceptables;
- ningún fallback silencioso.

```mermaid
flowchart TD
    EP[ExecutionProfile] --> HW{Hardware soporta dtype?}
    HW -->|no| REJECT[No elegible]
    HW -->|sí| AD{Adapter/modelo soporta?}
    AD -->|no| REJECT
    AD -->|sí| BM{Benchmark aprobado?}
    BM -->|no| LAB[solo lab]
    BM -->|sí| OK[elegible]
```

## Política térmica y de recursos

- umbral preventivo;
- enfriamiento entre lotes si procede;
- cancelación ordenada;
- disco mínimo antes de claim;
- RAM/swap guardadas;
- máximo de duración;
- watchdog del contexto CUDA;
- reciclaje de adapter tras OOM severo.

## Determinismo entre GPUs

No se promete identidad bit a bit entre GPUs/runtimes distintos. Se promete:

- registrar seed y parámetros;
- fijar release/runtime;
- detectar cambios;
- medir regresión perceptual y funcional;
- conservar el output original.

```mermaid
flowchart LR
    SAME[Same request/release/seed] --> G1[GPU A]
    SAME --> G2[GPU B]
    G1 --> O1[Output A]
    G2 --> O2[Output B]
    O1 --> CMP[Comparación técnica/perceptual]
    O2 --> CMP
```

## Matriz de soporte

| Worker profile | Capability | Model release | Execution profile | Estado | Evidencia |
|---|---|---|---|---|---|
| RTX-12 | music.generate.full_song | fijado | BF16/FP16 + offload | lab/candidate/stable | benchmark URI |
| RTX-12 | video.generate.image_to_video | fijado | FP8/BF16 | lab/candidate/stable | benchmark URI |
| RTX-16 | video.generate.audio_to_video | fijado | según modelo | lab/candidate | benchmark URI |
| RTX-24 | lipsync avanzado | fijado | BF16/FP16 | lab/candidate | benchmark URI |

La matriz es el producto de pruebas reales, no una declaración manual sin evidencia.
