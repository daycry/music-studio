# QA independiente del paquete real T-16

Conforme: 113 comprobaciones; 6 padres, 6 hijos y referencia decodificados.

Freeze de 61 fuentes, idéntico antes/después. Tres pares iguales por LM, DiT y metadatos; recibos nativos y manifiestos validados. Masters PCM24 48 kHz/estéreo/90 s; MP3 48 kHz/estéreo/90 s. Audio finito y no silencioso. Linaje y hashes source_master conformes.

Objetivo -17.042502361895934 LUFS. Medición independiente con audio_post.measure_audio/FFmpeg bloqueado. Seis recodificaciones volume-only son bit a bit idénticas: sin limitador ni compresor. Referencia original copiada exactamente por SHA, duración 227.64097916666665 s.

Detalles y SHA: [recibo](native-fullpack-qa-receipt.json). Freeze privado: freeze-before-private.json y freeze-after-private.json; contienen rutas relativas y no se publican como mapa.

Límites: sin escucha musical, ganador ni crecimiento/final de canción completa; sin GPU nueva, HTTP o UI. No cierre de T-16/M0 ni CA. PDF pendiente: no se instala renderer. Fuente de uso estimada; tokens, EUR y horas null; ventana combinada de root.

Comando: `. ./scripts/env.ps1; $env:PYTHONUTF8=1; uv run --frozen --no-sync --all-packages python .cache/dev-cycle/t16/native-fullpack-qa/verify_real.py` (exit 0).
