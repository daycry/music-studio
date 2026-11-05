# README: arranque verificado desde un clon nuevo

Última actualización: 2026-11-06.

**Resultado técnico parcial:** bootstrap Windows y recorrido integrado CPU/mock
verificados sobre el candidato público `faf4be75ae6fe84ef8f71649cb27ccb5002bf395`.
Esta prueba no cierra T-16 ni M1.

## Qué se ejecutó

Se creó el clon `.cache/r`, previamente ausente, y se siguieron las recetas del
README y de `docs/calidad/pruebas.md`. No se copiaron herramientas, intérprete,
dependencias, cachés, navegador ni pesos desde la instalación existente.
Docker reutilizó sus capas normales: no fue una máquina vacía ni un build
`--no-cache`.

El bootstrap instaló Python 3.12.14, Node 22.23.2 y pnpm 9.12.0 gestionados.
La preparación web precede al launcher, que conserva su comprobación de solo
lectura y sus hashes.

| Paso | Resultado | Duración |
|---|---|---:|
| Bootstrap Windows | exit 0 | 82,6 s |
| Inicialización del entorno | exit 0 | 0,3 s |
| Descarga y verificación de FFmpeg Linux | exit 0 | 19,6 s |
| Creación del ámbito aislado | exit 0 | 0,7 s |
| Arranque Compose, health y seed | exit 0 | 36,5 s |
| Descarga de Chromium | exit 0 | 24,6 s |
| Suite integrada | 14/14; gate exit 0 | 153,9 s |

Hubo **una** corrida integrada, sin fallos, flaky, skips ni interrupciones.
Incluye generación y publicación mock, reproducción, Range, descargas,
biblioteca, errores/reintentos, cancelación, tres anchos de pantalla y
SIGKILL/reconexión SSE. No sustituye las tres corridas de la
[QA Docker T-15](docker-ui-2026-11-05.md).

## Evidencia separada del host

`tests/test_web_tool_entrypoints.py` obtuvo 103/103 en 411,24 s de pytest.
Se ejecutó en el checkout principal con fixtures preparadas; no acredita
descargas frías. La regresión del bootstrap pasó de dos RED a dos GREEN,
y los cuatro casos focales finales pasaron. Las lentes A/B no registraron
gaps Critical, Important ni Minor.

## Identidad del despliegue

| Servicio | ID SHA-256 de imagen |
|---|---|
| web | `16005ab04d3e8d7241b00568671926559514eba9a33b786cf88743e72c90d3eb` |
| server | `d2ae013ef18abd9e051fa4cba3c00b2ca90246ce12e38f405a772dba2bad56d7` |
| engine-mock | `35ade97242660535f676960570f93c24c920cf57edb2b1d700b58fafd4d759fe` |

Los hashes de los 92 archivos Python del server y los siete del mock
coincidieron con el clon. Los tres contenedores tenían `DeviceRequests=null`.

## Límites y observaciones

Sólo se generó audio simulado CPU. No se ejecutaron ACE-Step/GPU, Ollama,
escucha o aceptación del propietario ni Claude CLI. La decisión de modelo
y la aceptación musical conservan sus puertas independientes.

El clon anidado emitió un aviso SWC de longitud de ruta 260 sin impedir
la corrida; no se ejecutó un build host Windows de ese clon.
Un `print` del arnés falló por cp1252 después de guardar el JSON y el exit 0:
no fue un fallo del gate. La observación EOL de un informe histórico
conserva hashes idénticos y diff vacío ignorando fin de línea; no se
atribuye al bootstrap.

Al finalizar la QA se retiró exclusivamente su stack: cero contenedores restantes,
puertos 3000/8000 libres y control liberado. Una reactivación posterior de la demo
por el orquestador se registra aparte en `CONTINUE-HERE.md`.
No hay PDF nuevo ni cambio de UI; esta evidencia no sustituye la aprobación visual M-02.

## Recibos locales

Estos enlaces apuntan a evidencia privada en `.cache/`, no distribuida por Git:

- [QA y tiempos](../../../../.cache/dev-cycle/20261105-t16-readme/qa-fixed/report.json).
- [Gate integrado](../../../../.cache/dev-cycle/20261105-t16-readme/qa-fixed/qa-gate.json).
- [Salida host](../../../../.cache/dev-cycle/20261105-t16-readme/qa-fixed/host-tests.stdout.log).
- [Regresión y focales](../../../../.cache/dev-cycle/20261105-t16-readme/fix1/implementation.md).
- [Revisión A/B](../../../../.cache/dev-cycle/20261105-t16-readme/review-1/verdicts.md).
- [Observación EOL](../../../../.cache/dev-cycle/20261105-t16-readme/qa-fixed/clone-newline-observation.json).
