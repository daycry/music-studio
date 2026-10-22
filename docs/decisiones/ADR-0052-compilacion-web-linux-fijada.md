# ADR-0052 · Compilación web Linux con dependencias fijadas

- **Estado:** aceptada bajo delegación autónoma del propietario; prueba técnica e implementación pendientes.
- **Fecha:** 2026-10-08.
- **Relacionadas:** [ADR-0035](ADR-0035-despliegue-docker-y-ollama-wsl.md), [ADR-0048](ADR-0048-herramientas-frontend-portatiles.md) y [ADR-0051](ADR-0051-dependencias-web-fijadas-y-uso-local.md).

## Contexto

La compilación Windows por el launcher canónico falla. Una primera ejecución no resolvió la caché de usuario del carrier SWC; configurar una caché propia permitió llegar a la validación nativa, que rechazó permisos de sustitución en sus ancestros. Proteger solamente la hoja no solucionó el fallo. No se cambian los permisos compartidos del repositorio ni se escribe en perfiles ajenos.

El despliegue de producto ya aprobado utiliza Docker, salvo Ollama compartido en WSL2. Por tanto, la siguiente prueba construye un entorno Linux nuevo con las dependencias oficiales fijadas; no copia node_modules Windows ni sus junctions. El resultado de esa prueba todavía no acredita una compilación válida.

## Decisión

Se elige Linux/Docker para la compilación y el runtime de producto. La prueba privada comienza con la imagen local identificada por `sha256:0a7108bf6c7bf5de370ffb1a3ed6be93d405b43ff159f681a8d18c0e2bc2e402`, observada como `node:22-alpine`. Una sonda CPU, sin red, GPU, puertos ni mounts, comprobó Node 22.23.3, Alpine 3.24.2, el LICENSE completo de Node y los metadatos de licencia de 18 paquetes del sistema. El contenedor propio fue eliminado. No se ha verificado firma ni procedencia remota de la imagen.

La versión Linux no sustituye silenciosamente Node Windows 22.23.2 en tools.lock. Antes de introducir el runtime en producto se fijará su referencia inmutable y se conservarán las licencias y avisos de la distribución. Pnpm sigue en 9.12.0 y los 609 archivos oficiales mantienen su SHA-256/SRI; se seleccionan dependencias compatibles con Linux/musl mediante una instalación congelada propia. No se modifica el lock para aparentar compatibilidad.

La caché de SWC reside en filesystem Linux, con ancestros cuya propiedad y permisos se comprueban. No se desactiva la seguridad del carrier, ni se usa un preload alternativo, binding falso o WASM para declarar un verde nativo.

El gate exige instalación offline verificable, transformación TypeScript nativa real, carga del binding de Next y compilación completa. Después se implementarán Dockerfile y Compose con contexto selectivo, runtime sin root, licencias presentes y puerto publicado sólo en loopback. La web y el server no usan CUDA; los engines mantienen sus imágenes GPU separadas.

## Verificación y límites

El diagnóstico readonly de SWC está sellado en la evidencia privada; root cotejó 107 archivos y 85 fuentes declaradas. La prueba Linux y sus artefactos siguen pendientes. El fallo Windows se conserva y no se convierte en PASS por esta decisión. Cualquier adaptación de la verificación de T-08 necesita evidencia real de Docker y revisión/QA posteriores.

`--network=none` de un build limita los pasos RUN, pero no acredita aislamiento de la resolución de FROM: la primera prueba privada observó un paso de autenticación del registro con `--pull=false`. El incidente se conserva; no se presenta esa corrida como totalmente offline. La alternativa debe utilizar la imagen local comprobada sin resolver tags ni introducir descargas.

No se promete igualdad bit a bit de imágenes ni artefactos. Sólo se tocarán recursos propios acreditados; no se ejecutará prune global ni se modificarán servicios existentes.
