# ADR-0001 · Reinicio desde cero

- **Estado:** aceptada · **Fecha:** 2026-09-28

## Contexto
La planificación anterior (julio–septiembre 2026) se escribió como para un proyecto corporativo: presupuestos en €, gates legales, dirección, clientes y ~1 MB de documentos. Había un runner a medio hacer, pensado para una GTX 1070 de 8 GB. El proyecto es personal y la máquina tiene ahora una RTX 5070 de 12 GB.

## Decisión
- El desarrollo **empieza de cero**. No se reutiliza el código del repo `suno-sondo-clone`.
- La documentación anterior se conserva **intacta** en `docs/archive/roadmap-2026-07-27/` como histórico. Ya no es fuente de verdad.
- La documentación vigente es la de `docs/` (fuera de `archive/`) y sigue un proceso ligero:
  - ADR para las decisiones.
  - Una iniciativa por hito en `docs/roadmap/`, compatible con el plugin `custom-agents`, sin evaluación económica.

## Consecuencias
- **Se conservan** las decisiones técnicas buenas: pesos seguros (safetensors, sin pickle), linaje desde el día 1, manifiesto por artefacto, FLAC + exportación a 48 kHz, UX derivada de Suno sin su identidad y la rúbrica de escucha.
- **Se descarta**: multiproveedor cloud, pod caliente, cuotas, kill switch, SSO + 2FA, WORM/C2PA, stop-loss en € y RACI.
