---
design: canonical-current-integration-handoff1
titulo: Ingreso de episodios y estado canónico en callers reales
estado: borrador
creado: 2026-10-08
actualizado: 2026-10-08
spec: ../../spec.md
evaluacion: n/a
plan: ../../improvement-plan.md
adr: ../../../../decisiones/ADR-0050-autoridad-canonica-aislada-del-benchmark.md
opcion_elegida: O2 dedicado y arbitraje A ya ratificados; corte recomendado pendiente de adjudicación root
generacion:
  fuente: estimado
  peso_predeclarado: 1
  actual_model: null
  actual_tokens: null
  actual_EUR: null
  actual_IAhours: null
---

> Publicación root: recomendación arquitectónica original; root autorizó este corte, implementación en progreso sin aceptación. Rutas relativas de enlaces ajustadas para esta ubicación. Evidencia privada original intacta.

# Handoff concreto del próximo corte T09

## 1. Contexto y restricciones

ADR-0050 ya decidió ubicación y arbitraje. Esta entrega aplica el método architect de custom-agents 1.22.0, con ownership, ausencia de nuevas opciones y medidor root impuestos por el encargo. TDD n/a: prosa. No modifica producto, pruebas, documentos públicos, decisiones ni ledger. El texto publicado de ADR0050 todavía dice «implementación, revisión y QA pendientes»: esa frase no invalida la aceptación limitada comunicada por root, ni convierte la integración en aceptada.

Base actual: lease `benchmark_canonical.py` f60d0271, QA127/90,35 whole; custodia existente. Process QA2 actual: 76 PASS, 1 PDH deseleccionado; canonical_runtime b84ce942 whole85,339168%, process d1d055 whole81,583199%, cero exclusiones; 69 protegidos, 108 launch/cleanup, 91 CLOSED_CONFIRMED y17 UNKNOWN_QUARANTINED, 107 asignaciones. Inspección de componente6 A/B limpia. QA1 42 PASS/34 setup errors permanece histórica. No se usa la cobertura runtime ~19% anterior como aceptación actual. Fuentes de esta lectura congeladas en source-before.json; mapa protegido del padre separado, sin importar módulos.

Nombres reales: `ParentMux`, `serve_mux`, `CanonicalProvider`, `CanonicalChannel`, `CanonicalPosition`. **No existe `IsolatedCanonical`**. `coordinator_audit` tampoco es una función: la entrada es `RuntimeChannel.audit_publications()` y desemboca en `_audit_publications()`/`_audit_delta()`.

## 2. Corte único recomendado, sin reabrir O2

Un corte sólo de constructor deja dos aceptaciones: `EpisodeAcquirer.acquire` publica antes de captura canónica y `_audit_delta` acredita en el worker largo. Un corte sólo de productor no hace seguro el consumidor; un corte que devuelve el dict de status como certificación tampoco. Recomiendo el conjunto acotado **ingreso de episodios + status/base tipados + cierre explícito de consumidores aún no migrados**. No promete que el CLI de160 funcione con el nuevo modo. Conserva el comportamiento legacy por defecto y añade una factoría de código confiado para el modo integrado. En ese modo el worker largo jamás obtiene state/store, ni un snapshot acreditado acumulado.

Complejidad media-alta por la frontera de publicación; riesgo principal autoridad duplicada; reversible retirando la factoría opt-in, sin desmontar los componentes aceptados. No hay alternativa útil menor que cumpla las dos fronteras. La integración completa de prerequisites/row exige selección tipada y lectores que todavía no existen y pertenece a otro corte.

## 3. Criterios del corte

1. Un sampler único ingresa la finalización real del sensor sin tomar `RuntimeChannel.transport` ni llamar al worker largo.
2. Sólo el hijo canónico captura, propone y hace commit. El supervisor conserva procedencia y publicación externa; sus arrays son evidencia observada, nunca una autoridad alternativa.
3. Accepted/rejected/interrupted no se confunden. Full observed head incluye rechazos; una interrupción sin restante original revoca, preservando evidencia sin fabricar commit tardío.
4. Status/base devuelven identidad privada registrada y acreditación fresca; todos los otros consumidores actuales quedan explícitamente cerrados en el modo nuevo antes de efectos.
5. El deadline de episodio es el original start+2s. El presupuesto de lectura independiente nunca lo renueva.

## 4. Colocación, bootstrap y secuencia concreta

**Factoría nueva propuesta:** `scripts/eval/benchmark_canonical_integration.py`. Su API futura debe aceptar configuración confiada del supervisor, no options JSON de un caller. Construye `EpisodeAcquirer` con su firma existente; antes de arrancar `ContinuousCoordinator`, construye `CanonicalChannel(acquirer.worker, private_root=..., stream=...)` y fija una asociación privada de identidad acquirer/canal. Construye después `ContinuousCoordinator(acquirer, interval_s=1)`, el operation worker con handler de código confiado NUEVO `benchmark_canonical_integration:_canonical_operation_provider`, y `RuntimeChannel(coordinator, worker, audit_binding=...)`. La asociación de ese último canal con la sesión canónica también es privada, instalada por la factoría; audit_binding no concede autoridad.

`_canonical_operation_provider` es una factoría NUEVA: construye `BenchmarkOperationProvider(config)` real y le instala un marcador privado por identidad reconocido por su guard. No deriva ese marcador de config/arguments, de `canonical_mux_v1`, de `validated`, ni de un fichero autocertificado. El handler integrado cierra incondicionalmente la familia de acciones de auditoría antigua indicada abajo. No permite que JSON seleccione modo legacy. La construcción legacy directa conserva su comportamiento. No se usa un doble de provider/coordinator para los gates de aceptación.

Antes de cualquier nacimiento: inventario fuente SHA/tamaño del árbol efectivo, factories, worker bootstrap y helpers; comparación con el freeze vigente aprobado por root y los source_hashes del plan, sin promover un hash enviado por caller. Congelar bytes del config confiado antes de operación. Tras nacimiento: ownership real Job/PID/FILETIME de sensor y operation worker y su pertenencia a esta sesión. La factoría retiene esos objetos y los comprueba antes de read/admisión; un PID en arguments no es binding. Inventario de source-after debe demostrar que no cambió el código durante la corrida futura.

Bootstrap canónico existente, no reinventado: `CanonicalChannel.__init__:937` exige **type(sensor) is OwnedProcess**, no subclass/doble ni mux, ownership actual igual a `sensor.ownership`; obtiene contexto/root de `_trusted_config_bytes`. Escribe sólo binding no secreto en bootstrap-epoch.json. `ParentMux.gate:179` fija config hash, factory hash, epoch y HMAC de32bytes antes de operar; key sólo por stdin privado. `OwnedProcess.__init__:274` asigna Job antes de gate; `_child:699` selecciona `serve_mux`, cuyo challenge compara `_own_birth` antes de construir provider. `CanonicalProvider.__init__:634` comprueba bootstrap sellado y nacimiento supervisor. No keys en logs/env/argv/files. El sender confiado es código supervisor que posee sensor/pipe/Job, no quien conoce root o cápsulas.

**Dos incompatibilidades actuales que el corte debe corregir mínimamente:**

- `CanonicalChannel.stream` es la identidad de sesión de auditoría, pero `CanonicalProvider.__call__:744` compara el request de episodio con ella; `ContinuousCoordinator._sample:145` pasa nombres de fase cambiantes a acquire. Mantener la identidad canónica de sesión; sustituir esa igualdad por binding al request auténtico del sensor y conservar su fase exacta en el intento. Validar tipo/fase de la finalización real, sin introducir una fase caller autorizante. No crear un nuevo canal por fase ni reiniciar ordinal/state.
- `_attempt:576` accede siempre a completion.value.proof. Extender el adaptador de ancla para finalización **rejected** observada real, con los campos existentes de `EpisodeAcquirer:577`: status, episode_id, result, request, ownership, observed. `_stage:842` debe permitir el original de rechazo que exige `validate_inventory_attempt` (nombre descubierto en el código: `rejected.json`), conservando namespace cerrado y sellos; no permitir comodines generales. `CanonicalState.capture/propose/commit` ya procesa ese intento mediante `transition:405` y `_attempt_header:231`; no duplicar esa semántica. Un resultado reject publica evidencia de rechazo, nunca sample o view positiva. La extensión abarca también los accesos accepted-only a `attempt["receipt"]` en `_ingest_latest`, `_stage`, `handle_ingest` y tentative publish/confirm: derivar episode/start/deadline del receipt accepted o del request rejected real, congelar siempre el intento completo y mantener `receipt_sha256` como sello del ancla de intento actual. No inventar un receipt positivo para reutilizar esas líneas. Añadir registro privado last_attempt para que acquire distinga ambos outcomes; last_receipt sólo se asigna a accepted. El watermark de rechazo puede sellar su inventario con los mismos publish/confirm y presupuesto; status/base debe fallar por el head negativo, sin devolver la posición anterior. Interrupted/EOF sin finalización privada válida revoca; su progreso/request/evidence se conserva en el padre y RAW, sin usar un dict como nueva entrada certificada.

**Accepted:** en `EpisodeAcquirer.acquire:552`, mantener start/request/call/validación de forma y ordinal. En la rama privada integrada, inmediatamente tras la finalización válida ejecutar `CanonicalChannel.ingest_latest()`; no append accepted previo. El recibo autoritativo congelado es el que este canal deriva de `_last_completion` real y expone en `last_receipt`, no otro receipt con un observed posterior. Validar su concordancia con el request y summary real; después del éxito y de comprobar restante, publicar `last_record`, receipts, previous_receipt y attempts con ese mismo receipt exacto. `_custody` sigue copiando evidencia del sampler tras retorno, no ejecuta capture.

Pseudocódigo de llamadas **existentes** (las conexiones privadas descritas arriba son modificaciones propuestas):

```python
acquirer = EpisodeAcquirer(root=episode_root, context_path=context_path,
                           sensor_config=sensor_config)
canonical = CanonicalChannel(acquirer.worker, private_root=private_root,
                             stream=session_stream)
coordinator = ContinuousCoordinator(acquirer, interval_s=1)
# Dentro de acquire; start/deadline ya fijados y worker.call ya observado:
commit = canonical.ingest_latest()
receipt = canonical.last_receipt
# Comprobar reloj original y publicar arrays sólo ahora.
# Dentro de la rama integrada de audit_publications/_audit_delta:
position = canonical.request_view(kind="status", deadline_ns=read_deadline)
canonical._resolve_position(position)
# Retornar position al consumidor tipado, jamás dict(position) como aprobación.
# Cierre de la sesión: canonical.close(); acquirer.close(); worker.close().
```

No se afirma que ese pseudocódigo sea código ejecutable del árbol actual. `ingest_latest` no toma receipt/paths caller. Su secuencia actual `begin/fragment/end/publish/confirm` se conserva: receipt_sha256 se registra en anchors antes de `_stage/capture`; `end` hace commit tentativo; `publish` persiste el ancla que referencia commit y observed parent de end; `confirm` lleva anchor_sha256 y completed observado por el padre al recibir publish. La segunda ancla no entra retroactivamente en receipt_sha256. Añadir en el registro externo del supervisor también el reloj de recepción de **confirm** antes de aceptación; comprobar exactremaining después de confirm y antes de arrays. Esto no modifica el hash del recibo ni el archivo externo; evita circularidad y distingue el ACK final de persistencia. Si cualquier paso/persistencia/witness/captura/espera/transfer llega tarde, cero arrays accepted y cero predecessor.

Cold startup se hace antes de sampler y fuera del episodio, con cota propia por nacimiento actual5s; el constructor CanonicalChannel no tiene parámetro startup_timeout_s. La factoría debe tener un límite total de bootstrap explícito, sin adjudicárselo a los2s ni fingir un argumento existente. Fallo parcial limpia sólo objetos nacidos propios y conserva UNKNOWN cuando corresponda.

**Carriles y tipos:** frames existentes son cerrados `epoch,binding,lane,seq,index,deadline_ns,payload,mac`; replies ligan epoch/binding/lane/seq y `type,index,payload,mac`. Ingest son begin/fragment/end/publish/confirm; read status/base. One pending por lane; outgoing padre2, child lane1 y responses2; MAX_REQUEST4096, MAX_FRAME262144, progress64, fragment1200, transferencia64Mi caracteres. No callbacks productores en control RPC. `serve_mux:386` ejecuta un witness por paso y reconsulta ingest antes del siguiente: mantener ocho witnesses/noveno ingest prioritario y leases actuales. El scheduler único puede bloquear en syscall; admisión independiente no demuestra cota de syscall ni cadencia.

`CanonicalPosition:618` ya liga token/epoch/context_sha256/cursor/prefix/kind/stream/worker y eq=False; `_resolve_position:1087` comprueba identidad del registro y worker abierto, **no acredita frescura**. El corte agrega un wrapper privado NUEVO de sesión/consumidor que registra dueño y request_id por identidad junto a esa posición, la invalida al cambiar epoch/canal y sólo permite consumo de status/base de la solicitud actual. No exporta/importa su constructor desde JSON ni reutiliza arrays aprobados. Tickets materiales futuros deberán incluir esos mismos campos, selector/type y operación consumible, con propiedad real del operation worker; en este corte no se emite ninguno. Cada solicitud hace `request_view` con reloj actual; una posición antigua o una copia idéntica no evita el read fresco.

## 5. Impacto y frontera exacta

| Owned por el futuro implementer | Cambio acotado |
|---|---|
| `scripts/eval/benchmark_canonical_integration.py` NUEVO | Factoría confiada, bindings privados, wrapper de vista y handler integrado que instala guard cerrado. Sin store/state. |
| `scripts/eval/benchmark_episode.py:521,552,676` | Rama integrada privada; aceptación tras canonical confirm; rejection completa; cierre de ambos propios, preservando causa primaria y evidencia. Firma y legacy default conservados. |
| `scripts/eval/benchmark_canonical_runtime.py:576,696,842,934` | Ancla rejected, fase auténtica separada de session stream, watermark negativo y registro parentcompletion final. No rediseñar mux/state/store. |
| `scripts/eval/benchmark_coordinator.py:105,436,467` | La rama integrada `_audit_delta` solicita posición fresca por canal independiente; ningún audit_delta_* al operation worker. Copias observadas sin nueva autoridad. |
| `scripts/eval/benchmark_runtime.py:652,741` | Guard privado del provider integrado antes de emit/efectos para auditorías/consumidores no migrados; sin refactorizar el cuerpo legacy. |
| `scripts/eval/tests/test_benchmark_canonical_integration.py` NUEVO | Tests causales de estas cinco fuentes con sensor/procesos/custodia/state/provider/coordinator reales y fixtures propios. |

Readonly en este corte: `benchmark_process.py`, `benchmark_canonical.py`, `benchmark_custody.py`, `benchmark.py`, todos los tests existentes, demás scripts/eval y docs públicos. Si el implementer demuestra defecto de un componente protegido, escalar hallazgo a root, no ampliar ownership silenciosamente. Mantener funciones/assertions/helpers/decoradores/legacy completos.

En modo integrado, guard debe rechazar **audit_begin/audit_fragment/audit_validate, audit_delta_*, calibration_export, accreditation, refresh_accreditation y row**, incluso entrando directamente al handler o mediante args_begin/fragment/execute. No aceptar audit_binding_path/root/headers/autosnapshot como escape. Los demás comandos conservan sus efectos originales, pero no producen certificación canónica. Toda ruta pública de RuntimeChannel debe pasar por su mediación privada o el guard; probar también operación directa y transferencia grande. Así los callers pendientes son alcanzables y fallan antes de I/O/API/publicación certificadora; no se dejan funcionando sobre snapshot stale.

`benchmark.py:201 run_session_v3`, montaje:276/304/324, `prepare_group_v3:63` (audit_publications:179), `collect_calibration_v3:117` y llamadas accreditation397/refresh416/row posteriores siguen legacy. **No activar esta factoría en ese CLI todavía**: necesita corte siguiente con lectores/material tickets/prerequisites. El presente corte sólo ofrece una vía productiva opt-in por APIs reales del coordinador, no reemplaza la ruta live existente ni afirma su seguridad canónica. Tampoco incluye packs, FINAL desde EMPTY, restore, CLI/restart ni exportación de anclas externas durables. Ante pérdida de sesión no se crea reemplazo para aparentar continuidad.

## 6. Riesgos y mitigaciones

| Riesgo | Gate requerido |
|---|---|
| Cambio runtime con historial de whole~19% no aceptado | WHOLE EACH actual >80% en **cada** una de las cinco fuentes cambiadas, líneas+ramas, cero exclusiones y sin promediar. Ejercitar el provider real legacy además del guard nuevo. Si no alcanza, la unidad no se acepta; no extraer funciones ni modificar denominadores. |
| Rechazo conserva antiguo positivo | Head negativo del state revoca leases; invalidar positions/tickets/publication y romper predecessor; conservar último aceptado sólo como historia, no view fresca. |
| Commit antes de parentfailure | Registrar confirm ACK separado; failclosed/epoch revocado aun con archivos committed; conservar RAW/progreso y no reintentar resultado incierto. |
| ReadFile cero bytes físicamente bloqueado | **UNTESTED**, gate nativo futuro explícito. Watchdog aborta sólo Job canónico conocido, despierta waiters y une readers/writers; sólo recibo comprobado puede devolver recursos. Ausencia de PID/Job vacío sola no convierte UNKNOWN en confirmed. |
| source/bootstrap/owner falsos | Freeze antes de nacimiento, factory confiada, ownership real antes de capture; mutation/MAC/EOF tardíos revocan y descartan reply/commit tardío. No duplicar autoridad local como workaround. |

Pruebas detalladas en report.md. No garantía de cadencia2,5s bajo kernel bloqueado, calibración,13h,160jobs, GPU ni calidad humana. Derechos de letra/uploads/consentimiento y verifiedfalse siguen vigentes; pruebas CPU con sensor policy no acreditan memoria GPU o calidad musical.

## 7. Dependencias y decisión root

No hay pregunta al propietario. Root puede asignar este conjunto de cinco módulos más un test nuevo como próxima unidad bounded, con guards pendientes explícitos. Root elige alcance y decide si separación phase/session requiere cambio documental; sólo root publica ADR/documentos/ledger/aceptación/meter. No copiar el diseño anterior como si sus APIs propuestas ya existieran. Si exige sustituir **ahora** el CLI live con todas sus acreditaciones, este corte no basta: se requiere adicionalmente selección/read-view tipado y migración de calibration/prerequisite/refresh/row en provider, observation/calibration/runner y montaje benchmark.py, con acceptance propio; no habilitar sólo un boolean.

Formal integrated review siguiente4 distinta de processcomponent6 y lease4; conservar todos los contadores. Handoff arquitectónico completado con reservas de frontera y cobertura, no aceptación de integración ni cierre T09/M0–M5.

## Changelog

2026-10-08: APIs vigentes inspeccionadas; se propone un único corte de ingreso/status con guards de consumidores pendientes, preservando O2/A y evidencias aceptadas limitadas.



## Desarrollo de fuentes y presupuesto absoluto — 2026-10-09

[ADR-0059](../../../../decisiones/ADR-0059-fuentes-y-presupuesto-absoluto-del-benchmark.md) adopta O2: verificador propio de fuentes, plazo absoluto desde la entrada y retención UNKNOWN de nacimientos o cleanup tardíos. Sustituye las ventanas renovadas por worker y las lecturas síncronas del supervisor fuera del presupuesto descritas anteriormente. Wiring y fixtures de contexto/plan coherentes se implementarán tras transferir las fuentes FIRSTcause; no acredita pruebas ni QA. Formal5 conserva formal3/4, rebateT10 y R09T13CLI pendiente.
