> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

﻿# Dictamen estático acotado

La hidratación de un Job del primer lector no es necesaria para calcular snapshot ni cursor. Sin embargo NO queda probada la equivalencia observable incondicional de la proyección EXACTA de 17 campos solicitada. Recomendación única: mantener el código actual y encargar a Root una unidad estática de cierre de dos precondiciones, antes de asignar implementación. No hay decisión de Root ni aceptación en este informe.

## Prueba de valores (condicional)

Sea F la secuencia siguiente. Para cada fila r, si los valores ORM coinciden con los valores procesados de sus columnas, canonical(dict(zip(F,r[0:17]))) == snapshot(job). La misma canonical conserva ensure_ascii=False, allow_nan=False, sort_keys=True y separadores compactos (resolver.py:23–53). No usar un objeto de proyección como Job o autoridad.

| Posición | Campo exacto | Fuente snapshot | Fuente tipo/columna |
|---|---|---|---|
|0|id|resolver.py:35|models/__init__.py:76 String(26), PK|
|1|owner_id|:36|models:77–79 FK|
|2|song_id|:37|models:415 FK|
|3|task|:38|models:400 Text|
|4|lane|:39|models:401 Text|
|5|request|:40|models:409 JSON|
|6|model_id|:41|models:408 Text nullable|
|7|engine_id|:42|models:407 Text nullable|
|8|attempt|:43|models:405 Integer|
|9|max_attempts|:44|models:406 Integer|
|10|status|:45|models:404 Text|
|11|priority|:46|models:402 Text|
|12|created_at|:47|models:80 Text|
|13|updated_at|:48|models:81 Text|
|14|deleted_at|:49|models:82 Text nullable|
|15|not_before|:50|models:403 Text nullable|
|16|cancel_requested_at|:51|models:418 Text nullable|

Los números relativos :36 etc. corresponden a apps/server/app/queue/resolver.py; models corresponde a apps/server/app/models/__init__.py. Job tiene 25 columnas: 20 propias + 5 Common. request NO es ContractJSON: este se aplica a JobAttempt (models:431–447,478–482). No atribuir a este cambio eliminación de validaciones contractuales de retries.

## Contradicciones y límites concretos

1. El ORM procesa también telemetry JSON (models:414). JSON.result_processor usa dialect._json_deserializer o json.loads (SQLAlchemy sql/sqltypes.py:2816–2825). Una proyección de 17 columnas omite esa conversión y cualquier fallo que produzca antes de entrar al writer. No hay validador load de Job localizado, pero esto no elimina la conversión. Las restricciones generadas de JSON (models:667–672) prohíben JSON inválido en una BD normal; no prueban por sí solas equivalencia frente a BD corrupta, migraciones reales, motores con deserializador particular o fixtures que desactiven checks. El writer vuelve a cargar telemetry para filas todavía elegibles, pero NO preserva el fallo del primer lector si una mutación posterior hace desaparecer esa fila del _query del writer. Preservar explícitamente ese procesador exigiría leer telemetry adicionalmente; contradice EXACT17. No recomendar saltar validación silenciosamente.
2. SQLAlchemy ORM consulta el identity map y puede conservar atributos de una instancia ya presente, mientras Core obtiene valores físicos (orm/loading.py:1087–1096,1133). candidate_batches acepta reader externo sin exigir mapa vacío ni ausencia de dirty/pending. Core de columnas de tabla también puede cambiar autoflush respecto a ORM (orm/context.py:332–359). Esto no es una afirmación de fallo del flujo real. Runtime crea lector nuevo (runtime.py:344); retry expunge Job y JobAttempt antes de yield (retry.py:118–134), sin relaciones ORM declaradas encontradas. Por ello el flujo actual proporciona fuerte evidencia de disjunción, pero no un contrato general de reader= para todos sus llamadores.

Búsqueda efectiva de listeners/validadores/reconstructors: apps/server/app y packages, Python, patrones event.listen/listens_for, sql_event.listen, reconstructor, validates, loaded_as_persistent, do_orm_execute, __declare, mapper_configured, attribute_instrument; búsqueda adicional en apps/server/tests. En producción aparecen connect/begin y after_commit (db.py:43–57), validadores y before_insert/update de JobAttempt/CpuExecution/PublicationIntentRevision (models:501–603), listener de migración; ningún listener de carga Job localizado en ese alcance. Tests sí registran loaded_as_persistent como observación. No se certifica ausencia universal de listeners dinámicos externos. No hay relationships en models que justifiquen cascadas de expunge de Job.

## Invariantes que la futura implementación debe conservar

_query admission.py:57–79 es autoridad de filtros: vista dispatchable_job, joins Song/User, owner local, borrados, dependency-only, cancelación, estados y carriles. Una sustitución de lista de columnas debe conservar FROM/joins/WHERE exactos; SQLAlchemy Select.with_only_columns(*entities, maintain_column_froms=True) está presente en sql/selectable.py:6130–6203. Usar columnas tipadas de Job.__table__, sin cast/texto para el contenido JSON ni lecturas por fila. Query sigue siendo el primer DB read del stream cuando así ocurre hoy; no introducir lectura preliminar ni otro connection.

Orden SQL exacto admission.py:189–207: prioridad 0..3, segundo UTC normalizado, fracción rellenada/truncada a seis dígitos, id; mismo tuple_ keyset. Si finalmente se acredita EXACT17, posiciones 0..16 snapshot y 17..20 cursor con labels exclusivos cursor_priority/cursor_second/cursor_fraction/cursor_id. id está duplicado deliberadamente en posiciones 0 y 20: no usar mapping ambiguo. No convertir fechas con julianday.

Mantener el mismo Session.begin/lector de admission.py:211–217 y db.py:50–52: WAL snapshot fijado por la primera lectura, una sola transacción para todas las páginas. No reiniciar por página: así se excluyen inserciones posteriores incluso backdated. Writer nuevo: admission.py:238–267, mismo writer lock, _query, snapshot comparado, dependencias, preload, elegibilidad, flush y expunge. Output sigue siendo exclusivamente Job ORM del writer original. Claim/reserve: admission.py:303–405 retiene CAS y CPU2/GPU1.

Para cualquier cambio concurrente de cualquiera de F, el writer actual devuelve canon distinto o _query lo excluye. request entero incluye dataRef/inputs y modelo efectivo especificado dentro de request; model_id/engine_id explícitos también se comparan. Cancel/deleted/owner/song/status pueden excluir primero. updated_at se compara incluso sin otra diferencia. Canon ignora orden de claves de JSON igual que hoy: una modificación que vuelve al mismo canon no se distingue hoy ni con proyección. Cambios de dependencias y disponibilidad de referencias se revalidan en writer, no se inventa su inclusión en F. Global priority/FIFO, merge de streams runtime.py:342–369 y caché negativa compartida permanecen intactos.

Memoria condicional: page <=400 filas, sources <=400 cadenas, current <=400 Jobs y parents/references acotados por página como hoy. Reader elimina creación/registro/población/expunge de sus Jobs, no necesita expunge_all ni tocar identidades de retry. Generator puede retener página anterior hasta asignar la siguiente: pico transitorio hasta dos páginas, O(size), no O(total). Los tamaños de request, padres y referencias no tienen una cota absoluta en bytes demostrada aquí; no afirmar memoria constante absoluta. Retirar expunge no retira una cascada funcional conocida, porque no se encontró relationship de Job.

Trabajo evitable por fuente: creación InstanceState/Job, alta identity map, población de 25 atributos, lectura de ocho campos ajenos a F y expunge por fila (loading.py:1115–1124; admission.py:233–237). El snapshot canónico de 17 campos y writer siguen necesarios. Beneficio esperado solo estimado cualitativamente: menos trabajo ORM lector; no hay mejora temporal medida ni ahorro CPU exclusivo acreditado. Root adjudication medido: snapshot_result 2.097692s y current_writer_scalar 2.8724865s wall; old failure cause UNKNOWN, unnecessary_repetition_proven false; un PASS no cancela 1025 PASS/1 FAIL/3 SKIP anterior.

## Exacta siguiente unidad recomendada (sin ejecución)

Root debe cerrar estáticamente: (a) DDL vigente del Job y fixtures/motores de los tests de scanning/admission: demostrar que telemetry omitida no aporta un rechazo semántico exigible o declarar que EXACT17 no es admisible; (b) todos los usos de candidate_batches(reader=...) y mutaciones/autoflush del lector: demostrar mapa limpio/disjunto en el contrato soportado. Leer específicamente apps/server/app/migrations/versions/0001_initial.py, 0002_snapshot_metadata.py, los fixtures que crean engine y los llamadores ya nombrados; no benchmark ni general queue redesign. Si cualquiera falla, rechazar EXACT17 o pedir a Root preservar explícitamente el validador con proyección adicional. Esta unidad no asigna futuras fuentes.

Solo tras cierre favorable, plan mínimo en admission.py/resolver.py y test_dispatcher_scanning.py, con helper aditivo dentro de módulos existentes: compartir F y canonical para Job/valores, cambiar únicamente lectura por columna/cursor; mantener writer original. TDD futuro separado: RED real de conteo de Job loaded_as_persistent por Session lector (actual >0 frente a requerido 0), sin contar writer; conteo de conversiones debe mantener request y todo validador obligatorio, no afirmar ContractJSON reducido. Después GREEN mínimo y pruebas de semántica: mutaciones de los 17 campos, inserciones tardías antiguas, prioridad global/FIFO microsegundos, request inválido no nulo, modelos efectivos/dataRef, cancelación y writer actual; mismo tipo Job de salida. Mantener original801 covered10, sin timer/assert/decorator/param changes. Ejecutar baseline1029 actual después del fix, WHOLE cada producción cambiada >=80% cero exclusiones en traza actual, luego revisión y QA frescas Root. Todo esto propuesto, cero tests ejecutados aquí.

Decisión/documentación: Root registra y actualiza plan si contrato idéntico; si cambia el dominio soportado de reader= o el rechazo/conversión de datos, Root necesita ADR nuevo y documento afectado. No nueva tabla, framework, cache, tipo contractual ni extracción para cobertura.

## Custodia y ejecución

Ownership código exacto []; escritos solo en esta carpeta privada. TDD n/a: análisis estático/prosa, sin código de producto ni RED/gates. Skills tdd/debug-root-cause leídas de copias existentes, aplicadas como prohibición de fabricar RED/causa. Ningún Python/import/test/native/benchmark/profiler/instalación/red/Git/GPU ejecutado. No env/DB/data/models leídos.

Limitación de captura explícita: el primer comando leyó CONTINUE hasta 160 líneas y por ello cruzó Historial (empieza119), además lanzó listado demasiado amplio de nombres de caché que truncó salida. No se usó historia como autoridad. Algunas fuentes se leyeron antes de copiar: supplemental-input-captures.json las identifica; no se presenta custodia BEFORE perfecta. Inputs iniciales de admission/resolver/models/tests fueron copiados antes de su lectura detallada, pero el hash se calculó después de copiar y no acredita atomicidad contra otros actores. Los resultados con salida truncada no prueban lectura completa. Las búsquedas en fuentes adicionales no tienen captura física previa exhaustiva. Originales CLI reservados intactos. Receipt incluye comparación de los siete protegidos con Root y hashes actuales. Esta limitación de procedencia acompaña el dictamen, no se oculta con nuevas fechas.
