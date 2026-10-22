# Revisión adversarial T-09 CPU — intento 1

Resultado: **0 Critical, 7 Important pendientes, 0 Minor** después de deduplicar A1/B3 y B1/D1. Lentes A+B+C+D. No se pasa a QA ni GPU hasta corregir y revalidar los Important. T-09 sigue en-progreso, todos los criterios GPU abiertos.

Se revisó íntegramente el diff aislado de 31 archivos (32 en el recibo: uno sin cambio), 5519 líneas, 183012 bytes, SHA `84a047145d748dc4953a2592744467940ffbd76ba728dc917070599eb29d82b6`. Las 32 fuentes siguen intactas. Scope-check exit0, sin avisos ni exclusiones de usuario. Ledger-lint0/6avisos futuros. A/B/C fueron despachos de contexto fresco respecto de implementación. D reutilizó el contexto de C porque el runtime rechazó otro thread; permaneció independiente de implementación y de resultados A/B. Esta limitación se registra, no se presenta como cuatro contextos nuevos.

| Criterio | Veredicto CPU | Evidencia |
|---|---|---|
| Matriz íntegra5perfiles×4duraciones×2brazos×cold+3warm | ✓ | benchmark_plan y pruebas de160intentos; ejecuciónreal pendiente |
| Duración real frente a solicitada | ✗ | R09-01 |
| Bind/copia equivalentes, hashes, raíces, delta>30s requiereADR | ✓ | benchmark_storage/benchmark y tests |
| Informe de copia/amortización/dispersión | ✗ | R09-03 |
| Ollama/umbralVRAM preflightCPU y restauración | ✓ | benchmark_runtime/benchmark y pruebas; GPUreal pendiente |
| VRAM en reposo publicada | ✗ | R09-02 |
| DXGI/LUID, fuentes separadas y muestreo bajo eventos | ✗ | MappingCPU conforme; cadencia fallaR09-04 |
| Resume tras cleanup por error | ✗ | R09-05 |
| Recomendación operacional y carga mediana | ✗ | Matriz incompleta no recomienda; agregacióncarga fallaR09-06 |
| Validación de captura | ✗ | R09-07; guardas previas actuales rechazan cambios antes de inferir |
| Cobertura oficial y TDD de entrega | ✓ | Media15archivos85,33%, mínimoindividual54,067%; parserplugin confirma media, 26RED/GREEN223 |
| Constitución/contrato aditivo/artefactos generados | ✓ | Sin violación explícita hallada; engine-v1.json up to date, exportcheckexit0 |
| Interop commands/agents/hooks y OpenAPI | n/a | Sin cambios de esas piezas en diff aislado |
| RuntimeGPU/INT8fit/navegador/calibraciónTaskManager/RTF real/calidad | No verificable | Todos pendientes expresamente; CPU no los acredita |

| # | Grado | Lentes | Fichero:línea | Gap | Escenario / evidencia | Veredicto |
|---|---|---|---|---|---|---|
| R09-01 | Important | A1/B3 | scripts/eval/benchmark_runner.py:297 | Duración solicitada no validada | Solicitud30s, WAV8frames/48k y telemetría concordante pasan output/fidelity/row valid con duración real0,0001666667s. | pendiente |
| R09-02 | Important | A2 | scripts/eval/benchmark_evidence.py:170 | VRAM en reposo ausente del informe | Baseline1497,123MiB existe en plan privado pero no aparece en Markdown canónico, pese a CA3. | pendiente |
| R09-03 | Important | A3 | scripts/eval/benchmark_evidence.py:167 | Copia, amortización y dispersión omitidas | copy_s12345,678 desaparece del informe; falta amortización bind/copia y dispersión previstas por diseño§5.6/§5.9. | pendiente |
| R09-04 | Important | B1/D1 | scripts/eval/benchmark_runtime.py:56 | Stream bloquea muestreo periódico | 51eventos en2,516s producen1muestra con interval_s1. La inactividad no limita duración de llamada. SFT50pasos×0,8s daría1frente≈40muestras (escenario, noGPUmedido). | pendiente |
| R09-05 | Important | B2 | scripts/eval/benchmark.py:365 | Cleanup por error rompe resume | Error health transitorio elimina contenedor sin cleanup.json; resume inspeccionaIDeliminado y fallaDOCKER_ACTION_FAILED después deTRANSPORT_UNAVAILABLE. | pendiente |
| R09-06 | Important | B4 | scripts/eval/benchmark_evidence.py:141 | Carga cold mezclada con warm sin carga | 8cold×31s+24warm×0s producen recomendación carga mediana0,000s pese a mediana cold31s. | pendiente |
| R09-07 | Important | B5 | scripts/eval/benchmark_runner.py:367 | Verificador acepta captura contradictoria | Recibos rehasheados con guidance_scale1frenteCFG7, metadataLMduración300frente30 o arguments_sha256DiTincorrecto pasan fidelity_valid. La captura actualrechaza esos parámetros conINVALID_PARAMS: fallo del verificador, no prueba de inferencia incorrecta. | pendiente |

Evidencia ejecutada por revisores, sin GPU/red/Docker: A45passed/1aviso7,02s y exportcheck0; B18passed más reproducciones de stream/cleanup/duración/agregación/recibos; C18passed/1aviso y guardas de rutas/pesos/ownership/token; D20passed/1aviso y stream51eventos/2,516s/1muestra. Los conjuntos se solapan: no sumarlos como tests distintos. El aviso cache_dir con caché desactivada es conocido.

Arbitraje del orquestador: los siete escenarios corresponden al código actual y al diseño. R09-07 se acepta con alcance limitado a la honestidad del verificador; no demuestra que la generación ignore CFG o duración. Reproducciones de revisión no son RED del fix: el implementer debe añadir regresiones, ejecutar el fallo antes del código y devolver nuevos GREEN/freeze. Nada de memoria/conocimiento ajeno, audio privado ni mapa ciego fue consultado. TDD n/a: este informe.
