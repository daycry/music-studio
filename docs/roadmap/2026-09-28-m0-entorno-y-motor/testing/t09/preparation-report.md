# T-09 — prerrequisitos del benchmark

Fecha: 2026-10-06. Investigación de solo lectura, con contexto reutilizado declarado. No se ejecutaron modelos, GPU, Docker, audio, instalaciones, descargas ni benchmarks. T-09 sigue en borrador; estos resultados preparan su implementación y no acreditan ningún criterio de rendimiento.

## Interfaces y medidas

La factoría de ACE-Step selecciona checkpoint y LM por variables de entorno (`engine_acestep.py:11–19`). La API `/v1` existente permite consultar identidad y estado, cargar, generar, observar eventos y descargar el hijo. La CLI actual fija BF16 cuando está disponible y no expone selección de modo/checkpoint/LM (`scripts/generate.py:43–70/467–468`). El benchmark debe registrar la configuración real enviada, junto con los recibos nativos, en vez de inferirla del nombre del candidato.

La telemetría actual distingue `load_s`, pero **`run_s` incluye la carga** (`engine_common/server.py:225–251`). Un job con modelo previamente cargado registra `load_s=0`; el tiempo total de CLI incluye además preflight, red, postproceso y publicación. Hay que definir relojes y condiciones frío/caliente antes de calcular RTF, y distinguir la inferencia de otros costes. Restar carga del tiempo total no constituye una medición directa de inferencia.

## Inventario observado

| Configuración prevista | Evidencia local | Pendiente |
|---|---|---|
| Turbo + LM 0.6B | Pesos presentes, tamaños y sellos vigentes | Medición de matriz |
| Turbo + LM 1.7B | Pesos presentes, tamaños y sellos vigentes | Medición y configuración efectiva del LM |
| SFT | Pesos presentes, tamaños y sellos vigentes | T-16 permanece abierta; medición nueva |
| Base | Pesos presentes, tamaños y sellos vigentes | Identidad/defaults/perfil propios antes de medir |
| XL-turbo | Cuatro shards fijados en lock, ausentes | Disponibilidad y modo compatible con 12 GB |

VAE y embedding compartidos están presentes con sellos vigentes. El inventario consultó JSON, tamaños y fechas: **no volvió a leer ni hashear los pesos grandes**. Los sellos conservan una verificación anterior; no prueban inferencia ni calidad.

El descriptor y adaptador actuales distinguen SFT y Turbo; los demás checkpoints reciben identidad y límites de Turbo (`descriptor.py:19–20/83–88`, `adapter.py:313–319`). Seleccionar base o XL mediante entorno todavía no basta para acreditar un perfil, recibo y manifiesto coherentes. Resolver ese requisito antes de comparar esas filas; no declarar un candidato medido por tener archivos disponibles.

## Almacenamiento, modos y spill

El montaje actual es de solo lectura y no existe aún selector bind/copia interior. Los dos brazos deben conservar lock, recursos y verificación equivalentes, registrando por separado copia, carga inicial y carga caliente. Controlar o declarar el efecto de la caché; no atribuir una diferencia a WSL si las condiciones no son comparables. La regla de abrir ADR si la diferencia supera 30 s sigue vigente.

Offload sí está expuesto. INT8 y `torch.compile` están desactivados en el adaptador actual (`adapter.py:290–302/485`). El script de benchmark no debe activar esos modos de forma oculta; necesitan soporte explícito, recibos coherentes y validación antes de medir.

La heurística de `spilled` (`engine_common/runtime.py:41–55`) no mide directamente memoria GPU compartida de Windows. NVML agregado, RAM de WSL y swap describen ámbitos diferentes; `spilled=false` no acredita sharedGPU cero. Falta instrumentar una referencia RTF y obtener una observación verificable de memoria compartida, conforme al criterio del Administrador de tareas. Offload voluntario debe distinguirse del desbordamiento accidental.

Antes de cualquier medición GPU siguen vigentes Ollama descargado por modelo, baseline de aproximadamente 1.600 MiB y navegador abierto. No se amplían las excepciones anteriores ni se cierran aplicaciones del propietario. Descarga y cleanup deben identificar exclusivamente el hijo/job propios.

## Evidencia y siguiente paso

Informe privado: `.cache/dev-cycle/t09/preparation/research.md`. Inventario: `.cache/dev-cycle/t09/preparation/weights-metadata.json`. La investigación forma parte del lote de trabajo abierto, sin ventana individual ni consumo IA medido. No ofrece números de rendimiento ni una recomendación de calidad.

Preparar el brief de implementación resolviendo explícitamente identidad base/XL, límites/modos, relojes de medición, comparación de almacenamiento y observación de spill. Mantener las duraciones 30/60/180/300 s, la matriz completa y su Verificación declarada. No sustituirlas por un dry-run ni por la comparación artística T-16. El estado permanece exclusivamente en `tasks.md`.
