# Candidato de referencias musicales — inspección de stems

En la carpeta de trabajo con Suno facilitada por el propietario existen archivos ZIP de stems. Se inspeccionó un candidato de otro tema, separado de los audios de T-16: **S1**, 168.794.837 bytes, SHA-256 `89ada7700a6f49b7b36f08a66e5b12b7aab0dda222d6ce5c0406f42d3163f5c0`. La ruta personal y los nombres originales quedan en el recibo privado. [Recibo portable](suno-stem-candidate-inspection-receipt.json).

El ZIP contiene siete WAV etiquetados como voz principal, coros, batería, bajo, guitarra, teclado y sintetizador. Las cabeceras de los siete declaran PCM16 estéreo a 48 kHz y la misma duración: 219,6000208 segundos. Se leyeron directorio ZIP y cabeceras RIFF/fmt/data. No se extrajeron, decodificaron, reprodujeron ni usaron muestras en un modelo.

Estas pistas son candidatas para referencias de timbre y para una entrada vocal de acompañamiento, tras validar procedencia, permiso de uso, contenido, aislamiento, amplitud y recorte. Los recursos derivados deberán crearse dentro del repositorio con hashes y linaje, preservando las fuentes. Los casos T-10 que exigen WAV FLOAT necesitan una conversión explícita y documentada.

**No se aprueban como ground truth.** Los nombres y cabeceras no acreditan pistas independientes ni cómo se obtuvieron. El protocolo T-10 exige conocer la mezcla y las pistas fuente; una separación estimada no satisface ese requisito. Tampoco se ha probado aún su aislamiento o calidad musical.

La inspección cambia el siguiente paso: hay material candidato de voz e instrumentos en la carpeta autorizada, además de los MP3 finales. No cambia el motor, no adopta pesos y no sustituye el corpus original de T-10 ni la prueba musical pendiente. TDD n/a: inspección operativa y documentación.
