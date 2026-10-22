# T11 — Revisión2/3

A/B/D independientes, selectorCfalseDtrue; root verifica cinco fuentes y los paquetes originales.0Critical1Important1Minor. R11-01..05 muestran corrección estática; no acreditan QA ni trabajo real pendiente de la tarea.

| ID | Grado | Evidencia | Escenario | Estado |
|---|---|---|---|---|
| R11-07 | Important | B2-01, run.py:336,219 | El timeout de lectura1s cancela un job válido tras pausa de2s, pese a disponer60s globales; /v1 no exige heartbeat1s. | Pendiente reproducción |
| R11-06 | Minor previo | D, metrics.py:219 | Verifica repetidamente FFmpeg por fila. | Pendiente |

Originales [A](review2-a.md),[B](review2-b.md),[D](review2-d.md). La siguiente revisión será3/3, sin reset. QA, GPU, corpus cantado, suelo WER,30tomas y valoración siguen pendientes; T11/M0 no cerrados.
