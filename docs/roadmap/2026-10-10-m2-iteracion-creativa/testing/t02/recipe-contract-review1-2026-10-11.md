# Revisión del contrato de recetas — intento 1

**Pendiente de corrección: 0 Critical, 4 Important y 1 Minor.** A y B revisaron los cuatro documentos completos. C y D no aplican según selector oficial. El contrato detallado no está ratificado y T-02 continúa en progreso.

La base privada es `6a91f990354a9a979f038e6fbad28ba434faa1e1`. El scope oficial dio cuatro archivos en alcance, cero fuera y cero avisos. ROOT verificó 36 fuentes del snapshot y 34 guardas canónicas, además de 31 filas del inventario documental del arquitecto. El cambio del ledger posterior al freeze fue exclusivamente de ROOT y amplía el alcance documental.

| Gap | Grado | Referencia del candidato | Escenario y corrección requerida |
|---|---|---|---|
| A01 | Important | recipe-contract-design.md:7, 9, 10 | Los enlaces a spec, plan y ADR no resuelven desde el destino canónico. Corregir las rutas relativas. |
| A02 | Important | recipe-contract-design.md:278; design.md:153 | El diseño global exige mapas efectivos dentro de la receta; el contrato nuevo guarda intenciones inmutables. Sincronizar el diseño y aclarar dónde se conserva el mapa medido. |
| B01 | Important | recipe-contract-design.md:235; worker/contracts.py:77 | CapturedDescriptor M1 rechaza por substring claves que M2 permite en declaraciones de schema. Separar el capturador nuevo sin alterar el comportamiento histórico. |
| B02 | Important | recipe-contract-design.md:317; queue/resolver.py:328 | Una proyección FLAC puede pasar JobRequest y contradecir el descriptor WAV. Cerrar roles, obligatoriedad y media types contra la tarea seleccionada, sin conversión implícita. |
| A03 | Minor | recipe-contract-design.md:365 | La frase combina tres reglas de credenciales. Separar sus condiciones. |

## Conformidad documental comprobada

A encontró conformes la inmutabilidad propuesta, cierre de campos, identidades, padres, letra histórica, basis efectivo, versión y lector legacy. Las reglas CPU, derechos y separación de master/source son coherentes en su alcance declarado. La sincronización del diseño y los enlaces quedaron rojos.

B encontró conformes la serialización, los lectores sin defaults, letra/basis, padres/mapas, pins/derechos y ausencia de ejecución engine ficticia en CPU. Quedaron rojos el capturador de descriptor y la compatibilidad de inputs proyectados.

Ambos leyeron todo el diff y comprobaron los 36 hashes, sin discrepancias. A resolvió los enlaces desde el destino previsto y contrastó la evidencia histórica de T-01 en el checkout. B informó cuatro descriptors públicos válidos rechazados por el capturador y una petición FLAC estructuralmente válida pero incompatible con un descriptor WAV, usando Python gestionado y módulos del snapshot. Esos resultados constan en sus respuestas; no se presentan como JUnit ni como tests de producto T-02.

ROOT confirmó A01 por resolución de rutas, A02 contra el párrafo vigente y B01/B02 contra los validadores reales. No hay rebates ni deuda aceptada. La corrección debe mantener la autoridad histórica de M1.

## Límites

TDD n/a: prosa. Cobertura de producto n/a. No hay RED, código de recetas, QA documental final, admisión, render, GPU, almacenamiento ni aceptación M1/M2. La Verificación propia de T-02 sigue pendiente de implementar.

Evidencia privada: `.cache/dev-cycle/m2/creative-recipes-t02-contract-review1-20261011/prepare-root.receipt.json`, `verification-root.receipt.json`, `source.diff` y `fusion-root.receipt.json`. Diseños originales conservados en `creative-recipes-t02-contract-20261011/` sin modificaciones.


## Tablas por criterio

Transcripción de los veredictos entregados por las lentes. Las líneas se refieren al snapshot revisado; no al código futuro.

### Lente A

| Criterio | Veredicto | Evidencia |
|---|---|---|
| T-01: CPU sin identidad ficticia; inferencia conserva campos | ✓ | ADR-0074:23/31/37; cpu-contract-design:147 |
| T-01: decisión aceptada antes de integración | ✓ | ADR-0074:19/88/94; tasks:93 |
| T-01: Verificación, revisión y QA documentales | ✓ | tasks:93; testing/t01/contract-qa-2026-10-10.md:11/31/82, gate0 y16/16 |
| T-02: inmutabilidad profunda definida | ✓ documental | recipe-contract-design:125/307; tuples/backing canónico/copias |
| T-02: extras, secretos, NaN e identidades | ✓ documental | recipe-contract-design:114/125/127/183/361/365/375 |
| T-02: padres y campos efectivos | ✓ documental | recipe-contract-design:136/158/191/269 |
| T-02: legacy sin reescritura/defaults | ✓ documental | recipe-contract-design:325/342/344/357/359 |
| T-02: focales, QA y aceptación de producto | no verificable | tasks:100/112–114, tarea abierta; recipe-contract-design:391, prosa sin ejecución de producto |
| CA-07: petición efectiva y nueva semilla | ✓ documental | recipe-contract-design:269–273 |
| CA-09: extensión, punto y contexto | ✓ documental | recipe-contract-design:201/205/239/260/282 |
| CA-11: repaint y regiones | ✓ documental | recipe-contract-design:239/261/283 |
| CA-15: crossfade conserva ambos padres y roles | ✓ documental | recipe-contract-design:170/185/265/286–290 |
| CA-29: CPU honesto, derechos e históricos | ✓ documental | recipe-contract-design:154/181/247/251/294/357 |
| DTO, variantes, versión y serialización | ✓ | recipe-contract-design:95–132/136–251/257–265 |
| Proyección /v1 y privacidad | ✓ | recipe-contract-design:313–323; engine_contract:53; references:237. El defecto de compatibilidad media es B02 |
| Constitución: local, linaje y server | ✓ | Constitución:16/18/19/32; recipe-contract-design:154/183/185/233/311 |
| Constitución: sincroniza documento afectado | ✗ | Constitución:73; design:153 vs recipe-contract-design:278/292, A02 |
| Alcance declarado | ✓ | tasks:106; scope4docs/0fuera/avisos/exclusiones |
| Generados/interop y cobertura de producto | n/a | No código, OpenAPI, schemas ni agents/commands/hooks; recipe-contract-design:36/391/404 |
| Docs-style: rutas reales | ✗ | recipe-contract-design:7/9/10, A01 |
| Docs-style: frases cortas | ✗ | recipe-contract-design:365; regla1 y37palabras, A03Minor |

### Lente B

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Inmutabilidad profunda y determinismo | ✓ documental | Contrato §§4.1–4.3/4.8 |
| Versiones, errores y legacy sin defaults | ✓ documental | §§4.8–4.9; snapshots:69; test_job_attempt_schema:486 |
| Descriptor capturado y política nueva | ✗ | B01; capturador real del snapshot rechaza cuatro properties válidas |
| Proyección e inputs del descriptor | ✗ | B02; FLAC estructuralmente válido frente source/WAV |
| Letra efectiva, basis y semilla | ✓ documental | §§4.5/4.7; private_context:127; publications:164 |
| Padres, roles y mapas de intención | ✓ documental | §§4.4/4.7 |
| Derechos, pins y autorización sintética | ✓ documental | §§4.6–4.7; provenance/packages:110; runtime_verified=false |
| CPU sin ejecución engine ficticia | ✓ documental | §§4.3/4.8; ADR-0073/0074 |

No se reabren estos veredictos sin nueva evidencia. Los cinco gaps conservan su traza y deberán trasladarse íntegros al intento 2.
