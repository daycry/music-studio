# T-16 — lente A, intento 1, tramo CPU

Fecha: 2026-10-06. Revisor fresco `/root/review_t16_1_a`, solo lectura. Base `ef66a36bedf08fb996f88ef6cb9633b5f51f13b8` más cambios locales/nuevos: 22 archivos, leídos por bloques. Journals ajenos excluidos sin lectura. Resumen estructurado conservado por el orquestador.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| CA1 identidad SFT/Turbo | ✓ | descriptor.py:19, adapter.py:448; test_inference_controls.py:19,44,59 |
| CA1 defaults Turbo8 y SFT50/CFG7 | ✓ | input_profile.py:8; test_inference_controls.py:76 |
| CA1 límites enteros/CFG finito y validación directa | ✓ | input_profile.py:10; test_inference_controls.py:105, catorce escenarios inválidos |
| CA1 CLI, briefs y manifiestos | ✓ | generate.py:153,386; test_generate_inference.py:12,37,52,75 |
| CA1 progreso/cancelación | ✓ | adapter.py:259,535; test_inference_controls.py:114, 23 pasos/CFG4 y CANCELLED |
| CA1 planned/captured/validador | ✓ | preflight.py:135,197,315; manifest.py:219,274; test_generate_preparation.py:161,191,213; deriva DiT rechazada |
| CA1 contrato y verified conservados | ✓ | Descriptor mantiene capacidades falsas; exportador exit 0; ningún contrato modificado |
| CA2 RED/GREEN | ✓ | Trece logs RED leídos y fallos reales; 41 pruebas declaradas verdes |
| CA2 cobertura | ✓ | JSON oficial cruzado con hunks: 59/63=93,65 %; mínimo del diff 86,36 %, archivo completo 88,34 % |
| CA2 ADR/documentos, sin pesos/locks/dependencias/default nuevo | ✓ | Diff completo y ADR-0027:26,30; documentos afectados actualizados |
| CA2 revisión y QA completos | Pendiente | Esta revisión en curso; QA independiente aún pendiente, no se cierra CA2 |
| CA3 seis tomas GPU/telemetría/descarga | Pendiente | Casilla abierta; pruebas CPU no se presentan como GPU |
| CA4 pares privados/escucha | Pendiente | Casilla abierta; sin ganador ni cierre |
| Alcance | ✓ | Scope propio exit 0, 22 en alcance y cero fuera; fixture solo dos kwargs autorizados |
| Verificación y estado | ✓ | 41 declaradas, 271 dirigidas y 156 de imagen; T-16 permanece en progreso |
| Constitución explícita | ✓ | Sin contradicción introducida de CONSTITUTION.md:19,21,24,25,32,33,37 |
| Entrada CFG frente al sampler Turbo | ✓ | ADR-0027:30 y fuente fijada generate_music.py:288 distinguen entrada7/interno1 |
| Interop | No aplica | No cambia commands/, agents/ ni hooks/ |

**Gaps: sin hallazgos de requisitos o constitución en el tramo CPU.** La aprobación de esta lente no cierra T-16 ni sustituye QA.

Evidencia ejecutada por el revisor: controles/CLI/preparación, 104 passed in 1.30s; hook real de progreso, 1 passed in 0.23s; scope/exportador exit 0 y cuatro ejemplos válidos. Cruce independiente de cobertura de los seis archivos y lectura de los 19 resúmenes nativos: trece admitidos/seis bloqueados. Consulta de ADR por script sin índice: cero aciertos, sin leer journals. Ninguna corrección de producto.
