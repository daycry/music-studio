---
id: ADR-0076
titulo: Admisión estricta S1 y owner TrustedInstaller sólo en el ancla del sistema
estado: aceptada
fecha: 2026-10-11
iniciativa: 2026-09-28-m1-mvp-estudio
opcion: S1
elegida_por: ROOT bajo delegación vigente del propietario
eleccion_fecha: 2026-10-11
revision_documental: A/B conforme, intento 1; aceptación documental de ROOT
fuente: ../roadmap/2026-09-28-m1-mvp-estudio/storage-nt-security-policy.md
---

# ADR-0076 · Admisión estricta del dominio del journal NT

## Contexto

[ADR-0075](ADR-0075-recibo-durable-y-ciclo-de-vida-del-almacenamiento.md) fija el journal estable O2 con custodia por handle y CAS. G2 necesita concretar owner, trustees, ACE efectivas/heredables y seguridad del prefijo. Una DACL cerrada del leaf no neutraliza DELETE_CHILD, WRITE_DAC o WRITE_OWNER del padre. [Microsoft: DeleteFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-deletefilew).

Una observación actual por nombre detecta grants MODIFY de SIDs no acreditados en workspace y `.cache`. No prueba política por handle ni ausencia de esas cuentas. Un positivo privado del leaf no valida automáticamente la cadena. El root del sistema tiene un owner de servicio que exige una excepción acotada.

## Decisión elegida

ROOT eligió **S1** por delegación vigente del propietario. La [política](../roadmap/2026-09-28-m1-mvp-estudio/storage-nt-security-policy.md) exige owner/DACL por handle y rechazo de grants efectivos outsider peligrosos en dominio, journal y todos los padres. Parseo desconocido o incertidumbre cierra admisión. No se mutan ACL existentes para pasar.

Sólo el principal autorizado, SYSTEM y Administrators integran la allowlist ordinaria. La única excepción es **owner TrustedInstaller en el root real del volumen del sistema Windows**, acreditado por SID exacto de la cuenta de servicio Windows y por el papel del handle. No se extiende a otro root, servicio, trustee explícito de mutación, padre, dominio o journal. Los SIDs de servicio se acreditan mediante los mecanismos Windows; no por prefijo o nombre del owner candidato. [Microsoft: SERVICE_SID_INFO](https://learn.microsoft.com/en-us/windows/win32/api/winsvc/ns-winsvc-service_sid_info).

La política interpreta ACE IO y herencia por componente, distingue creación de siblings de reemplazo del hijo y rechaza derechos de mutación del prefijo. Crear exige objeto nuevo, descriptor cerrado protegido desde NtCreateFile y FILE_CREATED; no adopta preexistentes. Sharing, revalidación y CAS permanecen complementarios; bytes/hash/owner aislado no conceden capacidades.

## Alternativas descartadas o aplazadas

- **S2, dominio privado durante lease:** permitido sólo como evidencia experimental de objetos nuevos. No constituye política de producción/restart ni positivo G2 completo.
- **S3, prefijo exterior mutable con dominio persistente:** aplazado. Replay de un dominio antiguo auténtico, bootstrap/reparse y custodia del código requieren una asociación activa independiente y otra decisión. No se implementan binding, token o controller.
- **Confiar en SIDs no resueltos, ampliar grupos o editar ACL existentes:** rechazado; no hay acreditación ni autorización para esas remediaciones.

## Motivo y consecuencias

S1 preserva la frontera vigente y reduce cambios. Si los handles confirman los grants observados, el host devuelve el diagnóstico G2 SECURITY_UNACCREDITED sin efectos. Se conserva ese diagnóstico documental existente; no nace una API pública, enum o endpoint.

La decisión no reabre O2, ADR-0075 o U1 aceptada, ni modifica wire W1–W6. No libera U2, provisión, SMOKE, VHDX, runtime, montaje o admin. La excepción acotada no afirma que el host ya la haya acreditado. Implementación y QA nativas siguen pendientes; T-05/M1 no pasan a verde.

El deployer/controller conserva su supuesto de confianza de ADR-0075. Este ADR no demuestra protección nueva del código ni resistencia al mismo SID malicioso o administrador. Cualquier cambio futuro de esa frontera exige otro ADR.

## Estado

Aceptada documentalmente por ROOT bajo delegación del propietario, tras revisión fresca A/B conforme en el intento 1. Esta aceptación no acredita implementación, permisos del host ni aceptación de T-05 o M1.
