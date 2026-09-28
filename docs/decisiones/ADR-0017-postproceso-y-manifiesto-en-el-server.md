# ADR-0017 · Post-proceso, manifiesto y render en el server; los engines devuelven salida cruda

- **Estado:** aceptada · **Fecha:** 2026-09-28

## Contexto

Varios documentos se contradecían sobre dónde se hace el post-proceso: en el engine o en el server. Además, el engine no conoce `song_id`, `take_id` ni el linaje, así que no puede escribir un manifiesto correcto.

## Decisión

- **Los engines devuelven salida cruda** en `data/tmp/<job_id>/` (WAV/FLAC en float, PNG, MP4 o JSON) junto con su telemetría. Nada más.
- **El server tiene un worker CPU** (carril `cpu` del dispatcher, sin torch) que hace:
  - el post-proceso de audio (paquete `packages/audio-post`): validación, medida de loudness y true peak, `master.flac`, `listen.mp3` y `peaks.json`;
  - el **manifiesto** de todo artefacto;
  - el traslado a `data/songs/…`;
  - el **render de vídeo y las exportaciones** con ffmpeg;
  - los backups.
- **ffmpeg en el server**: build **LGPL** para Windows (BtbN `win64-lgpl`, con libmp3lame, libopus y libsoxr), en `tools/ffmpeg/` dentro de la carpeta del proyecto y fijada por versión y SHA-256. La descarga la hace `scripts/fetch_tools.py`.
- **En M0 no hay server**: el CLI `scripts/generate.py` usa el mismo `audio-post` y el mismo escritor de manifiestos. Así el código de M0 se reaprovecha tal cual en M1.

## Consecuencias

- Los engines son más simples, y cambiar de modelo no cambia el formato de los ficheros que se guardan.
- El manifiesto tiene todo el contexto: canción, linaje, entradas con derechos y proveedor.
- Los engines necesitan ffmpeg solo si su upstream lo requiere internamente. ACE-Step lo necesita por torchcodec: se instala la build `lgpl-shared` y el adapter escribe con soundfile ([`../arquitectura/entorno.md`](../arquitectura/entorno.md)).
