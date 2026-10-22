# QA2 independiente — M1/T04, primera unidad parcial de esquema

**PASS técnico funcional dentro del alcance de QA2. Aceptación reservada a root.** No se cierra T04, ningún CA, Git ni M1. Continúan abiertos los ocho criterios de T04. Root puede evaluar esta dependencia antes de U1.

QA1 actual se referencia explícitamente: **522 PASS / 3 SKIP Windows / 0 FAIL**, 525 casos, incluidos 174 del esquema y ocho históricos. No se repitió la suite completa. Se revalidaron las diez fuentes y los **715 artefactos** de QA1. Las ejecuciones focales nuevas fueron dos ciclos nativos bajo cobertura y cinco casos Linux (tres symlinks reales y dos ciclos); se reportan por separado y no inflan los 522 casos. Los archivos de test copiados son byte/AST exactos, sin cambios de assertions, bootstrap ni renombrado de skips. La ejecución Linux usa filesystem POSIX privado del contenedor; el source readonly procede del clone exacto.

Cobertura de módulos completos, cero exclusiones, parser oficial custom-agents 1.22.0: tres ejecuciones referenciadas de QA1 y la ejecución focal actual de Alembic; todas tienen paridad de bytes con la misma fuente congelada. No combinación de rutas, líneas históricas cambiadas, promedio ni cobertura del diff inventada.

| Módulo | Cubiertas/total | % | Evidencia |
|---|---:|---:|---|
| apps/server/app/models/__init__.py | 336/338 | 99.41 | .cache\dev-cycle\m1\t04-schema-qa1/coverage-official.json |
| apps/server/app/snapshots.py | 360/385 | 93.51 | .cache\dev-cycle\m1\t04-schema-qa1/coverage-official.json |
| apps/server/app/migrations/job_attempt_invariants.py | 184/196 | 93.88 | .cache\dev-cycle\m1\t04-schema-qa1/coverage-official.json |
| apps/server/app/migrations/versions/0005_job_attempt.py | 18/18 | 100.00 | .cache\dev-cycle\m1\t04-schema-qa2/migration-coverage.json |

`0005` se cargó realmente mediante Alembic. `coverage run` usa el directorio filesystem `app/migrations/versions`; el JSON oficial captura las **18 líneas**, `upgrade`, `downgrade` y el cuerpo del módulo al 100 %. Se conserva la medición QA1 0/18 sin alterarla. Dos ciclos vacío/poblado y ocho comandos CLI sobre la wheel instalada verifican 0004→0005→0004→head, FKs, datos y el DDL golden de 0001–4 `2c233c…15d08`.

Las seis wheels de build oficiales se copiaron con SHA/bytes verificados desde el prerrequisito: Hatchling1.32.4, pathspec1.1.1, trove-classifiers2026.9.21.13, packaging26.3, pluggy1.6.0 y tomlkit0.13.3. La decisión root autoriza el venv privado gestionado y su instalación offline sin dependencias ni índice. Se construyeron wheels reales mediante CLI de Hatchling, no ZIP artesanal. Runtime limpio sin system-site-packages, export frozen del server, exactas versiones/URLs/hashes de uv.lock y dependencias locales instaladas mediante ambas wheels. Las descargas oficiales de runtime verificadas están en runtime-wheel-manifest.json; ninguna actualización ni instalación de Python del host. Ambos paquetes tienen origen wheel, RECORD y ausencia de editable shadow verificados. El cwd nativo es `outside`; app se carga desde runtimevenv/Lib/site-packages, sin PYTHONPATH ni sys.path insert para app. NoTorch real. Se conservan las restricciones de confinamiento existentes: datos debajo del ROOT del paquete instalado; no se cambió ni puenteó ROOT.

Native y Docker tienen código app byte-exacto y las mismas versiones runtime. Sondas independientes: UTCspace creado/actualizado/borrado→SQL→lectura tipada→project→validate→restore_new→entity_song→backup restaurado; se retiene la fila soft-deleted. Caso adicional: padre job soft-deleted con intento, registry y restore_new; un padre físicamente ausente es rechazado por SQL y no crea registry. Fecha imposible/1900-no-leap/hora24 rechazadas; leap2000/2024 legibles en Common y terminal. Terminal sin ts rechazado en SQL/helper/snapshot, terminal con ts estable en dos lecturas/proyección/restauración/backup. Snapshot viejo valida sin job_attempt y roundtrip no inventa identidad. Dos copias del contrato iguales; **21 tablas exportadas / 24 entidades**, medidos realmente. JSON Schema4.26 no registra checker date-time; se verifica la ausencia en ambos runtime y no se certifica RFC3339 estricto externo.

Instrumentación privada real before_cursor_execute, sin transformación del SQL: restore20/200/405 mide **29/29/32 SELECT**, de ellos **2/2/3 FROM job_attempt**. SQL completo en native-probes.json y docker-probes.json; mismas consultas como multiconjunto y conteos iguales. El orden observado var?a por traversal de sets, sin cambiar los traces originales; primera finalizaci?n exigi? orden id?ntico y se corrigi? esa expectativa privada, sin rerun. No inferencia de conteos a partir de fórmulas.

Docker CPU real sobre imagen T02 fijada por digest, instalada con las wheels actuales; overlay QA privado offline, no Dockerfile/Compose del producto. El backend se ejecutó únicamente en el venv privado ya fijado; Docker no necesita backend porque recibe wheels ya construidas. Esto no certifica que el build-system Hatchling no versionado del producto tenga futuros rebuilds reproducibles. Memoria512MiB/CPU0.5/runc, sin DeviceRequests, privileged ni socket Docker. Contenedor sin red sólo para estas sondas CPU; no se presenta como configuración de despliegue M1. Fuente readonly. HTTP real por loopback devuelve health200 y Host ajeno403; wire token real del cliente X-Studio-Engine-Token validado con transporte instrumentado y token sintético. El wire no acredita una llamada a un engine GPU real.

Dos lifespans comprobados cierran recursos, reparan snapshot dañado, mantienen FTS y backup. Docker restart real conserva la canción y head0005 y vuelve a responder HTTP. Se preservan inspect antes/después y StartedAt nuevo, JUnit cinco casos Linux, logs y pruebas de persistencia. Native además arranca un proceso uvicorn propio: PID y creación obtenidos con GetProcessTimes del handle actual, HTTP real, terminate de ese único hijo, wait/join y handles cerrados; esta terminación no se declara shutdown graceful. Los lifespans separados son la evidencia de cierre graceful.

Se eliminaron contenedores e imágenes propios comprobando labels y ausencia terminal. No había contenedores ajenos corriendo; el objeto no controlado real usado fue la imagen T02, inspect idéntico antes/después. No se inventa un test de supervivencia de proceso ajeno ni se detuvo ningún recurso ajeno. Datos y resultados privados retenidos.

Incidentes de sonda preservados: expectativa incorrecta de publicación tras commit SQL directo, corregida invocando reconcile existente; cliente wire alineado con su header real. Preflight inicial exigía un contenedor ajeno vivo inexistente, corregido a imagen no controlada existente. Timeout de readiness Docker al acabar las sondas funcionales: cleanup real y continuación usando resultado/marker persistido, sin repetir sondas terminadas. Import pytest falló antes de colección por shim py.py omitido; copia byte-exacta del shim original completa la closure privada y después pasan5/5. Las salidas iniciales no se borraron. Incidentes históricos fix1 Ruff cache compartida y T03 pnpm se conservan, sin certificar autorización operacional de todo el historial.

Ruff primera llamada --no-cache exit0. Fuentes10 y protegidos66 exactos antes/después; ninguna escritura canónica de código/tests/schema/contracts/locks/docs/ledger/Git. Sin subagentes/goals/GPU/WSL/Ollama/PDH/UI/pnpm/knowledge/sharedcache mutations. Modelo/tokens/EUR/horasIA reales NULL; peso2 estimado por root antesdispatch.

Gate backend focal oficial (7 ejecuciones seleccionadas, no nuevos casos canónicos):
```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 7,
    "failed": 0,
    "flaky": 0,
    "skipped": 0,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}
```

Gate backend QA1 congelado, referenciado y hashes actuales verificados:
```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 522,
    "failed": 0,
    "flaky": 0,
    "skipped": 3,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}
```

Gate global M1 conservado de QA1:
```json
{
  "verdict": "NO-VERDE",
  "reason": "sin resultados: results.json no existe (la ausencia de evidencia es rojo)"
}
```

M1 global sigue incompleto: no evidencia UI/E2E/manual; ninguna aceptación de dispatcher, admisión, cadenas, SSE, retry/recovery, GPU ni calidad de modelo. report.md/receipt.json/argv UTC exit/JUnit/cobertura/copies/checks/inventario privados permiten la evaluación de root. closed-noncli-inventory.json es plano con rutas relativas a esta fase y hashes/bytes; excluye CLI vivo, stderr CLI, metadata CLI, final-original y el propio inventario. Root custodia el CLI al terminar.


## Adjudicación del orquestador

Dependencia técnica de identidad durable aceptada después de verificar diez fuentes e inventario cerrado completo. T04 mantiene ocho criterios abiertos, Git y M1 pendientes. El resumen de QA sobre ausencia de control vivo corresponde al primer preflight; cleanup-complete y el inspect Docker4 prueban posteriormente que el control CPU creado por root sobrevivió. Los originales se conservan; no se atribuye ese control a una aplicación del usuario.
