---
fecha: 2026-10-11
estado: verificado-documental
agente: qa
model_tier: sonnet
effort: medium
model_tier_source: frontmatter del agente; sin override solicitado
scope: M3/T03 D-03 PD-O1 contrato documental, sin runtime
actual_usage: null
---

# Informe de QA — contrato documental de persistencia M3/T03

| Dato | Resultado |
|---|---|
| Fecha UTC | 2026-10-11T20:53:15.567818+00:00 |
| Estado del componente | VERDE documental, 579/579 comprobaciones propias; 0 fallos, flaky o skips |
| Estado de producto/hito | Pendiente; funciones M3 implementadas 0, T-03 abierta, sin adopción QA |
| URL auditada | No aplica: lectura local y JSON privado; ninguna UI/URL/servicio ejecutado |
| Plan | [Plan](../improvement-plan.md) · [Test-plan](../test-plan.md) |
| Fuente exacta | ca094b156a538467b495804899e5a21aff917113b44728df9ab88fbf92e76f13; 124361 bytes, 670 líneas |

## Veredicto del gate

Salida literal de `qa-gate.py` (exit 0) sobre resultados documentales realmente ejecutados, serializados con el formato de resultados compatible con el gate. El productor es `evidence/check.py`, **no Playwright**. Este gate no declara E2E ni producto verde.

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 579,
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

## Resumen y autenticidad del corte

101 pins de snapshot, guards canónicos y las dos ausencias reservadas comprobados antes; revalidación después en recibo final de evidencia. Los cuatro candidatos y diffs quedan ligados a `release-root.receipt.json`. Fuente fuente/contrato byte exactos. Diff actual `d1e1e37fb24e0dba77f85434485a016c375f4b24e29c76e14f468a9b6b6211e6`; diff revisado histórico `9f4a532dcf537b72e8602f1aabf39d7fa68159c4db320f982d33ad5fdc19ef0e`. No se atribuye el corte histórico al QA actual.

El overlay ROOT preserva el apéndice M2 ya adoptado en datos e iteración, la fila ADR-0084 ratificada y los registros administrativos de los tres ledgers. El prefijo actual de datos se conserva entero. Apéndice M3 y cuerpo normativo ADR-0083 coinciden con sus delimitadores originales; sólo se añade reserva administrativa separada. ADR-0083 sigue candidato local hasta adopción ROOT. Elección PD-O1 y opciones PD-O2 preservadas; revisión2 completa 29 criterios A/25 B y corrección B01, sin nuevos gaps, se conserva sin sustituir sus tablas por este resumen.

## Resultados documentales independientes

| Área | Evidencia propia y conclusión acotada |
|---|---|
| Inventario SQL documental | 40 tablas/384 columnas/40 PK; columnas únicas, namespace reservado disjunto, FK targets conocidos. Las 40 filas originales y todo §4.1–4.10 son texto exacto de f982b1bd original. Ninguna constraint fue creada/ejecutada |
| Censo FK | Criterio uniforme: cada declaración simple o compuesta cuenta como una. 145 simples explícitas + 5 compuestas = 150 explícitas; 22 owner FK de H separadas = 172 relaciones semánticas al expandir H. El 148 histórico de A/B queda intacto. El cómputo restringido 145 + 3 compuestas con target escrito completo da 148; las otras dos se escriben abreviadas en contrato línea266, m3_receipt: FK(execution_id,intent_id,execution_ordinal)→execution triple = m3_execution(id,intent_id,ordinal), y FK(intent_id,intent_revision)→intent_revision(intent_id,revision) = m3_intent_revision(intent_id,revision). Ambas resuelven columnas/UNIQUE. No se reconstruyó el algoritmo histórico del auditor; se conserva su provenance y se explicita éste |
| Baseline AST | Analysis UNIQUE(take_id,kind,analyzer_id); analyzer_version fuera. Asset enum take/artwork/shot_version/render/export/character/lora/cli_run, sin job/analysis/import/backup. Head0007 hijo0006; modelos/migraciones intactos, sólo AST sin imports |
| FIX1 namespace | 11 fieldsets exactos = columnas root expandidas/H; 6 raíces con kind original y 5 sin él; arrays sólo por familia y rows exactas. seal_kind separado de kind; G09 compara header/hash/bytes completos/SQL sin alterar kind. CapturedRef/HistoricRef son wrappers D-02 exteriores; familias internas no amplían su enum |
| JSON realmente ejecutado | Objetos completos de **forma**, 11 positivos y negativos por claves faltantes/extras, arrays/children, bool/string/version desconocida, discriminante incorrecto, duplicate keys iguales y nombres escapados, hash sin seal_kind y desigualdad de payload frente a root. Fixtures de forma usan NULL como placeholders: no se presentan como payloads de dominio válidos ni como SQL G09 ejecutado. Checker independiente stdlib, no reader de producto |
| Semántica normativa | Source/rights/letra/audio/stems/Analysis/timing/preset/video/result especificados; 19 parejas/7 sujetos iguales D-02. Historia inmutable; single/composite y spans/rates/duración medidos, ningún plan como evidencia audio. Corrección mantiene initial/context/audio/tokens; scopes/reservas/CAS y lost ACK/UNKNOWN no crean autoridad por flags |
| Derechos y privacidad | Requisitos AND de inputs/padres/tools/model realmente usados; hash no acredita derechos. Capturas no conceden autorización; serving/efectos invalid/UNKNOWN bloqueados. No PID, leases/credenciales ni paths privados en proyección portable. Requisito documental, no prueba de ejecución/autorización real |
| Migración futura | Sin reconstruir Analysis/Asset/Preset ni ampliar tres tablas de ADR-0074. Revalidar head, schema, guards, backup/rollback antes de DDL. Readers/gates D04/05–09/11/12 pendientes, sin fallback |
| Gates/checklist | G01..14 y PD01..20 completos y futuros. CA02/08/18/20/34/48 y E2E02/08/18/20/34/M48 preservados. Ninguno de los tests SQL/races/rollback fue ejecutado |

`checks.json` conserva cada ID DOC y detalle; `inventory.json` el AST/inventario; `json-shape-fixtures.json` los objetos reales probados. `execution.json` contiene argv, UTC, exits y SHA de stdout/stderr. Manifest final autentica todos los payloads privados y las fuentes/herramientas de esta ejecución.

## Cobertura y ledger

`ledger-lint.py`: exit0, **0 incoherencias y 41 avisos**, incluyendo Changelog ausente y cabecera administrativa de revisión no canónica. No se corrige el ledger en QA. `coverage-check.py`: exit0, 0 referencias rotas, 0 tareas sin cobertura, 0 tests sin referencia y 0 GWT sin cubrir; 34 bloques E2E y 15 manuales trazados. Comprobar referencias no ejecuta esos escenarios.

El gate unitario changed-only80% no se ejecutó: no hay código de producto modificado por este contrato ni runtime autorizado. No se inventa porcentaje unitario ni se etiqueta el porcentaje documental como cobertura E2E.

## Resultados E2E/API/accesibilidad

Automáticos E2E: **0 ejecutados** de 34 definidos; todos pendientes para implementación/liberación futura. Sin servidor/URL/guardrail HTTP porque no hubo llamadas a hosts. No SQL, ORM, DB, Alembic, imports de app, FFmpeg, audio/render, native, GPU, Docker/WSL, servicios, instalación ni control UI. El Chromium headless propio sólo exporta este informe.

## Checklist manual pendiente

- [ ] **M-01** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.
- [ ] **M-07** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.
- [ ] **M-10** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.
- [ ] **M-17** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.
- [ ] **M-21** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.
- [ ] **M-25** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.
- [ ] **M-28** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.
- [ ] **M-29** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.
- [ ] **M-31** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.
- [ ] **M-33** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.
- [ ] **M-43** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.
- [ ] **M-45** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.
- [ ] **M-46** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.
- [ ] **M-48** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.
- [ ] **M-49** — escenario original del [test-plan](../test-plan.md); pendiente, sin evidencia humana.

M-48 (derechos/procedencia/compatibilidad) permanece pendiente; no fue resuelto por flags de consent/commercial_use ni por SHA. Escucha, medios reales, Linux/Windows, conformidad audiovisual y full plan siguen pendientes.

## Diagnósticos del comprobador y PDF

Se conservan salidas iniciales del propio harness: extracción incorporaba marcadores/admin ADR; alias FK intent_revision y regex render_n0 mal reconocidos. Corregidos en evidencia propia, sin tocar fuentes. Segunda expectativa FK148 no incluía uniformemente las dos declaraciones abreviadas; corregida a censo explícito150/H22. `run.py` tuvo un error cp1252 al imprimir después de guardar streams; la reconfiguración UTF8 corrige la consola, no una fuente. No son fallos de producto ni flaky justificados. En diagnostic-1/check.py se guardó la versión corregida posterior, **no** se afirma snapshot contemporáneo del script inicial.

PDF generado mediante skill to-pdf usando cache instalado del repo y perfil Chromium propio. La inspección de imágenes, si se realiza, corresponde al **HTML con CSS print**, no a rasterización de páginas del PDF. No se afirma verificación raster PDF. El PDF y preview permanecen en evidencia privada; recibo PDF incluye pid propio/close/exit y hash final.

## Trazabilidad y cierre del alcance

T-03/D-03 → contrato documental PD-O1 fuente ca094b15, QA independiente actual → pendiente adopción y ejecución de Verificación canónica por ROOT. T-03 no se cierra por el actor QA. M3 sigue 2 tareas documentales previas aceptadas/0 funciones; ningún hito se marca completo. No handoff documenter ni Jira/Confluence desde este componente provisional. Uso real tokens/euros/horasIA null. La QA termina DONE y no escribe ledger/CAS/Git ni continúa mutando fuentes.
