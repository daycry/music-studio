# T-16 — integración CPU antes de la comparación musical

Fecha: 2026-10-06. Base: `ef66a36bedf08fb996f88ef6cb9633b5f51f13b8`. T-16 sigue en progreso: estos resultados no cierran la comparación GPU ni acreditan calidad musical.

## Implementación y controles

El [informe del implementer](cpu-implementation-report.md) registra 13 grupos RED previos a los cambios de producción, 41 pruebas declaradas verdes y 271 pruebas dirigidas verdes, un skip y cinco avisos. La cobertura oficial añadida es 59/63 = 93,65 %, con mínimo del diff por archivo de 19/22 = 86,36 %. El mínimo de archivos completos es 88,34 %; son medidas distintas. [JSON oficial](implementation-coverage.json).

Descriptor, adaptador, CLI, progreso y recibos mantienen identidad y controles coherentes: Turbo por defecto ocho pasos; SFT cincuenta y CFG7. El [ADR-0027](../../../../decisiones/ADR-0027-controles-de-inferencia-sft.md) explica por qué se necesitan seis tomas nuevas emparejadas y por qué los Turbo antiguos son referencias históricas.

## Imagen e integración nativa

Imagen nueva `music-studio/engine-acestep:m0-t16-controls`, ID `sha256:9e4fc86fe17269ef80ad6649d9f80b02f8d1f0c7af160f3f9d0fde362dfd8f84`. Build local exit 0 con dependencias y revisiones fijadas, sin descargar pesos ni cambiar locks. La etiqueta de servicio anterior no se ha sustituido todavía.

La suite de la imagen ejecutó `pytest tests /studio/apps/engines/common/tests -q -m 'not gpu'` con CUDA oculta, sin `--gpus`: **156 passed, 1 deselected, 5 warnings in 27.95s**, exit 0. Logs privados: `.cache/dev-cycle/t16/resumed/docker-build.txt` y `container-tests.txt`.

El probe sobre el upstream fijado y los tokenizadores locales ejecutó **19 casos**, 13 admitidos y seis bloqueados: los 16 casos de T-19 más SFT50, SFT35/CFG5 y Turbo4. Los 13 recibos nativos pasan el validador del host sin modificar sus bytes. [Recibo público](native-integrated-receipt.json). Los controles Turbo/SFT comparados tienen idénticos presupuestos y hashes de tokens LM/DiT e idéntica metadata LM. No se carga ningún peso musical ni se ejecuta inferencia GPU.

## Causa de los fallos del doble de integración

Los intentos fallidos se conservan en caché; no se presentan como verdes. El primero no encontraba adapter porque faltaba el PYTHONPATH de la imagen. Después, el doble DiT omitía parámetros explícitos de pasos/CFG: `inference.py` del upstream, líneas 886–890, filtra argumentos por `inspect.signature`, incluso si el doble admite `**kwargs`. El observador de depuración también cambiaba esa firma. Se aisló el filtro en la fuente fijada y se corrigió solo el probe efímero: parámetros explícitos y `@wraps` en el observador. No se relajó validación ni se cambió producción para hacer pasar el doble. El último probe registra 19 casos conformes, exit 0, en `native-probe-final.txt`.

## API HTTP aislada

Dos contenedores CPU efímeros de la imagen nueva, uno por checkpoint, comprobaron catálogo con identidad/límites Turbo y SFT, estimaciones default/override válidas, diez rechazos por motor en estimate/jobs y rechazo de identidad cruzada. No se envió ningún job válido ni hubo load. Las entradas LM/DiT de los defaults vuelven a coincidir. Ambos contenedores quedaron idle/sin modelo/job y se retiraron. [Recibo HTTP](http-controls-receipt.json).

La sonda de memoria usa el `CpuGpu` existente mediante factory efímera; sus ceros son sintéticos, no medición NVML ni telemetría GPU. El intento inicial con la factory normal falló health500 porque ese contenedor deliberadamente no exponía GPU/NVML; su log `http-turbo.txt` se conserva. Se cambió solo la factory del probe, sin habilitar GPU ni alterar producción. Los logs conformes `http-cpu-turbo.txt` y `http-cpu-sft.txt` permanecen privados.

## Verificaciones y alcance pendiente

En el host: `scripts/export_contracts.py --check` → `engine-v1.json up to date`; `scripts/verify_manifest.py packages/contracts/examples/` → `all valid (4 manifests)`; Ruff global → `All checks passed!`; `git diff --check` → exit 0. Entorno cargado con `scripts/env.ps1`; comandos mediante `uv run --frozen`.

La captura DiT corresponde a la frontera de entrada. Turbo recibe CFG7 allí, pero el handler fijado lo fuerza internamente a 1; no se afirma CFG7 efectivo en su sampler. SFT utiliza CFG7. Faltan revisión adversarial fresca, QA independiente, servicio GPU con la imagen nueva, seis tomas GPU, telemetría/descarga y escucha privada. Sin ganador, aprobación artística ni cierre de M0.
