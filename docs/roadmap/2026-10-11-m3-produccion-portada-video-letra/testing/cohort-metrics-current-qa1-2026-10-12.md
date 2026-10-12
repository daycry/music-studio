# Cohortes y métricas — QA documental y adopción normativa

ROOT ratificó CM-O1 y CM-P1 a las 2026-10-12T13:23:49.279192+00:00, tras [revisión2FULLA/B](cohort-metrics-review2-2026-10-12.md) y QA independiente **287/287**. Los dos defectos Important previos quedaron corregidos; A03Minor se aclara en la nota de procedencia de ADR0087. Se adoptaron3documentos; contrato fuente6cc06770734a9a8287a10c2a00fcaacc226eca2eb255c1b31f5df7f40b70c680/99562bytes se conserva exacto. Sólo ADR/index reciben overlays de estado/ratificación; no se retoca ningún umbral, cuerpo ni hash de material evaluado.

ROOT auditó los26artefactos propiosQA,143sources,61supports y213inputsdelectura con SHA/tamaño/stat. ManifestexternoSHA356f5bce8a47c6a882c5359ef54345b5531c8736c51269f56e30ededfde7a4ef,reportSHA005ca9b760b4b8417ba5c724c7997b7d2bccda336d81278a9466cea8620464fd. Raw01/02 fallaron sólo por manejo de newline/headings del harness; se conservan, raw03 y sealexit0. No fueron REDdeproducto ni cambios de fuente.

| Categoría comprobada | Resultado |
|---|---|
| Integridad143pins/61supports/26ownpayloads/213inputs | PASS;0diff/reparse |
| Fuente FINAL/ADRliteral/indexúnico/D02-D05 | PASS fullbyte/source6cc06770 |
| 9cuerpos aprobados/15casosadversos | PASS contenido tras sólo CRLF→LF; **no byteigualdad entre cortes** |
| Ratingentero1..5/min4/NULL/count/todasobservaciones | PASS escalar; no acta humana ejecutada |
| 39artefactos/23JSON/88Artifactrefs/10ciclosinversos | PASS estructural sintético; hashes fullbyte |
| DAGcomplete/K-A-Plan-E/I-F-R/P/runner-combine/source/config | PASS definición/ejemplo; sin ejecuciónoficial ni autoridad runtime |
| Casos futuros/missing/exclusions/80exact/branches/statements/CLIexits | PASS concreción; instrumentotodavíanoimplementado |
| Importssólostdlib/harnesspropio,noworkerhelpers/product | PASS scope documental |

La anterior afirmación de «byteexactos» en los retornosA2/B2 yworker queda precisada por el apéndice firmado de revisión2: cuerpos conservados tras normalizar newline exclusivamente para comparar, mientras los SHA siguen fullbyte. Los informes históricos y checkpoints no se reescriben para simular otra evidencia.

**Pendiente:** implementar scripts/m3_coverage_gate.py y tests con causalRED/GREEN/rawoficial/whole≥80/freshrevisiónQA/Verificación; adquirir derechos/material/personas/anotaciones/actasD13 antesevaluación; GPU/música/render/browser/player/recovery/E2E/manuales deproducto. El caso100/100fixture no acredita nada de eso. T06/Fase1/M3 quedan abiertos, objetivoM0–M5activo, ningún coste/tokens/horasIAactualinventado.
