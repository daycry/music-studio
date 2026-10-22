# Revisión de dos lentes — intento privado 2: piloto T-09

**A+B+D frescas: 0 Critical / 0 Important / 0 Minor.** B-L05 queda corregido en CPU: la inspección del contenedor detenido permite reutilizar cleanup con ownership y procesos muertos verificados, sin depender de una consulta HTTP imposible. Los controles de recurso activo, ajeno y estado incierto mantienen el bloqueo.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| B-L05 recuperación con transporte indisponible | ✓ CPU | autonomous-pilot-root.py:334–343; test_pilot.py:383–393 |
| Recursos activos/ajenos/inciertos | ✓ CPU | test_pilot.py:396–423; cleanup conserva assert_owner |
| Constitución/alcance/RED | ✓ | 64 fuentes y12documentos intactos; RED antes del cambio, suite32/coverage172of18692,4731% |
| Trabajo en recuperación | ✓ | Una inspección adicional fuera de bucles; sleep/cadencia no modificados |
| Producto O1–O5 y B4-L01–04 | aprobación preservada | Sin nueva evidencia que los reabra |
| QA y GPU | pendientes | Revisión CPU no cierra T-09 ni acredita matriz160 |

A ejecutó cinco casos dirigidos solapados con32; no se suman. B y D aportan sus mensajes originales en la recepción del orquestador. Por capacidad los despachos se completaron secuencialmente con contextos nuevos, sin omitir ni reutilizar lentes. Recibo derivado root; no atribuir al reviewer archivos que no escribió.

Siguiente: QA independiente de producto y ejecutor, documentación T-20 y puertas sin UI. Después, piloto real con originales nuevos y contexto previo; matriz160 sigue pendiente. No más lecturas manuales del propietario.
