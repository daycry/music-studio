# Revisión de dos lentes — intento 3: observabilidad autónoma T-09

Lentes A+B+D frescas, Cfalse/Dtrue por selector; scope0 y 64fuentes/12docs intactos. Resultado: **0Critical/1Important/0Minor**. Delta completo de dos archivos leído. A aprobó nominal; B encontró un caso nuevo reproducible, confirmado por root. D sin hallazgos.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| O4a consultas secuenciales con/sin historia | ✓ CPU | Diez dirigidos por lente; no sumados a suite95 |
| Guardas anteriores/custodia/TDD/constitución/alcance | ✓ preservado | 37sellos,64fuentes,12docs;coverage258/301=85,7143% |
| Futuro externo del piloto con continuidad | ✗ | B3-01 confirmado por root |
| Rendimiento del extremo máximo | ✓ CPU | Cuatro conversiones por muestra;24k→96k llamadas/0,0859424s; no RTF |
| Generated/OpenAPI | n/a | No comandos/agentes/hooks/specs en delta |
| GPU/T-09 cerrada | pendiente | Piloto/matriz160 no ejecutados |

| ID | Grado | Tarea | Corrección | Evidencia |
|---|---|---|---|---|
| R09-O4b/B3-01 | Important | T-09 | Pendiente | observation.py:612. now externo132,100;Windows131,030;WSL132,240/browser132,260;live132,000. validate_samples rechaza futuro;validate_auto usa el final futuro y acepta provider_verified. |

La aprobación nominal de A queda limitada por el escenario específico de B. No se reabre O1/O2/O3/O5 sin evidencia. O4a anterior está corregido; el nuevo gap no se transforma en deuda ni se baja de grado. El repro es sintético CPU, no adquisición real. Root conservó un original propio en review3/root-future-repro/receipt.json; su primer lanzamiento falló antes de escribir por import path, corregido sin repetir tests del agente.

Cada lente ejecutó10dirigidos propios con resultados solapados. B tuvo un error del envoltorio PowerShell después de pytestverde; freeze posterior Python salió0. D tuvo aviso de cacheprovider desactivado, sin fallos. Los revisores son de solo lectura: sus informes fueron mensajes originales, esta publicación es una síntesis del orquestador, no archivos originales producidos por los revisores.

**Decisión del orquestador al alcanzar el límite de3intentos:** continuar con una corrección acotada de este gap y una revisión excepcional explícita, bajo la delegación del propietario para decidir alternativas y finalizar autónomamente. No reiniciar el contador, no afirmar verde ni aceptar deuda. No cargar GPU antes de revisión y QA conformes. T-20 documental conserva aprobación y QA pendiente.
