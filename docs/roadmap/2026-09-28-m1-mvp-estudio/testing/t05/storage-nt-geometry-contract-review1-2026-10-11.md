# Revisión documental — geometría NT readonly G2 — intento 1

ROOT 2026-10-11T11:51:55.162094+00:00: conformidad técnica de la propuesta, **0 Critical / 0 Important / 1 Minor**. Lentes frescas A+B; C/D auto no aplican al diff sólo documental. Scope oficial: cuatro documentos, cero fuera/avisos/exclusiones de usuario. Base privada `c529e57ae4ea8f841a3871767557a54a8e20a266`.

ROOT revalida 27 archivos del snapshot, 25 fuentes canónicas (tasks con delta propio registrado) y nueve copias primarias. Las tablas completas y la evidencia que declaran los revisores se conservan abajo. Esa evidencia documental no prueba ninguna ejecución de U2b2.

| Gap | Grado | Veredicto ROOT | Evidencia |
|---|---|---|---|
| A01: frase W1 demasiado larga | Minor | Anotado, no bloquea corrección técnica conforme adversarial-review §3 | storage-durable-design.md:415; docs-style regla1. No se afirma corregido. |

Contrato privado elegido G2, ADR-0078 propuesta. **QA documental y adopción siguen pendientes**. No hay implementación ni release U2b2, ni cierre T-05/M1. Continúan gates de geometría nativa, store/writer/ACK, confianza completa, ext4 persistente, recovery y E2E.

TDD n/a: prosa. Sin cobertura de producto medida por esta revisión. Métricas reales null; no nuevas horas/tokens/coste inventados. Jira/Confluence desactivados.

## Lente A — salida completa

Lente A · intento 1 · diff `c529e57ae4ea8f841a3871767557a54a8e20a266...HEAD` privado (4 ficheros). Diff completo leído por ficheros. **0 Critical, 0 Important, 1 Minor.**

Rutas abreviadas: `G` = `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-geometry-design.md`; `D` = `storage-durable-design.md` de esa iniciativa; `A78` = `docs/decisiones/ADR-0078-geometria-nt-readonly-del-journal.md`.

| Criterio (T-05 / objetivo documental U2b2) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| Alcance: cuatro documentos declarados | ✓ | `tasks.md:208`; `source.diff` → cuatro rutas, sólo documentación |
| G2 elegida; revisión/adopción/release separados | ✓ | `tasks.md:5007`; `G:11`, `G:15`, `G:17`; `A78:4` |
| Preservar O2/ADR-0075 y S1/ADR-0076 | ✓ | `G:48`, `G:55`; ADR-0075/0076 leídos; cambio focal `D:154` |
| No atribuir geometría a U2b1 aceptada | ✓ | `G:45`, `G:46`, `G:323` |
| T-05 CA1: postproceso/publicación atómica | no verificable | `tasks.md:215` pendiente; `G:54`, `G:348`: fuera de esta entrega documental |
| T-05 CA2: ready/snapshot/analysis | no verificable | `tasks.md:216` pendiente; diff sin implementación |
| T-05 CA3: limpieza propia y fallos | no verificable | `tasks.md:217` pendiente; diff sin implementación |
| No cerrar tareas ni sustituir su Verificación | ✓ | `tasks.md:202`, `tasks.md:5009`; ningún cierre reclamado |
| TDD n/a para prosa; RED futuro explícito | ✓ | `tasks.md:5009`; `G:295`, `G:322` |
| Dos queries diferenciadas sobre la misma adquisición | ✓ | `G:139`, `G:143`, `G:144`, `G:192` |
| ABI, tamaños y offsets implementables | ✓ | `G:160`–`G:185`; `_IoStatusBlock` existente en `scripts/storage_journal_windows.py:803`; fuentes Microsoft congeladas verificadas |
| Apertura readonly síncrona y derechos existentes | ✓ | `G:53`; `scripts/storage_journal_windows.py:604`, `:612`, `:629` |
| Wrapper propio, parent retenido y lock global | ✓ | `G:154`, `G:192`–`G:201`; módulo existente `:458`, `:506`, `:776` |
| Metadata antes/después con campos existentes | ✓ | `G:198`; `MetadataObservation` en módulo existente `:836`; política en `:718` |
| Retorno gobierna; IOSB adicional es política propia | ✓ | `G:213`–`G:224`; copia primaria `primary/iosb.html` leída |
| PENDING/posretorno: composite retenido, poison, sin close/retry | ✓ | `G:183`, `G:211`, `G:227`–`G:233`; `context.call/retain` existentes `:470`, `:476` |
| Sin éxito parcial ni payload con longitud incompleta | ✓ | `G:202`, `G:216`, `G:228` |
| Raw congelado y derivación pura sin autoridad | ✓ | `G:140`–`G:152`, `G:237`, `G:263` |
| Cuatro tamaños, máscara cerrada y validación previa | ✓ | `G:241`–`G:244`, `G:264`; primaria MS-FSCC de alineación leída |
| Flags NT separados de Win32; bits 4/8 independientes | ✓ | `G:245`–`G:258`, `G:275`; primaria MS-FSCC de sectores leída |
| Offsets unknown/nozero bloquean; restricción propia explícita | ✓ | `G:248`–`G:256`; `A78:44` |
| B compatible con wire U1; sin default4096 | ✓ | `G:253`, `G:266`; `scripts/storage_journal.py:95`–`:101`; `D:415` |
| Writer reacredita adquisición, modos, S1 y buffers | ✓ | `G:278`–`G:280`; candidato no habilita ACK |
| Nuevos casos de verificación exigidos, sin resultados inventados | ✓ | `G:298`–`G:323`: R01–R21; cobertura futura, sin porcentaje actual reclamado |
| Constitución: local, BD exclusiva, rutas, idioma y ADR/documento juntos | ✓ | `docs/CONSTITUTION.md:16`, `:32`, `:43`, `:63`, `:65`, `:73`; `G:53`–`G:58`, `G:148`; A78 + D en mismo diff |
| Sin ingreso de dependencia/código Microsoft ni licencia nueva implícita | ✓ | `G:77`, `G:336`–`G:341`; diff sólo documental |
| Enlaces nuevos y snapshot íntegros | ✓ | Comprobación readonly → `ADDED_LOCAL_LINKS count=3 missing=0`; `SNAPSHOT_HASHES count=27 mismatches=0` |
| Generados/interop E2–E3 | ✓ — no aplica | Diff sin `commands/`, `agents/` ni `hooks/`; ningún contrato generado modificado |
| Memoria técnica vinculante contradictoria | ✓ | `knowledge-find.py --no-index --tipo adr --tipo-tarea backend …` → sin aciertos, exit 0 |
| docs-style: regla 1, frases cortas | ✗ | `D:415` contiene una frase añadida de 43 palabras; regla citada en `docs-style.md:15` |
| docs-style restante aplicable | ✓ | Opciones/ABI/política/casos tabulados; ejemplos reales, voz activa y términos concretos. Regla bilingüe no aplica |

Gaps:

| # | Grado | Gap | Tarea | fichero:línea | Escenario concreto |
|---|---|---|---|---|---|
| A01 | Minor | Incumple docs-style, regla 1: una frase de 43 palabras acumula derivación, requisitos y rechazo | T-05/U2b2 documental | `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md:415` | Al consultar W1, el lector debe interpretar en una sola frase el máximo, divisibilidad, flags, offsets y bloqueo; supera ampliamente las ~25 palabras de `docs-style.md:15`. No afecta al contrato técnico. |

Lo ejecutado: hashes del snapshot **27/27**; enlaces locales añadidos **3/3**; hashes de las nueve copias primarias **9/9**; consulta de conocimiento readonly **exit 0, cero aciertos**; conteo de frase W1 **43 palabras**. El inventario general de enlaces encontró referencias históricas ausentes del snapshot parcial; se excluyeron del juicio y se comprobaron las incorporadas por el diff.

Límites: sin importación de producto/DLL, tests, probes, GPU, Docker, WSL, admin ni escrituras. Las futuras garantías nativas no quedan acreditadas por esta revisión.

Fuera de mi lente (no reportado): ninguno.


## Lente B — salida completa

Lente B · intento 1 · diff c529e57ae4ea8f841a3871767557a54a8e20a266…HEAD ∪ source.diff (4 ficheros). Diff completo revisado por ficheros. **Sin defectos: 0 Critical / 0 Important / 0 Minor.**

`G` = `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-nt-geometry-design.md`.

| Criterio (T-05/U2b2) | ✓/✗/no verificable | Evidencia |
|---|---|---|
| Firmas, clases y ABI | ✓ | G:158–181; firmas primarias congeladas de cinco argumentos; header Microsoft fijado:76 confirma clase11 |
| Retorno NTSTATUS gobierna; IOSB restrictivo | ✓ | G:210–224; ambos0 es política propia, sin reinterpretar errores. Contraste con [Microsoft IOSB](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ns-wdm-_io_status_block) |
| Information exacto y sentinels | ✓ | G:183–188,214–216; longitudes28/4 antes de payload; sin exigir cambios en cada byte |
| Composite y PENDING query1/query2 | ✓ | G:183–184,211–212,227–233; retención conjunta, poison y prohibición de outputs/close/retry |
| Incertidumbre posretorno | ✓ | G:219–225,308–309; distingue rechazo acreditado de excepción dentro del binding; freeze queda protegido |
| Ownership e identidad misma adquisición | ✓ | G:192–202; metadata por handle, parejas completas, volumen común y owner cooperativo; compatible con runtime congelado:491–503,661–746 |
| Tamaños, máscara y B | ✓ | G:241–244,253,264–267; límites compatibles con JournalLayout:95–97; [máscaras NT Microsoft](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/9b0b9971-85aa-4651-8438-f1c4298bcb0d) |
| Flags, offsets y causas | ✓ | G:245–263; bits4/8 independientes, unknown bloqueante y offsets0 como restricción propia; [flags/offsets Microsoft](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/3e75d97f-1d0b-4e47-b435-73c513837a57) |
| Frontera U2b1/O2/S1 y writer | ✓ | G:43–57,206,278–280; ADR0078:22–47; no capacidad, fallback ni aceptación heredada |
| Coherencia de los otros tres documentos | ✓ | ADR0078:28–47,66–67; storage-durable-design:154,376,390,415; índice:113; nueva autoridad y estado propuesta coherentes |

Gaps: **sin defectos**.

Lo ejecutado: `git status/rev-parse/diff --stat` → base correcta y cuatro documentos,438 adiciones/4 bajas; cotejo diff→snapshot →468 líneas añadidas/contexto consistentes; SHA256 →27/27 snapshot y9/9 primarias, diff exacto; enlaces →84 comprobados,8 destinos snapshot y76 canónicos preexistentes,0 ausentes; `knowledge-find` →exit0, sin aciertos. Persona backend aplicada.

Límites: revisión documental; sin importar runtime/DLL, tests ni probes U2b2. No acredita implementación, exportaciones nativas, host, store/writer/ACK, ext4 o aceptación M1.

Fuera de mi lente (no reportado): ninguno.
