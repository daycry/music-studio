# QA del instrumento de cobertura — 2026-10-12

El componente CLI de cobertura pasó revisión adversarial y QA independiente. La tarea T-06 y el hito M3 siguen abiertos.

| Comprobación | Resultado |
|---|---|
| Revisión adversarial, intento 3 | A y B: cero hallazgos pendientes |
| Verificación literal de tests | 116 pasan, 1 omitido; exit 0 |
| Líneas del fichero de producción completo | 738/833 (88,60 %) |
| Ramas del fichero completo | 397/484 (82,02 %) |
| Cobertura combinada | 1135/1317 (86,18 %) |
| Exclusiones | Ninguna |
| Fuentes observadas antes y después | 153, sin cambios |
| Artefactos de QA verificados | 398 |
| Gate determinista | Exit 0; adaptador explícito de JUnit de pytest |

El omitido requiere permisos de symlink de Windows (1314). No acredita ese rechazo nativo. Los resultados de pytest se adaptaron con su procedencia explícita al gate; no son pruebas de Playwright o de la UI.

Un collector ROOT independiente ejecutó el entrypoint real con hijos propios de inventario y Coverage 7.16.2. El fixture Python produjo 4/4 líneas y 2/2 ramas cubiertas, con salida `pass` y exit 0. El contexto del collector se entrega exclusivamente en memoria. Sin ese contexto, el CLI devuelve `pending` y exit 2.

Las pruebas de informes combinados malformados conservan JSON de salida y devuelven `pending`. Los desacuerdos de versión o la corrupción demostrada devuelven `fail`. El instrumento no concede autoridad por un porcentaje, un booleano o un JSON presentado por el consumidor.

La integración instalada, los perfiles oficiales de JavaScript 5.0.3, el mapper TypeScript, Combined y branch-N/A reales permanecen pendientes. No se han probado aquí audio, GPU, UI, calidad musical, derechos ni las cohortes humanas de D13. El PDF privado se generó, con inspección estructural; su disposición visual no tiene una comprobación raster independiente.

Código aceptado: `scripts/m3_coverage_gate.py` SHA-256 `e18dd17b13896ca88673da265a3c22ff2420ac7501dff6db1c3fa4253e996ecf`. Tests: SHA-256 `9fb5c1c24bd7a77395d7ab884facae94b1cb89c8c7e34feefaaa87436bc3570e`. Recibos privados conservados bajo `.cache/dev-cycle/m3/cohort-metrics-t06-instrument-qa1-root-20261012/` y `cohort-metrics-t06-instrument-acceptance-root-20261012/`.
