# M-03 - backup y restauracion tecnica (2026-10-10)

Se ejecuto sobre una copia nueva, sin detener ni borrar la base activa:

```powershell
. .\scripts\env.ps1
uv run --package server python .cache/m03-backup-current/run_backup.py
```

Resultado: `backup()` creo `studio-backup-20261010T075836Z.sqlite`; `restore_backup()` creo una base nueva de 2.228.224 bytes. La comprobacion posterior devolvio `integrity=ok`, `foreign_key_errors=0` y 39 tablas. SHA-256 del backup: `bbab547954b1bb22468941693ce769032e30e97a0181549a35a8a7b7e474e6a0`.

Esta evidencia cubre el roundtrip tecnico y no sustituye M-03 manual: restauracion de la biblioteca real sobre el volumen persistente y `verify_manifest.py data/songs/` con canciones reales.
