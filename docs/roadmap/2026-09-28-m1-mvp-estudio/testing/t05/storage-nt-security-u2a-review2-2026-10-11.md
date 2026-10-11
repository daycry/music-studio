# Revisión U2a — intento 2 de 3

**A01 corregido; A/B/C sin gaps nuevos:0Critical/0Important/0Minor. QA independiente pendiente; T-05 y M1 abiertos.**

Base privada c2871f295d7abf390f17feceb401f78020052a74, dos archivos nuevos. W=scripts/storage_journal_windows.py; T=tests/test_storage_journal_windows.py, líneas del snapshot review2. Runtime91e279775c20561b14679845066f334f3af6d30fdc0a41a92ce5d0ee24af4b70, tests6671dbfccab19f2b9c8f7295b83513ebd21413d12759c0774de54d28f2bc5ad5. No archivos canónicos adoptados.

## Lente A

| Criterio T-05/U2a | Veredicto | Evidencia |
|---|---|---|
| Alcance lector/política y tests | ✓ | W:1,144;ledger208,4724;scope2/0/0 |
| CA1 SID/SD/offsets/longitudes/solapes/ACL NULL/ausente/vacía | ✓ | W:65,84;T:71;prefix/tests exactos |
| CA1 ACE desconocida/object/callback flags/máscaras | ✓ | W:171,204;T:123,156;positivos/negativos |
| CA1 orden IO/herencia/generic | ✓ | W:204;T:184,199;conservador |
| CA2 roles/owner independiente | ✓ | W:186;T:167,199 |
| CA2 outsiders/grupos/SID sin resolver/DENY no compensa ALLOW | ✓ | W:216;T:184 |
| CA2 nuevos protegidos/cerrados | ✓ | W:193,217;T:199,319;rawSD |
| CA2 TrustedInstaller rechazado | ✓ | W:189;T:167;release limitada |
| CA2 frozen/sin capacidad/sintético sin nativo | ✓ | W:42,144,252;T:61,628 |
| CA3 TokenUser/impersonación | ✓ | W:259;T:286,598;16 variantes y nativo |
| CA3 GetSecurityInfo prestado/ABI | ✓ | W:226,366;T:369,473 |
| CA3 S2positivo/two native outsiders | ✓ | T:369,389;actorJUnit;rawSD4positivos8negativos |
| CA3 LocalFree/closeonce/invalida/causas/BaseException | ✓ | W:311,319,332;T:473,490,598,616,664,691 |
| CA3 TDD errores/cleanup A01 | ✓ corregido | Deletion/stubs42RED→reescritura→42GREEN;84JUnit |
| CA4 padre readonly/raw/sin remediación | ✓ | T:400;raw/witness mutation=false |
| CA5 portable sinDLL | ✓ | W:357;T:217 actual |
| CA5 Linux real SHA nuevo | Pendiente QA | No hereda Linux histórico; no green adelantado |
| CA5 whole>=80/sin exclusiones | ✓ | Actor97,127937%;259/265lines+113/118branches,excluded0 |
| CA5 tests/inventarios/calidad | ✓ | Actor66PASS;1419FIX+368original;Ruff/format0 |
| Constitución explícita | ✓ | 18,33,42,52,81,89;sin BD/capacidad/contrato cambiado |
| Verificación tareas completadas | n/a | Ninguna M1completada;T05en-progreso |
| T05 audio-post/publicación atómica | n/a | ledger215;fueraU2a,abierto |
| T05 ready/song.json/análisis | n/a | ledger216;fueraU2a,abierto |
| T05 cleanup intento/publicación | n/a | ledger217;fueraU2a,abierto |
| Generados interop/E2-E3 | n/a | No commands/agents/hooks/contrato público |

## Lente B

| Criterio T-05/U2a | Veredicto | Evidencia |
|---|---|---|
| GetSecurityInfo/bounds antes copy | ✓ | W:226;T:473;7fault modes |
| TokenUser/impersonación/bounds | ✓ | W:259;T:286,598;16errores+nativo |
| Invalida/cleanuponce/primary/BaseException | ✓ | W:319;T:490,616,664 |
| Pseudo/borrrowed handles | ✓ | W:311;T:653;0borrowedclose |
| Native readonly/diagnóstico local | ✓ | Closedtrue;outsiders/padrefalse;nativetrue |
| Parser/policy/ABI/tests regresión | ✓ | Prefix/suffix/tests byteexactos |
| Integridad final | ✓ | runtime91e279/test6671db exactos |
| Portable actual | ✓ | T:217;PLATFORM_UNSUPPORTED sinDLL |
| Linux nativo SHA nuevo | Pendiente QA | No reutilizar histórico |

## Lente C

| Criterio T-05/U2a | Veredicto | Evidencia |
|---|---|---|
| TokenUser/impersonación/error cierra consulta | ✓ | W:259;independiente+doubles |
| Bounds SID/SD antescopy | ✓ | W:226,289;size/offset/pointer/SID negativos |
| Borrowed conservado/owninvalida | ✓ | W:319;callbacks/pseudo/cleanup/BaseException;4handles2consultas |
| Grants peligrosos rechazan | ✓ | W:186;outsiders/padre nativosreadonly |
| Local/sintético separados | ✓ | W:152,252;sin capacidad/admisión |
| Integridad candidato | ✓ | 1419prepost+2targetSHA exactos |

## Gap heredado y remedio

| ID | Grado original | Escenario | Veredicto |
|---|---|---|---|
|A01|Important|25errorcleanup tests posteriores pasaban contra09green|**Corregido**:borrado en copia,stubs importables,RED causal y reescritura posterior|

Último RED08:16:06.908333Z; reescritura08:16:43.357255Z; primerGREEN08:17:03.874917Z. 42pares/84JUnit individuales y SHA/raw/sourcebefore/tests verificados. Los42exit4 iniciales no cuentan; tampoco se retoca el original. Prefix parser/policy/clases frozen, ABI y tests byteexactos; cuerpo reescrito distinto de preimagen. [Intento1 completo](storage-nt-security-u2a-review1-2026-10-11.md).

A ejecutó62PASS/4deselected y verificó1419FIX+368originales+19autoridades/cronología. B62PASS/4deselected;8consultas readonly/8LocalFree/1tokenclose/0borrowedclose. Su primer harness eligió fixtureRED sin testigo completo; diagnóstico conservado en herramientas, selección corregida sin cambiar producto. C61PASS/5deselected+5controles native readonly, cuatro propios cerrados;1419prepost. Estos grupos se solapan; no sumarlos como suite nueva. Ningún reviewer escribió archivos.

ROOT verificó1419artefactos/142inputs/42pairs/actor66JUnit/whole97,127937/scope2/0/0 antes de despachar. C mandatoria con overlay review-only y paths relativos reales, Ctrue/Dfalse/0warnings; dev.json canónico intacto. Tokens/eur/horas realesnull, sin imputación inventada.

Siguiente QA fresca Windows y Linux real del SHA nuevo. Los resultados de actor/revisores no sustituyen QA, no acreditan G2cadena, bootstrapTI, writer/store/lifecycle/ACK/ext4/controller/M1. Reportes finales de los revisores y salidas reales en herramientas, sin inventar archivos propios de stdout/JUnit para sus replays.
