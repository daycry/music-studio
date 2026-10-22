---
author: qa
model: sonnet
effort: medium
status: pendiente-revision-y-qa-final
date: 2026-10-11
canonical_adopted: false
task_closed: false
---

# Baseline contractual M1 y recetas privadas T02 — T04

Baseline candidato versión 2 de autoría QA. Actualiza la propuesta íntegra original con FIX1 B01/B02 y corrige A01 en los enlaces; los bytes actuales y la evidencia histórica se contrastan por separado. Esta entrega prepara la revisión completa A/B y la QA posterior de T04; no emite aceptación del producto ni cierra el ledger.

## Formas conservadas e inventario

Se congelan PostPlan engine v1, manifiesto v1, snapshot/song v1 y tres requests históricos: seed-only con espacios y salto de línea, null/semilla grande y post input job/source/output_index. Son escenarios contractuales sintéticos derivados de fixtures y contratos existentes; no recibos de ejecución musical. La lectura legacy preserva bytes, hash crudo y presencia de campos sin añadir defaults, kind ni versión. El hash canónico se distingue del crudo.

Las ocho recetas privadas son variation_request, variation_audio, extend, repaint, cover, trim, fade y crossfade. Cada receta tiene un envelope CreativeRequestV1 separado. Los lectores históricos y nuevos conservan sus respectivos contratos: PostPlan permanece de origen engine, mientras las recetas CPU no inventan modelo, semilla ni attempt de ejecución. Los mapas requested_seconds expresan intención, no duración medida.

El [índice de fixtures](../../../../apps/server/tests/fixtures/creative/fixture-index.json) fija longitud y SHA de 22 JSON y excluye su propio archivo. Su [README](../../../../apps/server/tests/fixtures/creative/README.md) declara IDs, modelos, pins, derechos y textos sintéticos. Los hashes internos de assets/pesos son datos de contrato; los hashes del índice sí corresponden a los bytes JSON comprobados. runtime_verified permanece false; un descriptor verified sintético no habilita un modelo real.

## Wire privado y esquema code-first actual

[creative-recipe-v1.schema.json](../../../../packages/contracts/creative-recipe-v1.schema.json) describe CreativeRecipeV1 privado, Draft 2020-12. La versión se transporta mediante CreativeRequestV1 o schema_version de read_recipe; no introduce API pública ni manifiesto v2.

La generación original en [prepare.py](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-implementation-20261011/prepare.py) y el generador actual [prepare-schema.py](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/prepare-schema.py) obtienen model_json_schema(mode=serialization). Así respeta PlainSerializer de FrozenObject y expresa objetos wire, evitando exponer FrozenJSON.root como string. Añade explícitamente ModelDescriptor code-first como descriptor, con cierre recursivo de DTOs conforme a closed_model de T02; no expone FrozenDescriptor.payload como wire ni modifica el DTO histórico. La inspección de fuentes y del esquema corrobora estos pasos; no se ejecutó la generación durante esta producción documental.

JSON Schema comprueba forma, tipos y cierre. El codec sigue siendo autoridad para relaciones, canonicalidad, versión, secretos, capacidades y hashes. El documento no afirma equivalencia total entre el esquema y las reglas semánticas del codec.

| Artefacto fijado | SHA-256 |
|---|---|
| Schema privado | 05ef38f24f178a9294bcdaaf6a8ef122f37b9270ad22972b9c3f4ffd7f9688dc |
| Test T04 | 78921e088d88cf2950a3fedc1f936ddc64bacf11d50c82a54e867fb43f97a931 |
| PostPlan, bytes y hash canónico según índice | d15eb15db03be986d34a4e6b71a8412f1526f8a07ac4825aa01fcbadfc431b76 |
| Exporter real | d75b7da73c6a41b25615230ff717c4e8526e2dd7888addfc6022833413cec422 |

## OpenAPI aislado

La evidencia de [exportación](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-implementation-20261011/export-baseline.stdout) procede de scripts/export_contracts.py real con create_app(ContractSettings), sin iniciar runtime. Dos destinos privados base/repeat se exportaron y pasaron --check. Sus bytes, contrastados ahora, coinciden con el OpenAPI fijado: `f42adb4a03ba35d91010829028d8a8fd8bb98daa86d5f7c3d56ca68656a5f5c5`. No se sobrescribió el contrato canónico desde esta entrega.

[Lint oficial](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-implementation-20261011/openapi-lint.stdout): errores=[], avisos=[], exit 0. [Diff oficial](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-implementation-20261011/openapi-diff.stdout): cambios=[], rompedores=0, exit 0. Son resultados del implementer comprobados contra sus archivos y comandos; aquí no se repiten ni se presentan como QA final independiente.

## Evidencia histórica original — ámbito de los SHA anteriores

La ejecución del implementer usó el entorno gestionado ROOT, uv run --project ROOT --frozen --no-sync --all-packages y Python -X utf8 -B; el PYTHONPATH privado fija app, audio_post y engine_contract. [commands.json](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-implementation-20261011/commands.json) conserva argv, cwd, UTC, exits y reap. [imports.json](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-implementation-20261011/imports.json) fija seis módulos privados y sus SHA, todos contrastados ahora contra los archivos respectivos.

| Registro final del implementer | Casos verificados por JUnit | Fail/error/skip | Exit |
|---|---:|---|---:|
| [Focal T04](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-implementation-20261011/focal.junit.xml) | 48 | 0/0/0 | 0 |
| [Vecinos T02/T03](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-implementation-20261011/neighbors.junit.xml) | 274 (183 + 91 declarados) | 0/0/0 | 0 |
| [Ruff del test](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-implementation-20261011/ruff.stdout) | All checks passed! | n/a | 0 |
| Export + check dos destinos | OpenAPI idénticos | n/a | 0 |
| OpenAPI lint / diff oficiales | sin errores / sin cambios | n/a | 0 / 0 |

Los negativos originales del test cubren versión futura sin fallback legacy, cambios de bytes/hash, campos extra, forma, pins, identidad/song/owner discordantes, mapas y descriptor/params wire incompatibles. El manifiesto se lee con _validate real para forma contractual; no se simula verify_manifest con audio falso. snapshots.validate real comprueba cierre owner/song/job y request seed-only sin abrir SQLite ni crear archivos musicales. La proyección de inferencia es pura y no envía una ejecución.

En la versión 1, QA verificó integridad de 196 payloads originales, 142 fuentes del snapshot propietario y 113 pins readonly del snapshot del implementer, además de las dos fuentes adicionales. Las dos adicionales coinciden también con sus bytes actuales. Estos conteos tienen ámbitos distintos y no se suman como pruebas de producto. Los [checks históricos propios](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-baseline-owner-20261011/evidence-checks.json) conservan los hashes, comandos y resultados revisados.

TDD n/a en esta propuesta: schema/fixtures/prosa son configuración y los tests son regresiones de lectores/codec ya implementados. No se reclama RED de producto. Cobertura whole de runtime cambiado n/a: no cambia runtime ni se inventa porcentaje. [diagnostic-attempt1](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-implementation-20261011/diagnostic-attempt1/commands.json) conserva el rojo previo 45PASS/1FAIL y Ruff F401; la suposición token del test se corrigió a access_token según la prohibición histórica existente, sin cambiar el lector. El wrapper inicial incompleto se resolvió usando --project ROOT, sin instalación ni modificación de locks.

## FIX1 B01/B02: restricciones normativas locales y evidencia actual

El esquema previo `af44d416571d50425c65be3d041676ea1713ced4bed9f4b0a1ac5ae0e7113693` incluía anotaciones que Draft 2020-12 no aplicaba como límites en arrays/números. FIX1 conserva el origen code-first y añade mapping v1 en el generador privado: minLength/maxLength de arrays pasan a minItems/maxItems; gt/ge/lt/le de number/integer pasan a exclusiveMinimum/minimum/exclusiveMaximum/maximum. Los strings y keywords ya efectivos se preservan. El recorrido visita edges del schema, no nombres de properties ni examples; los controles prueban propiedades llamadas gt/minLength, ejemplos opacos e idempotencia.

La [auditoría allnodes](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/schema-allnodes-audit.json) registra 310 nodos, 9 nodos modificados y 11 traducciones, comprobados por QA sobre el JSON guardado. [test_generator.py](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/test_generator.py) y su JUnit verifican mapping, reproducibilidad, restricciones traducidas y fronteras. Seis DTO aislados —CpuSelection, SectionMapIntent, Crossfade, Extend, MasterAssetSnapshot y Fade— comprueban restricciones locales sin depender de hashes o reglas entre campos. Diez mutantes completos se rechazan por schema y codec recalculando el hash exterior. Esto no convierte el schema en autoridad para semántica de negocio, hash, relaciones, secretos o capacidades: esas reglas permanecen en DTO/codec sin cambio de runtime.

| Fuente actual FIX1 | SHA-256 |
|---|---|
| Schema | 05ef38f24f178a9294bcdaaf6a8ef122f37b9270ad22972b9c3f4ffd7f9688dc |
| Test | 78921e088d88cf2950a3fedc1f936ddc64bacf11d50c82a54e867fb43f97a931 |
| Índice, sólo cambia recipe_schema_sha256 | 7b20e03ea12ac5a1874ef817b61c0ecee38810841bef602d4b554a924a57725c |
| README, aclara regeneración FIX1 | 9f4dece6668f86bc4cd0783fe952aa6d7fbfe1c5205fd254478d762f523f85b3 |
| Generador privado | 76f196bcc42630775ae5407bc5337dd3776d0e6d5a83882d6e34913b8fc2609c |

La secuencia causal está conservada: [schema previo](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/schema-before.bin), [test antes de config](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/test-red.bin), [RED JUnit](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/red.junit.xml) y [recibo RED](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/red.receipt.json) documentan 20 casos, 18 fallos `DID NOT RAISE ValidationError` y 2 controles ya efectivos. El recibo RED termina `2026-10-11T16:48:40.758510+00:00`, antes del inicio de [generate](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/generate.receipt.json) `2026-10-11T16:49:21.610827+00:00`; después [GREEN](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/green.junit.xml) registra 20 PASS. Es regresión causal RED → configuración mínima → GREEN; TDD n/a para runtime inexistente, sin atribuir RED de producto a un error de auditor.

| Ejecución del implementer FIX1, contrastada ahora | PASS | Fail/error/skip | Exit |
|---|---:|---|---:|
| [Focal actual](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/focal-final.junit.xml) | 69 | 0/0/0 | 0 |
| [Vecinos T02/T03](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/neighbors.junit.xml) | 274 | 0/0/0 | 0 |
| [Generador privado](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/generator-tests-final.junit.xml) | 3 | 0/0/0 | 0 |
| [Nuevas regresiones pareadas](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/green.junit.xml) | 20 | 0/0/0 | 0 |
| [Regeneración --check](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/reproduce.receipt.json) | byteexacta | n/a | 0 |
| [Ruff final](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/ruff-all-final.receipt.json) / [formato final](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/format-all-check-final.receipt.json) | checks limpios / 6 archivos | n/a | 0/0 |

No se suman los 20 casos, ya contenidos en la focal, ni los ámbitos separados como aceptación global. La primera focal FIX1 [diagnóstica](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-fix1-20261011/focal.junit.xml) conserva 68 PASS/1 FAIL por TypeError del auditor al visitar properties; se corrigió el recorrido a edges. Ese diagnóstico no es fallo causal del producto. Se conservan los avisos pytest por anyio previamente importado y cache_dir desconocido al desactivar cacheprovider; sin skips ni errores finales.

QA autenticó 238 payloads FIX1, los 196 originales y los 7 del baseline QA anterior, y contrastó JUnit, recibos argv/cwd/UTC/exits/reap e imports privados actuales. Los 140 pins iniciales de este snapshot incluyen el documento propio; tras editarlo permanecen intactos los 139 no propios. Los 22 JSON de entrada siguen byteexactos; el índice se actualiza únicamente para fijar el nuevo schema. Los [checks actuales QA](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-baseline-owner2-20261011/evidence-checks.json) registran estos ámbitos y fuentes. Los 48 focales/274 vecinos de la tabla histórica corresponden a SHA anteriores; no se atribuyen al test/schema FIX1.

## Enlaces A01 y disponibilidad de la evidencia

Todos los enlaces se calculan desde el destino canónico `docs/roadmap/2026-10-10-m2-iteracion-creativa/testing/contract-baseline.md` respecto a la raíz del repositorio. La evidencia real permanece local en `.cache/dev-cycle/m2/`, ignorada por Git: los enlaces no prometen assets disponibles en GitHub. Para inspeccionar este snapshot privado, el chequeo resuelve cada enlace contra ese destino canónico; cuando el archivo del producto todavía no está adoptado, valida su ruta equivalente en este snapshot y declara ese fallback en el recibo de enlaces. No se crean copias ficticias ni se reutilizan ancestros del snapshot como si fueran el destino final.

## Propiedad, revisión y límites

El guardrail [denegó al implementer](../../../../.cache/dev-cycle/m2/creative-contract-harness-t04-implementation-20261011/guardrail-deny.json) escribir testing/contract-baseline.md. Ese original sigue ausente. QA, propietaria autorizada, produjo este documento sólo en el nuevo snapshot delegado; no reintentó la acción denegada por otra vía. El recibo ROOT y los guards before/after delimitan esta autoría separada. La constitución exige contratos code-first, estado exclusivo en tasks.md y honestidad sobre capacidades: por eso este baseline privado no cambia endpoints, estados ni habilita modelos.

Esta evidencia acredita regresión contractual CPU sintética. No acredita custodia real, storage durable, audio medido/escucha, pesos verificados, modelo instalado, jobs/takes/assets publicados, E2E-12/M-08 ni aceptación humana de M1/M2. La referencia Git de T03 corresponde a un componente y no demuestra por sí sola un árbol CI autónomo.

Pendientes: revisión adversarial fresca 2 completa A/B, QA final independiente de T04 y decisión del orquestador sobre adopción/cierre. No se ejecuta qa-gate ni se da verde global en esta producción documental. No hubo modificaciones de ledger, Git, runtime, locks, servicios, BD, producción, GPU, Ollama, administración ni instalaciones. Tokens/euros/horas IA reales null; las marcas UTC miden reloj de evidencia.
