# QA independiente del audio y condicionamiento de song60 /v1

**CPU_AND_ARTIFACT_QA_PASS**: 21/21 pruebas, exit0, sin gaps Important. Root cotejó 13 artefactos y el JUnit real.

Se leyeron las 5.760.000 muestras: WAV FLOAT, 48 kHz, dos canales, 60 s, finito; PCM crudo=copia y SHA idénticos. RMS −14,90318 dBFS. Una muestra fullscale, cero fuera de rango; fracción1,7361e−7, por debajo del umbral canónico0,005. No se exige clipping exactamente cero.

Style, letra etiquetada, acentos, idioma, semillas, modos y flags cotejados. LM198+310≤4096. El candidato DiT resuelto es cover por códigos LM: text94≤256 y lyrics120≤2048 coinciden con captured. Se comprobaron 16 archivos de tokenizadores, config de checkpoint y ocho fuentes contra originales y locks. Hashes de argumentos/CFG se validan como SHA64; sus preimágenes opacas no se reconstruyen.

Primera tanda20/21 conservada: el test propio esperaba request sin defaults; se corrigió usando la normalización canónica JobRequest, que añade inputs:[]. No fue un defecto del producto ni un rojo TDD de implementación. Fuentes59/protegidos32/originales15 intactos.

Sin nueva GPU, Docker, red, instalación, UI, suite de producto ni cobertura inventada. Escucha, naturalidad y obediencia musical siguen pendientes; verifiedfalse, T10 abierta. [Recibo](v1-song60-audio-qa-receipt.json).
