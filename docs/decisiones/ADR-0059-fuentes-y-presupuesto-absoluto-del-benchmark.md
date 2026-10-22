# ADR-0059 · Fuentes y presupuesto absoluto del benchmark

- **Estado:** aceptada por delegación autónoma del propietario; implementación, revisión y QA pendientes.
- **Fecha:** 2026-10-09.
- **Desarrolla:** [ADR-0050](ADR-0050-autoridad-canonica-aislada-del-benchmark.md) y [ADR-0045](ADR-0045-recuperacion-y-transporte-de-auditoria-del-benchmark.md).

## Problema y alternativas

La revisión integrada 4 detectó que el supervisor lee y calcula hashes antes de crear el plazo de lectura y después del RPC. También concede ventanas nuevas al arranque canónico y al coordinador, y admite un contexto y un plan de sesiones distintas. Comprobar el reloj después de una lectura bloqueada no limita esa lectura.

Se elige **O2: verificador de fuentes en un proceso propio de la sesión**. O1, verificar en el canal canónico, acopla un bloqueo del filesystem con el ingreso de episodios y exige reordenar su bootstrap. O3, bloquear los archivos originales contra escritura, amplía la custodia de todo el árbol, interfiere con la edición y no cuenta con una implementación portable acreditada. O2 conserva separados el muestreo, la autoridad canónica y las operaciones largas.

## Decisión

El supervisor fija un único plazo absoluto monotónico al entrar a creación, lectura, consumo u operación. Lo transmite a todos los pasos, incluidos verificación de fuentes, bootstrap, primer sample, challenge, argumentos y confirmación. No renueva segundos por worker ni por comprobación. Los episodios conservan su plazo original de dos segundos; los defaults de llamadas legacy se convierten una sola vez en absoluto cuando no se proporciona un plazo interno. Los relojes tienen el mismo dominio; se rechazan bool, NaN, infinito y límites inválidos.

Un verificador propio realiza apertura, lectura, hash y configuración bajo ese plazo. Su bootstrap mínimo procede del código confiado ya cargado del supervisor; carga los mismos bytes que acaba de comprobar, con una referencia de handler fija. El inventario esperado deriva del freeze confiado y de los archivos reales de contexto, plan, owner y configuración. El helper no elige hashes, rutas ejecutables ni autoridad a partir de un RPC de usuario. Comprueba el conjunto de fuentes, no sólo hashes de entradas antiguas, y rechaza aliases, enlaces y rutas fuera del alcance autorizado.

El protocolo privado tiene autenticación, epoch, request, challenge, secuencia, cuotas y tamaño acotados: gate inicial de como máximo 4 KiB, frames de como máximo 256 KiB, un request activo y fragmentación cerrada de inventario. Las respuestas quedan ligadas al deadline y fase pre/post. El supervisor registra un objeto privado unido al verificador y sus referencias nativas originales. Copiar JSON, presentar un hash o un boolean no crea ese objeto ni permite efectos. El verificador no contiene Store, State ni capabilities de lectura canónica.

Antes y después de cada lectura o consumo se verifican fuentes dentro del mismo plazo. Sólo tras verificación, acreditación canónica fresca y comprobación final se publica la vista. El lookup de bindings permanece en memoria; no oculta lecturas síncronas fuera de la cota. Los guards de operaciones permitidas usan el mismo presupuesto desde antes del guard hasta `args_execute`; los consumidores aún no migrados continúan rechazados antes de efectos. El sampler utiliza su ingreso independiente y no espera el transporte del verificador. Cambio, bloqueo o resultado tardío revoca la sesión y conserva la incertidumbre.

Contexto y plan deben coincidir en `session_id`, `plan_sha256`, `source_hashes`, `image_id` y `lock_sha256`. El archivo owner liga owner no vacío, sesión y plan. Se comprueban el contexto completo observado, root, policy, stream, epoch y objetos originales de sensor, canónico, verificador y operación. No se añade un owner ficticio al esquema cerrado de contexto. El handshake del provider real se comprueba antes de su primer efecto; el montaje manual tampoco elude esta asociación.

## Nacimiento, limpieza e incertidumbre

Las APIs de nacimiento y consultas nativas no ofrecen cancelación universal. Se registra un nacimiento propio antes de iniciar sus syscalls. Un actor interno conserva resultado, Job, Popen, handles, transporte, deadline y latch de revocación; el caller realiza una espera finita. Expirar fija REVOKED antes de devolver el error. Un resultado tardío nunca recibe gate ni vuelve a LIVE: queda retenido y se reconcilia exclusivamente mediante sus objetos nativos originales. No se busca ni termina un PID por nombre o por una referencia numérica recibida del caller.

Un thread, reader, writer, proceso o close pendiente mantiene recursos y gate en **UNKNOWN/quarantined**. No se promete salida del intérprete mientras exista un actor bloqueado ni se liberan slots por devolver un timeout. La limpieza comparte una reserva acotada para todo el conjunto; no concede una ventana nueva a cada worker. Exit, EOF, joins y pertenencia vacía acreditados siguen siendo necesarios para declarar recursos devueltos. Se conserva la primera excepción y los errores secundarios se registran aparte.

La garantía es espera finita del caller, rechazo de respuestas tardías y retención conservadora, sujeta a que el SO planifique al caller. No es una garantía de tiempo real del kernel. Dos hashchecks tampoco prueban un snapshot atómico del árbol ni ausencia de modificación y restauración entre observaciones. Esas garantías más fuertes requieren otra decisión y prueba; no se atribuyen a este verificador.

## Secuencia y pruebas

U1 implementa presupuesto y retención del nacimiento; U2 el verificador; U3 su wiring y vínculo de identidades; U4 la propagación en sensor/coordinador y argumentos. Se transfieren proceso, episodio, coordinador y sus tests sólo después de acabar la corrección FIRSTcause en curso; los actores no pisan esa propiedad. Los helpers nuevos tienen función arquitectónica propia y no se extrae código para evitar el gate de cobertura del módulo original.

Las fixtures positivas de integración se completarán con fuentes físicas y las cinco identidades coherentes antes del nacimiento, preservando assertions, parámetros y casos legacy. Los casos negativos incluyen contexto A con plan/owner B coherentes entre sí, sustitución de objetos, fuente cambiada, read bloqueado real, arranque tardío, pérdida del ACK, late birth, fallo de cleanup y conservación de la causa. Un evento bloqueado después de leer no acredita un `ReadFile` físicamente bloqueado.

Cada cambio exige RED conductual, cobertura actual de cada módulo completo ≥80 % sin exclusiones, originales antes del run, trazas del mismo UUID, revisión fresca y QA independiente. La próxima revisión integrada es 5, preservando formal3/4 y el rebate T10. La relectura del prefijo en la CLI legacy, su migración, FINAL, restore, calibración, 160 jobs GPU, cadencia prolongada y calidad musical siguen pendientes. Esta ADR no acredita implementación ni ejecución nativa de sus nuevas garantías.

El [diseño revisable](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t09/deadline-binding-design1-report.md) contiene callgraph, alternativas, firmas, fixtures y pruebas propuestas. Sus límites de captura inicial y dos hashes suplementarios posteriores a lectura permanecen declarados.
