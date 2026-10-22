---
id: ADR-0073
titulo: Recetas privadas y escucha A/B de iteración creativa
estado: aceptada
fecha: 2026-10-10
iniciativa: m2-iteracion-creativa
design: ../roadmap/2026-10-10-m2-iteracion-creativa/design.md
autoridad: elección del orquestador bajo delegación explícita del propietario
---

# ADR-0073 · Recetas privadas y escucha A/B de iteración creativa

## Contexto

M2 incorpora asistencia de texto, derivaciones musicales, edición CPU, árbol de versiones y comparación A/B. M1 ofrece cola SQLite, linaje, custodia y publicación por toma. Sus contratos de post-proceso requieren un intento ganador de engine; una edición CPU necesita autoridad propia. El comparador debe preservar masters y sus manifiestos.

El [diseño comparado](../roadmap/2026-10-10-m2-iteracion-creativa/design.md) presenta tres opciones con los mismos criterios. El orquestador elige y acepta O2 el 2026-10-10 bajo delegación explícita del propietario de tomar las mejores alternativas, tras revisar el diseño y este ADR. Este registro no atribuye al propietario lectura ni elección personal de O2. El diseño queda aprobado para handoff a planificación.

## Decisión

El server captura una receta privada, tipada, versionada e inmutable por operación confirmada en `job.request`. Incluye referencias propias, hashes, letra efectiva, parámetros, intervalos y ensamblado. Los compositores cerrados usan `job`/`job_dependency` y los carriles existentes; no añaden otro scheduler ni un editor de grafos reutilizables.

Las derivaciones producen takes hijos con aristas de todos sus padres, raíz canónica y mapas efectivos. El maestro solo cambia por la acción explícita vigente. La variación de petición recupera parámetros y letra históricos; `music.retake` consume audio fuente. Cada operación musical mantiene su descriptor/feature gate y su conformidad real independiente.

### Autoridad de edición CPU

El server distingue origen engine y CPU antes del render/publicación. Para engine conserva el terminal ganador y su procedencia. Para CPU conserva propietario, canción, job, execution_id, take destino, receta/hash, padres/assets/hashes, derechos, herramientas/pins y terminal propio. Exige contexto revalidado, intención CAS y cierre de custodia comprobado. La presencia de archivos no acredita éxito ni autoriza limpieza ajena.

No inventa un intento engine, modelo de inferencia ni semilla ejecutados. El edit registra cómputo CPU y herramientas reales; modelos/semillas de padres son antecedentes. El planner resolverá la representación compatible de los campos obligatorios actuales de Take antes de implementar edición. Si requiere cambiar una decisión vigente, lo hará explícito; esta decisión no permite un sentinel que finja inferencia.

El ensamblado mide duración, índices de muestra y fidelidad de regiones `keep`; PCM24 no demuestra identidad de muestras. Fades y crossfade declaran envolventes y ambos padres. Una envolvente lineal complementaria es la política propuesta, pendiente de prueba: no sustituye medir clipping/true peak ni escuchar la unión.

### Escucha A/B sin modificar masters

El worker CPU genera previews por par desde masters, mediante ganancia lineal y solo atenuación. Para mediciones `L_i` LUFS, `P_i` dBTP y techo `C = -1 dBTP`, el objetivo propuesto es `T = min(L_A, L_B, L_A + C - P_A, L_B + C - P_B)`. La ganancia propuesta es `g_i = T - L_i`. La fórmula evita aumento de nivel en el dominio medido; la salida renderizada se vuelve a medir tras conversiones.

El plan fija formato sin pérdida compatible, método y tolerancias antes del RED. La propuesta es diferencia A/B ≤0,5 LU y true peak ≤−1 dBTP. Si no cumple, baja el objetivo común con reintentos acotados o rechaza la comparación. No aplica limitadores diferentes que oculten la dinámica de los masters. Silencio, audio demasiado corto o medición no finita deshabilitan igualación automática con motivo.

La alternancia conserva tiempo absoluto dentro de la ventana común, sin prometer alineación musical de estructuras distintas. Latencia, drift, clicks y utilidad requieren medición y escucha. Antes de servir previews, el server emite su propio manifiesto CPU v2 inmutable con sujeto job autorizado y linaje de edición, conforme a la concreción posterior de [ADR-0074](ADR-0074-procedencia-cpu-y-contratos-versionados.md). Se resuelve desde recibo/contexto privado; no crea Take/intención ficticias ni asset job inválido. Los temporales conservan custodia, propiedad, derechos y hashes; no crean takes maestros ni modifican manifiestos emitidos.

### Texto, proveedores y GPU compartida

El adaptador LLM Docker implementa `/v1` hacia el Ollama compartido WSL2, conforme a [ADR-0035](ADR-0035-despliegue-docker-y-ollama-wsl.md). No crea otro servidor de inferencia ni almacén externo de pesos. Un coordinador observa residencia y VRAM y registra intervención propia antes de descargar. Comprueba ausencia y memoria liberada; detecta recarga ajena. Solo restaura modelos observados y efectivamente descargados por su turno, tras descargar el residente propio y comprobar ocupación compatible. Nunca detiene Ollama ni borra modelos.

El plan fijará recibo durable, recovery, timeout y destino privado Docker→WSL2. No promete exclusión global frente a otros clientes. El modelo de letras, sus hashes, revisión, licencia, idiomas, etiquetas y memoria siguen pendientes de selección y prueba real.

El LLM devuelve propuestas editables; aceptar crea versión de letra con padre y declaración aplicable. No encola música automáticamente. Providers externos permanecen dentro del server, por función, apagados de fábrica y sin fallback silencioso. Ninguno se habilita sin adapter verificado, clave y coste previo fiable. La música permanece siempre local; este ADR no selecciona una API externa.

## Alternativas descartadas

- **O1: handlers separados y ganancias A/B en navegador.** Duplica validación/autoridad por operación y exige demostrar igualdad sobre distintos decoders/grafos del cliente. Tiene menor coste inicial y mayor riesgo de divergencia.
- **O3: sesiones de edición y grafo persistente de recetas.** Añade entidades, compilador y una segunda historia de borradores/recetas. M2 no requiere esa reutilización ni la UX adicional. Tiene coste y riesgo superiores.

## Consecuencias

M2 amplía API, cola, worker, adapters y web conservando SQLite y el publicador de M1. Requiere contratos privados tipados y compatibilidad de recibos históricos; `/v1` solo admite ampliaciones opcionales. El server sigue sin torch y conserva post-proceso, BD y manifiestos como responsabilidad propia.

La arquitectura facilita pruebas CPU/mock de recetas, replay, linaje, derechos, cancelación y publicación. Esa evidencia no verifica un modelo musical, calidad, VRAM, red Ollama ni escucha A/B. Las capacidades y providers no verificados permanecen deshabilitados.

[ADR-0037](ADR-0037-avance-tecnico-condicionado.md) permite definición y unidades técnicas independientes tras plan aprobado. La aceptación de M2 conserva M1 cerrado, al menos 30 generaciones propias reales, M0/T-13, cada operación musical escuchada y todos los CA de [spec.md](../roadmap/2026-10-10-m2-iteracion-creativa/spec.md). No elimina ni cumple por declaración ningún gate.

No se modifican las fuentes selladas ni la matriz activa M0/T-09. Este ADR no ejecuta GPU, Ollama, Docker, descargas o suites. La corrección de la tabla histórica llama.cpp en contrato-engines queda a cargo del orquestador; ADR-0035 conserva autoridad.

## Estado

`aceptada` — arquitectura O2 elegida y revisada por el orquestador bajo delegación el 2026-10-10. Implementación, revisión de código y QA pendientes. No acredita implementación ni aceptación funcional. El orquestador conserva el índice compartido de decisiones y la promoción de estado.


La concreción de representación CPU de [ADR-0074](ADR-0074-procedencia-cpu-y-contratos-versionados.md) conserva esta arquitectura O2 y sustituye sólo la prescripción anterior de preview v1 por CPU v2. La inferencia y el post M1 mantienen v1. La excepción SQL, snapshots y API server v2 se delimitan allí y conservan derechos, custodia, revalidación y gates de audio de este ADR.
