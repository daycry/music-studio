# Imagen T-09 preparada tras QA CPU

Imagen aislada construida: `music-studio/engine-acestep:m0-t09-20261006-fa293f05`, ID `sha256:00c32a76c951a4494a23282edf4e53d946f43f244e0790cbd59e806030bd7f43`. Dockerfile y dependencias fijados existentes;33fuentes sin cambios. No se reemplazó la etiqueta del servicio anterior. [Recibo](image-ready-receipt.json).

El intento sin red falló en apt-get por no reutilizar sus capas. La construcción con la configuración habitual del Dockerfile terminóexit0, sin cambiar versiones, código o modelos. Los dos logs quedan sellados.

Sonda CPU real de la imagen:14fuentes ACE/common incluidas en el freeze coincidenSHA/tamaño; Torch2.10.0+cu128, torchao0.16.0, Transformers4.57.6, Accelerate1.12.0, safetensors0.7.0. CUDA no inicializada. Contenedorpropio runc, rednone, raízreadonly, sinGPU ni modelos; exit0 yeliminaciónverificada. Esto comprueba empaquetado/importación, no kernelsGPU ni fitXL.

Lectura manual del propietario: dedicada1,1/12GB, compartida0,1/15,8GB, sin hora indicada. TreslecturasPDH posteriores a18:45:41–43UTC:1137,9140625MiBdedicada y133,1015625MiBcompartida, status0. Compatibles con redondeo1,1/0,1GiB; no prueban simultaneidad. NVML1125MiB/Ollamavacío en eseinstante. El volumen compartido en reposo no acredita desbordamiento durante generación.

SoporteCPU con revisión5 yQA2conformes. Pendientes calibraciónbaseline/representativaTaskManager, capturainicialnavegadorvisible ypreflight fresco antesmatriz160jobs. ComputerUse sigue detenido porEscape; no se captura ni se entra en8768. T09/M0abiertos; no declararRTF/offload/XL/naturalidad/calidad por esta sonda. TDDn/a: evidencia operativa yprosa.
