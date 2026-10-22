# T-16 — retry2 GPU: fallo SFT, cero tomas publicadas

Fecha: 2026-10-06. [Recibo de ejecución y hashes](retry2-failure-receipt.json). Nueva sesión privada `01M47EM0TM0XV6EFJHXX7ETSR7`, distinta de la sesión abortada anterior. No se sobrescribieron takes, manifiestos, escuchas ni recibos históricos.

Antes de lanzar,15 hashes del arnés/fuentes de producto coincidieron con el recibo QA de fix3. Preflight real: GPU1315MiB de12227, Ollama vacío y engine8101 anterior idle/descargado. Se cumplió el techo1600 normal; no se usó una nueva excepción ni se reinterpretaron permisos previos. Imagen de producto9e4fc86 conservada, sin rebuild.

El orden aleatorio empezó por SFT. El job `01M47EM4GN8N4FPEAYA4BPB7WE` alcanzó loading/generating y progresos CLI10/50/51/52 %, terminó con **INTERNAL**, exit1, tras187,406s. El monitor no solicitó parada (`stop_reason=null`). La comparación completa terminó exit1; lista de outputs vacía, cero tomas publicadas y segundo grupo no ejecutado.

La descarga sí quedó confirmada (`unload_confirmed=true`). El contenedor propio7813b013 se identificó por ID/etiqueta, capturó logs y terminó con stop0/remove0. Se conservó el servicio8101 anterior. Tras terminar, GPU1315MiB; Ollama seguía vacío, sin modelo previo que restaurar. No quedó un proceso de generación vivo: el handle root72134 devolvió exit1.

El arnés fix3 atravesó correctamente preflight con cap0 y llegó a la generación real; este fallo nuevo no es la excepción anterior de la guarda. No demuestra que la música SFT funcione. El mensaje público y logs existentes no identifican la excepción nativa: el adaptador sanitiza detalles y el contexto privado upstream suprime stdout/stderr/loguru. No se concluye OOM, fallo de prompts, incompatibilidad de pesos o ausencia de forwards a partir del mensaje INTERNAL o del porcentaje redondeado.

Los registros conservan memoria agregada y WSL RAM/swap. Sus máximos están en el recibo con unidades/ámbito; no equivalen a pico asignado de CUDA ni a memoria GPU compartida de Windows. No se afirma `spilled=false` de una toma terminada, porque no existe manifiesto de salida.

## Siguiente paso

Investigación `custom-agents:debug-root-cause` en `.cache/dev-cycle/t16/retry2-diagnosis/`, de solo lectura/CPU, sin modificar fuentes selladas ni repetir GPU. Aislar la zona de fallo y probar una hipótesis barata; si falta detalle nativo, preparar instrumentación privada y un caso mínimo revisable antes de ejecutar otra prueba. No repetir seis tomas a ciegas ni empaquetar una comparación incompleta.

T-16 sigue en-progreso, CA3/4 abiertas, sin calidad aprobada ni ganador. La comparación y el objetivo completo permanecen pendientes; el fallo y cleanup reales son evidencia, no un cierre de tarea.
