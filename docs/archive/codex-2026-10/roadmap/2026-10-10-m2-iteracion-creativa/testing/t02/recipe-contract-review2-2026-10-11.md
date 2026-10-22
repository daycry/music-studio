# Revisión del contrato de recetas — intento 2

**A+B sin gaps pendientes ni nuevos: 0 Critical, 0 Important, 0 Minor.** Los cuatro Important y el Minor anteriores quedan corregidos documentalmente. ROOT confirma los cambios contra las fuentes; no hay rebates ni deuda aceptada. Contrato detallado pendiente de QA/ratificación; T-02 sigue en-progreso, sin código ni RED.

ROOT 2026-10-11T11:22:01.942969+00:00: 36 hashes del snapshot y 34 guardas canónicas verificados. Base privada 2f57a45189de0bc73ffc063abadbbab1ef627785. Scope oficial: cinco archivos, cero fuera/avisos/exclusiones. C/D auto false. Revisión fresca de diff completo y correction.diff con traspaso íntegro A21/B8 e histórico de cinco gaps.

| Gap | Grado anterior | Veredicto actual | Evidencia y escenario resuelto |
|---|---|---|---|
| A01 | Important | Corregido | recipe-contract-design:7/9/10; enlaces relativos desde destinos canónicos, con overlay ADR |
| A02 | Important | Corregido | global design:153, recipe-contract-design:311, ADR0077:30; intención sellada separada del mapa medido posterior |
| B01 | Important | Corregido documentalmente | recipe-contract-design:235/248/250/252; FrozenDescriptor M2 aislado; nombres declarados no pasan por guard substring M1 |
| B02 | Important | Corregido documentalmente | recipe-contract-design:336/338/340/342; roles únicos/conocidos, required completo y media exacta; FLAC/WAV incompatible rechazado |
| A03 | Minor | Corregido | recipe-contract-design:394/395/396; reglas PEM/Bearer/URI separadas |

## Tabla completa de la lente A

| Criterio | Resultado | Evidencia (recipe-contract-design salvo indicación) |
|---|---|---|
| T01 CPU sin identidad ficticia; inferencia conserva campos | ✓ conservado | ADR0074:23/37; cpu-contract-design:147 |
| T01 decisión antes de integrar | ✓ conservado | ADR0074:19/94; tasks:93 |
| T01 Verificación/revisión/QA | ✓ conservado | tasks:93; testing/t01/contract-qa-2026-10-10:11/31/82; gate0 y16/16 |
| T02 inmutabilidad profunda | ✓ documental | 126/237 |
| T02 extras, secretos, NaN e IDs | ✓ documental | 114/126/185/388/394 |
| T02 padres y campos efectivos | ✓ documental | 158/185/191/291/293 |
| T02 legacy sin reescritura/defaults | ✓ documental | 369/371/386; descriptor249/251 |
| T02 focales/QA/aceptación producto | No verificable aún | tasks100/110/114;426; abierta y sin RED/código/focales |
| CA07 petición efectiva/nueva semilla | ✓ documental conservado | 291/293 |
| CA09 extensión/punto/contexto | ✓ documental conservado | 201/260/282/287/302 |
| CA11 repaint/regiones | ✓ documental conservado | 260/283/287/303 |
| CA15 crossfade multipadre | ✓ documental | 170/185/286/306/307/311 |
| CA29 CPU/derechos/historia | ✓ documental | 154/181/266/270/313/386; ADR0074 |
| DTO/variantes/versión/serialización | ✓ documental | 95/126/130/136/239/249/251/278 |
| Proyección /v1 y privacidad | ✓ documental | 334/336/338/340/344/348/402 |
| Constitución local/linaje/server | ✓ documental | Constitución16/18/19/32;154/185/253/311 |
| Sincroniza documento afectado | ✓ corregido | Constitución73; global153;311; ADR0077:30 |
| Alcance declarado | ✓ | tasks106; scope5/0fuera/0avisos/0exclusiones |
| Generados/interop/cobertura | n/a | Sólo docs; sin agents/commands/hooks/OpenAPI/schema;36/426/438 |
| Docs-style rutas | ✓ corregido | 7/9/10; sonda reviewer107destinos/6overlay/0rotos |
| Docs-style credenciales | ✓ corregido | 392/394/395/396/398; regla1 |

## Tabla completa de la lente B

| Criterio | Resultado | Evidencia (recipe-contract-design salvo indicación) |
|---|---|---|
| Inmutabilidad/determinismo | ✓ documental conservado | 125/129/237/330 |
| Versiones/errores/legacy | ✓ documental conservado | 250/252/352/366/386 |
| Descriptor/política | ✓ documental, B01 corregido | 235/248/254/390 |
| Proyección/inputs | ✓ documental, B02 corregido | 336/338/340/342 |
| Letra/basis/semilla | ✓ documental conservado | 191/207/291/293 |
| Padres/roles/mapas | ✓ documental | 185/187/309/311; global153 |
| Derechos/pins/autorización sintética | ✓ documental conservado | 254/258/270/313/348 |
| CPU sin engine ficticio | ✓ documental conservado | 154/311/348; ADR0074:37 |

## Evidencia y límites

A informó lectura completa y verificación propia36/36snapshot+34/34guardas; enlaces107/6overlay/0rotos y sonda textual7/7. Su primer intento de sonda terminó1 por stdin PowerShellASCII que alteró literales; repeticiónUTF8 pasó sin cambiar fuentes. B informó36/36hashes inicial/final y sonda con contratos públicos/M1: cuatro schemas token/tokenizer/max_tokens/token_budget válidos públicamente y rechazados por capturador M1; JobRequestFLAC estructuralmente válido frente source/WAV. Confirma que los escenarios originales permanecen en M1 y que el nuevo contrato exige resolverlos separadamente. Ambos knowledge-find backend/ADR: exit0 sin aciertos.

Esas sondas constan en respuestas de revisores; no son JUnit/producto T02 ni logs capturados por ROOT. ROOT verificó independientemente bytes, guardas y correcciones documentales. TDD n/a: prosa; cobertura producto n/a. Ledger-lint ROOT0:0 incoherencias,29 avisos Changelog en tareas abiertas; no confundir con scope0avisos. Jira/Confluence desactivados. No scripts/export-interop ni contrato HTTP cambiado.

FrozenDescriptor/proyecciones todavía no existen; Verificación propia T02, TDD y QA funcional pendientes. Sin GPU/Ollama/BD/admin/WSL/Docker. M1 NO-VERDE; ninguna aceptación de T02/M2. QA siguiente sólo documental con adaptación explícita del gate, sin presentar resultados como Playwright.

Evidencia privada en `.cache/dev-cycle/m2/creative-recipes-t02-contract-review2-20261011/`: prepare-root.receipt.json, verification-root.receipt.json, source.diff, correction.diff, global-correction.diff y fusion-root.receipt.json. Original/review1 intactos.
