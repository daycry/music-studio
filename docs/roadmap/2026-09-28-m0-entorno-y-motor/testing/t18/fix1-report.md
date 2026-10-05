# T-18 — Fix1 de procedencia y compatibilidad

Fecha: 2026-10-05. Corrección de A1/B1/B2 de [revisión 1](review-attempt1.md). El servicio devolvió `agent thread limit reached` al reactivar el implementer y al intentar despachar uno nuevo; la corrección se ejecuta en el contexto principal con el método TDD del plugin. No se oculta la degradación. Revisión 2 y QA independiente siguen pendientes.

## RED real antes de corregir

- RED: `apps/engines/acestep/tests/test_adapter.py::test_key_descriptor_preserves_legacy_strings` falló por `ValidationError` en minLength/maxLength, dos casos de longitud 0/33 · 2026-10-05. GREEN: dos casos pasan tras restaurar `key: {type: string}`.
- RED: `tests/test_input_preparation.py::test_declared_lyrics_hash_matches_source_bytes` falló `DID NOT RAISE ValueError` · 2026-10-05. El caso válido distingue bytes BOM/CRLF de texto efectivo.
- RED: `tests/test_generate_preparation.py::test_manifest_rejects_false_lyrics_source_hash` falló `DID NOT RAISE ValueError` con un recibo externo y referencia válidos por hash · 2026-10-05. GREEN: dos regresiones de hash fuente pasan tras cruzarlo en preparador y verificador.
- RED: `tests/test_input_preparation.py::test_execution_binding_preserves_requested_seed` falló `None != {seed: 1234, n_outputs: 2}` · 2026-10-05.
- RED: `tests/test_generate_preparation.py::test_manifest_variant_seed_binding[1/None]` falló `DID NOT RAISE ValueError` en ambos casos · 2026-10-05. El primer intento del caso nulo devolvió `ENGINE_SEED_MISMATCH` por la fixture de protocolo fijada a semilla 1; se corrigió la fixture antes del RED contractual, sin modificar producción. GREEN: tres casos de binding pasan; se prueba semilla falsa fuera y dentro del rango, índice inválido y origen con semilla nula preservado.

El test adicional de error tipado para `fields` malformado ya pasaba: se conserva como regresión, sin inventar RED ni modificar producción para él. TDD n/a para prosa/config de los informes y documentación.

## Resultado de implementación

Los statements de producción nuevos preservan los campos aceptados por `/v1`; la preparación acepta una extensión privada `execution` comprobada, y el manifiesto incorpora `request.variant_index` opcional. Generaciones nuevas exigen binding válido en sus referencias de preparación; los manifiestos anteriores sin referencia siguen siendo válidos. La petición original no se modifica para ocultar la resolución de semillas aleatorias.

Verificación de los seis módulos declarados, con cobertura y temporales locales: **185 passed, 1 skipped, cinco warnings Starlette existentes**, exit 0, 9,02 s. Exportador: `engine-v1.json up to date`; ejemplos: `all valid (4 manifests)`; Ruff del alcance: `All checks passed!`; diff-check: exit 0. El probe real de preparación sigue confirmando 72 líneas, nueve tags, 32 hashes intactos y recibo `fa24e7c9…` inmutable, sin generación ni GPU.

| Producción | Statements cambiados ejecutados/total | Cobertura |
|---|---|---|
| input_preparation | 92/95 | 96,84 % |
| generate | 44/47 | 93,62 % |
| adapter | 2/2 | 100 % |
| manifest | 52/59 | 88,14 % |
| descriptor | Cambio dentro de literal, sin statements nuevos separados | Archivo completo 100 % |

La cobertura total de los directorios incluidos es 74 % porque incorpora scripts y código previo fuera de alcance; no se confunde con la cobertura de este cambio. El cruce reproducible con el diff queda en `.cache/dev-cycle/t18/measure-changed.py` y `fix1-changed-coverage.json`, con datos oficiales pytest-cov. No mide ramas ni calidad musical. No se cierra T-18 ni M0 con la implementación por sí sola.
