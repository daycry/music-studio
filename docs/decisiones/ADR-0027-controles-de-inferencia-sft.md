# ADR-0027 — Controles SFT y comparación con transporte emparejado

- **Estado:** aceptada
- **Fecha:** 2026-10-06
- **Decisor:** orquestador, con autorización del propietario para implementar el roadmap y elegir las mejores alternativas
- **Ámbito:** M0/T-16; controles de inferencia y experimento privado previo a la batería M0

## Contexto

El propietario pide más naturalidad de voces, ritmo e instrumentos, y exige comprobar las instrucciones antes de cambiar modelos. La [investigación de candidatos](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t15/model-review.md) recomienda probar SFT con sus controles correctos. La prueba anterior de captions no acredita un ganador ni la calidad requerida.

T-16 preveía tres tomas SFT nuevas frente a tres controles Turbo conservados de T-15. Después se priorizaron T-17–T-19. La [auditoría T-17](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t17/audit-report.md) documenta que el adaptador anterior enviaba BPM/duración al YAML del LM, pero no el idioma estructurado. [T-19](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t19/report.md) incorpora ese idioma, presupuestos nativos y capturas verificables. Las tomas de T-15 no tienen esas capturas históricas: la reproducción CPU del recorrido anterior no se presenta como captura GPU de aquellas tomas.

Una comparación de SFT nuevo con Turbo antiguo mezclaría la configuración musical con el cambio de transporte. La identidad de los archivos de caption/letra y de los parámetros solicitados no basta para afirmar igualdad de las entradas efectivas. Los audios, preparaciones y valoraciones anteriores deben preservarse.

## Alternativas

| Opción | Ventaja | Límite o coste |
|---|---|---|
| Tres SFT nuevas y controles Turbo de T-15 | Menor cómputo adicional | Transporte distinto y capturas históricas ausentes; no permite separar ese factor |
| Tres Turbo y tres SFT nuevas con el mismo transporte actual | Comparación emparejada, con recibos actuales | Tres generaciones Turbo adicionales; tiempos y consumo se medirán, sin estimaciones presentadas como datos |
| Ejecutar inmediatamente toda la batería de diez briefs | Mayor cobertura de usos | Adelanta T-11 y su evaluación, sin sustituir los requisitos de análisis y escucha de M0 |

## Decisión

Elegir seis tomas nuevas emparejadas: tres Turbo y tres SFT, 90 segundos, semillas 1/2/3, caption y letra de control T-15 idénticos por hash, español/BPM94, shift1, LM0,6B, BF16 y backend PT. Se conservan también los tres controles Turbo antiguos como referencia histórica separada; ningún take, manifiesto, preparación o valoración se sobrescribe.

La comparación cambia la configuración completa del decodificador: Turbo usa ocho pasos y sus defaults anteriores; SFT usa cincuenta pasos y CFG7. No se atribuye el resultado al checkpoint aislado. Identidad, parámetros explícitos, defaults efectivos y pasos de progreso/cancelación deben ser coherentes entre descriptor, adaptador, solicitud, manifiesto, perfil planned y fronteras captured. Las opciones CPU previstas son pasos enteros 1–8 para Turbo/1–200 para SFT y CFG finito 1–20 únicamente para SFT. Su implementación se acredita en el ledger antes de usarlas.

El handler del upstream fijado (`dce621408bee8c31b4fcf4811682eb9359e1bc94`) fuerza guidance_scale=1 para Turbo: `core/generation/handler/generate_music.py:286–294`, SHA-256 `4126b89bea9032d5ad1a5d9f906410ef4ede79a1d2328635aa365010473ee086`, comprobado en lectura. El valor7 heredado de GenerationParams permanece en la frontera de entrada, pero no significa CFG7 aplicado por Turbo. SFT sí usa CFG7 en esta configuración. Un recibo capturado en `dit.generate_music` acredita sus argumentos de entrada, no el valor posterior a una transformación interna del handler ni una ejecución GPU. La comprobación integrada conservará esa distinción; no se presenta una igualdad nominal de campos como igualdad del muestreo interno.

Antes de comparar, comprobar que ambas configuraciones reciben el mismo texto/metadata efectiva y los mismos controles LM; cualquier diferencia ajena a los controles DiT declarados impide presentar el par como emparejado. Si una entrada se rechaza, no se trunca ni se adapta silenciosamente. Las capturas nuevas conservan ambas ramas PT y distinguen entrada planificada de ejecución alcanzada.

La generación conserva las guardas actuales: Ollama descargado solo por modelo, baseline GPU ≤1600 MiB, cap a partir de VRAM libre, un modelo residente y parada conservadora ante desbordamiento. No se reutiliza una excepción GPU anterior. No cambia el motor por defecto, ni se añaden pesos/dependencias/locks, ni se declara ninguna capacidad verificada.

## Consecuencias

La prueba cuesta seis generaciones nuevas y mantiene intacta la historia. La hoja ciega compara las configuraciones nuevas con la referencia Suno original, mediante ganancia lineal y nivel común; resultados y mapa se custodian por separado. La [rúbrica canónica](../calidad/evaluacion-escucha.md#31-fidelidad-de-instrucciones-y-naturalidad) distingue fidelidad y naturalidad.

Un fragmento de 90 segundos no verifica el crecimiento ni el final completo de Libre. La presencia de tags en tokens y un recibo válido no demuestran obediencia musical. La prueba no elige ganador sin escucha humana ni sustituye T-08–T-13, los diez briefs, los umbrales de M0 o la canción completa posterior. El consumo adicional permanece sin medir hasta ejecutarse.
