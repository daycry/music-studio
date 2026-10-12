# Decisiones (ADR)

Formato: `ADR-XXXX-slug.md` con **Estado** (propuesta · aceptada · sustituida por ADR-YYYY), **Fecha**, **Contexto**, **Decisión**, **Motivo / Consecuencias**. Cortas: una pantalla.

| ADR | Decisión | Estado |
|---|---|---|
| [0001](ADR-0001-reinicio-desde-cero.md) | Reinicio desde cero; la documentación anterior se archiva | aceptada |
| [0002](ADR-0002-personal-local-first.md) | Uso personal, local-first, un solo usuario, sin auth; cloud solo como alternativa opcional (ADR-0014) | aceptada |
| [0003](ADR-0003-stack.md) | Next.js + FastAPI (sin torch) + un engine GPU en contenedor por familia de modelo | aceptada |
| [0004](ADR-0004-sqlite-y-cola-propia.md) | SQLite (WAL, backup diario) y cola propia en el server | aceptada |
| [0005](ADR-0005-todo-en-la-carpeta.md) | Todo dentro de la carpeta (incluidas cachés); qué se sincroniza con Synology y qué no | aceptada |
| [0006](ADR-0006-seguridad-de-pesos.md) | Pesos: safetensors/GGUF/ONNX; pickle solo convertido con auditor; código remoto fijado; revisión y SHA-256 | aceptada |
| [0007](ADR-0007-gpu-local-12gb.md) | GPU 12 GB: un modelo en VRAM, proceso hijo para liberar, tope desde VRAM libre, ACE-Step tier 4 (LM 0.6B) | aceptada |
| [0008](ADR-0008-procedencia-y-linaje.md) | Manifiesto v1 por artefacto y linaje multi-padre desde la primera migración | aceptada |
| [0009](ADR-0009-formatos-y-loudness.md) | FLAC + MP3; WAV 48 kHz a demanda; loudness por destino; true peak con ffmpeg | aceptada |
| [0010](ADR-0010-ux-derivada-de-suno.md) | UX derivada de Suno y Sondo, identidad propia | aceptada |
| [0011](ADR-0011-seleccion-de-modelos.md) | ACE-Step 1.5 (2B turbo + LM 0.6B) principal; HeartMuLa alternativa (M5); no comerciales solo en laboratorio | aceptada (a confirmar en M0) |
| [0012](ADR-0012-llm-de-letras.md) | Asistente de letras: Gemma 4 12B local por defecto; Claude API opcional | aceptada |
| [0013](ADR-0013-cancion-como-proyecto.md) | La canción es el proyecto: takes, letra, portada, vídeo y exportaciones dentro de ella | aceptada |
| [0014](ADR-0014-local-por-defecto.md) | Local por defecto en todo; APIs/suscripciones solo como alternativa opcional, visible y registrada | aceptada |
| [0015](ADR-0015-video-musical-por-niveles.md) | Vídeo musical por niveles N0–N3 (letra/visualizador → guion gráfico → planos protagonistas → todo generativo) | aceptada (a validar) |
| [0016](ADR-0016-comfyui-como-motor-de-imagen-y-video.md) | ComfyUI headless como motor de imagen y vídeo, workflows versionados | aceptada (a validar) |
| [0017](ADR-0017-postproceso-y-manifiesto-en-el-server.md) | Engines devuelven salida cruda; post-proceso, manifiesto y render en el server (worker CPU) | aceptada |
| [0018](ADR-0018-cola-de-jobs.md) | Cola de jobs: carriles gpu/cpu/remote, prioridades, dependencias, reintentos, recuperación | aceptada |
| [0019](ADR-0019-contratos-code-first.md) | Contratos code-first: OpenAPI generado, `engine-contract` Pydantic, esquemas JSON versionados | aceptada |
| [0020](ADR-0020-seguridad-local.md) | Seguridad local: Host/Origin, puertos en 127.0.0.1, token de engines, subidas validadas | aceptada |
| [0021](ADR-0021-repositorio-publico.md) | Remoto público `daycry/music-studio` (todos los derechos reservados); código anterior en `archive/legacy-main`; auth con `gh`; merge ff a `main` por tarea | aceptada |
| [0022](ADR-0022-memoria-tecnica-kwipu-graphiti.md) | Memoria técnica en Kwipu (export) y Graphiti (`shadow`, grupo `music-studio`) como MCP locales; liberar la VRAM de Ollama antes de trabajar con GPU | aceptada |
| [0023](ADR-0023-primera-cancion-con-material-privado.md) | Primera canción de M0 con «Libre» como entrada privada; B-02 mantiene su definición en la evaluación | aceptada |
| [0024](ADR-0024-hashes-de-codigo-remoto-en-descriptores.md) | Campo opcional remote_code en el descriptor, con rutas relativas y SHA-256; ampliación compatible de /v1 | aceptada |
| [0025](ADR-0025-limite-de-memoria-wsl.md) | WSL con límite de 16 GB, swap de 8 GB y recuperación de caché dropCache; perfil elegido por el propietario y aplicado | aceptada |
| [0026](ADR-0026-comparacion-controlada-shift.md) | Comparación privada shift 1/3; parámetro opcional y default anterior conservado | aceptada |
| [0027](ADR-0027-controles-de-inferencia-sft.md) | Controles SFT y seis tomas nuevas con transporte emparejado tras T-19; controles antiguos preservados | aceptada |
| [0028](ADR-0028-preparacion-fiel-de-instrucciones.md) | Preparación determinista original/efectiva, limpieza explícita de Markdown en tags y recibo privado inmutable | aceptada |
| [0029](ADR-0029-presupuesto-operativo-de-texto-acestep.md) | Preflight offline con plantillas/tokenizadores fijados, política LM y reserva completa, metadata entrenada y captura privada de fronteras | aceptada |
| [0030](ADR-0030-analisis-local-y-alineacion-secuencial.md) | Análisis local: ASR y alineación secuenciales, beat_this CPU desde configuración auditada y loaders safetensors offline | aceptada |
| [0031](ADR-0031-transcripcion-segmentada-con-tiempos-globales.md) | Transcripción hasta600s en fragmentos≤180s, reconocimientos correspondientes y offsets globales; residencia secuencial y límite independiente explícito hastaM3 | aceptada |
| [0032](ADR-0032-condicionamiento-dit-segun-rama-nativa.md) | Planificación de ambas ramas DiT y validación exacta de la resolución nativa con códigos LM; contenido y guardas íntegros | aceptada |
| [0033](ADR-0033-perfiles-y-medicion-directa-del-benchmark.md) | Benchmark del engine mediante /v1: perfiles base/XL, INT8 efectivo, inferencia directa y observación WDDM; copia interior efímera y referencias comparables | aceptada; implementación pendiente |

| [0034](ADR-0034-capacidades-nativas-y-accesibles-por-v1.md) | Matriz de capacidades con /v1 y laboratorio nativo seguro separados; verified sólo desde evidencia accesible del producto | aceptada; medición pendiente |

| [0035](ADR-0035-despliegue-docker-y-ollama-wsl.md) | Producto en Docker Compose, ComfyUI CUDA y Ollama compartido en WSL2 mediante adaptador; cola SQLite conservada | aceptada; implementación pendiente |

| [0036](ADR-0036-observabilidad-wddm-autonoma.md) | Observación automática WDDM con contraste dedicado separado y confianza shared explícita; puerta manual complementaria | aceptada; implementación pendiente |

| [0037](ADR-0037-avance-tecnico-condicionado.md) | Apertura técnica contra mock y aceptación real separadas; decisión del orquestador bajo delegación, sin cierre musical por automatización | aceptada; revisión/QA documental conformes, integración Git pendiente |

| [0038](ADR-0038-rechazo-explicito-host-origin.md) | Host inválido y Origin presente ajeno reciben403; GET/HEAD ordinarios pueden omitir Origin, SSE y métodos restantes lo exigen | aceptada; implementación y QA pendientes |

| [0039](ADR-0039-readquisicion-wddm-acotada.md) | Un reintento de adquisición completa con originales conservados y presupuesto2s, sin ampliar contraste ni cadencia; política y sesión nuevas | aceptada; implementación y QA pendientes |

| [0040](ADR-0040-frontera-parser-http-y-aplicacion.md) | Peticiones válidas con Host ajeno403; mensajes mal formados rechazados antes de ASGI400 conforme a RFC9112; originales de QA preservados | aceptada; rebate y QA de evidencia conformes, Git pendiente |

| [0041](ADR-0041-esquema-inicial-y-snapshots-del-server.md) | Esquema23 tipado, usuario/sujeto de asset separados, DAG y raíz canónica, FTS vigente, snapshots derivados y backup SQLite nativo empaquetado | aceptada; implementación y QA pendientes |
| [0042](ADR-0042-proveedor-wddm-aislado-y-preparacion-observada.md) | Proveedor persistente propio terminable, publicación de episodios dentro del plazo y preparación observada; política nueva v3 | aceptada; implementación y QA pendientes |

| [0043](ADR-0043-identidad-durable-de-intentos.md) | Job lógico e intento de engine separados; petición congelada, tres intentos totales y recuperación sin duplicados | aceptada; implementación y QA pendientes |

| [0044](ADR-0044-snapshots-con-dependencias-explicitas.md) | Raíz completa y dependencias dirigidas con soporte durable; invalidación y publicación de canciones afectadas | aceptada; implementación y QA pendientes |

| [0045](ADR-0045-recuperacion-y-transporte-de-auditoria-del-benchmark.md) | Disposición durable tras timeout y transporte incremental de auditoría, con validación final completa | aceptada; implementación, revisión y QA pendientes |

| [0046](ADR-0046-capsulas-canonicas-y-auditoria-incremental.md) | Cápsulas propias de originales como autoridad online, custodia nativa, referencias acotadas y FINAL independiente | aceptada; implementación, revisión y QA pendientes |

| [0047](ADR-0047-cola-empaquetada-en-app.md) | Dispatcher en app.queue y tres entregas funcionales; identidad, carriles y gates conservados | aceptada; implementación, revisión y QA pendientes |

| [0048](ADR-0048-herramientas-frontend-portatiles.md) | Node y pnpm verificados en tools, sin launcher de perfil ni cambio automático de gestor; runtime Docker conservado | aceptada; implementación, revisión y QA pendientes |

| [0049](ADR-0049-entradas-estables-fuera-del-writer.md) | Copias de entradas propias antes del writer, petición congelada y conservación ante commit o envío desconocidos | aceptada; implementación, revisión y QA pendientes |

| [0050](ADR-0050-autoridad-canonica-aislada-del-benchmark.md) | Autoridad online en proceso propio, ingreso prioritario, leases y watchdog independiente; publicación y FINAL separados | aceptada; implementación, revisión y QA pendientes |

| [0051](ADR-0051-dependencias-web-fijadas-y-uso-local.md) |609artefactos web fijados, uso local e instalación congelada sin scripts; decisión de2alias exactos, redistribución separada | aceptada; instalación y QA pendientes |

| [0052](ADR-0052-compilacion-web-linux-fijada.md) | Compilación web Linux con instalación congelada y caché nativa segura; el fallo Windows se conserva | aceptada; prueba e implementación pendientes |

| [0053](ADR-0053-postproceso-cpu-portable-en-el-server.md) | Audio-post portable y cómputo en hijo propio del server; publicación y SQLite en el padre | aceptada; implementación y QA pendientes |

| [0054](ADR-0054-ffmpeg-linux-fijado-para-el-server.md) | FFmpeg Linux estático fijado, receta LGPLv3 y adquisición TAR verificada antes del runtime | aceptada; adquisición y pruebas pendientes |

| [0055](ADR-0055-ejecucion-cpu-y-publicacion-durable-por-toma.md) | Ejecución local tipada, publicación por toma con historial inmutable y reconciliación; post agregado y análisis causal | aceptada; implementación, revisión y QA pendientes |

| [0056](ADR-0056-sse-con-buffer-y-recuperacion-de-estado.md) | SSE con replay en bus acotado, epoch y recuperación autorizada del estado; sin broker ni outbox nuevo | aceptada; implementación, revisión y QA pendientes |

| [0057](ADR-0057-custodia-propia-y-protocolo-json-del-worker-cpu.md) | Helper stdlib de custodia CPU, Job Windows/grupo supervisado Linux e IPC JSON acotado con resultados por toma | aceptada; implementación y prueba nativa pendientes |

| [0058](ADR-0058-sesion-publica-local-para-eventos.md) | Sesión local automática en memoria y credencial pública propia para SSE, sin reutilizar token de engines | aceptada; implementación y QA pendientes |

| [0059](ADR-0059-fuentes-y-presupuesto-absoluto-del-benchmark.md) | Verificador propio de fuentes, deadline compartido y retención de nacimientos tardíos del benchmark | aceptada; implementación y QA pendientes |
| [0060](ADR-0060-captura-write-once-de-procedencia-antes-del-envio.md) | Captura inmutable de procedencia tras load y Health fresco, antes de submit; sin reconstrucción histórica | aceptada; implementación y QA pendientes |
| [0061](ADR-0061-rechazo-con-rollback-confirmado-sin-invalidar-el-feed.md) | Rechazo con rollback confirmado conserva el feed; commit incierto mantiene invalidación y primera causa | aceptada; implementación y QA pendientes |
| [0062](ADR-0062-evidencia-sintetica-explicita-con-binding-del-server.md) | Variante explícita de evidencia sintética, ligada al backend y descriptor esperado por el server; sin pesos ficticios | aceptada; implementación y QA pendientes |
| [0063](ADR-0063-procedencia-en-resolucion-completa-tras-routing.md) | Construir la procedencia en resolución completa tras el filtro de ocupación, conservando controles positivos y el plazo original | aceptada; implementación en curso y QA pendientes |
| [0064](ADR-0064-verificacion-funcional-y-cobertura-con-coste-de-instrumentacion.md) | Suite funcional completa y cobertura separadas tras calibrar el coste de tracing; fuentes y conjuntos explícitos, sin ampliar plazos | aceptada; ejecuciones y QA pendientes |
| [0065](ADR-0065-comprobaciones-finales-de-metadata-bajo-barrera.md) | Conservar comprobaciones finales de paths e identidad de entradas autorizadas y staging bajo coordinador, sin bytes/red ni awaits | aceptada; integración y QA pendientes |
| [0066](ADR-0066-sincronizacion-con-el-submit-real-en-prueba-de-recuperacion.md) | Sustituir sólo la espera fija de acuse perdido por el submit real observado; assertions y presupuestos de producto conservados | aceptada; fixture, revisión y QA pendientes |
| [0067](ADR-0067-verificacion-vigente-del-esquema-sql-con-suite-completa.md) | Suite SQL completa1056 funcional/1055 instrumentada, gate de cuatro módulos y tres casos Linux vigentes | aceptada; ejecuciones y aceptación pendientes |
| [0068](ADR-0068-descarte-de-identidad-obsoleta-antes-de-procedencia.md) | Descartar cambios de identidad tras routing antes de construir procedencia, sin ampliar autoridad ni ocultar entradas inválidas | aceptada; implementación, revisión y QA pendientes |
| [0069](ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md) | Ext4 respaldado por VHDX dentro del proyecto para conservar publicación atómica no-clobber | aceptada; provisión, implementación y QA persistente pendientes |
| [0070](ADR-0070-contexto-privado-de-request-y-linaje-en-publicacion-audio.md) | Request y linaje exactos en contexto privado sellado, referencia opcional v1 y verificación común sin publicar letra/estilo | aceptada; implementación, revisión y QA pendientes |
| [0071](ADR-0071-probes-de-almacenamiento-en-dominio-aislado.md) | Helper CPU aislado y FD real del consumidor para probes frescos, limpieza propia y preservación de datos ajenos | aceptada; implementación, revisión y QA pendientes |

| [0072](ADR-0072-copia-de-pesos-con-presupuesto-de-io.md) | Copia de pesos a 128 MiB/s y sincronización por bloque para controlar la competencia de E/S | aceptada; TDD, revisión A/B/D, QA CPU y reproducción directa validados; matriz GPU pendiente |
| [0073](ADR-0073-recetas-privadas-y-escucha-ab-de-iteracion-creativa.md) | Recetas privadas por job, autoridad CPU explícita y previews A/B desde masters para M2 | aceptada bajo delegación; plan aprobado, implementación y QA pendientes |

| [0074](ADR-0074-procedencia-cpu-y-contratos-versionados.md) | Take CPU discriminada, excepción SQL limitada y contratos/preview v2; API M1 preservada | aceptada bajo delegación; T-01 contractual cerrada tras revisión 2 y QA16/16; implementación pendiente |
| [0075](ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md) | Journal estable por handle, CAS e intenciones para recuperación y sesiones del almacenamiento propio | aceptada bajo delegación; revisión 2 A/B conforme, implementación y QA física pendientes |
| [0076](ADR-0076-politica-estricta-de-confianza-del-journal-windows.md) | Política S1 de admisión por handles y excepción owner TrustedInstaller sólo para el root del sistema; S2 experimental y S3 aplazada | aceptada documentalmente por ROOT bajo delegación; revisión A/B conforme, implementación y QA nativas pendientes |

| [0077](ADR-0077-envelope-privado-de-recetas-creativas.md) | Envelope privado versionado, captura inmutable y lectores históricos de recetas creativas | aceptada; contrato O1 ratificado tras revisión A+B intento2 y QA documental18/18 |

| [0078](ADR-0078-geometria-nt-readonly-del-journal.md) | Geometría NT readonly por adquisición retenida y derivación de B candidato sin autoridad writer | aceptada por ROOT; revisión A+B1 con Minor anotado y QA documental33/33; implementación nativa pendiente |

| [0079](ADR-0079-composicion-creativa-por-muestras-medidas.md) | Composición creativa con frames medidos, conversiones explícitas y full/region sin doble ensamblado | aceptada; O1 y contrato ratificados por ROOT tras revisión2 y QA documental60/60 |

| [0080](ADR-0080-produccion-por-derivados-tipados-y-escena-n0-local.md) | Producción por derivados tipados y escena N0 local compartida | aceptada; O1 incorporada por ROOT tras revisión1 y QA documental175/175 |

| [0081](ADR-0081-store-del-journal-windows-con-kernel-io-privado.md) | Store del journal Windows con kernel I/O privado | aceptada; ROOT tras revisión2 y QA documental95/95, implementación nativa pendiente |

| [0082](ADR-0082-peticion-privada-de-produccion-y-autoridad-por-resultado.md) | Petición privada de producción y autoridad discriminada por resultado | aceptada por ROOT; PR-O1, revisión1 A/B sin gaps y QA documental403/403; implementación M3 pendiente |

| [0084](ADR-0084-frontera-nativa-y-admision-del-principal-windows.md) | Frontera nativa y admisión del principal Windows | aceptada; O1 elegida, ratificada tras revisión2 y QA documental; runtime pendiente |

| [0083](ADR-0083-persistencia-tipificada-y-revisiones-inmutables-de-produccion.md) | Persistencia tipificada y revisiones inmutables de producción | aceptada; D03/PD-O1 elegida, ratificada tras revisión2 y QA documental; runtime pendiente |

| [0085](ADR-0085-formatos-tipados-y-cierre-portable-de-produccion.md) | Formatos tipados y cierre portable de producción | aceptada; PF-O1 ratificada tras revisión2 y QA documental; runtime pendiente |

## Decisiones heredadas de la documentación archivada



Las decisiones D-01…D-30 de [`../archive/…/spec.md`](../archive/roadmap-2026-07-27/2026-07-27-plataforma-musical-ia/spec.md) §2 **no están vigentes** salvo las recogidas explícitamente en un ADR de esta tabla («Hereda D-xx»).




