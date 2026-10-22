**Lente A · M0/T-11 · intento 1/3: tres gaps Important.** Revisión íntegra de las cuatro fuentes nuevas y sus tests, exclusivamente sobre el contenido INLINE. No ejecuté herramientas, pruebas ni verificaciones de hashes.

| Criterio | Resultado |
|---|---|
| T-11 → diez briefs y estilo literal | ✓ Planifica 30 posiciones, conserva estilo/letra/tags y declara entradas/derechos pendientes (`run.py:104`, `run.py:134`). Las letras propias reales siguen pendientes. |
| T-11 → tres semillas fijas | ✓ Orden B-01…B-10 × 101/202/303 comprobado antes del workflow sintético (`run.py:508`). |
| T-11 → ganancia lineal −16 LUFS / ≤−1 dBTP | ✓ Implementación proporcional, medición posterior y conflicto sin derivación lista (`metrics.py:111`, `metrics.py:214`). |
| T-11 → anonimización y selección best-of-3 | ✗ Códigos temporalmente ordenables y agrupación incorrecta tras fallos parciales; gaps A1/A2. |
| T-11 → suelo WER real y perfil verificado | ✗ El validador positivo acepta procedencia/cobertura autodeclaradas; gap A3. El corpus real continúa pendiente. |
| T-11 → hoja Markdown y campos humanos vacíos | ✓ Rúbrica, métricas separadas, pendientes y ausencia de ganador automático (`run.py:645`). |
| T-11 → staging para análisis | ✓ Copia exclusiva a `data/tmp/<id>/in/audio.wav`, con contraste de contenido (`metrics.py:252`). |
| Alcance / Archivos | ✓ Los cuatro archivos corresponden a `tasks.md:455`; el scope INLINE declara cero archivos fuera de alcance. |
| Tests y cobertura | ✓ Evidencia aportada: 48 pruebas y 30 vecinas; módulos nuevos completos **86,83 % / 90,76 %**, sin exclusiones. Los tests leídos no cubren los escenarios A1–A3. |
| Constitución | ✗ A3 afecta la procedencia requerida para descontar el suelo; no atribuyo una infracción constitucional adicional sin principio explícito aplicable. Las rutas, ejecución local y ausencia de sobrescritura tienen guardas visibles. |
| Verificación de tarea cerrada | ✓ No procede exigir cierre: T-11 permanece `en-progreso` (`tasks.md:449`). Dry-run y exit 2 constan en la evidencia; la verificación de 30 tomas reales sigue abierta. |
| Generados / interop | ✓ No aplica: el diff no toca `commands/`, `agents/` ni `hooks/`. |
| OpenAPI | ✓ No aplica: ninguna spec OpenAPI cambia. |

| ID | Gravedad | Fichero:línea | Escenario concreto y requisito incumplido |
|---|---|---|---|
| A1 | Important | `scripts/eval/run.py:628` | Los códigos usan `generate.ulid()`, cuyo prefijo contiene el timestamp (`scripts/generate.py:208`). Si su creación cruza milisegundos, ordenar los nombres recupera bloques del orden original de slots, aunque la hoja esté barajada. El código aleatorio no debe revelar el orden del plan. El test de `test_evaluation_guards.py:470` comprueba únicamente el orden de la hoja. |
| A2 | Important | `scripts/eval/run.py:708` | `execute` filtra las tomas listas (`run.py:590`) y `anonymize` agrupa cada tres elementos consecutivos. Si B-01/101 tiene conflicto de pico, el primer grupo contiene B-01/202, B-01/303 y B-02/101. La selección deja de ser best-of-3 **por brief**. Debe conservar agrupación por brief y señalar grupos incompletos. |
| A3 | Important | `scripts/eval/metrics.py:283` | Dos archivos de audio distintos y textos con hashes correctos pasan la rama positiva al declarar `model_id`, `profile` y `coverage="whole_recording"`. No se verifica que sean audio válido/completo ni que la transcripción proceda realmente del descriptor/perfil indicado. Se emite `MEASURED` (`metrics.py:306`) y puede descontarse ese suelo mediante `run.py:424`. Incumple la exigencia de contenido completo y procedencia/modelo/perfil efectivamente verificados; no es simplemente la ausencia declarada de corpus real. |

**Critical: ninguno. Minor: ninguno.** Derechos reales, integración GPU, suelo ASR real, 30 canciones y escucha permanecen pendientes declarados; no los considero bugs introducidos ni aceptación conseguida. El candidato CPU requiere corregir A1–A3 antes de conformidad.