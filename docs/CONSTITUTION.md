# Constitución del proyecto — music-studio

> Estos principios son permanentes y se aplican a todo el trabajo del repositorio. Los agentes del plugin custom-agents la leen antes de empezar, y la revisión adversarial (lente A) marca como gap cualquier cambio que viole uno de ellos.
> **Para cambiar un principio** hace falta un ADR nuevo en `docs/decisiones/` y editar este fichero. No se cambia desde una tarea normal.
> Última revisión: 2026-10-22 (ADR-0089: se retira la excepción del VHDX de ADR-0069) · Mantenida por: el propietario

## 1. Principios de producto

1. **Local por defecto.** Música, letras, imagen, vídeo y análisis se generan con modelos locales. Un proveedor externo solo se usa si está activado explícitamente para esa función, se muestra en la UI y queda en el manifiesto. **La música es siempre local** (ADR-0014).
2. **La canción es el proyecto.** Takes, versiones de letra, análisis, portada, vídeo y exportaciones cuelgan de `song`, directamente o a través de sus entidades. Las bibliotecas globales son personajes, presets, colecciones y uploads; la infraestructura no es contenido musical y los sujetos CLI de M0 conservan su excepción hasta promoción a una canción. Assets y aristas deben acreditar pertenencia mediante su sujeto o extremos, sin exigir una columna redundante (ADR-0013, ADR-0041).
3. **Nunca se sobrescribe un take.** Toda edición (extender, regenerar sección, cover, variación, recorte) crea un take hijo, enlazado con su(s) padre(s) en `lineage_edge` y con `root_id` y `derivation`. El take maestro solo cambia por acción explícita del usuario.
4. **Honestidad en la UI.** El progreso solo avanza con eventos reales del engine. Las acciones que el modelo activo no soporta no se muestran, o se muestran deshabilitadas con el motivo.
5. **UX derivada de Suno y Sondo sin copiar su identidad**: ni logo, ni paleta, ni tipografía, ni textos (ADR-0010).

## 2. Arquitectura fijada / vetada

- **Fijado:** web (Next.js) → server (FastAPI, fuente de verdad, sin torch) → engines con el contrato `/v1`, todos en Docker para el producto. Ollama es la excepción: servicio local compartido en WSL2, consumido por un adaptador Docker (ADR-0003, ADR-0035).
- **Fijado:** **solo el server escribe en la base de datos** (SQLite WAL). Los engines no tienen estado persistente, no acceden a la BD ni a servicios cloud; la llamada local autorizada de `engine-llm` a Ollama es la excepción de red de ADR-0035. Solo escriben salida **cruda** en `data/tmp/<job_id>/`. El post-proceso, los manifiestos, el render y el traslado a `data/songs/` los hace el server (ADR-0004, ADR-0017).
- **Fijado:** el contrato server↔engines es `/v1` de [`arquitectura/contrato-engines.md`](arquitectura/contrato-engines.md) (tareas genéricas, eventos con `seq`, un terminal único); dentro de `/v1` solo se añaden campos opcionales. Los proveedores externos son adapters **dentro del server** (carril `remote`), nunca engines con claves (ADR-0014, ADR-0019).
- **Fijado:** la cola usa `job` y `job_dependency` con carriles `gpu` (1) / `cpu` (2) / `remote` opcional y desactivado por defecto, prioridades y dependencias. No se incorporan Kafka ni Redis (ADR-0018, ADR-0035).
- **Fijado:** **un único modelo residente en VRAM**. Los engines propios lo ejecutan en un proceso hijo que `unload` termina. Para Ollama compartido, el adaptador descarga el modelo y verifica ausencia y VRAM liberada sin detener el servicio ni borrar modelos; no presupone exclusión con consumidores ajenos. El tope de VRAM por proceso propio se calcula de la VRAM **libre** menos un margen, nunca como fracción fija; el pico se registra (ADR-0007, ADR-0035).
- **Fijado:** la lógica de negocio pide **capacidades**, nunca nombres de modelo. Añadir un modelo supone un adapter, un descriptor, la batería de conformidad y una fila en `docs/legal/licencias.md`.
- **Fijado:** la primera migración de M1 crea el esquema completo definido inicialmente en [`arquitectura/datos.md`](arquitectura/datos.md), baseline de 23 tablas de ADR-0041; después, **solo migraciones Alembic aditivas**, también para nuevas relaciones aprobadas posteriormente como `job_attempt` (ADR-0043). Renombrar o borrar columnas con datos exige un ADR. La excepción delimitada de [ADR-0074](decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md) permite relajar/reconstruir únicamente `take`, `publication_intent` y `publication_intent_revision` para origen CPU discriminado; inferencia conserva sus campos obligatorios. Exige exclusividad, backup restaurable, conservación de datos/IDs/FK/índices/checks/triggers y rollback probado; no se cambia el baseline. Todo artefacto generado tiene manifiesto versionado y linaje: inferencia conserva v1 y CPU autónomo usa v2, también sus previews; snapshots con cierre CPU usan v2. Ningún manifiesto emitido se reescribe y v1 solo crece con campos opcionales. La API server añade operaciones v2 sin alterar DTO M1; engine `/v1` sigue compatible.
- **Vetado:** `torch.load`, `pickle.load` o cualquier deserialización pickle de pesos en código propio. En runtime solo se cargan `safetensors`, `gguf` u `onnx`, verificados por SHA-256 contra `models/models.lock.json` y fijados por revisión (nunca `main`); los pickle de repos oficiales se convierten una vez con el auditor y el código remoto (`trust_remote_code`) va fijado por hash (ADR-0006).
- **Vetado:** rutas fuera de la carpeta del proyecto. Código, modelos, datos, evaluaciones y memoria viven dentro de `music-studio/` (ADR-0005). La excepción de ADR-0035 se limita al servicio Ollama preexistente y compartido; los datos del estudio y los nuevos pesos siguen dentro del proyecto.
- **Vetado:** integrar APIs generativas de música de terceros (Suno, Udio…).
- **Vetado:** modelos o herramientas cuyos pesos no permitan uso comercial como opción por defecto. Solo pueden usarse como «laboratorio», con `commercial_use: false` en el manifiesto (ADR-0011).
- **Vetado:** añadir un servicio de infraestructura (Postgres, Redis, colas externas, cloud) sin un ADR.

## 3. Convenciones

- Documentación y UI en **castellano**. **Identificadores de código, API, BD y JSON en inglés** (`song`, `take`, `master_take_id`). Todas las cadenas de la UI salen de `next-intl`; nada hardcodeado.
- El estado de las tareas vive **solo** en el `tasks.md` de su hito. Cada tarea se cierra con su `Verificación` ejecutada.
- Ramas y commits según [`arquitectura/convenciones.md`](arquitectura/convenciones.md) §7: rama por tarea `m1/t-04-dispatcher`, `fix/<slug>`, `docs/<slug>`; Conventional Commits en castellano con la tarea al final: `feat(server): dispatcher con cancelación [M1/T-04]`.
- Contratos **code-first** (ADR-0019): `openapi.json` y `engine-v1.json` se generan y se versionan en `packages/contracts/`; un test falla si difieren del código. Manifiesto, timeline y `song.json` tienen JSON Schema. Si cambia un contrato, el cambio va en el mismo commit que el código que lo usa. Convenciones de API, errores, unidades y configuración: [`arquitectura/convenciones.md`](arquitectura/convenciones.md).
- Unidades: tiempos en **segundos (float)**, frecuencias en Hz, loudness en LUFS/dBTP, tamaños en bytes. Fechas en ISO-8601 UTC. IDs en ULID.
- Toda decisión que contradiga un documento vigente se registra en un ADR y actualiza ese documento en el mismo cambio.

## 4. Seguridad y datos

- Los puertos publicados al host se limitan a `127.0.0.1` (`127.0.0.1:P:P`). Los contenedores se comunican por nombres de servicio; el server valida `Host` y `Origin` y los engines exigen token interno. La ruta Docker→Ollama WSL2 debe validarse sin exposición a la LAN; no se presupone conectividad ya probada (ADR-0020, ADR-0035).
- Ningún secreto en el repositorio: claves solo en `.env` (git-ignored) del server. Los engines no reciben claves de proveedores externos.
- **Derechos:** cada generación lleva la declaración de autoría de la letra. Todo audio o imagen subido lleva su declaración de derechos. Una foto de una persona real exige «soy yo» o «tengo su consentimiento». Sin declaración no se encola.
- Los engines **no descargan nada en ejecución** (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`); la descarga de modelos es un script aparte. El adaptador LLM puede comunicarse con el Ollama local compartido, sin descargar pesos ni acceder a cloud (ADR-0035). No se promete aislamiento de red a nivel Docker: no usar `network_mode: none` ni redes `internal`, que impedirían publicar los puertos (ADR-0020).
- Los nodos personalizados o código de terceros (adapters, nodos de ComfyUI) se fijan por commit y se revisan antes de integrarlos.
