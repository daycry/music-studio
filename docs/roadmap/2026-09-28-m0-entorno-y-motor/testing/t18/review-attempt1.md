# T-18 — Revisión adversarial, intento 1

Lentes A+B frescas; selector automático C/D=false. Base `08d6d82`, cambios locales y archivos nuevos de T-18 leídos por bloques. Puerta de alcance exit 0, sin archivos fuera de alcance, avisos ni exclusiones de usuario; siete journals ajenos preservados y excluidos por la regla predeterminada. No se reabren tareas históricas. Jira y Confluence desactivados.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Original/efectivo, limpieza opt-in, versos y cabeceras | ✓ | Tests y probe CLI real; 72 líneas, nueve tags íntegros y 32 registros de hashes anteriores intactos |
| Preparación offline, metadata opcional y autoría | ✓ | Pruebas de omisión/conflictos, CLI real y endpoint inaccesible |
| Publicación inmutable, confinamiento y datos privados | ✓ | Pruebas de publicación/fallo/integridad y lectura de informes públicos |
| Compatibilidad aditiva de key en `/v1` | ✗ | Schema base acepta longitud 0/33; nuevo descriptor las rechaza |
| Semilla de cada variante vinculada al recibo | ✗ | Cambiar semilla del manifiesto a 99999 conserva validación positiva |
| Hash declarado de letra coherente con bytes originales | ✗ | Recibo externo con hash declarado falso conserva validación positiva |
| RED, verificación y cobertura de implementación | ✓, QA pendiente | RED reales y recibos leídos; suite B 177 passed/1 skipped; statements cambiados ≥86,54 % |
| Contratos generados y documentación correspondiente | ✓ | Exportador al día, cuatro ejemplos anteriores válidos; ADR/pipeline/contrato/convenciones actualizados |

| # | Grado | Gap | Localización | Corrección / veredicto |
|---|---|---|---|---|
| A1 | Important | Restricción de un parámetro existente, incompatible con Constitución §2 | `apps/engines/acestep/descriptor.py:71` | Pendiente: conservar schema legado `key` string; validar la nueva opción CLI por separado |
| B1 | Important | La correspondencia preparation/request omite semilla y variante | `packages/audio-post/audio_post/manifest.py:103` | Pendiente: vincular base resuelta, incluida aleatoria, e índice a la semilla de cada salida |
| B2 | Important | No se cruza lyrics_sha256 declarado con bytes originales | `scripts/input_preparation.py:92`, `packages/audio-post/audio_post/manifest.py:112` | Pendiente: rechazar hash fuente discordante en preparación reutilizable y verificador |

A ejecutó 17 tests específicos, CLI help real y comparación de schemas; B ejecutó la verificación declarada (177 passed, 1 skipped, cinco warnings existentes) y dos probes sintéticos. Ambos comprobaron exportador y ejemplos. Root corroboró el schema base y acepta las dos reproducciones de B; sin rebates. No inferencia ni cambios de producción durante la revisión. Un contenedor existente se consultó solo para lectura CPU de fuente, CUDA oculta.

Fusión: cero Critical, tres Important y cero Minor pendientes. T-18 vuelve a en-progreso para fix1 con TDD. La ventana de revisión se cierra antes de la corrección; consumo estimado, horas/tokens/coste reales desconocidos. QA y cierre siguen pendientes.
