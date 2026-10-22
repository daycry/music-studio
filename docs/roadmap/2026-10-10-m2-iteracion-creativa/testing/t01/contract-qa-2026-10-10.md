# QA independiente M2/T-01 — prosa y contrato

Fecha UTC: 2026-10-10T19:24:04.366159+00:00. Resultado **PASS DOCUMENTAL: 16/16, 0 defectos documentales bloqueantes detectados**. Ownership exclusivo de esta carpeta privada; ningún archivo de app, tests, docs o ledger editado.

## Alcance y veredicto

La unidad prepara la elección O1 y la aceptación futura de ADR-0074. Se revisan 13 documentos, las fuentes reales de Take/publicación/DTO/schemas y la compatibilidad descrita. TDD n/a: prosa. Cobertura porcentual de diff n/a: no código de producto cambiado por esta unidad. No se inventa 100% de cobertura ni aceptación de M2.

`qa-gate.py` se ejecutó con **adaptación explícita** de los 16 checks documentales/estructurales reales registrados en `cases.json`; `documentary-gate-input.json` no es salida de Playwright. El VERDE del script significa PASS de estos checks exclusivamente. No acredita E2E, UI, funcionamiento de v2, una migración ni capacidad musical. No hubo Playwright, PDF, instalación, red, GPU, WSL, Docker o tests de producto, conforme el alcance solicitado.

Salida literal del gate (exit 0):

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 16,
    "failed": 0,
    "flaky": 0,
    "skipped": 0,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}
```

## Puertas ejecutadas

Entorno gestionado cargado con `scripts/env.ps1`; comando `uv run --frozen --all-packages python .../qa/check.py`. Los recibos JSON conservan UTC, argv exacto, exit, stdout y stderr del proceso real. `ledger-lint.json`: exit0, 0 incoherencias/0 avisos. `coverage-check.json`: exit0, 0 referencias rotas, 24 GWT cubiertos declarativamente, 0 tareas sin cobertura y 0 tests sin referencia. El plan contiene UI futura y por tanto no se marca test-plan n/a para todo M2; **T-01 no tiene UI**, está trazada a M-08 y CA-29/CA-32. Cobertura de referencias no es prueba ejecutada de producto.

`api-structure.json` y `api-additive-diff.json`: exit0; `api-nullable-negative.json`: exit1 esperado por cambio rompedor model_id M1. Se comprobaron realmente tres paths/cuatro operaciones adicionales y igualdad exacta de paths históricos del candidato privado. Esto es candidato estructural, no OpenAPI code-first regenerado de una implementación.

## Resultados observados

| Caso | Resultado | Comprobación | Evidencia |
|---|---|---|---|
| DOC-01 | PASS | Ledger coherente | ledger-lint.json |
| DOC-02 | PASS | Referencias GWT/escenarios coherentes | coverage-check.json:24 GWT; referencias declarativas, no ejecutadas |
| DOC-03 | PASS | 32 CA únicos en spec y matriz | spec.md:156-187; test-plan.md:320-351 |
| DOC-04 | PASS | Enlaces locales existen | links.json: 201 destinos; existencia local sin auditoría de anchors ni enlaces externos |
| DOC-05 | PASS | Once fuentes de sondas siguen vigentes | probe-sources.json; contraste SHA con receipt del architect |
| DOC-06 | PASS | SQLite frontera y v1 honesto | contract-probe.json + lectura ORM149-176,baseline111-143,manifest187-252,song477-593; no migración propuesta validada |
| DOC-07 | PASS | OpenAPI candidato aditivo y negativo rompedor | api-structure/api-additive-diff/api-nullable-negative.json; no implementación de endpoints |
| DOC-08 | PASS | Tres paths/cuatro operaciones y M1 intacto | candidatos privados y packages/contracts/openapi.json; DTO real domain_routes.py145-171 |
| DOC-09 | PASS | Excepción SQL exactamente tres tablas y NULL explícito | ADR0074:27-43; cpu-contract-design:125,170-172; ORM535-595 corroborado |
| DOC-10 | PASS | Backup/WAL/restauración/rollback/FK y downgrade | ADR0074:45; diseño:215-234; exige pruebas futuras sin afirmar migración aceptada |
| DOC-11 | PASS | Versiones históricas/mixtas y preview sin falsa identidad | ADR0074:49-77; datos396-404; pipeline245-249; schema Asset actual209-211 |
| DOC-12 | PASS | UNKNOWN y rechazo M1 autorizado sin ocultar CPU | ADR0074:53,72; design196-202; condición futura, no producto ejecutado |
| DOC-13 | PASS | B01 salida mismo SHA permitida con identidad propia | cpu-contract-design.md:170-172; silencio/fade no debe exigir bytes diferentes |
| DOC-14 | PASS | Autoría delegada y promoción pendiente root | ADR0074:4,19,94; tasks T01 sigue en-progreso; no promoción por QA |
| DOC-15 | PASS | SQLite producto diferenciada del host | recibo root sqlite-container-probe.json; host3.53.1 separado; sólo lectura, no nuevo Docker |
| DOC-16 | PASS | Trece documentos sin drift durante QA | sources-before.json/sources-after.json; tasks delta review2 sólo registro root constatado |

## Contraste cualitativo de fuentes y consecuencias

La lectura real de `models/__init__.py:149-176,198-211,535-595` confirma los tres campos requeridos de Take, la exclusión de asset job y la autoridad/seed obligatorios en intención/revisión. `worker/contracts.py:389,464,538`, `worker/publications.py:64-115` y las guardas de `cpu_publication_invariants.py` confirman que el post CPU M1 todavía depende de inferencia/ganador; no basta llamar CPU a la ejecución. El DTO real de `domain_routes.py:145-171` conserva model_id string; manifest v1 requiere seed y engine y song v1 exige identidad histórica. El diseño documenta cada ruptura y el lector nuevo pendiente sin presentar las fuentes actuales como v2.

La excepción propuesta está limitada a take/publication_intent/publication_intent_revision; CPU execution y asset no se reconstruyen. Backup íntegro con WAL, restauración temporal, rollback, FK ON, preservación de referencias/índices/checks/triggers y rechazo no destructivo de downgrade son gates futuros explícitos. La inferencia sigue exigiendo los campos; NULL SQL exige IS NOT NULL y unicidad CPU propia. No se autoriza sentinela/ganador/semilla heredada.

CPU edit crea Take/asset/ejecución propios, admite SHA de salida igual al padre y conserva autoridad propia: el caso silencio/fade B01 queda expresamente permitido. Historia v1/recibos/hashes no se reescribe, CPU autónomo/previews utiliza v2 y cierre mixto song v2. Previews job usan contexto/recibo privado sin falsa Take ni asset job. UNKNOWN bloquea efectos/serving/cleanup/liberación. Las cuatro API v2 aditivas preservan M1; M1 CPU se rechaza 409 tras autorización y antes de efectos, sin filtrar listas silenciosamente. Commercial_use requiere entradas y herramientas reales.

El recibo histórico de SQLite contenedor del orquestador registra3.40.1/rechazo ALTER; se leyó y selló como evidencia recibida, **no se repitió Docker** ni se acredita la imagen server futura. El host3.53.1 de la sonda privada es distinto. Las once fuentes del recibo architect corresponden a SHA actuales: no drift. Este contraste sostiene las fronteras del diseño, no valida una reconstrucción o migración propuesta.

## Integridad y trazabilidad

`sources-before.json` y `sources-after.json`: trece SHA actuales, sin drift durante QA. Frente a snapshot review2 sólo cambia tasks.md; su añadido final es el registro de revisión2 del orquestador (A/B limpias y B01 corregido), preservando T-01 en-progreso. Once fuentes adicionales de sonda: `probe-sources.json`/`probe-sources-after.json`, sin drift. `links.json`: 201 enlaces locales existentes, 0 rotos; no valida anchors ni fuentes externas. Enlaces .cache son evidencias privadas locales, no descargas públicas. `inventory.json` sella los artefactos QA y evidencia consultada.

## Pendientes y siguiente gate

- [ ] Orquestador acepta/promueve ADR-0074 y cierra T-01 sólo tras verificar estos recibos, revisión A/B y coherencia de los estados/documentos.
- [ ] M-08 contractual: aceptación del acta y compatibilidad por el orquestador. La elección delegada ya consta; no exige una nueva elección personal del propietario.
- [ ] Implementación T-04/T-05/T-07/T-09/T-26/T-29: regresiones M1, migración poblada/rollback/backup-restauración, lectores v1/v2, publicación/custodia y API reales con contratos regenerados/cobertura requerida.
- [ ] El resto de M-01..M-07, escucha/audio real, GPU/Ollama y aceptación final M1/M2 permanece fuera de esta unidad.

QA no cambia estados ni hace handoff documenter: esta es una unidad contractual, no cierre del plan/hito.


## Aceptación del orquestador

Informe transcrito desde la carpeta privada de QA, cuyo inventario y recibos conservan el alcance original. El orquestador verificó 23 artefactos y trece fuentes, gate 0 y negativo API 1 esperado. Tras revisión A/B intento 2 sin gaps, acepta ADR-0074 y la documentación; T-01 se cierra como decisión contractual. Implementación y aceptación integral de M2 permanecen pendientes. La promoción de estados posterior a QA no añade decisiones funcionales.
