# Diagnóstico de los fallos de SQL QA3

Fecha: 2026-10-09. Estado: causas focales contrastadas; corrección canónica,
revisión y QA conjunta pendientes. La verificación original conserva
**1026 PASS /27 FAIL /3 SKIP**, sin errores. No hay cobertura ni suplemento
Linux nuevos aceptados.

## Evidencia y resultado

Dos actores independientes clasificaron los25 fallos de scanning y los
otros dos. Un tercer actor hizo el diagnóstico focal privado; no será el
QA independiente de la corrección. Root cotejó resultados, salidas,
JUnit, variantes privadas y116 fuentes originales antes/después.

| Caso | Contraste ejecutado | Resultado e implicación |
|---|---|---|
| Reintento de intento incierto | Original frente a compartir sólo `resolver.synthetic_registry` con Admission | RED por procedencia no autorizada → GREEN. Las cuatro aserciones, intento prepared y terminal/procedencia NULL se conservan. No cambiar la política de reintentos. |
| Persistencia del token | Test idéntico, sin/con el recurso exacto `scripts/init_env.py` en el espejo | FileNotFoundError → GREEN. Las rutas temporales del test y sus controles de persistencia/formato/no divulgación permanecen. No se usa el `.env` real. |
| Scanning GPU, cabeza inválida | Registro declarado compartido; después ACK y residencia coherentes del doble | El registro permite alcanzar el fallo de ACK ausente. Añadir el ACK/residente positivo hace pasar las aserciones originales. No acredita aún los91 casos de la suite. |
| Cambio de identidad tras screen | Composición positiva correcta, inyección y aserciones originales | Sigue RED por ResolutionError con exactamente dos Health, versión1→changed. Job queued, attempt0 y ningún JobAttempt. Se necesita corregir el orden del cotejo, sin autorizar changed. |

Nueve ejecuciones focales:3PASS,6FAIL, cero errores/skips. Un primer
prototipo scanning omitió parte del wiring por un reemplazo textual
incorrecto. Se conserva y se excluye de causalidad; la comparación válida
usa el prototipo corregido. Los parámetros400/801 y sus plazos originales
no se ejecutaron en estos focales ni se alteraron.

La auditoría contractual recomienda conservar el aborto sin lease/reserva
cuando una observación fresca cambia respecto de routing. El control ya
existía después de resolve, pero la procedencia podía fallar antes.
[ADR-0068](../../../../decisiones/ADR-0068-descarte-de-identidad-obsoleta-antes-de-procedencia.md)
adelanta el cotejo usando esa misma observación, manteniendo los errores
explícitos de entradas inválidas y todos los controles de autoridad.

## Fuentes de evidencia y siguiente puerta

Los originales privados están en `.cache/dev-cycle/m1/`:
`t05-current-sql-independent-qa3/full-functional1056-none`, los dos
`t05-*-qa3-failure-review1`, `t05-identity-drift-contract-review1` y
`t05-qa3-causal-probes1`. Root selló el diagnóstico con recibo SHA-256
`08dc3dd602f6888ba712a4835cfde1d4a80b74fa03bb2dc8998bddbe61049ca0`.

Un implementer nuevo recibe ownership limitado a resolver/dispatcher,
dos fixtures y una prueba específica de drift. Debe ejecutar RED funcional
antes del código y conservar las34 firmas/decoradores/aserciones originales.
Después corresponden regresiones, revisión adversarial y QA independiente
completa de [ADR-0067](../../../../decisiones/ADR-0067-verificacion-vigente-del-esquema-sql-con-suite-completa.md).
Este diagnóstico no acepta SQL completo, publicación WAV, Docker, T05 ni M1.

## Corrección posterior, todavía sin aceptación final

El implementer nuevo aplicó el delta a resolver/dispatcher y a las dos
fixtures, y añadió ocho casos específicos. La única ejecución vecina
terminó **132 PASS /0 FAIL /0 SKIP**: scanning91, reintento manual33 e
identidad8. Root cotejó las cinco fuentes actuales,112 fuentes protegidas,
34 formas originales de pruebas y el JUnit. Ruff y formato pasaron.

La cobertura prerevisión está en curso sobre los dos archivos runtime
completos. Un primer intento falló durante la colección por configuración
de rootdir; no ejecutó tests y su cobertura de imports no es un gate.
El preflight corregido verificó1064 IDs y sólo801 deseleccionado para la
instrumentación. Se conservan ambas preparaciones y no se reescribe el
resultado rojo original. Revisión fresca, QA conjunta independiente con
seis fuentes completas y suplemento Linux siguen pendientes.

## Medición corregida y revisión del delta actual

La medición amplia detectó después cuatro fallos: dos observaciones de
catálogo omitidas por el filtro nuevo, y dos problemas de preparación
(lectura cp1252 de JSON UTF-8 y profundidad del temporal). El filtro se
movió después de la observación fresca;12 casos dirigidos pasaron. Dos
pruebas originales adicionales pasaron con UTF8 explícito y la profundidad
de temporales usada en QA3. No se modificaron snapshots, settings ni sus
aserciones.

La nueva medición sobre la versión corregida terminó con **1060 PASS,
0 FAIL,3 omisiones Windows originales y1 parámetro801 deseleccionado sólo
de instrumentación**. La cobertura completa de líneas y ramas es86,84%
para dispatcher y89,69% para resolver, sin excluir código. Root cotejó
JUnit, colección y fuentes actuales; no usa porcentajes de la versión
anterior para aceptar ésta.

Revisión adversarial de los cinco archivos actuales en curso. A/B/C son
actores nuevos; D se despacha al quedar una plaza. La verificación independiente
completa sin tracing, con801, las seis fuentes SQL/runtime y los tres casos
Linux sigue siendo necesaria. Esta medición prerevisión no cierra T05.
