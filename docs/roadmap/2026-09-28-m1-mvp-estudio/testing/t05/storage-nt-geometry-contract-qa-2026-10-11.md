# Adopción ROOT del contrato de geometría NT — 2026-10-11T12:16:41.617978+00:00

ROOT verifica53artefactos QA, los intentos rojos1/2 preservados,18candidatos,21originales,27snapshot,25guardas y nueve primarias.33/33 controles documentales y gate0, sólo DOC19 corrigió una búsqueda del arnés; contrato funcional intacto. Revisión A+B1:0Critical/0Important/1Minor anotado. ADR0078 y contrato adoptados; evidencia conductual, implementación y cierre M1 pendientes.

El informe original siguiente describe el estado privado en el instante de QA; se conserva íntegro salvo relocalización de enlaces. La adopción posterior sólo actualiza estado documental; no transforma estos controles en pruebas de producto.

---
agente: qa
tier_resuelto: sonnet
reasoning_resuelto: medium
tipo: QA documental de contrato
---

# QA documental M1/T05/U2b2 G2

Resultado documental: 33/33 verificaciones pasan en intento3; gate exit 0. Revisión previa A31/B10: 0 Critical, 0 Important, 1 Minor A01 frase W1 larga, conservada y no bloqueante.

Contrato privado elegido G2 por ROOT; ADR0078 sigue propuesta. No adopción, release, admission nativa ni cierre M1/U2b2. Sin producto imports, DLL, probes, NT simulado, Docker/WSL/GPU/admin, navegador o tests producto. Sin porcentaje de cobertura producto.

Se leyó la constitución y se respetó localización de artefactos, custodia y ledger canónico. Snapshot 27 y guardas25 antes/después; tasks usa únicamente delta autorizado qa-release-root.receipt.json. El resto24 permanece intacto. Referencias primarias offline verificadas por hashes; no se reconsultó la web.

Adaptación explícita DOCUMENTAL del gate oficial: resultados reales del harness se traducen exclusivamente a stats esperadas/no esperadas; no son resultados Playwright, JUnit o browser. Este verde se limita a estas obligaciones documentales.

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 33,
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

| Caso | Obligación ejecutada | Resultado | Evidencia |
|---|---|---|---|
| DOC01 | Snapshot 27 y guardas 25; delta tasks autorizado ROOT | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC01` |
| DOC02 | Diff y recibo de revisión pública íntegros | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC02` |
| DOC03 | Selected G2 frozen 18 artefactos | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC03` |
| DOC04 | Attempt1 original 21 artefactos preservados | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC04` |
| DOC05 | Nueve fuentes Microsoft offline con SHA completos | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC05` |
| DOC06 | Cuatro documentos y C/D false | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC06` |
| DOC07 | G2 aprobado privado; ADR propuesta y release false | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC07` |
| DOC08 | Funciones propuestas y propietario readonly exacto | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC08` |
| DOC09 | ABI cinco argumentos NT11/17 buffers28/4 | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC09` |
| DOC10 | IOSB y layouts exactos | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC10` |
| DOC11 | Arenas y sentinels; no igualdad arbitraria de bytes | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC11` |
| DOC12 | Orden global lock y metadata misma adquisición | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC12` |
| DOC13 | Identidad antes/después y volumen; no igualdad parent/object ID | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC13` |
| DOC14 | Retorno error gobierna y IOSB no override | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC14` |
| DOC15 | SUCCESS, Information exacta antes de leer payload | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC15` |
| DOC16 | PENDING query1 y query2 composite hasta reap | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC16` |
| DOC17 | Incertidumbre posretorno, poison y cero cierre | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC17` |
| DOC18 | Derivador puro diferenciado de custodia y nativo | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC18` |
| DOC19 | Tamaños y máscara cerrada sin bool | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC19` |
| DOC20 | Flags independientes, known mask y corroboración | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC20` |
| DOC21 | Offsets desconocidos y restrictivo propio zero | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC21` |
| DOC22 | B fórmula, causas cerradas y validación anterior cálculo | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC22` |
| DOC23 | Fixtures lógicos y límites exactos de controles | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC23` |
| DOC24 | Cero autoridad writer, journal compatible y cero fallback | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC24` |
| DOC25 | Runtime existente por lectura sin imports | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC25` |
| DOC26 | 21 casos futuros RED distintos; ninguno ejecutado | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC26` |
| DOC27 | M1 abierto, ext4/store/ACK y O2/S1 independientes | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC27` |
| DOC28 | Durable sólo cuatro líneas focales y preserva wire | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC28` |
| DOC29 | ADR/index/contrato referencias coherentes | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC29` |
| DOC30 | Enlaces locales resueltos sobre overlay de rutas canónicas | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC30` |
| DOC31 | Ledger-lint actual limpio | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC31` |
| DOC32 | Conocimiento gotcha contextual readonly | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC32` |
| DOC33 | Snapshot y guardas exactos después | passed | [raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/documentary-results.json) `DOC33` |

Cada evidencia raw contiene fragmentos exactos y líneas, hashes, targets o recibos ejecutados. Los fragmentos son comprobaciones del contrato leído y revisado semánticamente, no sustitutos de futuros tests conductuales. Los 21 R01–R21 son inventario futuro, no 21 tests producto pasados.

Pendientes: RED/GREEN U2b2, ambas queries NT reales/ABI, custodia nativa, S1 fullchain/outsiders, writer/exclusión/modos/buffers, journal/store/ACK/crash/lifecycle, ext4 persistente y QA integral/manual M1. La fórmula pura y sus controles se verifican como contrato, sin ejecutar un derivador aún inexistente.

PDF no generado: dependencias to-pdf ausentes; instalación prohibida por el alcance. No se sustituyó por un artefacto artificial. No screenshots aplicables: evidencia documental raw.

El sello final verifica además los 18 artefactos G2 y 21 originales después de ejecutar, los 32 resultados sin cambios de obligación, y los manifiestos de preservación de ambos intentos rojos. [Verificación final](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/final-verification.receipt.json) y [manifiesto final](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/final.manifest.json) contienen SHA-256 completos. La invocación managed exacta, UTC, exit y streams queda en [recibo wrapper](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3.wrapper.receipt.json), [stdout](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3.wrapper.stdout) y [stderr](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3.wrapper.stderr).

Diagnóstico de cierre conservado: la primera emisión del sello falló al imprimir el símbolo del umbral del gate en consola cp1252, después de completar las aserciones. Ese proceso tuvo exit1, aunque su payload interno marcaba exit0 para las aserciones; no se presenta como proceso verde. [Diagnóstico](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/seal-initial-diagnostic.json), [payload inicial](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/seal-initial-verification.payload.json) y [manifiesto inicial](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/seal-initial.manifest.json) intactos. Sólo se configuró stdout UTF-8; el cierre final real devuelve exit0.

Intento1 intacto 32/33 gate1: DOC19 buscaba un plural inexistente; la regla real exige cuatro tamanos pow2 512..65536 y cada fisico/efectivo divisible por logical. Intento2 diagnostico 32/33 gate1: pipe PowerShell perdio Unicode y no aplico el ajuste. Intento3 cambia exclusivamente DOC19 usando escapes ASCII; restantes 32 checks identicos, candidatos intactos. [Informe1](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt1/report.md), [sello1](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt1.preservation.manifest.json), [Informe2](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt2/report.md), [sello2](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt2.preservation.manifest.json).

[Controles previos](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/controls-before.json), [posteriores](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/controls-after.json), [recibo gate](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/qa-gate.receipt.json), [gate raw](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/qa-gate.stdout), [límite PDF](../../../../../.cache/dev-cycle/m1/storage-nt-geometry-contract-qa-20261011/attempt3/pdf-limit.receipt.json).
