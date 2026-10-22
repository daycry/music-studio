# Revisión de recetas creativas — producto — intento 2

ROOT 2026-10-11T12:31:28.885655+00:00: **0 Critical / 1 Important nuevo / 0 Minor**. A01/B01/B02 de intento1 corregidos; B03 es regresión nueva reproducida por B. A aprobó con sus casos; el contraejemplo adicional impide aceptar el criterio general de schemas.

Lentes frescas A/B. C/D auto false sobre tres archivos del diff de corrección; revisión C1 sin hallazgos conservada. Scope3/0fuera/0avisos/0exclusionesusuario. Base privada `21a30e8dac7deb97ac22c676351f5eebe99fcf17`. Cuatro fuentes siguen exactas a FIX1 verificada; no se sobrescriben originales, snapshots ni resultados.

| # | Grado anterior/actual | Gap | Veredicto ROOT | Evidencia |
|---|---|---|---|---|
| A01 | Important anterior | Fade sin RED causal | corregido intento2 | A2 reproduce nueve fade originalPASS→retiradoFAIL→reescritoPASS y secuencia propia |
| B01 | Important anterior | Unión objeto abierta | corregido intento2 | A2/B2; diez posiciones negativas y RED original→GREEN |
| B02 | Important anterior | Mapas/const tratados como schemas | corregido contraejemplos originales intento2 | A2/B2; literals/property-names y refs positivos; nuevo caso distinto en B03 |
| B03 | Important nuevo | Guarda exige cierre a tipos que excluyen objeto | pendiente FIX2 | recipes.py:996; string/required[], integer/minProperties0 y array/propertyNames válidos; prior ACCEPT→FIX1 RECIPE_INVALID |

FIX2 obligatoria mediante implementer fresco, misma representación/contrato aprobado y TDD causal. Revisión producto intento3 de3 tras corrección; QA independiente pendiente antes de cierre. No aceptación T02/M2, generación musical ni runtime M1.

## Lente A — salida completa

Lente A · intento 2 de 3 · diff `21a30e8dac7deb97ac22c676351f5eebe99fcf17...snapshot` (3 ficheros; `correction.diff` completo leído).

**Sin defectos nuevos: 0 Critical / 0 Important / 0 Minor. A01/B01/B02 corregidos.**

Referencias: R=`apps/server/app/creative/recipes.py`; T=`apps/server/tests/test_creative_recipes.py`; D=`docs/arquitectura/iteracion-creativa.md`. Líneas del snapshot. PA=`prior-review1.md`, tabla completa de A; sus criterios aprobados se conservan sin reabrir.

| Criterio T-02 / contrato | ✓/✗/no verificable | Evidencia |
|---|---|---|
| Mutar nested no cambia bytes/hash | ✓ | PA aprobado; suite propia del snapshot 169 PASS |
| Rechazar extras, secretos, NaN e IDs/refs inválidos | ✓ | PA aprobado; 169 PASS |
| Conservar padres y campos efectivos | ✓ | PA aprobado; 169 PASS |
| Legacy sin reescritura | ✓ | PA aprobado; 169 PASS |
| Verificación propia ejecutada y entregada | ✓ | `verification-final.receipt.json`: comando declarado, exit0, UTC y cuatro SHA finales |
| Revisión/QA conformes antes de cierre | no verificable | T-02 sigue `en-progreso`; QA independiente pendiente, sin cierre atribuido |
| TDD antes del comportamiento corregido | ✓ | Ocho pares causales, 14 casos; mismos SHA de tests y RED anterior al GREEN. Preimágenes y reproducción propia detalladas abajo |
| Alcance y ownership | ✓ | Recibo ROOT:3 cambiados/0 fuera/0 avisos/0 exclusiones usuario; coinciden con `Archivos` T-02 |
| §4.1–4.3 envelope, versión, límites, tipos y canonicalización | ✓ | PA aprobado; corrección no altera estos contratos |
| §4.4 pertenencia, antecedentes y raíz | ✓ | PA aprobado; 169 PASS |
| §4.5 letra histórica, autoría y composite | ✓ | PA aprobado; 169 PASS |
| §4.6 descriptor aislado y lectura sin defaults nuevos | ✓ | PA aprobado; helpers M1 importados realmente desde snapshot |
| §4.6 selección, schemas cerrados y capacidades | ✓ | R:941,976,981; T:657,666,677,696; tres contraejemplos y dos refs reproducidos antes/después |
| §4.6 pins y ausencia de autoridad runtime | ✓ | PA aprobado; corrección no modifica selección ni autorización |
| §4.7 operaciones, cardinalidad y mapas exactos | ✓ | R:829; T:774,793,801,806; nueve casos fade original PASS→cuerpo retirado FAIL→final PASS |
| §4.7 basis ganador, salida y params exactos | ✓ | PA aprobado; 169 PASS |
| §4.8 wrappers/readers/hash externo y embebido | ✓ | PA aprobado; 169 PASS |
| §4.8 proyección `/v1`, inputs/media/roles y master/source | ✓ | PA aprobado; 169 PASS |
| §4.9 privacidad y errores sin entrada encadenada | ✓ | PA aprobado; corrección mantiene las guardas |
| §4.9 históricos con ausencias/nulls/raw y seed grande | ✓ | PA aprobado; 169 PASS |
| Cobertura como apoyo | ✓ | `coverage-final.json`:88,49356548% combinado del módulo completo,915 statements/406 branches/0 exclusiones; recibo exit0. No sustituye QA |
| Constitución: server sin torch, inferencia/CPU, historia y derechos | ✓ | PA aprobado; Constitución:31; corrección sólo validación pura |
| Constitución: unidades, idioma y ledger | ✓ | Constitución:65,71; mapas en segundos, prosa castellana; ledger sin modificaciones del actor |
| Generados y documentación descriptiva | ✓ | D:72–77 describe la corrección y coincide con R:976–1036; docs-style aplicado. Export interop no aplica: sin `commands/`, `agents/`, `hooks/` |
| Límite de autoridad T-02 | ✓ | PA aprobado; conserva alcance CPU privado, sin aceptación M1/M2 |

| Gap anterior | Estado | Evidencia concreta |
|---|---|---|
| A01 — fade sin RED causal | corregido | Preimagen RED SHA `e909b086…` contiene sólo `keep` identidad: cuerpo fade eliminado. Nueve casos funcionales fallan ahí y pasan tras reescritura. `red2-fade-partition`→`green2-fade-partition` conserva exactamente el test corregido |
| B01 — unión objeto abierta | corregido | T:657 falla originalmente porque la captura acepta `undeclared`; final rechaza con `RECIPE_INVALID`. R:981 reconoce `object` dentro de `type` array |
| B02 — mapas/const tratados como schemas | corregido | T:666/677:original `RECIPE_INVALID`, final PASS con params fieles. R:976 distingue posiciones; T:696 prueba refs `#`/`#node`, RED→GREEN |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| — | — | Sin hallazgos nuevos | T-02 | — | — |

Lo ejecutado:

- Entorno gestionado y `.venv/Scripts/python.exe -B`; auditoría **244 artefactos**, **158 fuentes del snapshot**, cuatro fuentes finales y SHA de `correction.diff`: coincidencias exactas.
- `pytest.main` sobre snapshot, `--noconftest -p no:cacheprovider -o addopts=`: **169 passed**, exit0; un aviso `cache_dir` por desactivar el proveedor.
- **16 imports auténticos** del snapshot y equivalencia de `ResolutionError`, `closed_schema`, `SyntheticBinding` y `ModelDescriptor`. Sólo paquete raíz `app` preparado para evitar bootstrap; ningún helper sustituido.
- Reproducción causal propia: **9 fade + 3 schemas + 2 refs**; resultados concordantes con los ocho pares históricos. UTC ordenadas y mismo SHA del test en cada par.
- Diagnóstico inicial fade exit1 conservado y correctamente identificado: cambió únicamente la expectativa `RECIPE_CONTEXT_MISMATCH`→`RECIPE_INVALID`; después retiró nuevamente el cuerpo y repitió RED→GREEN. Las caracterizaciones posteriores no se cuentan como RED.
- Dos diagnósticos auxiliares de lectura/impresión fallaron por codificación Windows; repetidos con UTF-8. No afectaron a las ejecuciones funcionales ni modificaron artefactos.

Fuera de mi lente: ninguno. Sin `docs/knowledge/` en snapshot; contrato aprobado/ADR contrastados directamente. QA independiente e integración real pendientes; esta revisión no cierra T-02 ni acepta M1/M2. Sin escrituras, BD, Git, red, Docker, WSL o GPU.


## Lente B — salida completa

Lente B · intento 2 · diff `21a30e8dac7deb97ac22c676351f5eebe99fcf17...snapshot` (3 ficheros; correction.diff completo leído).

`R` = `apps/server/app/creative/recipes.py`, dentro del snapshot inmutable.

| Criterio / objetivo T-02 | ✓/✗/no verificable | Evidencia |
|---|---|---|
| B01: cerrar objetos en unions | ✓ · corregido | R:981–999; negativos en diez posiciones schema rechazan con `RECIPE_INVALID` |
| B02: distinguir mapas y literales | ✓ · contraejemplos originales corregidos | Suite169 PASS; ocho nombres de propiedades reservados capturan y hacen roundtrip |
| Refs locales y privacidad | ✓ | Anchor y pointer escapado aceptados; ref ausente/externo rechazada sin field/cause/context; cero eventos de socket |
| Regresiones de cierre sobre tipos no objeto | ✗ | R:996; tres comparativos propios `PRIOR ACCEPT → CURRENT RECIPE_INVALID` |
| A01: comportamiento fade | ✓ funcional; causalidad TDD fuera de B | Casos fade actuales ejecutados dentro de169 PASS |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| B03 | Important | La nueva guarda exige cierre a schemas cuyo tipo explícito excluye objetos | T-02 | `apps/server/app/creative/recipes.py:996` | Schema raíz cerrado con `properties.payload={"type":"string","required":[]}`; params `{"payload":"artistic setting"}`. `Draft202012Validator.check_schema/is_valid` pasan y la implementación previa permite captura; FIX1 devuelve `RECIPE_INVALID`. `required` no aplica a strings. También reproducido con `integer/minProperties:0` y `array/propertyNames:{type:string}`. No existe objeto abierto en estos casos. |

Lo ejecutado: Python gestionado `-B`, pytest sin conftest/caché → **169 passed, exit0**; **22 probes adicionales, exit0**; tres comparativos anteriores/actuales reproducen B03. Imports del snapshot acreditados por path/SHA; recipes SHA `65a5e8b1ea75c47d881475f959521adaafc925088c6977e62328ea6025718615`. `ResolutionError` y `closed_schema` compilados literalmente desde AST; contracts y DTO importados realmente. Un probe inicial omitió `schema_version` del reader; corregido y repetido. Aviso pytest por `cache_dir` al desactivar caché.

Fuera de mi lente: causalidad TDD A01 y seguridad integral. Sin `docs/knowledge/` en snapshot; persona backend aplicada. Sin escrituras, bootstrap, BD, GPU, Docker, WSL o red. T-02 abierta y QA pendiente.

