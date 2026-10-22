**Lente B: 4 defectos Important.** Revisión estática de las cuatro fuentes completas suministradas, incluidos ambos tests. Sin herramientas ni pruebas propias; hashes, cobertura y ejecuciones son evidencia declarada del paquete.

| Criterio | Resultado |
|---|---|
| Estilo, letra y tags literales; preparación vinculada | ✓ |
| Descriptor explícito, capacidad verificada y bloqueo GPU deliberado | ✓ |
| ACK incierto sin reenvío y cleanup no confirmado observable | ✓ |
| Ganancia lineal fija y conservación del raw ante conflicto | ✓ |
| WER bruto pendiente, CLAP limitado y ejes Audiobox separados | ✓ |
| Agrupación best-of-3 ante fallos parciales | ✗ |
| Acreditación del suelo WER positivo | ✗ |
| Aislamiento de respuestas métricas inválidas | ✗ |
| Plazo máximo durante streaming continuo | ✗ |

| Gravedad | Fichero:línea | Escenario concreto de fallo |
|---|---|---|
| Important | `scripts/eval/run.py:708` | `execute` filtra las tomas por `blind_ready` en la línea 590; `anonymize` agrupa después cada tres elementos por posición. Si una toma de B-01 falla o presenta conflicto de pico, el primer grupo mezcla las dos restantes de B-01 con una de B-02. La selección best-of-3 compara briefs diferentes. |
| Important | `scripts/eval/metrics.py:290` | `measure_floor` verifica hashes, pero no valida que `audio` sea audio ni vincula la transcripción a una ejecución acreditada del modelo/perfil y cobertura completa. Dos archivos de texto distintos como «audio», con declaraciones y hashes coherentes, producen `status="MEASURED"`. Ese resultado puede descontarse en `measure_take` si coincide el perfil declarado. El hash acredita bytes, no la procedencia ASR ni la cobertura. |
| Important | `scripts/eval/metrics.py:339` | Una salida CLAP con `score: null` provoca `TypeError` en `math.isfinite`. `measure_take` no captura ese error en `run.py:452`, ni `execute` en la línea 581. Se aborta la batería, quedan sin registrar la toma actual y el informe final, y no se ejecutan las métricas restantes. También ocurre con valores no numéricos de Audiobox. |
| Important | `scripts/eval/run.py:281` | El deadline se comprueba antes de abrir el stream, pero nunca dentro de `iter_lines()`. Un engine que envía eventos válidos continuamente, sin terminal y con intervalos inferiores al timeout de lectura, mantiene la llamada más allá de los 60 segundos. No se alcanza el timeout global ni el cleanup mientras continúa ese flujo. |

**Critical:** ninguno identificado. **Minor:** ninguno identificado.

Las letras y derechos reales ausentes, el corpus GT, la integración GPU, las 30 generaciones musicales y la escucha siguen pendientes declarados; no los contabilizo como bugs introducidos ni como aceptación cumplida. T-11 permanece **en-progreso** y la unidad CPU requiere correcciones y QA.