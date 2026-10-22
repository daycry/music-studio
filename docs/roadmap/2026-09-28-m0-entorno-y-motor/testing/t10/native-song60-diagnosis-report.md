# Diagnóstico T-10 — primera toma GPU fallida

**R10-08, Important: la captura oculta la firma de `generate_music` y el upstream elimina todos sus parámetros.** Defecto reproducido en CPU con el generador realmente instalado y sellado. [Recibo](native-song60-diagnosis-receipt.json).

El control sin captura llega a la guarda `Model not fully initialized`, esperada al no cargar pesos. Con captura, `inspect.signature` ve `(*args, **kwargs)` en lugar de los parámetros reales; el filtro upstream descarta `captions` y el resto. La llamada falla con `GenerateMusicMixin.generate_music() missing 1 required positional argument: 'captions'`; la frontera registra `{}`. No se ha aplicado ningún fix.

Tres sondas CPU, imagen sellada, contenedores propios eliminados, CUDA sin inicializar, sin pesos ni GPU. Root verifica 59 fuentes y 29 artefactos. La alternativa mínima es preservar las firmas de las envolturas temporales y probar la conservación de parámetros usando el filtro real fijado.

**Límite:** este defecto garantiza el fallo al llegar al DiT, pero no demuestra si fue la primera excepción de la toma GPU anterior; pudo existir un fallo previo en el LM. La siguiente toma conservará diagnóstico privado del resultado para distinguirlo. El mensaje público genérico permanece y ningún plan anterior se cambia. No se declara calidad, inferencia correcta ni cierre de T-10.
