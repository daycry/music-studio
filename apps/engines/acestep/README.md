Adaptador y Dockerfile del engine de música ACE-Step; proyecto uv independiente, fuera del workspace de la raíz, con torch propio. El padre HTTP permanece sin torch y los modelos se ejecutan en un proceso hijo. El estado y la evidencia de M0 viven en el ledger del hito.

El adaptador admite `shift` opcional (número finito de 1 a 5) para comparar distribuciones de pasos de inferencia. Omitirlo conserva el default upstream 1; no cambia las capacidades `verified` ni el modelo. El CLI lo transmite con `--shift`. [ADR-0026](../../../docs/decisiones/ADR-0026-comparacion-controlada-shift.md) recoge la comparación privada de M0/T-14; la recomendación upstream de 3 para Turbo no constituye una aprobación de calidad local.

## Controles de Turbo y SFT

El checkpoint configurado con `STUDIO_ACESTEP_CHECKPOINT` determina la identidad anunciada. Turbo sigue siendo el default; seleccionar SFT no cambia automáticamente el motor por defecto del proyecto ni verifica capacidades. El CLI descubre la identidad del catálogo del engine.

| Checkpoint | Identidad | Pasos por defecto y rango | CFG explícito |
|---|---|---|---|
| `acestep-v15-turbo` | `ace-step-1.5-turbo` | 8; enteros 1–8 | Rechazado |
| `acestep-v15-sft` | `ace-step-1.5-sft` | 50; enteros 1–200 | Default7; número finito 1–20 |

El CLI expone `--inference-steps` y `--guidance-scale`, también sobre briefs. Se registran los valores explícitos del pedido y se validan los controles efectivos en el adaptador, preflight y recibos de entrada. Booleanos, nulos, cadenas y valores fuera de rango se rechazan; los pasos tampoco admiten fracciones. El progreso y la cancelación usan el número efectivo de pasos.

La frontera de entrada a DiT conserva el valor7 histórico de GenerationParams en Turbo; su handler fuerza después guidance_scale=1 porque Turbo no aplica CFG como SFT. Capturar argumentos a la entrada no acredita el valor interno del sampler ni calidad musical. [ADR-0027](../../../docs/decisiones/ADR-0027-controles-de-inferencia-sft.md) documenta la configuración completa y la comparación con transporte emparejado.

Los tokenizadores, plantillas, reserva LM y límites DiT se comprueban antes de aceptar entradas; ninguna opción permite truncar instrucciones silenciosamente. Las pruebas CPU de controles no equivalen a inferencia GPU ni aprobación por escucha.

## Resolución del condicionamiento DiT

Los recibos nuevos usan `receipt_version: 2`. Antes de cargar modelos se ejecuta el resolver puro de la revisión upstream fijada y se presupuestan sus dos resultados legítimos: `text2music` sin códigos LM y `cover` con códigos no vacíos. La solicitud pública sigue siendo música desde texto. No se presupone que el LM producirá códigos. El resumen HTTP incluye la versión y ambos candidatos en `dit`; los registros `text` y `lyrics` conservan el candidato sin códigos como referencia.

La captura registra tipo inicial, presencia booleana de códigos, tipo resuelto y SHA-256 de la instrucción, sin guardar códigos ni textos en esa frontera. La instrucción efectiva y los IDs activos del tokenizador deben coincidir exactamente con el candidato elegido; instrucciones desconocidas, mutaciones y truncamiento siguen rechazados. CLI y manifiesto validan la rama y su vínculo con el planned antes de publicar. Los recibos v1 se leen con su política histórica, sin atribuirles esta frontera nueva. [ADR-0032](../../../docs/decisiones/ADR-0032-condicionamiento-dit-segun-rama-nativa.md) recoge la decisión.
