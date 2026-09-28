# ADR-0012 · LLM del asistente de letras: local por defecto, API como alternativa

- **Estado:** aceptada · **Fecha:** 2026-09-28 · Revisada el mismo día: en su primera versión la API era la opción por defecto

## Decisión
- **Por defecto, un LLM local:** **Gemma 4 12B-it** en `google/gemma-4-12B-it-qat-q4_0-gguf` (Apache 2.0, sin acceso restringido, ~7 GB). Corre en `engine-llm` con llama.cpp, detrás del contrato `/v1` y con la tarea `text.generate`. El formato GGUF está admitido desde [ADR-0006](ADR-0006-seguridad-de-pesos.md).
  - Comparte la GPU con el generador de música por turnos: el dispatcher descarga uno antes de cargar el otro. Las peticiones del asistente tienen **prioridad `interactive`** ([ADR-0018](ADR-0018-cola-de-jobs.md)).
  - Si Gemma rinde mal en castellano o en métrica, la alternativa local es **Qwen3.5-9B** (Apache 2.0). Se decide con la prueba de M2.
- **Alternativa opcional: Claude API** (Sonnet 5 / Haiku 4.5), como adapter externo en el server, en el carril `remote`. Está **desactivada** hasta que se pone una clave en `.env` y se activa en Ajustes ([ADR-0014](ADR-0014-local-por-defecto.md)).
- **Tratamiento común de la salida**, sea cual sea el proveedor:
  - se valida con el parser de etiquetas compartido (`lyrics-cases.json`); si no parsea, se regenera como máximo 2 veces;
  - el prompt de sistema prohíbe reproducir letras existentes;
  - la letra resultante se guarda con `declaration = assistant`.
- **El guion de vídeo** (M4) usa la misma tarea `text.generate`, con salida JSON validada contra el esquema de planos.

## Motivo
La regla del proyecto es: **local por defecto, y los servicios externos solo como alternativa opcional** ([ADR-0014](ADR-0014-local-por-defecto.md)). El coste es que el LLM no puede estar en VRAM a la vez que el generador; la UI indica cuándo tiene que «cargar el modelo de letras» y cuánto tarda.
