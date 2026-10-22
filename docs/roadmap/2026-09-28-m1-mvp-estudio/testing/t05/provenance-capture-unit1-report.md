> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Captura ADR-0060: implementación revisable, sin aceptación

Seis módulos y dos tests nuevos implementan selección inmutable, captura durable SQLite write-once y los tres caminos: primer envío, retry/offload y resend confirmado ausente. GPU verifica acuse y Health fresco; CPU no carga y conserva observed_model null real. OTHER conocido, identidad/version/contrato/digest discrepantes y captura/cancelación fallidas impiden submit. Nonmusic conserva pareja null. Resend musical legacy/null denegado, captura previa preservada incluso CPU antes descargada/ahora residente. No se inventan LM/DiT ni semillas efectivas; terminal.meta sigue separado. PublicationIntentRevision liga el SHA capturado real en una prueba SQLite.

## Resultado actual único

final-nontimed01: {'cases': 288, 'passed': 213, 'failures': 75, 'errors': 0, 'skips': 0}; tests nuevos: {'cases': 54, 'passed': 54}. EXIT 1. Once, sin retry ni cambio de fuentes tras el fallo. once whole-file de 11 archivos, ninguna omisión individual/--k/skip/timer weakening. La fuente de verdad es el JUnit/stdout/stderr/command-result actual; final-failures-original.json conserva las 75 trazas originales. Ruff check/format-check 0. Todos los archivos protegidos y todos los tests antiguos bytes/AST/type_comments exactos; currentSources.json compara cada fuente con su archivo pre-baseline.

La regresión NO pasa. Las fixtures musicales antiguas incluyen descriptors sin evidencia weights y digest literal synthetic; la selección estricta actual las rechaza como Invalid immutable engine request. También hay expectativas legacy de may_send/recovery sin captura que deben ser adjudicadas por Root, sin modificar sus assertions aquí. No se declara corregido QA2 ni se atribuye este resultado a un engine real. Reportar fallo una vez: no se reejecuta.

## WHOLE actual oficial, single trace

| Módulo | Líneas+ramas oficial | Excluidas |
|---|---:|---:|
| apps\server\app\queue\admission.py | 84.126984% | 0 |
| apps\server\app\queue\dispatcher.py | 69.731801% | 0 |
| apps\server\app\queue\provenance.py | 96.000000% | 0 |
| apps\server\app\queue\resolver.py | 86.580087% | 0 |
| apps\server\app\queue\retry.py | 77.372263% | 0 |
| apps\server\app\queue\runtime.py | 76.551724% | 0 |

Gate cada seis >=80: False. .coverage-original y coverage-original.json son copias físicas del único trace final actual. No promedio, modified-lines, unión con focal/histórico, exclusión ni extracción de helper para cobertura. provenance.py es el helper puro prescrito por ADR0060. No child propio de engine/worker ejecutado.

## TDD y custodia

red01: assert missing durable provenance en backend.submit tras Dispatcher/Admission/SQLite reales. green01 pasa ese mismo caso; descriptor original sobrevive a posterior mutación de catálogo. red02: retry sin wiring no envía; red03: resend legacy alcanza submit con null. Sus originales archivados antes de ejecutar (fuentes, fixture/tests, runner, argv UTC exit stdout stderr JUnit). Runtime/retry se escribieron inicialmente antes de sus tests específicos; se retiraron restaurando sólo preimágenes OWNED y se reescribieron después del RED. Ideas privadas conservadas; no rescate silencioso. Otros casos que ya pasan no se venden como RED.

Errores no causales preservados: focal01 owner fixture usaba el mismo ID local, corregido a new_id; preflight-collection alias tocó assert de nuestro PHASE, reparado en harness excluyendo fuentes nuevas y todos Assert; focal05 cancelled fixture faltaba telemetry, completada con datos sintéticos declarados. No ImportError/API absence/hasattr cuenta como RED. Copias skills tdd/debug-root-cause leídas; ledger/docs/knowledge excluidos por instrucción explícita Root. Primeras lecturas precedieron copias; CONTINUE First180 excedió el bloque prioritario: no custodia before-first-read ni lectura exacta sólo primary. Historial de comandos read-only iniciales separado UTC/stderr UNKNOWN. Managed interpreter físico capturado antes del primer pytest; stdlib/deps completos y TCB transitivo no congelados: UNKNOWN explícito, no retrospectiva. Private TEMP/TMP/UV/pycache/test/coverage configurados antes de ejecución. Bootstrap sólo relocaliza constantes de rutas selladas antes de importar tests, conserva Assert/decorators/params/functions; original fuente bytes intacta.

## Orden, límites y entrega

U1 metadata CLI exit0 ya existe; su baseline nativa falla y cleanup de todas las trazas no está acreditado. Root release explícito del fallo nativo ausente: fullSQL32/dispatcher_retry original80110/performance/heavy permanecen pendientes. referencias finite801 en su fichero funcional entero no es el original retry80110 y no lleva gate temporal. No GPU/Docker/WSL/Ollama/UI/PDH/network/installs/models/.env/dataset/hostPython. Source SSE/models/contracts/DDL/backends/worker/auth protegidos. Ningún docs/ledger/Git/goal/meter/knowledge ni subagente. No cambios ajenos revertidos.

Entrega código concreto con gates pendientes, no T05 completo ni aplicación/quality/E2E aceptada. Root debe adjudicar las regresiones, completar WHOLE >=80 y ordenar original32/801, después fresh review y QA independiente. Provider model/tokens/EUR/IA horas NULL sin originales. receipt.json, actor-command-accounting.json, currentSources.json, source-parity.json, protected-after.json y noncli-inventory.json permiten revisar alcance y evidencia.
