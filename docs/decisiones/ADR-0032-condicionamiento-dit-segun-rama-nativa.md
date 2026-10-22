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
