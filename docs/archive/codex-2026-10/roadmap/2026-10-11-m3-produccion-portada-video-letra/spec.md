---
spec: m3-produccion-portada-video-letra
descripcion: Producir canciones con stems, mezcla, análisis, letra sincronizada, portada, vídeo N0 y recuperación portable.
estado: aprobada
creado: 2026-10-11
actualizado: 2026-10-11
evaluacion: n/a (proyecto personal; ADR-0001)
design: design.md
plan: improvement-plan.md
depende-de: m2-iteracion-creativa
validacion: ROOT bajo delegación vigente del propietario; 2026-10-11T13:51:27.703097+00:00; requisitos aprobados, implementación y aceptación pendientes.
generacion:
  inicio: null
  fin: null
  fuente: estimado
  tokens_reales: null
  eur: null
  horas_ia: null
  duracion: null
  ratio_usado: null
  nota: Consumo real desconocido; no se atribuye tiempo de reloj a trabajo IA. La preparación comparte el marcador del lote de ROOT.
---

# Spec · M3 — Producción, portada y vídeo con letra

> **Estado:** requisitos aprobados por ROOT bajo delegación del propietario. Decisión arquitectónica O1 aprobada y diseño incorporado tras revisión y QA documental; plan pendiente. M3 no está implementado ni aceptado.
> **Evaluación:** n/a económica por ADR-0001. **Plan de implementación:** aprobado e incorporado por ROOT tras revisión y QA documental. **Diseño:** O1 aprobado e incorporado por ROOT tras revisión y QA documental.
> **Terminología:** take es una versión de audio; stems son pistas separadas vinculadas al take; cover musical es reinterpretación y portada es imagen. N0 es vídeo con letra o visualizador, sin planos generativos. Exportar una canción y respaldar la biblioteca son operaciones distintas.

## Contexto y objetivo

El propietario necesita convertir los takes de una canción en entregables utilizables: mezcla, audio preparado por destino, letras temporizadas, portada y vídeo N0. También necesita conservar y recuperar su biblioteca sin perder versiones, derechos o procedencia.

La fuente de alcance es [el roadmap](../README.md), §Secuencia de aceptación de hitos, y [el catálogo funcional](../../producto/funcionalidades.md), F-06, F-18, F-19, F-30 a F-35, F-40, F-41, F-44c, F-70 y F-85. Todos son obligatorios en M3; no se convierten en opcionales por dificultades de modelo, hardware o recuperación.

ADR-0037 permite definición y futuras unidades técnicas independientes con spec/plan aprobados y dependencias documentadas. La aceptación final requiere M2 cerrado, con sus condiciones heredadas de M1, generaciones propias reales y escucha musical. T02 de M2 cierra captura/readers/proyección pura; no acredita admisión, BD, composición ejecutada, publicación, UI o calidad. T03 ya está cerrado como planificador puro por muestras; su QA Windows/Linux no acredita render, publicación o calidad de audio ni el cierre de M2.

### Usuarios y actores

| Actor | Necesidad o responsabilidad |
|---|---|
| Propietario local | Seleccionar take, escuchar, mezclar, revisar tiempos y portada, declarar derechos, exportar y comprobar recuperación. |
| Web Next.js | Controles en castellano, reproducción, karaoke, comparación y estado real de los trabajos. |
| Server FastAPI | Autorizar pertenencia, resolver entradas, congelar contexto, encolar, postprocesar/renderizar, publicar y escribir SQLite. |
| Engine musical / separador / análisis | Ejecutar capacidades verificadas y entregar salidas crudas y telemetría por `/v1`. |
| ComfyUI headless Docker/CUDA | Generar y editar imágenes con workflows y nodos fijados y auditados; sin persistencia de dominio. |
| Ollama compartido y otros consumidores GPU | Servicio ajeno cuya residencia se observa y coordina sin detenerlo o borrar modelos. |

### Escenarios de uso

1. Abrir una canción, escoger el take maestro o uno concreto, separar stems, escuchar sus controles y exportar una mezcla nueva sin perder el origen.
2. Corregir tiempos de la letra realmente asociada a ese take y usar esa revisión en karaoke, LRC/SRT y vídeo N0.
3. Generar varias portadas a partir de estilo/letra, editar una por referencia o subir una imagen propia; elegirla para exportación y fondo N0.
4. Subir un tarareo, maqueta o voz con derechos y obtener una canción hija mediante capacidad comprobada; comparar un modo de calidad alta realmente viable.
5. Reutilizar un preset y conservar qué valores efectivos produjo; exportar una canción completa y restaurar una biblioteca sin sobrescribir historia.

## Decisiones de diseño

Esta tabla aplica decisiones vigentes. No selecciona arquitecturas nuevas, modelos, esquemas, endpoints o ADR.

| Decisión | Elección | Motivo |
|---|---|---|
| Raíz de contenido | `song`, con pertenencia directa o transitiva y referencias globales autorizadas | Constitución §1.2; ADR-0041. |
| Versiones de audio | Edición crea take hijo; stems son assets del take; maestro por acción explícita | Constitución §1.3; pipeline-audio §5. |
| Procedencia CPU | Autoridad propia real, sin modelo/engine/seed inventados; respetar formatos v1/v2 aplicables | ADR-0074; post CPU de inferencia conserva origen de inferencia. |
| Despliegue | Web/server/engines en Docker, Ollama compartido WSL2 como excepción | Constitución §2; ADR-0035. |
| Inferencia | Música siempre local; demás funciones locales de fábrica; resolver capacidades verificadas | Constitución §§1.1, 1.4 y 2. |
| Publicación y almacenamiento | Solo server; paquetes sin sobrescritura, CAS/replay y raíz ext4 acreditada dentro del proyecto | ADR-0069 y contratos históricos de M1/M2. |
| Evolución | Code-first, `/v1` compatible y ampliaciones aditivas; arquitectura fija los formatos antes del RED | Constitución §§2–3; ADR-0074/0077 no autorizan ampliación genérica de sus excepciones. |

## Configuración / parámetros

| Parámetro | Clave / mecanismo | Default | Valor objetivo |
|---|---|---|---|
| Take fuente | ID autorizado de take; maestro resuelto una vez al iniciar | Maestro cuando existe; selección explícita si falta | Contexto sellado con IDs/hashes, sin cambiarlo durante el trabajo. |
| Destino streaming/web | Perfil de exportación | Destino por defecto | MP3 320 kbps o FLAC, −14 LUFS, true peak ≤ −1 dBTP. |
| Destino broadcast/vídeo | Perfil de exportación | Acción explícita | WAV 48 kHz/24 bit, −23 LUFS, true peak ≤ −1 dBTP. |
| Destino podcast | Perfil de exportación | Acción explícita | WAV 48 kHz o MP3, −16 LUFS, true peak ≤ −1 dBTP. |
| Stems exportados | Perfil stems | Sin normalizar | WAV/FLAC 48 kHz, alineados muestra a muestra, ZIP. |
| Original | Exportación master | Sin transformar | Bytes originales de `master.flac`. |
| Ganancia y remuestreo | Pipeline del server | Ganancia lineal y soxr | Sin normalización dinámica silenciosa; medir después de codificar. |
| GPU | `STUDIO_VRAM_MARGIN_MB`, residencia y modo verificado | Margen documentado 512 MB, BF16 por defecto | VRAM libre menos margen; una residencia; picos y RAM/desbordamiento observados. |
| Upload audio | Validación por contenido | Derechos obligatorios | ≤50 MB y ≤10 min; además límites de tarea verificada. |
| Upload imagen | Validación por contenido | Derechos y consentimiento aplicables | ≤20 MB y ≤8192 px; sin confiar en extensión. |
| Stems | Descriptor de `audio.stems` | Disponible sólo si verificado | Voz, batería, bajo y otros; conformidad suma/error < −30 dB. |
| Letra, tiempos y vídeo | Versión histórica efectiva del take y revisión temporal | Sin sustituir por letra vigente Song | Segundos finitos; tiempos ordenados dentro del audio; fps racional; vínculo por hash. |
| Preset | Nombre, tipo y payload autorizado | No aplicado sin selección | Valores efectivos congelados por uso; referencias verificadas. |

Las tolerancias de loudness para todos los destinos, la métrica exacta de error de stems, los umbrales de precisión de alineación y los perfiles de render se concretan antes de sus pruebas en diseño (I-03/I-04). El objetivo y su gate permanecen obligatorios; una medición ausente nunca se presenta como conforme.

## Arquitectura y componentes

Se reutilizan `apps/web`, `apps/server`, `packages/audio-post`, `packages/contracts`, cola `job/job_dependency`, intentos y publicación durable de M1/M2. Esta reutilización es una dependencia, no una declaración de integración completa.

Las entidades previstas incluyen `song`, `take`, `lyrics_version`, `lineage_edge`, `asset`, `analysis`, `upload`, `artwork`, `preset`, `video_project`, `render` y `export`. Análisis está ligado al take y, para letra/secciones, a sus versiones efectivas. El montaje tiene autoridad en BD; las instantáneas de disco son derivadas. No se inventa aquí una nueva columna, migración ni un contrato privado M3. Los contratos definitivos deben poder representar honestamente mezclas, alineaciones corregidas, exportaciones y renders; si las decisiones vigentes no bastan, arquitectura propone el ADR antes de modificar producto.

Web añade producción, portada, vídeo N0 y exportación dentro de canción; presets y backup usan bibliotecas globales autorizadas. Mezcla interactiva usa Web Audio según F-31; el server produce el archivo exportado con contexto y resultados comprobados. Engine musical/separador, `engine-analysis` y `engine-comfy` son consumidores de capacidades: no se presume que un modelo histórico soporte una tarea por su nombre.

El server resuelve IDs a copias propias verificadas, roles contractuales y paths relativos seguros. El navegador no entrega rutas ejecutables, expresiones FFmpeg ni workflows arbitrarios. Engines escriben sólo su rawdir; FFmpeg, publicación, manifiestos, render y SQLite pertenecen al server. Las recetas M2 tienen ocho operaciones cerradas: M3 no añade operaciones a su versión1 por conveniencia. Las ausencias CPU se preservan y el cierre portable con CPU exige versiones compatibles sin alterar bytes históricos.

### Datos e integraciones

Los datos privados incluyen audio subido/generado, letra y sus versiones, imágenes, referencias, presets, análisis, mapas, renders y recetas/recibos. Un preset no confiere capacidades de timbre de F-71 ni entrenamiento LoRA de M5. Sus referencias sólo se consumen si la función ya dispone de capacidad verificada y derechos.

Cada resultado conserva inputs, padres, receta/contexto efectivo, parámetros, pins de modelos/herramientas/workflow/nodos, mediciones reales y derechos aplicables. `commercial_use` es la conjunción de dependencias; una fila de licencia histórica ni una declaración del proveedor garantiza autoría exclusiva o corpus auditado. Los manifiestos excluyen letra literal y fotos reales; el ZIP privado contiene los materiales necesarios con advertencia de contenido privado, sin claves, leases, PIDs o autoridad de procesos restaurable.

La canción portable incluye su raíz completa y el cierre necesario de referencias y antecedentes, sin expandir proyectos ajenos completos. Importar preserva evidencia original, identidad/linaje compatible y derechos; cualquier remapeo autorizado se registra como operación nueva, sin fingir que el importador generó la inferencia histórica. El backup incluye SQLite y todos los medios/referencias necesarios de la biblioteca, con catálogo, hashes y versiones/locks aplicables. No descarga ni incluye pesos por defecto; identifica los requeridos y distingue recuperación del contenido de disponibilidad de generación.

## Flujo (paso a paso)

1. El usuario abre canción y elige take. El server resuelve y congela fuentes, derechos, letra histórica y revisiones.
2. La UI permite stems, mezcla, análisis y alineación sólo según capacidades y datos disponibles. Muestra faltantes y errores por resultado.
3. El usuario ajusta mezcla, revisa letra/tiempos y elige preset, imagen generada/editada o subida. Cambios de letra no reescriben el audio cantado.
4. Cada trabajo valida parámetros, pertenencia, derechos, contenido y recursos antes de reservar/enviar; el progreso sigue eventos reales.
5. Engines entregan raw y el server valida/postprocesa, mide y publica resultados propios recuperables. Las ediciones musicales crean hijos; derivados no cambian automáticamente el maestro.
6. El usuario previsualiza karaoke/vídeo N0 y visualizador, selecciona exportación y recibe artefactos con contexto y mediciones finales.
7. Exportar/importar canción valida el cierre completo y publica sin colisiones ni efectos parciales; restituir no encola jobs históricos.
8. Backup captura un corte coherente de biblioteca; restauración verifica copia en destino propio, permite comparar antes de activar y conserva recuperación de la biblioteca previa ante fallos.

## Alcance

### Dentro (esta iteración)

| ID | Resultado exigido |
|---|---|
| F-06 | ZIP portable completo de canción, con audio, letras/historia, portada, vídeo, manifiestos, referencias necesarias y restauración validada. |
| F-18 | Regeneración de calidad alta mediante más pasos o modelo mayor que realmente cabe con margen en RTX5070/12GB; nuevo hijo y evaluación musical. XL es candidato, no requisito de compra de GPU ni adopción automática. |
| F-19 | Canción desde tarareo, maqueta o voz propios, como referencia o para acompañamiento; capacidades verificadas y declaración de derechos, nuevo take con linaje. |
| F-30 | Separación bajo demanda de voz, batería, bajo y otros, assets asociados al take, conformidad técnica y escucha real. |
| F-31 | Mezclador con mute, solo, volumen, reproducción y exportación de mezcla reproducible; conserva stems y padres/versiones. |
| F-32 | Destinos streaming/broadcast/podcast, WAV48kHz, ZIP stems, original, metadatos, letra embebida solicitada y portada si existe. |
| F-33 | BPM/beats, tonalidad, secciones y loudness al terminar cada take; métodos/procedencia y fallos parciales honestos, consumibles por vídeo. |
| F-34 | Tiempos por palabra/línea, karaoke, LRC/SRT, revisión/corrección de alineación y manejo de incertidumbre con letra histórica efectiva. |
| F-35 | Varias opciones de portada desde estilo/letra, edición con referencia, subida propia y exportación con audio. |
| F-40 | Vídeo N0 con tipografía cinética sincronizada por palabra sobre portada/fondo/visualizador, render/export local y audio final medido. |
| F-41 | Visualizador reactivo de onda, espectro y partículas, como fondo N0 o vídeo propio, basado en el audio efectivo. |
| F-44c | Imágenes propias como portada o fondo N0; derechos y consentimiento cuando corresponda. |
| F-70 | Presets con nombre de estilo, parámetros, referencia de timbre y estilo visual; captura efectiva por uso, sin reescritura retrospectiva. |
| F-85 | Backup/restauración de biblioteca consistente SQLite/assets, hashes/locks, recuperación comprobada y ejercicio seguro con biblioteca real. |

### Fuera (siguientes specs)

- Vídeo N1–N3, personajes, protagonista desde fotos, I2V, sincronía labial, guion de planos, editor multipista de timeline y herramientas de render avanzadas de M4. No elimina previsualización, exportación ni recuperación N0.
- LoRA, segundo motor musical y nueva inferencia de referencia de timbre de M5. F-70 conserva la referencia declarada y sólo la aplica a capacidades ya verificadas.
- Clonar voces reales, usar imágenes sin consentimiento, publicar en redes, acceso LAN, multiusuario y comercialización. Gate GC sigue vigente; uso personal no lo declara satisfecho.
- Adoptar RoFormer con permisos ambiguos como predeterminado, afirmar XL viable sin benchmark, o sustituir música local por servicios externos.
- Ampliar excepciones SQL de ADR-0074, reescribir esquemas históricos o añadir servicios de infraestructura sin decisión aparte.

### Restricciones

Constitución §§1–4 obliga local por defecto, canción como proyecto, takes inmutables, maestro explícito, UI honesta y castellano vía `next-intl`. Identificadores en inglés; ULID, segundos, Hz, LUFS/dBTP, bytes y UTC conforme convenciones. El producto corre en Docker, server sin torch; cola SQLite con GPU1/CPU2 y remote opcional apagado. No fallback externo silencioso.

RTX5070/12GB y RAM WSL son límites reales. Una residencia GPU, BF16 salvo modo alternativo comprobado, límite calculado con memoria libre y margen, medición de pico y memoria compartida/desbordamiento. El turno observa Ollama, descarga sólo residentes que interfieren y registra intervención propia; restaura sólo los observados/descargados por su turno. No para servicio, borra modelos ni presupone exclusión frente a aplicaciones ajenas.

Todo dentro del proyecto, incluida persistencia física VHDX de ADR-0069. UUID/raíz/NOREPLACE deben acreditarse; no fallback a NTFS/9p/tmpfs ni directorio parcial para aparentar aceptación. Runtime offline, pesos safetensors/gguf/onnx con revisión y SHA, sin pickle, `torch.load` o `pickle.load`; código remoto/nodos por commit y hash revisados. Modelo/herramienta necesita fila de licencia antes de integrarse; los no comerciales sólo laboratorio identificado.

Puertos host loopback, Host/Origin y token interno; secretos sólo server y sin eco. Uploads se validan por contenido y límites. Declaración de letra/audio/imagen y consentimiento exigibles antes de encolar. Procesos/cancelación/serving/limpieza requieren custodia acreditada: UNKNOWN bloquea efectos hasta reconciliación. Ninguna ruta ZIP, ID o hash sustituye autorización real.

No se fija fecha de entrega, presupuesto ni rendimiento inventado. La promesa N0 «en minutos» del catálogo requiere medición de una canción representativa sobre hardware real y objetivo definido previamente (I-04); no se acredita con fixture corto. TDD, revisión fresca y QA/cobertura por fase pertenecen a la implementación futura. Esta preparación no los ejecuta ni modifica ledgers.

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| Capacidad ausente/no verificada o preset incompatible | UI explica motivo y API rechaza sin enviar; no retaggear tarea/modelo ni activar equivalencia mock. |
| Derechos/autoría/consentimiento ausentes | Rechazo antes de cola o transferencia; conservar contenido previo. |
| Take/referencia de otro propietario/canción, borrado o no listo | Rechazo autorizado sin divulgar paths, letra o existencia ajena. |
| Audio/imagen malformados, oversize, hash cambiado o formatos incompatibles | Validación visible antes de inferencia; conversión explícita con recibo si está disponible, nunca silenciosa. |
| Separación incompleta, análisis parcial o alineación dudosa | Conservar métodos/estado y resultado revisable; no inventar beats/tonalidad/tiempos ni certificar export/vídeo correcto. |
| Objetivo LUFS/true peak inalcanzable | Fallo honesto sin publicar como conforme; conservar original y mediciones de intentos propios. |
| Letra compuesta, instrumental o desajustada respecto al canto | Mostrar contexto real, revisión/partes ausentes; no sustituir por letra Song ni inventar palabras cantadas. |
| Cambio concurrente de maestro/letra/preset/timeline | Contexto ya capturado se conserva; revisión nueva exige acción explícita; conflicto por rev/If-Match cuando aplica. |
| Cancelación, timeout, OOM o ocupación GPU ajena | Estado durable, motivo y cleanup propio acreditado; no bajar calidad/perfil ni usar cloud silenciosamente. |
| Reinicio tras raw/post/render/rename/commit o acuse perdido | Reconciliar intento, autoridad, custodia y publicaciones; reutilizar trabajo durable, no duplicar resultados ni sobrescribir. |
| ZIP malicioso, versión desconocida, medios ausentes o colisión | Rechazo antes de promoción; sin escape, deserialización/ejecución de contenido ni import parcial. |
| Backup interrumpido, datos cambiando o disco lleno | No declarar copia válida, conservar última íntegra y staging propio reconciliable. |
| Restore corrupto/incompatible o fallo al activar | Conservar biblioteca previa, rollback verificable y error; no borrar historia ni reactivar procesos importados. |
| Montaje incorrecto o custodia UNKNOWN | Abort/bloqueo explícito; no adoptar archivos por nombre/hash ni limpiar recursos de terceros. |

## Criterios de aceptación

Todos permanecen sin marcar: son requisitos futuros, no verificaciones realizadas.

- [ ] CA-01 — M3 sólo se acepta con M2 cerrado y sus gates heredados cumplidos; definición técnica ADR-0037 y mocks no satisfacen ese cierre.
- [ ] [GWT] CA-02 — Dada una canción y un take autorizado, cuando se inicia producción, entonces se congela identidad, hashes, revisiones, padres, letra efectiva y derechos; cambiar luego el maestro no retargetea el trabajo.
- [ ] [GWT] CA-03 — Dada tarea/feature no verificada, cuando UI/API solicita cualquier acción M3, entonces se explica/rechaza sin carga ni envío; una prueba sintética identificada no habilita el modelo real.
- [ ] [GWT] CA-04 — Dado audio/imagen/letra sin declaración exigible o foto real sin consentimiento, cuando se solicita usarla, entonces se rechaza antes de encolar y no se expone contenido privado.
- [ ] [GWT] CA-05 — Dado upload malformado, demasiado grande/largo, hash alterado o referencia ajena, cuando se valida, entonces se rechaza por contenido/propiedad/límite sin ruta arbitraria ni conversión oculta.
- [ ] [GWT] CA-06 — Dado un take listo y separación verificada, cuando se solicitan stems, entonces se publican voz/batería/bajo/otros como assets y manifiesto ligado al take, sin take nuevo ni cambio de master/padres.
- [ ] CA-07 — La separación real acredita alineación muestra a muestra y error de suma inferior a −30 dB según métrica fijada antes de prueba, método/modelo/pins y escucha de aislamiento/artefactos; fixture no verifica calidad del separador.
- [ ] [GWT] CA-08 — Dados stems listos, cuando se ajustan mute, solo y volumen, entonces reproducción respeta los controles, incluido silencio y combinación de solos; recargar conserva el estado guardado sin cambiar bytes de stems/master.
- [ ] [GWT] CA-09 — Dada mezcla elegida, cuando se exporta, entonces el server produce el resultado con ganancias/selección efectivas, fuentes/hashes y mediciones; cualquier take musical nuevo es hijo con todos sus padres, nunca reemplazo.
- [ ] CA-10 — Comparación real de reproducción y mezcla exportada comprueba sincronía, niveles, silencio, clipping y ausencia de saltos; método/tolerancia de comparación se fijan antes de validar, y escucha humana acredita utilidad.
- [ ] [GWT] CA-11 — Dado destino streaming, broadcast o podcast, cuando se exporta, entonces el archivo final decodificado cumple −14/−23/−16 LUFS respectivamente con tolerancia acordada y true peak ≤−1 dBTP; formato/tasa/bits se verifican, no se deducen del comando.
- [ ] [GWT] CA-12 — Dada exportación original o ZIP stems, cuando termina, entonces original conserva sus bytes y stems WAV/FLAC48kHz conservan alineación común y amplitud sin normalizar; ZIP tiene todas las pistas declaradas/hashes válidos.
- [ ] [GWT] CA-13 — Dados título/artista/año, take, portada y letra embebida solicitada, cuando se exporta, entonces un lector independiente recupera metadatos, take_id, portada y letra histórica correcta; omitir letra no la embebe.
- [ ] [GWT] CA-14 — Dado post/export cuyo objetivo no se alcanza, cuando termina, entonces no se presenta conforme ni sustituye el original y conserva error/mediciones/procedencia del tratamiento aplicado.
- [ ] [GWT] CA-15 — Dado un take recién terminado, cuando se analiza, entonces BPM/beats, tonalidad, secciones y loudness quedan ligados a sus hashes, métodos/versiones y letra aplicable, visibles y utilizables por N0.
- [ ] [GWT] CA-16 — Dado fallo parcial o audio instrumental/no analizable, cuando se consulta análisis, entonces se identifica cada resultado ausente/incierto y su motivo, sin valores sintéticos de reemplazo; no se bloquea la consulta de los resultados válidos.
- [ ] CA-17 — Análisis real se contrasta con medición de loudness y anotaciones independientes de beats/tonalidad/secciones; criterios por método y confianza se congelan antes de prueba. Etiquetas de letra no se presentan por sí solas como secciones medidas.
- [ ] [GWT] CA-18 — Dado un take con contexto textual histórico single/composite, cuando se alinea, entonces palabra/línea conserva su binding/version/hash y duración; cambiar `current_lyrics_version_id` no cambia su alineación.
- [ ] [GWT] CA-19 — Dados tiempos válidos, cuando se reproduce/se busca/pausa en karaoke y se exportan LRC/SRT, entonces líneas/palabras corresponden al audio y la revisión elegida; formatos se parsean, tiempos son ordenados/finitos y no exceden duración.
- [ ] [GWT] CA-20 — Dada alineación incierta, letra no cantada o región instrumental, cuando se muestra o corrige, entonces señala incertidumbre/faltantes y permite revisar tiempos por palabra/línea sin modificar el audio ni reescribir la evidencia anterior; corrección tiene revisión y origen propios.
- [ ] CA-21 — Escucha y revisión humana sobre audio cantado real en castellano, con palabras omitidas/repetidas y silencios, acreditan alineación y utilidad karaoke; se miden errores contra anotación independiente y umbrales previamente ratificados. Parser LRC/SRT o timestamps mock no acreditan esto.
- [ ] [GWT] CA-22 — Dados estilo/letra autorizados, cuando se generan portadas, entonces se ofrecen varias opciones distintas con parámetros/semillas/workflow/pins y manifiestos; elegir una actualiza portada por acción explícita.
- [ ] [GWT] CA-23 — Dada portada/referencia autorizada, cuando se edita con referencia, entonces produce nueva imagen con antecedentes/hashes/derechos, conserva la anterior y no afirma coherencia de personaje M4.
- [ ] [GWT] CA-24 — Dada imagen subida válida con derechos/consentimiento, cuando se usa, entonces `source=upload` y su referencia/procedencia se conservan como portada o fondo N0; no requiere generación ni habilita I2V.
- [ ] CA-25 — ComfyUI headless real en Docker/CUDA acredita generación y edición por referencia, workflows/nodos/pesos seguros fijados, VRAM/RAM/tiempos y unload; revisión visual humana acredita legibilidad/calidad de opciones. PNG mock no satisface esta capacidad.
- [ ] [GWT] CA-26 — Dada letra revisada y portada/fondo/visualizador, cuando se previsualiza/renderiza N0, entonces tipografía cinética resalta palabras según esa revisión y referencia el take/audio efectivos; muestra incertidumbre sin ocultarla.
- [ ] [GWT] CA-27 — Dado modo onda, espectro o partículas, cuando se reproduce/renderiza visualizador como fondo o vídeo propio, entonces reacciona al audio efectivo y al seek, y regiones silenciosas se distinguen de señal; no usa animación prefabricada como evidencia de reactividad.
- [ ] CA-28 — Render/export real Docker/FFmpeg se decodifica y reproduce de principio a fin: duración, fps/resolución, audio final LUFS/true peak, sincronía sin deriva y correspondencia palabra/pantalla se miden contra referencias; se escucha/ve en navegador y reproductor independiente, sin texto cortado o ilegible.
- [ ] CA-29 — Sobre canción representativa en la5070 se registra tiempo N0, carga CPU/RAM/VRAM y modo efectivo; el objetivo «en minutos», perfiles y tolerancias se fijan antes de prueba y no se cumplen con un clip fixture abreviado. No exige comprar GPU ni usar modelo que necesita16GB.
- [ ] [GWT] CA-30 — Dado tarareo/maqueta/voz propio validado, cuando se solicita referencia/acompañamiento mediante `music.complete`/`music.cover` o capacidad equivalente comprobada, entonces el server resuelve entrada y crea hijo con upload/padres/roles y derechos reales, sin identidad vocal prometida ni cambio automático de maestro.
- [ ] CA-31 — F-19 se verifica por ruta real de producto y escucha sobre material autorizado: la evaluación registra reconocimiento del motivo/estructura y acompañamiento útil, artefactos y límites. Soporte nativo de task sin integración o calidad no cierra el criterio.
- [ ] [GWT] CA-32 — Dado modo de calidad alta validado en M0, cuando se regenera, entonces sólo ofrece parámetros/perfil/pasos/modelo comprobados que caben con margen y publica hijo con valores efectivos; modo ausente queda deshabilitado con motivo y gate abierto.
- [ ] CA-33 — Calidad alta se compara con referencia emparejada usando mismo texto/metadata efectiva, recibos y nivel de escucha igualado; pruebas reales verifican GPU/RAM/desbordamiento y escucha humana registra mejora/compromisos. Más pasos, XL o un hash no prueban mejora musical por sí solos.
- [ ] [GWT] CA-34 — Dado preset con nombre, cuando se crea/edita/selecciona, entonces conserva estilo/parámetros/referencia/estilo visual autorizados; uso nuevo congela valores y refs efectivos y editar el preset no cambia trabajos/takes/renders anteriores.
- [ ] [GWT] CA-35 — Dado preset con referencia no disponible, permisos ausentes o parámetro incompatible, cuando se aplica, entonces muestra/rechaza el problema antes de envío; no omite silenciosamente referencia ni simula F-71/LoRA.
- [ ] [GWT] CA-36 — Dada canción con takes de inferencia/CPU, letras, portada, N0, valoraciones y referencias, cuando se exporta/importa en destino nuevo, entonces el cierre completo conserva historia, padres/roles, mapas, maestro, declaraciones y bytes de medios/manifiestos, con lectores de versiones compatibles.
- [ ] [GWT] CA-37 — Dados ZIPs con traversal absoluto/relativo, enlaces/junctions, entradas duplicadas, colisiones por normalización/case, expansión excesiva, versión desconocida, hash falso, medio ausente o vínculo ajeno, cuando se importa, entonces se rechaza sin escape ni promoción parcial. Límites de expansión explícitos se fijan antes de implementación.
- [ ] [GWT] CA-38 — Dada colisión de IDs/rutas o import repetido/concurrente, cuando se valida, entonces no sobrescribe takes/manifiestos ni mezcla propietarios; política de deduplicación/remapeo explícita preserva procedencia original y no inventa inferencias del importador.
- [ ] [GWT] CA-39 — Dada canción portable, cuando se inspecciona, entonces no contiene secretos, credenciales, rutas personales absolutas, leases/PIDs o autoridad activa; las letras/fotos necesarias permanecen en payload privado autorizado, fuera de manifiestos/logs.
- [ ] [GWT] CA-40 — Dada biblioteca con commits en WAL y medios/referencias, cuando se crea backup, entonces produce corte coherente SQLite/assets con integridad/FK/FTS, hashes, versiones/locks y catálogo verificables; copia SQLite sola o VHDX activo no se declara backup de biblioteca.
- [ ] [GWT] CA-41 — Dado backup íntegro, cuando se restaura a destino propio nuevo, entonces reproduce biblioteca, búsqueda, maestro, letras/linaje/presets/assets y reproducción, sin reactivar jobs/leases históricos; revisa herramientas/modelos requeridos y distingue faltantes de pérdida de contenido.
- [ ] [GWT] CA-42 — Dado fallo/cancelación/disco lleno/corrupción durante backup o restore/activación, cuando se recupera, entonces conserva última copia íntegra y biblioteca anterior, no borra medios ajenos y permite rollback/reintento sin doble publicación.
- [ ] CA-43 — El ejercicio de recuperación de biblioteca real usa copia/cohorte autorizada y guardas before/after de originales: restaura en destino nuevo y prueba consulta, búsqueda y reproducción real. La activación posterior exige backup restaurable y ventana exclusiva; no basta biblioteca sintética ni borrar original para demostrar recovery.
- [ ] [GWT] CA-44 — Dado job M3 cancelado, acuse perdido o reinicio en cada frontera raw/post/rename/commit/render/import/backup, cuando se reconcilia, entonces conserva petición/autoridad y terminal durable, sin regenerar éxito, duplicar resultados ni servir paquetes parciales; UNKNOWN bloquea publicación/serving/limpieza.
- [ ] CA-45 — Integración Docker persistente acredita publicación no-clobber/CAS/replay sobre raíz ext4/UUID correcta, colisiones y restart; backend/montaje incorrecto aborta. Tmpfs y mocks no acreditan almacenamiento real.
- [ ] CA-46 — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos.
- [ ] [GWT] CA-47 — Dada instalación local sin Internet/claves externas con dependencias verificadas, cuando se realizan flujos M3, entonces no hay descarga runtime ni envío externo silencioso, progreso corresponde a eventos y errores/logs/manifiestos no revelan letra literal, fotos o secretos.
- [ ] CA-48 — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura.
- [ ] CA-49 — La aceptación registra por separado CPU/fixtures, E2E sintético, Docker/FFmpeg persistente, GPU real, experiencia de navegador/reproductor y escucha/revisión humana; ningún helper documental, porcentaje de cobertura o prueba aislada sustituye evidencia de producto pendiente.

## Pruebas

Esta spec define evidencia exigida; no presenta pruebas ejecutadas. El plan futuro enlazará cada CA con sus tests/matrices y el ledger canónico; se conservan los mismos IDs para GWT.

| Nivel | Qué acredita | Qué no acredita |
|---|---|---|
| Puro CPU / fixture versionado | Captura inmutable, validación, bindings históricos, codecs/esquemas, cálculos/mapas y negativos; paquetes temporales de prueba | Modelo, canto, stems útiles, alineación cantada, producto Docker o recuperación de biblioteca real. |
| E2E con mock identificado | Controles, estados, persistencia contractual, conflictos, cancel/retry y flujos visibles | Capacidad GPU, calidad audiovisual o generaciones reales. |
| Integración Docker/FFmpeg/ext4 | Bytes decodificados, metadatos, LUFS/true peak, render real, publicación y recuperación por fronteras, restauración consistente | Inferencia aprendida y juicio perceptual del propietario. |
| Integración GPU RTX5070 | Cada tarea real, pins/carga/mode/VRAM/RAM/unload, custodia, ComfyUI/ref y sincronización con análisis real | Calidad por nombre del modelo o superioridad sin escucha. |
| Experiencia real | UI con canción completa, seek/pausa/recarga, audio/vídeo en browser y reproductor independiente, import y restore útiles | Auditoría del corpus o comercialización habilitada. |
| Escucha y revisión humana | Stems/mezcla, F-19, calidad alta emparejada, letra cantada/alineación, diseño de portada y legibilidad N0 | No reemplaza mediciones, seguridad ni recuperación durable. |

Cada ejecución real registra entorno/digest/pins, material autorizado sin exponerlo, fuentes/resultado/hashes, parámetros solicitados y efectivos, método/umbrales, mediciones y limitaciones. Los fallos reales se distinguen de prerrequisitos pendientes. Un requisito no acreditado conserva gate abierto.

### Matriz de cobertura

| Función / restricción | CA | Evidencia indispensable |
|---|---|---|
| F-06 | 36–39, 44, 48 | Contratos/negativos + roundtrip real multiversión y reproducción; sin sobrescritura. |
| F-18 | 32–33, 46 | Benchmark modo real/recibos M0 + escucha emparejada; deshabilitación honesta. |
| F-19 | 04–05, 30–31, 46 | Upload/resolución/linaje + GPU y escucha de audio propio autorizado. |
| F-30 | 06–07, 46 | Assets y comparación por muestras + separador real y escucha. |
| F-31 | 08–10 | Web Audio real + mezcla exportada y contraste/escucha. |
| F-32 | 11–14, 48 | Docker/FFmpeg, lector independiente, medición final y ZIP real. |
| F-33 | 15–17 | Persistencia/método, audio real y contraste independiente por resultado. |
| F-34 | 18–21 | Binding single/composite y revisión + alineación real/anotación/escucha, LRC/SRT. |
| F-35 | 22–25 | Generación/edit ComfyUI real, selección/subida y revisión visual. |
| F-40 | 26, 28–29, 44 | N0 completo real, sincronía, LUFS, reproducción/legibilidad, rendimiento y recovery. |
| F-41 | 27–29 | Onda/espectro/partículas reales, silencio/seek y vídeo independiente. |
| F-44c | 04–05, 24, 26 | Contenido/consentimiento + portada/fondo N0 renderizado. |
| F-70 | 34–35, 36, 41 | Captura por uso, referencias/capacidades, historia después de edición/restauración. |
| F-85 | 40–43, 45 | SQLite WAL+assets, restore real/rollback y montaje persistente. |
| M2 / apertura técnica | 01, 49 | Cierre canónico previo y niveles de evidencia separados. |
| Pertenencia, linaje, master | 02, 06, 09, 18, 30, 32, 36–38, 48 | IDs/roles/hashes/padres múltiples y referencias históricas reales. |
| Derechos, privacidad y licencias | 04–05, 13, 23–24, 35, 39, 47–48 | Declaraciones, consentimiento, conjunción y no eco/secretos. |
| Cancelación/recovery/custodia | 14, 20, 37–45 | Inyección de fallos en fronteras y verificación de autoridad propia/UNKNOWN. |
| Hardware y capacidad honesta | 03, 25, 29, 31–33, 46–47 | Medición RTX5070/WSL y gates por capacidad, sin equivalencia mock. |

## Referencias

Las fuentes vigentes se contrastaron con las 27 entradas congeladas del descubrimiento antes de esta promoción. Los recibos privados conservan hashes y propuesta original; estos enlaces apuntan a la documentación del proyecto. Los localizadores por sección/ID mantienen su significado.

- [AGENTS.md](../../../AGENTS.md), §§2–6: plugin, ownership, entorno aislado y límites.
- [docs/CONSTITUTION.md](../../CONSTITUTION.md), §§1–4: producto, arquitectura, contratos, derechos y privacidad.
- [docs/roadmap/README.md](../README.md), secuencia de aceptación y apertura técnica.
- [docs/producto/funcionalidades.md](../../producto/funcionalidades.md), las 14 funciones de matriz.
- [docs/arquitectura/datos.md](../../arquitectura/datos.md), §§1–4, persistencia/CPU/publicación y snapshots.
- [docs/arquitectura/contrato-engines.md](../../arquitectura/contrato-engines.md), §§1, 4–8: descriptores, tareas, raw y sintético.
- [docs/arquitectura/convenciones.md](../../arquitectura/convenciones.md), §§1–6 y almacenamiento operativo: formatos, uploads, logs y recovery.
- [docs/arquitectura/pipeline-audio.md](../../arquitectura/pipeline-audio.md), §§1, 3–5 y procedencia CPU: métricas, destinos, herramientas y suma stems.
- [docs/arquitectura/modelos.md](../../arquitectura/modelos.md), §§1, 3–6: candidatos históricos, calidad pendiente, separadores y VRAM.
- [docs/arquitectura/sistema.md](../../arquitectura/sistema.md), §§3–7: cola, server y futuras rutas; no capacidades acreditadas.
- [docs/arquitectura/iteracion-creativa.md](../../arquitectura/iteracion-creativa.md), captura, padres, proyección y alcance de pruebas.
- [docs/legal/licencias.md](../../legal/licencias.md), producción, imagen, análisis y herramientas; [docs/legal/comercializacion.md](../../legal/comercializacion.md), gate GC.
- [models/models.lock.json](../../../models/models.lock.json), modelos/componentes y revisiones; [tools/tools.lock.json](../../../tools/tools.lock.json), herramientas fijadas. No se abrieron pesos ni se descargó nada.
- [docs/roadmap/2026-10-10-m2-iteracion-creativa/spec.md](../2026-10-10-m2-iteracion-creativa/spec.md), CA-01/20/21/29 y alcance.
- [docs/roadmap/2026-10-10-m2-iteracion-creativa/design.md](../2026-10-10-m2-iteracion-creativa/design.md), arquitectura O2, recetas/autoridad y aceptación.
- [docs/roadmap/2026-10-10-m2-iteracion-creativa/cpu-contract-design.md](../2026-10-10-m2-iteracion-creativa/cpu-contract-design.md), O1 y compatibilidad.
- [docs/roadmap/2026-10-10-m2-iteracion-creativa/recipe-contract-design.md](../2026-10-10-m2-iteracion-creativa/recipe-contract-design.md), envelope exclusivo y ocho operaciones.
- [docs/roadmap/2026-10-10-m2-iteracion-creativa/tasks.md](../2026-10-10-m2-iteracion-creativa/tasks.md), T01/T02 completadas con alcance acotado; T03 en progreso.
- [docs/decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md](../../decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md), despliegue y convivencia.
- [docs/decisiones/ADR-0037-avance-tecnico-condicionado.md](../../decisiones/ADR-0037-avance-tecnico-condicionado.md), apertura separada de aceptación real.
- [docs/decisiones/ADR-0041-esquema-inicial-y-snapshots-del-server.md](../../decisiones/ADR-0041-esquema-inicial-y-snapshots-del-server.md), entidades, DAG y backup BD acotado.
- [docs/decisiones/ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md](../../decisiones/ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md), persistencia, quiesce y restore.
- [docs/decisiones/ADR-0073-recetas-privadas-y-escucha-ab-de-iteracion-creativa.md](../../decisiones/ADR-0073-recetas-privadas-y-escucha-ab-de-iteracion-creativa.md), autoridad y escucha.
- [docs/decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md](../../decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md), CPU sin identidad ficticia y formatos/API.
- [docs/decisiones/ADR-0077-envelope-privado-de-recetas-creativas.md](../../decisiones/ADR-0077-envelope-privado-de-recetas-creativas.md), contratos privados y fronteras puras.
- Plantilla exacta evaluator `templates/spec.md` indicada por `release-root.receipt.json`; comentarios guía y placeholders retirados.

## Decisiones confirmadas (ratificación de ROOT bajo delegación · 2026-10-11)

El propietario autorizó implementar todo el roadmap y delegó la elección entre alternativas. ROOT ratifica los requisitos tras contrastar el alcance íntegro y sus restricciones con las fuentes vigentes. Esta ratificación aprueba qué debe entregar M3; no atribuye una revisión humana específica del documento ni acredita capacidades, código, calidad audiovisual o cierre del hito. Arquitectura y plan son los siguientes pasos; evaluación económica n/a por ADR-0001.

## Supuestos

- S-01 — Se conserva el alcance publicado de 14 funcionalidades y el gate M2 cerrado. Se verificará contra canon fresco antes de promoción y antes de integración; no se presume cierre por esta lectura congelada.
- S-02 — Las piezas M1/M2 que se reutilizarán cumplirán sus propios gates; actualmente la captura pura no demuestra su integración durable. Los contratos de dependencia se revalidarán en arquitectura.
- S-03 — El catálogo/locks sólo declaran candidatos, revisiones y hashes; no demuestran instalación, licencia actualizada, compatibilidad CUDA, calidad o encaje. Toda habilitación exige su evidencia real.
- S-04 — No se usa material privado real en este descubrimiento. Las pruebas posteriores necesitarán cohortes autorizadas, sin trasladarlas a repositorio público ni informes literales.

### Incógnitas explícitas

| ID | Incógnita exacta | Resolución exigida y por qué no impide formular requisitos |
|---|---|---|
| I-01 | Capacidades reales ganadoras M0 para stems, F-19 y alta calidad; pasos/modo/checkpoint, licencias efectivas y margen en5070 | Benchmark/conformidad/escucha antes de habilitar. El resultado requerido queda definido sin fingir selección o recortar alcance. |
| I-02 | Modelos/workflows/nodos ComfyUI definitivos y pins/hash/licencias; soporte de edición por referencia y encaje CUDA | Arquitectura e integración real antes de adoptar. Generación múltiple/edit/ref y seguridad son requisitos independientes de la elección. |
| I-03 | Tolerancias LUFS por destino, fórmula de error suma stems, umbrales por método de análisis/alineación, confianza y política de revisión | Fijar métricas/cohorte/umbrales antes de RED/aceptación, con ROOT y escucha humana. Los objetivos publicados y fallos honestos se conservan; no se inventa precisión alcanzada. |
| I-04 | Perfiles codec/resolución/fps/fonts/render N0, tolerancias de sincronía/deriva y objetivo concreto de minutos sobre duración representativa | Diseño/licencias y medición real antes de aceptar. Render sincronizado/legible/reactivo sigue obligatorio sin atribuir rendimiento inexistente. |
| I-05 | Contratos privados M3 de mezcla/alineación/export/render/preset y cierre portable, versiones aplicables, política exacta de colisiones/remapeo y límites ZIP | Arquitectura code-first y ADR si cambia decisiones, antes de implementar. Se fija aquí integridad, historia, privacidad y rechazo seguro, no schemas nuevos. |
| I-06 | Integración durable/composición/autoridad M2, DTOv2 mixto, resolver de fuentes y publicador/recovery disponibles tras T03 y tareas siguientes | Relectura de seams liberados y evidencia canónica; no se modifica namespace concurrente. Dependencias explícitas permiten definir M3 sin aprobar esas piezas. |
| I-07 | Provisión ext4 persistente y mecanismo de corte coherente SQLite/assets, activación/rollback de restore y política backup/retención de biblioteca | Diseñar y probar sobre backend real, conservar backup BD diario14d existente sin confundirlo con biblioteca. Consistencia/restaurabilidad están especificadas aunque mecanismo quede pendiente. |
| I-08 | Cohorte privada representativa para canto castellano, tarareo/maqueta/voz, stems, imágenes, canciones multiversión y biblioteca real; anotaciones y acceso humano | ROOT coordina autorización/material y escucha en la ventana de pruebas. No requiere usar datos reales para redactar criterios. |

Estas incógnitas condicionan diseño/habilitación/aceptación, no autorizan eliminar una funcionalidad ni declarar conformidad con CPU/mock. ROOT resolverá las concreciones mediante arquitectura antes de planner/implementación. No se pasa a evaluator económico por ADR-0001.


Ratificación de requisitos: ROOT 2026-10-11T13:51:27.703097+00:00. Se conservan 49 criterios futuros sin marcar, 14 funciones y ocho incógnitas; no se reduce el alcance para facilitar tests. La aceptación final depende de M2 cerrado y de las evidencias reales de cada criterio.


## Aprobación y adopción ROOT del plan — 2026-10-11T16:16:11.792117+00:00

El propietario delegó la implementación de todo el roadmap y la elección entre alternativas. ROOT aprueba e incorpora este plan tras revisión2 fresca A/B sin gaps y QA documental563/563. Se han verificado107payloads,50fuentes,20enlaces; ledger/coverage-check/qa-gateoficialesexit0.42tareas/11fases/49CA14funciones/34E2E15manuales permanecen íntegros. No tareas M3cerradas ni producto probado. Consumo realnull. M2actual3/30(T03purocerrado),heredados ycalidad/humano/M2hito siguenpendientes; dependencias técnicas se liberanporunidad yfinalM3requiereM2cerrado. Originales privados/revisiones/QA intactos.
