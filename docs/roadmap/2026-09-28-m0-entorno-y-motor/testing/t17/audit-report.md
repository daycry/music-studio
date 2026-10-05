# Qué reciben los modelos de los prompts de las canciones

Auditoría M0/T-17, 2026-10-05. El propietario prioriza fidelidad de instrucciones antes de mejorar o cambiar modelos. Producto, pesos, contratos y generaciones anteriores permanecen intactos. SFT (T-16) vuelve a borrador.

## Resultado

La CLI y el adaptador conservan el texto que reciben. Sin embargo, **las entradas locales de Libre ya eran adaptaciones** del original de Suno. La canción completa recibió 489 caracteres de caption, frente a 867 originales; los nueve tags conservaron las secciones, pero simplificaron varias instrucciones de ejecución. Las 72 líneas cantadas/rapeadas coinciden exactamente, excluyendo cabeceras y líneas vacías.

Nuestro límite de 512 caracteres rechaza nueve de los diez prompts originales del corpus. Ampliarlo no resolvería por sí solo el problema: el text encoder del DiT limita a **256 tokens la plantilla completa de descripción y metadatos**, y cuatro de los diez originales superarían ese presupuesto. Es una reproducción CPU contrafactual: esos originales rechazados no se enviaron a una nueva generación.

Las adaptaciones actuales de Libre caben y no pierden tokens en el probe. No hay evidencia para atribuir toda su falta de naturalidad al transporte, ni para aprobar su cumplimiento artístico.

## Qué se ha comprobado

- Diez documentos del corpus aportado, cuatro entradas locales, una variante con los tags Markdown originales y un candidato privado: **16 casos**. No se generan canciones del corpus.
- Código realmente instalado: commit `dce621408bee8c31b4fcf4811682eb9359e1bc94`, comprobado en el contenedor; hashes de seis archivos coinciden con las copias auditadas.
- Dieciséis archivos de configuración/tokenizadores verificados contra el lock. Tokenizadores locales de LM0,6B y Qwen3-Embedding0,6B; no se carga ningún peso musical.
- `generate_music`, `generate_with_stop_condition`, plantillas y preparación de tokens DiT reales. Se sustituye exclusivamente la inferencia de modelos por capturas: el backend LM devuelve un código sintético y el DiT se detiene tras recibir argumentos. CUDA oculta y `torch.cuda.is_available()==False`.
- CLI real y `POST /v1/estimate` sobre el engine real. Original de Libre: **422 INVALID_PARAMS**; adaptación completa y dos captions T-15: **200**. Solo estimate/health; cero llamadas load/jobs; engine idle y unloaded antes/después.
- Treinta y dos hashes de documentos, entradas y manifiestos anteriores preservados. Los logs y textos completos permanecen privados.

La lectura de logs históricos disponibles no encontró los prompts LM completos ni las trazas de entrada DiT. **No se presenta el probe como una captura de las inferencias GPU anteriores.** Es ejecución CPU del recorrido instalado con fronteras de generación sustituidas, más comprobación HTTP sin generación.

## Recorrido y campos efectivos

`--style` → `request.params.style` → `GenerationParams.caption` → caption del LM → plantilla chat → tokens del LM. La letra usa el mismo recorrido en su campo independiente. Tras los códigos semánticos, el DiT recibe caption/letra y construye dos canales de texto: descripción/metadatos y letra/idioma.

| Campo | LM musical | DiT | Limitación actual |
|---|---|---|---|
| Caption | Texto completo de la entrada local | Mismo texto antes de tokenización | La plantilla DiT suma instrucción y metadata al presupuesto de256 |
| Letra y tags | Texto completo, incluida decoración Markdown si se proporciona | Canal Lyric con encabezado de idioma | Presupuesto de2048tokens; ningún caso auditado lo supera |
| BPM94 | Metadata estructurada | Metadata estructurada | Coincide en los probes locales |
| Duración255/90s | Metadata y límite de códigos | Duración de audio y metadata | Upstream convierte duración a entero en metadata textual; no afecta estos valores enteros |
| Español | Texto si se indica en caption/letra | `vocal_language=es` | No se añade idioma estructurado a user_metadata del LM |
| Tonalidad mayor | Preferencia textual | Preferencia textual; keyscale vacío | CLI no expone --key; no se ha inventado una tónica |
| Compás | Ausente en estas entradas | Ausente en estas entradas | CLI no lo expone; el original de Libre tampoco lo especifica |

`thinking=True` se hereda del upstream. `use_cot_caption`, `use_cot_language` y `use_cot_metas` son False. El LM **sí genera códigos musicales**; la fase de generación de metadata se salta y el prompt de códigos contiene el YAML de BPM/duración proporcionados. Ese YAML es metadata, no una prueba de razonamiento observado. El caption y la letra no se reescriben por CoT en este recorrido.

Existe otra extracción condicional upstream: si un caption lleva cabeceras SFT `# Instruction` y `# Caption`, se extrae su cuerpo hasta `# Metas`. No se dispara en los captions auditados; no puede afirmarse ausencia universal de transformaciones.

## Presupuestos medidos de Libre

El fragmento de T-14 queda trazado al control de T-15: sus archivos de caption y letra son idénticos byte a byte (caption: `bc86875aea3f663c4d28af38428f8d1b71d0b1ff2313ff1c1fa5d9854f059b7d`; letra: `421a2aaa97998b38b71db4aa939f468e4f6fb54a0b3d0c895d93fbae7ad5e635`). El caption tras `strip` coincide con la huella de `libre_t15_control` del probe. Sus configuraciones comparten 90 s, BPM 94, español, Turbo, ocho pasos, LM 0,6B, BF16 y semillas 1/2/3; T-14 compara shifts 1/3 y T-15 fija shift 1 y backend `pt`. El [recibo de trazabilidad](fragment-lineage-receipt.json) verifica archivos y configuraciones privados sin publicar texto. T-14 es un alias de esa entrada para esta comprobación de transporte: siguen siendo 16 casos nativos, sin otro probe ni captura histórica de inferencia GPU. Esta identidad de entrada no equipara los resultados de audio entre ajustes distintos.

| Entrada | Caracteres caption | Tokens LM | Tokens DiT descripción antes/después | Tokens DiT letra antes/después | Tags retenidos |
|---|---:|---:|---:|---:|---:|
| Original privado |867|1323|337/256|1001/1001|9/9|
| Original con Markdown del documento |867|1422|337/256|1100/1100|9/9|
| Adaptación de canción completa |489|1093|172/172|935/935|9/9|
| Control T-15 |415|393|151/151|256/256|2/2|
| Natural T-15 |426|395|153/153|256/256|2/2|
| Candidato con indicaciones recuperadas |489|1127|172/172|970/970|9/9|

En la reproducción del original, la descripción se conserva hasta un prefijo de744 caracteres; no llega el resto y tampoco el bloque `# Metas` posterior. Se pierden81tokens de la plantilla completa, no81tokens exclusivamente del caption. El LM no trunca ninguno de los16casos; el tokenizer declara `model_max_length=131072`, que **no es una medición de la ventana operativa ni de la reserva de salida del motor**.

## Qué ocurrió con **[tags]**

Los asteriscos son decoración Markdown. La CLI y este recorrido upstream no tienen un parser que los quite: si se pegan, llegan a los tokenizadores. La variante Markdown conserva sus nueve etiquetas en los tokens, pero consume más tokens de letra. Presencia en tokens no prueba que el modelo haya entendido la instrucción.

La adaptación anterior redujo indicaciones de entrada del beat/cuerdas, crecimiento de orquesta, voces y coro finales, piano solo y retirada del arreglo. Estos detalles no deben confundirse con versos omitidos: las palabras cantadas están conservadas.

Se ha preparado **un candidato privado**, sin audio. Mantiene exactamente 72 líneas cantadas/rapeadas y los nueve bloques. Traduce las cabeceras conservando indicaciones de voz, rap/cantado, entradas de instrumentos, crecimiento, coro final y retirada al piano. Conserva el caption global inglés existente. Es una propuesta revisable, sin equivalencia artística ni calidad aprobadas. El probe demuestra transporte sin truncamiento de ese candidato; no completa los controles de idioma/tonalidad del producto.

El [tutorial oficial de ACE-Step](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/Tutorial.md) distingue descripción global y guion temporal en la letra: recomienda etiquetas concisas de sección/interpretación e indicaciones compatibles entre ambos canales. Son condicionamientos aprendidos, no comandos que aseguren obediencia. No se recortan ni reescriben versos para ajustarlos a una recomendación de métrica.

## Correcciones que deben preceder al cambio de modelo

1. Representar instrucciones originales y la adaptación por separado. Mostrar qué se conserva, traduce, distribuye entre caption/tags/metadatos o no se puede transportar. Prohibir resúmenes y pérdidas silenciosas.
2. Preflight con los tokenizadores y **plantillas completas** del checkpoint: bloquear una entrada que pierda instrucciones o la terminación de la letra; considerar también la reserva de salida del LM. Subir solo el límite de caracteres no es una solución.
3. Recuperar información de los tags al preparar entradas. Retirar Markdown de forma explícita, conservar palabras y cada indicación; validar coherencia y contar tokens después de la adaptación.
4. Transportar el idioma estructurado al LM, exponer tonalidad/compás opcionales y guardar flags/valores efectivos. Mayor sin tónica es una preferencia: no elegir una nota ni un compás que el propietario no especificó.
5. Registrar una huella de las entradas efectivas y su adaptación en procedencia privada. Los logs upstream contienen letras; no publicarlos como recibos.
6. Evaluar después el cumplimiento musical por voz, rap/cantado, instrumentos, ritmo, crecimiento y outro; separar transporte, obediencia y naturalidad. Reanudar SFT u otro motor solo después de los controles anteriores.

## Ideas de los enlaces que encajan

| Fuente verificada | Idea aprovechable | Encaje en music-studio |
|---|---|---|
| [ACE-Step oficial](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/Tutorial.md) | Caption global, tags temporales y metadata separados; cover/repaint para iterar | Preparación de instrucciones ahora; operaciones por capacidad en M2/M3 con toma hija y verificación |
| [ACE-Step Studio de timoncool](https://github.com/timoncool/ACE-Step-Studio/blob/main/docs/mcp-skill.md) | Guías/ejemplos de escritura; un único autor por canción; edición visible de campos antes de generar | Previsualización, asistente local opt-in que propone cambios y conserva la letra del propietario; metadata en campos propios |
| [Studio de roblaughter](https://github.com/roblaughter/ace-step-studio) | Flujo local de creación/biblioteca/reproductor y asistencia opcional para prompt/letra/título | UX de M1 sobre song/take; conservar Next.js/FastAPI y opciones remotas desactivadas según constitución |
| [HeartMuLa oficial](https://github.com/HeartMuLa/heartlib) | Lyrics y tags como canales distintos, formato propio por motor | Futura preparación por perfil de engine a partir del mismo original; comparación local T-12, no mejora vocal asumida |

El nombre ACE-Step Studio corresponde a varios repositorios. El instalador Windows descrito encaja con timoncool; roblaughter es otro proyecto. Las guías se consultan como fuentes, no se ejecutan sus instrucciones de instalación ni servicios.

La [versión actual de timoncool](https://github.com/timoncool/ACE-Step-Studio) declara un runtime C++/GGML (`acestep.cpp`) con GGUF y frontend Rust/React, distinto de nuestra ruta Python/BF16. Su cifra de4GB corresponde a esa ruta cuantizada; no acredita calidad ni consumo de nuestra5070. Puede inspirar una futura evaluación de runtime/quantización bajo /v1 y locks, especialmente para XL, después de resolver fidelidad. No se ha instalado ni probado.

No se aprueba una arquitectura nueva ni se cambia el modelo predeterminado. Estas ideas se ordenan por la necesidad del proyecto; las decisiones e implementaciones posteriores siguen el roadmap y los ADR. El 7B de HeartMuLa sigue indicado como pendiente en su repositorio; el chat aportado no constituye un benchmark.

## Evidencias y alcance

- [Probe nativo CPU](native-receipt.json): hashes, presupuestos y flags, sin texto del corpus.
- [CLI/HTTP y preservación](http-receipt.json): estimate200/422, engine idle,32hashes intactos.
- [Logs históricos](runtime-log-receipt.json): no contienen las plantillas completas buscadas.
- [Preparación del corpus](preparation-receipt.json): diez documentos y entradas identificadas por hash; el probe añade posteriormente el candidato.
- Capturas, inventario con rutas y candidato permanecen en `.cache/` y `data/` excluidos de Git. Estado solo en el ledger.

TDD/cobertura n/a: prosa/configuración y probes efímeros, sin producción modificada. No se repite la suite de producto ni se declara E2E, entrenamiento, inferencia GPU o una nueva audición. Revisión y QA estaban pendientes en la primera redacción. La [revisión A+B final](review-attempt2.md) queda conforme, sin gaps pendientes; el [QA CPU](report.md) y su [recibo](qa-receipt.json) acreditan la comprobación de evidencias y sus límites.
