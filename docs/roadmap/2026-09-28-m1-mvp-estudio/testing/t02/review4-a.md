**Lente A · M1/T-02 · intento 4: sin defectos nuevos identificados en fix3.** R02-12 y R02-18 muestran corrección suficiente dentro del alcance solicitado.

Revisión estática exclusivamente del contenido INLINE. No ejecuté herramientas, tests ni hashes; las cifras de ejecución y custodia pertenecen a raíz.

| T-02 → criterio reevaluado | ✓/✗ | Evidencia y valoración |
|---|:---:|---|
| R02-12: impedir promoción ordinaria del soporte | ✓ | `fix3_invariants.py:6` rechaza cambios de marca sin excepción de importación y toda degradación a soporte. Cubre también promoción y título en un mismo UPDATE. `test_review_fix3_t02.py:32` verifica SQL/Core/ORM/bulk, permanencia de soporte, exclusión FTS/dispatch y rollback. |
| Promoción completa compatible y edición global legítima | ✓ | `snapshots.py:584` comprueba colisiones antes de abrir `snapshot_import`; `:602` promueve únicamente la raíz importada. Tests en `test_review_fix3_t02.py:77,189` y `test_review_fix2_t02.py:652` conservan restauración completa, dependencias adicionales y globals editables. |
| R02-18: eliminar lecturas individuales duplicadas | ✓ | `snapshots.py:570` carga identidades por tabla con IN≤400; `:600` reutiliza la caché y `:616` valida raíces por lotes. Tests en `test_review_fix3_t02.py:115,121` instrumentan el ámbito de restore. Raíz aporta 38/38/55 SELECT para 20/200/405 takes; no constituye una medida de latencia. |
| Colisiones y caché dentro de una transacción consistente | ✓ | `snapshots.py:560` adquiere el escritor antes de leer colisiones. Caché, excepción e inserciones usan la misma conexión. `test_review_fix3_t02.py:139,225` comprueba bloqueo concurrente, rechazo previo a la excepción y rollback de filas existentes/ausentes ante fallo tardío. |
| Migración aditiva y conservación histórica | ✓ | `0004_snapshot_promotion.py:7` encadena sobre `0003` y añade únicamente la guarda. Conforme a `CONSTITUTION.md:39`. `test_review_fix3_t02.py:286` cubre ciclos hasta head0004; el ajuste histórico en `test_review_fix2_t02.py:597` conserva sus assertions sobre0003. |
| Alcance del plan | ✓ | Guarda, restauración y regresiones corresponden a persistencia T-02 y `ADR-0044:18,20,26`. Scope suministrado: 32 archivos, ninguno fuera de alcance. |
| Tests y cobertura de apoyo | ✓ | Assertions relevantes leídas. Raíz aporta 327 aprobados/3 skips Windows y pruebas Linux separadas. **365/394 = 92,64 % mide tres módulos completos**, no líneas del diff; cero exclusiones. Los 30 casos de Verificación están incluidos, sin sumarlos otra vez. |
| Verificación y estado honesto | ✓ | Evidencia suministrada de selección exacta y ciclos CLI vacíos/poblados. `tasks.md:101` mantiene `en-revision`, con criterios abiertos. Los datos desconocidos del CLI original siguen desconocidos; no se atribuye limpieza global ni aceptación M-03. |
| Contratos y descripción aplicable | ✓ | Fix3 conserva los contratos; paridad de copias/wheel atribuida a raíz. `README.md:91` describe promoción validada y `fix3-report.md:5` documenta la guarda y lectura por lotes. No identifico contradicción nueva con la constitución explícita. |

Interop **no aplica**: no se modifican `commands/`, `agents/` ni `hooks/`. OpenAPI **no aplica**: los contratos suministrados son JSON Schema.

**Gaps: Critical 0 · Important 0 · Minor 0.** Se conservan los veredictos previos sin reabrir escenarios aprobados. Este resultado no cierra T-02 ni acredita QA, Git, M-03 o aceptación humana; la adjudicación corresponde al orquestador.