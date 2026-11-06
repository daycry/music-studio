# ADR-0032 — Condicionamiento DiT según la rama nativa

- **Estado:** aceptada
- **Fecha:** 2026-10-06
- **Decisor:** orquestador, con la autorización del propietario para implementar el roadmap y elegir las mejores alternativas
- **Ámbito:** corrección de integración M0/T-16; complementa ADR-0029

## Contexto

La [toma diagnóstica SFT de 30 s](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t16/native30-failure-report.md) falla en la guarda de tokens del DiT. El [diagnóstico CPU con fuente y tokenizadores fijados](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t16/native30-diagnosis-report.md) reproduce la causa: el plan calcula siempre la instrucción de `text2music`, pero el handler cambia a `cover` y a su instrucción cuando el LM proporciona códigos de audio no vacíos. La letra permanece íntegra. La comprobación de fidelidad detecta una diferencia legítima que el plan no contemplaba.

Esta resolución interna sirve para condicionar la generación con códigos del LM. No habilita una nueva operación pública de cover. El intento GPU no conservó los IDs finales ni una captura directa de la rama resuelta; los conteos del contrafactual CPU no se presentan como mediciones GPU.

## Alternativas

| Alternativa | Ventaja | Riesgo |
|---|---|---|
| Desactivar la guarda de tokens | Evita el rechazo actual | Permite pérdidas o cambios de instrucciones sin detectar |
| Planificar siempre la instrucción cover | Corrige el caso con códigos | Falla ante la rama legítima sin códigos y supone una salida futura del LM |
| Medir las ramas posibles y validar la resolución efectiva | Conserva las guardas y ambas rutas | Requiere extender el perfil, las capturas y la validación de recibos |

## Decisión

Medir antes de cargar modelos las dos ramas legítimas del código fijado. Ejecutar los métodos puros originales de resolución y formación de instrucciones, con sus SHA incorporados al perfil; no copiar sus textos manualmente. Comprobar el presupuesto completo de todas las ramas posibles, sin truncar caption, letra o metadata. Los límites de ADR-0029 se mantienen.

Capturar en el hijo el tipo inicial, la presencia de códigos como booleano, el tipo resuelto y el hash de la instrucción. Conservar la semántica nativa para strings y listas, incluidos vacíos y espacios. Los recibos no incorporan el contenido de los códigos de audio.

Validar la instrucción que llega a `_prepare_text_conditioning_inputs` contra la resolución capturada y la rama planificada. Después comprobar el conteo y SHA exactos de los tokens de descripción y letra. Una instrucción desconocida, una rama incoherente o un cambio no autorizado de contenido sigue siendo un error. La ausencia de códigos mantiene la ruta legítima de `text2music`.

El recibo planned declara candidatos y presupuestos; el captured declara la rama activa y los tokens comprobados. El llamante verifica su correspondencia antes de publicar. Conservar la compatibilidad de lectura de recibos históricos sin reescribirlos; los recibos nuevos deben declarar su perfil actual y no validar capturas antiguas como si incluyeran esta frontera.

## Verificación y límites

TDD con métodos y tokenizadores originales: ambas ramas, Turbo/SFT, códigos vacíos y listas, mutaciones de instrucción/texto/letra, presupuestos al límite y por encima, y recibos de rama incompatible. Mantener la preparación fiel, la reserva LM, los controles SFT/Turbo y todos los hashes históricos.

Revisión independiente y QA CPU preceden a la ejecución GPU. Después comprobar la captura de la rama en una generación real y retomar las seis tomas de comparación. No se desactiva ninguna guarda de VRAM, no se cambian pesos ni el motor por defecto, y no se declara calidad musical por superar esta validación.

## Ampliación compatible: observaciones de condicionamiento — 2026-11-06

[`input_capture`](../../apps/engines/acestep/adapter.py) amplía las cinco etapas de captura v2 con dos campos opcionales observados. `dit_resolution.audio_codes_sha256` aplica [`digest`](../../apps/engines/acestep/preflight.py) al envelope `{'audio_code_string': codes}`. `codes` es el argumento real enlazado por la firma del resolver DiT; se registra tras validar la resolución. El JSON canónico UTF-8 conserva tipo (`str`, lista o `None`), espacios y orden de lista. No guarda códigos en claro ni sustituye el valor por el plan o por `has_audio_codes`. `lm_arguments.lm_backend_observed` lee `runtime.lm.llm_backend` en la llamada LM: si existe, debe ser el string `pt`; una contradicción se rechaza. Si falta el atributo, se omite el campo, sin inferir PT del pedido o de la configuración. Esta observación acredita esa frontera LM, no una inicialización histórica ni CUDA. La huella acredita la entrada raw exacta al resolver DiT; no acredita identidad de latentes, transformaciones posteriores ni obediencia musical.

[`validate_input_receipt(payload, request, index, *, private_params=False, require_conditioning=False)`](../../packages/audio-post/audio_post/manifest.py) conserva la lectura histórica v1/v2 sin los campos. Si aparecen, exige SHA-256 hexadecimal minúsculo de 64 caracteres y backend observado `pt`, además de las comprobaciones existentes. `require_conditioning=True` exige v2 y ambas observaciones válidas. Valida un recibo individual: no compara dos huellas. Un futuro comparador deberá validar cada recibo con ese modo y contrastar huellas, backend, texto/metadata y controles LM existentes; dos ausencias no prueban igualdad. La auditoría privada `.cache/dev-cycle/20261106-m0-t16/qa/{report.md,additional.json}` acredita 41 tests CPU, seis MP3 y seis fuentes válidos, y hashes de caption/letra del control T-15 coincidentes. Esos recibos carecen de ambas observaciones y no certifican emparejamiento completo; permanecen intactos. El fix registra 230 tests focales y 41 canónicos verdes en `.cache/dev-cycle/20261106-m0-t16/fix1/evidence.md`, con un fallo Windows intermitente en la suite ampliada de esa fase, anterior a la corrección de identidad y a QA2. La extensión no cambia HTTP `/v1` ni manifiesto v1. Las futuras generaciones GPU y la escucha del propietario siguen pendientes; M0/T-16, M0 y M1 continúan abiertos, sin ganador SFT/Turbo.

La [QA2 independiente del 2026-11-06](../roadmap/2026-09-28-m0-entorno-y-motor/testing/condicionamiento-cpu-2026-11-06.md) acredita `PASS_CPU_SOFTWARE_ONLY`: una corrida con 437 aprobados, 9 omitidos y 0 fallos (446 casos, 23,11 s). Cubre 18/18 statements afectados frente a `3dede62`; en pipeline, la expresión de la línea 38 se atribuye al `Return` de la 32. La cobertura de directorios completos es 74,56 %, sin afirmar un 80 % global. Los recibos privados son `qa-fixed2/report.md` y `qa-fixed2/summary.json` bajo el mismo directorio de evidencias. Este verde CPU no completa el emparejamiento histórico ni acredita GPU, calidad musical o cierre de T-16, M0 o M1.
