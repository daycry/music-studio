# Revisión de dos lentes — intento 1: compositor puro T03

ROOT 2026-10-11T15:35:46.493130+00:00: A/B frescas,0Critical/1Important/0Minor. C/DautoFalse,2ficheros enalcance sinexclusiones. A01 confirmado por obligación explícita del contratoAC01 yguarda runtime correcta; no bug de producción. AC15freeze conserva assertionscausales yAC17wrapperRED aceptados porA, purezaAC17regresión identificada.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Falta negativo fade sum>N trasrounding | T-03 | pendienteFIX1 fresco | 4.95+5.05seconds→50+51frames>N100; runtime rechaza, test ausente |

## Lente A

Lente A · intento 1/3 · diff `b92e4ce4483036a97548e35c584e3ac153533861...HEAD` ∪ archivos nuevos (2 ficheros)

**Veredicto: 0 Critical, 1 Important, 0 Minor.** El comportamiento observado es correcto; falta una regresión exigida expresamente por AC01.

Referencias: `C` = `apps/server/app/creative/composition.py`; `T` = `apps/server/tests/test_creative_composition.py`. Líneas del snapshot revisado. Diff completo leído por archivos: C1208/T1152 líneas; reconstrucción comparada con `source.diff` y fuentes byte exactas.

| Criterio (T-03 / objetivo) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| AC01 · trim/fade, negativos y cuentas | ✗ | T244/T800/T947 cubren cuentas, regiones inválidas y centro vacío. Falta negativo `Fin+Fout>N` por redondeo; C895 aparece entre líneas no cubiertas. Probe propio confirma rechazo correcto. |
| AC02 · decimal half-up, exponentes y signed zero | ✓ | C584/C746; T158/T761. RED/GREEN decimal y signed-zero funcionales conservados. |
| AC03 · colapso y rampa mínima | ✓ | C1142; T236/T261/T932. RED singleton/colapso seguido de GREEN; rampa de 2 frames aceptada. |
| AC04 · números exactos y revalidación | ✓ | C28/C34/C608; T166/T191/T1037. bool, strings, Decimal y no finitos rechazados; facts manipulados revalidados. |
| AC05 · límites numéricos/estructurales | ✓ | C585/C713/C719/C1153; T183/T668/T777/T1048. MAX aceptado sin audio; overflow/suma/depth/colección/bytes rechazados. |
| AC06 · duración medida y bindings | ✓ | C72/C757; T216/T274/T849. Snapshot, identidad, SHA, formato y duración incoherentes rechazados. |
| AC07 · extremos anclados sin clamp | ✓ | C626; T223. N/rate→N; `nextafter(duration,+inf)` rechazado. |
| AC08 · ambos padres, roles y raíces originales | ✓ | C757/C782/C1095; T294/T832. Ambos mapas preservados; inversión/falta de padres rechazada; mínimo entre raíces originales. |
| AC09 · conversión explícita y facts/pins | ✓ | C645/C687/C1035; T334/T889/T1087. Tramos convertidos usan `convert`; faltantes, scope parcial, pin/target/binding incorrectos y extras rechazados. |
| AC10 · cola nominal vacía y políticas | ✓ | C99/C1035; T422/T989/T1007. Bc81 conserva cola; Bc80 la omite; Bc79 falla. Políticas identity/duplicate/average comprobadas. |
| AC11 · repaint full/region y grids locales | ✓ | C901; T379/T517. 105 frames en ambos shapes con piezas diferentes; región global[6,8) consume engine local completo; full80 rechazado/full81 aceptado. |
| AC12 · engine binding y ensamblado único | ✓ | C784/C980; T409/T446/T1135. Hash/shape/facts incompatibles rechazados; full convertido usa una pieza. |
| AC13 · extend/extremos y duración efectiva | ✓ | C909/C913/C1137; T490. at0/atN, keeps vacíos omitidos, full demasiado corto rechazado; duración deriva de frames. |
| AC14 · claims y estado sin acreditar audio | ✓ | C460/C466/C959; T471/T1063. Full `declared_keep_unverified`, region `direct_copy`, estado `resolved_unrendered`; fuentes incompatibles rechazadas. |
| AC15 · congelación y conservación de receta | ✓ | C47/C509; T361. RED real por DTO mutable y GREEN con congelación. Diferencia AST analizada: retiró únicamente 12 líneas ajenas de conversión, recolocadas en T334; aserciones de freeze conservadas. |
| AC16 · codec/replay, dominio y tamper | ✓ | C1149/C1194; T614/T732/T820/T967/T1106. Replay de ocho operaciones; bytes no canónicos, duplicados, versiones y mapas manipulados rechazados. |
| AC17 · pureza y wrapper | ✓ | C1–22/C737; T550. Sin imports directos/calls de audio/GPU/SQL/I/O; spy `open` pasa. RED acredita revalidación del wrapper; pureza declarada correctamente como regresión ya verde. |
| AC18 · errores sanitizados/readers históricos | ✓ | C541; T599/T1021. Error sólo código, sin cause/context/input secreto; mediciones ausentes producen `COMPOSITION_FACTS_REQUIRED`. Readers M1 intactos. |
| T-03 · negativos y full/region probados | ✗ | `tasks.md:144`; único hueco identificado: negativo redondeado de fades, A01. |
| T-03 · roles/formato y convert explícito | ✓ | `tasks.md:145`; C994/C1035 y T294/T334/T422. |
| T-03 · verificación y puertas completas | no verificable | `tasks.md:130/146`: sigue `en-progreso`. Verificación del actor89PASS confirmada por ejecución propia; QA independiente todavía pendiente. No se atribuye cierre. |
| TDD por comportamiento | ✓ para evidencia presentada | Auditoría propia de 18 pares primarios: preimages SHA, JUnit RED1/GREEN0, procesos reaped y orden temporal. AC15/AC17 examinados semánticamente; diagnósticos de fixtures/import/cwd no acreditados como RED. |
| Alcance | ✓ | `scope.stdout`: 2 en alcance, 0 fuera, 0 avisos, 0 exclusiones. `git status --short` privado muestra únicamente los dos archivos nuevos declarados por T-03. |
| Constitución y ADR-0079 | ✓ | Constitución:11/18/22/24/33–36; DTO privado puro, sin escritura de take/BD, modelo, pesos o contrato público. Hechos sintéticos identificados; no acreditan autoridad/audio reales. |
| Generados/interoperabilidad | ✓ · no aplica | Diff no toca `commands/`, `agents/`, `hooks/`, contratos públicos ni generados. Documentación contractual ya preparada; producto permanece privado. |
| Cobertura como apoyo | ✓ | Coverage.py oficial del actor: 545/576 líneas =94,618056%; 229/260 ramas =88,076923%; 0 líneas excluidas. Se verificaron datos/manifiesto; no sustituye lectura de tests ni QA. |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| A01 | Important | Falta el negativo obligatorio de suma de fades tras resolver muestras | M2/T-03 · AC01 | `apps/server/tests/test_creative_composition.py:947`; guarda en `apps/server/app/creative/composition.py:894` | Padre100@10Hz, fade-in4,95s y fade-out5,05s: receta T02 válida porque suma10s; half-up produce50+51=101>N100. El builder devuelve correctamente `COMPOSITION_OUT_OF_BOUNDS`, pero ningún test entregado ejercita esa guarda (C895 no cubierta). `composition-contract-design.md:273` exige explícitamente «fade sum>N rechazados» y `tasks.md:144` exige negativos de duración probados. |

Lo ejecutado:

- Python gestionado, `. ./scripts/env.ps1`; `uv run --frozen --no-sync --all-packages python -X utf8 -B -`, invocando pytest sobre el snapshot → **89 passed**, 1 warning de importación previa de anyio, exit0. Imports de composition/recipes observados en el snapshot. JUnit propio: `.cache/dev-cycle/m2/creative-composition-t03-product-review1-a-evidence-20261011/junit.xml`.
- Auditoría independiente → **660 artefactos SHA verificados**, 92 recibos/streams examinados, 18 pares primarios con causalidad verificada; fuentes finales byte exactas.
- Probe del hueco → control(4,96;5,04) produce100 frames; negativo(4,95;5,05) produce `COMPOSITION_OUT_OF_BOUNDS`.
- Consulta `knowledge-find.py --tipo adr --tipo-tarea backend --contexto "Compositores cerrados y mapas temporales puros" --iniciativa m2-iteracion-creativa` → sin aciertos.
- Primer lanzamiento propio falló por quoting/SyntaxError antes de ejecutar pruebas; no se cuenta como RED ni fallo de producto.

Fuera de mi lente (no reportado): ninguno. C/D oficiales `false`. Sin audio/render, SQL, publicación, capacidades reales ni aceptación M2 acreditadas.


## Lente B

Lente B · intento 1/3 · diff b92e4ce4483036a97548e35c584e3ac153533861…candidato privado (2 ficheros)

**Sin defectos de corrección reproducidos.** Leído el diff completo, dividido en runtime de 1208 líneas y tests de 1152 líneas. Persona backend aplicada; consulta `knowledge-find.py` sin aciertos.

Las referencias siguientes corresponden al snapshot de `.cache/dev-cycle/m2/creative-composition-t03-product-review1-20261011/snapshot`; `test` significa `apps/server/tests/test_creative_composition.py`.

| Criterio (T-03) | ✓/✗/no verificable | Evidencia ejecutada o leída |
|---|---|---|
| AC01 Operaciones e intervalos | ✓ | `test:244,800,947`: trim/fade, negativos y centro vacío; PASS |
| AC02 Half-up decimal y cero firmado | ✓ | `test:158,761`; adicionalmente 60 comparaciones con oráculo racional exacto |
| AC03 Colapso y rampas mínimas | ✓ | `test:236,261,932`: cero y singleton rechazados; PASS |
| AC04 Tipos estrictos y revalidación | ✓ | `test:166,191,1037`: bool, coerciones y DTO alterados; PASS |
| AC05 Límites aritméticos/estructurales | ✓ | `test:183,668,777,1048`: overflow, profundidad y colecciones; PASS |
| AC06 Facts, duración y bindings | ✓ | `test:216,274,849`: identidad/hash/formato/duración; PASS |
| AC07 Extremos medidos y bounds | ✓ | `test:223`: anclaje N y `nextafter` fuera; PASS |
| AC08 Dos padres, roles y raíces originales | ✓ | `test:294,832`; inversión/faltantes rechazados; PASS |
| AC09 Conversión completa y pin | ✓ | `test:334,889,1087`: scope, evidence, pin y facts extra; PASS |
| AC10 Cola nominal vacía y políticas | ✓ | `test:422,989,1007`: Bc81/80/79 y duplicación/promedio; PASS |
| AC11 Repaint full/region y grids locales | ✓ | `test:379,517`: counts distintos y región global [6,8) sobre salida local; PASS |
| AC12 Ocho operaciones y ensamblado único | ✓ | `test:409,446,1135`; probe adicional de 10 combinaciones operación/shape |
| AC13 Extend y keeps vacíos | ✓ | `test:490`: zero/end/full demasiado corto y repaint completo; PASS |
| AC14 Claims y fuentes honestas | ✓ | `test:471,1063`: full declarado, region directo, status unrendered; PASS |
| AC15 Inmutabilidad funcional | ✓ | `test:361`: nested DTO/wrapper/dump/input; PASS; causalidad TDD fuera de B |
| AC16 Codec, replay y tampering | ✓ | `test:614,732,820,967,1106`; 44 manipulaciones adicionales rechazadas |
| AC17 Pureza y preservación T02/M1 | ✓ | `test:550`, lectura completa de imports/calls; regresión T02 183 PASS |
| AC18 Errores sanitizados | ✓ | `test:599,1021`; probes comprueban mensaje sólo código y cause/context ausentes |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| — | — | Sin defectos | T-03 | — | — |

Lo ejecutado:

- Entorno gestionado mediante `. .\scripts\env.ps1`; `uv run --frozen --no-sync --all-packages python -X utf8 -B`, imports dirigidos al snapshot.
- `pytest.main` sobre composition + recipes, `--noconftest -p no:cacheprovider --rootdir=<snapshot>` → **272 PASS**, dos warnings del arnés: módulo anyio ya importado y opción `cache_dir` desconocida al desactivar su plugin.
- Probe independiente → **60 comprobaciones de redondeo, 10 planes operación/shape, 44 rechazos sanitizados**, exit 0.
- SHA finales intactos: runtime `f2b5a79f…`; tests `67eb4757…`. Archivos canónicos aún ausentes. Sin escritura de fuentes, ledger ni Git.

Fuera de mi lente (no reportado): causalidad TDD de AC15/AC17 corresponde a A. Esta revisión no acredita QA de producto, render ni audio real.
