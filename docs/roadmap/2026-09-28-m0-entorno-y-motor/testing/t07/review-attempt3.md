# Revisión T-07 — intento 3 de 3

2026-10-05, base main11c1884, diff y nuevos declarados: 39 ficheros en snapshot, 34 T-07 y cinco journals ajenos. Lentes A+B+D con contexto fresco, secuenciales por límite de threads concurrentes. Se pasó la tabla completa del intento2; aprobados conservados, solo fix2 reevaluado salvo nueva evidencia. Scope0, fuera=[], avisos=[], sin exclusiones de usuario. Cfalse/Dtrue; no cambian API ni interop. Jira/Confluence desactivados, sin promoción de conocimiento ajeno.

| Criterio T-07 | Resultado | Evidencia |
|---|---|---|
| Material privado/declaración previa y B-02 preservada | ✓ conservado A | tasks:295/305, recibo own; briefs.yaml; material literal no leído |
| Directa/catálogo, semilla, variantes, instrumental, engine/token | ✓ conservado A | generate:55/114/132/175/290/324 y tests:28/61/119/321/362 |
| Eventos reales, cuatro archivos, procedencia y publicación inmutable | ✓ conservado A | generate:199/376/432/441/517/523; integración mock/FFmpeg y regressions Windows |
| B1 Ctrl+C, descarga confirmada, error primario y protección ajena | ✓ corregido/conservado A+B | 64 CLI verdes; mockreal130/loadedNone, errores por identidad |
| B2/D2 presupuesto global único | ✓ corregido A+B+D | generate:349/413/540/543 marca antes y no repite; test_generate_has_one_cleanup_budget completo |
| Sin outputs tras unload fallido, sentinel intacto | ✓ B | cuatro reproducciones independientes, post nunca ejecutado |
| TDD/cobertura/alcance/docs/constitución | ✓ A | RED600→GREEN≤300, 312/332=93,98 %, scope/ledger/diffcheck0, pipeline:101 actualizado |
| Generación normal y manifiestos reales | ✓ conservado A | cli-full-generation-receipt exit0,255s,all valid(2 manifests); no generación repetida por fixes de error |
| Escalado y espera Windows | ✓ conservado D | intento1:1/8/64 poststub y esperas≤1,5s; sin evidencia nueva |
| Escucha y primera impresión | pendiente declarada | tasks:282/297; T-07 abierta, no calidad musical atribuida a tests |

## Evidencia ejecutada

A: uv run --no-sync --all-packages python -B -m pytest tests/test_generate.py -q --tb=short -p no:cacheprovider --basetemp=.cache/pytest/review-t07-a3 -o addopts= →64 passed,6warnings,5,25s. Scope0/0fuera/0avisos, ledger0incoherencias/7avisosChangelog, diffcheck0. Código/tests/diff leídos por bloques, privados no leídos.

B: uv run --no-sync --all-packages python -B -m pytest tests/test_generate.py -q --tb=short -p no:cacheprovider --basetemp=.cache/review-t07-b3-pytest -o addopts= →64 passed,6warnings,5,29s. Cuatro reproducciones independientes con HTTPfake y reloj exclusivoCLI: 409persistente→300s/entrada[0]/3001unload/ENGINE_CLEANUP_TIMEOUT; 500→0s/unaentrada/unload1/ENGINE_HTTP_500; ReadTimeout y KeyboardInterrupt→0s/unaentrada/unload1/misma instancia primaria. Todos con aviso/nota, ningún manifiesto, post no ejecutado y sentinel intacto. Último409 en299,9999999999997, no segunda ventana. Exit0. Montaje inicial TemporaryDirectory fallóACL0700 antes de generate; repetir con mkdirnormal único.cache permitió reproducción válida.

D: pytest tests/test_generate.py::test_generate_has_one_cleanup_budget con entorno gestionado →1passed,1warning,0,91s,exit0. Deadline individual y presupuesto único confirmados por fuente; no repite benchmark aprobado.

Advertencias conocidas de cacheprovider/TestClient. No GPU ni cancelación GPU real de las lentes, ni modificaciones del producto/ledger/Git. Fusión: **0 Critical/0 Important pendiente/0 Minor**. B1 y B2/D2 corregidos. Siguiente QA independiente sin UI; escucha aún pendiente. La revisión técnica no completa el criterio humano.
