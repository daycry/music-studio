# Lente A3: traspaso ROOT de respuesta completa

ROOT normaliza la respuesta del actor review_m2_t05_contract_a3; no es una transcripción literal. Diff privado3docs/base56698d80586be971263028fc0d756d3399c6e9d1; fuente a608b81f,97459B461líneas. C=creative-persistence-contract.md; T=tasks.md; K=Constitución; D=datos; I=iteracion-creativa, en snapshot.

| Criterio | Resultado | Evidencia actual A3 |
|---|---|---|
| A1 cierres | ✓ documental | T200,214–222/C23,461 tarea abierta |
| A2 alcance | ✓ | T207/scope3fuera0avisos0info0 |
| A3 tests requeridos | ✓ documental | C346–377/T210 verificación conservada |
| A3 cobertura real | no verificable | C461, runtime pendiente |
| A4 excepción SQL | ✓ | K39/ADR74:31–43/C100,188,289,295 sólo3rebuild |
| A4 canción/padres/maestro | ✓ | K18–19/C54,98,223,319 hija/DAG/maestro |
| A4 server local/engine v1 | ✓ | K31–35/C73,96,166,307 |
| A5 Verificación ejecutada | no verificable | T210,216 abierta |
| A6 interop/OpenAPI | ✓ n/a actual | Markdown; C305,435 futura regeneración |
| A6 documentos afectados | ✓ | D441–457/I168–180 extracción y prefijos exactos |
| A7 guía prosa | ✓ | C287 párrafo conservado, primera frase21palabras |
| T05 biblioteca/backup | ✓ documental | C277–295,364–369 WAL/restore/rollback/pin pendientes |
| T05 inferencia obligatoria | ✓ | C188–191,211,350 seed0/required |
| T05 reserva CPU | ✓ | C98–110,116–120 reserva/batch propio/sinPUBfalso |
| Discriminación NULL | ✓ | C100,188–191,211,223 batch noNULL/CHECKUNKNOWNcerrado |
| CpuExecution aditivo/dispatch | ✓ | C73,108,191,269,289 |
| Plan/receipt/package | ✓ | C75–164,269 refs finales despuésraw/receipt/cierre |
| Derechos/herramientas | ✓ | C96,154,166,223,321 pins/AND |
| UNKNOWN | ✓ | C170,178,235,327 bloquea efectos/serving/cleanup/retry |
| Ciclos FK | ✓ documental | C108–110,176,207,217–219,353 sin triggercommit |
| CAS/unicidad/retry | ✓ documental | C174–182,209,213,355–357 CASconjunto/historia/lostACK |
| SQL directo/límitesSHA | ✓ documental | C67–69,211,215,221,350–362 criptografía separada |
| Replay0006 | ✓ documental | C277–279,363 legacy congelado/0001–0007 intactas |
| Upgrade exclusivo/backup | ✓ documental | C281–293 FKOFFantesBEGIN/ONantesruntime |
| Downgrade previo efectos | ✓ | C295,369 CPUno representable bloquea |
| Songv1 bytes/digests | ✓ documental | C311,317,372 registry frozen/defaults omitidos/batchM1 |
| Songv2 closure | ✓ documental | C313–323,372–373 inversas/todosordinals/sinPUB |
| Import sin custodia viva | ✓ | C325–327,374 historia no reactiva/UNKNOWN |
| Cuatro operacionesAPIv2 | ✓ documental | C299–305,370 codefirst/batch/editorial |
| M1 409/listado entero | ✓ | C307,371 authorizebeforeorigin/409beforewrites |
| Preview sin filas ficticias | ✓ documental | C227–237,375 codec/cierre/decoder pendientes |
| Gates T07 | ✓ | C55,117,166,269,377,437,461 no autoridad porcodec |

0Critical/Important/Minor NUEVOS documentales. Gaps anteriores: A01=B01Important corregido2/conservado3(C98,106–120,158,172,215 sourceSHArealNOTNULLdesdebirth); A02Minor corregido2/conservado3(C287primerafrase21palabras/párrafobyteexact); B02Important corregido3(C100,178,182,188,223,301,313,323,352,356 batchreservaULIDrealnoNULLsinFK/Batch/padre).

Retry: C178 cambia juntosTake.cpu_execution_id/cpu_plan_sha256/batch_id medianteCASantesReady; C182 conserva refs/historia. ASTCreativeRecipe/Request/ParentSnapshot no contiene batchactivo a reescribir. durable_ready_takelegacy(cpu_publication_invariants.py746) se activa porintencióncommitted; no prohibición histórica incondicional de batchantesReady. Planexecutionimmutable648–674. C176–182/319 separan reservaactiva/grupoporordinal; ready/softdeletedready sinrebinding. TestsSQL/ORMC356–360 siguen pendientes.

Actor ejecutó auditoresSTDINstdlib managedPython-B trasenv, exit0:120/120pinsreadonly/sourceexacta;108998B519líneasdiff3docs entero/461contrato/appendicesexact/prefijosraw. ASTDDL Mapped[str]/String26/DDL0001:106NOTNULL/check141/index670/noFKbatch/noBatch, sourceNOTNULL0006. knowledge-findADR/dbcontext sinaciertos/ADR74leídodirecto. C/Dfalse/docsonly; tierfrontmatter. Sin escrituras/SQL/ORM/appimports/native/DB/fixtures/GPU/DockerWSL/services/Git/install/QAproducto. Todos32criterios preservados. DONE/cese. B3 y QA pendientes; ROOT no acepta aún contrato/T05.


## Lente B3: traspaso ROOT normalizado

| CriterioB | Resultado | Evidencia |
|---|---|---|
| Reserva antes render | ✓ documental/B02corregido | C100,106,110,116 ULIDreserva/noPUBfalso |
| Tipos/dominosSHA | ✓ documental conservado | C63–69,148–164 batchderivado/noautorref |
| Refs/ciclos/historia | ✓ documental | C108–110,178–182,198–215 grupoordinalpropio |
| NULL/unicidad/CAS/ownership | ✓ documental/B02corregido | C172–182,188–223 CASexecution/hash/batch;readyimmutable |
| Fuente/tools/rights/UNKNOWN | ✓ documental conservado | C148–170,223 noautoridadporbatch |
| M1/replay0006 | ✓ documental conservado | C275–277,363–364 ASTinstalldinámico/Base.metadata;freeze pendiente |
| Upgrade/backup/FK/rollback | ✓ documental conservado | C279–297 FKOFFbeforeBEGIN/ONbeforeRuntime |
| APIv2/409M1 | ✓ documental | C299–307,370–371 batchactivo/provenance;M1beforeeffects |
| Songv1v2/import | ✓ documental | C311–327,372–374 todosordinals/historia/batchM1exact |
| Preview/hashcycles | ✓ documental conservado | C225–239 preview sinTake/Batch/asset-job |
| RuntimeSQL/ORM/API/render | no verificable | C377,461 prosa antesRED |

GapsA01=B01Important:corregido2/conservado3(C106–120,174,215). A02Minor:corregido2/conservado3, fueraB(C289inventarioFIX1→FIX2unchanged;A287frase21palabras). B02Important:corregido3(C100,178,188,223,301,313,323 ownULID/CAS3punteros/historiaordinal). CERO gaps documentales nuevos/pendientes; ninguna deuda/rebate. Bactor DONE/cese, tabla11 completa. Actor managedPython-Bstdinstdlibexit0:120pins/candidato97459B461l/a608b81f/priorSHA/source.diff exact/appendicesexact/ASTbatchy0006. Diffentero porbloques; knowledge-find sinaciertos/personasbackenddb. No writes/SQL/ORM/importproducto/DB/native/GPU/DockerWSL/services/install/QAproducto.

## Fusión ROOT

32criteriosA+11B completos conservados, estados3gaps previos sin omitir. A/BsinCriticalImportantMinor documentales; scope3/fuera0avisos0/CfalseDfalse. QA documental independiente pendiente. Prosa no demuestra código/schema/cobertura ni runtime T07. T05/M2 abiertos, no gateproducto por prosa; O1/ADR0074ratificados siguen fundamento. Tablas originales completas de revisión2 preservadas en prior-review.md.
