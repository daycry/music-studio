# Revisión de dos lentes — intento 2: compositor puro T03

ROOT 2026-10-11T15:51:38.984405+00:00: A/B frescas,0Critical/Important/Minor. A01regresiónobligatoriacorrecta yTDDcausalreescrituraguardaexistente confirmado. Runtimef2b5a79byteexact/FIX213/95nonowned,91focal183T02274combinados,whole94.79/88.46sinexclusiones. C/DautoFalse,scope2sinavisos/excl. Originales intactos; QAindependiente/CAS/cierreT03pendientes.

Nota de precisión deB2: B2 confirma auditado source.diff/snapshotreview2 SHA433a842b, runtimef2b5a79/tests2c5464e/274PASS. Encabezado anterior arrastró base review1; correcto0b70074668d680d3656f115edeb8b2dcd12a967d. Resto veredicto sin cambios, no nueva revisión ni mutaciónfuentes. Originalrespuestaconencabezadovietjo conservada íntegra;correcciónindependiente deautoradjunta.

| # | Grado anterior | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Negativo fade sum>N ausente | T03 | corregidoFIX1/review2 | T1155negativo/T1169control, ambaslentes274PASSpropias |

## Lente A

Lente A · intento 2/3 · diff `0b70074668d680d3656f115edeb8b2dcd12a967d...HEAD` ∪ archivos nuevos (2 ficheros)

**A01 corregido. 0 Critical, 0 Important, 0 Minor pendientes.**

Leídos literal A, respuestas A/B completas del intento anterior, `source.diff` completo dividido por archivos y `fix-only.diff`. Se reevalúa exclusivamente FIX1; los criterios aprobados conservan su veredicto. `C` = `apps/server/app/creative/composition.py`; `T` = `apps/server/tests/test_creative_composition.py`, dentro del snapshot review2. C1208/T1185 líneas.

| Criterio (T-03 / objetivo) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| AC01 · trim/fade, negativos y cuentas | ✓ · corregido | T1155 prueba receta válida4.95+5.05=10s, padre100@10Hz y resolución50+51>N; exige `COMPOSITION_OUT_OF_BOUNDS` sanitizado. T1169 controla50+50=N, piezas/mapas exactos y ausencia de keep central. Ejecución propia PASS. |
| AC02 · decimal half-up, exponentes y signed zero | ✓ · conservado | C584/C746; T158/T761. Evidencia previa conservada; pruebas originales byteexactas y ejecución propia PASS. |
| AC03 · colapso y rampa mínima | ✓ · conservado | C1142; T236/T261/T932. Singleton/colapso rechazados y rampa2 aceptada; PASS. |
| AC04 · números exactos y revalidación | ✓ · conservado | C28/C34/C608; T166/T191/T1037. Tipos estrictos y facts manipulados; PASS. |
| AC05 · límites numéricos/estructurales | ✓ · conservado | C585/C713/C719/C1153; T183/T668/T777/T1048. MAX, overflow, profundidad, colecciones y bytes; PASS. |
| AC06 · duración medida y bindings | ✓ · conservado | C72/C757; T216/T274/T849. Identidad, SHA, formato y duración; PASS. |
| AC07 · extremos anclados sin clamp | ✓ · conservado | C626; T223. N/rate→N y `nextafter` fuera rechazado; PASS. |
| AC08 · ambos padres, roles y raíces originales | ✓ · conservado | C757/C782/C1095; T294/T832. Mapas/roles y mínimo entre raíces originales; PASS. |
| AC09 · conversión explícita y facts/pins | ✓ · conservado | C645/C687/C1035; T334/T889/T1087. `convert`, scope completo y bindings/pins; PASS. |
| AC10 · cola nominal vacía y políticas | ✓ · conservado | C99/C1035; T422/T989/T1007. Bc81/80/79 y políticas de canales; PASS. |
| AC11 · repaint full/region y grids locales | ✓ · conservado | C901; T379/T517. Counts, piezas y coordenadas locales; PASS. |
| AC12 · engine binding y ensamblado único | ✓ · conservado | C784/C980; T409/T446/T1135. Binding/shape y una pieza full convertida; PASS. |
| AC13 · extend/extremos y duración efectiva | ✓ · conservado | C909/C913/C1137; T490. Extremos, keeps vacíos y duración derivada de frames; PASS. |
| AC14 · claims y estado sin acreditar audio | ✓ · conservado | C460/C466/C959; T471/T1063. Claims honestos y `resolved_unrendered`; PASS. |
| AC15 · congelación y conservación de receta | ✓ · conservado | C47/C509; T361. Veredicto anterior y evidencia causal conservados; función original byteexacta y PASS. No se reabre el traslado de assertions ya juzgado. |
| AC16 · codec/replay, dominio y tamper | ✓ · conservado | C1149/C1194; T614/T732/T820/T967/T1106. Replay/codec/tamper; PASS. |
| AC17 · pureza y wrapper | ✓ · conservado | C1–22/C737; T550. Runtime íntegro, spy `open` y wrapper; PASS. Pureza conserva su clasificación previa de regresión ya verde. |
| AC18 · errores sanitizados/readers históricos | ✓ · conservado | C541; T599/T1021 y nuevo T1155. Sólo código, cause/context ausentes; PASS. |
| T-03 · negativos y full/region probados | ✓ · corregido | `tasks.md:144`, contratoAC01 `composition-contract-design.md:273`; T1155 completa el único negativo pendiente. |
| T-03 · roles/formato y convert explícito | ✓ · conservado | `tasks.md:145`; C994/C1035 y T294/T334/T422; PASS. |
| T-03 · verificación y puertas completas | no verificable · conservado | `tasks.md:130/146`: tarea abierta. Pruebas propias274PASS; QA independiente aún pendiente. No se atribuye cierre. |
| TDD por comportamiento | ✓ · FIX1 comprobado | Preimage original→borrado exclusivo de guarda2líneas→RED AssertionError→reap→reescritura byteexacta→GREEN. Recibos, hashes, streams, JUnit y cronología comprobados. Los18pares previamente aprobados conservan su veredicto. |
| Alcance | ✓ | Snapshot97SHA verificados; `source.diff`/`fix-only.diff` autenticados. `scope.stdout`:2 en alcance,0 fuera,0 avisos,0 exclusiones. Status privado sólo C/T nuevos. FIX1 añade únicamente2tests. |
| Constitución y ADR-0079 | ✓ · conservado | Constitución:11/18/25/32/33/36; runtime puro intacto y dos regresiones sintéticas sin publicación/BD/modelos/audio. Sin contradicción nueva. |
| Generados/interoperabilidad | ✓ · no aplica | Diff no toca `commands/`, `agents/`, `hooks/` ni contratos públicos/generados. |
| Cobertura como apoyo | ✓ | Coverage.py oficial autenticado:546/576líneas=94,791667%;230/260ramas=88,461538%;0excluidas. C895 ahora ejecutada. No sustituye lectura de tests ni QA. |

Gaps:

| # | Grado anterior | Gap | Tarea | fichero:línea | Escenario concreto | Estado actual |
|---|---|---|---|---|---|---|
| A01 | Important | Negativo de suma de fades redondeados ausente | M2/T-03 · AC01 | T1155; guarda C894–895 | Padre100@10Hz,4.95/5.05→50+51=101>N100, con recetaT02 válida | **Corregido** por regresión negativa exacta y control pareado T1169; ambos PASS propios. |

La secuencia FIX1 acredita **reescritura causal de una guarda existente**. El runtime anterior ya rechazaba correctamente el caso; el RED documentado elimina exclusivamente esa guarda y comprueba la diferencia de código de error. No se presenta como descubrimiento de un bug ni como funcionalidad nueva.

Lo ejecutado:

- Entorno gestionado: `. .\scripts\env.ps1`; `uv run --frozen --no-sync --all-packages python -X utf8 -B -`.
- Auditoría propia → **213 payloads FIX1 y97fuentes snapshot SHA verificados**; diff completo y fix-only autenticados; original89tests como prefijo byteexacto; runtime final `f2b5a79f…` y tests `2c5464e9…`;95nonowned y mapas de custodia anteriores intactos.
- Auditoría causal → preimage RED elimina sólo2líneas; RED1/GREEN0; `deletion < REDstart < REDend/reap < rewrite < GREENstart`; streams/JUnit y fuentes antes/después coherentes.
- Pytest propio sobre composition+recipes del snapshot → **274 passed,0fail/error/skip**, exit0;91+183casos. Un aviso `cache_dir` por desactivar cacheprovider. JUnit: `.cache/dev-cycle/m2/creative-composition-t03-product-review2-a-evidence-20261011/junit.xml`.
- Imports observados de app/tests pertenecen al snapshot y sus SHA coinciden; fuentes finales intactas después de ejecutar.
- `knowledge-find.py --tipo adr --tipo-tarea backend --contexto "Compositores cerrados y mapas temporales puros" --iniciativa m2-iteracion-creativa` → sin aciertos, exit0.
- Un comando inicial de lectura falló por sintaxis PowerShell antes de leer/ejecutar producto; corregido y conservado en la conversación. No es RED ni fallo de producto.

Fuera de mi lente (no reportado): ninguno. B1 previa sin defectos conservada; C/D oficiales `false`. QA independiente, adopción canónica, cierreT03, render y audio real siguen pendientes.


## Lente B (original, con precisión anterior)

Lente B · intento 2/3 · diff `b92e4ce4483036a97548e35c584e3ac153533861…candidato privado` (2 ficheros; FIX1 modifica sólo tests).

**Sin defectos nuevos: 0 Critical, 0 Important, 0 Minor.** Diff completo leído por archivos: runtime1208/tests1185 líneas; reconstrucción exacta verificada. Veredictos B1 conservados, sin evidencia para reabrirlos.

| Criterio (T-03 / objetivo) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| FIX1 · rechazo tras half-up | ✓ | `apps/server/tests/test_creative_composition.py:1155`; probe propio: padre100@10Hz, 4.95/5.05→50+51=101; rechazo `COMPOSITION_OUT_OF_BOUNDS`, mensaje sólo código, cause/context ausentes. Guarda runtime:894. |
| FIX1 · control sin centro | ✓ | `apps/server/tests/test_creative_composition.py:1169`; probe propio:4.96/5.04→50+50=100; dos fades/mapas exactos [0,50)/[50,100), envelopes correctos y ningún keep. Repetición/replay byteexactos. |
| FIX1 · preservación/regresión | ✓ | Runtime SHA `f2b5a79f…` intacto; tests SHA `2c5464e9…`, prefijo anterior byteexacto; ejecución propia **274 PASS** =91 focal+183 T02;97 fuentes intactas después. |
| Veredictos B1 restantes | ✓ · conservados | Transferencia completa leída; sólo dos tests añadidos, sin alteración funcional nueva. |
| A01 anterior | corregido funcionalmente; juicio A pendiente | Negativo/control presentes y pasan; causalidad TDD corresponde a A. No existía bug actual de runtime. |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| — | — | Sin defectos nuevos | T-03/FIX1 | — | — |

Lo ejecutado: entorno gestionado ROOT; `uv run --frozen --no-sync --all-packages python -X utf8 -B -` → auditoría213 payloads FIX1/97 fuentes, hashes de ambos diffs y reconstrucción exacta; probes negativo/control; `pytest.main` → **274 passed, exit0**. Dos avisos del arnés: anyio previamente importado y cache_dir desconocido con cacheprovider desactivado. JUnit propio: `.cache/dev-cycle/m2/creative-composition-t03-product-review2-b-evidence-20261011/junit.xml`. Persona backend aplicada; `knowledge-find.py` sin aciertos.

Fuera de mi lente: causalidad TDD para A. C/D oficiales false. Canónicos ausentes; sin modificaciones de fuentes/ledger/Git. Esta revisión no acredita QA independiente, render/audio real ni cierre T03.
