# Experimento NT: rechazo de una junction real

**Hechos experimentales limitados verificados. T-05 y M1 siguen abiertos.**

La llamada relativa `NtCreateFile`, con `OBJ_DONT_REPARSE` y `FILE_OPEN_REPARSE_POINT`, abrió el alias mismo: NTSTATUS0/IOSB0/Information1. Su identidad correspondía a la junction, distinta del destino ordinario. El atributo reparse y el tag `0xA0000003` permiten rechazar ese objeto antes de conceder autoridad. Los indicadores de apertura, por sí solos, no demuestran que el hijo sea ordinario.

Se creó una junction únicamente en el directorio privado del experimento, sin habilitar privilegios ni modificar ACL existentes. `FSCTL_SET_REPARSE_POINT` tuvo éxito y `FSCTL_GET_REPARSE_POINT` devolvió los mismos560 bytes; DataLength552. Los nombres UTF16 y sus límites se comprobaron. No se siguió el enlace ni se efectuaron llamadas relativas de varios componentes. El control ordinario anterior y posterior mantuvo su identidad.

Las identidades, atributos y descriptores del destino, del archivo de control y del padre permanecieron iguales. El archivo de control se escribió60 bytes, se hizo Flush y se leyó antes y después sin diferencias. SHA256:31a6af1a329c5c4a8e5d5e1f44129c5c697df96af2537a3fc89788b274932f06. Ambos directorios y el archivo se conservan; no se afirma invariancia de timestamps ni de todos los siblings ajenos.

El intento nativo original terminó con exit1: contador170→171, aunque todos los handles propios registrados se invalidaron y cerraron una vez y quedaron cero scalars propios. Se conserva ese resultado. Un programa mínimo independiente aisló el incremento en la primera llamada UUID:145→146; las siguientes se mantuvieron en146. Un tercer proceso calentó UUID antes de fijar su baseline y permaneció146→146. No se atribuye identidad al handle interno ni se lo cierra, no se corrige retrospectivamente el contador original y no se repite la junction para obtener un verde.

ROOT verificó16 archivos regulares sellados,74 artefactos de experimentos anteriores y8 fuentes readonly. El inventario usa rutas explícitas; no recorre ni sigue la junction. Comprobación independiente posterior: los tres procesos propios ya no existían. El sello tiene SHA256:a970462f27e26d7020863ca4eac27ed52118146fdaff4fbeda52e4c37c694ec7.

Evidencia privada congelada: `.cache/dev-cycle/m1/storage-nt-reparse-probe-20261011` (raw-attempt01, raw-uuid-minimal, raw-uuid-control, logs, buffers, inventario y cleanup). Verificación ROOT: `storage-nt-security-u2a-review1-20261011/g1-verification-root.receipt.json`, checker y lectura independiente de PIDs. Comandos nativos reales con entorno gestionado: `uv run --frozen --no-sync --all-packages python <instrumento>`. Exit original1, controles UUID0. ROOT sólo relee evidencia; no vuelve a ejecutar el instrumento.

TDD/cobertura n/a: instrumento experimental, sin adopción de código. No acredita G1 completo de producto, confianza G2 de toda la cadena, journal, commit, replay, crash/restart, ACK, durabilidad eléctrica, publicación VHDX o montaje ext4. El lector U2a propuesto conserva su alcance local y no incorpora esta prueba como autorización operativa.

Véanse la [preparación NT](storage-nt-preparation-2026-10-11.md), la [política S1](../../storage-nt-security-policy.md) y el [informe global](../current-validation-2026-10-10.md).
