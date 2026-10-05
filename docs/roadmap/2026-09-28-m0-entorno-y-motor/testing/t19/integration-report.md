# Integración CPU y HTTP de T-19

Fecha: 2026-10-06. Esta evidencia precede a la revisión independiente y QA; no cierra la tarea ni acredita calidad musical.

La imagen reconstruida `music-studio/engine-acestep:m0-t19-preflight` incorpora la producción congelada de T-18/T-19. Identificador obtenido mediante `docker image inspect`: `sha256:13326c0f3aab17230ab05ec88d0ddecd414740f02900cc76caf47b965bb07801`. El build terminó con exit 0, reutilizando capas de herramientas y dependencias fijadas. Los locks no cambiaron y no se descargaron modelos. La etiqueta local `m0-t05` apunta también a esa imagen.

## Resultados ejecutados

| Comprobación | Resultado |
|---|---|
| Verificación declarada de cinco módulos | 120 passed, 1 skipped; exit 0 |
| Workspace completo explícito (`tests packages apps/engines`) | 355 passed, 5 skipped, 1 deselected; exit 0 |
| Suite ACE-Step y common dentro de la imagen | 133 passed, 1 deselected; exit 0 |
| Exportador de contratos | `engine-v1.json up to date`; exit 0 |
| Cuatro manifiestos legados | `all valid (4 manifests)`; exit 0 |
| Ruff global | `All checks passed!`; exit 0 |
| Cobertura oficial de statements añadidos | 327/354 = 92,37 %; mínimo por fichero 86,05 % |
| Probe nativo integrado | 16 casos, diez aceptados y seis bloqueados; exit 0 |
| HTTP real, ocho comprobaciones | Dos estimates aceptados y seis rechazos de estimate/jobs; exit 0 |

La [cobertura de implementación](implementation-coverage.json) cruza las líneas añadidas respecto a `83fc652` con statements ejecutados/faltantes de coverage.py. Incluye todos los statements de los dos módulos nuevos. El descriptor cambia literales, sin statements nuevos; su fichero tiene cobertura 30/30. La suite de cobertura tiene 222 pruebas CPU verdes y no se confunde su agregado histórico con el porcentaje del cambio. QA debe medirlo independientemente.

El [probe integrado](native-integrated-receipt.json) ejecuta la producción incluida en la imagen, el upstream fijado y tokenizadores locales verificados. CUDA oculta, sin GPU expuesta, sin pesos musicales ni forward. Coinciden entrada conditional/unconditional, reserva completa y ambos canales DiT. La captura distingue estos límites de una inferencia real. Conserva el candidato fiel: LM 1131/33 tokens y DiT 172/970. Todos los recibos anteriores permanecen intactos.

El [recibo HTTP](http-receipt.json) acredita el servicio reconstruido: el candidato fiel y un caption sintético de 600 caracteres reciben `input_budget` planned. Original que excede presupuesto, caption excesivo y duración 481 s reciben `INVALID_PARAMS`, HTTP 422, tanto en estimate como en jobs. Los jobs siguen sin existir (404), health sigue idle, loaded y job_id nulos. No se envía ningún job aceptable: la prueba no genera audio ni carga la GPU. El servicio se sustituyó después de comprobar que estaba idle y descargado. `STUDIO_ALLOW_UNVERIFIED=1` es una excepción local de laboratorio para validar estas rutas; las capacidades no pasan a verified.

## Fallos preservados y correcciones de fixtures

La suite completa inicial reprodujo seis fallos en tests anteriores de VRAM, semillas y shift: sus dobles de generación carecían de la nueva dependencia de preflight. Se corrigieron únicamente esos tres módulos, manteniendo los asserts originales y añadiendo comprobaciones de invocación por variante. Los controles de producción permanecieron congelados. RED: `root-full-suite.txt`, 6 failed/349 passed. GREEN: `fixture-full-suite-green.txt`, 355 passed. No se omitieron tests para obtener el verde.

Los primeros comandos Docker fallaron por preparación incompleta de la fixture: mock ausente o a profundidad incorrecta, temporales common sin montaje escribible y falta de los montajes/env propios del servicio. La ejecución final conserva profundidad de mock, caché privada escribible, modelos/datos solo lectura y `data/tmp` escribible; CUDA permanece oculta. Se ejecuta la producción de la imagen y los tests ACE-Step actualizados del host montados solo lectura. Evidencia final `container-suite6.txt`: 133 passed en 29,06 s. Las advertencias de terceros se conservan en las salidas, sin tratarlas como errores ni ocultarlas.

El primer probe HTTP exigía erróneamente status 400; el handler vigente declara 422 para INVALID_PARAMS. Se corrigió el script de verificación para usar el contrato existente; no se cambió la API. El segundo probe pasó todas las comprobaciones.

Las salidas completas, RED y comandos están en `.cache/dev-cycle/t19/`; contienen datos privados y no se publican. El [informe de implementación](implementation-report.md) aporta la evidencia TDD. Este tramo no modifica recibos T-17, los originales de Suno ni journals ajenos. La presencia de tags en tokens sigue sin demostrar obediencia musical.
