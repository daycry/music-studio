# ADR-0063 · Procedencia en resolución completa tras routing

- **Estado:** aceptada por delegación del propietario; implementación en curso, revisión y QA pendientes.
- **Fecha:** 2026-10-09.
- **Relacionadas:** [ADR-0060](ADR-0060-captura-write-once-de-procedencia-antes-del-envio.md) y [ADR-0062](ADR-0062-evidencia-sintetica-explicita-con-binding-del-server.md).

## Problema y alternativas

El caso original de 801 jobs exige alcanzar un candidato CPU en diez segundos
cuando la GPU está ocupada. La ruta construía procedencia completa antes de que
el dispatcher descartara los candidatos ocupados. Un diagnóstico pasante registró
800 selecciones con 6,989 segundos acumulados, incluidas en los 8,441 segundos
del recorrido de routing. Los tiempos son anidados y no se suman.

Se compararon mantener esa construcción anticipada, posponerla hasta la
resolución completa y conservar una caché de selecciones. Se elige posponerla:
evita trabajo para candidatos descartados y mantiene la autoridad ligada a la
resolución actual. Una caché exigiría invalidación adicional frente a cambios de
descriptor, backend, identidad y observaciones.

## Decisión

`route` conserva los checks de elegibilidad y la información necesaria para
determinar tarea, modo y carril. La construcción del snapshot de procedencia y
la emisión de su lease se realizan en `resolve`, después del filtro de ocupación,
antes de cargar, reservar y enviar. El preflight positivo vuelve a observar el
backend y conserva las validaciones completas de descriptor, identidad y binding.

La admisión y la captura write-once mantienen sus controles de autoridad. El envío
requiere la captura durable y el Health fresco descritos en ADR-0060/0062.
La ruta provisional no constituye una selección autorizada para enviar.

## Verificación y límites

Primero se prueba que routing no emite selección/lease y que la resolución
positiva mantiene la autoridad. Después se ejecuta el caso original de 801 jobs
con sus diez segundos, contadores de catálogo, heartbeat y límites SQL intactos.
La medición traza los ocho módulos completos exigidos, sin excluir líneas o ramas.
También deben pasar los casos de captura, suplantación, mutación y reenvío.

La evidencia privada está en
`.cache/dev-cycle/m1/t05-synthetic-compatibility-unit1/commands/diagnostic-route-select-801/`.
Este ADR registra la causa medida y la decisión; aún no acredita el rendimiento
del fix, la revisión independiente, QA ni el cierre de T-05.
