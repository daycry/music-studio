**Lente A — inspección de componente U1 nº 2: 0 Critical / 0 Important / 0 Minor pendientes en el alcance revisado.** No implica cierre de T-04: sigue `en-progreso`, con ocho CA abiertos. La revisión formal de integración nº 4 permanece pendiente.

Las rutas abreviadas corresponden a `apps/server/app/queue/` y `apps/server/tests/`.

| T-04 → criterio de aceptación | Resultado | Evidencia fichero:línea |
|---|---|---|
| CA1: GPU1/CPU2, prioridad/FIFO, `not_before`, CPU sin descargar GPU | ✓ Conforme en U1; integración pendiente | `admission.py:96,113,120,184`; `dispatcher.py:36,51`; `test_dispatcher_admission.py:91,101,263,282,574` |
| CA2: protocolo de nueve operaciones y HTTP `/v1` | ✓ Transporte implementado; consumo integrado pendiente | `backends/protocol.py:48`; `backends/http.py:136`; `test_queue_backend.py:29,122,276` |
| CA3: generación → post → beats, N salidas y `seed+i` | ✗ Pendiente U3, fuera de esta entrega | `tasks.md:186`; `test_dispatcher_admission.py:409` conserva explícitamente el límite de desbloqueo |
| CA4: selección por tarea verificada y catálogo en caché | ✓ Conforme en U1 | `resolver.py:117,146,172`; `test_queue_resolver.py:146,192,219,257` |
| CA5: unload previo y comprobación de memoria libre | ✓ Conforme para residencia propia acreditada | `dispatcher.py:80,98,116`; `test_dispatcher_admission.py:430,504` |
| CA6: NDJSON, reenganche, progreso, telemetría y SSE | ✓ Transporte; ✗ integración pendiente U2 | `backends/http.py:231`; `test_queue_backend.py:219,260`; `tasks.md:189` |
| CA7: retries y único offload por VRAM | ✗ Pendiente U2, fuera de esta entrega | `tasks.md:190`; `dispatcher.py:1` |
| CA8: recuperación durable, retry manual y batch/serie | ✓ Reserva inicial e incertidumbre; ✗ recuperación completa pendiente U2/U3/I-01 | `admission.py:159,255,286`; `test_dispatcher_admission.py:311`; `test_queue_inputs.py:176`; `tasks.md:191` |

Los ✗ anteriores son alcance pendiente declarado, **no gaps de U1 ni cierres indebidamente acreditados**.

| Comprobación transversal | Resultado |
|---|---|
| Cierres y verificación | ✓ No hay tarea cerrada en este diff. `tasks.md:171,179` mantiene T-04 abierta. Los 150 tests focales no sustituyen su verificación completa; no la ejecuté para suplir evidencia. |
| Alcance | ✓ Los nueve archivos modificados pertenecen a la cola y sus tests previstos por `tasks.md:177` y la fase 2 de `improvement-plan.md:39`. Sin cambios de esquema, contratos ni infraestructura en el diff inspeccionado. |
| Tests | ✓ Leídos los cuatro módulos completos: assertions de transporte, capacidad concurrente, selección, residencia, pertenencia, CAS, staging y conservación tras commit durable. |
| Constitución | ✓ Sin infracción identificada de los principios explícitos de `docs/CONSTITUTION.md:18,19,20,21,22,25,33,37`. |
| Generados E2/interop | N/A: el diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar el exportador. |
| Descripción E3 | ✓ Staging y retención descritos en `docs/decisiones/ADR-0049-entradas-estables-fuera-del-writer.md:10`, `docs/arquitectura/sistema.md:124` y `docs/arquitectura/datos.md:116`. |
| Custodia | ✓ Comprobé por SHA-256 que las 12 fuentes actuales coinciden con el manifiesto vigente y las copias `sources-final-v2/`. |

Cobertura oficial **completa por módulo**, sobre v2 y con **cero exclusiones**:

| Módulo | Cobertura |
|---|---:|
| Admisión | 143/155 — 92,26 % |
| HTTP | 157/170 — 92,35 % |
| Protocolo | 32/32 — 100 % |
| Dispatcher | 77/90 — 85,56 % |
| Inputs | 112/130 — 86,15 % |
| Resolver | 131/143 — 91,61 % |

La evidencia original `final-frozen-v2.command.json:1`, stdout y JUnit registra **150 PASS, 0 fallos, 0 errores, 0 skips**, exit 0. No usé promedio, cobertura de líneas cambiadas ni combinación histórica.

**Gap anterior A-U1-01: corregido.** Contrasté fuentes baseline retiradas, argv, UTC y JUnit: transporte falla por llamada ausente; resolver por payload vacío; admisión por selección/reservas ausentes; dispatcher por POST y switch ausentes. Son RED de comportamiento anteriores a la reconstrucción. Los fallos de presencia, fixtures, colección y la corrida supersedida de 149 tests no se acreditan.

La evidencia nativa entregada usa SQLite migrada y un hijo CPU del engine-mock real mediante ASGI. Los escenarios HTTP inyectados y de residencia sintética permanecen diferenciados. Mi comprobación propia fue de lectura, hashes y análisis en memoria de artefactos; **no ejecuté suites de producto**. QA independiente, Linux, wheel y Docker siguen pendientes.