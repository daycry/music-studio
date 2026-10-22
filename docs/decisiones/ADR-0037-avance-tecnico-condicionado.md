# ADR-0037 · Avance técnico condicionado a la aceptación musical

- **Estado:** aceptada por decisión del orquestador bajo delegación del propietario.
- **Fecha:** 2026-10-07.
- **Autoridad:** el propietario pidió continuar autónomamente y delegó elegir las mejores alternativas. O2 la elige el orquestador; no se atribuye al propietario una elección específica de esta opción.
- **Alcance:** cambia la secuenciación de construcción y aceptación de los hitos; conserva los contratos, criterios funcionales, derechos y aceptación humana.

## Contexto y alternativas

M0 permanece abierto y su elección musical depende de escucha humana. M1 dispone de spec aprobada, plan y contratos `/v1` con engine-mock. Su bloqueo absoluto impide construir seguridad, persistencia e interfaz que no requieren elegir un motor. [Diseño comparado](../roadmap/2026-09-28-m1-mvp-estudio/design.md).

| Opción | Evaluación |
|---|---|
| O1: esperar todo M0 | Simple; paraliza unidades independientes mientras falta la escucha. |
| O2: avanzar técnicamente contra mock, conservar aceptación real | Elegida: reversible, mantiene las pruebas reales y permite progreso autónomo. |
| O3: usar un motor real provisional como producto | Riesgo de habilitar capacidades no verificadas y alterar el benchmark activo. |

## Decisión

Se permite construir y probar M1 contra engine-mock antes de cerrar M0, después de aprobar esta secuenciación mediante revisión y QA documental. Los contratos disponibles y las dependencias técnicas siguen siendo obligatorios. No se elimina ningún criterio de aceptación ni se cambia un estado para aparentar su cumplimiento.

Una tarea solo se cierra al ejecutar sus verificaciones y cumplir sus propios criterios. Implementación, QA CPU, E2E contra mock y despliegue Docker real sin GPU son evidencias distintas; ninguno acredita integración GPU, calidad musical ni elección del modelo. Una tarea con criterio real pendiente conserva ese criterio abierto y su estado en progreso o revisión.

T-01 puede acreditar server/configuración/seguridad y Docker real sin torch. T-02 puede acreditar esquema completo, linaje, WAL/FTS y backup/restauración con biblioteca de prueba. T-04 conserva I-01, resuelta con datos de M0; no se fija batch ni rendimiento por suposición. M-01 se conserva como prueba real compartida de aceptación del hito en T-16: las tareas técnicas de post-proceso no la sustituyen. M-02 y M-03 conservan su evidencia exigida.

La aceptación final de M1, T-16 y el uso musical validado conservan M0/T-13 cerrado, music.song/music.instrumental verificadas, M-01 y los demás criterios de la spec. El mock se identifica como sintético. Una tarea o feature real con verified:false se rechaza y se muestra deshabilitada con su motivo; no se usa la excepción de laboratorio para eludirlo.

Los hitos M2–M5 pueden abrir definición y unidades técnicas independientes después de documentar sus specs, planes y dependencias. Se conservan sus umbrales de uso real y aceptación secuencial; las generaciones del mock no cuentan como uso musical. Esta decisión no aprueba nuevas funcionalidades ni permite saltar TDD, revisión, QA, contratos, licencias o controles GPU.

Durante GPU160 no se modifican sus fuentes selladas, modelos, imagen ni entradas, ni se inicia inferencia adicional. Se coordina la carga de CPU y Docker: una interferencia observada se registra y se trata según las guardas existentes; no se amplían márgenes para ocultarla. Producto en Docker, excepción Ollama compartido WSL2 y cola SQLite se conservan ([ADR-0035](ADR-0035-despliegue-docker-y-ollama-wsl.md)).

## Consecuencias y validación

El progreso permanece en cada tasks.md. Los gates de inicio se sustituyen por apertura técnica y aceptación final explícitas, enlazadas en spec/plan/tests/roadmap. M0/T-13 y las capacidades reales siguen pendientes. Cambiar un candidato continúa siendo una decisión de modelo aparte; este ADR no escoge un ganador ni acredita despliegue.

Validación de esta decisión: revisión A/B sin gaps y QA documental conforme (9 documentos/482 enlaces/0 errores), con [evidencia de T-00](../roadmap/2026-09-28-m1-mvp-estudio/testing/t00/qa-report.md). Integración Git pendiente. Los gates de implementación de cada tarea siguen completos.
