---
design: m2-iteracion-creativa
titulo: Iteración creativa con recetas privadas y publicación por toma
estado: aprobado
creado: 2026-10-10
actualizado: 2026-10-11
spec: spec.md
evaluacion: n/a (ADR-0001)
plan: improvement-plan.md
adr: ../../decisiones/ADR-0073-recetas-privadas-y-escucha-ab-de-iteracion-creativa.md
opcion_elegida: O2
validacion: orquestador bajo delegación explícita del propietario, 2026-10-10
generacion:
  artefacto: docs/roadmap/2026-10-10-m2-iteracion-creativa/design.md
  inicio: '2026-10-10T18:30:35Z'
  fin: '2026-10-10T18:32:55Z'
  fuente: estimado
  tokens_reales: null
  eur: null
  horas_ia: null
  duracion: null
  duracion_reloj: 2m
  ratio_usado: 300000
  ratio_origen: default no calibrado (300000)
  nota: El medidor cerró sin respuestas detectables; tokens, horas IA y coste permanecen desconocidos. Fuente estimado, sin presentar cifras inventadas como medición.
  avisos:
    - 'usage-meter: ventana sin respuestas del modelo; no acredita consumo real.'
---

# Diseño — M2: iteración creativa

> **Spec:** [spec.md](spec.md), aprobada por el orquestador bajo delegación del propietario. **Evaluación:** n/a por ADR-0001. **Plan:** [improvement-plan.md](improvement-plan.md), borrador pendiente de aprobación formal. **ADR:** [ADR-0073](../../decisiones/ADR-0073-recetas-privadas-y-escucha-ab-de-iteracion-creativa.md), aceptada por el orquestador bajo delegación el 2026-10-10 (implementación pendiente).

| Campo | Valor |
|---|---|
| Estado | `aprobado` |
| Opción elegida | `O2` — receta privada tipada y carriles existentes |
| Validación | Orquestador, 2026-10-10, bajo delegación explícita del propietario de elegir las mejores alternativas. No atribuye lectura ni elección personal de O2 al propietario. |

## 1. Contexto y restricciones

M2 incorpora F-16/F-17, F-20 a F-26 y F-86. La canción mantiene sus letras versionadas y takes históricos. Las operaciones producen hijos; el comparador solo modifica la escucha. Cover significa reinterpretación musical, no imagen de portada.

La inspección local es una muestra acotada, realizada el 2026-10-10. No acredita integración real ni calidad de modelos. [CONTINUE-HERE.md](../../../CONTINUE-HERE.md) mantiene M1 abierto, incluida la validación persistente ext4/VHDX y la escucha. El diseño conserva ese estado.

| Base existente | Evidencia y límite relevante para M2 |
|---|---|
| `apps/server/app/models/__init__.py` | Existen `LyricsVersion`, `Take`, `LineageEdge`, `Provider`, `Setting`, `Job` y `JobAttempt`. El take ya admite las derivaciones M2 y varios padres. |
| `apps/server/app/queue/chains.py` | Crea generación → `post.audio` → beats en transacción. Hoy restringe generación a `music.song`/`music.instrumental`; no implementa las derivaciones por admitirlas el esquema. |
| `apps/server/app/queue/resolver.py`, `inputs.py` | Resuelve descriptores, esquemas y referencias propias. Se reutiliza la comprobación de capacidades y pertenencia, sin aceptar paths del navegador. |
| `apps/server/app/worker/planning.py`, `contracts.py` | `compose_post_plan` exige terminal del intento ganador de un engine. `PostPlan` está cerrado a `post.audio`; una edición CPU no cabe fingiendo un intento musical. |
| `apps/server/app/worker/publications.py`, `execution.py` | Ofrecen captura de contexto, custodia, intención, publicación y reconciliación por toma. El plan comprobará su aceptación M1 antes de integrar M2. |
| `packages/audio-post/audio_post/pipeline.py` | `process_audio` conserva master PCM24 y normaliza `listen.mp3`. `measure_audio` mide LUFS y true peak. El MP3 puede llevar limitación: no sustituye al master para una comparación fiel. |
| `apps/web/components/PlayerContext.tsx`, `PlayerDock.tsx` | La alternancia existente selecciona otra variante y pausa. No acredita comparación con reloj común ni igualación A/B. |
| `apps/web/components/Waveform.tsx` | Importa RegionsPlugin y marca beats. La selección editable y el bucle regional todavía requieren implementación. |
| `apps/engines/acestep/descriptor.py`, `adapter.py` | Hay integración musical existente. Un parámetro interno `cover` no demuestra soporte público de `music.cover` ni de las otras operaciones M2. |
| `docker-compose.yml` | Existe despliegue web/server/mock y engines musicales/análisis. No existe aún `apps/engines/llm/`; su adaptador y red privada requieren construcción y prueba. |

**Restricciones que fijan las soluciones**

- Constitución §§1–2: música siempre local; el server es el único escritor SQLite y publicador. Ningún engine altera maestros, manifiestos o contenido de dominio.
- [ADR-0035](../../decisiones/ADR-0035-despliegue-docker-y-ollama-wsl.md): adaptador LLM Docker hacia Ollama WSL2 compartido. No se reabre llama.cpp propio ni otro Ollama.
- Constitución §2 y [ADR-0018](../../decisiones/ADR-0018-cola-de-jobs.md): cola SQLite `gpu` 1/`cpu` 2; `remote` opcional. No Kafka, Redis ni infraestructura nueva.
- Un único modelo residente en VRAM; observar, descargar y restaurar únicamente modelos cuya intervención pertenece a la operación. Nunca detener Ollama ni borrar modelos.
- `/v1` code-first solo crece con campos opcionales. Nuevas tareas se expresan en descriptores; declarar o transportar parámetros no vuelve `verified` una capacidad.
- El server continúa sin torch. FFmpeg y bibliotecas CPU existentes procesan el audio en el hijo bajo custodia del server.
- Referencias, pesos, código remoto y herramientas tienen revisión, hash y licencia. Los nuevos pesos y datos del estudio permanecen dentro del proyecto.
- Los manifiestos emitidos no se reescriben. `commercial_use` combina modelos, herramientas y entradas. Un edit sin inferencia registra herramientas reales, sin atribuirle un modelo ficticio.
- [ADR-0037](../../decisiones/ADR-0037-avance-tecnico-condicionado.md) permite unidades técnicas independientes tras plan aprobado. M2 no se acepta hasta M1 cerrado, 30 generaciones propias reales, M0/T-13 y escucha de cada operación.
- La matriz activa M0/T-09 y sus fuentes selladas permanecen intactas. Este diseño no ejecuta GPU, Ollama, Docker, descargas ni benchmarks.

## 2. Opciones (3)

### O1 — Ampliar cada flujo de M1 por separado

Cada acción posee validación, creación de jobs y ensamblado específicos. Los handlers reutilizan cola y publicador, pero cada operación construye su contexto de publicación. El asistente y los proveedores añaden handlers propios. El navegador aplica ganancias A/B a dos fuentes medidas, con un reloj de reproducción común.

No añade una entidad de recetas. Las peticiones guardan los parámetros de cada handler en `job.request`. Las pruebas deben demostrar coherencia entre handlers y medir la salida del navegador, incluido su remuestreo.

| Criterio | Valoración |
|---|---|
| Complejidad | Media: poca estructura nueva; cada handler asume su validación, linaje y recuperación. |
| Riesgo | Alto: diferencias entre operaciones; autoridad CPU duplicada; audio A/B depende del decoder y grafo del navegador. |
| Coste relativo | S: menor coste inicial frente a O2/O3; crece con nuevas operaciones y regresiones cruzadas. |
| Reversibilidad | Alta: handlers y player se pueden sustituir; conservar peticiones históricas exige lectores por operación. |

### O2 — Receta privada tipada por job y ejecución sobre los carriles existentes

El server compone una receta inmutable al confirmar la operación. La receta incluye referencias propias, hashes, letra efectiva, operación, intervalos y política de ensamblado. Se guarda como JSON privado versionado en `job.request`, con evidencia durable del contexto antes de ejecutar. No introduce otro scheduler ni un lenguaje de workflows arbitrarios.

Un conjunto cerrado de compositores transforma las recetas en las cadenas existentes. Los tipos distinguen generación musical, edición CPU y asistencia de texto. Reutilizan custodia, eventos, publicación y recuperación; cada tipo mantiene su autoridad propia. El LLM y los adapters externos conservan `/v1`/`EngineBackend` y el gate por capacidad.

El comparador pide previews CPU por par desde masters. La misma política de ganancia genera y mide ambas escuchas. Las previews son derivados temporales privados, identificados por hashes y versión de política; no son nuevos takes ni modifican manifiestos históricos.

| Criterio | Valoración |
|---|---|
| Complejidad | Media-alta: contrato privado, compositores acotados y autoridad CPU diferenciada; conserva infraestructura y dominio existentes. |
| Riesgo | Medio: cambios en las fronteras del publicador y limpieza de previews; recetas cerradas y pruebas de replay reducen divergencias. |
| Coste relativo | M: más contrato inicial y render A/B que O1; menos entidad, editor y migraciones que O3. |
| Reversibilidad | Alta: versión privada de receta y lectores compatibles; datos canónicos siguen en song/take/linaje y assets. |

### O3 — Proyecto de edición con recetas reutilizables y grafo persistente

Añade entidades SQLite aditivas para sesiones de edición, versiones de receta y nodos de operación. El usuario puede guardar una composición sin renderizar y aplicarla a varios takes. Un compilador traduce el grafo a `job`/`job_dependency`; esos jobs siguen siendo la única cola. El asistente y las previews cuelgan de la sesión.

Esta opción preserva song como raíz y los engines sin estado. Introduce dos historias relacionadas: versiones de receta y takes publicados. Exige reglas de reconciliación entre ambas y una UI de borradores que la spec no solicita.

| Criterio | Valoración |
|---|---|
| Complejidad | Alta: nuevas relaciones, compilador del grafo, historial de sesiones y consultas/UI adicionales. |
| Riesgo | Alto: doble representación de construcción y más ventanas de recuperación; posible ampliación funcional fuera de M2. |
| Coste relativo | L: mayor que O1/O2 por persistencia y UX de recetas reutilizables. |
| Reversibilidad | Media: eliminar la UX es posible; recetas publicadas y dependencias históricas requieren conservar schema y lectores. |

## 3. Criterios de decisión

1. **Autoridad y recuperación antes que ahorro inicial.** Un hijo listo debe acreditar origen, contexto, hashes y publicación sin alterar sus padres.
2. **Fidelidad medible.** `section_map` describe la construcción efectiva. A/B compara masters mediante ganancias controladas, sin esconder un limitador distinto por toma.
3. **Reutilizar piezas vigentes.** Cola, custodia, permisos, events y Publisher preceden a nuevos almacenes o schedulers. La ampliación debe ser compatible con M1.
4. **Aislar incertidumbre real.** El código CPU/mock avanza sin habilitar tareas musicales o modelos LLM no verificados. Modelos y providers continúan deshabilitados hasta su evidencia.
5. **Mantener el alcance del catálogo.** M2 necesita confirmar operaciones y revisar propuestas; no requiere un editor de grafos reutilizables.
6. **Facilitar replay.** Peticiones privadas versionadas conservan parámetros efectivos y contexto. Cambiar una política posterior no cambia hijos ni manifiestos anteriores.

## 4. Recomendación · opción elegida y por qué

**Recomendación del arquitecto: O2.** El contrato privado permite compartir validación y replay sin crear otro dominio de edición. Reutiliza el publicador, pero reconoce que CPU y engine tienen autoridades diferentes. Las previews por par permiten medir exactamente la señal comparada.

**Opción elegida: O2, por el orquestador el 2026-10-10 bajo delegación explícita del propietario.** La receta tipada satisface autoridad, recuperación y replay. Reutiliza las piezas vigentes y conserva las pruebas reales pendientes. La aprobación del diseño no declara implementadas ni aceptadas las funcionalidades.

O1 se descarta por duplicación de autoridad y variabilidad del audio en navegador. O3 se descarta por añadir un historial de recetas que M2 no exige. El orquestador decide ambas exclusiones bajo delegación; no se atribuyen al propietario personalmente.

### Construcción propuesta para O2

| Frontera | Responsabilidad y evidencia que conserva |
|---|---|
| Confirmación | Resolver IDs, pertenencia, estado `ready`, derechos y descriptor verificado. Validar números finitos y región contra duración real. Guardar receta y nuevos jobs/takes/aristas en transacción. |
| Variación de petición | Recuperar petición efectiva elegida y su letra histórica; nueva semilla explícita. No reconstruirla desde los campos actuales de song. El hijo es `variant`. |
| Variación desde audio | Enviar master del take elegido como `source` a `music.retake`. No sustituirla por repetición de semilla. |
| Extender/regenerar | Declarar si el adapter devuelve toda la pieza o solo una región. El compositor verifica esa forma antes de ensamblar; nunca duplica partes suponiendo ambas cosas. |
| Cover | Generar desde `source` y estilo efectivo. Parámetros y fidelidad proceden del descriptor verificado. No inferir soporte público por la rama interna de ACE-Step. |
| Edición CPU | Recorte y envolventes explícitas; crossfade con padres `crossfade_a`/`crossfade_b`, dos mapas ligados a sus aristas y raíz canónica según ADR-0041. El hijo registra `derivation: edit`. |
| Publicación | Engine: terminal ganador capturado. CPU: ejecución propia, receta/hashes/pins y cierre de custodia. Ambas pasan por intención CAS, no-clobber, manifiesto y confirmación M1. |
| Árbol | Consultar aristas reales, incluidos varios padres. No representar crossfade como árbol de padre único. El endpoint de marcar maestro sigue siendo la única promoción explícita. |
| Texto | Job `text.generate` interactivo; deltas son borrador. El terminal validado ofrece propuesta; aceptar crea LyricsVersion con padre y `source: assistant`. No genera música automáticamente. |
| Remote | Adapter dentro del server para una función autorizada. Enabled, clave y estimación fiable son condiciones de envío; nunca fallback ante fallo local, nunca música externa. |

**Receta y autoridad CPU.** `PostPlan` actual no acepta un origen CPU; no se rellenarán campos engine con identidades inventadas. La ampliación privada tendrá variantes tipadas o un plan CPU separado que comparta la fase final del Publisher. ADR-0074 y cpu-contract-design.md concretan O1: origen discriminado, API/formatos v2 y excepción SQL limitada a tres tablas; implementación y compatibilidad se prueban antes de integrar. Los planes privados históricos y recibos de M1 conservan su lector y significado.

La autoridad CPU procede del server: propietario, canción, job, execution_id, take destino, receta versionada y su hash, padres/assets/hashes, derechos, herramientas/pins y resultado terminal propio. Exige revalidación del contexto, CAS vigente y cierre comprobado del hijo. No posee `winning_attempt_id` de engine ni infiere confianza por archivos presentes. El job y su ejecución se reconcilian conforme a custodia M1; un estado UNKNOWN bloquea publicación y limpieza.

La procedencia efectiva del edit declara cómputo CPU y herramientas; no declara un modelo ni semilla ejecutados. Los modelos y semillas de padres son antecedentes identificados, no inferencia del edit. El plan debe resolver los campos actuales obligatorios de Take sin inventar identidades ni falsear esos antecedentes. No integra ediciones mientras esa representación y su compatibilidad no estén aprobadas y probadas.

La receta sellada conserva intenciones temporales, antecedentes y reglas de muestreo. Los intervalos solicitados se expresan en segundos. El plan de construcción resuelve índices de muestra una sola vez. La autoridad y el recibo de ejecución conservan mapas efectivos y duración medida, ligados al hash de la receta. El paquete/manifiesto y las aristas de linaje finales reflejan esos resultados en su fase de publicación. No se reescriben la receta sellada ni los manifiestos emitidos, conforme a Constitución §2. Un `keep` pretende conservar la región; su fidelidad exige comparación medida con tolerancia fijada antes del test. PCM24, redondeo o conversión no acreditan identidad de muestras. Un fade declara su envolvente. Cambiar sample rate o canales no se oculta bajo `keep`.

Para crossfade se propone una envolvente lineal complementaria por defecto, con duración positiva limitada a ambas entradas. El plan fija cómo adaptar formatos distintos mediante FFmpeg/soxr fijado. La envolvente no prueba ausencia de clipping: se mide la salida, incluido true peak tras conversión. Rechaza resultados inválidos o clipping sin modificar al padre. No se inventa una escala de fidelidad musical ni se aplica crossfade automático a uniones del modelo.

**A/B propuesto, pendiente de prueba.** Medir `L_i` LUFS y `P_i` dBTP sobre cada master con la herramienta fijada. Para techo `C = -1 dBTP`, elegir un objetivo común `T = min(L_A, L_B, L_A + C - P_A, L_B + C - P_B)`. Aplicar `g_i = T - L_i`: solo atenuación y ninguna limitación dinámica.

Las previews usan un formato sin pérdida compatible con el navegador, cuya selección fija el plan tras prueba de decoder. Se remuestrean solo si hace falta y se miden después del render. Si cambia true peak por conversión, bajar el objetivo común y repetir con límite acotado; si no cumple, comparación no disponible con motivo. No reutilizar las escuchas MP3 normalizadas y limitadas como masters del comparador.

Se propone diferencia final A/B ≤0,5 LU y true peak ≤−1 dBTP, con valores medidos sobre el audio servido. Es una política propuesta, no evidencia de audio ya ejecutada. El plan fija método, clips controlados y tolerancia antes del RED. Audio silencioso, demasiado corto o sin medición finita no admite igualación automática; conserva escucha ordinaria con aviso.

La alternancia conserva tiempo absoluto dentro de ambas duraciones y una ventana común. Al llegar al final común se detiene la comparación; fuera de ella no promete equivalencia temporal. Dos elementos de audio precargados comparten estado de transporte y selección; solo uno es audible. El plan verificará clicks, pausas, latencia y drift antes de fijar tolerancias. No se afirma alineación musical entre covers o versiones de diferente estructura.

Las previews viven en temporales del server dentro de `data/`, con propietario, hashes de origen y política. Antes de servirlas, el server emite un manifiesto v2 CPU propio e inmutable, con sujeto job autorizado y recibo/contexto privado; no inserta asset job ni Take ficticia y linaje de edición. El plan verifica ese sujeto y las herramientas reales; no inventa un modelo de inferencia. Su limpieza exige ausencia de lectores/custodia propia; un resultado parcial nunca se sirve. No se registran como take maestro ni se insertan retroactivamente en su manifiesto. El cambio de hash, derechos, borrado o pertenencia invalida acceso y caché.

**LLM local y residencia compartida.** El nuevo adaptador implementa `/v1` hacia Ollama; reutiliza autenticación, secuencias y terminal único de la factoría común cuando encajen. Su runtime de residencia será específico: `ProcessSupervisor.unload` no prueba descarga de un modelo que posee un servicio ajeno. El adaptador no crea contexto CUDA ni un segundo servidor de inferencia.

El server coordina también turnos musicales cuando Ollama contiene modelos ajenos al estudio. Un coordinador de residencia observa nombres/revisiones y VRAM, registra una intervención privada antes de descargar y vuelve a comprobar antes de cargar. No se limita a mirar `Dispatcher.resident`, que hoy solo representa residentes propios. Un cliente externo puede recargar durante el trabajo: la detección produce espera/error observable y no prueba exclusión global.

La intervención abarca el turno GPU completo. Primero descarga los modelos observados que impiden el turno; después verifica ausencia y VRAM. Al terminar descarga el residente propio antes de restaurar. La restauración solo afecta a la lista observada y efectivamente descargada por ese turno, cuando no hay otra ocupación incompatible. Si Ollama estaba vacío, no carga nada al salir. Un estado incierto o reinicio requiere reconciliar el recibo; no adivinar propiedad ni restaurar en paralelo.

El plan fijará la persistencia del recibo, timeout, lectura real de VRAM y política de recuperación. Nunca usará `setting` como prueba suficiente de posesión global. Los modelos del estudio tienen revisión/hash/licencia dentro del proyecto; reutilizar un servicio existente no acredita procedencia de sus modelos. El endpoint Docker→WSL2 queda configurado en lista cerrada y requiere prueba privada real sin LAN, descargas ni cloud.

**Texto y providers.** Las acciones F-17 guardan entrada, versión base, parámetros y salida propuesta en contexto privado. Reescribir sección reemplaza solo el intervalo textual elegido; el server comprueba el resto y las etiquetas. No permite que una respuesta libre del LLM sobrescriba toda la letra. `rev`/`If-Match` protege aceptación sobre una letra que cambió durante la inferencia. Desconectar SSE no equivale a cancelar el job.

F-86 expone registros existentes y disponibilidad real por función. No añade un provider externo concreto por esta decisión. Sin adapter verificado, clave o estimación fiable, aparece deshabilitado y no envía. Claves únicamente en entorno del server; config, logs, DTOs y manifiestos contienen solo identidad, coste y estado sanitizado. La aceptación local no depende de contratar una API opcional.

## 5. Impacto en módulos y ficheros

Las rutas existentes se comprobaron durante el recon. Las rutas nuevas son destinos propuestos, no ficheros ya implementados. Ninguna fila autoriza escribir código antes del plan aprobado.

| Módulo / fichero | Cambio previsto para O2 | Nuevo / modificado |
|---|---|---|
| `apps/server/app/domain_routes.py`, `api_models.py` | DTOs/endpoints de derivación, árbol, asistencia, comparación y providers; IDs y pertenencia. Mantener master explícito y API M1. | Modificado |
| `apps/server/app/models/__init__.py`, `migrations/versions/` | Reutilizar entidades; concretar ampliaciones aditivas y excepción precisa de ADR-0074 para autoridad CPU/recibos. Nunca renombrar o borrar datos. | Modificado; migración nueva si necesaria |
| `apps/server/app/lyrics.py`, `apps/web/lib/lyrics.ts`, `packages/contracts/lyrics-cases.json` | Validar etiquetas y propuestas de sección con los mismos casos; conservar versiones históricas. | Modificado |
| `apps/server/app/queue/chains.py`, `references.py`, `inputs.py`, `provenance.py` | Crear derivaciones con referencias resueltas y linaje; derechos/contexto efectivo y dependencias atómicas. | Modificado |
| `apps/server/app/queue/resolver.py`, `dispatcher.py`, `runtime.py` | Capacidades reales, carriles, residencia Ollama y cancelación/recovery de texto. Reutilizar semántica de M1. | Modificado |
| `apps/server/app/creative/recipes.py` | DTO privado versionado y compositores cerrados. Sin expresiones, paths arbitrarios ni grafo programable. | Nuevo propuesto |
| `apps/server/app/worker/contracts.py`, `planning.py`, `execution.py`, `publications.py`, `audio_child.py` | Separar autoridad CPU/engine, render edits/previews y compartir publicación/custodia; conservar compatibilidad de recibos históricos. | Modificado |
| `packages/audio-post/audio_post/pipeline.py`, `manifest.py`, `private_context.py` | Reutilizar medición/manifiestos; extensión opcional para construcción y herramientas efectivas. No normalizar masters ni reescribir manifiestos. | Modificado si exige el contrato final |
| `apps/engines/acestep/adapter.py`, `descriptor.py` | Adaptar cada task/feature M2 con su conformidad real; no editar fuentes selladas durante T-09. | Modificado después de liberar la dependencia |
| `apps/engines/common/engine_common/server.py`, `runtime.py` | Reutilizar o factorizar hooks necesarios para la residencia delegada a Ollama sin alterar comportamiento de engines propios. | Modificado solo si hace falta |
| `apps/engines/llm/` | API `/v1`, descriptor, cliente Ollama, eventos/cancelación y runtime de residencia sin inferencia propia. | Nuevo propuesto |
| `apps/server/app/providers/` | Registro/adapters opcionales server-side y coste previo; ningún provider nuevo se habilita por defecto. | Nuevo propuesto |
| `apps/web/app/create/page.tsx`, `components/LyricsEditor/LyricsEditor.tsx` | Modo simple y propuestas editables; aceptación separada de generación y preservación instrumental. | Modificado |
| `apps/web/app/songs/[id]/page.tsx`, `components/Waveform.tsx`, `PlayerContext.tsx`, `PlayerDock.tsx` | Región/bucle, operaciones, árbol con varios padres y transporte A/B medido. | Modificado |
| `apps/web/app/system/page.tsx`, `messages/es.json`, `lib/api.ts` | Ajustes por función, disponibilidad y estado de clave; next-intl y cliente tipado. | Modificado |
| `packages/engine-contract/engine_contract/__init__.py`, `packages/contracts/engine-v1.json`, `openapi.json`, `manifest-v1.schema.json`, `apps/web/lib/generated/api.d.ts` | Cambios code-first aditivos y schemas opcionales; regeneración sincronizada. No añadir obligatorios a `/v1`. | Modificado si exige el contrato final |
| `docker-compose.yml`, `.env.example`, `apps/server/app/settings.py` | Servicio LLM y destino privado permitido; música siempre local y remote apagado. | Modificado |
| `models/models.lock.json`, `scripts/fetch_models.py`, `docs/legal/licencias.md` | Incorporar únicamente el modelo LLM seleccionado y verificado posteriormente; runtime offline. | Modificado después de resolver modelo |
| `apps/server/tests/`, `apps/engines/mock/tests/`, `apps/web/e2e/`, tests junto a componentes | Evidencia de recetas/linaje/replay, rechazo, texto, providers, audio CPU y E2E; identificar mock como sintético. | Modificado y nuevos tests según plan |

| Dependencia técnica | Condición antes de integrar o aceptar |
|---|---|
| M1 cola/intentos/eventos | Contratos y evidencia vigentes de admisión, terminales, retry y recovery. No ampliar fronteras usando mocks como autoridad real. |
| M1 publicador/CPU | Custodia, recibos, publicación no-clobber y recuperación aceptados para el seam que se modifica. Fuente de edición CPU diferenciada y replay probado. |
| Almacenamiento | Persistencia ext4/VHDX, mount/UUID y límites de ADR-0069. Preview temporal no convierte tmpfs en evidencia persistente. |
| Derechos/letra | Versiones propias declaradas y procedencia efectiva por hijo. Crossfade combina derechos de ambos padres. |
| Capacidades musicales | Conformidad individual `retake`/`extend`/`repaint`/`cover`, schema efectivo y escucha. El gate continúa abierto sin ella. |
| LLM | Modelo, revisión/hash, formato, licencia, etiquetas/idiomas, memoria y cancelación verificados; red Docker→WSL2 real. |
| Aceptación M2 | M1 cerrado, 30 generaciones reales propias, M0/T-13 y escucha humana. La apertura técnica no reemplaza estos gates. |

## 6. Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Tratar edición CPU como terminal de engine | Alta si se extiende PostPlan sin variante | Procedencia falsa o bypass del publicador | Autoridad CPU explícita; validar receta, entradas, herramientas y custodia. Replay de ambas variantes; ningún intento ficticio. |
| Derivación recoge letra actual en lugar de la histórica | Media | Autoría o parámetros erróneos | Receta captura versión efectiva desde la petición elegida; revalidar propietario/hash/contexto antes de publicar. |
| Adapter devuelve pieza completa y el server vuelve a ensamblarla | Media | Duplicación, corte o mapa falso | Contrato por operación y formato de salida real; prueba de segmentos y escucha antes de verificar. |
| Crossfade oculta un padre o raíz incorrecta | Media | Linaje/derechos incompletos | Aristas de ambos padres con roles/mapas y menor raíz original ULID. No UI de padre único. |
| Clipping, drift o falsa igualdad A/B | Media | Comparación engañosa | Ganancia común solo atenuación, salida renderizada y medida, techo/tolerancia fijados antes de test; medir transporte y escuchar. |
| Silencio/clip corto produce LUFS no finito | Media | Ganancia inválida o audio extremo | No igualar automáticamente; estado visible y escucha ordinaria. Test de medición ausente y no finita. |
| Preview parcial, acceso a audio borrado o limpieza concurrente | Media | Fuga de datos o reproducción corrupta | Propiedad, hashes y acceso revalidados; no servir parciales; limpieza de recursos propios sin lectores activos. |
| Ollama ajeno recarga durante un turno GPU | Alta | Dos residentes, spill o fallo | Observación y controles durante turno; espera/error visible. No prometer mutex global; recibo y restauración condicionada. |
| Reinicio pierde qué descargó el estudio | Media | Restauración ajena o GPU ocupada al publicar | Recibo durable de intervención, reconciliación de observación/acción/resultado y ausencia de otra ocupación. UNKNOWN no concede autoridad. |
| Asumir que el servicio compartido acredita pesos | Media | Modelo sin hash/licencia | Verificar modelo/revisión/archivos del estudio antes de descriptor real. Ningún nombre histórico se considera ganador. |
| Clave/coste externo incorrectos o fallback silencioso | Media | Envío involuntario o secreto expuesto | Función+activación+clave+estimación verificada; sanitización; remote desactivado de fábrica y música excluida. |
| M1 sigue abierto o cambia un seam concurrentemente | Alta | Construcción sobre garantías no aceptadas | Dependencias trazadas por unidad; releer seams al integrar, preservar cambios ajenos y mantener criterios reales abiertos. |
| Probar M2 interfiere con T-09 activo | Media | Invalida evidencia del benchmark | No ejecutar inferencia ni modificar fuentes selladas. Coordinar future carga CPU/Docker y ventana GPU con el orquestador. |
| El documento de engines conserva llama.cpp en su tabla histórica | Alta | Implementación contradice ADR vigente | ADR-0035 y Constitución fijan Ollama adaptador. El orquestador/documenter actualizará la tabla al registrar el diseño; no reabrir ADR-0012. |

## 7. Preguntas abiertas

- **Plan:** el planner debe respetar O2 y resolver las incógnitas siguientes antes de sus unidades de implementación. El diseño aprobado no sustituye al plan ni a sus gates.
- **Autoridad CPU:** concretar variantes de plan/recibo y representación durable compatibles con PostPlan/CapturedProvenance existentes. `Take.model_id`, `model_version` y `seed` actuales son obligatorios; aplicar el origen discriminado de ADR-0074, sin identidad ficticia, y probar la migración/lectores antes de editar audio.
- **Modelo LLM:** seleccionar por pruebas de etiquetas, idiomas, fidelidad de sección, cancelación, memoria, hash/revisión y licencia. Este diseño no escoge uno ni afirma calidad.
- **Ollama:** resolver endpoint privado y controles disponibles; fijar recibo de intervención, restauración y recuperación. Validar conexión y residencia real cuando T-09 libere recursos.
- **Operaciones musicales:** extraer schemas/limits del descriptor verificado y fijar respuesta completa frente a región. No inventar continuidad, fidelidad ni escalas de control.
- **Audio CPU:** fijar formatos/canales de crossfade, índices de muestra y envolventes; medir fidelidad de keep y uniones. Los mapas solo declaran operaciones del contrato vigente.
- **A/B:** confirmar formato preview compatible, instrumento de medida, tolerancia propuesta ≤0,5 LU/≤−1 dBTP y política temporal. Medir clicks/drift/latencia con audio controlado; escucha humana pendiente.
- **Cache/preview:** fijar clave, límites de disco, expiración, manifiesto CPU v2 con sujeto job autorizado desde recibo privado y custodia de lectores en temporales propios. No trasladar datos fuera del proyecto.
- **Providers:** no hay proveedor seleccionado. Habilitar solo adapters documentados y verificados con costes fiables; decidir si una integración opcional merece spec aparte.
- **Documentación vigente:** la tabla de engine-llm en `contrato-engines.md` sigue nombrando llama.cpp. La segunda pasada debe señalizar su actualización al orquestador; ownership actual limita esta escritura a design.md.
- **ADR:** ADR-0073 registra O2 en `docs/decisiones/`, destino autorizado por el orquestador conforme a AGENTS.md. Nace `propuesta`, pendiente de revisión/aceptación; el orquestador mantiene el índice compartido. No se duplica en `docs/knowledge/adr/`.
- **Gates:** identificar evidencia de M1 cerrado y 30 generaciones propias; verificar individualmente las cuatro operaciones, LLM/VRAM y utilidad A/B. CPU/mock no cierra aceptación musical.

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-10-10 | Primera pasada: tres opciones, recomendación O2 y dependencias reales; estado borrador y elección pendiente. |
| 2026-10-10 | Segunda pasada: el orquestador elige O2 bajo delegación; diseño aprobado, ADR-0073 propuesta y enlace mínimo desde spec. Precisa autoridad CPU y límites de evidencia de keep/crossfade. |


La concreción contractual posterior de [ADR-0074](../../decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md) conserva O2 como arquitectura global y elige O1 sólo entre las alternativas de representación CPU. Inferencia/post M1 conservan v1; CPU autónomo/previews usan v2, historia mixta song v2 y cuatro operaciones server v2. Los schemas nuevos no modifican tipos históricos v1 y la excepción SQL se limita a tres tablas.


## Concreción de composición T03 — O1 elegida, contrato en revisión

[Contrato por muestras medidas](composition-contract-design.md) y [ADR-0079](../../decisiones/ADR-0079-composicion-creativa-por-muestras-medidas.md) preservan O2 global. ROOT elige O1 bajo delegación: preflight puro, conversiones completas medidas y plan final sin estimar frames. Full/region tienen construcción distinta, keeps full no verificados y gate PCM posterior. El contrato sigue en revisión; no se implementa producto antes de ratificación y RED. T03/M2 no están aceptados.
