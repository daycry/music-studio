# QA técnica T-10 — intento 2

**QA_CPU_PASS. El plan nuevo creado en Windows funciona en el contenedor Linux real.** QA de contexto fresco tras revisión A+B limpia. [Recibo](cpu-qa2-receipt.json).

La sonda usa la imagen sellada, `runc`, sin dispositivos GPU, sin red y con rootfs y entradas de sólo lectura. Verifica seis módulos del laboratorio, 14 fuentes empaquetadas y **436 archivos upstream**: todos coinciden. La entrada original coincide con el plan. Se instancian factoría y supervisor sin cargar un modelo, y torch permanece sin importar. Exit 0; contenedor propio eliminado tras verificar identidad y aislamiento. El plan anterior sigue intacto; la prueba crea una sesión nueva de 522 filas sin habilitar capacidades.

Once pruebas dirigidas del CLI pasan sin fallos ni omisiones; Ruff y formato conformes en los dos archivos. La suite de 88 y la cobertura oficial del archivo modificado, **98/119 = 82,352941 %**, se verifican por sellos y fuentes congeladas y no se repiten. Root verifica 31 artefactos y las 59 fuentes, además de locks, texto, `.coverage` raíz y el plan anterior.

Gates oficiales exit 0: ledger sin incoherencias y seis avisos de Changelog en tareas abiertas; coverage-check reconoce la declaración sin UI, `applies=false`. Playwright no aplica y no se declara como ejecutado. Un error inicial del driver al leer claves Windows del JSON de cobertura se corrigió en el parser privado antes de ejecutar tests o Docker; no duplicó esas ejecuciones.

Esta prueba cierra el defecto de portabilidad observado. **T-10 permanece abierta:** faltan inferencia GPU, recursos y aceptación musical. No se cargaron pesos ni se generó audio. Las capturas iniciales ya están guardadas; esta QA no requiere que el propietario las envíe.
