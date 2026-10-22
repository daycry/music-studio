**Lente B · M0/T-11 · intento 3/3: sin nuevos defectos de corrección. R11-07 corregido por lectura estática.**

Revisé el delta y las seis fuentes completas INLINE, con las dependencias suministradas. Sin herramientas, tests propios ni comprobación de hashes; ejecuciones, cobertura y custodia son evidencia aportada por root.

| Criterio | Resultado y evidencia |
|---|---|
| R11-07: silencio legítimo dentro del plazo global | ✓ `run.py:359` permite reenganchar tras timeout de lectura mientras quede plazo. |
| Identidad y cursor al reenganchar | ✓ Conserva `job_id` y último `seq` validado (`run.py:334`, `:335`, `:351`); descarta el fragmento incompleto para recibirlo mediante replay. |
| POST único y ACK incierto | ✓ El reenganche queda dentro del GET de eventos; no repite submit ni altera su tratamiento (`run.py:313`, `:328`). |
| Deadline, validación y terminal | ✓ Mantiene comprobaciones por bloque/línea, propaga errores distintos de TIMEOUT y termina sin esperar EOF (`run.py:216`, `:343`, `:358`, `:360`). |
| Regresiones de R11-01…05 | ✓ Sin evidencia concreta nueva que invalide los veredictos anteriores. |
| Nuevas pruebas | ✓ Cubren pausa, fragmento descartado, expiración, UTF-8 dividido y límite de buffer. Sus resultados nativos son aportados, no ejecutados por esta revisión. |

**Defectos nuevos: 0 Critical, 0 Important, 0 Minor.**

| ID previo | Gravedad | Fichero:línea | Escenario y estado |
|---|---|---|---|
| R11-06 | Minor, lente D | `scripts/eval/metrics.py:219` | Normalizar 30 tomas repite 30 verificaciones completas del mismo FFmpeg. Sigue pendiente; no consta corrección ni aceptación de deuda. |

T-11 continúa **en-progreso**, con QA pendiente. Derechos/letras reales, integración GPU, corpus cantado y suelo ASR acreditados, 30 canciones y escucha humana siguen abiertos. El candidato CPU y el workflow sintético no satisfacen esos criterios.