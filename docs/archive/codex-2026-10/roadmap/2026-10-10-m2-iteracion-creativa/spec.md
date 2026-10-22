---
spec: m2-iteracion-creativa
descripcion: Iterar sobre takes sin sobrescribir y preparar letras y estilo con asistencia local.
estado: aprobada
creado: 2026-10-10
actualizado: 2026-10-10
evaluacion: n/a (proyecto personal; ADR-0001)
design: design.md
plan: improvement-plan.md
depende-de: m1-mvp-estudio
generacion:
  artefacto: docs/roadmap/2026-10-10-m2-iteracion-creativa/spec.md
  inicio: '2026-10-10T18:12:29Z'
  fin: '2026-10-10T18:14:54Z'
  fuente: estimado
  tokens_reales: { entrada: 14000, salida: 6000, cache_creacion: 0, cache_lectura: 0 }
  eur: null
  horas_ia: 0.066667
  duracion: 4m
  duracion_reloj: 2m
  ratio_usado: 300000
  ratio_origen: default no calibrado (300000)
  nota: Estimación a juicio de entrada/salida; horas derivadas de 20000 tokens estimados. No son tokens medidos.
  avisos:
    - 'usage-meter: ventana sin respuestas del modelo (¿start y close seguidos?)'
    - El meter devolvió tokens_reales y horas_ia null; se completan a juicio, fuente estimado. Coste EUR desconocido.
---

# Spec · M2 — Iteración creativa

> **Estado:** aprobada por el orquestador bajo la delegación del propietario de implementar todo el roadmap y elegir las mejores alternativas. No atribuye aprobación específica de este documento al propietario.
> **Evaluación:** n/a por ADR-0001. **Plan de implementación:** [improvement-plan.md](improvement-plan.md), borrador completo; aprobación formal por el orquestador pendiente.
> **Diseño:** [design.md](design.md), O2 aprobada por el orquestador bajo delegación explícita del propietario el 2026-10-10; mantiene todos los criterios y gates reales.
> **Terminología:** cover significa reinterpretación musical de un take; portada significa imagen y pertenece a M3.

## Contexto y objetivo

El propietario necesita mejorar una canción existente sin perder sus versiones anteriores. M2 añade asistencia para letra y estilo y las operaciones creativas del catálogo vigente.

El alcance procede de [funcionalidades.md](../../producto/funcionalidades.md), F-16, F-17, F-20 a F-26 y F-86. La interacción procede de [ux.md](../../producto/ux.md), §§4.1, 4.4, 5–7.

[ADR-0037](../../decisiones/ADR-0037-avance-tecnico-condicionado.md) permite definir y construir unidades independientes contra contratos y mock. Requiere spec y plan aprobados antes de implementar. El plan está creado en borrador; su aprobación formal por el orquestador debe preceder a la implementación.

La aceptación final conserva M1 cerrado y al menos 30 generaciones musicales propias de uso real. El mock no cuenta. Conserva M0/T-13, elección mediante escucha humana, capacidades reales verificadas y los demás gates de M1.

### Usuarios y actores

| Actor | Responsabilidad |
|---|---|
| Propietario local | Describe, revisa letras, elige takes, declara derechos y acepta la calidad por escucha. |
| Web Next.js | Presenta controles, propuestas editables, árbol de versiones y comparación. |
| Server FastAPI | Valida, encola, publica artefactos y escribe SQLite, linaje y manifiestos. |
| Engine musical | Ejecuta tareas verificadas y entrega audio crudo privado. |
| Adaptador LLM Docker | Traduce `text.generate` hacia el Ollama local compartido en WSL2. |
| Proveedor externo opcional | Atiende una función expresamente activada; jamás genera música. |

## Decisiones de diseño

Las elecciones siguientes aplican fuentes vigentes. No constituyen una selección nueva de modelo o proveedor.

| Decisión | Elección | Motivo |
|---|---|---|
| Contenido raíz | `song`; letra versionada y takes hijos | Constitución §§1.2–1.3 y datos §1. |
| Capacidad musical | Resolver `music.retake`, `music.extend`, `music.repaint`, `music.cover` por descriptor verificado | Constitución §1.4 y contrato §4. |
| Asistencia de texto | Local por defecto mediante `engine-llm` Docker y Ollama WSL2 | ADR-0035 sustituye el backend propio de llama.cpp. |
| Edición sin IA | Worker CPU del server y FFmpeg fijado | F-24 y responsabilidad del server; no cargar un modelo GPU. |
| Proveedores externos | Ajustes por función, apagados de fábrica; claves solo en `.env` del server | ADR-0014 y datos §1.1. |
| Secuenciación | Apertura técnica separada de aceptación musical final | ADR-0037; ningún mock acredita uso real. |
| Evolución contractual | Code-first, engine `/v1` compatible, API server v2 aditiva y migraciones con excepción CPU delimitada ADR-0074 | Constitución §2 y convenciones §3. |

## Configuración / parámetros

| Parámetro | Clave / mecanismo | Default | Valor objetivo |
|---|---|---|---|
| Tarea y subcapacidad | `tasks`, `features`, `verified`, `params_schema` | Deshabilitada cuando no está verificada | Mostrar y validar solo parámetros admitidos. |
| Región musical | `[t0,t1]`, segundos finitos | Sin selección implícita | `0 <= t0 < t1 <= duration_s`. |
| Punto de extensión | Tiempo dentro del take, segundos | Final o punto elegido explícitamente | Validar contra duración y límites del descriptor. |
| Fidelidad del cover | Esquema declarado por la tarea | Sin escala inventada | Control disponible únicamente si la feature está verificada. |
| Recorte, fades y crossfade | Tiempos en segundos | Operación elegida por el usuario | Intervalos y duraciones compatibles con entradas reales. |
| Proveedor | `provider.function`, `enabled`, `config` | Externo desactivado | Activación independiente por función; configuración sin secretos. |
| Clave externa | `STUDIO_PROVIDER_<NOMBRE>_API_KEY` | Ausente | Solo server; nunca DTO, URL, BD, log o manifiesto. |
| Cola | Carriles `gpu`, `cpu`, `remote` | GPU 1, CPU 2; remote apagado | Sin segundo modelo residente en VRAM. |

## Arquitectura y componentes

M2 reutiliza `apps/web`, `apps/server`, los contratos de `packages/contracts` y la cola SQLite de M1. Reutiliza `song`, `take`, `lyrics_version`, `lineage_edge`, `asset`, `job`, `job_attempt`, `provider` y `setting`.

La web añade modo simple, acciones del asistente, selección de región, edición, árbol y comparador. El server resuelve IDs y pertenencia; no acepta rutas arbitrarias del navegador.

Los engines musicales permanecen en Docker con `/v1`, token interno y salidas crudas en `data/tmp/`. Solo el server escribe BD, publica assets, genera manifiestos y actualiza `song.json`. El server permanece sin torch.

El adaptador `engine-llm` corre en Docker y llama al Ollama compartido. No crea otro almacén de modelos ni servicio Ollama. La conectividad privada Docker→WSL2 exige validación real antes de aceptarla.

Las tareas de edición generan `derivation: edit`. Las musicales generan `variant`, `extend`, `repaint` o `cover`. El linaje conserva padres, `root_id` y `section_map` cuando corresponda. El crossfade declara ambos padres con sus roles.

El comparador aplica la igualación de loudness a la escucha. Conserva los masters y sus hashes. No incorpora análisis musical completo ni exportación por destinos de M3.

## Flujo (paso a paso)

1. El usuario abre una canción o prepara una descripción en modo simple.
2. El asistente propone letra y estilo; el usuario puede editarlos antes de cualquier generación musical.
3. El usuario confirma la letra aplicable y su declaración de autoría; el server guarda una versión sin modificar versiones históricas.
4. Para iterar, el usuario selecciona un take y una acción disponible. La región admite selección y bucle sobre la onda.
5. El server comprueba pertenencia, derechos, parámetros, capacidad verificada y recursos antes de encolar.
6. El engine entrega salida cruda o el worker CPU edita audio. La UI muestra eventos reales y errores persistentes.
7. El server publica un take hijo con assets y manifiesto inmutable. El padre y el maestro actual permanecen intactos.
8. El usuario navega el árbol, compara dos takes con loudness igualado y cambia el maestro solo mediante acción explícita.
9. En Ajustes, el usuario puede activar una alternativa externa disponible por función. La UI declara proveedor y coste antes del envío.

## Alcance

### Dentro (esta iteración)

| Funcionalidad | Resultado exigido |
|---|---|
| F-16 · Modo simple | Descripción, idioma, instrumental y duración; propuestas de letra y estilo editables antes de generar. |
| F-17 · Asistente | Generar letra, reescribir sección, continuar, cambiar tono y sugerir estructura; etiquetas válidas. |
| F-20 · Variación | Repetir petición con nueva semilla o variar un take mediante `music.retake`, según capacidad verificada. |
| F-21 · Extender | Continuar desde final o punto elegido, con letra y estilo para la continuación. |
| F-22 · Regenerar sección | Seleccionar `[t0,t1]` en la onda, preescuchar en bucle y solicitar regeneración con letra/estilo opcionales. |
| F-23 · Cover | Reinterpretar un take de la canción con otro estilo; fidelidad según feature verificada. |
| F-24 · Editar audio | Recortar, fundidos y crossfade sin IA, con linaje y nuevo take. |
| F-25 · Árbol de versiones | Navegación entre originales, variantes, extensiones, regeneraciones, covers y ediciones. |
| F-26 · Comparador A/B | Comparar dos takes de la canción con loudness igualado sin alterar archivos maestros. |
| F-86 · Proveedores | Activar/desactivar alternativas por función, estado de clave y coste; sin elegir hoy un proveedor no documentado. |

La conexión LLM, cancelación, eventos, descarga y convivencia real con Ollama forman parte de M2 por ADR-0035. Las APIs externas de texto son opcionales para F-17. Una integración externa ausente o no verificada queda deshabilitada con motivo.

### Fuera (siguientes specs)

- Portadas, imágenes, vídeo con letra, personajes y videoclip: M3/M4. F-86 no habilita sus generadores por adelantado.
- Subir audio propio como referencia o añadir acompañamiento (F-19), XL/calidad alta (F-18), stems y mezclador: M3.
- Análisis completo, alineación de letra, exportación por destinos, presets, importación de proyecto y backup de biblioteca: M3.
- LoRA, referencia de timbre y segundo motor musical: M5.
- Clonación de voces reales, acceso LAN, multiusuario y comercialización.
- Seleccionar automáticamente otro motor, declarar capacidades verificadas por transportar parámetros o sustituir música local por una API.

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| Task o feature no verificada | UI deshabilitada con motivo; API rechaza `CAPABILITY_UNAVAILABLE` sin encolar. |
| Región, fade, punto o fidelidad inválidos | Error de validación sobre el campo; ningún archivo ni take padre cambia. |
| Letra sin autoría | `LYRICS_DECLARATION_REQUIRED`; no se encola música vocal. Instrumental conserva su excepción. |
| Entrada sin derechos | `RIGHTS_DECLARATION_REQUIRED`; no se encola ni se transmite al proveedor. |
| Take ajeno, borrado o no listo | Rechazo conforme a API vigente; no se expone ruta privada ni se crea un hijo listo. |
| LLM devuelve tags inválidos o falla | Error visible; preservar texto previo y permitir revisión. No generar música automáticamente. |
| Conflicto de edición concurrente | `409 CONFLICT` según `rev`/`If-Match`; conservar versión histórica y no pisar cambios. |
| Ollama inaccesible o GPU ocupada por terceros | Espera o error observable; no cloud silencioso ni gestión destructiva del servicio compartido. |
| Cancelación o reinicio | Estados y recuperación de M1; sin publicación parcial como `ready`, ni terminal duplicado, ni nueva generación de un hijo ya publicado. |
| Proveedor apagado, clave ausente o coste desconocido | No enviar solicitud externa; explicar el requisito pendiente. |
| Fallo de post-proceso/publicación | Conservar origen y error; limpiar solo recursos propios y recuperar con las garantías durables de M1. |

## Criterios de aceptación

- [ ] CA-01 — Antes de aceptar M2, M1 está cerrado y existe evidencia de al menos 30 generaciones musicales propias de uso real. Ninguna generación mock entra en el recuento. M0/T-13 y aceptación humana siguen vigentes.
- [ ] [GWT] CA-02 — Dada una descripción en modo simple, cuando termina el asistente, entonces muestra letra y estilo editables. No se encola música hasta la acción explícita de generar.
- [ ] [GWT] CA-03 — Dado modo simple instrumental, cuando se genera, entonces usa `music.instrumental` sin exigir declaración de letra y conserva el texto previamente escrito.
- [ ] [GWT] CA-04 — Dada una letra existente, cuando se ejecuta cada acción de F-17, entonces propone el cambio solicitado con etiquetas válidas y conserva las versiones previas. Reescribir una sección conserva el resto.
- [ ] [GWT] CA-05 — Dada una propuesta del asistente aceptada, cuando se guarda, entonces crea `lyrics_version` con `source: assistant`, declaración aplicable y vínculo a su padre. El take registra la versión efectiva.
- [ ] [GWT] CA-06 — Dada música vocal sin declaración, cuando se solicita generar o derivar, entonces el server rechaza antes de encolar. La autoría figura en procedencia y manifiesto cuando se genera.
- [ ] [GWT] CA-07 — Dada una petición previa, cuando se solicita variación con otra semilla, entonces registra la semilla efectiva, el nuevo take `variant` y el origen sin sobrescribirlo. Los parámetros restantes conservan la petición elegida.
- [ ] [GWT] CA-08 — Dado un take listo y `music.retake` verificada, cuando se solicita variación del audio, entonces la entrada `source` corresponde a ese take y el hijo conserva su linaje.
- [ ] [GWT] CA-09 — Dado un take listo, cuando se extiende desde el final o desde un punto válido, entonces el hijo registra el punto, letra y estilo efectivos, `derivation: extend` y `section_map` de la construcción resultante.
- [ ] [GWT] CA-10 — Dada una onda con beats disponibles, cuando el usuario selecciona una región, entonces puede ajustar `[t0,t1]`, usar imán a beats y preescuchar en bucle. El imán a secciones solo aparece cuando existen límites reales.
- [ ] [GWT] CA-11 — Dada una región válida, cuando termina `music.repaint`, entonces crea un hijo `repaint` con selección, parámetros y mapa de partes conservadas/regeneradas. El padre permanece intacto.
- [ ] [GWT] CA-12 — Dado un take y `music.cover` verificada, cuando se reinterpreta, entonces el hijo `cover` registra estilo y origen. Un control de fidelidad solo aparece si su feature y esquema están verificados.
- [ ] [GWT] CA-13 — Dados intervalos vacíos, negativos, no finitos o fuera del audio, cuando se solicita extender, regenerar o editar, entonces UI y server rechazan sin encolar trabajo inválido.
- [ ] [GWT] CA-14 — Dado un take listo, cuando se recorta o se aplican fundidos, entonces el worker CPU produce un hijo `edit` con duración y envolvente correspondientes. No carga un modelo GPU ni altera el padre.
- [ ] [GWT] CA-15 — Dados dos takes listos de la misma canción, cuando se aplica crossfade válido, entonces crea un hijo `edit` con ambos padres, roles `crossfade_a`/`crossfade_b` y mapa temporal verificable.
- [ ] [GWT] CA-16 — Dados padre e hijo, cuando termina cualquier operación, entonces sus IDs y assets son diferentes, el hash del padre no cambia y `master_take_id` no cambia sin elección explícita.
- [ ] [GWT] CA-17 — Dada una canción con derivaciones y varios padres, cuando se abre el árbol, entonces muestra relaciones reales, operación y maestro. Seleccionar un nodo abre su audio y procedencia; recargar conserva el árbol.
- [ ] [GWT] CA-18 — Dados dos takes listos de una canción con distinto loudness medido, cuando se comparan A/B, entonces la escucha aplica igualación y permite alternarlos. Los masters y manifiestos conservan sus hashes.
- [ ] CA-19 — La prueba A/B usa audio controlado y medición de salida para comprobar igualación, ausencia de clipping y tratamiento explícito de silencio o medición ausente. El plan fija tolerancia y método antes del test; la escucha humana verifica utilidad.
- [ ] [GWT] CA-20 — Dada una tarea o feature real `verified: false`, cuando se intenta usar desde UI o API, entonces permanece deshabilitada y se rechaza sin envío. El mock identificado como sintético no habilita su equivalente real.
- [ ] CA-21 — Las cuatro operaciones musicales se verifican individualmente con audio real y escucha humana. Se registra continuidad en extensión/regeneración y fidelidad estilística del cover sin prometer obediencia perfecta. Una capacidad no verificada conserva su gate abierto; no se declara M2 completo.
- [ ] [GWT] CA-22 — Dado `text.generate`, cuando llegan deltas, cancelación o terminal, entonces UI y server conservan secuencias y un único terminal. Cancelar o desconectar no corrompe la letra histórica ni encola música automática.
- [ ] CA-23 — Compose despliega web/server/engines y el adaptador LLM. La prueba real acredita conexión privada Docker→Ollama WSL2, `text.generate` y cancelación, sin abrir puertos a la LAN ni descargar pesos durante runtime.
- [ ] CA-24 — La prueba real alterna LLM y motor musical sin dos modelos residentes. `unload` verifica ausencia y VRAM liberada; detecta ocupación ajena. Solo restaura modelos observados y descargados por esa operación, sin parar Ollama ni borrar modelos.
- [ ] [GWT] CA-25 — Dada una instalación sin clave ni Internet y con modelos locales verificados, cuando se usa M2, entonces letras y música usan el carril local. Un fallo local no activa un proveedor externo.
- [ ] [GWT] CA-26 — Dados Ajustes, cuando se activa/desactiva una alternativa disponible, entonces cambia solo su función. La UI muestra proveedor, estado de clave y coste previo; música no ofrece proveedor externo.
- [ ] [GWT] CA-27 — Dado un adapter externo explícitamente activado y verificado, cuando se confirma una solicitud, entonces el server usa `remote` y registra proveedor, modelo, `request_id` y coste en procedencia/manifiesto. Sin activación, clave o estimación fiable no envía.
- [ ] [GWT] CA-28 — Dadas respuestas, eventos, errores y logs de providers, cuando se inspeccionan, entonces ninguna clave aparece; `provider.config` tampoco contiene secretos. Browser y engines nunca reciben claves externas.
- [ ] CA-29 — Todo resultado publicado cumple su schema de manifiesto: inferencia conserva v1 y CPU autónomo, incluidas previews A/B, usa v2 con procedencia honesta conforme ADR-0074. Conserva derechos y `commercial_use` combinado de modelos, herramientas y entradas. Ningún manifiesto emitido se reescribe; cierre portable con CPU usa song v2 y lectores despachan v1/v2. La API server añade v2 preservando DTO/operaciones M1, sin ocultar CPU; engine `/v1` sigue compatible. Migraciones conservan biblioteca M1 y garantías históricas bajo la excepción SQL precisa, con backup/rollback/FK probados.
- [ ] [GWT] CA-30 — Dado un error, cancelación o reinicio durante una derivación, cuando se recupera la canción, entonces conserva padres y maestro, estados honestos y reintento según M1. Solo resultados íntegros se muestran como `ready`.
- [ ] CA-31 — E2E cubre cada flujo nuevo y su rechazo con mock identificado. UI en castellano vía `next-intl`, teclado, foco visible y anuncios de estado respetan UX §7; progreso solo procede de eventos reales.
- [ ] CA-32 — TDD, revisión adversarial, QA, cobertura cambiada mínima 80 %, contratos regenerados y verificaciones del ledger se acreditan antes del cierre. Pruebas CPU/mock y aceptación musical real quedan separadas.

## Pruebas

El futuro `test-plan.md` trazará cada CA a pruebas y evidencia. Los criterios GWT se traducen a casos reproducibles conservando sus IDs.

| Evidencia | Verifica | No acredita |
|---|---|---|
| Tests CPU y mock | Parámetros, permisos, versiones, linaje, errores, eventos y contratos | Capacidad del modelo o uso musical real. |
| Edición CPU con audio controlado | Recorte, fades, crossfade y comparación medidos | Calidad creativa de inferencia. |
| E2E Docker contra mock | Flujos, persistencia, UI y recuperación | GPU/Ollama y escucha humana. |
| Integración real LLM/VRAM | Red privada, `text.generate`, cancelación, descarga y convivencia | Elección musical de M0. |
| Inferencia y escucha musical | Cada operación con audio propio y juicio humano | No sustituible por métricas o mocks. |
| Registro de uso real | M1 cerrado y 30 generaciones propias identificables | No incluye salidas sintéticas ni solo ejecuciones de tests. |

Esta definición no ejecuta GPU, Ollama, Docker ni suites. La matriz activa M0/T-09 permanece intacta. Cualquier validación futura coordina recursos y fuentes selladas según ADR-0037.

## Referencias

- [Catálogo funcional](../../producto/funcionalidades.md), «Crear música», «Iterar sobre un take», «Sistema»: diez funcionalidades de M2.
- [Roadmap vigente](../README.md), M2 y «Apertura técnica y aceptación de hitos».
- [UX vigente](../../producto/ux.md), §§4.1, 4.4, 5–7. No existe `flujos-ux.md` en las fuentes consultadas.
- [Constitución](../../CONSTITUTION.md), producto, arquitectura, seguridad y derechos.
- [Contrato engines](../../arquitectura/contrato-engines.md), §§4–7: capacidades, tareas, eventos y mock.
- [Datos](../../arquitectura/datos.md), §§1.1–1.2 y manifiesto: versiones, linaje, mapas y proveedores.
- [Convenciones](../../arquitectura/convenciones.md), §§1–6: idioma, unidades, errores, secretos y logs.
- [Pipeline audio](../../arquitectura/pipeline-audio.md): preparación fiel, validación y publicación.
- [ADR-0014](../../decisiones/ADR-0014-local-por-defecto.md): alternativas externas apagadas y música siempre local.
- [ADR-0035](../../decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md): adaptador Docker y servicio compartido.
- [ADR-0037](../../decisiones/ADR-0037-avance-tecnico-condicionado.md): progreso técnico condicionado.
- [Spec M1](../2026-09-28-m1-mvp-estudio/spec.md): dependencias y aceptación previa.

## Decisiones confirmadas (fuentes vigentes · 2026-10-10)

Las decisiones citadas ya existen en Constitución y ADR. El orquestador revisó el alcance contra el catálogo vigente y aprobó los requisitos bajo la delegación recibida el 2026-10-10. No registra una aprobación específica nueva del usuario, un modelo elegido ni capacidades verificadas. Conserva los 32 criterios y los gates reales de M1, uso y escucha. Las incógnitas de implementación se resolverán en diseño/plan y verificaciones, sin aceptar M2 antes de sus gates.

Confluence y Jira están desactivados en el proyecto. Este artefacto permanece local; el orquestador registra la iniciativa en el índice compartido.

## Supuestos e incógnitas

| ID | Supuesto o incógnita | Cómo condiciona la aceptación |
|---|---|---|
| I-01 | M1 sigue abierto; no consta aquí evidencia de 30 generaciones propias en uso real. | No aceptar M2 hasta acreditar ambas condiciones. |
| I-02 | No se ha elegido ni verificado aquí un modelo local de letras, revisión, licencia, hash, etiquetas e idiomas. | Validar antes de habilitar F-16/F-17 reales; no reutilizar un nombre histórico como ganador. |
| I-03 | No consta soporte real completo de las cuatro operaciones musicales en el modelo finalmente elegido. | Batería real por task/feature; documentar límites y dejar controles deshabilitados hasta verificar. |
| I-04 | Esquemas exactos de continuación, región, fidelidad y variantes dependen del descriptor verificado. | El plan los extrae del contrato real sin inventar escalas ni máximos. |
| I-05 | La semántica efectiva de audio conservado y generado depende del adapter y post-proceso. | Fijar ensamblado y `section_map` antes de implementar; escuchar uniones y medir segmentos. |
| I-06 | F-26 no fija tolerancia LUFS, tratamiento de silencio ni punto temporal al alternar. | El plan propone política verificable y prueba ausencia de clipping antes de aceptar A/B. |
| I-07 | No se elige ahora ningún proveedor externo ni se conocen sus costes/términos. | F-86 configura adapters disponibles; ninguno se activa sin validación, licencia y coste fiable. API opcional no bloquea local. |
| I-08 | La red Docker→Ollama y coexistencia con clientes ajenos requieren prueba real. | No dar conexión o exclusión global por acreditadas mediante mock. |
| I-09 | Las secciones musicales completas pertenecen al análisis de M3. | M2 usa beats reales y selección manual; no inventa secciones. |
| I-10 | Se supone que M1 ofrece publicación durable, pertenencia y recuperación conforme a sus criterios. | Antes de integrar una unidad M2 comprobar esas dependencias; no reemplazarlas con fallback. |

No se fija presupuesto ni plazo en esta spec. El siguiente paso es diseño y handoff a `planner` por custom-agents, con evaluación económica n/a según ADR-0001.


La representación CPU de CA-29 se concreta en [cpu-contract-design.md](cpu-contract-design.md) y [ADR-0074](../../decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md), elegida por el orquestador bajo delegación. No reduce CA-32 ni los gates musicales/manuales y no declara compatibilidad implementada.
