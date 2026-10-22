# Plan de pruebas — M3: producción, portada y vídeo con letra

| | |
|---|---|
| **Estado** | borrador |
| **Plan** | [improvement-plan.md](improvement-plan.md) |
| **URL local** | http://127.0.0.1:3000; API propia en http://127.0.0.1:8000 según Compose aislado |

Plan de pruebas incorporado por ROOT. Todos los escenarios están pendientes. E2E GWT mantiene correspondencia 1:1: el número E2E coincide con CA. Los quince CA técnicos/perceptuales restantes tienen bloque M con mismo número. El runner guarda JUnit, captura, SHA y entorno; un caso sintético conserva su etiqueta y no habilita descriptor real.

## Preparación, ejecución y límites de evidencia

- QA usa únicamente stack local privado y fuentes congeladas de fase. `. ./scripts/env.ps1` antes de uv/python; herramientas y modelos dentro del proyecto.
- Se crea canción/cohorte de prueba autorizada, jamás se borra biblioteca activa. Se comprueban ownership, ext4/UUID y guardas SHA before/after. Datos/annotations privados en eval/m3, sin secretos ni medios en Git.
- Flujo sintético puede usar seam de test privado identificado, pero no editar verified para habilitar modelo real. Repetir los flujos obligatorios por ruta real con capacidades conformes es gate separado T36–41.
- QA instala runners sólo según autorización vigente. Este plan no instala Chromium; el browser de QA tampoco se presume renderer de producto.
- E2E de integración: `pnpm --dir apps/web exec playwright test e2e/m3-*.spec.ts` en shell con expansión comprobada; runner selecciona los archivos enumerados en tasks.md. Cada bloque CA corresponde a un test nombrado, no a una sola aserción compartida.
- Medición Docker/FFmpeg y lector independiente usa scripts declarados T34–41. GPU5070/12GB, ausencia spill y unload pertenecen a pruebas reales T35–40; actas de persona permanecen obligatorias.
- APIs smoke API-xx son ofrecidas como opt-in al adoptar, no añadidas por defecto. No A11Y-xx ni instalación axe sin solicitud. Negativos API/ownership sí son parte de los escenarios.

## Automáticos (E2E — los ejecuta qa con Playwright)

### E2E-02 — CA-02

- **Objetivo**: — Dada una canción y un take autorizado, cuando se inicia producción, entonces se congela identidad, hashes, revisiones, padres, letra efectiva y derechos; cambiar luego el maestro no retargetea el trabajo.
- **Precondiciones**: — Dada una canción y un take autorizado. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se inicia producción; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Cambiar maestro/letra/preset mientras el job está pendiente; comparar captura y hashes before/after.
- **Aserciones**:
  - [ ] se congela identidad, hashes, revisiones, padres, letra efectiva y derechos; cambiar luego el maestro no retargetea el trabajo.
  - [ ] Cambiar maestro/letra/preset mientras el job está pendiente; comparar captura y hashes before/after.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-02, T-03, T-12, T-14

### E2E-03 — CA-03

- **Objetivo**: — Dada tarea/feature no verificada, cuando UI/API solicita cualquier acción M3, entonces se explica/rechaza sin carga ni envío; una prueba sintética identificada no habilita el modelo real.
- **Precondiciones**: — Dada tarea/feature no verificada. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, UI/API solicita cualquier acción M3; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Probar descriptor verified=false, feature ausente y recibo fixture; observar cero carga, encolado y transferencia.
- **Aserciones**:
  - [ ] se explica/rechaza sin carga ni envío; una prueba sintética identificada no habilita el modelo real.
  - [ ] Probar descriptor verified=false, feature ausente y recibo fixture; observar cero carga, encolado y transferencia.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-12, T-35

### E2E-04 — CA-04

- **Objetivo**: — Dado audio/imagen/letra sin declaración exigible o foto real sin consentimiento, cuando se solicita usarla, entonces se rechaza antes de encolar y no se expone contenido privado.
- **Precondiciones**: — Dado audio/imagen/letra sin declaración exigible o foto real sin consentimiento. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se solicita usarla; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Quitar declaración de letra/audio/imagen y consentimiento de foto real por separado; revisar redacción del error sin datos ajenos.
- **Aserciones**:
  - [ ] se rechaza antes de encolar y no se expone contenido privado.
  - [ ] Quitar declaración de letra/audio/imagen y consentimiento de foto real por separado; revisar redacción del error sin datos ajenos.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-06, T-12, T-23, T-27

### E2E-05 — CA-05

- **Objetivo**: — Dado upload malformado, demasiado grande/largo, hash alterado o referencia ajena, cuando se valida, entonces se rechaza por contenido/propiedad/límite sin ruta arbitraria ni conversión oculta.
- **Precondiciones**: — Dado upload malformado, demasiado grande/largo, hash alterado o referencia ajena. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se valida; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Probar formatos truncados, oversize/duración, hash cambiado y referencia de otro propietario.
- **Aserciones**:
  - [ ] se rechaza por contenido/propiedad/límite sin ruta arbitraria ni conversión oculta.
  - [ ] Probar formatos truncados, oversize/duración, hash cambiado y referencia de otro propietario.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-12, T-23, T-27

### E2E-06 — CA-06

- **Objetivo**: — Dado un take listo y separación verificada, cuando se solicitan stems, entonces se publican voz/batería/bajo/otros como assets y manifiesto ligado al take, sin take nuevo ni cambio de master/padres.
- **Precondiciones**: — Dado un take listo y separación verificada. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se solicitan stems; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Comparar take/master/padres antes/después y los cuatro roles/tasa/canales/muestras publicados.
- **Aserciones**:
  - [ ] se publican voz/batería/bajo/otros como assets y manifiesto ligado al take, sin take nuevo ni cambio de master/padres.
  - [ ] Comparar take/master/padres antes/después y los cuatro roles/tasa/canales/muestras publicados.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-14, T-15

### E2E-08 — CA-08

- **Objetivo**: — Dados stems listos, cuando se ajustan mute, solo y volumen, entonces reproducción respeta los controles, incluido silencio y combinación de solos; recargar conserva el estado guardado sin cambiar bytes de stems/master.
- **Precondiciones**: — Dados stems listos. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se ajustan mute, solo y volumen; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Probar mute+solo del mismo stem, varios solos, todos mute, ganancias0, seek/pausa y reload.
- **Aserciones**:
  - [ ] reproducción respeta los controles, incluido silencio y combinación de solos; recargar conserva el estado guardado sin cambiar bytes de stems/master.
  - [ ] Probar mute+solo del mismo stem, varios solos, todos mute, ganancias0, seek/pausa y reload.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-03, T-13, T-16

### E2E-09 — CA-09

- **Objetivo**: — Dada mezcla elegida, cuando se exporta, entonces el server produce el resultado con ganancias/selección efectivas, fuentes/hashes y mediciones; cualquier take musical nuevo es hijo con todos sus padres, nunca reemplazo.
- **Precondiciones**: — Dada mezcla elegida. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se exporta; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Cambiar selección/ganancias, exportar y verificar todos los padres/roles/recipe; conservar bytes del master.
- **Aserciones**:
  - [ ] el server produce el resultado con ganancias/selección efectivas, fuentes/hashes y mediciones; cualquier take musical nuevo es hijo con todos sus padres, nunca reemplazo.
  - [ ] Cambiar selección/ganancias, exportar y verificar todos los padres/roles/recipe; conservar bytes del master.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-17

### E2E-11 — CA-11

- **Objetivo**: — Dado destino streaming, broadcast o podcast, cuando se exporta, entonces el archivo final decodificado cumple −14/−23/−16 LUFS respectivamente con tolerancia acordada y true peak ≤−1 dBTP; formato/tasa/bits se verifican, no se deducen del comando.
- **Precondiciones**: — Dado destino streaming, broadcast o podcast. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se exporta; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Exportar los tres destinos y medir cada archivo final decodificado con medidor independiente; probar objetivo incompatible.
- **Aserciones**:
  - [ ] el archivo final decodificado cumple −14/−23/−16 LUFS respectivamente con tolerancia acordada y true peak ≤−1 dBTP; formato/tasa/bits se verifican, no se deducen del comando.
  - [ ] Exportar los tres destinos y medir cada archivo final decodificado con medidor independiente; probar objetivo incompatible.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-05, T-18, T-36

### E2E-12 — CA-12

- **Objetivo**: — Dada exportación original o ZIP stems, cuando termina, entonces original conserva sus bytes y stems WAV/FLAC48kHz conservan alineación común y amplitud sin normalizar; ZIP tiene todas las pistas declaradas/hashes válidos.
- **Precondiciones**: — Dada exportación original o ZIP stems. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, termina; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Comparar SHA original; inspeccionar todas las entradas del ZIP y medir amplitud/offset/longitud común48kHz.
- **Aserciones**:
  - [ ] original conserva sus bytes y stems WAV/FLAC48kHz conservan alineación común y amplitud sin normalizar; ZIP tiene todas las pistas declaradas/hashes válidos.
  - [ ] Comparar SHA original; inspeccionar todas las entradas del ZIP y medir amplitud/offset/longitud común48kHz.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-04, T-05, T-18, T-36

### E2E-13 — CA-13

- **Objetivo**: — Dados título/artista/año, take, portada y letra embebida solicitada, cuando se exporta, entonces un lector independiente recupera metadatos, take_id, portada y letra histórica correcta; omitir letra no la embebe.
- **Precondiciones**: — Dados título/artista/año, take, portada y letra embebida solicitada. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se exporta; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Leer el archivo con herramienta distinta del escritor; repetir con y sin letra embebida y letra vigente cambiada.
- **Aserciones**:
  - [ ] un lector independiente recupera metadatos, take_id, portada y letra histórica correcta; omitir letra no la embebe.
  - [ ] Leer el archivo con herramienta distinta del escritor; repetir con y sin letra embebida y letra vigente cambiada.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-04, T-18, T-36

### E2E-14 — CA-14

- **Objetivo**: — Dado post/export cuyo objetivo no se alcanza, cuando termina, entonces no se presenta conforme ni sustituye el original y conserva error/mediciones/procedencia del tratamiento aplicado.
- **Precondiciones**: — Dado post/export cuyo objetivo no se alcanza. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, termina; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Usar fuente cuyo loudness/TP no permite política ratificada; comprobar error y conservación de original/mediciones.
- **Aserciones**:
  - [ ] no se presenta conforme ni sustituye el original y conserva error/mediciones/procedencia del tratamiento aplicado.
  - [ ] Usar fuente cuyo loudness/TP no permite política ratificada; comprobar error y conservación de original/mediciones.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-05, T-18, T-36

### E2E-15 — CA-15

- **Objetivo**: — Dado un take recién terminado, cuando se analiza, entonces BPM/beats, tonalidad, secciones y loudness quedan ligados a sus hashes, métodos/versiones y letra aplicable, visibles y utilizables por N0.
- **Precondiciones**: — Dado un take recién terminado. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se analiza; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Comparar hashes/métodos/versiones; enlazar resultados al N0 de ese audio y no al maestro posterior.
- **Aserciones**:
  - [ ] BPM/beats, tonalidad, secciones y loudness quedan ligados a sus hashes, métodos/versiones y letra aplicable, visibles y utilizables por N0.
  - [ ] Comparar hashes/métodos/versiones; enlazar resultados al N0 de ese audio y no al maestro posterior.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-14, T-19

### E2E-16 — CA-16

- **Objetivo**: — Dado fallo parcial o audio instrumental/no analizable, cuando se consulta análisis, entonces se identifica cada resultado ausente/incierto y su motivo, sin valores sintéticos de reemplazo; no se bloquea la consulta de los resultados válidos.
- **Precondiciones**: — Dado fallo parcial o audio instrumental/no analizable. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se consulta análisis; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Simular fallo de un método y audio instrumental; otros resultados siguen consultables, sin placeholders numéricos.
- **Aserciones**:
  - [ ] se identifica cada resultado ausente/incierto y su motivo, sin valores sintéticos de reemplazo; no se bloquea la consulta de los resultados válidos.
  - [ ] Simular fallo de un método y audio instrumental; otros resultados siguen consultables, sin placeholders numéricos.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-19

### E2E-18 — CA-18

- **Objetivo**: — Dado un take con contexto textual histórico single/composite, cuando se alinea, entonces palabra/línea conserva su binding/version/hash y duración; cambiar `current_lyrics_version_id` no cambia su alineación.
- **Precondiciones**: — Dado un take con contexto textual histórico single/composite. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se alinea; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Usar take single y composite, luego cambiar current_lyrics_version_id y verificar binding invariable.
- **Aserciones**:
  - [ ] palabra/línea conserva su binding/version/hash y duración; cambiar `current_lyrics_version_id` no cambia su alineación.
  - [ ] Usar take single y composite, luego cambiar current_lyrics_version_id y verificar binding invariable.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-03, T-04, T-13, T-20, T-21

### E2E-19 — CA-19

- **Objetivo**: — Dados tiempos válidos, cuando se reproduce/se busca/pausa en karaoke y se exportan LRC/SRT, entonces líneas/palabras corresponden al audio y la revisión elegida; formatos se parsean, tiempos son ordenados/finitos y no exceden duración.
- **Precondiciones**: — Dados tiempos válidos. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se reproduce/se busca/pausa en karaoke y se exportan LRC/SRT; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Buscar al principio/medio/final, pausar/reanudar; parsear LRC/SRT y comprobar límites por revisión.
- **Aserciones**:
  - [ ] líneas/palabras corresponden al audio y la revisión elegida; formatos se parsean, tiempos son ordenados/finitos y no exceden duración.
  - [ ] Buscar al principio/medio/final, pausar/reanudar; parsear LRC/SRT y comprobar límites por revisión.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-21

### E2E-20 — CA-20

- **Objetivo**: — Dada alineación incierta, letra no cantada o región instrumental, cuando se muestra o corrige, entonces señala incertidumbre/faltantes y permite revisar tiempos por palabra/línea sin modificar el audio ni reescribir la evidencia anterior; corrección tiene revisión y origen propios.
- **Precondiciones**: — Dada alineación incierta, letra no cantada o región instrumental. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se muestra o corrige; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Repetidas/omitidas/silencio/instrumental; corregir palabra y línea, comparar Analysis/audio e historial intactos.
- **Aserciones**:
  - [ ] señala incertidumbre/faltantes y permite revisar tiempos por palabra/línea sin modificar el audio ni reescribir la evidencia anterior; corrección tiene revisión y origen propios.
  - [ ] Repetidas/omitidas/silencio/instrumental; corregir palabra y línea, comparar Analysis/audio e historial intactos.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-03, T-13, T-20, T-21

### E2E-22 — CA-22

- **Objetivo**: — Dados estilo/letra autorizados, cuando se generan portadas, entonces se ofrecen varias opciones distintas con parámetros/semillas/workflow/pins y manifiestos; elegir una actualiza portada por acción explícita.
- **Precondiciones**: — Dados estilo/letra autorizados. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se generan portadas; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Solicitar varias opciones distintas; inspeccionar seeds/pins/workflows y sólo elegir una con acción CAS explícita.
- **Aserciones**:
  - [ ] se ofrecen varias opciones distintas con parámetros/semillas/workflow/pins y manifiestos; elegir una actualiza portada por acción explícita.
  - [ ] Solicitar varias opciones distintas; inspeccionar seeds/pins/workflows y sólo elegir una con acción CAS explícita.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-11, T-14, T-22, T-23

### E2E-23 — CA-23

- **Objetivo**: — Dada portada/referencia autorizada, cuando se edita con referencia, entonces produce nueva imagen con antecedentes/hashes/derechos, conserva la anterior y no afirma coherencia de personaje M4.
- **Precondiciones**: — Dada portada/referencia autorizada. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se edita con referencia; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Editar una referencia autorizada; inspeccionar nueva imagen y conservación de su antecesora/hashes/derechos.
- **Aserciones**:
  - [ ] produce nueva imagen con antecedentes/hashes/derechos, conserva la anterior y no afirma coherencia de personaje M4.
  - [ ] Editar una referencia autorizada; inspeccionar nueva imagen y conservación de su antecesora/hashes/derechos.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-11, T-22, T-23

### E2E-24 — CA-24

- **Objetivo**: — Dada imagen subida válida con derechos/consentimiento, cuando se usa, entonces `source=upload` y su referencia/procedencia se conservan como portada o fondo N0; no requiere generación ni habilita I2V.
- **Precondiciones**: — Dada imagen subida válida con derechos/consentimiento. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se usa; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Subir imagen válida y elegir portada/fondo; source upload sin seed/modelo ni llamada de generación/I2V.
- **Aserciones**:
  - [ ] `source=upload` y su referencia/procedencia se conservan como portada o fondo N0; no requiere generación ni habilita I2V.
  - [ ] Subir imagen válida y elegir portada/fondo; source upload sin seed/modelo ni llamada de generación/I2V.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-23

### E2E-26 — CA-26

- **Objetivo**: — Dada letra revisada y portada/fondo/visualizador, cuando se previsualiza/renderiza N0, entonces tipografía cinética resalta palabras según esa revisión y referencia el take/audio efectivos; muestra incertidumbre sin ocultarla.
- **Precondiciones**: — Dada letra revisada y portada/fondo/visualizador. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se previsualiza/renderiza N0; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Seleccionar timing revision y audio mezclado distinto del master; comprobar palabra/pantalla e incertidumbre.
- **Aserciones**:
  - [ ] tipografía cinética resalta palabras según esa revisión y referencia el take/audio efectivos; muestra incertidumbre sin ocultarla.
  - [ ] Seleccionar timing revision y audio mezclado distinto del master; comprobar palabra/pantalla e incertidumbre.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-04, T-07, T-14, T-24, T-25, T-26, T-39

### E2E-27 — CA-27

- **Objetivo**: — Dado modo onda, espectro o partículas, cuando se reproduce/renderiza visualizador como fondo o vídeo propio, entonces reacciona al audio efectivo y al seek, y regiones silenciosas se distinguen de señal; no usa animación prefabricada como evidencia de reactividad.
- **Precondiciones**: — Dado modo onda, espectro o partículas. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se reproduce/renderiza visualizador como fondo o vídeo propio; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Alternar onda/espectro/partículas, señal/silencio y seek; comprobar dependencia causal de features de audio.
- **Aserciones**:
  - [ ] reacciona al audio efectivo y al seek, y regiones silenciosas se distinguen de señal; no usa animación prefabricada como evidencia de reactividad.
  - [ ] Alternar onda/espectro/partículas, señal/silencio y seek; comprobar dependencia causal de features de audio.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-07, T-24, T-25, T-26, T-39

### E2E-30 — CA-30

- **Objetivo**: — Dado tarareo/maqueta/voz propio validado, cuando se solicita referencia/acompañamiento mediante `music.complete`/`music.cover` o capacidad equivalente comprobada, entonces el server resuelve entrada y crea hijo con upload/padres/roles y derechos reales, sin identidad vocal prometida ni cambio automático de maestro.
- **Precondiciones**: — Dado tarareo/maqueta/voz propio validado. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se solicita referencia/acompañamiento mediante `music.complete`/`music.cover` o capacidad equivalente comprobada; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Tarareo/maqueta/voz autorizados, conversión explícita si necesaria y capacidad verificada; comprobar hijo y roles.
- **Aserciones**:
  - [ ] el server resuelve entrada y crea hijo con upload/padres/roles y derechos reales, sin identidad vocal prometida ni cambio automático de maestro.
  - [ ] Tarareo/maqueta/voz autorizados, conversión explícita si necesaria y capacidad verificada; comprobar hijo y roles.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-10, T-27

### E2E-32 — CA-32

- **Objetivo**: — Dado modo de calidad alta validado en M0, cuando se regenera, entonces sólo ofrece parámetros/perfil/pasos/modelo comprobados que caben con margen y publica hijo con valores efectivos; modo ausente queda deshabilitado con motivo y gate abierto.
- **Precondiciones**: — Dado modo de calidad alta validado en M0. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se regenera; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Modo verificado y otro no verificado; comprobar parámetros efectivos/margen, hijo y gate abierto del ausente.
- **Aserciones**:
  - [ ] sólo ofrece parámetros/perfil/pasos/modelo comprobados que caben con margen y publica hijo con valores efectivos; modo ausente queda deshabilitado con motivo y gate abierto.
  - [ ] Modo verificado y otro no verificado; comprobar parámetros efectivos/margen, hijo y gate abierto del ausente.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-10, T-28

### E2E-34 — CA-34

- **Objetivo**: — Dado preset con nombre, cuando se crea/edita/selecciona, entonces conserva estilo/parámetros/referencia/estilo visual autorizados; uso nuevo congela valores y refs efectivos y editar el preset no cambia trabajos/takes/renders anteriores.
- **Precondiciones**: — Dado preset con nombre. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se crea/edita/selecciona; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Crear/editar/seleccionar preset con refs; cambiarlo tras envío y verificar job/take/render previos intactos.
- **Aserciones**:
  - [ ] conserva estilo/parámetros/referencia/estilo visual autorizados; uso nuevo congela valores y refs efectivos y editar el preset no cambia trabajos/takes/renders anteriores.
  - [ ] Crear/editar/seleccionar preset con refs; cambiarlo tras envío y verificar job/take/render previos intactos.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-03, T-13, T-29

### E2E-35 — CA-35

- **Objetivo**: — Dado preset con referencia no disponible, permisos ausentes o parámetro incompatible, cuando se aplica, entonces muestra/rechaza el problema antes de envío; no omite silenciosamente referencia ni simula F-71/LoRA.
- **Precondiciones**: — Dado preset con referencia no disponible, permisos ausentes o parámetro incompatible. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se aplica; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Ref perdida, permisos ausentes e incompatible por separado; comprobar cero envío sin sustitución silenciosa.
- **Aserciones**:
  - [ ] muestra/rechaza el problema antes de envío; no omite silenciosamente referencia ni simula F-71/LoRA.
  - [ ] Ref perdida, permisos ausentes e incompatible por separado; comprobar cero envío sin sustitución silenciosa.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-29

### E2E-36 — CA-36

- **Objetivo**: — Dada canción con takes de inferencia/CPU, letras, portada, N0, valoraciones y referencias, cuando se exporta/importa en destino nuevo, entonces el cierre completo conserva historia, padres/roles, mapas, maestro, declaraciones y bytes de medios/manifiestos, con lectores de versiones compatibles.
- **Precondiciones**: — Dada canción con takes de inferencia/CPU, letras, portada, N0, valoraciones y referencias. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se exporta/importa en destino nuevo; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Roundtrip a destino nuevo, lector histórico y cierre completo CPU/inferencia; comparar bytes, linaje y reproducción.
- **Aserciones**:
  - [ ] el cierre completo conserva historia, padres/roles, mapas, maestro, declaraciones y bytes de medios/manifiestos, con lectores de versiones compatibles.
  - [ ] Roundtrip a destino nuevo, lector histórico y cierre completo CPU/inferencia; comparar bytes, linaje y reproducción.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-04, T-08, T-29, T-30, T-31, T-41

### E2E-37 — CA-37

- **Objetivo**: — Dados ZIPs con traversal absoluto/relativo, enlaces/junctions, entradas duplicadas, colisiones por normalización/case, expansión excesiva, versión desconocida, hash falso, medio ausente o vínculo ajeno, cuando se importa, entonces se rechaza sin escape ni promoción parcial. Límites de expansión explícitos se fijan antes de implementación.
- **Precondiciones**: — Dados ZIPs con traversal absoluto/relativo, enlaces/junctions, entradas duplicadas, colisiones por normalización/case, expansión excesiva, versión desconocida, hash falso, medio ausente o vínculo ajeno. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se importa; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Un caso por traversal absoluto/relativo, link/junction, duplicate, case/normalización, bomba, versión/hash/medio/owner.
- **Aserciones**:
  - [ ] se rechaza sin escape ni promoción parcial. Límites de expansión explícitos se fijan antes de implementación.
  - [ ] Un caso por traversal absoluto/relativo, link/junction, duplicate, case/normalización, bomba, versión/hash/medio/owner.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-08, T-31, T-41

### E2E-38 — CA-38

- **Objetivo**: — Dada colisión de IDs/rutas o import repetido/concurrente, cuando se valida, entonces no sobrescribe takes/manifiestos ni mezcla propietarios; política de deduplicación/remapeo explícita preserva procedencia original y no inventa inferencias del importador.
- **Precondiciones**: — Dada colisión de IDs/rutas o import repetido/concurrente. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se valida; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. IDs/rutas colisionados, import repetido y dos concurrentes; verificar no clobber y mapa source→local ratificado.
- **Aserciones**:
  - [ ] no sobrescribe takes/manifiestos ni mezcla propietarios; política de deduplicación/remapeo explícita preserva procedencia original y no inventa inferencias del importador.
  - [ ] IDs/rutas colisionados, import repetido y dos concurrentes; verificar no clobber y mapa source→local ratificado.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-04, T-08, T-31, T-41

### E2E-39 — CA-39

- **Objetivo**: — Dada canción portable, cuando se inspecciona, entonces no contiene secretos, credenciales, rutas personales absolutas, leases/PIDs o autoridad activa; las letras/fotos necesarias permanecen en payload privado autorizado, fuera de manifiestos/logs.
- **Precondiciones**: — Dada canción portable. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se inspecciona; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Inspeccionar catálogo/manifiestos/logs; credenciales/PID/leases/paths absolutos ausentes, payload privado conserva medios.
- **Aserciones**:
  - [ ] no contiene secretos, credenciales, rutas personales absolutas, leases/PIDs o autoridad activa; las letras/fotos necesarias permanecen en payload privado autorizado, fuera de manifiestos/logs.
  - [ ] Inspeccionar catálogo/manifiestos/logs; credenciales/PID/leases/paths absolutos ausentes, payload privado conserva medios.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-04, T-08, T-30, T-31, T-41

### E2E-40 — CA-40

- **Objetivo**: — Dada biblioteca con commits en WAL y medios/referencias, cuando se crea backup, entonces produce corte coherente SQLite/assets con integridad/FK/FTS, hashes, versiones/locks y catálogo verificables; copia SQLite sola o VHDX activo no se declara backup de biblioteca.
- **Precondiciones**: — Dada biblioteca con commits en WAL y medios/referencias. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se crea backup; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Crear commits WAL y assets durante preparación; mantenimiento quiesce obtiene corte coherente con FK/FTS/catalog.
- **Aserciones**:
  - [ ] produce corte coherente SQLite/assets con integridad/FK/FTS, hashes, versiones/locks y catálogo verificables; copia SQLite sola o VHDX activo no se declara backup de biblioteca.
  - [ ] Crear commits WAL y assets durante preparación; mantenimiento quiesce obtiene corte coherente con FK/FTS/catalog.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-09, T-32, T-41

### E2E-41 — CA-41

- **Objetivo**: — Dado backup íntegro, cuando se restaura a destino propio nuevo, entonces reproduce biblioteca, búsqueda, maestro, letras/linaje/presets/assets y reproducción, sin reactivar jobs/leases históricos; revisa herramientas/modelos requeridos y distingue faltantes de pérdida de contenido.
- **Precondiciones**: — Dado backup íntegro. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se restaura a destino propio nuevo; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Restore nuevo propio ext4; comprobar búsqueda, maestro, audio y jobs inertes, dependencies missing diferenciadas.
- **Aserciones**:
  - [ ] reproduce biblioteca, búsqueda, maestro, letras/linaje/presets/assets y reproducción, sin reactivar jobs/leases históricos; revisa herramientas/modelos requeridos y distingue faltantes de pérdida de contenido.
  - [ ] Restore nuevo propio ext4; comprobar búsqueda, maestro, audio y jobs inertes, dependencies missing diferenciadas.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-09, T-29, T-33, T-41

### E2E-42 — CA-42

- **Objetivo**: — Dado fallo/cancelación/disco lleno/corrupción durante backup o restore/activación, cuando se recupera, entonces conserva última copia íntegra y biblioteca anterior, no borra medios ajenos y permite rollback/reintento sin doble publicación.
- **Precondiciones**: — Dado fallo/cancelación/disco lleno/corrupción durante backup o restore/activación. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se recupera; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Fault injection por fase backup/restore/binding, cancel, disco lleno y corrupción; rollback y guardas originales.
- **Aserciones**:
  - [ ] conserva última copia íntegra y biblioteca anterior, no borra medios ajenos y permite rollback/reintento sin doble publicación.
  - [ ] Fault injection por fase backup/restore/binding, cancel, disco lleno y corrupción; rollback y guardas originales.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-09, T-32, T-33, T-41

### E2E-44 — CA-44

- **Objetivo**: — Dado job M3 cancelado, acuse perdido o reinicio en cada frontera raw/post/rename/commit/render/import/backup, cuando se reconcilia, entonces conserva petición/autoridad y terminal durable, sin regenerar éxito, duplicar resultados ni servir paquetes parciales; UNKNOWN bloquea publicación/serving/limpieza.
- **Precondiciones**: — Dado job M3 cancelado, acuse perdido o reinicio en cada frontera raw/post/rename/commit/render/import/backup. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se reconcilia; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Inyectar fallo/cancel/acuse perdido en cada frontera con hook sólo en stack privado; reiniciar y observar terminal durable.
- **Aserciones**:
  - [ ] conserva petición/autoridad y terminal durable, sin regenerar éxito, duplicar resultados ni servir paquetes parciales; UNKNOWN bloquea publicación/serving/limpieza.
  - [ ] Inyectar fallo/cancel/acuse perdido en cada frontera con hook sólo en stack privado; reiniciar y observar terminal durable.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-02, T-09, T-14, T-25, T-31, T-32, T-33, T-34

### E2E-47 — CA-47

- **Objetivo**: — Dada instalación local sin Internet/claves externas con dependencias verificadas, cuando se realizan flujos M3, entonces no hay descarga runtime ni envío externo silencioso, progreso corresponde a eventos y errores/logs/manifiestos no revelan letra literal, fotos o secretos.
- **Precondiciones**: — Dada instalación local sin Internet/claves externas con dependencias verificadas. Contratos ratificados, tareas de integración liberadas y stack propio listo. Gate real de cada capacidad antes de usarla; fixture identificado se registra aparte.
- **Pasos**:
  1. Preparar ese estado mediante API/seed privado autorizado y registrar IDs, revisión y hashes originales.
  2. En la UI, se realizan flujos M3; registrar requests/respuestas y eventos reales, incluyendo el estado terminal.
  3. Bloquear salida externa en harness de QA sin alterar servicios ajenos; comprobar flows y eventos/logs sin secretos.
- **Aserciones**:
  - [ ] no hay descarga runtime ni envío externo silencioso, progreso corresponde a eventos y errores/logs/manifiestos no revelan letra literal, fotos o secretos.
  - [ ] Bloquear salida externa en harness de QA sin alterar servicios ajenos; comprobar flows y eventos/logs sin secretos.
  - [ ] Ninguna mutación/transferencia ajena ni éxito declarado sin evidencia; guardas y historial permanecen intactos.
- **Capturas esperadas**: estado inicial, acción/formulario, resultado o error y revisión/historial; sanitizadas de letra/fotos/secretos.
- **Evidencia complementaria**: JUnit y trazas HTTP sanitizadas; métricas/recibos reales de T34–41 cuando aplica. Captura sola no acredita LUFS, hashes, ext4 o GPU.
- **Cubre tareas**: T-07, T-12, T-22, T-25, T-35

## Manuales (M — los realiza una persona con instrumentos de QA)

Los instrumentos automatizan mediciones técnicas. La persona valida contenido real, utilidad perceptual y el alcance de aceptación; ninguna lectura de prosa marca el producto conforme. Orden: contratos/seams → instrumento y artefacto candidato → acta humana → revisión fresca y QA independiente → cierre ROOT. El acta puede rechazar o dejar pendiente; no se inventa aprobación. T-42 permanece abierto hasta completar actas, matriz y QA.

### M-01 — CA-01

- **Qué revisar**: — M3 sólo se acepta con M2 cerrado y sus gates heredados cumplidos; definición técnica ADR-0037 y mocks no satisfacen ese cierre.
- **Preparación**: M2 cerrado y sus gates heredados acreditados, con verificación instrumental previa conservada; T-42 aún abierto para reconciliar la aceptación M3. contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La autenticidad del entorno, la compatibilidad histórica y la decisión de aceptación requieren inspección independiente y autoridad ROOT.
- **Criterio de aceptación**:
  - [ ] — M3 sólo se acepta con M2 cerrado y sus gates heredados cumplidos; definición técnica ADR-0037 y mocks no satisfacen ese cierre.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-01, T-42

### M-07 — CA-07

- **Qué revisar**: — La separación real acredita alineación muestra a muestra y error de suma inferior a −30 dB según métrica fijada antes de prueba, método/modelo/pins y escucha de aislamiento/artefactos; fixture no verifica calidad del separador.
- **Preparación**: contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La calidad, legibilidad, utilidad y representatividad requieren juicio sobre material real; métricas automáticas solas no lo acreditan.
- **Criterio de aceptación**:
  - [ ] — La separación real acredita alineación muestra a muestra y error de suma inferior a −30 dB según métrica fijada antes de prueba, método/modelo/pins y escucha de aislamiento/artefactos; fixture no verifica calidad del separador.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-05, T-10, T-15, T-36

### M-10 — CA-10

- **Qué revisar**: — Comparación real de reproducción y mezcla exportada comprueba sincronía, niveles, silencio, clipping y ausencia de saltos; método/tolerancia de comparación se fijan antes de validar, y escucha humana acredita utilidad.
- **Preparación**: contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La calidad, legibilidad, utilidad y representatividad requieren juicio sobre material real; métricas automáticas solas no lo acreditan.
- **Criterio de aceptación**:
  - [ ] — Comparación real de reproducción y mezcla exportada comprueba sincronía, niveles, silencio, clipping y ausencia de saltos; método/tolerancia de comparación se fijan antes de validar, y escucha humana acredita utilidad.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-05, T-16, T-17, T-36

### M-17 — CA-17

- **Qué revisar**: — Análisis real se contrasta con medición de loudness y anotaciones independientes de beats/tonalidad/secciones; criterios por método y confianza se congelan antes de prueba. Etiquetas de letra no se presentan por sí solas como secciones medidas.
- **Preparación**: contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La calidad, legibilidad, utilidad y representatividad requieren juicio sobre material real; métricas automáticas solas no lo acreditan.
- **Criterio de aceptación**:
  - [ ] — Análisis real se contrasta con medición de loudness y anotaciones independientes de beats/tonalidad/secciones; criterios por método y confianza se congelan antes de prueba. Etiquetas de letra no se presentan por sí solas como secciones medidas.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-06, T-19, T-37

### M-21 — CA-21

- **Qué revisar**: — Escucha y revisión humana sobre audio cantado real en castellano, con palabras omitidas/repetidas y silencios, acreditan alineación y utilidad karaoke; se miden errores contra anotación independiente y umbrales previamente ratificados. Parser LRC/SRT o timestamps mock no acreditan esto.
- **Preparación**: contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La calidad, legibilidad, utilidad y representatividad requieren juicio sobre material real; métricas automáticas solas no lo acreditan.
- **Criterio de aceptación**:
  - [ ] — Escucha y revisión humana sobre audio cantado real en castellano, con palabras omitidas/repetidas y silencios, acreditan alineación y utilidad karaoke; se miden errores contra anotación independiente y umbrales previamente ratificados. Parser LRC/SRT o timestamps mock no acreditan esto.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-06, T-20, T-21, T-37

### M-25 — CA-25

- **Qué revisar**: — ComfyUI headless real en Docker/CUDA acredita generación y edición por referencia, workflows/nodos/pesos seguros fijados, VRAM/RAM/tiempos y unload; revisión visual humana acredita legibilidad/calidad de opciones. PNG mock no satisface esta capacidad.
- **Preparación**: contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La calidad, legibilidad, utilidad y representatividad requieren juicio sobre material real; métricas automáticas solas no lo acreditan.
- **Criterio de aceptación**:
  - [ ] — ComfyUI headless real en Docker/CUDA acredita generación y edición por referencia, workflows/nodos/pesos seguros fijados, VRAM/RAM/tiempos y unload; revisión visual humana acredita legibilidad/calidad de opciones. PNG mock no satisface esta capacidad.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-06, T-11, T-22, T-23, T-38

### M-28 — CA-28

- **Qué revisar**: — Render/export real Docker/FFmpeg se decodifica y reproduce de principio a fin: duración, fps/resolución, audio final LUFS/true peak, sincronía sin deriva y correspondencia palabra/pantalla se miden contra referencias; se escucha/ve en navegador y reproductor independiente, sin texto cortado o ilegible.
- **Preparación**: contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La calidad, legibilidad, utilidad y representatividad requieren juicio sobre material real; métricas automáticas solas no lo acreditan.
- **Criterio de aceptación**:
  - [ ] — Render/export real Docker/FFmpeg se decodifica y reproduce de principio a fin: duración, fps/resolución, audio final LUFS/true peak, sincronía sin deriva y correspondencia palabra/pantalla se miden contra referencias; se escucha/ve en navegador y reproductor independiente, sin texto cortado o ilegible.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-06, T-07, T-25, T-26, T-39

### M-29 — CA-29

- **Qué revisar**: — Sobre canción representativa en la5070 se registra tiempo N0, carga CPU/RAM/VRAM y modo efectivo; el objetivo «en minutos», perfiles y tolerancias se fijan antes de prueba y no se cumplen con un clip fixture abreviado. No exige comprar GPU ni usar modelo que necesita16GB.
- **Preparación**: contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La calidad, legibilidad, utilidad y representatividad requieren juicio sobre material real; métricas automáticas solas no lo acreditan.
- **Criterio de aceptación**:
  - [ ] — Sobre canción representativa en la5070 se registra tiempo N0, carga CPU/RAM/VRAM y modo efectivo; el objetivo «en minutos», perfiles y tolerancias se fijan antes de prueba y no se cumplen con un clip fixture abreviado. No exige comprar GPU ni usar modelo que necesita16GB.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-06, T-07, T-25, T-26, T-39

### M-31 — CA-31

- **Qué revisar**: — F-19 se verifica por ruta real de producto y escucha sobre material autorizado: la evaluación registra reconocimiento del motivo/estructura y acompañamiento útil, artefactos y límites. Soporte nativo de task sin integración o calidad no cierra el criterio.
- **Preparación**: contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La calidad, legibilidad, utilidad y representatividad requieren juicio sobre material real; métricas automáticas solas no lo acreditan.
- **Criterio de aceptación**:
  - [ ] — F-19 se verifica por ruta real de producto y escucha sobre material autorizado: la evaluación registra reconocimiento del motivo/estructura y acompañamiento útil, artefactos y límites. Soporte nativo de task sin integración o calidad no cierra el criterio.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-06, T-10, T-27, T-40

### M-33 — CA-33

- **Qué revisar**: — Calidad alta se compara con referencia emparejada usando mismo texto/metadata efectiva, recibos y nivel de escucha igualado; pruebas reales verifican GPU/RAM/desbordamiento y escucha humana registra mejora/compromisos. Más pasos, XL o un hash no prueban mejora musical por sí solos.
- **Preparación**: contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La calidad, legibilidad, utilidad y representatividad requieren juicio sobre material real; métricas automáticas solas no lo acreditan.
- **Criterio de aceptación**:
  - [ ] — Calidad alta se compara con referencia emparejada usando mismo texto/metadata efectiva, recibos y nivel de escucha igualado; pruebas reales verifican GPU/RAM/desbordamiento y escucha humana registra mejora/compromisos. Más pasos, XL o un hash no prueban mejora musical por sí solos.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-06, T-10, T-28, T-40

### M-43 — CA-43

- **Qué revisar**: — El ejercicio de recuperación de biblioteca real usa copia/cohorte autorizada y guardas before/after de originales: restaura en destino nuevo y prueba consulta, búsqueda y reproducción real. La activación posterior exige backup restaurable y ventana exclusiva; no basta biblioteca sintética ni borrar original para demostrar recovery.
- **Preparación**: contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La calidad, legibilidad, utilidad y representatividad requieren juicio sobre material real; métricas automáticas solas no lo acreditan.
- **Criterio de aceptación**:
  - [ ] — El ejercicio de recuperación de biblioteca real usa copia/cohorte autorizada y guardas before/after de originales: restaura en destino nuevo y prueba consulta, búsqueda y reproducción real. La activación posterior exige backup restaurable y ventana exclusiva; no basta biblioteca sintética ni borrar original para demostrar recovery.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-06, T-09, T-33, T-41

### M-45 — CA-45

- **Qué revisar**: — Integración Docker persistente acredita publicación no-clobber/CAS/replay sobre raíz ext4/UUID correcta, colisiones y restart; backend/montaje incorrecto aborta. Tmpfs y mocks no acreditan almacenamiento real.
- **Preparación**: contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La autenticidad del entorno, la compatibilidad histórica y la decisión de aceptación requieren inspección independiente y autoridad ROOT.
- **Criterio de aceptación**:
  - [ ] — Integración Docker persistente acredita publicación no-clobber/CAS/replay sobre raíz ext4/UUID correcta, colisiones y restart; backend/montaje incorrecto aborta. Tmpfs y mocks no acreditan almacenamiento real.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-09, T-14, T-31, T-32, T-33, T-34, T-41

### M-46 — CA-46

- **Qué revisar**: — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos.
- **Preparación**: contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La autenticidad del entorno, la compatibilidad histórica y la decisión de aceptación requieren inspección independiente y autoridad ROOT.
- **Criterio de aceptación**:
  - [ ] — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-10, T-11, T-15, T-22, T-27, T-28, T-35, T-36, T-37, T-38, T-40

### M-48 — CA-48

- **Qué revisar**: — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura.
- **Preparación**: contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La autenticidad del entorno, la compatibilidad histórica y la decisión de aceptación requieren inspección independiente y autoridad ROOT.
- **Criterio de aceptación**:
  - [ ] — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-01, T-02, T-03, T-04, T-12, T-13, T-14, T-17, T-30, T-31, T-41

### M-49 — CA-49

- **Qué revisar**: — La aceptación registra por separado CPU/fixtures, E2E sintético, Docker/FFmpeg persistente, GPU real, experiencia de navegador/reproductor y escucha/revisión humana; ningún helper documental, porcentaje de cobertura o prueba aislada sustituye evidencia de producto pendiente.
- **Preparación**: M2 cerrado y gates heredados acreditados; matriz candidata con todas las evidencias instrumentales previas, actas y revisión/QA disponibles para inspección; T-42 aún abierto, sin exigir su propio cierre. contratos ratificados y seams técnicos liberados por ROOT; instrumento y artefacto candidato de las tareas relacionadas listos para evaluación, sin exigir su cierre. Cohorte privada real/autorizada, instrumentos congelados y referencias independientes. Registrar versión/SHA/duración/entorno antes de evaluar; tareas que requieren el acta siguen en-progreso o en-revision.
- **Pasos**:
  1. Ejecutar las Verificaciones instrumentales de las tareas relacionadas y conservar raw reports por SHA.
  2. Escuchar, ver, reproducir o inspeccionar el resultado completo según el criterio; comparar contra referencia independiente y umbral previo.
  3. Anotar muestras evaluadas, errores/artefactos/ausentes y conclusión de la persona; conservar gates abiertos si falta evidencia.
- **Por qué no se automatiza completamente**: La autenticidad del entorno, la compatibilidad histórica y la decisión de aceptación requieren inspección independiente y autoridad ROOT.
- **Criterio de aceptación**:
  - [ ] — La aceptación registra por separado CPU/fixtures, E2E sintético, Docker/FFmpeg persistente, GPU real, experiencia de navegador/reproductor y escucha/revisión humana; ningún helper documental, porcentaje de cobertura o prueba aislada sustituye evidencia de producto pendiente.
  - [ ] Acta firmada con método, referencias, umbrales previamente ratificados y enlace al resultado instrumental vigente; ausencia o fallo no se presenta como aprobado.
- **Cubre tareas**: T-06, T-42

## Cobertura (tarea → escenarios)

| Tarea | Cubierta por |
|---|---|
| T-01 | M-01, M-48 |
| T-02 | E2E-02, E2E-44, M-48 |
| T-03 | E2E-02, E2E-08, E2E-18, E2E-20, E2E-34, M-48 |
| T-04 | E2E-12, E2E-13, E2E-18, E2E-26, E2E-36, E2E-38, E2E-39, M-48 |
| T-05 | M-07, M-10, E2E-11, E2E-12, E2E-14 |
| T-06 | E2E-04, M-17, M-21, M-25, M-28, M-29, M-31, M-33, M-43, M-49 |
| T-07 | E2E-26, E2E-27, M-28, M-29, E2E-47 |
| T-08 | E2E-36, E2E-37, E2E-38, E2E-39 |
| T-09 | E2E-40, E2E-41, E2E-42, M-43, E2E-44, M-45 |
| T-10 | M-07, E2E-30, M-31, E2E-32, M-33, M-46 |
| T-11 | E2E-22, E2E-23, M-25, M-46 |
| T-12 | E2E-02, E2E-03, E2E-04, E2E-05, E2E-47, M-48 |
| T-13 | E2E-08, E2E-18, E2E-20, E2E-34, M-48 |
| T-14 | E2E-02, E2E-06, E2E-15, E2E-22, E2E-26, E2E-44, M-45, M-48 |
| T-15 | E2E-06, M-07, M-46 |
| T-16 | E2E-08, M-10 |
| T-17 | E2E-09, M-10, M-48 |
| T-18 | E2E-11, E2E-12, E2E-13, E2E-14 |
| T-19 | E2E-15, E2E-16, M-17 |
| T-20 | E2E-18, E2E-20, M-21 |
| T-21 | E2E-18, E2E-19, E2E-20, M-21 |
| T-22 | E2E-22, E2E-23, M-25, M-46, E2E-47 |
| T-23 | E2E-04, E2E-05, E2E-22, E2E-23, E2E-24, M-25 |
| T-24 | E2E-26, E2E-27 |
| T-25 | E2E-26, E2E-27, M-28, M-29, E2E-44, E2E-47 |
| T-26 | E2E-26, E2E-27, M-28, M-29 |
| T-27 | E2E-04, E2E-05, E2E-30, M-31, M-46 |
| T-28 | E2E-32, M-33, M-46 |
| T-29 | E2E-34, E2E-35, E2E-36, E2E-41 |
| T-30 | E2E-36, E2E-39, M-48 |
| T-31 | E2E-36, E2E-37, E2E-38, E2E-39, E2E-44, M-45, M-48 |
| T-32 | E2E-40, E2E-42, E2E-44, M-45 |
| T-33 | E2E-41, E2E-42, M-43, E2E-44, M-45 |
| T-34 | E2E-44, M-45 |
| T-35 | E2E-03, M-46, E2E-47 |
| T-36 | M-07, M-10, E2E-11, E2E-12, E2E-13, E2E-14, M-46 |
| T-37 | M-17, M-21, M-46 |
| T-38 | M-25, M-46 |
| T-39 | E2E-26, E2E-27, M-28, M-29 |
| T-40 | M-31, M-33, M-46 |
| T-41 | E2E-36, E2E-37, E2E-38, E2E-39, E2E-40, E2E-41, E2E-42, M-43, M-45, M-48 |
| T-42 | M-01, M-49 |



## Aprobación y adopción ROOT del plan — 2026-10-11T16:16:11.792117+00:00

El propietario delegó la implementación de todo el roadmap y la elección entre alternativas. ROOT aprueba e incorpora este plan tras revisión2 fresca A/B sin gaps y QA documental563/563. Se han verificado107payloads,50fuentes,20enlaces; ledger/coverage-check/qa-gateoficialesexit0.42tareas/11fases/49CA14funciones/34E2E15manuales permanecen íntegros. No tareas M3cerradas ni producto probado. Consumo realnull. M2actual3/30(T03purocerrado),heredados ycalidad/humano/M2hito siguenpendientes; dependencias técnicas se liberanporunidad yfinalM3requiereM2cerrado. Originales privados/revisiones/QA intactos.
