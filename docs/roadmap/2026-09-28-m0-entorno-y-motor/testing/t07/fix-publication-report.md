# T-07 — corrección acotada de publicación en Windows

Fecha: 2026-10-05. Ownership: solamente `scripts/generate.py` y `tests/test_generate.py`. Se preserva la entrega original. No se tocaron la toma privada, `runtime/`, replay, dependencias, docs, ledger, Git ni GPU.

## Fase 1 — reproducción mínima

El orquestador reprodujo el fallo al renombrar la carpeta de staging: PermissionError errno 13 / WinError 5, con origen existente y destino inexistente. La misma operación pasó al añadir stat/print antes del rename, sin espera. Esa observación acota una denegación intermitente, pero NO identifica su proceso externo y NO permite atribuirla a antivirus.

La regresión usa exclusivamente fixtures sintéticas propias: contrato real /v1, artefacto mínimo con SHA-256 y escritor de manifiesto real; el audio se sustituye en este test por una fixture para aislar únicamente la publicación. `Path.rename` levanta WinError 5 en el primer intento; el segundo ejecutaría el renombrado real.

```
uv run --frozen --all-packages pytest 'tests/test_generate.py::test_publication_transient_windows_lock[5]' -q --tb=short -p no:cacheprovider
scripts/generate.py:431: in generate
    (staging / dest.name).rename(dest)
PermissionError: [WinError 5] synthetic transient publication lock
1 failed, 1 warning in 0.43s
exit 1
```

RED: `tests/test_generate.py::test_publication_transient_windows_lock[5]` falló con `PermissionError: [WinError 5] synthetic transient publication lock` · 2026-10-05.

## Fase 2 — aislamiento

La excepción ocurre tras completar postproceso/manifiesto y descargar el engine; una reproducción CPU no requiere GPU ni volver a generar audio. El test reducido falla exclusivamente en el rename. El origen sintético existe y su destino no existe. Se descarta un fallo de contrato/hash/manifiesto del test porque la ejecución llega al mismo punto de publicación tras validarlos. La creación del bloqueo externo original sigue sin identificarse.

## Fase 3 — hipótesis comprobada

Hipótesis falsable: «una denegación Windows transitoria en el primer rename aborta la publicación aunque el siguiente rename sería válido». El RED la confirma: la versión anterior hace un único rename y propaga WinError 5; la siguiente operación real, habilitada por la fixture, no se intentaba.

Después del cambio mínimo, los casos WinError 5 y 32 pasan con exactamente dos intentos y carpeta/manifiesto final presentes:

```
uv run --frozen --all-packages pytest tests/test_generate.py::test_publication_transient_windows_lock -q --tb=short -p no:cacheprovider
2 passed, 1 warning in 0.58s
exit 0
```

## Fase 4 — corrección y controles

`publish_directory` usa únicamente rename: máximo cinco intentos, pausas 0,1/0,2/0,4/0,8 s (1,5 s de espera total). Reintenta solo `os.name == nt` y `winerror` 5 o 32. Propaga errores Unix, códigos Windows distintos y denegaciones persistentes. Antes de cada intento rechaza un destino existente, incluido uno que aparezca durante una espera. No sobrescribe ni copia ficheros parcialmente; audio y procedencia no cambian.

Si falla persistentemente una variante posterior, se retiran exclusivamente las carpetas nuevas publicadas por ese intento y se limpia staging. La prueba descubrió esa publicación parcial del código previo:

```
uv run --frozen --all-packages pytest tests/test_generate.py::test_publication_persistent_lock_rolls_back_variants -q --tb=short -p no:cacheprovider
assert not list(data.glob("cli/*/*"))
AssertionError: quedó la primera variante publicada
1 failed, 1 warning in 0.40s
exit 1
```

RED: `tests/test_generate.py::test_publication_persistent_lock_rolls_back_variants` falló porque quedó la primera variante tras agotarse los reintentos de la segunda · 2026-10-05.

También se garantiza que una denegación de limpieza no sustituye el error original; se añade la nota `PUBLICATION_CLEANUP_FAILED`. No se promete borrar una carpeta cuyo sistema de archivos siga denegando su eliminación. Esta condición tuvo su propio RED:

```
uv run --frozen --all-packages pytest tests/test_generate.py::test_publication_cleanup_keeps_original_error -q --tb=short -p no:cacheprovider
assert raised.value is failure
AssertionError: OSError('synthetic staging cleanup denial') sustituyó PermissionError(... WinError 5)
1 failed, 1 warning in 0.40s
exit 1
```

RED: `tests/test_generate.py::test_publication_cleanup_keeps_original_error` falló porque el error de limpieza ocultaba el WinError 5 de publicación · 2026-10-05.

## Comprobación final

```
. ./scripts/env.ps1
Python 3.12.14 gestionado

uv run --frozen ruff check scripts/generate.py tests/test_generate.py
All checks passed!
exit 0

uv run --frozen ruff format --check scripts/generate.py tests/test_generate.py
2 files already formatted
exit 0

$env:COVERAGE_FILE = '.cache/dev-cycle/t07/fix-publication.coverage'
uv run --frozen --all-packages pytest tests/test_generate.py -q --tb=short -p no:cacheprovider --cov=scripts --cov-report=json:.cache/dev-cycle/t07/fix-publication-coverage.json --cov-report=term-missing
scripts/generate.py: 263/279 statements = 94,27 %
Coverage JSON written to file .cache/dev-cycle/t07/fix-publication-coverage.json
50 passed, 1 warning in 4.98s
exit 0

uv run --frozen --all-packages pytest -m 'not gpu' -q --tb=short -p no:cacheprovider
176 passed, 1 warning in 15.68s
exit 0
```

La advertencia es `PytestConfigWarning: Unknown config option: cache_dir` al desactivar cacheprovider frente al problema ACL previo del cache de pytest. La cobertura relevante corresponde únicamente al código cambiado `generate.py`; el total global de `scripts/` incluye herramientas históricas no ejercitadas por esta tarea.

Regresiones: bloqueo transitorio y persistente para 5/32, máximo y pausas exactas, propagación del mismo objeto de error, limpieza de variantes y staging, preservación del error original si falla la limpieza, no reintento Unix/otros códigos y destino existente/aparecido durante espera. Las integraciones sintéticas anteriores de audio-post/manifiesto siguen verdes.

## Memoria técnica — candidato para root

La skill exige registrar un gotcha tras una depuración que afecta una garantía; docs pertenecen exclusivamente al orquestador y no se modifican desde este agente. Candidato (no aprobación):

- Síntoma: WinError 5/32 en rename final puede abortar una ejecución cuyo audio y manifiesto ya se completaron.
- Causa comprobada: el publicador de un solo intento no tolera una denegación transitoria; el proceso externo concreto del incidente original es desconocido.
- Qué hacer: rename sin sobrescritura, reintento Windows 5/32 acotado, rollback de carpetas propias si falla una variante y preservación del error primario.
- Evidencia: `test_publication_transient_windows_lock`, `test_publication_persistent_lock_rolls_back_variants`, `test_publication_cleanup_keeps_original_error` y esta comprobación CPU.

Fix solicitado listo para revisión adversarial fresca. La escucha y el cierre de T-07 siguen siendo responsabilidad de root.

DONE
