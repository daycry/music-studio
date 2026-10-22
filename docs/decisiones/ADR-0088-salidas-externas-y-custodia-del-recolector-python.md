---
id: ADR-0088
titulo: Salidas externas y custodia del recolector Python
estado: aceptada
fecha: 2026-10-12
iniciativa: 2026-10-11-m3-produccion-portada-video-letra
seleccion: ROOT bajo delegación autónoma del propietario; O1; registrada 2026-10-12T18:35:50Z
---

# ADR-0088: Salidas externas y custodia del recolector Python

## Contexto

El [contrato CM](../roadmap/2026-10-11-m3-produccion-portada-video-letra/cohort-metrics-contract.md), §8.1, exige raw fuera de base/candidate. Su argv de §8.3 prescribe una salida interna. El candidato `f908b0c6` crea dos outputs internos y los mueve después; A1 confirma la contradicción. B1 confirma que matar UV deja pytest vivo y pierde stdout/stderr/custodia al esperar nuevamente sin plazo.

## Decisión

ROOT elige O1 bajo la delegación del propietario. Raw, effective raw, coverage data, logs y temporales nacen en un namespace propio externo a base/candidate, dentro del proyecto. El argv Python usa `--cov-report=json:<ruta_absoluta_raw_externa>` preaprobada; cwd, raíces, nodes, flags y configuración congelados conservan su alcance.

El primer backend reutiliza `scripts/eval/benchmark_process.py:OwnedProcess` y su Job Windows propio, sin ampliar API o admisiones. ROOT fija una Factory externa a los árboles evaluados y verifica sus bytes antes de importar/ejecutar candidato. El broker queda asignado al Job antes del gate. Sólo la ruta existente de miembros actuales del Job propio, con identidad verificada, permite retener handles. PID, JSON o bool no conceden autoridad.

Los plazos son absolutos y los logs están acotados antes del run. Timeout, cancelación, overflow o excepción revocan efectos y terminan exclusivamente el grupo original. ROOT conserva prefijos exactos, argv, entorno, UTC y observaciones reales. Cierre no acreditado conserva `UNKNOWN_QUARANTINED`; no se convierte en conocido por una etiqueta o callback. E/C/P de éxito requieren bytes completos estables, exit0, fuentes exactas y devolución real de recursos acreditada por el padre.

## Alternativas descartadas

- **O2 — Staging byte congelado separado:** conserva argv relativo, pero añade tercer inventario, equivalencia de imports/cwd y remapping. Coverage.py admite la solución externa de O1.
- **O3 — Excepción de dos outputs internos:** exige relajar la regla de inmutabilidad. Moverlos después no satisface la norma actual; la excepción resulta innecesaria.

## Consecuencias

La [copia del contrato](../roadmap/2026-10-11-m3-produccion-portada-video-letra/cohort-metrics-contract.md) precisa sólo §§8.1/8.2.1/8.3. Schemas, versiones, readers, campos, DAG, umbrales, gates musicales y G/T aceptados permanecen intactos. Los fallos usan diagnósticos fuera de los readers E/C/P; no inventan `exit_code:0`, fin real o reap para encajar sus campos.

Windows es el primer soporte propuesto. Linux/Docker siguen pendientes de custodia genérica propia y QA independiente. `KernelGroup` y admisiones M2 no se amplían. No se añaden servicios, herramientas externas, SDK instalados, GPU ni privilegios.

La fuente CM `6cc06770734a9a8287a10c2a00fcaacc226eca2eb255c1b31f5df7f40b70c680`, raws y recibos previos permanecen inmutables. Este nuevo corte exige preaprobaciones y ejecuciones nuevas. No transfiere créditos históricos a la fuente corregida ni cierra T06, M3, D13 o M0–M5.

## Estado

`aceptada`. ROOT ratifica O1 bajo delegación del propietario tras revisión A/B documental sin gaps y QA independiente84/84, qa-gateexit0. La propuesta revisada y sus SHA permanecen en el recibo de adopción; no se atribuye aprobación directa adicional al usuario. La implementación posterior exige RED causal A1/B1, coverage whole por módulo, revisión y QA runtime independientes.
