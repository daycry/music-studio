# ADR-0021 · Repositorio remoto público en `daycry/music-studio`

- **Estado:** aceptada · **Fecha:** 2026-09-28 · Sustituye la línea «remoto privado» de [`../arquitectura/convenciones.md`](../arquitectura/convenciones.md) §7

## Contexto
La documentación preveía un remoto **privado** como copia del código. El repositorio antiguo (`suno-sondo-clone`) ya estaba renombrado a `daycry/music-studio`, era público y contenía el código anterior.

## Decisión
- **Remoto:** `https://github.com/daycry/music-studio`, **público**, por decisión del propietario.
- **Nueva historia:** `main` contiene el reinicio desde cero ([ADR-0001](ADR-0001-reinicio-desde-cero.md)).
- **Código anterior:** se conserva en `archive/legacy-main` (`5455e68`) y en `feature/plataforma-musical-ia`.
- **Autenticación:** git se autentica con el `gh` CLI (`credential.helper = !gh auth git-credential`), configurado **solo en el repositorio local**, sin tocar la configuración global.
- **Descripción del repo:** neutra, sin marcas de terceros ([gate GC-f](../legal/comercializacion.md)).

## Consecuencias
- **Todo lo que se commitea es público.** Nunca se versionan:
  - secretos (`.env` está ignorado; `STUDIO_ENGINE_TOKEN` y las claves de proveedores solo viven ahí);
  - pesos (`models/`);
  - datos personales;
  - audio o fotos de la biblioteca (`data/`).
- **Revisión previa a cada push:** comprobar que `git status` no incluye nada de `data/`, `models/` ni `.env`. La lente de seguridad de la revisión adversarial vigila que no haya secretos en el diff.
- **Licencia:** el repo sigue sin fichero `LICENSE`, lo que significa «todos los derechos reservados». Elegir una es una decisión aparte, ligada a la comercialización.
