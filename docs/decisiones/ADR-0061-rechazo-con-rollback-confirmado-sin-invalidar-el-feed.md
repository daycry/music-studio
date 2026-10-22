# ADR-0061 · Rechazo con rollback confirmado sin invalidar el feed

- **Estado:** aceptada por delegación del propietario; implementación, revisión y QA pendientes.
- **Fecha:** 2026-10-09.
- **Desarrolla:** [ADR-0056](ADR-0056-sse-con-buffer-y-recuperacion-de-estado.md).

## Decisión

Se elige O1: la integración transaccional devuelve un resultado privado e inmutable que conserva la excepción y su traceback cuando la preparación se rechaza, el rollback y el cierre terminan satisfactoriamente y no se ha intentado commit. El coordinador reconoce tipo exacto y sello interno, fuera del catch de errores inciertos, y vuelve a lanzar el mismo error sin modificar epoch, ring ni suscriptores.

Ni un valor JSON, un booleano, el tipo ValueError ni un rollback posterior a un commit fallido constituyen esa evidencia. La autoridad procede de la integración transaccional revisada; el sello no aísla frente a código Python hostil dentro del proceso.

Una excepción genérica, un fallo de begin, rollback o close, un intento de commit con resultado desconocido y un resultado inválido conservan la política incierta. Se registra el error secundario sin sustituir el primario y se invalida el feed cuando corresponde. La confirmación de publicaciones, el retorno durable y los fallos posteriores al commit de B01 no cambian.

El consumidor sin coordinador mantiene el comportamiento legacy. El camino coordinado separa preparación, rollback confirmado y commit; comparte las validaciones mediante un helper interno sin repetirlas ni debilitarlas. Se conservan owner/song/attempt/ordinal/secuencia, permisos, límites y la barrera antes de SQLite.

## Motivo y verificación

VULN-001 Medium del SAST U2c mostraba que un evento rechazado antes del commit podía borrar replay y cerrar lectores ajenos. El wrapper de excepción alternativo añade cause/context sin ofrecer certeza adicional; el resultado privado separa evidencia interna y excepción pública.

El primer RED debe usar SQLite, EventBus y suscriptor reales: evento de contrato válido con identidad o secuencia incorrectas, rechazo y DB sin cambios, epoch/ring/lector conservados. También se verifican commit incierto, rollback/close fallidos y primera causa. Ninguna de esas pruebas se declara ejecutada aquí. Cobertura actual de cada módulo completo >=80 % sin exclusiones, revisión fresca y QA independiente siguen obligatorias.

No se añade tabla, servicio, ruta HTTP ni protocolo público. No acredita todos los escritores, snapshot WAL, replay autorizado, cliente, exposición SSE ni el cierre de T-06.
