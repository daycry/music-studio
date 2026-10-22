**Lente B · M0/T-11 · intento 2/3: 0 Critical, 1 Important nuevo.** Revisión estática del diff y de las cinco fuentes completas INLINE. Sin herramientas, pruebas propias ni comprobación de hashes; ejecuciones y cobertura son evidencia aportada por root.

| Criterio | Resultado |
|---|---|
| R11-01: códigos sin timestamp y reanudación estable | ✓ Corregido mediante códigos aleatorios persistidos. |
| R11-02: agrupación por brief/candidato ante fallos parciales | ✓ Conserva los grupos planificados, incluidos los vacíos. |
| R11-03: impedir descuento de suelo autodeclarado | ✓ Devuelve `PENDING` y rechaza autorizar el descuento. La ejecución controlada real permanece pendiente. |
| R11-04: aislar CLAP/Audiobox inválidos | ✓ Validación de estructura y tipos con errores `ValueError` aislados por métrica. |
| R11-05: deadline durante tráfico continuo | ✓ Comprueba el plazo al recibir bloques y procesar líneas. |
| Espera de eventos válidos dentro del plazo disponible | ✗ El nuevo timeout de lectura aborta trabajos legítimos tras un segundo sin tráfico. |
| Fidelidad literal, bindings, staging y conservación del raw | ✓ Sin regresiones nuevas identificadas. |
| Fuentes de tests | ✓ Sin defectos adicionales de corrección identificados. |

| ID | Gravedad | Fichero:línea | Escenario concreto de fallo |
|---|---|---|---|
| B2-01 | Important | `scripts/eval/run.py:336` y `scripts/eval/run.py:219` | Un job CPU aceptado emite un evento y tarda dos segundos en producir el siguiente, completando dentro de los 60 segundos permitidos. El stream fija `read timeout ≤ 1 s`; `chunks()` convierte ese vencimiento en `ValueError("TIMEOUT")`, aborta el job y solicita cleanup/cancelación pese a quedar plazo global. `/v1` no exige eventos ni keepalives cada segundo. La lectura breve necesita permitir continuar esperando o reengancharse desde `last` hasta el deadline, sin repetir el POST. |

**R11-06 Minor continúa pendiente**, sin modificación ni aceptación de deuda; pertenece a la lente D. No identifico otros defectos nuevos de lente B.

Derechos/letras reales, integración GPU, corpus y suelo ASR acreditados, 30 canciones y escucha siguen pendientes declarados. No constituyen aceptación conseguida ni nuevos bugs de esta unidad. **T-11 permanece en-progreso; candidato CPU pendiente de corrección y QA.**