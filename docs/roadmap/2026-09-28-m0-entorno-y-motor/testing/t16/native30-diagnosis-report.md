# T-16: diagnóstico CPU de la excepción nativa de 30 segundos

Informe sanitizado; material técnico y entradas RAW permanecen privados. Fases 1–3 de `custom-agents:debug-root-cause`; fase 4 no aplicada.

## Resultado

Existe un defecto reproducible en la planificación del condicionamiento DiT: `native_plan()` calcula siempre la instrucción por defecto de `text2music`, pero el handler fijado resuelve legítimamente `text2music` a `cover` y sustituye la instrucción cuando recibe códigos de audio no vacíos. La guarda exacta de tokens detecta esa diferencia y aborta en `adapter.py:224` con `EngineError(INVALID_PARAMS, "Tokens DiT cambiaron tras el preflight")`.

El defecto está probado en CPU con los métodos originales y tokenizadores locales de la imagen inmutable. La traza del fallo real alcanza exactamente esa guarda después de terminar la tokenización. Los IDs finales y la instrucción resuelta del intento GPU no fueron capturados: no se presenta el conteo CPU 150 como una medición GPU, ni se afirma haber vuelto a ejecutar el fallo GPU. La atribución al caso real combina esta reproducción con la traza y las fronteras reales; la captura directa de la rama activa quedará en el fix y su validación.

## Fase 1: reproducción mínima

Imagen: `sha256:9e4fc86fe17269ef80ad6649d9f80b02f8d1f0c7af160f3f9d0fde362dfd8f84`.

Comando: Docker `run --rm --network none`, sin `--gpus`, `CUDA_VISIBLE_DEVICES=` y offline HF/transformers; ejecuta `/diagnosis-out/cpu-reproduce.py` en Python gestionado de la imagen. Único montaje RW: esta carpeta. `models/`, inputs privados y trazas anteriores son RO. No se instancia ningún modelo ni se ejecuta inferencia LM/DiT/VAE.

Reproducción mínima sintética: caption y letra pequeños, idioma `es`, duración 30 s, BPM 94, controles SFT50/CFG7/shift1. El código de audio es un marcador sintético y jamás usa salida musical real.

| Caso | Texto plan/real CPU | Letra plan/real CPU | Resultado de la guarda original |
|---|---:|---:|---|
| Sin códigos: `text2music` | 59 / 59 | 18 / 18 | Pasa |
| Con códigos: resolución `cover` | 59 / 58 | 18 / 18 | `INVALID_PARAMS`, mensaje de tokens DiT |
| Contrafactual: plan con instrucción resuelta | 58 / 58 | 18 / 18 | Pasa, guarda intacta |

La misma prueba con las entradas privadas originales, preservando BOM/decodificación y CRLF según el CLI, produce 151/151 sin códigos, 151/150 con códigos, letra 256/256 intacta y 150/150 con planificación resuelta. Los SHA de tokens de letra son idénticos en las tres variantes. Los IDs completos no se imprimen ni se publican. Los hashes y conteos están en `cpu-reproduction.json`.

## Fase 2: aislamiento

- Fallo real: traza privada `service_generate.py:100 → conditioning_batch.py:117 → adapter.py:224`; error nativo `INVALID_PARAMS`. `_prepare_text_conditioning_inputs` entra y termina; la guarda falla inmediatamente después. No alcanza `_execute_service_generate_diffusion`.
- Captura parcial real no vacía: `boundaries` contiene `lm_arguments`, `lm_formatted_prompt` y `dit_arguments`; el resumen anterior buscaba nombres de claves distintos y no examinaba `boundaries`.
- LM real: conditional397, unconditional33, reserve160. Los tres registros completos (conteos y SHA) coinciden exactamente con el preflight reconstruido en CPU a partir de los inputs privados originales. No se cambió ni mostró caption/letra.
- `preflight.py:174` usa `build_dit_inputs("text2music", None, ...)`: `None` selecciona `DEFAULT_DIT_INSTRUCTION`.
- `inference.py:895` entrega los argumentos al handler; la captura `dit_arguments` acredita los parámetros originales antes de la resolución interna.
- `generate_music.py:279` llama `_resolve_generate_music_task`. `generate_music_request.py:47` define el resolver que cambia tipo e instrucción con códigos no vacíos.
- `batch_prep.py:78` define el método que repite la instrucción resuelta en `instructions_batch`; `_prepare_generate_music_service_inputs` la transporta a `service_generate`, `conditioning_batch.py:117` a `_prepare_text_conditioning_inputs` y `conditioning_text.py:86` la formatea para tokenizar.

Descartes acotados:

- No es OOM en la excepción observada: clase `EngineError`, código `INVALID_PARAMS`, lugar de fallo en la guarda de fidelidad, sin traza CUDA/OutOfMemoryError/VramGuard. Alcanzar `service_generate` demuestra que la preflight VRAM del handler no devolvió error en este intento. Esto no mide spill ni prueba que una difusión completa cabría en VRAM.
- No es truncamiento en esta reproducción: texto 151 y letra 256 están dentro de 256/2048; plan sin truncamiento y IDs activos del tokenizador son idénticos al usar la instrucción correcta. Se mantiene `enforce_budget`.
- No es cambio de caption/letra/idioma/metadata: controles y hash exacto del LM coinciden con el caso real; los argumentos DiT fueron capturados antes del fallo; entre controles CPU se cambia únicamente la resolución de instrucción mediante presencia de códigos sintéticos.
- No se usa SFT-stems: `verified_checkpoint_profile` valida la configuración local fijada y excluye `is_lego_sft`; la rama Global/Local no interviene.

## Fase 3: hipótesis falsable y prueba

"Falla porque el preflight planifica la plantilla text2music, mientras los códigos no vacíos del LM activan la resolución nativa cover con otra instrucción; la guarda de tokens compara esa segunda plantilla contra la primera."

Se confirma en los controles CPU: retirar códigos mantiene la plantilla y pasa; introducir códigos cambia solo la instrucción y falla en la guarda original; recalcular el plan con la instrucción resuelta hace pasar los SHA exactos, sin alterar código productivo, caption, letra, presupuestos ni la guarda. Evidencia: `cpu-reproduction.json`, exit0 terminal del proceso CPU final.

## Fix propuesto, sin aplicar

1. Planificar antes de cargar modelos las dos ramas nativas legítimas: sin códigos (`text2music`/instrucción original) y con códigos (`cover`/instrucción nativa cover). Extraer/ejecutar los métodos puros de la fuente fijada y añadir sus SHA al perfil; no duplicar a mano sus textos. Presupuestar ambas ramas sin truncamiento; fallar antes de cargar si alguna rama posible excede el límite. No asumir que el LM siempre producirá códigos.
2. Mantener la request pública y los inputs originales íntegros. El cambio interno de modo para hints LM no crea una operación pública cover ni modifica el caption ni la letra.
3. Capturar la resolución efectiva en el hijo: tipo inicial, indicador booleano `has_audio_codes`, tipo resuelto y `instruction_sha256`. Nunca almacenar/publicar el contenido de los códigos en esos recibos. `_resolve_generate_music_task(self, task_type, audio_code_string, instruction)` acepta código string o lista; `_has_non_empty_audio_codes` comprueba si hay elementos no vacíos tras `.strip()`. Para `text2music` con códigos no vacíos devuelve `("cover", TASK_INSTRUCTIONS["cover"])`; sin ellos devuelve el tipo e instrucción recibidos. Otros tipos conservan ambos.
4. En la captura de `_prepare_text_conditioning_inputs`, verificar las `instructions` efectivas (argumento posicional índice1 o keyword `instructions`) contra la rama resuelta antes de seleccionar su registro planificado. Validar luego conteo y SHA exacto de IDs en ambas ramas como hoy. Una instrucción desconocida o cualquier mutación de caption/letra/tokens debe seguir fallando.
5. El recibo planned declara candidatos/presupuestos; el captured declara la rama activa y sus tokens verificados. Ambos deben vincularse por hashes y reflejar el transporte real. Mantener fallback legítimo sin códigos y no sustituir el recibo previsto por un cover incondicional.
6. TDD/regresión propuesta: códigos vacíos, whitespace, lista vacía y lista con un elemento no vacío; Turbo/SFT; ambas ramas con IDs correctos; corrupción de instrucción/texto/letra; presupuestos de ambas ramas en el borde y +1; recibos con rama incompatible rechazados. La integración GPU, posteriormente, requiere revisión y preflight propios; estos resultados no validan calidad musical ni capacidad de una canción completa.

## Conservación y límites

Solo se escribieron archivos en `.cache/dev-cycle/t16/native30-diagnosis/`. Producto, runner sellado, imagen y trazas históricas congelados; `delivery-receipt.json` verifica SHA anteriores/posteriores y coincidencia host/imagen. No se ejecutó Git, instalación, build, suite global, GPU, modificación de ledger/docs ni escritura en docs/knowledge.

Los intentos auxiliares de comparar LM inicialmente fallaron porque el helper usaba `Path.read_text`, que normaliza CRLF, y no replicaba la decodificación `utf-8-sig` del CLI. Se corrigió exclusivamente el helper para leer bytes y decodificar como el CLI; el control final verifica igualdad completa LM. Esos fallos auxiliares no son RED de producto ni una causa alternativa del fallo original.

La evidencia RAW permanece privada en `private-error-extract.json` y en los archivos originales; publicar solo este resumen tras revisión. Los IDs finales, instrucciones y código LM del intento GPU no se capturaron directamente. No se reproduce de nuevo ni se establece el estado de las tomas de 90 s.
