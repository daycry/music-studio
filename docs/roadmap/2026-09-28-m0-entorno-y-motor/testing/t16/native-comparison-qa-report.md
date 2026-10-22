# QA independiente T-16: configuración privada de comparación nativa

Estado: **CONFORME_CPU_CONFIGURACION**. 14 pruebas CPU; 0 fallos, 0 errores y 0 omitidas. Sólo esta entrega; T16 y M0 siguen abiertos.

Funciones reales extraídas del AST con dobles: namespaces Turbo/SFT, colisión sin mutación, owner/imagen/job ajenos conservados, baseline 1600 aceptado y 1601 rechazado, propagación de éxito/fallo del bloque principal y finally (stop/join/close), limpieza tras timeout de arranque/logs/stop. Ejecución íntegra del candidato con --prepare-only y procesos/HTTP doblados: exit0 antes de jobs/Popen. Ejecución real --prepare-only: exit 0, sin generación; única operación Docker permitida, image inspect de lectura. Sin GPU, cargas de modelos, contenedores nuevos, jobs, audio, builds, instalaciones ni suites de producto.

51 rutas declaradas y 54 rutas únicas congeladas antes/después. Diferencias: []. Fuentes de producción: 9, hashes coincidentes: True. Artefactos de entrega verificados respecto de rutas relativas a entrega: True. Runner/plan fijados por SHA; plan sólo cambia image_digest. Cuatro lentes A/B/C/D conformes comprobadas en review-final.json.

Runtime real: Python 3.12.14. AST feature_version=(3,11) valida sólo gramática; no ejecución real en Python3.11.

ℹ️ test-plan: n/a (sin UI). Ledger exit 0; coverage-check exit 0. Se conserva su salida completa en [coverage.stdout.txt](../../../../../.cache/dev-cycle/t16/native-comparison-qa/coverage.stdout.txt): cobertura eximida por declaración, no cobertura E2E medida. qa-gate n/a: cambio literal de configuración, sin UI ni results.json E2E. Cobertura porcentual n/a; no se inventa verde global ni porcentajes. Avisos/eximidos/rutas UI figuran en la salida enlazada.

Evidencia: [JUnit](../../../../../.cache/dev-cycle/t16/native-comparison-qa/junit.xml), [pruebas](../../../../../.cache/dev-cycle/t16/native-comparison-qa/pytest.stdout.txt), [prepare](../../../../../.cache/dev-cycle/t16/native-comparison-qa/prepare.stdout.txt), [ledger](../../../../../.cache/dev-cycle/t16/native-comparison-qa/ledger.stdout.txt), [freeze antes](../../../../../.cache/dev-cycle/t16/native-comparison-qa/freeze-before.json), [freeze después](../../../../../.cache/dev-cycle/t16/native-comparison-qa/freeze-after.json), [recibo](../../../../../.cache/dev-cycle/t16/native-comparison-qa/receipt.json).

Manual pendiente: CA3/CA4, seis tomas de90 segundos reales y calidad musical/escucha; winner=null. No aprobación musical, cierre del hito ni handoff a documenter. Tokens/eur/horas reales desconocidos (null).

PDF: pendiente: motor to-pdf y sus dependencias no disponibles en la caché de usuario ni en .cache/tools del repositorio. No se ha instalado nada. Autorización de esta QA exige herramientas existentes únicamente.

Salida literal de coverage-check (no ejecución de cobertura):

```text
ℹ️  test-plan: n/a (sin UI) declarado en improvement-plan.md: iniciativa sin UI por diseño, la puerta de cobertura NO se ha ejecutado (no es «cobertura OK»)
ℹ️  se listan para la revisión 20 tarea(s) del ledger (la spec no aporta criterios rastreables) (T-00, T-01, T-02, T-03, T-04, T-05, T-06, T-07, T-08, T-09, T-10, T-11, T-12, T-13, T-14, T-15, T-16, T-17, T-18, T-19): la puerta no exigía cobertura de estos (solo la exige de los [GWT]), así que aquí no se exime nada — su evidencia es el campo `Verificación` de la tarea que los cierra en tasks.md
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["T-00", "T-01", "T-02", "T-03", "T-04", "T-05", "T-06", "T-07", "T-08", "T-09", "T-10", "T-11", "T-12", "T-13", "T-14", "T-15", "T-16", "T-17", "T-18", "T-19"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": null}
```

Ledger: 0 incoherencias y6 avisos por Changelog ausente en T09/T10/T11/T12/T13/T16. Pytest informa un aviso de cache_dir desconocido porque cacheprovider se desactiva; no es un fallo del producto ni un RED.

