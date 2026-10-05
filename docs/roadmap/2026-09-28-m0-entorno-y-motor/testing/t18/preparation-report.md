# T-18 — Preparación fiel antes de generar

Fecha: 2026-10-05. Alcance: preparación, procedencia y metadata opcional. La revisión y QA final se registran por separado; este informe no cierra la tarea ni acredita calidad artística.

## Qué cambia

La CLI conserva la letra por defecto y permite retirar explícitamente el envoltorio Markdown de las cabeceras. El recibo privado distingue los bytes fuente, los textos efectivos y sus diferencias; una adaptación manual del caption conserva su original. La generación usa la misma preparación y una referencia opcional en sus manifiestos nuevos. Tonalidad y compás se transmiten sin defaults inventados.

`original` es la petición antes de la transformación de tags; los bytes del material de origen declarado se conservan en `fields`. Por ejemplo, con un archivo de estilo original y un caption adaptado, `fields.style.original` guarda el original y la petición guarda el caption elegido. `explicit_style` y el diff hacen visible esa adaptación. El hash de archivo fuente no se confunde con el hash de texto UTF-8 efectivo.

La preparación se publica por SHA-256 en `data/preparations/`; una referencia del manifiesto apunta al recibo y lo verifica. El recibo externo debe conservarse junto con las publicaciones si se trasladan: no se afirma todavía exportación autónoma de proyectos, prevista en hitos posteriores. Los manifiestos existentes sin esta referencia siguen siendo válidos.

Al generar se publica un recibo con binding de ejecución: semilla base resuelta y cantidad de variantes. El origen conserva la petición anterior, incluida una semilla nula; `request.variant_index` permite verificar la semilla exacta de cada manifiesto. Un hash de letra declarado discordante con sus bytes fuente se rechaza antes de HTTP y también al verificar recibos externos. El campo `key` del descriptor mantiene su schema legado; las restricciones de la nueva opción CLI se aplican por separado.

## Prueba privada CPU

El probe ejecuta la CLI real con un endpoint local inaccesible, sin generación. El archivo privado de letra anterior ya tenía las nueve cabeceras españolas sin decoración. Para probar la limpieza se crea una derivación privada que añade exclusivamente `**` a esas cabeceras; no se presenta como el archivo Markdown original recibido.

La preparación resultante debe coincidir exactamente con las 72 líneas anteriores y sus nueve cabeceras completas. Debe conservar el caption original y el adaptado por separado, mostrar sus diferencias y mantener la autoría registrada `own`. El compás y la tonalidad permanecen omitidos porque no hay tónica ni compás declarados.

El probe comprueba los 32 registros de hashes de T-17 antes y después, repite la preparación para confirmar que no cambia su archivo ni fecha, y comprueba que los versos no aparecen en stdout/stderr. No carga modelos, no produce takes y no atribuye al modelo obediencia ni naturalidad. [Recibo CPU](preparation-receipt.json).

## Rúbrica para la evaluación musical posterior

Esta rúbrica acompaña a la entrada revisada cuando T-19 acredite el presupuesto y la metadata. Los valores quedan pendientes hasta la escucha; no se rellenan a partir de presencia de tags en tokens.

| Aspecto | Qué escuchar | Evidencia a guardar |
|---|---|---|
| Texto | Pronunciación peninsular, palabras omitidas o añadidas, tags que se canten accidentalmente | Sección y tiempo del audio; transcripción con suelo WER medido |
| Voces | Reparto hombre/mujer/dueto/coro, rap frente a canto y voz limpia al frente | Nota por sección, naturalidad y cumplimiento por separado |
| Ritmo | BPM solicitado, encaje de sílabas, groove y transiciones | Medición y escucha; distinguir cifra BPM de encaje vocal |
| Instrumentos | Piano, beat, cuerdas, metales, percusión orquestal y electrónica pedidos | Presencia y protagonismo por sección, evitando un sí/no global |
| Arco | Inicio íntimo, entradas progresivas, clímax de orquesta y coro | Tiempos de entradas reales; coherencia con las cabeceras |
| Carácter | Tonalidad mayor y sensación luminosa o serena | Análisis tonal más valoración humana, sin inventar tónica |
| Final | Retirada del arreglo, piano y últimas palabras audibles | Tramo final completo; un fragmento de 90 s no lo acredita |
| Referencia | Distancia frente al ejemplo Suno en voz, instrumentación y naturalidad | Escucha a nivel comparable; referencia artística, no control causal |

Las cabeceras no aportan timestamps: las observaciones se anclan al audio realmente producido. El recibo de preparación prueba transporte y procedencia; T-19 comprobará tokens, idioma LM y frontera efectiva. T-08/T-12/T-13 conservan la evaluación artística y decisión del motor. M0 sigue abierto.
