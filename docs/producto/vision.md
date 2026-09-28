---
documento: vision
titulo: Visión del producto — music-studio
estado: vigente
fecha: 2026-09-28
actualizado: 2026-09-28
---

# Visión — music-studio

## Qué es

Un **estudio personal de generación musical con IA**, equivalente funcional a Suno + Sondo, que corre **entero en local**: escribes una letra (o describes una idea), eliges un estilo y obtienes canciones completas con voz, que puedes escuchar, iterar, editar por secciones, separar en stems y exportar — y **convertir en videoclip** sincronizado al ritmo, con un protagonista coherente (inventado o a partir de tus fotos). **Cada canción es un proyecto** que reúne letra, versiones, portada, vídeo y exportaciones ([ADR-0013](../decisiones/ADR-0013-cancion-como-proyecto.md)).

- **Motor:** modelos de pesos abiertos ejecutados en la GPU propia (RTX 5070, 12 GB) — **local por defecto en todo** (música, letras, imagen, vídeo). APIs o suscripciones externas solo como alternativa opcional, nunca para la música ([ADR-0014](../decisiones/ADR-0014-local-por-defecto.md)).
- **Interfaz:** web local (Next.js) con la experiencia de uso de Suno como referencia — no su identidad visual.
- **Usuario:** una persona (el propietario). El diseño no cierra la puerta a varios usuarios ni a una comercialización futura, pero **no se construye nada para ellas hasta que haga falta**.

## Por qué

- **Control total**: qué modelo genera, con qué parámetros, dónde viven los ficheros. Por defecto nada sale de la máquina (los proveedores externos son opcionales y visibles, [ADR-0014](../decisiones/ADR-0014-local-por-defecto.md)).
- **Iteración rápida y sin coste marginal**: la GPU es propia; generar 50 variantes cuesta electricidad.
- **Aprendizaje**: dominar el stack de audio generativo (modelos, post-proceso, UX de iteración).
- **Opcionalidad**: si el producto funciona, poder comercializarlo sin reescribirlo (ver [`../legal/comercializacion.md`](../legal/comercializacion.md)).

## Principios

1. **Local-first y autocontenido.** Todo — código, pesos de modelos, audio generado, base de datos, memoria del proyecto — vive dentro de la carpeta del proyecto. Nada de rutas en otras unidades.
2. **Construir en vertical, no en capas.** Cada hito termina con algo que se usa (una canción que se escucha), no con infraestructura sin producto encima.
3. **El modelo es un plugin.** Ningún modelo concreto aparece en la lógica de negocio; se declara qué sabe hacer y la app consulta esa declaración. El catálogo open source cambia cada pocos meses.
4. **Honestidad en la UI.** Progreso real, tiempos reales, capacidades reales. Si un modelo no sabe hacer algo, el botón no existe o lo dice.
5. **Procedencia por artefacto, sin burocracia.** Cada take, imagen o plano de vídeo guarda qué modelo, qué pesos (hash), qué parámetros, qué semilla y de qué deriva. Es barato hacerlo desde el día 1 e imposible reconstruirlo después.
6. **Seguridad básica no negociable.** Pesos solo en `safetensors`/`gguf`/`onnx` (los pickle se convierten con auditor, nunca se cargan), verificados por SHA-256 y fijados por revisión; licencias revisadas antes de integrar cualquier modelo o herramienta ([ADR-0006](../decisiones/ADR-0006-seguridad-de-pesos.md)).
7. **Proceso ligero.** Un solo desarrollador asistido por IA: decisiones cortas en ADR, backlog por hito, sin presupuestos en euros ni gates corporativos.

## No-objetivos (por ahora)

- Multiusuario, cuotas, facturación, SaaS público.
- Despliegue en cloud. La GPU alquilada o las APIs externas solo existen como **alternativa opcional desactivada** por función ([ADR-0014](../decisiones/ADR-0014-local-por-defecto.md)).
- Clonación de voz de personas reales.
- Aplicaciones móviles nativas, edición DAW completa, mastering profesional.
- Vídeos que no partan de una canción del estudio (el vídeo siempre es de una canción; ver [ADR-0015](../decisiones/ADR-0015-video-musical-por-niveles.md)).
- Usar la imagen o la voz de terceros sin su consentimiento.
- Copiar la identidad visual de Suno (logo, paleta, tipografía, textos).

## Cómo se mide el éxito

| Señal | Umbral |
|---|---|
| Calidad | En la escucha de referencia ([`../calidad/evaluacion-escucha.md`](../calidad/evaluacion-escucha.md)), ≥ 7 de 10 briefs con una pista que usarías tal cual o con retoque cosmético |
| Velocidad | Canción de 3 min generada en ≤ 2 min de reloj en la 5070 (objetivo; se mide en M0) |
| Uso real | ≥ 100 generaciones propias y ≥ 1 canción usada en algo real (vídeo, maqueta, proyecto) |
| Vídeo | Vídeo con letra de 3 min en ≤ 10 min; videoclip N1 en ≤ 45 min en la 5070 (se mide en M4) |
| Fluidez | Iterar (variante, extender, regenerar sección) sin salir de la pantalla y sin esperar más que la propia inferencia |

## Referencias

- Documentación anterior (planificación corporativa, julio–septiembre 2026): [`../archive/roadmap-2026-07-27/`](../archive/roadmap-2026-07-27/) — histórico, no vigente.
