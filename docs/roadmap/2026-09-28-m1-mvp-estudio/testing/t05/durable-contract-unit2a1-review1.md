# Contratos CPU — revisión1

Cuatro lentes frescas A/B/C/D: **0Critical/0Important/0Minor**. QA independiente siguiente; no aceptación T05/M1.

### Lente A

**Lente A · T-05/U2a1 · inspección 1: sin gaps Critical, Important ni Minor en el alcance revisado.** Este resultado no acepta T-05 completa ni M1.

Leídos los tres archivos completos y el diff congelado: coinciden entre sí y con las copias anteriores/posteriores de la corrida oficial.

| T-05 → criterio de U2a1 | Resultado | Evidencia fichero:línea |
|---|---|---|
| Autoridad inmutable, ULID, ordinal/secuencia positivos, índice original y semilla no negativa | ✓ | `contracts.py:248`; tests `test_worker_contracts.py:124`, `:155`, `:321` |
| Procedencia tipada, descriptor profundamente inmutable, carga/observación coherentes y digest desconocido separado | ✓ | `contracts.py:138`, `:206`; tests `test_worker_contracts.py:184`, `:191`, `:387` |
| JSON finito, acotado y validación recursiva de secretos/extras | ✓ | `contracts.py:49`, `:114`; tests `test_worker_contracts.py:362`, `:369` |
| PostPlan versionado, 1–64 entradas únicas, copia consistente y autoridades coincidentes | ✓ | `contracts.py:301`, `:323`; tests `test_worker_contracts.py:244`, `:299`, `:407` |
| Rutas relativas sin traversal, alias Windows ni controles Unicode | ✓ | `contracts.py:263`; tests `test_worker_contracts.py:221`, `:426` |
| Paquete cerrado y resultados discriminados; éxito cotejado con autoridad completa del plan | ✓ | `contracts.py:375`, `:395`, `:433`; tests `test_worker_contracts.py:251`, `:448`, `:471` |

| Criterio de revisión | Resultado y fundamento |
|---|---|
| 1. Cierres realmente implementados | ✓ Coherencia: T-05 permanece `en-progreso`, `tasks.md:198`. Sus CA completos —publicación/FFmpeg, ready/snapshot/beats y limpieza/fallo— siguen abiertos en `:211`, `:212`, `:213`; esta unidad no los acredita. |
| 2. Alcance declarado frente al plan | ✓ Los tres archivos corresponden a worker y su test declarados en `tasks.md:204`. La división contractual está explícita en `:1063` y concuerda con `improvement-plan.md:64`. Diff aislado: tres archivos, ninguno fuera de alcance. |
| 3. Tests y cobertura | ✓ Lectura de las aserciones completas. Evidencia oficial: **74 PASS**, exit **0**, módulo completo **268/274 = 97,8102 %**, cero exclusiones. Única traza `final-official`; sin promedios ni unión histórica. `__init__.py:1` contiene únicamente docstring: TDD n/a. |
| 4. Constitución explícita | ✓ Sin violaciones observadas de música local (`CONSTITUTION.md:16`), pertenencia (`:18`), frontera server/engine (`:32`, `:33`), confinamiento (`:43`), estado/verificación (`:58`) y unidades/ULID (`:64`). |
| 5. Verificación de tareas cerradas | No aplica a un cierre: T-05 está abierta. Las verificaciones de `tasks.md:207` y `:208` no se acreditan mediante esta suite dedicada. No se ejecutaron para suplir evidencia. |
| 6. Generados y piezas descriptivas E2/E3 | No aplica al diff: no toca `commands/`, `agents/` ni `hooks/`. Tampoco cambia `/v1`, schemas o manifiestos públicos. No corresponde ejecutar `export-interop.py --check`. |

TDD original contrastado mediante argv, UTC, JUnit y fuentes previas: RED por semilla negativa, payloads inválidos aceptados, versión booleana, controles Unicode y autoridad de resultado discordante. Los errores de BOM, `AttributeError` y reparación del ULID sintético no cuentan como RED causal.

Evidencia ejecutada por el revisor: lecturas y cotejos de hashes/diff. Los 74 tests y el lint provienen de las trazas originales inspeccionadas; no se repitieron. Son pruebas nativas Windows con datos sintéticos, sin acreditar captura confiable de procedencia, SQL/CAS, medios, custodia, publicación física, Docker o E2E.

### Lente B

**Sin defectos de corrección identificados en U2a1.**

| Criterio | Resultado | Fichero:línea |
|---|---|---|
| Tipos estrictos, límites y finitud | ✓ | `apps/server/app/worker/contracts.py:30` |
| Procedencia y descriptor profundamente inmutable | ✓ | `apps/server/app/worker/contracts.py:139` |
| Validación de rutas | ✓ | `apps/server/app/worker/contracts.py:263` |
| Consistencia de copias, índices y autoridades | ✓ | `apps/server/app/worker/contracts.py:305` |
| Resultados vinculados al plan y paquete cerrado | ✓ | `apps/server/app/worker/contracts.py:375` |

Critical: 0 · Important: 0 · Minor: 0.

Diff completo de tres archivos cotejado con las fuentes congeladas. Evidencia oficial comprobada: 74 PASS; cobertura real del módulo completo **268/274 = 97,8102 %**, cero exclusiones. RED causales contrastados con argv, UTC, JUnit y capturas previas.

Revisión estática y comprobaciones en memoria; no repetí la suite ni escribí archivos. El resultado se limita a contratos tipados: no acredita runtime, publicación durable ni aceptación de T-05/M1.

### Lente C

**Sin hallazgos de seguridad.** Critical: 0 · Important: 0 · Minor: 0.

Revisión C, primera inspección de U2a1: los tres archivos completos del diff capturado coinciden con las fuentes actuales y sus SHA-256 congelados. El selector automático indicó C=false; root añadió C por privacidad de metadatos y rutas locales.

Las referencias siguientes pertenecen a [contracts.py](../../../../../apps/server/app/worker/contracts.py).

| Criterio | Evidencia fichero:línea | Resultado |
|---|---|---|
| Inyección SQL/comando/plantilla | `contracts.py:96`, `contracts.py:405` | ✓ Serialización y comparación puras; sin sinks de ejecución. |
| Autenticación y sesión | `contracts.py:39` | ✓ No introduce endpoints, credenciales ni gestión de sesiones. |
| Secretos hardcodeados y privacidad | `contracts.py:49`, `contracts.py:114`, `contracts.py:244` | ✓ Sin secretos reales; rechazo recursivo de claves sensibles y extras. |
| Deserialización insegura | `contracts.py:154`, `contracts.py:157` | ✓ JSON y validación Pydantic; sin pickle ni ejecución de objetos. |
| Path traversal | `contracts.py:263`, `contracts.py:405` | ✓ Rechaza rutas absolutas, traversal, separadores Windows y controles Unicode; destinos finales exactos. |
| SSRF | `contracts.py:162` | ✓ Sin llamadas de red ni resolución de URLs. |
| Permisos y autorización | `contracts.py:350`, `contracts.py:375`, `contracts.py:443` | ✓ Coherencia de pertenencia y comparación completa de autoridad para resultados exitosos. La autorización efectiva sigue siendo responsabilidad del padre. |
| Inmutabilidad y valores inválidos | `contracts.py:138`, `contracts.py:334`, `contracts.py:438` | ✓ Descriptor canónico separado, entradas acotadas y medidas finitas. |

**Evidencia revisada:** argv, UTC, JUnit y originales RED/GREEN; RED causales por aceptación indebida, excluyendo BOM, `AttributeError` y reparación de fixture. La corrida vigente `final-official` acredita **74 PASS**, cobertura del módulo completo **268/274 = 97,8102 %**, cero exclusiones; lint oficial exit 0.

Mi ejecución se limitó a lecturas y cotejos de integridad en memoria; no ejecuté tests ni pruebas de explotación. Los tests entregados usan datos sintéticos en Windows: no acreditan custodia filesystem, SQL/CAS, autorización integrada ni cierre de T-05/M1.

### Lente D

**Sin hallazgos.** Critical: 0 · Important: 0 · Minor: 0.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| N+1 | ✓ Sin consultas ni llamadas externas dentro de bucles. | `apps/server/app/worker/contracts.py:350` |
| Bloqueos síncronos | ✓ Validación en memoria; sin `sleep`, E/S ni procesos. | `apps/server/app/worker/contracts.py:148` |
| Trabajo repetido evitable | ✓ SHA de procedencia calculado una vez antes de recorrer las tomas. | `apps/server/app/worker/contracts.py:352` |
| Complejidad con volumen real | ✓ Validación lineal con conjuntos. Validar los 64 resultados implica como máximo 2.080 inspecciones de entradas; no acredita degradación relevante. | `apps/server/app/worker/contracts.py:337`, `:375` |

Activación: selector `lens-selection.json`, modo `auto`, patrón de ruta `worker` en los tres ficheros.

Fuentes actuales coinciden con los tres hashes congelados. Evidencia oficial consultada: 74 PASS; cobertura del módulo completo 268/274 = 97,81 %, cero exclusiones. **Revisión estática y documental**, sin ejecutar tests ni benchmarks. Alcance limitado a U2a1; no acredita rendimiento del worker integrado ni aceptación de T-05.