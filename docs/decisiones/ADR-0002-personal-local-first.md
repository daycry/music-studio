# ADR-0002 · Uso personal, local-first, un solo usuario

- **Estado:** aceptada · **Fecha:** 2026-09-28

## Decisión
- La aplicación corre en la máquina del propietario y escucha solo en `127.0.0.1`. Sin autenticación.
- Hay **un solo usuario**, pero todas las entidades llevan `owner_id`.
- Sin GPU cloud por defecto. Los proveedores externos solo existen como alternativa opcional por función ([ADR-0014](ADR-0014-local-por-defecto.md)).

## Consecuencias
- Sale del alcance: cuotas, rate limiting por usuario, fairness, tope de gasto, login, 2FA y roles.
- Antes de exponerla en la red local o comercializarla: token de acceso y [gate GC](../legal/comercializacion.md).
