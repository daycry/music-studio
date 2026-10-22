# T-06 · Contrato del cliente de eventos

Este contrato precisa el cliente de [integration-design.md](integration-design.md).
No acredita la ruta HTTP, los escritores ni el cierre de T-06.

La suscripción recibe un consumidor de eventos normales y un consumidor
**obligatorio** de reemplazo completo del snapshot. Sin este último, se
rechaza la suscripción antes del bootstrap. El cliente no puede confirmar
un cursor de snapshot que ha ignorado ni transformar sus chunks en eventos
individuales. No existen consumidores productivos de la firma anterior en
la inspección del diseño; sus pruebas se adaptan al contrato explícito.

Si el consumidor cambia de canción desde el propio callback, la entrega
anterior no puede restaurar su cursor después del reset. La confirmación
ocurre tras una aplicación satisfactoria y sólo si el scope sigue vigente.
Una excepción del consumidor conserva el cursor confirmado anterior.

Una credencial sólo vive en memoria y pertenece a la suscripción, no a cada
conexión. Los cambios de canción y reconexiones conservan esa credencial;
el cierre definitivo solicita su revocación por `DELETE /api/session` con
header dedicado, sin retrasar indefinidamente el cierre. Los errores son
finitos y sanitizados; no se presenta una solicitud de revocación como
confirmación de que el servidor ya la ejecutó.

Esta precisión evita crear una sesión nueva por cada cambio de filtro y
abandonar las anteriores hasta el TTL de ocho horas. El registro real
admite 32 sesiones; la navegación normal no debe agotar ese límite.

La espera de cancelación de un stream tiene un límite declarado de dos
segundos, dentro del máximo de 30 s del diseño. Si no termina, se conserva
su promesa y estado desconocido, se informa de forma finita y no se afirma
cierre confirmado ni se abre otra conexión hasta resolver la incertidumbre.
La primera causa de fallo se mantiene. La suscripción no puede quedar
esperando indefinidamente al cleanup para informar del error o cancelar
una transición de scope. Si ofrece recuperación tras una finalización
tardía, debe comprobarla con una prueba causal.

El fix conserva los ocho archivos de ownership, todas las garantías
anteriores y los gates de revisión y QA. Cada escenario nuevo necesita
un RED conductual anterior a su corrección y una verificación completa
posterior sobre las fuentes finales.
