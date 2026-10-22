---
estado: aprobado
fecha: 2026-10-11
iniciativa: m3-produccion-portada-video-letra
alcance: contrato documental por unidad
D-01: O1 ratificada por ROOT
D-12: ratificada por ROOT tras revisión y QA documental
---

# Qué dependencias puede consumir M3

Última actualización: 2026-10-11.

Este contrato concreta T-01, CA-01 y CA-48 del [ledger M3](tasks.md). ROOT ratifica D-12 después de revisión y QA. La tarea sigue abierta; ninguna función M3 queda habilitada por documentarla.

El corte es el snapshot de 77 fuentes entregado por ROOT el 2026-10-11T16:55:17.175557+00:00. El apéndice fija ubicaciones repo y SHA-256 de bytes. Una liberación nueva exige releer su fuente y sus gates. Los estados viven en el ledger.

D-01 conserva O1: derivados tipados sobre la cola existente y escena N0 compartida offline. [ADR-0080](../../decisiones/ADR-0080-produccion-por-derivados-tipados-y-escena-n0-local.md) figura aceptada en este corte. El brief conserva redacción anterior de propuesta; prevalece la fuente entregada. No se reabre O1 ni se fijan campos pendientes D-02–D-09.

## Qué significa disponible

| Nivel | Evidencia necesaria | Lo que permite |
|---|---|---|
| Código existe | Fuente identificada por SHA y lector real | Leer y preparar una integración; no declararla aceptada |
| Componente puro aceptado | Liberación ROOT del alcance exacto, revisión y QA por SHA | Consumir su interfaz pura dentro del alcance autorizado |
| Integración de producto aceptada | Wiring, autoridad viva, custodia, almacenamiento y pruebas reales de la unidad | Usar esa operación concreta; no inferir otras capacidades |
| Git/clone/CI autónomo | Cierre de imports, dependencias, locks y ejecución reproducible del árbol publicado | Afirmar reproducibilidad; publicar sólo archivos de componente no la demuestra |

Un hash acredita bytes; no concede custodia, ACL, permiso, derecho ni capacidad runtime. Un lock fija referencias; no acredita subjects ni un CAS activo. «No disponible» bloquea el uso indicado aunque exista código.

[ADR-0037](../../decisiones/ADR-0037-avance-tecnico-condicionado.md) permite definición y unidades técnicas independientes autorizadas. Mantiene gates reales y aceptación secuencial. Este contrato no elude `published` ni la autoridad runtime M1/T05.

## Qué gate acredita cada operación

| Gate | Evidencia exigida antes del uso |
|---|---|
| CPU | Pruebas de la unidad con entradas y lectores concretos, revisión y QA para los mismos SHA |
| Nativo | Adquisición propia, modo/geometría/policy acreditados, barreras y recuperación real; readonly no concede writer |
| ext4 | Provisión publicada, binding y admisión vivos, permisos y publicación durable real en la raíz del proyecto |
| E2E | Wiring y recorrido completo del producto, reinicio/cancelación/recuperación; mock identificado no acredita GPU o calidad musical |
| Manual | Acta independiente con instrumentos, cohorte, hashes y umbrales previos; ningún acta se presume por prosa |
| ROOT | Liberación explícita por unidad/SHA/operación y registro en su fuente canónica; si falta, permanece pendiente |

## Catálogo por frontera de integración

Cada clave F remite a ubicación y SHA completos del apéndice. Diseño aceptado acredita requisitos; la liberación ROOT acredita sólo su alcance exacto. «Pendiente ROOT» exige una liberación por unidad para ese uso.

| Seam y fuente | Autoridad y operación | Formato, versión y lector | Disponibilidad exacta y liberación ROOT | Gate pendiente y consumidor M3/condición de uso |
|---|---|---|---|---|
| S01 U1 — F41,F26 | Codec puro; inspección, conflicto y replay lógico | Journal1/receipt1; `inspect_journal`, `decide_request` | Disponible sólo codec aceptado, alcance conservado por contrato store F25:44; no ACK | CPU lógico; ningún efecto físico. M3 puede estudiar bytes, no abrir admisión |
| S02 U2 — F42,F26,F27,F28 | Observación readonly, policy S1 y geometría G2 candidata | Observaciones tipadas; `read_handle_geometry`, cadena/close | Alcance readonly conservado en F25:44; no writer ni capacidad de producto | Nativo por adquisición real y release propia. M3 no convierte B candidato en ACK |
| S03 Kernel/store — F25,F77 | Kernel I/O privado y store CAS/ACK propios | Interfaces propuestas; no lector operativo liberado | No disponible implementación; ROOT aceptó contrato, no E/S nativa | Nativo: arenas, modos, barriers, cortes/reap y cadena S1. Integración M3 espera release |
| S04 Bootstrap/lifecycle — F26,F43,F44,F45,F46 | Controller propio: seed, publish, attach, validate, quiesce/detach | Receipt1 y session/journal; readers existentes limitados | No disponible lifecycle durable; ROOT pendiente por unidad | Nativo+ext4+reinicio. Ningún JSON por ruta sustituye journal ni bootstrap acreditado |
| S05 Recibo/binding/admisión — F46,F47,F48,F49 | `ReceiptLease`, `PublishedDiskBinding`, preflight real | Receipt1; lector readonly y binding observado | Código existe; no liberación global de admisión runtime entregada | ext4+nativo+E2E. M3 sólo opera tras published y sesión validada; UNKNOWN bloquea |
| S06 Cola — F38,F39 | Server; `job/job_dependency`, prioridades y dependencias | Contratos M1; dispatcher/chains | Código existe; no integración M3 aceptada. Carriles GPU1/CPU2 son límites fijados | CPU+E2E con slots/cancel/restart reales. No nuevo runner ni servicio paralelo |
| S07 Post inference — F31,F32,F33 | Server, intento ganador y terminal acreditados | `PostPlan.version=1`, `post.audio`; validación de resultado | Código M1 existe; no autoridad CPU autónoma liberada | CPU+ext4+E2E. Reutilización sólo tras release; prohibido fabricar terminal/attempt para CPU |
| S08 Publicación/custodia — F34,F31 | `Publisher`, intención por toma y resultado autorizado | Autoridad/paquete M1; reader de contratos privados | Código existe; no publisher M3 multi-sujeto disponible | ext4+E2E cortes rename/commit/serving y reap. Export/Render/Artwork necesitan autoridad propia |
| S09 Contexto privado/rights — F50,F51,F52 | Server conserva request efectivo y linaje histórico | private_context1 y manifest1; `verify_private_context`, `verify_manifest` | Código M1 existe; no contexto ProductionRequest nuevo liberado | CPU+E2E y privacidad. Nunca sustituir letra histórica por letra actual de Song |
| S10 DTO/migraciones M1 — F35,F40,F22 | Server único writer SQLite; baseline y DTO M1 | DTO actuales; migraciones documentadas y modelos | Código existe; M1 formal abierto. No adaptación CPU2 de producto liberada | CPU+E2E datos poblados/backup/rollback. No alterar required/tipos M1 para encajar CPU |
| S11 Snapshot v1 — F36,F54,F22 | Server proyecta cierre por pertenencia y DAG | `version:1`; `project`, `validate`, `restore` | Código v1 existe; snapshot CPU2 no disponible | CPU+E2E closure/FK/assets. No exportar una historia CPU como falsa inferencia v1 |
| S12 Backup BD/media — F36,F37,F22 | Backup SQLite y proyección M1; no mantenimiento conjunto M3 | SQLite backup/restore y song1; ZIP de medios no acreditado aquí | Código backup BD existe; biblioteca consistente/paquete media no disponible | E2E+manual restauración real. Capturar BD no prueba corte coherente de medios |
| S13 Recetas M2 — F29,F20,F65,F66 | Captura/lectura/proyección puras; caller resuelve contexto | CreativeRecipeV1/CreativeRequestV1; `read_recipe`, `read_request` | Disponible T02 puro aceptado; no admisión, render o publicación M2 | CPU puro. M3 mantiene las ocho operaciones cerradas; no añade stems/export a recipe1 |
| S14 Composición T03 — F30,F62,F63 | Plan puro ligado al SHA de receta; facts medidos aportados por caller | `CompositionPlanV1`; `read_composition_plan` (F30:1150), build (F30:806) | ROOT acepta componente puro; 91 focales/183 regresión por plataforma, no render | Render PCM/soxr/custodia/E2E pendientes. M3 puede estudiar el plan, no afirmar audio producido |
| S15 Request/section map CPU M2 — F19,F21,F20 | Resolver/ejecutor/publisher futuros conservan receta e inputs | CPU plan/receipt, mapas efectivos; contrato de diseño | No disponible integración; T04 FIX1 no adoptado en este corte | CPU+ext4+E2E, binding a audio final. MapIntent requested_seconds no es mapa medido |
| S16 Manifest CPU2 — F19,F72,F51,F53 | Ejecución real server/herramientas; padres como antecedentes | Manifest2 CPU y reader dispatch v1/v2 pendientes | Decisión ADR-0074 aceptada; schema/emisor/lector CPU2 no implementados según corte | CPU+E2E histórico mixto. No engine/model/seed ficticios ni reescribir manifest1 |
| S17 Contratos públicos — F53,F54,F55,F56,F8 | Código server/engine origina contratos generados | OpenAPI actual, engine `/v1`, manifest/song/timeline1 | Artefactos actuales existen; no OpenAPI/TimelineV2 M3 ratificados | CPU de generación/diff/compatibilidad antes de integración. Sólo crecimiento opcional en `/v1` |
| S18 ACE-Step — F57,F6 | Descriptor seleccionable sólo con task/feature verificados | ModelDescriptor1.5; `descriptor()` | Código existe; music.song/instrumental y features `verified:false` en fuente | GPU/conformidad/margen+manual musical. Pin/fixture no habilita retake/timbre/LoRA ni alta calidad |
| S19 Analysis — F58,F6 | Descriptor por método; estado/binding real de resultado | Descriptor1; `descriptors()`, tasks enumeradas | Código existe; transcribe/align/clap/aesthetics/beats `verified:false` | Conformidad CPU/GPU según método+manual. No infiere key/sections/loudness ni éxito por nombre del modelo |
| S20 Comfy/portada — F76,F4,F6 | Hijo propietario de Comfy/CUDA; raw `/v1`, server publica Artwork | Adapter/workflows cerrados futuros; reader aún no liberado | No disponible capacidad M3 en este corte | GPU+unload+pins/licencias+manual imagen. Generar y editar referencia requieren gates separados |
| S21 Player — F59 | Estado de cola/reproducción y variante | `PlayerTrack`, `PlayerProvider`; localStorage queue | Código UI existe; no mixer sincronizado aceptado | E2E+manual transporte común de stems, memoria/seek; no cuatro players independientes |
| S22 Canvas — F60 | Visualización de progreso/peaks | `GenerativeVizProps`; canvas2d y rAF | Código existe; no escena N0 ni features audio reactivas verificadas | E2E+manual. Onda decorativa/progreso no cumple espectro/partículas del audio efectivo |
| S23 N0/render/export — F76,F55,F10 | VideoProject revisionado y plan derivado; server/hijo propio | Escena temporal, perfiles y contratos futuros | No disponible bundle/renderer/export M3; TimelineV2 pendiente | CPU+custodia+E2E+manual canción completa. Codec/font/browser y equivalencia preview/render requieren pruebas |
| S24 Import/portable — F76,F19,F36 | Import propio valida cierre/hashes/rights/DAG antes de promover | Catálogo y versiones de manifest/song futuros | No disponible import M3 con autoridad por paquete | ext4+E2E cortes/replay/colisiones. Hash igual no acredita archivo ajeno; no reescribe historia |
| S25 Backup biblioteca/activación — F76,F37,F25 | Coordinador exclusivo y binding raíz/BD, distinto del publisher | Paquete/catálogo/recibo mantenimiento futuros | No disponible backup conjunto ni switch/rollback M3 | ext4+E2E+manual nueva biblioteca íntegra. No copiar VHDX activo como backup |

## Qué versiones existen y cuáles siguen pendientes

El número 2 no identifica un único contrato. F51:229 lee `input_receipts.receipt_version=2` dentro de manifest v1. No es ManifestV2 CPU. F50:121 mantiene private_context1; F31:464 mantiene PostPlan1.

| Familia | Existe en el corte | Falta antes del consumo dependiente |
|---|---|---|
| Engine | `/v1`, tareas y ModelDescriptor actuales | Conformidad real por task/feature y versión efectiva; fields nuevos sólo opcionales |
| Receta/composición | CreativeRecipeV1/CreativeRequestV1 y CompositionPlanV1 puros | Admisión/ejecución/render/publicación que acrediten los hechos |
| Preparación de inputs | Lector de input receipt1/2 en manifest.py | No convertir receipt2 en autoridad CPU2 autónoma |
| Manifest | Schema/verificador v1 actual | Schema/emisor/reader Manifest2 CPU y distribución coordinada |
| Song snapshot | Schema/proyección/validación version1 | Song2 con cierre mixto CPU; conservación de bytes históricos |
| API/DTO | API/DTO M1 actuales | Operaciones CPU v2 y ProductionRequest M3 antes del RED dependiente |
| Timeline | timeline-v1 cerrado actual | TimelineV2/bindings nuevos ratificados; no extras silenciosos en v1 |

D-02–D-04 concretan requests, SQL, manifests y readers. D-05–D-09 mantienen decisiones propias del [plan](improvement-plan.md). Una sonda/fixture no acredita reader de producto ni migración aplicada. ProductionRequest, nuevos campos CPUv2/TimelineV2 y CAS multi-sujeto aún requieren ratificación; T-01 no los define.

## D-12: propuesta concreta a ROOT

Ratificar disponibilidad limitada al scope puro ya aceptado, por unidad/SHA. Mantener bloqueada toda integración consumidora de un seam pendiente. Cada liberación nueva identifica operación, versión/reader, fuentes, autoridad viva, gates y condición de uso.

Alternativa conservada: esperar release integrada M1/M2 antes de toda implementación consumidora. El avance por componentes puros permite trabajo independiente autorizado sin convertirlo en producto aceptado. ROOT debe ratificar D-12; esta propuesta no cambia plan, presupuesto, ADR o Constitución.

| Caso/fallo | Resultado exigido | Autoridad que puede abrirlo |
|---|---|---|
| SHA diferente del liberado o reader ausente | Dependencia no disponible; releer/revisar/QA nueva fuente | ROOT por unidad |
| U1 clean o U2 B candidato sin writer/ACK | No admisión, no efecto de lifecycle | Release kernel/store y controller M1/T05 |
| `published` no acreditado, sesión UNKNOWN o custodia abierta | Bloquear dispatch/publicación dependiente | Controller/binding real y prueba ext4/nativa |
| CpuSelection válida sin recibo de ejecución | No publicar ni inventar terminal | Resolver/ejecutor/publisher CPU M2 |
| Plan T03 válido sin PCM/soxr medido | No afirmar conformidad musical/render | Tareas reales M2 y sus gates |
| Task/feature `verified:false` o pin runtime_verified false | Capacidad no habilitada; explicar ausencia | Conformidad real del descriptor/selección |
| Manifest v2 futuro leído como v1 o DTO M1 relajado | Rechazo explícito; decisión/versionado antes de cambio | Tareas de contrato y migración ratificadas |
| Archivo existente con hash igual pero sin custody/intent propia | No adoptar ni reutilizar como éxito | Autoridad del sujeto y reconciliación propia |
| Derechos/padres/hash faltantes o ownership incoherente | No encolar/publicar; no rellenar desde estado actual | Captura autorizada server y validación real |

## CA-01: qué sigue abierto para aceptar M3

M1 conserva estado formal 0/17 y T05 abierto. F64, recibo ROOT del store, declara `product_native_verified:false`, `T05_closed:false`, `M1_accepted:false`. Sus 95 checks son documentales.

M2 conserva 3/30 y `M2_accepted:false` en F62. T03 cerrada acepta composición pura; T04 FIX1 no adoptada permanece pendiente. M3 exige M2 cerrado y gates heredados. No basta cerrar T-01 ni ejecutar mocks.

[M-01](test-plan.md) y T-42 conservan instrumentos, cohorte real, acta independiente y decisión ROOT. Docker/GPU, post/publicación, reinicio y aceptación musical mantienen evidencias separadas. Este documento no genera resultados ni actas.

## CA-48: procedencia y compatibilidad exigidas

Cada consumidor identifica sujeto, versión/reader y fuentes efectivas con hashes. Conserva propietario/canción, padres ordenados, linaje y declaraciones históricas. Contrasta bytes y pertenencia reales; validar un DTO no acredita esos hechos.

Inference conserva el cómputo realmente ejecutado y autoridad ganadora. CPU conserva executor server, receta, herramientas y recibo propios. Upload conserva source upload y declaración. Los modelos de padres son antecedentes; no se copian como modelo ejecutado, engine, seed o intento nuevo.

`commercial_use` requiere conjunción de derechos de entradas/padres, letra y herramientas; incluye modelo sólo cuando intervino. Un false restringe el resultado. Un true validado no sustituye prueba legal ni licencia. [Licencias](../../legal/licencias.md) sigue obligatoria antes de integrar modelos/herramientas.

Los readers preservan bytes/hash/semántica v1 históricos. El nuevo lector despacha explícitamente versión y rechaza desconocidas sin fallback ni defaults que reescriban evidencia. La convivencia v1/v2 CPU sigue requisito pendiente de producto. No se relaja schema v1 para CPU ni se reescribe un manifiesto emitido.

Los contratos son code-first. Código, copias schema y OpenAPI generado cambian coordinadamente, con prueba de equivalencia. DTO M1 conserva compatibilidad. La excepción SQL ADR-0074 es delimitada; no autoriza CAS multi-sujeto ni migraciones M3 adicionales. Toda decisión nueva precede al RED, con exclusividad, backup restaurable y rollback probado.

[M-48](test-plan.md) conserva inspección independiente y evidencia instrumental. T-01 sólo concreta condiciones. Ninguna función M3 real se implementó aquí.

## Qué acredita la evidencia histórica entregada

F62 acepta T03 el 2026-10-11T16:01:36.792725+00:00: 91 focales, 183 regresiones y 274 casos por plataforma. La cobertura conjunta es 92.82296650717703%; QA exits 0. El scope sigue puro. Son mediciones históricas de ROOT, no pruebas ejecutadas por documenter.

F63, recibo Git del 2026-10-11T16:08:19.316069+00:00, fija `cc6efaf66bbf75aad53e0c26a809616f58b06cec` y cinco archivos de componente. Declara `component_commit_only:true`, `main_merged:false`, `autonomous_tree_or_CI_proven:false`. No acredita clone/CI autónomo ni dependencias M1 cerradas.

F65/F66 documentan imports transitivos M1 y pins T02. Coincidir con QA conserva qué fuentes se usaron; no acepta esos módulos como producto M1. Esta pasada no reaudita todo Git ni modifica locks.

Los recibos privados se identifican por ruta/SHA para auditoría local. No son enlaces públicos portables: `.cache`, entradas privadas y rutas personales no se publican. Navegación relativa al destino canónico; referencias `file:line` indican líneas del corte.

## Fuentes fijadas por ROOT

Cada clave remite a ubicación repo y SHA-256 del corte. Son evidencia, no capacidades activas. F5 registra la página antes del añadido mínimo M3; su hash de entrega se informa aparte.

| Clave | Ubicación repo | SHA-256 del corte |
|---|---|---|
| F1 | `AGENTS.md` | `914438ce2743d757d6b0aca903cafb6abd7e5075676ae35ee6bb82b71a328789` |
| F2 | `.claude/dev.json` | `ee4728bbc6a88539c5f85c2050dcd1c1bea9ece58e93f5fafa4f2d497c2b70b1` |
| F3 | `docs/CONSTITUTION.md` | `b15df6b30747dbe594d97a8fe2f896509586da4b890de981c42c1f27234861b2` |
| F4 | `docs/legal/licencias.md` | `fe67d7b80f275d1c2a39230ac7f75a9f48d59768b29d4d4b472e3fa2f7b0ba43` |
| F5 | `docs/arquitectura/iteracion-creativa.md` | `81810360a6168d58851e48789ab067acd719a7519160f849dd3857857ccbb142` |
| F6 | `docs/arquitectura/contrato-engines.md` | `122e0eeb3f18bf2c7d7b967ee02462b090c7a230ecb02b8a2fdb0fde5e9bd471` |
| F7 | `docs/arquitectura/datos.md` | `a5ffb07c5de4e8598162e91338868f14772ca0fdcd82ebb13c23dbcc4f2f3547` |
| F8 | `docs/arquitectura/convenciones.md` | `77a0745f0e7c45b2c5b4c7af348435149f88c96a986f71d68e484d02d5cc491b` |
| F9 | `docs/arquitectura/sistema.md` | `f7011628a2ba526ff1ed22fa3e263097f61e568456a449161770f7556dcee3d4` |
| F10 | `docs/arquitectura/pipeline-audio.md` | `d84f639cb901a4a4266713950ad9deefdb2c3aed65f5508f071a82e16b2b01d8` |
| F11 | `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/spec.md` | `1472125bf6b5c7e544648c84aac3331853cf5ec45fed00e0d83acf718d6e8c10` |
| F12 | `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/design.md` | `afdb2a4208ad2177533903de17f7c7a75906ff1ee3a9cc4c13219261231cfd67` |
| F13 | `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/improvement-plan.md` | `2e179881dda6762e7f03bae42e6dca2d1b85aa4e5d3b7fd37318b9dcf6ee191b` |
| F14 | `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/tasks.md` | `0bde857c7c677ef7b006b6b13935230a9d16a6b66eb7ba0b7816d9cdf8c6653b` |
| F15 | `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/test-plan.md` | `fe76ac3f78983a36f4efabf98efa85eee9b97593574ea3095f895d5bc5f45855` |
| F16 | `docs/roadmap/2026-10-10-m2-iteracion-creativa/spec.md` | `1cb6a36d6b0be15d814aff1839c76649bce3b93c08b71e5af0ee7988e94f5180` |
| F17 | `docs/roadmap/2026-10-10-m2-iteracion-creativa/tasks.md` | `719acb5d07cb79858b534662d25fcd8385bcb311244c482f2e004d5d311fba26` |
| F18 | `docs/roadmap/2026-10-10-m2-iteracion-creativa/improvement-plan.md` | `f7e269dcba3a799053bff9a51771e8e31d58e76788f2b7c7db6b0c3f59e421e2` |
| F19 | `docs/roadmap/2026-10-10-m2-iteracion-creativa/cpu-contract-design.md` | `74ce671c453115d77025226325318b50f824d232b6bf9d328f182d163302519f` |
| F20 | `docs/roadmap/2026-10-10-m2-iteracion-creativa/recipe-contract-design.md` | `9e4ace1a979b4058ade751cb3bf45a0819c89fe3a2419aa460f0ea8f4adb0c20` |
| F21 | `docs/roadmap/2026-10-10-m2-iteracion-creativa/composition-contract-design.md` | `321e55cd5e1fd142e89f5be496f6640b36f453f58a4dd5c026c6d0932e8ec151` |
| F22 | `docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md` | `0914eb62aeaf8b62df0c38aca73b3a522601481e425896892e9e232f0efe4899` |
| F23 | `docs/roadmap/2026-09-28-m1-mvp-estudio/spec.md` | `b71f4940a6c297de922e5b63bf7a12567b2bdc139ee649ca7045e11cb2471eab` |
| F24 | `docs/roadmap/2026-09-28-m1-mvp-estudio/improvement-plan.md` | `15b555c14bc54731223b914914e2a82a9b4d5138b945981f76aac2a5c85729a0` |
| F25 | `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md` | `fba4df08da053b442c157de3696d33c88c1c430c43655607490114c9cd95efd9` |
| F26 | `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md` | `489f7521786574c554e8a276cf1eeca68fad557b5aed6e9c9132d0338953eefa` |
| F27 | `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-security-policy.md` | `4b87e0f36d1e05b05a3274876006aabf7b5a8e7f1cee4208c80321d99c7acdab` |
| F28 | `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-geometry-design.md` | `47abeb0ccece79e7927e212f3a279df593c445675690a94577e2e73d83a80122` |
| F29 | `apps/server/app/creative/recipes.py` | `d8eb051277b436f5ba049611221a1bfc9161e1a5561dd984058ce76d645ab9ca` |
| F30 | `apps/server/app/creative/composition.py` | `f2b5a79fcb4d489bc2155393adae6abf12049dda15836bd6960f24a806c312d3` |
| F31 | `apps/server/app/worker/contracts.py` | `4c04a5a5698e88ab1d31f65e9f3924e6b63e077b6dc2ee282f35da2c85fb891b` |
| F32 | `apps/server/app/worker/planning.py` | `3aca3783d91b398fc4932f0c61759563cc2a1d4088ce23ef81b0186148bb8dcd` |
| F33 | `apps/server/app/worker/execution.py` | `f2cb4a27f7bf531f98d9f3f2698e8d3509da9306c6d3b602fed5fc7ce3cb617f` |
| F34 | `apps/server/app/worker/publications.py` | `c905685a2b5b7ac689578707e548440f3939ddbf22e6fb71bf77ec4128fae054` |
| F35 | `apps/server/app/models/__init__.py` | `9c86ef171968e799908068c1f98ce47186b9e2ed3337c019a7e9696d38dac0df` |
| F36 | `apps/server/app/snapshots.py` | `61189b40618a86bdaf7cd0266ab565112b55dc2de053875925c4567fff8c46f4` |
| F37 | `apps/server/app/backup.py` | `8a677bd8a25c05be484db10464a0010e0462be127e4f96881a90faa0896bcf1d` |
| F38 | `apps/server/app/queue/chains.py` | `65bbbf0a53a121e2c4efaaa95df73d8d1764eba09b51cb9debfdc667df5eeb7f` |
| F39 | `apps/server/app/queue/dispatcher.py` | `832284d9fc94dbaeddc9e5b3843fd91886d6891e4ad6f653f0feb317903ca7e7` |
| F40 | `apps/server/app/api_models.py` | `dbc89ab614a633097a95db399989fb5d99d342261f39f4d22489858fec825383` |
| F41 | `scripts/storage_journal.py` | `5db83df2584f419177162054c02eda46c33abcca253bcf3b2130301bec6f6ea5` |
| F42 | `scripts/storage_journal_windows.py` | `8f0e7bdb4c5dda0b92d186ea8293861209efe9170e5c36d8ce21c7662395c973` |
| F43 | `scripts/storage.py` | `ec629649a7a33dce31226d0c8154961931057772ff8e1c26fd4216a9142dc2e1` |
| F44 | `scripts/storage_attach.py` | `31ee85f23c76b148079d37ee30fd34e0ca0bc21defcdbdd6b5c4d7ebbf561358` |
| F45 | `scripts/storage_publish.py` | `5a1d4e4a3da3e95874e39baeb50e5755e78e540385f8472a5656e9377fa4b528` |
| F46 | `scripts/storage_operator.py` | `47f20bcbb9c76ef261dae799ab6308ac83aced98b31ff08b1b55cb1bcf3c56b8` |
| F47 | `scripts/storage_receipt_store.py` | `2d0944b45b66ccb210492585d7c093e88d1c6cfb8a066642ccd42dbdc04ed8f3` |
| F48 | `packages/storage-guard/studio_storage_guard/receipt.py` | `811a5782ab0b84c0252e552e871d976fd944ec8059591c9afc492370394846f5` |
| F49 | `packages/storage-guard/studio_storage_guard/preflight.py` | `c2c1634c157208e73a2f90ec24cf49d14693ae24633067aa377f2d8ae180001f` |
| F50 | `packages/audio-post/audio_post/private_context.py` | `0397c05c53785f9068daef896ef92fb3a3c9a2ed6772dfb7f790ac9ad6c65c23` |
| F51 | `packages/audio-post/audio_post/manifest.py` | `b646e71e60ced32d7d7bcf2a54fe5d07b4f1d9cced4f1f989cb118f4c362a0b8` |
| F52 | `packages/audio-post/audio_post/pipeline.py` | `32f7fba8ddfce97c7624edae025b36fb5a80250cf29ca24958b2ca1fc5a19c03` |
| F53 | `packages/contracts/manifest-v1.schema.json` | `13d837fe3ecae22a6b3b3bdea66de8599e0b5fe2ce49fc08ec05457f5f9b9224` |
| F54 | `packages/contracts/song-v1.schema.json` | `c84b8c4baa8698931ce4590bf81b6cef1fb20ecbdcf1e1447ec94860bae5a2f1` |
| F55 | `packages/contracts/timeline-v1.schema.json` | `d85666a0dbb7f9e67a6d7442d2e44d6b971ca9584eb424941b6330e582948660` |
| F56 | `packages/contracts/openapi.json` | `f42adb4a03ba35d91010829028d8a8fd8bb98daa86d5f7c3d56ca68656a5f5c5` |
| F57 | `apps/engines/acestep/descriptor.py` | `64fab407f9d48d2fb29d3142149d40bc69ce9db755341d536de643ccba630e2f` |
| F58 | `apps/engines/analysis/engine_analysis/descriptor.py` | `5627a19c0a0eccd9c127b83ff7232f7f7b5a43fecf491121202a5cdd35c45e17` |
| F59 | `apps/web/components/PlayerContext.tsx` | `13406a75980366e766eaf00706bef480951d3cec93d3174ce82c24ea47f003ab` |
| F60 | `apps/web/components/GenerativeViz.tsx` | `8469a1b511bda61192c599c64e25c831307ecb8c836dd2976408cefcfdba7c6a` |
| F61 | `docker-compose.yml` | `532887ac0b473dd28f0c33549c2dfd07bd766d66711c03f4253f410854b4747d` |
| F62 | `.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-root-20261011/acceptance-root.receipt.json` | `53208103132f28f44954a703e92f236ed8e985b2e1c9d0cf101641fa7062971a` |
| F63 | `.cache/dev-cycle/m2/creative-composition-t03-product-current-qa1-root-20261011/git-root.receipt.json` | `8f4c63808d14a74c8f96b16a183232e2d4280fe455140b2be6294617ffe5f5cc` |
| F64 | `.cache/dev-cycle/m1/storage-journal-store-contract-current-qa1-root-20261011/acceptance-root.receipt.json` | `f27ca01762418de442dfb987159395fe998b3eff18cfc1dbc13860bd00e2cad9` |
| F65 | `.cache/dev-cycle/m2/creative-recipes-t02-git-dependency-audit-20261011/audit.md` | `7d128688e8aa72e0b03b80e742241e63cad1f2a61bf33decb379e3b65d38f6a3` |
| F66 | `.cache/dev-cycle/m2/creative-recipes-t02-git-dependency-audit-20261011/static-dependencies.receipt.json` | `d402675d623bf0b257b05e574a8a7bbebae3339aa7839b35abd9ccedcc7e1387` |
| F67 | `docs/decisiones/ADR-0037-avance-tecnico-condicionado.md` | `81872969db8fb81f8794c12a1534b261ab07ab4e2ac76c63ad25e5e2cd91cdb6` |
| F68 | `docs/decisiones/ADR-0055-ejecucion-cpu-y-publicacion-durable-por-toma.md` | `b0a3577432d7748ba181f0843f1796920760c3e44af2554d3e09ef42be7edee9` |
| F69 | `docs/decisiones/ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md` | `42431718ba4b1e185369369e9fa685e1a096e5927d61cf125f84a8a15c30b027` |
| F70 | `docs/decisiones/ADR-0070-contexto-privado-de-request-y-linaje-en-publicacion-audio.md` | `30d49741d40725b8fed415d85507d3b89c55d1318e7a66ae80cd6173db10789c` |
| F71 | `docs/decisiones/ADR-0073-recetas-privadas-y-escucha-ab-de-iteracion-creativa.md` | `f5e4cc7197dd1cede3f77d81971e11444d3437198d333ce3bd50c93d599f5283` |
| F72 | `docs/decisiones/ADR-0074-procedencia-cpu-y-contratos-versionados.md` | `0174e9cc195c8c784b909abfe730ed60bcb593983dc525b74b25299a285b5ffd` |
| F73 | `docs/decisiones/ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md` | `548aa6e7e6e90e6482b4d9ab28f29c544141b6c6258c870a2ebcbff00d45feb0` |
| F74 | `docs/decisiones/ADR-0077-envelope-privado-de-recetas-creativas.md` | `72174b8c68743f162a5e4a61c662493e96737fc90b20ff8cf3399fc3f3c806bb` |
| F75 | `docs/decisiones/ADR-0079-composicion-creativa-por-muestras-medidas.md` | `a67a0d6ee53bd65762b581076c87416ec06f4ec05b6fc8ed054217026e61f268` |
| F76 | `docs/decisiones/ADR-0080-produccion-por-derivados-tipados-y-escena-n0-local.md` | `e57e656253e7829ba2122996112a2517ac08c153f4c1ad1a150d182f59aab8e4` |
| F77 | `docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md` | `71a54e543c589d41f255445b08daaaeeabb7a6b5745db2ae6b9e5175add581a8` |


## Acta ROOT de ratificación D-12 y adopción T-01 — 2026-10-11T17:42:04.104230+00:00

ROOT ratifica disponibilidad por componente puro, operación y SHA liberados conforme ADR-0037/O1. Una dependencia no disponible conserva sus gates y bloquea su integración; no hay autoridad por hash, lock o documento. Revisión fresca A/B sin gaps y QA independiente422/422 controles documentales, qa-gate oficial0; se adopta el contrato y su enlace arquitectónico. T-01 cierra únicamente esta concreción. CA-01/CA-48 quedan concretados; su aceptación de producto sigue en las tareas reales y T-42. El corte de77fuentes anterior permanece histórico íntegro. Estado actual: M1formal0/17, M2=4/30 y T04cerrada sólo contractual; K1 es candidato de implementación pendiente de revisión/QA, no producto admitido. Ningún M1/M2/M3 íntegro aceptado ni integración bloqueada habilitada. Nuevas liberaciones exigen relectura por SHA/operación/gate; no se reescriben pruebas o bytes históricos. Las referencias anteriores a D12 pendiente/propuesta quedan supersedidas por esta acta.
