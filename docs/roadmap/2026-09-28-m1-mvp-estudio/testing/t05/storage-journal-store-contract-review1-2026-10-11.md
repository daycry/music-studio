# Revisión contractual1 — store nativo Windows

ROOT 2026-10-11T14:55:23.433358+00:00: A/B frescas,0Critical/1Important/0Minor. A01 confirma enlaces privados noadaptados en los destinoscanónicos diseño/ADR. Sin rebate ni deuda; no contratoadoptado ni nativewriter probado. La organizaciónO2 sigueelegida, durableO2/S1/G2preservados.

| Gap | Grado | Veredicto | Corrección |
|---|---|---|---|
| A01 | Important | confirmado | Sustituir referenciasprivadas spec/plan/adr/fuente y enlaces por destinoscanónicos resolubles. |

ROOT verifica20fuentes/diff y preserva respuestas completas. ReviewAleyó plan delcheckout fuera desnapshot; FIX congelará esecontexto adicional actual explícito, no inventa pinretrospectivo. Store/bootstrap/lifecycle/recoverycausal/ext4/ACK/E2E siguenobligacionesfutureproducto, no cierreT05/M1porreview. C/DautoFalse5docs/0fuera/0avisos; no proofnativecallsde las páginasMicrosoft citadas.

## Lente A

Lente A · intento 1 · diff `1d77034c9f40e055df88ad6287650acde1a68275...HEAD ∪ dirty` (5 ficheros). Diff completo leído por tramos. Referencias relativas al snapshot de revisión.

| Criterio (T-XX / objetivo) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| T05: alcance documental declarado | ✓ | `tasks.md:208`; recibo: 5 en alcance, 0 fuera, 0 avisos |
| T05: estado y aceptación preservados | ✓ | `tasks.md:202,215–217`: en-progreso y tres CA pendientes; diseño:29 |
| T05: postproceso, traslado atómico y manifiesto reales | no verificable | `tasks.md:215`; este diff no implementa ni acredita producto |
| T05: ready, song.json y análisis dependiente | no verificable | `tasks.md:216`; obligación pendiente conservada |
| T05: limpieza propia y fallo de validación | no verificable | `tasks.md:217`; obligación pendiente conservada |
| Verificación de tarea cerrada | ✓ | Ninguna tarea pasa a completado; T05 continúa abierta |
| O2 interna conserva ADR-0075/O2, ADR-0076/S1 y ADR-0078/G2 | ✓ | Diseño:42,54,58–60,158 |
| Capacidades nominales; tokens/copias no fabrican autoridad | ✓ | Diseño:81–101,107–119 |
| Ancla, root real y todos los ancestros S1 | ✓ | Diseño:123–146; política S1:81,89 |
| Creación propia; sin adopción, SMOKE ni overwrite | ✓ | Diseño:148–154,190–194 |
| Kernel completo: ABI, modo, streams, arenas e I/O exacto | ✓ | Diseño:158–184; testigo de receta flush pendiente explícito |
| J01: exclusión writer READ/WRITE/DELETE | ✓ | Diseño:138,258 |
| J02: read view y sharing | ✓ | Diseño:110,137,259 |
| J03: reread/CAS; head readonly insuficiente | ✓ | Diseño:202–204,260 |
| J04: cabecera/EOF/slots previos inmutables | ✓ | Diseño:194,205,261 |
| J05: ACK antes de efecto/completion | ✓ | Diseño:209,215,262 |
| J06: handles retenidos y revalidación de cadena | ✓ | Diseño:133,182,202,207,263 |
| J07: conteos exactos y bloques disjuntos | ✓ | Diseño:182,206–207,264 |
| J08: cadena íntegra; rechazo de corrupción | ✓ | Diseño:208,242–248,265 |
| J09: poison, custodia y cierre sin retry scalar | ✓ | Diseño:219–227,266 |
| J10: replay exacto de toda cadena | ✓ | Diseño:204,213,267 |
| C0 | ✓ | Diseño:233: cero escritura |
| C1 | ✓ | Diseño:234,244,271: incertidumbre, clasificación y parcial real |
| C2 | ✓ | Diseño:235,244: conservación; sin COMMIT/efecto |
| C3 | ✓ | Diseño:236,244: PREPARE no constituye head |
| C4 | ✓ | Diseño:237,244,271: parcial bloqueante |
| C5 | ✓ | Diseño:238,244: sólo clean recuperable con nueva barrera |
| C6 | ✓ | Diseño:239: reacreditación y replay sin slot/efecto nuevo |
| C7 | ✓ | Diseño:240,225–227: commit y cleanup separados |
| Probe parcial sin bypass/promoción de trust | ✓ | Diseño:273–277 |
| Bootstrap/lifecycle/recovery causal/ext4 permanecen obligatorios | ✓ | Diseño:248–250,279–281,321–327; plan vigente:84–92 |
| Constitución: infraestructura separada de BD; datos dentro del proyecto | ✓ | Constitución:32,43–50; diseño:48,301 |
| TDD/cobertura y QA futuros, sin evidencia nativa inventada | ✓ | Diseño:254,269–281; `.claude/dev.json`:3,12 |
| Enlaces desde destinos canónicos futuros | ✗ | Comprobación `Test-Path`: cuatro destinos distintos ausentes |
| Original y snapshots preservados | ✓ | Hashes propios: original17/17, revisión20/20; original diseño coincide `d296448…`; diff `ee7c8c53…` |
| Interop E2/E3 | ✓ | No aplica: diff sólo de documentos; sin `commands/agents/hooks` |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto | CWE |
|---|---|---|---|---|---|---|
| A01 | Important | Referencias privadas pendientes de adaptación en los documentos destinados a canon; incumple requisito explícito y docs-style regla 5 | T05 | `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md:74`; `docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md:36` | Publicar los bytes revisados deja diseño→`adr-0081-proposal.md` y ADR→`selected-design.md` sin destino. También fallan `spec`, `plan`, `adr` del diseño (líneas7/9/10) y `fuente` del ADR (línea10). `Test-Path=False` tanto desde snapshot como desde destino canónico futuro. La promesa de adaptación posterior en diseño:38 no verifica esos enlaces en esta entrega. | — |

Lo ejecutado: hashes SHA-256 → 17 originales y 20 de revisión sin discrepancias; original diseño y diff coinciden recibos; resolución de enlaces → seis referencias fallidas a cuatro destinos; `knowledge-find.py --tipo adr --tipo-tarea backend …` → exit0, sin aciertos. Plan leído del checkout vigente: no está congelado en el snapshot. Sin escrituras, Git, GPU, admin, instalaciones ni experimentos.

Fuera de mi lente (no reportado): pruebas nativas, corrección de bindings y aceptación física del producto quedan pendientes; los ✓ anteriores acreditan definición documental.


## Lente B

Lente B · intento 1 · diff `1d77034c9f40e055df88ad6287650acde1a68275...HEAD ∪ dirty` (5 ficheros, 451 líneas).

**Sin defectos de corrección: 0 Critical / 0 Important / 0 Minor.** Los ✓ acreditan coherencia documental del contrato; no ejecución del store futuro.

Rutas relativas al `snapshot/` indicado. `D` = `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md`.

| Criterio (T-05 / objetivo) | ✓/✗/no verificable | Evidencia leída |
|---|---|---|
| Interfaces cerradas y capacidades | ✓ | D:80–123: registro/owner/nonce; tokens y snapshots no conceden autoridad; lifecycle separado |
| ABI y arenas alineadas | ✓ | D:166–182: tamaños x64, firmas, base original, overflow y conteos exactos; contraste con [NtReadFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntreadfile), [NtWriteFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntwritefile) y [VirtualFree](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-virtualfree) |
| J01–J02: sharing bilateral | ✓ | D:139–144,258–259: writer share=0 y readers SHARE_READ; [NtCreateFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntcreatefile) |
| J03: CAS actual | ✓ | D:99–101,202–205: adquisición actual, token completo, reread; expectativa readonly no autoriza append |
| J04: inicialización e inmutabilidad | ✓ | D:188–194,205: cero físico, EOF fijo, cabecera y slots previos conservados; incompleto no sobrescrito |
| J05: barreras y ACK | ✓ | D:206–215: PREPARE→flush→read; COMMIT→flush→read→Seal; efecto y completion requieren ACK propios |
| J06: trustchain y handles retenidos | ✓ | D:127–154,158–164: ancla ratificada, adquisición relativa, S1 completa, geometría del mismo owner |
| J07: buffers/counts/bloques | ✓ | D:180–182,206–207: alineación B, offset explícito, short count bloqueante, PREPARE/COMMIT disjuntos |
| J08: cadena completa | ✓ | D:242–248; `scripts/storage_journal.py:833–902`: incomplete/corrupt no deja head operativo ni sucesor |
| J09: ownership/poison/cleanup | ✓ | D:219–227: registro anterior a llamada, recursos retenidos ante incertidumbre, scalar no repetido, commit/cleanup separados |
| J10: replay histórico | ✓ | D:204,213,239–240; `scripts/storage_journal.py:928–943`: búsqueda completa, conflicto de bytes, barrera nueva, cero slot/efecto adicionales |
| C0–C7 y fronteras pendientes | ✓ | D:233–250,269–281: clasificación conservadora, kill/reap real futuro; resolución causal independiente pendiente |
| Probe parcial sin ACK de producto | ✓ | D:273–277: sin promoción probe→ChainLease/writer ni bypass S1 |
| Receta exacta access/Flush y comportamiento nativo | no verificable | D:184,254,308,323 exige testigo futuro y cierre sin fallback. [FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers) documenta GENERIC_WRITE; el documento reconoce expresamente la frontera |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| — | — | Sin defectos identificados | T-05 | — | — |

Lo ejecutado: lectura completa dividida por documentos/secciones; `Get-FileHash` → **20 fuentes coinciden** y diff SHA-256 `ee7c8c53e320c6f679d9c20913daf86312852df6ec8a3e02c02889c52ac16915` exacto; consulta `knowledge-find.py` → exit 0, sin aciertos; contraste con Microsoft Learn. Sin escrituras, tests nativos, instalaciones o experimentos.

Fuera de mi lente: enlaces privados/canónicos ya señalados por A. Bootstrap legacy, lifecycle, recovery causal completo, provisión S1 y ext4 siguen pendientes explícitos; este veredicto no acepta T-05/M1.
