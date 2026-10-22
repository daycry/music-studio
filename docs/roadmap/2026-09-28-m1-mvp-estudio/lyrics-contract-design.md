# M1/T-03 — Contratos y análisis de etiquetas

El orquestador elige O1 bajo delegación: factoría sin escrituras durante construcción/exportación, contrato de API generado desde las rutas reales y parsers independientes Python/TS contrastados con casos compartidos. O2 añadiría un modo de exportación; O3 separaría constructores y aumentaría el riesgo de divergencia. [ADR-0019](../../decisiones/ADR-0019-contratos-code-first.md) sigue siendo la decisión del contrato.

T-02 tiene ownership de main.py hasta su entrega; la integración de T-03 espera esa liberación. Logging, migración y workers se inicializan en lifespan. El exportador no inicia lifespan, no usa datos ni secretos reales y proporciona configuración validada y neutral, con dotenv desactivado y valores independientes del entorno. No se usa model_construct ni se retira la seguridad. /health declara operationId, respuesta tipada y errores reales403/500 desde FastAPI; no se añaden respuestas manualmente al JSON exportado.

El exportador conserva byte a byte engine-v1 y sus mensajes, compara ambos contratos antes de informar en --check y no escribe en ese modo. La web genera api.d.ts desde el OpenAPI versionado y comprueba drift sin sobrescribir el destino. Tooling mínimo TS/Vitest/openapi-typescript, con versiones y licencias comprobadas; Next.js y la UI pertenecen a T-08.

El parser es puro. Devuelve versión1, original exacto, sections, annotations y warnings. Nunca modifica el estilo ni la letra ni activa la opción M0 strip_tag_markdown. Los rangos absolutos start/end, base0/final exclusivo, se expresan en unidades UTF-16 en los dos idiomas. Conserva BOM, CRLF, Unicode, asteriscos del cuerpo y todas las direcciones.

Una cabecera ocupa una línea completa, con espacio/tab horizontal opcional; admite corchetes solos o envoltorio Markdown doble completo. BOM inicial no impide reconocerla. No admite corchetes anidados. Dentro: alias, opcional número positivo seguro para JS sin ceros iniciales o FINAL y, opcionalmente, direcciones tras el primer separador ASCII « - ». El alias original se conserva; kind clasifica la estructura. La comparación reconoce mayúsculas/minúsculas españolas, incluidos acentos. Direcciones es texto literal: no se infieren voces/instrumentos ni se promete que el modelo obedezca todos los tags.

| kind | Alias |
|---|---|
| intro | intro, introducción |
| verse | verse, verses, verso, versos, estrofa, estrofas |
| pre-chorus | pre-chorus, pre chorus, precoro, pre-coro, preestribillo |
| chorus | chorus, choruses, coro, coros, estribillo, estribillos |
| post-chorus | post-chorus, post chorus, postcoro, post-coro, postestribillo |
| bridge | bridge, puente |
| hook | hook, gancho |
| break | break, pausa |
| instrumental | instrumental |
| solo | solo |
| outro | outro, salida |

Cada sección incluye kind, alias/aliasRange, number o null, qualifier final o null, headerRange, bodyRange, directions con text/range o null y empty. headerRange abarca la línea con su terminación; bodyRange va hasta la siguiente cabecera reconocida o el final. Vacío significa sólo espacios/tabs/CR/LF. Las candidatas que comienzan con corchetes o su envoltorio incompleto y fallan se conservan como annotations y generan MALFORMED_TAG o UNKNOWN_TAG; no abren sección. Corchetes dentro de texto ordinario no se interpretan como cabecera. EMPTY_SECTION señala la cabecera vacía. Advertencias ordenadas por rango y código; no son por sí mismas rechazo de generación.

Los resultados esperados de lyrics-cases.json se escriben independientemente de las implementaciones. Ambas suites consumen todos los mismos casos: tags Suno completos con RAP/CANTADO, alias, números/final, secciones vacías, desconocidos/malformados/anidados, envoltorios, texto normal, BOM/CRLF/astrales y offsets numéricos. Los casos sintéticos no contienen la letra privada completa de Libre.

Python vive en app/lyrics.py para empaquetarse con el server; TS en apps/web/lib/lyrics.ts. La integración preserva los tests de seguridad T-01 y migración/lifespan T-02 y requiere revisión/QA independientes. El diseño es una decisión previa a implementar; no acredita exportación, parser ni UI funcionando.
