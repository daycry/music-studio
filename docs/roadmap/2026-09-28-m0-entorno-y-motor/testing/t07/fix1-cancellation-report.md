# T-07 — fix1 de cancelación tras revisión B1

Fecha: 2026-10-05. Se corrigió exclusivamente B1 Important de `testing/t07/review-attempt1.md`. Ownership de código: `scripts/generate.py`, `tests/test_generate.py`. Se conservaron informes previos, publicación y toma privada. Sin cambios de dependencias, contrato, engine común, documentos, ledger, Git ni GPU. No se ejecutó replay ni generación nueva.

## Verificación del señalamiento y RED

B1 era correcto: DELETE devuelve antes de que el trabajo termine, mientras unload requiere que no haya un trabajo activo. El finally anterior hacía ambos seguidos; el 409 de unload sustituía KeyboardInterrupt.

La regresión usa `create_mock_app(stage_delay_ms=1000)` real, token sintético, directorio temporal propio y una interrupción al abrir el stream de eventos después de aceptar el trabajo. Ejecuta `main` y comprueba exit 130 más estado idle/loaded=None antes de cerrar el TestClient.

```
. ./scripts/env.ps1
uv run --no-sync --all-packages pytest tests/test_generate.py::test_ctrl_c_during_loading_waits_for_unload -q --tb=short -p no:cacheprovider
assert m.main([]) == 130
AssertionError: assert 1 == 130
stderr: Error: ENGINE_HTTP_409
1 failed, 1 warning in 0.79s
exit 1
```

RED: `tests/test_generate.py::test_ctrl_c_during_loading_waits_for_unload` falló con `assert 1 == 130`, stderr `ENGINE_HTTP_409` · 2026-10-05.

Después del primer cambio de limpieza, esa misma regresión pasó: `1 passed, 2 warnings in 0.87s`, exit 0.

La ampliación del plazo también tiene rojo observado, eliminando la versión provisional de diez segundos antes de escribir el plazo definitivo. El reloj es sintético; la carga finaliza a los veinte segundos simulados, sin esperar veinte segundos reales:

```
uv run --no-sync --all-packages pytest tests/test_generate.py::test_cleanup_waits_beyond_ten_seconds -q --tb=short -p no:cacheprovider
ValueError: ENGINE_CLEANUP_TIMEOUT
1 failed, 1 warning in 0.37s
exit 1
```

RED: `tests/test_generate.py::test_cleanup_waits_beyond_ten_seconds` falló con `ENGINE_CLEANUP_TIMEOUT` con el plazo provisional de diez segundos · 2026-10-05.

GREEN después del plazo definitivo: el mismo comando dio `1 passed, 1 warning in 0.31s`, exit 0.

## Cambio mínimo

`finish_job` usa el contrato existente: consulta el estado del job propio y health, solicita cancelación si aún no es terminal, espera terminal e idle y solo entonces intenta unload. Confirma después por contrato `idle`, sin job activo y `loaded=None`. Una respuesta exitosa de unload por sí sola no se presenta como descarga acreditada.

Plazo máximo de limpieza 300 s, con reloj monotónico. Cada petición HTTP usa timeout de hasta cinco segundos o el tiempo restante menor; cada espera de polling es de hasta 0,1 s y nunca supera el tiempo restante. El deadline se comprueba antes y después de cada petición. Los timeouts HTTP son por fases de transporte de httpx; una llamada en curso queda limitada por esos timeouts, y se rechaza su resultado si ya superó el deadline. No se lanzan hilos ni peticiones sin límite.

Tras solicitar cancelación, el CLI muestra `Cancelación solicitada; esperando la liberación del engine.`. Durante una carga ACE-Step, la cancelación cooperativa puede tener que esperar a que concluya esa carga. Si se alcanza el plazo, falla un transporte o no se puede confirmar descarga, se muestra solamente `Aviso: ENGINE_CLEANUP_UNCONFIRMED` y se añade esa nota a la excepción primaria, sin sustituirla. Así Ctrl+C sigue produciendo exit 130; otros errores conservan exactamente su objeto y causa. No se atribuye la limpieza fallida a una avería de GPU.

Si el job desaparece, cambia de ID, health muestra otro job activo o el modelo cargado difiere, no se fuerza unload ni se cancela un trabajo ajeno. Un 409 al intentar unload tras observar idle se reevalúa mediante estado/health, dentro del mismo plazo. Una descarga que responde éxito pero sigue mostrando loaded se considera no acreditada.

La misma espera/confirmación se aplica al paso de descarga del camino de éxito, conservando el orden descarga → postproceso CPU → publicación. No cambia audio, procedencia ni lógica de publicación.

## Pruebas de regresión

- Ctrl+C durante loading con mock real: exit 130 y loaded=None antes de cerrar la app.
- Fallos de transporte en cancelación, fallo HTTP de unload y desaparición del job: preservación por identidad de KeyboardInterrupt y ValueError, nota y aviso sanitizados; no descarga ajena.
- Reloj sintético: carga de veinte segundos, plazo máximo de trescientos segundos, una sola solicitud DELETE, timeouts HTTP acotados y polling sin bloqueo real.
- Job/modelo ajeno: sin operaciones DELETE/POST destructivas.
- 409 de unload: reevaluación y descarga posterior; unload que no acredita loaded=None: error seguro.
- Integraciones mock/FFmpeg/post/manifiesto y regresiones de publicación Windows continúan verdes.

Los fakes históricos ahora representan estados reales loading → done/cancelled → idle y loaded → None al recibir unload. Se conservaron sus escenarios y aserciones originales. No se esperó un plazo de trescientos segundos real.

## Verificación final ejecutada

```
. ./scripts/env.ps1
Python 3.12.14 gestionado

uv run --no-sync ruff check scripts/generate.py tests/test_generate.py
All checks passed!
exit 0

uv run --no-sync ruff format --check scripts/generate.py tests/test_generate.py
2 files already formatted
exit 0

$env:COVERAGE_FILE = '.cache/dev-cycle/t07/fix1-cancellation.coverage'
uv run --no-sync --all-packages pytest tests/test_generate.py -q --tb=short -p no:cacheprovider --cov=scripts --cov-report=json:.cache/dev-cycle/t07/fix1-cancellation-coverage.json --cov-report=term-missing
scripts/generate.py: 304/324 statements = 93,83 %
Coverage JSON written to file .cache/dev-cycle/t07/fix1-cancellation-coverage.json
63 passed, 6 warnings in 5.95s
exit 0

uv run --no-sync --all-packages pytest -m 'not gpu' -q --tb=short -p no:cacheprovider
189 passed, 6 warnings in 16.93s
exit 0
```

Cobertura del código cambiado superior al 80 %. El total global de scripts incluye herramientas históricas fuera de esta corrección. Warnings: una opción cache_dir desconocida al desactivar cacheprovider y cinco avisos de Starlette por el argumento timeout con TestClient, que no simula límites de transporte reales. Los plazos y límites se ejercitan por reloj sintético y argumentos HTTP; no se simula una red realmente bloqueada durante trescientos segundos.

La escucha del propietario y el cierre de T-07 siguen a cargo de root. La entrega deja B1 corregido para revisión fresca intento 2; no declara QA independiente ni una nueva prueba GPU.

DONE
