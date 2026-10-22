# Observación de GPU y continuación autónoma

Registrado el 2026-10-07. El propietario delega la continuación de todo M0–M5 y no podrá proporcionar más lecturas manuales. Este registro no declara completado el benchmark.

El último dato comunicado fue **9,5 GB de memoria dedicada máxima y 0,2 GB compartida**. No hay hora de observación ni escala explícita; solo la dedicada se declaró como máximo. El registro anterior de 8,8 GB dedicada y 0,1 GB compartida tiene los mismos límites. Ninguno sustituye una pareja de muestras simultáneas.

Una sonda automática nueva de diez muestras, desde 2026-10-06T22:56:24Z, dio NVML máximo de 1.264 MiB, PDH dedicado de unos 1.278 MiB y compartido de unos 132 MiB. DXGI identificó la RTX 5070 y su LUID; todos los estados PDH fueron válidos. No se cargó un modelo ni se accedió a una pantalla. La ventana de benchmark previamente registrada ya no existe: el heartbeat devolvió PID 0 y `visible=false`. No se reutilizará su antigua captura como acreditación de presencia actual.

La captura representativa anterior sigue discrepando: a 2026-10-06T21:32:15.356Z mostraba 1,3 GB dedicada, mientras la muestra próxima, 0,214 s después, indicaba NVML 8.904 MiB y PDH dedicado 8.918 MiB. La causa no está probada. Se conservan captura, tiempos y estados originales; no se certifica esa calibración.

Microsoft explica que Rendimiento agrega memoria por GPU, mientras los contadores por proceso pueden duplicar memoria compartida. La documentación sobre errores de contadores por proceso **no demuestra** la causa de nuestra discrepancia en Rendimiento. [Semántica del Administrador de tareas](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/), [limitación de contadores por proceso](https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/gpu-process-memory-counters-report-wrong-value).

El siguiente paso es comparar alternativas de acreditación automática con evidencia verificable, manteniendo la matriz, los límites de VRAM, el navegador y la separación entre memoria compartida observada y desbordamiento causal. Las lecturas manuales serán evidencia complementaria, sin nuevas solicitudes al propietario. Cualquier cambio del diseño vigente requiere un ADR y su validación; este informe no modifica esa puerta.

Evidencias privadas: `.cache/dev-cycle/t09/owner-peak-and-autonomy-20261007.json`, `.cache/dev-cycle/t09/autonomous-baseline-20261007/` y `.cache/dev-cycle/t09/representative-capture-instrumental60-20261006/`. Windows Performance Recorder está disponible y enumera un perfil GPU; solo se consultó su inventario, sin iniciar una grabación.
