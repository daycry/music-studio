# Entradas privadas preparadas para el benchmark

Cuatro fixtures de canción propias y autorizadas para 30, 60, 180 y 300 segundos. [Recibo portable](inputs-preparation-receipt.json). Texto y declaración de autoría preservados en los archivos privados del proyecto; no se publican letras, prompts ni rutas personales.

La letra y el caption son los del fragmento de 90 segundos fijado en T-16. Se conserva el mismo condicionamiento en las cuatro duraciones para medir el coste del audio solicitado sin introducir cambios de texto. Sólo cambia `duration_s`; la retirada del espacio exterior del caption reproduce exactamente la entrada efectiva de T-16. No se crean versos ni se inventa una tonalidad concreta.

Las duraciones de 180/300 segundos siguen siendo pruebas temporales con este fragmento; no representan una versión fiel de la canción completa ni una evaluación musical. La matriz mantiene sus cinco configuraciones, dos almacenamientos y cuatro repeticiones por duración. Cada ejecución posterior generará nuevos identificadores y códigos latentes, sin reutilizar jobs históricos.

Preparación offline: cero HTTP, modelos o generaciones. Los originales de T-16 quedaron intactos y se comprobaron sus hashes. Falta el freeze/revisión/QA del harness, la nueva imagen y los prerrequisitos Windows observables; no hay plan de jobs ejecutado ni números de rendimiento. TDD n/a: datos privados de evaluación y prosa.
