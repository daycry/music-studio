# M-03 · saneamiento de staging y verificación de manifiestos — 2026-10-10

## Alcance

Se comprobó la biblioteca actual después del backup/restauración técnico de M-03, sin borrar ni reescribir la base viva.

## Evidencia ejecutada

- `docker compose ps --all`: únicamente `engine-acestep` permanecía activo; no había server ni worker que pudiera estar publicando.
- Se localizaron tres directorios `data/songs/**/takes/.pending-*` huérfanos. Dos contenían un `manifest.json` que fallaba con `PRIVATE_CONTEXT_INVALID`; el tercero no contenía manifiesto.
- Se recorrieron todas las columnas de texto de `data/db/studio.sqlite` buscando los IDs de canción, ejecución, take y staging. No hubo referencias.
- Los tres directorios se movieron con `shutil.move` a `.cache/dev-cycle/m03/pending-quarantine-20261010/`, conservando los archivos y registrando ruta, tamaño y SHA-256 en `receipt.json`.
- Verificación posterior: `uv run --package audio-post python scripts/verify_manifest.py data/songs/` devuelve `MANIFEST_MISSING`.

## Interpretación

El saneamiento elimina staging huérfano de la biblioteca publicada sin ocultar un manifiesto inválido. La biblioteca actual contiene snapshots `song.json`, pero no manifiestos `audio_take` publicados; por eso la aceptación manual M-03 sigue pendiente. Este recibo no cierra T-02 ni T-16.
