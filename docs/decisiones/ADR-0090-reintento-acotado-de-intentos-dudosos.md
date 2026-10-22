# ADR-0090 · Reintento acotado de un intento de engine dudoso tras un reinicio

- **Estado:** aceptada. El propietario la eligió el 2026-10-22, en M1/T-04, al preguntarle qué hacer con un job GPU dudoso: «Reintento acotado».
- **Fecha:** 2026-10-22.
- **Modifica:** ADR-0018 (Reintentos, Recuperación) y ADR-0043 (consumo de intentos). Actualiza `docs/arquitectura/sistema.md`.

## Contexto

ADR-0043 dice que un reinicio no consume intento y que el intento vigente se reenvía con el mismo ID y el mismo payload congelado. Ese reenvío solo es seguro si no hay salida previa, es decir, `last_seq == 0` y sin `tmp/<attempt>`.

En el caso **dudoso**, el engine ya había emitido eventos o había dejado una salida parcial antes del reinicio:

- reenviar con el mismo ID podría mezclar la salida nueva con la vieja;
- ADR-0043 prohíbe borrar esa salida a ciegas.

El código heredado dejaba el job `interrupted` y suspendido **sin límite**, sin camino de vuelta. Eso contradice CA-09 de M1 («interrupted → se reencola»).

## Decisión

1. Si el engine **confirma con una respuesta de estado válida** que no tiene el intento y el reenvío no es seguro (`last_seq > 0`, salida previa o reenvío ya hecho), el server registra para ese intento un terminal `error` sintético con `retryable: true`, y el job pasa a `failed`.
2. A partir de ahí actúa el reintento automático de siempre: un intento **nuevo** con otro ID y otro `tmp/<attempt>`, la misma petición congelada y la misma semilla. Este caso **consume** un intento del presupuesto (`max_attempts = 3`).
3. Si el engine no responde, o la respuesta no es un estado válido, nada cambia: el job sigue `interrupted` y espera. La ausencia nunca se deduce de un error de transporte.
4. El caso seguro de ADR-0043 (mismo ID, sin consumir intento) se mantiene igual.

## Consecuencias

- Una generación interrumpida a mitad acaba siempre en `succeeded` o en `failed` definitivo después de tres intentos. Ya no se queda colgada.
- En este caso, el reintento ya no depende de que el **engine** marque el error como `retryable`: lo marca el server, con la ausencia confirmada como prueba.
- El `tmp/<attempt>` del intento abandonado no se reutiliza. Su limpieza es la deuda B5 de T-04, que se trata junto a la fuga de temporales H5.
