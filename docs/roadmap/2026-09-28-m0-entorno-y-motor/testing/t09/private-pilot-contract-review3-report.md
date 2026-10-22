# Revisión privada R09-P3 — intento 3

A+B+D sin gaps nuevos. Historial conservado. Revisión estática de paquetes completos; no QA independiente ni calibración GPU.

## d-inline

**Lente D — sin hallazgos.** Critical: 0 · Important: 0 · Minor: 0.

Revisado íntegramente el diff aislado R09-P3 y las fuentes inline; el alcance evaluado es exclusivamente rendimiento introducido o reabierto por ese delta privado v2.

| Criterio | Resultado | Evidencia fichero:línea |
|---|---|---|
| N+1 o nuevas operaciones por elemento | ✓ | `pilot-v2.py:220–222`: cambia únicamente la condición posterior a una ejecución; no añade consultas ni bucles. |
| Bloqueos síncronos introducidos | ✓ | `pilot-v2.py:278`: espera preexistente para la cadencia de las diez muestras por fase, sin modificación en el diff. |
| Trabajo repetido con degradación relevante | ✓ | `test_pilot_v2.py:615–634`: lectura, hash y validación del fixture por caso CPU; para los 35 controles aportados no se identifica un escenario de carga con degradación material. |
| Complejidad o volumen creciente | ✓ | `test_pilot_v2.py:16–22,637–672`: directorio por caso y tres controles nuevos; ninguna expansión de la matriz ni procesamiento nuevo proporcional a jobs/eventos. |

La aceptación de `done` conserva las guardas físicas y de lifecycle posteriores; `error` y `cancelled` se rechazan antes de la fase loaded. No se exige ningún marcador opcional adicional.

**Límites:** revisión estática del paquete, sin herramientas, ejecuciones, recomputación de hashes ni QA independiente. Los 35 controles y la cobertura **173/186, cero exclusiones**, son evidencia aportada del módulo completo, no cobertura del diff ni medición de rendimiento. Se preservan las revisiones anteriores; no se amplía la revisión a los 415 archivos del inventario ni a OpenAPI/interoperabilidad.

T-09/M0 continúa abierto, GPU4 sigue sin calibración acreditada y la calidad humana permanece pendiente. El terminal histórico se considera únicamente fixture contractual CPU.

## a-inline-supplement

**Lente A · suplemento de private review3 · R09-P3: sin hallazgos nuevos.** Se conserva el contador y los resultados previos; este dictamen se limita al delta original incluido y su evidencia complementaria.

| Criterio | Resultado y evidencia |
|---|---|
| T-09 → retirar el requisito inventado `executed` | ✓ `pilot-v2.py:221` exige únicamente terminal `done`. `DoneData` define `artifacts`, `result` y `telemetry`, sin `executed` (`packages/engine-contract/engine_contract/__init__.py:115`). El fixture completo termina en `done` y carece de ese campo (`actual-terminal-fixture.json:89`). |
| T-09 → conservar rechazo de error/cancelación | ✓ La condición rechaza ambos antes de `proof("loaded")` (`pilot-v2.py:221`, `:241`). Los dos casos parametrizados validan su terminal con `Event` y comprueban ausencia de prueba loaded, solo diez muestras baseline y recuperación (`test_pilot_v2.py:652`). |
| T-09 → conservar controles físicos y lifecycle | ✓ El diff no altera las comprobaciones posteriores de residencia, unload, muestras, contexto ni recuperación. Permanecen en `pilot-v2.py:241`, `:262`, `:279`, `:298` y `:318`. |
| Alcance del plan y archivos | ✓ Corrección privada vinculada al benchmark T-09 (`tasks.md:401`); el delta modifica la copia v2 y sus pruebas, sin cambiar producción ni `/v1`. El `scope.json` amplio aporta contexto, pero no demuestra por sí solo el alcance de estos archivos privados. |
| Tests correspondientes al cambio | ✓ Lectura de la regresión positiva y los dos casos negativos (`test_pilot_v2.py:637`, `:652`). RED muestra el rechazo por `executed` (`red-regression.stdout.txt:100`); el recibo declara 35 pruebas y suite final con exit 0 (`receipt.json:15`, `:69`). |
| Cobertura | ✓ Evidencia aportada: **173/186 = 93,01 % del módulo completo**, cero exclusiones (`final-coverage.json:1`). No es porcentaje de cobertura del diff ni medición independiente. |
| Constitución | ✓ Sin violación nueva identificada: se elimina una exigencia ajena al contrato, preservando el terminal único (`docs/CONSTITUTION.md:19`); los temporales nuevos quedan dentro del proyecto (`:25`); T-09 permanece abierta (`:33`). |
| Verificación de tareas cerradas | No aplica al cierre: T-09 figura `en-progreso` (`tasks.md:395`). No se acredita aquí su Verificación de matriz (`:403`). |
| Generados/descripciones e interop | No aplica: el delta no modifica contratos ni `commands/`, `agents/` o `hooks/`. |
| OpenAPI | No aplica: ninguna spec OpenAPI cambia en el delta. |

**Precisión sobre la premisa:** `validate_events` comprueba secuencia, identidad del job y terminal único al final (`benchmark_evidence.py:48`); **no llama a `Event.model_validate`**. `execute_run` utiliza esa validación de secuencia y terminal (`benchmark_runner.py:33`, `:148`, `:177`). La validación tipada del fixture sí está explícita en `test_pilot_v2.py:629`. Por tanto, no atribuyo al runner una validación tipada que el paquete no demuestra. Esta distinción no aporta un defecto nuevo de conformidad al retirar `executed`.

T-09 → criterios de aceptación generales:

| Criterio del ledger | Estado acreditado aquí |
|---|---|
| Matriz completa de configuraciones y duraciones (`tasks.md:407`) | ✗ Pendiente |
| Comparación bind/copia y ADR condicionado (`:408`) | ✗ Pendiente |
| Descarga de Ollama y VRAM real registrada (`:409`) | ✗ Pendiente de acreditación de la medición |
| Navegador visible y observación válida (`:410`) | ✗ Pendiente; mocks CPU no acreditan calibración |
| Experimento opcional `torch.compile` (`:412`) | No acreditado; opcional |
| Recomendación argumentada con números (`:413`) | ✗ Pendiente |

Estas pendientes no son gaps nuevos del fix ni cierres indebidamente declarados.

**Gaps nuevos: Critical 0 · Important 0 · Minor 0.** Evaluación exclusivamente estática del paquete inline. Sin herramientas, comandos, tests nuevos, recomputación de hashes ni QA independiente. GPU4 sigue sin calibración acreditada; matriz, escucha humana, calidad musical y cierre M0 permanecen pendientes.

## b-inline-supplement

**Lente B · suplemento de private review3 · R09-P3: sin defectos nuevos.** Critical: 0 · Important: 0 · Minor: 0. Se preservan los resultados anteriores, sin reiniciar el contador.

| Criterio | Resultado | Evidencia del paquete |
|---|---|---|
| Aceptar `done` sin exigir `executed` | ✓ | `pilot-v2.py:220–222`; `DoneData`, `engine_contract/__init__.py:115–118`, no define ese campo. El fixture completo contiene `done` sin él. |
| Mantener identidad, secuencia y terminal único | ✓ | `benchmark_evidence.py:48–60`; llamadas desde `benchmark_runner.py:33–35,148,177–180`. |
| Rechazar `error` y `cancelled` antes de observar loaded | ✓ | `pilot-v2.py:221–222`; controles tipados en `test_pilot_v2.py:652–672`. |
| Conservar comprobaciones físicas y recuperación | ✓ | El diff mantiene las guardas posteriores de `pilot-v2.py:241–279` y la recuperación de `318–365`. |
| Usar el terminal histórico como fixture contractual | ✓ | `test_pilot_v2.py:615–634,637–649`: valida el payload; lifecycle y sensores siguen simulados. |

**Precisión sobre la premisa:** `validate_events` valida identidad, secuencia y unicidad/posición del terminal; **no llama a `Event.model_validate` ni valida su cuerpo tipado**. La validación tipada del fixture sí aparece explícitamente en `test_pilot_v2.py:629–630`. Esta distinción no demuestra una regresión causada por retirar `executed`, que tampoco validaba el cuerpo contractual.

Evalué estáticamente todas las líneas suministradas del diff y archivos, limitando los hallazgos al delta R09-P3. No ejecuté herramientas, comandos ni tests, ni recalculé hashes. Los 35 controles y la cobertura 173/186, sin exclusiones, son evidencia aportada del módulo completo, no cobertura del diff ni QA independiente.

T-09 y M0 permanecen abiertos: GPU4 no queda calibrado por esta revisión; matriz real, observaciones físicas y evaluación humana de calidad siguen pendientes.

