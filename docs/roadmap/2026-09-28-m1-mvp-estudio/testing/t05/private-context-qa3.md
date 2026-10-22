# T-05: contexto privado — revisión y QA independiente

Fecha: 2026-10-09. Componente técnico aceptado: helper compartido de
[ADR-0070](../../../../decisiones/ADR-0070-contexto-privado-de-request-y-linaje-en-publicacion-audio.md)
y limpieza portable del fixture. La integración del worker continúa pendiente.

El helper conserva la request normalizada completa, parámetros solicitados,
índice de salida, linaje y prueba de letra en un recibo privado canónico por
SHA-256. El manifiesto público contiene una referencia opcional al recibo y
los parámetros permitidos. La declaración de letra proviene de la prueba
capturada por el padre; el helper valida integridad, no concede autoridad SQL.

La primera revisión detectó dos defectos Important: la API directa aceptaba
enteros/floats como booleanos comerciales y una sustitución concurrente por
FIFO podía bloquear la lectura Linux. Se corrigieron con pruebas rojas reales
antes del cambio. El FIFO nativo anterior bloqueó al hijo propio hasta el
deadline de tres segundos; se terminó y recogió únicamente ese hijo. Después
de corregir la apertura, el FIFO se rechaza antes de leerlo. La segunda revisión
A/B/C terminó sin defectos pendientes, conservando las demás aprobaciones.

QA2 quedó **NO VERDE**: cuatro fixtures originales Linux fallaban al limpiar
symlinks con `rmdir`. Se conserva ese resultado. Una reparación independiente
cambió solamente la limpieza: `unlink` para symlink y `rmdir` para junction.
Las aserciones y el resto del AST quedaron intactos; revisión A/B sin defectos.

La nueva QA3 ejecutó:

| Verificación | Resultado |
|---|---|
| Windows funcional, 255 casos originales | 250 PASS, 5 SKIP, 0 deselect, exit0 |
| Windows con cobertura oficial | 250 PASS, 5 SKIP, 0 deselect, exit0 |
| Cinco casos originales omitidos en Windows, ejecutados en Linux | 5 PASS, 0 FAIL/ERROR/SKIP, exit0 |
| Módulo completo `manifest.py` | 378/415 líneas+ramas cubiertas: 91,0843 %, sin exclusiones |
| Módulo completo `private_context.py` | 267/302: 88,4106 %, sin exclusiones |

Las cinco omisiones Windows son cuatro symlinks sin privilegio y el FIFO POSIX.
En QA3 Linux, el FIFO se rechazó en 0,669224 s y el hijo terminó y fue recogido.
Ruff y formato scoped terminaron con exit0. Los tests de distribución instalada
y el benchmark reparado forman parte de la selección Windows.

Root verificó 85 artefactos inventariados, siete fuentes actuales, diez fuentes
protegidas, nueve inputs del snapshot Linux y terminales/JUnit/cobertura. También
cotejó ID, owner, imagen, estado detenido y cleanup del contenedor propio;
sin privilegios, red ni peticiones GPU. No se usaron modelos ni datos del usuario.
Las fixtures/cachés excluidas del inventario se declaran expresamente; no se
afirma un inventario completo del checkout.

Evidencia detallada y aceptación:
`.cache/dev-cycle/m1/t05-private-context-receipt-independent-qa3/`.
La fase QA2 permanece en su directorio histórico, sin sobrescribir ni
reinterpretar sus cuatro FAIL.

Este resultado no acredita captura SQL en el worker, presupuesto conjunto
plan+recibo, publicación/replay de canción con letra, almacenamiento persistente,
calidad audible ni QA E2E de la aplicación. Esos gates siguen abiertos en T-05.
