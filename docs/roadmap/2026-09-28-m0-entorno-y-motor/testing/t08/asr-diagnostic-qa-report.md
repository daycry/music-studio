# QA independiente CPU del diagnóstico ASR privado

Estado: **DONE_WITH_CONCERNS**. 40 comprobaciones conformes; dos jobs reales mediante el runner congelado y dobles de cálculo CPU, más dos rechazos negativos esperados. No se atribuye este resultado a inferencia GPU ni se cierra T-08/M0.

| Caso | Exit real | Terminal único | Padre PID | Hijo PID | Trazas |
|---|---:|---|---:|---|---:|
| success | 0 | done | 9 | [13] | 13 |
| failure | 2 | error | 18 | [22] | 7 |

Verificados SHA de los dos scripts, AST, importación sin Torch, preflight original (rechaza n_outputs=2 y role=image), entrada confinada y SHA, factory del runner real, PID/PPID distintos, un solo hijo y terminal, padre sin Torch antes/después, descarga, borrado TMP del fallo y conservación de trazas fuera de TMP. Los metadatos no contienen audio, texto, letra, captions, params ni tokens. El fallo RuntimeError es una fixture declarada; no es un fallo de producto. Los casos wrong-sha y escaped-path rechazan antes de crear trazas con exit1 esperado.

Audio propio: WAV sintético de silencio, mono PCM16/16000Hz/1s, SHA256 643f8a8dc8bd9c19225afffad2becfec5426180b3749cb208abdf1a6c8354efc. Generado exclusivamente dentro de /data tmpfs; ningún audio original leído. Lock RO SHA256 a6874200535337a2236004aa24a535603110a19b4499e743bc73431518f49e4e; no hay pesos montados.

Imagen inmutable sha256:306e3b0fbc1170ee066e2aed099ef6638ea7dad7faf3ab5b67edfa90e64b70c9; baseline producto8663287, sin rebuild ni cambios de producto. Python de contenedor: 3.12.3 (main, Jul 15 2026, 23:46:41) [GCC 13.3.0]. Host gestionado mediante scripts/env.ps1, Python3.12.14; sin instalaciones.

Comando Docker ejecutado: docker run --rm --network none --read-only --tmpfs /data:rw,size=64m --tmpfs /tmp:rw,size=64m -e CUDA_VISIBLE_DEVICES= -e NVIDIA_VISIBLE_DEVICES=void -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/diagnosis:/studio/apps/engines/analysis -v <diagnosis_wrapper.py>:/diagnosis/diagnosis_wrapper.py:ro -v <run_one_job.py>:/diagnosis/run_one_job.py:ro -v <lock>:/models/models.lock.json:ro -v <probe.py>:/qa-probe/probe.py:ro -v <carpeta QA>:/qa-output:rw --entrypoint python <digest> /qa-probe/probe.py. Sin --gpus; ausencia de /dev/nvidia* comprobada. Red none; scripts y lock RO, data tmpfs, destinos nuevos exclusivos por pasada.

Incidencia de fixture: primer Docker exit1 por PYTHONPATH sin la ruta del paquete de la imagen (ModuleNotFoundError: engine_analysis), antes de jobs. Se añadió /studio/apps/engines/analysis a PYTHONPATH, sin cambiar fuentes. Primera pasada corregida: exit0, 38 checks, dos jobs (success/failure). Segunda pasada amplía con los dos negativos: exit0, 40 checks; destinos final-success/final-failure nuevos. Evidencia de la primera pasada permanece en success/failure; los stdout/stderr propios de cada modo corresponden a la pasada final. No se ejecutó ninguna suite ajena.

Evidencia final y comandos del runner: probe-results.json; summaries y trazas en final-success/ y final-failure/. Receipt congela SHA de fuentes y artefactos privados, incluido el probe. Ninguna traza privada anterior leída.

Sin UI: coverage-check applies=false, qa-gate n/a; no Playwright, E2E UI, porcentaje de cobertura ni PDF declarados. No ejecución de GPU, pesos, red, instalaciones ni lectura/escritura de conocimiento. Escritura limitada a esta carpeta QA; ledger/docs/Git/meters quedan al orquestador.

Pendiente: ejecución ASR GPU diagnóstica autorizada por root con preflight nuevo, inferencia/precisión reales, causalidad del fallo ASR y cierre de T-08/M0. Este pase CPU permite preparar esa siguiente prueba, sin conceder autorización GPU por sí mismo.
