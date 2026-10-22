# Decisión root del diseño de dispatcher

Se elige O1: app.queue y tres unidades funcionales secuenciales. El diseño original conserva estado pendiente como evidencia de la recomendación anterior a esta decisión. No acredita implementación ni aceptación de la dependencia de esquema.

U1: admisión SQLite, backend HTTP y resolver; U2: eventos, reintentos, recuperación y cancelación; U3: cadenas, referencias y reintento manual. Rutas contractuales reales para cualquier ampliación futura: packages/contracts/song-v1.schema.json y apps/server/app/models/song-v1.schema.json; los paths song-v1.json/app/contracts propuestos en el original son incorrectos y no se usarán.

Las propuestas de nuevas tablas de eventos/recovery, fencing multiproceso e identidad de reinicio del engine quedan sin aprobar. Antes de U2 se compararán con el requisito real de T06: buffer limitado con estado actual cuando se agota. No se promete replay histórico ilimitado ni exactly-once del socket. U1 no debe asumir seguridad multiproceso, prueba de reinicio por versión ni resolver I-01 con resultados sintéticos. Wheel/Docker/imports stdlib se comprobarán en QA.
