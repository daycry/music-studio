# T-05/U2b1 — revisión de dos lentes, intento 3

ROOT fusiona A+B a 2026-10-11T10:26:29.465093+00:00: **0 Critical,0 Important,0 Minor**. Diff único test false_query sobre base9e27683, runtimeaf192 intacto; C/Dauto false sin avisos. Revisiones1/2 completas conservadas, cuatro Important corregidos en2 no reabiertos sin evidencia nueva. Esta revisión autoriza QA2 independiente; no CAS ni cierre T05/M1.

| # | Grado anterior | Gap | Tarea | Veredicto actual | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Cleanup sin primaria escrito antes RED | T05/U2b1 | corregido intento2, conservado | runtimeaf192 byteexact; FIX1 seis pares y revisión2 A/B/C |
| B01 | Important | Custodia posPENDING perdida | T05/U2b1 | corregido intento2, conservado | runtimeaf192 byteexact, no nueva evidencia adversa |
| B02 | Important | Retry cierre con None | T05/U2b1 | corregido intento2, conservado | runtimeaf192 byteexact, no nueva evidencia adversa |
| B03 | Important | Adquisición SUCCESS antes registro perdida | T05/U2b1 | corregido intento2, conservado | runtimeaf192 byteexact, no nueva evidencia adversa |
| QA1-FIX2 | Fallo de fixture | FALSE Linux no alcanza retorno por ctypes ausente | T05/U2b1 | corregido por emulación scoped del nodo | F1fallo/F3controlpreimageexacta; A/Bpropios comprueban FALSE5/cierre202/restauración |


ROOT verificó freeze470payload/1reparsestat-only/25snapshotinputs, AST exterior y assertions anteriores exactos, raws/JUnit/sourceSHA/UTC/F1-F3-causal/5TAR+F2diagnostic y27hijosnuevos por plataforma. QA1frozen392 íntegro; nuevos Windows139/Linux110+29SKIP actor,139nodos/skips sin cambios. No se suman ejecuciones de actor/revisores a un total de casos disjuntos.

A ejecutó auditores directos Windows real y Linux simulado, sin suite nueva; output propio reportado por mensaje, sin capsule raw. Un auditor salió1 al leer ledger mixtoUTF8 después de sus comprobaciones; relectura byte-safe posterior0, no fallo de producto. ROOT conserva la salida completa y limitación, no inventa JUnit propio deA. B ejecutó focal+vecinos18PASS/121deselected y probe Linux sintético, ROOT coteja JUnit/receipt/witness. Ninguno ejecutó Linux nativo propio; QA2 lo hará. Harness F1/F3 inicial reconstruido/sellado posterior explícito, no sello contemporáneo. F2propio posteriorF3, diagnósticoQA1 previo ya disponible.

No coverage nueva atribuida a FIX2, testonly. Resultados actor no sustituyen QA; noPENDINGnativo/nohandler repetido/nofugasglobal/geometry/fullchain/store/ACK/lifecycle/ext4/E2E/manuales. Canon91e279/6671db intacto. Jiraoff, sin publicaciones de conocimiento ni mensajes externos. Tokens/eur/horasIA realesnull.

## Tablas completas recibidas


Lente A · intento 3 · diff `9e27683fd0e484d17a63120e8cac448c635b0f9a...HEAD` ∪ cambio sin comitear (1 fichero)

**Sin defectos de conformidad: 0 Critical, 0 Important, 0 Minor.** Diff completo leído. Veredictos aprobados de review2 conservados; reevaluado únicamente FIX2.

Rutas de código/documentación relativas al snapshot review3. `F` = `.cache/dev-cycle/m1/storage-nt-observation-u2b1-fix2-20261011`.

| Criterio (T-XX / objetivo) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| T05/U2b1 — alcance mínimo autorizado | ✓ | `tests/test_storage_journal_windows.py:978`: único nodo modificado; `tasks.md:208,4950` declara fichero y reparación. Scope registrado exit0, 1 cambiado, fuera/avisos/exclusiones de usuario vacíos. |
| Preservación runtime y pruebas anteriores | ✓ | Auditor propio: runtime SHA `af192c76519d88e8b1cbd267a8326bf74e54a871dbcd5c0dc5a13a8297e56db4`; test SHA `020aeffe612e1c43aa1c420c4f969babfabf277f269ca96050d6d6c7d9c5adfe`. Otras 67 definiciones y AST completo exterior al nodo intactos. |
| Canal last_error exclusivamente local/Linux | ✓ | Test:979–987: celda privada y `monkeypatch`; Windows conserva ctypes real. Ejecución propia verifica restauración de APIs y ausencia de APIs tras teardown de la rama Linux simulada. |
| FALSE con buffer plausible continúa rechazándose | ✓ | Doble:804–822 escribe buffer, establece error5 y retorna0; runtime:687–699 comprueba retorno antes de interpretar metadata. Nodo propio pasa con canal Windows real y rama Linux simulada. |
| Cierre propio exactamente una vez; sin poison ocultado | ✓ | Test:992–994 conserva `[202]`, comprueba error5 y `_RETAINED is None`; no reset de custodia añadido. Ejecución propia: retained=None, LIVE_CONTEXTS0. |
| F1/control F3 anteriores a reparación | ✓ | Fuentes físicas exportadas F1/F3 verificadas contra f36ada. JUnit F1: 1FAIL/exit1; F3: 1PASS/exit0, canal set5/get5, retainedfalse. |
| Cronología y procedencia declaradas honestamente | ✓ | `F/report.md`, receipts y `harness-provenance.json`: F1 10:06:42Z → F3 10:06:55Z → F2 propio 10:07:20Z; diagnóstico QA1 previo disponible. Harness reconstruido/sello posterior explícitos, sin atribuir sello contemporáneo. |
| TDD de nueva funcionalidad runtime | ✓ — n/a | Runtime byteexact; fallo reproduce regresión real del doble existente, no ImportError artificial ni crédito RED de funcionalidad nueva. A01 y demás correcciones review2 conservadas sin nueva evidencia que las invalide. |
| Inventario y omisiones preservados | ✓ | Auditor propio de JUnit: 139 nodos en idéntico orden Windows/Linux/QA1; mismos 29 skips Linux y mismos motivos; ningún skip Windows nuevo. |
| Regresión/cobertura dentro de su alcance | ✓ | JUnit actor FIX2 leído: Linux110PASS29SKIP, Windows139PASS, ceroFAIL/ERROR. Cobertura nueva runtime n/a, test-only; QA1 combinada92,32914923% sin exclusiones es histórica y no se atribuye al SHA FIX2. |
| Constitución explícita | ✓ | `docs/CONSTITUTION.md:32,43,65,69`: sin cambios de BD, almacenamiento, estados ni contratos. Emulación sintética identificada como tal. |
| Tareas cerradas y Verificación declarada | ✓ | Auditor byte-safe: 17 estados formales, cero completados. T05:202 en-progreso y CA:215–217 abiertos; no se exige cerrar todo T05/M1 en este componente. |
| Generados/E2–E3 | ✓ — no aplica | Diff exclusivamente test; no toca commands/agents/hooks ni contratos generados. |
| QA2/adopción/ext4/E2E/manuales/M1 | no verificable aquí | Gates pendientes y límites expresos; resultados actor y llamadas propias no acreditan aceptación integral. |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto | CWE |
|---|---|---|---|---|---|---|
| — | — | Sin defectos | T05/U2b1 | — | — | — |

Lo ejecutado:

Comando exacto usado en los tres auditores, con el cuerpo correspondiente pasado mediante `$auditCode` en cada llamada:

```powershell
. .\scripts\env.ps1
uv run --frozen --no-sync --all-packages python -X utf8 -B -c $auditCode
```

- **Auditor directo, exit0:** AST/SHA y llamada al nodo mediante `pytest.MonkeyPatch.context()`. Windows real: PASS/APIs originales conservadas. Rama Linux **simulada sobre Windows**, retirando temporalmente las dos APIs antes de llamar al nodo: PASS/APIs ausentes nuevamente tras teardown. Custodia final=None; LIVE_CONTEXTS0.
- **Auditor físico/JUnit, exit1 de lectura:** verificó primero AST exterior, fuentes físicas F1/F3, sus SHA, JUnit y paridad139/29. Después falló únicamente `ledger.read_text(encoding='utf-8')`: `UnicodeDecodeError`, byte `0xf3`, posición374854. No fallo de producto ni de pytest; esas comprobaciones previas imprimieron resultados válidos.
- **Relectura byte-safe, exit0:** leyó `tasks.md` como bytes y extrajo estados con `re.findall(rb'^- \*\*Estado\*\*: ([^\r\n]+)', raw, re.M)`; `len(states)==17`, ninguno contiene `b'completado'`. Scope exit0 confirmado.

Leídos íntegros literal A, spec, plan, constitución, reportes review1/review2/QA1, nodo y doble afectado; ledger por secciones pertinentes/estados. Snapshot sin `docs/knowledge`: sin memoria técnica curada aplicable. No writes de producto/canon/ledger/Git/frozen, ni fixtures/hijos nuevos.

Fuera de mi lente (no reportado): sin incidencias nuevas para enrutar. C/D auto false. No ejecución Linux nativa propia ni claim QA integral/T05/M1.


Lente B · intento 3 · diff `9e27683fd0e484d17a63120e8cac448c635b0f9a…HEAD` ∪ cambios sin comitear (1 fichero). **Sin defectos nuevos**; B01/B02/B03 aprobados en intento 2 conservados.

| Criterio (T05/U2b1 FIX2) | ✓/✗/no verificable | Evidencia relativa al snapshot |
|---|---|---|
| Emulación limitada al nodo Linux | ✓ | tests/test_storage_journal_windows.py:978; celda local, sin cambios runtime. |
| FALSE sobre buffer plausible y error 5 | ✓ | tests:819,989; probe propio registra handle202/kind18/buffer poblado/retorno0/error5. |
| Cierre202 y ausencia de poison | ✓ | tests:992; prueba actual y probe pasan sin reset de `_RETAINED`. |
| Restauración del monkeypatch | ✓ | tests:981; probe parte con APIs ausentes, `undo()` restaura ausencia y después identidades nativas originales. |
| Windows conserva APIs reales | ✓ | tests:979; ejecución propia Windows pasa y conserva identidad de ambas funciones. |
| Sin masking nuevo | ✓ | tests:992–994; una excepción entered retenida o falta de cierre incumple las assertions. Runtime:476,695 conserva tratamiento diferenciado de PENDING/FALSE. |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto | CWE |
|---|---|---|---|---|---|---|
| — | — | Sin defectos | T05/U2b1 | — | — | — |

Lo ejecutado: entorno `scripts/env.ps1`, `uv run --frozen --no-sync --all-packages python -X utf8 -B`, pytest focal y vecinos: **18 PASS,121 deselected,exit0**. Además un probe sintético de la rama Linux/restauración: PASS. Evidencia propia en `.cache/dev-cycle/m1/reviewer-u2b1-b3-20261011/{junit-b3.xml,receipt-b3.json}`; hashes posteriores runtime `af192…` y tests `020ae…`, fuentes congeladas intactas.

Leídos receipts/JUnit del actor: Linux110PASS29SKIP y Windows139PASS, ceroFAIL/ERROR. **Linux propio no ejecutado**; el probe de rama no es testigo nativo Linux. Sin memoria técnica en snapshot. No acredita plataformas distintas, CAS, QA conjunta ni cierre T05/M1.

Fuera de mi lente: disciplina TDD/proveniencia corresponde a A; ningún hallazgo adicional.
