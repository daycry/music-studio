# ADR-0058 · Sesión pública local para eventos

- **Estado:** aceptada por delegación autónoma del propietario; implementación y verificación pendientes.
- **Fecha:** 2026-10-09.
- **Relacionadas:** [ADR-0056](ADR-0056-sse-con-buffer-y-recuperacion-de-estado.md) y [ADR-0020](ADR-0020-seguridad-local.md).

## Contexto y alternativas

El stream SSE necesita una credencial pública propia. El token interno de los engines no se entrega al navegador. El cliente actual consulta FastAPI directamente y no existe un proxy Next para toda la API.

Se compararon bootstrap con header y credencial efímera en memoria (A), cookie HttpOnly (B) y proxy Next del mismo origen con credencial del lado del servidor (C). Se elige A: conserva la ruta local actual, no añade servicios ni una pantalla de acceso y permite revocar lectores. B exige una política nueva de cookies entre los orígenes locales; C añade proxy y cancelación de dos transportes.

## Decisión

El server mantiene como máximo 32 sesiones en memoria, vinculadas al ULID del único usuario local activo. Las credenciales se generan mediante secrets.token_urlsafe(32), tienen duración absoluta de ocho horas basada en reloj monotónico y se invalidan al revocar, cerrar o reiniciar el registro. La validación utiliza compare_digest; el registro no persiste tokens ni los imprime. Los relojes y fuentes aleatorias inyectados se reservan a factorías internas de pruebas.

El bootstrap automático será POST /api/session/bootstrap, con body vacío, Origin exactamente configurado, Host loopback permitido y header X-Studio-Session-Bootstrap: 1. Devuelve la credencial pública y su vigencia con Cache-Control:no-store. El header propio exige preflight en el navegador; la política de CORS debe permitir únicamente método, path, origen y headers previstos. Origin no autentica procesos locales capaces de construir peticiones. No se añade acceso mediante Host server:8000 ni se confía en headers de proxy.

GET /api/events y DELETE /api/session usan X-Studio-Session-Token. No hay tokens en URL, cursor, cookies, almacenamiento persistente del navegador ni NEXT_PUBLIC. El cliente usa fetch con credentials:omit y conserva la credencial sólo en memoria. El navegador establece Origin; no se intenta escribirlo desde JavaScript. Expiración/revocación cierra el lector sin cancelar los jobs. Los errores son finitos y no devuelven la entrada original. La sesión no permite que el cliente elija owner_id; canción y jobs conocidos se autorizan antes de emitir datos.

La integración HTTP valida headers únicos, parámetros permitidos y permisos antes de iniciar la respuesta. Se generan OpenAPI y tipos del cliente en el mismo cambio compatible que registra los endpoints. La primera unidad sólo implementa el registro y los DTOs puros; no registra rutas, cambia main/security, escribe SQLite ni acredita CORS o autenticación HTTP. La política general Host/Origin existente se conserva.

La recuperación de ADR-0056 usa DTOs cerrados de estado de job y controles system.status begin/chunk/end; sólo end confirma epoch:H. Los límites siguen siendo 1.000 activos, 64 conocidos, 64 jobs por chunk, como máximo 17 chunks y 64 KiB por frame. No se inventa progreso para valores desconocidos. Se preserva TrustedScope original de 64 IDs; un feed dinámico con autoridad interna, publicaciones acreditadas y revalidación de replay se implementará explícitamente después. El diseño de datos no acredita esa autorización.

## Secuencia y verificación

Registro y DTOs puros primero; bootstrap/revoke y contrato después; barrera de escritores, lectura WAL, feed autorizado y transporte SSE antes de cliente/reducer y E2E. TDD conductual, cobertura de cada módulo completo >=80 % sin exclusiones, revisión fresca de seguridad y QA independiente. Las pruebas HTTP deben incluir origen ajeno, requests simples, headers repetidos, revocación, expiración y ausencia de reutilización del token de engines. Docker y navegador son gates posteriores. T06 permanece abierta.

## Fuentes primarias

La semántica de preflight y headers propios se verificó en [MDN CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS). La generación y comparación de credenciales se contrastaron con [Python 3.12 secrets](https://docs.python.org/3.12/library/secrets.html). Son fundamentos del diseño, no pruebas ejecutadas de nuestra integración.
