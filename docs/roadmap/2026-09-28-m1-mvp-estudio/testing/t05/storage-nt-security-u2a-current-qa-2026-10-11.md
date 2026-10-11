# QA actual de la unidad de seguridad Windows — 11 de octubre de 2026

**ROOT acepta únicamente el componente de observación y diagnóstico de seguridad. T-05 y M1 permanecen abiertos.** La revisión independiente A/B/C del [intento 2](storage-nt-security-u2a-review2-2026-10-11.md) no tiene gaps pendientes. La corrección TDD conserva 42 RED individuales anteriores a la reescritura y sus 42 GREEN posteriores.

| Plataforma | PASS | SKIP | FAIL / ERROR | Cobertura completa con ramas |
|---|---:|---:|---:|---:|
| Windows | 66 | 0 | 0 / 0 | 97,127937 % |
| Linux CPU | 43 | 23 | 0 / 0 | 76,501305 % |
| Combinada oficial | — | — | — | **97,127937 %** |

La cobertura combinada acredita 259/265 líneas y 113/118 ramas, sin exclusiones, y supera el gate del 80 %. La medición Linux individual queda por debajo del umbral porque este módulo contiene APIs exclusivas de Windows; se conserva su resultado real. Sus 23 omisiones corresponden a cinco testigos nativos Windows y 18 dobles que requieren funciones Win32 de `ctypes`. No se suman ejecuciones de revisores como pruebas adicionales.

## Integridad y adopción

ROOT verificó los 173 archivos regulares del freeze de QA, 78 archivos del snapshot —20 fuentes y autoridades más 58 archivos de su Git privado—, los JUnit, las bases y reportes oficiales de cobertura, procedencia real de imports y TAR de Linux. Se preservó el snapshot sin cambios.

Los archivos de producto aceptados son:

| Archivo | SHA-256 |
|---|---|
| `scripts/storage_journal_windows.py` | `91e279775c20561b14679845066f334f3af6d30fdc0a41a92ce5d0ee24af4b70` |
| `tests/test_storage_journal_windows.py` | `6671dbfccab19f2b9c8f7295b83513ebd21413d12759c0774de54d28f2bc5ad5` |

El freeze de QA es `b33cb6ed9dda1bda5437bdb941c27a3cdb8ec5f1af7d81a937c1eb4a7da4469f`. Los recibos de verificación y adopción de ROOT están bajo `.cache/dev-cycle/m1/storage-nt-security-u2a-root-20261011/`. La adopción copia exactamente estas dos fuentes, previamente ausentes, después de revisión y QA; no reescribe módulos existentes.

## Testigos nativos y recursos

Los cinco testigos Windows contrastan el principal de seguridad, un objeto propio con protección al crear, dos permisos peligrosos de terceros y la consulta de un padre existente sin cambiar su descriptor. Las observaciones se obtienen por handles prestados; la unidad libera sus descriptores y tokens propios y conserva los handles que no posee.

Un control frío conservado termina con diferencia inicial de ocho handles en el arnés de creación de fixtures. Su assertion de baseline global falla y se conserva como diagnóstico, sin atribuirlo al binding ni ocultarlo. Un control posterior separa el calentamiento real del fixture: `156 → 174 → 174 → 182 → 183 → 183 → 182`. Cien consultas no agregan handles; el dueño del fixture cierra el suyo y el préstamo continúa válido. Los procesos de prueba han terminado. Este control no acredita ausencia de cualquier fuga en toda la aplicación.

El contenedor CPU de QA emplea la imagen fijada `7c65be72…`, UID/GID 10001, red deshabilitada, raíz y fuentes de solo lectura, capacidades retiradas y `no-new-privileges`. Su TAR de 163.840 bytes, SHA-256 `422a94ace255b8defc09ea3cddf5e1ea6a7578739ed5b32d69f82a1e1817163e`, contiene 13 miembros regulares verificados. Se exportó antes de terminar y retirar el contenedor propio; PID final 0. El error inicial de `docker cp` sobre tmpfs se conserva: se recuperó el mismo TAR mediante lectura binaria sin repetir pytest.

## Límite del sello de consola

ROOT detectó que `POSTPYTEST.json` de Windows registró `stdout.txt` vacío antes de que el proceso vaciara su búfer al terminar. El archivo final tiene 1574 bytes, SHA-256 `9a5015e906ecd6ff41625fcec61400083fd249b676b58a8f07933a4bbdde3abc`, y queda autenticado por el freeze final de QA, **no por aquel sello anterior**. JUnit, cobertura, recibo e imports coinciden exactamente con sus sellos anteriores y finales. No se alteró el original ni se repitieron pruebas verdes.

## Alcance aceptado y siguiente frontera

Se acepta el parser, la política conservadora y los lectores de principal y seguridad por handle. Un diagnóstico local no concede capacidad de escritura, bootstrap, autoridad de una cadena ni admisión durable. TrustedInstaller continúa rechazado en esta unidad; el host conserva el rechazo de la cadena completa por permisos de terceros.

No se acredita store, writer, commit, ACK, recuperación tras crash, montaje ext4, VHDX de producto, lifecycle ni E2E de M1. Continúa la unidad de apertura relativa de objetos existentes y lectura de metadata y geometría, antes de ampliar la autoridad del controlador. Ruff y formato pasan; tokens, euros y horas reales quedan `null`.
