---
id: ADR-0080
titulo: Producción por derivados tipados y escena N0 local
estado: aceptada
fecha: 2026-10-11
iniciativa: m3-produccion-portada-video-letra
design: ../roadmap/2026-10-11-m3-produccion-portada-video-letra/design.md
spec: ../roadmap/2026-10-11-m3-produccion-portada-video-letra/spec.md
autoridad: ROOT bajo delegación explícita del propietario; O1 elegida el2026-10-11T14:16:13.016842+00:00
destino_canonico: docs/decisiones/ADR-0080-produccion-por-derivados-tipados-y-escena-n0-local.md
adopcion_canonica: incorporada por ROOT tras revisión y QA documental
---

# ADR-0080: Producción por derivados tipados y escena N0 local

## Contexto

M3 exige stems, mezcla, análisis, letra sincronizada, portada, audio y vídeo N0. También exige presets, portabilidad y recuperación de biblioteca. La spec aprobada conserva14funciones y49criterios. M0/M1/M2 siguen abiertos en sus dependencias reales.

El server dispone de cola SQLite, entidades iniciales y mecanismos de publicación por toma. Sus contratos M1 exigen autoridad de inferencia; no representan automáticamente un export, render o upload CPU. Las recetas M2 tienen ocho operaciones cerradas. Ampliarlas por conveniencia duplicaría autoridad o cambiaría su significado.

El [diseño comparado](../roadmap/2026-10-11-m3-produccion-portada-video-letra/design.md) contrasta derivados tipados con un documento revisionado de producción y runner de sesión. ROOT eligió O1 bajo delegación después de comparar. No se atribuye lectura ni validación personal de estos documentos al propietario.

Los enlaces de este archivo se resuelven desde su destino canónico futuro. La copia privada y su evidencia permanecen fuera del canon hasta revisión, QA y adopción de ROOT.

## Decisión

El server coordina M3 mediante peticiones y resultados tipados sobre `job/job_dependency`, con un paquete de escena N0 compartido entre preview y render offline. No incorpora un agregado persistente de sesión de producción ni depende de la web viva para exportar.

### Autoridad y versiones de producción

Cada acción captura contexto inmutable: propietario, canción, fuentes/IDs/hashes, revisiones, letra histórica, derechos y parámetros efectivos. El namespace privado M3 es independiente de CreativeRequestV1. No añade operaciones a la versión1 de ADR-0077 ni reescribe jobs históricos.

Compositores cerrados expresan dependencias de stems, análisis, mezcla, export y N0. El server conserva la única autoridad SQLite y los carriles GPU1/CPU2. Un resultado acreditado puede reutilizarse por contexto/autoridad/hashes; un archivo presente o un hash aislado no acredita éxito.

Stems son assets del take. Mezcla y alineación conservan revisiones propias; una corrección temporal no modifica audio, letra histórica o evidencia anterior. La edición musical publicada como Take crea hijo con todos los antecedentes; el maestro sólo cambia por acción explícita.

Export, Render y Artwork conservan sus sujetos y autoridad real. CPU y upload no inventan engine, modelo, semilla o intento ganador. Los modelos de padres son antecedentes, no cómputo ejecutado por el derivado.

El plan debe concretar requests, planes, recibos, intenciones, revisiones SQL y contratos por sujeto. Sus implementaciones dependientes empiezan después de ratificar ese contrato. Esta decisión no fija todos sus campos ni amplía la excepción SQL de ADR-0074.

Manifest y Song v1/v2 históricos mantienen bytes y significado. El diseño de formatos M3 evaluará las extensiones realmente compatibles. Si un sujeto o ausencia no cabe, requiere formato discriminado y decisión delimitada, antes del RED dependiente. El timeline-v1 cerrado no admite palabras/bindings añadidos sin evolución contractual explícita.

### Escena N0 compartida y render del server

`video_project.timeline` y su revisión conservan la autoridad del montaje. Un plan derivado fija timeline_rev/hash, audio final, revisión temporal, portada, features, perfil, fonts y herramientas. No introduce otra fuente de verdad del montaje.

La escena recibe un tiempo explícito. La preview sigue el reloj de audio; el renderer usa índice de cuadro y fps racional. El seek reconstruye el estado correspondiente. Onda, espectro y partículas consumen features del audio efectivo, con ventanas/hop y eje temporal declarados. El silencio tiene respuesta medible.

El renderer ejecuta un bundle cerrado y local mediante un hijo headless propio, bajo custodia del server. Propone rasterización CPU, sin modelos residentes propios. Su pin, flags, licencia, recursos y proceso de cierre requieren concreción y conformidad. Disponer del browser de QA no habilita este renderer.

El server codifica/muxea mediante FFmpeg fijado, mide la salida final y publica. Los engines sólo entregan raw autorizado por `/v1`. El navegador del usuario no aporta paths ejecutables, scripts, filtros o workflows arbitrarios. El bundle no depende de disponibilidad o versión de la aplicación web viva.

La validación usa canciones completas del proyecto, incluida Libre4:15, con sus duraciones reales. Una cohorte3min o fixture corto no limita el producto ni satisface un criterio sobre canción completa. Perfiles, umbrales y objetivo de minutos se ratifican antes de la medición correspondiente; no se rebajan después de un fallo.

### Audio por destino y tratamiento explícito

La exportación mide entrada, aplica política ratificada, codifica y mide el archivo final decodificado. Streaming, broadcast/vídeo y podcast conservan objetivos−14/−23/−16LUFS y true peak≤−1dBTP con las tolerancias que se ratifiquen antes del RED dependiente.

La política inicial emplea ganancia constante y soxr. Si LUFS y techo no se alcanzan simultáneamente, el resultado conserva rechazo medido y no se presenta conforme. Un tratamiento dinámico adicional exige decisión y parámetros visibles antes del renderer/export dependiente. Nunca se aplica silenciosamente ni se atribuye calidad a sus comandos.

Original conserva bytes. ZIP stems conserva amplitud y alineación común según su perfil. Metadatos, letra histórica solicitada y portada requieren lectura independiente de los artefactos finales.

### Biblioteca portable y recuperación

Export/import conserva raíz, cierre necesario, versiones, linaje, maps, revisiones, derechos y bytes. La evidencia original permanece íntegra. Los materiales privados necesarios viajan en payload autorizado, sin claves, rutas personales ni autoridad de procesos restaurable.

El importador valida catálogo/rutas/cuotas/hashes/propiedad/DAG antes de promover. Usa staging propio e intenciones durables para el cierre completo. Colisión ajena rechaza; replay exige recibo propio. Remapeo explícito necesita contrato que preserve evidencia original y registre identidad local por separado; nunca reescribe un manifiesto histórico.

Backup de biblioteca usa mantenimiento exclusivo, corte SQLite nativo y catálogo/medios del mismo corte. Bloquea nuevas mutaciones y dispatch, drena custodia propia y suspende purga. UNKNOWN impide iniciar o finalizar efectos. La copia de medios ocurre sin writer abierto durante E/S.

Ese coordinador es trabajo pendiente; PublicationCoordinator actual no acredita el corte por sí solo. El plan debe concretar journal, recuperación y quiesce de todos los mutadores. El backup diario de BD14d continúa como operación distinta; no demuestra backup de biblioteca.

Restore valida biblioteca nueva en ext4 propio y prueba consulta, búsqueda y reproducción. No reactiva jobs/leases históricos ni confunde modelos faltantes con contenido perdido. La activación necesita backup restaurable, ventana exclusiva, binding coherente de raíz/BD e intención durable con rollback. Copiar VHDX activo no satisface este requisito.

### Capacidad real y alcance obligatorio

Stems, audio propio, calidad alta, métodos de análisis/alineación y Comfy generación/edición son capacidades que deben integrarse y verificarse. Cada una requiere pesos seguros, pins/licencias, conformidad y su evidencia real. Un nombre de modelo, fila histórica o prueba sintética no las habilita.

Se conserva un modelo residente y la medición de VRAM libre menos margen. Los engines propios descargan su proceso hijo; el turno Ollama restaura sólo residentes observados y descargados por esa intervención. No detiene el servicio ni borra modelos. La selección de O1 no aprueba un checkpoint, codec, browser, métrica o capacidad por defecto.

Todos los contratos, modelos, métricas, licencias y gates pendientes son trabajo que el plan debe representar. No es necesario tener producto terminado antes de planificar tareas de concreción. Ninguna dependencia abierta autoriza recortar14funciones/49criterios ni cerrar aceptación con fixtures.

## Alternativas descartadas

- **O2 — Documento revisionado y runner de sesión.** Ofrece producción conjunta por revisión, pero persiste otra autoridad y exige reconciliar documento, jobs, resultados y timeline. Su captura de ruta web condiciona export a disponibilidad/versión web. M3 puede añadir esa UX mediante compositores sin incorporar ahora ese agregado.
- **Ampliar CreativeRequestV1 o reutilizar PostPlan de inferencia con identidades ficticias.** Contradice ADR-0077/0074 y falsea CPU/upload. Se conserva namespace y autoridad específicos.
- **Animación de progreso o captura en tiempo real como prueba N0.** No acredita reactividad ni sincronización con el audio efectivo. Se emplea escena temporal explícita y validación de canción completa.
- **Backup SQLite aislado o copia del VHDX activo como recuperación de biblioteca.** No acredita coherencia SQLite/assets. Se conserva corte lógico y restore validado antes de activación.

## Consecuencias

O1 conserva scheduler, entidades y autoridad por resultado. Añade trabajo explícito para contratos de derivados, revisiones, escena compartida, renderer local y mantenimiento de biblioteca. Los históricos y sus lectores permanecen disponibles.

La implementación tendrá más handlers que un runner agregado. Compensa esa complejidad con recuperación por resultado y export independiente de la web viva. El baseline de backup exclusivo puede exigir una ventana larga; los pins durables para optimizar copia serían una decisión posterior.

M1 storage persistente y M2 composición/DTO/resolver/publicación siguen siendo dependencias reales. ADR-0037 permite unidades independientes con plan y gates documentados. La aceptación M3 exige cierre M2 y heredados, además de toda su evidencia musical/audiovisual y recuperación real.

El planner debe respetar O1 y representar las concreciones como dependencias previas al RED correspondiente. CPU/fixtures, E2E sintético, Docker/FFmpeg/ext4, GPU, experiencia browser/reproductor y escucha/revisión humana permanecen niveles separados.

Este ADR no autoriza nuevas reconstrucciones SQL, servicios de infraestructura, descargas runtime, ampliaciones incompatibles de `/v1` o cambios de autoridad de engines. Una decisión posterior que cambie esas reglas debe declararlo y actualizar sus documentos.

## Estado

`propuesta` — O1 elegida por ROOT bajo delegación el2026-10-11T14:16:13.016842+00:00. Revisión fresca, QA documental, numeración/índice/enlaces y adopción canónica pertenecen a ROOT y siguen pendientes. No se atribuye revisión personal al propietario ni aceptación M3.

El umbral ADR se cumple: cierra O2 y afecta cola, datos, render y recuperación. Esta copia privada no modifica `docs/decisiones`, spec, plan o ledger. El diseño original y el snapshot permanecen byteexactos.

Evidencia privada: [selección ROOT](../../.cache/dev-cycle/m3/production-design-options-20261011/selection-root.receipt.json), [brief segunda pasada](../../.cache/dev-cycle/m3/production-design-options-20261011/second-pass-brief.md) y [diseño comparado original](../../.cache/dev-cycle/m3/production-design-options-20261011/design.md). Original SHA256: c9d8f7382ebcc56343d9445206aaddb41cf23d3eaeba84ec2d689e3feb28c35d. Los enlaces privados se resuelven desde el destino canónico declarado.


## Incorporación documental de ROOT — 2026-10-11T15:01:22.398925+00:00

DecisiónO1 incorporada trasreview1A/BsinImportant/MinorA01corregido yQA175/175; ROOT88artefactos/48fuentes/39links verificados. Plan/contratosdeimplementación/capacidades/GPU/E2E/audio/escucha/aceptaciónM3pendientes. Las referencias a propuesta/adopciónpending en el cuerpo describen la preparación original; este acta fija el estado documental vigente.
