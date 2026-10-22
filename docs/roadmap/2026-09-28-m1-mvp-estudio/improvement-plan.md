---
storage_durable_design: storage-durable-design.md
design: design.md
test-plan: test-plan.md
generacion:
  fuente: estimado        # redactado a mano el 2026-09-28; sin usage-meter
---

# 2026-09-28-m1-mvp-estudio

> M1: MVP del estudio web sobre el motor de M0 (canción = proyecto, generación en vivo, biblioteca, reproductor).

> Despliegue elegido por el propietario el 2026-10-06: web, server y engines en Docker Compose; Ollama compartido en WSL2 detrás de un adaptador sin inferencia propia en M2. [ADR-0035](../../decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md). Implementación pendiente; no cambia el alcance funcional de M1.

| | |
|---|---|
| **Fecha** | 2026-09-28 |
| **Estado** | borrador |
| **Tipo** | Nueva Funcionalidad |
| **Prioridad** | Alta |
| **Solicitante** | Propietario |
| **Responsable** | Propietario (con IA) |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | n/a: proyecto personal ([ADR-0001](../../decisiones/ADR-0001-reinicio-desde-cero.md)) |
| **Diseño** | [Avance técnico condicionado](design.md), [ADR-0037](../../decisiones/ADR-0037-avance-tecnico-condicionado.md) |

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|---|---|---|---|
| Tiempo humano | **153 h** | 0 h | Media |
| Tareas | **17** | 0 hechas | — |

## Fases

| Fase | Tareas | Estimado (h) | Resultado |
|---|---|---|---|
| Fase 0 — Secuenciación | T-00 | — | Gates técnicos y finales explícitos, sin horas retrospectivas inventadas |
| Fase 1 — Server base | T-01…T-03 | 20 | Server seguro, esquema completo, contratos exportados |
| Fase 2 — Cola y post-proceso | T-04…T-06 | 26 | Dispatcher con carriles y dependencias, worker CPU y SSE |
| Fase 3 — API de dominio | T-07 | 12 | Canciones, takes, letras, generaciones, colecciones y sistema |
| Fase 4 — Web | T-08…T-14 | 86 | Infra E2E, crear, generación en vivo, biblioteca, vista de canción, reproductor y sistema (cada tarea con su E2E) |
| Fase 5 — Pruebas y cierre | T-15, T-16 | 9 | Suite E2E estable y README de puesta en marcha |

**Paralelismo:** una vez cerrada la Fase 1, la Fase 4 (web contra `engine-mock` y los tipos generados) puede avanzar en paralelo con las Fases 2 y 3.

## Cómo se ejecuta

Con `/dev-cycle docs/roadmap/2026-09-28-m1-mvp-estudio`. La spec ya está aprobada y el plan escrito, así que se salta directamente a la implementación. `qa` ejecuta [`test-plan.md`](test-plan.md) con Playwright contra `http://127.0.0.1:3000` y `engine-mock`. **Apertura técnica condicionada:** tras revisión/QA documental de ADR-0037, se puede construir y probar contra mock con las dependencias técnicas satisfechas. **Aceptación final:** M0/T-13 cerrado, capacidades reales verificadas y todas las pruebas reales/manuales exigidas; no se cierra una tarea con su criterio propio pendiente.

## Riesgos del plan

Los E2E arrancan web, server y `engine-mock` con Docker Compose. El navegador usa las URLs publicadas en `127.0.0.1`; el server resuelve el mock por nombre interno. Se validan SQLite persistente, migraciones y FFmpeg LGPL Linux. Ollama no es requisito de las pruebas M1.

| Riesgo | Mitigación |
|---|---|
| SSE y `Range` entre navegador y API en Docker | El navegador usa la API publicada en `127.0.0.1:8000`; los contenedores usan nombres internos y listas explícitas de Host/Origin. Verificar SSE sin buffering y Range ([convenciones.md](../../arquitectura/convenciones.md)) |
| El esquema completo en la primera migración parece sobredimensionado | Es deliberado: las tablas vacías no cuestan nada y así se evitan migraciones rompedoras en M2–M5 |
| Varios engines en marcha a la vez se reparten la VRAM | Dispatcher con `unload` entre engines y comprobación de la VRAM libre en `/v1/health` ([ADR-0007](../../decisiones/ADR-0007-gpu-local-12gb.md)) |
| Persistencia o FFmpeg no funcionan al pasar el server a Linux | Verificar SQLite WAL tras recrear el contenedor, migraciones y build LGPL Linux fijada; no usar binarios Windows dentro de Docker ([ADR-0035](../../decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md)) |


## Secuencia acotada de T-05 tras ADR-0055

[ADR-0055](../../decisiones/ADR-0055-ejecucion-cpu-y-publicacion-durable-por-toma.md) fija publicación independiente por toma dentro de la cadena agregada. U1 portable tiene aceptación técnica acotada; U2a será contrato/migración/snapshots, sin procesos ni FS publication. Siguen captura de procedencia/roles, custodia nativa del hijo, publicación/reconciliación y análisis/runtime compartido CPU2. Cada unidad mantiene TDD, revisión fresca y QA; pruebas reales Docker/E2E y calidad siguen pendientes. El ledger es la única fuente de estado.


## Secuencia acotada T-06

Con [ADR-0056](../../decisiones/ADR-0056-sse-con-buffer-y-recuperacion-de-estado.md), primero bus/framing acotados y sus tests de comportamiento, luego API-contract antes de routing y credencial pública, integración transaccional de escritores/snapshot, cliente y E2E. Conserva los tests y autoridades T-04; no usa el token engine en navegador. La aceptación completa queda en los criterios del ledger.

La [preparación de integración](testing/t06/integration-readiness.md) identifica
las conexiones pendientes, los escritores participantes y las pruebas de
consistencia WAL/reconexión. Se ejecutará después de liberar la propiedad de la
unidad de procedencia sintética, sin modificar sus fuentes en paralelo.


## Captura de procedencia antes de la publicación CPU

[ADR-0060](../../decisiones/ADR-0060-captura-write-once-de-procedencia-antes-del-envio.md) fija O2: snapshot seleccionado inmutable y primera captura tras load/Health fresco, antes de submit, sin backfill histórico. La próxima unidad implementa seis módulos de cola y sus tests; respeta la propiedad de fuentes y las verificaciones SSE activas. Es prerrequisito de las revisiones de publicación, no evidencia de worker completo.

## Almacenamiento operativo

[ADR-0089](../../decisiones/ADR-0089-reencauce-tras-codex.md) aparca el VHDX ext4 y el journal Windows de ADR-0069/0075. Los datos viven en `data/`, montado en los contenedores. Cada take se publica así:

1. Se escribe en un directorio de staging.
2. Se mueve con `rename` normal a `data/songs/<song_id>/<take_ulid>/`. El id es único, así que no hay colisión y no hace falta `NOREPLACE`.
3. Se confirma la fila en SQLite. Esa fila es la autoridad: un directorio sin fila es huérfano y se limpia al arrancar.
