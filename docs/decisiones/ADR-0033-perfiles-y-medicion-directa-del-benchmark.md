# ADR-0033 — Perfiles y medición directa del benchmark

- **Estado:** aceptada; implementación y medición pendientes
- **Fecha:** 2026-10-06
- **Decisor:** orquestador, con autorización del propietario para implementar el roadmap y elegir las mejores alternativas
- **Ámbito:** M0/T-09; complementa ADR-0007, ADR-0011 y ADR-0029

## Contexto y alternativas

T-09 debe comparar Turbo con LM0,6B/1,7B, SFT, base y XL-turbo con offload/INT8 si cabe, durante30/60/180/300s. El engine distingue actualmente Turbo/SFT; seleccionar base/XL no acredita una identidad propia. `run_s` incluye carga y no es el reloj de inferencia. `spilled=false` no mide memoria GPU compartida de Windows.

| Opción | Ventaja | Coste / riesgo |
|---|---|---|
| O1: harness sobre `/v1` con perfiles y telemetría aditiva | Mide el adapter que usa el producto | Ampliar perfiles, medición y observadores con conformidad |
| O2: worker upstream independiente | Aislamiento del experimento | Duplica guardas; sus resultados pueden diferir del engine |
| O3: ampliar la CLI musical y publicar takes | Mide la experiencia completa | Amplía la publicación y no elimina la necesidad de un reloj directo |

## Decisión

Elegir **O1**, usando contenedores propios y el contrato vigente. Mantener Turbo/BF16 como configuración inicial y `verified=false` hasta la conformidad correspondiente. No convertir un resultado de rendimiento en aprobación artística.

Registrar checkpoints por coincidencia exacta: Turbo, SFT, base y XL-turbo tienen identidades propias; un desconocido se rechaza. Base32/CFG7 y XL-turbo8 siguen el código oficial fijado; los controles actuales de Turbo/SFT se conservan. El benchmark fija explícitamente shift1, LM/PT y el resto de condiciones por celda, sin presentarlos como defaults universales.

Medir directamente con reloj monotónico sincronizado alrededor de la generación upstream. Conservar `load_s`, `run_s` y el tiempo de pared; publicar `inference_s`, duración real del audio y `RTF=inference_s/audio_duration_s` en campos opcionales de `Telemetry.extra`, usando `rtf` existente cuando haya medición válida. No restar carga para fabricar un reloj de inferencia ni imponer campos nuevos en `/v1`.

Exponer `offload-int8` explícitamente: activaciones BF16, offload CPU y cuantización oficial `int8_weight_only` de lineales del decoder DiT. Rechazar su desactivación silenciosa y comprobar aplicación efectiva. Mantener safetensors/locks/código fijado y loaders auditados; no introducir pickle ni cuantizar el LM por suposición. La importación y compatibilidad CUDA reales deben verificarse antes de medir.

Comparar bind con una **copia temporal dentro de un contenedor propio**, bajo la raíz lógica `.cache` del proyecto, con layout, recursos y hashes equivalentes. No crear un almacén permanente fuera del repositorio ni migrar el Docker compartido. Las fuentes permanecen en `models/`; la copia se elimina al retirar su contenedor. Separar copia y verificación de la carga, declarar la caché del filesystem y alternar el orden de brazos. Un delta comparable superior30s exige otro ADR basado en los resultados.

Observar WDDM del adaptador identificado por LUID/DXGI, registrar navegador visible, VRAM/NVML y RAM/swap WSL por separado. Conservar observación verificable del Administrador de tareas; no inventar captura si no hay acceso. La referencia RTF usa tres ejecuciones calientes elegibles de la misma celda. Datos ausentes o ambiguos producen un diagnóstico parcial, sin recomendación completa.

**Complemento vigente, 2026-10-07:** [ADR-0036](ADR-0036-observabilidad-wddm-autonoma.md) permite acreditar automáticamente WDDM mediante el método explícito `wddm_auto_v1`, conservando el contraste manual como alternativa y evidencia complementaria. El contraste NVML de dedicada no calibra compartida Windows; la confianza y el conflicto histórico se publican. Matriz, navegador, preflight, referencias y cleanup permanecen obligatorios.

## Consecuencias y verificación

La matriz mantiene veinte celdas y dos brazos de almacenamiento; una ejecución fría y tres calientes por celda/brazo permiten medir dispersión y referencia RTF. Jobs nuevos, recibos inmutables, reanudación por estado real y cleanup exclusivo. XL ausente/no factible se documenta con evidencia; no se elimina su fila.

TDD, regresiones de T-16, revisión fresca y QA preceden a la matriz GPU. El [ledger](../roadmap/2026-09-28-m0-entorno-y-motor/tasks.md) conserva estado y verificaciones; no hay cifras de rendimiento nuevas en esta decisión.

Fuentes: [defaults upstream fijados](https://github.com/ace-step/ACE-Step-1.5/blob/dce621408bee8c31b4fcf4811682eb9359e1bc94/acestep/ui/gradio/events/generation/model_config.py), [cuantización upstream](https://github.com/ace-step/ACE-Step-1.5/blob/dce621408bee8c31b4fcf4811682eb9359e1bc94/acestep/core/generation/handler/init_service_loader.py), [lock fijado](https://github.com/ace-step/ACE-Step-1.5/blob/dce621408bee8c31b4fcf4811682eb9359e1bc94/uv.lock), [memoria en Administrador de tareas](https://devblogs.microsoft.com/directx/gpus-in-the-task-manager/).
