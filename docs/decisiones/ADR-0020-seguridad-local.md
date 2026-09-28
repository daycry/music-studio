# ADR-0020 · Seguridad local sin autenticación

- **Estado:** aceptada · **Fecha:** 2026-09-28 · Precisa [ADR-0002](ADR-0002-personal-local-first.md)

## Contexto
Aunque no haya login, cualquier página abierta en el navegador puede atacar `127.0.0.1:8000`, por CSRF o por DNS rebinding. Además, Docker publica por defecto los puertos en `0.0.0.0`, así que quedan accesibles desde toda la red local.

## Decisión
- **Server:**
  - Valida `Host ∈ {127.0.0.1:8000, localhost:8000}`.
  - Exige `Origin == STUDIO_WEB_ORIGIN` en todo método distinto de GET y HEAD, y en el SSE.
  - CORS con una lista cerrada que solo contiene la web.
- **Engines:**
  - Los puertos se publican **siempre** como `127.0.0.1:P:P` en `docker-compose.yml`.
  - Exigen la cabecera `X-Studio-Engine-Token` = `STUDIO_ENGINE_TOKEN`, un secreto persistente que `scripts/init_env.py` genera una sola vez en `.env`.
  - Corren con `HF_HUB_OFFLINE=1` y `TRANSFORMERS_OFFLINE=1`.
  - Una red Docker `internal` impediría publicar puertos, así que el corte de salida a internet se consigue por configuración, no por red. Este límite queda documentado.
- **Subidas:**
  - Se valida el contenido real con ffprobe o Pillow, no la extensión.
  - Límites de tamaño y duración ([`../arquitectura/convenciones.md`](../arquitectura/convenciones.md) §5).
  - Se reencodifican antes de llegar a un modelo.
- **Secretos:** solo en el `.env` del server. Los engines nunca reciben claves de proveedores externos.

## Salida
Exponer la app en la LAN (acceso desde el móvil) exige un ADR con un token de acceso y TLS.
