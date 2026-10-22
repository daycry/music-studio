# Revision de continuidad R09-O7 (T-09)

A+B+D: 0 Critical / 0 Important / 0 Minor. Global7, sin reiniciar historial. Tres contextos nuevos leen paquete exacto; no ejecutaron pruebas ni verificaron hashes live. Root cotejo67fuentes/12docs. PrimerA porCLI sin lecturas NO contado. Capacidad de colaboracion agotada; fallbackCLIefimero de sololectura con paquete inline, sin cambiar permisos.

## Lente A

**Lente A — sin hallazgos de requisitos o constitución en el delta R09-O7.** La evidencia aportada respalda la corrección CPU; T-09 y M0 siguen abiertos. No he realizado nuevas ejecuciones, recalculado hashes ni comprobado el sistema de archivos.

| Criterio | Resultado | Evidencia y límites |
|---|---|---|
| T-09 → matriz de configuraciones y duraciones | Pendiente | `tasks.md:407`; este delta no acredita generaciones ni matriz. |
| T-09 → comparación bind mount/copia | Pendiente | `tasks.md:408`; sin mediciones nuevas. |
| T-09 → descarga de Ollama y VRAM en reposo | Pendiente | `tasks.md:409`; sin preflight GPU nuevo. |
| T-09 → navegador visible y observación de desbordamiento | ✓ parcial | `benchmark_runner.py:53` y `:69` monitorizan las dos llamadas bloqueantes en `wddm_auto_v1`. No certifica observación real bajo carga. |
| T-09 → experimento opcional `torch.compile` | Pendiente/opcional | `tasks.md:412`; fuera de este delta. |
| T-09 → recomendación basada en números | Pendiente | `tasks.md:413`; no se presenta una recomendación prematura. |
| Alcance declarado | ✓ | Los dos ficheros del diff pertenecen a módulos/pruebas de `scripts/eval/`, declarados en `tasks.md:401`. El recibo de alcance declara cero ficheros fuera de alcance. |
| Tests de la corrección | ✓ | Lectura completa de los tests aportados: estimate y resume lentos, errores, pérdida de observación, intención preservada, identidad/estado, terminal, petición inmutable y rama manual. |
| Constitución | ✓ | Sin infracción explícita introducida por el delta. T-09 permanece `en-progreso`, coherente con `docs/CONSTITUTION.md:33`. |
| Verificación de tareas cerradas | No aplica | La única tarea proporcionada está abierta (`tasks.md:395`). Su verificación GPU/matriz no se declara ejecutada por esta entrega. |
| Interop/E2/E3 | No aplica | El diff aislado no toca `commands/`, `agents/` ni `hooks/`. |
| OpenAPI | No aplica | El diff aislado no modifica una especificación OpenAPI. |

La secuencia conserva las garantías visibles: estimate debe terminar antes de escribir la intención (`benchmark_runner.py:79`); resume consulta el mismo job y no entra en el envío (`:51`); `NOT_FOUND` exige otro intento (`:64`); la validación de identidad/estado sigue delegada a `resume_action` (`:67`). Las ramas manual y legacy conservan las llamadas síncronas mediante el discriminador explícito.

Los recibos aportados declaran **229 tests de producto y 32 privados sin fallos**, suite final con exit code 0 y cobertura **228/265 = 86,04 % del módulo completo**, sin exclusiones. Esto no es cobertura del diff ni cobertura de ramas. Los RED aportados muestran ambas pérdidas de continuidad originales.

**Gaps:** Critical 0 · Important 0 · Minor 0.

**Límites de la revisión:** faltan los cuerpos de `validate_samples`, `resume_action` y los fixtures de `test_benchmark_observation` para comprobar independientemente sus reglas internas. Su comportamiento queda respaldado por los tests y recibos aportados. Se mantiene la preocupación declarada sobre la espera del hilo hasta el límite de transporte de 70 s; no aparece evidencia nueva para reabrirla. QA y validación GPU siguen pendientes.

## Lente B

**Lente B, observabilidad 7 / R09-O7: sin defectos nuevos identificados en el delta proporcionado.** Critical: 0 · Important: 0 · Minor: 0.

| Criterio | Resultado y evidencia |
|---|---|
| Estimación observada | ✓ `benchmark_runner.py:69`: `wddm_auto_v1` usa el monitor existente antes de escribir estimación e intención. |
| Reanudación sin duplicar envío | ✓ `benchmark_runner.py:51`: monitoriza el GET; conserva la rama sin POST y el tratamiento de `NOT_FOUND`. |
| Fallos e intención | ✓ `benchmark_runner.py:79`: un fallo de estimación o guarda impide alcanzar la escritura de intención y el envío. |
| Identidad, petición y terminal | ✓ Se mantienen las comprobaciones en `benchmark_runner.py:31`, `:39`, `:67` y `:98`; el delta no las omite. |
| Métodos manual y legado | ✓ Las condiciones en `benchmark_runner.py:60` y `:76` conservan las llamadas síncronas para métodos distintos de `wddm_auto_v1`, incluido el campo ausente. |
| Hilo de operación | ✓ El helper aportado usa un executor con cierre y propaga `future.result()`. Se conserva la preocupación declarada sobre esperar al transporte cuando falla la guarda. |

La evidencia CPU aportada declara 229 pruebas de producto, 32 privadas y cobertura **228/265 (86,04 %), sin exclusiones**, del módulo completo. No constituye cobertura específica del delta.

**Sin nuevas ejecuciones de runtime**, herramientas ni recálculo independiente de hashes. La implementación completa de `validate_samples`, `resume_action` y el transporte API no está incluida: su comportamiento interno queda fuera de la comprobación independiente de este paquete. La corrección real del hueco de 15,6891821 s sigue pendiente de validación GPU; T-09, la matriz y M0 permanecen abiertos.

## Lente D

**Lente D: sin hallazgos de rendimiento introducidos o reabiertos por el delta R09-O7.** Critical: 0 · Important: 0 · Minor: 0.

| Criterio | Resultado y evidencia |
|---|---|
| Estimate lento | ✓ `benchmark_runner.py:69–78`: una llamada monitorizada por ejecución automática. Permite muestrear durante la espera sin añadir solicitudes HTTP. |
| GET de reanudación lento | ✓ `benchmark_runner.py:53–67`: una consulta al mismo job; no introduce reenvíos ni consultas por muestra. |
| Volumen previsto: 160 jobs | ✓ Dos puntos de monitorización alternativos por ejecución, con un trabajador por operación. No aparece N+1 ni concurrencia creciente con el tamaño de la matriz. |
| Fallos, intención e identidad | ✓ El delta conserva el orden de persistencia, tratamiento de `NOT_FOUND` y validación de identidad/estado. Los controles aportados cubren estos escenarios. |
| Terminal, petición y modo manual | ✓ Las comprobaciones previas permanecen; la rama manual mantiene llamadas síncronas. |
| `sleep` que activó D | ✓ `benchmark_runner.py:197` permanece sin cambios; este delta no introduce una degradación concreta en ese punto. |

La espera del hilo al perder observabilidad, limitada por el transporte declarado de hasta 70 s, sigue siendo una preocupación conocida; no aporto un hallazgo nuevo sobre ella.

**Sin nuevas ejecuciones runtime.** Revisé únicamente el contenido inline; no ejecuté tests ni recalculé hashes. El paquete declara 229 tests de producto, 32 privados y cobertura del módulo completo de **228/265 (86,04 %), sin exclusiones**. La cadencia real bajo GPU sigue sin verificarse; T-09, sus criterios completos y la matriz permanecen abiertos.

QA independiente/GPU nuevas pendientes. Riesgo heredado de espera de hilo limitado por transporte conservado.
