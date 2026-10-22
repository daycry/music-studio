# Revisión T-10 — intento 3

Lentes A+B de contexto fresco: **0 Critical, 0 Important, 0 Minor**. Diff correctivo completo de dos archivos leído y reconstruido desde preimágenes. Selector automático C/D false y puerta de alcance exit 0 sin avisos, info ni exclusiones de usuario. [Recibo](review3-receipt.json).

| Criterio | Veredicto | Evidencia |
|---|---|---|
| R10-07: plan Windows portable | ✓ CPU | capabilities.py:97; .as_posix; test con PureWindowsPath y resolución por componentes POSIX |
| Custodia y guardas CLI | ✓ CPU | rechazo de cambios en plan/harness/texto/derechos/recursos; estados pendientes y guarda de contenedor |
| Planes anteriores | ✓ | plan QA SHA a04150c2 preservado; planes nuevos comprobados |
| TDD | ✓ | RED UTF-16 BOM: AssertionError funcional antes del fix; GREEN posterior |
| Cobertura del archivo cambiado | ✓ | 98/119: 82,352941 %, fuente oficial pytest-cov |
| Alcance/constitución | ✓ | cambios de rutas internas, ledger único y declaración de derechos conservados |
| R10-01…06 previos | ✓ preservados | sin evidencia nueva que justifique reapertura |
| Linux real/GPU/música | pendiente | revisión técnica no acredita el preflight real ni aceptación musical |

Cada lente ejecutó 11 pruebas dirigidas del CLI, sin fallos ni omisiones. Se solapan: no se cuentan como 22 pruebas únicas. Root verificó ambos JUnit y las 59 fuentes actuales. `.coverage` raíz se conserva; el incidente de caché Ruff previo permanece declarado y no se afirma preservación del árbol completo. Sin suite88 repetida, Docker, GPU, modelos ni audio por revisores. QA fresca y preflight real pendientes; T-10 sigue en progreso.
