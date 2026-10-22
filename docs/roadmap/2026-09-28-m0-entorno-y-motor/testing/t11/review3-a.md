**Lente A · M0/T-11 · intento 3/3: sin nuevos defectos de conformidad identificados. R11-07 corregido por lectura estática; R11-06 Minor continúa pendiente.**

Revisados el delta y las seis fuentes completas INLINE. No ejecuté herramientas, tests ni comprobaciones de hashes. Custodia, resultados y cobertura son evidencia aportada por root.

| T-11 → criterio | Resultado y evidencia |
|---|---|
| Diez briefs y estilo/letra/tags literales | ✓ Conformidad CPU conservada: 30 posiciones, preparación vinculada y texto sin adaptación automática (`run.py:104`, `:134`, `:602`). Letras propias y declaraciones reales pendientes. |
| Tres semillas fijas por brief | ✓ Valida B-01…B-10 × 101/202/303 (`run.py:589`). |
| Ganancia lineal −16 LUFS ±0,2 / ≤−1 dBTP | ✓ Sin cambios: ganancia proporcional, medición posterior y conflicto sin derivación lista (`metrics.py:111`, `:214`). |
| Anonimización, mapa separado y best-of-3 | ✓ Conservadas las correcciones R11-01/R11-02: códigos aleatorios, grupos por brief/candidato, incompletos explícitos y reanudación estable (`run.py:687`, `:711`, `:837`). |
| Suelo WER real | ✓ Conservada la protección R11-03 contra aceptación falsa: `PENDING`, media nula y rechazo del descuento autodeclarado (`metrics.py:309`, `run.py:503`). **El criterio real sigue abierto.** |
| Hoja Markdown y campos humanos | ✓ Rúbrica, métricas separadas y selección vacía; ningún ganador automático (`run.py:784`, `:853`). |
| Staging para engine-analysis | ✓ Copia exclusiva y hash exacto en `data/tmp/<job_id>/in/audio.wav` (`metrics.py:252`). |
| R11-07: silencio legítimo dentro del plazo | ✓ El timeout breve reabre únicamente GET desde el último `seq` validado; mantiene identidad y deadline, descarta fragmentos incompletos y propaga errores distintos de `TIMEOUT` (`run.py:328–366`). El POST permanece fuera del bucle (`:313`). |
| Regresiones del streaming | ✓ Tests específicos para pausa real de 2 s, fragmento incompleto, POST único, éxito sin cancelación y expiración lógica; UTF-8 dividido y límite de buffer (`test_evaluation_stream_silence.py:26`, `:201`). Conservados los casos anteriores de deadline y terminal. |
| Alcance / Archivos | ✓ Las seis fuentes corresponden a `tasks.md:457`; scope aportado con cero archivos fuera de alcance. |
| Tests y cobertura | ✓ Evidencia actual: **130 passing**, `run.py` **439/483 = 90,89 %**, `metrics.py` **187/190 = 98,42 %**, cero exclusiones; Ruff/formato exit 0. Complementa la lectura; no acredita calidad musical. |
| Constitución | ✓ Sin nuevas infracciones explícitas identificadas. Se conservan ejecución local, confinamiento, exclusividad y bloqueo de entradas sin declaración (`CONSTITUTION.md:16`, `:19`, `:43`, `:77`). |
| Verificación de tarea cerrada | ✓ No aplica el gap de cierre sin evidencia: T-11 permanece `en-progreso` (`tasks.md:451`). Dry-run y comando completo exit 2 constan; la verificación de 30 tomas reales sigue pendiente. |
| Generados / interop | ✓ No aplica: el diff no toca `commands/`, `agents/` ni `hooks/`. |
| OpenAPI | ✓ Criterio omitido: ninguna spec OpenAPI cambia. |

| ID | Gravedad | Fichero:línea | Escenario concreto / estado |
|---|---|---|---|
| R11-06 | Minor previo, pendiente | `scripts/eval/metrics.py:219` | Normalizar 30 tomas repite 30 veces la verificación íntegra del ZIP/binario de FFmpeg y `-version`. Sin corrección ni aceptación de deuda acreditadas; hallazgo previo de lente D. |

**Nuevos gaps: 0 Critical, 0 Important, 0 Minor.** Se mantienen los veredictos favorables anteriores sin evidencia nueva que los contradiga.

La unidad CPU puede pasar a QA independiente. T-11 sigue abierta: faltan entradas y derechos reales, integración GPU/preflight, ejecución controlada del corpus y suelo ASR, 30 generaciones musicales y valoración humana. Los 120 IDs sintéticos y los probes nativos CPU no satisfacen esos criterios.