---
id: ADR-0031
titulo: Transcripción segmentada con tiempos globales y residencia secuencial
estado: aceptada
fecha: 2026-10-06
---

# ADR-0031 — Transcripción segmentada con tiempos globales

## Contexto

La revisión2 de T-08 confirmó que aceptar600s y enviar todo el audio al ForcedAligner no garantiza tiempos representables. El config local fijado contiene5000 clases de80ms: máximo399,92s. Un probe CPU por la rama productiva entregó450s y publicó tiempos limitados a399,92s; no demuestra precisión del modelo, pero sí el uso de una ventana temporal insuficiente. La receta Qwen fijada usa fragmentos de180s al producir timestamps.

[ADR-0030](ADR-0030-analisis-local-y-alineacion-secuencial.md) conserva ASR y alineador secuenciales. La solución debe mantener esa residencia única, texto reconocido sin letra esperada y tiempos derivados del modelo. El propietario ha delegado las decisiones técnicas dentro de la implementación del roadmap; se elige la alternativa que conserva el alcance de transcripción hasta600s.

## Alternativas

| Opción | Ventaja | Limitación |
|---|---|---|
| Reducir la transcripción a180s | Cambio pequeño | Recorta el alcance de canciones completas y la entrada ya admitida; descartada |
| Repartir el texto completo entre ventanas por longitud | Evita conservar reconocimientos por fragmento | Puede asociar palabras al audio equivocado y fabricar offsets; descartada |
| Reconocer fragmentos, descargar ASR y alinear esos mismos fragmentos | Conserva hasta600s y correspondencia audio/texto real | Requiere conservar límites, textos e idiomas por fragmento; elegida |
| ASR y alineador juntos por fragmento | Receta combinada directa | Dos modelos residentes o recargas reiteradas; incumple la residencia fijada o añade coste innecesario |

## Decisión

`audio.transcribe` conserva el máximo600s. El backend reconoce fragmentos contiguos de hasta180s y conserva `start_s`, `end_s`, texto e idioma reconocidos de cada uno. El texto agregado procede de esos reconocimientos; el idioma agregado conserva la semántica upstream. Los fragmentos cubren el audio, incluidos silencios; no se inventa texto ni palabras para silencio.

Después de reconocer todos los fragmentos, se libera ASR una vez y se carga ForcedAligner una vez, con el cap dinámico actual. Se alinean las mismas porciones de audio con sus propios reconocimientos/idiomas y se suman sus offsets reales a los tiempos locales. Se valida el resultado antes de publicarlo como JSON crudo. No se reparte texto por heurística, no se sustituye por la letra esperada y no se presentan ventanas uniformes como tiempos por palabra.

La tarea independiente `audio.align_lyrics` permanece preparada y sin verificar hastaM3. Un texto aportado completo no trae por sí mismo correspondencia entre fragmentos de audio y texto. Hasta implementar y validar esa asociación enM3, el backend y descriptor deben declarar el límite180s de esa ruta independiente y rechazar entradas mayores de forma explícita. La limitación no se aplica a la transcripción segmentada ni elimina el requisito de alineación de canciones completas deM3.

Idioma no soportado y audio no decodificable son errores de entrada `INVALID_PARAMS`; no deben disfrazarse como `INTERNAL`, ni esta clasificación debe ocultar fallos internos o VRAM. El padre continúa sin torch/CUDA y la salida conserva procedencia y etapas. No cambia el contrato `/v1`, la escritura exclusiva del server enBD ni el linaje de takes.

## Consecuencias y verificación

Los límites y reconocimientos por fragmento permiten recomponer tiempos globales para canciones completas sin duplicar residencia. Puede haber efectos de corte en la precisión; requieren medición WER/escucha y no se declaran resueltos por tests de transporte. Las pruebas CPU deben reproducir el defecto anterior y comprobar correspondencia, offsets posteriores a400s, bordes y residencia; la inferencia GPU y precisión siguen pendientes.

Implementación actual: T-08 fix2, con RED previo y revisión3/QA pendientes. Esta decisión no declara el código terminado ni capacidades `verified=true`. [Informe de revisión2](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t08/review-2.md).
