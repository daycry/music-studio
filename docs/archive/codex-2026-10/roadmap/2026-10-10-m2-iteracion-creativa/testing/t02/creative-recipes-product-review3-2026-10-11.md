# Revisión de producto T-02 — intento 3 de 3 — 2026-10-11T12:49:07.125071+00:00

ROOT fusiona las dos lentes frescas completas: **0 Critical / 0 Important / 0 Minor**. B03 corregido en intento3; A01/B01/B02 permanecen corregidos desde intento2. No se reabren criterios aprobados sin evidencia nueva. C/D auto false sobre el diff completo de tres archivos; C1 limpia conservada. Scope oficial3/0fuera/0avisos/0exclusionesusuario. Ninguna tarea se cierra con esta revisión: QA independiente pendiente.

| # | Grado anterior | Gap | Tarea | Veredicto actual | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Fade sin RED causal | T-02 | corregido intento2, conservado | FIX2 no cambia fade; pares FIX1 y juicio A2 conservados |
| B01 | Important | Unión objeto abierta | T-02 | corregido intento2, conservado | A3/B3 prueban objetos explícitos, uniones y cierre implícito |
| B02 | Important | Mapas/const tratados como schemas | T-02 | originales corregidos intento2, conservado | A3/B3 prueban mapas/literales/refs locales; recorrido intacto |
| B03 | Important | Cierre exigido a tipos que excluyen objetos | T-02 | corregido intento3 | R996; tres pares RED→GREEN y comparativos independientes A3/B3 |

ROOT verificó136artefactosFIX2/219originales/244FIX1/158snapshot anterior y tresREDcausales con tests idénticos. La verificación declarada tiene183PASS/exit0 sinJUnit; cobertura oficial separada183JUnit/88,502269%0excl. Las dos lentes ejecutaron183PASS independientes; B añade205probes, A cinco negativos y tres comparativos. Estos resultados no prueban música, render, SQL/admission, UI ni almacenamiento M1. T02 sigue abierto hasta QA.

Evidencia privada preservada: `.cache/dev-cycle/m2/creative-recipes-t02-product-review3-20261011/prepare-root.receipt.json`, `release-root.receipt.json`, `response-a.md` y `response-b.md`; preimágenes FIX2 intactas. Respuestas completas a continuación, sin sustituirlas por una conclusión resumida.

## Lente A — salida completa

Lente A · intento 3 de 3 · diff `b52b72dfa155aa971e346279d42adff5f00c34f4...snapshot` (3 ficheros; `correction.diff` completo leído).

**Sin defectos nuevos: 0 Critical / 0 Important / 0 Minor. B03 corregido.** A01/B01/B02 conservan los veredictos anteriores. T-02 continúa `en-progreso`; QA independiente pendiente.

Referencias relativas al snapshot `.cache/dev-cycle/m2/creative-recipes-t02-product-review3-20261011/snapshot/`: R=`apps/server/app/creative/recipes.py`; T=`apps/server/tests/test_creative_recipes.py`; D=`docs/arquitectura/iteracion-creativa.md`; L=`docs/roadmap/2026-10-10-m2-iteracion-creativa/tasks.md`; C=`docs/CONSTITUTION.md`. F=`.cache/dev-cycle/m2/creative-recipes-t02-product-fix2-20261011/`. Tabla completa previa y respuestas A/B leídas; criterios aprobados conservados sin reapertura.

| Criterio T-02 / contrato | ✓/✗/no verificable | Evidencia |
|---|---|---|
| Mutar nested no cambia bytes/hash | ✓ conservado | T:197,1061,1088; criterio previamente aprobado; suite propia actual 183 PASS |
| Rechazar extras, secretos, NaN e IDs/refs inválidos | ✓ conservado | T:245,973,1253,1292; cambios limitados a cierre de schemas; 183 PASS |
| Conservar padres y campos efectivos | ✓ conservado | T:397,483,1343; previamente aprobado; 183 PASS |
| Legacy sin reescritura | ✓ conservado | T:211,321,1026; previamente aprobado; 183 PASS |
| Verificación propia ejecutada y entregada | ✓ | `F/verification-final.receipt.json`: argv exactamente `uv run pytest -q apps/server/tests/test_creative_recipes.py`, exit0, UTC y cuatro SHA antes/después; stdout **183 passed in 1.06s**. Este comando no lleva JUnit |
| Revisión/QA conformes antes de cierre | no verificable | L:98,114: tarea abierta; QA independiente pendiente. No se atribuye cierre ni aceptación |
| TDD antes del comportamiento corregido | ✓ | Tres pares `red-final-string/integer/array`→`green-string/integer/array`: RED exit1 por `RECIPE_INVALID`, GREEN exit0; mismo test SHA `add3236e…`, preimágenes verificadas y RED anterior al GREEN |
| Alcance y ownership | ✓ | L:105; `scope.stdout`:3 cambiados/0 fuera/0 avisos/0 exclusiones usuario. `git status --short` privado muestra exclusivamente R/T/D |
| §4.1–4.3 envelope, versión, límites, tipos y canonicalización | ✓ conservado | R:1297,1345,1369; T:279,299,996,1262; corrección no altera estos contratos |
| §4.4 pertenencia, antecedentes y raíz | ✓ conservado | T:245,397,423; previamente aprobado; 183 PASS |
| §4.5 letra histórica, autoría y composite | ✓ conservado | T:397,429,449,1343; previamente aprobado; 183 PASS |
| §4.6 descriptor aislado y lectura sin defaults nuevos | ✓ conservado | T:532; 16 módulos importados realmente desde snapshot; cuatro identidades M1 comprobadas |
| §4.6 selección, schemas cerrados y capacidades | ✓ reevaluado | R:941,981,996; T:657,700,778,793. Objetos explícitos, uniones con objeto y objetos implícitos siguen exigiendo `additionalProperties:false` |
| §4.6 schemas con tipo explícito que excluye objetos — B03 | ✓ corregido | R:996; T:680. Tres schemas válidos según `Draft202012Validator` reproducen **FIX1 `RECIPE_INVALID`→FIX2 captura con params fieles** |
| §4.6 validación de tipos no objeto | ✓ | T:721: siete tipos/unión aceptan su valor y rechazan objeto incompatible; controles preexistentes PASS antes del fix, sin atribuir RED |
| §4.6 mapas, literales y refs locales | ✓ conservado y comprobado | R:1001,1007,1016,1030; T:733,744,763,807. Recorrido intacto en diff; suite actual pasa |
| §4.6 pins y ausencia de autoridad runtime | ✓ conservado | T:1096,1145,1181; imports/helpers M1 auténticos, sin modificación de su contrato |
| §4.7 operaciones, cardinalidad y mapas exactos | ✓ conservado | R:798; T:841,860,868,873,896,946; A01 corregido en intento2, 183 PASS actuales |
| §4.7 basis ganador, salida y params exactos | ✓ conservado | T:483,508,1297; previamente aprobado; 183 PASS |
| §4.8 wrappers/readers/hash externo y embebido | ✓ conservado | R:1369,1383; T:279,996,1277; previamente aprobado |
| §4.8 proyección `/v1`, inputs/media/roles y master/source | ✓ conservado | T:251,583,592,603,1038; previamente aprobado; 183 PASS |
| §4.9 privacidad y errores sin entrada encadenada | ✓ conservado | R:80; T:314,345,1156,1314; el fix no cambia estas guardas |
| §4.9 históricos con ausencias/nulls/raw y seed grande | ✓ conservado | T:211,321,1026,1230; previamente aprobado |
| Cobertura como apoyo | ✓ | `F/coverage-final.json`:**88,50226928895613%** combinado de líneas/ramas,916 statements/406 branches/0 exclusiones; comando oficial pytest-cov gate80 exit0,183 PASS. No se presenta como porcentaje exclusivo del diff |
| Constitución: server sin torch, historia y derechos | ✓ conservado | C:19,31,32,39,84; corrección exclusivamente en validación pura, sin inferencia, publicación ni escrituras históricas |
| Constitución: unidades, idioma y ledger | ✓ | C:63,65,71; D:78–80 en castellano; estado sólo L, sin cambios del actor al ledger |
| Generados y documentación descriptiva | ✓ | D:78–80 describe exactamente R:996–1000; `docs-style` leído y aplicado, sin infracción citable. Interop no aplica: diff sin `commands/`, `agents/` ni `hooks/`; exportación del schema sigue reservada a T-04 |
| Límite de autoridad T-02 | ✓ | L:98,114 y diseño contractual:36; entrega CPU privada, sin aceptación T-02/M1/M2 ni acreditación musical |

Tabla previa conservada y veredictos:

| # | Grado anterior | Gap | Tarea | Veredicto actual | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Fade sin RED causal | T-02 | corregido intento2, conservado | `prior-review2.md` / `prior-response-a.md`: nueve casos originalPASS→cuerpo retiradoFAIL→reescritoPASS y pares causales; FIX2 no toca fade; T:841–896 pasa |
| B01 | Important | Unión objeto abierta | T-02 | corregido intento2, conservado | R:981; T:657,700,778,793; unión con objeto sigue cerrada. Reproducción propia rechaza antes/después |
| B02 | Important | Mapas/const tratados como schemas | T-02 | contraejemplos originales corregidos intento2, conservado | R:1007–1035 intacto; T:733,744,763,807 pasa; no reapertura |
| B03 | Important | Cierre exigido a tipos que excluyen objetos | T-02 | **corregido intento3** | R:996; tres RED causales sobre runtime FIX1 SHA `65a5e8b1…`, GREEN sobre FIX2 SHA `d8eb0512…`; reproducción propia con mismos valores y params fieles |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| — | — | Sin hallazgos nuevos | T-02 | — | — |

Lo ejecutado:

- Entorno gestionado mediante `scripts/env.ps1` y `.venv/Scripts/python.exe -B`; sin Python de máquina.
- Auditoría propia SHA/tamaño: **136 artefactos FIX2 +219 originales +244 FIX1**, **158 fuentes snapshot actual +158 previo**, cuatro fuentes finales y hash del diff: coincidencias exactas.
- Auditoría de tres pares causales: preimágenes iguales a sus pins; fuentes antes/después intactas; mismo SHA del test; RED anterior al GREEN. Cada JUnit rojo contiene1 failure/0 errors; cada verde1 test/0 failures/errors.
- `pytest.main` sobre snapshot con `--noconftest --rootdir=<snapshot> -p no:cacheprovider -o addopts=` → **183 passed, exit0**. Aviso `cache_dir` debido a desactivar el proveedor de caché.
- **16 imports auténticos** desde el snapshot y equivalencia de `ResolutionError`, `closed_schema`, `SyntheticBinding` y `ModelDescriptor`. Sólo paquete raíz `app` preparado en memoria para evitar bootstrap; helpers sin sustitución.
- Reproducción causal propia del `validate_schema` literal obtenido por AST de la preimagen RED: **3 casos FIX1 rechazados→FIX2 aceptados**; `check_schema/is_valid` conformes y params conservados.
- **5 controles de cierre** —objeto explícito, unión con objeto y tres objetos implícitos— rechazados tanto antes como después.
- Snapshot actual **158/158 SHA intactos después de ejecutar**. `git status` privado coincide con los tres archivos declarados.
- Diagnósticos auxiliares propios de lectura fallaron por codificación/alias de encoding y resolución inicial de rutas del manifest FIX1; corregidos y repetidos. Sin efectos funcionales ni modificaciones de artefactos.

Fuera de mi lente: ninguno. C/D auto false según selector oficial; C1 limpia conservada. Tier oficial `fuente.model/effort=frontmatter`, sin overrides. Sin `docs/knowledge/` en snapshot; constitución, ADR-0077 y diseño aprobado contrastados directamente. QA independiente e integración real pendientes. Sin escrituras de archivos, ledger, markers, Git, BD, modelos, servicios, Docker, WSL o GPU.


## Lente B — salida completa

Lente B · intento 3 de 3 · diff `b52b72dfa155aa971e346279d42adff5f00c34f4...snapshot` (3 ficheros; `correction.diff` completo leído).

**Sin defectos: 0 Critical / 0 Important / 0 Minor. B03 corregido.**

R=`apps/server/app/creative/recipes.py`; T=`apps/server/tests/test_creative_recipes.py`. Referencias al snapshot congelado.

| Criterio / objetivo T-02 | ✓/✗/no verificable | Evidencia |
|---|---|---|
| B03: keywords de objeto con tipos explícitos no objeto | ✓ | R:996; T:680. Tres comparativos propios: FIX1 `RECIPE_INVALID` → FIX2 acepta string/required, integer/minProperties y array/propertyNames; params y reader/hash exactos |
| Conservar semántica Draft 2020-12 | ✓ | 70 positivos propios: siete tipos × diez keywords de objeto; `check_schema` y validación oficial conformes |
| Mantener validación de tipos | ✓ | R:1094; otros 70 casos propios rechazan objetos incompatibles; seis declaraciones `type` malformadas rechazadas |
| B01: objetos, uniones e implícitos cerrados | ✓ | R:981,996; 20 nodos abiertos rechazados; cinco cerrados aceptados y sus extras rechazados |
| B02: distinguir mapas y literales | ✓ | R:976,1008; diez nombres de propiedades reservados y cuatro literales const/default/enum/examples aceptados |
| Refs locales y recursión | ✓ | R:1001; pointers, anchor y pointer escapado aceptados; missing/externa rechazados; recursión `#`/`#node` aceptada |
| Privacidad y entradas límite | ✓ | Errores propios sin field/cause/context; texto excesivo, NaN, token y Bearer rechazados sin exponer sentinel |
| Pureza y lectura fiel | ✓ | Positivos propios preservan schemas de entrada, params, bytes/hash; mutar vistas no altera captura; snapshot158 intacto antes/después |
| A01: comportamiento fade previamente aprobado | ✓ funcional conservado | Suite propia183 PASS; corrección no modifica fade. Causalidad TDD corresponde a A |
| QA independiente y aceptación T-02/M2 | no verificable | Pendientes; esta revisión no acredita cierre |

| Gap anterior | Estado actual | Evidencia |
|---|---|---|
| A01 Important — fade sin RED causal | Corregido intento2, conservado | Veredicto anterior; ningún cambio nuevo en fade |
| B01 Important — unión objeto abierta | Corregido intento2, conservado | R:981 y negativos propios |
| B02 Important — mapas/const tratados como schemas | Corregido intento2, conservado | Mapas y literales positivos propios |
| B03 Important — cierre exigido a tipos no objeto | Corregido intento3 | R:996; tres comparativos propios y tres pares históricos RED→GREEN |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| — | — | Sin hallazgos | T-02 | — | — |

Lo ejecutado:

- Python gestionado mediante `scripts/env.ps1`, `python -X utf8 -B`; `pytest.main` sobre snapshot, sin conftest/caché: **183 passed, exit0**. Un aviso `cache_dir` por desactivar su proveedor.
- **205 probes propios PASS, exit0**, incluidos los tres comparativos causales funcionales contra la preimagen FIX1.
- Imports auténticos de recipes, queue.inputs, queue.resolver, worker.contracts y engine_contract; cuatro identidades coincidentes. Sólo namespace raíz `app` preparado para evitar bootstrap; ningún helper sustituido.
- Auditoría SHA/bytes: **136 artefactos FIX2, 219 originales, 244 FIX1 y 158 fuentes anteriores** intactos; snapshot actual158 y diff exactos.
- Tres `red-final-*` fallan funcionalmente con `RECIPE_INVALID`; sus `green-*` pasan con idénticos SHA de tests y RED anterior a GREEN. Once controles anteriores ya PASS, sin atribuirles RED.
- Recibo de verificación exacta `uv run pytest -q apps/server/tests/test_creative_recipes.py`:183 PASS/exit0. Cobertura entregada:183 casos, whole **88,502269%**, cero exclusiones; apoyo leído, sin sustituir QA.

Fuera de mi lente: causalidad TDD y conformidad formal corresponden a A. C/D auto false y C1 limpia conservadas, sin ejecutarlas aquí. Persona backend aplicada; snapshot sin `docs/knowledge/`. Sin escrituras, ledger, markers, Git, BD, instalaciones, GPU, Ollama o servicios. T-02/M2 siguen sin aceptación.
