# ADR-0029 — Presupuesto operativo y captura de instrucciones de ACE-Step

- **Estado:** aceptada
- **Fecha:** 2026-10-05
- **Decisor:** orquestador, con la autorización del propietario para implementar el roadmap y elegir las mejores alternativas
- **Ámbito:** M0/T-19; controles de entrada de ACE-Step y hook opcional de engines

## Contexto

La [auditoría T-17](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t17/audit-report.md) reproduce las plantillas y tokenizadores del código fijado a `dce621408bee8c31b4fcf4811682eb9359e1bc94`, con inferencia sustituida por capturas CPU. Un límite de caracteres no representa el presupuesto real: nueve de diez prompts originales se rechazan por el límite administrativo y cuatro excederían la descripción completa del DiT. El LM también necesita reservar espacio para la salida de códigos de audio. Conservar los tags en la preparación de T-18 no resuelve esos límites.

El propietario pide asegurar el recorrido de las instrucciones antes de perfeccionar o cambiar el modelo. La fidelidad del transporte se puede verificar; la obediencia musical necesita generación y escucha. El padre HTTP debe seguir sin torch/CUDA y el engine solo puede escribir salida cruda en `data/tmp/<job_id>/`.

## Alternativas

| Alternativa | Ventaja | Coste o riesgo |
|---|---|---|
| Ampliar caracteres y conservar truncamiento upstream | Cambio pequeño | Pierde instrucciones sin avisar y no reserva toda la salida |
| Aproximar tokens o duplicar plantillas en el padre | Evita un proceso CPU | Puede divergir del checkpoint y confundir ventana declarada con política operativa |
| Medir código y tokenizadores fijados en proceso CPU, con rechazo y captura posterior | Comprueba límites reales sin cargar pesos en GPU | Añade validación local, timeout, integridad y recibos |

## Decisión

Elegir medición offline en un proceso CPU aislado, con CUDA oculta, métodos y plantillas del upstream fijado y tokenizadores/configuración locales verificados contra el lock. Un fallo de fuente, hash, configuración o timeout impide aceptar la entrada. No se sustituye por una estimación optimista ni se descarga material en runtime.

El perfil declara explícitamente la política operativa del backend `pt`: **entrada más reserva de salida ≤4096 tokens**, independiente del `model_max_length=131072` que declara el tokenizer. La reserva debe cubrir la duración solicitada y las ramas activas de generación, sin reducirla silenciosamente para encajar. El DiT se valida sobre sus canales completos: **256 tokens de descripción con instrucciones y metadatos**, y **2048 tokens de letra con sus cabeceras e idioma**. El límite efectivo de duración del LM del tier 4 se valida antes de ejecutar; no se admite un clamp silencioso.

El servidor común admite un hook opcional de preflight para `estimate` y `jobs`, previo a cargar o encolar. ACE-Step lo conecta y protege también la entrada directa del adaptador. Los demás engines conservan su comportamiento cuando no proporcionan hook. Los límites administrativos de texto solo pueden ampliarse cuando estos controles ya estén activos. Ninguna feature pasa a `verified` por validar un campo o su presencia en tokens.

El idioma entra en la metadata `language` del formato YAML entrenado del LM y en el canal vocal del DiT. Tonalidad y compás explícitos se transmiten en el formato que admite el upstream fijado; sus omisiones no inventan valores. Los controles de CoT que reescriben caption, letra o metadata permanecen desactivados. Una extracción condicional de caption no autorizada se rechaza.

También se verifica la configuración del checkpoint DiT seleccionado. Turbo, SFT y Base normales conservan el perfil de canción/instrumental. El indicador `is_lego_sft` activa en el upstream una plantilla Local/Global específica de SFT-stems; esa operación no está expuesta por el adaptador de M0. Un checkpoint de ese tipo se rechaza antes de cargar, con motivo explícito, hasta que el adaptador de stems incorpore su perfil y prueba diferencial. No es una prohibición de esa capacidad en el roadmap ni una declaración de soporte por tener sus pesos.

Se distinguen recibos **planned**, calculados antes de generar, y **captured**, obtenidos de las fronteras realmente alcanzadas durante la ejecución. Una captura CPU con inferencia sustituida se identifica como tal; no acredita inferencia GPU ni calidad musical. Los recibos registran hashes, conteos, flags y defaults efectivos. El engine escribe datos crudos privados; el llamante valida referencias e integridad y conserva la procedencia junto con los manifiestos. Eventos, errores y documentación pública no publican letras, prompts ni rutas personales.

## Consecuencias

El usuario recibe un rechazo verificable cuando una instrucción se perdería. Puede adaptar su prompt de forma explícita, conservando el original y el diff de T-18, sin que el sistema traduzca, resuma o trunque por su cuenta. Una entrada aceptada significa que cabe y que se transporta íntegra; no significa que el modelo siga cada instrucción musical.

La integración debe comprobar el código incorporado a la imagen del engine, además de los tests CPU del host. Se permite reconstruir esa imagen con código local y dependencias fijadas, sin nuevos pesos, herramientas ni cambios de locks. T-19 conserva la GPU sin cargar y deja la evaluación artística a T-08/T-12/T-13. El futuro cambio de modelo o backend requiere un perfil y pruebas propios; no hereda los presupuestos de ACE-Step por suposición.
