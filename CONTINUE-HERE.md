# Continuar aquí

> Estado canónico: [M1/tasks.md](docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md). M2/M3 congelados por ADR-0089.

**Actualizado:** 2026-11-04. Alcance CPU solicitado implementado y verificado.

## Restricciones vigentes

- No usar WSL, Docker, GPU ni Ollama: están ocupados. El producto sigue desplegándose en Docker.
- No abrir la BD del usuario ni tocar cambios ajenos de journal y restos M2/almacenamiento sin seguimiento.

## Entrega CPU

- Crear, feed, biblioteca, canción y reproductor implementados; SSE, reintentos con hijo/linaje, búsquedas, valoraciones y descargas corregidos.
- Servidor: 2067 pass, 77 skip, 0 fallos; wrapper: 79 pass; web: 413 pass/32 archivos. Build, ESLint, TypeScript, Ruff, formato y contratos: exit 0.
- Cobertura por archivo >=80 % en seis módulos del servidor, wrapper y 12 módulos web. Fuentes y 74 archivos de tests conservan SHA durante V6.
- Revisiones A/B/C/D del código conformes; delta final de dos arneses revisado por A/B/D, sin gaps. QA CPU: tres corridas 21/21 (19 UI interceptada + 2 HTTP aislados).
- Rama de entrega: m1/t-15-cpu-verificacion. Main conserva su estado anterior; integración pendiente de las puertas de producto.
- Servicios temporales propios detenidos. Evidencia local: .cache/dev-cycle/20261103-cpu-m1/final-validation.json.

## Qué queda cuando se autorice usar los recursos

1. Recompilar el despliegue Docker y ejecutar T-15 con engine-mock real: recuperación, FFmpeg, persistencia y medios/SSE/Range; no sustituirlo por fixtures UI.
2. Completar los manuales y M0 escucha/decisión de modelo; T-16 exige ACE-Step real y aceptación musical del propietario.
3. Cerrar tareas e integrar ramas según el ledger; M2/M3 continúan congelados.

Guía: [pruebas CPU](docs/calidad/pruebas.md). Informe histórico: [QA UI](docs/roadmap/2026-09-28-m1-mvp-estudio/testing/cpu-ui-2026-11-03.md).
