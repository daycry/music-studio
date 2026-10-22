# Revisión de dos lentes — intento privado 1: piloto T-09

A+B+D frescas revisan únicamente el ejecutor privado y sus pruebas. Los cuatro defectos previos B4-L01–04 están corregidos en CPU. **Queda un Important B-L05**: al fallar Docker start con contenedor propio detenido, el GET de salud de la recuperación falla antes de llegar al cleanup existente. No se han ejecutado prepare/run reales ni GPU.

| ID | Grado | Tarea | Estado | Evidencia |
|---|---|---|---|---|
| B4-L01–04 | Important anterior | T-09 laboratorio | corregidos CPU | A11 y B16 dirigidos, solapados con27; cobertura completa170/184=92,3913% |
| B-L05 | Important | T-09 laboratorio | pendiente | autonomous-pilot-root.py:335; start falla/GET TRANSPORT_UNAVAILABLE: cleanup_calls0, contenedor detenido sin retirar y lease conservado |

La reproducción B ejecuta run() completo con el rig CPU y falla una aserción de recuperación (exit1, 00:21:49.6998616–00:21:49.9429658Z). La misma primitiva real DockerBackend.cleanup con procesos/HTTP simulados reconoce ownership y procesos muertos y retira el contenedor. A nominal no cubrió ese transporte indisponible; el caso específico B prevalece. D no detecta degradación introducida. Fuentes64 y documentos12 intactos. Los originales de revisión son mensajes de agentes de solo lectura; esta publicación es síntesis del orquestador.

Los criterios de producto O1/O2/O3/O4/O4a/O4b/O5 siguen aprobados; no se reabren sin evidencia nueva. D se despachó fresco después de A/B por capacidad, sin reutilizar contexto. QA independiente y piloto GPU siguen pendientes. No se suman tests dirigidos solapados. Incidentes instrumentales y de decodeBOM se conservan en recibo. Siguiente: RED propio para B-L05 → corrección acotada → revisión privada2 → QA CPU independiente → piloto real.
