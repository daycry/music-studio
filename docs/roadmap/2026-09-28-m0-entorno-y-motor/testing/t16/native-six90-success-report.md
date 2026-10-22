# T-16: seis tomas nativas y paquete real de escucha

La comparación de la sesión `01M47Q4EJZK09RBPA0ECWC57D4` terminó con seis tomas de 90 segundos y tres pares privados. Generación y empaquetado corregido: exit0. [Recibo portable](native-six90-success-receipt.json). No se declara ganador ni mejora musical.

Se verificaron los seis maestros FLAC PCM24, 48 kHz, estéreo, finitos y no silenciosos, sus manifiestos y recibos nativos v2. Letra/caption de control por hash, BPM94/es, shift1, LM0,6B/BF16/PT y controles LM/DiT/metadata iguales por semilla. Turbo8 frente a SFT50/CFG7 compara configuraciones completas. Los textos y el mapa de códigos se conservan privados.

| Grupo | Tiempo de pared del job | Baseline VRAM | Descarga y contenedor propio |
|---|---:|---:|---|
| Turbo, tres tomas | 258.078 s | 1314 MiB | Confirmadas |
| SFT, tres tomas | 270.078 s | 1314 MiB | Confirmadas |

Pico comunicado máximo 7893.35 MiB frente a cap mínimo 10114.70 MiB; `spilled=false` en las seis. Esto es telemetría del proceso/heurística, no una medición de memoria GPU compartida de Windows. `run_s` incluye carga y se comparte por batch: no sumarlo tres veces ni presentarlo como RTF directo de inferencia. La matriz de rendimiento sigue pendiente en T-09.

El packer corregido182e7f91 valida envelopes planned/captured reales, normaliza con ganancia lineal y crea manifiestos hijos con linaje, sin sobrescribir maestros ni atribuir al hijo recibos de generación. Nivel común -17.0425 LUFS; seis copias entre -17.0419 y -17.0400 LUFS, pico máximo -1.9 dBTP. Sin compresor ni limitador. Referencia Suno copiada íntegra por SHA, con volumen de reproducción explícito; sus secciones no están sincronizadas con los fragmentos locales.

La página de escucha está servida en [8768](http://127.0.0.1:8768/listen.html). Comprobación real HTTP22/22: GET/HEAD de página, seis MP3 y referencia, tipos/longitudes/bytes exactos; seis rutas privadas/listados rechazadas404. La política del navegador rechazó abrir este origen localhost; no se intentó otra vía. Render visual y valoración auditiva no acreditados. Servidores históricos8766/8767 preservados.

QA independiente del fullpack conforme: [113 comprobaciones reales](native-fullpack-qa-report.md), 61 fuentes inmutables y seis recodificaciones lineales idénticas por SHA. Verificación canónica: 21 manifiestos CLI y seis de escucha válidos. La evidencia privada íntegra y sus SHA figuran en el recibo. Las revisiones de código y QA de contrato/HTTP previas están en [contrato](native-packer-contract-qa-report.md) y [listener](native-listener-qa-report.md). M0 permanece abierto.
