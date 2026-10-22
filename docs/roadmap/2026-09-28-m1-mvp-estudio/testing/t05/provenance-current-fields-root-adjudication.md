# Adjudicación raíz: campos de procedencia

La exploración sirve como mapa estático de fuentes y huecos de captura, no como prueba de valores observados en una generación real. Se verificaron inventario, copias y los siete archivos protegidos declarados por raíz. No se abrió BD, data ni modelos.

Se corrige un falso positivo del informe: el digest del receipt no está demostrado distinto del SHA de bytes. preflight.digest trata str como UTF-8 directo; adapter escribe JSON sin indentación y en una sola línea. El probe puro con acentos, emoji y saltos escapados produce el mismo SHA que hashlib.sha256(bytes). No procede cambiar producción por esa conclusión. Si una escritura futura añade saltos físicos, su semántica requerirá otra verificación.

El modelo actual es PublicationIntentRevision; AssetRevision no es una clase encontrada en el alcance. Las reservas actuales no rellenan toda CapturedProvenance: hay que fijar descriptor/Health, parent ganador y roles/declaraciones antes del envío. Los controles efectivos upstream, códigos LM y kwargs dinámicos requieren captura propia; options/catalog/latesthealth no reconstruyen observación.

La siguiente unidad propuesta es captura pre-send y roles, tras resolver el 801 y concretar contrato. No se autoriza aún ese cambio ni un canal nuevo de metadata. SQL/T05, manifest builder, worker y validación de calidad continúan pendientes. Los límites de lectura inicial, receipts por comando y ausencia de inspección de datos reales se conservan.
