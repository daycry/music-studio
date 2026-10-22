# Revisión de recetas creativas — producto — intento 1

ROOT 2026-10-11T12:13:18.659462+00:00: **0 Critical / 3 Important / 0 Minor**, pendientes de corrección. Lentes frescas A/B/C; D auto false. Scope oficial: cuatro archivos, cero fuera de alcance, avisos o exclusiones de usuario. Base privada `296c19ac30f9313e6ee063000c32cf7e3f5339cd`.

Las cuatro fuentes siguen byte exactas a la entrega original; 219 artefactos conservados, 144 pruebas y cobertura oficial 88,1578947368 % verificados en la preparación. El verde de esos casos no cubre los contraejemplos nuevos B01/B02 ni sustituye la causalidad TDD de fade. A aprobó funcionalidad bajo sus pruebas; B aporta evidencia nueva que invalida la aceptación del cierre de schemas. No se altera ni se oculta ninguna salida original.

| # | Grado | Gap | Tarea | Veredicto ROOT | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Fade sin RED causal previo | T-02 | Pendiente; borrar sólo la implementación afectada y reescribir tras RED | recipes.py:827; preimagen red3 y dos casos ya verdes, lente A |
| B01 | Important | Objeto en type union no cerrado | T-02 | Pendiente; reproducir y cerrar schemas de objeto en unions | recipes.py:965; payload type object/null acepta undeclared, lente B |
| B02 | Important | Mapas y valores const confundidos con schemas | T-02 | Pendiente; recorrer posiciones reales de schema | recipes.py:969; propiedad llamada properties y const objeto válidos rechazados, lente B |

T-02 permanece en-progreso, sin aceptación M2. Corrección obligatoria por implementer fresco, seguida de revisión intento 2 de 3 y QA independiente. No se prueba SQL, derechos reales, generación musical, almacenamiento, GPU ni runtime M1.

## Lente A — salida completa

Lente A · intento 1 · diff `296c19ac30f9313e6ee063000c32cf7e3f5339cd...snapshot` (4 ficheros nuevos)

Diff completo leído por ficheros: `__init__.py` 69 líneas, `recipes.py` 1502, tests 1142 y arquitectura 136. Reconstrucción de las adiciones y cuatro SHA coinciden exactamente con el snapshot.

Referencias: `R` = `apps/server/app/creative/recipes.py`; `T` = `apps/server/tests/test_creative_recipes.py`; `D` = `docs/arquitectura/iteracion-creativa.md`.

| Criterio (T-02 / contrato ratificado) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| Aceptación: mutar nested no cambia bytes/hash | ✓ | R:291, R:361, R:732; T:197, T:830; casos ejecutados PASS |
| Aceptación: rechazar extras, secretos, NaN e IDs/refs inválidos | ✓ | R:117, R:135, R:285, R:1180; T:222, T:313, T:1004; PASS |
| Aceptación: conservar padres y campos efectivos | ✓ | R:860, R:1088, R:1156; T:397, T:483, T:1112; PASS |
| Aceptación: legacy sin reescritura | ✓ | R:1321, R:1370; T:211, T:321, T:795; PASS |
| Verificación propia ejecutada y entregada | ✓ | `verification-final2.receipt.json`: argv focal, exit0, UTC y cuatro SHA; JUnit144/0fallos/0errores |
| Revisión/QA conformes antes de cierre | no verificable | `tasks.md:98`: en-progreso; QA independiente pendiente. No se presenta como tarea cerrada |
| TDD antes del comportamiento implementado | ✗ | A01: fade ya implementado en `red3-preimage.py:603` y ambos tests pasan contra esa preimagen |
| Alcance y ownership | ✓ | `scope.stdout`:4 ficheros,0 fuera,0 avisos,0 exclusiones de usuario; coincide `tasks.md:105` |
| §4.1–4.3 envelope, versión, límites, tipos y canonicalización | ✓ | R:135, R:217, R:245, R:679, R:714; T:279, T:298, T:739, T:1031; PASS |
| §4.4 pertenencia, antecedentes y raíz | ✓ | R:455, R:477, R:494, R:1180; T:222, T:413; PASS |
| §4.5 letra histórica, autoría y composite | ✓ | R:537, R:860; T:397, T:429, T:449, T:941, T:1112; PASS |
| §4.6 descriptor M2 aislado y lectura sin defaults nuevos | ✓ | R:361, R:403, R:1235; T:524, T:532, T:925; PASS; capturadores M1 intactos |
| §4.6 selección, schemas cerrados y capacidades | ✓ | R:938, R:978, R:991; T:564, T:583, T:627, T:914; PASS |
| §4.6 pins y ausencia honesta de autoridad runtime | ✓ | R:561, R:616, R:1217; T:865, T:950; PASS |
| §4.7 ocho operaciones, cardinalidad y mapas exactos | ✓ funcional / ✗ TDD fade | R:635, R:796, R:1156; T:397, T:665, T:715; PASS actuales; A01 conserva brecha causal |
| §4.7 basis ganador, salida elegida y params exactos | ✓ | R:1088; T:483, T:508, T:1066; PASS |
| §4.8 wrappers/readers/hash externo y embebido | ✓ | R:732, R:1283, R:1307, R:1321; T:279, T:765, T:1046; PASS |
| §4.8 proyección `/v1`, inputs/media/roles y separación master/source | ✓ | R:978, R:1445, R:1467; T:251, T:583, T:592, T:603, T:807; PASS |
| §4.9 privacidad y errores sin entrada encadenada | ✓ | R:78, R:113, R:117, R:135; T:313, T:345, T:1061, T:1083; PASS |
| §4.9 históricos con ausencias/nulls/raw y seed grande | ✓ | R:747, R:1321, R:1370; T:211, T:321, T:795, T:999; PASS |
| Cobertura como apoyo, sin sustituir lectura | ✓ | `coverage-final2.json`:88,1578947% líneas+ramas,894 statements,398 branches,0 líneas excluidas; receipt exit0 |
| Constitución: server sin torch, inferencia/CPU, historia y derechos | ✓ | Constitución:31,39,41,84; R:494, R:501, R:616, R:860, R:1217; ninguna escritura/publicación introducida |
| Constitución: unidades, idioma y ledger | ✓ | Constitución:63,65,71; R:245; D:1; task permanece abierta y actor no modifica ledger |
| Generados y documentación descriptiva | ✓ | D:10–136 describe código y límites; sin cambios commands/agents/hooks ni contratos públicos. Export privado asignado expresamente a T-04 |
| Límite de autoridad T-02 | ✓ | D:126; tests sintéticos puros; sin SQL, admisión, engine, audio real, render ni publicación |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| A01 | Important | Captura/validación de fade implementada sin RED causal propio; la caracterización posterior no cumple la ley TDD | T-02 | `apps/server/app/creative/recipes.py:827`; `apps/server/tests/test_creative_recipes.py:665` | `red3-preimage.py` SHA `126dfd98523f698a0103dbfaf54271c15051b4b0a303f24fcc970225371ed749` ya contiene el cuerpo fade en603–608. Ejecutados ambos casos finales contra esa preimagen: **2 PASS**. No hay nodo RED funcional de fade entre los JUnit conservados; ambos aparecen PASS en `green4.xml`. Los RED anteriores alcanzan trim/crossfade/captura ausente, no esta rama. `tasks.md:118` y skill TDD exigen rojo antes del comportamiento; declararlo caracterización es honesto, pero no satisface ese requisito. |

Lo ejecutado:

- Python gestionado con entorno cargado: auditoría SHA/diff/JSON/JUnit → cuatro fuentes exactas; diff completo exacto; scope4/0/0.
- Ejecución directa de los **144 casos del snapshot:144 PASS/0 FAIL**. Sin conftest ni bootstrap de `app`; `ResolutionError` y `closed_schema` compilados literalmente del AST del snapshot.
- Prueba causal sobre `red3-preimage.py`: dos casos fade **PASS/PASS**. Extend/repaint produjeron `RECIPE_INVALID`; no se les atribuye caracterización verde ni se generaliza A01.
- Lectura de recibos finales y cobertura oficial del actor; no sustituye QA independiente.

Fuera de mi lente (no reportado): sin hallazgos adicionales. Sin `docs/knowledge/` en snapshot; ADR-0073/0074/0077 contrastados directamente. No aceptación integral M1/M2 ni pruebas musicales, GPU, Docker, WSL o custodia.


## Lente B — salida completa

Lente B · intento 1 · diff 296c19ac30f9313e6ee063000c32cf7e3f5339cd...HEAD ∪ cambios privados (4 ficheros nuevos; lectura completa por tramos).

| Criterio / objetivo | ✓/✗ | Evidencia |
|---|---|---|
| T-02: captura, inmutabilidad, UTF-8, límites y sello | ✓ | `recipes.py:135`, `:285`, `:1235`; tests propios 144 PASS |
| T-02: padres, raíces, derechos, letra, basis y mapas | ✓ | `recipes.py:796`, `:860`, `:1088`, `:1156`; negativos y roundtrips ejecutados |
| T-02: cierre correcto de params_schema | ✗ | `recipes.py:965`; dos contraejemplos propios reproducidos |
| T-02: descriptor, capacidades, binding y pins | ✓ | `recipes.py:403`, `:978`, `:991`; tests ejecutados |
| T-02: lectores nuevos/legacy y proyecciones | ✓ | `recipes.py:1307`, `:1321`, `:1445`, `:1467`; tests ejecutados |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto | CWE |
|---|---|---|---|---|---|---|
| B01 | Important | Se sellan parámetros con objetos abiertos | T-02 | `apps/server/app/creative/recipes.py:965` | Schema raíz cerrado con `properties.payload={"type":["object","null"]}` sin `additionalProperties:false`. Params `{"payload":{"undeclared":42}}` se capturan correctamente pese a que el contrato §4.6 exige cerrar cada schema de objeto. La guarda únicamente reconoce `type=="object"` o presencia de `properties`. | — |
| B02 | Important | Se rechazan schemas cerrados válidos al interpretar mapas y datos como schemas | T-02 | `apps/server/app/creative/recipes.py:969` | Schema `{"type":"object","properties":{"properties":{"type":"string"}},"additionalProperties":false}` y params `{"properties":"artistic setting"}` producen `RECIPE_INVALID`. El recorrido visita el mapa de propiedades y confunde su nombre declarado `properties` con una keyword de schema. También rechaza un `const:{"type":"object"}` dentro de un schema de objeto cerrado válido. | — |

Lo ejecutado: intérprete gestionado `.venv/Scripts/python.exe -B`, `pytest.main(..., "--noconftest", "-p", "no:cacheprovider")` sobre snapshot → **144 passed**, exit 0; un aviso `Unknown config option: cache_dir` por desactivar caché. **16 imports** de `app.*`/`engine_contract` comprobados dentro del snapshot; NumPy ausente. Probes independientes: los tres schemas/params pasan `Draft202012Validator`; B01 → `CAPTURE_ACCEPTED`; ambas variantes B02 → `CAPTURE_REJECTED RECIPE_INVALID`. Sin escrituras ni ejecución de BD/GPU/Docker/WSL.

Fuera de mi lente: TDD, conformidad documental y seguridad corresponden a A/C. No se acredita integración, generación musical, custodia ni cierre T-02/M2.


## Lente C — salida completa

Lente C · intento 1 · diff `296c19ac30f9313e6ee063000c32cf7e3f5339cd...HEAD` (4 ficheros del snapshot; lectura dividida por ficheros)

| Criterio / objetivo T-02 | ✓/✗/no verificable | Evidencia |
|---|---|---|
| Secretos y namespaces | ✓ | `apps/server/app/creative/recipes.py:117`, `:184`, `:195`; pruebas focales y cinco blobs propios rechazados. `PRIVATE KEY` es patrón de rechazo. |
| Errores sin eco ni cadena privada | ✓ | `recipes.py:78`, `:1270`; pruebas focales y probes confirman `field=None`, `__context__=None`, `__cause__=None`. |
| SSRF / refs de schema | ✓ | `recipes.py:938`; cuatro probes `$ref` externo, `$dynamicRef`, `$recursiveRef`, `$id` rechazados; **0 llamadas de red**. |
| Traversal / transporte | ✓ | `recipes.py:348`, `:773`, `:1467`; diez rutas inseguras rechazadas y proyección focal aprobada. |
| Deserialización / límites | ✓ | `recipes.py:135`, `:217`, `:1263`; JSON estricto, duplicados/ciclos/non-finitos rechazados; sin pickle/eval. |
| Inyección, auth y permisos introducidos | ✓ | Diff completo: sin SQL, shell, plantillas ejecutables, endpoints, sesiones ni efectos de autorización. `recipes.py:1184` comprueba coherencia interna; el DTO no acredita pertenencia real. |

Gaps: **sin hallazgos — 0 Critical / 0 Important / 0 Minor**.

Lo ejecutado: Python gestionado `.venv`, imports verificados dentro del snapshot; pytest focal **56 passed / 88 deselected, exit 0**, dos avisos de configuración/rewrite; probes CPU **exit 0**. Reconstrucción de todas las adiciones de `source.diff`: **4/4 coincidencias byte exactas**, sin eliminaciones.

Límites: revisión de seguridad del payload puro; no acredita integración, custodia, ejecución ni QA integral. Sin modificaciones, Git, BD, red, GPU o servicios.

Fuera de mi lente (no reportado): ninguno.


