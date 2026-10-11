# Informe de QA — ProductionRequest M3/T-02, componente documental

| | |
|---|---|
| Fecha | 2026-10-11T18:54:36.681750+00:00 |
| Estado del componente | VERDE documental; resultado oficial de qa-gate |
| URL auditada | n/a: no UI ni red; sólo documentos privados del corte ROOT |
| Plan | [Plan](../improvement-plan.md) · [test-plan](../test-plan.md) |
| Alcance | D-02 documental, cinco candidatos; no aceptación de T-02 ni M3 |

## Veredicto (qa-gate)

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 403,
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

El reporter JSON es una adaptación explícita de controles documentales ejecutados por Python al formato que lee el gate oficial del plugin 1.21.1. No es una ejecución Playwright ni una prueba del comportamiento runtime. No hay flaky justificados ni resultados omitidos en estos controles.

## Resumen

- Controles documentales independientes: **403/403 pasan**, 0 fallos.
- Snapshot: 81 fuentes fijadas por SHA; cinco candidatos exactos; nueve payloads del actor original conservados.
- Dos prefijos históricos byte exactos; 19 parejas únicas, siete sujetos y seis tipos de receipt.
- Enlaces: **138 ocurrencias / 131 parejas source-target únicas**, resueltas desde los destinos canónicos con mapa de los cinco candidatos. El recuento histórico del actor fue 54 ocurrencias; no se presenta como 54 destinos únicos ni como una comprobación de enlaces de la QA actual.
- TDD n/a: prosa; cobertura runtime n/a. No hay porcentaje unitario ni supuesto 80% de cobertura de producto.

## Resultados automáticos documentales

Se ejecutó `controls.py`: inventario/SHA, alternativas y elección ROOT, tipos declarados, parseo de tablas y enums, refs y evidence unions, límites numéricos exactos, casos válidos/invalidos normativos, autoridad y transiciones descritas, guards, enlaces y gates oficiales. Las aserciones consultan la especificación; no implementan un validador M3 ni convierten ejemplos de prosa en pruebas runtime.

Los controles de conservación y compatibilidad acreditan bytes del corte: DTO M1, engine `/v1`, PostPlan y CreativeRequest históricos no se modificaron por esta QA. Las comprobaciones de rights, CAS, terminal y publicación sólo acreditan su definición documental. D-03/D-04/D-05–09 y las capacidades reales siguen siendo gates de implementación; no se anuncia una migración, reader ni capacidad ya disponibles.

La primera ejecución dio 383/390 y gate 1. Seis fallos eran del parser QA (delimitadores de enums dentro de código, espacio tras separador y selección de la definición de refs), sin defecto de producto demostrado. Otro fallo fue la diferencia del ledger ROOT frente al corte; se conserva la preimagen y la ratificación de overlay. La segunda ejecución corrige el harness; no excluye controles ni cambia documentos. `attempt1/` conserva scripts, JSON, resultados y salida del gate originales.

## Cobertura (coverage-check) y ledger

`ledger-lint.py`: **0 incoherencias, 41 avisos** informativos de Changelog del ledger de M3. `coverage-check.py`: exit 0, cero referencias rotas, tareas sin cobertura, tests huérfanos y GWT sin cubrir. Esta puerta mide referencias declaradas, no ejecución de los escenarios.

```json
{"applies": true, "defined": ["E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-08", "E2E-09", "E2E-11", "E2E-12", "E2E-13", "E2E-14", "E2E-15", "E2E-16", "E2E-18", "E2E-19", "E2E-20", "E2E-22", "E2E-23", "E2E-24", "E2E-26", "E2E-27", "E2E-30", "E2E-32", "E2E-34", "E2E-35", "E2E-36", "E2E-37", "E2E-38", "E2E-39", "E2E-40", "E2E-41", "E2E-42", "E2E-44", "E2E-47", "M-01", "M-07", "M-10", "M-17", "M-21", "M-25", "M-28", "M-29", "M-31", "M-33", "M-43", "M-45", "M-46", "M-48", "M-49"], "referenced": ["E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-08", "E2E-09", "E2E-11", "E2E-12", "E2E-13", "E2E-14", "E2E-15", "E2E-16", "E2E-18", "E2E-19", "E2E-20", "E2E-22", "E2E-23", "E2E-24", "E2E-26", "E2E-27", "E2E-30", "E2E-32", "E2E-34", "E2E-35", "E2E-36", "E2E-37", "E2E-38", "E2E-39", "E2E-40", "E2E-41", "E2E-42", "E2E-44", "E2E-47", "M-01", "M-07", "M-10", "M-17", "M-21", "M-25", "M-28", "M-29", "M-31", "M-33", "M-43", "M-45", "M-46", "M-48", "M-49"], "broken_refs": 0, "tasks_sin_cobertura": [], "tests_sin_referencia": [], "gwt_cubiertos": ["CA-02", "CA-03", "CA-04", "CA-05", "CA-06", "CA-08", "CA-09", "CA-11", "CA-12", "CA-13", "CA-14", "CA-15", "CA-16", "CA-18", "CA-19", "CA-20", "CA-22", "CA-23", "CA-24", "CA-26", "CA-27", "CA-30", "CA-32", "CA-34", "CA-35", "CA-36", "CA-37", "CA-38", "CA-39", "CA-40", "CA-41", "CA-42", "CA-44", "CA-47"], "gwt_sin_cubrir": [], "gwt_sin_id": 0, "test_plan_na": false, "marcador_no_canonico": null}
```

El test-plan completo de M3 contiene 34 escenarios E2E y 15 manuales. Permanecen futuros y abiertos. Ningún escenario UI/API/A11Y de producto se ejecutó aquí; no hay URL, screenshots de aplicación ni validación de GPU, Docker, ext4, almacenamiento, import o mantenimiento.

## Checklist manual pendiente

- [ ] M-01 — CA-01 — no ejecutado en esta QA documental.
- [ ] M-07 — CA-07 — no ejecutado en esta QA documental.
- [ ] M-10 — CA-10 — no ejecutado en esta QA documental.
- [ ] M-17 — CA-17 — no ejecutado en esta QA documental.
- [ ] M-21 — CA-21 — no ejecutado en esta QA documental.
- [ ] M-25 — CA-25 — no ejecutado en esta QA documental.
- [ ] M-28 — CA-28 — no ejecutado en esta QA documental.
- [ ] M-29 — CA-29 — no ejecutado en esta QA documental.
- [ ] M-31 — CA-31 — no ejecutado en esta QA documental.
- [ ] M-33 — CA-33 — no ejecutado en esta QA documental.
- [ ] M-43 — CA-43 — no ejecutado en esta QA documental.
- [ ] M-45 — CA-45 — no ejecutado en esta QA documental.
- [ ] M-46 — CA-46 — no ejecutado en esta QA documental.
- [ ] M-48 — CA-48 — no ejecutado en esta QA documental.
- [ ] M-49 — CA-49 — no ejecutado en esta QA documental.

## Trazabilidad

| Tarea / criterio | Resultado del componente | Evidencia real pendiente |
|---|---|---|
| T-02 / D-02 | Contrato revisable verificado documentalmente | Adopción ROOT; T-02 continúa abierta |
| CA-02 / E2E-02 | Captura única y no retarget definidos | Captura/lectura e integración reales |
| CA-44 / E2E-44 | Intención, CAS, commit/replay/cancel/UNKNOWN definidos | Ejecución, crash, ext4, publicación e import/backup reales |
| CA-48 / M-48 | Familias, versiones, procedencia y rights definidos | Code-first, migraciones/readers y revisión manual real |
| D-03–D-09 | Fronteras y gates declarados | Ratificación propia antes del RED de cada rama |

ADR-0082 permanece propuesta privada numerada por ROOT; no se adopta ni se cambia su estado. No se cierra plan, spec, tarea ni hito y no se dispara handoff de documentación de producto por este verde documental.

## Evidencias y límites

Namespace local de evidencia: `.cache/dev-cycle/m3/production-request-t02-current-qa1-20261011/`. Incluye `controls.py`, `controls-execution.receipt.json`, `raw/controls-results.json`, `raw/results.json`, los tres gates con argv/exit/stdout/stderr y SHA, `raw/links.json`, `raw/prefixes.json`, `raw/original-actor-payloads.json`, guards antes/después y recibo de overlay ROOT. El PDF vive en ese namespace: `report.pdf`; éste es el único informe nuevo publicado bajo `docs/`.

Sólo se escriben artefactos nuevos de QA y este informe autorizado. Sin instalación, GPU, servicios, modelos, datos privados, código de app, ORM/DDL, Git, locks o medidores. Consumo real de tokens/euros/horas IA desconocido (`null`); el tiempo de reloj no se presenta como trabajo IA.

## SHA del candidato auditado

| Destino canónico candidato | SHA-256 |
|---|---|
| `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/production-request-contract.md` | `28b7de913514d8f88d66b44fe43143cc18ed992fd7116cc0089731825893f8e4` |
| `docs/arquitectura/contrato-engines.md` | `4b93f92f0ea4c31d267def1eca40402bc5b060702994956b3adbde9aede122cd` |
| `docs/arquitectura/datos.md` | `d38fe1993962c2ba31379acb01412da0fe869943f8d2cce06701bf70802c9109` |
| `docs/decisiones/ADR-0082-peticion-privada-de-produccion-y-autoridad-por-resultado.md` | `7378e9c5ca433eaaca471cf9eca598c8aa4fcb8c594291a60589865865670168` |
| `docs/decisiones/README.md` | `325a79fa3a5a3754238f47e86fe695d5118a77d379b50af72448ac94a5358479` |
