# ADR-0014 · Local por defecto; APIs y suscripciones solo como alternativa opcional

- **Estado:** aceptada · **Fecha:** 2026-09-28 · Matiza [ADR-0002](ADR-0002-personal-local-first.md)

## Decisión

- **Todo funciona en local por defecto**: música, letras, imagen, vídeo, análisis y evaluación. La aplicación funciona entera sin conexión y sin claves.
- **Los proveedores externos son alternativas opcionales**, desactivadas de fábrica:
  - APIs de LLM para las letras;
  - APIs de vídeo o de imagen para los planos que la 5070 no pueda generar con la calidad o en el tiempo deseados;
  - GPU en la nube.
- **Cada proveedor externo es un adapter que vive en el server** (carril `remote`) e implementa la misma interfaz y el mismo descriptor que los engines ([`../arquitectura/contrato-engines.md`](../arquitectura/contrato-engines.md)). No es un contenedor, porque los engines no tienen red ni claves ([ADR-0020](ADR-0020-seguridad-local.md)).
- **Activación:**
  - se activa **por función**, en Ajustes (tabla `provider`), con la clave en `.env`;
  - nunca se usa en silencio: la UI muestra qué proveedor genera cada cosa y, antes de lanzar, cuánto va a costar.
- **Registro:**
  - lo generado con un proveedor externo lo recoge el manifiesto (`provider`), con modelo, `request_id` y coste;
  - antes de activar un proveedor, sus términos de uso se registran en [`../legal/licencias.md`](../legal/licencias.md).
- **La generación de música es siempre local.** No se integra ninguna API de Suno, Udio o similares: es justo el riesgo de procedencia que el proyecto quiere evitar.

## Motivo

Control, privacidad, coste marginal cero y aprendizaje. Las alternativas externas cubren dos huecos: los límites de calidad o de VRAM de la GPU propia, y poder comparar resultados.
