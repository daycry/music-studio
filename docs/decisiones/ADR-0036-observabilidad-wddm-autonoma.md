# ADR-0036 — Observabilidad WDDM autónoma

- **Estado:** aceptada; implementación y acreditación real pendientes
- **Fecha:** 2026-10-07
- **Decisor:** orquestador, con delegación explícita del propietario para continuar todo el roadmap y elegir las mejores alternativas
- **Ámbito:** M0/T-09; complementa ADR-0033 y sustituye la obligatoriedad de su contraste manual

## Contexto y alternativas

El propietario no podrá aportar más lecturas. El contraste histórico con Rendimiento discrepa de PDH/NVML y su causa sigue desconocida. Las lecturas manuales sin hora no pueden acreditar simultaneidad.

| Opción | Resultado |
|---|---|
| O1: PDH agregado acreditado por API y contraste dedicado separado | Elegida: automatizable sin instalaciones, con confianza limitada explícita |
| O2: PDH más WPR/WPA | Contraste futuro condicionado a extractor y tablas reales validados |
| O3: conservar la puerta manual | Diagnóstico parcial de respaldo; dependería de una intervención que el propietario no puede proporcionar |

## Decisión

Usar `wddm_auto_v1` como alternativa explícita a `task_manager_v1`. PDH mide Dedicated/Shared Usage del adaptador exacto por LUID/DXGI; el validador comprueba identidad, tipos, bytes sin escala, estados, timestamps y frescura. La política experimental versionada del [diseño aprobado](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/autonomous-observability-design.md) debe fijarse y sellarse antes de una nueva carga.

Acreditar diez muestras baseline, diez bajo carga representativa real y diez después de unload. Contrastar **solo dedicada** con NVML mediante consultas acotadas y alineadas en tiempo, observando subida y recuperación. Mantener CUDA del hijo y RAM/swap WSL separados. Registrar `shared_validation_level=provider_verified`, `shared_independent_validation=false` y el contraste histórico conflictivo. NVML/CUDA no calibran memoria compartida Windows; no se declara ausencia causal de spill.

Conservar el navegador visible, una evidencia inicial propia, identidad PID/creationTime/HWND/exe y heartbeat. Una pestaña propia y una ventana visible son evidencias separadas si la API no acredita su unión. No controlar aplicaciones ajenas ni acceder a la página de valoraciones denegada.

Mantener la matriz160, configuraciones/duraciones/brazos, relojes directos, treswarm por celda, VRAMlibre menos512MiB, reposo≤1600MiB, Ollama compartido, ownership y cleanup. Datos ausentes/ambiguos/caducados o estados inválidos producen resultado parcial, sin completar ni recomendar desde datos inválidos. La confianza y los límites se publican con los números.

## Consecuencias y verificación

TDD, revisión adversarial y QA independientes preceden al piloto real y a la matriz. Se preservan todos los recibos, capturas y umbrales históricos; no se recalifican intentos previos. El esquema nuevo es aditivo y no modifica el contrato /v1, pesos, dependencias o engines. Rendimiento operativo y calidad musical siguen separados.

Microsoft describe [memoria agregada por GPU](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/); los [errores documentados de contadores por proceso](https://learn.microsoft.com/en-us/troubleshoot/windows-client/performance/gpu-process-memory-counters-report-wrong-value) no explican nuestra discrepancia en Rendimiento. El diseño cita APIs públicas y alternativas descartadas; no introduce una ABI D3DKMT reservada.
