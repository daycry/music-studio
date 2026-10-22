---
id: ADR-0075
titulo: Journal por handle para autoridad y recuperación del almacenamiento propio
estado: aceptada
fecha: 2026-10-11
iniciativa: 2026-09-28-m1-mvp-estudio
opcion: O2
elegida_por: ROOT bajo delegacion vigente del propietario
eleccion_fecha: 2026-10-11
revision_documental: A/B conforme, intento 2
fuente: ../roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md
---

# ADR-0075 · Journal por handle del almacenamiento propio

## Contexto

ADR-0069 fija ext4 respaldado por el VHDX físico del proyecto. ADR-0071 protege los probes mediante helper Docker aislado. El recibo v1 tiene seis fases monotónicas. `ReceiptLease` acredita sólo lectura y `PublishedDiskBinding` consulta el disco publicado; sus componentes aceptados no incluyen commits ni lifecycle.

Attach y publish todavía escriben JSON por ruta después de sus efectos. Un crash puede separar el efecto real del recibo. El JSON mutable y un rename ordinario no proporcionan CAS por identidad ni recovery seguro.

## Decisión elegida

El controlador de plataforma usa un journal estable de infraestructura con slots de generaciones inmutables, PREPARE y COMMIT por el mismo handle. CAS exige exclusión nativa, token de generación e identidades del journal, volumen, raíz y padres. Conserva el JSON v1 publicado como semilla histórica inmutable. Los consumidores nuevos resuelven sólo la cadena sellada autorizada del journal.

ROOT eligió O2 el 2026-10-11 bajo delegación vigente del propietario. La revisión documental A/B del intento 2 quedó conforme. La decisión está aceptada; su implementación y QA física siguen pendientes.

El journal registra intenciones antes de create/publish/attach/validate/detach y resultados después de sus efectos acreditados. Una request repetida conserva su identidad y devuelve el commit previo si ya existe. Un commit o cierre incierto cierra admisión y exige reconciliación actual. No usa SQLite; sólo el server escribe la BD de producto.

Create requiere archivos nuevos. Bootstrap legacy es una operación explícita con lease v1, snapshot e identidad revisados y binding vigente; no adopción por SHA/path. El disco SMOKE actual no se sobrescribe, no se promueve a producción ni se usa como prueba de 64 GiB.

La fase v1 `validated` permanece histórica. Sesiones/epochs separadas representan reattach, quiesce y detach. Cada reinicio reacredita montaje/UUID/roles y conserva los preflights por FD de ADR-0071. `provision_domains` no se repite sobre una biblioteca usada o parcialmente creada.

## Alternativas descartadas

- **O1: JSON mutable reemplazado** — obliga a cambiar identidad y compartir DELETE, entra en conflicto con leases readonly y conserva incertidumbre de namespace. `ReplaceFileW` no soporta su opción write-through. [Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-replacefilew).
- **O3: JSON y COMMIT en archivos separados** — conserva historia, pero introduce nombres y markers nuevos en cada transición. NOREPLACE no demuestra persistencia del directorio tras power loss. [Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/winbase/ns-winbase-file_rename_info).
- **Escritura por ruta seguida de fsync y reread** — no acredita custodia, exclusión de rival ni atomicidad conjunta con el montaje. No constituye la alternativa durable.

## Consecuencias

El formato operativo nuevo pertenece a infraestructura y no cambia `StorageReceipt` v1, contratos de música ni SQLite. Los módulos nuevos de journal/lifecycle implementan el writer; los entrypoints antiguos con efectos deben delegar al mismo controller o rechazar ejecución. No quedan writers paralelos JSON/journal.

El envelope añade generación, cadena, request idempotente, identidades y sesión alrededor del payload v1 intacto. Las read views niegan WRITE/DELETE y bloquean adquisición de writer. El writer exclusivo bloquea nuevas read views. Cada frontera comprueba metadata/padres y capacidades reales antes y después del efecto; nunca toma el snapshot readonly como CAS todavía vigente.

El journal reserva capacidad fija antes de efectos y nunca reescribe slots anteriores. Agotamiento, corrupción, forks o alineación no acreditada bloquean operaciones. No hay compactación automática. El historial y el final publicado se conservan ante fallo; recuperación exige autoridad nativa actual.

Flush1 sella PREPARE/cuerpo antes de escribir COMMIT; flush2 precede al ACK. La respuesta perdida después de flush2 recupera el mismo request/commit sin otro slot ni efecto. Un cierre incierto invalida la autoridad local y conserva resultado y cleanup por separado; no se reintenta un scalar. Truncación o daño interior no se reparan con el seed ni aceptando un prefijo viejo. Los cutpoints y las diez invariantes verificables están en [storage-durable-design.md](../roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md), apartados 4.2 a 4.6.

`FlushFileBuffers` y write-through respaldan barreras del archivo bajo las condiciones de Windows y del hardware. Se separa crash de proceso, comprobable con pruebas CPU, de power loss del host. No se promete fsync de directorios ni atomicidad conjunta de rename, journal y montaje. [Microsoft: FlushFileBuffers](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers), [CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

La primera implementación puede verificar codecs, CAS, exclusión NT, identities, flush, errores/close y crash de archivos en artefactos privados sin admin. Attach/validated/detach, producción ext4 y backup/recovery siguen sujetos a QA real elevada posterior. Dobles CPU no completan esas verificaciones.

## Preservación, rollback y trazabilidad

El JSON v1 se conserva byte a byte con su identidad. El VHDX final no se borra para compensar attach. Detach sólo opera sobre disco/mount propios, bajo gate de admisión y tras quiesce de consumidores acreditados. Ninguna operación detiene WSL, Docker u Ollama globalmente.

Rollback del código deshabilita ejecución y mantiene journal/seed/VHDX intactos. No restaura un JSON viejo como autoridad mutable ni permite operar al writer legacy. La vuelta a servicio requiere un reader/controller compatible y reconciliación; no downgrade destructivo.

ROOT confirma el número 0075 y enlaza esta decisión con ADR-0069/0071, el diseño de ejecución y el documento de datos.

El diseño canónico es `docs/roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md`, con enlaces bidireccionales específicos `storage_durable_design:` desde spec/plan. Se preserva el enlace `design: design.md` actual de la iniciativa. Estos enlaces documentan la elección aprobada; no acreditan implementación.

## Estado

Decisión aceptada bajo delegación. O2 elegida por ROOT el 2026-10-11; revisión documental A/B conforme en el intento 2. No se afirma aceptación de código ni QA. El detalle normativo y la matriz de fallos están en [diseño](../roadmap/2026-09-28-m1-mvp-estudio/storage-durable-design.md).
