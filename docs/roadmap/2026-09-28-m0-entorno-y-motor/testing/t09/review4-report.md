# Revisión adversarial T-09 CPU — intento 4

Resultado: **0 Critical, 0 Important, 0 Minor pendientes**. R09-08 queda corregido en el soporte CPU. T-09 sigue en-progreso: revisión limpia no acredita el benchmark GPU ni sustituye QA.

Cuatro contextos frescos A/B/C/D. Delta íntegro de dos archivos,6550bytes,SHA `143b3460b1557e1f47dee5d5c7b16bc4bdfd9e7f0638c30ccbfaeea3048aa071`. Root verificó las33fuentes congeladas, sin cambios. Scope4exit0, sin fuera de alcance, avisos, info ni exclusiones de usuario. Full histórico aislado232673bytes/SHA `26a6367e5e85fb44b591c4aaabe02cbb93f489e8e0cd817c9a01cf2e2ba23362`; esta pasada revisó la corrección y sus regresiones, no volvió a leer entero el histórico.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Sensor consume el periodo, pero resta horizonte | ✓ | Runner116–125; sensor1/1,5s observa done1,01/1,51s; controles B independientes conformes |
| Deadline compartido events/status | ✓ | Runner139–153; no segundo periodo adicional para status |
| Horizonte agotado y terminal tardío | ✓ | Sensor4/5s: cero consultas; done posterior al límite rechazado |
| Identidad, secuencia y resume | ✓ | after0/1/2 y seq1/2/3 del mismoJ, sin resubmit; C rechaza eventos/estado de otrojob |
| Control sensor500ms | ✓ | Muestras0/1/2/3s; stream500ms; no promesa de cadencia exacta con sensor lento |
| HTTP absoluto, tamaño, token y cierre | ✓ | Regresiones preservadas, sin cambio del transporte en este delta; C302 sin redirección |
| Coste añadido | ✓ CPU | O(1) por vuelta y oportunidades acotadas; D simula3700s, no mideGPU |
| TDD, cobertura y alcance | ✓ | RED propio; entrega272tests; mediaoficial15módulos87,5511%; scope0 |
| CA reales T-09 | Pendientes | Matriz, bind/copia, preflight, spill, calibración, recomendación y experimento compile opcional no acreditados por CPU |

Ejecuciones comunicadas por los revisores: A45+10passed/0,87+0,46s; B55passed/1,32s más controles en memoria; C32passed/0,12s más tres sondas simuladas; D32passed/7deselected/0,53s más simulación. Son conjuntos solapados: no se suman como tests distintos. C corrigió dos problemas de preparación de su sonda (ruta temporal y quoting JSON) antes de repetirla; no fueron defectos de producto. El aviso cache_dir corresponde al proveedor de caché desactivado.

Los intentos1/2/3 quedan íntegros. Se conserva el arbitraje parcialR09-07: faltan argumentos/códigosLM dinámicos para reconstruir SHA64hex; los campos verificables permanecen corregidos. Esta revisión4 es la continuación concreta elegida por root bajo la delegación existente, no reset ni nueva aprobación puntual. No se acepta deuda.

Siguiente puerta: QA independiente sinUI por diseño. Computer Use continúa detenido trasEscape; no se reinicia, no se capturaGPU ni se accede a8768. Sin modelos, Docker, audio, red, instalaciones o conocimiento/memorias ajenos durante la revisión. [Recibo](review4-receipt.json). TDDn/a: publicación del informe.
