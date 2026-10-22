**Lente A: sin gaps Critical/Important/Minor demostrados en esta unidad parcial.** T-04 continúa `en-progreso`; esta revisión no acredita su cierre ni aceptación técnica. Revisión exclusivamente estática del paquete INLINE, sin herramientas ni ejecución propia.

| T-04 → criterio de aceptación | ✓/✗ | Conclusión |
|---|---|---|
| CA1: carriles, concurrencia, prioridad/FIFO y `not_before` | ✗ Pendiente | Fuera de esta unidad; casilla abierta en `tasks.md:183`. |
| CA2: `EngineBackend` y cliente HTTP `/v1` | ✗ Pendiente | No implementados ni declarados completos (`tasks.md:184`). |
| CA3: cadena generación → post → beats | ✗ Pendiente | No implementada ni declarada completa (`tasks.md:185`). |
| CA4: resolver por tarea verificada | ✗ Pendiente | Reservado para próxima unidad (`tasks.md:186`). |
| CA5: descarga y comprobación de VRAM | ✗ Pendiente | Sin ejecución GPU ni aceptación inferida (`tasks.md:187`). |
| CA6: consumo NDJSON, cursor y bus SSE | ✗ Pendiente | Persistir cursor/terminal no demuestra consumo ni efectos transaccionales (`tasks.md:188`). |
| CA7: reintentos y offload | ✗ Pendiente | El esquema prepara intentos; no implementa la política (`tasks.md:189`). |
| CA8: recuperación, reconciliación y reintento manual | ✗ Pendiente | Conservación estructural implementada; recuperación ejecutable futura (`tasks.md:190`). |

Los ocho ✗ representan trabajo explícitamente pendiente, **no defectos ni cierres falsos**.

| Criterio transversal A | Resultado | Evidencia y valoración |
|---|---|---|
| Implementación del alcance parcial declarado | ✓ | `models/__init__.py:447` introduce la relación tipada; `job_attempt_invariants.py:95` valida identidad y terminal; `0005_job_attempt.py:20` instala la ampliación. Corresponde a ADR-0043:10–24 y `tasks.md:193`. |
| Alcance y `Archivos` | ✓ | Los ocho ficheros corresponden a modelos, migraciones, snapshots, ambas copias contractuales y tests declarados en `tasks.md:177`. El ajuste histórico a `0004` en `test_review_fix3_t02.py:310` conserva el objetivo del test; el ciclo actual sigue comprobando `head == 0005` en `test_job_attempt_schema.py:817`. |
| Tests con significado comprobable | ✓ | Lectura de pruebas de roundtrip tipado, rechazo SQL/ORM, reserva congelada, terminal/cursor, snapshots legados, soporte/procedencia, colisiones, invalidación, backup y ciclos nativos. Referencias: `test_job_attempt_schema.py:149`, `:307`, `:340`, `:398`, `:544`, `:659`, `:764`, `:846`. |
| Cobertura | ✓ Como apoyo | Recibo aportado: módulos completos **99,41 % / 93,51 % / 93,51 % / 100 %**, cero exclusiones. **No aporta porcentaje específico del diff**; no lo sustituyo por cobertura global. |
| Constitución explícita | ✓ | No observo violación de escritura exclusiva del server (`CONSTITUTION.md:32`), ampliación aditiva y baseline histórico (`:39`), contratos juntos (`:62`) ni confinamiento (`:43`). No cambia `/v1` ni introduce persistencia en engines. |
| Verificación de tareas cerradas | No aplica | T-04 no está cerrada ni tiene CA marcadas. La verificación de dispatcher en `tasks.md:180` permanece pendiente; los recibos parciales no la sustituyen. |
| Contratos y compatibilidad histórica | ✓ | Ambas copias contienen la ampliación opcional `job_attempt`; ausencia tratada como `[]` en `snapshots.py:231` y `:563`. Test de igualdad/legacy en `test_job_attempt_schema.py:489`. Se distinguen correctamente **20→21 tablas exportadas** y **23→24 entidades**. |
| Interop E2/E3 de commands/agents/hooks | No aplica | Ninguno de los ocho ficheros toca esas carpetas. |
| Comparación OpenAPI | Omitido | No hay modificación de una spec OpenAPI; los dos contratos modificados son JSON Schema. |

Evidencia de ejecución **aportada, no ejecutada por este revisor**: 89 casos nuevos; último recibo conjunto **97 pases** y suite BD/snapshots/migraciones **220 pases, 1 skip**, después del ajuste histórico explícito. Los ocho fallos anteriores quedan documentados.

**Gaps: ninguno demostrado.** Wheel/Docker y QA independiente permanecen pendientes; tampoco se acredita dispatcher, recuperación operativa, calidad musical ni aceptación final de T-04/M1.