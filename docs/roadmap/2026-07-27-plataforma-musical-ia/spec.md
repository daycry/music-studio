---
titulo: Plataforma propia de generación musical por IA (equivalente funcional a Suno)
slug: plataforma-musical-ia
fecha: 2026-07-27
actualizado: 2026-09-01
autor: Daycry (7590335+daycry@users.noreply.github.com)
estado: aprobada
aprobada: 2026-07-27
ratificada: 2026-08-18
prioridad: Alta
evaluacion: ./evaluation.md
plan: ./improvement-plan.md
---

# Spec: Plataforma propia de generación musical por IA

> **Cadena de artefactos**
> **Spec** (este documento) → **Evaluación**: [`evaluation.md`](./evaluation.md) → **Plan**: [`improvement-plan.md`](./improvement-plan.md) (`en-progreso`, Fase 0 + Fase 1 — sub-fase F1 activa) → **Test plan**: [`test-plan.md`](./test-plan.md) → **Diseño de UI**: [`ui-design.md`](./ui-design.md)
>
> Estado de la spec: **aprobada** (2026-07-27). Evaluación económica **completada**. Ciclo PM cerrado.
>
> ⚠️ **Aprobada no significa «empezar a construir».** El gate **G2 (legal)** es bloqueante y va **antes** de cualquier gasto de desarrollo: hasta que legal responda por escrito, no arranca ni la Fase 0. Ver `evaluation.md` §10.1.
>
> **Revisión 2 (2026-07-27)** — incorpora las correcciones de una auditoría independiente: re-estimación al alza de los cimientos y del registry, adelanto del gate legal **antes** de cualquier gasto, recorte de la abstracción prematura del registry, redefinición de la suite de conformidad, cierre de huecos de seguridad, almacenamiento cifrado y política de retención, topes de gasto, límites de uso con números y referencia de UX explícita.
>
> 🔴 **Revisión 3 (2026-07-27) — el estado sigue siendo `aprobada`, pero las cifras aprobadas ya no son las mismas.** Dos auditorías independientes más (una de coherencia, otra adversarial de secuenciación) encontraron defectos de **secuenciación y alcance**, no de aritmética: la trazabilidad estaba entera en la Fase 2 mientras la Fase 1 generaba audio sin ledger (y una cadena WORM **no admite backfill**), G1 era inejecutable como estaba escrito, no había gate de derechos sobre la **letra** de entrada, el esquema no modelaba **linaje**, y los gates no tenían gobernanza ni matriz de resultados. Consecuencia económica: **1.566 → 1.622 h base** y **Fase 1 de 33.000 € → 38.400 €**. ✅ **Las cifras de la revisión 3 fueron ratificadas por el usuario el 2026-08-18.** Detalle en §13 y en `evaluation.md` §13.

---

## 1. Contexto y objetivo

### 1.1 Contexto de negocio

Daycry necesita música para producciones audiovisuales con **procedencia de derechos controlada**. Hoy esa necesidad se cubre con librerías de producción o con servicios de generación musical de terceros (Suno, Udio), y ambos caminos presentan problemas: el primero limita la creatividad y encaja mal con el brief de cada pieza; el segundo introduce un riesgo de derechos que en 2025 se materializó cuando las grandes discográficas demandaron a Suno y a Udio por infracción de copyright en los datos de entrenamiento.

Incorporar audio de procedencia dudosa en una producción comercial es un riesgo que Daycry no puede trasladar a sus clientes. De ahí la iniciativa: **construir una plataforma propia, con modelos open source self-hosted**, en la que Daycry controle qué modelo genera cada pista, con qué parámetros y con qué declaración de procedencia.

> **⚠️ Matiz que hay que leer antes de aprobar nada.** Construir esta plataforma con los modelos open source disponibles hoy **no produce audio con procedencia más limpia que Suno**: produce audio **mejor auditado**. El manifiesto de C-10 dirá `training_data_declaration: no divulgada` para ACE-Step y para YuE, porque sus autores no publican el corpus. La única vía a procedencia realmente limpia es C-09 (fine-tuning sobre catálogo propio licenciado), que es justamente lo que la evaluación recomienda aplazar. Si el criterio de legal es «poder garantizar derechos limpios al cliente», eso hay que saberlo **antes** de gastar, no después: ver el gate **G2** en `evaluation.md` §10.1, adelantado a la semana 0.

### 1.2 Objetivo

Una plataforma web en la que un usuario introduce **una letra**, **un prompt de estilo musical** y **opciones de voz**, y obtiene **una canción completa descargable en MP3, FLAC y WAV** *(WAV como exportación a demanda, D-09; y a **48 kHz** para encajar en Avid/Premiere/broadcast, D-23)*, con un registro de trazabilidad asociado a cada pista **desde la primera generación** (manifiesto v1 de C-10a, D-20).

### 1.3 No-objetivos de esta fase

Esta spec cubre la **fase 1: uso interno de Daycry** (1–5 usuarios, 100–1.000 generaciones/mes). La **fase 2 (SaaS público)** queda explícitamente fuera de alcance, pero **el diseño no debe cerrarle la puerta**: por eso se exige desde el inicio aislamiento por usuario/proyecto, cuotas, auditoría y un contrato de modelo estable.

---

## 2. Decisiones de diseño

| # | Decisión | Motivo | Alternativa descartada |
|---|----------|--------|------------------------|
| D-01 | **Modelos open source self-hosted**, nunca API de terceros generativos | Control de procedencia, coste marginal bajo, sin exposición al litigio de un proveedor | API de Suno/Udio: es exactamente el riesgo que se quiere eliminar. **Salvedad:** un proveedor generativo con **indemnización comercial contractual** compra el mitigante sin construir nada; se evalúa como opción de compra en `evaluation.md` §6.5 |
| D-02 | **Model registry pluggable** como pieza de primer orden: el modelo es un plugin con contrato estable | Requisito explícito del usuario. El catálogo open source se mueve muy rápido y ningún modelo gana en todo; además hay que poder enchufar modelos propios fine-tuneados | Integración directa de un modelo en la lógica de negocio (hardcoded): condena a reescribir el backend en cada cambio de catálogo |
| D-03 | **Next.js (frontend) + Python/FastAPI (backend de orquestación)** | Requisito del usuario. Python es donde vive todo el ecosistema de inferencia de audio | Backend único en Node: obligaría a un puente frágil hacia el runtime de inferencia |
| D-04 | **Generación asíncrona por cola de trabajos**, nunca petición HTTP síncrona | La inferencia tarda de decenas de segundos a varios minutos, y la GPU puede tener arranque en frío | Request/response síncrono: timeouts garantizados |
| D-05 | **GPU desacoplada de la API**, invocada como recurso efímero por la cola, **con keep-warm** | Con 1–5 usuarios la utilización de una GPU dedicada 24/7 sería marginal (`evaluation.md` §6) | GPU dedicada 24/7 desde el día uno |
| D-05b | **Postura de GPU en dos capas:** *keep-warm* con idle timeout de **10 min** tras cada trabajo, y **pod caliente en horario laboral** (8 h × 22 días = 176 h/mes). **Horario `Europe/Madrid`, días laborables, con calendario ajustable por el administrador** (festivos, rodajes, cierres) | En generación musical el usuario itera 5–10 variantes seguidas; sin keep-warm paga el arranque en frío en **cada** variante. El pod caliente elimina el arranque en frío mientras alguien trabaja por ≈ 80 €/mes más — irrelevante frente al coste de desarrollo. Sin calendario editable, el pod se paga en agosto y no está el día de una entrega en sábado | Pod estrictamente efímero: ahorra ~80 €/mes y degrada el único punto de UX que el diseño no resuelve. Horario fijo sin calendario: paga cuando no se usa y falta cuando se usa |
| D-06 | **ACE-Step 1.5 como modelo de referencia inicial** (Apache 2.0; **8 GB VRAM es el suelo con offloading, 24 GB la cifra de confort**), con **HeartMuLa como segundo adapter** y **YuE 7B como candidato condicional** (tercer adapter, **fuera de la Fase 1**) | ACE-Step es el mejor punto de partida local generalista, con iteración rápida y estilo dirigible; HeartMuLa cubre multilingüe y aporta HeartTranscriptor. **YuE no es un «adapter adicional» ya presupuestado**: es una partida condicional de Fase 2 (≈ 50 h con el router, `evaluation.md` §7 C-01) que solo se activa si G1-bis demuestra que la adherencia a la letra de los dos primeros modelos es insuficiente | MusicGen Stereo: licencia **CC BY-NC**, no comercial. Queda **descartado por licencia**. Presuponer tres adapters en Fase 1: contradice D-16 |
| D-07 | **Toda generación emite un registro de procedencia** (modelo, versión, hash de pesos, licencia, declaración de datos de entrenamiento, prompt, semilla, entradas) | Es la única forma de que legal pueda auditar una pista años después | Registro de logs sin estructura |
| D-08 | **Autenticación doble vía**: SSO social/corporativo **y** usuario+contraseña, con **2FA (TOTP) configurable** en ambos casos | Requisito del usuario | Solo SSO (bloquea a colaboradores externos) o solo credenciales |
| D-09 | **Formato de almacenamiento: FLAC (lossless) + MP3 320 kbps.** WAV **solo como exportación a demanda**, y **a 48 kHz** (D-23). Loudness EBU R128 **con objetivo parametrizado por destino**, no un único valor | El audio sintetizado **no contiene 24 bits de información real**: guardar WAV es pagar ~40 % más de almacenamiento por cero información. FLAC es lossless y estándar en post-producción. WAV se genera al vuelo si un montador lo pide — y lo pide a **48 kHz**, porque es el estándar de Avid/Premiere/broadcast y los modelos generan a 44,1 | WAV como formato de almacenamiento: 40 % de sobrecoste acumulativo (ver §12.2) sin beneficio. WAV a 44,1 kHz: obliga al montador a resamplear a mano en cada pista |
| D-10 | **Watermarking del audio generado como componente propio** | Los modelos y las herramientas de voz open source **no traen safety ni watermarking de fábrica**; si Daycry lo quiere, hay que construirlo | Asumir el riesgo sin marca. **⚠️ Candidatos con licencia MIT identificados** (SilentCipher, AudioSeal — hallazgo 2026-08-18), **robustez en música por validar**: ver I-13, riesgo de licencia circular rebajado |
| D-11 | **Fine-tuning propio tratado como pipeline separado** que publica en el registry, no como un modo de la app | Requiere dataset licenciado, GPUs de entrenamiento y perfil de ML; su ciclo de vida no es el de una feature de producto | Botón "entrenar" en la UI |
| D-12 | **La UX de Suno es la referencia explícita del frontend.** En la fase de implementación se hará un **estudio guiado de su interfaz con navegador** (Claude in Chrome) para derivar flujos, estados, disposición y affordances | Requisito del usuario: «es necesario que sea como Suno». Replicar el **modelo de interacción** de un producto de referencia es práctica normal y ahorra decisiones de diseño desde cero | Diseñar la UX desde cero: más caro y con más riesgo de acertar peor |
| D-12b | **Se deriva la UX, no la identidad visual.** Flujos, estados y disposición sí; logotipo, tipografía de marca, paleta e iconografía propias de Suno **no**: se viste con la identidad de Daycry | Copiar el modelo de interacción no es problemático; copiar píxel a píxel la identidad visual de un producto propietario es otra cosa, y con la fase 2 (SaaS público) sobre la mesa conviene no heredar ese problema | Clon visual literal |
| D-13 | **La suite de conformidad valida por tolerancia perceptual, no por igualdad bit-a-bit con semilla fija** | La inferencia de difusión en GPU **no es bit-reproducible** entre versiones de driver, cuDNN o kernels de atención. Una suite basada en igualdad por semilla se rompe en el primer `pip upgrade`, y es el gate obligatorio para registrar modelos: sería un **single point of failure del proceso de desarrollo** | Casos dorados por semilla fija (propuesta de la revisión 1, **retirada**) |
| D-14 | **Solo `safetensors`. Prohibido `pickle` / `torch.load` sobre checkpoints no confiables** | Cargar un checkpoint `pickle` de terceros es ejecución remota de código directa. `weights_sha256` verifica **integridad**, no **inocuidad** | Aceptar cualquier formato de pesos |
| D-15 | **Aislamiento de credenciales del runner**: el runner nunca recibe credenciales de storage de larga vida, solo **URLs firmadas de alcance por trabajo** y token efímero; red de salida restringida; prefijo de bucket por trabajo | El registry acepta pesos **y código de adapter de terceros**, y el runner corre con acceso a almacenamiento: sin aislamiento, un adapter hostil se lleva el bucket | Credenciales compartidas en el contenedor |
| D-16 | **Recorte de abstracción prematura en el registry**: fase 1 entrega contrato + descriptor + **dos adapters** + conformidad + versionado. **Fuera de fase 1**: el router de capacidades y el formulario dinámico desde `params_schema` | Se abstrae en la **segunda** instancia, no en la primera. Con un modelo desplegado, el router es un `return "ace-step"`. El formulario dinámico cuesta más que 2–3 formularios a mano y da **peor** UX: widgets genéricos, sin etiquetas de dominio, sin orden, sin validación cruzada | Construir router y formulario dinámico en fase 1 |
| D-17 | **Tope de gasto mensual con kill switch en el proveedor**, además del `max_gpu_seconds` por trabajo | Hay presupuesto por trabajo pero **ningún límite agregado**. Un bucle de reintentos en un proveedor medido es la forma clásica de fundir el presupuesto un fin de semana | Solo límite por trabajo |
| D-18 | **Ledger de procedencia con inmutabilidad real (WORM)**: object lock con retención en bucket dedicado + cadena de hashes encadenados + sello diario firmado | Append-only *por convención de aplicación* no aguanta una auditoría de un artefacto al que se le atribuye valor legal: cualquier `UPDATE` con las credenciales adecuadas lo desmonta | `INSERT`-only en Postgres por convención |
| D-19 | **Cuotas, concurrencia y paralelismo con valores numéricos por defecto** (§12.1), no «cuotas» como concepto | Sin números, el 429 no se puede implementar y las esperas no se pueden prometer. 5 usuarios encolando 20 trabajos cada uno sobre un solo pod son **~8 h** de espera para el último | Cuotas declaradas sin valores |
| **D-20** | **La trazabilidad se parte en dos: `C-10a` en Fase 1 y `C-10b` en Fase 2.** En Fase 1, desde la **primera** pista: esquema del manifiesto **firmado por legal antes de implementar C-11**, emisión del manifiesto en cada generación, **ledger append-only con cadena de hashes**, invariante en CI y **`manifest_schema_version` obligatorio desde v1**. En Fase 2: C2PA real con firma y certificados, WORM con object lock, certificado PDF y watermarking | Tres contradicciones concretas de la revisión 2: (a) el criterio de aceptación de C-01 (Fase 1) exigía «manifiesto de procedencia completo» que no existía hasta la Fase 2; (b) la **regla 4** del registry obliga a los adapters a emitir `provenance` en un formato que **legal no había firmado**; (c) la Fase 1 corría ≥ 2 semanas generando audio sin ledger, y **una cadena WORM no admite backfill** — ese audio quedaría fuera de la cadena **para siempre** | Toda la trazabilidad en Fase 2: convierte el audio de la Fase 1 en audio no auditable de forma irreversible |
| **D-21** | **Declaración de autoría/derechos de la letra en C-01**, con el mismo patrón que C-08: bloqueo duro, registro en auditoría (usuario, fecha, contenido) y campo `lyrics_declaration` en el manifiesto | C-08 exigía declaración de titularidad para el audio subido y **C-01 aceptaba cualquier letra sin nada**. Un usuario puede pegar una letra con copyright y el sistema generaría una obra derivada con **manifiesto impecable sobre un input infractor** — exactamente el riesgo que la iniciativa dice reducir | Confiar en el criterio del usuario interno. El filtro automático de similitud de letras queda como **mejora futura no bloqueante** |
| **D-22** | **El linaje se modela en el esquema desde el día 1** (C-13): `parent_id`, `root_id`, `derivation_kind`, `section_map` (nullable) y `source_generation` en el manifiesto v1 | El flujo de §4 ya promete variantes y extensión en Fase 1, y la UX de referencia trabaja con **pares de variantes**. Sin linaje en el esquema, C-07 (Fase 3) empieza con una **migración en producción** y los manifiestos de las derivadas **no pueden referenciar a su padre** | Añadir linaje cuando llegue C-07: migración de datos con valor legal en producción |
| **D-23** | **Exportación a 48 kHz** con resample **soxr** vía ffmpeg, y **objetivo de loudness por destino**: broadcast **−23 LUFS**, streaming **−14 LUFS**, stems **sin normalizar**. El valor por destino se decide con el supervisor musical en la Fase 0 | Los modelos generan a 44,1 kHz; el estándar de Avid/Premiere/broadcast es 48 kHz. Un único objetivo de loudness sirve para un destino y estropea los otros dos | Entregar 44,1 kHz y un único LUFS: obliga a reprocesar cada pista en la sala de montaje |
| **D-24** | **Compartir = URL de la pista en la aplicación** (requiere sesión). Las **URLs firmadas** son un mecanismo **interno del reproductor**, nunca el objeto compartible | Una URL firmada que circula por correo es una fuga de audio sin control de acceso ni trazabilidad de quién lo escuchó; y caduca, así que además rompe | «Compartir» = copiar la URL firmada: fuga de audio y enlaces roscos que caducan |
| **D-25** | **UI en castellano con `next-intl` desde el día 1**; catalán e inglés como incógnita de Fase 2 (I-19). **WCAG AA no es objetivo de la Fase 1** (5 usuarios internos), pero el reproductor y el editor de forma de onda se construyen con **componentes accesibles por defecto** y la deuda queda registrada. **Reconciliación (2026-09-01):** el **contraste AA de color en todo par texto/fondo sí es requisito desde la Fase 1** — viene del sistema de diseño (`ui-design.md`); lo que no es objetivo de la Fase 1 es la **conformidad WCAG AA completa** (navegación por teclado auditada, lectores de pantalla, etc.) | Retrofitear i18n cuesta varias veces lo que cuesta arrancar con la librería puesta; y las dos piezas de UI más difíciles de hacer accesibles a posteriori son precisamente el reproductor y la forma de onda. Decir «no es objetivo» por escrito es más honesto que prometerlo y no cumplirlo | Hardcodear cadenas en castellano; o prometer WCAG AA sin presupuestarlo |
| **D-26** | **Un pod caliente + un segundo pod efímero bajo demanda** (máximo 4), con **despacho FIFO y fairness round-robin por usuario** | La opción G recomendada presupuesta **un** pod caliente (128 €/mes); «2 pods por defecto» contradecía el presupuesto. El trabajo que desborda el pod caliente paga arranque en frío (2–6 min): se declara, no se esconde. El round-robin evita que un usuario con 20 trabajos encolados bloquee a los otros cuatro | 2 pods calientes (el doble de coste sin demanda que lo justifique) o FIFO puro (un usuario monopoliza la cola) |
| **D-27** | **G1 evalúa solo ACE-Step.** HeartMuLa pasa un **G1-bis** con el mismo protocolo al registrarse su adapter en la Fase 1, como **condición de sus horas** | El protocolo decía que cada brief se genera «con ACE-Step 1.5 y HeartMuLa», pero la contenerización de HeartMuLa está en C-11 (Fase 1), **después** de G1: el gate era **inejecutable como estaba escrito** | Mover la contenerización de HeartMuLa a la Fase 0 (encarece el gate) o evaluar a ciegas un modelo que aún no existe |
| **D-28** | **Stop-loss intra-fase**: checkpoint obligatorio **al cierre de C-13**. Si se ha consumido > 60 % del presupuesto de la Fase 1 con < 40 % del alcance entregado, **parada y decisión de dirección**. Runbook de **desmantelamiento** de una página (qué se conserva, baja del proveedor GPU, destrucción de datos) | Los gates G1/G2/G3 están **entre** fases; dentro de la Fase 1 no había ningún punto de parada, y es la fase más larga (≈ 5 semanas de desarrollo). Y si se para, hay que saber cómo se apaga sin dejar facturas abiertas | Confiar en que la fase se detecte desviada al final |
| **D-29** | **Proveedor GPU local, además de cloud.** El runner es el **mismo contenedor** en tres modos de despliegue, seleccionables por configuración `GPU_PROVIDER=local\|runpod\|mock`: (a) **cloud RunPod** (pod caliente + efímero, D-05/D-05b, el default de producción); (b) **local con GPU propia**, vía **NVIDIA Container Toolkit**, en un perfil `docker compose --profile gpu-local`: detección de GPU/VRAM al arrancar, **offloading automático si < 24 GB** (D-06), y aviso explícito de tiempos degradados; (c) **mock** (`MOCK_GPU=1`, ya existente para tests). **Todos los modos heredan los mismos invariantes**: solo `safetensors` (D-14), aislamiento de credenciales del runner (D-15), manifiesto y ledger idénticos (D-20) y `max_gpu_seconds` por trabajo (D-17) — el **tope de gasto agregado mensual no aplica** en local (no hay facturación por hora de proveedor), pero el límite por trabajo sí. **La Fase 0 usa el modo local preferentemente** (confirmación 13, §8) desde antes de que exista `T-85`: en los spikes basta invocar el contenedor de `T-05` directamente (`docker run --gpus all`), sin esperar a la abstracción de proveedor completa | Petición expresa del usuario (**confirmación 12**, 2026-08-18, §8): poder ejecutar el runner en el propio ordenador donde arranca la plataforma, con **RTX 4090/5090 (24 GB)** como referencia de hardware y **8 GB como suelo con offloading** (D-06, §11.1). Útil para desarrollo, demos sin coste de cloud y como contingencia si RunPod no está disponible | Un proveedor local con su propia lógica de aprovisionamiento y su propio adapter: duplicaría el contrato del runner y rompería la garantía de que los contratos observables (manifiesto, formatos, duración, loudness) son idénticos entre entornos (spec §7) |
| **D-30** | **Instalador del runner GPU local**: un **CLI/script de instalación** que implanta el modo `GPU_PROVIDER=local` (D-29) en una **máquina nueva**, con cuatro piezas — (a) **preflight automatizado**: detección de GPU, **VRAM**, driver NVIDIA, Docker y **NVIDIA Container Toolkit** (comprobación real, `docker run --rm --gpus all …`, no solo presencia del binario), con un mensaje accionable **por cada carencia** (requisito incumplido, valor observado, comando de remedio); (b) **descarga y colocación de los pesos** con **verificación SHA-256** contra hashes esperados y **rechazo de todo lo que no sea `safetensors`** (invariante D-14, no negociable también aquí); (c) **selección y escritura de la configuración local**: modo `GPU_PROVIDER=local\|runpod\|mock`, perfil `docker compose --profile gpu-local` y guardarraíl **G-01** (`ACE_STEP_REQUIRE_GPU=1` en todos los modos de **medición**); (d) **desinstalación limpia básica** (sin restos). **Fuera de alcance:** interfaz gráfica, auto-update y **empaquetado firmado de Windows** — si algún SO objetivo lo exigiera, es un delta aparte, no parte de esta decisión. ⏳ **Ampliación propuesta el 2026-09-01 (`T-86`, F6): +32 h base / +1.920 € con margen, PENDIENTE de ratificación económica.** La decisión de diseño queda registrada aquí; **no autoriza gasto** ni altera las cifras ratificadas (39.360 €) hasta que se ratifique | D-29 dejó el runner **ejecutable** en local, pero **implantarlo en una máquina nueva sigue siendo un procedimiento manual** descrito en un runbook. Hoy los ítems **6–7** del `pre-dev-checklist.md` (**CS-35** toolkit, **CS-36** pesos) se comprueban **a mano y sin dueño asignado**, y el hash de los pesos depende de que alguien lo anote. Con **más de una máquina objetivo** (desarrollo, demo sin coste cloud, contingencia si RunPod no está disponible — los tres usos que motivaron D-29) el runbook no escala: cada implantación repite las mismas comprobaciones y falla de formas distintas. Un preflight **ejecutable** convierte esas comprobaciones en **repetibles y auditables**, y la verificación SHA-256 cierra por construcción el hueco de integridad de los pesos. **No sustituye a CS-34**: la comprobación manual del entorno de referencia de los spikes sigue haciendo falta **una vez** (el instalador vive en F6; F2 arranca antes) | **Seguir con el runbook manual** de `T-85` (`runbooks/gpu-local-requisitos.md`): suficiente para una máquina y una persona; con varias, convierte cada instalación en una sesión de soporte y deja la integridad de los pesos al criterio del operador. **Instalador con GUI, auto-update o empaquetado firmado de Windows**: multiplica el coste sin resolver el problema real, que es el **preflight** — se declara delta aparte |

---

## 3. Arquitectura y componentes

### 3.1 Vista de conjunto

```
┌──────────────────────────────────────────────────────────────────┐
│  Next.js (App Router)  ·  UX derivada de Suno (D-12)             │
│  editor de letras · prompt de estilo · opciones de voz           │
│  biblioteca · reproductor · descargas · trazabilidad             │
│  admin: cuotas, gasto, modelos                                   │
└───────────────┬──────────────────────────────────────────────────┘
                │  HTTPS + JWT (Auth.js)         ▲ SSE/WebSocket (progreso)
                ▼                                │
┌──────────────────────────────────────────────────────────────────┐
│  FastAPI — API de orquestación                                   │
│  /generations · /models · /voices · /provenance · /library        │
│  validación · cuotas · rate limit · auditoría · tope de gasto     │
└───┬───────────────┬───────────────┬──────────────────────────────┘
    │               │               │
    ▼               ▼               ▼
┌────────┐   ┌────────────┐   ┌──────────────────┐
│Postgres│   │Redis + cola│   │Object storage S3 │
│metadata│   │  de jobs   │   │ FLAC/MP3/stems   │
└────────┘   └──────┬─────┘   └──────────────────┘
     │              │ dispatch                    ┌──────────────────┐
     └──────────────┼────────────────────────────►│ Bucket WORM      │
                    │                             │ ledger procedencia│
                    ▼                             └──────────────────┘
┌──────────────────────────────────────────────────────────────────┐
│  GPU Runner (pod con keep-warm 10 min · pod caliente en horario)  │
│  credenciales aisladas: URL firmada por trabajo (D-15)           │
│  ┌────────────────────────── MODEL REGISTRY ──────────────────┐  │
│  │ adapter: ace-step-1.5 │ heartmula │ (yue-7b) │ <propio-ft> │  │
│  │ solo safetensors (D-14)                                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│  post-proceso: ffmpeg (loudness/transcode) · Demucs (stems)      │
│                · SVC opcional (RVC v2 / YingMusic-SVC)           │
│  provenance + watermarking (⚠️ candidatos MIT por validar, I-13)  │
└──────────────────────────────────────────────────────────────────┘
```

### 3.2 Componentes

| Componente | Responsabilidad | Notas |
|-----------|-----------------|-------|
| **Web app (Next.js)** | Editor de letras con etiquetas de sección, prompt de estilo, selector de voz, biblioteca, reproductor, descargas, panel de procedencia, **panel de administración de cuotas y gasto** | Los formularios de parámetros se escriben **a mano por modelo** (2–3 formularios), no se generan desde `params_schema` (D-16). La disposición y los flujos se derivan del estudio de la UI de Suno (D-12) |
| **Auth (Auth.js)** | OAuth social y corporativo + credenciales + TOTP 2FA + códigos de recuperación + roles | Emite JWT verificado por FastAPI vía JWKS |
| **API de orquestación (FastAPI)** | Alta de trabajos, validación, cuotas y rate limit (§12.1), selección de modelo, estado, auditoría | Sin lógica de inferencia dentro |
| **Postgres** | Usuarios, proyectos, trabajos, generaciones, voces, modelos registrados, registros de procedencia y auditoría | El ledger de procedencia se replica al **bucket WORM** (D-18); Postgres es el índice consultable, no la fuente de verdad inmutable |
| **Redis + worker de cola** | Cola con prioridades, reintentos **idempotentes por clave**, cancelación, DLQ con runbook, cuarentena de *poison jobs* | `arq` o Celery |
| **GPU Runner** | Cargar pesos, ejecutar el adapter, post-procesar, subir artefactos, reportar telemetría | Caché de pesos **y de imagen de contenedor** en el host/volumen persistente (§9, S-01); credenciales aisladas (D-15) |
| **Object storage (S3-compatible)** | Artefactos con URLs firmadas, **ciclo de vida a almacenamiento frío**, retención con números y **GC de huérfanos** | Coste calculado en §12.2 y en `evaluation.md` §6.6 |
| **Servicio de procedencia y derechos** | Manifiesto por pista (estilo C2PA / Content Credentials), watermarking, certificado exportable JSON/PDF, cadena de hashes | Soporta C-10 y el gate de legal. El watermarking es **incógnita abierta** (I-13) |
| **Observabilidad y control de gasto** | Trazas OpenTelemetry, métricas de cola, **segundos de GPU y coste por generación**, **tope de gasto mensual + kill switch**, alertas con destinatario nombrado, SLO y error budget, **métrica de calidad en el tiempo** | El coste por pista y el gasto acumulado del mes deben ser visibles desde el día uno (§12.3) |
| **Pipeline de fine-tuning** (fase posterior) | Dataset con metadatos de licencia, captioning, entrenamiento, evaluación, promoción al registry | Fuera del camino crítico de la app |

### 3.3 Contrato del model registry pluggable

Es la pieza estructural de la plataforma. Un modelo **declara lo que sabe hacer** y la aplicación consulta esa declaración en lugar de nombrar modelos en la lógica de negocio.

**Descriptor del modelo** (dato, versionado y persistido):

```python
class ModelCapability(StrEnum):
    TEXT_TO_MUSIC       # prompt de estilo -> música
    LYRICS_TO_SONG      # letra + estilo -> canción cantada
    INSTRUMENTAL        # generación sin voz
    VOICE_CONDITIONING  # condicionar timbre/registro vocal
    STEM_OUTPUT         # entrega stems nativos
    SECTION_INPAINT     # regenerar un tramo concreto
    CONTINUATION        # extender una pista existente
    AUDIO_TO_AUDIO      # cover / remezcla sobre audio de entrada
    FINE_TUNABLE        # admite pesos derivados propios

class ModelDescriptor(BaseModel):
    id: str                          # "ace-step"
    version: str                     # "1.5.0"
    display_name: str
    weights_uri: str
    weights_format: Literal["safetensors"]  # D-14: nada más se acepta
    weights_sha256: str              # integridad (NO inocuidad)
    license: str                     # "Apache-2.0"
    commercial_use: bool
    training_data_declaration: str   # OBLIGATORIO; "no divulgada" es un valor válido y frecuente
    provenance: ProvenanceDeclaration # OBLIGATORIO: alimenta C-10
    capabilities: set[ModelCapability]
    params_schema: dict              # JSON Schema: valida en la API (NO genera la UI, D-16)
    limits: ModelLimits              # max_duration_s, sample_rate, channels
    hardware: HardwareProfile        # min_vram_gb, vram_confort_gb, gpu recomendada, s/min de audio
    status: Literal["experimental", "activo", "deprecado"]
```

**Interfaz del adapter** (comportamiento, estable):

```python
class MusicModelAdapter(Protocol):
    descriptor: ModelDescriptor

    async def load(self, ctx: RunnerContext) -> None: ...
    async def generate(self, req: GenerationRequest) -> GenerationResult: ...
    async def health(self) -> HealthStatus: ...
    async def unload(self) -> None: ...
```

```python
class GenerationRequest(BaseModel):
    lyrics: str | None
    style_prompt: str
    duration_s: int
    instrumental: bool
    voice: VoiceSpec | None          # preset de voz o referencia clonada
    source_audio: AudioRef | None    # cover / remezcla / continuación
    section_edit: SectionEdit | None # inpaint de un tramo [t0, t1]
    seed: int | None                 # trazabilidad, NO garantía de bit-reproducibilidad
    model_params: dict               # validado contra params_schema
    max_gpu_seconds: int             # presupuesto por trabajo
    idempotency_key: str             # reintentar no duplica artefactos

class GenerationResult(BaseModel):
    artifacts: list[AudioArtifact]   # flac, mp3, stems (wav a demanda, 48 kHz — D-23)
    provenance: ProvenanceRecord     # manifest_schema_version, modelo, versión, hash,
                                     # licencia, seed, entradas, lyrics_declaration (D-21),
                                     # source_generation (linaje, D-22)
    telemetry: RunTelemetry          # gpu_seconds, vram_peak, reintentos, coste
```

**Reglas del contrato (invariantes):**

1. Ningún identificador de modelo aparece en la lógica de negocio: la selección se resuelve contra **capacidades declaradas**. En fase 1 esa resolución es una **función trivial y explícita** (con un modelo activo, un `return`); el **router de capacidades con preferencias y fallback se construye cuando haya un tercer modelo** que lo justifique (D-16).
2. Añadir un modelo = **un adapter nuevo + su descriptor + pasar la suite de conformidad**. *(Corrección de la revisión 1: la afirmación «cero cambios en frontend» era **falsa**. Es cierta para un modelo que aporte capacidades **ya soportadas** por la UI. Un modelo que estrene `AUDIO_TO_AUDIO` o `SECTION_INPAINT` **necesita affordances de UI nuevas sí o sí** — subida de audio, selección de región sobre la forma de onda. El registry evita reescribir el backend; no hace magia en el frontend.)*
3. La UI conoce los parámetros de los modelos que soporta, con formularios escritos a mano y etiquetas de dominio. `params_schema` es la **validación de contrato en la API**, no un generador de interfaz (D-16).
4. Todo `GenerationResult` trae `provenance`, **en el formato v1 del manifiesto firmado por legal antes de implementar este contrato** (D-20, C-10a) y con **`manifest_schema_version` explícito**. Un adapter que no lo emita, o que lo emita en un esquema sin versión, no pasa la conformidad. *(Corrección de la revisión 3: esta regla obligaba a los adapters a emitir un formato que legal **no había firmado**, porque C-10 entera vivía en la Fase 2. C-10a se adelanta a la Fase 1 y su primera tarea es la firma del esquema.)*
5. `training_data_declaration`, `provenance` y `commercial_use` son **obligatorios**; un modelo con `commercial_use: false` (p. ej. cualquiera bajo CC BY-NC) es rechazado por el registry en producción. **Esta regla aplica también a las herramientas del pipeline**, no solo a los generadores: ver I-13 (licencia circular del watermarking) y **I-13b** (ficha de licencia verificada de **toda** herramienta del pipeline antes de la fase que la integra — pesos de Demucs, RVC, HeartCodec/HeartTranscriptor).
6. Los modelos propios fine-tuneados entran **por la misma puerta**, con `parent_model` y `dataset_id` en su declaración de procedencia.
7. Versionado inmutable: `id@version` nunca se reescribe; se publica una versión nueva. Las pistas antiguas siguen siendo auditables.
8. **Suite de conformidad por tolerancia perceptual** (D-13): el gate no compara muestras bit a bit. Comprueba (a) invariantes exactos — esquema, duración, sample rate, canales, loudness objetivo, ausencia de NaN/silencio, procedencia emitida, límites respetados; y (b) invariantes perceptuales sobre un conjunto de briefs fijos — **similitud CLAP audio-texto y WER de la letra cantada dentro de un umbral**, no iguales a un valor. La semilla se registra para trazabilidad, no como garantía de reproducibilidad bit a bit.
9. **Solo `safetensors`** (D-14). Un descriptor con otro formato se rechaza en el registro. El código de adapter de terceros se revisa antes de registrarse y corre sin credenciales persistentes.
10. **Aislamiento de credenciales** (D-15): el runner recibe URLs firmadas de alcance por trabajo y con caducidad corta. Ningún adapter puede leer artefactos de otro trabajo.

---

## 4. Flujo paso a paso (generación estándar)

1. El usuario se autentica (SSO social/corporativo o usuario+contraseña; 2FA si lo tiene activado).
2. Crea o abre un **proyecto**.
3. Escribe la **letra** con etiquetas de sección (`[verso]`, `[estribillo]`, `[puente]`), o la genera con el **asistente de letras** y la edita. **Declara la autoría/derechos de la letra** (propia · generada por el asistente · con permiso documentado): es **bloqueo duro** y queda en auditoría y en el manifiesto como `lyrics_declaration` (D-21).
4. Define el **prompt de estilo**, la **duración**, si es **instrumental**, el **destino** (broadcast / streaming / stems, que fija el objetivo de loudness, D-23) y las **opciones de voz** (preset de timbre/género/registro o voz propia).
5. `POST /generations` con `idempotency_key`. La API valida la petición, comprueba **cuota, concurrencia y profundidad de cola** (§12.1), valida `model_params` contra `params_schema` y resuelve el modelo por capacidades.
6. El trabajo entra en la cola en estado `queued`. La UI muestra posición y una **estimación de espera realista** (incluye arranque en frío si el pod está apagado; ~0 si está caliente).
7. La cola usa el **pod caliente** si está disponible; si no, provisiona uno **efímero** bajo demanda y carga los pesos desde caché (imagen y pesos ya cacheados en el host). Estado `starting`. **Despacho FIFO con fairness round-robin por usuario** (D-26). Tras el trabajo el pod queda **keep-warm 10 min**, de modo que las variantes 2..N son inmediatas.
8. **Inferencia** con presupuesto de `max_gpu_seconds`, reportando progreso. Estado `running`.
9. **Post-proceso**: normalización de loudness EBU R128 **al objetivo del destino** (broadcast −23 / streaming −14 / stems sin normalizar, D-23), codificación a **FLAC + MP3 320**, separación de stems si se pidió, pasada de conversión de voz si aplica. WAV solo si se solicita exportación, **resampleado a 48 kHz con soxr**.
10. **Procedencia**: se sella el **manifiesto v1** de la pista (con `manifest_schema_version`, `lyrics_declaration` y `source_generation`) y se **encadena su hash al ledger append-only** — esto ocurre **desde la primera pista de la Fase 1** (C-10a, D-20). La firma **C2PA**, el **object lock WORM** y el **watermarking** llegan en la Fase 2 (C-10b) y se aplican sobre el mismo manifiesto versionado, sin necesidad de backfill.
11. Subida de artefactos con **escritura en dos fases** (registro `pending` en Postgres → subida → confirmación) para que no existan ficheros huérfanos ni registros sin fichero. Estado `succeeded`.
12. Notificación al frontend por SSE/WebSocket; la pista aparece en la biblioteca.
13. El usuario escucha, descarga MP3/FLAC/stems (o WAV a 48 kHz a demanda), **comparte la URL de la pista en la aplicación** (requiere sesión; las URLs firmadas son solo el mecanismo interno del reproductor, D-24) o **itera**: extender, regenerar una sección, o generar una variante con otra semilla — **sin pagar arranque en frío**, gracias al keep-warm. Cada derivada nace con `parent_id`, `root_id` y `derivation_kind` (D-22), así que su manifiesto **referencia a su padre desde el primer día**.
14. Todo queda en el **registro de auditoría** (quién, cuándo, con qué modelo, qué coste de GPU) y el gasto se acumula contra el **tope mensual** (D-17).

---

## 5. Alcance

### 5.1 Dentro de alcance (características evaluadas)

Estas son las 10 características marcadas por el usuario más las **cuatro** transversales que su ejecución exige. **El reparto en fases y su coste están en [`evaluation.md`](./evaluation.md)**; esta spec no prejuzga qué entra en el primer entregable.

| ID | Característica | Origen |
|----|----------------|--------|
| C-01 | Generación a partir de letra + prompt de estilo | Usuario |
| C-02 | Instrumental sin voz | Usuario |
| C-03 | Selector de tipo de voz (timbre, género, registro) | Usuario |
| C-04 | Clonación de voz propia | Usuario |
| C-05 | Asistente IA de letras | Usuario |
| C-06 | Descarga de stems separados | Usuario |
| C-07 | Extender / regenerar secciones concretas | Usuario |
| C-08 | Cover / remezcla de una pista existente | Usuario |
| C-09 | Fine-tuning de modelos propios | Usuario |
| C-10 | Trazabilidad de licencias y derechos del audio generado | Usuario |
| C-11 | **Model registry pluggable** | Usuario (requisito de primer orden) |
| C-12 | **Autenticación**: SSO social + usuario/contraseña + 2FA configurable | Usuario (requisito explícito) |
| C-13 | **Cimientos de plataforma**: monorepo, cola de trabajos, storage, biblioteca, reproductor, CI/CD, IaC, observabilidad | Requisito implícito |
| C-14 | **Infraestructura GPU y orquestación de inferencia** | Requisito implícito |

Son **4 transversales** (C-11, C-12, C-13, C-14) y **10 del usuario** (C-01…C-10). *(La revisión 1 decía «tres transversales» y listaba catorce filas: corregido.)*

> **Revisión 3 — C-10 se parte en dos entregas (D-20).** Siguen siendo 14 características, pero C-10 se presupuesta y planifica como **15 fichas**: **C-10a** (38 h, **Fase 1**: esquema firmado por legal, emisión del manifiesto desde la primera pista, ledger append-only con cadena de hashes, invariante en CI, `manifest_schema_version`) y **C-10b** (67 h, **Fase 2**: C2PA real con custodia de clave en KMS, WORM con object lock, certificado PDF, watermarking condicionado a I-13). El total de C-10 no cambia: **105 h**. El motivo no es de coste, es de irreversibilidad: **una cadena WORM no admite backfill**.

> ⛔ **No-go vigente (2026-07-27, ratificado 2026-08-18)**: esta característica pertenece a la Fase 4, declarada no-go por falta de catálogo licenciado para fine-tuning y por riesgo RGPD de la clonación de voz (ver `evaluation.md` §9.2 y decision-brief). Los criterios de aceptación se conservan solo como pre-planificación; no planificar como ejecutable. Aplica a **C-04 (clonación de voz propia)** y **C-09 (fine-tuning de modelos propios)**; sus filas de §5.1 y sus criterios de §5.2 se leen bajo esta advertencia.

### 5.2 Criterios de aceptación por característica

La lista de §5.1 era un inventario, no un contrato. Estos son los criterios que hacen verificable cada entrega. Todos son condición de cierre, no de intención.

| ID | Criterio de aceptación (verificable) |
|----|--------------------------------------|
| C-01 | Dado un brief con letra etiquetada y prompt de estilo, se obtiene una pista de la duración pedida ±5 %, **loudness EBU R128 dentro de ±1 LU del objetivo del destino elegido** (broadcast −23 / streaming −14, D-23), en FLAC + MP3 320 —y en **WAV a 48 kHz** si se pide la exportación—, con **manifiesto v1 de C-10a completo** (`manifest_schema_version`, `lyrics_declaration`, `source_generation`) y **su hash encadenado al ledger**, en menos de 10 min de reloj p95 con pod caliente. **Sin `lyrics_declaration` no se encola nada** (bloqueo duro, D-21). Un fallo de inferencia se reintenta y **no** consume cuota. |
| C-02 | La misma petición con `instrumental: true` produce una pista **sin voz detectable** (verificado con separación de fuentes: energía de la pista vocal < umbral definido en el spike) y con valores por defecto propios de estilo. |
| C-03 | Existe un catálogo de ≥ 8 presets de voz, cada uno con audio de muestra escuchable en la UI, y el resultado de generar con un preset es reconocible como ese preset por 2 de 3 evaluadores en escucha ciega. Si no se alcanza, **se documenta la limitación en la UI** en lugar de prometerla. **Los presets se restringen a condicionamiento por etiquetas o por audio sintético del propio modelo**; si algún preset derivase de **grabaciones de voces reales**, la verificación documentada de derechos **por preset** es criterio de aceptación (y sin ella el preset no se publica). |
| C-04 | ⛔ **No-go vigente (Fase 4, ratificado 2026-08-18; ver la advertencia de §5.1)** — criterio conservado como pre-planificación. Sin consentimiento registrado (identidad, alcance, fecha, texto firmado) no se entrena ni se infiere. Una solicitud de borrado elimina audio original, dataset derivado **y pesos derivados**, verificado por prueba automatizada. DPIA archivada antes del primer entrenamiento. |
| C-05 | Genera letra estructurada con etiquetas de sección válidas para C-01, en streaming, con rate limit aplicado (§12.1) y coste de tokens registrado por usuario. **El prompt de sistema prohíbe reproducir letras existentes** y la salida se **valida como letra etiquetada parseable** por C-01 antes de ofrecerse; una salida no parseable se regenera, no se entrega. La letra generada por el asistente rellena `lyrics_declaration` automáticamente (D-21). |
| C-06 | Entrega 4 stems (voz, batería, bajo, otros) alineados con la mezcla ±10 ms, empaquetados, reproducibles en el reproductor multipista sincronizado, y **no se generan por defecto**. |
| C-07 | Regenerar una sección `[t0, t1]` devuelve una pista de la misma duración total, con el resto del audio **bit-idéntico fuera de la región** y un empalme que 2 de 3 evaluadores no identifican en escucha ciega. |
| C-08 | Ninguna pista de entrada se procesa sin declaración de titularidad registrada en auditoría con usuario, fecha y contenido. La declaración es un bloqueo duro, no una casilla. |
| C-09 | ⛔ **No-go vigente (Fase 4, ratificado 2026-08-18; ver la advertencia de §5.1)** — criterio conservado como pre-planificación. Un modelo entrenado se publica en el registry con `parent_model`, `dataset_id` y licencia de cada pista del dataset, pasa la suite de conformidad, y su evaluación se compara contra el modelo base con el protocolo de G1. Rollback en un paso. |
| **C-10a** (Fase 1) | **Legal ha firmado el esquema del manifiesto v1 antes de que se implemente C-11.** Ninguna pista puede existir sin manifiesto (invariante probado en CI), todo manifiesto lleva `manifest_schema_version`, y la **cadena de hashes del ledger append-only valida de extremo a extremo** desde la **primera** generación de la Fase 1. Existe un **verificador multi-versión** y un **test de CI con corpus de manifiestos** de todas las versiones emitidas. |
| **C-10b** (Fase 2) | El manifiesto se **firma con C2PA** (clave en **KMS gestionado**, rotación anual, revocación documentada), el ledger pasa a **bucket con object lock** y sello diario firmado **sin backfill** (los registros de Fase 1 ya están encadenados), el certificado se exporta en **JSON y PDF**, y **ninguna pista puede existir sin watermark** (invariante en CI) — esto último **condicionado a I-13**: si no hay librería con licencia comercial limpia, el invariante se replanifica y se declara. |
| C-11 | Dos adapters registrados pasan la suite de conformidad perceptual; un tercer adapter ficticio con `commercial_use: false` es **rechazado**; un descriptor con pesos no-`safetensors` es **rechazado**; un descriptor sin `manifest_schema_version` en su `provenance` es **rechazado** (regla 4); el runner no puede acceder a artefactos de otro trabajo (prueba negativa). **El adapter de HeartMuLa no se da por entregado hasta pasar G1-bis** (mismo protocolo que G1, D-27), y existe la **matriz de capacidades verificadas** del spike (`SECTION_INPAINT`, `AUDIO_TO_AUDIO`, `VOICE_CONDITIONING`, `CONTINUATION`) con evidencia por modelo, no declaración del README del modelo. |
| C-12 | Las dos vías de acceso funcionan, el 2FA es activable y desactivable con reautenticación, existen códigos de respaldo de un solo uso y un flujo de recuperación probado, y FastAPI rechaza JWT inválidos o caducados. |
| C-13 | Un `docker compose up` (o equivalente) levanta el entorno completo; CI ejecuta pruebas y despliega a `stage`; existe traza OTel de extremo a extremo de una generación con `gpu_seconds` y coste; la biblioteca lista, filtra y reproduce. **El esquema modela linaje desde la primera migración** (`parent_id`, `root_id`, `derivation_kind`, `section_map` nullable — D-22) con prueba de que una derivada referencia a su padre; **exporta WAV a 48 kHz** con resample soxr y aplica el objetivo de loudness por destino (D-23); **compartir devuelve la URL de la pista en la aplicación**, no una URL firmada (D-24); la UI arranca con `next-intl` y **ninguna cadena hardcodeada** (D-25). Al cierre de C-13 se ejecuta el **checkpoint de stop-loss** con el runbook de desmantelamiento escrito (D-28). |
| C-14 | Con el proveedor primario caído, el circuit breaker conmuta al secundario sin pérdida de trabajos; un trabajo que excede `max_gpu_seconds` se aborta con coste registrado; el tope de gasto mensual dispara el kill switch en pruebas. |

### 5.3 Fuera de alcance

- **SaaS público** (fase 2): multi-tenancy real, facturación, planes, alta autoservicio, moderación a escala, protección antiabuso.
- Aplicaciones móviles nativas.
- Mastering profesional, mezcla tipo DAW, edición multipista.
- Generación de vídeo o videoclip.
- Colaboración multiusuario en tiempo real sobre el mismo proyecto.
- **Integración con MAM u otros sistemas internos de Daycry** → incógnita I-04, no presupuestada.
- Distribución o publicación del audio en plataformas de streaming.
- Cualquier modelo con licencia no comercial (MusicGen Stereo, CC BY-NC).
- **Réplica de la identidad visual de Suno** (D-12b): se deriva la UX, no la marca.
- **Filtro automático de similitud de la letra** contra corpus de letras con copyright: **mejora futura no bloqueante** (Fase 3 o posterior). El bloqueo de la Fase 1 es la **declaración** de derechos (D-21), no la detección automática.
- **Conformidad WCAG AA** (D-25): explícitamente **no es objetivo de la Fase 1** con 5 usuarios internos. Se construye con componentes accesibles por defecto y la deuda queda registrada para el caso de que se active la fase 2 SaaS.
- **Tercer adapter (YuE 7B) y router de capacidades**: **partida condicional de Fase 2** (≈ 50 h, no presupuestada aquí), solo si G1-bis muestra adherencia a la letra insuficiente (D-06, D-16). **🆕 MiniMax-Music3 se apunta como candidato condicional adicional** (§11.1), sujeto a dictamen de legal sobre su Community License — no presupuestado, no sustituye a YuE.
- **Idiomas de la UI distintos del castellano** (I-19).

---

## 6. Manejo de errores

| Clase de error | Detección | Respuesta |
|----------------|-----------|-----------|
| Validación de entrada | Pydantic + JSON Schema del modelo | 422 con el campo concreto; nada se encola |
| Cuota agotada | Contador por usuario/mes (§12.1) | 429 con la fecha de reinicio y la cuota restante |
| Cola demasiado profunda / concurrencia excedida | Límites de §12.1 | 429 con la espera estimada; el trabajo **no** se encola |
| Modelo sin la capacidad pedida | Resolución por capacidades | 409 explicando qué capacidad falta y qué modelos sí la tienen |
| Modelo no apto comercialmente | Regla 5 del contrato | Rechazo en el registry; nunca llega a producción |
| Pesos en formato no permitido | Regla 9 (D-14) | Rechazo en el registro del modelo, con motivo explícito |
| Arranque en frío excedido | Timeout de aprovisionamiento | Reintento en otro proveedor/región; aviso en UI; **la cuota no se consume** |
| Falta de VRAM (OOM) | Excepción del runner | Reintento con offloading / menor duración; si persiste, se enruta a GPU mayor y se registra |
| **GPU local sin VRAM suficiente** (D-29, modo `gpu-local`) | Detección de GPU/VRAM al arrancar el contenedor | **Arranque fallido con mensaje claro** (nunca silencioso): VRAM detectada, mínimo requerido (8 GB suelo) y, si hay un proveedor cloud configurado (`GPU_PROVIDER=runpod`), la opción explícita de enviar el trabajo allí en su lugar |
| Fallo del modelo o artefactos corruptos | Validación de salida (duración, silencio, sample rate, NaN) | Reintento con semilla nueva (máx. 2); si persiste, `failed` con diagnóstico |
| Presupuesto de GPU por trabajo excedido | `max_gpu_seconds` | Aborto controlado, artefacto parcial descartado, coste registrado |
| **Tope de gasto mensual alcanzado** | Contador agregado de coste (D-17) | **Kill switch**: se pausa el despacho, se apagan los pods, alerta al responsable nombrado. Los trabajos quedan `queued`, no `failed` |
| Proveedor de GPU caído | Circuit breaker por proveedor | Conmutación al proveedor secundario; degradación anunciada |
| Fallo de almacenamiento | Reintento con backoff | Artefacto retenido en el runner hasta confirmación; sin pérdida silenciosa |
| **Inconsistencia de doble escritura** (artefacto en S3 + fallo al escribir en Postgres) | Escritura en dos fases + **reconciliación diaria** | La clave de S3 se deriva del `job_id`, así que la reconciliación es determinista: fichero sin registro → **GC de huérfanos**; registro `pending` caducado → limpieza. Sin esto se pagan para siempre ficheros que nadie ve |
| **Trabajo veneno** (*poison job*): falla siempre y bloquea la cola | Contador de fallos por `idempotency_key` y por hash de parámetros | Cuarentena tras 3 intentos; no se reencola automáticamente; entra en DLQ etiquetado como veneno |
| **DLQ acumulada** | Alerta por profundidad de DLQ | **Runbook de reproceso** documentado: inspección, corrección, reproceso idempotente por lotes, límite de reintentos manuales, registro de quién reprocesó qué |
| **Cancelación de un trabajo** | Acción de usuario o del sistema | Regla declarada: los `gpu_seconds` consumidos **hasta el aborto siempre se registran e imputan al proyecto**. Consumen **cuota del usuario prorrateada** solo si la cancelación es del usuario; si la cancela el sistema, no |
| Audio de entrada con derechos dudosos (C-08) | Gate de derechos en la ingesta | Bloqueo con requerimiento de declaración de titularidad |
| **Letra sin declaración de autoría/derechos (C-01)** | **Gate de derechos de la letra** (D-21): `lyrics_declaration` ausente o incompleta | **422 y bloqueo duro: nada se encola.** La declaración (propia · generada por el asistente · con permiso documentado) se registra en auditoría con usuario, fecha y contenido, y viaja en el manifiesto. *Hueco cerrado en la revisión 3: C-08 tenía gate y C-01 no, de modo que una letra con copyright producía una obra derivada con manifiesto impecable sobre un input infractor* |
| **Salida del asistente de letras no parseable (C-05)** | Validación de la letra etiquetada contra el parser de C-01 | Regeneración automática (máx. 2); si persiste, se devuelve el texto **sin** ofrecerlo como letra válida para generar |
| Falta de consentimiento de voz (C-04) | Gate de consentimiento | Bloqueo; sin consentimiento registrado no se entrena ni se infiere |

Principios: **idempotencia por `idempotency_key`**, reintentos con backoff exponencial, DLQ con alerta y runbook, ningún fallo de infraestructura consume cuota de usuario, ninguna escritura parcial queda invisible, y todo error visible al usuario lleva el `job_id` para soporte.

---

## 7. Pruebas

| Nivel | Qué se prueba | Notas |
|-------|---------------|-------|
| Unitarias | Esquemas, resolución por capacidades, cuotas, cálculo de coste, manifiesto de procedencia, cadena de hashes del ledger | Rápidas, sin GPU |
| **Suite de conformidad de adapters** | Invariantes **exactos** (esquema, duración, sample rate, loudness, procedencia, límites, formato de pesos) + invariantes **perceptuales** (CLAP y WER dentro de umbral sobre briefs fijos) | **Gate obligatorio** para registrar un modelo. **No** compara muestras por semilla fija: la inferencia de difusión en GPU no es bit-reproducible entre versiones de driver/cuDNN/kernels (D-13) |
| Contrato API ↔ frontend | Tipos generados desde OpenAPI; `params_schema` validado en la API | Evita deriva |
| Integración | Ciclo completo con GPU real, incluyendo keep-warm y arranque en frío | Nocturno, con presupuesto de GPU acotado |
| **Evaluación de calidad (Gate G1 y G1-bis)** | Protocolo escrito con rúbrica, escala, número de pistas, evaluadores y umbral; línea base ciega contra **Suno** y contra **la librería de producción que se usa hoy**; métricas objetivas CLAP y WER (HeartTranscriptor) | Es el **gate de decisión** sobre si el open source alcanza el nivel exigible. **G1 evalúa solo ACE-Step** (es el único modelo contenerizado en la Fase 0); **HeartMuLa pasa G1-bis** con el mismo protocolo al registrarse su adapter en la Fase 1 (D-27). Protocolo completo en `evaluation.md` §10.2 |
| **Regresión de manifiestos multi-versión** | Un **verificador** valida manifiestos de **todas** las versiones de esquema emitidas, con un **corpus de manifiestos** en CI (uno por versión) | Sin esto, subir `manifest_schema_version` rompe la verificación de las pistas antiguas — que es justo lo que el ledger promete que no pasará (C-10a, D-20) |
| **Concurrencia en una sola GPU** | ¿Caben **2 inferencias simultáneas** en los 48 GB de la L40S sin degradar el tiempo por pista? | Medido en el spike de la Fase 0 (+3 h). Si caben, el throughput se dobla **a coste cero** y la espera de §12.1 se parte por dos |
| Seguridad | Autorización por proyecto, 2FA, URLs firmadas, subida de audio (tipo/tamaño/contenido), **prueba negativa de aislamiento de credenciales del runner**, rechazo de pesos no-`safetensors` | |
| Privacidad / RGPD | Borrado efectivo de una voz, de su dataset y de **sus pesos derivados**; retención; exportación | Crítico para C-04 |
| Regresión de procedencia | Ninguna pista puede existir sin manifiesto ni sin watermark; la cadena de hashes del ledger valida de extremo a extremo | Invariante de producto |
| Resiliencia y coste | Caída de proveedor, DLQ y reproceso, *poison job*, doble escritura interrumpida, **disparo del tope de gasto** | Verifica §6 con fallos inyectados |
| Carga y latencia | Cola con 5 usuarios × 20 trabajos, paralelismo de pods, esperas prometidas vs. reales | Valida los números de §12.1 |

---

## 8. Decisiones confirmadas por el usuario (2026-07-27)

| # | Confirmación |
|---|--------------|
| 1 | El motor será **open source self-hosted**, con **model registry pluggable** para incorporar modelos propios fine-tuneados. Es un **requisito de primer orden**, no un extra. |
| 2 | Stack: **Next.js** (frontend) + **Python/FastAPI** (backend de orquestación de inferencia GPU). |
| 3 | **Fase 1: uso interno de Daycry.** Fase 2 (SaaS público) fuera de alcance ahora, pero el diseño no debe cerrarle la puerta. |
| 4 | Volumen fase 1: **100–1.000 generaciones/mes**. Usuarios fase 1: **1–5**. |
| 5 | **Infraestructura sin decidir.** El usuario pide expresamente que la evaluación **compare** GPU cloud on-demand vs. on-premise vs. cloud corporativo y **recomiende** una para este volumen, valorando si una GPU dedicada 24/7 está justificada. |
| 6 | **Autenticación**: SSO con redes sociales **y** usuario+contraseña, con **2FA configurable**. Ambas vías. |
| 7 | **Sin fecha comprometida.** La fecha 31/07 era un placeholder; el calendario sale de la estimación, por fases. |
| 8 | **Tarifa de desarrollo: 50 €/h**, confirmada. |
| 9 | Alcance declarado de fase 1: las **10 características** C-01 a C-10. *(La evaluación cuestiona que las 10 quepan en una fase 1 y propone una segmentación; la decisión es del usuario.)* |
| 10 | **Hardware de ACE-Step**: funciona «perfecto» en **RTX 4090 / 5090**, con **24 GB de VRAM recomendados**; también funciona con menos VRAM usando **offloading**, a costa de velocidad. Se traduce en: 8 GB es el **suelo** (con offloading), **24 GB es la cifra de confort** para canciones completas. Obliga a revisar la elección de GPU (§11.3 y `evaluation.md` §6.2). |
| 11 | **La interfaz debe ser «como Suno»**: la UX de Suno es la referencia del frontend y en la fase de implementación se hará un **estudio guiado de su interfaz usando el navegador** (Claude in Chrome) para derivar flujos, estados y disposición. Ver D-12 y D-12b (se deriva la UX, no la identidad visual). |
| **12** | **GPU local, además de cloud (2026-08-18).** El runner debe poder ejecutarse también **en local, usando la GPU del propio ordenador donde arranca la plataforma**, no solo en RunPod. Hardware de referencia: **RTX 4090/5090 (24 GB)**; **8 GB es el mínimo con offloading** (coherente con D-06). Ver D-29. Ampliación de alcance registrada en el changelog (§13), con `T-85` en `tasks.md` — **ratificada económicamente el 2026-08-18** (el delta de +960 € pasa a formar parte de los 39.360 € ratificados de Fase 0+1). |
| **13** | **Fase 0 en modo GPU local preferente (2026-08-18, misma fecha).** Los spikes de la Fase 0 (`T-03`–`T-08`) y la generación de las 10 pistas del gate G1 (`T-09`) se ejecutan preferentemente en una GPU local (≥ 8 GB, D-29) para eliminar el coste cloud de esa fase. **Excepción:** la medición de arranque en frío (S-01/S-01b: scheduling, pull de imagen, pesos) no se puede reproducir en local y sigue midiéndose contra el pod real de RunPod. `T-85` (proveedor GPU local de producción con abstracción completa de `GPU_PROVIDER`) no se adelanta: sigue en F6 con sus dependencias — la Fase 0 usa `docker run --gpus all` directo sobre el contenedor de `T-05`, sin esa capa de abstracción. |

---

## 9. Supuestos

| # | Supuesto | Impacto si es falso |
|---|----------|--------------------|
| S-01 | **Arranque en frío del pod GPU: 2–6 min con imagen de contenedor cacheada en el host; 5–12 min en el peor caso.** Desglose para ACE-Step 1.5 (~7 GB en fp16): scheduling 10–60 s + **pull de imagen CUDA+torch de 8–15 GB → 120–300 s si no está cacheada (término dominante)** + descarga de pesos 60–120 s + contexto CUDA y carga a VRAM 30–60 s + warm-up de kernels 30–120 s. *(La revisión 1 decía 1–3 min: era optimista ~2×.)* Mitigado por keep-warm y pod caliente (D-05b) | Sin keep-warm, el usuario paga el arranque en frío en **cada** variante de una iteración de 5–10. Es un problema de UX, no de coste (§6.4 de la evaluación) |
| S-01b | **La imagen del contenedor está cacheada en el host**, no solo los pesos en volumen persistente | Es el término dominante del arranque en frío. La revisión 1 cacheaba los pesos y **no la imagen**: hueco concreto que C-14 debe cerrar |
| S-02 | Tiempo de GPU medio por pista entregada de **150 s** (incluye reintentos y post-proceso), con ACE-Step 1.5 en GPU de ≥ 24 GB en torno a 90 s | Todo el cálculo de coste de inferencia escala linealmente con este número. **Debe medirse en el spike.** Con 8 GB y offloading el tiempo sube de forma material |
| S-02b | **El factor de sobrecoste de facturación es 1,90×**, no 1,60×. Fórmula: `factor = (150 s de trabajo útil + arranque + 15 s de cierre) / 150 s`. Con 75 s de arranque → 1,60× (extremo optimista); con **120 s → 1,90×**; con 300 s → 3,10×. **Aclaración (2026-09-01):** los 150 s de S-02 ya **incluyen reintentos y post-proceso**; S-02b los usa como denominador de «trabajo útil» por **convención conservadora** — al llevar el denominador esos componentes, el factor de sobrecoste queda **sobrestimado, nunca subestimado**. Ambos supuestos son coherentes sin cambiar los números | Mueve el coste mensual de 48 € a 58 € o 94 € a 1.000 gen/mes: **irrelevante para el presupuesto, material para la UX** |
| S-03 | La calidad de ACE-Step 1.5 / HeartMuLa alcanza el nivel utilizable en producción audiovisual | Si no, la iniciativa entera se replantea; es el gate G1 |
| S-04 | Hay al menos un perfil full-stack senior disponible que domine **Next.js + FastAPI + CUDA + DSP de audio + procedencia legal**. Ese perfil combinado es **raro** | Riesgo de persona clave: ver I-01 y R-15. **El calendario está condicionado a resolver I-01**; hoy no hay respuesta a «quién lo hace» |
| S-05 | Los pesos Apache 2.0 pueden desplegarse en la infraestructura elegida sin restricción contractual adicional | Bloqueante |
| S-06 | Legal aceptará el audio generado en producciones con un registro de procedencia adecuado, **aun sabiendo que la declaración de datos de entrenamiento de ACE-Step y YuE es «no divulgada»** | Sin este visto bueno la plataforma no entra en producción. **Por eso G2 se consulta antes de gastar** (§1.1) |
| S-07 | No hay requisito de integración con MAM en fase 1 | Añade esfuerzo no presupuestado |
| S-08 | El coste de tokens del agente IA está **verificado el 2026-07-27** (Claude Opus 5, **5 $/M input · 25 $/M output**, escrito en `.claude/rates.json`). Coste calculado en `evaluation.md` §9.1: **959 € base / 1.151 € con margen** *(revisión 3; la revisión 2 daba 938 € / 1.126 € sobre 1.566 h)* | Ninguno: es un dato, no un supuesto. Si el precio cambiase, el coste escala linealmente y sigue siendo ≈ 1,2 % del coste humano |
| S-09 | **El almacenamiento crece de forma acumulativa y sin techo natural**: con stems por defecto y 1.000 gen/mes supera el coste de GPU en el **mes 10 frente a la GPU efímera a 48 €/mes** (opción B, factor 1,6×); **frente a la opción G recomendada de 128 €/mes, en torno al mes 25** | Obliga a política de retención, ciclo a frío y GC desde el día uno (§12.2). La base importa: con la postura recomendada el cruce está fuera del horizonte de la Fase 1 |
| S-10 | El watermarking robusto a transcode a MP3 320 era **trabajo de nivel investigación** sin librería identificada. **Actualización 2026-08-18:** hay **dos candidatos con licencia MIT** (SilentCipher, AudioSeal); el supuesto «nivel investigación» solo vuelve a aplicar si la prueba de robustez sobre música (F10/`T-57`) falla en ambos | Ver I-13. No se debe presupuestar como «un componente» hasta verificar robustez y licencia del candidato elegido |
| **S-11** | **Las ~40 pistas de los spikes y de G1** (≈ 20 propias + 10 de Suno + 10 de librería) viven en una **carpeta segregada de evaluación**, con **retención de 12 meses** y **manifiesto retroactivo simplificado solo para las 20 propias**; las de Suno y de librería **no se usan en ninguna producción** y su uso como línea base exige **verificar los ToS de Suno** (junto con los del estudio de UI de D-12) en la semana de G2 (**2 h de legal, dentro de las 32 h de §6.5d de la evaluación**) | Si los ToS no permiten el uso como línea base comparativa, G1 pierde una de sus dos referencias y hay que rediseñar el protocolo **antes** de escuchar, no después |
| **S-12** | **Un pod caliente cubre la demanda de 1–5 usuarios en horario**; el trabajo que lo desborda va a un **segundo pod efímero** y **paga arranque en frío (2–6 min)**, lo que se muestra en la espera estimada de la UI | Si la demanda real exige dos pods calientes, el coste de GPU pasa de ≈ 128 € a ≈ 256 €/mes: sigue siendo ruido presupuestario, pero hay que decirlo antes, no facturarlo después |

## 10. Incógnitas (bloquean o condicionan la estimación)

| # | Incógnita | Qué desbloquea | Criticidad |
|---|-----------|----------------|-----------|
| ~~I-01~~ | ~~**¿Quién ejecuta esto?** Tamaño y composición del equipo. ¿Hay un ML engineer? ¿Hay más de una persona?~~ | ✅ **CERRADA el 2026-09-01** (decisión del propietario: proyecto personal en solitario): **el equipo es el propietario en solitario, con la IA como multiplicador**. Consecuencia: **el calendario pasa a ser orientativo**, no compromiso — las fechas de `evaluation.md` §9.4 siguen siendo ilustrativas, ahora por diseño | — |
| I-02 | **¿Tiene Daycry GPUs propias o capacidad GPU en su cloud corporativo?** | Cierra la decisión de infraestructura | Alta |
| I-03 | **¿Existe catálogo musical licenciado y con derechos de entrenamiento?** | **Bloquea C-09 por completo**: sin dataset no hay fine-tuning, y sin C-09 no hay procedencia limpia. **C-09 no está solo «bloqueada»: la Fase 4 (C-09 + C-04) está en no-go decidido** (2026-07-27, ratificado 2026-08-18 — `evaluation.md` §9.4/§10.1, decision-brief); resolver I-03 es precondición de una **nueva evaluación**, no de planificar | Crítica |
| I-04 | **Integración con MAM u otros sistemas internos**: ¿obligatoria en fase 1? | Alcance y esfuerzo adicional | Media |
| I-05 | **Posición de legal sobre la procedencia del audio generado** con modelos cuya declaración de datos de entrenamiento es «no divulgada» | **Gate G2, ahora en la semana 0.** Es la única incógnita capaz de anular el 100 % del presupuesto | Crítica |
| **I-05b** | **¿Es protegible y licenciable en exclusiva el output generado por IA sin autoría humana?** En la UE, la música sin intervención autoral humana puede **carecer de protección**: un cliente que exige exclusividad **no la puede obtener** sobre una obra no protegible | **Segunda pregunta del gate G2** (misma consulta, mismas 32 h de legal). Condiciona qué se le puede prometer contractualmente a un cliente, con independencia de la respuesta a I-05 | **Crítica** |
| ~~I-06~~ | ~~Precio vigente de tokens del modelo IA~~ | ✅ **CERRADA el 2026-07-27**: precio verificado **5 $/M input · 25 $/M output** (Claude Opus 5) y escrito en `.claude/rates.json`. Coste en `evaluation.md` §9.1: **959 € base / 1.151 € con margen** | — |
| I-07 | Tiempos reales de inferencia por modelo y por GPU, **y consumo de VRAM pico con y sin offloading** | Precisión del coste de infraestructura y elección de GPU | Alta |
| I-08 | Precio real de object storage del proveedor elegido, egress y política de retención corporativa | Coste operativo a 24 meses (§12.2 lo calcula a tarifa S3 estándar de referencia) | Media |
| I-09 | Latencia máxima aceptable de extremo a extremo | Valida o invalida S-01 y la postura de GPU | Media |
| I-10 | ¿Hay política corporativa que exija watermarking obligatorio? | Prioridad de C-10 y del componente de marca | Media |
| I-11 | Presupuesto máximo aprobado para la iniciativa | Determina la segmentación en fases. **🆕 Nota (2026-09-01, modo personal):** **el presupuesto lo decide el propietario**; las cifras en € de la evaluación (39.360 €, 98.280 €…) son **informativas** en modo personal — equivalencias de esfuerzo a tarifa de referencia, no partidas aprobadas por terceros | Alta |
| I-12 | Idiomas requeridos para el canto | Elección de modelo (HeartMuLa destaca en multilingüe) | Media |
| I-13 | **¿Qué librería de watermarking de audio es robusta a transcode a MP3 320 y tiene licencia comercial limpia?** Varios watermarkers open source de referencia tienen términos restrictivos (en algunos casos pesos con cláusula no comercial) que hay que verificar contra la **regla 5 del propio registry**. **🆕 Hallazgo 2026-08-18 (verificado contra fuentes primarias):** dos **candidatos** con licencia limpia — **SilentCipher** (Sony, github.com/sony/silentcipher · huggingface.co/Sony/SilentCipher, **MIT** código y pesos, 44,1 kHz, umbral psicoacústico, robusto a MP3/OGG/AAC, mensaje de 40 bits) y **AudioSeal** (Meta, github.com/facebookresearch/audioseal, **MIT** incluidos los pesos desde abril 2024, detector rápido, pensado para voz — robustez en música por validar). **No cierra I-13**: falta la prueba de robustez sobre música transcodificada, prevista en F10 (`T-57`) | D-10 y C-10. **Riesgo de licencia circular**: ya no es «sin solución identificada» — es «candidatos con licencia MIT, robustez en música por validar» | **Alta** |
| I-14 | **Precio de una GPU cloud de 24 GB (RTX 4090/5090) en el proveedor elegido** | Elección de GPU: la L40S de 48 GB sirve pero probablemente está sobredimensionada para ACE-Step solo | Media |
| I-15 | **Plan de entornos** dev/stage/prod: ¿cuántos, dónde y con qué coste? | Coste de infraestructura no-GPU, hoy sin presupuestar | Media |
| ~~I-16~~ | ~~**¿Quién es el propietario operativo tras la entrega?** Guardias, actualizaciones, respuesta a alertas~~ | ✅ **CERRADA el 2026-09-01** (decisión del propietario: proyecto personal en solitario): **propietario operativo = el propietario** (`gates/gobernanza.md` §6.1). El OPEX (≈ 15 %/año del build) es su tiempo; la cifra se conserva como referencia informativa para el gate de comercialización GC-01 | — |
| I-17 | Política corporativa de retención de logs y de datos personales | Configuración de observabilidad y RGPD | Media |
| ~~I-18~~ | ~~**Tarifa interna de las horas de no-desarrollo**: supervisor musical, legal, DPO~~ | ✅ **CERRADA el 2026-09-01**: **N/A en modo personal** (decisión del propietario: proyecto personal en solitario) — no hay tarifa interna que imputar; las horas de no-desarrollo de `evaluation.md` §6.5(d) son tiempo del propietario. Las consultas legales reales (de pago) renacen en el gate de comercialización **GC-01** (`gates/gobernanza.md` §8a/§8b) | — |
| **I-13b** | **Ficha de licencia verificada de TODA herramienta del pipeline**, no solo de los generadores: **pesos de Demucs** (código MIT pero **modelos con términos no comerciales** que hay que leer), **RVC** (licencia confusa), **HeartCodec / HeartTranscriptor**, ffmpeg y sus codificadores. **🆕 Hallazgo 2026-08-18 (confirmado, issue #327 de `facebookresearch/demucs`):** los pesos preentrenados de Demucs (`htdemucs`/`htdemucs_ft`/`htdemucs_6s`) son **CC-BY-NC 4.0** — el código es MIT pero los pesos **no** permiten uso comercial. C-06 tal como está descrita **no puede lanzarse comercialmente con esos pesos**. Candidatos alternativos por verificar peso a peso: **MDX-Net (UVR5)**, variantes **Mel-Band RoFormer** con pesos MIT (p. ej. `silverdaw/mel-band-roformer-vocals-onnx` en HF; muchos pesos RoFormer de la comunidad no declaran licencia) | La **regla 5** del registry aplica al pipeline completo. Cada fase se abre con la ficha de las herramientas que integra (**4–6 h por fase**, dentro de las horas de la característica que las integra): C-06 → Demucs (**bloqueado por el hallazgo anterior**, pendiente elegir alternativa); C-10b → watermarker; C-03/C-04 → RVC/YingMusic; C-07 → HeartTranscriptor | **Alta** |
| **I-19** | **Idiomas de la interfaz** más allá del castellano: ¿catalán? ¿inglés? | Alcance de i18n en Fase 2. La Fase 1 arranca en castellano con `next-intl` (D-25), así que añadir un idioma es traducir, no refactorizar | Baja |
| ~~**I-20**~~ | ~~**¿Quién es el supervisor musical nombrado y quiénes son los 3–5 usuarios piloto** con ≥ 2 h/semana comprometidas?~~ *(Avance parcial histórico 2026-08-18: el entonces responsable asumió supervisor musical; faltaban 2 de 3 evaluadores y los pilotos)* | ✅ **CERRADA el 2026-09-01** (decisión del propietario: proyecto personal en solitario): **evaluador único y usuario piloto = el propietario** — ver `gates/gobernanza.md` §2–§3 (`T-02` completado). El protocolo numérico de G1 se conserva íntegro (7/10 ≥ 4/5, WER ≤ 15 %) y G3 se reinterpreta en modo solo sin degradar su función. La versión corporativa (3 evaluadores, 3–5 pilotos con ≥ 2 h/semana) se conserva en el gate de comercialización **GC-01** (`gates/gobernanza.md` §8g) | — |
| ~~**I-21**~~ | ~~¿Qué GPU (modelo y VRAM real) tiene la máquina local objetivo del modo `gpu-local` (D-29)?~~ **✅ CERRADA 2026-09-01**: la máquina de desarrollo y de los spikes es el PC actual del propietario (Windows) — **NVIDIA GeForce GTX 1070, 8 GB de VRAM** (confirmado con `Win32_VideoController`; driver NVIDIA aún sin instalar). **Justo en el suelo de D-06/D-29: viable con offloading OBLIGATORIO.** Matices: arquitectura Pascal (2016, sin tensor cores, BF16 no soportado) — los tiempos por pista quedarán muy por encima de la referencia de S-02 (150 s, calibrada para L40S/RTX 4090); `T-03` medirá la cifra real y, si resulta impracticable, RunPod queda como camino de medición (ítems 8–9 del checklist). El despliegue final puede quedarse en esta máquina o ir a otra (portabilidad: instalador D-30/`T-86`) | Condiciona si el offloading automático se activa por defecto y si S-02/S-02b (tiempo y coste por pista) aplican tal cual o degradan en ese modo | Alta |
| **I-22** | **¿Qué sistemas operativos y máquinas son exactamente el objetivo del instalador (D-30)?** ¿**Linux nativo**, **Windows 11 + WSL2**, ambos? Y, ligada a ella: **¿quién mantiene el instalador tras la entrega** (nuevos drivers, nuevas versiones del toolkit, nuevos hashes de pesos)? — enlaza con **I-16** (propietario operativo) | **Condiciona directamente el esfuerzo del preflight y de las pruebas en máquina limpia de `T-86`**: con un solo SO la tarea cae en la parte baja del rango estimado (24 h); con Linux **y** Windows+WSL2 sube a la alta (40 h), por el paso de GPU a través de WSL2, rutas/permisos distintos y una segunda ronda de pruebas manuales. Mientras siga abierta, la estimación asume el supuesto **conservador de dos SO** (32 h). **🆕 2026-09-01: la máquina de desarrollo es Windows (decisión del propietario), así que el camino Windows 11 + Docker Desktop/WSL2 es el PRIMERO a soportar** — el supuesto de dos SO deja de ser conservador y pasa a ser el caso probable si el despliegue final acaba en Linux. El segundo tramo condiciona además si el instalador es un entregable **mantenido** o un artefacto de un solo uso | **Alta** |

---

## 11. Referencias

### 11.1 Modelos de generación musical open source (investigación julio 2026)

| Modelo | Params | Licencia | VRAM mín. | VRAM de confort | Arquitectura | Fuerte en |
|--------|--------|----------|-----------|-----------------|--------------|-----------|
| **ACE-Step 1.5** | 3,5B | Apache 2.0 | **8 GB (suelo, con offloading → más lento)** | **24 GB** (RTX 4090 / 5090: rendimiento «perfecto» según el usuario) | LM-planner + diffusion-renderer híbrido | Mejor punto de partida local generalista; iteración rápida, estilo dirigible |
| **HeartMuLa** | ~3B | Apache 2.0 | 10–12 GB (con HeartCodec cargado) | 16–24 GB | Music LM condicionado a letra + tags | Multilingüe (casi todas las lenguas). Familia: **HeartCodec** (codec 12,5 Hz), **HeartTranscriptor** (transcripción de letra, base Whisper), **HeartCLAP** (alineamiento audio-texto) |
| **YuE 7B** | 7B | Apache 2.0 | 16 GB | 24 GB+ | LM autorregresivo sobre tokens de codec | Canciones completas con letra, 3–5 min, 44,1 kHz estéreo; mejor adherencia a la letra, inferencia lenta |
| **DiffRhythm 2** | — | Apache 2.0 | — | — | Block Flow Matching | Lo más novedoso arquitectónicamente del catálogo 2026; síntesis rápida |
| **MusicGen Stereo** | — | **CC BY-NC (NO comercial)** | 12 GB | — | — | Loops cortos de fondo. **Descartado por licencia** (confirmado de nuevo el 2026-08-18) |
| **Stable Audio Open 1.5** | — | — | 12 GB | — | — | Diseño sonoro y texturas; límite de 47 s por muestra |
| **🆕 MiniMax-Music3** (candidato condicional, ver §5.3) | LLM 8B global + 0,6B local + Flow Matching | **MiniMax-Music3 Community License** (uso comercial permitido con condiciones — no Apache 2.0, ver más abajo) | ≈ 8 GB con *group offloading* | 24 GB | Híbrida LLM + Flow Matching | Canciones completas hasta 5 min, 32 kHz estéreo, control fino por secciones con captions estructurados (Global Metadata / Vocal Details / Arrangement); `safetensors`, soporte `diffusers`/SGLang/ComfyUI |
| **🆕 ACE-Step 1.5 XL** (`xl-base`/`xl-sft`/`xl-turbo`, candidatas de spike) | 4B (DiT) | Apache 2.0 | ≥ 12 GB con offload | ≥ 20 GB | DiT | Mayor calidad de audio que la base 3,5B; candidatas a incluir en la medición del spike de Fase 0 (`T-03`/`T-05`) y en el gate G1 si la VRAM local lo permite |

**🆕 Hallazgo 2026-08-18 (verificado contra fuentes primarias):** la familia **HeartMuLa** (HeartMuLa-oss-3B, HeartCodec-oss, HeartTranscriptor-oss) está publicada en Hugging Face con **Apache 2.0 y `safetensors`**; HeartTranscriptor-oss (base Whisper, ≈ 3 GB) sirve directamente para la medición de WER del protocolo de G1. MusicGen sigue **CC BY-NC** — descarte correcto, sin cambios.

**🆕 MiniMax-Music3, candidato condicional a tercer adapter (huggingface.co/MiniMaxAI/MiniMax-Music3, febrero 2026).** Es hoy el modelo de text-to-audio más tendencia de Hugging Face. **La licencia (MiniMax-Music3 Community License) permite uso comercial pero exige**: (a) mostrar «MiniMax-Music3» de forma prominente en la UI del producto que lo use; (b) autorización escrita previa si los ingresos anuales derivados superan 20 M$; (c) AUP y salvaguardas técnicas obligatorias. **No es Apache 2.0**: requiere dictamen de legal antes de considerarse alcance. Se apunta como candidato condicional **junto a YuE** (§5.3) — no sustituye la partida condicional de YuE, la complementa como alternativa a evaluar si G1-bis lo justifica. Añade una pregunta al lote del gate G2 (ver `tasks.md` T-01): *¿acepta legal los términos de la MiniMax-Music3 Community License (atribución prominente en UI + cláusulas AUP/salvaguardas) para uso interno y para producciones de cliente?*

**Nota de hardware (confirmación 10 del usuario):** el mínimo de 8 GB documentado sigue siendo cierto, pero es el **suelo con offloading**, no la configuración de trabajo. La cifra de confort para canciones completas es **24 GB**, con RTX 4090/5090 como referencia práctica. Consecuencias: (a) el spike debe **medir VRAM pico y s/min con y sin offloading**; (b) la elección de GPU cloud debe considerar una de 24 GB antes de asumir la L40S de 48 GB (I-14); (c) si se opera con 8 GB, S-02 sube y con él el coste por generación.

**Trade-off arquitectónico documentado:** los modelos LM (YuE, SongGen) destacan en alineamiento con la letra pero sufren inferencia lenta y artefactos estructurales; los de difusión (DiffRhythm) sintetizan más rápido pero pierden coherencia estructural de largo alcance. Ningún modelo gana en todo: **es la justificación directa de D-02 (registry pluggable)** — y también el límite de esa justificación: dos adapters bastan para demostrarlo, un router de capacidades completo no es necesario en fase 1 (D-16).

La familia **HeartMuLa** es especialmente relevante porque el transcriptor y el CLAP resuelven de fábrica piezas que habría que construir: alineado de letra con el audio, búsqueda semántica en la biblioteca y **las métricas objetivas de la suite de conformidad perceptual** (D-13) y del gate G1.

**Nota sobre reproducibilidad:** la semilla se registra por trazabilidad, pero **no garantiza salida idéntica**. La inferencia de difusión en GPU depende de versión de driver, cuDNN, kernels de atención y orden de reducción en coma flotante. Cualquier prueba que asuma igualdad bit a bit será *flaky*.

**Matiz legal de primer nivel:** el self-hosting **no cambia el estatus legal del output**. La licencia Apache 2.0 cubre **los pesos y el código**, no limpia la procedencia de los datos de entrenamiento. Para Daycry, que incorporará este audio en producciones comerciales, esto exige **validación de legal antes de gastar** (gate G2 en semana 0), y significa que **C-10 documenta el problema, no lo resuelve**: la única vía a procedencia realmente limpia es C-09 sobre catálogo propio licenciado.

### 11.2 Voz cantada y clonación

- **RVC v2** — opción de referencia en voice cloning open source, nacida para conversión de voz cantada. Enfoque *retrieval-based*, con naturalidad superior a los modelos puramente generativos.
- **so-vits-svc** — content encoder HuBERT + generativo estilo VITS. **El fork con soporte realtime tiene mantenimiento limitado desde primavera de 2023** → riesgo de dependencia abandonada.
- **YingMusic-SVC** — conversión de voz cantada *zero-shot* robusta (Flow-GRPO + sesgos inductivos específicos de canto). Más reciente.
- Otras: Chatterbox, Coqui XTTS, OpenVoice, Bark. **w-okada Voice Changer** como front multi-arquitectura.
- **Limitaciones documentadas del open source en este terreno:** requisitos altos de GPU, calidad inconsistente, falta de control emocional y **ausencia de safety y watermarking integrados** (D-10, I-13).
- **Verificación de licencia obligatoria** antes de integrar cualquiera de estas herramientas: la regla 5 del registry aplica al pipeline completo, no solo a los generadores.

### 11.3 Costes de GPU cloud (verificados julio 2026)

| Recurso | Precio | Fuente/observación |
|---------|--------|--------------------|
| **L40S (48 GB)** | desde ~0,39 $/h on-demand (proveedores especializados); **0,79 $/h en RunPod** | Holgada para estos modelos; probablemente **sobredimensionada** para ACE-Step solo |
| **GPU de 24 GB (RTX 4090 / 5090)** | **`⚠️ verificar` (I-14)** | Es la **cifra de confort de ACE-Step** (confirmación 10). Si su precio es una fracción del de la L40S, el coste mensual baja en la misma proporción. No se inventa el precio |
| **A100 80 GB** | 1,19–1,39 $/h (RunPod); **spot verificado hasta 0,68 $/h**; on-demand 1,21–4,10 $/h según proveedor | Lambda: A100 40 GB desde 1,99 $/h |
| **H100** | PCIe desde 1,99 $/h (RunPod) / 3,29 $/h (Lambda); SXM 2,69 $/h (RunPod) / 4,29 $/h (Lambda) | |
| **Serverless (RunPod)** | H100 ~4,55 $/h de compute activo; A100 ~2,72 $/h | Solo se paga el tiempo activo |
| Mercado | El on-demand entre Spheron, Lambda, RunPod y Nebius queda dentro de un 20 %; los marketplaces y neo-clouds son los más baratos | |
| Object storage (referencia) | **0,023 $/GB-mes** (S3 estándar) | Base del cálculo de §12.2. Precio del proveedor final `⚠️ verificar` (I-08) |
| Tipo de cambio | **0,92 EUR/USD** | `.claude/rates.json` |

### 11.4 Contexto legal

Suno y Udio fueron **demandados por las grandes discográficas en 2025** por infracción de copyright. Es la motivación de negocio de esta iniciativa y, al mismo tiempo, el recordatorio de que el riesgo vive en los **datos de entrenamiento**, no en el modo de despliegue.

**Consecuencia que hay que aceptar por escrito antes de aprobar:** las fases 1 y 2 de este proyecto entregan una plataforma con **la misma exposición de derechos que Suno** — mejor auditada, no más limpia. C-10 permite responder «qué modelo, qué pesos, qué licencia, qué declaración»; y esa declaración dirá «no divulgada». Si el requisito de legal es garantizar derechos limpios al cliente, ninguna de las fases 1–3 lo cumple: lo cumple C-09, que está bloqueada por I-03.

---

## 12. Operación, límites y seguridad

### 12.1 Límites de uso (valores por defecto, configurables)

Sin números no se puede implementar el 429 ni prometer una espera. Estos son los valores de partida:

| Límite | Valor por defecto | Razonamiento |
|--------|-------------------|--------------|
| Cuota por usuario | **200 generaciones/mes** | Con 5 usuarios da exactamente el techo declarado de 1.000 gen/mes |
| Concurrencia por usuario | **2 trabajos en ejecución** | Evita que un usuario monopolice los pods |
| Profundidad máxima de cola | **20 trabajos por usuario, 60 global** | Por encima, 429 con espera estimada |
| Duración máxima por pista | **180 s por defecto, 300 s máximo** | Coherente con los límites de los modelos (YuE 3–5 min) |
| **Pods GPU en paralelo** | **1 pod caliente + 1 pod efímero bajo demanda** (máximo 4) *(revisión 3: antes decía «2 por defecto», que contradecía el presupuesto de la opción G — **un** pod caliente, 128 €/mes)* | Determina a la vez coste y espera. Con el pod caliente: un usuario que encola 20 trabajos espera **~50 min** el último (150 s/gen) y los 5 usuarios con 20 cada uno son **~8 h**. **El trabajo que desborda el pod caliente arranca un pod efímero y paga 2–6 min de arranque en frío** (S-12): la UI lo muestra en la espera estimada. Con 4 pods la espera baja a ~2 h y el coste sube en proporción. **Si el spike confirma que caben 2 inferencias concurrentes en los 48 GB de la L40S, estas esperas se parten por dos a coste cero** |
| **Política de despacho** | **FIFO con fairness round-robin por usuario** | FIFO puro deja que un usuario con 20 trabajos encolados bloquee a los otros cuatro durante horas. El round-robin reparte turnos entre usuarios con cola pendiente sin abandonar el orden dentro de cada usuario (D-26) |
| Rate limit del asistente de letras | **30 peticiones/usuario/día** y tope de tokens de salida por usuario/día | El coste de tokens del LLM es la única partida de coste abierta sin GPU |
| Tamaño máximo de audio de entrada (C-08) | `⚠️ definir en C-08` | Depende del gate de titularidad |

Existe **UI de administración de cuotas** (subir/bajar por usuario, ver consumo, resetear) — sin ella, ajustar un límite es un `UPDATE` a mano en producción.

### 12.2 Almacenamiento: volumetría, coste y retención

Volumetría por generación: **~55 MB sin stems**, **~245 MB con stems**. A tarifa de referencia S3 estándar (0,023 $/GB-mes, 1 USD = 0,92 €) y 1.000 gen/mes, el gasto es **acumulativo**:

| Escenario | Mes 1 | Mes 12 | Mes 24 | Acumulado 12 m | Acumulado 24 m |
|-----------|-------|--------|--------|----------------|----------------|
| **Stems por defecto** (245 MB/gen) | 5 €/mes | **62 €/mes** | **124 €/mes** | **404 €** | **1.555 €** |
| Stems a demanda (55 MB/gen) | 1,2 €/mes | 14 €/mes | 28 €/mes | 91 € | 349 € |
| Stems a demanda + FLAC en lugar de WAV | ~0,7 €/mes | ~8 €/mes | ~17 €/mes | ~55 € | ~210 € |

**El almacenamiento supera el coste de GPU en el mes 10** en el escenario de stems por defecto **frente a la GPU efímera a 48 €/mes** (opción B con factor 1,6×); **frente a la opción G recomendada, de 128 €/mes, el cruce se va al ≈ mes 25**. Sin declarar la base, la frase no significa nada. Luego crece sin techo mientras la GPU se mantiene plana. Medidas obligatorias desde el día uno:

- [ ] **Stems a demanda**, nunca por defecto (×4,5 de volumen).
- [ ] **FLAC como formato de almacenamiento** en lugar de WAV 24 bit (D-09): ~40 % menos por artefacto sin pérdida de información real, porque el modelo no genera 24 bits de información real. WAV se exporta al vuelo si se pide.
- [ ] **Política de retención con números**: artefactos de generaciones **no marcadas como favoritas** → ciclo a almacenamiento frío a los **30 días**, borrado a los **180 días** salvo que pertenezcan a una producción entregada. Favoritas y pistas usadas en producción: retención indefinida con su manifiesto.
- [ ] **Ciclo de vida automático** a clase de almacenamiento frío (configuración de bucket, no proceso propio).
- [ ] **GC de artefactos huérfanos** por reconciliación diaria contra Postgres (ver §6, doble escritura).
- [ ] **Egress medido y presupuestado** (`⚠️ verificar` tarifa, I-08): con 1–5 usuarios es marginal, pero debe estar instrumentado antes de la fase 2.

### 12.3 Observabilidad, gasto y SLO

| Elemento | Definición |
|----------|-----------|
| **Tope de gasto mensual + kill switch** | Límite configurable de coste de GPU por mes. Al 50 % y 80 %: alerta. Al 100 %: **se pausa el despacho y se apagan los pods** en el proveedor (D-17). Los trabajos quedan `queued` |
| Alertas con destinatario | Toda alerta tiene un **responsable nombrado** y un canal, no un dashboard que nadie mira. Mínimo: gasto, profundidad de DLQ, tasa de fallos, proveedor caído, ledger de procedencia sin encadenar |
| **SLO y error budget** | Éxito de generación ≥ **98 %** mensual (excluyendo rechazos por validación); latencia p95 de extremo a extremo ≤ **10 min** con pod caliente. Consumido el error budget, se congelan features y se trabaja en fiabilidad |
| Coste por generación | Métrica de primer nivel: `gpu_seconds`, € por pista, € acumulado del mes, coste por usuario y por proyecto |
| **Métrica de calidad en el tiempo** | CLAP y WER medios por `modelo@version`, con alerta de **deriva al subir la versión de un adapter**. Sin esto, una regresión de calidad es invisible hasta que un montador se queja |
| Retención de logs | `⚠️ definir` contra política corporativa (I-17). Propuesta: 30 días en caliente, 12 meses en frío, datos personales minimizados |
| Trazas | OpenTelemetry de extremo a extremo: petición → cola → pod → adapter → post-proceso → storage |

### 12.4 Continuidad, entornos y secretos

| Elemento | Definición |
|----------|-----------|
| **Backup / RPO / RTO** | Postgres con PITR: **RPO ≤ 15 min, RTO ≤ 4 h**. Bucket de artefactos con versionado y borrado diferido de 30 días. Prueba de restauración al menos una vez por fase |
| **Inmutabilidad del ledger (WORM)** | Bucket dedicado con **object lock y retención**, cadena de hashes (cada registro incluye el hash del anterior) y **sello diario firmado**. Append-only por convención de aplicación **no basta** para un artefacto con valor legal declarado (D-18). **Secuencia obligada (D-20):** la **cadena de hashes** se implementa en la Fase 1 (C-10a) y el **object lock** en la Fase 2 (C-10b) — nunca al revés, porque **una cadena WORM no admite backfill** y el audio de la Fase 1 quedaría fuera para siempre |
| **Custodia de la clave C2PA** | **KMS gestionado del proveedor** (nunca la clave en el repositorio, en CI ni en el runner), **rotación anual**, **procedimiento de revocación documentado** y registro de qué versión de clave firmó cada manifiesto. Horas dentro de C-10b |
| **Runbook de desmantelamiento** | Una página, escrita en la Fase 1 (D-28): qué se conserva (ledger, manifiestos, pistas usadas en producción), **baja del proveedor GPU y cierre de facturación**, destrucción del resto de datos con constancia. Es el otro lado del stop-loss: si se para, se para sin dejar facturas abiertas |
| **Entornos** | `dev` local + `stage` + `prod`. Coste de infraestructura no-GPU de los tres: `⚠️ no presupuestado` (I-15). La GPU se comparte: `stage` usa pods efímeros con tope de gasto propio |
| **Gestión de secretos** | Gestor de secretos del proveedor o Vault; nada en repositorio ni en variables de entorno de CI en claro; rotación documentada; el runner **nunca** recibe secretos de larga vida (D-15) |
| **Plan de migraciones** | Alembic con migraciones versionadas, reversibles y probadas en `stage`; regla explícita: **el ledger de procedencia no se migra destructivamente**, se versiona |
| **Propietario operativo** | `⚠️ sin asignar` (I-16). Sin propietario nombrado, el OPEX de mantenimiento (≈ 15 %/año del build) no tiene dueño ni presupuesto |

---

## 13. Changelog

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-07-27 | Creación de la spec a partir de los requisitos confirmados por el usuario y de la investigación técnica de julio 2026. Estado `borrador`. | evaluator |
| 2026-07-27 | Enlace a la evaluación económica [`evaluation.md`](./evaluation.md). Campo `plan` en `pendiente`. | evaluator |
| 2026-07-27 | **Revisión 2 tras auditoría independiente.** Correcciones de texto: «cuatro transversales» (§5.1, antes «tres»). Cambios de criterio: gate legal G2 adelantado a la semana 0 y consecuencia de exposición de derechos declarada por escrito (§1.1, §11.4); recorte de abstracción del registry (D-16: fuera router de capacidades y formulario dinámico de fase 1) y corrección de la regla 2 del contrato, que era falsa; suite de conformidad redefinida por **tolerancia perceptual** en lugar de igualdad por semilla (D-13); dos invariantes de seguridad nuevos (D-14 solo `safetensors`, D-15 aislamiento de credenciales del runner); arranque en frío corregido a 2–6 min / 5–12 min peor caso con caché de imagen de contenedor como hueco cerrado (S-01, S-01b, S-02b); postura de GPU con keep-warm y pod caliente (D-05b); FLAC en lugar de WAV como formato de almacenamiento (D-09); tope de gasto con kill switch (D-17); ledger WORM real (D-18); límites de uso con números (D-19, §12.1); almacenamiento calculado con retención, ciclo a frío y GC (§12.2); observabilidad, SLO y deriva de calidad (§12.3); backup/RPO/RTO, entornos, secretos, migraciones y propietario operativo (§12.4); criterios de aceptación por característica (§5.2); nuevos huecos de la tabla de errores (§6). Información nueva del usuario: hardware de ACE-Step con 24 GB de confort (confirmación 10, §11.1, §11.3) y UX de Suno como referencia con estudio guiado de su interfaz (confirmación 11, D-12, D-12b). Incógnitas nuevas: I-13 a I-18. Supuestos nuevos: S-01b, S-02b, S-09, S-10. | evaluator |
| 2026-07-27 | **Revisión 3 tras dos auditorías independientes más (coherencia + adversarial de secuenciación).** El estado sigue siendo `aprobada`, pero **las cifras cambian y requieren re-ratificación del usuario**: lo ratificado fueron 33.000 € de Fase 1 y ahora son **38.400 €** (total **1.566 → 1.622 h** base). **Defectos de coherencia corregidos:** S-08 ya no dice que el precio de tokens está a 0 y pendiente (está verificado; coste 959 €/1.151 €); **I-06 tachada como cerrada** también aquí (estaba cerrada en la evaluación y abierta en la spec); §1.2 matiza «WAV como exportación a demanda» (D-09); S-09 y §12.2 declaran la **base** del cruce almacenamiento-GPU (mes 10 frente a los 48 €/mes de la GPU efímera; ≈ mes 25 frente a los 128 €/mes de la opción G recomendada). **Secuenciación y alcance (lo importante):** **D-20** parte C-10 en **C-10a (38 h, Fase 1)** y **C-10b (67 h, Fase 2)** porque una cadena WORM **no admite backfill** y la Fase 1 generaba ≥ 2 semanas de audio sin ledger — se corrigen a la vez el criterio de aceptación de C-01 (exigía un manifiesto que no existía hasta la Fase 2) y la **regla 4** del contrato (obligaba a emitir un formato que legal no había firmado), y se añade `manifest_schema_version` con verificador multi-versión y corpus en CI; **D-21** gate de derechos de la **letra** en C-01 (bloqueo duro, `lyrics_declaration`, fila nueva en §6) y endurecimiento del asistente de letras en C-05, con el filtro automático de similitud declarado **mejora futura no bloqueante** (§5.3); **D-22** linaje en el esquema desde el día 1 (`parent_id`, `root_id`, `derivation_kind`, `section_map`, `source_generation`) para que C-07 no arranque con una migración en producción; **D-27** G1 evalúa **solo ACE-Step** y HeartMuLa pasa **G1-bis** al registrarse su adapter (el protocolo anterior era inejecutable: HeartMuLa se contenariza en la Fase 1, después de G1), más **matriz de capacidades verificadas** en el spike; **D-06** degrada YuE de «adapter adicional» a **candidato condicional** de Fase 2 (≈ 50 h no presupuestadas). **Decisiones baratas que faltaban por escrito:** **D-23** exportación a 48 kHz con soxr y loudness por destino (−23/−14/sin normalizar); **D-24** compartir = URL de la pista en la app, URLs firmadas solo internas; **D-25** i18n en castellano con `next-intl` desde el día 1 (I-19 para catalán/inglés) y WCAG AA fuera de objetivo de Fase 1 con componentes accesibles por defecto; **D-26** un pod caliente + un efímero bajo demanda con despacho FIFO + round-robin por usuario (§12.1 decía «2 pods», contradiciendo el presupuesto de la opción G); **D-05b** horario `Europe/Madrid`, laborables, calendario ajustable por el admin; **D-28** stop-loss intra-fase al cierre de C-13 y runbook de desmantelamiento (§12.4); custodia de la clave C2PA en KMS con rotación anual y revocación documentada (§12.4). **Supuestos nuevos:** S-11 (política de las ~40 pistas de spikes/G1: carpeta segregada, retención 12 meses, manifiesto retroactivo simplificado para las 20 propias, **verificación de los ToS de Suno** en la semana de G2) y S-12 (un pod caliente basta; el desborde paga arranque en frío). **Incógnitas nuevas:** **I-05b** (¿es protegible/licenciable en exclusiva el output sin autoría humana? — segunda pregunta de G2), **I-13b** (ficha de licencia de toda herramienta del pipeline: Demucs, RVC, HeartCodec/HeartTranscriptor), **I-19** (idiomas de la UI), **I-20** (supervisor musical y 3–5 usuarios piloto **nombrados**, condición del veredicto). Criterios de aceptación actualizados: C-01, C-03, C-05, C-10a, C-10b, C-11, C-13. Pruebas nuevas: regresión de manifiestos multi-versión y concurrencia de 2 inferencias en una L40S. | evaluator |
| 2026-08-18 | **Ampliación: modo GPU local (D-29, T-85, E2E-GPU-04).** Nueva decisión **D-29**: el runner soporta tres modos de despliegue seleccionables por `GPU_PROVIDER` — cloud RunPod (default), **local con GPU propia** vía NVIDIA Container Toolkit (perfil compose `gpu-local`, detección de VRAM y offloading automático si <24 GB) y mock. Todos heredan los mismos invariantes (`safetensors`, aislamiento de credenciales, manifiesto/ledger, `max_gpu_seconds`). Nueva confirmación del usuario (**#12**, §8: RTX 4090/5090 como referencia, 8 GB como suelo) y nueva incógnita **I-21** (VRAM real de la máquina local objetivo). Fila nueva en la tabla de errores (§6): GPU local sin VRAM suficiente. **No cambia el estado de la spec ni las cifras ratificadas (38.400 €)**: el delta de horas (`T-85`, +16 h base / +960 €) vive en `improvement-plan.md`/`tasks.md` como ampliación de alcance a la espera de ratificación económica. | planner |
| 2026-08-18 | **Ratificación de la ampliación GPU local (+960 €) y decisión: Fase 0 en GPU local preferente** (misma fecha). Confirmación **12** actualizada: la ampliación `T-85`/D-29 queda **ratificada económicamente**; los 39.360 € de Fase 0+1 (incluida la ampliación) son la cifra ratificada, no solo los 38.400 € originales. Nueva **confirmación 13**: la Fase 0 (spikes `T-03`–`T-08` y generación de pistas de G1 `T-09`) se ejecuta preferentemente en GPU local, sin esperar a `T-85`; el arranque en frío sigue midiéndose solo en RunPod. Línea añadida en D-29 con esta matización. | planner |
| 2026-08-18 | **Hallazgos HF 2026-08-18 registrados como candidatos** (SilentCipher/AudioSeal para I-13, Demucs CC-BY-NC confirmado en I-13b, MiniMax-Music3 candidato condicional con pregunta añadida a G2, vía LoRA en anexo F4, XL en spikes). Registro informativo, sin cambio de cifras, fases ni estados: **1.622 h base / 39.360 € con margen** de Fase 0+1 ratificados intactos. Detalle en §10 (I-13, I-13b) y §11.1 (tabla de modelos, candidatos MiniMax-Music3 y ACE-Step XL); nota junto a la partida condicional de YuE en §5.3. | planner |
| 2026-09-01 | **Corrección de coherencia tras revisión integral (`revision-2026-09-01.md`).** (a) **Advertencia visible de no-go de la Fase 4** añadida a C-04 y C-09 en §5.1/§5.2 (criterios conservados solo como pre-planificación) e **I-03 actualizada**: C-09 no está solo «bloqueada», la Fase 4 está en no-go decidido. (b) **D-10, diagrama §3.1 y S-10** alineados con la I-13 vigente: «sin solución identificada» → candidatos MIT (SilentCipher, AudioSeal), robustez en música por validar. (c) Frontmatter: `actualizado: 2026-09-01` y campo `ratificada: 2026-08-18`. (d) Cabecera de cadena de artefactos ampliada con `test-plan.md` y `ui-design.md`. (e) **I-20** anota el avance parcial del 2026-08-18 (Daycry acumula supervisor musical; faltan 2 de 3 evaluadores de G1; usuarios piloto sin nombrar) sin cerrar la incógnita. (f) **D-25** reconciliado con el sistema de diseño: el contraste AA de color sí es requisito desde la Fase 1; lo que no es objetivo es la conformidad WCAG AA completa. (g) **S-02b** aclara que los 150 s de S-02 incluyen reintentos y post-proceso y que usarlos como denominador de «trabajo útil» es convención conservadora (sobrestima el factor). Sin cambio de cifras, fases ni estados. | revision-2026-09-01 |
| 2026-09-01 | **Ampliación propuesta: instalador del runner GPU local (D-30, `T-86`, I-22).** Nueva decisión **D-30**: un **CLI/script de instalación** que implanta el modo `GPU_PROVIDER=local` (D-29) en una máquina nueva — **preflight automatizado** de GPU/VRAM/driver NVIDIA/Docker/**NVIDIA Container Toolkit** (`docker run --rm --gpus all …`) con mensaje accionable por carencia; **descarga y colocación de los pesos con verificación SHA-256** y rechazo de todo lo que no sea `safetensors` (invariante **D-14**); **selección y escritura de la configuración local** (`GPU_PROVIDER=local\|runpod\|mock`, perfil compose `gpu-local`, guardarraíl **G-01** `ACE_STEP_REQUIRE_GPU=1` en los modos de medición); y **desinstalación limpia básica**. **Fuera de alcance:** GUI, auto-update y empaquetado firmado de Windows (delta aparte si un SO objetivo lo exigiera). Convierte en **repetibles** los ítems 6–7 del `pre-dev-checklist.md` (CS-35/CS-36), hoy manuales y sin dueño, **sin eliminar** la comprobación manual única de la máquina de referencia de los spikes (**CS-34 sigue vigente**). Nueva incógnita **I-22** (qué SO/máquinas objetivo exactamente —Linux nativo, Windows+WSL2 o ambos— y **quién mantiene el instalador tras la entrega**, ligada a I-16), que condiciona el esfuerzo del preflight. **No cambia el estado de la spec ni las cifras ratificadas (39.360 €)**: el delta de horas (`T-86`, **+32 h base / +38,4 h con margen / +1.920 €**, rango 24–40 h) vive en `improvement-plan.md`/`tasks.md` como **ampliación de alcance a la espera de ratificación económica**. | evaluator |
| 2026-09-01 | **Adaptación a proyecto personal en solitario (decisión del propietario: proyecto personal en solitario).** El propietario real del proyecto (Daycry) declara que es un **proyecto personal de una sola persona con posible comercialización futura**. Incógnitas cerradas en §10: **I-01** (equipo = el propietario en solitario, con la IA como multiplicador; el calendario pasa a ser orientativo), **I-16** (propietario operativo = el propietario), **I-18** (tarifa interna: N/A en modo personal) e **I-20** (evaluador único y usuario piloto = el propietario, `T-02` completado — ver `gates/gobernanza.md`). **I-11** anotada: el presupuesto lo decide el propietario y las cifras en € son informativas en modo personal. **I-21 sigue abierta** (máquina GPU local), igual que las demás. Todo lo corporativo-legal desactivado por el modo solo se reagrupa en el nuevo **gate de comercialización GC-01** (`gates/gobernanza.md` §8: consulta legal real I-05, I-05b, ToS de Suno, re-verificación de licencias I-13/I-13b para uso comercial, RGPD/DPIA si Fase 4, Anexo A, gobernanza con personas reales) — solo aplica si el proyecto pasa a ser comercial o con terceros. Los umbrales de G1 (7/10 ≥ 4/5, WER ≤ 15 %) y el stop-loss **no cambian**. Sin cambio de cifras (39.360 € / 98.280 € siguen como referencia informativa). | propietario (Daycry) |
| 2026-09-01 | **Máquina objetivo del modo GPU local (I-21/I-22).** Decisión del propietario: **el desarrollo y los spikes se ejecutan en su PC actual (Windows)**; el despliegue final puede quedarse en esa máquina o ir a otra (portabilidad cubierta por el instalador D-30/`T-86`). I-21 queda reducida a confirmar **modelo de GPU y VRAM** (`nvidia-smi`); I-22 anotada: **Windows 11 + Docker Desktop/WSL2 es el primer SO a soportar**. Sin cambio de cifras ni de estados. | propietario (Daycry) |
| 2026-09-01 | **I-21 cerrada: GPU confirmada — NVIDIA GeForce GTX 1070, 8 GB de VRAM** (PC de desarrollo, Windows; driver NVIDIA pendiente de instalar). Justo en el **suelo de 8 GB** de D-06/D-29 → **offloading obligatorio**. Aviso registrado: Pascal sin BF16 ni tensor cores — los supuestos de tiempo de S-02 (150 s/pista, base L40S/4090) **no aplican tal cual** en esta máquina; `T-03` medirá la realidad y RunPod queda como alternativa de medición si lo local resulta impracticable. Sin cambio de cifras ni de estados. | propietario (Daycry) |
