# Revisión de un candidato LoRA para T-10

Consulta documental: 2026-10-06. No se descargaron pesos ni se incorporó un modelo al código, al lock o al catálogo de licencias.

Se revisó el [modelo oficial Chinese New Year](https://huggingface.co/ACE-Step/ACE-Step-v1.5-chinese-new-year-LoRA/blob/099af17b726c5a602b84dc65babbba43ea32b862/README.md), fijando la lectura del README a `099af17b726c5a602b84dc65babbba43ea32b862`. La ficha declara un adaptador entrenado con doce canciones, voces e instrumentos de tradición china. Sus metadatos indican CreativeML-OpenRAIL-M, pero el texto restringe el uso a investigación e intercambio académico y prohíbe uso comercial. No se puede heredar la licencia del modelo base.

La ficha prescribe síntesis sólo con DiT, sin Think. Eso impide asumir que encaja directamente con el perfil `thinking=true` de T-09. La configuración y los pesos de esa revisión no fueron accesibles con la herramienta de consulta; sus hashes y compatibilidad exacta siguen sin verificarse.

Decisión del orquestador: **no incorporarlo ni usarlo como material de T-10 por ahora**. Faltan procedencia y autorizaciones del conjunto de entrenamiento, compatibilidad con el checkpoint fijado y auditoría del loader seguro. Su estilo tampoco valida naturalidad de dueto en español. La fila LoRA conserva `pending_prerequisite`; no equivale a «no funciona».

Siguiente búsqueda: artefacto propio o autorizado que cumpla los requisitos del [diseño aprobado](capabilities-design.md). TDD n/a: prosa de investigación.
