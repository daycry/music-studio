# T-10 — revisión del prompt instrumental, intento 5

**Sin gaps nuevos: 0 Critical, 0 Important, 0 Minor.** Lentes A+B de contexto fresco; delta correctivo completo de cuatro archivos leído. Scope oficial exit0 sin avisos, info ni exclusiones. Selector automático C/D false. [Recibo](review5-receipt.json).

| Criterio | Resultado | Evidencia |
|---|---|---|
| Caption instrumental exacto y letra instrumental, ambas superficies | ✓ CPU | capabilities_plan.py:130–139; 18 combinaciones |
| Caption ausente, vacío o malformado | ✓ | ValueError explícito; seis regresiones |
| Otros casos, controles y semillas | ✓ | 12 casos; resto de producción intacto |
| TDD y cobertura del archivo cambiado | ✓ | RED24 y GREEN37; suite127; 54/55=98,1818 % |
| Alcance y constitución | ✓ | 59 fuentes actuales y cuatro cambios autorizados |
| R10-01…08 | ✓ preservados | sin evidencia nueva que reabra aprobados |
| Verificación musical integral | pendiente | T-10 sigue en-progreso, no verified ni cierre ficticio |

A ejecutó 37 pruebas dirigidas y B36, solapadas. Ambos JUnit sin fallos, errores ni omisiones, cotejados por root. A recibió aviso de opción cache_dir desconocida al desactivar cacheprovider: no fallo, no ocultado. No suite127 repetida ni GPU, modelos o audio por las lentes. Límites históricos de argv/exits y custodia exhaustiva de audio conservados.

R10-09 queda corregido CPU. Se conserva historia1–4: nuevo defecto detectado después de revisión limpia, no reinicio del bucle. QA4 independiente y ejecución instrumental real pendientes. Jira desactivado; knowledge fuera de alcance.
