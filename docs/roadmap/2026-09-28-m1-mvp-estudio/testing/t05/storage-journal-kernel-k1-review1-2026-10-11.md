# K1: revisión de dos lentes, intento 1

Fusión ROOT estructurada de los retornos finales A1/B1. Es normalización explícita, no transcripción literal. Diff completo de cuatro fuentes, base privada 7256bace33e78f307b571097ae07abee194c077b. Lentes A+B; C/D auto false. Resultado: 0 Critical, 1 Important deduplicado, 0 Minor. No adopción del producto.

## Tabla completa transferible de A1

| Criterio | Estado previo | Evidencia y límite |
|---|---|---|
| A1 cumplimiento | ✗ | A01; T05 continúa abierto |
| A2 alcance | ✓ | Cuatro fuentes completas, diff exacto |
| A3 tests/cobertura individual | ✓ | 88PASS/3deselected de A; actor whole354/362 y70/70, sin exclusiones |
| A4 constitución/fronteras | ✓ | Sólo memoria; no archivos, trust, ACK, GPU, BD |
| A5 verificación tareas cerradas | ✓ | No cierre T05/M1; 91PASS actor no sustituye QA |
| A6 generados/descripciones | ✓ | Sin OpenAPI ni interop; C2 adoptado |
| API privada/assembly/tipos exactos | ✓ | Siete funciones, capacidades opacas, identidad/pid y DTO cerrados |
| K1-01 plataforma/import | no verificable | Gates CPU pasan; Linux negativo real pendiente |
| K1-02 ABI antes recursos | ✓ | Signatures/offsets/widths/símbolos/normalización probados |
| K1-03 alineación/cuotas/overflow | ✓ | (8,8912896,9437176) solicitado, no reserva física OS |
| K1-04 registro/identidad/owner/pid | ✓ | Rechazo antes backend de falsificación/otro contexto/pid |
| K1-05 copias/bounds/independencia | ✓ | CPU positivo y testigo nativo ROOT actual |
| K1-06 custodia pre-entry/return | ✓ | Calls fuertes y cortes alloc/ack/register |
| K1-07 revocación/cierre único/outcome | ✗ | A01: corte de finalización después TRUE |
| K1-08 orden inverso/cuotas/primaria | ✗ | A01: closed con cuota/inflight incompletos |
| K1-09 lock real/pid | ✓ | Events/RLock sin sleeps; rechazo pid previo backend |
| K1-10 DTO frozen/sanitizados | ✓ | Enum cerrado y chaining suprimido; estado incorrecto A01 |
| K1-11 Windows memoria real | ✓ | ROOT alive17324→29416, B512/4096/65536, freeoriginal×1 y ausencia final; no reconstruye30628/19224 |
| K1-12 preimágenes/whole/review/QA | no verificable | 23guards intactos; QA independiente pendiente |
| TDD causalidad RED/GREEN | ✓ | Diez grupos funcionales; red1013=5FAIL/1PASS honesto; sin imports/fixtures rotos |
| TDD lock/pid anterior al test | ✓ | green050708→red0910 nullcontext/sinpid→green0910 acredita retiro/reescritura,7FAIL→7PASS |
| TDD historia íntegra temprana | no verificable | Sin fulltest snapshots antes supplemental-controls; no reconstrucción ni infracción inferida |

## Tabla completa transferible de B1

| Criterio | Estado previo | Evidencia y límite |
|---|---|---|
| Plataforma/import/ABI/errores | ✓ | Gates CPU/signatures/offsets/normalización |
| Identidad/registro/owner/pid | ✓ | Negativos calls0 |
| Cuotas/alineación/bounds/overflow | ✓ | Ocho máximas y negativos previos |
| Copias exactas/independientes/vacías | ✓ | Casos CPU ejecutados |
| Custodia alloc/copy/cuarentena global | ✓ | Entrada/registro y poison bloqueante |
| Reconocimiento completo cierre | ✗ | B01 igual A01 |
| Revocación/sinretry | ✓ | Free×1, outcome estable |
| Cierre inverso/rollback/primaria | ✓ | Casos existentes; A01 limita cierre afirmativo |
| Serialización/diagnósticos | ✓ | Events/RLock/DTO |
| Windows nativo/Linux real | no verificable | No ejecutados por B |
| Integridad diff | ✓ | Cuatro fuentes DIFF_MATCH |

## Gaps deduplicados y adjudicación ROOT

| ID | Alias | Grado | Estado | Fuente | Escenario y requisito |
|---|---|---|---|---|---|
| A01 | B01 | Important | pendiente | scripts/storage_journal_windows_io.py:499–502 | Release TRUE seguido por interrupción de CloseOutcome, _charge o inflight.remove publica state/outcome closed antes del registro completo. C2 §4.6 exige unknown estable y custodia conservadora. ROOT lee fuente/contrato; defecto confirmado, sin rebate. |

A1: 88PASS/3deselected; B1:87PASS/4deselected. Ambos conservaron fuentes y ejecutaron probes CPU privados. Probe charge: outcomeclosed/repeat_sameTrue/infoClosed/contextunknown/poisonTrue/charge(1,512,1023)/inflight1/free1. Probe remove: mismo con charge0. Probe constructor: outcomeunknown pero infoClosed. Control: closed/contextlive/charge0/inflight0/free1.

FIX1 debe probar primero cortes de creación, accounting y remoción y sus ventanas completas, incluidas contexto/rollback, sin retry ni free doble ni perder custodia. No basta intercambiar dos asignaciones sin cerrar las ventanas de estado. Tabla previa aprobada se conserva; revisión2 sólo reabre ante evidencia nueva. QA Windows/Linux y whole actual por fuente siguen obligatorios. T05/M1 permanecen abiertos.
