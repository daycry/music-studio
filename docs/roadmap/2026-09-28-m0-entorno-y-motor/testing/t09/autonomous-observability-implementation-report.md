# T-09 — Entrega CPU de observabilidad autónoma

Entrega técnica aceptada para revisión: **135 tests**, sin fallos, errores ni omisiones; 43 RED conservados. Ruff y formato pasan sobre ocho archivos modificados.

La cobertura oficial de coverage.py es 1107/1370 líneas (**80,80 %**) sobre los siete módulos de producción cambiados. Es cobertura ponderada por líneas de esos archivos, no de las líneas del diff ni un mínimo individual por módulo.

Root verificó 83 artefactos, 64 fuentes finales y 62 preimágenes. Ocho fuentes cambiaron y 56 permanecen intactas, incluido el transporte y lifecycle de benchmark_runtime. [Recibo](autonomous-observability-implementation-receipt.json).

La implementación incorpora método WDDM explícito, política sellada, identidad/estado/unidades/frescura de contadores, heartbeat del navegador y guardas antes de enviar y durante un trabajo. La ventana de 15 minutos no interrumpe una matriz con observación continua fresca. La compartida conserva validación del proveedor, sin contraste independiente ni atribución causal de spill.

Revisión adversarial, QA independiente, piloto real de carga/descarga y matriz160 siguen pendientes. T-09 permanece abierta. Esta entrega no acredita GPU, rendimiento ni calidad musical. La interfaz y los originales requeridos para la acreditación están en el informe privado de implementación bajo `.cache/dev-cycle/t09/autonomous-observability-implementation/report.md`.
