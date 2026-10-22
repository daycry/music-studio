# Plan de pruebas — M2: iteración creativa

| | |
|---|---|
| **Estado** | borrador |
| **Plan** | [improvement-plan.md](improvement-plan.md) |
| **Ledger** | [tasks.md](tasks.md) |
| **Spec** | [spec.md](spec.md),32 CA |
| **URL local** | http://127.0.0.1:3000; server local127.0.0.1:8000 según Compose vigente |

Los bloques E2E conservan GWT de spec mediante CA-XX. Fixtures sintéticos identificados no acreditan modelo, audio real, red WSL o VRAM. QA usa instancia Compose local propia después de liberar seams y coordinar carga T-09; no arranca nada durante planificación. Server es único writer. Evidencia privada en data/eval y .cache/dev-cycle/m2; informes versionados sanitizados no guardan letras ni rutas personales.

## Automáticos (E2E — los ejecuta qa con Playwright)

Precondiciones comunes: aplicación local propia levantada por workflow autorizado, sesión local vigente, datos sintéticos propietario A/canción/takes/listos y segundo propietario B, eventos/descriptor mock etiquetados y fixture rechazo descriptor real false. Baseline parent/master/asset/manifest hashes antes de cada operación; se comparan después. Seed/corpus/tiempos y número de jobs capturados por fixture determinista. Cada flujo positivo incluye rechazo por permiso/rights/capacidad/estado o parámetros cuando corresponde. Todos se ejecutan por teclado además del gesto que exija onda.

### E2E-01 — Modo simple: propuesta y generación explícita

- **Objetivo**: CA-02, CA-03, CA-05, CA-06, CA-25, CA-31, comportamiento GWT en instalación local; evidencia sintética de UI/API.
- **Precondiciones**: comunes; fixture dedicado del flujo con baseline hashes y eventos secuenciados, sin capacidad real habilitada por mock.
- **Pasos**:
  1. Dado el contexto y versión base capturados, abrir el flujo correspondiente.
  2. Cuando: Crear descripción española con idioma/duración; pedir propuesta y editar letra/estilo. Activar instrumental con letra previa escrita; generar explícitamente y repetir vocal sin declaración.
  3. Entonces: inspeccionar UI, requests/jobs/eventos y recargar estado persistido de la fixture.
- **Aserciones**:
  - [ ] Letra/estilo editables, cero música encolada antes del click; versión assistant con padre/autoría al aceptar.
  - [ ] Instrumental utiliza music.instrumental sin declaración, conserva texto previo; vocal sin declaración rechaza antes de job y no envía.
  - [ ] Sin Internet/clave funciona ruta sintética local; fallo LLM no llama remote.
- **Capturas esperadas**: formulario/selección, propuesta o hijo, rechazo y estado después de recargar; audio métricas/timeline cuando aplique.
- **Cubre tareas**: T-17, T-18, T-20, T-26

### E2E-02 — Cinco acciones del asistente, streaming y conflicto

- **Objetivo**: CA-04, CA-05, CA-22, CA-31, comportamiento GWT en instalación local; evidencia sintética de UI/API.
- **Precondiciones**: comunes; fixture dedicado del flujo con baseline hashes y eventos secuenciados, sin capacidad real habilitada por mock.
- **Pasos**:
  1. Dado el contexto y versión base capturados, abrir el flujo correspondiente.
  2. Cuando: Parametrizar generar/reescribir sección/continuar/cambiar tono/estructura sobre letra versionada. Reescribir solo sección; aceptar con rev, después provocar edición concurrente. Producir tags inválidos, cancelar y desconectar/reconectar SSE.
  3. Entonces: inspeccionar UI, requests/jobs/eventos y recargar estado persistido de la fixture.
- **Aserciones**:
  - [ ] Tags válidos por casos compartidos, texto exterior intacto, histórico/source assistant preservado.
  - [ ] 409 no pisa nueva versión; invalid/truncated terminal preserva original.
  - [ ] Deltas ordenados y un terminal; desconexión no cancela y cancelación no genera música.
- **Capturas esperadas**: formulario/selección, propuesta o hijo, rechazo y estado después de recargar; audio métricas/timeline cuando aplique.
- **Cubre tareas**: T-15, T-18, T-20, T-26

### E2E-03 — Dos vías de variación

- **Objetivo**: CA-06, CA-07, CA-08, CA-16, CA-20, CA-31, comportamiento GWT en instalación local; evidencia sintética de UI/API.
- **Precondiciones**: comunes; fixture dedicado del flujo con baseline hashes y eventos secuenciados, sin capacidad real habilitada por mock.
- **Pasos**:
  1. Dado el contexto y versión base capturados, abrir el flujo correspondiente.
  2. Cuando: Seleccionar petición efectiva previa; cambiar letra/style actual song y pedir nueva seed. Después usar variación audio source con descriptor mock retake; repetir real verified=false y take ajeno/borrado.
  3. Entonces: inspeccionar UI, requests/jobs/eventos y recargar estado persistido de la fixture.
- **Aserciones**:
  - [ ] Nueva seed efectiva y resto de petición/letra histórica conservados, hijo variant distinto.
  - [ ] retake tiene input master/hash elegido; no usa simple repetición de seed como sustituto.
  - [ ] Padre/master/hash no cambian; sin derechos o cap real false no encola/envía.
- **Capturas esperadas**: formulario/selección, propuesta o hijo, rechazo y estado después de recargar; audio métricas/timeline cuando aplique.
- **Cubre tareas**: T-02, T-06, T-10, T-11, T-21, T-26

### E2E-04 — Extensión final/punto y mapa

- **Objetivo**: CA-09, CA-13, CA-16, CA-20, CA-31, comportamiento GWT en instalación local; evidencia sintética de UI/API.
- **Precondiciones**: comunes; fixture dedicado del flujo con baseline hashes y eventos secuenciados, sin capacidad real habilitada por mock.
- **Pasos**:
  1. Dado el contexto y versión base capturados, abrir el flujo correspondiente.
  2. Cuando: Parametrizar desde final y punto interior; fijar letra/style continuación. Fixture adapter entrega región o salida completa. Negativos punto NaN/negativo/fuera y descriptor false.
  3. Entonces: inspeccionar UI, requests/jobs/eventos y recargar estado persistido de la fixture.
- **Aserciones**:
  - [ ] Hijo extend/maps derivan de construcción medida y parámetros capturados; sin duplicación al entregar pieza completa.
  - [ ] Punto inválido bloquea UI/server antes job; zero/limits según descriptor.
  - [ ] Padre/maestro intactos y false no envío.
- **Capturas esperadas**: formulario/selección, propuesta o hijo, rechazo y estado después de recargar; audio métricas/timeline cuando aplique.
- **Cubre tareas**: T-02, T-03, T-06, T-12, T-21, T-26

### E2E-05 — Selección, imán y repaint

- **Objetivo**: CA-10, CA-11, CA-13, CA-16, CA-20, CA-31, comportamiento GWT en instalación local; evidencia sintética de UI/API.
- **Precondiciones**: comunes; fixture dedicado del flujo con baseline hashes y eventos secuenciados, sin capacidad real habilitada por mock.
- **Pasos**:
  1. Dado el contexto y versión base capturados, abrir el flujo correspondiente.
  2. Cuando: Seleccionar [t0,t1] por teclado/arrastre, activar loop e imán beats en fixture real identificado. Con y sin boundaries de secciones. Regenerar con letra/style; repetir intervalos vacío/NaN/negativo/fuera y feature false.
  3. Entonces: inspeccionar UI, requests/jobs/eventos y recargar estado persistido de la fixture.
- **Aserciones**:
  - [ ] Selecciona/ajusta y loop respeta límites; imán sections solo con datos reales, no estructura inventada.
  - [ ] Hijo repaint conserva mapa keep/regenerate y captura efectiva; no muta padre/maestro.
  - [ ] Negativos UI y server no encolan; false deshabilitado y rechazo.
- **Capturas esperadas**: formulario/selección, propuesta o hijo, rechazo y estado después de recargar; audio métricas/timeline cuando aplique.
- **Cubre tareas**: T-02, T-03, T-06, T-13, T-21, T-26

### E2E-06 — Cover y fidelidad por feature

- **Objetivo**: CA-12, CA-13, CA-16, CA-20, CA-31, comportamiento GWT en instalación local; evidencia sintética de UI/API.
- **Precondiciones**: comunes; fixture dedicado del flujo con baseline hashes y eventos secuenciados, sin capacidad real habilitada por mock.
- **Pasos**:
  1. Dado el contexto y versión base capturados, abrir el flujo correspondiente.
  2. Cuando: Seleccionar take+style cover. Parametrizar fidelity verificada schema/ausente/false; source ajeno o no listo, capability false real.
  3. Entonces: inspeccionar UI, requests/jobs/eventos y recargar estado persistido de la fixture.
- **Aserciones**:
  - [ ] Hijo cover distinto con origen/style/linaje correctos.
  - [ ] Control fidelity solo permitido por schema/feature; ausencia no crea escala ficticia.
  - [ ] No envío ante rights/source/cap inválidos y maestro/padre intactos.
- **Capturas esperadas**: formulario/selección, propuesta o hijo, rechazo y estado después de recargar; audio métricas/timeline cuando aplique.
- **Cubre tareas**: T-06, T-14, T-21, T-26

### E2E-07 — Ediciones CPU y crossfade

- **Objetivo**: CA-13, CA-14, CA-15, CA-16, CA-29, CA-31, comportamiento GWT en instalación local; evidencia sintética de UI/API.
- **Precondiciones**: comunes; fixture dedicado del flujo con baseline hashes y eventos secuenciados, sin capacidad real habilitada por mock.
- **Pasos**:
  1. Dado el contexto y versión base capturados, abrir el flujo correspondiente.
  2. Cuando: Recortar, fade-in/out, crossfade dos takes misma canción. Parametrizar formatos mixtos y duraciones límite. Probar segundo take ajeno, longitud0/NaN/excesiva y clipping del fixture.
  3. Entonces: inspeccionar UI, requests/jobs/eventos y recargar estado persistido de la fixture.
- **Aserciones**:
  - [ ] Nuevo edit con duración/mapas medidos y crossfade ambos roles/parents/root canónica.
  - [ ] Operación CPU no carga modelo; tools provenance y manifest nuevo/hash sin CPU inference falsa.
  - [ ] Inválidos no job/ready parcial ni overwrite; clipping visible, padres/master inmutables.
- **Capturas esperadas**: formulario/selección, propuesta o hijo, rechazo y estado después de recargar; audio métricas/timeline cuando aplique.
- **Cubre tareas**: T-02, T-03, T-07, T-08, T-22, T-26

### E2E-08 — DAG de versiones, audio y maestro explícito

- **Objetivo**: CA-16, CA-17, CA-29, CA-31, comportamiento GWT en instalación local; evidencia sintética de UI/API.
- **Precondiciones**: comunes; fixture dedicado del flujo con baseline hashes y eventos secuenciados, sin capacidad real habilitada por mock.
- **Pasos**:
  1. Dado el contexto y versión base capturados, abrir el flujo correspondiente.
  2. Cuando: Abrir canción con originales/variant/extend/repaint/cover/edit y crossfade multipadre. Navegar todos nodos por teclado, inspeccionar procedencia, recargar; elegir maestro explícitamente y rechazar nodo ajeno.
  3. Entonces: inspeccionar UI, requests/jobs/eventos y recargar estado persistido de la fixture.
- **Aserciones**:
  - [ ] Aristas/operación/ambos padres/maestro representan datos reales; recarga mismo DAG.
  - [ ] Seleccionar nodo reproduce audio autorizado sin promoverlo; click maestro es única promoción.
  - [ ] CPU tools y antecedentes separados; sin private paths/secretos ni modelo ficticio.
- **Capturas esperadas**: formulario/selección, propuesta o hijo, rechazo y estado después de recargar; audio métricas/timeline cuando aplique.
- **Cubre tareas**: T-05, T-23, T-26

### E2E-09 — Comparación A/B y límites

- **Objetivo**: CA-18, CA-19, CA-29, CA-30, CA-31, comportamiento GWT en instalación local; evidencia sintética de UI/API.
- **Precondiciones**: comunes; fixture dedicado del flujo con baseline hashes y eventos secuenciados, sin capacidad real habilitada por mock.
- **Pasos**:
  1. Dado el contexto y versión base capturados, abrir el flujo correspondiente.
  2. Cuando: Abrir par distinto loudness, esperar previews precargadas/medidas; alternar y seek en ventana común, llegar al final. Audio silence/<3s/no finite, decoder incompatible, preview partial y origen borrado/hash cambiado.
  3. Entonces: inspeccionar UI, requests/jobs/eventos y recargar estado persistido de la fixture.
- **Aserciones**:
  - [ ] Solo un audible y tiempo absoluto en ventana común, stop al final; métricas correspondientes audio servido.
  - [ ] Master/manifest hashes intactos; error de medición muestra escucha ordinaria y motivo sin igualación engañosa.
  - [ ] No servir parcial/ajeno/cache obsoleta; thresholds técnicos se comprueban con instrumento real T-29/M-02, mock no acredita calidad.
- **Capturas esperadas**: formulario/selección, propuesta o hijo, rechazo y estado después de recargar; audio métricas/timeline cuando aplique.
- **Cubre tareas**: T-09, T-24, T-26

### E2E-10 — Providers off, configuración por función y preflight

- **Objetivo**: CA-25, CA-26, CA-27, CA-28, CA-31, comportamiento GWT en instalación local; evidencia sintética de UI/API.
- **Precondiciones**: comunes; fixture dedicado del flujo con baseline hashes y eventos secuenciados, sin capacidad real habilitada por mock.
- **Pasos**:
  1. Dado el contexto y versión base capturados, abrir el flujo correspondiente.
  2. Cuando: Ajustes sin adapter/key/red: leer motivos. Con adapter sintético explícitamente marcado, activar una función; probar key ausente/verified=false/cost unknown, confirmación coste/petición y desactivar. Simular fallo local.
  3. Entonces: inspeccionar UI, requests/jobs/eventos y recargar estado persistido de la fixture.
- **Aserciones**:
  - [ ] Off por fábrica, sin API musical; cambiar función no habilita otras.
  - [ ] Sin enabled+verified+key+estimación fiable+confirmación no envía; synthetic remote registra provider/model/request_id/coste.
  - [ ] Nunca secrets en DOM/URLs/eventos/logs/config/manifest y no fallback local→remote. No llamada API real en esta prueba.
- **Capturas esperadas**: formulario/selección, propuesta o hijo, rechazo y estado después de recargar; audio métricas/timeline cuando aplique.
- **Cubre tareas**: T-19, T-25, T-26

### E2E-11 — Cancelación, recovery, permisos y temporales

- **Objetivo**: CA-22, CA-29, CA-30, CA-31, comportamiento GWT en instalación local; evidencia sintética de UI/API.
- **Precondiciones**: comunes; fixture dedicado del flujo con baseline hashes y eventos secuenciados, sin capacidad real habilitada por mock.
- **Pasos**:
  1. Dado el contexto y versión base capturados, abrir el flujo correspondiente.
  2. Cuando: Parametrizar todos flujos texto/derivación/edit/AB. Cancelar en queued/running/post; fixture reinicia durante publicación y replay. Abrir preview con lector activo y solicitar cleanup. Provocar UNKNOWN.
  3. Entonces: inspeccionar UI, requests/jobs/eventos y recargar estado persistido de la fixture.
- **Aserciones**:
  - [ ] Un terminal secuenciado, error durable, ningún ready parcial ni publicación repetida; conserva parents/master.
  - [ ] Retry respeta M1 y no reinfiere resultado publicado; cleanup solo propios sin lectores/custodia UNKNOWN.
  - [ ] Revalidación rights/owner/hash rechaza acceso. Crash/replay sintético se complementa con M-05 persistente.
- **Capturas esperadas**: formulario/selección, propuesta o hijo, rechazo y estado después de recargar; audio métricas/timeline cuando aplique.
- **Cubre tareas**: T-07, T-09, T-16, T-17, T-18, T-20, T-22, T-23, T-24, T-26

### E2E-12 — Gates honestos y validaciones server adversas

- **Objetivo**: CA-06, CA-13, CA-20, CA-25, CA-28, CA-31, CA-32, comportamiento GWT en instalación local; evidencia sintética de UI/API.
- **Precondiciones**: comunes; fixture dedicado del flujo con baseline hashes y eventos secuenciados, sin capacidad real habilitada por mock.
- **Pasos**:
  1. Dado el contexto y versión base capturados, abrir el flujo correspondiente.
  2. Cuando: Parametrizar cada operación real false y mock true sintético claramente etiquetado. Invocar API saltando UI con NaN/Infinity/out-of-range/rights missing/source ajeno/cost unknown. Revisar estado/foco y progreso.
  3. Entonces: inspeccionar UI, requests/jobs/eventos y recargar estado persistido de la fixture.
- **Aserciones**:
  - [ ] Real sigue deshabilitado/rechaza no envío aunque mock true; ningún progreso por timers.
  - [ ] Validación server preserva estado y no revela datos privados; UI error localizable/keyboard/foco/anuncios.
  - [ ] Contratos regenerate y gates de QA documentados en M-08, no afirmados por escenario.
- **Capturas esperadas**: formulario/selección, propuesta o hijo, rechazo y estado después de recargar; audio métricas/timeline cuando aplique.
- **Cubre tareas**: T-04, T-06, T-11, T-12, T-13, T-14, T-19, T-21, T-25, T-26

## Manuales (M — los realiza una persona)

Los instrumentos técnicos pueden producir recibos automáticamente; la escucha, la calidad y la aceptación no se marcan sin persona. Realizadas después de la ventana propia autorizada por root, respetando Ollama/T-09 y restauración de recursos.

### M-01 — Edición y fidelidad real de las uniones

- **Qué revisar**: CA-14, CA-15, CA-16, CA-29. Medir trims/fades/crossfade en masters propios antes/después y escuchar uniones en cascos. Revisar ambas aristas, mapas/raíz y conversión de formatos.
- **Por qué no se automatiza**: juicio humano, integración real o revisión de evidencia completa; mocks no prueban esta frontera.
- **Criterio de aceptación**:
  - [ ] Keep alineado≤1LSB PCM24; convert referencia≤2LSB y etiqueta; duración±1 muestra, clipping rechazo truepeak>−1dBTP.
  - [ ] Hash masters/manifests padres exacto; crossfade roles/maps ambos, ninguna carga GPU ni identidad inference falsa.
  - [ ] Escucha confirma fade/unión útil sin clicks audibles; si falla no cerrar.
- **Cubre tareas**: T-08, T-22, T-29

### M-02 — Igualación A/B, decoder y transporte real

- **Qué revisar**: CA-18, CA-19. Usar audio propio/controlado con contraste de niveles/transitorios, silencio/corto y sample rates distintos. Medir salida realmente servida con FFmpeg fijado, decoder Chromium, ganancia, truepeak y transport. Escuchar utilidad sin conocer selección cuando sea viable.
- **Por qué no se automatiza**: juicio humano, integración real o revisión de evidencia completa; mocks no prueban esta frontera.
- **Criterio de aceptación**:
  - [ ] ≤0,5LU y≤−1dBTP; ganancia≤0 sin limitación independiente; no usar MP3 listen ni cambios de masters.
  - [ ] Silencio/<3s/nonfinite deshabilita igualdad;3 renders máximo y fallo explícito, cache no parcial.
  - [ ] Medir drift≤50ms/alternancia≤150ms tras preload conforme política previa confirmada; ausencia clicks/pausas juzgada humana. Sin equivalencia musical de estructuras distintas.
- **Cubre tareas**: T-09, T-24, T-29

### M-03 — Cuatro capacidades musicales y30 generaciones propias

- **Qué revisar**: CA-01, CA-07, CA-08, CA-09, CA-11, CA-12, CA-20, CA-21. Después de liberar T-09 y elegir modelo M0, generar/escuchar retake, extend final+punto, repaint y cover por separado. Identificar inputs/versions/seeds/rights/terminales/mapas; registrar30 generaciones propias reales M1 y prueba de cierre M1/M0T13.
- **Por qué no se automatiza**: juicio humano, integración real o revisión de evidencia completa; mocks no prueban esta frontera.
- **Criterio de aceptación**:
  - [ ] Conformidad individual, continuidad extend/repaint y fidelidad estilística cover revisadas; no prometer obediencia perfecta.
  - [ ] Cada feature verificada solo tras prueba; una false mantiene M2 abierto, mock no30.
  - [ ] M1 cerrado, M0/T-13 y aceptación humana documentados antes de T-30.
- **Cubre tareas**: T-10, T-11, T-12, T-13, T-14, T-21, T-27, T-30

### M-04 — LLM elegido y Ollama compartido real

- **Qué revisar**: CA-04, CA-22, CA-23, CA-24, CA-25. Probar cinco acciones con corpus definido T-28, latencia/idioma/tag fidelity y licencia/hash propios. Conectar adapter Docker a WSL privado sin LAN; cancelar/replay. Probar residente inicial vacío/ajeno, cambio LLM→música→LLM, recarga tercero y restart recovery de recibo.
- **Por qué no se automatiza**: juicio humano, integración real o revisión de evidencia completa; mocks no prueban esta frontera.
- **Criterio de aceptación**:
  - [ ] Hash/revisión/licencia y formato runtime propios seguros;100% tags corpus, sección exterior intacta y calidad humana aceptada.
  - [ ] Ausencia unload y VRAM observadas sin dos residentes; restaurar solo realmente descargados por own execution; vacío queda vacío.
  - [ ] No global mutex/stop Ollama/delete model/modelstore externo/descarga runtime/cloud; errores y UNKNOWN honestos; prueba real con recibos, no mocks.
- **Cubre tareas**: T-15, T-16, T-17, T-28, T-30

### M-05 — Custodia, manifiestos y replay persistente real

- **Qué revisar**: CA-16, CA-29, CA-30. Sobre ext4/VHDX aceptado M1, recoger UUID/toolpins/manifest/hashes before; inducir cortes propios durante render/rename/commit y recuperar. Incluir cleanup con lectores, rev cambiado y CPU/existing engine receipt.
- **Por qué no se automatiza**: juicio humano, integración real o revisión de evidencia completa; mocks no prueban esta frontera.
- **Criterio de aceptación**:
  - [ ] No ready parcial, duplicate/overwrite de padres, CAS/no-clobber y CLOSED_CONFIRMED; UNKNOWN bloquea limpiar/publicar.
  - [ ] Manifest nuevo inmutable por cada resultado y preview job sujeto autorizado; derechos/commercial_use combinados.
  - [ ] Baseline historical M1 sigue legible, restore válido; tmpfs solo diagnóstico no evidencia persistente.
- **Cubre tareas**: T-07, T-08, T-28, T-29, T-30

### M-06 — Provider opcional: revisión de privacidad y coste

- **Qué revisar**: CA-25, CA-26, CA-27, CA-28. Revisar registry off/por función, key estado sanitized, request estimate/confirm y fallos sin fallback. No hay proveedor concreto seleccionado; si se integra uno autorizado, añadir licencia/version/cost source y recibo real antes de verified.
- **Por qué no se automatiza**: juicio humano, integración real o revisión de evidencia completa; mocks no prueban esta frontera.
- **Criterio de aceptación**:
  - [ ] Sin adapter real queda unavailable/off con motivo y no envío, música siempre local.
  - [ ] Key únicamente env server; logs/browser/engines/DB/config/manifests sin secretos.
  - [ ] CA27 llamada real condicional: marcar rama n/a por adapter real ausente; no fingir receipt sintético real ni exigir contratar API para aceptar M2 local.
- **Cubre tareas**: T-19, T-25

### M-07 — Teclado, castellano, foco y utilidad

- **Qué revisar**: CA-02, CA-04, CA-10, CA-17, CA-18, CA-26, CA-31. Completar cada flujo nuevo solo teclado, revisar foco visible/orden/anuncios y next-intl; evaluar lectura del DAG multipadre, claridad cover musical vs portada y comparación.
- **Por qué no se automatiza**: juicio humano, integración real o revisión de evidencia completa; mocks no prueban esta frontera.
- **Criterio de aceptación**:
  - [ ] UI castellano completo sin strings hardcoded, tabs/dialogs/forms operables y estados reales anunciados.
  - [ ] Errores accesibles conservan texto/audio y gates visibles; sin identidad Suno copiada.
  - [ ] Juicio visual/escucha útil aceptado por persona, no declaración de QA automático.
- **Cubre tareas**: T-20, T-21, T-22, T-23, T-24, T-25, T-30

### M-08 — Puertas de calidad, compatibilidad y cierre

- **Qué revisar**: CA-29, CA-31, CA-32. Revisar ledger/terminales, RED antes código/reviews fresh A/B+C/D según auto, QA/cobertura≥80 por fase; OpenAPI diff/regeneration/TS/schema copias y ADR CPU. Revisar matriz completa32CA.
- **Por qué no se automatiza**: juicio humano, integración real o revisión de evidencia completa; mocks no prueban esta frontera.
- **Criterio de aceptación**:
  - [ ] ledger-lint/coverage-check exit0 y links existentes; cada Verificación ejecutada con resultado/hash propio.
  - [ ] OpenAPI server v2 aditivo (cuatro operaciones), DTO M1 intacto y rechazo explícito CPU después de autorización/antes de efectos; engine /v1 opcional. Inferencia v1 intacta, CPU/previews v2 y song v2 mixto con lectores por versión. Excepción SQL limitada ADR-0074 con backup/restauración, WAL, FK/triggers, rollback y downgrade seguro probados antes de aceptación.
  - [ ] No hito completado con requisito real pendiente; consumo unknown no se anuncia medido.
- **Cubre tareas**: T-01, T-04, T-26, T-30

## Cobertura (tarea → escenarios)

| Tarea | Cubierta por |
|---|---|
| T-01 | M-08 |
| T-02 | E2E-03, E2E-04, E2E-05, E2E-07 |
| T-03 | E2E-04, E2E-05, E2E-07 |
| T-04 | E2E-12, M-08 |
| T-05 | E2E-08, M-08 |
| T-06 | E2E-03, E2E-04, E2E-05, E2E-06, E2E-12 |
| T-07 | E2E-07, E2E-11, M-05, M-08 |
| T-08 | E2E-07, M-01, M-05 |
| T-09 | E2E-09, E2E-11, M-02, M-05 |
| T-10 | E2E-03, M-03 |
| T-11 | E2E-03, E2E-12, M-03 |
| T-12 | E2E-04, E2E-12, M-03 |
| T-13 | E2E-05, E2E-12, M-03 |
| T-14 | E2E-06, E2E-12, M-03 |
| T-15 | E2E-02, M-04, M-08 |
| T-16 | E2E-11, M-04 |
| T-17 | E2E-01, E2E-11, M-04 |
| T-18 | E2E-01, E2E-02, E2E-11 |
| T-19 | E2E-10, E2E-12, M-06 |
| T-20 | E2E-01, E2E-02, E2E-11, M-07 |
| T-21 | E2E-03, E2E-04, E2E-05, E2E-06, E2E-12, M-03, M-07 |
| T-22 | E2E-07, E2E-11, M-01, M-07 |
| T-23 | E2E-08, E2E-11, M-07 |
| T-24 | E2E-09, E2E-11, M-02, M-07 |
| T-25 | E2E-10, E2E-12, M-06, M-07 |
| T-26 | E2E-01, E2E-02, E2E-03, E2E-04, E2E-05, E2E-06, E2E-07, E2E-08, E2E-09, E2E-10, E2E-11, E2E-12, M-08 |
| T-27 | M-03, M-05 |
| T-28 | M-04, M-05 |
| T-29 | M-01, M-02, M-05 |
| T-30 | M-03, M-04, M-05, M-07, M-08 |

## Matriz de aceptación completa (CA → tarea/evidencia)

| CA | Tareas | Escenarios | Evidencia exigida |
|---|---|---|---|
| CA-01 | T-30 | M-03 | Real + recibos propios + aceptación humana; no sustituible por mock |
| CA-02 | T-18, T-20 | E2E-01, M-07 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-03 | T-18, T-20 | E2E-01 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-04 | T-18, T-20, T-28 | E2E-02, M-04, M-07 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-05 | T-18, T-20 | E2E-01, E2E-02 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-06 | T-06, T-10, T-18, T-20 | E2E-01, E2E-03, E2E-12 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-07 | T-02, T-10, T-21, T-27 | E2E-03, M-03 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-08 | T-11, T-21, T-27 | E2E-03, M-03 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-09 | T-02, T-03, T-12, T-21, T-27 | E2E-04, M-03 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-10 | T-21 | E2E-05, M-07 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-11 | T-02, T-03, T-13, T-21, T-27 | E2E-05, M-03 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-12 | T-14, T-21, T-27 | E2E-06, M-03 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-13 | T-03, T-06, T-08, T-12, T-13, T-21, T-22 | E2E-04, E2E-05, E2E-06, E2E-07, E2E-12 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-14 | T-03, T-08, T-22, T-29 | E2E-07, M-01 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-15 | T-02, T-03, T-08, T-22, T-29 | E2E-07, M-01 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-16 | T-05, T-06, T-07, T-08, T-10, T-11, T-12, T-13, T-14, T-22, T-23, T-29 | E2E-03, E2E-04, E2E-05, E2E-06, E2E-07, E2E-08, M-01, M-05 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-17 | T-05, T-23 | E2E-08, M-07 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-18 | T-09, T-24, T-29 | E2E-09, M-02, M-07 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-19 | T-09, T-24, T-29 | E2E-09, M-02 | Real + recibos propios + aceptación humana; no sustituible por mock |
| CA-20 | T-04, T-06, T-11, T-12, T-13, T-14, T-21, T-26, T-27 | E2E-03, E2E-04, E2E-05, E2E-06, E2E-12, M-03 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-21 | T-11, T-12, T-13, T-14, T-27, T-30 | M-03 | Real + recibos propios + aceptación humana; no sustituible por mock |
| CA-22 | T-15, T-18, T-20, T-28 | E2E-02, E2E-11, M-04 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-23 | T-15, T-17, T-28, T-30 | M-04 | Real + recibos propios + aceptación humana; no sustituible por mock |
| CA-24 | T-16, T-17, T-28, T-30 | M-04 | Real + recibos propios + aceptación humana; no sustituible por mock |
| CA-25 | T-17, T-18, T-19, T-25, T-26, T-28 | E2E-01, E2E-10, E2E-12, M-04, M-06 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-26 | T-19, T-25 | E2E-10, M-06, M-07 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-27 | T-19, T-25 | E2E-10, M-06 | Contrato sintético + rama real condicional solo si provider autorizado/verificado |
| CA-28 | T-19, T-25, T-26 | E2E-10, E2E-12, M-06 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-29 | T-01, T-02, T-04, T-05, T-07, T-08, T-09, T-15, T-19, T-23, T-26, T-27, T-28, T-29, T-30 | E2E-07, E2E-08, E2E-09, E2E-11, M-01, M-05, M-08 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-30 | T-06, T-07, T-09, T-16, T-24, T-26, T-29 | E2E-09, E2E-11, M-05 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-31 | T-20, T-21, T-22, T-23, T-24, T-25, T-26, T-30 | E2E-01, E2E-02, E2E-03, E2E-04, E2E-05, E2E-06, E2E-07, E2E-08, E2E-09, E2E-10, E2E-11, E2E-12, M-07, M-08 | Pruebas focales/E2E y recibos; manual cuando indicado |
| CA-32 | T-01, T-04, T-26, T-30 | E2E-12, M-08 | Pruebas focales/E2E y recibos; manual cuando indicado |

## Método y tolerancias antes de RED

- CPU render y A/B usan FFmpeg fijado del proyecto, medición ebur128/true peak mediante measure_audio, hash de bytes/PCM y pins guardados. No LLM/GPU para editar. Fixtures auditables seno/transitorios/ruido/silencio, duración≥3s para LUFS y múltiples sample rates/channels. Audio propio de escucha complementa las señales controladas.
- Índices round-half-up y ventanas semiabiertas; duration medida±1 sample. Keep alineado misma rate/channels error≤1LSB PCM24, sin identidad binaria prometida. Conversión marcada convert y contra referencia FFmpeg/soxr fijada error≤2LSB; no declara equivalencia perceptual exacta. Prueba stereo↔mono explícita; no cambia formato bajo keep.
- Crossfade lineal complementario, duración positiva dentro ambos padres. Medir true peak después conversion; >−1dBTP rechaza con motivo, no normaliza ni altera padre para pasar.
- A/B desde masters: objetivo min(LA,LB,LA+C−PA,LB+C−PB),C=−1dBTP; gain≤0 sin limitación. WAV PCM24 decoder comprobado antes entrega; sin formato sin pérdida compatible, comparison unavailable hasta resolver contrato. Re-medición real servido ≤0,5LU/≤−1dBTP,3 renders máximo disminuyendo mismo target; silencio/<3s/nonfinite no igualdad automática.
- Tiempo absoluto hasta mínimo de duraciones, no alineación musical. Política candidata drift≤50ms/alternancia≤150ms tras preload; T-24 confirma instrumento/umbral antes RED del transporte y M-02 mide real. Si falta instrumento o codec, no se anuncian métricas ni se afloja tolerancia para ocultar fallo.
- Instrumentos capturan request efectivo/recipe version/hash/provenance/tools/parents/output sample counts/terminal/replay/storage UUID y tipo de evidencia. No timestamps/cost/tokens reales inventados. CA-29 implica commercial_use combinado y manifest nuevos inmutables; CPU no model/seed de inferencia falso.
- Texto: corpus≥20 español+10 idioma alternativo declarado, cinco acciones y secciones;100% tags válidos y exterior intacto en corpus contractual, quality/idioma por persona. Latencias p50/p95 medidas/reportadas sin objetivo numérico inventado. Modelo seleccionado por resultados, hash/revisión/licencia, memoria y cancelación.
- CA-01/21/23/24/19 exigen evidencia real y aceptación; CA-27 ramo provider real puede ser n/a por adapter ausente con motivo, registry off/preflight/secret-safety sí obligatorio. Sin provider contratado no se simula llamada real ni reduce aceptación local.

## API smoke y accesibilidad opcionales

El contrato cambia endpoints: se propone API smoke curl como ampliación opcional cuando root elija incluirla; este plan ya verifica APIs por tests focales + E2E/rechazo, no inventa bloques API-xx no autorizados. Axe-core no pedido; teclado/foco/anuncios obligatorios ya incluidos E2E/M-07, sin instalación adicional. Jira/Confluence desactivados.



## Compatibilidad contractual CPU (T-01 / CA-29)

La elección O1 de [cpu-contract-design.md](cpu-contract-design.md) y ADR-0074 se verifica documentalmente ahora; la implementación se prueba en T-04/T-05/T-07/T-09/T-26/T-29. Incluir NOT NULL de inferencia, NULL exclusivo CPU, rechazo de CHECK UNKNOWN y duplicados con NULL; preservar datos/IDs/índices/FK diferidas y entrantes/triggers tras reconstrucción de sólo tres tablas. Probar backup WAL restaurable, fallos de migración/rollback, foreign_keys ON y downgrade rechazado sin efectos si hay CPU.

Probar lectores v1/v2, bytes/hashes v1 históricos, song v2 con padres mixtos, export/import completo sin reactivar ejecución y post M1 inalterado. En API server mantener DTO/paths M1, añadir las cuatro operaciones v2, probar 409 para CPU en M1 después de autorización y antes de mutar; listado jamás filtra CPU silenciosamente. Preview v2 se publica temporalmente desde recibo/contexto privado sin Take/intención/asset job falsos. UNKNOWN bloquea publicación/serving/cleanup/slot; estas pruebas futuras no se sustituyen por la sonda contractual T-01.
