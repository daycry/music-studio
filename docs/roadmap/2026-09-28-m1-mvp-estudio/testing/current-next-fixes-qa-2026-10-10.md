# QA independiente actual — segunda unidad M1 · 2026-10-10

**Componente CPU/API: NO-VERDE. M1 integral: NO-VERDE.** El gate HTTP y los umbrales whole pasan, pero las regresiones detectan expectativas obsoletas de revisión con fallos y errores de preparación. No se cierra ninguna tarea ni se cambia el ledger.

## Alcance y custodia

Ocho fuentes integradas verificadas antes y después, contra `next-fixes-review/integration-receipt.json`. Copia privada de fuentes actuales; sin datos canónicos, GPU, Ollama ni instalación. Windows Python gestionado 3.12.14; Linux SQLite 3.40.1, UID/GID 10001, capacidades eliminadas, no-new-privileges, red none, fuentes montadas de solo lectura. Imagen CPU fijada `sha256:7c65be72cf35ef0989407f280405f49c41662d01caa32a4c75bf4eec4d55ee25`.

## Puertas deterministas

Ledger-lint: exit 0, cero incoherencias y un aviso de UTF-8 leído con reemplazos en tasks.md. Coverage-check: exit 0, cero referencias rotas; T-00 documental sin cobertura declarada. Guardrail: exit 0, HTTP exclusivamente `127.0.0.1:8000`. Los escenarios HTTP focales cubren parcialmente E2E-01/E2E-02 y API-01/API-02; no equivalen a UI, ready, assets, Range ni recuperación integral.

## Resultados actuales

| Selección | Pasan | Fallos | Errores | Omitidos |
|---|---:|---:|---:|---:|
| Windows ampliado | 227 | 2 | 0 | 0 |
| Windows JSON focal | 124 | 0 | 0 | 0 |
| Windows chains | 32 | 0 | 49 | 0 |
| Linux JSON | 124 | 0 | 0 | 0 |
| Linux chains | 32 | 0 | 49 | 0 |
| Linux FIFO | 66 | 0 | 0 | 1 |

La primera selección Windows incluyó el fichero dispatcher_retry completo; se conserva su terminal y los dos fallos, sin excluirlos. La selección focal posterior de 124 casos verifica el alcance JSON previsto, sin sustituir la ampliada.

### Hallazgos

- `apps/server/tests/test_dispatcher_retry.py:1824`: `test_shared_reader_interleaved_three_pages_native[True/False]` espera `0006`; la BD real migrada tiene `0007`. Dos fallos actuales de regresión.
- `apps/server/tests/test_dispatcher_admission.py:217`: fixture compartida `engine` espera `0006`; ocasiona 49 errores de setup en chains en cada plataforma. Las diez pruebas nuevas de modelo implícito/explícito, cambio de default y legacy fail-closed sí pasan, pero no corrigen esta falta de evidencia del conjunto.

## HTTP real y BD

Playwright request real: 6/6, sin reintentos. Server construido desde Dockerfile oficial con tag propio y mock existente preservado. Cuatro combinaciones de idioma omiten model_id, responden 202 y conservan dos takes distintos. La lectura SQLite de solo lectura después de detener el server confirma head 0007, job.model_id/job.engine_id capturados como mock y concordancia con take.model_id; autoría own, textos y parámetros de idioma se conservan. Hubo una primera ejecución HTTP de 6/6 sin recibo del wrapper; la ejecución posterior registrada con guardrail genera los results.json vigentes. Por ello la BD contiene ocho creaciones y dieciséis takes; no se presentan como doce tests finales.

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

## Cobertura whole, sin exclusiones

```json
{
  "Windows JSON": {
    "apps\\server\\app\\migrations\\job_attempt_invariants.py": {
      "covered_lines": 189,
      "num_statements": 202,
      "percent_covered": 93.56435643564356,
      "percent_covered_display": "94",
      "missing_lines": 13,
      "excluded_lines": 0,
      "percent_statements_covered": 93.56435643564356,
      "percent_statements_covered_display": "94"
    },
    "apps\\server\\app\\migrations\\versions\\0007_job_attempt_json_guard.py": {
      "covered_lines": 15,
      "num_statements": 15,
      "percent_covered": 100.0,
      "percent_covered_display": "100",
      "missing_lines": 0,
      "excluded_lines": 0,
      "percent_statements_covered": 100.0,
      "percent_statements_covered_display": "100"
    }
  },
  "Windows chains": {
    "apps\\server\\app\\migrations\\job_attempt_invariants.py": {
      "covered_lines": 169,
      "num_statements": 202,
      "percent_covered": 83.66336633663366,
      "percent_covered_display": "84",
      "missing_lines": 33,
      "excluded_lines": 0,
      "percent_statements_covered": 83.66336633663366,
      "percent_statements_covered_display": "84"
    },
    "apps\\server\\app\\migrations\\versions\\0007_job_attempt_json_guard.py": {
      "covered_lines": 14,
      "num_statements": 15,
      "percent_covered": 93.33333333333333,
      "percent_covered_display": "93",
      "missing_lines": 1,
      "excluded_lines": 0,
      "percent_statements_covered": 93.33333333333333,
      "percent_statements_covered_display": "93"
    },
    "apps\\server\\app\\queue\\chains.py": {
      "covered_lines": 79,
      "num_statements": 86,
      "percent_covered": 91.86046511627907,
      "percent_covered_display": "92",
      "missing_lines": 7,
      "excluded_lines": 0,
      "percent_statements_covered": 91.86046511627907,
      "percent_statements_covered_display": "92"
    }
  },
  "Linux JSON": {
    "apps/server/app/migrations/job_attempt_invariants.py": {
      "covered_lines": 189,
      "num_statements": 202,
      "percent_covered": 93.56435643564356,
      "percent_covered_display": "94",
      "missing_lines": 13,
      "excluded_lines": 0,
      "percent_statements_covered": 93.56435643564356,
      "percent_statements_covered_display": "94"
    },
    "apps/server/app/migrations/versions/0007_job_attempt_json_guard.py": {
      "covered_lines": 15,
      "num_statements": 15,
      "percent_covered": 100.0,
      "percent_covered_display": "100",
      "missing_lines": 0,
      "excluded_lines": 0,
      "percent_statements_covered": 100.0,
      "percent_statements_covered_display": "100"
    },
    "apps/server/app/queue/chains.py": {
      "covered_lines": 22,
      "num_statements": 86,
      "percent_covered": 25.58139534883721,
      "percent_covered_display": "26",
      "missing_lines": 64,
      "excluded_lines": 0,
      "percent_statements_covered": 25.58139534883721,
      "percent_statements_covered_display": "26"
    }
  },
  "Linux chains": {
    "apps/server/app/migrations/job_attempt_invariants.py": {
      "covered_lines": 169,
      "num_statements": 202,
      "percent_covered": 83.66336633663366,
      "percent_covered_display": "84",
      "missing_lines": 33,
      "excluded_lines": 0,
      "percent_statements_covered": 83.66336633663366,
      "percent_statements_covered_display": "84"
    },
    "apps/server/app/migrations/versions/0007_job_attempt_json_guard.py": {
      "covered_lines": 14,
      "num_statements": 15,
      "percent_covered": 93.33333333333333,
      "percent_covered_display": "93",
      "missing_lines": 1,
      "excluded_lines": 0,
      "percent_statements_covered": 93.33333333333333,
      "percent_statements_covered_display": "93"
    },
    "apps/server/app/queue/chains.py": {
      "covered_lines": 79,
      "num_statements": 86,
      "percent_covered": 91.86046511627907,
      "percent_covered_display": "92",
      "missing_lines": 7,
      "excluded_lines": 0,
      "percent_statements_covered": 91.86046511627907,
      "percent_statements_covered_display": "92"
    }
  }
}
```

La cobertura del directorio completo es informativa: el umbral se valora sobre cada fuente de producto afectada. Los errores de fixture impiden aceptar chains, incluso con el gate HTTP verde.

## Incidencias del arnés conservadas

Se corrigieron exclusivamente scripts propios: quoting de una preparación Python; ruta de bash inexistente; expectativa inicial de ocho filas frente a dieciséis por las dos ejecuciones HTTP; comprobación de cleanup que incluía el contenedor nativo aún en marcha; quoting del comando de metadatos. No se cambiaron las fuentes probadas ni se fabricaron estados de generación. Recibos parciales y logs permanecen en la carpeta de evidencia.

## Evidencia y limpieza

Evidencia: `.cache/dev-cycle/m1/validation-20261010/next-fixes-qa/`, incluyendo terminales, JUnit, JSON whole coverage, trazas request, results.json, http-db-readonly.json e inventario con hashes y metadatos de entradas especiales. No hay screenshots de UI: esta auditoría es API request focal. Contenedores y red Compose propios retirados; tag server propio retirado; mock original preservado; token retirado en archivos de configuración e inspect. Ningún contenedor propio permanece.

PDF omitido: no se encontraron dependencias de to-pdf en las cachés gestionadas comprobadas; no se instalaron dependencias ni se usó caché personal.

## Checklist pendiente

- [ ] Corregir los dos literales de head detectados y volver a revisión/QA con fuentes nuevas.
- [ ] M-01: generación GPU y escucha humana; M0/T-13.
- [ ] M-02: UI, revisión visual y accesibilidad.
- [ ] M-03: backup/restauración de datos reales.
- [ ] ext4/VHDX persistente, recuperación, assets y reproducción Range integral.

No se documenta cierre ni se da handoff a documenter; estados y Git son responsabilidad del orquestador. Métricas de tiempo/tokens no disponibles como mediciones de API.
