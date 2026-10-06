# T-16 — revisión del arnés privado, intento 1

Fecha: 2026-10-06. Revisión independiente A+B de la preparación GPU y del paquete CPU; no reabre el producto aprobado en review-1.md/cpu-qa-report.md. El arnés está en .cache/dev-cycle/t16, declarado en Archivos y excluido de Git. Ambas lentes leyeron las fuentes completas; A se ejecutó después de B porque el despacho simultáneo fue rechazado por el límite de threads.

Scope-check contra ef66a36: exit 0, sin archivos fuera de alcance ni avisos. Selector automático sobre Git: C/D=false; no cubre los archivos ignorados. Las lentes examinaron expresamente esos archivos y no aportaron hallazgos adicionales concretos de seguridad o rendimiento.

| Criterio T-16 | A | Evidencia y límite |
|---|---|---|
| CA1/2: implementación y puertas CPU de producto | Conforme | 41 pruebas declaradas, 430 completas; cobertura añadida 93,65 %, mínimo 86,36 %, antecedentes independientes conservados |
| Alcance, preparación emparejada y autoría | Conforme CPU | Plan y bytes de control contrastados con ADR-0027; sin letras ni captions públicos |
| Baseline y cancelación dirigida | Conforme CPU | Dobles: cuatro escenarios, modelo Ollama cargado y baseline1601 rechazados; no acredita limpieza exterior |
| Preservación, linaje y escucha | Conforme en diseño; ejecución pendiente | Copias nuevas y mapa privado; defectos de ejecución en tabla inferior |
| CA3: seis audios, GPU y descarga | No verificable | Sigue abierta; ninguna carga ni generación nueva |
| CA4: paquete musical y escucha | No verificable | Sigue abierta; ninguna calidad ni ganador aprobado |
| Interop/OpenAPI | No aplica | No cambia ese alcance |

| ID | Grado | Defecto de corrección confirmado | Escenario y evidencia | Estado |
|---|---|---|---|---|
| H1 | Important | Limpieza omitida ante timeouts | run-comparison.py:116/162: docker run puede crear antes de vencer30s; docker logs puede vencer15s antes de stop/rm. Dobles B: no se ejecuta la limpieza | Pendiente |
| H2 | Important | Copia parcial de referencia no recuperable | pack-comparison.py:165/167: se escribe directamente al nombre final; reintento omite copiar y falla por hash. Doble B en memoria | Pendiente |
| H3 | Important | Falta math en el empaquetador | pack-comparison.py:38/128 importa por AST validate_listening_audio, que usa math.isfinite. Doble A: NameError con un MP3 válido; el probe del hijo no cubría esa llamada | Pendiente |
| H4 | Important | Job ajeno terminado indirectamente | run-comparison.py:140/164: supervise detecta foreign_job_detected, pero finally detiene el contenedor que lo aloja. Lectura A del recorrido completo; guardas anteriores solo cubrían DELETE | Pendiente |

A sin gaps de requisitos; sus dos hallazgos de corrección se fusionan con B. Total: cuatro Important, cero Critical/Minor; sin rebates. Se corrigen antes de GPU y de una segunda revisión fresca. Fuentes originales conservadas en caché privada; recibos CPU anteriores mantienen su valor histórico, no se actualizan para aparentar que probaban una versión posterior.

Evidencia independiente: B comprobó entorno CLI, primer ULID reservado, baseline, cancelación propia, timeouts y copia parcial mediante dobles CPU; A AST3.11 de seis scripts, dos cruces SHA de recibos, preparación/planes, guardas4/4 y diff-check0. Ninguna lente escribió archivos, instaló, ejecutó Docker real, cargó modelos ni leyó el audio original.

T-16 permanece en-progreso. Fuente de consumo estimado; horas IA, tokens y coste reales desconocidos. Jira/Confluence desactivados; journals ajenos preservados, sin promoción de conocimiento.
