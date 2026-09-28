# ADR-0009 · Formatos de audio y loudness

- **Estado:** aceptada · **Fecha:** 2026-09-28 · Hereda D-09 y D-23 de la documentación archivada

## Decisión

**Almacenamiento**
- `master.flac`: 24 bit, frecuencia de muestreo nativa (48 kHz en ACE-Step), sin normalizar.
- `listen.mp3`: 320 kbps, a −14 LUFS y ≤ −1 dBTP.
- No se guarda WAV. El WAV a 48 kHz se genera al exportar, remuestreando con soxr.

**Exportación por destino**

| Destino | Loudness integrado |
|---|---|
| Streaming | −14 LUFS |
| Vídeo / broadcast (EBU R128) | −23 LUFS |
| Podcast | −16 LUFS |
| Stems | Sin normalizar |

En todos los destinos, pico verdadero ≤ −1 dBTP.

**Normalización**
- Se mide con pyloudnorm, o con ffmpeg `ebur128`, y se aplica **ganancia lineal**. No se usa `loudnorm` dinámico.
- El **pico verdadero** se mide con ffmpeg `ebur128=peak=true` o con sobremuestreo ×4 (BS.1770). pyloudnorm no mide pico verdadero.
- Si aplicar la ganancia hiciera superar −1 dBTP, se pasa un limitador y queda anotado en el manifiesto.

**Herramientas**
- ffmpeg en build **LGPL**: `win64-lgpl` en el server; `linux64-lgpl-shared` en los engines que la necesiten para torchcodec.

El detalle está en [`../arquitectura/pipeline-audio.md`](../arquitectura/pipeline-audio.md).
