# M1/T03 — Corrección propuesta de Minor R03-01

La reproducción nativa de `[Ⅳ]\n` confirmó categoría Nl, `isalpha() == False` y UNKNOWN_TAG en Python. La decisión de root exige letras Unicode categoría L, coincidiendo con TypeScript. El nuevo fixture `roman-numeral-not-letter` se escribió manualmente antes del código: original intacto, sections vacío, anotación y aviso MALFORMED_TAG, rango UTF-16 0..4. No se obtuvo su expectativa de ningún parser.

RED: `apps/server/tests/test_lyrics.py::test_lyrics_contract[roman-numeral-not-letter]` falló por UNKNOWN_TAG frente a MALFORMED_TAG · 2026-10-07. `red-python.command.json`, stdout/stderr y JUnit conservan argv, inicio/fin UTC y exit1. Antes del cambio de producción, TypeScript pasó los dos tests del mismo fixture (110 restantes omitidos explícitamente por selección). No hubo fallo de setup ni se eliminó evidencia.

Cambio mínimo: conservar el regex de topología existente y exigir `isalpha()` para todos los caracteres del alias excepto sus separadores horizontales/guion. `isalpha()` exige categorías Lu/Ll/Lt/Lm/Lo; no incluye Nl/No. Así se excluyen también números mezclados con letras, como requiere `\p{L}`. La rama de alias conocidos precede al predicado y permanece intacta. Ningún cambio de TypeScript, numeración ASCII, campos, texto, Markdown, direcciones ni rangos.

GREEN actual: Python112pass y TypeScript112pass sobre los mismos56fixtures, incluidos cortes literales. Los55registros previos conservan contenido y orden; inserción JSON sin reserializar registros anteriores. Tests genéricos canónicos intactos. Cobertura oficial del módulo Python entero:66/66sentencias,100%,0líneas excluidas (`python-coverage.json` y `.coverage-python`). V8 real del módulo TypeScript entero:68/68sentencias,53/53líneas,5/5funciones,57/62ramas=91,93%, configuración exclude[] intacta (`ts-coverage/coverage-final.json`). Se cumplen todos los umbrales80. Ruff y comprobación de formato del único Python propio exit0.

Pytest emitió aviso Unknown config option cache_dir al desactivar cacheprovider; ambos resultados son funcionales (RED por igualdad contractual, GREEN112). Ruff se ejecutó inicialmente sin override de caché: no se certifica ausencia de escrituras en su caché compartida preconfigurada. No se borró ni restauró caché ajena. No hubo fix automático/global ni cambios de configuración.

`receipt.json`, `sources-current/`, `sources-protected/`, `owned.diff` y preimágenes de root permiten revisar ambos cambios. Las16fuentes protegidas coinciden exactamente en bytes/SHA256 con el baseline de root, incluidos API, tipos y contratos. No se repitió la suite API351pass3skip histórica ni se presenta como nueva; se ejecutó el módulo completo del parser, sin repetir vecinos M0 ajenos a este cambio.

La unidad queda entregada para revisión2 y QA fresca de root. No acredita cierre T03/M1, Git, UI, GPU ni calidad humana. Sin deps/instalaciones/red/subagentes/ledger/docs públicos/knowledge. Peso1 estimado; modelo/tokens/EUR/horasIA reales NULL. El inventario privado excluye explícitamente cli-original.jsonl, cli-stderr-original.txt, cli-metadata y final-original: root sellará el CLI solo después de metadata terminal0 del wrapper.


Custodia root: metadata terminal0,18fuentes actuales y16protegidas exactas; inventario noCLI cerrado verificado. Ambos JUnit completos112pass, RED exit1 y cobertura Python66/66sinexclusiones verificados. Revisión2 y QA pendientes.
