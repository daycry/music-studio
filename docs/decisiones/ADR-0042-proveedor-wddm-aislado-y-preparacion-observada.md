# ADR-0042 — Proveedor WDDM aislado y preparación observada

- **Estado:** aceptada; implementación, revisión y QA pendientes
- **Fecha:** 2026-10-07
- **Decisor:** orquestador, bajo delegación autónoma del propietario
- **Ámbito:** M0/T-09, corrección de R09-T01 y R09-T02; complementa ADR-0039

Las lentes A/B/D corroboran dos Important. Una consulta síncrona retorna después de2s y la persistencia final queda fuera del reloj comprobado. La continuidad v2 atraviesa create/start/wait-health/verificación sin observaciones; una preparación de3s aborta antes de inferencia. Rechazar después o reiniciar el predecesor no resuelve esos defectos.

Un arquitecto fresco comparó proceso nuevo por episodio, proveedor persistente aislado con coordinación independiente y procesos separados por sensor. Se elige proveedor persistente: mantiene recursos DXGI/PDH dentro de un proceso propio y reduce apertura/IPC por tick. El coordinador conserva una única cadena durante preparación, ejecución y cierre, también mientras se copian/verifican pesos.

El proveedor y sus descendientes tienen ownership verificable y terminación acotada mediante Job Object Windows, sin carrera de asignación ni cierres de procesos ajenos. No se transportan handles ctypes. Un bloqueo se interrumpe con el presupuesto original restante; no se confía en cancelar un Future para interrumpir una llamada nativa. Los valores que nunca retornaron no se inventan: la adquisición interrumpida conserva la evidencia parcial disponible y queda rechazada.

Se conserva cada RAW completo antes de clasificar. Los episodios, aceptación y continuidad se preparan y persisten antes de publicar un commit verificable. El cómputo comprende adquisición, validación y persistencia real, incluido el commit; una finalización tardía no avanza el predecesor ni entra en métricas aunque existan bytes preparados. El validador offline recalcula las referencias, relojes y finalización, y conserva registros rechazados/interrumpidos.

No se amplían2s por episodio,2,5s de cadencia ni los otros umbrales de ADR-0039. Las operaciones largas de preparación conservan sus propios plazos y se observan concurrentemente. Una creación Docker cuyo resultado sea incierto exige recuperación por ownership, sin repetir create ni inferencia. Cerrar su cliente no prueba que se haya cancelado la acción remota.

Se introduce política **wddm_auto_v3** y protocolo explícito de publicación de episodios. V1/v2 históricos conservan su interpretación y no acreditan este mecanismo. Fuentes y módulos nuevos se sellan; plan160, piloto y acreditación serán nuevos. /v1, engines, imagen y pesos permanecen intactos. La medición shared mantiene provider_verified/independent=false y no acredita cero spill.

La corrección exige RED de ambos defectos, pruebas de bloqueo real de proceso/descendiente, persistencia/commit lento, cadena continua en preparación>3s, RAW con fallo posterior y recuperación sin duplicados. Una sonda Windows con LUID/PDH/ctypes reales y cero inferencia comprueba aislamiento y limpieza. Revisión y QA independientes preceden cualquier carga GPU. No se promete planificación de SO en tiempo real ni durabilidad física de disco.

[Revisión con gaps](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/transition-review1-report.md). T-09 permanece abierto.

La [ADR-0045](ADR-0045-recuperacion-y-transporte-de-auditoria-del-benchmark.md) precisa la disposición tras timeout y el transporte incremental de auditoría. Conserva la política v3 y la validación canónica final; su implementación y QA siguen pendientes.


**Desarrollo de integración:** [ADR-0050](ADR-0050-autoridad-canonica-aislada-del-benchmark.md) fija la autoridad online en proceso propio, lectura por pasos e ingreso prioritario. La ratificación del diseño no acredita implementación, plazos, FINAL ni rendimiento.
