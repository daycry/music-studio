# ADR-0038 — Rechazo explícito de Host y Origin

- **Estado:** aceptada; revisión y QA técnica conformes, integración Git pendiente
- **Fecha:** 2026-10-07
- **Decisor:** orquestador, bajo delegación del propietario para elegir alternativas y continuar autónomamente
- **Ámbito:** M1/T-01; aclaración de ADR-0020 y CA14 de la spec aprobada

La revisión A detectó que la primera implementación devolvía400 para Host ajeno y permitía un Origin explícitamente ajeno en GET/HEAD. La spec exige403 para ambos rechazos. La excepción de ADR-0020 para GET/HEAD permite omitir Origin; no autoriza un Origin ajeno cuando se recibe.

Se conserva CA14: un Host único y bien formado fuera de la lista cerrada recibe403 `INVALID_HOST`. Si un transporte entrega a ASGI un Host ausente o duplicado, el middleware también lo rechaza403. El parser HTTP rechaza mensajes mal formados antes de ASGI con400 conforme a [ADR-0040](ADR-0040-frontera-parser-http-y-aplicacion.md); la ampliación inicial de403 a esa fase queda sustituida. Un Origin presente que no sea el único Origin permitido recibe403 `FORBIDDEN_ORIGIN` en cualquier método. GET/HEAD ordinarios pueden omitir Origin; SSE y los demás métodos exigen el Origin permitido. CORS mantiene su lista cerrada y el producto sigue publicado en loopback.

Se descartan adaptar la spec a400 y permitir Origin ajeno en GET/HEAD. Exigir Origin también a toda navegación y consulta ordinaria impediría comprobaciones locales sin aportar un requisito aprobado.

La corrección necesita RED contra el comportamiento anterior, revisión A/B/C y QA independiente con Docker. La revisión B también exige conservar `Allow` al convertir405 a RFC9457. [Revisión inicial](../roadmap/2026-09-28-m1-mvp-estudio/testing/t01/review1-report.md). No cambia la autenticación interna de engines ni añade sesiones, roles o acceso remoto.
