---
design: n/a               # la arquitectura vive en docs/arquitectura/ y docs/decisiones/
test-plan: test-plan.md
generacion:
  fuente: estimado        # redactado a mano el 2026-09-28; sin usage-meter
---

# 2026-09-28-m1-mvp-estudio

> M1: MVP del estudio web sobre el motor de M0 (canción = proyecto, generación en vivo, biblioteca, reproductor).

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
| **Diseño** | n/a: ver [`../../arquitectura/`](../../arquitectura/) y [`../../producto/ux.md`](../../producto/ux.md) |

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|---|---|---|---|
| Tiempo humano | **153 h** | 0 h | Media |
| Tareas | **16** | 0 hechas | — |

## Fases

| Fase | Tareas | Estimado (h) | Resultado |
|---|---|---|---|
| Fase 1 — Server base | T-01…T-03 | 20 | Server seguro, esquema completo, contratos exportados |
| Fase 2 — Cola y post-proceso | T-04…T-06 | 26 | Dispatcher con carriles y dependencias, worker CPU y SSE |
| Fase 3 — API de dominio | T-07 | 12 | Canciones, takes, letras, generaciones, colecciones y sistema |
| Fase 4 — Web | T-08…T-14 | 86 | Infra E2E, crear, generación en vivo, biblioteca, vista de canción, reproductor y sistema (cada tarea con su E2E) |
| Fase 5 — Pruebas y cierre | T-15, T-16 | 9 | Suite E2E estable y README de puesta en marcha |

**Paralelismo:** una vez cerrada la Fase 1, la Fase 4 (web contra `engine-mock` y los tipos generados) puede avanzar en paralelo con las Fases 2 y 3.

## Cómo se ejecuta

Con `/dev-cycle docs/roadmap/2026-09-28-m1-mvp-estudio`. La spec ya está aprobada y el plan escrito, así que se salta directamente a la implementación. `qa` ejecuta [`test-plan.md`](test-plan.md) con Playwright contra `http://127.0.0.1:3000` y `engine-mock`. **No se empieza hasta cerrar M0 (T-13).**

## Riesgos del plan

| Riesgo | Mitigación |
|---|---|
| SSE y `Range` detrás del proxy de desarrollo de Next | La web habla directamente con `127.0.0.1:8000`, con CORS de lista cerrada ([convenciones.md](../../arquitectura/convenciones.md)) |
| El esquema completo en la primera migración parece sobredimensionado | Es deliberado: las tablas vacías no cuestan nada y así se evitan migraciones rompedoras en M2–M5 |
| Varios engines en marcha a la vez se reparten la VRAM | Dispatcher con `unload` entre engines y comprobación de la VRAM libre en `/v1/health` ([ADR-0007](../../decisiones/ADR-0007-gpu-local-12gb.md)) |
