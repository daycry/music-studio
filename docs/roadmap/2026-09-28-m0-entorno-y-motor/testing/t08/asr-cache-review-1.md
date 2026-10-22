# T-08 — revisión 1 de la caché ASR conforme

2026-10-06. A, B, C y D son contextos frescos, independientes de implementar. Se ejecutaron secuencialmente por el límite de agentes. Todos leyeron los cuatro deltas completos: Dockerfile, README, tag de Compose y test nuevo. Los tres baselines reproducen los SHA del recibo CLAP anterior; se preservan sus finales de línea mixtos. El [parcial](asr-cache-review-1-in-progress.md) conserva los resultados y desviaciones del despacho.

| Criterio | A | B | C | D |
|---|---|---|---|---|
| Caché real escribible, UID10001 y configuración predeterminada | Conforme | Conforme | Conforme | Conforme |
| Ruta fija dentro del proyecto, propietario engine y permisos0755 | Conforme | Conforme | Sin ampliación de privilegios | Preparación en build |
| Preservación de CLAP, modelos, dependencias, token, montajes y puertos | Conforme | Conforme | Sin exposición nueva | Sin operaciones nuevas por duración |
| Regresión real anterior al cambio | RED/GREEN acreditados | Test completo coherente | Sin ejecución dinámica nueva | Una escritura/lectura de33bytes en el test |
| Documentación y tag correctos | Conforme | Conforme | Conforme | Sin recorrido productivo adicional |
| Alcance y hashes |22fuentes/39artefactos |22fuentes |3baselines |3baselines/22fuentes/39artefactos/19imagen |
| QA independiente, ASR y alineación GPU, precisión y memoria | Pendientes | Pendientes | Pendientes | Pendientes |

Cero Critical, Important o Minor; sin rebates ni deuda. C no identifica CWE aplicable. D no encuentra N+1, bloqueo o complejidad adicional por audio de hasta600s; no aporta benchmark GPU. Cada lente ejecutó por separado la regresión real del FileCacheManager en imagen d20ae562: A1passed0,36s, B1passed0,37s, C1passed0,36s, D1passed0,37s. Son pruebas dirigidas independientes, no una suite agregada. Sin GPU, pesos, montajes ni overrides de caché/usuario; red desactivada.

A declaró una consulta ADR/knowledge de cero aciertos pese a la exclusión explícita del despacho. No se usa ningún resultado; la desviación está conservada en el parcial. B, C y D respetaron la prohibición de consultas y no mutaron archivos. El lookup de tier propio de A falló en un paquete sin agents y declaró fallback al frontmatter instalado; el despacho de root usó su lookup disponible. No se inventa el consumo del modelo.

Root vuelve a comprobar22fuentes y39artefactos congelados antes de publicar. Cobertura del cambio de configuración n/a: no hay lógica Python productiva nueva. El test verifica la escritura/lectura, ruta, UID, propietario y permisos sin ocultar el defecto con variables de entorno. Interop y OpenAPI no aplican. La corrección mínima conserva el runtime sin privilegios.

Esta revisión permite pasar a QA independiente. No prueba transcripción o alineación real, pico VRAM/spill, calidad musical ni los criterios completos de T-08. M0 continúa abierto y no se integra main.
