---
category: GOTCHA
evidencia: validated_case
fuentes:
  - packages/audio-post/audio_post/pipeline.py
  - packages/audio-post/tests/test_directory_attributes.py
  - .cache/dev-cycle/20261106-m0-t16/windows-diagnosis/diagnóstico.md
  - .cache/dev-cycle/20261106-m0-t16/fix2/red-pinned.log
  - .cache/dev-cycle/20261106-m0-t16/fix2/full-final.log
  - https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants
tags:
  - "area:almacenamiento"
  - "plataforma:windows"
  - "componente:audio-post"
  - "tema:identidad-directorios"
---

# Los bits de residencia local no identifican un directorio Windows

Propuesta pendiente de curación por `knowledge-curator`. `GOTCHA` y
`validated_case` son propuestas conforme a la taxonomía del proyecto;
no constituyen aprobación ni autorización de exportación.

## Síntoma

La QA CPU amplia registró dos falsos cambios de identidad al crear un hijo
o enumerar un directorio vacío. El atributo comparado cambió de `0x10` a
`0x180010`, con FileId nativo estable. La corrida original conserva
422 tests aprobados, 9 omitidos y 2 fallos; no se convierte en verde.

## Causa

`_directory_identity` incluía los bits `PINNED` y `UNPINNED` en su tupla.
La sonda controlada extrajo por AST la función del árbol y del baseline
`3dede62cc9a76511eaf3eca30fb9082439b51222`; ambos reprodujeron el defecto
con dev/ino/mode/tag constantes. Esto prueba la causa lógica del falso
positivo, no una corrida nativa amplia fallida del baseline.

Las [constantes oficiales de Windows](https://learn.microsoft.com/en-us/windows/win32/fileio/file-attribute-constants)
asignan `0x80000` a `PINNED` y `0x100000` a `UNPINNED`, relativos a
residencia local. `REPARSE_POINT=0x400` es distinto. El disparador externo
que alteró los atributos en la QA sigue desconocido; no se atribuye a un
proveedor, servicio o filtro concreto.

## Alternativa aplicada

El fix excluye únicamente esos dos bits además de `0x10000000`, cuya
exclusión ya existía. Conserva dev/ino/mode/tag y el resto de atributos.
Un cambio de identidad o del bit oculto sigue distinguiendo directorios;
reparse, tag no nulo, fichero regular y enlace siguen rechazados.
Los controles nativos de FileId y sustitución permanecen en la suite.

## Evidencia y límites

La regresión `test_residency_metadata_preserves_same_directory[pinned]`
ejecutó el módulo real y falló antes del fix con `524304 != 16`.
El implementador conservó ese RED y el GREEN posterior. La selección
final de directorios pasó 22 tests. La suite final de `audio-post` pasó
231 tests y omitió 9, exit 0. Los controles negativos comprueban cambios
dev/ino/mode y atributos restantes, además de rechazar reparse y tags.

Los recibos privados están en `.cache/dev-cycle/20261106-m0-t16/fix2/`:
`red-pinned.log`, `focused-final.log`, `full-final.log` y
`full-final-exit.txt`. El diagnóstico de fases 1–3 permanece en
`.cache/dev-cycle/20261106-m0-t16/windows-diagnosis/diagnóstico.md`;
su fase 4 era entonces una propuesta, aplicada después en este fix.

La fase 4 tiene implementación y pruebas propias. La [QA2 independiente
del 2026-11-06](../../../roadmap/2026-09-28-m0-entorno-y-motor/testing/condicionamiento-cpu-2026-11-06.md)
acredita `PASS_CPU_SOFTWARE_ONLY`: 437 aprobados, 9 omitidos y 0 fallos
en una corrida, incluidas las dos pruebas nativas y 13 regresiones nuevas.
Los recibos privados son `qa-fixed2/report.md` y `qa-fixed2/summary.json`
bajo el mismo directorio de evidencias. La QA amplia anterior permanece
roja como historia. Este caso no acredita emparejamiento histórico completo,
generación GPU, aceptación musical ni cierre de T-16, M0 o M1.
La propuesta sigue pendiente de curación, sin promoción ni exportación.
