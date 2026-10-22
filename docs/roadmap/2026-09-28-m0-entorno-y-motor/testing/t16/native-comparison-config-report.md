# Preparación privada de comparación nativa T-16

READY_CONFIG_ONLY. Derivados privados de dos archivos, sin modificar originales.
Plan: único cambio `image_digest`, ahora `sha256:18d94fd4b377016a895e5cd89ee446b64c872421b0d401987f58b0583b16da2d`. Se conservan seis tomas90s,
semillas1/2/3, shift1, Turbo8 y SFT50/CFG7, idioma/BPM/LM y hashes de entradas.
Runner: cabecera y seis tipos de configuración literal (siete ocurrencias adicionales),
sin cambiar algoritmos, randomización, relojes, guardas, cancelación ni limpieza.
`task_root` y CLI siguen en T16; destinos nativos propios y nuevo ULID de salida.

Evidencia real: AST Python3.11 PASS; prepare-only exit0:
`{"status": "ready_cpu", "takes": 6, "duration_s": 90, "image_digest": "sha256:18d94fd4b377016a895e5cd89ee446b64c872421b0d401987f58b0583b16da2d", "gpu_executed": false}`. Docker image inspect exit0 e ID exacto.
Rollback de runner/plan byteexacto y cuerpo idéntico tras deshacer literales.
Freeze antes/después: 51 archivos idénticos, incluidas nueve fuentes,
dependencias, originales, revisión previa y QA privada; inventarios/puntero intactos.
Los cuatro hashes completos viven en receipt.json; delta.patch/rollback.patch y
literal-changes.json acreditan los cambios; freeze-before/after.json acreditan contexto.

TDD n/a: configuración literal/cabecera. No GPU, jobs, contenedores, pesos,
instalaciones, build ni suites de producto. Revisión fresca y QA independiente pendientes.
No acredita CA3/4, calidad musical, ganador ni cierre de T16/M0.

Incidencia local del verificador: primer arranque exit1 DEPENDENCY_MISSING por
nombre inexistente scripts/prepare_generation.py en su lista de freeze. Corregida
la lista antes de crear candidatos; segundo arranque exit0. No fue un fallo
del arnés ni motivó cambio de lógica.
