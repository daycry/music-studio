---
id: ADR-0085
estado: aceptada
fecha: 2026-10-11
---

**Título:** Familias de publicación tipadas M3, dispatch multiversión y escena N0 portable.

**Estado propuesto:** propuesta. **Decisión arquitectónica:** ROOT por delegación explícita el2026-10-11, PF-O1; revisión/adopción canon separadas. **Número:** no reservado por este actor.

**Contexto.** ADR-0074 conserva manifiestos inferencia1/CPU2, snapshotsCPU2 y API M1. El corte code-first aún valida manifest1 y emite Song1; timeline1 describe montaje, no N0. D-02/D-03 fijan19pares/7sujetos y capturas/sellos/CAS tipados. Analysis/import/backup no caben en el manifiesto1 actual ni son Asset/Take ficticios. Un original cerrado no puede reescribirse para añadir esos sujetos, remap, privacidad o escenario.

**Decisión.** Adoptar PF-O1: readers family/version/reader exactos, referencias byte-exactas, envelopes Artifact1/Package1/prepared por7sujetos y ramas engine/cpu/upload/import/maintenance de evidence real. No hybrid como executor, ningún engine/seed de padre como ejecución. CPUv2 y SongCPUv2 originales cerrados; nuevo song_bundle1 **siempre** para índice portable M3, refiere snapshot1/2 sin modificación y closure/proyección D-08. TimelineV2/SceneN01 para N0 con audio/timing/context/features/pins/fonts/clock fijos. Metadata1 exclusiva de audio/stems/video/lyrics, ligada a take/letra histórica solicitada; export_project/project_zip exige metadata_ref NULL literal en prepared/final/Package y closure Songv1/SongCPUv2/SongBundleM31, incluso con Takes. Song válida master NULL/takes [] conserva título/letra/portada/revisiones sin metadata de Take ni audio/Take ficticios; operation/kind/payload/profile coinciden con D-02 y gate ausente bloquea antes efectos; original byte-exacto+sidecar, embedding derivado; stems4roles48k sin normalizar con offsets/frames comunes.

**Cierre/remap/privacidad.** Toda historia/cierre requerido por §4.5 conserva padres/roles/maps/maestro/declaraciones/refs/media/manifests/metadatos/rights. Catálogos D-08 y biblioteca D-09 conservan sus gates. Replay sólo receipt propio misma captura; no adopción por hash/ID/ruta, no-clobber/CAS y maps nuevos con originals/owners source separados. Operaciones import/maintenance no se convierten en inferencia. No live authority/leases/PIDs/secretos/paths absolutos; payload privado autorizado para letra/foto. Original inadmisible impide export completo sin reescribirlo.

**Documentos que cambia explícitamente.** Convenciones actuales describen sólo API sin versión y formatos/paths básicos: actualizar sólo la extensión multiversión D-04, conservando API aditiva ya autorizada ADR-0074. Datos actual describe Song1/timeline1/autoridad por Take: añadir la concreción M3 por sujeto, TimelineV2 y nueva familia SongBundleM31. La prescripción CPU2 de ADR-0074 no se invalida. No cambiar baseline/DTO M1/engine /v1 ni ampliar reconstrucción SQL.

**Alternativas descartadas.** PF-O2 manifiesto universalv3/proyección única, por reinterpretación de historia y reconciliación innecesaria. Sentinelas, alias por versión y JSON libre, por procedencia falsa y falta de reader. Sanitizar originales en export o remap, por romper byte-exactitud. Asset job/analysis/import/backup o Song de biblioteca artificial, por contradicción de D-03/baseline.

**Consecuencias/gates.** Nuevos schemas/readers/goldens concretos code-first, migraciones sólo aprobadas D-03 y comparación compatible previa CPU2. Package prepared elimina SHA circular y no autoriza serving. Perfils/métricas/codec/tags/fonts D-05/06/07, catalog/identitymap/cuotas D-08, mantenimiento D-09 y validación runtime/crash/concurrencia quedan pendientes. Aprobación documental no acredita ejecución, producto, remap ni restore.

**Umbral.** Cierra alternativa real y afecta contracts/snapshots/worker/render/import/backup: requiere ADR específico y apéndices adoptados antes de schemas/código. ROOT reserva número y enlaza cadena; este actor no reserva ADR canon.


## Ratificación ROOT — 2026-10-12T04:36:08.008220+00:00

PF-O1 ratificada bajo delegación del usuario tras revisión2 FULL32A/5B sin gaps y QA documental46/46. Contrato fuente cf967985d01f102a908ddd0c9658d59985156aafffc47691abc71e9995e56c83, 130pins y7artefactos verificados. A01/B01 corregidos; project_zip metadata_ref NULL literal siempre, cuatro medios ByteRef y lector Take intacto. Esta ratificación fija formatos; no acredita lectores, goldens ejecutados ni funciones de producción. T-04 documental cerrada; M3 producto pendiente.
