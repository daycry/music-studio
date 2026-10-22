---
design: t10-capacidades-acestep
titulo: Medición de capacidades nativas y accesibles por /v1
estado: aprobado
creado: 2026-10-06
actualizado: 2026-10-06
spec: ../../spec.md
evaluacion: n/a
plan: ../../improvement-plan.md
adr: ../../../../decisiones/ADR-0034-capacidades-nativas-y-accesibles-por-v1.md
opcion_elegida: O1
validada: 2026-10-06
validacion_via: root, elegida O1, bajo autorización explícita del propietario para elegir alternativas del roadmap
generacion:
  fuente: estimado
  tokens: null
  coste_eur: null
  horas: null
  marcador: se conserva la única ventana existente de root; no se abre otra
---

# Diseño — T-10: capacidades de ACE-Step

Diseño O1 aprobado por root el 2026-10-06, bajo autorización explícita del propietario para elegir las mejores alternativas del roadmap. T-10 continúa en borrador y no hay capacidad nueva verificada. La spec está aprobada. Root escribirá `docs/decisiones/ADR-0034-capacidades-nativas-y-accesibles-por-v1.md` y publicará la decisión. Este artefacto privado permite despachar implementación; no sustituye el informe final, el ledger, el ADR ni la validación musical. Los originales anteriores a la elección se conservan en `original-before-o1-approval/`, con SHA en el receipt.

## 1. Contexto y restricciones

T-10 exige ocho operaciones y cinco features de `music.song`, checkpoint, comando exacto, audio de evidencia y veredicto. También exige averiguar la conservación fuera de la región de repaint y alinear `verified` con funcionamiento real. `music.song` e `music.instrumental` verificadas son puerta de M1. T-07 y T-19 están completadas; T-09 está en implementación concurrente. El default sigue Turbo + LM 0.6B, BF16, PT, shift 1, sin compile.

El adaptador actual sólo publica `music.song` y `music.instrumental`. Su schema admite `negative_prompt`, `bpm` y `key`; `generation_options()` los convierte en `lm_negative_prompt`, `bpm` y `keyscale`. Los recibos capturados prueban transporte, no obediencia. `timbre_ref` y `lora` aparecen como features no verificadas, pero no tienen transporte implementado. Las seis operaciones restantes no están declaradas. El servidor común devuelve `INVALID_PARAMS`/422 para tarea no declarada antes de load/preflight; no existe aquí un código `TASK_NOT_SUPPORTED` que deba suponerse.

La ruta `models/ace-step-1.5/upstream` no existe. El snapshot local es `.cache/dev-cycle/t17/upstream-acestep/`; once archivos decisivos se cotejaron byte a byte con fuentes oficiales de la revisión `dce621408bee8c31b4fcf4811682eb9359e1bc94`. Copias y SHA están en `sources/` y `receipt.json`. No se ejecutó código descargado. Las referencias siguientes expresan candidaturas de API, nunca éxito de inferencia.

Durante la espera de elección hubo cambios concurrentes ajenos: el ledger y `apps/engines/acestep/adapter.py` variaron respecto al receipt original. El adaptador pasó de SHA `ff02449b32d6a51488cc68be1fafb7393f0b60fc0f9ef8b3df174ef4842c6a5c` a `df35a733c312c535840c03296c99fa4ddd642dc0650e9944d6c2232d995c7229`. Se releyó `generation_options()` y mantiene el transporte identificado; no se revisó ni validó toda la modificación concurrente, ni se tocó ese archivo. El receipt registra la deriva y conserva ambos snapshots de procedencia. T-09 sigue en-progreso y T-10 borrador; revalidar SHA/interfaces al freeze antes de implementar el laboratorio.

**Restricciones que fijan las opciones**

- Código, pesos, tokenizadores y código remoto fijados y comprobados por SHA; sólo formatos seguros. El loader existente de `patches.py` no acredita por sí solo la ruta PEFT de LoRA.
- Todo runtime GPU en hijo propio y contenedor local; un residente en VRAM; cap de memoria libre menos 512 MiB, BF16 y modos explícitos; unload mata el hijo y se comprueba liberación real. Nada de raw CLI upstream por suposición.
- El hijo sólo escribe crudos y recibos en `data/tmp/<job_id>/`. El llamante conserva copias de evaluación, post-procesa, renderiza y emite manifiestos; no hay BD en el laboratorio. Cada operación deriva un artefacto nuevo, nunca sobrescribe fuente o take.
- La implementación de T-09 tiene ownership de `scripts/eval/` y ACE/common. Esperar su freeze, comparar SHA y coordinar un ownership posterior antes de incorporar T-10; no parchear archivos compartidos durante ese trabajo.
- No se lee audio, feedback ni mapa privado de T-16. Las entradas de T-10 son independientes, propias o autorizadas. Sin reconocimiento de artistas/personas ni suplantación de voz.
- No se toca `docs/knowledge/`, memoria, locks, Git, producción ni el ledger durante esta preparación. No se ejecuta GPU, Docker, benchmark, build ni instalaciones.

### Dos planos de evidencia

Cada fila guarda `surface = v1 | native_lab`, no un único veredicto mezclado. En cada superficie hay `execution_status = pending_prerequisite | planned | rejected | executed | failed` independiente de `verdict = null | funciona | degradada | no funciona`. `pending_prerequisite` no se convierte en «no funciona». El diseño contiene filas `planned`, con veredicto null; los rechazos aún no se han ejecutado.

El informe final tendrá ocho filas principales y cinco de features por checkpoint evaluado; las columnas `/v1` y laboratorio nativo muestran sus comandos y evidencia separadas. `funciona` exige salida real, controles técnicos y criterio musical cumplido. `degradada` exige salida real con limitación observada. `no funciona` exige rechazo real o fallo acreditado; el origen del fallo identifica adaptación, checkpoint, recurso o semántica. Un rechazo previo a GPU prueba indisponibilidad de la superficie, no incapacidad del checkpoint. Un rechazo produce `audio_output = null`, motivo explícito y JSON/NDJSON de evidencia; no se inventa audio ni se llama audio de salida a la fuente.

### Matriz íntegra de operaciones

Duraciones iniciales de 60 s, fuentes estéreo 48 kHz WAV FLOAT, semillas 101/102/103, batch 1. Cada prueba conserva seed real de LM/DiT, n_outputs 1, prompt/lyrics original y efectivo, checkpoint, LM, modo, pasos, CFG, shift y fuente por SHA. Hay controles adicionales indicados abajo. Turbo 8 pasos, SFT 50/CFG 7, base 32/CFG 7; los perfiles proceden de T-09 congelado. Son valores de protocolo propuestos, no nuevas mediciones ni defaults.

| Operación | `/v1` hoy | Candidato nativo fijado / checkpoints iniciales | Entrada y prueba musical/técnica |
|---|---|---|---|
| `music.song` | Accesible, `verified: false` | `text2music`; Turbo y SFT, base como contraste explícito | Letra original breve etiquetada en es, style propio, 60 s; voz cantada, texto inteligible y acorde al style. Tres semillas; escucha con timestamps. No declarar calidad de canción completa por este fragmento. |
| `music.instrumental` | Accesible, `verified: false` | `text2music`, instrumental true y `[Instrumental]`; Turbo/SFT/base | Style original sin artistas, 60 s; ausencia de palabras y de voz cantada, contenido musical no silencio. Tres semillas. |
| `music.retake` | Rechazo esperado: tarea no declarada | `cover` con fuente y overlay `retake_seed`/`retake_variance`; Turbo/SFT/base | Fuente propia de 60 s. Control variance 0, contraste variance 0.2 con retake_seed 201 y 202, seed principal 101. Debe variar algo musical conservando identidad/estructura; hash distinto sólo prueba cambio de muestras. Si se usa retake sin fuente no cumple la semántica de variación del catálogo. |
| `music.extend` | Rechazo esperado: tarea no declarada | No hay task_type extend. Hipótesis compuesta: fuente 60 s + padding explícito 30 s y repaint `[60,90)`; Turbo/SFT/base | Pad del llamante conservado por SHA y section_map; source 90 s, extensión audible de 30 s, continuidad en 60 s y conservación prefijo. Se informa «composición mediante repaint», nunca soporte native extend directo. Si falla, conservar el rechazo/fallo y no renombrar complete como extend. |
| `music.repaint` | Rechazo esperado: tarea no declarada | `repaint` sobre fuente 60 s y `[20,30)`; Turbo/SFT/base | Cambio local original de instrumentación, mismo style/lyrics fuera. Probar aggressive sin splice y balanced/conservative con splice nativo, capturando configuración efectiva. Contar diferencias exactas y escuchar bordes. Protocolo preciso abajo. |
| `music.cover` | Rechazo esperado: tarea no declarada | `cover`, `src_audio`, caption de estilo diferente; Turbo/SFT/base | Fuente propia 60 s; conservar melodía/ritmo identificables con cambio de estilo audible. Capturar audio_cover_strength; control 1.0 y contraste explícito 0.5, sin atribuir efecto antes de escucha. No confundir reference_audio de timbre con src_audio de cover. |
| `music.complete` | Rechazo esperado: tarea no declarada | `complete` sólo en base candidato; instrucción con clases de acompañamiento | Voz aislada propia 60 s y ground truth multipista. Instrucción `generate_instruction('complete', complete_track_classes=['drums','bass','guitar'])`, source vocals; acompañamiento real y preservación/alineación de voz. No «completar duración»: semántica del catálogo es acompañamiento de voz. Turbo/SFT se registran como candidaturas no expuestas por el selector fijado; una negativa nativa requiere ejecución real, no lectura del selector. |
| `audio.stems` | Rechazo esperado: tarea no declarada | `extract` en base, una llamada por `track_name` y su instrucción | Mezcla propia 60 s con voces/batería/bajo/guitarra separados conocidos. Extraer al menos vocals, drums, bass y guitar; registrar N crudos, sangrado, alineación y fidelidad frente a stems reales. Sumar stems no garantiza reconstrucción exacta. Si sólo se ejecuta vocals, se describe el alcance parcial como degradado y no se promete separación completa. |

Lo que declare un selector upstream determina qué candidaturas probar primero. No sustituye comprobación de checkpoint ni predice el resultado. XL no se añade automáticamente a la matriz de capacidades: sólo tras T-09 y decisión de root si su ruta cabe; la matriz de capacidades obligatoria permanece íntegra aunque XL resulte inviable. Registrar el criterio de selección de checkpoints y toda exclusión de perfil, evitando trasladar un éxito de base a Turbo.

### Matriz íntegra de features de `music.song`

| Feature | Transporte `/v1` vivo | Caso nativo y controles | Prerrequisito y aceptación |
|---|---|---|---|
| `negative_prompt` | `params.negative_prompt` → `lm_negative_prompt`; no negative prompt DiT | Turbo/SFT/base: caption con elemento perceptible (p.ej., distorsión), control vacío frente a exclusión de ese elemento, mismos tres seeds; LM CFG 2 fijo y thinking true. Capturar paso al LM. | Cambio audible consistente; un campo aceptado, texto presente en YAML o hashes distintos no prueban exclusión. Alcance LM se documenta como tal. Si efecto inconsistentemente débil, degradada y verified false. |
| `bpm` | `params.bpm` → metadata LM y `bpm` DiT | 80 y 120 BPM, letra/style iguales, seeds 101/102/103, 60 s; variantes sin BPM como control. | Beat analysis del engine ya instalado, por turnos de GPU, y escucha/tap corroborados. Propuesta de tolerancia previa: ±5 % contra BPM pedido; ambigüedad half/double se declara y se resuelve por escucha, nunca se ajusta automáticamente a objetivo. |
| `key` | `params.key` → `keyscale` | `C major` y `F# minor`, mismos tres seeds, 60 s; sin key como control. | Cambios coherentes con tonalidad solicitada. `audio.key` corresponde a M3 y no se supone disponible. Usar auditoría tonal humana/autorizada de músico o herramienta ya licenciada instalada y revisión musical; si falta ese evaluador, pending_prerequisite. No instalar separador/detector nuevo por rutina. |
| `timbre_ref` | Feature declarada, sin input descriptor/params/mapper. `inputs.role=timbre` podría pasar validación sin consumirse; probar no-op, no dar por hecho rechazo. | `text2music` + `reference_audio` de 30 s propio, controles referencia A/B/ausente, 60 s y mismos seeds; capturar segmentos front/middle/back reales. | Audio autorizado, declaración de derechos y consentimiento si contiene voz real. Atribuir textura/timbre musical, sin reconocimiento de identidad ni promesa de clonación. La ruta hace muestreo aleatorio: seed de Python y hashes/offsets de segmentos deben acreditarse aparte del seed LM/DiT. |
| `lora` | Feature declarada, `params.lora` no admitido; rechazo schema esperado | LoRA real compatible con checkpoint, `dit.load_lora(path)`, estado cargado/activado/escala efectiva; control off/0 frente on/1, tres seeds, 60 s | No se halló artefacto LoRA por inventario de nombres bajo models; ausencia no equivale a fallo inferencial. Archivo real propio/autorizado, config, hashes, licencia de pesos y fuente/dataset/consentimiento documentados; revisión de loader PEFT local safetensors sin fallback pickle/red antes de carga. No entrenar M5 ni descargar modelo por esta preparación. Sin archivo seguro: native pending_prerequisite, v1 sólo no funciona después del rechazo real. |

### Ground truth de repaint y preservación

La fuente será independiente de T-16, de 60 s, WAV FLOAT estéreo 48 kHz, finita, amplitud ≤0.8 y sin resample/normalización ni clipping. Conservar archivo y PCM SHA, frames, orden/canales/dtype/endian, más ground truth de stem/mix si existe. Usar intervalo semiabierto `[20,30)` = muestras `[960000,1440000)` en 48 kHz, con definición única de redondeo y sin tolerancia fuera de esa región.

Capturar cuatro estados: fuente decodificada float32; fuente tras preparación/clamp/cast; salida inmediatamente después de VAE y antes del splice; salida nativa después del splice. Si upstream no expone un estado, un wrapper privado temporal sobre el callable fijado registra su frontera sin alterar retorno. Sellar SHA y el propio wrapper. Comparar arrays por bytes/bit pattern, no `allclose` ni igualdad de archivo WAV (cabeceras pueden cambiar). Registrar conteo de samples diferentes y máximo error por canal: prefijo, interior, sufijo, bordes y bandas de crossfade. Verificar también shape/duración y signed zero; el post-proceso PCM24/MP3 queda excluido de esta comparación.

El código fijado contiene splice de waveform tras VAE. En aggressive se omite; balanced con strength 0.5 resuelve aproximadamente 25 ms y conservative 50 ms fuera de los bordes. El parámetro declarado `repaint_wav_crossfade_sec=0` no prueba que el valor efectivo resuelto sea cero. Sus rampas pueden cambiar muestras fuera de `[20,30)`; además el source se castea al dtype predicho y puede perder precisión. Por tanto, comprobar fuente original y fuente procesada separadamente. Que el exterior coincida después de splice no acredita preservación por difusión: el recibo identifica el empalme nativo.

Si no queda bitexact respecto a la fuente original, la conclusión responderá directamente «no; requiere empalme». El laboratorio puede medir por separado un empalme del llamante que copie exactamente el exterior y aplique crossfade sólo dentro del intervalo; no se integra ni se acredita `music.repaint` accesible por `/v1` con ese compuesto sin decisión/ADR. Escuchar 5 s a cada lado y dentro de bordes: clicks, cambio de fase/timbre, continuidad y cambio solicitado. No corregir duración, resamplear ni recortar silenciosamente para hacer pasar la comparación.

## 2. Opciones

### O1 — Matriz `/v1` real y laboratorio nativo privado con dos superficies

Medir song/instrumental y features transportadas por el engine congelado. Conservar rechazos/no-ops `/v1` de todos los demás casos. Añadir un harness privado de investigación que reuse carga segura, hijo, guardia, cancelación y escritura cruda, y llame API nativa fijada para editar/extract/complete/referencias/LoRA. Los resultados nativos se documentan como integración pendiente de M2/M3/M5, con prerequisitos explícitos. La única modificación funcional permanente de T-10 es un descriptor basado en evidencia `/v1`; no ampliar tasks en ese descriptor por éxito del laboratorio.

| Criterio | Valoración |
|---|---|
| Complejidad | Media-alta: harness seguro y trece casos, sin seis operaciones de producto nuevas |
| Riesgo | Medio: confundir laboratorio con API o loader PEFT inseguro; se mitiga con superficies y bloqueos explícitos |
| Coste relativo | M: audio y escucha reales, reutiliza infraestructura congelada, evita integración prematura |
| Reversibilidad | Alta: laboratorio y evidencias aislados; descriptor conservador reversible por nuevo resultado, sin reescribir manifiestos |

### O2 — Integrar operaciones y features en `/v1` antes de medir

Añadir schemas, inputs descriptors, transporte, preflight específico, linaje del llamante, output de stems, loaders y rutas de edición; después medir todos los casos en una sola superficie. Permite verificar operación end-to-end, pero amplía archivos y tareas respecto a T-10 y adelanta piezas M2/M3/M5. Exige decisión de root, ADR y alcance/brief de implementación revisado antes de tocar producción.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: integra semántica de ocho operaciones, cinco features y soportes de API |
| Riesgo | Alto: expansión de alcance y colisión con T-09, tratamientos de entrada distintos, empalme/LoRA sin auditoría |
| Coste relativo | L: integra antes de conocer funcionamiento y necesita más conformidad/TDD/revisión/QA |
| Reversibilidad | Media-baja: contratos/descriptores/callers acoplados; sólo cambios opcionales compatibles en /v1 |

### O3 — Evaluar únicamente la superficie actual y dejar laboratorio para hitos posteriores

Realizar los trece casos de acceso `/v1`, medir song/instrumental y sus tres features transportadas, informar rechazo/no-op del resto y listar incertidumbres nativas. Sirve como resultado intermedio y puede satisfacer la puerta mínima de M1, pero no prueba funcionamiento nativo ni repaint y no completa por sí solo T-10. No reducir los trece casos ni marcar la tarea completada con esta opción sin modificar formalmente alcance; esa modificación no se recomienda.

| Criterio | Valoración |
|---|---|
| Complejidad | Baja: usa el engine actual y conserva trece intentos |
| Riesgo | Alto para cumplimiento: deja repaint/nativo/LoRA sin medición; riesgo de falso cierre |
| Coste relativo | S: útil como primer bloque, trabajo nativo aplazado |
| Reversibilidad | Alta: resultado intermedio ampliable; no altera motor ni catálogo |

## 3. Criterios de decisión

1. Cumplir los ocho casos/cinco features y pregunta de repaint sin fabricar audio, rechazos ni mediciones. Ausencia de prerequisitos mantiene el caso pendiente.
2. Separar funcionamiento nativo, disponibilidad `/v1` y calidad musical; `verified` se decide sólo con funcionamiento accesible real. La honestidad del contrato pesa más que comodidad del informe.
3. Respetar alcance aprobado y ownership; medir antes de adelantar integración de M2/M3/M5. Default y contratos actuales se conservan salvo decisión explícita.
4. Reutilizar loader y ciclo seguro, nunca inferencia raw upstream ni nuevas dependencias sin revisión. No mezclar T-09 performance con matriz de capacidades.
5. Evidencia reproducible y custodiada: fuente/checkpoint/modo/SHA/input efectivo/output + escucha acreditada. Una prueba CPU no se transforma en una capacidad musical verificada.

## 4. Recomendación · opción elegida y por qué

**Opción elegida O1, validada por root el 2026-10-06 mediante «Elegida: O1», bajo autorización explícita del propietario.** Es fiel a la spec: M0 verifica capacidades y deja edición expuesta al usuario para M2/M3. Mantiene trece casos y evidencia nativa real sin fingir que el adaptador ya tiene su transporte. Se descarta O2 para esta ejecución porque adelanta integración y amplía alcance antes de medir; se descarta O3 como solución completa porque deja sin resolver mediciones nativas y repaint. El ADR reservado para root es `docs/decisiones/ADR-0034-capacidades-nativas-y-accesibles-por-v1.md`; este agente no lo escribe ni presupone su publicación.

### Resolución autónoma de materiales y ground truth

Para complete/stems se puede preparar un conjunto independiente de T-16 con pistas propias o autorizadas generadas por separado —voz, batería, bajo, guitarra— y mezcladas después con ganancias lineales conocidas. Cada componente se conserva antes de la mezcla como ground truth: archivo original, PCM, SHA, procedencia, prompt/seed/configuración cuando se genera, licencia y declaración de derechos. La mezcla se calcula desde esas pistas y coeficientes sellados, manteniendo la misma frecuencia, canales, offset y duración; se evita clipping y no se aplica limitador ni efecto no lineal que impida relacionar mezcla con componentes. La categoría musical de cada pista debe comprobarse: una generación supuestamente vocal con acompañamiento no se etiqueta como voz aislada limpia ni permite afirmar separación de clases que no se conoce.

La otra ruta es un corpus multipista aportado por el propietario con licencia y autoría acreditadas, o grabaciones propias alineadas. El generador/herramienta de preparación y todos los inputs siguen sujetos a licencias, formatos seguros, ejecución local y prerequisitos del runtime; la producción posterior de esos materiales requerirá su plan/recibo y no fue ejecutada aquí. **Una separación estimada de una mezcla no es ground truth real:** no usar output de ACE-Step extract ni de otro separador para inventar los stems conocidos, medirlos contra sí mismos o tratar ausencia de sangrado inferida como verdad. Esos audios pueden ser objetos de evaluación con referencia desconocida, pero no sustituyen el conjunto multipista controlado.

LoRA dispone de una ruta independiente: investigar después un artefacto compatible con licencia, autoría/dataset, consentimiento cuando corresponda, revisión, config y SHA verificables; si no existe un candidato adecuado, root puede abrir una tarea explícita de preparación/auditoría. Antes de inferencia se audita la ruta PEFT fijada y se excluye todo fallback pickle o red. No entrenar M5 implícitamente ni preparar pesos sin autorización de alcance para forzar M0. Hasta que exista un archivo seguro real, la fila nativa `lora` conserva `pending_prerequisite`, verdict null y verified false; T-10 no se cierra con ese pendiente.

### Protocolo de ejecución que deberá concretar el implementer

- Generar plan privado inmutable por caso/checkpoint/surface/input_sha/seed; guardar JSON exacto, comando ejecutable completo con rutas relativas y versión SHA del harness, stdout/stderr privado, respuesta HTTP, eventos NDJSON con seq/terminal, metadatos y audio. Los comandos no se inventan aquí como si hubiera un CLI de capacidades; el implementer define `scripts/eval/capabilities.py` o runner privado y root aprueba interfaz antes de ejecutar.
- Cada fila referencia `eval/capabilities/<session>/<checkpoint>/<case>/<seed>/`; audio fuente/evidencia propia y crudo se copian desde `data/tmp/<job_id>/`, preservando SHA. El comando puede ser `uv run --frozen scripts/eval/capabilities.py run --plan eval/capabilities/<session>/plan.json --case <id>` únicamente después de que ese CLI exista y su interfaz se congele. Los parámetros reales viven en un plan sellado, no en aliases musicales implícitos.
- Para rechazo: petición válida estructuralmente al `/v1` real propio con task/feature solicitada, identidad y entradas correctas; conservar HTTP status, problem code, body_sha y ausencia de load/job/output. El rechazo genérico por falta de token, fuente o id inválido no acredita que la operación esté sin implementar. No fabricar eventos de job cuando el API rechaza antes de encolar.
- Para timbre: intentar el rol contractual `timbre` con fuente real autorizada y registrar si el servidor acepta pero el mapper no consume; también probar params desconocidos por schema. El no-op se acredita con captura del mapper/nativo, y comparación emparejada donde proceda; no asumir que tiene que rechazar por tener inputs descriptor vacío.
- El laboratorio reutiliza infraestructura ligera congelada para autenticación/ownership, proceso hijo, timeout, cancelación y unload; recibe tareas sólo en factoría privada experimental, separada de la factoría de producción y sin falsear descriptores públicos. Adaptador de investigación explícito transforma cada caso a API nativa y valida shape/semántica/inputs/preflight de esa ruta. `prepare_runtime()` y `AceStepAdapter.load()` pueden reutilizarse; el `generate()` actual es sólo text2music, no sirve sin mapeo adicional.
- Congelar/validar fuentes nuevas que alcanza el laboratorio (repaint, extract/complete y LoRA), safe loader efectivo, recursos del lock, ausencia de fallback pickle/red y exactitud de inputs. El preflight text2music existente no se hereda como correcto para tareas sin LM; capturar los límites efectivos de cada camino y rechazar clamp/truncamiento oculto.
- Preflight GPU actualizado: mirar Ollama, descargar sólo modelo previamente cargado, comprobar nvidia-smi ≤1600 MiB, acquire lease, una GPU/secuencia, cap libre menos margen. Reusar controles T-09 sólo tras freeze; ninguno se ejecutó en este diseño. Al final unload/reap hijo, health libre ±300 MiB, retirar sólo contenedor propio y restaurar sólo Ollama descargado. No tocar engine ajeno del 8101 ni afirmar no-spill sólo por NVML.
- No ejecutar benchmark de T-09 de nuevo ni medir los 160 jobs: esta sesión guarda tiempo/VRAM propios como contexto de fallos, sin competir con la selección por rendimiento. Varios checkpoints se cargan secuencialmente; nunca dos resident.

### QA, render y escucha

CPU/TDD: tests del plan de trece casos, separación de surface/prereq/verdict, no verified por simulación, scope/checkpoint/mode de recibo, alineación descriptor↔matriz, rechazos correctos y no-op de inputs, cálculos de PCM exterior con transientes cerca del borde, signed zero/canales/duración, artefactos faltantes/hash cambiado y rutas de salida. LoRA sin prerequisitos se bloquea antes de carga. Tests artificiales sólo acreditan el verificador, nunca el repaint del modelo. Se usan las puertas del dev-cycle, revisión fresca y cobertura ≥80 % de código cambiado, después del freeze T-09; sin suite extensa en esta preparación.

QA integrado posterior: generar audio real, verificar artefactos finitos/no silencio/RMS >−60 dBFS/clipping, duración contextual, cancelar y comprobar unload. Render de escucha con audio-post/ffmpeg instalado por el llamante, audio de comparación con ganancia lineal, mismo loudness objetivo −16 LUFS y true peak ≤−1 dBTP; si no cabe sin compresión, reducir objetivo común y registrar limitación. Nunca usar escucha MP3 ni FLAC PCM24 como ground truth bitexact del crudo.

Página/listado local de escucha por casos con controles accesibles, fuente y salida separadas, intervalo y seeds; renderer verificado visualmente sólo si herramienta/superficie está permitida, sin reintentar la pestaña de T-16 bloqueada. Custodia privada independiente, sin acceder a mapas T-16. Los seeds y checkpoints no se revelan como preferencias: registrar comentarios con timestamps, rúbrica D1–D5 pertinente, observación cumplimiento vs naturalidad y persona/sistema de escucha. Ninguna escucha real ni render visual se realizó aquí; no afirmar CA por validación CPU, CLAP, WER o el diseño. Cuando se requiera músico para key, registrar ese prerequisito.

Descriptor posterior: `verified: true` sólo si task/feature se accede por producción `/v1`, funcionó en su checkpoint y modo documentados y la evidencia existe sellada; `degradada`, rechazo, no-op, pendiente o éxito nativo sin integración conservan false. No inferir song feature por pruebas de instrumental ni compartir flags entre Turbo/SFT/base. El boolean de descriptor no expresa modos: registrar el modo validado y limitar anuncio si otros modos no se verificaron; root decide si hace falta campo opcional de detalle antes de publicarlo. No añadir timbre/lora/otras tasks sólo para hacer pasar tests. Antes de cerrar: informe con ocho operaciones y cinco features por checkpoint ejecutado, condición de repaint resuelta, verificación exacta `uv run pytest apps/engines/acestep -k descriptor -q` y lectura del informe por root; tarea no DONE si faltan mediciones/prerequisitos de su alcance.

## 5. Impacto en módulos y ficheros

| Ruta real o nueva propuesta | Impacto futuro O1 / responsable |
|---|---|
| `eval/results/capacidades-acestep.md` | Informe canónico de capacidades; root publica tras QA y escucha |
| `eval/capabilities/` | Planes, comandos, fuentes, ground truth, recibos y audio privados; implementer posterior |
| `apps/engines/acestep/descriptor.py` | Sólo flags verificados sustentados en superficie /v1; esperar freeze T-09 |
| `apps/engines/acestep/tests/test_adapter.py` y nuevo `tests/test_descriptor_capabilities.py` vecino | Tests de evidencia/descriptor y límites de surface, después de ownership específico |
| `scripts/eval/capabilities.py`, `capabilities_plan.py`, `capabilities_evidence.py` (nuevos) | Harness de investigación y reporte, interfaz propuesta pendiente; no existen hoy, `scripts/eval/` reservado T-09 |
| `eval/capabilities/<session>/lab/` (nuevo, privado) | Adapter/factoría nativa propios y wrappers fijados; experimentos no expuestos por factoría pública |
| `apps/engines/acestep/adapter.py`, `patches.py`, `preflight.py`, `benchmark_profiles.py`, `input_profile.py`, `engine_acestep.py` | Reutilización sólo lectura después de freeze, revisión de diferencias; no cambio de producción de transporte O1 |
| `apps/engines/common/engine_common/{runtime,worker,server}.py` | Lifecycle, errores, outputs y guardia reutilizados sólo lectura; no tarea nueva pública O1 |
| `packages/engine-contract/engine_contract/__init__.py`, `packages/contracts/engine-v1.json` | Sin modificación O1 salvo decisión opcional documentada; O2 exigiría verificar contrato code-first |
| `data/tmp/<job_id>/`, `data/inputs/<t10-source>/` (nuevos privados) | Inputs autorizados por SHA y crudos escritos exclusivamente por hijo; copias/render por llamante |
| `docs/decisiones/ADR-NNN-*.md`, docs afectados y testing T-10 | Decisión y publicación sólo root; no ADR escrito por este agente |

## 6. Riesgos y mitigaciones

| Riesgo | Mitigación / límite |
|---|---|
| T-09 cambia descriptor/adapter durante lectura | Receipt con SHA vivo inicio/fin; no aplicar patch a snapshot antiguo. Freeze posterior y revalidación de interfaces antes de dispatcher T-10 |
| Pesos base/XL disponibles confundidos con soporte | Cada fila identity checkpoint/LM/mode y ejecución; nunca verified por archivo instalado o selector upstream |
| API de extend ausente, retake es overlay, complete semánticamente distinto | Mapping explícito y prueba musical; distinguir compuesto mediante repaint y operación directa. ADR si se decide integrar compuesto |
| Splice nativo modifica bandas exteriores o source dtype | Capturar antes/después, región exacta y crossfade efectivo; originalfloat32 vs processed source y salida. Empalme del llamante sólo experimento separado |
| LoRA PEFT elude patch Transformers o usa fallback .bin | Auditar fuente exacta instalada y ruta local, exigir safetensors, config/weights por SHA/lock; fail closed hasta aprobarlo. No confiar en `use_safetensors` de cuatro modelos base |
| No hay LoRA compatible autorizado ni fuente vocal/multipista | pending_prerequisite con owner y criterio resoluble; root procura material/decide tarea específica, no se genera/traina/descarga aquí ni se sustituye por mock |
| Feature timbre entrada aceptada pero ignorada | Prueba capturada de mapper y parámetros nativos, controles emparejados; rechazo/éxito HTTP no demuestra efecto |
| Metadata es correcta pero música no obedece BPM/key/negativo | Captura y escucha separadas, tolerancias previas, sin umbral ajustado al ver los resultados |
| Capturas/logs contienen letra privada/rutas/token | Artefactos bajo eval privado, informe público sólo IDs/hashes/rutas relativas y resumen; no body del token ni textos privados |
| QA automatizado confundido con música usable o análisis ocupa otra GPU | Escucha manual y evaluación por turnos, descarga/carga secuencial; D5 de batería completa pertenece T-11/T-13 |
| Medidor solapado o imputación de reloj como tokens | No abrir otra ventana; generación estimada con nulls; root consolida consumo de su lote |

## 7. Preguntas abiertas

1. Elección resuelta: O1 aprobada. Publicación del ADR-0034 y asignación del brief de implementación corresponden a root; no se requieren nuevas elecciones para continuar la preparación autorizada.
2. ¿Qué conjunto multipista controlado se preparará: componentes propios/autorizados generados por separado y luego mezclados, o corpus del propietario? Es necesario para complete/stems y continuidad. El implementer podrá resolver la primera ruta de forma autónoma dentro del alcance autorizado con procedencia y controles, conservando el pendiente hasta que existan las pistas; el agente no ha inspeccionado audio privado.
3. ¿Qué LoRA propio/autorizado compatible se obtendrá en la investigación posterior, o qué tarea explícita de preparación/auditoría deberá abrirse? Hasta tener fichero/config/licencia/SHA y loader auditado, la fila nativa permanece pending_prerequisite; T-10 no se cierra por afirmar que «el archivo no existe» ni mediante entrenamiento implícito de M5.
4. ¿Qué persona/herramienta ya aprobada valida tonalidad y cuándo se hará escucha? Resolver mediante inventario de herramientas ya licenciadas y disponibles, revisión del análisis y escucha documentada, o valoración autorizada del propietario/músico. No hay audio.key integrado de M3 que pueda asumirse como analizador disponible; falta de evaluador sigue siendo pending_prerequisite y no se inventa un veredicto.
5. Tras freeze T-09, root asigna ownership de scripts/eval y acepta interfaz del laboratorio; su ejecución musical sólo puede arrancar con prerequisitos y QA/TDD concretos.
6. Si un perfil tiene éxito únicamente en un modo, ¿se restringe anuncio a ese modo o se añade detalle opcional? No se acredita BF16/offload/INT8 indistintamente.

TDD n/a: preparación de diseño y procedencia, sin implementación testeable. `receipt.json` registra validación documental y hashes; no test de T-10, escucha, render ni inferencia ejecutados. Handoff: diseño O1 aprobado; root publica ADR-0034 y despacha brief de implementer que respete las dos superficies, matriz completa y prerequisitos. No handoff de plan nuevo ni modificación del ledger por este agente.
