# ADR-0050 — Autoridad canónica aislada del benchmark

- **Estado:** aceptada; dependencias de lease/proceso con aceptación técnica acotada; integración y aceptación global pendientes
- **Fecha:** 2026-10-08
- **Decisor:** orquestador bajo mandato autónomo explícito del propietario
- **Ámbito:** M0/T-09; desarrolla ADR-0042, ADR-0045 y ADR-0046

La autoridad online reside en un `OwnedProcess` canónico dedicado de sesión, separado del sensor WDDM y del worker de operaciones largas. `CustodyStore`, `CanonicalState`, sus referencias y el registro de vistas permanecen juntos en ese hijo; no se transportan handles ni se importan referencias de otro store. Esto conserva la selección de cápsulas de ADR-0046. Se descarta alojar la custodia en el supervisor: una llamada nativa bloqueada allí no puede terminarse dentro del presupuesto original.

El supervisor observa Job, PID y FILETIME reales y congela las anclas independientes del contenido de las cápsulas. El bootstrap sellado y la autenticación de sesión ligan contexto, epoch, carril y secuencia antes de admitir ingreso; un diccionario del caller o una ruta no crean autoridad. La protección confía en el supervisor y el sistema local; no promete aislamiento frente a otro proceso capaz de leer su memoria.

El IPC de esta sesión admite ingreso independiente del consumidor. Un scheduler canónico único prioriza ingreso entre pasos de lectura; checkout y finalización mantienen locks breves, y cada witness se realiza fuera del lock del estado. Los handles nativos siguen bajo su protección existente. Un read-view consume un plazo absoluto propio, incluyendo esperas, sin renovar dos segundos por cada witness. Limitar tamaños no prueba tiempo: un syscall bloqueado revoca la sesión. El watchdog del supervisor termina exclusivamente el Job canónico conocido sin adquirir locks de RPC, writer, auditoría o custodia. Sólo exit, EOF, joins y Job vacío comprobados acreditan devolución de recursos; hasta entonces el estado es cuarentena desconocida.

Espera, captura, transición, commit y publicación externa del episodio consumen el plazo original de dos segundos. El recibo original se congela antes de capturarlo. La ancla de finalización externa se mantiene separada para evitar hashes circulares. Commit sin publicación observada a tiempo no publica arrays aceptados ni conserva continuidad. No se acepta tarde ni se reintenta una operación de resultado incierto como si no hubiera ocurrido.

`RuntimeChannel` media vistas y operaciones materiales: sólo intercambia ingredientes seleccionados, referencias tipadas acotadas y tickets propios ligados a request, worker, epoch, cursor y prefix. JSON parecido, booleans de validación y tokens autofabricados fallan antes de efectos. Cada acreditación comprueba reloj externo actual, también cuando no existen datos nuevos. La transición semántica y los validadores compartidos siguen siendo únicos. Los witnesses de identidad de prefijo conservan coste lineal con cero payload histórico; no se presenta todo el sistema como O(delta).

Se autorizan extensiones aditivas cerradas `canonical_view` en publications y `renewal_base` apuntando directamente a una acreditación base inmutable. No eliminan sellos, contexto, comprobaciones materiales ni guardas de ciclo/profundidad16; el formato anterior permanece interpretable offline y ambas formas de renovación simultáneas se rechazan. Live v1/v2 continúa prohibido antes de efectos, incluso con proveedores inyectados.

La implementación se acepta por dependencias acotadas: primero leases y lectura por pasos; después bootstrap/ingreso/watchdog y mediación de callers. Cada módulo cambiado completo requiere cobertura actual≥80% sin exclusiones, RED funcional previo, revisión fresca y QA. El módulo runtime no queda aceptado por extraer un adapter ni por su cobertura previa aproximada del19%. La próxima revisión integrada mantiene intento4, sin reiniciar historial.

Packs≤32, FINAL desde EMPTY y restore tipado tienen aceptación separada. FINAL reconstruye originales, cápsulas, packs y anclas externas independientes; mutar un original suelto lo invalida aunque su cápsula online permanezca sana. Restore crea custodia, epoch y referencias nuevos; hasta su implementación y aceptación, reinicio live falla cerrado. Ninguna decisión de arquitectura acredita cadencia2,5s, plazo bajo bloqueo nativo,13h,160 outcomes, GPU, calibración o calidad musical.

[Contrato de integración](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/canonical-isolated-integration-design.md) y [decisión acotada](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/canonical-isolated-layout-decision.json).


El corte vigente de integración aplica [ingreso real y status/base independientes](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/canonical-current-integration-handoff1-design.md): cinco módulos productivos y un test nuevo. No activa el CLI ni emite tickets materiales; los consumidores aún no migrados fallan antes de efectos en ese modo. La autorización de implementación no acredita sus pruebas, revisión ni QA.


## Desarrollo de fuentes y presupuesto absoluto — 2026-10-09

[ADR-0059](ADR-0059-fuentes-y-presupuesto-absoluto-del-benchmark.md) adopta O2: verificador propio de fuentes, plazo absoluto desde la entrada y retención UNKNOWN de nacimientos o cleanup tardíos. Sustituye las ventanas renovadas por worker y las lecturas síncronas del supervisor fuera del presupuesto descritas anteriormente. Wiring y fixtures de contexto/plan coherentes se implementarán tras transferir las fuentes FIRSTcause; no acredita pruebas ni QA. Formal5 conserva formal3/4, rebateT10 y R09T13CLI pendiente.
