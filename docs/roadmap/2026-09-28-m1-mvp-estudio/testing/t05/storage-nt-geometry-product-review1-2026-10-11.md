# Revisión de producto T-05/U2b2 — intento 1 de 3 — 2026-10-11T13:12:38.084904+00:00

ROOT fusiona A+B frescas: **0 Critical / 4 Important / 0 Minor**. C/D auto false sobre diff completo. Contrato documental G2 ya adoptado: su contador es distinto. T-05 sigue en-progreso; candidato privado, sin CAS ni aceptación M1.

| # | Grado | Gap | Tarea | Veredicto | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Clases y longitudes exactas sin RED causal | T-05/U2b2 R02 | pendiente FIX1 | A: bootstrap ausente no prueba clases11/17 y longitudes28/4; preimágenes y UTC |
| A02 | Important | Cuatro DTO frozen escritos antes del test | T-05/U2b2 R17 | pendiente FIX1 | A: green-abi12:21:35 frente characterization12:29:17 |
| B01 | Important | Parent original no fijado al adquirir child | T-05/U2b2 R11 | pendiente FIX1 | B: parent101→303 e ID distinto antes de entrar; devuelve4096 |
| B02 | Important | Retención descarta arena metadata incierta | T-05/U2b2 R09/R19 | pendiente FIX1 | B: FALSE997/interrupt+GC pierde buffer; control U2b1 lo conserva |


La lente A no eleva un intercambio de owner con el mismo scalar bajo la precondición cooperativa. B01 reproduce otro HANDLE101→303 e identidad distinta antes de iniciar la lectura: la procedencia original se pierde. ROOT conserva este defecto de corrección como Important; no afirma una garantía contra adversario arbitrario dentro del proceso. B02 reproduce incertidumbre dentro de GetFileInformationByHandleEx con buffer de salida, distinta del test previo en GetFileType sin buffer. El control U2b1 conserva esa arena; es una regresión introducida.

ROOT verifica nuevamente2369archivos+5reparse stat-only/27fuentes congeladas y cuatro recibos/streams propios de B. Los hijos sintéticos se terminan y reapean por su padre; no se afirma PENDING nativo. Los resultados Windows405/Linux297+29SKIP/codec208 del implementer permanecen evidencia de implementación, no QA independiente. A ejecuta266casos y B373nodos distintos con alcances declarados. Sin GPU, administración, bootstrap, store, writer, ACK, ext4, datos o BD.

## Lente A — respuesta completa

Lente A · intento 1 · diff `18631c786d3e32f70d8abe40dae423306f0f0f71...HEAD` · 2 ficheros, leído completo por bloques.

**Conformidad funcional: 21/21 criterios comprobados. TDD: 2 gaps Important; 0 Critical y 0 Minor. No conforme para adopción todavía.**

Las referencias de runtime/tests corresponden al snapshot congelado de `.cache/dev-cycle/m1/storage-nt-geometry-product-review1-20261011/`. `E/` significa `.cache/dev-cycle/m1/storage-nt-geometry-implementation-20261011/evidence/`.

| Criterio T05/U2b2 | ✓/✗ | Evidencia |
|---|---|---|
| R01 entrada/ABI | ✓ | `scripts/storage_journal_windows.py:1006`, `:1145`, `:1163`; tests preentry/original-acquisition/signed-ABI pasan. RED conductuales específicos separados del bootstrap. |
| R02 firmas, clases y longitudes | ✓ funcional | Runtime `:1060`, `:1264`, `:1276`; double comprueba HANDLE202, clases11/17 y longitudes28/4; firmas verificadas y consultas nativas propias pasan. **Causalidad TDD pendiente, A01.** |
| R03 retorno NT gobierna | ✓ | Runtime `:1072`; error/warning/informational rechazan antes de interpretar salida. Tests de error y acceso prohibido pasan. |
| R04 IOSB restrictivo | ✓ | Runtime `:1080`; ambos status0 exigidos, sentinel/PENDING/error de IOSB rechazados. `E/red-nt-completion` acredita RED conductual. |
| R05 Information exacto | ✓ | Runtime `:1080`; rechazo sin clamp/reissue/partial-success. Casos 0/27/29/max y alignment3/5 pasan. |
| R06 buffers y sentinels | ✓ | Runtime `:1051`; patrónA5 y sentinels noSUCCESS/info noexacta. Ausencia de escritura IOSB rechazada; payload plausible no sustituye completion. |
| R07 PENDING query1 | ✓ | Runtime `:1072`, `:1135`; composite retenido, cero salida/postmetadata/query2/close; poison global. RED pending1 y prueba propia pasan. |
| R08 PENDING query2 | ✓ | Runtime `:1048`, `:1066`; buffers e IOSB independientes conservados, sin resultado parcial. RED pending2 y prueba propia pasan. |
| R09 transferencia/posretorno | ✓ | Runtime `:470`, `:1123`, `:1135`; RED copy/freeze/postreturn/postmetadata/custody-clear leídos. Pruebas propias en hijos terminados y reapeados pasan. |
| R10 before-entry | ✓ | Runtime `:1028`, `:1048`; binding/ABI/argumentos antes de query; allocation falla sin calls ni retención artificial. Allocation correctamente caracterizada como comportamiento conservado. |
| R11 identidad/adquisición | ✓ | Runtime `:511`, `:1145`, `:1113`; parejas metadata completas, original scalar/parent/context y revocaciones entre fronteras. Tests de diez campos por parent/object pasan. |
| R12 tamaños | ✓ | Runtime `:922`; cuatro tamaños, límites/potencia2 y relaciones con logical. `E/red-sizes`:18 fallos conductuales; controles posteriores pasan. |
| R13 máscaras cerradas | ✓ | Runtime `:932`; conjunto cerrado, mask0 válido, bool rechazado antes de aritmética. Tests cerrados y controles pasan. |
| R14 flags | ✓ | Runtime `:935`, `:945`; máscara0xF y bits1/2 necesarios; no-seek/TRIM independientes. RED y controles3/7/11/15 pasan. |
| R15 offsets | ✓ | Runtime `:937`; UNKNOWN/nozero bloqueantes, contradicciónsector separada de partition. RED aislados y combinaciones pasan. |
| R16 combinación/procedencia | ✓ | Runtime `:1060`, `:969`; dos clases sobre la misma adquisición, fuente cerrada y raw independientes. No se exige igualdad numérica sector/mask. |
| R17 salida pura | ✓ funcional | Runtime `:906`, `:969`; DTO/tipos/source/raw exactos, correspondencia LE y causas seguras acumuladas. Tests raw/pure-metadata/all-causes pasan. **Inmutabilidad nueva sin TDD previo, A02.** |
| R18 close/custodia | ✓ | Runtime `:470`, `:1135`; poison conserva cierre unknown repetible sin syscall; rechazos completos permiten un cierre ordinario. Pruebas propias pasan. |
| R19 sin ampliación | ✓ | Diff sólo runtime/tests autorizados; sin writer/store/admission/ACK/fallback. U1 exacto; AST de tests anteriores conservado y regresión codec208 acreditada con parser real. |
| R20 NT nativo | ✓ | Test `tests/test_storage_journal_windows.py:547`; archivo/directorio propios consultados con ambas funciones. Witness propios status0/info28/4/raw y metadata coherentes; candidato65536 sólo numérico. |
| R21 portable | ✓ | Runtime `:1008`, test `:611`; Linux real del actor297PASS/29SKIP/79deselected, import/derivador puro/lector portable separados. No atribuyo los405 casos Windows a Linux. |
| Alcance | ✓ | Scope oficial2/0fuera/0avisos/0exclusionesusuario. Verificación propia27pins exactos; sólo tres métodos anteriores modificados: retain, registro de adquisición y firmas. |
| Constitución | ✓ | `docs/CONSTITUTION.md:24`, `:25`, `:32`, `:33`: sin pesos/servicios/dependencias nuevas, datos externos ni escritura del ledger. Identificadores ingleses; T05/M1 abiertos. |
| Verificación/cobertura | ✓ en alcance | ROOT receipt/JUnit405Win/208codec/297Linux leídos; whole módulo90,0608519%,0exclusiones. Ejecución propia266 geometryPASS. No sustituye QA independiente ni Verificación integral de T05. |
| TDD por criterio | ✗ | A01/R02 y A02/R17. Los RED causales restantes se distinguen de caracterizaciones y diagnósticos de arnés. |
| Generados/documentación | ✓ / n/a | No cambia commands/agents/hooks: interop n/a. ContratoG2/ADR0078 previamente adoptados; esta revisión corresponde al producto y conserva su contador propio. |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| A01 | Important | R02 carece de RED causal que acredite clases/longitudes exactas; el bootstrap no cubre esa exigencia | T05/U2b2 · R02/TDD | `storage-nt-geometry-design.md:295`; `E/red-nt-completion/storage_journal_windows.py:970`; `tests/test_storage_journal_windows.py:210` | `red-reader-control` falla porque el lector está ausente. `green-reader-control` ya introduce clases11/17 y Length28/4 correctos; las preimágenes posteriores los conservan. `red-signatures` falla en `hasattr` por binding ausente. No consta RED con control adquirido y clase/longitud incorrecta ni retirada/reescritura posterior de ese comportamiento. RED signed-ABI/preentry-ABI prueban rechazo de structs incorrectos, no esta frontera. |
| A02 | Important | Cuatro DTO frozen escritos antes de su test de inmutabilidad | T05/U2b2 · §4.1/R17/TDD | `E/green-abi/storage_journal_windows.py:856`, `:873`, `:884`, `:895`; `E/characterization-controls/test_storage_journal_windows.py:455` | A las12:21:35 `green-abi` contiene los cuatro `dataclass(frozen=True)` y sólo el test geométrico de structs. El test de resultados frozen aparece a las12:29:17 y pasa a la primera. No existe RED ni retirada/reescritura de esos DTO después del test. Es comportamiento nuevo, no caracterización de U2a/U2b1; incumple la ley dura de TDD. |

Lo ejecutado:

- Python gestionado mediante `scripts/env.ps1`, snapshot propio de auditoría; `pytest … -k geometry -q` → **266PASS,139deselected,44,69s**. JUnit: `.cache/dev-cycle/m1/storage-nt-geometry-product-a1-audit-20261011/geometry-junit.xml`.
- **27pins sin diferencias**, tres modificaciones AST anteriores autorizadas, **68 nodos anteriores de tests no geométricos sin cambios**.
- **22 recibos propios de hijos geométricos**: todos ready, terminados por su padre y reapeados, SHA final exacto. Dos witness NT propios, archivo/directorio.
- Lectura ejecutada de todos los RED/JUnit/preimágenes y matriz de caracterizaciones. Consulta `knowledge-find.py` de ADR: sin aciertos.
- Un warning propio `cache_dir` procede de deshabilitar cacheprovider; no es fallo de producto.

Límites/preocupaciones: PENDING sólo sintético; ningún resultado acredita S1, writer, atomicidad, ACK, bootstrap, ext4 o cierreM1. El owner original cooperativo sigue siendo precondición: sustituir `parent.owner` antes de entrar puede aceptar un wrapper con el mismo scalar; no lo elevo a gap porque el contrato conserva explícitamente ese supuesto y no promete defensa contra manipulación hostil dentro del proceso.

Fuera de mi lente: ninguna incidencia adicional reportada como B/C/D.


## Lente B — respuesta completa

Lente B · intento 1 · diff `18631c786d3e32f70d8abe40dae423306f0f0f71...candidato privado` (2 ficheros, 1279 líneas leídas completas).

**Resultado: 0 Critical, 2 Important, 0 Minor.**

Referencias: `SW` = snapshot de revisión, `scripts/storage_journal_windows.py`; `TW` = mismo snapshot, `tests/test_storage_journal_windows.py`. Evidencias propias bajo `.cache/dev-cycle/m1/storage-nt-geometry-product-b1-audit-20261011/`.

| Criterio / objetivo T-05/U2b2 | ✓/✗/no verificable | Evidencia |
|---|---|---|
| R01 entrada/ABI | ✓ | SW:1006/1163; prechecks y ABI ejecutados, cero queries en rechazos |
| R02 firmas/clases/longitudes | ✓ | TW:521/547; firmas verificadas y consultas nativas 11/17 sobre archivo/directorio propios |
| R03 error NT prevalece | ✓ | SW:1078; TW:232, negativos ejecutados sin copia del payload |
| R04 IOSB exacto | ✓ | SW:1082; TW:268, completion no0/sentinel rechazada |
| R05 longitudes exactas | ✓ | TW:268/794; respuestas cortas/largas rechazadas |
| R06 sentinels | ✓ | SW:1050; TW:268, ausencia de escritura de Status/Information rechazada |
| R07 PENDING query1 | ✓ | TW:282; hijo ejecutado, composite retenido, sin query2 ni close |
| R08 PENDING query2 | ✓ | TW:282; hijo ejecutado, ambos buffers/IOSB retenidos |
| R09 incertidumbre y transferencia | ✗ | Copia/freeze/posretorno conservan composite; **B02 pierde el buffer de postmetadata incierta** |
| R10 fallo antes de query | ✓ | TW:383/665; ABI/binding/allocation fallidos sin queries |
| R11 misma adquisición e identidad | ✗ | Parejas before/after y revocaciones durante queries comprobadas; **B01 acepta parent sustituido antes de entrar** |
| R12 tamaños/relaciones | ✓ | SW:925; negativos y controles 512/4096/65536 ejecutados |
| R13 máscaras cerradas | ✓ | SW:933; TW:91/588, controles y rechazos ejecutados |
| R14 flags | ✓ | SW:936/946; bits conocidos e independientes comprobados |
| R15 offsets | ✓ | SW:938; UNKNOWN/nonzero y causas específicas comprobados |
| R16 combinación | ✓ | SW:1042/1113; combinación sector4096/mask511 admitida, drift rechazado |
| R17 DTO/raw/derivación pura | ✓ | SW:959; tipos exactos, bytes LE, longitudes/status/source y congelación ejecutados |
| R18 close bajo poison | ✓ | TW:282; close repetido unknown sin syscall, rechazo completo permite cierre ordinario |
| R19 ausencia de ampliación/regresiones | ✗ | DTO sin capacidades y 113 regresiones seleccionadas pasan; **B02 reabre custodia U2b1 al anidar metadata** |
| R20 testigos NT ordinarios | ✓ | TW:547; archivo/directorio propios, status0/info28/4, raw y parejas de metadata; candidato lógico65536 |
| R21 portable | ✓, alcance limitado | TW:611 y SW:906/1006; rechazo posix sin DLL y derivación pura ejecutados en Windows. Linux real no ejecutado por esta lente |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| B01 | Important | Owner/handle originales del parent no quedan fijados al adquirir el objeto | T-05/U2b2, R11 | SW:512 y SW:1027 | `_acquisition` guarda únicamente child handle, wrapper parent y contexto. El owner/handle del parent se añaden al empezar geometría. Sustituir `parent.owner` antes de entrar, pasando de parent101 a otro directorio303 del mismo volumen, supera los checks: ambas queries sobre child202 se ejecutan y devuelve candidato4096 con metadata del parent nuevo. Se mezcla la adquisición original con otro parent. |
| B02 | Important | La retención geométrica descarta la arena nativa de postmetadata incierta | T-05/U2b2, R09/R19 | SW:475; llamada anidada SW:1103 | Tras ambas queries, `read_handle_metadata` crea su propia arena y entrega su buffer a `GetFileInformationByHandleEx`. Si esa llamada retorna FALSE/error997 o lanza `KeyboardInterrupt`, `retain(arena_metadata)` conserva exclusivamente `_geometry_custody`. Tras unwind+GC, el buffer de metadata desaparece aunque la completion esté sin acreditar y el proceso propietario siga vivo. El composite geométrico permanece, pero no protege ese buffer. |

Evidencia de reproducción:

| Caso | Artefacto propio | Salida real |
|---|---|---|
| B01 | `geometry-child-ed5f158a69ef4cf4b8d4bbf76f49c92e/stdout.txt` | `original_parent_handle:101`, `current_parent_handle:303`, queries `[[0,202,28,11],[1,202,4,17]]`, parent ID distinto, `candidate_b:4096` |
| B02, excepción durante metadata | `geometry-child-29fb152b430844a39613bfa1ef128cfe/stdout.txt` | `retained_composite:true`, `metadata_buffer_alive:false`, `close:"unknown"` |
| B02, FALSE/error997 | `geometry-child-9dea123dfc2648e8abcb0f7045a87244/stdout.txt` | `metadata_false_error997:true`, `retained_composite:true`, `metadata_buffer_alive:false` |
| Control directo U2b1 | `geometry-child-54c994bbeb25441f9a91c398507ac427/stdout.txt` | Misma contingencia: `metadata_buffer_alive:true`, `retained_has_identity:true` |

Cada reproducción y control anteriores tiene `receipt.json`: padre propio termina y reapea al hijo, `ready_before_retirement:true`, `reaped:true`, stderr vacío. Son dobles sintéticos; no se afirma PENDING nativo ni se provoca escritura sobre memoria liberada.

Lo ejecutado:

- Entorno gestionado mediante `scripts/env.ps1`; pytest con temporales/cachés propios y bytecode desactivado.
- `-k 'geometry and not child and not native'` → **243 passed, 162 deselected**, exit0.
- Selección contingencia/composite/postmetadata/testigo NT → **8 passed, 397 deselected**, exit0.
- Selección revocación durante queries/adquisición original → **9 passed, 396 deselected**, exit0.
- `-k 'not geometry and not child and not native'` → **113 passed, 292 deselected**, exit0.
- Total verificable de esas selecciones: **373 nodos distintos**. Una invocación inicial completa perdió la captura de su resultado final; no se utiliza para acreditar405PASS.
- Diff/status privados: exactamente los dos ficheros previstos. Runtime propio y snapshot ROOT conservan SHA256 `4f543c4ffc1c825ba87e953aa9e54ee88921c4e62a64299cb164eb8ef2f1de44`.
- Diagnóstico inicial de sustitución con warning de escape conservado; sustituido como evidencia por la reproducción limpia B01.

Fuera de mi lente: sin hallazgos adicionales reportados. Memoria ADR consultada sin aciertos; aplicada persona backend. No se modificó canon, ledger ni snapshot congelado. **T-05/M1 siguen abiertos; esta revisión no acredita QA, S1, writer ni durabilidad.**
