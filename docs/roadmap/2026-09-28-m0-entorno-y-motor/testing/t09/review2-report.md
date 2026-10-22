# Revisión adversarial T-09 CPU — intento 2

Resultado: **0 Critical, 2 Important pendientes, 0 Minor**. Los dos casos residuales de R09-04 tienen causas distintas: bloqueo dentro del parser HTTP y presupuesto del muestreo después del sensor. No se pasa a QA ni GPU. T-09 permanece en-progreso y conserva abiertos los criterios del benchmark real.

Cuatro revisores de contexto fresco (A/B/C/D), todos de solo lectura. Diff de corrección de ocho archivos, 53152 bytes, SHA `85e2efafd71cd418b589683c9f3bd80b3acd7b11e6e767b62e19d50c3f9f580b`; las 32 fuentes congeladas siguen intactas. Scope-check exit0, sin avisos ni exclusiones. El diff completo aislado conserva 214245 bytes y SHA `662e32296b1ea051a3a2d1e06c01a5390ad249b18a22e3297252b8a179a3e361`. Ningún diff global mezclado con T-08/T-16 fue usado.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Duración, baseline, copia/amortización/dispersión | ✓ | A/B confirman las correcciones y regresiones de fix1 |
| Cleanup/resume sin duplicados y carga cold/warm | ✓ | A/B confirman estados duraderos y agregación |
| Captura efectiva, CFG y metadatos | ✓ con límite | Se preserva el rebate parcial R09-07 explicado debajo |
| Flujo continuo sin monopolizar el observador | ✓ parcial | D: 51 eventos en 2,578 s, tres muestras, intervalos 1,016/1,000 s |
| Plazo HTTP incluyendo parser chunked | ✗ | R09-04a, caso válido adicional encontrado por B |
| Cadencia incluyendo el tiempo del sensor | ✗ | R09-04b, reproducción de D |
| Seguridad del diff | ✓ | C sin hallazgos; ownership, rutas y token conservados |
| Coste de informes y recuperación para 160 jobs | ✓ | D sin degradación significativa adicional |
| Cobertura y TDD de fix1 | ✓ | 13 RED, suite243; media oficial de 15 archivos 86,8137 %, no cobertura de líneas del diff |
| Runtime GPU/XL/RTF/calidad musical | Pendiente | Esta revisión CPU no acredita ejecución ni calidad |

| # | Grado | Lente | Fichero:línea | Gap | Escenario / evidencia | Veredicto |
|---|---|---|---|---|---|---|
| R09-04a | Important | B2 | `scripts/eval/benchmark_runtime.py:94` | El parser chunked puede superar el plazo global | HTTPResponse válido: cabecera de chunk 36\r\n enviada byte a byte cada 25 ms. Un presupuesto de 40 ms devuelve done tras aproximadamente 109 ms. read1 llama internamente a readline y efectúa varias lecturas con timeout de inactividad; el límite externo no las interrumpe. | pendiente |
| R09-04b | Important | D2 | `scripts/eval/benchmark_runner.py:119` | El presupuesto del stream no descuenta el coste del sensor | Observación CPU de 4 s, intervalo de 1 s y sensor síncrono de 0,5 s: tres muestras, intervalos 1,500/1,500 s. Concede otro segundo al stream después del sensor. La latencia real de los sensores no se ha medido; el caso sintético demuestra el defecto de programación. | pendiente |

| Hallazgo anterior | Veredicto en intento 2 |
|---|---|
| R09-01 | corregido: duración solicitada validada con tolerancia nativa 1921/48000 s |
| R09-02 | corregido: baseline real publicado, sin inventar observaciones ausentes |
| R09-03 | corregido: copia, amortización y dispersión publicadas por separado |
| R09-04 | parcial: quedan R09-04a y R09-04b |
| R09-05 | corregido: recibo duradero de cleanup y resume sin duplicar jobs |
| R09-06 | corregido: carga cold separada de warm |
| R09-07 | corregido para CFG/metadatos/formato; subcaso SHA64hex descartado (rebatido) |

Arbitraje R09-07 preservado: un hash DiT válido de 64 caracteres no se puede reconstruir del recibo sin la preimagen de kwargs dinámicos y códigos LM. El adapter valida controles antes de inferir y registra su hash real (`adapter.py:269–294`); `preflight.py:228–255` registra parámetros planificados. El subcaso de reconstrucción SHA64hex se mantiene **descartado (rebatido)**; sí se verifican CFG, metadatos, formato y procedencia. No demuestra un fallo de inferencia ni permite inventar una preimagen.

Ejecuciones de los revisores: A39 passed/7,83 s; B39 passed/8,05 s; C13 passed/0,94 s; D16 passed/0,41 s. Los conjuntos se solapan y no se suman. B reprodujo la cabecera chunked válida en memoria con HTTPResponse; D reprodujo tanto el flujo original como el coste sintético del sensor. Sin GPU, Docker, red, pesos, audio, mapa ciego ni lectura de conocimiento ajeno.

Diagnóstico sistemático: se aplica `debug-root-cause` fuera del gancho de tres rojos de QA. El siguiente implementer debe archivar reproducción mínima, controles y prueba de cada hipótesis antes del código; después, RED/GREEN y suite. Un chequeo del reloj tras read1 que siga permitiendo bloquear no corrige la causa. La evidencia se conserva aquí y en el ledger: no se escribe gotcha/memoria en docs/knowledge por ownership ajeno explícito. TDD n/a: publicación de este informe.
