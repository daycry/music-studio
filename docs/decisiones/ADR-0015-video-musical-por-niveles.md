# ADR-0015 · Vídeo musical por niveles

- **Estado:** aceptada (pendiente de validar con el spike de vídeo) · **Fecha:** 2026-09-28 · Sustituye el no-objetivo «generación de vídeo» de la primera versión de `vision.md`

## Contexto
El propietario quiere la parte de vídeo al estilo de Sondo.ai: un videoclip sincronizado con el ritmo, con personajes coherentes, editor de línea de tiempo, letra como subtítulos y exportación en 16:9 y 9:16. En una 5070 de 12 GB, un videoclip de 3 minutos totalmente generado con IA tarda entre 3 y 20 horas.

## Decisión
- **Proyectos de vídeo.** Cada canción puede tener **varios**. La fuente de verdad de cada uno es su `timeline`, que se guarda en la BD con `rev` para control de concurrencia ([`../arquitectura/datos.md`](../arquitectura/datos.md) §1.3). En disco solo hay una instantánea derivada.
- **Cuatro niveles**, acumulativos por plano:

  | Nivel | Qué es | Tiempo |
  |---|---|---|
  | **N0** | Vídeo con letra o visualizador | Minutos |
  | **N1** | Guion gráfico: imágenes clave coherentes, animadas en 2.5D y cortadas al beat | — |
  | **N2** | N1 más planos generativos protagonistas y cantante con sincronía labial | — |
  | **N3** | Todo generativo | En cola nocturna |

- **N0 siempre disponible**, como vista previa inmediata.
- **Stack local por defecto, con pesos de uso comercial**: Wan 2.2/2.1, InfiniteTalk, Z-Image, Qwen-Image(-Edit), FLUX.2 klein 4B, Depth Anything V2 Small y beat_this.
  - Las **secciones** de la canción salen de la **estructura de la letra** (las etiquetas `[verse]`/`[chorus]`) alineada con el audio. allin1 queda en laboratorio: arrastra Demucs y madmom.
  - En laboratorio: LTX-2.5 y SkyReels V3.
  - Descartados por licencia: Hunyuan (excluye la UE), Sonic y FLUX-dev.
- **APIs de vídeo**: solo como alternativa opcional por plano ([ADR-0014](ADR-0014-local-por-defecto.md)).
- **Cola**: un job por plano, con dependencias (imagen clave → clip → render). Los trabajos largos (N3, reescalado) pueden marcarse como `nightly` ([ADR-0018](ADR-0018-cola-de-jobs.md)).

## Consecuencias
- Detalle en [`../arquitectura/video.md`](../arquitectura/video.md).
- Hitos: **M3** trae N0 (vídeo con letra) y la portada; **M4** es el hito de vídeo (N1–N3) y empieza con un spike de medición en la 5070.
- RAM: con 32 GB, los modelos de 14B van justos. Se mide en el spike, y se recomiendan 64 GB si se usa mucho N2/N3.
