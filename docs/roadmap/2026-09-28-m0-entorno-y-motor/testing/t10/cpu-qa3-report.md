# QA T-10 — firma y próxima toma diagnóstica

**QA_CPU_PASS** tras revisión A+B limpia. Nueve pruebas dirigidas del módulo nativo pasan; Ruff y formato conformes. Root verifica JUnit91 y cobertura oficial 307/346 = 88,7283 % del único archivo de producción cambiado mediante las fuentes congeladas; la suite completa no se repite. [Recibo](cpu-qa3-receipt.json).

Gates oficiales exit 0, ledger sin incoherencias y seis avisos de Changelog; declaración sin UI aceptada por coverage-check, `applies=false`. Playwright no aplica. Las 59 fuentes, 30 protegidos, planes anteriores y `.coverage` se mantienen intactos.

QA señaló que un fallo al escribir diagnóstico privado podía sustituir un retorno o error del motor. Root corrigió exclusivamente los helpers de la prueba: la escritura se hace como mejor esfuerzo y conserva el resultado o excepción originales. Un addendum separado verifica nueve combinaciones de éxito, resultado fallido y excepción con escritura normal, OSError y destino existente. Identidad, firmas y restauración se conservan. Los helpers nuevos coinciden con los sellos v2; el informe anterior no se reescribe. No se repiten los tests de producto por ese cambio privado.

El runner distingue instrumentación configurada de una entrada realmente observada; sólo el marcador privado acredita que se alcanzó la generación. SHA del entrypoint y factoría se verifica, entradas y controles del plan permanecen iguales. QA no ejecutó GPU ni cargó pesos. La próxima toma tendrá diagnóstico privado y monitorización, sin modificar errores públicos ni declarar aún aceptación musical. T-10 sigue abierta.
