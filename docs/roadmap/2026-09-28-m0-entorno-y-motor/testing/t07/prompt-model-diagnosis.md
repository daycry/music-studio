# Diagnóstico inicial: prompt, configuración y modelo

2026-10-05. El propietario percibe los tres desajustes en la primera toma: ritmo/encaje de la letra, afinación y carácter de la voz. La valoración sigue siendo negativa. [Respuesta aclaratoria](owner-quality-details.json).

## Evidencia confirmada

- El material original de Suno y su MP3 se inspeccionaron en modo lectura. Copias verificadas por SHA-256 se conservan en la entrada privada; letras, prompts, metadatos personales y rutas externas no se versionan. También se localizaron WAV y un ZIP de stems; no se extrajeron ni escucharon sus pistas. No se subió audio a servicios externos.
- El prompt del documento original de Suno coincide con el prompt privado recibido. La generación local utilizó una adaptación de 490 caracteres, nueve secciones y los mismos versos; no el prompt completo de 867 caracteres. No son entradas equivalentes entre motores.
- La referencia Suno dura 227,640979 s; las tomas locales duran 255 s. Todos los MP3 son estéreo a 48 kHz. Se desconoce la versión de Suno que produjo la referencia. La duración y el bitrate no determinan calidad.
- El WAV crudo y el master de la primera toma mantienen la posición de sus 12.240.000 muestras por canal: producto escalar normalizado 0,9999999999999774 y error absoluto máximo 5,960464477539063e-08, compatible con cuantización a PCM24. Este paso no ha desplazado independientemente voz y música. No es una prueba de afinación ni una evaluación de escucha. [Recibo numérico](reference-technical-comparison.json).
- El adaptador actual usa DiT Turbo y LM 0,6B, BF16/backend pt. `generation_options` no fija `inference_steps`, `shift` ni `thinking`: la fuente upstream auditada fija 8, 1 y True respectivamente. El LM está inicializado y participa en los códigos musicales; desactivar las opciones `use_cot_*` indicadas en el adaptador no equivale a desactivar el LM.
- La fuente auditada pasa `shift` sin corregirlo. La documentación oficial recomienda **shift=3 para Turbo** y aclara que el valor por defecto 1 se aplica tal cual; solo guidance_scale se corrige automáticamente. [Documentación oficial de inferencia, Generation Parameters](https://github.com/ace-step/ACE-Step-1.5/blob/main/docs/en/INFERENCE.md).

## Lo que sigue sin estar demostrado

No se ha probado que shift=1 cause los tres desajustes, ni que un cambio de prompt los resuelva. No se ha realizado una audición por el agente ni una separación de voz/instrumental; la valoración musical procede del propietario. Las dos generaciones anteriores con semilla 1 tampoco acreditan determinismo bit a bit. No se atribuye el resultado a RAM insuficiente: ambas generaciones registran swap cero y spilled=false.

## Comparación controlada propuesta

Primero comparar shift=1 y shift=3 con el mismo modelo, letra, caption, BPM, duración, semilla y resto de parámetros, preservando cada toma. Conviene repetir pares para distinguir tendencia de variación entre generaciones. Después comparar la presentación del prompt y las etiquetas de secciones, conservando todas las palabras de la letra y manteniendo el ajuste que se esté evaluando fijo. El propietario valorará por separado ritmo, afinación, carácter de voz, crecimiento y outro. La referencia Suno sirve como objetivo artístico, no como control de una única variable entre motores.

Cambiar parámetros o el adaptador requiere TDD, revisión y QA dentro de dev-cycle. Este registro no cambia el motor, no modifica la letra, no declara calidad aprobada ni acredita una prueba A/B ejecutada. La medición y selección de M0 siguen abiertas (T-08 a T-13).
