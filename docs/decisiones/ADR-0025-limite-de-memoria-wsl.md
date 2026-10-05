# ADR-0025 — Límite de memoria de WSL

**Estado:** aceptada por elección del propietario.
**Fecha:** 2026-10-05.

## Contexto

T-00 configuró 24 GB de RAM y 16 GB de swap para WSL. La prueba GPU de T-06 produjo audio de 30 s con ese perfil: pico usado de la VM excluyendo `MemAvailable` de 4.567,90 MiB y swap de 1,293 MiB; la caché final era 16.121,92 MiB. Son métricas Linux con ámbitos distintos, no una medida de RAM física de Windows. El propietario pidió reducir el consumo, eligió 16/8 GB, editó el archivo y solicitó reiniciar WSL.

## Decisión

El perfil global queda así:

```ini
[wsl2]
memory=16GB
swap=8GB

[experimental]
autoMemoryReclaim=dropCache
```

El propietario escribió y corrigió el archivo global. El agente ejecutó el reinicio solicitado con `wsl --shutdown`, sin cambiar ese archivo. Antes no había contenedores ejecutándose ni modelos en Ollama. Tras arrancar Ubuntu, `/proc/meminfo` informó 16.375.452 kB de RAM total y `/proc/swaps` 8.388.608 KiB, sin uso. Docker Desktop volvió a responder con servidor Linux.

## Consecuencias y límites

`memory` limita la VM; no reserva continuamente esa cantidad para WSL. La swap usa disco. `dropCache` permite recuperar caché automáticamente; el reinicio puede afectar a todas las distribuciones WSL y a Docker. [Configuración oficial de Microsoft](https://learn.microsoft.com/en-us/windows/wsl/wsl-config).

La prueba de audio se realizó antes del cambio, con 24 GB. Los nuevos límites están aplicados, pero aún falta medir una canción completa, cargas con offload y la convivencia con otros stacks. Si aparece presión de memoria sostenida, se revisará el límite con mediciones. No se modifica el tope de VRAM ni la política de un modelo GPU a la vez.

Fuentes: [entorno E-03](../arquitectura/entorno.md), [QA T-06 y métricas](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t06/report.md), [ledger](../roadmap/2026-09-28-m0-entorno-y-motor/tasks.md). La configuración de T-00 queda como registro histórico.
