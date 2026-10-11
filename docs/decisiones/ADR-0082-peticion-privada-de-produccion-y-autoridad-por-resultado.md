---
id: ADR-0082
titulo: ProductionRequest privado y autoridad discriminada por resultado
estado: aceptada
fecha: 2026-10-11
decision: D-02
opcion_elegida: PR-O1
namespace: decisión canónica; contratos de implementación futuros
autoridad_de_eleccion: ROOT bajo delegación vigente; 2026-10-11T18:10:35.263982+00:00
adopcion: aceptada por ROOT tras revisión1 y QA documental403/403
---

# ADR-0082: petición privada de producción y autoridad por resultado

## Contexto

ADR-0080 ya fija derivados sobre job/job_dependency y escena N0 local. D-12 ya limita disponibilidad por componente/operación/SHA. Los contratos M1 PostPlan1/PublicationAuthority exigen Take, ganador y terminal de inferencia; las recetas M2 v1 conservan ocho operaciones cerradas. M3 tiene siete familias de resultado, incluyendo upload y mantenimiento, que no caben en esas autoridades sin falsear procedencia.

ROOT compara PR-O1/PR-O2 y elige explícitamente PR-O1 en choice-root.receipt.json. La comparación y elección privada forman parte del namespace de entrega; no se atribuye ratificación personal al propietario. El contrato completo candidato está en snapshot/docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-request-contract.md.

## Decisión propuesta para adopción

ProductionRequest1 y ProductionRecipe1 capturan una única representación privada del server, independiente de M1/M2:19parejas cerradas operation/subject, identidades/result_key inmutables y fuentes/padres/letra/rights/perfiles/revs/selección sólo en recipe. JSON UTF-8 canónico nuevo y límites exactos de choice-root; historial conserva bytes/versiones sin rewrite ni nuevos defaults.

La unidad es un resultado tipado o set de roles requeridos; import publica cierre completo y biblioteca conserva mantenimiento exclusivo. Preview es temporal privado del job, sin Asset.subject_type job. No se agrega sesión persistente de producción ni runner paralelo. Scope Song y biblioteca discriminados impiden Song/Take ficticios.

Intención previa a efecto, revisión inicial1 y CAS de identidad/estado/revisión activos se complementan con autoridad/binding/custodia vivos. Runtime context de intent/lease/expected_revision queda fuera de captura y portable. Los recibos privados distinguen engine_raw/cpu_result/upload_result/publication/import/maintenance. Terminal de engine/CPU no certifica commit. Commit durable prevalece ante cancel tardío/ACK perdido; replay reproduce resultado propio sin regenerar ni doble publicación. UNKNOWN conserva custodia y bloquea efectos/publicación/serving/cleanup/liberación.

Commercial_use es conjunción de entradas/padres/letra/herramientas y modelo realmente usado. CPU y upload no fabrican engine/model/seed/ganador. Derechos/consent y evidencia de licencia son comprobables, no concedidos por SHA/DTO.

D-03 fija SQL/revisiones sin ampliar por analogía la excepción ADR-0074; D-04 fija formatos/readers por sujeto; D-05–09 fijan perfiles/catalog/cut/binding. Esos seams son tipados y no se ejecutan antes de ratificación propia. No se relaja timeline-v1 ni M1 DTO ni engine/v1; tampoco se declara Manifest3 elegido.

## Alternativas descartadas

- PR-O2: contratos y versiones por familia con dispatch mínimo. Aísla evolución, pero duplica obligaciones CAS/replay/privacy en siete lectores.
- PostPlan1 con ganador ficticio o ampliación CreativeRequestV1 por conveniencia: ya vetados por ADR-0074/0077/0080; no se reabren.
- Persistencia de sesión, deduplicación por hash o import de autoridad activa: no satisfacen autoridad propia/closure y contradicen el alcance fijado.

## Consecuencias y verificación pendiente

Hay núcleo contractual común con ramas cerradas y recovery uniforme; evolución coordinada de envelope/reader exige mantener históricos. Los tipos de autoridad se conservan separados y las reglas específicas import/maintenance no se reducen a publisher ordinario.

Este candidato cambia la concreción documental en contrato nuevo y dos apéndices byte-preservados. No cambia código, schemas, API, ORM, DDL, runtime, tests, ledger, Git ni disponibilidad. ROOT reserva número y actualiza índice/documentación/ledger al adoptar tras revisión/QA. No se modifica ADR-0074/0077/0080 ni se declara T-02 cerrada.

Los destinos canónicos previstos son docs/decisiones/ADR-NNN-<slug>.md (número/slug pendientes ROOT) y docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-request-contract.md. No hay enlace numerado ficticio. El recibo de entrega identifica fuentes y SHA, manifest sin incluirse a sí mismo, guards y diff exacto; pruebas de producto siguen en sus tareas.


## Reserva y mapeo ROOT para revisión

Número0082reservadoenlarevisiónprivada, noadopción. Sourcecandidatoinicial07c37ca6intacto. El contrato normativo destino es [ProductionRequest](../roadmap/2026-10-11-m3-produccion-portada-video-letra/production-request-contract.md). Referencias anteriores al namespace de entrega son evidencias históricas privadas; no autoridad runtime ni paths de producto. Estado de decisión: propuesta hasta review/QA/acta ROOT.


## Acta ROOT de adopción — 2026-10-11T19:03:55.596469+00:00

Decisión aceptada documentalmente tras revisiónA/Bsin gaps yQA403/403/gate0, por delegación vigente del usuario. Las referencias preadopción a reserva/propuesta/candidato/pendientes son históricas; esta acta fija su estado vigente. PR-O1, sus límites y contratos no conceden authority runtime ni aceptaciónM3; D03–09 y producto conservan gates propios. OriginalactorADR07c37ca6 yderivadorenumbered revisado preservados privados; ningún históricoM1/M2 reescrito.
