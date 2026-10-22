# T-08 — revisión intento 2: tres Important pendientes

Fecha: 2026-10-06. A, B y C ejecutadas con contexto fresco, independientes de implementar. C pudo despacharse después de terminar A; los primeros despachos C/followup fueron rechazados por límite de threads. No se sustituyó un proceso vivo por un timeout. D=false por selector. Snapshot: [19 fuentes fix1](fix1-delivery-receipt.json), imagen80eee31.

| Criterio | Veredicto |
|---|---|
| Base, dependencias, puerto, montajes, token y beats | Conforme implementación CPU; inferencia requerida pendiente |
| R-CLAP-01/02, texto completo, ventana y rechazo de exceso | Corregidos CPU; extractor/tokenizer reales, embeddings doble |
| Loaders, recursos, salida cruda, residencia y secuencia | Conformes en alcance CPU; memoria e inferencia GPU pendientes |
| Tiempos para toda duración admitida | **No conforme: B-LONG-01** |
| Clasificación de entradas inválidas | **No conforme: B-INPUT-01** |
| Alcance, constitución, TDD y cobertura | Conformes en el diff; task en-progreso y CA abiertas |
| Documentación del motor ejecutado | **No conforme: A-T08-DOC-01** |
| Seguridad introducida/reabierta | C: sin hallazgos, con límites CPU explícitos |
| Generados, interop, OpenAPI | N/a: sin cambios de contratos/commands/agents/hooks |
| Verificación completa, QA y cierre | No acreditados, pendientes explícitos |

| ID | Grado | Gap | Evidencia y escenario | Veredicto |
|---|---|---|---|---|
| A-T08-DOC-01 | Important | README58/68 usa imagen histórica en comandos CPU | Compose construye/ejecuta fix1, pero comandos `docker run` siguen m0-t08/37e9355, con CLAP roto y sin regresión nueva | Aceptado, pendiente fix2 |
| B-LONG-01 | Important | backend254/adapter97 alinean audio completo sin segmentar | Se aceptan600s. Config fijado tiene5000 clases de80ms, máximo399,92s. Probe CPU adapter→backend→ForcedAligner.align/parse real entrega450s y publica palabra399,92s; una palabra420s no es representable. Upstream usa segmentos180s para timestamps | Aceptado, pendiente fix2 |
| B-INPUT-01 | Important | backend236/247 y descriptor67 dejan errores de entrada como INTERNAL | Worker real con language="not-a-language" o archivo declarado WAV/hash válido de bytes no decodificables devuelve INTERNAL por ValueError/LibsndfileError | Aceptado, pendiente fix2 |

El orquestador acepta los escenarios como defectos de requisitos/corrección; no son preferencias de estilo. R-CLAP-01/02 quedan corregidos CPU, sin reabrirlos. Los tres Important nuevos obligan corrección antes de QA/cierre.

## Evidencia y límites

A leyó el diff dividido por archivos, comprobó19SHA de fuentes y12de evidencias, XML RED/GREEN, cobertura309/34390,09 % y lock111; AST conforme. No volvió a ejecutar suites. Verificación GPU/QA no acreditadas. Su gap documental corresponde a comandos vigentes del README, no a recibos históricos.

B comprobó19SHA y config fijado del alineador, leyó loaders y orquestación, y ejecutó en la imagen80eee31 la suite CPU:33passed/4deselected/1aviso en4,08s. El probe temporal ejecutó la rama productiva y align/parse upstream reales, con ASR, processor y logits dobles; demuestra rango/consumo por la rama, **no precisión de inferencia**. El artefacto se creó y validate_words aceptó399,92s. Los probes de entrada pasaron por el worker real. CUDA_INITIALIZED=False; sin pesos ni GPU. Los probes fueron evidencia de la sesión de herramientas del revisor, no archivos nuevos escritos por este.

C comprobó19SHA, AST de14Python sin ejecución dinámica, lock111paquetes/512artefactosHTTPS+SHA y tres commitsGit. Probes HTTP en memoria: token ausente/incorrecto401, válido200; dos rutas externas rechazadas con INVALID_PARAMS antes del backend. Padre sin torch/child; sin escrituras, Docker ni repetir suites. No encontró vulnerabilidades introducidas/reabiertas; no es auditoría universal ni QA. `.eval()` corresponde a métodos de modelos.

## Corrección siguiente

Fix2 debe conservar transcripción hasta600s, dividir el audio reconocido en segmentos compatibles, asociar texto/idioma reconocido a su propio fragmento y recomponer tiempos con offsets reales. Mantener descarga ASR antes de cargar alineador y una sola residencia. No repartir texto completo por heurística ni suministrar letra esperada. Clasificar idioma/audio inválidos como INVALID_PARAMS sin ocultar errores internos o de VRAM. Actualizar comandos vigentes sin alterar antecedentes históricos. RED previo por defecto, nuevas fuentes/imagen/recibos; revisión3 conserva esta tabla y reevalúa cambios sin reabrir conformidades salvo evidencia nueva. T-08/M0 siguen abiertos.
