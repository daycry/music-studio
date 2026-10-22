# QA independiente actual — corrección de HEAD · M1 · 2026-10-10

**Componente CPU/API: VERDE. M1 integral: NO-VERDE.** La regresión actual conjunta pasa en Windows y Linux y acredita los tres umbrales whole. Este resultado reemplaza el rojo de las expectativas de revisión en la unidad anterior; no cierra ninguna tarea ni el hito.

## Alcance y fuentes

Tres literales de expectativa `0006 → 0007`, integrados por CAS el 2026-10-10 a las 20:37:16 UTC después de revisión independiente A/B/D sin gaps. Unión sellada de diez fuentes: las ocho fuentes de la unidad anterior, con overrides de los tres tests actuales (dispatcher_retry ya pertenecía a las ocho). No se usan hashes de preimagen como fuente actual. Copia privada desde el checkout actual, hashes antes/después idénticos. El contenido de las 71 fuentes de runtime del server coincide byte a byte con la QA anterior; prueba en historical-http-runtime-proof.json.

## Entorno y puertas

Windows: Python 3.12.14 gestionado por el entorno del repositorio. Linux: SQLite 3.40.1 nativo, UID/GID 10001, capacidades eliminadas, no-new-privileges, red none y fuentes montadas de solo lectura. Imagen CPU fijada `sha256:7c65be72cf35ef0989407f280405f49c41662d01caa32a4c75bf4eec4d55ee25`. Fixtures, SQLite y resultados exclusivamente en head-fix-qa. Sin GPU, Ollama, instalación, datos canónicos ni operaciones WSL/storage.

Ledger-lint exit 0: cero incoherencias y un aviso UTF-8 de tasks.md leído con reemplazos. Coverage-check exit 0: cero referencias rotas; T-00 documental sin cobertura declarada. Ese aviso no se presenta como cobertura UI.

## Regresión actual, una sola selección por plataforma

| Plataforma | Pasan | Fallos | Errores | Omitidos |
|---|---:|---:|---:|---:|
| Windows | 310 | 0 | 0 | 0 |
| Linux | 300 | 0 | 0 | 10 |

Selección: test_attempt_json_guard_upgrade.py, test_job_attempt_schema.py, dispatcher_retry completo, test_retry_implicit_model_validation.py, test_queue_chains.py, test_queue_manual_retry.py, test_domain_routes_lifecycle_validation.py y test_generation_language_optional.py. Sin exclusión de los casos que antes fallaban ni adaptación de sus aserciones por QA.

Los diez omitidos Linux son controles nativos propios de WinEvent; todos se ejecutan y pasan en Windows. Se conserva su lista y motivo oficial en summary.json. No se convierten errores en skips.

Los tests de modelo implícito/explícito, cambio del default, modelo original no disponible y conflicto legacy fail-closed se ejecutan de nuevo. Las verificaciones de HEAD y la fixture compartida que causaron el rojo anterior pasan con el head real 0007. Estas pruebas usan API/SQLite reales con backend sintético; no acreditan generación musical GPU.

## Cobertura actual whole por fuente de producto

| Plataforma | Fuente | Líneas | Cobertura | Exclusiones |
|---|---|---:|---:|---:|
| Windows | apps/server/app/migrations/job_attempt_invariants.py | 189/202 | 93.5644 % | 0 |
| Windows | apps/server/app/migrations/versions/0007_job_attempt_json_guard.py | 15/15 | 100.0000 % | 0 |
| Windows | apps/server/app/queue/chains.py | 84/86 | 97.6744 % | 0 |
| Linux | apps/server/app/migrations/job_attempt_invariants.py | 189/202 | 93.5644 % | 0 |
| Linux | apps/server/app/migrations/versions/0007_job_attempt_json_guard.py | 15/15 | 100.0000 % | 0 |
| Linux | apps/server/app/queue/chains.py | 84/86 | 97.6744 % | 0 |

Todos los módulos de producto afectados superan el 80 % whole con cero líneas excluidas. JSON oficial y salida term-missing conservados. No se sustituye cobertura por conteos de pytest.

## HTTP y FIFO: evidencia histórica asociada, sin ejecución nueva

Se vuelve a ejecutar qa-gate sobre el results.json real anterior, sin copiarlo ni modificarlo ni fabricar JSON desde pytest. HTTP histórico: 6/6, request Playwright contra server Docker oficial/local y mock, guardrail registrado entonces. Su SHA-256 y la igualdad de los 71 ficheros de runtime justifican reutilizar esta evidencia para un delta exclusivo de tests. Cero pruebas HTTP nuevas en esta pasada.

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 6,
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

FIFO POSIX histórico de la QA anterior: 66 PASS, 1 SKIP, fixture con el mismo SHA actual. No se repite. Lectura histórica de SQLite después de detener el server: head 0007, modelo/engine efectivos capturados y concordantes con take, autoría/idioma preservados, dos takes distintos por canción. Nada de esto acredita ready, assets, Range o UI actual.

Referencias históricas: [informe anterior](current-next-fixes-qa-2026-10-10.md), [results.json HTTP](../../../../.cache/dev-cycle/m1/validation-20261010/next-fixes-qa/results.json), [observación SQLite](../../../../.cache/dev-cycle/m1/validation-20261010/next-fixes-qa/http-db-readonly.json) y [JUnit FIFO POSIX](../../../../.cache/dev-cycle/m1/validation-20261010/next-fixes-qa/linux-fifo/junit.xml). La evidencia anterior sellada permanece intacta.

## Trazabilidad y limpieza

T-02: upgrade/downgrade/rollback, guardas JSON y HEAD actual. T-04: admisión, cola y reintento implícito/default/legacy, snapshot del lector y post-failure retry. Los casos de idioma y autoría conservan cobertura parcial CPU/API de T-07. No se afirma cumplimiento completo de tareas o E2E UI.

Evidencia nueva: `.cache/dev-cycle/m1/validation-20261010/head-fix-qa/`, con diez SHA, JUnit Windows/Linux, terminales con exit 0, JSON oficiales de cobertura, metadatos nativos, inventario y SOURCE_SEAL_FINISHED. El contenedor nativo propio está terminado con PID 0 y eliminado. No se crearon red, tag ni token nuevos. ACE persistente y mock originales preservados, sin acciones sobre ellos. PDF omitido: dependencias de to-pdf ausentes en las cachés gestionadas comprobadas; no se instalan.

Artefactos nuevos: [terminal Windows](../../../../.cache/dev-cycle/m1/validation-20261010/head-fix-qa/windows.terminal.json), [JUnit Windows](../../../../.cache/dev-cycle/m1/validation-20261010/head-fix-qa/windows.xml), [terminal Linux](../../../../.cache/dev-cycle/m1/validation-20261010/head-fix-qa/linux-run.terminal.json), [JUnit Linux](../../../../.cache/dev-cycle/m1/validation-20261010/head-fix-qa/linux/junit.xml), [cobertura Windows](../../../../.cache/dev-cycle/m1/validation-20261010/head-fix-qa/windows-coverage.json), [cobertura Linux](../../../../.cache/dev-cycle/m1/validation-20261010/head-fix-qa/linux/coverage.json), [resumen](../../../../.cache/dev-cycle/m1/validation-20261010/head-fix-qa/summary.json), [prueba de runtime histórico](../../../../.cache/dev-cycle/m1/validation-20261010/head-fix-qa/historical-http-runtime-proof.json), [cleanup](../../../../.cache/dev-cycle/m1/validation-20261010/head-fix-qa/cleanup-receipt.json), [inventario](../../../../.cache/dev-cycle/m1/validation-20261010/head-fix-qa/artifact-inventory.json) y [sello final](../../../../.cache/dev-cycle/m1/validation-20261010/head-fix-qa/SOURCE_SEAL_FINISHED.json).

## Checklist pendiente para M1 integral

- [ ] M-01: generación GPU real, escucha humana y cierre M0/T-13.
- [ ] M-02: UI, revisión visual y accesibilidad.
- [ ] M-03: backup/restauración de datos reales.
- [ ] Persistencia ext4/VHDX, recovery, assets y Range integral.
- [ ] Revisión/cierre de las tareas completas y Git por el orquestador.

Sin cambio de ledger, spec o plan ni handoff de cierre a documenter. Las mediciones de tokens/coste de API no están disponibles: no se atribuye consumo real a esta QA.
