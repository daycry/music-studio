# Revisión U2a — intento 1

**0 Critical / 1 Important / 0 Minor. A01 pendiente de corrección; candidato no incorporado.** T-05 y M1 siguen abiertos. Base privada `55d28e53a4c4d1542d8750e6b01af090f913e4e1`, dos nuevos archivos (406/711 líneas). Scope2 dentro/0 fuera/0avisos. Revisión fresca A/B/C; QA independiente posterior todavía pendiente.

Referencias `W` y `T`: `scripts/storage_journal_windows.py` y `tests/test_storage_journal_windows.py` del snapshot congelado `storage-nt-security-u2a-review1-20261011`. Los números de línea corresponden a ese candidato, no a una fuente canónica aceptada. Los SHA son runtime805b4abfee03d20da2afa8422f4c425f542998f356eb9894fd49c1355fb6f8dd y tests6671dbfccab19f2b9c8f7295b83513ebd21413d12759c0774de54d28f2bc5ad5.

## Lente A: conformidad

| Criterio T-05/U2a | Veredicto | Evidencia |
|---|---|---|
| Alcance: sólo lector/política local y tests | ✓ | Diff2ficheros; tasks:208,4724; scope2/0/0 |
| CA1 SID/SD/offsets/longitudes/solapes/ACL NULL/ausente/vacía | ✓ | W:65–140; T:71–120 |
| CA1 ACE desconocida/object/callback, flags/máscaras | ✓ | W:171–183,202–210; T:123–163; controles positivos |
| CA1 orden, IO/herencia/generic rights | ✓ | W:204–223; T:184–214; política conservadora local |
| CA2 tres roles y owner independiente | ✓ | W:186–200; T:166–177,199–214 |
| CA2 outsiders/grupos/SID sin resolver; DENY no compensa ALLOW | ✓ | W:216–223; T:184–196 |
| CA2 nuevos objetos protegidos y cerrados | ✓ | W:193,217–218; T:199–207,319–339 |
| CA2 TrustedInstaller permanece rechazado | ✓ | W:189–192; T:169–172; release:15 |
| CA2 diagnóstico frozen, sin capacidad ni acreditación sintética nativa | ✓ | W:42–62,143–168,251–254; T:61–68,378–384,628–633 |
| CA3 TokenUser y rechazo impersonación | ✓ | W:257–294; T:265–292,506–613; principal nativo y wellknown |
| CA3 GetSecurityInfo por handle prestado, ABI explícita | ✓ | W:226–254,347–406; T:369–385,473–487 |
| CA3 positivo S2 y dos negativos nativos efectivos | ✓ | T:295–396; 09green1PASS/10green2PASS; rawSD3positivos6negativos |
| CA3 LocalFree/cierre propio una vez, invalidación previa/causas/BaseException | ✓ | W:305–335; T:473–503,598–625,664–677; comportamiento verde |
| CA3 TDD previo en fronteras errores/cleanup | **✗ A01** | Ramas ya existentes08/09green; tests posteriores12-existing-behavior;25PASS contra09 |
| CA4 padre existente readonly rechazado, raw privado, sin remediación | ✓ | T:399–429; 11green1PASS; native=true/mutation=false |
| CA5 Linux real portable, ninguna DLL | ✓ | linux-portable.json:UID/GID10001,2PLATFORM_UNSUPPORTED,dll_calls[]; manual declarado |
| CA5 whole≥80%,sin exclusiones | ✓ |97,0027%;247/253statements,109/114branches,excluded0; apoyo a lectura |
| CA5 tests/inventarios/calidad | ✓ | ActorJUnit66/0fail/error/skip;368hashes,48registros etapas;Ruff/format0 |
| Constitución explícita | ✓ | Constitución:18,25,33,37,42; sin cambios BD/estado ni decisión contradictoria |
| Verificación de tareas completadas | n/a | M1 ninguna completada;T05en-progreso,tasks:202 |
| T05 audio-post/publicación atómica | n/a | tasks:215;fueraU2a,abierto |
| T05 ready/song.json/análisis dependiente | n/a | tasks:216;fueraU2a,abierto |
| T05 cleanup intento/publicación fallida | n/a | tasks:217;fueraU2a,abierto |
| Generados interop/E2–E3 | n/a | Diff no toca commands/agents/hooks ni contrato público generado |

## Lente B: corrección

| Objetivo | Veredicto | Evidencia |
|---|---|---|
| SID/SD/ACL/ACE/máscaras/orden/IO | ✓ | W:65; pruebas sintéticas/doubles |
| S1local/owner/outsiders/generic/TI | ✓ | W:186; positivos/negativos |
| TokenUser/buffers/cleanup propio | ✓ | W:226; principal independiente y fallos causales |
| GetSecurityInfo nativo readonly | ✓ | leafnative/localtrue;outsiders0x2/0x40000localfalse;padrefalse |
| Portable/origen sintético | ✓ | Focal portable; rawLinux2errores/0DLL leído |
| Integridad candidato | ✓ | SHAfinales exactos, sin modificación |

Sin defectos funcionales confirmados,0Critical/Important/Minor. B leyó ambos archivos y ejecutó62PASS/4deselected, evitando crear fixtures en el freeze. Consultas readonly adicionales conservaron handles prestados y cerraron propios; contraste IsValidAcl no confirmó defecto.

## Lente C: seguridad

| Objetivo | Veredicto | Evidencia |
|---|---|---|
| Parser cerrado SID/SD/ACL/ACE | ✓ | W:65; negativos ejecutados |
| Allowlist/owner/DENY/ALLOW/herencia/TI | ✓ | W:186; outsiders/grupos/TI rechazan |
| TokenUser independiente/impersonación/bounds | ✓ | W:257; nativo y doubles |
| GetSecurityInfo/recursos propios | ✓ | W:226; borrowed conservado/cleanup causal |
| Diagnóstico sin capacidad/sintético sin native | ✓ | W:152; pruebas ejecutadas |

Sin hallazgos explotables,0Critical/Important/Minor. C ejecutó61PASS/5deselected y cinco controles nativos readonly: principal independiente, leaf cerrado, WRITE_DATA/WRITE_DAC outsiders y padre. Verificó368artefactos y dos targets pre/post, sin escrituras. Selector auto sobre diff Cfalse/Dfalse; release exige C. Overlay sólo de revisión fuerza C, config canónica intacta. La primera selección suplementaria con paths absolutos activó D por `.cache` del contenedor de evidencia; se conserva el raw y se corrigió a los dos paths relativos reales, copiando las fuentes exactas al overlay: Ctrue/Dfalse/0warnings. No se confunde el directorio de evidencia con una ruta de rendimiento del producto.

## Gap y decisión de ROOT

| ID | Grado | Ubicación | Escenario | Veredicto |
|---|---|---|---|---|
| A01 | Important | W:305;T:473,598,616 |09green07:48:37 ya contiene errores TokenUser/SD,cleanup/invalidación/BaseException. Tests entran12-existing-behavior07:50:00 y25casos pasan contra la fuente anterior. | **Confirmado, pendiente FIX1** |

Incumple release:22,26 y la ley dura `tdd/SKILL.md:21`: «El código escrito antes de su test se borra y se reescribe tras el rojo». Reconocer cobertura posterior es honesto pero no cumple TDD. ROOT libera un implementer fresco en `storage-nt-security-u2a-fix1-20261011`: borrar sólo el segmento afectado de una copia privada, dejar stubs importables, tests/RED causales individuales y reescritura posterior mínima. Original/freeze/gap intactos. Luego revisión2/3 y QA fresca; no adopción adelantada.

A ejecutó61PASS/5deselected, principal/wellknown, verificación368hashes/48registros y replay rawSD; además25tests etapa12 contra preimagen09 en memoria:25PASS. Estos conjuntos se solapan; no se suman como una suite nueva. Evidencia de revisores en llamadas de herramientas y reportes finales, lectura sólo; ROOT no inventa archivos de stdout escritos por agentes ni un nuevo JUnit para esos replays.

No se atribuye conformidad TDD al código aún no corregido. El ledger tiene codificación mixta preexistente, fuera del diff; ninguna tarea se cierra. G1/G2 completos, store/writer/lifecycle/ext4/E2E/M1 permanecen fuera de esta aceptación de componente.
