# Comprobación diferencial CPU de T-19

- **Estado:** conforme para las plantillas, tokenizadores y fronteras reproducidas; integración CPU realizada, revisión y QA T-19 pendientes
- **Fecha local:** 2026-10-06
- **Recibo público:** [native-receipt.json](native-receipt.json)
- **Refuerzo de backend PT:** [native-pt-receipt.json](native-pt-receipt.json)
- **Contexto:** [auditoría T-17](../t17/audit-report.md), [criterios T-19](../../tasks.md) y [ADR-0029](../../../../decisiones/ADR-0029-presupuesto-operativo-de-texto-acestep.md)

El probe compara el plan del preflight con la llamada a `generate_music`, las plantillas LM y el condicionamiento textual DiT del upstream fijado. Usa sus tokenizadores locales y comprueba 16 archivos de configuración/tokenizadores contra el lock. La inferencia del LM se sustituye por un código sintético; el DiT se detiene tras preparar texto. CUDA oculta, sin GPU expuesta ni pesos musicales cargados.

**Resultado:** 16 casos comprobados, diez aceptados y seis bloqueados, exit 0. Los casos C007–C010 y las variantes de Libre con estilo original se rechazan por presupuesto. Las adaptaciones conservadas y el candidato fiel caben. En los casos aceptados coinciden los hashes de tokens calculados por el preflight y obtenidos en las fronteras reales reproducidas; se capturan argumentos LM, prompt formateado LM, argumentos DiT y tokens DiT.

| Candidato fiel de Libre | Conteo |
|---|---|
| LM conditional | 1131 tokens |
| LM unconditional | 33 tokens |
| DiT descripción y metadata | 172 tokens |
| DiT letra y cabeceras | 970 tokens |

La metadata YAML del LM contiene `language: es`. Los recibos distinguen planificación de captura. Ningún rechazo trunca para aceptar. La presencia de los tags en tokens no acredita interpretación musical ni naturalidad de voz, ritmo o instrumentación.

El probe inicial comprueba conditional y calcula unconditional con el método nativo. El refuerzo posterior recorre además `generate_from_formatted_prompt → _run_pt → _run_pt_single` reales, sustituyendo el forward por un tensor sintético y sin cargar un modelo. Captura los IDs y máscaras de las dos ramas CFG antes de inferir; sus conteos, hashes y reserva completa de salida coinciden con el preflight en los diez casos aceptados. Exit 0, 16 casos y seis bloqueados. Un intento intermedio falló por una fixture que exigía `skip_genres` aunque faltaba en `cfg`; se corrigió delegando en los defaults upstream reales, sin modificar producción para pasar la fixture. Evidencias previas preservadas; recibo reforzado en carpeta privada `probe3`.

Las primeras comprobaciones se ejecutaron con la **imagen existente T-14**, el código T-19 del host montado solo lectura y el upstream instalado en `/opt/acestep`. Esos recibos no afirman que T-14 incorpore el código nuevo. Después se reconstruyó la imagen y se comprobó su producción integrada, sin overlay del host: [recibo integrado](native-integrated-receipt.json) e [informe de integración CPU/HTTP](integration-report.md). Las evidencias anteriores se conservan como historial.

Reproducción privada: `.cache/dev-cycle/t19/verify-native-preflight.py`, corpus T-17 original de 16 casos solo lectura y salidas nuevas `native-public.json`/`native-private.json`. Los recibos T-17 y originales no se regeneraron ni sobrescribieron. El recibo público contiene conteos y hashes; los textos y parámetros completos permanecen privados.
