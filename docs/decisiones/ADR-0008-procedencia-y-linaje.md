# ADR-0008 · Manifiesto de procedencia y linaje desde el día 1

- **Estado:** aceptada · **Fecha:** 2026-09-28 · Simplifica D-07 y D-20…D-22 de la documentación archivada

## Decisión
- **Cada artefacto generado lleva un `manifest.json` (v1):** take, stems, imagen, versión de plano de vídeo, render, export o LoRA. Recoge:
  - los modelos usados, con su rol, revisión, hashes, licencia y declaración de datos de entrenamiento;
  - el pipeline (engine, imagen, workflow, código remoto);
  - la petición, con la letra por hash y la semilla;
  - las entradas, con sus derechos y su consentimiento;
  - el linaje, el post-proceso, el proveedor (local o externo), `commercial_use` y la telemetría.

  El esquema completo está en [`../arquitectura/datos.md`](../arquitectura/datos.md) §3. Lo escribe el server ([ADR-0017](ADR-0017-postproceso-y-manifiesto-en-el-server.md)).
- **Linaje desde la primera migración:** `lineage_edge` admite varios padres y guarda `section_map`; además se guardan `take.root_id` y `take.derivation`.
- **Declaraciones obligatorias:**
  - autoría de la letra en cada generación: propia · asistente · dominio público · con permiso;
  - derechos de todo lo que se sube;
  - consentimiento cuando aparece una persona real.

  Sin declaración, el trabajo no se encola.
- **El manifiesto v1 solo crece:** los campos nuevos son opcionales y un manifiesto ya emitido no se reescribe nunca.
- **Fuera del alcance personal:** firma C2PA, ledger WORM y watermarking. Se retoman en el [gate GC](../legal/comercializacion.md).

## Motivo
Hacerlo desde el principio no cuesta casi nada; reconstruirlo después es imposible. El linaje es además lo que permite extender, regenerar secciones, montar el árbol de versiones y hacer vídeo sin migraciones.
