---
tipo: qa-documental
agente: qa
model: sonnet
effort: medium
tier_fuente: release-root.receipt.json/frontmatter
fecha: 2026-10-11
estado_componente: VERDE
estado_hito: NO-VERDE
alcance: contrato documental T05/K2; sin runtime ni UI
tokens_reales: null
coste_real: null
horas_ia_reales: null
---

# Informe de QA — T05/K2, adquisición candidata O1

| Dato | Resultado |
|---|---|
| Fecha | 2026-10-11T19:33:42.115868+00:00 |
| Estado del componente documental | **VERDE** — 119/119 controles documentales pasan |
| Estado global M1 | **NO-VERDE**; T05/M1 abiertos, aceptación persistente pendiente |
| URL auditada | No aplica: contrato Markdown, sin tráfico a app ni operaciones nativas |
| Plan | [Plan M1](../../improvement-plan.md) · [Pruebas M1](../../test-plan.md) |
| Candidato | 744 líneas, 63.074 bytes, SHA256 `110f291d8c61517794e8dc955f06d6ac591c1a11c263280b5e09dd68e97bfb78` |
| Objeto auditado | `snapshot/docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-acquisition-design.md` |
| Evidencia privada | `.cache/dev-cycle/m1/storage-journal-k2-acquisition-current-qa1-20261011/testing/` |

## Veredicto oficial qa-gate

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 119,
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

El runner propio ejecutó aserciones documentales y exportó outcomes en el esquema de suites/resultados que admite qa-gate. **No ejecutó Playwright ni E2E**. Cada resultado se conserva en JSON y JUnit, con criterio, descripción, detalle calculado y diagnóstico. No hay reintentos, flaky, skips o outcomes inventados. El gate sólo acredita este contrato, nunca UI, permisos reales o producto.

## Resumen y límites

- 119/119 controles: 28 entradas snapshot, 27 guardas canónicos, 25 pins SDK y 39 controles de integridad, reglas y aritmética. Candidato canónico ausente. Mapeo del design.md original comprobado byte exacto.
- SDK: 25 Markdown de MicrosoftDocs/sdk-api, commit inmutable `656e9656bfaef34dd29cd7ee9e1146aec17e924c`, descargados y hasheados sólo en memoria por esta QA; tamaños/hashes coinciden. No instalación ni ejecución SDK.
- Cálculo independiente de layouts x64, máscaras de los ocho profiles, SID/ACE/ACL, rangos del control10240+7, padding, buffers UTF16 y suma locator108565/pool1048576. Son cálculos CPU; no binder ni NtCreateFile real.
- La separación K4a→K2→K3→K4b→K5→store conserva S1/C2/O2. CREATE exige guard parent S1 nominal actual; seeds CPU tienen tipo distinto y no emiten admisión nativa. Issuer K4a y G1 real siguen pendientes antes de liberar K2 nativo.
- Se verifican reglas de preentry/IOSB, A1–A7, rollback ordinario frente a BaseException, cortes CloseTRUE/C4, RLock, pins y postorden, cuotas únicas/tombstones/rotación, DTO cerrados. No se ejecutaron esas transiciones de un runtime K2 inexistente.
- Sin cobertura runtime modificada: TDD n/a prosa. No porcentaje unitario ficticio. La matriz K2-01..K2-18 sigue describiendo tests causales futuros, no productos ejecutados por esta QA.
- Se leyó el contrato completo, options/choice y transferencia normalizada A33/B10: 0 gaps de ambas lentes; no se reconstruyen mensajes originales ni diagnósticos tempranos ausentes.
- Overlay ROOT K1 aceptado actual explícito. Prepare histórico ledger `01eedffd3b406ac529a40d944f6f43b6e192eb73fd4c446af461e6a0142a73c0` difiere del release `a55a070dedfb1c389a9f060fe4dc9a017af967c672ed7599858fe9dba06e49d1`; no se atribuye evidencia histórica a la versión actual.

## Puertas de entrada oficiales

Ledger-lint (exit 0), salida literal:

```text
⚠️  el fichero no es UTF-8 limpio (leído con reemplazos)
ledger-lint: 0 incoherencias · 1 avisos (tasks.md)
```

Coverage-check (exit 0), salida literal:

```text
⚠️  T-00: sin cobertura declarada (si es tarea de UI, es un criterio huérfano → NO verde)
{"applies": true, "defined": ["API-01", "API-02", "E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10", "E2E-11", "M-01", "M-02", "M-03"], "referenced": ["API-01", "API-02", "E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10", "E2E-11", "M-01", "M-02", "M-03"], "broken_refs": 0, "tasks_sin_cobertura": ["T-00"], "tests_sin_referencia": [], "gwt_cubiertos": [], "gwt_sin_cubrir": [], "gwt_sin_id": 0, "test_plan_na": false, "marcador_no_canonico": null}
```

Estas puertas miden coherencia del ledger y cobertura declarada por el test-plan, no ejecución del hito. T-00 es tarea documental (`Tipo: docs`, prosa/secuenciación, ledger:41–55), no de UI; su ausencia en el test-plan E2E es aviso de triage, no criterio UI huérfano. El aviso UTF-8 histórico del ledger no es una incoherencia dura ni una prueba de UI. Sus stderr y argv/SHAs están en raw/gate-receipts.json y raw/*.stderr.txt.

## Controles ejecutados y trazabilidad

Cada fila vincula un criterio contractual con una aserción real del auditor y su evidencia. Los fragmentos de prosa se comprueban por cláusula/posición; las filas aritméticas calculan valores independientemente. Estos controles no implementan ni prueban producto.

| ID | Criterio | Aserción ejecutada | Resultado | Evidencia |
|---|---|---|---|---|
| D001 | integridad | 744 líneas, 63074 bytes y hash fijado | passed | `raw/D001.json` |
| S01 | integridad snapshot | docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md | passed | `raw/S01.json` |
| S02 | integridad snapshot | uv.lock | passed | `raw/S02.json` |
| S03 | integridad snapshot | AGENTS.md | passed | `raw/S03.json` |
| S04 | integridad snapshot | tests/conftest.py | passed | `raw/S04.json` |
| S05 | integridad snapshot | docs/roadmap/2026-09-28-m1-mvp-estudio/testing/t05/storage-journal-store-flush-native-2026-10-11.md | passed | `raw/S05.json` |
| S06 | integridad snapshot | docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-security-policy.md | passed | `raw/S06.json` |
| S07 | integridad snapshot | scripts/storage_journal_windows_io.py | passed | `raw/S07.json` |
| S08 | integridad snapshot | docs/CONSTITUTION.md | passed | `raw/S08.json` |
| S09 | integridad snapshot | docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-kernel-design.md | passed | `raw/S09.json` |
| S10 | integridad snapshot | pyproject.toml | passed | `raw/S10.json` |
| S11 | integridad snapshot | packages/storage-guard/studio_storage_guard/receipt.py | passed | `raw/S11.json` |
| S12 | integridad snapshot | docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-geometry-design.md | passed | `raw/S12.json` |
| S13 | integridad snapshot | tests/test_storage_journal_windows_io.py | passed | `raw/S13.json` |
| S14 | integridad snapshot | docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md | passed | `raw/S14.json` |
| S15 | integridad snapshot | tests/test_storage_journal_windows_abi.py | passed | `raw/S15.json` |
| S16 | integridad snapshot | scripts/storage_journal_windows_abi.py | passed | `raw/S16.json` |
| S17 | integridad snapshot | tests/test_storage_journal_windows.py | passed | `raw/S17.json` |
| S18 | integridad snapshot | conftest.py | passed | `raw/S18.json` |
| S19 | integridad snapshot | scripts/storage_journal_windows.py | passed | `raw/S19.json` |
| S20 | integridad snapshot | docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md | passed | `raw/S20.json` |
| S21 | integridad snapshot | scripts/storage_journal.py | passed | `raw/S21.json` |
| S22 | integridad snapshot | .cache/dev-cycle/m1/storage-journal-store-flush-probe-20261011/flush_probe_experimental.py | passed | `raw/S22.json` |
| S23 | integridad snapshot | docs/roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md | passed | `raw/S23.json` |
| S24 | integridad snapshot | .claude/dev.json | passed | `raw/S24.json` |
| S25 | integridad snapshot | docs/roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md | passed | `raw/S25.json` |
| S26 | integridad snapshot | scripts/env.ps1 | passed | `raw/S26.json` |
| S27 | integridad snapshot | docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md | passed | `raw/S27.json` |
| S28 | integridad snapshot | docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-acquisition-design.md | passed | `raw/S28.json` |
| G01 | guardas canónicos | docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md | passed | `raw/G01.json` |
| G02 | guardas canónicos | uv.lock | passed | `raw/G02.json` |
| G03 | guardas canónicos | AGENTS.md | passed | `raw/G03.json` |
| G04 | guardas canónicos | tests/conftest.py | passed | `raw/G04.json` |
| G05 | guardas canónicos | docs/roadmap/2026-09-28-m1-mvp-estudio/testing/t05/storage-journal-store-flush-native-2026-10-11.md | passed | `raw/G05.json` |
| G06 | guardas canónicos | docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-security-policy.md | passed | `raw/G06.json` |
| G07 | guardas canónicos | scripts/storage_journal_windows_io.py | passed | `raw/G07.json` |
| G08 | guardas canónicos | docs/CONSTITUTION.md | passed | `raw/G08.json` |
| G09 | guardas canónicos | docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-kernel-design.md | passed | `raw/G09.json` |
| G10 | guardas canónicos | pyproject.toml | passed | `raw/G10.json` |
| G11 | guardas canónicos | packages/storage-guard/studio_storage_guard/receipt.py | passed | `raw/G11.json` |
| G12 | guardas canónicos | docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-geometry-design.md | passed | `raw/G12.json` |
| G13 | guardas canónicos | tests/test_storage_journal_windows_io.py | passed | `raw/G13.json` |
| G14 | guardas canónicos | docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md | passed | `raw/G14.json` |
| G15 | guardas canónicos | tests/test_storage_journal_windows_abi.py | passed | `raw/G15.json` |
| G16 | guardas canónicos | scripts/storage_journal_windows_abi.py | passed | `raw/G16.json` |
| G17 | guardas canónicos | tests/test_storage_journal_windows.py | passed | `raw/G17.json` |
| G18 | guardas canónicos | conftest.py | passed | `raw/G18.json` |
| G19 | guardas canónicos | scripts/storage_journal_windows.py | passed | `raw/G19.json` |
| G20 | guardas canónicos | docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md | passed | `raw/G20.json` |
| G21 | guardas canónicos | scripts/storage_journal.py | passed | `raw/G21.json` |
| G22 | guardas canónicos | .cache/dev-cycle/m1/storage-journal-store-flush-probe-20261011/flush_probe_experimental.py | passed | `raw/G22.json` |
| G23 | guardas canónicos | docs/roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md | passed | `raw/G23.json` |
| G24 | guardas canónicos | .claude/dev.json | passed | `raw/G24.json` |
| G25 | guardas canónicos | docs/roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md | passed | `raw/G25.json` |
| G26 | guardas canónicos | scripts/env.ps1 | passed | `raw/G26.json` |
| G27 | guardas canónicos | docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md | passed | `raw/G27.json` |
| D002 | adopción | Destino aún ausente | passed | `raw/D002.json` |
| D003 | mapeo | Original arquitecto byte exacto | passed | `raw/D003.json` |
| D004 | elección | O1 y options pin | passed | `raw/D004.json` |
| D005 | historia | Prepare previo conservado y release posterior explicitan drift ledger | passed | `raw/D005.json` |
| D006 | normativa | C2/S1/O2 conservados | passed | `raw/D006.json` |
| D007 | K2-01 | Capabilities exactas y PID/registro | passed | `raw/D007.json` |
| D008 | K4a | Issuer y pin efectivos previos, sin ciclo | passed | `raw/D008.json` |
| D009 | K2-01 scopes | Scopes cerrados y CPU distinto | passed | `raw/D009.json` |
| D010 | K4b CREATE | Guard nominal parent S1 actual | passed | `raw/D010.json` |
| D011 | K2-02 | 8 profiles: cálculo bitwise íntegro, shares/disposition | passed | `raw/D011.json` |
| L01 | K2-17 layouts | UNICODE_STRING | passed | `raw/L01.json` |
| L02 | K2-17 layouts | OBJECT_ATTRIBUTES | passed | `raw/L02.json` |
| L03 | K2-17 layouts | IO_STATUS_BLOCK | passed | `raw/L03.json` |
| L04 | K2-17 layouts | SD absolute | passed | `raw/L04.json` |
| L05 | K2-17 layouts | ACL | passed | `raw/L05.json` |
| L06 | K2-17 layouts | ACE_HEADER | passed | `raw/L06.json` |
| L07 | K2-17 layouts | ACCESS_ALLOWED_ACE | passed | `raw/L07.json` |
| D012 | K2-17 signatures | 21 firmas SDK y 11 args NtCreateFile | passed | `raw/D012.json` |
| D013 | K2-04 | Descriptor cerrado, dedup GROUP sin grants | passed | `raw/D013.json` |
| D014 | K2-04/14 ACL/SID | SID 12..68 y ACE/ACL extremos | passed | `raw/D014.json` |
| D015 | K2-03 UTF16 | Units y terminadores calculados | passed | `raw/D015.json` |
| D016 | K2-03 validation | Devices/control/astral/surrogates/trailing | passed | `raw/D016.json` |
| D017 | K2-05 locator | 6 pasos, RootNULL, SUBST/ambiguity y G1 pendiente | passed | `raw/D017.json` |
| D018 | K2-14 | Todos rangos control y padding SDK | passed | `raw/D018.json` |
| D019 | K2-14 | Pool, frame y locator suma exacta | passed | `raw/D019.json` |
| D020 | K2-14 | Backings únicos, carga requested y CPU/native separados | passed | `raw/D020.json` |
| D021 | K2-15 | Monotonicidad records/owners y cuarentena | passed | `raw/D021.json` |
| D022 | K2-06 | Preentry A0-A3 y IOSB sentinels | passed | `raw/D022.json` |
| D023 | K2-07 | Exact SUCCESS y scalar privado validado | passed | `raw/D023.json` |
| D024 | K2-08 | Failure sentinel vs IOSB escrito, cuatro status mappings | passed | `raw/D024.json` |
| D025 | K2-09 | Pending e incertidumbre no frees ni retry | passed | `raw/D025.json` |
| D026 | K2-10/11 | Todas ventanas A1-A7, ordinaria vs BaseException | passed | `raw/D026.json` |
| D027 | K2-12 | CloseTRUE antes C4 unknown/free1/retry0 | passed | `raw/D027.json` |
| D028 | K2-13 | Locks/pins/postorden y primer unknown | passed | `raw/D028.json` |
| D029 | K2-16 | DTO cerrado y sin secretos | passed | `raw/D029.json` |
| D030 | K2-18 límites | 18 controles futuros; CPU no producto, G1/K3/K4/K5 pendientes | passed | `raw/D030.json` |
| D031 | enlaces | 6 enlaces/5 destinos desde M1 canónico | passed | `raw/D031.json` |
| D032 | SDK pins | 25 rutas Microsoft commit inmutable | passed | `raw/D032.json` |
| P01 | SDK fuente primaria | winternl/nf-winternl-ntcreatefile | passed | `raw/P01.json` |
| P02 | SDK fuente primaria | ntdef/ns-ntdef-_object_attributes | passed | `raw/P02.json` |
| P03 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-setsecuritydescriptordacl | passed | `raw/P03.json` |
| P04 | SDK fuente primaria | fileapi/nf-fileapi-getvolumenameforvolumemountpointw | passed | `raw/P04.json` |
| P05 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-createwellknownsid | passed | `raw/P05.json` |
| P06 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-isvalidsid | passed | `raw/P06.json` |
| P07 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-getlengthsid | passed | `raw/P07.json` |
| P08 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-initializesecuritydescriptor | passed | `raw/P08.json` |
| P09 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-initializeacl | passed | `raw/P09.json` |
| P10 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-addaccessallowedace | passed | `raw/P10.json` |
| P11 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-setsecuritydescriptorowner | passed | `raw/P11.json` |
| P12 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-setsecuritydescriptorgroup | passed | `raw/P12.json` |
| P13 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-setsecuritydescriptorcontrol | passed | `raw/P13.json` |
| P14 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-getsecuritydescriptorcontrol | passed | `raw/P14.json` |
| P15 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-getsecuritydescriptorowner | passed | `raw/P15.json` |
| P16 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-getsecuritydescriptorgroup | passed | `raw/P16.json` |
| P17 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-getsecuritydescriptordacl | passed | `raw/P17.json` |
| P18 | SDK fuente primaria | securitybaseapi/nf-securitybaseapi-isvalidsecuritydescriptor | passed | `raw/P18.json` |
| P19 | SDK fuente primaria | fileapi/nf-fileapi-getvolumepathnamew | passed | `raw/P19.json` |
| P20 | SDK fuente primaria | fileapi/nf-fileapi-querydosdevicew | passed | `raw/P20.json` |
| P21 | SDK fuente primaria | fileapi/nf-fileapi-getdrivetypew | passed | `raw/P21.json` |
| P22 | SDK fuente primaria | winnt/ne-winnt-well_known_sid_type | passed | `raw/P22.json` |
| P23 | SDK fuente primaria | winnt/ns-winnt-security_descriptor | passed | `raw/P23.json` |
| P24 | SDK fuente primaria | winnt/ns-winnt-acl | passed | `raw/P24.json` |
| P25 | SDK fuente primaria | winnt/ns-winnt-access_allowed_ace | passed | `raw/P25.json` |

## Pruebas M1 fuera del alcance y pendientes

| ID | Escenario del test-plan | Resultado en esta QA |
|---|---|---|
| E2E-01 | Crear canción con dos variantes y escucharla | No ejecutado en esta QA documental |
| E2E-02 | La autoría de la letra es obligatoria | No ejecutado en esta QA documental |
| E2E-03 | Validación de etiquetas de la letra | No ejecutado en esta QA documental |
| E2E-04 | Error del engine y reintento | No ejecutado en esta QA documental |
| E2E-05 | Cancelar | No ejecutado en esta QA documental |
| E2E-06 | Recuperación tras reiniciar el server | No ejecutado en esta QA documental |
| E2E-07 | Vista de canción: take maestro, valoración y versiones de letra | No ejecutado en esta QA documental |
| E2E-08 | Biblioteca: búsqueda, filtros y papelera | No ejecutado en esta QA documental |
| E2E-09 | Beats en la onda (análisis dependiente) | No ejecutado en esta QA documental |
| E2E-10 | Página Sistema | No ejecutado en esta QA documental |
| E2E-11 | Instrumental sin declaración de autoría | No ejecutado en esta QA documental |
| API-01 | Seguridad local: Host y Origin | No ejecutado en esta QA documental |
| API-02 | OpenAPI | No ejecutado en esta QA documental |

## Checklist manual

- [ ] **M-01 — Generación real con GPU**: pendiente de ejecución real/humana en la aceptación M1.
- [ ] **M-02 — Revisión visual y de accesibilidad básica**: pendiente de ejecución real/humana en la aceptación M1.
- [ ] **M-03 — Backup y restauración**: pendiente de ejecución real/humana en la aceptación M1.

Además: G1 DIRECTORY/no-follow/NTGUID; K4a issuer/pin; K3 observación; K4b cadena S1 real; K5 read/write/flush; rotación/reap; store PREPARE/COMMIT/ACK y recovery causal; bootstrap/lifecycle; VHDX/ext4/UUID persistente y backup/restauración. Ningún green documental cierra esas puertas.

## Incidencias de preparación y conservación

El primer intento falló antes de invocar Python: PowerShell no pudo abrir testing/raw/audit-run.log porque raw aún no existía (DirectoryNotFoundException). El exit_code 0 del shell era LASTEXITCODE previo y **no** resultado de auditoría. Se creó sólo el directorio autorizado y después corrió el auditor una vez, 119PASS/exit0. Diagnóstico completo, sin atribuirle historia anterior, en raw/preflight1-full.txt. No fallos de producto demostrados.

## Evidencias y cierre

Resultados: raw/results.json, raw/controls.json, raw/junit.xml y raw/imports.json. Scripts propios: audit_document.py y build_report.py. Las fuentes reales de entrada y herramientas quedan fijadas en el manifiesto SHA256/bytes; el manifiesto se excluye de sí mismo. Recibo final vuelve a verificar los 27 guardas y la ausencia del candidato. No se tocaron ledger/spec/estados/canon/código/Git, servicios, Docker/WSL, ACL, DB, modelos ni GPU. Cese significa fin de este auditor; ningún hijo de producto fue iniciado.

PDF generado con $custom-agents:to-pdf mediante herramientas ya disponibles dentro del repositorio, sin instalar. La inspección visual y sus límites constan en el recibo PDF; vistas de HTML no acreditan todas las páginas PDF. Informe local, sin Confluence/Jira/handoff de hito.
