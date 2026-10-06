# T-16 — revisión del arnés privado, intento 2

Fecha: 2026-10-06. A+B frescas, secuenciales por límite de threads. Recibieron la [tabla completa del intento1](harness-review-1.md), incluidos sus criterios aprobados y cuatro Important; sin rebates. Diff completo de snapshots privados contra runner/packer actuales, pruebas nuevas y evidencia. No se reabre el producto CPU aprobado.

| ID / criterio | A | B | Evidencia |
|---|---|---|---|
| H1: limpieza ante timeouts | Conforme CPU | Corregido | Arranque dentro del finally; logs/stop/rm independientes; etiqueta/imagen e ID verificados; tres escenarios más identidad ajena |
| H2: referencia y recuperación | Conforme CPU | Corregido | Temporal exclusivo, hash y hardlink sin sustitución; interrupción/reintento, destino y temporal ajenos preservados |
| H3: math/validación MP3 | Conforme CPU | Corregido | Import presente, globals de función AST y FFprobe real de senoide existente |
| H4: job ajeno | Conforme CPU | Corregido | Detección del monitor y lectura final; dos escenarios sin stop/rm, cleanup diferido registrado |
| CA1/2 de producto y alcance | Conservados | No reabiertos | Sin código de producto, pesos, locks, dependencias, contratos ni imagen cambiados |
| Hashes actuales e históricos | Conforme | Conforme | Cuatro fuentes actuales y dos snapshots; SHA T-15 fijado; recibos anteriores distinguidos como antecedentes |
| Constitución/preservación/linaje | Conforme en tramo corregido | Sin defectos | Fuente de referencia intacta; padres fuera del diff; no nuevas rutas exteriores |
| CA3/4: GPU, paquete musical y escucha | No verificable | No verificados | Abiertos; ninguna inferencia ni ganador, sin sustitución por tests CPU |
| Interop/OpenAPI | No aplica | No aplica | No cambia ese alcance |

Resultado: **cero Critical/Important/Minor pendientes**. A ejecutó12passed/0avisos/exit0, AST3.11 de cuatro archivos y siete hashes; B12passed/1aviso/exit0, fuentes y SHA T-15 verificados. El aviso B es WinError5 al escribir caché pytest; no se presenta esa ejecución sin avisos. Diff-check0 por A. Sin Docker real, GPU, instalaciones ni audio original; FFprobe solo sobre fixture sintética existente.

Selector C/D=false sobre Git; los privados ignorados se revisaron expresamente. No aparecieron otros hallazgos concretos de seguridad/rendimiento. Scope0 previo, ledger coherente. QA independiente del arnés pendiente; no se declara la limpieza real ni un paquete musical completo por estas pruebas. Fuente de consumo estimado, horas IA/tokens/coste reales desconocidos. Journals ajenos intactos; Jira/Confluence desactivados.
