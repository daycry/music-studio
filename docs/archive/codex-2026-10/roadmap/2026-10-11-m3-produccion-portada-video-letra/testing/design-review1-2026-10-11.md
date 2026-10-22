# Revisión arquitectónica1 — M3 producción y N0

ROOT 2026-10-11T14:52:47.528185+00:00: A/B frescas,0Critical/Important y1Minor A01 de estado textual de spec. Sin recortes del alcance49CA/14funciones ni capacidades reales atribuidas. Modo sin plan: aún no existe ledgerM3; se revisan spec aprobada/Constitución/ADRs y objetivo delegado, no tareas completadas.

| Gap | Grado | Veredicto ROOT | Acción |
|---|---|---|---|
| A01 | Minor | confirmado, sin rebate | CopiaQA de spec expresa decisiónO1 aprobada con adopción y plan pendientes; fuentesreview1 intactas. |

ROOT verifica49entradas de pins que corresponden48archivos únicos: la spec tenía separadores / y\ en el inventario de preparación. La duplicación de referencia no altera bytes; auditorB reporta48únicos y A49entradas. Este diagnóstico se preserva sin atribuirlo a defecto de arquitectura. Sólo4documentos cambiados, C/DautoFalse. AuditorA119enlaces/49CAfuturos0marcados, Bcontrasta seams reales sinproductQA. Respuestas completas siguientes, originales intactas; QA independiente y adopción pendientes.

## Lente A

Lente A · intento 1 · diff `de586bb8c408a23aa056788f0168dd120dab42ad...HEAD ∪ dirty` (4 ficheros).

**0 Critical · 0 Important · 1 Minor.** Diff completo leído por fichero. Revisión documental: ✓ significa cobertura arquitectónica conservada; ningún ✓ acredita implementación o aceptación del producto.

Localizadores del snapshot `.cache/dev-cycle/m3/production-design-review1-20261011/snapshot/`:

- `design.md` y `spec.md`: `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/`.
- `ADR-0080`: `docs/decisiones/ADR-0080-produccion-por-derivados-tipados-y-escena-n0-local.md`.
- `CONSTITUTION.md`: `docs/CONSTITUTION.md`.

| Criterio / objetivo | ✓/✗/no verificable | Evidencia |
|---|---|---|
| Alcance íntegro, alternativas y elección delegada | ✓ | `design.md:74`, `design.md:137`, `design.md:219`; O1/O2 comparadas, 14 funciones conservadas. |
| CA-01 · aceptación condicionada | ✓ | `design.md:244`, `ADR-0080:97`; cierre M2 y heredados obligatorio. |
| CA-02 · contexto inmutable | ✓ | `design.md:245`, `ADR-0080:32`. |
| CA-03 · capacidad no verificada | ✓ | `design.md:246`, `design.md:129`. |
| CA-04 · derechos/consentimiento | ✓ | `design.md:247`; spec normativa conservada. |
| CA-05 · validación de uploads | ✓ | `design.md:248`, `design.md:169`. |
| CA-06 · stems como assets | ✓ | `design.md:249`, `design.md:145`. |
| CA-07 · conformidad real stems | ✓ | `design.md:250`, `design.md:323`; métrica propuesta y escucha pendientes. |
| CA-08 · mixer persistente y controles | ✓ | `design.md:251`, `design.md:145`. |
| CA-09 · mezcla y padres reales | ✓ | `design.md:252`, `design.md:149`. |
| CA-10 · comparación preview/export | ✓ | `design.md:253`, `design.md:323`. |
| CA-11 · medición final por destino | ✓ | `design.md:254`, `design.md:151`. |
| CA-12 · original/ZIP stems | ✓ | `design.md:255`, `design.md:153`. |
| CA-13 · metadatos y letra histórica | ✓ | `design.md:256`, `design.md:153`. |
| CA-14 · export no conforme | ✓ | `design.md:257`, `design.md:151`; rechazo medido preservado. |
| CA-15 · familias de análisis | ✓ | `design.md:258`, `design.md:155`. |
| CA-16 · fallos parciales honestos | ✓ | `design.md:259`, `design.md:155`. |
| CA-17 · contraste independiente | ✓ | `design.md:260`, `design.md:324`. |
| CA-18 · binding textual histórico | ✓ | `design.md:261`, `design.md:157`. |
| CA-19 · karaoke/LRC/SRT/seek | ✓ | `design.md:262`, `design.md:157`. |
| CA-20 · revisión temporal propia | ✓ | `design.md:263`, `design.md:157`. |
| CA-21 · alineación cantada real | ✓ | `design.md:264`, `design.md:331`; anotación y revisión humana pendientes. |
| CA-22 · generación múltiple/selección | ✓ | `design.md:265`, `design.md:159`. |
| CA-23 · edición por referencia | ✓ | `design.md:266`, `design.md:159`; gate separado de generación. |
| CA-24 · imagen propia/fondo | ✓ | `design.md:267`, `design.md:159`. |
| CA-25 · Comfy Docker/CUDA real | ✓ | `design.md:268`, `design.md:329`. |
| CA-26 · palabra sincronizada N0 | ✓ | `design.md:269`, `design.md:161`. |
| CA-27 · reactividad/seek/silencio | ✓ | `design.md:270`, `design.md:163`. |
| CA-28 · render completo y reproducción | ✓ | `design.md:271`, `design.md:165`, `design.md:167`. |
| CA-29 · rendimiento canción completa | ✓ | `design.md:272`, `design.md:325`; Libre 4:15 incluida, objetivo previo obligatorio. |
| CA-30 · audio propio con linaje | ✓ | `design.md:273`, `design.md:169`. |
| CA-31 · utilidad musical real | ✓ | `design.md:274`, `design.md:328`; integración y escucha pendientes. |
| CA-32 · modo alta calidad comprobado | ✓ | `design.md:275`, `design.md:169`. |
| CA-33 · comparación emparejada | ✓ | `design.md:276`, `design.md:169`. |
| CA-34 · preset congelado por uso | ✓ | `design.md:277`, `design.md:171`. |
| CA-35 · preset incompatible | ✓ | `design.md:278`, `design.md:171`. |
| CA-36 · cierre portable multiversión | ✓ | `design.md:279`, `design.md:173`. |
| CA-37 · import malicioso/sin parcial | ✓ | `design.md:280`, `design.md:175`, `design.md:326`. |
| CA-38 · colisiones/replay/remapeo | ✓ | `design.md:281`, `design.md:177`; autoridad local separada de evidencia original. |
| CA-39 · privacidad/autoridad inerte | ✓ | `design.md:282`, `design.md:173`. |
| CA-40 · corte SQLite/assets | ✓ | `design.md:283`, `design.md:179`; mantenimiento nuevo, no garantía del coordinador actual. |
| CA-41 · restauración útil y jobs inertes | ✓ | `design.md:284`, `design.md:183`. |
| CA-42 · fallo/rollback/preservación | ✓ | `design.md:285`, `design.md:185`. |
| CA-43 · recuperación biblioteca real | ✓ | `design.md:286`, `design.md:331`. |
| CA-44 · recovery por fronteras | ✓ | `design.md:287`, `design.md:189`, `design.md:191`. |
| CA-45 · ext4/UUID/publicación real | ✓ | `design.md:288`, `design.md:70`. |
| CA-46 · residencia/VRAM/Ollama | ✓ | `design.md:289`, `ADR-0080:77`; restaura sólo intervención propia. |
| CA-47 · offline/privacidad/eventos | ✓ | `design.md:290`, `ADR-0080:101`; spec restricciones conservadas. |
| CA-48 · procedencia/versiones/compatibilidad | ✓ | `design.md:291`, `design.md:64`, `design.md:322`. |
| CA-49 · niveles de aceptación separados | ✓ | `design.md:292`, `ADR-0080:99`. |
| Constitución: canción/takes/autoridad/Docker/cola/local | ✓ | `CONSTITUTION.md:16`, `:18`, `:19`, `:31`, `:32`, `:35`; diseño `:43`, `:68`, `:145`, `:149`, `:159`, `:179`. |
| Constitución: versiones/migraciones/pesos/licencias | ✓ | `CONSTITUTION.md:37`, `:39`, `:41`, `:53`, `:69`; diseño `:64`, `:72`, `:199`, `:322`, `:328`, `:329`. No amplía la excepción SQL ni habilita candidatos. |
| Descripción vigente del estado del diseño | ✗ | `spec.md:8` enlaza diseño; `spec.md:26–27` todavía lo declara pendiente frente a `design.md:4`, `:29`. A01. |
| Enlaces desde destino canónico | ✓ | Comprobación propia → `canonical-target links=119 broken=0`, exit 0. |
| Fidelidad snapshot/diff/criterios | ✓ | Comprobación propia → 49 hashes correctos, 4 documentos, 49 CA únicos, 14 funciones; 49 CA futuros y 0 marcados. |
| Plan/ledger, tareas cerradas y verificaciones | no verificable · n/a | No existen todavía: `tasks_exists=False plan_exists=False`. Ninguna tarea se declara cerrada. |
| Producto, cobertura y conformidad de capacidades | no verificable | `design.md:315`, `:333`; contratos, pins, métricas, instalación, integración, GPU y aceptación permanecen pendientes. |
| Interop generado | ✓ · n/a | Ninguno de los cuatro documentos toca `commands/`, `agents/` o `hooks/`. |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto | CWE |
|---|---|---|---|---|---|---|
| A01 | Minor | Cuerpo de la spec conserva el estado anterior del diseño | Objetivo arquitectónico M3 | `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/spec.md:26` | Tras enlazar `design.md`, un lector del encabezado recibe «Diseño pendiente», mientras el documento enlazado declara O1 aprobada como decisión y adopción canónica pendiente. No implica aceptación M3. ROOT reconoce la discrepancia, sin rebate. | — |

Lo ejecutado: lecturas UTF-8 y búsquedas `rg`; auditor PowerShell de hashes, alcance, CA y enlaces → exit 0, `49/49`, `4 documentos`, `49 CA únicos`, `14 funciones`, `119 enlaces/0 rotos`, `0 CA marcados`. SHA del diff: `bb2654153cedb3a62bda00526209b865a7046d0bd5c6f8f864ed480965bd2f72`. `knowledge-find.py --tipo adr --tipo-tarea docs --contexto "M3 producción portada vídeo letra" --iniciativa m3-produccion-portada-video-letra`, con Python gestionado `-B` → exit 0, sin aciertos; aplicados Constitución y ADR explícitos leídos. Sin escrituras ni ejecución de producto; Git no ejecutado por restricción del despacho. No se identificaron infracciones citables adicionales de `docs-style`.

Fuera de mi lente (no reportado): sin hallazgos adicionales. Viabilidad, rendimiento y calidad audiovisual requieren los gates futuros declarados.


## Lente B

Lente B · intento 1 · diff de586bb8c408a23aa056788f0168dd120dab42ad…HEAD ∪ dirty (4 documentos; snapshot congelado, sin Git)

`D` = `docs/roadmap/2026-10-11-m3-produccion-portada-video-letra/design.md`; `R` = `docs/decisiones/ADR-0080-produccion-por-derivados-tipados-y-escena-n0-local.md`. Líneas verificadas en el snapshot recibido. ✓ significa consistencia arquitectónica documental, no aceptación funcional.

| Criterio / objetivo | ✓/✗/no verificable | Evidencia leída o ejecutada |
|---|---|---|
| Contexto congelado, dependencia M2 y capacidades/derechos (CA01–05) | ✓ | D:45,78,189,244; R:32. No retargeteo por cambios posteriores ni habilitación por fixtures. |
| Stems, mezcla reproducible y linaje (CA06–10) | ✓ | D:145,147,149,323. Transporte común, ganancias efectivas, mute/solo definidos y fuentes preservadas. |
| Export, LUFS/TP, original y metadatos (CA11–14) | ✓ | D:151,153,323; R:58. Medición final decodificada y rechazo explícito cuando ambos objetivos son incompatibles. |
| Análisis y alineación histórica/revisable (CA15–21) | ✓ | D:155,157,324. Resultados parciales independientes, revisiones sin sobrescritura y segmentación sin truncar a180s; límite confirmado en descriptor. |
| Comfy/upload, audio propio, calidad alta y presets (CA22–25,30–35,46) | ✓ | D:159,169,171,328–330. Autoridades reales, captura por uso y gates separados; ACE sólo declara song/instrumental no verificados. |
| N0 offline, reactividad y sincronización (CA26–29) | ✓ | D:161,163,165,167,325. Audio efectivo, tiempo explícito, seek reproducible y canción completa; pin/codec/rendimiento pendientes. |
| Portable/import íntegro y sin promoción parcial (CA36–39) | ✓ | D:173,175,177,326. Cierre completo, transacción posterior a medios, intención propia y evidencia histórica separada del remapeo. |
| Backup/restore/activación y recovery (CA40–45) | ✓ | D:179,181,183,185,191,327. Corte exclusivo, mutadores detenidos, custodia reconciliada y binding durable con rollback; backup.py actual sólo cubre SQLite. |
| Offline, procedencia CPU, compatibilidad y niveles de evidencia (CA47–49) | ✓ | D:64,68,70,202,208,322,333; R:38,40,103. Namespace independiente de ocho operaciones M2 y sin autoridad de inferencia ficticia. |
| Calidad musical/audiovisual, tiempos, GPU y recuperación real | no verificable | Son gates futuros explícitos; este diff documental no contiene implementación ni evidencia real de esas capacidades. |

Gaps: **sin defectos de corrección encontrados** — 0 Critical / 0 Important / 0 Minor.

Lo ejecutado: SHA256 **48/48 archivos únicos coinciden**, hash de `source.diff` coincide; **49CA** idénticos entre spec/design y **14 funciones únicas**. Lectura completa del diff dividida por documentos; contraste readonly de modelos, chains, planning/execution, backup, snapshots, timeline-v1, Constitución y ADR0074/0077/0069. `knowledge-find.py --tipo adr --contexto … --iniciativa m3-produccion-portada-video-letra` → exit0, sin aciertos. Sin escrituras ni pruebas de producto.

Fuera de mi lente: contradicción de estado textual «diseño pendiente» en spec, ya asignada a A; no incorporada a estos gaps.
