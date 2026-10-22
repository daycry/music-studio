> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# QA independiente · T05 U1

**SCOPEDPASS** dentro del componente, pendiente de adjudicación por root. Una sola suite actual: 228 PASS, 4 SKIP de symlink Windows, 5 warnings de Starlette; exit 0. TDD n/a: QA de solo lectura, sin modificaciones ni nuevos tests.

| Archivo completo | Líneas cubiertas | Total | Cobertura actual | Excluidas |
|---|---:|---:|---:|---:|
| packages\audio-post\audio_post\manifest.py | 231 | 250 | 92.40% | 0 |
| packages\audio-post\audio_post\pipeline.py | 128 | 133 | 96.24% | 0 |

Cobertura oficial de cada módulo desde `current.coverage` y `current-coverage.json`, una ejecución fresca; ninguna unión histórica, extracción, media ni exclusión. El probe instalado hijo no lleva instrumentación de cobertura.

Fuentes actuales coinciden con snapshot de adjudicación; congelación y copias previas a la suite en sources-before.json/source-copies. Cotejo final sin deriva. Los dos tests antiguos del paquete son byte y AST idénticos a preimágenes: asserts, decoradores, parámetros y funciones intactos. Protección de locks/config/producto en protected-match.json. No se congela todo scripts/ ni se atribuye el trabajo Linux disjunto a audio.

FFmpeg Windows real: ZIP coincide en SHA y tamaño con lock; binario coincide con entrada del ZIP. Version y buildconf actuales conservados, LGPL sin enable-gpl/nonfree, lame/soxr presentes. Sin descarga ni Linux ejecutado. Tests reales de API por defecto y root explícito verifican outputs/loudness/picos/preservación. Guards anteriores a lectura/FFmpeg, destino existente y reemplazos se validan. Cuatro junctions nativas PASS; cuatro symlinks SKIP por privilegio. Reemplazos usan callbacks controlados y rename real; no prueban concurrencia arbitraria ni custodia TOCTOU completa.

Schema empaquetado byte idéntico al canónico; importlib.resources, wheel y sdist actuales comprobados. Hatchling y dependencias existentes cacheadas de lectura, sin nuevos paquetes ni red. Instalación de este paquete únicamente con uv offline/no-deps/no-cache --target privado. Probe fuera checkout valida manifest válido, rechaza inválido, escribe/verifica manifiesto, ejecuta audio y comprueba torch ausente. Observer privado de solo lectura conserva dist/instalación antes del teardown en current-fixture-artifacts; hashes en current-build-installed-artifacts.json. No se sustituyen por artefactos históricos. Contenidos de dependencias cacheadas no se copiaron antes: límite de custodia del entorno, no skip silencioso.

RED históricos revisados y copiados: root ignorada produce unexpected read; manifest válido instalado falla por FileNotFoundError del recurso en checkout; destino existente lee antes de validar; reemplazos aceptan raíz cambiada o borran master ajeno. TypeError/API ausente y recurso inexistente no se cuentan como RED causal. Copias de preimágenes y logs originales históricas rotuladas, sin ejecutarlas ni alterar producto.

ledger-lint exit 0: 0 incoherencias, 1 aviso de cabecera revisión línea 965 (ajeno al componente). M1 tiene test-plan; UI/E2E y sus gates quedan fuera de esta QA. No results.json/qa-gate global fabricado ni testplan alterado. No se ejecutaron las verificaciones completas worker/E2E de T05; no cierre del hito.

Actual argv/UTC/exit/stdout/stderr y PID de hijos directos retenidos en actor-command-accounting.json, espera real con communicate. Descendientes FFmpeg/build/install/probe: PID UNKNOWN, sin prueba Jobs/árbol/cleanup. Logs internos capturados por tests no interceptados aparte; scripts/probe exactos permanecen en copia del test. No instalación compartida, host Python, GPU/UI/PDH/WSL/Ollama/Docker/red/modelos/Git/ledger/meter/docs/acceptance ni subagentes. TEMP/TMP/pycache/STUDIO_TEST_ROOT/coverage privados configurados antes de env.ps1; este sobreescribe UV_CACHE_DIR durante su carga, restaurado al privado antes del harness y ejecución de tests. No operación uv ocurrió durante esa carga.

Model/tokens/EUR/horas IA NULL. Los cuatro archivos parent-reserved no se escriben por el actor. Inventario NONCLI incluye todos los archivos privados excepto esos cuatro nombres exactos en top-level y el propio inventario. Root decide aceptación; este PASS no acredita full T05, Linux/Docker, integración worker/pipeline, M1, E2E ni música.
