# Revisión de dos lentes — intento 2: contrato del store del journal

ROOT 2026-10-11T15:29:24.916384+00:00: A/B frescas,0Critical/Important/Minor. A01Important del intento1 corregido con seis referencias canónicas; no cambio contractual. Scope4docs,0fuera/avisos/exclusiones,C/DautoFalse. Originalreview20/FIX21/review2intactos. Architect entregó propuesta readonly y ROOT aplicó FIX1; autoría explícita. Producto nativo,fullchainS1,bootstrap,lifecycle,ACK,causalrecovery y ext4 siguen pendientes. T05/M1abiertos; QA documental independiente siguiente.

| # | Grado anterior | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Referencias privadas rotas | T-05 | corregido FIX1/review2 | A6/6refs y3/3integración; B6/6; cuerpoD76+ exacto |

## Lente A

Lente A · intento 2 de 3 · diff `eeebe6b2b0043361debac48809c3d2aa2d3abaf3...HEAD ∪ dirty` (4 documentos). Diff completo leído por tramos; reevaluación limitada a FIX1.

**A01 corregido. Gaps actuales: 0 Critical / 0 Important / 0 Minor.**

Rutas relativas a `snapshot/`. D = `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md`; ADR = `docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md`.

| Criterio (T-05 / objetivo) | ✓/✗/no verificable | Evidencia propia |
|---|---|---|
| A01: referencias frontmatter y enlaces canónicos | ✓ | Resolución ejecutada: **6/6** existentes dentro del snapshot; D:7,9–10,74; ADR:10,36 |
| Integración diseño↔ADR e índice | ✓ | Resolución ejecutada: **3/3** aristas añadidas válidas; índice ADR y `storage-durable-design.md:482` |
| FIX1 limitado a corrección autorizada | ✓ | Comparación ejecutada: únicos spans D:7,9–10,38,74 y ADR:10,36 |
| Alcance documental | ✓ | Recibo congelado: 4 en alcance, 0 fuera, 0 avisos; `tasks.md:208` declara destinos |
| T-05 abierta; sin cierre ni verificación ficticia | ✓ | `tasks.md:202,215–217`; D:29; ADR:63 |
| CA: postproceso, traslado y manifiesto reales | no verificable | `tasks.md:215`: pendiente; diff documental |
| CA: ready, song.json y análisis dependiente | no verificable | `tasks.md:216`: pendiente |
| CA: limpieza propia y fallo de validación | no verificable | `tasks.md:217`: pendiente |
| O2 / S1 / G2 preservados | ✓ | D:42,54,58–60,158; cuerpo contractual desde D:76 idéntico al intento 1 |
| Capacidades nominales; token no concede autoridad | ✓ | D:81–101,107–119; aprobación anterior preservada |
| Ancla y todos los ancestros S1 | ✓ | D:123–146; sin cambios |
| Creación propia; sin adopción/SMOKE/overwrite | ✓ | D:148–154,190–194; sin cambios |
| ABI, arenas, modo, streams e I/O exacto | ✓ | D:158–184; sin cambios |
| J01: exclusión writer | ✓ | D:138,258; sin cambios |
| J02: read view/sharing | ✓ | D:110,137,259; sin cambios |
| J03: adquisición actual y CAS | ✓ | D:202–204,260; sin cambios |
| J04: cabecera/EOF/historia inmutables | ✓ | D:194,205,261; sin cambios |
| J05: ACK antes de efecto/completion | ✓ | D:209,215,262; sin cambios |
| J06: handles retenidos/revalidación | ✓ | D:133,182,202,207,263; sin cambios |
| J07: conteos exactos/bloques separados | ✓ | D:182,206–207,264; sin cambios |
| J08: cadena íntegra/rechazo de corrupción | ✓ | D:208,242–248,265; sin cambios |
| J09: poison/custodia/cierre sin retry scalar | ✓ | D:219–227,266; sin cambios |
| J10: replay exacto de toda cadena | ✓ | D:204,213,267; sin cambios |
| C0: cero escritura | ✓ | D:233; sin cambios |
| C1: parcial incierto conservado | ✓ | D:234,244,271; sin cambios |
| C2: sin COMMIT/efecto | ✓ | D:235,244; sin cambios |
| C3: PREPARE no constituye head | ✓ | D:236,244; sin cambios |
| C4: COMMIT parcial bloqueante | ✓ | D:237,244,271; sin cambios |
| C5: recuperación clean con nueva barrera | ✓ | D:238,244; sin cambios |
| C6: replay sin nuevo slot/efecto | ✓ | D:239; sin cambios |
| C7: commit y cleanup separados | ✓ | D:240,225–227; sin cambios |
| Probe parcial no fabrica positivo full-chain | ✓ | D:273–277; sin cambios |
| Bootstrap/lifecycle/recovery causal/ext4 siguen obligatorios | ✓ | D:248–250,279–281,321–327; plan congelado:84–92 |
| Constitución preservada | ✓ | Constitución:32,43–50; D:48,301; sin cambios contractuales |
| TDD/cobertura/QA futuros sin evidencia inventada | ✓ | D:254,269–281; no código añadido |
| Originales y snapshot preservados | ✓ | SHA-256 ejecutado: original review1 **20/20**, review2 **21/21**, cero discrepancias |
| Interop E2/E3 | ✓ | No aplica: diff no toca `commands/`, `agents/` ni `hooks/` |

Gaps:

| # | Grado anterior | Gap | Tarea | fichero:línea | Escenario concreto | Veredicto |
|---|---|---|---|---|---|---|
| A01 | Important | Referencias privadas rotas al publicar los bytes revisados | T-05 | D:7,9–10,74; ADR:10,36 | El layout canónico congelado ahora resuelve las seis referencias a spec, plan, diseño y ADR con hashes exactos | **Corregido** |

Lo ejecutado: auditoría en `.venv` gestionada, modo `-B`, sin escrituras → 21/21 y 20/20 hashes válidos; diff SHA-256 `e60bcff49510cc59a88fd8bdc1b5d5cc6c67b2627d9b88d60995c89542333076` exacto; referencias 6/6; integración 3/3; cuerpo contractual desde D:76 idéntico. `knowledge-find.py --tipo adr --tipo-tarea backend …` → exit 0, sin aciertos. Git no ejecutado conforme al despacho; revisado el diff suministrado.

Fuera de mi lente: semántica nativa y aceptación del producto siguen pendientes. Este veredicto acredita la corrección documental; no acepta T-05/M1.


## Lente B

Lente B · intento 2 de 3 · diff `eeebe6b2b0043361debac48809c3d2aa2d3abaf3...HEAD ∪ dirty` (4 documentos; FIX1 en 2).

**Sin defectos de corrección: 0 Critical / 0 Important / 0 Minor.** Diff completo leído por tramos; sólo se reevalúa lo corregido.

Rutas relativas al snapshot de revisión2. `D` = `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md`; `ADR` = `docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md`.

| Criterio (T-05 / objetivo) | Veredicto previo | ✓/✗/no verificable | Evidencia propia |
|---|---|---|---|
| Referencias corregidas conservan la asociación spec→plan→diseño→ADR | A01 Important; fuera de B | ✓ | D:7/9/10/74 y ADR:10/36; resolución propia: 6/6 destinos existentes dentro del snapshot |
| Corrección no concede aceptación o autoridad nueva | B1 sin defectos | ✓ | D:38/74 mantiene adopción pendiente; D:14/15 y ADR:12/13 mantienen revisión pendiente e implementación no liberada |
| Interfaces, capacidades, S1 y CAS | ✓ documental | ✓ conservado | Comparación línea a línea: D:76–333 idéntico al intento1; ningún cambio en adquisición, autoridad o API |
| J01–J10, poison, replay y ACK | ✓ documental | ✓ conservado | D:198–281 idéntico; ADR:38–65 idéntico. Sin evidencia nueva para reabrir lo aprobado |
| C0–C7 y recovery | ✓ documental | ✓ conservado | D:229–250 idéntico; conservación de colas bloqueadas y resolución causal pendiente |
| Integración documental mantiene límites del store | ✓ documental | ✓ | `storage-durable-design.md:481–485` idéntico; `docs/decisiones/README.md:119` conserva ADR-0081 como propuesta |
| Originales y fuentes congeladas | ✓ | ✓ | `Get-FileHash`: snapshot anterior 20/20 y actual 21/21 coinciden con sus recibos; cero discrepancias |
| Comportamiento nativo y receta access/Flush | no verificable | no verificable | D:184/323 y ADR:42 conservan testigo futuro obligatorio; esta revisión no ejecuta store ni prueba ACK |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| — | — | Sin defectos identificados | T-05 | — | — |

Lo ejecutado: lectura completa de `source.diff`, `fix-only.diff` y veredictos anteriores; hashes y comparación documental; resolución de seis referencias; `knowledge-find.py --tipo adr --tipo-tarea backend …` mediante entorno gestionado → exit0, sin aciertos. SHA-256 propio de `source.diff` coincide con `e60bcff49510cc59a88fd8bdc1b5d5cc6c67b2627d9b88d60995c89542333076`. Sin escrituras, Git, tests nativos o experimentos.

Fuera de mi lente: A determina el cierre formal de A01. Full-chain S1, bootstrap, lifecycle, recovery causal y ext4 permanecen pendientes; este veredicto documental no acepta T-05/M1.
