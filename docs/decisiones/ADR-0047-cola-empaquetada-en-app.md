# ADR-0047 — Cola empaquetada en app

- **Estado:** aceptada; implementación, revisión y QA pendientes
- **Fecha:** 2026-10-07
- **Decisor:** orquestador, bajo delegación autónoma explícita del propietario
- **Ámbito:** M1/T-04; ubicación del código y entregas funcionales

Se elige `apps/server/app/queue/`, importado como `app.queue`. La ubicación anterior `apps/server/queue/` podría colisionar con el módulo `queue` de la biblioteca estándar y no entra en el wheel que actualmente empaqueta `app`. Se compararon un segundo paquete `studio_queue` y un cambio monolítico del runtime. El namespace elegido reutiliza el paquete existente y permite imports normales en desarrollo y distribución; no requiere hacks de carga ni dependencias nuevas. Su inclusión efectiva en wheel y Docker se comprobará en QA.

Tras aceptar la unidad de identidad durable, la implementación sigue tres entregas secuenciales: admisión transaccional con backend HTTP y resolver; consumo de eventos, reintentos, recuperación y cancelación; construcción de cadenas, referencias y reintento manual. Cada entrega conserva TDD, revisión fresca y QA. No se marca un criterio completo antes de verificar todo su comportamiento.

Permanecen SQLite, carriles GPU1/CPU2, producto Docker, Ollama compartido en WSL y ADR-0043. El dispatcher depende del protocolo EngineBackend, no de su implementación HTTP. Las conexiones no mantienen el escritor SQLite adquirido durante red. Un acuse incierto conserva ID y petición; no habilita otra generación ni libera capacidad por presunción. Las variantes reales siguen condicionadas por I-01.

Esta decisión **no aprueba** nuevas tablas de eventos o recuperación, una ampliación del contrato de health, ni una garantía multiproceso. Esas propuestas requieren decisión acotada antes de implementarlas. El requisito vigente de SSE permite un buffer limitado y estado actual cuando se agota; no se convierte en replay histórico ilimitado. Versión de imagen o estado idle no prueban reinicio. Sin evidencia válida se conserva la incertidumbre y el cursor, sin reset especulativo.

Los ocho criterios originales y la verificación de T04 siguen vigentes. [Comparativa original](../roadmap/2026-09-28-m1-mvp-estudio/testing/t04/dispatcher-design-options.md), [límites propuestos](../roadmap/2026-09-28-m1-mvp-estudio/testing/t04/dispatcher-unit-boundaries.md) y [adjudicación root](../roadmap/2026-09-28-m1-mvp-estudio/testing/t04/dispatcher-design-root-decision.md). Las rutas contractuales corregidas en esta última prevalecen sobre los nombres erróneos de la propuesta original.
