# Revisión de producto 2 — geometría NT readonly FIX1

ROOT 2026-10-11T13:47:04.577957+00:00: lentes frescas A+B, cero Critical/Important/Minor; cuatro Important anteriores corregidos. C/Dauto false según selector real; scope dos archivos sin exclusiones ni avisos. Revisión documental G2 permanece separada. No hay deuda aceptada ni reapertura sin evidencia nueva.

| # | Grado anterior | Gap | Tarea | Veredicto actual | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Clases y longitudes sin RED causal | T05/U2b2 | corregido | A2 valida cuatro RED funcionales 0!=28/4/11/17, reescritura posterior y mismos tests GREEN |
| A02 | Important | DTO frozen sin RED causal | T05/U2b2 | corregido | A2 valida cuatro mutaciones reales sin excepción en RED y rechazo tras reescritura |
| B01 | Important | Parent original perdido antes entrada | T05/U2b2 | corregido | B2 compara parent101→303/ID; FIX1 cero metadata/query, cierre child ordinario único |
| B02 | Important | Buffer metadata incierta perdido | T05/U2b2 | corregido | B2 seis contingencias comparativas: metadata arena y dosbuffers/dosIOSB conservados, poison, closeunknown sin retry |

ROOT comprueba JUnit real A280 y B31+10 (41 únicos), 27sources por auditor y 71recibos de hijos con streams/hashes. ContrapruebasB14 original/FIX1 reproducen rechazo de parentrevocado y retención completa metadata bajo incertidumbre. FIX1 anterior1261/original2374/evidencia causal siguen preservados; canon af192/3de1e82 no cambia. AuditorA indica audit/geometry-junit.xml en su prosa: la ruta efectiva de argv/recibo es geometry-junit.xml en su namespace raíz; se conserva su respuesta original, ROOT usa el archivo efectivo. Esto no altera resultado280 ni veredicto.

QA independiente Windows/Linux/codec/cobertura y adopciónROOT pendientes. Esto no acredita store/writer/ACK/bootstrap/fullchain/ext4/E2E/manuales ni cierra T05/M1. PENDING/errores inciertos son sintéticos en hijos propios, no condiciones nativas peligrosas.

## Lente A — respuesta completa

Lente A · intento PRODUCTO 2 de 3 · diff `a2b5027211353e237b183d2fd54d3c43b02551d5...candidato FIX1` (2 ficheros, 1419 líneas leídas completas por bloques).

**Conforme en el alcance revisado: 0 Critical, 0 Important, 0 Minor. A01 y A02 corregidos.** Se conserva lo aprobado en producto1; diseño G2 y su contador documental permanecen separados.

Referencias: `SW`/`TW` son `scripts/storage_journal_windows.py` y `tests/test_storage_journal_windows.py` del snapshot de review2. `E` es `.cache/dev-cycle/m1/storage-nt-geometry-product-fix1-20261011/evidence/`. Auditoría propia: `.cache/dev-cycle/m1/storage-nt-geometry-product-a2-audit-20261011/`.

| Criterio (T-05/U2b2) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| R01 entrada y ABI | ✓ | SW:1013; TW:516 y :911; rechazos previos sin query ni retención artificial. |
| R02 clases, longitudes y firmas | ✓ | TW:18 y :654. A01: `E/a01-red` contiene lector/bindings/adquisición202 válidos; cuatro fallos `0≠28/4/11/17`. Reescritura posterior y GREEN4/4 con tests SHA idéntico. |
| R03 error NT gobierna | ✓ | SW:1086; TW:365 y :818; error/warning/informational rechazan sin interpretar salida. |
| R04 IOSB exacto | ✓ | SW:1090; TW:401; no0/sentinel rechazados. |
| R05 Information exacto | ✓ | TW:401 y :927; cortos/largos rechazados sin resultado parcial. |
| R06 sentinels y bytes | ✓ | SW:1051; TW:318 y :401; falta de escritura de Status/Information rechazada. |
| R07 PENDING query1 | ✓ | TW:415 y :818; composite retenido, sin query2/postmetadata/close; hijo propio retirado y reapeado. |
| R08 PENDING query2 | ✓ | TW:415; ambos buffers e IOSB permanecen custodiados. |
| R09 incertidumbre posretorno | ✓ | SW:470; TW:111, :479, :854 y :882. B02 conserva además la arena nativa de metadata; `exception` y `FALSE/997` pasan. |
| R10 fallos antes de entrada | ✓ | TW:516 y :798; binding/ABI/allocation fallidos sin queries. |
| R11 adquisición e identidad | ✓ | SW:512 y :1152; TW:79, :570, :594 y :626. B01 fija owner y HANDLE originales en constructor; sustituciones previas rechazan antes de metadata/query. |
| R12 tamaños y relaciones | ✓ | SW:913; TW:208, :218 y :721; unknown/invalid/incoherent bloquean; tamaños físicos distintos admitidos. |
| R13 máscaras cerradas | ✓ | TW:224 y :721; conjunto permitido y controles mask0 incluidos. |
| R14 flags independientes | ✓ | TW:232 y :721; flags3/7/11/15 permitidos; unknown y falta de corroboración bloquean. |
| R15 offsets | ✓ | TW:247; UNKNOWN/nonzero bloquean con causas diferenciadas. |
| R16 combinación | ✓ | TW:343, :570 y :594; sector4096/mask511 coherentes; drift y adquisiciones sustituidas rechazados. |
| R17 DTO/raw/derivación pura | ✓ | SW:868, :885, :896, :907 y :913; TW:49 y :282. A02: cuatro mutaciones reales fallan por ausencia de FrozenInstanceError en RED; mismas pruebas GREEN4/4 tras reconstrucción frozen. |
| R18 close bajo poison | ✓ | TW:111, :415 y :818; close repetido unknown sin syscall; rechazo completo permite cierre ordinario. |
| R19 límites y regresiones | ✓ | TW:761; DTO sin capacidades. U1 y fuentes protegidas exactas; receipt ROOT acredita codec208PASS y 68 nodos anteriores de tests conservados. |
| R20 NT nativo ordinario | ✓ | TW:680 ejecutado en auditoría propia; archivo/directorio propios, ambas queries, status0/info28/4 y parejas de metadata coherentes. |
| R21 portable | ✓ | TW:744; aprobado previamente y sin delta funcional. Receipt ROOT: Linux301PASS/29SKIP; separado de Windows419PASS. |
| §4.1 tipos frozen y API cerrada | ✓ | SW:868–913; TW:49 y :761. A02 corregido causalmente; ninguna capacidad de writer. |
| §4.2 ABI y arenas | ✓ | TW:18, :67 y :654; structs28/4 y firmas exactas. A01 corregido causalmente. |
| §4.3 adquisición original | ✓ | SW:512 y :1152; TW:79. Tres sustituciones previas rechazadas sin syscall. |
| §4.4 custodia completa | ✓ | SW:470; TW:111. Buffer de metadata y composite sobreviven a GC; poison y retirada por padre comprobados. |
| §4.5 política B | ✓ | SW:913; TW:208–282 y :721; conserva conformidad aprobada, sin nueva flexibilización. |
| §4.6 separación del writer | ✓ | TW:761; sin writer/admission/ACK/fallback ni modificación del wire U1. |
| Alcance y plan | ✓ | Snapshot Git: sólo SW/TW modificados; declarados en `tasks.md:208`. Scope ROOT2/0fuera/0avisos/0exclusiones. |
| Constitución y ADR0078 | ✓ | `docs/CONSTITUTION.md:18`, :25, :32, :33 y :37; readonly, identificadores ingleses, evidencias dentro del proyecto y T05 abierto. Contrato NT/G2 conservado. |
| TDD FIX1 | ✓ | Fuentes, streams, JUnit, tests SHA y tiempos de los cuatro pares primarios comprobados. Diagnósticos inválidos excluidos; replays suplementarios tratados separadamente. |
| Cobertura | ✓ | Receipt ROOT y reporte final: módulo completo90,0608519%, líneas90,4109589%, ramas89,0625%, excluidas0. Apoyo, sin sustituir lectura de tests. |
| Generados/documentación | ✓ / n/a | No cambia commands/agents/hooks: interop no aplica. Diseño y ADR adoptados previamente; no se reabre su revisión documental. |
| Verificación integral/cierre T05 | no verificable, pendiente | `tasks.md:202` conserva `en-progreso`; CA y verificación integral: :210. Este candidato no declara completado T05/M1. |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| — | — | Sin defectos de Lente A pendientes | T-05/U2b2 | — | A01 y A02 corregidos; sin reapertura de criterios aprobados. |

Lo ejecutado:

- Entorno gestionado con `scripts/env.ps1`; snapshot propio: `pytest tests/test_storage_journal_windows.py -k geometry -q` → **280PASS,139deselected,56,84s**. JUnit en `audit/geometry-junit.xml`.
- **27 pins del snapshot exactos** y hashes de ambos diffs comprobados. Canon runtime/tests y candidato permanecen exactos.
- **28 hijos propios**: ready, terminados por su padre, reapeados y con SHA final exacto.
- Verificación de fuentes/streams/JUnit y orden `RED terminado < reescritura < GREEN`. Intercalaciones B01/B02 trazadas mediante los deltas independientes A02 y B01; no invalidan los pares primarios.
- Consulta `knowledge-find.py` de ADR: sin aciertos; ADR0078 comprobada directamente.
- Warning propio por `cache_dir` al desactivar cacheprovider; sin fallo de producto.

Fuera de mi lente (no reportado): B arbitra sus defectos de corrección. PENDING sigue siendo sintético; esta revisión no acredita S1, bootstrap, writer, ACK, ext4, QA integral ni cierre M1. Ledger y fuentes canónicas no modificados por esta lente.


## Lente B — respuesta completa

Lente B · intento 2 de 3 · diff `a2b5027211353e237b183d2fd54d3c43b02551d5...candidato FIX1` (2 ficheros).

**Sin defectos nuevos: 0 Critical / 0 Important / 0 Minor. B01 y B02 corregidos.**

Diff completo leído por bloques: 1419 líneas; `fix-only.diff` leído íntegro. Sólo se reevalúa FIX1; los criterios aprobados anteriormente se conservan sin reabrirlos.

`SW/TW`: runtime/tests del snapshot congelado de `storage-nt-geometry-product-review2-20261011`. `E`: `.cache/dev-cycle/m1/storage-nt-geometry-product-b2-audit-20261011/`.

| Criterio T-05/U2b2 | ✓/✗/no verificable | Evidencia |
|---|---|---|
| R01 entrada/ABI | ✓ conservado | Veredicto B1 leído; FIX1 rechaza parent revocado antes de metadata/query. |
| R02 firmas/clases/longitudes | ✓ | TW:16; cuatro casos funcionales pasan, queries exactas `202/28/11` y `202/4/17`. |
| R03 error NT prevalece | ✓ conservado | Código y veredicto B1 leídos; tratamiento del retorno intacto en FIX1. |
| R04 IOSB exacto | ✓ conservado | Validación intacta; testigo propio exige ambos status0. |
| R05 longitudes exactas | ✓ conservado | Validación intacta; testigo propio Information28/4. |
| R06 sentinels | ✓ conservado | Inicialización y comprobación intactas. |
| R07 PENDING query1 | ✓ | Prueba focal en hijo pasa; composite retenido, sin query2/cierre. |
| R08 PENDING query2 | ✓ | Prueba focal en hijo pasa; dos buffers y dos IOSB retenidos. |
| R09 incertidumbre/transferencia | ✓ corregido B02 | SW:470; seis comparativas de postmetadata incierta conservan ahora su buffer y el composite. |
| R10 fallo antes de query | ✓ conservado | Validaciones intactas; sustitución del parent produce cero llamadas. |
| R11 adquisición/identidad | ✓ corregido B01 | SW:512/1034/1152; owner/HANDLE originales fijados al adquirir child; tres variantes nuevas y revocaciones pasan. |
| R12 tamaños/relaciones | ✓ conservado | Derivador sin cambios; veredicto B1 leído. |
| R13 máscaras | ✓ conservado | Derivador sin cambios. |
| R14 flags | ✓ conservado | Derivador sin cambios. |
| R15 offsets | ✓ conservado | Derivador sin cambios. |
| R16 combinación | ✓ conservado | Comparaciones intactas; testigo nativo propio mantiene ambas parejas iguales. |
| R17 DTO/raw/derivación | ✓ | TW:45; cuatro mutaciones frozen rechazadas; candidato lógico4096 conservado. Causalidad TDD corresponde a A. |
| R18 close bajo poison | ✓ | Contingencias focales/comparativas: close repetido unknown, cero CloseHandle y nuevas operaciones bloqueadas. |
| R19 regresiones U2b1 | ✓ corregido B02 | Control directo conserva metadata; ocho casos previos de adquisición/retención/cierre pasan. Consumidores de `_RETAINED` revisados, sin desempaquetado incompatible. |
| R20 NT ordinario | ✓ | Archivo/directorio propios: retorno0/IOSB0, Information28/4, parejas de metadata iguales, candidato lógico65536. |
| R21 portable | ✓ conservado, alcance limitado | Import/derivador no modificados; veredicto B1 conservado. Linux real no ejecutado por esta lente. |

Gaps:

| # | Grado anterior | Gap | Tarea | fichero:línea | Veredicto y escenario comprobado |
|---|---|---|---|---|---|
| B01 | Important | Parent original no fijado al adquirir child | T-05/U2b2 R11 | SW:512/1034 | **Corregido.** Original: parent101→303, ID `50…50`, dos queries y candidato4096. FIX1: rechazo, cero metadata y cero queries; cierre ordinario child202 una vez. |
| B02 | Important | Arena de metadata incierta perdida | T-05/U2b2 R09/R19 | SW:473/478 | **Corregido.** Original libera buffer tras GC; FIX1 lo conserva junto a dos buffers/dos IOSB. Probados identidad del objeto, standard del parent y path del objeto, cada uno con KeyboardInterrupt y FALSE997. Poison y closeunknown permanecen sin repetir I/O. |

Lo ejecutado:

- Entorno gestionado mediante `scripts/env.ps1`; copia privada byteidéntica de los 27 artefactos.
- Selección focal → **31 passed / 388 deselected**, exit0; `E/focal.receipt.json`, streams y JUnit.
- Regresiones focales y testigos ordinarios → **10 passed / 409 deselected**, exit0; `E/regression.receipt.json`. **41 nodos distintos**, sin fallos ni skips.
- **14 contrapruebas comparativas** original/FIX1 → resultados esperados; `E/comparative-results.json` y scripts/streams/recibos individuales en `E/comparative/`.
- **43 recibos de hijos comprobados**, reaped y streams preservados; `E/verification.json`.
- Snapshot27, copia27 y dos fuentes canónicas conservan sus SHA256. Git privado muestra exclusivamente los dos ficheros previstos modificados.
- Persona backend aplicada; consulta ADR mediante `knowledge-find.py` sin aciertos. ADR-0078 y contrato §4.1–4.6 leídos directamente.

Fuera de mi lente: A01/A02 y causalidad TDD corresponden a A. No modifiqué producto, snapshot congelado ni ledger. Las contingencias son sintéticas en hijos propios; esta revisión no acredita PENDING nativo, QA completa, writer, S1, durabilidad ni aceptación T-05/M1.
