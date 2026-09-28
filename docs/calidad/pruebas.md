---
documento: pruebas
titulo: Estrategia de pruebas
estado: vigente
fecha: 2026-09-28
actualizado: 2026-09-28
---

# Estrategia de pruebas

**Regla de oro:** las pruebas automáticas validan **contratos observables** (estados, duración, formato, loudness, manifiesto, linaje), nunca la calidad musical. La calidad se decide escuchando ([evaluacion-escucha.md](./evaluacion-escucha.md)).

| Nivel | Qué | Herramienta | Cuándo |
|---|---|---|---|
| Unitarias server | Validación de peticiones, parser de etiquetas de letra, resolución por capacidades, transiciones de estado, linaje, manifiesto y su verificador | pytest | Siempre, sin GPU |
| Unitarias engines y `packages/weights` | Auditor de pickle (rechaza opcodes no tensoriales, convierte a safetensors), verificación SHA-256 y sello, cálculo del tope de VRAM, supervisor de proceso hijo (load/unload), cancelación, prohibición de `torch.load`/`pickle.load` (búsqueda en `apps/` y `packages/`) | pytest | Siempre, sin GPU |
| Unitarias audio-post | Normalización a ±0,5 LU del objetivo, true peak ≤ −1 dBTP (medido con ffmpeg `ebur128=peak=true`), duración ±5 %, detección de silencio, NaN y clipping, picos | pytest con audio sintético + ffmpeg LGPL | Siempre |
| Unitarias web | Parser de etiquetas (mismos casos que el server, en `packages/contracts/lyrics-cases.json`), componentes clave | vitest | Siempre |
| **Contrato** | `openapi.json` versionado = generado; `engine-v1.json` = generado desde `packages/engine-contract`; manifiesto, timeline y song.json validan contra sus JSON Schema; parsers de letra Py y TS pasan `lyrics-cases.json` | pytest + vitest | Siempre |
| **E2E** | Crear → cola → progreso → take en la canción → reproducir → descargar; errores; cancelación; recuperación tras reinicio | Playwright contra `engine-mock` | Siempre (CI local) |
| **Conformidad de adapter** | Con GPU real, por tarea del descriptor: duración, sample rate, canales, sin silencio ni NaN, telemetría completa (`load_s`, `run_s`, `vram_peak_mb`, `vram_cap_mb`, `spilled`), VRAM pico bajo el tope, liberación real tras `unload` | pytest marcado `gpu` | Al añadir o actualizar un modelo |
| **Escucha** | Batería de 10 briefs | `scripts/eval/` + oído | M0 y cada cambio de modelo |

## engine-mock

Ver [`../arquitectura/contrato-engines.md`](../arquitectura/contrato-engines.md) §7: implementa el contrato `/v1` sin GPU para todas las tareas (audio, texto en streaming, imagen, vídeo, análisis), con retardos y fallos inyectables. Es el engine por defecto en desarrollo de UI y en los E2E. Cada hito con UI tiene su `test-plan.md` (bloques E2E-xx y M-xx) en la carpeta del hito, que ejecuta el agente `qa` del plugin.
