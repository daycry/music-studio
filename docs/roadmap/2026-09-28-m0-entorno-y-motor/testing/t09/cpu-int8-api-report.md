# Comprobación real de la API INT8 en CPU

La imagen inmutable de ACE-Step contiene **Torch2.10.0+cu128 y torchao0.16.0**. Una capa Linear de32×16, inicializada en CPU en BF16, se cuantizó con Int8WeightOnlyConfig(version1); el verificador actual encontró una de una capas esperadas, AffineQuantizedTensor/PlainAQTTensorImpl y almacenamiento int8. Exit0. [Recibo](cpu-int8-api-receipt.json).

Esta comprobación usa la API real y tensores reales pequeños; no usa pesos ACE-Step. No acredita cuantización completa del DiT, offload real, compatibilidad de kernels CUDA, carga XL ni ajuste en12GB. Los indicadores offload del objeto de prueba son sintéticos: se verifica la guarda del adaptador, no transferencia real de memoria. La prueba GPU sigue pendiente tras revisión y QA.

Contenedor propio con runtime runc, sin GPU solicitada ni modelos montados, red deshabilitada, filesystem de solo lectura y tmpfs limitado. CUDA no se inicializó. Fuentes montadas de solo lectura, adapterSHA92ca199a intacto antes/después; contenedor inspeccionado por ID/label/imagen/estadoexited y retirado. Ningún paquete instalado en host, peso descargado ni servicio existente modificado.

torchao advierte que version1 está deprecada para una versión futura. Sigue soportada en la versión0.16.0 fijada; cambiar ahora a version2 alteraría clase/semántica del tensor y exige otra prueba/decisión. Se conserva el perfil aprobado. No se atribuye a esta sonda el cumplimiento de los criterios del benchmark. TDD n/a: observación experimental de solo lectura y prosa.
