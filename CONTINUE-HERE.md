# Continuar aquí

> Estado canónico: [M1/tasks.md](docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md). M2/M3 congelados por ADR-0089.

**Actualizado:** 2026-11-06. M1: **15 tareas completadas, 2 canceladas y T-16 en-progreso**. La parte README de T-16 ya pasó; falta la aceptación con ACE-Step real.

**M0:** 14 tareas completadas, 3 canceladas; abiertas T-08/T-09/T-13/T-16. T-20 documental cerrada con revisión A/B, Compose validado en cuatro perfiles y QA sin UI (`.cache/dev-cycle/20261106-m0-t20/`). No acredita ejecución GPU ni conectividad Ollama.

## Restricciones

- Docker/WSL disponibles; **GPU/Ollama fuera de las pruebas actuales**. No cargar modelos ni alterar servicios ajenos.
- No abrir SQLite viva desde Windows. Preservar los cambios ajenos del journal y restos M2/almacenamiento; 71 archivos ajenos conservados por hash.
- Sólo el orquestador actualiza el ledger. Ningún verde mock equivale a escucha o cierre musical.

## Evidencia técnica

- T-15: servidor Linux2214 pass/17 skip; web419/32 archivos; herramientas138 pass. QA Docker14/14 x3 y M-02 oscuro/teclado/reducedmotion aprobados, QA-V01 corregido. [Informe](docs/roadmap/2026-09-28-m1-mvp-estudio/testing/docker-ui-2026-11-05.md) y PDF8p inspeccionado. Entrega integrada en main por a8b2824.
- T-16: el clon limpio inicial descubrió que bootstrap exigía una caché histórica. Corregido con preparación explícita de Node/pnpm fijados antes del launcher; hashes/check-only conservados. A/B sin gaps; C/D no aplican al delta según selector.
- Candidato público de código T-16 **faf4be7**, rama `m1/t-16-arranque-documentado`: otro clon nuevo `.cache/r`, bootstrap+init+FFmpeg Linux+Compose/health/seed+Chromium exit0; **una corrida14/14**, gate0. Módulo host separado **103/103**, exit0. [Informe de primer arranque](docs/roadmap/2026-09-28-m1-mvp-estudio/testing/readme-arranque-2026-11-06.md). No se copiaron herramientas/cachés; Docker sí reutilizó capas normales.
- El aviso SWC260 del clon anidado no impidió el recorrido Docker; no acredita build host Windows de ese clon. Pytest-cov no mide PowerShell; no se inventa porcentaje. Runtime completo T-15:79,31% ramas; fix1 vs review1:58/59 líneas cambiadas cubiertas.
- Evidencia privada: `.cache/dev-cycle/20261105-t16-readme/{qa-fixed,review-1,fix1}/`; T-15 en `.cache/dev-cycle/20261105-m1-docker/`. Los tres candidatos de conocimiento siguen pendientes de curación.

## Demo activa: sólo audio simulado

- `http://127.0.0.1:3000/create`, API `http://127.0.0.1:8000`. Proyecto exclusivo **music-studio-e2e-368b45c362fb**, reactivado por root DESPUÉS de terminar y retirar QA. No hay procesos de QA vivos.
- Compose privado `.cache/dev-cycle/20261105-t16-readme/compose.demo.json`, env/datos bajo `.cache/r/.cache/e2e-runs/368b45c362fb/`. No imprimir secretos ni resetear datos. Recibo `demo-receipt.json` en el directorio T-16.
- Tres imágenes exactas verificadas: web16005ab0, serverd2ae013e, mock35ade972, tags `music-studio/<servicio>:m1-t16-20261106-cold`. Sin DeviceRequests; sólo web/API publicadas en loopback. T-15 antiguo está detenido; sus datos se conservan. No detener Docker/WSL/Ollama globalmente.

## Siguiente puerta

1. Revisar M0/T-16 sin GPU: sus tests de controles son CPU y existen seis carpetas de escucha en `data/eval/libre-sft/01M47Q4EJZK09RBPA0ECWC57D4/`. Comprobar integridad/procedencia antes de dar por preparadas las tomas; no ejecutar helpers históricos de `.cache/dev-cycle/t16/` que pueden arrancar GPU. La escucha/elección sigue siendo T-13.
2. Cerrar M0/T-08/T-09/T-13 cuando se pueda usar GPU: validación del engine de análisis, benchmark recortado y escucha/decisión de modelo/modo del propietario. No sustituir esa decisión por los resultados mock.
3. M1/T-16: generar desde la web con ACE-Step/GPU reales, manifiesto y telemetría válidos (spilled:false), escucha y aceptación del propietario; conservar M-03 y el ritual final de dev-cycle (docs/changelog/retro). M1 sigue abierto.
4. **Petición del propietario:** una vez cerrado M1, ejecutar Claude CLI para buscar hallazgos en lo implementado y guardar su informe. CLI instalado; aún NO invocado. No enviar secretos ni datos del usuario.
5. M2/M3 continúan congelados hasta cerrar M1; no reactivar restos del árbol como si estuvieran aprobados.
