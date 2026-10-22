# Informe de QA — M1 MVP del estudio web

| | |
|---|---|
| **Fecha** | 2026-10-10 |
| **Estado global** | VERDE para los tests ejecutados; cierre del hito NO evaluado |
| **URL auditada** | http://127.0.0.1:3000 (API http://127.0.0.1:8000) |
| **Plan** | [`../improvement-plan.md`](../improvement-plan.md) · [`../test-plan.md`](../test-plan.md) |

## Veredicto (qa-gate)

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 15,
    "failed": 0,
    "flaky": 0,
    "skipped": 1,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}
```

La URL pasó el guardrail de host local. La corrida usó el Playwright ya instalado en el workspace y Chromium disponible en la caché local; no se instaló nada fuera del repositorio.

## Resumen

- **Automáticos:** 15 pasan, 1 omitido, 0 fallan.
- **Manuales pendientes:** M-01, M-02 y M-03.
- El gate automático es verde para lo ejecutado, pero E2E-06 sigue bloqueado por el host y `coverage-check` marca T-00 sin cobertura declarada.

## Puertas previas

- `ledger-lint.py`: `0 incoherencias · 0 avisos`.
- `coverage-check.py`: referencias rotas `0`; tareas sin cobertura: `T-00`; tests sin referenciar: `[]`.
- `T-00` queda como gap de trazabilidad y evita considerar el plan globalmente cerrado.

## API

| Bloque | Resultado | Evidencia |
|---|---|---|
| API-01 | PASA | `POST /api/songs` con `Origin: http://evil.test` devuelve 403 y `FORBIDDEN_ORIGIN`. |
| API-02 | PASA | `GET /openapi.json` devuelve 200 y contiene `/api/generations`. |

## Resultados automáticos

| Bloque | Resultado | Evidencia |
|---|---|---|
| E2E-01 | PASA | Player y navegación de toma verificados por Playwright. |
| E2E-02 | PASA | Creación con letra y autoría `own`; captura representativa: [E2E-02-create.png](screenshots/E2E-02-create.png). |
| E2E-03 | PASA | Conservación de letra en instrumental y rechazo de etiqueta inválida. |
| E2E-04 | PASA | Tarjeta de generación y progreso verificados. |
| E2E-05 | PASA | Cancelación conserva el job visible. |
| E2E-06 | OMITIDO | Bloqueado en este host: el test exige `E2E_RECOVERY=1`, `MOCK_STAGE_DELAY_MS=5000` y reinicio real mediante `scripts/e2e_stack.py restart-server`. No se inventa evidencia de recuperación/persistencia. |
| E2E-07 | PASA | Vista de canción, tomas, onda, letra y procedencia. |
| E2E-08 | PASA | Biblioteca, búsqueda/lista y papelera/restauración. |
| E2E-09 | PASA | BPM y beats mostrados en la vista de canción. |
| E2E-10 | PASA | Página Sistema; captura representativa: [E2E-10-system.png](screenshots/E2E-10-system.png). |
| E2E-11 | PASA | Instrumental sin declaración y reexigencia al desactivarlo. |

Los resultados completos están en [`raw/results.json`](raw/results.json). No se acreditan aquí GPU ACE real, almacenamiento persistente ext4/VHDX, reinicio/reconciliación ni calidad de audio.

## Checklist manual

- [ ] **M-01 — Generación real con GPU:** repetir E2E-01 con `engine-acestep`, escuchar el resultado y comprobar `spilled: false` (T-04, T-05, T-16).
- [ ] **M-02 — Revisión visual y accesibilidad:** temas claro/oscuro, contraste, foco, teclado y `prefers-reduced-motion` (T-08, T-13).
- [ ] **M-03 — Backup y restauración:** ejecutar sobre datos reales, restaurar `studio.sqlite` y validar `verify_manifest.py data/songs/` (T-02, T-16).

## Trazabilidad

| Tarea | Resultado |
|---|---|
| T-01, T-03 | API-01/API-02 y E2E-03 pasan. |
| T-04, T-06, T-07, T-09, T-10, T-11, T-12, T-13, T-14, T-15 | Escenarios E2E cubiertos pasan; E2E-06 queda omitido por prerrequisito de host. |
| T-02, T-08, T-16 | Manual pendiente (M-02/M-03/M-01). |
| T-00 | Sin cobertura declarada según `coverage-check.py`. |

## Evidencias

- Capturas: [`screenshots/`](screenshots/)
- Resultados y trazas: [`raw/results.json`](raw/results.json), [`raw/artifacts/`](raw/artifacts/)
- El stack Compose fue levantado localmente para la corrida; no se modificó producto ni `tasks.md`.

## Evidencia adicional ? E2E-06 aislado

Tras el informe inicial, se levant? el stack Compose aislado con `E2E_ISOLATED=1`, `E2E_RECOVERY=1` y `MOCK_STAGE_DELAY_MS=5000`. El spec dedicado `apps/web/e2e/recovery.spec.ts`, ejecutado con un worker, termin? **1/1 en 18,5 s** y el stack se retir?. Esto acredita la recuperaci?n mock sobre el ?rbol aislado; no acredita todav?a la publicaci?n sobre el VHDX/ext4 persistente exigida por ADR-0069.

## Actualizacion 2026-10-10 - M-01 tecnico

La ejecucion real del engine ACE-Step ya esta verificada en Docker: `tests/test_gpu.py -m gpu` paso 1/1 con WAV valido de 30 s, telemetria BF16, `spilled=false` y descarga del proceso hijo. Ver [m01-gpu-real-2026-10-10.md](m01-gpu-real-2026-10-10.md). El informe automatico no marca M-01 completo porque aun falta la escucha humana de la toma.
