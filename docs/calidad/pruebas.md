---
documento: pruebas
titulo: Estrategia de pruebas
estado: vigente
fecha: 2026-09-28
actualizado: 2026-11-03
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

## Desarrollar y probar la web en Windows sin WSL ni GPU

Este perfil comprueba la UI con datos sintéticos. El producto conserva el despliegue Docker de la [constitución](../CONSTITUTION.md#2-arquitectura-fijada--vetada). No necesita arrancar Docker, Ollama ni engines. Presupone dependencias y navegador de pruebas ya instalados dentro del proyecto; estos comandos no incluyen instalación.

Desde la raíz, carga el entorno en cada terminal. Usa el wrapper [scripts/pnpm.ps1](../../scripts/pnpm.ps1), que ejecuta el Node gestionado y valida argumentos mediante [pnpm.py](../../scripts/pnpm.py):

```powershell
. ./scripts/env.ps1
& ./scripts/pnpm.ps1 --filter ./apps/web test
& ./scripts/pnpm.ps1 --filter ./apps/web lint
& ./scripts/pnpm.ps1 --filter ./apps/web typecheck
& ./scripts/pnpm.ps1 --filter ./apps/web build
uv run --frozen --no-sync scripts/export_contracts.py --check
```

La cobertura se activa con `exec vitest '--' run --coverage`; los umbrales y archivos medidos están en [vitest.config.ts](../../apps/web/vitest.config.ts). El recibo de una fase puede usar una configuración más específica: hay que conservarla junto con su informe y no presentar su porcentaje como cobertura de todo el repositorio. Mantén entre comillas el primer `'--'` de transporte en PowerShell; el wrapper sólo retira ese separador y conserva los posteriores.

En otra terminal inicia la web con `& ./scripts/pnpm.ps1 --filter ./apps/web dev`. El script de [package.json](../../apps/web/package.json) usa Webpack y escucha en `127.0.0.1:3000`, igual que el build usa Webpack. No sustituyas el comando por un Node del sistema.

### Preparar exclusivamente el servidor HTTP temporal

Los dos smokes de API necesitan un HTTP real en `127.0.0.1:8000`. No apuntes a la biblioteca habitual ni al stack vivo. Este ejemplo ejecutado desde la raíz crea una carpeta nueva bajo `.cache/qa-cpu/`, omite `.env`, desactiva engines y usa un token efímero. Si el puerto está ocupado, no detengas el servicio ajeno: aplaza estos dos smokes.

En una terminal con el entorno cargado:

```powershell
@'
from pathlib import Path
import secrets
import sys
import uvicorn

root = Path.cwd().resolve()
assert (root / "apps/server/app/main.py").is_file()
sys.path.insert(0, str(root / "apps/server"))
from app.main import create_app
from app.settings import Settings

data = root / ".cache/qa-cpu" / secrets.token_hex(8)
settings = Settings(
    _env_file=None, engine_token=secrets.token_urlsafe(32),
    data_dir=data, engines={}, storage_uuid=None,
)
uvicorn.run(create_app(settings), host="127.0.0.1", port=8000)
'@ | uv run --frozen --no-sync python -
```

La factoría [create_app](../../apps/server/app/main.py) conserva migración y ciclo de vida reales sobre esa BD temporal. `engines={}` impide usarla para generar canciones. Cierra únicamente estos dos procesos de prueba con `Ctrl+C` al terminar; sus datos temporales no pertenecen a la biblioteca del usuario.

### Ejecutar e interpretar Playwright CPU

Con ambos procesos anteriores disponibles:

```powershell
& ./scripts/pnpm.ps1 --filter ./apps/web exec playwright '--' test --config=playwright.cpu.config.ts
```

[playwright.cpu.config.ts](../../apps/web/playwright.cpu.config.ts) no arranca servicios: usa un worker, Chromium con `--disable-gpu` y excluye recuperación, análisis y colecciones. Guarda JSON, HTML, trazas y capturas en `.cache/playwright-ui/`. Para ejecutar sólo UI sin el HTTP temporal, añade `'--grep-invert=API-'` al mismo comando.

| Evidencia | Qué demuestra | Qué queda fuera |
|---|---|---|
| Tests UI con [fixtures](../../apps/web/e2e/fixtures.ts) | Formulario, eventos, estados, errores, biblioteca y reproducción ante respuestas controladas; una ruta API no declarada devuelve 404 | Engine, persistencia y SSE reales; audio y VRAM son sintéticos |
| [API-01/02](../../apps/web/e2e/api-smoke.spec.ts) | Rechazo de Origin ajeno y contrato OpenAPI del servidor temporal | Generación, reintento y publicación de audio |
| Unitarias y build | Comportamiento de módulos y compilación | Calidad musical, integración Docker y aceptación manual |

El [informe QA CPU de M1](../roadmap/2026-09-28-m1-mvp-estudio/testing/cpu-ui-2026-11-03.md) conserva los resultados observados y sus límites. Los E2E con engine-mock, FFmpeg, recuperación y medios reales siguen siendo una verificación distinta en el [plan canónico](../roadmap/2026-09-28-m1-mvp-estudio/test-plan.md). No se sustituyen por este perfil ni por repetirlo tres veces.
