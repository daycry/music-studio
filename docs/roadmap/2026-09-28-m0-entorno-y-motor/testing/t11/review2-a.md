**Lente A · M0/T-11 · intento 2/3: sin nuevos defectos de conformidad identificados.** R11-01…05 presentan correcciones conformes por lectura estática. R11-06 permanece Minor pendiente. **T-11 continúa en-progreso; esta revisión no acredita aceptación integral ni QA.**

Revisadas las cinco fuentes completas y el delta INLINE. No ejecuté herramientas, tests ni verificaciones de hashes; las ejecuciones y la custodia citadas son evidencia aportada por root.

| T-11 → criterio | Resultado y evidencia |
|---|---|
| Diez briefs, estilo/letra/tags literales | ✓ Unidad CPU: conserva 30 posiciones, texto efectivo y preparación vinculada (`run.py:104`, `run.py:134`, `run.py:595`). Letras propias y declaraciones reales siguen pendientes. |
| Tres semillas fijas por brief | ✓ Valida B-01…B-10 × 101/202/303 (`run.py:582`). |
| Ganancia lineal −16 LUFS ±0,2 / ≤−1 dBTP | ✓ Ganancia única proporcional, medición posterior y conflicto sin publicación lista (`metrics.py:111`, `metrics.py:214`). Tests de proporcionalidad y conflicto en `test_evaluation_cpu.py:504`. |
| Anonimización y mapa separado — R11-01 | ✓ Códigos aleatorios sin timestamp, mapa privado y reanudación estable (`run.py:728`, `run.py:746`). Regresión específica en `test_evaluation_fix1.py:46`. |
| Best-of-3 ante fallos parciales — R11-02 | ✓ Agrupa por brief/candidato y conserva grupos previstos, incluidos vacíos e incompletos (`run.py:688`, `run.py:704`, `run.py:833`). Tests en `test_evaluation_fix1.py:62`, `:132` y `:150`. |
| Suelo WER acreditado — R11-03 | ✓ Corregida la aceptación falsa: valida PCM y devuelve `PENDING`, `mean=null`; un diccionario del llamante no autoriza descuento (`metrics.py:295`, `metrics.py:309`, `run.py:496`). Tests en `test_evaluation_fix1.py:226` y `:365`. La ejecución controlada con corpus real sigue sin implementar/acreditar. |
| Hoja Markdown y campos humanos | ✓ Rúbrica, métricas separadas, grupos incompletos y selección vacía; no ganador automático (`run.py:777`, `run.py:839`). |
| Staging para engine-analysis | ✓ Copia exclusiva a `data/tmp/<job_id>/in/audio.wav`, con hashes contrastados (`metrics.py:252`). Test en `test_evaluation_cpu.py:138`. |
| Respuestas métricas inválidas — R11-04 | ✓ Validación de estructura y números antes de operar; errores aislados por métrica (`run.py:470`, `run.py:526`, `metrics.py:335`). Tests en `test_evaluation_fix1.py:301` y `:359`. |
| Plazo durante streaming — R11-05 | ✓ Comprueba deadline por bloque y línea, limita lecturas y termina sin esperar EOF tras terminal (`run.py:210`, `run.py:238`, `run.py:340`). Pruebas socket aportadas en `test_evaluation_fix1.py:439`; reloj lógico acelerado, no 60 segundos reales. |
| Alcance / Archivos | ✓ Cinco fuentes dentro de `tasks.md:457`; scope aportado sin archivos fuera de alcance. |
| Tests y cobertura | ✓ Evidencia actual aportada: **126 passing**, `run.py` **431/478 = 90,17 %**, `metrics.py` **187/190 = 98,42 %**, cero exclusiones; Ruff/formato exit 0. Apoya la lectura, no acredita calidad musical. |
| Constitución | ✓ Sin nuevas infracciones explícitas identificadas: ejecución local, confinamiento, publicación exclusiva y bloqueo por derechos visibles; principios en `CONSTITUTION.md:16`, `:19`, `:43`, `:77`. |
| Verificación de tarea cerrada | ✓ No aplica el gap de cierre sin evidencia: T-11 está `en-progreso` (`tasks.md:451`). Dry-run y comando completo exit 2 están aportados; la verificación de 30 tomas reales continúa abierta. |
| Generados / interop | ✓ No aplica: no cambia `commands/`, `agents/` ni `hooks/`. |
| OpenAPI | ✓ Criterio omitido: ninguna spec OpenAPI cambia. |

| ID | Gravedad | Fichero:línea | Escenario concreto / estado |
|---|---|---|---|
| R11-06 | Minor, previo | `scripts/eval/metrics.py:219` | Cada normalización repite verificación del ZIP/binario y ejecución `-version`. Una batería de 30 tomas repite ese trabajo 30 veces. Permanece pendiente; ninguna corrección ni aceptación de deuda acreditada. |

**Nuevos gaps: 0 Critical, 0 Important, 0 Minor.** Se conserva el Minor previo. Derechos, integración GPU/preflight, corpus cantado y suelo ASR real, 30 generaciones musicales y escucha humana permanecen abiertos; el workflow sintético de 120 IDs no satisface esos criterios.