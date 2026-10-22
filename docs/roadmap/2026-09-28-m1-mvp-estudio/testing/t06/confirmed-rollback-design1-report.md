> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

﻿# Rollback confirmado: decisión interna propuesta para Root

OWNED runtime: []. Diseño estático; sin implementación, imports, tests ni reproducción nativa. TDD n/a: prosa de diseño. Root selecciona y acepta. VULN-001 Medium sigue abierta; QA246 aceptada se conserva como evidencia histórica, sin dispensar el hallazgo.

## Fuente y causa acotada

publication.py:81–100 invalida ante toda excepción del callback; events.py:242–254 conecta opcionalmente ese callback con _commit. _commit:256–344 combina Session y session.begin(): valida propiedad (263–279), replay contradictorio (280–291), secuencia/terminal (293–294) y estado activo (295–296) antes de modificar Job/JobAttempt (297–317). Construye el batch antes de salir del contexto que intenta commit (343–344). El rechazo sale por rollback, pero el coordinador carece de evidencia del resultado.

EventBus.mark_gap:96–102 cambia epoch/secuencia, borra ring y cierra suscriptores. Subscription._close_locked:188–195 borra replay/pending. Causa inferida del código y del root-adjudication.json de SAST; no reproducción propia.

test_publication_coordinator.py:150–172 exige identidad primaria ante commit incierto y nota por gap secundario; 224–246 prueba consumidor coordinado y replay benigno; 249–289 preserva efectos durables frente a publicación fallida/proyección privada; 292–345 acredita B01 con SQLite/bus reales (rechazo, certificado inválido, shutdown y aceptación); 348–375 rechaza ack desconocido. No prueba retención del feed ante rechazo con rollback confirmado.

## Dos interfaces, recomendación O1

O1: objeto de resultado privado inmutable y sellado, sin convertir el rechazo en éxito.
Firmas propuestas en publication.py:
- _ConfirmedRollback(primary: Exception, traceback: TracebackType | None, *, seal: object).
- _confirmed_rollback(primary: Exception, traceback: TracebackType | None) -> _ConfirmedRollback.
- commit_and_publish(self, commit: Callable[[], CommitPublication | _ConfirmedRollback], bus: PublicationBus) -> PublicationOutcome.

Un singleton privado sella el objeto; comprobar tipo exacto y sello por identidad. Único uso autorizado de la fábrica: integración transaccional EventConsumer, después de rollback completado y sin entrar a commit. No campo JSON, bool, tipo ValueError ni flag de sesión constituyen evidencia. El sello evita confundir valores ordinarios; no es aislamiento frente a Python hostil dentro del proceso. La autoridad procede del código transaccional revisado. Ningún adaptador puede emitir el objeto basándose en payloads o en una afirmación del callback genérico.

Si el callback lanza, conserva el camino incierto actual. Si retorna el certificado auténtico, FUERA del try del callback, ejecutar:
raise result.primary.with_traceback(result.traceback) from None
sin gap/publicación ni retorno PublicationOutcome. El caller recibe el mismo primario: clase, args e identidad intactos; frames originales conservados como cola del traceback. Los frames de propagación nuevos son inevitables: no prometer igualdad completa del traceback. Objeto con sello/tipo inválido conserva INVALID_COMMIT_RESULT + gap.

O2: _ConfirmedRollbackRejection(primary: Exception, traceback: TracebackType | None, *, seal: object), excepción privada sellada; callback firma actual, catch específico y rethrow del primario guardado. Igual evidencia requerida, pero añade una excepción transitoria y cause/context que deben ocultarse para evitar fuga del wrapper. No ofrece mayor certeza transaccional. Elegir O1 por separar evidencia interna y excepción pública original.

## Integración mínima

Firmas propuestas en events.py:
- _commit(self, attempt_id, engine_id, event, stamp) -> CommitPublication.
- _prepare_batch(self, session: Session, attempt_id, engine_id, event, stamp) -> CommitPublication.
- _commit_coordinated(self, attempt_id, engine_id, event, stamp) -> CommitPublication | _ConfirmedRollback.

Extraer exclusivamente cuerpo 258–343 a _prepare_batch, incluyendo writer, validaciones, modificaciones, construcción de batch y retornos duplicate/no-op. _commit conserva sus contextos actuales y usa el helper: misma conducta legacy ValueError/error. En accept solo cambiar el callback coordinado a _commit_coordinated.

El camino coordinado usa Session y transacción explícitas. No envolver preparación y salida de un contexto que intente commit con el mismo catch:
1. Begin y preparación del batch, sin invocar commit. Begin fallido sin transacción acreditada queda incierto.
2. Ante excepción de preparación, guardar inmediatamente primario y traceback; ejecutar rollback REAL. Emitir certificado solamente después de rollback completo y cleanup de Session satisfactorio, sin haber entrado a commit.
3. Rollback/close fallidos mantienen el primario y política incierta; registrar secundarios aparte. No finally cuyo close sustituya el error primario.
4. Preparación exitosa entra en otro bloque que llama transaction.commit(). Cualquier excepción allí es incierta, incluso si rollback posterior funciona. Un commit puede haberse hecho durable antes de lanzar. Retornar CommitPublication solo tras commit y cleanup satisfactorios.

No usar estado is_active/in_transaction después de commit como prueba ni contextmanager que suprima excepciones. Preparación debe seguir limitada a SQLite/memoria, sin publicación ni efectos externos. Se certifica la frontera precommit y rollback real, no una clase de excepción. Puede cubrir también fallos de preparación distintos del rechazo de dominio bajo las mismas garantías.

Preservar error con raise desnudo mientras su handler esté activo. Propuesta de diagnóstico privado para rollback/close secundarios: atributo _publication_secondary_errors: tuple[tuple[str, Exception], ...] en el primario, etiquetas rollback/close, más nota; no modificar cause/context para almacenar secundarios ni sustituir clase/args/identidad. Si la limpieza falla después de preparación exitosa o commit, su error se propaga incierto. No emitir certificado antes de cleanup. El manejo existente del gap secundario B01 permanece intacto.

Duplicados benignos siguen siendo batches vacíos confirmados tras commit. No fake success para rechazo. Invalidate deliberado, resultado inválido, publicación/rechazo/shutdown postcommit, conteo confirmado y gap secundario: publication.py:101–133 no cambia.

## Ownership y plan causal futuro

Dos runtime como máximo: apps/server/app/publication.py y apps/server/app/queue/events.py. Un test nuevo: apps/server/tests/test_publication_confirmed_rollback.py. No cambios a sse.py, modelos, DDL, servicios, HTTP o tests anteriores. Admission/provenance son contexto protegido, sin modificación.

Antes de cualquier fix, esperar terminal real y handoff explícito de Provenance sobre publication/events/test. Esta unidad no verifica ni declara liberación. Root despacha implementación, revisión fresca y QA.

Primer test nuevo contra APIs actuales: fixtures prepared/event existentes, SQLite real, EventConsumer coordinado, EventBus y suscriptor reales. Sembrar ring con evento aceptado; mantener lector con replay/pending sin consumir. Capturar epoch/cursor/ring/colas/subscriber_count y proyección completa de Job/JobAttempt con lector independiente. Entregar evento engine-contract válido con job_id distinto pero ID válido. Exigir ValueError esperado y DB/feed sin cambios, lector abierto. El código actual debe fallar en igualdad de epoch/ring, no en import/colección. Ese sería RED causal futuro, no observado aquí.

Expandir inputs a owner incorrecto, ordinal incoherente (fixture capturada antes del rechazo), seq adelantado y terminal contradictorio. No desactivar validaciones. Verificar rollback completado en frontera transaccional real y sin commit. Para identidad, un observador de salida de _prepare_batch guarda la excepción REAL de validación y traceback, relanzándola sin sustituirla; exigir raised.value is observed_primary, frames originales retenidos y ningún wrapper. Variante legacy conserva tipo/mensaje y validación.

Casos inciertos focales: commit ejecuta SQLite commit real y luego lanza primario (DB durable + gap aunque rollback posterior funcione); commit falla antes de confirmar (también gap); rollback ejecuta rollback real y después lanza secundario (primario de validación intacto, secundario separado, gap); close secundario; callback genérico ValueError sin evidencia (gap); objeto/resultado inválido no evita gap. Inyectar fallos solo en fronteras commit/rollback/close, manteniendo SQLite/consumidor/bus reales. No sustituir producción por stub para el RED.

Archivar source/test/fixture/runner antes de ejecución futura, con argv/UTC/exit/stdout/stderr/JUnit reales. Fallos de bootstrap históricos no son RED. Una baseline final apropiada abarca coordinator/snapshot/bus y consumidores vecinos; preservar todos los tests/asserts/decoradores/params antiguos. Cada runtime completo cambiado >=80%, cero exclusiones, un trace fresco; sin unir evidencia antigua ni inferir desde QA246. Root define invocación final y aceptación; no cierre global T06/HTTP/E2E.

## Límites y contabilidad

Inspección PowerShell/rg y escritura privada únicamente. Copias de entradas después de lectura y antes de informe: limitación registrada, no captura pre-import inventada ni freeze global. Primera tentativa de escritura falló en parsing JavaScript antes de ejecutar o crear archivos; no fallo de producto/RED. Lecturas amplias iniciales tuvieron salida truncada; CONTINUE leído inicialmente hasta 100 líneas, sin entrar al Historial. Brief M0 genérico descubierto y leído por error, descartado; brief correcto de esta fase leído después. Sin atribuir ese brief M0 al diseño.

Provider/model/tokens/EUR/horas IA NULL sin origen real. Sin afirmación de implementación, reproducción, cobertura o aceptación. No nuevos agentes, ledger, ADR, Git, goals ni medidores.
