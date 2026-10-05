# Informe de QA — M0/T-15, comparación de prompts

| | |
|---|---|
| Fecha | 2026-10-05 |
| Estado global | CONFORME técnicamente; calidad musical pendiente del propietario |
| URL auditada | http://127.0.0.1:8767/listen.html (solo local) |
| Plan | [improvement-plan.md](../../improvement-plan.md) · [ledger T-15](../../tasks.md) |

## Veredicto

ℹ️ Sin UI por diseño (`test-plan: n/a (sin UI)`). `ledger-lint` exit 0, 0 incoherencias y 7 avisos Changelog; `coverage-check` exit 0 por declaración canónica. La puerta de cobertura NO se ha ejecutado. `qa-gate.py` no aplica; sin resultados E2E ni porcentajes fabricados. El cierre técnico de T-15 corresponde al orquestador; M0 sigue abierto.

## Resumen

Preparación por hashes y prueba CPU independientes conformes. Generación real y recibos GPU/preservación verificados; 14 manifiestos CLI y 6 derivados válidos. HTTP y metadatos del navegador conformes dentro del alcance descrito. TDD/cobertura n/a: investigación, prosa, configuración privada y arnés efímero; código de producción sin cambios. No se repite la suite de T-14 ni se reutiliza su porcentaje como medición nueva.

## Cobertura (coverage-check)

La lista `eximidos` contiene T-00, T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10, T-11, T-12, T-13, T-14, T-15. `eximidos_exigidos: false`: son elementos para revisión, sin criterios GWT exigidos. `marcador_no_canonico: null`, `rutas_ui: []`, `rutas_ui_origen: {}`.

Advertencia `rutas_ui_degradado`: el diff contra «merge-base main…HEAD (a6eba66e)» no aporta ficheros; se han mirado únicamente cambios sin comitear y alcance declarado. Esto no prueba la ausencia de interfaz en un diff completo. Salida íntegra en [raw/coverage-check.log](raw/coverage-check.log).

## Resultados técnicos

| Comprobación | Resultado | Evidencia |
|---|---|---|
| Ledger | 0 incoherencias, 7 avisos; exit 0 | [log](raw/ledger-lint.log) |
| Memoria técnica | Consulta gotchas sin aciertos, exit 0 | [log](raw/knowledge-check.log) |
| Preparación | Letra idéntica por SHA-256, captions distintos de 415/426 caracteres con hashes acordes; parámetros públicos constantes, seis tomas previstas | [invariantes](raw/prepare-invariants.json) |
| CPU de fix1 | Exit 0; cancelación solo del job propio ante 95 %/fallo de monitor, no cancelación ajena; MP3 real de 10 s rechazado, 90 s aceptado, checkpoint/hash incorrectos rechazados | [log](raw/fix1-cpu-probe.log) |
| Compatibilidad AST | Gramática 3.11 de cuatro archivos y reserva del primer ULID verificadas en CPU | [log](raw/fix1-cpu-probe.log) |
| Revisión independiente | A+B intento 2: 0 gaps pendientes | [revisión](review-attempt2.md) |
| Generación GPU/manifiestos/normalización | Seis tomas nuevas de 90 s; 14 CLI + 6 derivados válidos; ganancia lineal sin limitador | [generación](generation-receipt.json), [CLI](raw/cli-manifests.log), [derivados](raw/derived-manifests.log), [validación](raw/runtime-validation.json) |
| Preservación/HTTP/metadatos | 30 archivos anteriores y referencia intactos según recibo de hashes del orquestador; 14 HEAD conformes; 7 players sin error | [preservación](preservation-receipt.json), [HTTP](raw/http-head.json), [navegador](listening-receipt.json) |

Constitución respetada: música local, preservación de takes/manifiestos y un modelo en VRAM. QA no carga modelos, no cambia producto ni lee texto privado de letra/captions/mapa. Muestreo del monitor cada 2 s no garantiza observar picos entre muestras; no se equipara presupuesto agregado con spill.

## Checklist manual (para una persona)

- [ ] Escuchar los tres pares a ciegas y valorar ritmo, afinación, voz e instrumentos.
- [ ] Elegir A/B/empate/ninguna sin consultar el mapa y exportar la valoración.
- [ ] Decidir calidad musical y próximos candidatos. Ningún ganador se deduce de metadatos.

## Trazabilidad

| Tarea | Resultado |
|---|---|
| T-15 | CPU/preparación/revisión y ejecución real técnicamente conformes; calidad pendiente del propietario |
| T-08–T-13 y M0 | Siguen abiertos, no afectados por este veredicto provisional |

## Evidencias y límites

Salidas originales con exit real en `raw/`, UTF-8 sin BOM y LF. Sin E2E/API/A11Y definidos, capturas o trazas ficticias. PDF no generado: motor `to-pdf` sin dependencias instaladas; no se instala por restricción de alcance y ubicación local del proyecto. Reporte solo local; Jira/Confluence no aplican.
## Ejecución real y escucha técnica

El recibo del orquestador acredita dos tandas exit 0 y seis tomas nuevas de 90 s, sesión `01M46QBFERQBK6XCH2Z4QQP9B1`. Ambas parten de 1.327 MiB, Ollama vacío y engine idle/unloaded, inferiores al límite estricto de 1.600 MiB. Cap dinámico 10.104,1758 MiB; pico 7.891,2583 MiB, `spilled: false`, `stop_reason: null` y `unload_confirmed: true` en ambas tandas. 177 muestras: RAM WSL pico excluyendo disponible 4.805,84375 MiB y swap pico 0,51953125 MiB. Reloj total 383,281 s; `run_s` incluye carga y no se suman tiempos por toma ni se deriva RTF.

Recibo de parámetros comparado con plan público: semillas 1/2/3 por caption, shift 1, BPM 94, es, BF16/PT, Turbo/LM0.6B, 8 pasos, letra por SHA-256 y captions distintos. Solo varía caption. La preservación de 30 archivos previos y de la referencia original procede de la comprobación SHA-256 before/after del orquestador; QA contrasta ese recibo, sin volver a cargar GPU ni leer el mapa privado.

Seis manifiestos derivados contienen padre de linaje, `limiter: false`, ganancias negativas, LUFS entre −16,39094 y −16,38576 frente al objetivo −16,39150, y picos entre −4,3 y −2,0 dBTP. `verify_manifest.py` confirma integridad de archivos y esquema. La referencia Suno permanece original; atenuación de reproducción declarada −3,20233 dB. La propiedad `volume` del navegador no está verificada.

HTTP HEAD independiente: página y siete recursos de audio devuelven 200. `.map-private.json`, manifiesto, scores, normalización privada y dos rutas de traversal devuelven 404. Solo se leen cabeceras/estado; no contenido privado. El recibo de navegador del orquestador acredita siete reproductores `readyState: 4`, `error: null`; seis de 90 s y referencia de 227,640979 s, sin errores de consola. 24 campos de puntuación, seis campos de instrumentos y botón exportar presentes. No se pulsa exportar ni se rellenan valoraciones. Servidores restablecidos tras reinicio del daemon; no se regeneran tomas ni se recarga la valoración anterior.

La primera aserción local de metadatos intentó exigir hash de letra en el request derivado, donde no existe ese campo; se corrigió a linaje del derivado y comparación del hash de entrada en el recibo fuente. No era un fallo del artefacto. Se declara en `raw/runtime-validation.json`.

**Recibo QA:** `status: passed`, `cli_manifest_count: 14`, `derived_manifest_count: 6`. Este passed es verificación técnica del alcance sin UI, no salida de Playwright ni aprobación de calidad musical. Pendientes tres decisiones manuales: escucha de cuatro dimensiones, exportación de valoración y elección de calidad/candidato. No handoff de cierre de M0 ni estados de la spec global por este agente.
