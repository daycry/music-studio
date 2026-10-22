# Preflight real del laboratorio T-10 — intento 1

La imagen sellada arranca, pero **el plan generado en Windows no es portable a Linux**. No se cargó ningún modelo ni se usó GPU. [Recibo](runtime-preflight1-receipt.json).

Reproducción: contenedor propio `runc`, sin red ni dispositivos GPU, rootfs de sólo lectura, montajes selectivos de scripts, texto y modelos también de sólo lectura; entrypoint Python evita el import de torch del entrypoint normal. La sonda verifica los sellos del plan aceptado de QA antes de instanciar la factoría.

Falla con `FileNotFoundError` al abrir `/studio/scripts\eval\capabilities.py`. La causa está en `capabilities.py:96`: `str(p.relative_to(root))` serializa separadores Windows; el consumidor Linux los interpreta como caracteres del nombre. `upstream_seal` ya normaliza separadores. El error ocurre antes de importar el laboratorio o cargar pesos, por lo que esta prueba no acredita todavía factoría ni upstream completos.

El contenedor se eliminó tras verificar su identidad, imagen y etiqueta. Las 59 fuentes, el lock y `.coverage` permanecen intactos. La QA CPU anterior se conserva como evidencia de su alcance; este fallo de integración nuevo requiere una regresión y nueva revisión del cambio. Se generará un plan nuevo tras el fix: ningún plan ni sello anterior se reescribe.

R10-07, Important: serializar rutas del plan en formato POSIX para la ejecución del plan Windows en el contenedor Linux. La alternativa de generar el plan sólo en Linux evita el síntoma, pero deja sin cubrir el flujo CLI Windows→Docker.
