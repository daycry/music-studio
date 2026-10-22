# QA actual de custodia Linux

Componente aceptado por ROOT tras revisión fresca A/B/D sin gaps y QA independiente sobre las fuentes adoptadas. **T-05 y M1 siguen abiertos**: este resultado no acredita el almacenamiento persistente ni el E2E completo.

| Comprobación | Resultado |
|---|---|
| Custodia nativa Linux | 52/52, 49,09 s; cero fallos, errores u omisiones |
| CPU, SQLite, audio y FFmpeg reales | 7/7, 92,27 s; cero fallos, errores u omisiones |
| Módulo completo custody_linux | 242/274 líneas, 88,3212 %, cero exclusiones |
| Módulo completo custody_linux_supervisor | 353/437 líneas, 80,7780 %, cero exclusiones |
| Gate técnico JUnit y cobertura | exit 0; Playwright no aplica |
| Integridad contrastada por ROOT | 2.312 artefactos, 109 fuentes actuales y 62 imports de proyecto |
| Exportación y retirada | tar verificado antes de retirar contenedores propios; Pid 0 |

La ejecución usa la imagen CPU existente, fuentes de solo lectura y procesos Linux reales. Los errores del bootstrap de pruebas están etiquetados como inyectados; las señales, pidfds, esperas y recogida de procesos son reales. La cobertura oficial utiliza únicamente líneas medidas de fuentes con SHA idéntico. La variante temporal de planificación con otro SHA queda separada y no participa en el gate.

Los diagnósticos de preparación quedan conservados: bind que ocultó el intérprete, fixture hijo omitida, directorio de trabajo incorrecto, bind de herramientas sin recibo y error de copystat en la exportación. La autenticidad integral de FFmpeg se comprobó durante la última suite, después del fallo del preflight de preparación; el producto verificó el recibo auténtico antes del cómputo. Esa secuencia no se presenta como un preflight anterior a la suite. No se repitió la suite nativa tras obtener verde.

El tar final mide 44.247.040 bytes y tiene SHA-256 `dced4110779ba8d613059efac3a6a8d3638b6af2651fecbff3c753d3461c5236`. ROOT cotejó los 908 miembros regulares, ambos raw SQLite de cobertura y los JUnit originales. Los 109 archivos corresponden al código actual y no han cambiado durante QA. Exit 143 de la retirada corresponde al proceso inactivo del contenedor, mientras pytest y docker exec terminaron con 0.

Los originales, inventario, raw, diagnósticos y recibo de aceptación están en los namespaces locales `linux-custody-current-qa-20261010` y `validation-20261010` bajo `.cache/dev-cycle/m1/`. No se generaron resultados Playwright sintéticos. PDF no generado: dependencias de render no preparadas.

Continúan pendientes el controller durable, la persistencia ext4/VHDX, Range, recovery y backup reales, las valoraciones manuales y el cierre formal del hito. Véase el [informe global vigente](../current-validation-2026-10-10.md).
