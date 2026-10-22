# ADR-0048 — Herramientas frontend portátiles

- **Estado:** aceptada; implementación, revisión y QA pendientes
- **Fecha:** 2026-10-07
- **Decisor:** orquestador, bajo delegación autónoma explícita del propietario
- **Ámbito:** M1/T08; concreta ADR-0005 y conserva ADR-0035

El launcher pnpm del perfil puede descargar y ejecutar otra versión al leer packageManager. Se usarán herramientas propias verificadas dentro del proyecto: Node22.23.2 y pnpm9.12.0, este último mantiene el pin ya versionado. Node es una herramienta de desarrollo; el producto continúa en Docker y Ollama compartido permanece en WSL2.

Los archivos oficiales y su origen/hash/licencias quedan fijados en tools/tools.lock.json. La extracción rechaza rutas que escapan, enlaces, miembros duplicados y límites inválidos antes de escribir. Ninguna instalación global, Corepack, launcher del perfil ni cambio de gestor automático. La llamada a pnpm se hace con el node portable y el archivo bin/pnpm.cjs verificado. Store/cache/state/config/TEMP se confinan al proyecto; se desactiva la gestión automática de versiones y se comprueban pins antes de ejecutar.

Primer ámbito de implementación: descarga, extracción segura y check/version en Windows, sin modificar todavía env/bootstrap ni resolver dependencias. La receta posterior migrará los comandos de desarrollo para usar estas herramientas. El inventario de24 paquetes es de primer nivel: el lock pnpm transitivo completo y sus licencias/hashes requieren verificación separada antes de instalación del frontend. Los avisos incluidos de Node, pnpm y Next conservan sus licencias propias. No se acredita seguridad global de paquetes por tener hashes ni verificación PGP de Node que no se ha ejecutado.

Linux/imagen Docker exigen fijar sus artefactos/digest propios y prueba real; el ZIP Windows no lo demuestra. No se cambia Python gestionado, FFmpeg ni modelos/GPU. La adopción técnica exige TDD, revisión fresca, QA de extracción/probes/confinamiento y preservación de locks anteriores.


[ADR0051](ADR-0051-dependencias-web-fijadas-y-uso-local.md) fija el candidato de dependencias web y autoriza instalación local congelada. La decisión de dos alias npm byteidénticos no modifica el extractor de herramientas portátiles. Compatibilidad, build y despliegue siguen pendientes.
