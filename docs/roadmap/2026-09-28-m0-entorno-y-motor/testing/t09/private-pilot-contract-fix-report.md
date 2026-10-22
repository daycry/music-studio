# R09-P3 — piloto privado v2 (CPU)

## Fase 1 — reproducción
RED: test_pilot_v2.py::test_typed_actual_done_without_flag_reaches_lifecycle falló con ValueError: pilot_job_not_done · 2026-10-07.
Comando/UTC/exit/stdout originales: red-regression.command.json y red-regression.stdout.txt. Exit 1, un fallo. Primer intento red.command.json: error de importación del plugin, no RED válido.

## Fase 2 — aislamiento
Event y DoneData validan el terminal íntegro GPU4 sin executed. La copia exacta del terminal tiene SHA d48086b5737c3244c30a1a2ab65dd1d64bf52da268498718e78dc5c801ad96b9; originales, contrato, test previo y copia baseline están sellados en provenance.json.
Fallo acotado a pilot-v2.py:221 (copia baseline de v1): exige un campo ausente del contrato. Se descartan payload inválido e import roto como causa del RED válido. Las guardas físicas posteriores no causan este fallo: aún no se ejecutaron.

## Fase 3 — hipótesis probada
«El piloto rechaza un terminal done válido porque exige data.executed=True, campo que DoneData no define». La regresión validó el payload real completo y ejecutó el piloto baseline con mocks CPU; falló exactamente en esa condición. No se ejecutaron procesos reales ni llamadas de red dentro de los tests.

## Fase 4 — fix y verificación
pilot.diff contiene un único cambio de condición: conservar type != done y retirar la exigencia de executed. execute_run ya valida eventos; se mantienen sin cambios health-loaded, unload, contexto, hash, baseline, umbrales, sensores, validación y recuperación/ownership.
tests.diff conserva los 32 controles y adapta SOURCE al laboratorio v2. Sustituye el done inventado por el terminal real validado; añade la regresión y dos terminales tipados error/cancelled que deben rechazarse antes de las muestras loaded.
GREEN individual: 1 passed. Suite dedicada final: 35 passed. Cobertura oficial módulo completo: 173/186 = 93,01075268817205 %, cero líneas excluidas. private.coverage, coverage.rc, final-junit.xml y final-coverage.json son propios de esta fase. Ruff py312 y format --check: exit 0; comandos completos y salidas preservados.

## Custodia y límites
custody-before.json/custody-after.json cotejan todos los protegidos, fuentes67 y documentos12 con sus freezes; todos coinciden. Incluyen originales privados, fallidos y datos enumerados; no se regeneró audio ni se tocó root .coverage. evidence-seals.json no incluye temporales ni pytest-cache.
Todas las observaciones de lifecycle/sensores de la suite son CPU sintéticas. El terminal GPU4 se usa solo como fixture contractual: no acredita fases loaded/unloaded, calibración, prerequisitos reales, matriz160, calidad ni cierre M0. Revisión/QA independiente y plan nuevo con observaciones reales quedan al orquestador.
Incidencia de alcance: el RED válido heredó tmp_path global y escribió .cache/pytest-tmp/e04d821fffdc4ef8a1705d88092301fd pese a --basetemp; se preservó sin borrar. Las ejecuciones siguientes usan fixture local dentro de esta fase. Incidencias de importación y Ruff por target previo quedan en receipt.json.
No se escribe gotcha: la autorización explícita prohíbe knowledge/memoria. Costes, tokens y esfuerzo IA desconocidos; medidor propiedad del root. No ledger, Git, GPU, Docker, WSL, UI, red, instalaciones, modelos, subagentes ni cambios de producto.

DONE_CPU_WITH_CONCERNS
