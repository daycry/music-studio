# T11 R11-07 — candidato fix2

Corrección mínima en GET de eventos: timeout de lectura permite reenganchar desde el último seq validado mientras reste deadline global. Cierra el stream anterior y descarta bytes parciales; nunca repite POST ni cambia job_id. Los errores de contrato distintos de TIMEOUT siguen fallando. No altera bindings, métricas, ACK desconocido, autenticación ni redacción.

RED funcional antes del cambio: red2.xml/receipt/stdout, socket real con pausa de 2 segundos falla con TIMEOUT. El primer GREEN prototipo tenía telemetry inválida y estado inválido: conservado, consumió accidentalmente 63.32 segundos reales; NO presentado como test acelerado válido. Después red4 vuelve a demostrar TIMEOUT y cancelación usando fixture válida contra preimagen inmutable, sin revertir producto. Otros fallos de preparación/lint permanecen guardados.

Final congelado: suite.xml/receipt/stdout, 130 pass = 48 originales + 48 fix1 + 4 nuevos + 30 vecinos. Clones idénticos byte a byte; únicamente bootstrap redirige ROOT y temporales privados. FFmpeg pretest verificado mediante ZIP/binario/version fijados existentes, sin descargar. run.py 439/483=90.890269%; metrics.py 187/190=98.421053%; cobertura oficial nueva con cero exclusiones, contrastada contra analysis2 del archivo .coverage actual. Métricas históricas quedan históricas; esta suite sí vuelve a medir metrics.py entero.

Pruebas nuevas: dos casos nativos válidos con pausa real2s (incluye fragmento UTF8 incompleto descartado/replay), terminal abierto sin esperar EOF, una expiración en 0.6 segundos reales equivalente a60 lógicos, UTF8 dividido entre chunks y límite1MiB. Viejos ocho casos native_socket preservan deadline con líneas/chunks/blancos/silencio continuo y terminal. Propiedades JUnit native_proof registran cursores, POST único, cancelación ausente en éxitos, tiempo real y escala, socket propio cerrado/thread unido, control extranjero vivo y respondiendo antes de su cierre propio. Los tres servidores de control se cierran y sus threads se unen al final de cada prueba. No certifica limpieza histórica: UNKNOWN permanece.

Custodia: source-FROZEN.json/sources-after.json y copias sources; los cuatro protegidos (metrics y tres tests canónicos) exactos antes/después. clone-source-parity.json identifica originales intactos. Ruff lint-final y format-final exit0 sobre sólo fuentes propias. Sin cambios docs/ledger/Git/benchmark/T02 ni servicios/GPU/instalación. No cierre T11, no fix R11-06, no corpus/GT/derechos/escucha acreditados. Root continúa review3 y QA.

Peso estimado2; modelo real/tokens/EUR/horasIA NULL. Historial accidental63.32s es wallclock y nunca horasIA.


**Custodia root:**130JUnitpass,6fuentes/copias y4protegidosverificados. El inventario del implementer selló la CLI todavía viva:cli-original.jsonl cambió después. El sello prematuro se conserva como inválido; root registra el hash actual únicamente trasmetadataCLIexit0. Los107artefactos noCLI son exactos. No atribuir ese sello antiguo a una CLI terminada. Revisión3/QApendientes.
