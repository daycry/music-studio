# Revisión independiente de T-15 — intento 1

2026-10-05. Lentes A y B, agentes `reviewer` de contexto fresco, solo lectura. Se revisó el diff completo frente a `main`, la preparación efímera y los metadatos privados. No hubo GPU ni escrituras de los revisores. `scope-check --json`: exit 0, sin avisos ni exclusiones de usuario; siete journals ajenos preservados. Selector: C=false, D=false, por tratarse de prosa/configuración sin cambios de producto. Tier del revisor: frontmatter, sin override disponible de modelo.

| Criterio | Resultado |
|---|---|
| Investigación primaria, licencias y límites; sin superioridad local inventada | Conforme |
| Letra/control idénticos, hashes, captions 415/426, configuración fija | Conforme; comprobación CPU independiente |
| Preflight y descarga previstos | Conforme por lectura; ejecución pendiente |
| Parada ante spill | Important R1 |
| Recuperación de MP3 completos | Important R2 |
| Privacidad, códigos separados, ganancia lineal, linaje | Conforme por lectura; ejecución pendiente |
| TDD/cobertura n/a; producto/contratos/pesos intactos; M0 abierto | Conforme |
| Seis tomas, normalización real y QA | Pendientes; tarea aún en progreso |

| # | Grado | Gap | Evidencia y escenario | Estado |
|---|---|---|---|---|
| R1 (A1/B1) | Important | La supervisión comprueba spill después de terminar tres salidas | `.cache/dev-cycle/t15/run-comparison.py:105–126`. CPU: `VramGuard` con cap 1000 y pico 960 marca `spilled=true`, sin excepción; la tanda puede continuar. Root confirma la semántica 95 %/100 % en `engine_common/runtime.py`. | Pendiente de fix1 |
| R2 (B2) | Important | Recuperación puede certificar un MP3 parcial como 90 s | `.cache/dev-cycle/t15/run-comparison.py:199–209`. B reproduce un MP3 decodificable de 10,032 s que cumple la condición de LUFS/pico; el manifiesto con metadato fijo de 90 s pasa esquema. Root confirma que faltan duración y procedencia antes de adoptar una copia existente. | Pendiente de fix1 |

Fusión: 0 Critical, 2 Important, 0 Minor. Los dos gaps se aceptan; no hay rebates. Se devuelven al implementer antes de generar. Las verificaciones runtime pendientes no son defectos de una tarea cerrada ni autorizan cerrarla. AST 3.11 y hashes conformes, sin ejecución de producto ni suite nueva. Los revisores contrastaron las fuentes oficiales enlazadas en [la investigación](model-review.md).
