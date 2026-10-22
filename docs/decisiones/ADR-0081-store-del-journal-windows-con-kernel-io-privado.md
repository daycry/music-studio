---
id: ADR-0081
titulo: Store del journal Windows con kernel I/O privado
estado: aceptada
fecha: 2026-10-11
iniciativa: 2026-09-28-m1-mvp-estudio
opcion: O2
elegida_por: ROOT bajo delegación vigente del propietario
eleccion_utc: '2026-10-11T14:39:03.061125+00:00'
fuente: ../roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md
privado: false
revision_documental: aceptada; revisión2 A/B y QA95checks
implementacion: no liberada
canonical_target: docs/decisiones/ADR-0081-store-del-journal-windows-con-kernel-io-privado.md
canonical_design_target: docs/roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md
generacion:
  fuente: estimado
  medidor: ROOT
  tokens: null
  coste: null
  horas_ia: null
---

# ADR-0081 · Store del journal Windows con kernel I/O privado

## Contexto

ADR-0075/O2 fija journal estable, intención durable, PREPARE/COMMIT y ACK. ADR-0076/S1 exige cadena de confianza completa. ADR-0078/G2 aporta geometría readonly sin autoridad de writer. Las tres decisiones permanecen aceptadas.

`scripts/storage_journal.py` implementa el codec U1. `scripts/storage_journal_windows.py` implementa observaciones readonly U2 aceptadas. Falta construir adquisición writable, arenas alineadas, I/O exacto, CAS y ACK sin ampliar esas capacidades retrospectivamente.

## Decisión

ROOT eligió organización **O2** el 2026-10-11 bajo delegación vigente del propietario: separar `scripts/storage_journal_windows_io.py` y `scripts/storage_journal_store.py`.

El primer módulo será el kernel privado propietario de adquisiciones nativas y arenas. El segundo acreditará trust, tokens, snapshots, CAS, PREPARE/COMMIT, ACK y clasificación de recovery. El [contrato seleccionado](../roadmap/2026-09-28-m1-mvp-estudio/storage-journal-store-design.md) fija las interfaces, estados, J01–J10 y cortes C0–C7.

RootContext/ChainLease nacen sólo de adquisiciones actuales y contexto deployer ratificado. Snapshots, hashes, tokens o dicts no conceden autoridad. `GatedNativeProbe` permite demostrar I/O sobre objetos nuevos propios liberados después de revisión; devuelve evidencia parcial y nunca ACK o ChainLease de producción.

El store conserva U1 y su rechazo de colas incomplete/corrupt. Sólo una cadena clean con request exacto sellado puede recuperar ACK mediante barrera y revalidación nuevas. La resolución causal de una cola bloqueada necesita otra concreción; no se salta, rellena o legitima historia con este ADR.

La receta de acceso específico sin APPEND_DATA y FlushFileBuffers mantiene un gate nativo exacto antes del ACK. Microsoft documenta GENERIC_WRITE para flush y la incompatibilidad de APPEND_DATA con no-buffering NT. Si el testigo no acredita la receta, se concreta la frontera antes de admitir escritura operativa; no hay fallback de derechos o buffering. [Microsoft: FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers), [NtCreateFile](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntcreatefile).

## Alternativas descartadas

- **O1, store integrado en el módulo Windows:** viable con las mismas garantías, pero concentra cambios writable/trust/recovery sobre observación U2 aceptada.
- **O3, proceso dedicado propietario e IPC:** viable como aislamiento, pero agrega autenticación, framing, respuestas perdidas y reap a la misma exigencia nativa.

O2 separa custodia del kernel de semántica CAS/ACK y permite conservar los contratos readonly aceptados. No reduce pruebas ni alcance del store frente a las alternativas.

## Consecuencias

La implementación añade módulos y pruebas nuevos. Conserva wire U1, `StorageReceipt` v1, `ReceiptLease` y `PublishedDiskBinding`. El controller futuro retirará writers JSON por ruta sólo tras concretar y verificar cada wiring.

Bootstrap legacy, lifecycle, admisión y resolución causal independiente siguen como trabajo pendiente exigido. El rechazo conservador de una cola es un comportamiento parcial; no sustituye recovery persistente del producto final. La aceptación de T05/M1 necesita además cadena S1, ext4/UUID y efectos físicos reales, startup, recovery y backup/restauración.

El host actual conserva grants MODIFY outsider en ancestros y no acredita una cadena positiva. Un leaf propio protegido no los corrige. ROOT deberá ratificar la provisión concreta que permita S1; remediar ACL existentes requiere decisión específica y no forma parte de esta elección.

ACK acredita barreras e identidades observadas bajo las precondiciones del contrato. No promete durabilidad absoluta frente a powerloss ni atomicidad entre journal, rename y montaje. Las pruebas de subprocess no sustituyen reinicio de host o ensayos físicos.

## Estado

`propuesta` — organización O2 seleccionada por ROOT; revisión/QA documental y adopción canónica pendientes. Esta decisión privada no libera implementación, experimentos, bootstrap, plataforma elevada ni aceptación T05/M1.

Una vez revisado el contrato, la delegación vigente permite a ROOT liberar pruebas propias reversibles. Los efectos reales de plataforma y la remediación de ACL requieren sus gates concretos. ROOT publicará los destinos indicados en frontmatter y registrará el índice canónico, sin modificar el diseño original o snapshot de esta pasada.


## Acta de adopción ROOT — 2026-10-11T15:37:47.375671+00:00

Revisión2A/B0gaps yQA documental95/95,gateverde; ROOTverifica60payload/21fuentes/19guardascanónicas/2seams/7tools. ContratoO2incorporado, sin implementación ni evidencia nativeFlush/ACK/fullchainS1/bootstrap/lifecycle/causalrecovery/ext4/E2E/manuales. Esos gates siguen obligatorios. Implementación futura sólo por unidad liberada yTDD/revisión/QA; no cierreT05/M1. Originales privados íntegros.
