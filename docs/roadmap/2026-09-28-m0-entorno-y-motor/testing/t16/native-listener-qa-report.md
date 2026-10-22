# QA independiente — listener nativo T-16

**Resultado acotado: CONFORME, 54/54 casos HTTP, 0 fallos; ejecución exit 0.** No constituye cierre de T-16 ni verde E2E del producto.

ℹ️ sin UI por diseño (`test-plan: n/a (sin UI)`): ledger-lint exit 0, 0 incoherencias y 6 avisos de Changelog; coverage-check exit 0, declaración aceptada y puerta de cobertura no ejecutada.

## Alcance y aislamiento

Candidato SHA-256 `3c123f51a3f047726e3a428c7dcbd7ac4d99ca2d8ebad18f4363f507679c71cc`. Se extrajeron mediante AST la clase original completa `ListeningHandler` y su asignación `allowed`, sin mocks de métodos y sin ejecutar el setup del script. Servidor `ThreadingHTTPServer(('127.0.0.1', 0), ListeningHandler)` con fixtures propios: HTML, seis secuencias deliberadamente NO AUDIO y referencia NO AUDIO. Los nombres históricos de rutas son fixtures; no se leyeron originales, punteros ni sesiones vivas.

Guardrail del plugin 1.21.1 exit 0 para loopback antes de iniciar. Puerto efímero **59422**: servidor cerrado, hilo terminado y conexión posterior rechazada. Sin tocar 8766/8767/8768, sin GPU, modelos, jobs, Docker, fullpack, instalación ni suites del producto. No se consultó conocimiento ni memoria.

## Evidencia HTTP

| Grupo | Casos | Resultado |
|---|---:|---|
| GET/HEAD de 8 rutas, sin consulta y con consulta | 32 | 200; bytes exactos en GET, cuerpo vacío HEAD, Content-Length y MIME correctos |
| Rechazos de mapa/manifest, listados, traversal y ruta codificada | 20 | 404; sin exponer bytes privados |
| POST de HTML y fixture mp3 | 2 | 501 |

Cada solicitud y su status/MIME/SHA del cuerpo están en [http-cases.json](../../../../../.cache/dev-cycle/t16/native-listener-qa/http-cases.json). Resultado de ejecución en [summary.json](../../../../../.cache/dev-cycle/t16/native-listener-qa/summary.json), JUnit en [junit.xml](../../../../../.cache/dev-cycle/t16/native-listener-qa/junit.xml), salidas en [exits.json](../../../../../.cache/dev-cycle/t16/native-listener-qa/exits.json). 28 archivos congelados antes/después idénticos; incluye las 20 fuentes/dependencias de origen y 8 artefactos de entrega/revisión. Los 20 hashes originales coinciden además con el freeze entregado.

## Puertas y trazabilidad

T-16 → protocolo HTTP de configuración del listener; no acredita CA3/CA4. A+B+D frescas conformes en review-final conservado; selector C no aplica. Esta QA añade HTTP real independiente, sin repetir los 88 casos de dobles de B.

JSON literal de puertas no aplicables (sin inventar salida de qa-gate):

```json
{
  "qa_gate": {
    "executed": false,
    "status": "n/a",
    "percent": null
  },
  "coverage_gate": {
    "executed": false,
    "status": "n/a",
    "percent": null
  },
  "reason": "test-plan: n/a (sin UI)"
}
```

Salida literal de coverage-check:

```text
ℹ️  test-plan: n/a (sin UI) declarado en improvement-plan.md: iniciativa sin UI por diseño, la puerta de cobertura NO se ha ejecutado (no es «cobertura OK»)

ℹ️  se listan para la revisión 20 tarea(s) del ledger (la spec no aporta criterios rastreables) (T-00, T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10, T-11, T-12, T-13, T-14, T-15, T-16, T-17, T-18, T-19): la puerta no exigía cobertura de estos (solo la exige de los [GWT]), así que aquí no se exime nada — su evidencia es el campo `Verificación` de la tarea que los cierra en tasks.md

{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14", "T-15", "T-16", "T-17", "T-18", "T-19"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": null}
```

Salida literal de ledger-lint:

```text
⚠️  T-09: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título

⚠️  T-10: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título

⚠️  T-11: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título

⚠️  T-12: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título

⚠️  T-13: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título

⚠️  T-16: sin campo **Changelog** (otras tareas lo declaran) — su bullet del CHANGELOG degradará al título

ledger-lint: 0 incoherencias · 6 avisos (tasks.md)
```

## Comprobaciones manuales pendientes

- [ ] Root: aceptar fullpack tras QA separada del fix de contrato; comprobar metadatos y seis90 antes de iniciar listener propio.
- [ ] Reproducción real en navegador, codecs y escucha privada de las seis tomas y referencia.
- [ ] CA3/CA4, evaluación de calidad y posible ganador. M0 permanece abierto.

No se prueba aquí fallback/setup completo, navegador, codec, calidad ni aislamiento frente a enlaces simbólicos creados por un actor con acceso al filesystem. Los fixtures sólo verifican protocolo/allowlist; MIME audio/mpeg procede de la extensión y no implica audio válido. PDF pendiente; no se instaló ningún renderer. Estado de plan/ledger intacto, sin handoff documental. Métricas: fuente estimada; tokens/EUR/horas null, ventana combinada de root sin ventana propia.
