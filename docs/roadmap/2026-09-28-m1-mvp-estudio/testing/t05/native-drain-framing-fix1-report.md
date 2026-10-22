> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# Drain: entrega de componente, sin aceptación

Cambio mínimo en custody.py: todo chunk stdout entra al decoder existente aunque parsing=False; se consume entero su generador. _message sólo se ejecuta mientras parsing=True y stop no está activado. Framing, schema, secuencia, cuota acumulada y EOF usan el decoder original; bad sigue sticky. No se guarda otra copia completa de salida; stdout/stderr siguen acotados a 16 KiB. No cambios en backends, supervisor, protocolo, contratos o fixtures.

RED: test_real_wire_held_until_draining_retains_owner[truncated] falló con CLOSED_CONFIRMED/cancelled y release_gate=True frente a UNKNOWN_QUARANTINED · 2026-10-09. Bytes reales 000000107b retenidos por una lectura física, entregados durante DRAINING. Terminate y close reales True, sin sustituciones de autoridad. Prueba escrita antes de producto; fuente archivada antes del run; JUnit assertion genuina, sin EBADF. Testigo vivo antes de assertion/rescate y waitpid real posterior [9,0]. Focal GREEN Linux2 PASS. Antecedente EBADF diagnóstico no es RED; calendario QA anterior y terminateFalse histórico siguen UNKNOWN.

linux: 40 PASS / 1 FAIL / 0 ERROR / 0 SKIP; windows: 46 PASS / 0 FAIL / 0 ERROR / 0 SKIP

Linux tiene nueve casos nuevos y Windows diez: held truncated/invalid, válido sin efectos en Windows, y siete fronteras de pipe físico por OS: valid/schema/valid-before-bad/truncated/quota/final-EOS/length. Estas fronteras usan grupos reales y pipes propios; ejercitan _read directamente y no se presentan como certificados de terminación. El test Windows normal observa el decoder completo de result/closed sin _message/queues/saw_closed. Los 68 originales mantienen funciones, AST, asserts, decoradores y parámetros.

El original Linux backpressure falló con CLOSED_CONFIRMED; queda sin parche ni debilitamiento. No se demuestra su causa ni equivalencia con la QA histórica67/1. No aceptación ni suite final completamente verde. Root debe adjudicarlo antes de QA independiente y cierre. Los nuevos casos se conservan sin pedir retornos kernel True para fabricar éxito.

Cobertura WHOLE oficial líneas+ramas, cero exclusiones, sólo RAW de la pareja actual UUID 66649042-8205-44dc-af3e-00bb977fed03, incluidos hijos Windows/Linux actuales, copias antes de combine --keep:
- apps\server\app\worker\custody.py: 87.83783783783784%; excluidas=0
- apps\server\app\worker\custody_linux.py: 85.88588588588588%; excluidas=0
- apps\server\app\worker\custody_linux_supervisor.py: 81.65137614678899%; excluidas=0
- apps\server\app\worker\custody_windows.py: 88.18897637795276%; excluidas=0

Sólo facade custody.py es producción modificada. Cobertura de backends/supervisor, si aparece, se incluye como observación de fuentes intactas, no ownership ni nuevo gate de producción modificada.

Límites de evidencia: el runner focal GREEN sobrescribió nombres de comandos/metadata del RED. Se conservan fuente física, fixture/herramientas precopiadas, JUnit, prueba anterior a assertions/rescate y native-call-used/CID del RED; metadata completa de comandos RED es PARCIAL, no se reconstruye. Snapshots pidfd RED posteriores a close muestran invalid/UNKNOWN; waits reales están en disposition del backend. Los tests adicionales no se reclaman como RED independientes: son cobertura de fronteras tras RED causal y mínimo fix. TCB explícita OS/kernel/libc/base interpreter/stdlib; no cierre exhaustivo de imports transitorios. Horas/tokens/EUR/modelo NULL sin fuente del proveedor; CLI originales reservados intactos.

Primer final01 incompleto por timeout privado launcher180s; history conserva fuentes/RAW/argv y contenedor remove0/gone1. Final02 reparó launcher y cleanup: wait420, sin cambiar timers nativos; su resultado86PASS/1FAIL se conserva en history/final02-before-lint-repair. Final03 fresco se justifica por tres avisos de lint nuevos reparados (import spacing y dict literal en tests añadidos); misma producción, fuentes/test actuales nuevos, sin RAWunion. Herramientas físicas precopiadas y bind sólo lectura, guard de fuentes/fixtures/entry/instrument actual antes de spawn. Hubo error privado PowerShell de delimitación al reparar cleanup; se restauraron exclusivamente las dos fuentes OWNED desde snapshot propio antes de corregirlas. No RED ni cambio en originales.

Todos los contenedores propios usan imagen fijada, UID65532, capdropALL, read-only, no-new-privileges, networknone, pids128/mem1GiB/cpu2/tmpfs128MiB; no GPU/pull/build/install/download. Captura CID beforestart, subprocess.wait real, inspect/remove/gone actuales. No cambio de topología producto. Cada finally de tests nuevos reenvía cleanup real incluso si join falla, y conserva testigo hasta completar wrappers. No fuente protegida cambiada ni contratos.py reformateado; deuda histórica formato1 sigue abierta. Ruff scoped queda en final/result.json, sin claim global.

No ledger/docs/ADRs/Git/knowledge/objetivos/medidor modificados. No full801/full1029/app/E2E/GPU/QA independiente. Se entrega para revisión fresca de componente drain y QA dualOS independientes de Root, conservando Linuxreview1/2/3 y toda historia sellada.

NEEDS_CONTEXT: Root debe adjudicar el fallo original Linux backpressure y las limitaciones de evidencia antes de aceptar el componente.
