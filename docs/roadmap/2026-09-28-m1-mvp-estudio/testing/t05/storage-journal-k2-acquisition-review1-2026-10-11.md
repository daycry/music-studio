# T-05/K2 — revisión de dos lentes, intento 1

ROOT fusiona las respuestas completas de A1 y B1 recibidas antes del cierre de sesión. Esta tabla es una normalización explícita de esas respuestas, no una transcripción literal. Se conserva la totalidad de criterios y límites; no se inventan archivos de retorno de los revisores.

Diff documental único: base `f286d2cc5f55419030c036163a390299809687df`, candidato 744 líneas, 63.074 bytes, SHA `110f291d8c61517794e8dc955f06d6ac591c1a11c263280b5e09dd68e97bfb78`. D significa storage-journal-acquisition-design.md. Los ✓ acreditan conformidad documental, nunca runtime.

| Criterio de A | Resultado | Evidencia |
|---|---|---|
| Elección O1 expresa y campos ratificados | ✓ | choice-root.receipt; D:110–116; alternativas D:69 |
| Alcance declarado | ✓ | tasks:208; scope1/fuera0/avisos0 |
| C2/O2, U1/U2 readonly y S1 | ✓ | D:54–58,698; C2:342; ADR0081:36 |
| Estado histórico frente al actual | ✓ | D:54,729; overlay ROOT K1 aceptado/K2 no liberado |
| Constitución/doctrina | ✓ | Constitución18,25,32–37; D:56,704,738 |
| K2-01 capacidades/PID/provenance | ✓ | D:122,132,142,187,424; exact type+registro+referencia |
| K2-02 profiles y máscaras cerradas | ✓ | D:195,206,208,219 |
| K2-03 nombres/UTF16 | ✓ | D:309,311,374; rechazo antes ENTRY |
| K2-04 SD/SID/GROUP/dedup | ✓ | D:237,266,342,354 |
| K2-05 locator/ancla/SDK | ✓ | D:315,326,330,332; navegación sin autoridad |
| K2-06 pre-entry/output/IOSB/refs/pins/charge | ✓ | D:382,390,432,485 |
| K2-07 éxito exacto | ✓ | D:297,508,510,518 |
| K2-08 fallo conocido/sentinel | ✓ | D:521,522,528,532; NULL e IOSB intacto/escrito distintos |
| K2-09 incertidumbre y poison | ✓ | D:303,305,519,525,546; sin retry/wait/cancel |
| K2-10 retorno antes de registro | ✓ | D:491,493,500; A6 íntegro antes publicación |
| K2-11 rollback acreditado/primaria/cleanup | ✓ | D:502,504,573,615 |
| K2-12 CloseTRUE/reconocimiento | ✓ | D:560,563,565,569; corte postTRUE unknown/free1/retry0 |
| K2-13 locks/pins/revocación/postorden | ✓ | D:546,552,554,575,579 |
| K2-14 quotas/backings/padding | ✓ | D:434,447,449,459,467; control10247, pool1048576, locator108565; no cota física OS/Python |
| K2-15 tombstones/rotación/reap | ✓ | D:452,457,475,479,481; monotónicos, cuatro owners totales |
| K2-16 DTO/errores | ✓ | D:589,598,613,617; sin HANDLE/path/SID/texto arbitrario |
| K2-17 structs/signatures/helpers | ✓ | D:237,258,282,290,416 |
| K2-18 nativo/G1 pendiente | ✓ | D:225,627,640,731; receta futura, no positivo inventado |
| K4a previo sin ciclo RootContext | ✓ | D:50,154,156,158; issuer requiere contrato antes RED |
| CREATE requiere K4b parent S1 | ✓ | D:176,178,185; seed CPU distinto |
| K3/K5/store/recovery/bootstrap/lifecycle/ext4 | ✓ | D:727,736,738; C2:343–351; ADR0081:62 |
| TDD/cobertura documental | ✓ | D:621–642; n/a prosa; 18 controles futuros no ejecutados |
| T05 audio-post/publicación/manifiesto | no verificable | tasks:215; pendiente |
| T05 ready/song.json/analysis | no verificable | tasks:216; pendiente |
| T05 limpieza/fallo validación | no verificable | tasks:217; pendiente |
| Verificación de tarea cerrada | ✓ | T05 no se cierra; tasks:202; D:738 |
| Generados/interop/OpenAPI | ✓ | no aplica, único Markdown |
| Enlaces/docs-style | ✓ | seis enlaces/cinco destinos; guía leída, no violación citable |

| Criterio de B | Resultado | Evidencia |
|---|---|---|
| K2-01 admisión/owner/PID | ✓ | D:117–189; K4a previo, CREATE K4b |
| K2-02/03 perfiles/dispositions/UTF16 | ✓ | D:191–227,374–390 |
| K2-04/17 SDK/layouts/descriptor | ✓ | D:229–305,342–372; layouts CPU propios,25 pins Microsoft |
| K2-05 locator/ancla | ✓ | D:307–340; G1 DIRECTORY/no-follow pendiente |
| K2-06/07/08 output/IOSB/completion | ✓ | D:483–542; slot previo/NULL+sentinel/success exacto |
| K2-09/10/11 PENDING/cortes/rollback | ✓ | D:487–504,519–530; completion antes rollback |
| K2-12/13 cierre/pins/carreras | ✓ | D:544–585; reconocimiento íntegro/CloseHandle≤1/postorden |
| K2-14/15 cuotas/padding/lifetime | ✓ | D:392–481; control10247/locator108565/ACL≤236 |
| K2-16 sanitización/DTO | ✓ | D:587–617; campos/tipos cerrados |
| Ejecución K2/K2-18 nativo | no verificable | D:642,727–738; todos gates runtime pendientes |

Gaps: 0 Critical, 0 Important, 0 Minor; sin rebates. C/D auto=false por selector, no auditoría completa de seguridad o rendimiento.

A verificó diff/candidato/original íntegros, 28/28 pins privados, 7/7 fuentes K1/U1/U2 canónicas, 6/6 enlaces y 25/25 pins Microsoft descargados sólo en memoria. Scope0, ledger0/una advertencia UTF8 histórica, selector0, knowledge-find0 sin aciertos. B verificó 28/28 pins, 27/27 fuentes originales, 25/25 Microsoft, overlay test e2→b1 por AST idéntico y layouts SD40/ACL8/ACE12/US16/OA48/IOSB16. Sin escrituras ni llamadas nativas operativas por ambas lentes.

Diagnósticos de auditores preservados en sus mensajes: A uv desde snapshot parcial exit2, tier sin agents exit2 y stdout cp1252 exit1, corregidos con intérprete gestionado/tier del receipt/stdout UTF8; B quoting -c inicial fallido, corregido stdin. No fallos de producto. ROOT conserva también preflight1 propio con test formateado; overlay acotado de AST idéntico, no excepción general.

QA documental y adopción aún pendientes. K4a issuer/principal/pin, G1 real, K3/K4b/K5/rotación/store/ACK/recovery/bootstrap/lifecycle/ext4/E2E/manuales permanecen obligatorios. T05 y M1 abiertos. No liberación runtime K2 por este informe.
