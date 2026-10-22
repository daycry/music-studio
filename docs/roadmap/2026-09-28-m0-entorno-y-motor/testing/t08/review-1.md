# T-08 — revisión intento 1: corrección obligatoria, pasada incompleta

Fecha: 2026-10-06. A/C completaron su alcance CPU; B fue interrumpida expresamente por el orquestador al confirmar dos defectos de la entrega original. El handle pasó de `running` a `interrupted`, comprobado con `list_agents`. No se infiere una terminación a partir de un timeout ni se considera B conforme. La causa del cambio de paso es evidencia reproducida, no tiempo de espera. [Recibo de los dos RED en la ruta real](clap-route-red-receipt.json).

A/C comparten contexto reutilizado de QA T-19; B reutilizaba revisión T-17. Son contextos independientes de implementar, pero no frescos. D=false por selector; C=true por Docker y disparadores del diff. [Cobertura parcial A/C](review-in-progress.md) y [entrega CPU original](cpu-delivery-report.md) conservadas.

| Criterio | Veredicto del intento 1 |
|---|---|
| Base, dependencias, servicio y beats | Conforme en evidencia CPU A; GPU pendiente |
| Loaders y pesos seguros | A/C sin gaps en su alcance; B incompleta |
| Transcripción y tiempos | Dobles conformes; inferencia GPU pendiente |
| Preprocesamiento y salida CLAP | **No conforme: dos defectos reproducidos** |
| Residencia, child y unload | CPU/beat conforme; memoria GPU pendiente |
| Constitución, licencias, RED y cobertura original | A/C conformes en lo leído, sin extender a QA |
| Corrección global y verificación completa | **No aprobadas**: B incompleta, fix y QA pendientes |

| ID | Grado | Gap y escenario | Evidencia | Veredicto |
|---|---|---|---|---|
| R-CLAP-01 | Important | `backend.py:280–287` propaga `truncation=False` al audio; CLAP real rechaza un audio de 30 s | Probe real y `LocalBackend.run` con procesador real: `NotImplementedError: data_truncating False not implemented` | Pendiente de fix1 |
| R-CLAP-02 | Important | `backend.py:304` accede a `chunk_length_s`, atributo inexistente del extractor fijado; audio de 1 s llega al retorno y falla | `LocalBackend.run` con extractor real: `AttributeError: 'ClapFeatureExtractor' object has no attribute 'chunk_length_s'` | Pendiente de fix1 |

Los dos gaps los confirmó el orquestador sobre la investigación CPU, **no son un informe final emitido por B**. La reproducción de ruta completa usa `ClapProcessor`, `ClapFeatureExtractor` y `RobertaTokenizer` reales 4.57.6, vocabulario/merges y audio sintéticos; solo el modelo de embeddings es un doble para evitar pesos e inferencia. Conserva la lógica productiva de `LocalBackend.run`. El RED dirigido final da dos fallos reales, sin fallos de fixture, y dos avisos de parámetro `audios` deprecado, en4,06s. La primera observación mostró también dos avisos de caché pytest sin permiso; se corrigió su destino antes de la captura final. No se confunde ese forward doble con una métrica real.

Evidencia privada nueva: `.cache/dev-cycle/t08/clap-route-regression/test_clap_route.py`, `red.log` y `red.xml`; [diagnóstico anterior y recibo](clap-preprocessing-diagnosis.md). Backend original SHA `3a033ae8adb384cc71552108fa39a6956b205170101375fbef93bcfb424e147d`, imagen `37e9355`. Producto intacto durante ambas investigaciones. El nuevo test se incorporará al engine con RED previo antes de corregir; los antecedentes no se sobrescriben.

El lote de calidad se cerró 01:40:45 UTC (inicio 01:13:24): fuente estimado, tokens/coste/horas IA null; 27 minutos de reloj no se imputan como IA. Incluye QA T-16, revisión T-08 e investigaciones CPU T-08/T-09, sin reparto individual ficticio. Fix1 abrió una ventana propia a 01:40:45 UTC.

Siguiente puerta: corregir ambos gaps con TDD, nueva imagen/recibo/cobertura, **revisión intento 2 también del alcance B que quedó incompleto**, y QA independiente. No reducir la nueva revisión a las dos líneas del fix. T-08 sigue en-progreso y sus tres criterios abiertos; no GPU ni cierre de M0 por esta pasada.
