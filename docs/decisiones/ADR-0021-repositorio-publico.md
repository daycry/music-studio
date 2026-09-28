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
- **Licencia:** `LICENSE` explícita de **todos los derechos reservados** (código visible, sin permiso de uso, copia ni distribución). Es la opción reversible: más adelante se puede abrir con una licencia libre, pero una licencia abierta ya concedida no se puede retirar de lo publicado, y así la comercialización queda abierta. Los componentes de terceros conservan sus licencias ([`../legal/licencias.md`](../legal/licencias.md)).
- **Integración:** una rama por tarea (`m0/t-02-…`), y al cerrarla (verificación ejecutada y revisión pasada) **merge fast-forward a `main` sin PR** y push. Si `main` avanzó, se hace rebase de la rama antes. Con un solo desarrollador, el PR no aporta nada que no den ya la verificación, la revisión de dos lentes y `qa`.
