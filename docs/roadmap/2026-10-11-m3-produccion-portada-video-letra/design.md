---
design: m3-produccion-portada-video-letra
titulo: Producción por derivados tipados y escena N0 local
estado: aprobado
creado: 2026-10-11
actualizado: 2026-10-11
spec: spec.md
evaluacion: n/a (ADR-0001)
plan: improvement-plan.md
adr: ../../decisiones/ADR-0080-produccion-por-derivados-tipados-y-escena-n0-local.md
opcion_elegida: O1
validacion: ROOT bajo delegación del propietario; 2026-10-11T14:16:13.016842+00:00; decisión arquitectónica, sin validación personal atribuida al propietario
adopcion_canonica: incorporada por ROOT tras revisión y QA documental
destino_canonico: docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/design.md
generacion:
  fuente: estimado
  inicio: null
  fin: null
  tokens_reales: null
  eur: null
  horas_ia: null
  duracion: null
  nota: Preparación dentro del marcador único de ROOT; no se abre otro medidor. Consumo real desconocido; reloj no equivale a trabajo IA.
---

# Diseño — M3: producción, portada y vídeo con letra

> **Spec:** [requisitos aprobados](spec.md). **Evaluación:** n/a económica. **Plan:** pendiente. **ADR:** [ADR-0080, propuesta](../../decisiones/ADR-0080-produccion-por-derivados-tipados-y-escena-n0-local.md).
> O1 elegida por ROOT bajo delegación del propietario el2026-10-11T14:16:13.016842+00:00. La decisión de arquitectura está aprobada; revisión, QA documental y adopción canónica siguen pendientes. No acredita implementación ni aceptación M3.
> Copia privada destinada a la ruta canónica indicada en frontmatter. Los enlaces de cadena se resuelven desde ese destino futuro. La evidencia privada se separa en la sección7.

| Campo | Valor |
|---|---|
| Estado | aprobado para la decisión arquitectónica; adopción canónica pendiente |
| Opción elegida | O1 — derivados tipados y escena N0 compartida offline |
| Validación | ROOT bajo delegación del propietario,2026-10-11T14:16:13.016842+00:00; no se atribuye lectura o aprobación personal del documento al propietario |
| Alcance conservado | 14 funciones, 49 CA; ninguna aceptada por este documento |

## 1. Contexto y restricciones

M3 convierte takes en stems, mezclas, análisis, letra sincronizada, portadas, audio y vídeo N0. Conserva presets, exportación portable y recuperación de biblioteca. Las 14 funciones son obligatorias, aunque sus modelos o mecanismos aún requieran validación.

La Constitución §§1–4 fija canción como raíz, takes inmutables, maestro explícito, server sin torch y único escritor SQLite. Fija cola `job/job_dependency`, GPU1/CPU2, engines Docker `/v1` y un modelo residente. Ollama es un servicio compartido externo al producto, conforme a ADR-0035.

ADR-0037 permite diseño y unidades independientes. La aceptación M3 exige M2 cerrado y todos los gates heredados. M1/T05 y la composición/integración M2 siguen siendo dependencias. No se atribuye a T02 la admisión, ejecución, publicación o UI que aún no acredita.

### Qué existe y qué debe cambiar

| Seam consultado | Hecho observado | Consecuencia para ambas opciones |
|---|---|---|
| `apps/server/app/models/__init__.py`, Analysis/Artwork/Preset/VideoProject/Render/Export | Existen entidades iniciales; Analysis es única por take/kind/analyzer | Conservar entidades. Añadir revisiones temporales sin sobrescribir análisis ni fingir un nuevo analyzer por corrección. |
| `apps/server/app/queue/chains.py:add_dependents` | Crea post.audio y audio.beats por take | Ampliar compositores cerrados; no presumir importación durable de todos los análisis. |
| `apps/server/app/worker/planning.py:compose_post_plan` | Exige generación e intento ganador; produce PostPlan v1 | No usarlo para export/render/upload CPU con identidades de inferencia inventadas. |
| `apps/server/app/worker/execution.py:CpuAudioService` | Admisión y ejecución centradas en post.audio | Concretar nuevos handlers y autoridad antes de su RED. CPU2 existente no equivale a servicio M3 integrado. |
| `apps/server/app/snapshots.py:_project` | Construye cierre y snapshot version1 | Añadir lectores/proyección del cierre M3 y CPU compatible; no afirmar que snapshot v2 esté integrado. |
| `apps/server/app/backup.py:backup/restore_backup` | Backup SQLite nativo y restauración a BD nueva; no incluye medios | Conservar backup diario14d. Añadir backup de biblioteca y activación separada. |
| `apps/engines/acestep/descriptor.py:descriptor` | Sólo music.song/music.instrumental; verified false | Stems, audio propio y alta calidad requieren capacidades reales nuevas/verificadas; nombre del modelo no las habilita. |
| `apps/engines/analysis/engine_analysis/descriptor.py:descriptors` | Tareas conservadoras sin verificar; align_lyrics limita duración a180s | Gate por tarea/método. Una canción mayor no se trunca: requiere segmentación medida o ampliación validada. |
| `apps/web/components/GenerativeViz.tsx` | Canvas de progreso, con valores prefabricados o peaks al terminar | No acredita F-41. Añadir visualizador reactivo ligado al audio efectivo y al seek. |
| `apps/web/components/PlayerContext.tsx` | Cola y estado de reproductor; no mixer sincronizado | Añadir transporte Web Audio común para stems; conservar reproducción convencional. |
| `packages/contracts/timeline-v1.schema.json` | Schema cerrado, con letras por plano y sin tiempos por palabra | Concretar TimelineV2/plan N0 antes del código. No insertar propiedades incompatibles en v1. |
| Inventario `apps/engines` y Compose congelado | No existe módulo engine-comfy ni servicio Comfy en los paths consultados | Su despliegue, adapter y workflows son trabajo futuro; no hay capacidad Comfy reutilizable acreditada. |

ADR-0073/0077 fijan recetas M2 y ocho operaciones cerradas. M3 requiere otro namespace privado tipado; no añade mix/render/export a CreativeRequestV1. ADR-0074 distingue CPU autónomo y conserva inferencia histórica. Su excepción SQL sólo alcanza tres tablas precisas; no autoriza relajar Asset, Analysis u otras tablas.

### Límites de las dos opciones

Ambas conservan `/v1` compatible, SQLite y el publicador del server. Los engines sólo escriben raw autorizado. El server resuelve referencias a copias propias y produce postproceso, manifiestos y render. El navegador nunca suministra paths ejecutables, scripts, expresiones FFmpeg o workflows Comfy arbitrarios.

La publicación requiere raíz ext4/UUID acreditada, NOREPLACE, CAS y custodia reconciliada conforme a ADR-0069. UNKNOWN bloquea serving, promoción y limpieza. No se incorporan Kafka, Redis ni otro escritor de BD.

Todo modelo y herramienta requiere pin, hash, fila de licencia y conformidad. Las tablas históricas de modelos/licencias son antecedentes, no evidencia actual de cabida, calidad ni permiso definitivo. No se elige XL, RoFormer o checkpoint Comfy por esa documentación.

## 2. Opciones (2)

### O1 — Derivados tipados sobre la cola existente

El server captura una petición privada versionada por acción. Compositores cerrados materializan jobs y dependencias de stems, análisis, mezcla, export y N0. Cada resultado publica su propia entidad y recibo. Los jobs exitosos se reutilizan sólo con autoridad, contexto y hashes acreditados.

Las revisiones de mezcla y alineación son entradas inmutables. El montaje vive en `video_project.timeline` con revisión. Un plan N0 derivado vincula audio final, alineación, portada, features y fonts. No existe un editor genérico de grafos ni una segunda fuente de verdad del montaje.

El renderer N0 del server usa un paquete Canvas compartido con la preview. Un hijo headless propio evalúa cuadros en `t = frame_index / fps`. Renderiza un bundle cerrado y local, sin depender de la web viva. La rasterización CPU requiere pin/flags y conformidad; no carga un modelo GPU propio. FFmpeg codifica y muxea; el server mide y publica. Esto propone una nueva herramienta empaquetada, aún sin pin ni gate aprobado.

Backup/import/restore usan handlers de mantenimiento separados. No heredan una autoridad de Take ficticia. Comparten primitivas de confinamiento, custodia y publicación sólo después de verificar sus interfaces.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: varios contratos/resultados y un renderer compartido; la cola ya expresa dependencias. |
| Riesgo | Medio-alto: integración de múltiples fronteras; resultados parciales y recovery quedan delimitados por job/artefacto. |
| Coste relativo | M: reutiliza scheduler e infraestructura; exige adapters tipados y empaquetado de render. |
| Reversibilidad | Alta para handlers/renderer; media para migraciones aditivas y formatos ya publicados, que deben conservarse. |

### O2 — Documento revisionado de producción y runner de sesión

Un documento por canción captura selección, mezcla, análisis, alineación, portada y destinos. Cada confirmación crea una revisión inmutable. Un job de sesión interpreta esa revisión, ejecuta etapas y guarda checkpoints internos. Puede omitir etapas ya acreditadas, conservar resultados parciales y reanudar tras fallos.

El documento contiene decisiones de producción; el montaje sigue siendo `video_project.timeline`. El runner no crea otra cola. Expande llamadas GPU/CPU como dependientes en `job/job_dependency` y espera sin ocupar un slot. Sin ese diseño, CPU2 podría bloquearse esperando hijos.

El server captura cuadros de una ruta web interna congelada para esa revisión. El browser pertenece al worker del server y nunca al usuario. La exportación necesita web disponible y compatible con la revisión. Debe impedir acceso a otras rutas, red externa y endpoints de mutación.

Import/restore incluye revisiones del documento y checkpoints de contenido, pero excluye su autoridad activa. Debe reconciliar documento, jobs, entidades publicadas y timeline. Backup de biblioteca conserva el mismo corte coherente exigido en O1.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: entidad/revisiones de sesión, runner, checkpoints y coherencia con jobs y timeline. |
| Riesgo | Alto: autoridad duplicada entre sesión y jobs; recovery y captura dependen de versión/disponibilidad web. |
| Coste relativo | L: persiste otro agregado y exige resolver sus transacciones, invalidaciones y migraciones. |
| Reversibilidad | Media-baja: los proyectos portables conservarían documentos/checkpoints; retirar el runner requiere lectores históricos. |

### Comparación con el mismo alcance

| Aspecto | O1 | O2 |
|---|---|---|
| Unidad durable | Acción/resultado tipado | Revisión de producción, con jobs subordinados |
| Recuperación | Resultado independiente e intención de publicación | Checkpoint de sesión reconciliado con cada job/publicación |
| Reutilización | Fuente/recibo/hash del resultado concreto | Caché de etapas dentro de revisión/documento |
| Preview y render | Paquete de escena compartido, ejecución offline por cuadros | Ruta web de la revisión, capturada por worker propio |
| Biblioteca portable | Entidades y revisiones de contenido | Lo anterior más documentos/revisiones de producción |
| Stems, música, Comfy y hardware | Mismos gates reales, sin modelos elegidos | Mismos gates reales, sin modelos elegidos |
| Scope | Las 14 funciones y49CA | Las 14 funciones y49CA |

O2 tiene una ventaja real: presenta una revisión unificada para producir varios destinos de una vez. M3 no exige sesiones reutilizables ni confirmar todos los destinos conjuntamente. O1 permite añadir esa UX posteriormente como compositor de acciones, sin introducir ahora su autoridad persistente.

## 3. Criterios de decisión

1. Autoridad única y recuperación verificable pesan más que agrupar controles. Cada resultado debe conservar contexto y terminal propio.
2. Reutilizar cola y linaje pesa más que reducir inicialmente el número de handlers. Las recetas M2 no se amplían por conveniencia.
3. Preview y export deben consumir la misma escena temporal. Ninguna depende de animación prefabricada o del reloj de captura.
4. El alcance no se reduce por dificultad GPU. Capacidad ausente conserva el requisito pendiente y la UI deshabilitada.
5. Portabilidad exige lectores históricos y cierre de referencias. Un formato nuevo debe tener migración/compatibilidad definidos antes del RED.
6. Añadir herramientas exige conformidad/licencias; disponer de Playwright para QA no autoriza su browser como renderer de producto.

## 4. Recomendación · opción elegida y por qué

**Recomendación del arquitecto: O1.** Mantiene las fronteras actuales de job, entidad y publicación. Evita una segunda historia durable de producción. Separa fallos de análisis, portada y export sin invalidar resultados independientes.

**O1 — Derivados tipados sobre la cola existente, con escena N0 compartida offline.** ROOT la eligió bajo delegación el2026-10-11T14:16:13.016842+00:00. La autoridad por resultado satisface criterios1–2; la escena temporal compartida responde al criterio3. Los formatos históricos y gates explícitos conservan criterios4–6. [ADR-0080](../../decisiones/ADR-0080-produccion-por-derivados-tipados-y-escena-n0-local.md) registra la decisión como propuesta; su revisión/adopción no equivale a producto terminado.

La decisión cruza el umbral: cierra O2 y afecta cola, datos, render y portabilidad. Los archivos privados seleccionados se entregan a ROOT; esta pasada no modifica spec/plan, índice ni canon.

**O2 descartada por ROOT:** su documento unificado aporta producción conjunta, pero introduce reconciliación entre sesión, jobs, resultados y timeline. Su captura acopla export a disponibilidad/versión web. O1 permite esa UX futura mediante compositores cerrados sin ese agregado persistente.

### Diseño funcional de la arquitectura seleccionada O1

**Stems y mixer.** Separar crea assets del take, no un take nuevo. El server registra sample rate, canales, número de muestras y cuatro roles. MixRevision captura IDs/hashes, mute, solo y ganancias finitas. Mute prevalece sobre solo; si existe algún solo, sólo contribuyen stems solo no muteados. Todas las fuentes comparten transporte y origen temporal.

La preview usa Web Audio sobre PCM decodificado con presupuesto de memoria. AudioBufferSourceNode permite planificación precisa en memoria. Para fuentes grandes, un worklet por bloques requiere su propia conformidad; no se sustituyen stems por cuatro elementos audio independientes. Es una decisión de implementación condicionada por memoria, no evidencia ya obtenida. [Especificación W3C consultada el2026-10-11](https://www.w3.org/TR/webaudio/#AudioBufferSourceNode).

El server exporta con las ganancias efectivas y suma sin normalización implícita. Una mezcla publicada como Take crea hijo CPU con todos sus antecedentes. Una exportación derivada puede ser Export sin Take nuevo; conserva receta y autoridad CPU propia. Debe definirse esa representación antes del RED.

**Audio de destino.** Medir entrada, aplicar ganancia constante y soxr, codificar y medir el archivo final decodificado. El plan fija la política de tratamiento antes del renderer/export dependiente. Cualquier normalización o limitación dinámica adicional requiere decisión explícita, parámetros y evidencia visibles; nunca es silenciosa. Los objetivos son −14/−23/−16 LUFS y techo−1dBTP. Si no caben simultáneamente sin cambiar dinámica, export falla como no conforme. No activa limitador ni normalización dinámica silenciosa. Ebur128 es un candidato de medición documentado; su presencia y comportamiento en el pin requieren probe de producto. [FFmpeg oficial consultado el2026-10-11](https://ffmpeg.org/ffmpeg-filters.html#ebur128-1).

Original conserva bytes. ZIP stems convierte sólo cuando el perfil exige48kHz y preserva amplitudes, offsets y longitud común. El lector independiente verifica metadatos, letra histórica embebida por solicitud y portada.

**Análisis y alineación.** Cada método produce resultado con estado y binding al hash de audio. Beats, key, sections y loudness fallan separadamente. La sección tomada de etiqueta textual conserva origen textual; no cuenta como medición musical.

LyricsTimingRevision referencia resultado inicial, padre de revisión, tokens estables y bindings single/composite por fragmento. La corrección cambia tiempos y marcas de incertidumbre; no cambia audio, texto histórico ni análisis anterior. LRC/SRT, karaoke y N0 consumen una revisión explícita. Un missing no se convierte en palabra cantada. Fragmentar audio largo conserva offsets globales y valida solapes/fronteras;180s no se usa como truncación automática.

**Portada.** Engine-comfy requiere adapter `/v1` y un proceso hijo propietario de Comfy/CUDA. Unload termina ese árbol propio y acredita memoria libre. Workflows cerrados exponen parámetros semánticos; nodos/weights/commits quedan fijados. Generación múltiple y edición por referencia son gates distintos. La elección de portada modifica Song sólo mediante acción explícita/CAS. Upload crea Artwork source=upload sin modelo ni seed inventados.

**N0 y reactividad.** La revisión de VideoProject y sus bindings son autoridad. El plan derivado contiene timeline_rev/hash, take/audio final hash, timing_revision, artwork y perfiles. La escena compartida acepta `time_s` explícito. El reloj de audio alimenta preview; el índice de cuadro alimenta export. Partículas usan semilla visual declarada y función temporal reproducible, con energía/espectro del audio efectivo.

Features de onda y espectro se calculan sobre el audio final elegido, con ventana/hop/pins y eje temporal declarado. Las partículas responden a esas features, incluido silencio. El análisis de otro master no sirve como feature del mix. Seek recomputa estado temporal; requestAnimationFrame no determina el tiempo musical.

El renderer carga assets validados y fonts locales. Layout conserva márgenes/line wrapping; largas palabras y líneas tienen casos de legibilidad. El browser hijo renderiza cada cuadro tras fijar estado y esperar fonts/assets. La API oficial de screenshot describe captura; no garantiza rendimiento ni equivalencia audiovisual. Ambas requieren prueba sobre canción completa. [Playwright oficial consultado el2026-10-11](https://playwright.dev/docs/api/class-page#page-screenshot).

No se presume codec H264 disponible en FFmpeg LGPL. El perfil final exige codec/container realmente presentes, reproducción en browser y lector independiente, licencia y prueba de tiempo. La selección de codec/font y pin del browser precede al RED del renderer.

**Audio propio y calidad alta.** Compositor musical integra upload mediante roles y capacidades comprobados. Media types incompatibles exigen conversión explícita y recibo. El hijo conserva derechos y linaje. Alta calidad usa únicamente modo M0 ganador y probado con margen; más pasos o XL no prueban mejora. Benchmark y escucha emparejada siguen pendientes.

**Presets.** La biblioteca global contiene nombre y payload versionado. Cada uso copia valores y referencias efectivas a la petición inmutable. Editar/eliminar preset no cambia trabajos anteriores. Referencia de timbre se conserva, pero sólo se aplica si esa capacidad ya está verificada; no habilita F-71 ni LoRA.

**Portable e import.** El paquete incluye raíz y cierre necesario de antecedentes/referencias. Conserva manifiestos y bytes originales, versiones leídas, declaraciones, maps y revisiones. El catálogo separa material privado de manifiestos/logs. No incorpora claves, paths personales ni autoridad activa.

El importador valida catálogo, límites, hashes, propiedad, DAG y todos los paths antes de promoción. Copia a staging propio y usa intenciones durables por lote/paquete. Una transacción publica referencias sólo cuando el cierre completo tiene medios promovidos y custodia acreditada. Reconciliar destinos preexistentes exige autoridad del import, no sólo hash.

Propuesta de colisiones: replay sólo si existe recibo propio del mismo import y resultado; ID ocupado por contenido ajeno/conflictivo rechaza. Remapeo explícito crea una importación nueva y mapa source→local separado, manteniendo evidencia original. Ningún manifiesto histórico se reescribe. La autoridad local/importada debe concretarse por ADR antes de implementar remapeo.

**Backup/restauración.** El baseline seguro usa mantenimiento exclusivo: bloquear nuevas mutaciones y dispatch, drenar procesos/leases propios y suspender purga. UNKNOWN impide iniciar el corte. Captura SQLite mediante su API nativa y catálogo de medios del mismo corte. Copia y valida todos los medios con escrituras/purga suspendidas; no mantiene una transacción writer durante E/S.

Es un coordinador de mantenimiento nuevo, no una garantía ya aportada por PublicationCoordinator. Conserva un recibo durable y sólo reabre escrituras tras su reconciliación. Una optimización futura con pins durables permitiría copiar tras reabrir; no forma parte del baseline propuesto.

Backup publica paquete cerrado con SQLite, assets/referencias, catálogo, schemas y locks aplicables. No incluye pesos por defecto. Restaurar valida a biblioteca nueva en raíz ext4 propia: integridad/FK/FTS, medios y reproducción. Jobs/leases históricos permanecen inertes; disponibilidad de generación se verifica aparte.

Activación requiere backup restaurable y ventana exclusiva. Un protocolo durable de binding de biblioteca y rollback cambia raíz/BD juntas; antes de definirlo no se modifica la biblioteca activa. El crash debe recuperar una biblioteca completa previa o nueva. Copiar VHDX activo no es backup de biblioteca.

### Recuperación común

La intención privada identifica petición, propietario, fuentes, contexto y resultado esperado. La ejecución propia registra custodia, herramienta/modelo efectivo y mediciones. Raw, render y paquetes sólo se adoptan por autoridad acreditada.

Cancel/restart reevalúa cada frontera: resolución→envío→raw→post→preparado→rename→commit→serving. El éxito durable se reproduce sin regenerarlo. Fallos parciales mantienen resultados independientes. Un terminal de engine no certifica post/render; archivo presente no certifica commit.

## 5. Impacto en módulos y ficheros

Las rutas existentes se localizaron con rg y se muestrearon en sus seams. Las nuevas rutas son propuestas bajo módulos reales; no se presentan como ficheros existentes. La elección O2 cambia la coordinación, no reduce las responsabilidades funcionales.

| Ruta real | O1 propuesto | O2 adicional o distinto | Tipo |
|---|---|---|---|
| `apps/server/app/models/__init__.py` y `apps/server/app/migrations/versions/` | Relaciones aditivas para revisiones/contextos/publicación M3; preservar baseline y excepciones | Documento/revisiones/checkpoints de producción | modificar y nuevas migraciones |
| `apps/server/app/queue/chains.py` | Compositores cerrados y análisis posttake completos | Runner crea dependientes por etapa | modificar |
| `apps/server/app/queue/runtime.py`, `resolver.py` y `recovery.py` | Dispatch tipado, resolver por roles/versiones, recovery y mantenimiento | Recuperación del agregado y espera sin slot | modificar |
| `apps/server/app/worker/contracts.py`, `planning.py`, `execution.py` | Conservar v1; interfaces/handlers M3 separados | Contrato runner/checkpoint | conservar históricos; adapters nuevos |
| `apps/server/app/worker/packages.py` y `publications.py` | Reusar primitivas tras contrato; nuevos sujetos/intenciones; no hacer passing de Take ficticia | Intención de sesión además de resultado | modificar selectivamente tras recon adicional |
| `apps/server/app/production/` | Namespace nuevo propuesto para requests/mix/alignment/export/render | Documento y runner | nuevo bajo `apps/server/app` |
| `apps/server/app/domain_routes.py` y `api_models.py` | Operaciones aditivas/DTO versionados; autorización y serving por sujeto | Rutas de documento/revisiones | modificar y rutas nuevas |
| `apps/server/app/backup.py`, `snapshots.py`, `closure_rows.py` | Corte de biblioteca, cierre M3/CPU, import/restore y autoridad inerte | Cierre de documento/checkpoints de contenido | modificar |
| `packages/audio-post/audio_post/pipeline.py` y `manifest.py` | Mix/export, métricas finales y lectores/manifiestos por origen | Mismos resultados y perfiles | modificar tras definición contractual |
| `packages/contracts/timeline-v1.schema.json` y `song-v1.schema.json` | Conservar bytes históricos; nuevos schemas/dispatch compatibles | Schema de documento de producción | conservar; nuevos schemas |
| `packages/engine-contract/engine_contract/__init__.py` | Nuevas capacidades por descriptor dentro de compatibilidad `/v1`; sin campos requeridos nuevos | Igual | modificar sólo si contrato aditivo lo requiere |
| `apps/engines/acestep/descriptor.py` y `adapter.py` | Tareas verificadas stems/audio propio/modo alta calidad | Igual | modificar después de gates M0 |
| `apps/engines/analysis/engine_analysis/descriptor.py` y `backend.py` | Métodos completados, bindings y segmentación validada | Igual | modificar después de conformidad |
| `apps/engines/comfy/` y `docker-compose.yml` | Nuevo engine-comfy propuesto, adapters/workflows/nodos auditados | Igual | nuevo módulo y servicio engine previsto |
| `apps/web/app/songs/[id]/page.tsx`, `lib/api.ts`, `components/PlayerContext.tsx` | Producción canción, transporte mixer, karaoke y acciones de export | Documento revisionado/producción conjunta | modificar |
| `apps/web/components/GenerativeViz.tsx` | Conservar su semántica de progreso; nuevo renderer N0/reactividad | Misma distinción | conservar; componentes nuevos |
| `apps/web/messages/es.json` y `apps/web/lib/generated/api.d.ts` | Cadenas castellanas y DTO regenerado desde código | Igual | modificar/regenerar por contratos |
| `packages/n0-scene/` y `apps/server/Dockerfile` | Paquete nuevo propuesto/bundle local y herramientas del renderer | Ruta web en `apps/web` y herramientas del browser del server | nuevo/modified según opción |
| `models/models.lock.json`, `tools/tools.lock.json`, `docs/legal/licencias.md` | Pins efectivos sólo tras elección/licencia/conformidad | Igual | cambios futuros, ninguno en esta pasada |

### Destino de las 14 funciones

| Función | Destino en O1 | Destino en O2 | CA conservados | Verificación futura indispensable |
|---|---|---|---|---|
| F-06 | Handler portable/import y cierre | Export de revisión con mismo cierre | 36–39,44,48 | Roundtrip real multiversión; negativos ZIP; reproducción |
| F-18 | Compositor de regeneración de calidad | Etapa musical de documento | 32–33,46 | Modo M0 real y escucha emparejada |
| F-19 | Upload+compositor musical tipado | Entrada musical de revisión | 04–05,30–31,46 | Ruta real de producto y escucha propia |
| F-30 | Job audio.stems→assets del take | Etapa stems reutilizable | 06–07,46 | Muestras/suma y separador/escucha real |
| F-31 | MixRevision, transporte, export CPU | Mezcla capturada en revisión | 08–10 | Mute/solo/sync; comparación exportada y escucha |
| F-32 | Handlers export por perfil | Destinos dentro de revisión | 11–14,48 | FFmpeg final, lector independiente y ZIP |
| F-33 | Jobs por método y resultados parciales | Checkpoints de análisis por método | 15–17 | Contraste independiente sobre audio real |
| F-34 | LyricsTimingRevision/karaoke/export texto | Revisión temporal vinculada al documento | 18–21 | Anotación cantada castellana y corrección/seek |
| F-35 | Engine-comfy→Artwork→elección | Etapa portada y elección explícita | 22–25 | Generar/editar realmente, varias opciones y revisión visual |
| F-40 | Plan de escena→renderer offline→Render | Documento→ruta web capturada→Render | 26,28–29,44 | Canción completa, sincronía/legibilidad/perfil y recovery |
| F-41 | Features+escena temporal compartida | Features consumidas por ruta congelada | 27–29 | Onda/espectro/partículas, silencio y seek real |
| F-44c | Upload→Artwork/fondo autorizado | Fuente subida del documento | 04–05,24,26 | Contenido/derechos y render N0 |
| F-70 | Biblioteca preset→captura por acción | Biblioteca→valores congelados por revisión | 34–35,36,41 | Historia conserva refs/valores tras editar/importar |
| F-85 | Mantenimiento exclusivo/corte/restore nuevo | Mismo corte, con documentos adicionales | 40–43,45 | WAL+medios coherentes, biblioteca real y rollback |

### Trazabilidad individual de los 49 criterios

Las verificaciones de esta tabla son futuras. Los textos completos y normativos permanecen en la spec aprobada. O2 conserva todos los destinos mediante su runner, con reconciliación adicional de sesión.

| CA | Destino arquitectónico | Verificación futura, conservada |
|---|---|---|
| CA-01 | Gate de aceptación | Cierre canónico M2 y heredados; mock no lo sustituye |
| CA-02 | Captura/contexto | Cambiar maestro/revisiones tras iniciar no retargetea |
| CA-03 | Resolver/capability gate | Tarea/feature no verificada rechaza antes de carga/envío |
| CA-04 | Admisión y derechos | Faltan declaración/consentimiento: rechazo sin eco privado |
| CA-05 | Upload/resolver | Malformado/oversize/hash/ajeno: rechazo sin conversión oculta |
| CA-06 | Publisher stems | Cuatro assets del take, sin toma nueva ni cambio maestro |
| CA-07 | Conformidad stems | Muestras alineadas, error<−30dB y escucha real |
| CA-08 | MixRevision/Web Audio | Mute/solo/volumen/silencio y recarga sin alterar fuentes |
| CA-09 | Handler mezcla/publicación CPU | Ganancias/sources efectivos; hijo con todos los padres cuando aplica |
| CA-10 | Preview/export mixer | Sincronía/niveles/silencio/clipping/saltos y escucha humana |
| CA-11 | Handler export/medidor | Archivo final decodificado cumple LUFS/TP/formato/bits/tasa |
| CA-12 | Original/ZIP stems | Bytes originales;48kHz/amplitud/alineación/hashes de todas las pistas |
| CA-13 | Metadata writer/reader | Lector independiente recupera take/portada/letra histórica solicitada |
| CA-14 | Terminal export | Objetivo fallido no se anuncia conforme; conserva original/evidencia |
| CA-15 | Compositor análisis/resultados | Todas las familias ligadas al audio/método/contexto y visibles para N0 |
| CA-16 | Estados por método | Ausentes/inciertos explican motivo y no ocultan válidos |
| CA-17 | Conformidad análisis | Loudness/anotaciones independientes; etiquetas no fingen medida |
| CA-18 | Binding de alineación | Single/composite/version/hash sobreviven cambio de letra vigente |
| CA-19 | Karaoke/LRC/SRT | Seek/pausa/revisión; parseo y tiempos finitos ordenados en duración |
| CA-20 | Revisión temporal | Incertidumbre/omisión/instrumental y corrección sin reescribir evidencia |
| CA-21 | Gate de alineación real | Canto castellano, omisiones/repeticiones/silencios, anotación y escucha |
| CA-22 | Comfy generación/Artwork | Varias opciones con pins/semillas; elección explícita de portada |
| CA-23 | Comfy edit/referencia | Nueva imagen, antecedentes/derechos y anterior preservada |
| CA-24 | Upload→Artwork/fondo | source upload/procedencia, sin habilitar generación ni I2V |
| CA-25 | Gate Comfy real | Docker/CUDA/generación+ref/seguridad/VRAM/RAM/unload/revisión visual |
| CA-26 | Scene/Timeline/TimingRevision | Palabra sincronizada, take/audio correcto e incertidumbre visible |
| CA-27 | Features y escena reactiva | Onda/espectro/partículas responden a audio/seek/silencio |
| CA-28 | Renderer/FFmpeg/producto | Decodificar canción completa; fps/res/duración/audio/sync/legibilidad y dos reproductores |
| CA-29 | Benchmark N0 | Canción representativa5070 y recursos/tiempo frente a objetivo prefijado |
| CA-30 | Upload+compositor musical | Capacidad real/roles/derechos; hijo y maestro intacto |
| CA-31 | Gate audio propio | Ruta producto y escucha de motivo/estructura/acompañamiento/artefactos |
| CA-32 | Selector calidad alta | Sólo perfil M0 validado y valores efectivos; ausente deshabilitado |
| CA-33 | Gate mejora musical | Pareja misma metadata/texto, niveles igualados y GPU/RAM/escucha |
| CA-34 | Preset/captura | Uso congela valores y referencias, edit posterior no altera historia |
| CA-35 | Preset/admisión | Ref ausente/permisos/param incompatibles rechazan sin omitir ni simular |
| CA-36 | Cierre portable/lectores | Roundtrip completo inferencia+CPU/letras/maps/master/presets/medios/rights |
| CA-37 | Import sandbox/catalog | Traversal/enlaces/duplicates/case/bomba/version/hash/ausente/ajeno sin promoción parcial |
| CA-38 | Import intent/CAS | Colisión/replay/concurrencia/remapeo explícito sin sobrescritura/mezcla |
| CA-39 | Filtro portable privado | Sin claves/paths/PIDs/leases; letra/fotos necesarias sólo payload privado |
| CA-40 | Mantenimiento/corte biblioteca | WAL+assets/referencias,integridad/FK/FTS/catálogo/locks/hashes |
| CA-41 | Restore nuevo/reconciliación | Biblioteca/búsqueda/reproducción, jobs inertes y dependencias faltantes diferenciadas |
| CA-42 | Backup/restore/activation intent | Fallo/cancel/disco/corrupción preserva copia válida/original y rollback |
| CA-43 | Ejercicio real de recuperación | Copia/cohorte autorizada,before/after,restore nuevo; activar con backup+exclusividad |
| CA-44 | Recovery por frontera | Cancel/acuse/restart raw/post/rename/commit/render/import/backup sin duplicar/parciales |
| CA-45 | Storage gate compartido | Ext4/UUID/NOREPLACE/CAS/replay/restart reales; wrong backend aborta |
| CA-46 | Coordinador/GPU/Ollama | Una residencia,cap libre−margen,picos/RAM/spill/unload y restauración propia |
| CA-47 | Offline/privacidad/eventos | Sin Internet/claves externas/runtime-download/eco privado ni progreso ficticio |
| CA-48 | Manifest/DTO/compatibilidad | Origen/hashes/rights/conjunción,v1/v2 intactos y cambios decididos antes de migrar |
| CA-49 | Matriz de aceptación | CPU,fixture,E2E,FFmpeg/ext4,GPU,browser y humanos registrados separadamente |

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| M1 storage y M2 composición no integrados | Alta, dependencias abiertas | Alto | Apertura técnica por ADR-0037; relectura de seams liberados y gates reales antes de integrarlos. |
| PostPlan y publicaciones por take no sirven para export/render/upload | Alta | Alto | Contratos/intenciones M3 propios; compartir primitivas, nunca identidad de inferencia ficticia. |
| Capacidad stems/F19/alta calidad no acreditada | Alta | Alto | Selección/conformidad M0, licencia/peso seguro, escucha y gates por tarea. Scope permanece obligatorio. |
| Comfy no integrado, permiso o VRAM insuficiente | Alta | Alto | Gate separado generación/ref; evaluar candidatos seguros; unload hijo y medición5070 antes de habilitar. |
| Error o ambigüedad de alineación cantada/compuesta | Alta | Alto | Binding por fragmento, uncertainty, revisión humana y cohorte anotada. Segmentación sin truncar letra/audio. |
| LUFS/TP incompatibles con ganancia lineal | Media | Alto | Medir salida decodificada; rechazo honesto. Una política dinámica sería decisión aparte explícita. |
| Desfase mixer/browser/render o memoria por stems largos | Media | Alto | Transporte común, sample clocks y presupuestos; comparar export y escucha. Worklet requiere conformidad propia. |
| Renderer headless lento o diferencias fonts/layout | Media | Alto | Bundle cerrado/frame time explícito; pin/licencia; probes fullsong. CA29 permanece abierto si falla. |
| Codec de vídeo no presente o incompatible browser | Media | Alto | Inventario real del FFmpeg fijado y decodificación; no introducir codec GPL/nonfree silenciosamente. |
| ZIP/import reescribe historia o recupera autoridad activa | Media | Alto | Lectores versionados, rechazo de colisiones, mapa de import separado y jobs inertes. Negativos por estructura/bytes. |
| Backup coherente requiere ventana larga | Alta en baseline exclusivo | Medio-alto | Exponer mantenimiento/cancelación; E/S fuera writer; conservar copia previa. Pins durables serían mejora posterior. |
| Activación nueva cambia raíz sin cambiar BD de forma recuperable | Media | Crítico | Contrato de binding/activation intent y crash rollback previo al código; no activar con procedimiento parcial. |
| Ampliación genérica de ADR0074/0077 | Media | Alto | Namespace privado M3 y decisión explícita de formatos; migraciones sólo aditivas salvo ADR nuevo delimitado. |
| Sesión O2 duplica autoridad o bloquea slots | Alta en O2 | Alto | Runner sin slot mientras espera; única revisión congelada, checkpoints atados a jobs y reconciliación probada. |

## 7. Preguntas abiertas

El plan debe incluir tareas explícitas de concreción y sus dependencias. Cada contrato/métrica se ratifica antes del RED de su implementación dependiente. Los gates reales preceden a habilitar o aceptar esa capacidad, sin exigir producto terminado para planificar. Ninguna incógnita reduce las14funciones/49CA. ROOT conserva la resolución autónoma mediante arquitectura y evidencia.

| ID | Decisión necesaria | Propuesta y punto de resolución |
|---|---|---|
| D-01 | Elección cerrada O1 | ROOT eligió O1 el2026-10-11T14:16:13.016842+00:00. ADR0080 propuesta; revisión/QA/adopción pendientes. No se atribuye lectura personal al propietario. |
| D-02 / I-05 | Requests/planes/recibos/intenciones M3 | Namespace ProductionRequestV1 discriminado por operación; `recipe/hash` único, contexto, fuentes, derechos, perfil, tooling y salidas esperadas. El plan incluye una tarea de concreción de campos/versiones/publicación por sujeto, previa al RED dependiente. |
| D-03 / I-05 | Revisiones SQL y autoridad de derivados | MixRevision/LyricsTimingRevision y producción/publicación aditivas. El plan incluye concreción FK/unique/CAS/owner/schema antes del RED dependiente. Analysis original no cambia por corrección. |
| D-04 / I-05 | Manifiestos/Timeline/Song portable | Conservar manifest/song v1/v2 históricos. Evaluar si CPUv2 cubre los sujetos M3 sin romper lectores; si no, nuevo formato discriminado con ADR específico. TimelineV2 para tiempos/bindings N0; nada nuevo en schema cerrado v1. Resolver mediante tarea contractual del plan antes del RED dependiente. |
| D-05 / I-03 | Loudness, stems y equivalencia mixer | Propuesta: LUFS objetivo±0,5LU y TP≤−1dBTP medidos al final. Error stems `20log10(RMS(sum−source)/RMS(source))<−30dB`, sin ajustar ganancia/offset para ocultar errores; misma tasa/canales/muestras. Silencio usa caso aparte y fallo no medible. Mixer: ≤1muestra de offset y residual<−60dB en PCM común antes del codec, luego escucha. ROOT ratifica fórmulas/medidor/cohorte antes de RED; son objetivos propuestos, no resultados. |
| D-06 / I-03 | Análisis y alineación por método | Congelar anotaciones independientes y métricas por resultado. Propuesta inicial palabra: mediana≤100ms,P95≤250ms; contabilizar omitidas/repetidas/unmatched aparte. Beats tolerancia70ms/F1; key/secciones necesitan métrica/rúbrica propia. ROOT debe cerrar umbrales numéricos y política incertidumbre antes de RED de cada método; no se declara capacidad por esos números. |
| D-07 / I-04 | Perfiles N0/render/tiempo | Propuesta CPU offline30/1fps,1080p16:9 y equivalente vertical; fuente local Inter fijada; sync de palabra≤1cuadro, deriva audio/vídeo≤1cuadro de principio a fin. La cohorte incluye canciones completas con sus duraciones reales, incluida Libre4:15; no se limita producto o aceptación a3min. ROOT ratifica presupuesto de minutos por perfil/duración antes de medir. El candidato anterior3min/10min no es un umbral aprobado ni permite abreviar una canción. Inventario codec/browser y gate/licencias preceden a RED; fracaso no rebaja objetivo retrospectivamente. |
| D-08 / I-05 | ZIP límites y política colisiones | Propuesta catálogo cerrado:100000entradas,100GiB expandido,2GiB/entrada,ratio máximo100:1, profundidad16; cuotas/disco explícitos. Son límites de entrada, no promesa de capacidad5070. ROOT ratifica límites mediante una tarea contractual del plan antes del RED de import. Rechazo por colisión; replay sólo por recibo propio. Remapeo requiere contrato/evidencia source→local aparte. |
| D-09 / I-07 | Corte/retención/activación de biblioteca | Baseline mantenimiento exclusivo+catálogo+backup nativo, sin writer abierto en copia. El plan incluye concreción de journal/quiesce de todos los mutadores y binding DB/raíz con rollback antes de implementar corte/activación. No heredar retención14d del backup BD como política de biblioteca; propuesta conservar último válido y retención configurada, sin purga automática inicial. |
| D-10 / I-01 | Ganadores stems/F19/calidad alta | ROOT reusa evidencia M0 sólo después de sus gates. Resolver modelos/modos/licencias/cohorte real antes de habilitar; nunca por tabla histórica o nombre. |
| D-11 / I-02 | Modelo/workflows de portada/ref y process tree | ROOT compara generación y edit/ref, pesos/formato/licencia/pins y VRAM real; no se elige checkpoint en esta pasada. Contrato del adapter/workflow cerrado antes de implementar, conformidad real antes de habilitar. |
| D-12 / I-06 | Disponibilidad real de componentes M2 | Releer variantes CPU/resolver/publisher/DTOv2 después de liberación canónica. T02 puro no sustituye dichas unidades. Bloquear unidad dependiente, permitir independientes autorizadas tras plan. |
| D-13 / I-08 | Material autorizado y anotaciones/escucha | ROOT coordina cohorte privada representativa y revisión humana. No usar biblioteca activa/GPU para elaborar este diseño. Toda aceptación perceptual mantiene su propia evidencia pendiente. |

La elección O1 permite pasar a planificación después de revisión/QA/adopción documental de ROOT. El plan incluye D02–D04/D08–D09 como tareas de concreción con gates previos al RED de sus dependientes; no exige resolverlas fuera del plan. También incluye selección/integración/conformidad de modelos y renderer, métricas, licencias y material completo. Los números y candidatos D05–D11 permanecen propuestas pendientes: esta elección no los ratifica. Un gate abierto identifica trabajo obligatorio, nunca un motivo para recortar el hito o sustituir evidencia real por fixtures.

### Fuentes y evidencia de esta pasada

La spec congelada tiene SHA256 `908efce7635cf7ce267ed16fa71f990c57162b6b7d925e95b6f440907ef8ed63`. El release enumera31archivos congelados. Se verificaron31/31 contra sus hashes antes de redactar. Ninguno se modificó.

Se leyó primero el checkpoint vigente de CONTINUE-HERE y se consultó el registro de memoria del agente. Ese registro era anterior a M3; las decisiones descritas proceden de la spec y los documentos/seams actuales, no de resultados antiguos de M0.

La consulta knowledge-find por tipo ADR/contexto M3 no devolvió entradas. Se aplicaron Constitución y ADR explícitos de `docs/decisiones` del snapshot. No se abrió journal ajeno ni se creó marcador; ROOT conserva el único marcador de lote.

Validación histórica de primera pasada,2026-10-11T14:12:31Z: siete secciones1–7;49CA únicos y14funciones únicas; cero placeholders y cero comentarios guía. Estado borrador y elección pendiente. Snapshot31/31 y fuentes adicionales15/15 conservan sus SHA. La spec canónica conserva SHA908efce completo indicado arriba y estado aprobada.

En el canon,30/31entradas del release coincidían. `docs/roadmap/2026-10-10-m2-iteracion-creativa/tasks.md` cambió concurrentemente a SHA `eb26cf2f16dc5c9158d8763a7919f4d32f631ba57ef22d50467391da7cd122e3`. Este actor no escribió ese fichero ni lo restauró. El snapshot M2 original permanece intacto; la integración deberá releer el ledger canónico vigente.

Evidencia histórica anterior conservada en design.md original. En esta segunda pasada, escritura exclusiva selected-design.md y adr-0080-proposal.md privados. ROOT registra report/receipt y hace revisión/QA/adopción. Después de esa adopción, el handoff a planner exige respetar O1 y mantener tareas de concreción y gates de todo el scope.

Se muestrearon fuentes de código, no todo el backend. Las páginas oficiales se consultaron sólo para Web Audio, scanner FFmpeg y captura de cuadros. Documentan primitivas, no el despliegue actual, sus pins ni rendimiento/calidad. No hubo descargas, instalación, tests de producto, inferencia, GPU, Docker/WSL/servicios, SQL, Git ni actualización canónica.

El inventario SHA de lecturas adicionales aparece a continuación. Las rutas son relativas al repositorio y permanecen readonly para este actor.

### Inventario SHA de lecturas adicionales

| Ruta | SHA256 |
|---|---|
| `apps/server/app/models/__init__.py` | `9c86ef171968e799908068c1f98ce47186b9e2ed3337c019a7e9696d38dac0df` |
| `apps/server/app/worker/planning.py` | `3aca3783d91b398fc4932f0c61759563cc2a1d4088ce23ef81b0186148bb8dcd` |
| `apps/server/app/worker/contracts.py` | `4c04a5a5698e88ab1d31f65e9f3924e6b63e077b6dc2ee282f35da2c85fb891b` |
| `apps/server/app/worker/execution.py` | `f2cb4a27f7bf531f98d9f3f2698e8d3509da9306c6d3b602fed5fc7ce3cb617f` |
| `apps/server/app/queue/chains.py` | `65bbbf0a53a121e2c4efaaa95df73d8d1764eba09b51cb9debfdc667df5eeb7f` |
| `apps/server/app/queue/runtime.py` | `4bcc34b3f6486dec7c7a627b80fc545b05fb6da3703dd60b568f9d329a9bc28e` |
| `apps/server/app/queue/resolver.py` | `8278f3c623ebd7bd7e55ad6d40dade4f86ee809d63407c0379fe5bd9db630b68` |
| `apps/server/app/domain_routes.py` | `ecec486608fac6a59e0cfef111f523c321fe5c841fb62ca5944b9938b03f7e12` |
| `apps/server/app/backup.py` | `8a677bd8a25c05be484db10464a0010e0462be127e4f96881a90faa0896bcf1d` |
| `apps/server/app/snapshots.py` | `61189b40618a86bdaf7cd0266ab565112b55dc2de053875925c4567fff8c46f4` |
| `apps/engines/acestep/descriptor.py` | `64fab407f9d48d2fb29d3142149d40bc69ce9db755341d536de643ccba630e2f` |
| `apps/engines/analysis/engine_analysis/descriptor.py` | `5627a19c0a0eccd9c127b83ff7232f7f7b5a43fecf491121202a5cdd35c45e17` |
| `apps/web/components/GenerativeViz.tsx` | `8469a1b511bda61192c599c64e25c831307ecb8c836dd2976408cefcfdba7c6a` |
| `apps/web/components/PlayerContext.tsx` | `13406a75980366e766eaf00706bef480951d3cec93d3174ce82c24ea47f003ab` |
| `packages/contracts/timeline-v1.schema.json` | `d85666a0dbb7f9e67a6d7442d2e44d6b971ca9584eb424941b6330e582948660` |


### Evidencia privada de selección y preservación

[Selección de ROOT](../../../.cache/dev-cycle/m3/production-design-options-20261011/selection-root.receipt.json) registra O1 y el alcance49CA/14funciones. [Diseño original](../../../.cache/dev-cycle/m3/production-design-options-20261011/design.md) conserva SHA256 c9d8f7382ebcc56343d9445206aaddb41cf23d3eaeba84ec2d689e3feb28c35d. [Brief de segunda pasada](../../../.cache/dev-cycle/m3/production-design-options-20261011/second-pass-brief.md) fija ownership privado y las tareas de concreción del plan.

El snapshot31 permanece readonly. La divergencia histórica de tasks M2 indicada arriba no se adopta: el recibo de selección identifica una revisión posterior66bd3b9e bajo ROOT. El planner releerá el ledger/seams canónicos vigentes. Ningún cambio ajeno se restaura desde estas copias.

Estado de decisión aprobado significa elección arquitectónica ratificada por ROOT. ADR propuesta, adopción documental, implementación de14funciones y aceptación49CA son estados distintos. No hay producto, publicación, instalación, SQL, GPU, servicios, Git o ledger ejecutados por esta segunda pasada.

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-10-11 | Primera pasada privada: dos opciones, O1 recomendada,14funciones/49CA conservados y decisiones pendientes explícitas. |
| 2026-10-11 | Segunda pasada: ROOT eligió O1; ADR0080 propuesta, matrices intactas, tareas de concreción en plan y canciones completas incluidas. |


## Incorporación documental de ROOT — 2026-10-11T15:01:22.398925+00:00

DecisiónO1 incorporada trasreview1A/BsinImportant/MinorA01corregido yQA175/175; ROOT88artefactos/48fuentes/39links verificados. Plan/contratosdeimplementación/capacidades/GPU/E2E/audio/escucha/aceptaciónM3pendientes. Las referencias a propuesta/adopciónpending en el cuerpo describen la preparación original; este acta fija el estado documental vigente.


## Aprobación y adopción ROOT del plan — 2026-10-11T16:16:11.792117+00:00

El propietario delegó la implementación de todo el roadmap y la elección entre alternativas. ROOT aprueba e incorpora este plan tras revisión2 fresca A/B sin gaps y QA documental563/563. Se han verificado107payloads,50fuentes,20enlaces; ledger/coverage-check/qa-gateoficialesexit0.42tareas/11fases/49CA14funciones/34E2E15manuales permanecen íntegros. No tareas M3cerradas ni producto probado. Consumo realnull. M2actual3/30(T03purocerrado),heredados ycalidad/humano/M2hito siguenpendientes; dependencias técnicas se liberanporunidad yfinalM3requiereM2cerrado. Originales privados/revisiones/QA intactos.
