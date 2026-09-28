---
documento: pipeline-audio
titulo: Pipeline de audio — post-proceso, formatos y exportación
estado: vigente
fecha: 2026-09-28
actualizado: 2026-09-28
---

# Pipeline de audio

Se ejecuta en el **worker CPU del server** (paquete `packages/audio-post`) sobre la salida en crudo del engine ([ADR-0017](../decisiones/ADR-0017-postproceso-y-manifiesto-en-el-server.md)). En M0 lo invoca el CLI `scripts/generate.py`.

## 1. Etapas tras la inferencia

```
salida cruda del engine (WAV/FLAC float32, sr nativo; ACE-Step = 48 kHz estéreo)
  → validación: duración ±5 % de la pedida, sin NaN/Inf, no silencio (RMS > −60 dBFS),
                sin clipping sostenido (> 0,5 % de muestras a ±1,0)
  → medición: loudness integrado (pyloudnorm, BS.1770-4) y true peak (ffmpeg ebur128=peak=true)
  → master.flac : 24 bit, sr nativo, SIN normalizar
  → listen.mp3  : 320 kbps CBR, ganancia lineal hasta −14 LUFS; si el true peak resultante
                  > −1 dBTP → limitador suave (ffmpeg alimiter) y se anota en el manifiesto (post.limiter)
  → peaks.json  : ~2.000 pares min/max por canal (formato compatible con wavesurfer.js)
```

- **Ganancia lineal**, nunca `loudnorm` dinámico: `loudnorm` puede pasar a modo dinámico sin avisar y cambiar la mezcla.
- **Remuestreo** con soxr (`aresample=resampler=soxr`), solo cuando el destino lo pide (p. ej. 48 → 44,1 kHz para MP3, si hiciera falta).
- La lectura y escritura propias usan **soundfile** y **ffmpeg**, nunca torchaudio (ver [entorno.md](./entorno.md), E-07).

## 2. Exportación a demanda (M3)

| Destino | Formato | Loudness | Notas |
|---|---|---|---|
| **Streaming / web** | MP3 320 o FLAC | −14 LUFS, ≤ −1 dBTP | Opción por defecto |
| **Vídeo / broadcast** | WAV 48 kHz, 24 bit | −23 LUFS (EBU R128), ≤ −1 dBTP | Para Premiere, DaVinci o Avid |
| **Podcast** | WAV 48 kHz o MP3 | −16 LUFS, ≤ −1 dBTP | |
| **Stems** | WAV/FLAC 48 kHz por pista, en un zip | Sin normalizar | Alineados sample a sample con la mezcla |
| **Original** | `master.flac` tal cual | Sin tocar | |

Metadatos que se escriben al exportar:

- título, artista y año;
- comentario con el `take_id`;
- letra embebida (ID3 `USLT` o Vorbis `LYRICS`), si se pide;
- portada, si existe (M3).

## 3. ffmpeg

- **Server (Windows):** build BtbN `win64-lgpl` en `tools/ffmpeg/`, fijada en `tools/tools.lock.json`.
- **Engines (Linux):** build BtbN `linux64-lgpl-shared`, porque torchcodec necesita las `.so`.
- **Comprobación en build o arranque:**
  - `-buildconf` **contiene** `--enable-libmp3lame`, `--enable-libsoxr` y `--enable-libopus`;
  - **no contiene** `--enable-gpl` ni `--enable-nonfree`.

## 4. Stems (M3)

Hay dos vías, según [modelos.md](./modelos.md) §4:

- la tarea `audio.stems` del generador (el extract de ACE-Step, que requiere el checkpoint base);
- un separador dedicado, que se carga después de descargar el generador de la VRAM.

Los stems se guardan como `asset` del take (`role=stem:vocals`, etc.); no generan un take nuevo. **Prueba de conformidad:** la suma de los stems se compara con la mezcla y el error debe quedar por debajo de −30 dB.
