# Validación actual de M1 — 10 de octubre de 2026

**M1 no obtiene el verde integral.** La interfaz y los límites HTTP tienen pruebas conformes, pero el recorrido real no publica los takes sobre el bind Windows de desarrollo. La suite completa del backend terminó roja y las correcciones posteriores se verifican por separado. Los estados de las tareas permanecen exclusivamente en `../tasks.md`.

## Evidencia de interfaz y Docker

| Comprobación | Resultado actual | Alcance |
|---|---|---|
| Build oficial server, web y motor mock | Exit 0 | Dockerfiles originales; imágenes propias de QA |
| Playwright existente | 15/15 PASS | Fixtures de interfaz y pruebas API; no once recorridos integrales |
| Unitarios web | 260/260 PASS, 24 archivos | Árbol actual |
| Lint y TypeScript web | Exit 0 / Exit 0 | Árbol actual |
| API Host/Origin | 403 en peticiones ajenas | Límites HTTP reales |
| API sin autoría | 422 `LYRICS_DECLARATION_REQUIRED` | Petición real |
| Creación real con idioma `es` | 202, dos takes | Motor mock, post-proceso y FFmpeg ejecutados |
| Publicación real | `OSError 22` en `rename_noreplace` | Bind Windows; no almacenamiento ext4 autorizado |
| Playwright sobre esos takes reales | 0/1 PASS; 1 FAIL | No llegan a `ready`; gate `NO-VERDE` |
| SSE real | 200 y evento `system.status` | No acredita replay tras reinicio |
| Reproducción Range del take nuevo | 404 | No hay asset publicado; no se acredita 206 |

No se sustituyó el destino por tmpfs ni se inventó un UUID. La limitación del bind Windows coincide con la evidencia que originó [ADR-0069](../../../decisiones/ADR-0069-almacenamiento-ext4-del-proyecto-para-publicacion-atomica.md). El volumen ext4, el reinicio con assets persistentes, la reproducción y el backup/restauración de esa biblioteca siguen pendientes.

La QA original detectó que omitir `language` producía `422 INVALID_PARAMS` aunque el DTO lo declara opcional y nullable. La construcción incorporaba `language: null` antes de encolarse; ese diagnóstico está derivado de la fuente, sin captura de dispatch del caso rechazado. La corrección posterior omite el parámetro cuando no tiene valor y conserva el idioma explícito o ya presente en `params`. La regresión causal y la validación independiente se registran al final.

## Custodia y verificación independiente

El orquestador verificó a las **19:41:56 UTC** los 133 archivos del inventario de QA, los 1.748 sellos de fuentes finales, ambos JUnit, ocho terminales y el log de los 260 unitarios. El único cambio entre sellos inicial y final es `CONTINUE-HERE.md`, actualizado por el orquestador para reflejar la prioridad M1; no hay cambios de producto durante esta QA. El sellado original excluyó `tools/`, por lo que no acredita sus fuentes completas.

Los tres contenedores de QA y su red se retiraron por identidad propia, junto con la credencial temporal. El contenedor persistente ACE-Step se conservó. No se usaron GPU ni Ollama. El PDF de QA se omitió porque faltan las dependencias gestionadas del renderer; no se instalaron globalmente.

Evidencia local privada, disponible en este checkout y excluida de Git:

- [Informe QA y matriz de los once E2E](../../../../.cache/dev-cycle/m1/validation-20261010/e2e/report.md).
- [Inventario SHA](../../../../.cache/dev-cycle/m1/validation-20261010/e2e/inventory.json).
- [Comprobación del orquestador](../../../../.cache/dev-cycle/m1/validation-20261010/verify_e2e_root.receipt.json).
- [Candidato del idioma y fragmentos de contrato](../../../../.cache/dev-cycle/m1/validation-20261010/e2e/raw/language-candidate.json).

## Backend y verificaciones declaradas

La suite de server, contratos, audio-post y storage-guard se ejecutó en Linux con FFmpeg fijado, sin GPU, sobre las fuentes selladas antes de las correcciones. Resultado: **2.109 PASS, 88 FAIL, 11 SKIP, un error y cuatro warnings; pytest exit 1, 597,63 s**. El wrapper del contenedor terminó con exit 0 sin propagar el fallo de pytest: ese 0 no acredita un verde. La raíz verificó **1.734 artefactos y 380 fuentes congeladas**, JUnit y terminales a las 19:49:18 UTC. Los contenedores propios quedaron detenidos con PID 0.

Los 88 fallos no equivalen a 88 defectos del producto: parte procede de dependencias omitidas por el auditor, rutas y ejecutables exclusivos Windows, o fixtures nativas de credenciales e inyección no suministradas. Un segundo focal, conservando el original, pasa 28 casos y mantiene ocho fallos por hooks privados ausentes. No se modificó producto para fabricar señales de fallo ni se convirtieron negativos en skips.

Se han reproducido estos problemas funcionales y de fixtures:

- Inserción SQL de `Infinity`: rechazada sin filas nuevas, pero SQLite 3.40.1 produce `OperationalError: malformed JSON` en vez del `IntegrityError` contractual esperado.
- Dos commits concurrentes de canciones: la prueba de serialización de reconcile reproduce `database is locked`.
- Shutdown con writer concurrente: falla en la suite original; el focal exacto pasa, pero no se descarta el fallo original como flaky sin explicar su causa.
- FIFO creado por una prueba: la función de limpieza rechaza correctamente la entrada especial, pero la prueba no retira su propio FIFO.
- Ruff nativo: un bloque de imports y 13 archivos sin formato. Corrección preparada sólo en un espejo privado, sin aplicar durante el sellado de QA.

La verificación declarada de T-00 tampoco pasa en el árbol actual: su helper histórico se detiene al decodificar bytes no UTF-8 del ledger. Además depende de un inventario congelado anterior a los cambios posteriores autorizados. No se presenta su verde histórico como verificación actual.

La cobertura oficial acotada de `audio_post/manifest.py` y `pipeline.py` es **297/388 = 76,55 %**, inferior al 80 %. El 82 % global de audio-post no sustituye ese scope. La batería audio-post Windows pasa 161 casos y omite cinco propios de plataforma. Custodia Windows pasa 45 y falla uno que depende de un `parent.py` externo ausente; ese fallo no demuestra un fallo de muerte del árbol porque no se alcanzó la barrera de nacimiento.

Se corrigió una referencia material del informe privado: la BD canónica **`data/db/studio.sqlite` sí existe y ocupa 2.228.224 bytes**. El archivo de cero bytes `data/studio.sqlite` es una ruta antigua. Se añadió un suplemento sin alterar el inventario ni el informe originales. La lectura fue binaria, sin abrir un escritor ni restaurar datos. Esta presencia tampoco acredita backup/restauración de la biblioteca ext4 y sus assets.

Evidencia adicional local:

- [Informe original del backend](../../../../.cache/dev-cycle/m1/validation-20261010/backend/report.md).
- [Verificación del orquestador](../../../../.cache/dev-cycle/m1/validation-20261010/verify_backend_root.receipt.json).
- [Corrección de la ruta de BD](../../../../.cache/dev-cycle/m1/validation-20261010/backend/backup-path-correction/supplement.md).

## Correcciones después del sellado de QA

El formato de 13 archivos y un bloque de imports se integró mediante CAS y comprobación AST, sin cambios de lógica. Ruff nativo pasa; la revisión actual comprueba 157 archivos formateados. Los originales de QA permanecen intactos.

El idioma opcional se corrigió. Se conservan los dos fallos causales anteriores al cambio. La validación final pasa **203/203**, con lint, formato y contratos conformes; la cobertura del módulo completo `domain_routes.py` es **654/755 = 86,62 %, sin exclusiones**. La cobertura inicial del 73,77 % se amplió con escenarios reales de biblioteca, historial, autoría, sesión, linaje, papelera, assets y reintentos.

El bloqueo concurrente tiene causa reproducida **517 / SQLITE_BUSY_SNAPSHOT**: la primera preparación de FTS5 dentro de BEGIN puede leer una vista invalidada por otro commit. La reparación inicializa FTS5 en autocommit al conectar. Conserva BEGIN, los tiempos de espera y las barreras. Las fuentes finales pasan **37 casos y omiten uno en Windows; pasan 38 en Linux**, incluyendo persistencia y apagado del runtime. La cobertura del módulo completo `db.py` es **60/64 = 93,75 %, sin exclusiones**. El RED final sobre la fuente anterior conserva el error 517 y demuestra que la segunda fila no se había persistido.

Tres revisores con contexto fresco, A/B/D, leyeron el diff acotado y no encontraron defectos introducidos. D midió 107 pasos SQLite constantes con 0, 100 y 10.000 canciones; no hay recorrido proporcional a la biblioteca. El control de alcance pasa con 17 archivos, ninguno fuera de lo declarado y ninguna exclusión; la lente C no se activó. El orquestador verificó 79 artefactos de concurrencia, 16 SHA actuales, 203 casos JUnit y las coberturas originales a las 20:02:34 UTC. **La QA independiente posterior pasa: 349 casos y un omitido en Windows, 38/38 en Linux y 6/6 HTTP reales con `qa-gate` exit 0. Se acepta únicamente esta unidad CPU/API. M1 permanece NO-VERDE.**

La segunda unidad CPU/API queda aceptada tras corregir tres expectativas de HEAD de migración y pasar revisión 2 A/B/D. La QA independiente actual combina JSON y reintentos: **310 pruebas pasan en Windows; 300 pasan en Linux y diez controles WinEvent se omiten por plataforma**. Cero fallos y errores. La cobertura de módulos completos es 93,56 % para la guarda JSON, 100 % para la migración 0007 y 97,67 % para chains, sin exclusiones. Se preservan los rojos anteriores de dos fallos y 49 errores de preparación por plataforma. [QA actual de la unidad](current-head-fix-qa-2026-10-10.md).

El orquestador verifica 3.053 artefactos y los diez SHA de fuentes hasta terminar esa QA. Los seis casos HTTP y los 66 casos FIFO con un omitido son resultados históricos del mismo runtime, expresamente identificados; esta última ejecución no genera casos HTTP nuevos. **El verde correctivo CPU/API no cierra M1.**

También queda aceptada la custodia nativa del disco publicado: 19 pruebas funcionales, 17 de regresión y cobertura completa del 94,4 %. La revisión detectó una fuga de handles al fallar la entrada al contexto; se corrigió con RED/GREEN y QA nativa independiente. La raíz verificó 153 artefactos y ocho fuentes/dependencias. [Informe de custodia](t05/storage-binding-qa-2026-10-10.md).

El incremento del operador attach queda aceptado en su alcance técnico después de revisión 2 A/B y QA independiente: **72 pruebas funcionales, 19 de binding nativo y 14 de custodia Windows pasan**, con cobertura completa del 92,31 %, sin exclusiones. La raíz verificó 314 artefactos y 16 fuentes/dependencias. [QA del operador](t05/storage-attach-binding-qa-2026-10-10.md). Los comandos WSL se sustituyen explícitamente por dobles CPU; no se acredita attach real. La actualización del recibo por ruta no demuestra exclusión ni durabilidad: ReceiptLease se implementa en privado. Montaje ext4, commit durable, validated y detach permanecen pendientes. **M1 integral permanece NO-VERDE.** La nueva suite completa del backend termina con **2.185 PASS, 81 FAIL, 11 SKIP y cero errores**, en 1.070,43 s según el log. Pytest devuelve exit 1. La raíz comprueba el JUnit oficial y el terminal; la ejecución principal usa UID 10001, capacidades nulas y no-new-privileges. El desglose por causa, los focales del arnés y el sello final han terminado: no se interpretan los 81 fallos como 81 defectos ni se declara verde integral.

El orquestador verificó 3.275 artefactos de la primera QA y conserva dos entradas nativas que Windows no permite leer, sin atribuirles una verificación de contenido. Los 16 SHA de la primera unidad permanecieron iguales hasta terminar su QA; el cambio posterior del literal del head en un test forma parte de la segunda unidad.

Evidencia posterior:

- [QA independiente CPU/API](current-fixes-qa-2026-10-10.md).
- [Comprobación raíz de esa QA](../../../../.cache/dev-cycle/m1/validation-20261010/verify_fixes_qa_root.receipt.json).
- [Integración posterior pendiente de aceptación](../../../../.cache/dev-cycle/m1/validation-20261010/next-fixes-review/integration-receipt.json).

- [Revisión A](../../../../.cache/dev-cycle/m1/validation-20261010/review/lens-a.md), [B](../../../../.cache/dev-cycle/m1/validation-20261010/review/lens-b.md), [D](../../../../.cache/dev-cycle/m1/validation-20261010/review/lens-d.md).
- [Verificación raíz](../../../../.cache/dev-cycle/m1/validation-20261010/verify_fixes_root.receipt.json).
- [Entrega concurrencia](../../../../.cache/dev-cycle/m1/validation-20261010/concurrency-fix/APPLIED_REPORT.md).
- [Cobertura API](../../../../.cache/dev-cycle/m1/validation-20261010/language-fix/coverage-extension/handoff.json).

No quedan acreditados M-01 (motor musical real y escucha), M-02 (validación visual/manual) ni M-03 (backup/restauración de biblioteca persistente). La aceptación final de M0/T-13 sigue siendo una dependencia explícita de CA-01. Este informe conserva esas puertas; los verdes parciales no cierran M1.

## Unidades nativas pendientes de integración

El cierre idempotente de `Server` conserva un fallo causal de doble cierre y pasa revisión independiente A/B sin gaps introducidos. El candidato privado pasa 90 pruebas y obtiene 93,91 % de cobertura completa, sin exclusiones. Su integración y QA sobre fuentes actuales esperan al sello de la validación del backend.

La primera revisión del lease del recibo detectó dos defectos Important: reintento de cierre incierto sobre un handle reutilizado y lecturas concurrentes sobre un cursor compartido. El segundo candidato conserva ambos RED causales y pasa 38 pruebas, con cobertura completa de 97,99 %, sin exclusiones. Está en revisión 2 A/B; todavía no se ha aplicado ni aceptado. No acredita commit durable ni montaje físico.

## Suite actual sellada y comprobada

La raíz verifica **9.821 artefactos, 1.767 fuentes iniciales/finales, JUnit oficiales y terminales** a las 21:32:04 UTC. Los tres cambios de documentación autorizados se separan de las fuentes de producto. La entrada `added_documents` capturó el informe QA antes de su última generación; el hash final del sello sí verifica el informe actual. Una actualización posterior del ledger por revisión 2 también se declara aparte. Ninguno se oculta como fuente idéntica. [Informe completo](current-backend-full-qa-2026-10-10.md).

Los 81 fallos principales se desglosan en 39 relacionados con fixtures de credenciales, 19 por omisión del recibo FFmpeg del arnés, dos stubs de resolver incompletos, ocho hooks privados ausentes, diez incompatibilidades de plataforma/audio y tres resultados de custodia sin causa adjudicada. El focal nuevo con el recibo FFmpeg real pasa **19/19**; custodia con credenciales reales pasa **21/21**. IPC conserva **84/85** y un focal aislado rojo por el doble cierre. Estas ejecuciones se conservan separadas y no reemplazan el rojo de la suite principal.

La cobertura oficial de esta ejecución es **66,27 % para manifest.py y 75,19 % para pipeline.py**, sin exclusiones. Continúan por debajo del 80 %. Los verdes de API, SQLite y cola no sustituyen este gate. Los tres resultados de custodia pendientes corresponden a finalización normal, transporte EOF y saturación de la cola.

Después del sello, la raíz integra únicamente el cierre del helper por comparación exacta de dos preimágenes. La QA nativa independiente sobre esas fuentes actuales está en curso. ReceiptLease conserva B01/B02 corregidos, pero revisión 2 detecta B03 en la prueba: la reutilización de un HANDLE dentro de 512 aperturas no está garantizada. Se corrige sólo la prueba en un tercer candidato privado; el rojo independiente y todos los originales permanecen intactos. Las dos fixtures de resolución se reparan en otro candidato privado. **M1 sigue NO-VERDE; las tareas no se cierran.**

El componente de cierre del helper queda aceptado tras QA independiente actual: **91/91 Linux y 5/5 Windows**, cobertura completa **93,91 %**, sin exclusiones. La raíz verifica 102 artefactos y 17 fuentes, JUnit y terminales. [QA del cierre](t05/storage-helper-close-qa-2026-10-10.md). Los permisos efectivos, permitidos, heredables y ambientales de los hijos nativos son cero y NNP vale 1; el bounding set conserva las cinco capacidades acotadas del setup del arnés, descritas expresamente. **La aceptación de este componente no cierra T-05 ni M1.**

El lease del recibo existente queda aceptado únicamente en su alcance nativo tras revisión 3 A/B y QA actual independiente: **38/38 pruebas**, cobertura completa **97,99 %**, sin exclusiones. La raíz verifica 91 artefactos y seis fuentes/dependencias. [QA del recibo](t05/storage-receipt-lease-qa-2026-10-10.md). Conserva todos los rojos causales y el fallo previo de precondición del allocator; la prueba actual comprueba ausencia de reintento con ocho testigos nativos sin exigir reutilización. El lease no acredita escritura, commit durable ni lifecycle de montaje. **T-05/M1 permanecen abiertos.**

Las fixtures del resolver quedan aceptadas tras revisión A/B y QA independiente actual: **18/18 Windows y 18/18 Linux**. Root verifica 400 artefactos y 182 fuentes; solo se completan dos campos del doble conforme al contrato existente. [QA del resolver](t07/domain-resolver-fixtures-qa-2026-10-10.md). Cobertura de runtime modificado: n/a. T-07/M1 siguen abiertos.

Diagnóstico Linux de los tres focales aceptado por root: 867 artefactos y 32 comparaciones de fuentes verificadas. Se prepara corrección privada de la carrera terminal y de barreras de estímulo; todavía sin aceptación de fix. El candidato test-only de audio obtiene en Linux 180 pasadas y cinco omisiones de casos Windows; cobertura oficial completa manifest84,31% y pipeline96,24%, fuentes runtime intactas. Windows conserva siete fallos y16errores teardown por transición de un bit de atributos de carpeta; su semántica todavía se investiga, ahora en diagnóstico privado independiente. Estos son resultados de implementación, pendientes de revisión y QA; **M1 continúa NO-VERDE**.

Las pruebas portátiles de audio quedan aceptadas **en Linux** tras revisión A/B, CAS y QA actual independiente: **180 pasadas y cinco omisiones de casos Windows**. Cobertura oficial completa del manifiesto **84,31 %** y del postproceso **96,24 %**, sin exclusiones. Root verifica 307 artefactos, 237 fuentes y 19 imports privados. [QA Linux de audio](t05/audio-portability-linux-qa-2026-10-10.md). Windows sigue rojo y su corrección está en desarrollo privado; esta aceptación conserva el SHA del runtime anterior. No acredita M1/T-05 ni multiplataforma.

La corrección de identidad de directorio se integra por CAS a las22:12:39UTC tras revisión A/B sin hallazgos: ignora exclusivamente el bit incidental observado en directorios y conserva las demás señales y las guardias de custodia. El candidato obtiene Windows213PASS13SKIP yLinux207PASS19SKIP, cobertura completa pipeline96,32%, helper94,44%/88,89% sin exclusiones. Son resultados de implementación, no QA aceptada: **la QA independiente actual está en curso**. Pipeline ahora32f7fba8.../helper03e2b66b...; las pruebas anteriores con11f72.../da1fb... quedan congeladas. La corrección de custodia Linux sigue privada y su cobertura del supervisor aún no alcanza80%; M1 no se cierra.


## Actualización verificada — 22:21 UTC

La corrección de identidad de directorios obtiene aceptación del componente tras QA independiente sobre las fuentes actuales: **213 pases y 13 omisiones justificadas en Windows; 207 pases y 19 omisiones en Linux; cero fallos y errores**. Cobertura completa del postproceso **96,32 %** y del helper **94,44 % / 88,89 %**, sin exclusiones. ROOT verificó 1.050 artefactos, 379 fuentes/herramientas y los cuatro gates oficiales. [Informe QA actual](t05/directory-attributes-current-qa-2026-10-10.md). Los resultados anteriores con fuentes congeladas se conservan como históricos.

**M1 sigue sin verde integral.** El E2E de publicación persistente, Range/recovery/backup y las aceptaciones manuales siguen pendientes. La corrección de custodia Linux permanece privada: supervisor **75,46 %**, inferior al gate; además el último positivo de audio instrumentado falla y su causa sigue pendiente. No se acepta ni integra ese candidato, ni se inicia M2/T-02.


El fallo de audio al añadir instrumentación tiene causa comprobada: el arnés intentaba serializar una ruta Path a JSON antes de ejecutar FFmpeg. Ambos controles, con y sin save, reproducen TypeError/status126; esto no demuestra fallo de codec ni del modelo musical. ROOT verifica los artefactos y comienza la corrección exclusiva del arnés. La aceptación de custodia sigue pendiente: el supervisor aún no alcanza la cobertura requerida y los ocho negativos requieren su fixture de fallo explícito. También se diseña el controller de almacenamiento durable que falta para commit, recuperación, validated y detach. Ninguna de estas unidades está integrada ni sustituye el E2E persistente.


Actualización ROOT 20261010T225218Z: custodia candidata whole88,32/80,78% gate0 y evidencias verificadas, revisiónA/B/D/QA/CAS pendientes. Diseño durable O2 elegido; A1A01Important/A02Minor corregidos privados, recheck2 pendiente; B1sin defectos. Codec/store/lifecycle sin implementar. Contratos exportadosvigentes exit0. T-05/M1 siguen NO-VERDE.


Actualización ROOT 20261010T230433Z: diseño durable O2/ADR0075 adoptados conreview2A/B yQA205+42docchecks140enlaces/18artefactos verificados, codigo/QAreal pendientes. Custodiareview1A+B+Dsin gaps/CAS4sources22:57:58; QAactual en curso tras errorespreparación conservados, no verde. U1codecwireW1–W6ratificado/actorprivadoTDD. T-05/M1 NO-VERDE.


Actualización ROOT 20261010T231217Z: custodia Linux aceptada como componente tras QA actual52+7, whole88,3212/80,7780 % sin exclusiones, ROOT2312artefactos/109fuentes/62imports. Informe testing/t05/linux-custody-current-qa-2026-10-10.md. Controller durable aún privado U1; M1 NO-VERDE.


Actualización ROOT 20261010T232910Z: custodia Linux aceptada componente52+7/whole88,32-80,78% (informe t05). U1 codec sólo candidato200Windows+200Linux/whole94,6367%sinexcl; ROOT171artefactos/tar170regulares/rawSQLite actuales verificados. Revisión1A+B3Important verificados: statusmutable, history/published bool-int igual aunquebytesdistintos, JSON5000digitsValueError sinclasificar. CorrecciónTDDfix1privada en curso; review2/QAindependiente/CAS pendientes, no implementacióncanónicaU1. Diseño/wire/API privados revisados como3paths scope0; NTU2brief14fuentes actuales comprobadas, sin code/probes/liberación. M1 NO-VERDE, estados sin cierre.


Actualización ROOT 20261011T070007Z: U1codec puro aceptado tras A/Breview2sin gaps/QAactual208+208/receipt3+3/whole95%0excl; CAS3sourcesbyteidénticas yfreezeG0. [Informe](t05/storage-journal-codec-current-qa-2026-10-11.md). T05/M1 NO-VERDE: NTU2sin código, G2ACLpendiente, lifecycle/ext4/VHDX/Range/recovery/backup/E2E/manuales/Git pendientes. QAactor entrega sellada completa antes de fallo de uso de su chat final; ROOTverified74artefactos/13sources/raws/tar14regulares.


## T-05 — preparación NT experimental y decisión G2 de ROOT

ROOT verifica el inventario sellado de 14 archivos del probe G1/G3, sus 15 entradas de custodia y fuentes U1 intactas. Control02 nativo exit0: aperturas relativas, creación exclusiva y sharing bilateral; handles192→203→192, cierres únicos con revocación previa y procesos propios restantes0. Intento01 exit1 y delta+1 se conservan: no se atribuye baseline limpio. Son instrumentos experimentales sin imports de producto ni crédito TDD. G3 permanece cerrado en esta entrega: Flags15 no completamente documentados por FileStorageInfo, cero escritura/flush/relectura. No se acredita durabilidad ni aceptación de U2/T05/M1. Namespace congelado storage-nt-abi-preparation-20261011.

Diseño G2 privado f85559c6 presenta S1/S2/S3 y contraejemplo de replay tras restart. ROOT elige S1 para producción, con excepción exacta TrustedInstaller sólo en el ancla de sistema por acreditar; S2 únicamente evidencia limitada de lease. S3 se aplaza hasta resolver bootstrap, asociación activa independiente y custodia de código. La política estricta rechaza grants peligrosos de outsiders sin cambiar ACL existentes ni adoptar SMOKE. Candidato documental privado en preparación, aún sin ratificación canónica ni liberación de implementación U2. Una lectura por nombre no acredita descriptor por handle. Se libera sólo un nuevo experimento G3 mediante NtQueryVolumeInformationFile, sin reinterpretar bits de FileStorageInfo; resultado pendiente.

Medidor ROOT m1/lote-nt-security-abi-preparation activo desde07:02:28Z; sin marcadores de actores ni cifras reales inventadas. T05 y M1 siguen abiertos; persistencia, lifecycle, Range/recovery/backup, E2E y manuales pendientes.


T-05 ROOT 20261011T071520Z: nuevo experimento G3 verificado8artefactos/14previosintactos; consulta NT independiente clase11/status0/info28, E/S sin caché alineada131072 bytes→Flush→relecturaexacta/samehandle/reopen, identidad intacta/handles192→203→192/PID0. No reinterpretar FileStorageInfo ni afirmar durabilidad/64slots/crash. [Informe](t05/storage-nt-preparation-2026-10-11.md). Archivos declara política S1 y ADR0076 por decisión de ROOT, candidatos aún sin aceptar. U2/T05/M1 abiertos; no modificaciones ACL existentes.


## T-05 ROOT: política NT S1 incorporada y preparación nativa verificada — 20261011T074038Z

**Revisión de dos lentes — intento 1** documental: A29/B6 criterios,0Critical/0Important/0Minor; C/D no seleccionadas para prosa. [Tablas completas](t05/storage-nt-security-s1-review-2026-10-11.md). [QA fresca](t05/storage-nt-security-s1-qa-2026-10-11.md):64/64exit0,91entradaspre/post,8artefactos sellados; ROOT verifica antes del CAS07:34:48UTC. Cuatro documentos adoptados; cinco reemplazos exclusivamente de metadatos acreditados, originales distintos de SHA finales. TDD n/a:prosa. No cambia wire/runtime/estados.

G2 experimental:27artefactos/6PIDs propios restantes0; descriptor por handle confirma dos outsiders MODIFY en padres, por lo que admisión completa S1 permanece cerrada. Fixture nuevo protegido al crear demuestra sólo leaf/lease. Cold GetSecurityInfo+8 y ConvertStringSD+7 handles, repeticiones0; controls tras calentamiento170→179→170, no se afirma identificación de handles OS. Symlink privado rechaza1314; negativo reparse real pendiente, sin privilegios/remediación ACL.

G4 experimental:25artefactos/5PIDs restantes0;73writes exactas contiguas sobre75563008B de ceros→Flush→73reads exactas completas, SHAa09d7ea396297c226ba6b6b3f9a6b81a450d91bb4c8265bf73e88f0b55dcdefe. EOF75563008/Allocation82837504 (no cuota exacta), un stream::$DATA, sin sparse/compression, ID/SD intactos. Tres fixtures conservadas. Diagnósticos de streaming hash preservados; liberar dos objetos hash propios devuelve baseline173→184→173, no cierre de handles opacos. ROOT verificó25artefactos y225MB de fixtures antes del CAS. [Informe nativo](t05/storage-nt-preparation-2026-10-11.md).

Sin journal de producción, commit, crash, ACK, durabilidad eléctrica, ext4/WSL/admin ni aceptación T05/M1. Próxima unidad U2a: lector/parser/política local readonly con TDD, sin store completo; release explícita posterior de ROOT, no derivada de estos experimentos. G1reparse/G2cadena/lifecycle/controller/E2E siguen pendientes.


## T-05 ROOT: U2a en revisión y nueva validación backend — 20261011T081114Z

Candidato U2a congelado, aún ausente canónicamente: sólo `scripts/storage_journal_windows.py` y `tests/test_storage_journal_windows.py`. ROOT verifica368 artefactos,48 registros de etapas RED/GREEN (no48 rojos válidos),18 inputs de revisión, scope2/0fuera/0warnings. Actor Windows66PASS y whole97,0027% (247/253 statements,109/114 branches,excluded0); Linux manual real UID10001/rednone/readonly/NNP con dos PLATFORM_UNSUPPORTED y cero DLL, sin pytest/JUnit inventados. **Evidencia de actor; QA fresca y aceptación pendientes.** SHA candidato805b4abfee03d20da2afa8422f4c425f542998f356eb9894fd49c1355fb6f8dd / test6671dbfccab19f2b9c8f7295b83513ebd21413d12759c0774de54d28f2bc5ad5.

Revisión A/B fresca en curso; C de seguridad exigida explícitamente por release, aunque selector automático no detecta este módulo WinACL. Overlay privado de revisión selecciona C=true y D=false; no cambia dev.json canónico. TDD original preservado: máscara unknown-standard mal elegida no cuenta RED; etapa12 coverage existente sin RED nuevo. Revisión verifica ley TDD sobre implementación/errorpaths, sin otorgar conformidad adelantada. ROOT restauró un helper propio de inspección al SHA exacto congelado; preimagen posterior y recibo repair se conservan, sin alterar los dos archivos de producto/test.

G1 experimental con junction real: ROOT16artefactos/74previos/8sources/PIDs0 verificados. NtCreateFile abre alias mismo; tagreparse/ID distinto exige rechazo por metadata. Sin traversal, sentinel60B intacto. Exit1 original contador170→171 conservado; mínimo independiente UUID145→146 y control separado146→146. No corrección retrospectiva/handleopaco/repetición artificial. [Informe](t05/storage-nt-reparse-experiment-2026-10-11.md). NoG1full/G2/producción.

Backend fresco en curso en imagen CPU existente pinned. Native52/52,IPC90/90,custody21/21 tienen ejecuciones reales exit0 y exportaciones verificadas por el actor; aceptación ROOT pendiente del sello/selección/imports/coverage/cleanup. Principal2153nodos sigue ejecutándose tras readiness real de tres raíces temporales, tmp_path_factory, FFmpeg y credenciales. Diagnósticos previos de arnés conservados: rutas fuera de .cache y fuentes audio omitidas impiden atribuir esas ejecuciones a QA completa. Corrección exclusivamente de preparación, no relaxmarks ni tests producto. Cruce offline de81fallos históricos con testigos focales sólo es índice candidato, no verde global actual ni81bugs resueltos.

Marker ROOT activo `m1/lote-u2a-review-backend-qa`; anteriores cerrados sin solapamiento. Tokens/eur/horasIA realesnull; no asignaciones inventadas. T05/M1/estados sin cambios; contrato S1 mantiene admisión completa cerrada ante MODIFY outsiders, U2a sólo diagnóstico readonly. Ext4 persistente/lifecycle/recovery/backup/Range/E2E/escucha/Git siguen pendientes.


## Revisión de dos lentes — intento 1: T-05/U2a — 20261011T081819Z

**A/B/C frescas:0Critical/1Important/0Minor. A01 confirmado y abierto; no adopción.** [Tabla completa y evidencia](t05/storage-nt-security-u2a-review1-2026-10-11.md). A61PASS/5deselected; B62PASS/4deselected; C61PASS/5deselected+5controlesnative readonly; se solapan y no se agregan como suite. Native/rawSD/hash368/48registros preservados, dos targets exactos. Scope2/0/0. Selector auto Cfalse/Dfalse; C mandatoria por release. Entrada suplementaria absoluta produjo D por .cache de evidencia; raw conservado, corregido a paths relativos y fuentesexactas: Ctrue/Dfalse/0warnings, sin config canónica editada.

| ID | Grado | Tarea | fichero:línea | Escenario | Veredicto |
|---|---|---|---|---|---|
|A01|Important|T-05/U2a CA3|scripts/storage_journal_windows.py:305;tests/test_storage_journal_windows.py:473,598,616|09green contiene errores/cleanup ya implementados;25tests de12-existing-behavior posteriores pasan contra esa preimagen|Confirmado,pendingFIX1|

ROOTrelease FIX1 sólo dos archivos en snapshot nuevo, actor fresco implement_u2a_fix1. Ley tdd: borrar código anterior altest y reescribir después de RED auténtico, no cobertura retrospectiva. Implementer comunica42nodes aislados causalesrojos después de borrar segmento y antes de reescritura; primerharness42exit4porargv inválido conservado sin créditoTDD. Esto aún es evidencia de actor, recibos/rootverificación/handoff/review2 y QA independiente pendientes. Originalfreeze805b4a/6671db intacto; no transferir su Linuxmanual al SHA nuevo. T05/M1/checkboxes sin cambios.

UsageROOTreviewbatch cerrado08:15:27Z/reloj12m/estimado, realesnull; markeractivo m1/lote-u2a-fix1-backend, sin solapamiento ni costes individuales inventados. Backendprincipal continúa tras readiness válida; grupos52/90/21 no se repiten. Provenance main/native sys.modules exactos; credential90/21 sólo guard-before-import seals+coveragefilenames, no sys.modules retrospectivo. No declarar verdeglobal antes de rawfinal/seal/cobertura/partición/cleanup.


## Revisión de dos lentes — intento 2: T-05/U2a FIX1 — 20261011T082913Z

**A01 corregido; A/B/Cfresh0Critical/0Important/0Minor.** [Tablas completas](t05/storage-nt-security-u2a-review2-2026-10-11.md). ROOT1419artefactos+142inputs+42pairs/84JUnitindividuales/actor66PASS/whole97,1279370excluded/scope2/0/0verificados. Prefix/parser/policy/ABI/tests byteexactos; runtime91e279nuevo, original805b4a intacto. Los25tests posteriores ahora preceden reescrituraauténtica después deRED. Los42exit4previos no cuentan. Originalfreeze368 sigueexacto. Ctrue/Dfalse conoverlayonlyreviewconfig y pathsrelativos; dev.jsoncanónico intacto. ReviewerA/B62PASS4deselected yC61PASS5deselected+nativecontrolsreadonly, conjuntos solapados/no sumar.

| ID | Grado original | Veredicto | Evidencia |
|---|---|---|---|
|A01|Important|Corregido|delete/stubs42RED→reescritura08:16:43→42GREEN;84JUnit/pinsraw verificados|

Evidencia TDD actual por criterio, copiada por ROOT tras verificación del handoff (fase local, no cierreT05):

RED: tests/test_storage_journal_windows.py::test_portable_platform_rejects_without_loading_dll falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_native_principal_matches_independent_token_user falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_native_closed_descriptor_read_borrowed_handle falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_native_outsider_effective_grant_rejected[write-data] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_native_outsider_effective_grant_rejected[write-dac] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_native_existing_host_parent_rejects_without_mutation falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_faults_are_closed_and_cleanup_once[status] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_faults_are_closed_and_cleanup_once[missing] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_faults_are_closed_and_cleanup_once[invalid] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_faults_are_closed_and_cleanup_once[oversize] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_faults_are_closed_and_cleanup_once[control] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_faults_are_closed_and_cleanup_once[inconsistent] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_faults_are_closed_and_cleanup_once[cleanup] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_reader_baseexception_and_cleanup_primary_preserved falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[impersonation] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[thread-denied] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[process-missing] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[process-failed] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[size-large] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[size-error] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[size-success] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[query-failed] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[query-size] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[pointer-outside] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[pointer-prefix] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[truncated] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[invalid-sid] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[native-invalid-sid] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[native-length] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_double_principal_error_contract_and_close_once[cleanup] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_cleanup_invalidates_owned_pointer_before_callback falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_principal_rejects_pseudo_handle_without_closing_it falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_borrowed_scalar_validation_never_closes_it[None] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_borrowed_scalar_validation_never_closes_it[True] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_borrowed_scalar_validation_never_closes_it[0] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_borrowed_scalar_validation_never_closes_it[-1] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_borrowed_scalar_validation_never_closes_it[18446744073709551615] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_borrowed_scalar_validation_never_closes_it[18446744073709551616] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_borrowed_scalar_validation_never_closes_it[handle6] falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_principal_baseexception_primary_and_cleanup_separated falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_native_load_error_is_typed falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.
RED: tests/test_storage_journal_windows.py::test_cleanup_without_primary_exception_is_typed falló con NotImplementedError (portable: assertion PLATFORM_UNSUPPORTED sobre stub) · 2026-10-11; GREEN exit0 individual.

QA independiente preparada conrelease privada storage-nt-security-u2a-qa-20261011, sólo lector/políticafreshWindows y LinuxrealnuevoSHA; noadopciónantesQA. Backendfuncionalactual actor2298PASS18SKIP/0FAIL/0ERROR en4gruposdisjuntos, selloROOTacceptancependiente. No80cadaarchivoglobal niM1green. MarkerROOT m1/lote-u2a-review2-backend; métricas realesnull. No checkbox/estado modificado.


## Validación actual CPU y adopción T-05/U2a — 2026-10-11T08:42:29.270073+00:00

ROOT acepta el backend CPU actual en cuatro grupos disjuntos:2298PASS18SKIP0FAIL0ERROR/2316JUnit/0duplicados. Verificación independiente53132archivos/3332196132bytes/1770fuentesactuales/4TARcausales; propiosPID0. [Informe backend](current-backend-post-components-qa-2026-10-11.md). Los81nodos históricos exactos se cotejan:77PASS4SKIP0ausentes; originales rojos intactos. Whole80archivos/8por debajo80; afectadosmedidos>=80conIPCbranch separado, no verdeglobal de cobertura. ImagenCPU/persistenciatmpfs no acreditaext4producto. Procedenciagruposcredencialeslimitada explícita.

U2aFIX1 aceptada en alcance lector/política tras review2A/B/C0gaps y QA fresca66PASSWindows/43PASS23SKIPLinux, exit0ambos. Wholeoficialcombinada259/265lines+113/118branches=97,127937%,0exclusiones/gate0; Linuxindividual76,501305%honesto. ROOT173payload+78snapshot(20fuentes/58Gitprivado)+9suplementobufferingverificados; JUnit/coverage/imports/TARexactos y recursospropiosreaped. Windowsstdoutfinal1574B autenticadofreeze,noPOSTprevio; sueltabúfer posterior, norepetirtests. Contadorinitialfixture+8conservado,100consultasplateau/cierrepropio−1; noocultarbaselinefailed.

ROOTCAS dosfiles nuevos ausentes 2026-10-11T08:42:29.270073+00:00: scripts/storage_journal_windows.pySHA91e279775c20561b14679845066f334f3af6d30fdc0a41a92ce5d0ee24af4b70 y tests/test_storage_journal_windows.pySHA6671dbfccab19f2b9c8f7295b83513ebd21413d12759c0774de54d28f2bc5ad5, bytesQAexactos. [QA actual](t05/storage-nt-security-u2a-current-qa-2026-10-11.md). Freezeacceptedprivado en storage-nt-security-u2a-root-20261011/adoption-root.receipt.json.

Diagnóstico local no capacidad; G2cadena sigue rechazado, bootstrapTI/store/writer/ACK/ext4/lifecycle/E2E/manuales pendientes. T05/T15/M1 siguen abiertos, sin checkbox/estado/Git/ACL/datos alterados. Próximaunidad U2baperturarelativaexistentes/metadata/geometríareadonly aún sinrelease; no creanobjetos ni autoridad. MarkerROOT m1/lote-u2a-qa-backend-accept, tokens/eur/horasIA realesnull.


## T-05: release de apertura relativa y metadata — 2026-10-11T08:48:25.614820+00:00

U2a aceptada y congelada por ROOT tras revisión2 A/B/C y QA independiente. Se libera U2b1 al actor fresco implement_nt_observation_u2b1 en snapshot privado storage-nt-observation-u2b1-20261011: sólo FILE_OPEN de hijos existentes, metadata por el mismo handle y cierre local. Geometría se reserva para U2b2. Es división de la implementación O2/S1 ya aprobada, no un nuevo plan ni una ampliación de autoridad.

Base privada612dbb9388c86cdcca4e99e4bb70a2695bff2f2d;22fuentes/inventario actual, runtimebase91e279/testbase6671db. Release y recibo privados conservan el brief del plugin íntegro; preimágenes aceptadas y cuerpos/tests U2a no se refactorizan. Política de sincronía ratificada: NTretorno distinto dePENDING gobierna; pending/entered sinretorno no concede salida ni close, arenas y owner vivos hasta reap, contexto revocado. Retener un scalar no acredita custodia del prestado. Caller confiable debe conservar adquisición; los tests de contingencia se ejecutan en hijo propio y no prueban pendingnativo.

TDD causal obligatorio antes de cada cuerpo inclerrores/cleanup; revisión fresca A/B/C y QA independiente antes de CAS. Sin geometry/create/store/writer/ACK/bootstrapTI/fullchain/CLI/admin/WSL/ACL existentes/datos. TDD n/a del release documental. No estados/checks alterados. Marker anterior m1/lote-u2a-qa-backend-accept cerrado08:42:57Z (13m reloj, no horasIA); activo m1/T05-U2b-observacion-NT. Tokens/eur/horasIA realesnull.


## T-05/U2b1 candidato y revisión en curso — 2026-10-11T09:14:54.896636+00:00

Candidato privado congelado, no adoptado: apertura relativa FILE_OPEN existente, metadata Win32 y close/context. Runtime1556847e29c4e5ba08486765ededaf80110b7851a715ad83bfd415dd76dc5c29; tests11e598146a73ded9bb144c113baa0e75a379379c8473b2d408204c390e662093. ROOT verifica1242payload/5reparse stat-only sin traversal,22inputs,18defsU2a/31defs-tests exactas,100runs individuales54RED46GREEN y112PASS (66U2a+46nuevos). Ocho REDcleanup con adquisición válida superseden bootstrap sin adquisición; originales inválidos conservados y no acreditados como causal. Whole485/520líneas93,2692%,159/178ramas89,3258%,combinado92,2636%,exclusiones0/omitvacío/pragmas0; Ruff0. Nativecold151/importwarm170/fixturewarm171/open172/close171 (12iteraciones)/ownerclose170: +19inicialhonesto,sin allocatorreuse. PENDING/unknown son dobles propios con8childreaps, no pendingnativo ni durabilidad.

Revisión fresca intento1A/B/C activa en storage-nt-observation-u2b1-review1-20261011, baseprivada901701760860b52488cd166556652c6f3cd6a518. Scope2filesexit0,0avisos/0exclusuario. AutoCfalseDfalse; overlay sólo revisión Csiempre produceCtrueDfalse sin alterar dev.json. B informaB01Important pendiente: interrupción tras retornoSTATUS_PENDING/pre reconocimiento puede liberararena y permitir siguienteoperación; reproducción/fullfusion pendientes. No se acepta candidato con gap abierto. QA independiente preparada, aún no ejecutada ni autorizada antes reviewlimpia; CASposterior. Fuente U2a canónica91e279/6671db intacta. GeometríaU2b2/bootstrap/store/writer/ACK/fullchain/ext4/lifecycle/E2E/manuales/Git pendientes; T05/M1abiertos y cero checkbox/estado modificado. Meterimplementación cerrado,revisión m1/T05-U2b1-review1 activo; tokens/eur/horasIA realesnull.


## Revisión de dos lentes — intento 1: T-05/U2b1 — cuatro Important pendientes

A+B+C frescos, Dfalseporselector. ROOT2026-10-11T09:20:39.783534+00:00fusiona0Critical4Important0Minor,sinrebates. Csinseguridadnueva; A01TDDyB01-B03corrección bloqueanCAS/QA. [Informe completo](t05/storage-nt-observation-u2b1-review1-2026-10-11.md).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Cleanup sin primaria implementado sin RED/test; runtime:558 | T05/U2b1 | pendiente FIX1: borrar sólo __exit__nuevo a stub→RED válido→reescribir; no restaurar cuerpo anterior | LenteA100runs/coverage558missing/probepropioexit0; defecto disciplina,no bug funcional |
| B01 | Important | KeyboardInterrupt posPENDING/pre reconocer libera arena, no poison; runtime:486 | T05/U2b1 | pendiente FIX1: ampliar custodia/cobertura transición, REDregresión previo | Bdouble5hijos;ROOTsinglefault/control6hijosreaped:arenadead/nextoptrue vscontrolalive/false |
| B02 | Important | KeyboardInterrupt posCloseHandle/pre publish permite retry con None; runtime:534 | T05/U2b1 | pendiente FIX1: estado idempotente reservado antes, REDregresión previo | ROOT[202,None] vscontrol[202],actualfakeNonefalse/retention |
| B03 | Important | KeyboardInterrupt posSUCCESS/pre registrar pierde adquisición; runtime:621 | T05/U2b1 | pendiente FIX1: arena/owner durante transfer, REDregresión previo | ROOTopen1/closed[]/owner0/retainedfalse vscontrolclose202 |

T05/M1abiertos. FIX1fresco requiereREDcausalantesdecódigo;A01borrar/rewrite__exit__sintest,UAaceptadaintacta.Geometría/bootstrap/store/ACK/ext4pendientes. LedgerúnicoROOT,sincheckbox/estadosalterados.


## T-05/U2b1 FIX1 autorizado — 2026-10-11T09:24:56.242765+00:00

ROOT delega cuatro Important a actor fresco implement_u2b1_fix1 en storage-nt-observation-u2b1-fix1-20261011/snapshot. Release dbc9799b2f70d54ea86b1095cf16cdf61a81821074b63aafbeb466cc206943f2,23 fuentes/base privada431ae3357a35177b59081364d93434fe77abfb42. Ownership sólo dosfuentes/evidencia; preservación U2a/112nodosprevios; A01stub→RED→reescritura y B01-B03regresionesREDprevio. Revisión1completa y ROOT6hijosdobles corroboran bloqueo. ReviewerB yCJUnit47cadauno son exactamente47nodos iguales tras normalizar sólo prefijo cápsula; no94. ROOTverifica28payload por cápsula/8reapreceipts cada una sintraversal; importpathactualnoinstrumentado,noatribuirsys.modulescaptura. Jiraenabledfalse,nooperacionesexternas. Meterreview1cerrado09:22:58Z/ventana12mrelojnoIAmedida; activo m1/T05-U2b1-fix1. QA preparada bloqueada hasta review2limpia; cero adopción/checkbox/estado. T05/M1abiertos; geometryU2b2 y ext4/integración amplio pendientes. Tokens/eur/horasIA realesnull.


## Revisión de dos lentes — intento 2: T-05/U2b1 — A/B/C sin gaps pendientes

ROOT 2026-10-11T09:46:46.890459+00:00:0Critical/Important/Minor; cuatro Important intento1 corregidos,sinrebates,deudanula. Dfalse selectorauto/overlay,canondevauto intacto. [Tablas e informe](t05/storage-nt-observation-u2b1-review2-2026-10-11.md).

| # | Grado inicial | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Cleanup sin primaria escrito sin RED | T05/U2b1 | corregido: __exit__ borrado a pass, RED causal válido, reescritura distinta anterior | A2 verifica source-before/UTC/hash/JUnit; escenario propio PASS |
| B01 | Important | PosPENDING liberaba arena y dejaba operar | T05/U2b1 | corregido: custodia y poison cubren transición posretorno | B2/C2/A2 fault/control, arena/owner vivos, cero close/segunda operación |
| B02 | Important | Posclose permitía retry CloseHandle(None) | T05/U2b1 | corregido: reserva idempotencia/revocación/retención de unknown | Fault/control [202] una vez, sin None; 8close transiciones adicionales |
| B03 | Important | SUCCESS antes de registro perdía adquisición | T05/U2b1 | corregido: arena/owner durante transferencia y constructor | Fault/control custodia/no nueva operación;11open transiciones adicionales |

ROOT588payload/23snapshot/6pares/139actorPASS/74reviewernodosúnicos verificados; wholelíneas95,514%/ramas91,758%0excl. QAactualWin/Linux y CAS posteriores; nadaadoptado, T05/M1abiertos. No pendingnativo/nofugasglobal/cadena/store/ACK. Marker m1/T05-U2b1-review2 activo hasta releaseQA; tokens/eur/horasIA null.


## QA independiente U2b1 en ejecución — 2026-10-11T09:54:02.676802+00:00

ROOT autoriza y delega a qa_u2b1_current tras revisión2 A/B/C sin gaps. Release450e23fafb38f6d35c95fb3d2b6f07a88d00098c197085cf3cbbf5b3166bf305,24fuentes readonly; candidatoaf192/f36ada. QA actual Windows/Linux unidadCPU, cobertura whole e imports/procesos/artefactos auténticos pendientes; no adelantar resultados. Canon91e279/6671db permanece intacto. Marker m1/T05-U2b1-QA activo, review2 cerrado09:48:33Z/reloj11m noIAmedida. Sólo ROOT ledger; tokens/eur/horas reales null. T05/M1 abiertos.

Contenedores QA próximos: exportar/verificar evidencia y PID0 antes de retirar únicamente el contenedor propio. Los históricos se retiran cuando su archivo está verificado; ACE y otros stacks intactos. No prune global.


## QA U2b1 intento1 rojoLinux y release FIX2 — 2026-10-11T10:04:46.269785+00:00

Windows139PASS; Linux105PASS29SKIP5FAIL. Whole90,6555/78,1032/combinada92,3291%0exclusiones: gatecobertura0, funcional1. ROOT392payload/1reparse/24fuentes/54hijos/TAR134/imports/streams/PID0rm verifica. Causa fixture ctypes.set_last_error ausenteLinux, closed[],retained; cuatrocascadas. No bugkernelWindows demostrado ni aceptaciónconjunta. [Informe](testing/t05/storage-nt-observation-u2b1-current-qa-2026-10-11.md).

ROOT autoriza FIX2fresco sólo test false_query/canal last_error scoped Linux; runtimeaf192 fijo, canon91e279/6671db intacto. debug-root-cause F1–F3/controlanteseditar y regresión real; nofalseTDD nuevo runtime. Revisión y QA intento2 pendientes. Marker m1/T05-U2b1-fix2; T05/M1 abiertos, tokens/eur/horas reales null. Cuatrocontenedoresbackenddetenidos conTARverificadosretirados; ACE intacto. Git integración pendiente: HEAD8663287 desde6octubre, rama compartidam1/t-02-esquema dirty; no mezclar archivos pendientes ni hacer stageglobal/pushciego.


## Git: primer lote aceptado commiteado y subido — 2026-10-11T10:09:35.132654+00:00

ROOTcommit7822b4d88519fa852d3987795fc3d32a3520dcb5 en m1/t-02-esquema, push a origin y ls-remote exacto. Cincoarchivos: runtime/test U2a91e279/6671db y tres informes revisión1/revisión2/QA. Sólo componente seguridad yaROOTaceptado; no declaraT05/M1cerrados ni publicaU2b1privado. Índicevacío antes/después; stage explícito cincoarchivos, sin stageglobal/reset/checkout/merge/forcepush. Worktreefuentes byteexactas despuéscommit. Esto es excepción ROOT acotada al guard de integración de checkout compartido: todoslos demás cambios pendientes permanecen fuera delcommit; actores trabajan sólo snapshotspropios sinGit. Contenedores4backendretirados trasTARverificados, informesintactos/ACEUp.

FIX2test-only actor informaWin139PASS/Linux110PASS29SKIP, candidato020aeffe612e1c43aa1c420c4f969babfabf277f269ca96050d6d6c7d9c5adfe/runtimeaf192 sin cambio; informe/freeze, ROOTverificación, revisión nueva y QAintento2 aún pendientes. No adoptar ni cerrar por el resumen. MarkerFIX2activo.


## T-05/U2b1 FIX2 verificado; revisión 3 en curso — 2026-10-11T10:21:08.615505+00:00

ROOT verificó 470 payloads regulares y 1 reparse por stat, 25 fuentes privadas y cambio exclusivo a false_query. Runtime af192 byte exacto; tests020aeffe. QA1 frozen392 permanece íntegro. F1 reproduce fallo de fixture Linux sobre f36ada, F3 control mismo SHA pasa; F2 propio posterior F3 (diagnóstico QA1 ya leído). Harness inicial reconstruido posterior declarado, sin atribuir sello contemporáneo. TAR/streams/reaps verificados; 27 hijos nuevos Windows y 27 Linux reaped exit0. Actor final139PASSWindows/110PASS29SKIPLinux, mismos139nodos y29skips; resultados actor no sustituyen QA.

Scope-check revisión3:1 fichero,0 fuera de alcance/avisos; C/D auto false. Base privada9e27683. Lentes frescas A/B despachadas. Código canónico U2a91e279/6671db intacto, sin CAS. Revisiones anteriores conservadas; sólo se reevalúa FIX2 con evidencia nueva. T-05/M1 abiertos, ext4/store/ACK/lifecycle/E2E/manuales pendientes. Marker ROOT activo m1/T05-U2b1-review3; FIX2 cerrado. Tokens/eur/horas IA reales null.

Evidencia: `.cache/dev-cycle/m1/storage-nt-observation-u2b1-review3-20261011/verification-root.receipt.json`, `prepare-root.receipt.json` y `record-root.receipt.json`.


## Revisión de dos lentes — intento 3: T-05/U2b1 FIX2 — A/B sin gaps

ROOT 2026-10-11T10:26:29.465093+00:00:0Critical/Important/Minor; C/Dauto false, un test modificado, runtimeaf192 intacto. Cuatro gaps intento1 conservados como corregidos en2; regresión de fixture Linux corregida. [Informe y tablas completas](testing/t05/storage-nt-observation-u2b1-review3-2026-10-11.md).

| # | Grado anterior | Gap | Tarea | Veredicto actual | Evidencia |
|---|---|---|---|---|---|
| A01 | Important | Cleanup sin primaria escrito antes RED | T05/U2b1 | corregido intento2, conservado | runtimeaf192 byteexact; FIX1 seis pares y revisión2 A/B/C |
| B01 | Important | Custodia posPENDING perdida | T05/U2b1 | corregido intento2, conservado | runtimeaf192 byteexact, no nueva evidencia adversa |
| B02 | Important | Retry cierre con None | T05/U2b1 | corregido intento2, conservado | runtimeaf192 byteexact, no nueva evidencia adversa |
| B03 | Important | Adquisición SUCCESS antes registro perdida | T05/U2b1 | corregido intento2, conservado | runtimeaf192 byteexact, no nueva evidencia adversa |
| QA1-FIX2 | Fallo de fixture | FALSE Linux no alcanza retorno por ctypes ausente | T05/U2b1 | corregido por emulación scoped del nodo | F1fallo/F3controlpreimageexacta; A/Bpropios comprueban FALSE5/cierre202/restauración |

QA2Windows/Linux autorizada y pendiente; noCAS ni cierreT05/M1. A auditoresrealWindows/Linuxsimulado; B18PASS+probe simulado, no Linux nativo propio. Un auditorAlecturaUTF8exit1 conservado yrelecturabyte-safe0. ROOT payloads/AST/JUnit/recibos verificados. Meterreview3 sigue activo hastareleaseQA2.


## T-05/U2b1: QA2 aceptada y componente incorporado — 2026-10-11T10:35:13.197152+00:00

ROOT verifica361payload/1reparsestat-only/26sources/JUnit/imports/27childreaps porplataforma/TAR134/PID0rm. Windows139PASS0SKIP, Linux110PASS29SKIP0FAIL/ERROR; mismo139nodes y29skiprazones QA1. WholeWindows/combinada90,655509%;Linux77,684798%separado,0excl/omit; unión oficial946Win/780Linux/946combined autenticada. Gate funcional0 yWindows/combinada>=80gate0.

CAS2fuentesaf192/020aeffe ejecutado después revisión3A/Blimpia+QA2; Ruffposterior sólo formato(test3de1e82,ASTidéntico, runtimeexacto). Check0/format--check0 finales, falloformato1inicial preservado; sin repetir suite verde porformato. [Informe vigente de componente](testing/t05/storage-nt-observation-u2b1-current-qa2-2026-10-11.md). QA1rojo íntegro, no resultado viejo atribuido a nuevoSHA.

M1NO-VERDE/T05en-progreso: geometry/store/writer/ACK/bootstrap/fullchain/ext4/lifecycle/E2E/manuales pendientes. QA2marker cerrado; no pausa del objetivoM0–M5. PróximaunidadT05U2b2 necesitaADRcontratoNTantesimplementación; M2T02briefCPUindependientegenerado pero no iniciado. Gitincremental del componente pendiente de este registro, restantes cambios sin integrar. Tokens/eur/horasIA realesnull.


## Git incremental U2b1 y avance CPU independiente ? 2026-10-11T10:38:20.945968+00:00

Commit/push 67e1f09fae4d2d2b1931dc66c0e349f3938fe270 verificado en origin/m1/t-02-esquema; siete ficheros aceptados(runtime/tests/reviews1?3/QA1?2), index vac?o. Sin stageglobal, checkout, mainmerge ni otros cambios pendientes incorporados. M1/T05 siguen abiertos.

M2/T02 pas? aen-progreso conforme dependenciaT01yADR0037; briefdeterminista f283d133 generadoexit0(warning tama?o conservado). Actor fresco implement_m2_t02_recipes posee s?lo cuatroficheros declarados+evidencia propia. MarkerROOT activo m2/T02-recetas-privadas; QA2U2b1cerrado. No aceptaci?nM2 ni30generaciones fingidas, ning?nmodeloGPUcargado. Geometr?aT05U2b2 a?npropuesta, constantesNT primarias verificadasen .cache/dev-cycle/m1/storage-u2b-contract-refinement-20261011/, noADRratificado/implementaci?n.


## T-02: contexto previo al RED en concreci?n ? 2026-10-11T10:40:29.472328+00:00

Implementerfresco devolvi? NEEDS_CONTEXT justificado, fuentesintactas/noRED/no c?digo: CPUdesign exige fijarDTO/envelope/readersantesRED. Actorarchitectfresco design_m2_t02_recipe_contract trabaja s?lo propuestaen .cache/dev-cycle/m2/creative-recipes-t02-contract-20261011/, opciones+contratocerrado. ROOT escoger? bajo delegaci?ndelpropietario y ratificar? antes?nicoredispatch. No solicitud alhumano ausente ni bloqueo delobjetivo, T02en-progreso/M2noaceptado. Marker?nicoROOTm2/T02-recetas-privadas incluyeconcreci?ncontractual; m?tricasrealesnull. U2b1aceptado/push67e1f09 siguevigente, M1noaceptado.
