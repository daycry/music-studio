# T-08 — QA independiente final de conformidad

2026-10-06. **DONE_WITH_CONCERNS: integración técnica acreditada en el alcance examinado, cero gaps técnicos actuales detectados.** Cotejo CPU de evidencias reales ejecutadas por root; esta QA no ha ejecutado GPU, suite de producto, build, descarga ni instalación. T-08, T-16/main y M0 no se cierran desde esta auditoría.

| Cotejo independiente | Resultado |
|---|---|
| Fuentes y freeze actual | 22/22 SHA coincidentes; antes/después idénticos |
| Evidencia caché precedente | 39/39 artefactos previos, 3/3 baselines y 41/41 artefactos de QA preservados |
| Fuentes copiadas a imagen | 19/19 SHA del probe congelado coinciden con checkout y recibo QA; no nuevo probe de pesos |
| Identidad Docker actual | `docker image inspect` del tag `m0-t08-asr-cache` devuelve `sha256:d20ae562803cb577c290f0229c0df07551a20647be92feca3d678f523b300c62` |
| Build final previo | Recibo de corrección con build exit 0 para esa identidad; Dockerfile base y uv fijados por digest, dependencias git por commit y lock propio congelado |
| Suite GPU canónica de root | JUnit SHA correcto, cuatro casos, cero fallos/errores/skips; 174,941 s. Wrapper documentado añade nombre/owner/JUnit, mantiene `pytest -m gpu -q` |
| Salidas crudas | 4/4 SHA correctos bajo `data/tmp`; tareas, stages y revisiones coinciden con recibo y lock |
| ASR + ForcedAligner secuenciales | Texto no vacío; 87 palabras, tiempos finitos/monótonos hasta 29,92 s; código libera ASR antes de cargar alineador |
| CLAP | Score finito en [-1,1], `text_truncated=false` |
| Audiobox | Exactamente CE/CU/PC/PQ, todos finitos |
| Beats | 120 BPM, tolerancia ±2 cumplida y 61 beats; descriptor y ruta del backend CPU |
| Hijo y unload | Test común usado por los cuatro casos afirma supervisor vivo/PID distinto, HTTP unload 200 y supervisor terminado |
| QA CPU previa actual | JUnit de 48 casos, 0 fallos/errores/skips; no ejecución propia de esta auditoría |
| CLAP histórico preservado | 14/14 artefactos y 18/18 fuentes sin delta coinciden. Dockerfile/README/tag Compose son los tres deltas legítimos posteriores; no se exigen sus SHA históricos al checkout actual |
| Ledger fresco | 0 incoherencias, 7 avisos de Changelog; exit 0 |

El probe previo de la imagen acredita UID10001, caché Triton real writable, propietario10001, modo0755, padre inicialmente sin Torch y CUDA no inicializada. Los SHA del probe y sus fuentes se verificaron ahora. Compose congelado sin interpolación acredita puerto exclusivamente 127.0.0.1:8130, /models y /data RO, /data/tmp RW, token por placeholder y reserva NVIDIA. No se leyó `.env`, ni se imprimió o probó un token. Las fuentes actuales coinciden con ese Compose; no se repitió su expansión. El incidente anterior de token interpolado permanece documentado y sanitizado; no se elimina ni se presenta como una ejecución nueva segura que borre lo ocurrido.

Se cotejaron fuentes de `adapter.py`, `backend.py`, `safety.py`, `descriptor.py`, Dockerfile, pyproject y test GPU. El verificador exige bytes/SHA para recursos fijados, rechaza recursos no fijados y carga pesos safetensors estrictos. Qwen usa local_files_only, use_safetensors y trust_remote_code=false; los otros loaders usan safetensors y strict=True. AST de código propio no contiene llamadas torch.load/pickle.load. No se rehasharon pesos completos ni se lanzó un modelo. Las filas legales de Qwen-ASR, ForcedAligner, LAION, Audiobox, beat_this y dependencias están registradas; se conservan sus advertencias de atribución/datos/redistribución. Constitución §2 y §4 respetadas en el alcance examinado.

Los tres CA técnicos de T-08 cuentan ahora con evidencia de configuración/build, tareas reales y residencia/descarga. El orquestador determina su estado y cierre tras resolver la integración dependiente de T-16; esta QA no altera CA ni ledger. `audio.align_lyrics` independiente y las capacidades siguen `verified=false` hasta M3/T-10: es estado pendiente de validación, no una afirmación de baja calidad.

**Límites pendientes:** ASR autodetecta English con letra castellana. El recibo heurístico muestra 84/86 tokens presentes en vocabulario de referencia y 43 contiguos; no es ground truth temporizado ni WER. Idioma explícito/precisión, fidelidad y calidad musical siguen pendientes. Pico VRAM y spill son null en esta suite; post-GPU y unload no acreditan un pico o ausencia de spill. T-09–T-13, escucha y M0 siguen abiertos. No se regenera por estos límites sin una necesidad nueva.

ℹ️ sin UI por diseño (`test-plan: n/a (sin UI)`). E2E/qa-gate n/a: no se fabrica JSON de reporter ni verde E2E. Coverage-check no ejecutado en esta nueva lectura; existe antecedente applies=false. Cobertura del delta de configuración n/a; el backend CLAP conserva su antecedente oficial 88,94 % y no se lo atribuye a esta QA. PDF pendiente por herramientas ausentes, sin instalar. No hay checklist E2E manual definida para esta tarea backend; los pendientes de fidelidad/escucha anteriores requieren sus tareas canónicas.

Evidencia propia: [recibo](conformance-qa-receipt.json), `.cache/dev-cycle/t08/conformance-qa/before.json`, `.cache/dev-cycle/t08/conformance-qa/after.json`, `.cache/dev-cycle/t08/conformance-qa/probe.py`, `.cache/dev-cycle/t08/conformance-qa/ledger-lint.log`. Todos los escritos se limitan a `.cache/dev-cycle/t08/conformance-qa/`. Sin Git, ledger, docs públicas, conocimiento ni cachés ajenas modificados.

Publicación del orquestador: se adaptan únicamente los enlaces de evidencias privadas al destino público; el informe original y sus SHA se conservan en el recibo.
