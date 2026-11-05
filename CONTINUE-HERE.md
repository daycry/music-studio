# Continuar aquí

> Estado canónico: [M1/tasks.md](docs/roadmap/2026-09-28-m1-mvp-estudio/tasks.md). M2/M3 congelados por ADR-0089.

**Actualizado:** 2026-11-05. T-15 y las tareas técnicas T-01 a T-13 cerradas tras QA Docker. **M1 sigue en-progreso: T-16 pendiente.**

## Restricciones vigentes

- Docker y WSL disponibles; GPU/Ollama fuera de las pruebas actuales. No cargar modelos ni cambiar servicios ajenos sin nueva indicación que levante esa restricción.
- No abrir la BD del usuario desde Windows. Preservar cambios ajenos del journal y restos M2/almacenamiento sin seguimiento.
- Sólo el orquestador actualiza `tasks.md`. El verde con mock CPU no acredita música ni aceptación final.

## Entrega técnica verificada

- Servidor Linux final: **2214 pass, 17 skip de Windows, cero fallos/errores**, custodia/FFmpeg/publicación reales incluidos. Fuentes/tests sin cambios de SHA. Cobertura fix1 cambiada frente a review1: 58/59 = 98,31 %; runtime completo mantiene **79,31 % de ramas**.
- Web **419 pass/32 archivos**; herramientas Windows **138 pass/0 skip**. Build, ESLint, TypeScript, Ruff/formato y contratos: exit 0.
- QA independiente Docker: **14/14 en tres corridas**, cero fallos/flaky/skips/retries, cada gate exit 0. M-02 oscuro, teclado y movimiento reducido aprobado; grid/list en 1440/768/390 px. QA-V01 corregido. [Informe MD](docs/roadmap/2026-09-28-m1-mvp-estudio/testing/docker-ui-2026-11-05.md) / [PDF](docs/roadmap/2026-09-28-m1-mvp-estudio/testing/docker-ui-2026-11-05.pdf), ocho páginas inspeccionadas.
- Revisiones A/B/D del lote y del fix final sin gaps pendientes; C no aplica según selector. Los dos candidatos de conocimiento permanecen pendientes de curación.
- Recuperación real adicional: SIGKILL del server durante generación y FFmpeg, y reinicio exclusivo del mock. Backup/restauración privados con medios y `private-contexts/`: 18 canciones, 22 takes, 60 assets, 15 manifiestos válidos.
- Evidencia privada: `.cache/dev-cycle/20261105-m1-docker/final-validation.json`; no versionar raw, env ni datos. Evidencia CPU histórica: `.cache/dev-cycle/20261103-cpu-m1/final-validation.json`.
- Entrega de código/documentación `f26d102` publicada en `m1/t-15-docker-integracion` e integrada por fast-forward en `main`, ambos remotos comprobados. Git normalizó CRLF a LF en trece archivos al cambiar de rama: contenido normalizado idéntico al contexto probado, registrado en `git-delivery.json`; los SHA crudos originales siguen acreditando las imágenes evaluadas.

## Despliegue privado para pruebas

- Proyecto `music-studio-e2e-t15-20261105`: web/server/engine-mock CPU; web `http://127.0.0.1:3000`, API `http://127.0.0.1:8000`. **Genera audio simulado**, no usa ACE-Step/GPU.
- Datos, Compose resuelto y env privados en `.cache/dev-cycle/20261105-m1-docker/`; no resetearlos. Contexto limpio desde 5541902 con 29 overlays explícitos, sin restos M2/almacenamiento.
- Imágenes finales: server `music-studio/server:m1-t15-20261105-fix1` (`69e939e7…`), web `music-studio/web:m1-t15-20261105-visual` (`68da3894…`). Nueve módulos server verificados dentro de Linux.
- QA ha liberado el control; no quedan navegadores ni procesos de QA activos. No detener Docker/WSL/Ollama globalmente.
- Retirados los siete contenedores auxiliares inactivos de QA; evidencias conservadas y tres servicios de demostración activos. Los 71 archivos de cambios ajenos conservan su hash.

## Siguiente trabajo

1. **T-16:** cerrar antes M0/T-13 (escucha y decisión de modelo); después generar desde la web con ACE-Step/GPU reales, comprobar manifiesto/telemetría y aceptación musical del propietario. No sustituirlo por mock.
2. Seguir el README desde cero en entorno aislado y completar el ritual de cierre de dev-cycle (documentación, changelog y retro). La receta Compose se ha validado en lectura/sintaxis, no como arranque frío completo.
3. **Petición del propietario (2026-11-05): cuando M1 esté cerrado, ejecutar Claude CLI para analizar lo implementado en busca de hallazgos y guardar el informe.** CLI instalado; aún no invocado. Darle código/contratos/ledger y evidencia pública, sin secretos ni datos del usuario; revisar sus hallazgos contra pruebas antes de corregirlos.
4. M2/M3 siguen congelados hasta cerrar M1. No reactivar restos del árbol como si estuvieran aprobados.

Guía de pruebas y aislamiento: [docs/calidad/pruebas.md](docs/calidad/pruebas.md).
