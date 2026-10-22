# T-09 — sonda nativa tras paralelizar observadores

Fecha: 2026-10-10  
Método: `wddm_auto_v3`, proveedor `NativeProvider`, sin cargar ACE-Step ni
Ollama (`ollama ps` vacío). La RTX 5070 mostraba 1.137 MiB usados y 10.807
MiB libres antes de la sonda.

## Cambio verificado

El proveedor nativo activa `parallel_operations=True` en `Observers`. NVML,
PDH, WSL y el heartbeat del navegador se adquieren en paralelo; el resultado
y los callbacks se publican en el orden canónico y cada operación conserva su
propio bracket de tiempos. El modo secuencial usado por los fixtures CPU queda
sin cambios.

## Evidencia

- RED/GREEN TDD: `test_parallel_observers_overlap_slow_wsl_and_windows` falló
  antes por `TypeError` (no existía la opción); después pasó **1/1**.
- Vecinos de observadores/proveedor: **21/21**; Ruff y formato dirigidos,
  limpios.
- Sonda nativa única: **91 ms**, `errors=[]`; NVML 41 ms, PDH 8 ms, WSL 68
  ms y navegador 2 ms.
- Continuidad nativa: **10/10** muestras, `errors=0`, máximo observado 84,49
  ms (WSL máximo 66,43 ms).

La sonda no acredita la matriz T-09: no cargó un modelo, no ejecutó una toma
ACE-Step y no sustituye las 160 ejecuciones ni la calibración/QA WDDM exigidas
por el plan.
