# Revisión adversarial — T-17, intento 1

Revisión independiente A+B comunicada por el orquestador. Alcance: auditoría CPU y documentación; sin cambios de producto ni inferencia GPU. QA final pendiente en este intento; la tarea no queda cerrada por esta revisión.

| Lente A: criterio | Resultado |
|---|---|
| Corpus y comparación de entradas | ✓ |
| Presupuestos de tokens | ✓ |
| Código instalado y hashes de origen | ✓ |
| Flags efectivos | ✓ |
| Preservación del material previo | ✓ |
| Publicación sin contenido privado | ✓ |
| Constitución | ✓ |
| Alcance CPU/prosa | ✓ |
| Trazabilidad explícita T-14 → control T-15 | ✗ |

Lente B: todos los criterios comprobados conformes; sin defectos de corrección encontrados.

| Hallazgo | Gravedad | Escenario y corrección preparada |
|---|---|---|
| A1: faltaba trazabilidad pública del fragmento T-14 al control T-15 | Important | El lector no podía comprobar qué entrada de T-14 cubría el probe. Se añade el alias con hashes y metadatos verificados en [fragment-lineage-receipt.json](fragment-lineage-receipt.json) y el párrafo enlazado del [informe](audit-report.md). Pendiente de confirmación independiente en intento 2. |
| A2: primera frase del candidato demasiado larga | Minor | Mezclaba preparación, conservación y traducción. Se divide en frases cortas en el informe, sin cambiar conclusiones. Pendiente de confirmación independiente en intento 2. |

Comprobaciones independientes comunicadas por A+B: 16 casos nativos, seis hashes de código origen, 16 archivos de tokenizer contra lock, 32 registros preservados, 72 versos conservados y cuatro recibos públicos coincidentes con sus fuentes. Scope: exit 0. Ledger: cero incoherencias y ocho avisos. No se han presentado rebates.

Las correcciones preparadas no convierten retrospectivamente este intento en verde. El siguiente intento debe comprobarlas y el QA final debe acreditar su propio alcance.
