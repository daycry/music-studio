# Entradas originales para T-10

Se prepararon siete archivos de texto independientes de los audios, feedback y mapa privado de T-16. Están en `data/inputs/t10-capabilities/original-text-v1/`: letra breve en español, caption de canción, instrumental y cuatro captions para una futura preparación separada de voz, batería, bajo y guitarra. El manifiesto conserva SHA-256 y tamaño de cada archivo, con SHA-256 propio `91852a971aa785685407cff28aa2ed33826a983052ae70ca399d4370e1643b88`.

La letra se creó expresamente por el asistente para esta evaluación autorizada y lleva la declaración `assistant`. Sus etiquetas usan corchetes canónicos sin envoltura Markdown. No contiene nombres de artistas ni pide imitar a una persona real.

El caption común omite BPM y tonalidad para evitar contradicciones con los controles emparejados de 80/120 BPM y `C major`/`F# minor`. La conservación de estos textos hasta las entradas efectivas del LM y DiT deberá comprobarse en los recibos del runtime; preparar texto y SHA no demuestra obediencia musical. El presupuesto de tokens del runtime todavía no se ha validado.

**No se generó audio y no hay ground truth multipista listo.** Los cuatro captions aislados son candidatos para la preparación futura tras revisión y QA del harness. Sólo podrán constituir stems conocidos si cada audio generado contiene realmente la clase solicitada y se conserva por separado, con procedencia, configuración, PCM y SHA. La mezcla posterior usará coeficientes lineales conocidos, offsets iguales y ningún clipping o procesamiento no lineal. Una separación estimada no puede sustituir estas pistas originales.

Los archivos y el manifiesto son privados bajo `data/`; este informe no publica la letra ni acredita ninguna capacidad del modelo. TDD n/a: textos y manifiesto de procedencia, sin código de producto ni inferencia.
