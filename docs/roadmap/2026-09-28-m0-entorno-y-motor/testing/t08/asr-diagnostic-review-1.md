# T-08 — revisión 1 del diagnóstico privado ASR

2026-10-06. Lentes A+B+D frescas e independientes de implementar. Propuesta completa de dos scripts sobre baseline ausente, producto8663287 e imagen306e3b0. Scope0 sin avisos ni exclusiones de usuario. Selector C=false/D=true por ruta cache. El rechazo inicial de D por límite de threads está preservado en el [parcial](asr-diagnostic-review-1-in-progress.md); tras terminar el implementerT16, D pudo ejecutarse en contexto nuevo.

| Criterio | A | B | D |
|---|---|---|---|
| Factory, hijo real y padre sinTorch | Conforme, import/preflight CPU | Conforme, éxitoPID7→11/fallo16→20 | Delegación una vez, sin paralelismo |
| Loaders/cap/preflight originales | Conforme | Conforme, libre−512 | Sin trabajo repetido por carga |
| Entrada confinada/SHA/terminal/exit | Conforme, rechazo n_outputs2 | Éxito0/fallo2, terminal único | O(bytes+eventos+trazas), sin bucles anidados |
| Trazas privadas y metadatos mínimos | Conforme | Conforme | Doce emisiones para dos fases en proxy CPU |
| Descarga y borradoTMPfallido | Conforme CPU | Ambos descargados, falloTMPborrado | Un job secuencial |
| Alcance y preservación | Dos SHA conformes | Dos archivos completos | Wrapper1–94/runner1–60, SHA/AST/compilación conformes |
| GPU real, causaASR y precisión | Pendientes | Pendientes | Timeout600 transmitido, inferencia real no medida |

Cero Critical/Important/Minor; sin rebates ni deuda. A y B evidencias detalladas en parcial. D ejecutó entorno gestionado Python-B, SHA/AST/compilación y proxy backend/sink en memoria: REVIEW_D_CPU_STATIC_AND_PROXY_OK, exit0. Sin GPU, pesos, lectura de entradas/trazas privadas, producto, Git, ledger ni conocimiento. C no aplica según selector. No se atribuye cancelación real, QA o causalidad ASR a estas revisiones.

Siguiente puerta: QA independiente del arnés privado, luego una única ejecución diagnóstica GPU30s si preflight nuevo cumple baseline≤1600MiB/Ollama vacío y no hay otro modelo activo. T08/M0 siguen abiertos; CLAP GPU ya pasó en su ejecución separada.
