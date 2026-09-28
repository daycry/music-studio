# ADR-0013 · La canción es el proyecto

- **Estado:** aceptada · **Fecha:** 2026-09-28 · Sustituye al «proyecto = carpeta de pistas» de la primera versión de `datos.md`

## Contexto
En Suno, cada generación es una pista suelta. En Sondo y en cualquier DAW, **la canción es el proyecto**: dentro de ella viven la letra y sus versiones, los audios generados, la versión elegida, la portada, el vídeo y las exportaciones. El propietario lo quiere así.

## Decisión
- **`song` es la entidad central.**
  - Cada audio generado es un **take** de la canción, con su árbol de linaje.
  - La canción apunta a un **take maestro**.
- **Qué cuelga de la canción:**
  - la letra, con versiones y su propio linaje;
  - el estilo y las notas;
  - portadas, **proyectos de vídeo** y exportaciones.
- **Qué cuelga de cada take:** el **análisis** (beats, secciones, tonalidad, tiempos de la letra) y los **stems**. Dos takes de la misma canción tienen distinto tempo y estructura, y la vista de canción muestra los del take seleccionado.
- **Agrupación y bibliotecas globales:**
  - Las **colecciones** (álbum o carpeta) son opcionales y sustituyen al antiguo «proyecto».
  - Los **personajes**, los **presets** y las **subidas** son bibliotecas globales que se reutilizan entre canciones.
- **En disco**, cada canción es una carpeta autocontenida y portable (`data/songs/<song_id>/`), con un `song.json` legible. Se puede exportar e importar como zip.

## Consecuencias
- **UI:** gira en torno a la **vista de canción**, con pestañas Audio · Letra · Vídeo · Portada · Exportar ([`../producto/ux.md`](../producto/ux.md)).
- **Crear sigue siendo rápido:** si se genera sin haber creado antes una canción, se crea automáticamente una **canción borrador**, con el título sacado de la letra o del estilo.
- **Esquema:** está en [`../arquitectura/datos.md`](../arquitectura/datos.md) §1 y entra completo en la primera migración de M1.
