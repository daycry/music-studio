# QA independiente actual — M2/T05 legacy 2A

**DONE en el alcance CPU de congelación legado. T05 completo sigue NO-VERDE / en-progreso.**

Windows: 702 PASS + 1 SKIP; Linux: 703 PASS. Cada plataforma ejecutó los mismos 703 node IDs con el test final `5f9f0951…`; los 23 casos focales actuales pasan en ambas. Symlink omitido en Windows y probado realmente en Linux. Cero fallos/errores actuales.

Fuentes: seis candidatas (cinco runtime, un test), 217 pins antes/después/final. Imports exclusivos del snapshot: Windows 63; Linux 63. Versiones 0001–0007, literal DDL 0006 y modelo base son byte exactos frente a las copias físicas readonly de actor y revisión; los blobs Git de base privada `28b818d` coinciden normalizando únicamente CRLF/LF; codec adoptado conserva su pin. Todos los artefactos se producen en este namespace; no cambios a código, ledger, Git canónico, biblioteca personal ni servicios.

## Cobertura oficial por módulo

coverage.py branch=True, source=filesystem, config_file=False; omit=[], exclude_lines=[], partial_branches=[]. Ninguna línea excluida. Cada módulo completo cumple ≥80 % en líneas, ramas y porcentaje combinado en Windows, Linux y combinación oficial.

| Módulo | Windows líneas/ramas/total | Linux líneas/ramas/total | Combinada líneas/ramas/total |
|---|---:|---:|---:|
| fix2_invariants.py | 98.7013% / 98.0000% / 98.4252% | 98.7013% / 98.0000% / 98.4252% | 98.7013% / 98.0000% / 98.4252% |
| cpu_publication_invariants.py | 92.0530% / 85.2564% / 89.7380% | 92.0530% / 85.2564% / 89.7380% | 92.0530% / 85.2564% / 89.7380% |
| snapshots.py | 93.6430% / 87.8151% / 91.4992% | 93.8875% / 88.2353% / 91.8083% | 93.8875% / 88.2353% / 91.8083% |
| legacy_m1_registry.py | 100.0000% / 100.0000% / 100.0000% | 100.0000% / 100.0000% / 100.0000% | 100.0000% / 100.0000% / 100.0000% |
| fix1_invariants.py | 100.0000% / 100.0000% / 100.0000% | 100.0000% / 100.0000% / 100.0000% | 100.0000% / 100.0000% / 100.0000% |

El helper `custom-agents:unit-tests` midió 95,93 % de media del diff, sólo diagnóstico. Se ejecutó sobre Git privado con base exacta y seis cambios; su runner volvió a generar el informe mediante coverage.py desde `.coverage` actual, sin stdout inventado ni sustitución del umbral individual. Cobertura global de toda app: 44,32 %, no gate de todo el backend.

## SQLite real y custodia

La auditoría propia retiene dos SQLite de fixtures M1 pobladas, heads 0006/0007, bajo snapshot/.cache/audit-retained. Para cada head conserva schema SQL (586 entradas), tablas (39), filas (41), columnas, IDs y valores, proyección v1 y digests. Reinstalación con metadata futura inyectada antes de reload de todos los consumidores compara exactamente los efectos reales baseline (incluida invalidación) y revierte las transacciones. 27 tablas / 356 columnas tipadas iguales al modelo base; codecs Seed/ContractJSON/WorkerJSON métodos AST iguales. Casos SQL enormes/NULL/negativos, alias, consultas de autoridad, auxiliares históricos y batches se ejecutan en la suite real.

Evidencias: audit/registry-typed-shape.json; audit/codecs-ast.json; audit/0006-preimage.json; audit/0007-preimage.json; audit/audit-receipt.json; windows y linux2 results.xml/.coverage/coverage.json/argv.json/imports.json/before-pins.json/after-pins.json; combined/.coverage/coverage.json.

## Incidentes de arnés preservados

Linux inicial: 3 FAIL / 374 PASS / 326 ERROR. Causa: fixture histórico exige escritura en rutas fijas bajo snapshot/.cache, pero el bind RW inicial sólo cubría snapshot/.cache/linux. Se conserva JUnit, coverage y consola de ese intento. Linux2 repite los 703 casos completos con única caché de snapshot RW y fuentes RO; imagen CPU preexistente, --rm, --network none, workingdir /studio. No bypass del confine_path ni modificación de fixtures/fuentes. Primer diagnóstico helper falla por quoting Windows/shlex FileNotFoundError; segundo usa argv estructurado y rutas slash, exit0, ambas evidencias conservadas.

El cierre tuvo dos preflight fallidos por comparar representaciones Git (blob LF / checkout autocrlf) con snapshots físicos. No falló ninguna prueba del producto ni se editó fuente alguna. `git-checkout-representation.json` registra hashes, tamaños y CRLF por archivo, igualdad exacta entre releases físicos e igualdad del blob sólo tras normalización EOL.

Un tercer preflight de inventario recibió `ValueError: not a symbolic link` al consultar desde Windows el reparse creado por el caso Linux de symlink. El inventario final lo registra explícitamente, sin seguirlo y con target_unreadable; no lo elimina ni oculta archivos regulares.

## Puertas y pendientes

ledger-lint: 0 incoherencias duras, 29 avisos históricos; coverage-check: 0 referencias rotas y 0 huérfanos GWT/UI. Ruff check: All checks passed!; format --check: 6 files already formatted. Salidas completas en harness/. No qa-gate E2E de Playwright ni PDF/UI en este alcance CPU; `cpu-strict-gate.json` es explícitamente un gate CPU independiente.

- [ ] M-08 / biblioteca personal M1 real antes-después, backup/WAL/restauración de producción.
- [ ] SQL v2 / ORM v2 integrados, API/Song v2, import y publicación nuevos.
- [ ] PORT-01 completo: nueva head, cierres mixtos/crossfade, historial y linaje de producción.
- [ ] CA-16/CA-17/CA-29 completos y Verificación full T05, UI y manuales del hito.
- [ ] Integración CAS de las seis fuentes únicamente por ROOT tras auditar recibos/payloads.

Las cinco filas “no verificable” de A y el alcance no verificable B se conservan íntegros abajo. Performance D es comparación local in-memory / conteos de consultas (25/33), no validación de IO de producción. Nada cierra T05/M2 ni dispara documentación. Horas/tokens/euros reales null; elapsed es reloj del proceso.

## Gate CPU estricto (JSON completo)

```json
{
  "scope": "M2/T05 legacy 2A CPU only",
  "verdict": "DONE scoped CPU; full T05 NO-VERDE/pending",
  "exit": 0,
  "junit": {
    "windows": {
      "junit": {
        "failures": 0,
        "errors": 0,
        "skipped": 1,
        "tests": 703,
        "passed": 702
      },
      "focal": 23,
      "symlink": "skipped",
      "run": {
        "start": "2026-10-12T09:04:27.709359+00:00",
        "end": "2026-10-12T09:09:15.876597+00:00",
        "pytest_exit": 0,
        "pins": 217,
        "imports": 63
      }
    },
    "linux2": {
      "junit": {
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "tests": 703,
        "passed": 703
      },
      "focal": 23,
      "symlink": "passed",
      "run": {
        "start": "2026-10-12T09:06:11.102981+00:00",
        "end": "2026-10-12T09:20:09.939050+00:00",
        "pytest_exit": 0,
        "pins": 217,
        "imports": 63
      }
    }
  },
  "whole_file_coverage": {
    "windows": {
      "apps/server/app/migrations/fix2_invariants.py": {
        "lines": 98.7012987012987,
        "branches": 98.0,
        "combined": 98.4251968503937,
        "statements": 77,
        "covered_lines": 76,
        "num_branches": 50,
        "covered_branches": 49,
        "excluded_lines": 0,
        "official_source_path": "apps\\server\\app\\migrations\\fix2_invariants.py",
        "sha256": "d1806d374c75003b49f57019a51721ab955e37873d1b4b57c5bf98793265e2af"
      },
      "apps/server/app/migrations/cpu_publication_invariants.py": {
        "lines": 92.05298013245033,
        "branches": 85.25641025641026,
        "combined": 89.73799126637554,
        "statements": 302,
        "covered_lines": 278,
        "num_branches": 156,
        "covered_branches": 133,
        "excluded_lines": 0,
        "official_source_path": "apps\\server\\app\\migrations\\cpu_publication_invariants.py",
        "sha256": "331b9aa2ee1abb4b4f20f3102df47e72e27f1ca6342488be4558766675884f6a"
      },
      "apps/server/app/snapshots.py": {
        "lines": 93.64303178484107,
        "branches": 87.81512605042016,
        "combined": 91.49922720247295,
        "statements": 409,
        "covered_lines": 383,
        "num_branches": 238,
        "covered_branches": 209,
        "excluded_lines": 0,
        "official_source_path": "apps\\server\\app\\snapshots.py",
        "sha256": "0de4f2fa3eaf8fcd42ee448200e40d07c5ba8875c8397e5acbb99c426598be99"
      },
      "apps/server/app/migrations/legacy_m1_registry.py": {
        "lines": 100.0,
        "branches": 100.0,
        "combined": 100.0,
        "statements": 41,
        "covered_lines": 41,
        "num_branches": 8,
        "covered_branches": 8,
        "excluded_lines": 0,
        "official_source_path": "apps\\server\\app\\migrations\\legacy_m1_registry.py",
        "sha256": "2b73ae668bdc4a99d73dcf30c5fc01c89d06dc3d86e89bdd2621712b605c7da0"
      },
      "apps/server/app/migrations/fix1_invariants.py": {
        "lines": 100.0,
        "branches": 100.0,
        "combined": 100.0,
        "statements": 76,
        "covered_lines": 76,
        "num_branches": 38,
        "covered_branches": 38,
        "excluded_lines": 0,
        "official_source_path": "apps\\server\\app\\migrations\\fix1_invariants.py",
        "sha256": "0fd52fec3c108e72626a39f593d963d4a38555ea7fc5196528919e5fee9348ae"
      }
    },
    "linux2": {
      "apps/server/app/migrations/fix2_invariants.py": {
        "lines": 98.7012987012987,
        "branches": 98.0,
        "combined": 98.4251968503937,
        "statements": 77,
        "covered_lines": 76,
        "num_branches": 50,
        "covered_branches": 49,
        "excluded_lines": 0,
        "official_source_path": "apps/server/app/migrations/fix2_invariants.py",
        "sha256": "d1806d374c75003b49f57019a51721ab955e37873d1b4b57c5bf98793265e2af"
      },
      "apps/server/app/migrations/cpu_publication_invariants.py": {
        "lines": 92.05298013245033,
        "branches": 85.25641025641026,
        "combined": 89.73799126637554,
        "statements": 302,
        "covered_lines": 278,
        "num_branches": 156,
        "covered_branches": 133,
        "excluded_lines": 0,
        "official_source_path": "apps/server/app/migrations/cpu_publication_invariants.py",
        "sha256": "331b9aa2ee1abb4b4f20f3102df47e72e27f1ca6342488be4558766675884f6a"
      },
      "apps/server/app/snapshots.py": {
        "lines": 93.8875305623472,
        "branches": 88.23529411764706,
        "combined": 91.80834621329211,
        "statements": 409,
        "covered_lines": 384,
        "num_branches": 238,
        "covered_branches": 210,
        "excluded_lines": 0,
        "official_source_path": "apps/server/app/snapshots.py",
        "sha256": "0de4f2fa3eaf8fcd42ee448200e40d07c5ba8875c8397e5acbb99c426598be99"
      },
      "apps/server/app/migrations/legacy_m1_registry.py": {
        "lines": 100.0,
        "branches": 100.0,
        "combined": 100.0,
        "statements": 41,
        "covered_lines": 41,
        "num_branches": 8,
        "covered_branches": 8,
        "excluded_lines": 0,
        "official_source_path": "apps/server/app/migrations/legacy_m1_registry.py",
        "sha256": "2b73ae668bdc4a99d73dcf30c5fc01c89d06dc3d86e89bdd2621712b605c7da0"
      },
      "apps/server/app/migrations/fix1_invariants.py": {
        "lines": 100.0,
        "branches": 100.0,
        "combined": 100.0,
        "statements": 76,
        "covered_lines": 76,
        "num_branches": 38,
        "covered_branches": 38,
        "excluded_lines": 0,
        "official_source_path": "apps/server/app/migrations/fix1_invariants.py",
        "sha256": "0fd52fec3c108e72626a39f593d963d4a38555ea7fc5196528919e5fee9348ae"
      }
    },
    "combined": {
      "apps/server/app/migrations/fix2_invariants.py": {
        "lines": 98.7012987012987,
        "branches": 98.0,
        "combined": 98.4251968503937,
        "statements": 77,
        "covered_lines": 76,
        "num_branches": 50,
        "covered_branches": 49,
        "excluded_lines": 0,
        "official_source_path": ".cache\\dev-cycle\\m2\\creative-persistence-t05-legacy-freeze-current-qa1-20261012\\snapshot\\apps\\server\\app\\migrations\\fix2_invariants.py",
        "sha256": "d1806d374c75003b49f57019a51721ab955e37873d1b4b57c5bf98793265e2af"
      },
      "apps/server/app/migrations/cpu_publication_invariants.py": {
        "lines": 92.05298013245033,
        "branches": 85.25641025641026,
        "combined": 89.73799126637554,
        "statements": 302,
        "covered_lines": 278,
        "num_branches": 156,
        "covered_branches": 133,
        "excluded_lines": 0,
        "official_source_path": ".cache\\dev-cycle\\m2\\creative-persistence-t05-legacy-freeze-current-qa1-20261012\\snapshot\\apps\\server\\app\\migrations\\cpu_publication_invariants.py",
        "sha256": "331b9aa2ee1abb4b4f20f3102df47e72e27f1ca6342488be4558766675884f6a"
      },
      "apps/server/app/snapshots.py": {
        "lines": 93.8875305623472,
        "branches": 88.23529411764706,
        "combined": 91.80834621329211,
        "statements": 409,
        "covered_lines": 384,
        "num_branches": 238,
        "covered_branches": 210,
        "excluded_lines": 0,
        "official_source_path": ".cache\\dev-cycle\\m2\\creative-persistence-t05-legacy-freeze-current-qa1-20261012\\snapshot\\apps\\server\\app\\snapshots.py",
        "sha256": "0de4f2fa3eaf8fcd42ee448200e40d07c5ba8875c8397e5acbb99c426598be99"
      },
      "apps/server/app/migrations/legacy_m1_registry.py": {
        "lines": 100.0,
        "branches": 100.0,
        "combined": 100.0,
        "statements": 41,
        "covered_lines": 41,
        "num_branches": 8,
        "covered_branches": 8,
        "excluded_lines": 0,
        "official_source_path": ".cache\\dev-cycle\\m2\\creative-persistence-t05-legacy-freeze-current-qa1-20261012\\snapshot\\apps\\server\\app\\migrations\\legacy_m1_registry.py",
        "sha256": "2b73ae668bdc4a99d73dcf30c5fc01c89d06dc3d86e89bdd2621712b605c7da0"
      },
      "apps/server/app/migrations/fix1_invariants.py": {
        "lines": 100.0,
        "branches": 100.0,
        "combined": 100.0,
        "statements": 76,
        "covered_lines": 76,
        "num_branches": 38,
        "covered_branches": 38,
        "excluded_lines": 0,
        "official_source_path": ".cache\\dev-cycle\\m2\\creative-persistence-t05-legacy-freeze-current-qa1-20261012\\snapshot\\apps\\server\\app\\migrations\\fix1_invariants.py",
        "sha256": "0fd52fec3c108e72626a39f593d963d4a38555ea7fc5196528919e5fee9348ae"
      }
    }
  },
  "readonly_historical_baseline_exact": {
    "apps/server/app/migrations/versions/0006_cpu_publication.py": "e67fa61a46619fb075a8667fbde05f8461b4078b414fa5412d8f4cbeb3017c4e",
    "apps/server/app/migrations/versions/0004_snapshot_promotion.py": "b50439cc88ac5b6e17ac4d8b87d15af5acf9675136f588422061e01a51d335ae",
    "apps/server/app/migrations/versions/__init__.py": "321bbcdfa7b590f46141a0963ee2e2001ee2f58bcdc51ec587b943c304cc91e1",
    "apps/server/app/migrations/versions/0001_initial.py": "762e019de05c245e08172814fba3138e5fb8311b5c987f6ffc715bef50f5eac5",
    "apps/server/app/models/__init__.py": "9c86ef171968e799908068c1f98ce47186b9e2ed3337c019a7e9696d38dac0df",
    "apps/server/app/creative/durable_contracts.py": "50e1c0ac8db635fc41eed3acdbac36c0ec3430fdb7cccd57815d35db9c1431f6",
    "apps/server/tests/test_creative_persistence.py": "de3a3c20b315d25ef6b03f3ff388d6444090a60af529fc874e012f2431a96728",
    "apps/server/app/migrations/versions/0002_snapshot_metadata.py": "ad9358218a3c863f8b5a1343cda226f530f4467eb446194220f130776b2fbf02",
    "apps/server/app/migrations/versions/0007_job_attempt_json_guard.py": "c01ef3349af18d730ce5f05c0dcbc849e2cf13da741a5d9cad4add93b493183f",
    "apps/server/app/migrations/versions/0005_job_attempt.py": "18c1c33471f900e5669d5fdfe81990580f83e6ebda10c55f53ea9ad4fc7a611b",
    "apps/server/app/migrations/versions/0003_snapshot_guards.py": "35648983fd5fee7412678ddba9abdc781e0143cf239a8e30ed82ca535c0b7ecc",
    "apps/server/app/migrations/versions/0001_schema.sql": "9fe867481051286ff592e9b668deae8d65cf88f475d6e7faf9a7cdf8d53a3998"
  },
  "217_pins_before_after_final": true,
  "current_test_sha256": "5f9f095188520d70703d9bed3e4ac777f39d83be756f2964ec6f23e6745bfd08",
  "reviews_preserved": {
    "A": 43,
    "B": 14,
    "D": 6
  },
  "no_ui_e2e_qa_gate_claim": true,
  "no_GPU_audio_models_download_services": true,
  "actual_usage": {
    "hours": null,
    "tokens": null,
    "euros": null
  },
  "utc": "2026-10-12T09:25:04.374358+00:00"
}
```

## Revisión previa íntegra 43A / 14B / 6D (proveniencia: ROOT, no revisión fresca de QA)

# M2/T05 congelación del legado — revisión1 A/B/D sin gaps

ROOTnormaliza43A/14B/6D completos; ninguna aprobación integra fullT05. Cauto false,Dauto true por4routesmigrations; scope6/0fuera/0avisos. A1propio23PASS/217pins/44imports/27tables356colscomparadas, B1propio23+43PASS/217pins44/48imports/ASTcodecs/DDLs/headsfixturepopulated; D1memoriaSQLsolo loadprobesmedidosnoproducción. 0Critical0Important0Minor actuales. QAactualfinaltestSHA pendiente.

# M2/T05 legado2A — LenteA1 completa, B/D pendientes

ROOT normaliza43A íntegros del reviewer freshA1. No gapsAactuales;Brobustez yDperformance todavía vivos. NoQA/CAS/closurefullT05.

| CriterioA | Resultado | Evidencia |
|---|---|---|
| diff complet | ✓ | 6sources5runtime1test4blocks |
| ownership/scope | ✓ | tasks207/1514/1519/1522 scope6/0/0 |
| scopehistoric | ✓ | scope-before-ROOT-declaration.json noexclusions |
| MIG01 head0006 | ✓ | test78[0006] |
| MIG01 head0007 | ✓ | test78[0007] |
| futurebeforeload | ✓ | test21/48 newtablecolumnbeforeallreloads |
| staticregistry | ✓ | registry86 27literals noappmodels/reflection |
| columnsorder | ✓ | 27tables356cols0diffM1sealed |
| typesJSONnull | ✓ | SQLSQLite/nonasnull/models/nullability0diff |
| PKdefaultsFK | ✓ | 0diff/test96 DDLactual |
| Seedlegacy | ✓ | registry27/test234/249 SQLreal |
| ContractJSONWorkerJSON | ✓ | registry46/65 None/modelserializelegacy |
| legacyinstallsignature | ✓ | cpu493/668 fixedcolumnsourceonly |
| fullhistoricalguards | ✓ | SQLtriggersactualbodyunchanged |
| fix1fix2helpers | ✓ | fix1 23/78 fix2 39/56 test128 |
| authorityqueries | ✓ | cpu258/270/275 test2664futuretables |
| immutable0001..7 | ✓ | 217pins0diff historicalrevisions |
| acceptedcodecimmutable | ✓ | 50e1de3apinsstable |
| PORT01v1projection | ✓parcial | snap24/28 test145 SELECTreal |
| globalexclusions | ✓ | setting/provider/presetexact |
| populateddigests | ✓parcial | test195heads6/7 docdigestsafterrollback |
| reinstallrealeffects | ✓ | test195 schemascolumnsrowsvalues/invalidationbaseline |
| uninstallrollback | ✓ | test195 bothtransactionsreverted |
| TDDreplay | ✓ | REDfuturetrigger2fails04:29:43.825703Z |
| TDDprojection | ✓ | REDnoColumnSong.future_m2 04:29:50.727963Z |
| TDDhelpers | ✓ | RED4actualtriggerfuturecolumn |
| TDDauthorityqueries | ✓ | restoredoriginalselects RED4OperationalError04:43:12.193444Z before rewrite |
| REDincidentsseparate | ✓ | indent/type/assertpreliminarynotcredited |
| currentfocaltests | ✓ | 23PASSown5.78s |
| wholecoverage5 | ✓apoyo | cpu92.053/85.256/89.738;fix1 100;fix2 98.701/98/98.425;registry100;snap93.643/87.815/91.499 |
| noomitexclude | ✓ | sourcefilesystem/configfalse/excluded0 |
| suitefocalidentity | ✓ | 699cases698PASS1SKIP then23focal4testsaddedlater |
| constitutionbaseline | ✓ | C42 historicpinsimmutable |
| constitutionsongtake | ✓ | C21/22 noedit/publication |
| constitutionserverpaths | ✓ | C34/46 privateSQLite44imports |
| constitutionledgerclosure | ✓ | C72 taskopennoQAclaim |
| interopOpenAPI | n/a | nochangegeneratedschema/docs |
| knowledge | ✓ | ADR/db0hits directcontractread |
| T05personallibrarybackup | no verificable | personalWALbackuprestore realpending |
| T05CPUauthoritySQLv2 | no verificable | schemaORMv2 integratedpending |
| PORT01fullv2 | no verificable | newhead/mixed/crossfadehistorypending |
| CA16CA17CA29full | no verificable | spec171/172/184 operations/lineage/publicationfullpending |
| fullVerificationQA | no verificable | T05open QAactualtestSHA after4casespending |

EjecutadoA1: managedenv/.venv -B focalactual23PASS5.78s/217pinsbeforeafter/44imports privados;27M1tables356columns exacttypes/nullability/PK/serverdefaults/FKtarget/SQLtypes/codecmodels compared0diff. RED/cov/JUnitactor leídos y sourcefinalscope actual. Warningcache_dir por no:cacheprovider, sinfallofuncional. Fuenteprivatefixesdentro6owned; versiones0001..7 yacceptedcodecimmutable. Dactivated por4routesmigrations; Cfalse. No performanceverdictdesdeA, sin producto/generaciones/backupactualclaim.


## LenteB completa

| CriterioB | Estado | Evidencia |
|---|---|---|
| staticregistry | ✓ | registry85;356types+futuretablebeforereloadrealheads6/7 |
| columnstype/null/default/FK | ✓ | registry86/27tables356columnsbaselineexact |
| 3codecs | ✓ | registry26/45/65 AST methodsbaselineexact |
| seedNULLinvalid | ✓ | test230/23ownPASS/SQLaliasesSeedtyped |
| replayhistórico | ✓ | test77/privateSQLreal6/7 |
| CPUfixedguards | ✓ | cpu668/reinstallactualschemasallrowsequal |
| helpersdirty | ✓ | fix1 24/78 fix2 54;84/125DDLbyteexact |
| authorityselectsbounded | ✓ | cpu270/276/test266+43regressionownPASS |
| v1projection/excluded | ✓ | snap27/422/preimagefullpopulatedequal |
| digests/relationships/SQLRows | ✓ | snap84/121/434 aliasesmutationignored |
| privatefieldsNULL | ✓ | snap36/67 codecsbaseline |
| restorecollisionunboundedseed | ✓ | snap632 realroundtrip/unchangedcollision/seedtest |
| custodyimports | ✓ | 217pins44/48ownprivateimports |
| T05fullSQLv2APIpublicationlibrarybackup | no verificable | 2Afreezeonly nofutureintegrationproof |

## LenteD completa

| CriterioD | Estado | Evidencia |
|---|---|---|
| N+1introduced | ✓ | cpu2674grouped;24projectionSELECTidentical |
| libraryscale | ✓ | snap422/inmem30/100/1000songs20takes:25queriesbothmedian4.826–5.052ms |
| takebatchscale | ✓ | unchangedclosure_rows7;1000songs20980takesroot1000,baseline33frozen33queries31.920/31.581ms,batch400IDs |
| registryconstruction | ✓ | registry86/snap24 oneimport6.679msmedianstableidentity |
| SQLguardsworkperrow | ✓ | samegeneratorsCPU40sentences196836B/fix1 84/32890B/fix2 125/141386B |
| restore/serialization/locks | ✓readsource | snap69/496/582/673 nochangedloopslocks/collisionbatches400 |

Bincidentespropiosharnesssinuninstall/JSONadjacentespreimage corregidos sinfuentes, no productbugs niQA. Dlatencias soninmemory/sólo localcomparación, noIOdisco ni concurrenciaverdict; generadoresregistranSQLnoinstalación real. Baseline698PASS1skipWindowsoldtestSHAbefore4querytests+focalfinal23truthful. No fixtureactualpersonal-library/backup/generationclaims. NEWSQLv2/ORMv2API/Songv2/import/publicación/PORT01full/walbackupM1personalpending. NoT05/M2closure.
