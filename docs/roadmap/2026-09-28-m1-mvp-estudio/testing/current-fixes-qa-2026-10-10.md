# QA independiente de correcciones CPU/API de M1 — 2026-10-10

**Componente CPU/API: VERDE acotado. M1 integral: NO-VERDE.** No cierra ninguna tarea ni estados del plan/spec. Fuentes congeladas: 16/16 SHA-256 iguales al recibo de revisión antes/después, incluido `db.py` c7a1a01f y `domain_routes.py` ecec4866. Runtime Docker real: cuatro fuentes lógicas coinciden con el checkout.

## Alcance y resultados nuevos

| Ejecución independiente | Resultado | Evidencia |
|---|---|---|
| Windows: seis ficheros API + FTS/persistencia/shutdown + dispatcher CPU/recovery/schema/attempt | 349 pasan, 1 omitida, 0 fallos, 0 errores | `windows-final.xml`, `windows-final.log`, `windows-final.terminal.json` |
| Linux nativo: FTS/persistencia/shutdown | 38/38 pasan | `linux-final/junit.xml`, `linux-final-run.log`, `linux-final-inspect.json` |
| Playwright HTTP real: idioma omitido/null/params-fr/explicit-es, autoría/schema, seguridad/contrato | 6/6 pasan, sin retries | `results.json`, `playwright-junit.xml`, `test-results/` trazas |
| Export code-first / Ruff check / Ruff format | 0 / 0 / 0 | `export-attempt2`, `ruff-check`, `ruff-format` logs/terminales |
| ledger-lint / coverage-check | 0 incoherencias / 0 referencias rotas | logs/terminales propios |

Selección API original: 203 casos; selección DB Linux: 38. La ejecución Windows final reúne también los tests formateados de dispatcher/recovery/schema/attempt; la omisión Windows corresponde al rechazo de symlink del snapshot, probado en Linux. Linux usa imagen fijada `sha256:7c65be72cf35ef0989407f280405f49c41662d01caa32a4c75bf4eec4d55ee25`, UID/GID10001, ALL capacidades retiradas, no-new-privileges, red none, sin GPU, server actual RO y fixtures propias. No se ejecutó suite completa.

`coverage-check` avisa **T-00 sin cobertura declarada**. No hay GWT huérfanos ni referencias rotas; se conserva el aviso para el hito completo. T-00 es diagnóstico del entorno, no tarea UI.

## Gate determinista — solo HTTP focal

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

`qa-gate.py` exit0 sobre el `results.json` real nuevo, sin adaptar estadísticas pytest ni reutilizar pases antiguos. Los seis casos usan Playwright `request`, sin navegación/UI; las evidencias son respuestas JSON adjuntas y trazas, no screenshots visuales. El guardrail del kit autoriza exclusivamente `http://127.0.0.1:8000`. Server oficial reconstruido con tag propio y mock original preservado; Compose privado, sin GPU y bind de datos exclusivamente de QA.

## Cobertura oficial WHOLE

```json
{
  "domain_routes.py": {
    "apps\\server\\app\\domain_routes.py": {
      "covered_lines": 654,
      "num_statements": 755,
      "percent_covered": 86.62251655629139,
      "percent_covered_display": "87",
      "missing_lines": 101,
      "excluded_lines": 0,
      "percent_statements_covered": 86.62251655629139,
      "percent_statements_covered_display": "87"
    }
  },
  "db.py": {
    "apps/server/app/db.py": {
      "covered_lines": 60,
      "num_statements": 64,
      "percent_covered": 93.75,
      "percent_covered_display": "94",
      "missing_lines": 4,
      "excluded_lines": 0,
      "percent_statements_covered": 93.75,
      "percent_statements_covered_display": "94"
    }
  }
}
```

Ambos ficheros completos ≥80 %, ninguna línea excluida. No se atribuye esta cobertura al servidor completo ni al producto GPU.

## Identidad durable y límites

La API real acepta omitido/null con 202; preserva `params.language=fr` y precedencia del campo explícito `es`. Cada petición crea dos takes distintos, cuya identidad y pertenencia se comprueban vía API. Tras apagar solo el server propio, lectura SQLite `mode=ro`: 4 canciones, 8 takes, 16 jobs (generación/post), 4 versiones de letra y 4 intentos. `durable-own-db.json` conserva las filas; la autoría, los mismos IDs y parámetros sobreviven al cierre. El descriptor requerido y rechazo correspondiente se prueban en los tests API con resolver real; no se modifica el descriptor mock del despliegue. La validación HTTP negativa conserva autoría/schema. Los takes observados quedan `queued`: no afirma ready, assets, Range, audio, recuperación persistente ni ext4.

## Intentos y carencias del arnés conservados

- Primer snapshot omitió `app/models` por filtro de directorios: error de colección/import y export; corregido el filtro de copia, sin tocar producto.
- Windows intento2: 333 pass/1 skip/3 fail/13 errors. Linux intento1:37 pass/1 fail. Causa demostrada: parent privado `queue` no creado y binario fijado ausente de snapshot. Se crearon los parents y copió el binario Linux real con SHA-256 `953632dece404bb1461a4a2285f0191a6105d72c81f9da577eb54326a7fad49a`; no se ejecutó ese binario en Windows ni se fabricó placeholder. Finales nuevos verdes, sin retries ciegos.
- Cleanup inicial inventarió también el contenedor nativo que ya había sido eliminado por su propio arnés; conservado en registros. Forense final corrigió exclusivamente la ruta privada real `data/db/studio.sqlite`. No intervención en datos canónicos.

## Pendientes de M1 y trazabilidad

T-02: FTS/persistencia CPU comprobadas; backup/restauración de datos reales M-03 pendiente. T-03/T-07/T-09: contrato, ciclo API, idioma/autoría comprobados. T-04: dispatcher/recovery CPU y encolado real comprobados; GPU y recuperación/publicación persistente pendientes. T-05/T-06/T-15: aceptación ext4/VHDX y E2E-01 listo/audio/Range siguen sin acreditar en esta unidad.

- [ ] M-01: generación real GPU y escucha humana.
- [ ] M-02: revisión visual y accesibilidad básica.
- [ ] M-03: backup/restauración real.
- [ ] Publicación/recuperación persistente sobre ext4 autorizado e integral E2E-01.

PDF omitido: no existen dependencias gestionadas de `to-pdf` disponibles; no se instalaron paquetes ni Chromium. Informe exclusivamente local. Sin handoff documenter ni cierre de estados; el orquestador conserva ledger/Git.

## Artefactos y cleanup

Carpeta: `.cache/dev-cycle/m1/validation-20261010/fixes-qa/`. `inventory.json` incluye SHA-256/tamaños de evidencias; `summary.json`, sellos antes/después y `SOURCE_SEAL_FINISHED.json`. Cleanup: propios server/mock/nativos, red propia y tag server propio retirados; imagen CPU/mock originales preservadas. ACE persistente 588080f047b5/d8d39e3a no tocado. `cleanup.json` registra cero contenedores propios restantes.
