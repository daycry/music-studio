---
design: n/a               # la arquitectura vive en docs/arquitectura/ y docs/decisiones/
test-plan: n/a (sin UI)
generacion:
  fuente: estimado        # redactado a mano el 2026-09-28; sin usage-meter
---

# 2026-09-28-m0-entorno-y-motor

> M0: entorno reproducible, primera canción por CLI en la RTX 5070, medición y elección de modelo por escucha.

| | |
|---|---|
| **Fecha** | 2026-09-28 |
| **Estado** | en-progreso |
| **Tipo** | Infra / Investigación |
| **Prioridad** | Crítica |
| **Solicitante** | Propietario |
| **Responsable** | Propietario (con IA) |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | n/a: proyecto personal, sin presupuesto en € ([ADR-0001](../../decisiones/ADR-0001-reinicio-desde-cero.md)) |
| **Diseño** | n/a: ver [`../../arquitectura/`](../../arquitectura/) y [`../../decisiones/`](../../decisiones/) |

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|---|---|---|---|
| Tiempo humano | **88 h** (80 h sin la T-12 opcional) | 0 h | Media |
| Tareas | **15** (14 obligatorias; T-14 añadida con autorización del propietario) | [Ver ledger canónico](tasks.md) | — |

## Fases

| Fase | Tareas | Estimado (h) | Resultado |
|---|---|---|---|
| Fase 1 — Preparación | T-00, T-01 | 6 | Máquina lista y repositorio con su esqueleto |
| Fase 2 — Cimientos compartidos | T-02, T-03, T-04 | 26 | Pesos seguros, contrato `/v1` con engine-mock, audio-post y manifiesto |
| Fase 3 — Motor musical | T-05, T-06, T-07 | 19 | **🎯 Primera canción por CLI** |
| Fase 4 — Medición y elección | T-08 … T-13, T-14 adicional | 37 | Benchmark, matriz de capacidades, batería de evaluación, escucha y decisión de modelo |

El detalle, los criterios y las verificaciones están en [`tasks.md`](tasks.md), el registro canónico del progreso.

## Cómo se ejecuta

Con `/dev-cycle docs/roadmap/2026-09-28-m0-entorno-y-motor` del plugin custom-agents. La spec ya está aprobada y el plan escrito, así que se saltan las Fases 1–2 del ciclo (evaluar y planificar) y se va directo a la implementación. Hay que respetar el orden de fases de `tasks.md`. La T-00 es manual y la marca el propietario. M0 no tiene UI: `qa` corre en modo «sin UI» (`ledger-lint` más los tests).

## Riesgos del plan

| Riesgo | Mitigación |
|---|---|
| La API Python de ACE-Step no expone progreso por pasos ni cancelación | Envolver el bucle de difusión o, como mínimo, emitir las etapas; la cancelación se comprueba entre variantes. Queda documentado en T-06 |
| El upstream cambia (repositorio muy activo) | Repositorio y pesos fijados por commit y revisión; actualizar exige repetir T-09 y T-10 |
| El LM 0.6B da peor calidad que el 1.7B | Medir y escuchar en T-09 y T-13; si el 1.7B cabe con margen, pasa a ser el modo por defecto |
| El bind mount es lento al cargar | Medido en T-09; si supera 30 s, se abre un ADR sobre caché local |

## Ampliación autorizada — T-14, 2026-10-05

El propietario autoriza una comparación privada de tres pares de «Libre»: shift 1/3, fragmentos de 90 s, semillas 1/2/3, entrada y resto de parámetros iguales. Se incorpora al [ledger canónico](tasks.md) sin sustituir la batería fija ni los criterios de T-08–T-13. El parámetro opcional conserva el default anterior; [ADR-0026](../../decisiones/ADR-0026-comparacion-controlada-shift.md). Estimación adicional no fijada: no se inventan horas ni coste y las 88 h originales siguen siendo el presupuesto orientativo del alcance inicial. La preparación y ejecución técnica no eligen un ganador: queda pendiente la escucha del propietario.
