# Derivado privado del empaquetador T-16

Estado: **READY_CONFIG_ONLY**. Revisión adversarial y QA fresca pendientes.

El candidato `pack-comparison.py` deriva del original `.cache/dev-cycle/t16/pack-comparison.py` (SHA-256 `226b312267c89dba6bf3691220f1375f6be4414ee515ddff84953fe461454780`).
SHA-256 del candidato: `e09d81433e25a19a3b161d7a56963c3fdc40aa7ca4ef13de6c27587a4bcf8d5f`.
Solo cambian tres literales: runtime nativo, configuración nativa y puntero nativo. Se añaden tres comentarios
de cabecera y se conserva el docstring original. La configuración conserva SHA-256 `a68a2ff5c52891694d21f4ef7451da2559efbf4c3aaf1471ae1846cc187f024c`.
El argumento sigue siendo `--session` obligatorio; no se añadió `--prepare-only` ni otros flags.

La comprobación CPU estática usa Python gestionado 3.12.14, AST de Python 3.11 y compilación
en memoria. El AST completo coincide con el original después de normalizar exactamente las tres rutas;
no se ejecutó ningún nodo del packer. Esto preserva todas sus comprobaciones y operaciones: seis salidas,
validación de recibos nativos mediante `validate_input_receipt`, emparejamiento LM/DiT por semilla,
ganancia lineal sin limiter, checkpoint y reanudación, publicación atómica de la referencia,
manifiestos hijos y linaje, privacidad y ciego A/B por semilla.

`delta.patch` y `rollback.patch` fueron aplicados en memoria con comprobación de contexto;
ambos reproducen sus respectivos destinos byte por byte. La reversión literal también coincide
byte por byte con el original. `literal-changes.json` declara las tres sustituciones únicas.

Se congelaron 71 rutas (69 archivos presentes) en mapas
`freeze-before.json` y `freeze-after.json` con claves relativas a la raíz del repositorio, idénticos.
Las nueve fuentes de producción coinciden con `native-resolution-comparison/receipt.json`.
Se preservan T-15 y sus ocho helpers por SHA/AST, ambos fuentes de comparación, CLI controlado,
`scripts/generate.py`, audio-post/manifest y antecedentes QA. Los punteros ausentes figuran como null.
Los inventarios inmediatos de runtime y productos permanecen idénticos; no se leyeron audios, letra,
caption, valores de `.env` ni rutas personales de referencia.

El recibo CPU histórico del packer registra SHA `bd054d20a33c4c532a7b1727619d3b29c26020a0fd7fa55fa6dcbeb64f8f4413`,
distinto del original vigente: es un antecedente preservado, sin crédito de QA para el candidato.
Los posteriores `harness-fix1-receipt.json` y `harness-qa-receipt.json` sí registran el SHA
del original vigente (12 tests CPU históricos); se cotejaron y preservaron
sin repetir suites ni atribuir ese tramo a la QA fresca del derivado.
TDD n/a: configuración literal y comentarios. No se empaquetó una sesión real ni sintética,
no se generaron tomas, no se tocaron GPU, modelos, Docker, jobs, instalaciones, producto, documentación,
ledger o Git, ni se accedió a memoria/knowledge. Las seis tomas de 90 s siguen pendientes;
CA3/CA4 siguen abiertos. No hay ganador ni calidad musical aprobada.

Los SHA propios de `receipt.json` usan claves relativas a esta carpeta y excluyen el propio recibo.
`own-artifacts-sha256.json` incluye el recibo y excluye únicamente su propio archivo para evitar circularidad.
