# Constitución del proyecto — music-studio

> Estos principios son permanentes y se aplican a todo el trabajo del repositorio. Los agentes del plugin custom-agents la leen antes de empezar, y la revisión adversarial (lente A) marca como gap cualquier cambio que viole uno de ellos.
> **Para cambiar un principio** hace falta un ADR nuevo en `docs/decisiones/` y editar este fichero. No se cambia desde una tarea normal.
> Última revisión: 2026-09-28 · Mantenida por: el propietario

## 1. Principios de producto

1. **Local por defecto.** Música, letras, imagen, vídeo y análisis se generan con modelos locales. Un proveedor externo solo se usa si está activado explícitamente para esa función, se muestra en la UI y queda en el manifiesto. **La música es siempre local** (ADR-0014).
2. **La canción es el proyecto.** Takes, versiones de letra, análisis, portada, vídeo y exportaciones cuelgan de `song`. Ninguna entidad de contenido existe sin su `song_id`, salvo las bibliotecas globales: personajes, presets y colecciones (ADR-0013).
3. **Nunca se sobrescribe un take.** Toda edición (extender, regenerar sección, cover, variación, recorte) crea un take hijo, enlazado con su(s) padre(s) en `lineage_edge` y con `root_id` y `derivation`. El take maestro solo cambia por acción explícita del usuario.
4. **Honestidad en la UI.** El progreso solo avanza con eventos reales del engine. Las acciones que el modelo activo no soporta no se muestran, o se muestran deshabilitadas con el motivo.
5. **UX derivada de Suno y Sondo sin copiar su identidad**: ni logo, ni paleta, ni tipografía, ni textos (ADR-0010).

## 2. Arquitectura fijada / vetada

- **Fijado:** los procesos son web (Next.js) → server (FastAPI, fuente de verdad, sin torch) → engines GPU en Docker con el contrato `/v1` (ADR-0003).
- **Fijado:** **solo el server escribe en la base de datos** (SQLite WAL). Los engines no tienen estado persistente, no acceden a la BD ni a la red, y solo escriben salida **cruda** en `data/tmp/<job_id>/`. El post-proceso, los manifiestos, el render y el traslado a `data/songs/` los hace el server (ADR-0004, ADR-0017).
- **Fijado:** el contrato server↔engines es `/v1` de [`arquitectura/contrato-engines.md`](arquitectura/contrato-engines.md) (tareas genéricas, eventos con `seq`, un terminal único); dentro de `/v1` solo se añaden campos opcionales. Los proveedores externos son adapters **dentro del server** (carril `remote`), nunca engines con claves (ADR-0014, ADR-0019).
- **Fijado:** la cola es la tabla `job` con carriles `gpu` (1) / `cpu` / `remote`, prioridades y dependencias (ADR-0018).
- **Fijado:** **un único modelo residente en VRAM**, ejecutado en un proceso hijo que `unload` termina. El tope de VRAM por proceso se calcula de la VRAM **libre** menos un margen, nunca como fracción fija; el pico se registra (ADR-0007).
- **Fijado:** la lógica de negocio pide **capacidades**, nunca nombres de modelo. Añadir un modelo supone un adapter, un descriptor, la batería de conformidad y una fila en `docs/legal/licencias.md`.
- **Fijado:** la primera migración de M1 crea el esquema completo de [`arquitectura/datos.md`](arquitectura/datos.md); después, **solo migraciones Alembic aditivas**. Renombrar o borrar columnas con datos exige un ADR. Todo artefacto generado tiene manifiesto v1 y linaje; un `manifest.json` emitido no se reescribe nunca y v1 solo crece con campos opcionales.
- **Vetado:** `torch.load`, `pickle.load` o cualquier deserialización pickle de pesos en código propio. En runtime solo se cargan `safetensors`, `gguf` u `onnx`, verificados por SHA-256 contra `models/models.lock.json` y fijados por revisión (nunca `main`); los pickle de repos oficiales se convierten una vez con el auditor y el código remoto (`trust_remote_code`) va fijado por hash (ADR-0006).
- **Vetado:** rutas fuera de la carpeta del proyecto. Código, modelos, datos, evaluaciones y memoria viven dentro de `music-studio/` (ADR-0005).
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

- Todo escucha en `127.0.0.1` (puertos Docker publicados como `127.0.0.1:P:P`); el server valida `Host` y `Origin`; los engines exigen token interno (ADR-0020). Sin exposición a la red sin un ADR.
- Ningún secreto en el repositorio: claves solo en `.env` (git-ignored) del server. Los engines no reciben claves de proveedores externos.
- **Derechos:** cada generación lleva la declaración de autoría de la letra. Todo audio o imagen subido lleva su declaración de derechos. Una foto de una persona real exige «soy yo» o «tengo su consentimiento». Sin declaración no se encola.
- Los engines **no descargan nada en ejecución** (`HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`); la descarga de modelos es un script aparte. No se promete aislamiento de red a nivel Docker: no usar `network_mode: none` ni redes `internal`, que impedirían publicar los puertos (ADR-0020).
- Los nodos personalizados o código de terceros (adapters, nodos de ComfyUI) se fijan por commit y se revisan antes de integrarlos.
