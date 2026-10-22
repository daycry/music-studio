# Informe de QA — Plan M3: producción, portada y vídeo con letra

| | |
|---|---|
| Fecha UTC | 2026-10-11T16:08:25.183229+00:00 |
| Estado documental | VERDE — qa-gate oficial sobre comprobaciones documentales reales |
| Estado de producto | Pendiente: 0 E2E ejecutados, 15 manuales pendientes, 0/42 tareas completadas |
| URL auditada | Ninguna; no se contactó app/host/servicio |
| Plan | [Plan candidato](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/snapshot/docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/improvement-plan.md) · [Test-plan candidato](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/snapshot/docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/test-plan.md) |

## Veredicto (qa-gate)

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 563,
    "failed": 0,
    "flaky": 0,
    "skipped": 0,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}
```

**Adaptación transparente:** `raw/results.json` no es una salida de Playwright ni JUnit. `audit.py` ejecuta 563 comprobaciones documentales y conserva booleano, nombre y evidencia en [checks.json](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/checks.json); las convierte 1:1 al esquema de suites que lee el gate oficial. No inventa capturas, pruebas de producto ni porcentajes unitarios. El `qa-gate.py` instalado se ejecutó sin alterar su umbral: [stdout](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/qa-gate.stdout), [recibo](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/qa-gate.receipt.json). Este verde sólo permite evaluar la adopción documental por ROOT. No es un marcador global «M3 sin UI».

## Resumen

- Comprobaciones documentales: 563/563, 0 fallos actuales.
- Snapshot: 50/50 pins antes y después; lectura UTF8 íntegra de cinco documentos, comparaciones literales de 49 criterios normativos y matrices de 14 funciones.
- Ledger: 42 tareas, 11 fases, todas borrador; DAG explícito sin desconocidas, adelantos ni ciclos. Estimación 930 h base/1116 h con margen, confianza baja; consumo/tokens/coste/horas IA reales null.
- FIX1: manifiesto de 69 payloads cotejado por SHA y bytes; los tres candidatos actuales coinciden. El manifiesto excluye únicamente su propio path por autorreferencia.
- No hubo instalación, Playwright, JUnit, cambios de código/canon/ledger/Git, GPU/Ollama, servicios, SQL, FFmpeg, Docker, navegador o datos de producción.

## Cobertura declarada (coverage-check) y ledger

```text
ledger-lint: 0 incoherencias · 0 avisos (tasks.md)
```

`ledger-lint.py`: exit0, 0 incoherencias y 0 avisos. [Salida](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/ledger.stdout) · [Recibo](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/ledger.receipt.json).

`coverage-check.py`: exit0, 34 GWT cubiertos mediante bloques E2E individuales, 49 escenarios definidos/referenciados; referencias rotas 0, tareas sin cobertura 0, escenarios sin referencia 0, GWT sin cubrir 0. [JSON oficial completo](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/coverage.stdout) · [Recibo](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/coverage.receipt.json). Es cobertura del plan, no cobertura de código ni ejecución E2E. No hay bloques API/A11Y solicitados.

## Cadena, alcance y correcciones

Spec aprobada; O1/ADR0080 ya incorporados documentalmente. Sus referencias antiguas a propuesta/adopción pendiente son historia delimitada por el acta final de incorporación ROOT. Plan privado en borrador; tres archivos canónicos todavía ausentes. Enlaces de frontmatter/rutas se resuelven desde el destino canónico futuro, dando prioridad a snapshot y usando canon sólo como fallback readonly. `spec: m3-...` en la spec y `design: m3-...` en design son identificadores, no enlaces.

La transferencia revisión2 se comprobó completa y por SHA. ROOT la identifica como síntesis normalizada de A/B, nunca transcripción literal. Se distinguen matriz actual49CA14F y tabla general/histórico de los tres Important corregidos.

| Corrección | Resultado documental | Límite |
|---|---|---|
| G01 | Las 15 preparaciones exigen contratos/seams e instrumentos/artefactos candidatos listos, sin exigir el cierre de tareas necesitadas del acta; acta real→review/QA→ROOT cierre. M01/M49 conservan M2 cerrado/heredados, T42 abierta. | Ninguna acta obtenida aquí. |
| G02 | Sólo ROOT escribe estados/resumen del ledger tras adopción; subagentes entregan evidencia. | QA no modificó ni cerró tareas. |
| G03 | Inventario completo por SHA y stack, raw oficial por fichero completo, umbral exacto≥80 sin medias, omisiones/exclusiones, missing, redondeo, stale o source-map ambiguo; herramienta/report ausente es pendiente. | Script/tests aún futuros, declarados T06, RED causal y revisión/QA obligatorios antes de cerrar fase1. Ningún caso adverso del script se ejecutó aquí. |

Se conserva stems/mixer con transporte común, export de original/ZIP/perfiles y medición final independiente, análisis parcial honesto, letra histórica/alineación cantada, generación/ref Comfy Docker, derechos/uploads, escena común N0 offline sobre audio final y canción completa (incluida Libre4:15), presets congelados, portable multiversión, backup SQLite+assets y restore/activación atómicos con rollback/ext4, GPU compartida y restauración sólo de intervención propia Ollama, seguridad/pins/licencias/firmas. Ausencia de capacidad no reduce las 14 funciones ni habilita descriptor por fixture.

## Contexto congelado y concurrencia ROOT

Los hashes canónicos difieren de snapshot en cuatro rutas esperadas: spec/design contienen enlaces privados propuestos; ledgers M1/M2 registran actividad ROOT posterior. El release canónico de esta QA ya incorpora M2 T03 cerrado en 3/30; durante la preparación ROOT añadió registro Git incremental y se observa nuevo SHA de tasks M2. [before/after y todas las diferencias](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/canonical-context.json). No se restauró ninguna fuente ni se atribuyó el SHA congelado a canon vigente. M2 sigue en-progreso y no está aceptado; M3 T42 mantiene M2 y gates heredados como requisito final.

## Resultados automáticos previstos (no ejecutados)

Los 34 E2E permanecen pendientes. Cada bloque tiene setup, acción, aserciones y capturas/recibos complementarios definidos; todavía requiere implementación y stack local autorizado. No se generaron capturas de UI ni se verificaron codecs, LUFS, calidad musical, render, GPU, persistencia ext4 o recuperación real.

| Escenario | Criterio | Tareas | Resultado producto |
|---|---|---|---|
| E2E-02 | CA-02 | T-02, T-03, T-12, T-14 | Pendiente |
| E2E-03 | CA-03 | T-12, T-35 | Pendiente |
| E2E-04 | CA-04 | T-06, T-12, T-23, T-27 | Pendiente |
| E2E-05 | CA-05 | T-12, T-23, T-27 | Pendiente |
| E2E-06 | CA-06 | T-14, T-15 | Pendiente |
| E2E-08 | CA-08 | T-03, T-13, T-16 | Pendiente |
| E2E-09 | CA-09 | T-17 | Pendiente |
| E2E-11 | CA-11 | T-05, T-18, T-36 | Pendiente |
| E2E-12 | CA-12 | T-04, T-05, T-18, T-36 | Pendiente |
| E2E-13 | CA-13 | T-04, T-18, T-36 | Pendiente |
| E2E-14 | CA-14 | T-05, T-18, T-36 | Pendiente |
| E2E-15 | CA-15 | T-14, T-19 | Pendiente |
| E2E-16 | CA-16 | T-19 | Pendiente |
| E2E-18 | CA-18 | T-03, T-04, T-13, T-20, T-21 | Pendiente |
| E2E-19 | CA-19 | T-21 | Pendiente |
| E2E-20 | CA-20 | T-03, T-13, T-20, T-21 | Pendiente |
| E2E-22 | CA-22 | T-11, T-14, T-22, T-23 | Pendiente |
| E2E-23 | CA-23 | T-11, T-22, T-23 | Pendiente |
| E2E-24 | CA-24 | T-23 | Pendiente |
| E2E-26 | CA-26 | T-04, T-07, T-14, T-24, T-25, T-26, T-39 | Pendiente |
| E2E-27 | CA-27 | T-07, T-24, T-25, T-26, T-39 | Pendiente |
| E2E-30 | CA-30 | T-10, T-27 | Pendiente |
| E2E-32 | CA-32 | T-10, T-28 | Pendiente |
| E2E-34 | CA-34 | T-03, T-13, T-29 | Pendiente |
| E2E-35 | CA-35 | T-29 | Pendiente |
| E2E-36 | CA-36 | T-04, T-08, T-29, T-30, T-31, T-41 | Pendiente |
| E2E-37 | CA-37 | T-08, T-31, T-41 | Pendiente |
| E2E-38 | CA-38 | T-04, T-08, T-31, T-41 | Pendiente |
| E2E-39 | CA-39 | T-04, T-08, T-30, T-31, T-41 | Pendiente |
| E2E-40 | CA-40 | T-09, T-32, T-41 | Pendiente |
| E2E-41 | CA-41 | T-09, T-29, T-33, T-41 | Pendiente |
| E2E-42 | CA-42 | T-09, T-32, T-33, T-41 | Pendiente |
| E2E-44 | CA-44 | T-02, T-09, T-14, T-25, T-31, T-32, T-33, T-34 | Pendiente |
| E2E-47 | CA-47 | T-07, T-12, T-22, T-25, T-35 | Pendiente |

## Checklist manual (para una persona)

- [ ] **M-01 — CA-01**: — M3 sólo se acepta con M2 cerrado y sus gates heredados cumplidos; definición técnica ADR-0037 y mocks no satisfacen ese cierre.
- [ ] **M-07 — CA-07**: — La separación real acredita alineación muestra a muestra y error de suma inferior a −30 dB según métrica fijada antes de prueba, método/modelo/pins y escucha de aislamiento/artefactos; fixture no verifica calidad del separador.
- [ ] **M-10 — CA-10**: — Comparación real de reproducción y mezcla exportada comprueba sincronía, niveles, silencio, clipping y ausencia de saltos; método/tolerancia de comparación se fijan antes de validar, y escucha humana acredita utilidad.
- [ ] **M-17 — CA-17**: — Análisis real se contrasta con medición de loudness y anotaciones independientes de beats/tonalidad/secciones; criterios por método y confianza se congelan antes de prueba. Etiquetas de letra no se presentan por sí solas como secciones medidas.
- [ ] **M-21 — CA-21**: — Escucha y revisión humana sobre audio cantado real en castellano, con palabras omitidas/repetidas y silencios, acreditan alineación y utilidad karaoke; se miden errores contra anotación independiente y umbrales previamente ratificados. Parser LRC/SRT o timestamps mock no acreditan esto.
- [ ] **M-25 — CA-25**: — ComfyUI headless real en Docker/CUDA acredita generación y edición por referencia, workflows/nodos/pesos seguros fijados, VRAM/RAM/tiempos y unload; revisión visual humana acredita legibilidad/calidad de opciones. PNG mock no satisface esta capacidad.
- [ ] **M-28 — CA-28**: — Render/export real Docker/FFmpeg se decodifica y reproduce de principio a fin: duración, fps/resolución, audio final LUFS/true peak, sincronía sin deriva y correspondencia palabra/pantalla se miden contra referencias; se escucha/ve en navegador y reproductor independiente, sin texto cortado o ilegible.
- [ ] **M-29 — CA-29**: — Sobre canción representativa en la5070 se registra tiempo N0, carga CPU/RAM/VRAM y modo efectivo; el objetivo «en minutos», perfiles y tolerancias se fijan antes de prueba y no se cumplen con un clip fixture abreviado. No exige comprar GPU ni usar modelo que necesita16GB.
- [ ] **M-31 — CA-31**: — F-19 se verifica por ruta real de producto y escucha sobre material autorizado: la evaluación registra reconocimiento del motivo/estructura y acompañamiento útil, artefactos y límites. Soporte nativo de task sin integración o calidad no cierra el criterio.
- [ ] **M-33 — CA-33**: — Calidad alta se compara con referencia emparejada usando mismo texto/metadata efectiva, recibos y nivel de escucha igualado; pruebas reales verifican GPU/RAM/desbordamiento y escucha humana registra mejora/compromisos. Más pasos, XL o un hash no prueban mejora musical por sí solos.
- [ ] **M-43 — CA-43**: — El ejercicio de recuperación de biblioteca real usa copia/cohorte autorizada y guardas before/after de originales: restaura en destino nuevo y prueba consulta, búsqueda y reproducción real. La activación posterior exige backup restaurable y ventana exclusiva; no basta biblioteca sintética ni borrar original para demostrar recovery.
- [ ] **M-45 — CA-45**: — Integración Docker persistente acredita publicación no-clobber/CAS/replay sobre raíz ext4/UUID correcta, colisiones y restart; backend/montaje incorrecto aborta. Tmpfs y mocks no acreditan almacenamiento real.
- [ ] **M-46 — CA-46**: — Cada capacidad GPU real acredita una residencia, tope libre menos margen, modos efectivos, picos VRAM/RAM y ausencia de desbordamiento no declarado; unload comprueba liberación y turno Ollama se restaura sólo según intervención propia, sin detener servicio ni borrar modelos.
- [ ] **M-48 — CA-48**: — Artefactos tienen procedencia/versiones/hashes/rights comprobables, CPU sin ejecución de inferencia ficticia y `commercial_use` conjuntivo; se leen v1/v2 históricos sin reescritura. Contratos code-first y DTOs M1 conservan compatibilidad; cambios no cubiertos requieren decisión previa y migración segura.
- [ ] **M-49 — CA-49**: — La aceptación registra por separado CPU/fixtures, E2E sintético, Docker/FFmpeg persistente, GPU real, experiencia de navegador/reproductor y escucha/revisión humana; ningún helper documental, porcentaje de cobertura o prueba aislada sustituye evidencia de producto pendiente.

## Trazabilidad (tarea → resultado)

| Tarea | Escenarios | Resultado producto |
|---|---|---|
| T-01 | M-01, M-48 | Pendiente; borrador |
| T-02 | E2E-02, E2E-44, M-48 | Pendiente; borrador |
| T-03 | E2E-02, E2E-08, E2E-18, E2E-20, E2E-34, M-48 | Pendiente; borrador |
| T-04 | E2E-12, E2E-13, E2E-18, E2E-26, E2E-36, E2E-38, E2E-39, M-48 | Pendiente; borrador |
| T-05 | M-07, M-10, E2E-11, E2E-12, E2E-14 | Pendiente; borrador |
| T-06 | E2E-04, M-17, M-21, M-25, M-28, M-29, M-31, M-33, M-43, M-49 | Pendiente; borrador |
| T-07 | E2E-26, E2E-27, M-28, M-29, E2E-47 | Pendiente; borrador |
| T-08 | E2E-36, E2E-37, E2E-38, E2E-39 | Pendiente; borrador |
| T-09 | E2E-40, E2E-41, E2E-42, M-43, E2E-44, M-45 | Pendiente; borrador |
| T-10 | M-07, E2E-30, M-31, E2E-32, M-33, M-46 | Pendiente; borrador |
| T-11 | E2E-22, E2E-23, M-25, M-46 | Pendiente; borrador |
| T-12 | E2E-02, E2E-03, E2E-04, E2E-05, E2E-47, M-48 | Pendiente; borrador |
| T-13 | E2E-08, E2E-18, E2E-20, E2E-34, M-48 | Pendiente; borrador |
| T-14 | E2E-02, E2E-06, E2E-15, E2E-22, E2E-26, E2E-44, M-45, M-48 | Pendiente; borrador |
| T-15 | E2E-06, M-07, M-46 | Pendiente; borrador |
| T-16 | E2E-08, M-10 | Pendiente; borrador |
| T-17 | E2E-09, M-10, M-48 | Pendiente; borrador |
| T-18 | E2E-11, E2E-12, E2E-13, E2E-14 | Pendiente; borrador |
| T-19 | E2E-15, E2E-16, M-17 | Pendiente; borrador |
| T-20 | E2E-18, E2E-20, M-21 | Pendiente; borrador |
| T-21 | E2E-18, E2E-19, E2E-20, M-21 | Pendiente; borrador |
| T-22 | E2E-22, E2E-23, M-25, M-46, E2E-47 | Pendiente; borrador |
| T-23 | E2E-04, E2E-05, E2E-22, E2E-23, E2E-24, M-25 | Pendiente; borrador |
| T-24 | E2E-26, E2E-27 | Pendiente; borrador |
| T-25 | E2E-26, E2E-27, M-28, M-29, E2E-44, E2E-47 | Pendiente; borrador |
| T-26 | E2E-26, E2E-27, M-28, M-29 | Pendiente; borrador |
| T-27 | E2E-04, E2E-05, E2E-30, M-31, M-46 | Pendiente; borrador |
| T-28 | E2E-32, M-33, M-46 | Pendiente; borrador |
| T-29 | E2E-34, E2E-35, E2E-36, E2E-41 | Pendiente; borrador |
| T-30 | E2E-36, E2E-39, M-48 | Pendiente; borrador |
| T-31 | E2E-36, E2E-37, E2E-38, E2E-39, E2E-44, M-45, M-48 | Pendiente; borrador |
| T-32 | E2E-40, E2E-42, E2E-44, M-45 | Pendiente; borrador |
| T-33 | E2E-41, E2E-42, M-43, E2E-44, M-45 | Pendiente; borrador |
| T-34 | E2E-44, M-45 | Pendiente; borrador |
| T-35 | E2E-03, M-46, E2E-47 | Pendiente; borrador |
| T-36 | M-07, M-10, E2E-11, E2E-12, E2E-13, E2E-14, M-46 | Pendiente; borrador |
| T-37 | M-17, M-21, M-46 | Pendiente; borrador |
| T-38 | M-25, M-46 | Pendiente; borrador |
| T-39 | E2E-26, E2E-27, M-28, M-29 | Pendiente; borrador |
| T-40 | M-31, M-33, M-46 | Pendiente; borrador |
| T-41 | E2E-36, E2E-37, E2E-38, E2E-39, E2E-40, E2E-41, E2E-42, M-43, M-45, M-48 | Pendiente; borrador |
| T-42 | M-01, M-49 | Pendiente; borrador |

## Incidencia del harness conservada

Primera ejecución: 562 checks pasan, 2 fallan; gate NO-VERDE. El harness confundió los identificadores propios `spec:` y `design:` con paths. Son metadatos de la plantilla; las referencias de cadena en esos documentos sí fueron validadas. Se corrigió exclusivamente `audit.py`, se movió el raw intacto a [attempt1](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/attempt1/audit-summary.json) y se repitieron todos los checks. El original no se borra ni se rebautiza como resultado de producto. Un pin adicional de herramienta knowledge explica que el denominador final sea 563 tras retirar las dos falsas expectativas. La primera generación de informe falló antes de ejecutar por SyntaxError en finalize.py (f-string sin terminar, línea87); corregida sólo en la herramienta privada. No fue fallo ni ejecución de producto; la observación del tool queda registrada en raw/finalize-diagnostic.json, sin presentar un stream original no capturado.

## Evidencias y límites

[Harness](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/audit.py) · [Lecturas completas](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/read-complete.json) · [Pins previos](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/pins-before.json) · [Pins posteriores](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/pins-after.json) · [Herramientas SHA](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/source-tools.json) · [Comprobaciones](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/checks.json) · [Adaptación de resultados](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/results.json) · [Resumen](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/audit-summary.json) · [Contexto gestionado](../../../../.cache/dev-cycle/m3/production-plan-current-qa1-20261011/raw/execution-context-final.json).

Knowledge-find por gotcha/contexto devolvió salida vacía; fallback `--tipo gotcha --limit 0` tampoco aportó entrada aplicable. No se escribió conocimiento. Sólo fuentes locales y snapshot, sin navegación web para revisar contratos documentales futuros.

Guardrail: no se seleccionó URL ni se ejecutó E2E o acceso a hosts; por ello no procede guardrail_assert de conexión. El test-plan conserva127.0.0.1:3000/8000 para futura QA local.

PDF opcional omitido por scope explícito de ROOT; no se instalaron renderer/rasterizadores. El informe Markdown y sus enlaces se verifican estructuralmente; no se atribuye preview visual ni PDF. No se midió cobertura unitaria de producto ni porcentaje ficticio. Producto exige instrumentos oficiales futuros y sus umbrales completos por fichero.

DONE_WITH_CONCERNS: sin gaps documentales nuevos; las limitaciones son evidencia de producto pendiente y PDF opcional ausente. ROOT debe verificar estos payloads y decidir adopción. No se dispara handoff a documenter de producto, se cambia estado canónico ni se acepta M3.


## Aprobación y adopción ROOT del plan — 2026-10-11T16:16:11.792117+00:00

El propietario delegó la implementación de todo el roadmap y la elección entre alternativas. ROOT aprueba e incorpora este plan tras revisión2 fresca A/B sin gaps y QA documental563/563. Se han verificado107payloads,50fuentes,20enlaces; ledger/coverage-check/qa-gateoficialesexit0.42tareas/11fases/49CA14funciones/34E2E15manuales permanecen íntegros. No tareas M3cerradas ni producto probado. Consumo realnull. M2actual3/30(T03purocerrado),heredados ycalidad/humano/M2hito siguenpendientes; dependencias técnicas se liberanporunidad yfinalM3requiereM2cerrado. Originales privados/revisiones/QA intactos.
