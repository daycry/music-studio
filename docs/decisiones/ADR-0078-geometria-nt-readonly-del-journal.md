---
id: ADR-0078
titulo: Autoridad NT de geometría readonly y candidato B separado del writer
estado: aceptada
fecha: 2026-10-11
iniciativa: 2026-09-28-m1-mvp-estudio
opcion: G2
elegida_por: ROOT bajo delegación vigente del propietario
eleccion_utc: '2026-10-11T11:43:04.005269+00:00'
revision_documental: conforme A+B intento1; QA documental33/33 intento3
adopcion_canonica: ROOT 2026-10-11T12:16:41.617978+00:00
recomendada: G2
fuente: ../roadmap/2026-09-28-m1-mvp-estudio/storage-nt-geometry-design.md
privado: false
numeracion: 0078 libre verificada por ROOT antes de publicación
---

# ADR-0078 · Autoridad NT de geometría readonly del journal

## Contexto

ADR-0075/O2 fija el journal estable y ADR-0076/S1 fija su frontera de confianza. Ambas decisiones permanecen aceptadas.
U1 admite B potencia2 entre512 y65536. U2b1 aceptada excluye geometría; el diagnóstico Win32 Flags15 anterior no acredita bitsNT por similitud.
Necesitamos fijar la autoridad y la política geométrica antes del RED de U2b2, conservando sus límites readonly.

## Decisión aceptada tras revisión y QA documental

**ROOT eligió G2 el 2026-10-11T11:43:04.005269+00:00 bajo la delegación vigente del propietario: dos consultas NT diferenciadas sobre la misma adquisición propia retenida.**
`NtQueryVolumeInformationFile(FileFsSectorSizeInformation=11)` y `NtQueryInformationFile(FileAlignmentInformation=17)`.
Sus buffers fijos28/4bytes, IOSB y ownership siguen el contrato exacto de [contrato de geometría NT](../roadmap/2026-09-28-m1-mvp-estudio/storage-nt-geometry-design.md).
No se consulta Win32 para completar/reemplazar resultados fallidos. La geometría permanece independiente de S1 y del writer.

La lectura devuelve dos copias frozen con metadata antes/después. Exige retorno0, IOSB.Status sobrescrito0 e Information exacto28/4.
Exigir IOSB.Status0 además del retorno0 es política restrictiva de estas queries; Microsoft permite que ambos difieran y hace gobernar el retorno noPENDING.
No cambia la semántica de apertura U2b1 ni convierte IOSB en override de un error retornado.

PENDING o incertidumbre posretorno conserva arena compuesta, ambos buffers y owner bajo poison global aceptado.
No espera, sondea, cancela, reintenta, interpreta outputs ni cierra recursos relacionados. El owner debe retirarse/reapearse antes de otro trabajo nativo.

El derivador puro valida cuatro tamaños potencia2 entre512 y65536, múltiplos de logical, y máscaraNT en{0,1,3,7,15,31,63,127,255,511}.
Sólo tras validación convierte mask+1. Valida máscaraNT0xF y exige bits1/2 más offsets conocidos exactamente0.
Bits4/8 no-seek/TRIM no determinanB. Unknowns, bits desconocidos, nonzerooffset o falta de corroboración producen candidatoNone con causas.
La política offsets0 es conservadora propia del proyecto, no una afirmación universal de Microsoft sobre todos los offsets posibles.

B candidato es max(cuatro tamaños,mask+1), divisible por todos y dentro del wireU1. Una cifra calculada no acredita ninguna capacidad.
El writer futuro consulta y valida su propia adquisición/exclusión, S1, modos y buffers. Conserva el B de un journal existente o bloquea incompatibilidad.
No adopta un snapshot readonly previo como autoridad de writer, flush, creación o ACK.

## Alternativas descartadas por la elección G2

- **G1 — NT raw sin B ahora:** viable, pero aplaza política necesaria para liberar el componente derivador y el writer.
- **G3 — diagnóstico Win32 y NT aplazada:** viable como aplazamiento, pero deja íntegro el gate geométrico pendiente.
- **Mezclar APIs o fallback que admita el host:** descartada por perder procedencia; no forma parte de las opciones válidas.

ROOT eligió G2 para cerrar la dependencia geométrica antes del writer. G1/G3 quedan descartadas en esta unidad por aplazarla. La elección no ratifica implementación ni admisión.

## Consecuencias

La autoridad geométrica se documentaría en un cambio focal de `storage-durable-design.md`. No cambia O2/S1, wireU1, SQLite o contratos de producto.
La política puede rechazar geometrías legítimas fuera del perfil acreditado. Conserva raw y bloquea; no flexibiliza gates para acomodar el host.
Son necesarias nuevas pruebas/revisión/QA de U2b2. U2b1, experimentos previos y lectura documental no las sustituyen.
Continúan pendientes bootstrapTI, cadenaS1, store/writer/ACK, durable journal, ext4 persistente, lifecycle y aceptaciónM1/T05.

## Estado

`aceptada` — G2 elegida por ROOT bajo delegación, revisada A+B1 y QA documental33/33. Contrato adoptado; implementación y evidencia nativa pendientes.
ROOT publica ADR-0078 tras verificar el número libre; ADR-0077 de M2 permanece intacto. Minor documental A01 anotado, no bloqueante; no se afirma corregido.

Referencias oficiales: [queriesNT de volumen](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntqueryvolumeinformationfile),
[queryNT de alineación](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-ntqueryinformationfile),
[flags/offsetsNT](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/3e75d97f-1d0b-4e47-b435-73c513837a57),
[máscarasNT](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-fscc/9b0b9971-85aa-4651-8438-f1c4298bcb0d),
[autoridad de retornoNTSTATUS](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/wdm/ns-wdm-_io_status_block).
