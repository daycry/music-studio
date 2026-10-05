# ADR-0028 — Preparar instrucciones conservando original y entrada efectiva

- **Estado:** aceptada
- **Fecha:** 2026-10-05
- **Decisor:** orquestador, con la autorización del propietario para implementar el roadmap y elegir las mejores alternativas
- **Ámbito:** M0/T-18; preparación de CLI, reutilizable en M1

## Contexto

La [auditoría T-17](../roadmap/2026-09-28-m0-entorno-y-motor/testing/t17/audit-report.md) distingue el material original, la adaptación previa a la CLI y las fronteras del LM musical y del DiT. Los versos de la canción privada se conservaban, pero varias indicaciones de sección se habían simplificado. La CLI no retiraba decoración Markdown ni conservaba una comparación explícita entre original y adaptación. La prioridad del propietario es comprobar estas entradas antes de atribuir la calidad al modelo o cambiarlo.

## Alternativas

| Alternativa | Beneficio | Coste o riesgo |
|---|---|---|
| Limpiar y resumir automáticamente con un LLM | Facilita encajar en límites | Puede cambiar la intención, perder indicaciones y mezclar preparación con creación |
| Seguir con archivos preparados manualmente y sin recibo | Menor cambio de código | No permite comprobar qué se adaptó ni vincularlo a una generación |
| Preparación determinista, opt-in y con procedencia privada | Conserva el original y hace revisable cada cambio | Requiere recibo, validación de integridad y pruebas de publicación |

## Decisión

Elegir preparación determinista en un módulo de biblioteca estándar consumido por la CLI. Se mantienen original y entrada efectiva, hashes de texto UTF-8 y de bytes fuente por separado, transformaciones y diferencias. El estilo sigue entrando como texto mediante `--style`; un archivo de estilo original se declara de forma explícita. Una adaptación manual queda identificada, sin afirmar equivalencia semántica automática.

La letra conserva su texto por defecto. Solo una acción explícita retira el envoltorio Markdown de cabeceras `**[...]**`, conservando literalmente las instrucciones interiores, el orden y el resto de la letra. No se eliminan asteriscos globalmente, no se traducen tags y no se resumen instrucciones.

Una preparación sin generación funciona offline, sin catálogo, HTTP, modelo, trabajo de audio ni FFmpeg. La generación normal usa la misma preparación y vincula un recibo privado e inmutable a sus manifiestos nuevos. El recibo se comprueba contra la petición efectiva; una referencia o contenido alterados se rechazan. Se preservan todos los originales, tomas y manifiestos ya publicados. La referencia nueva es opcional para mantener compatibles los manifiestos v1 existentes.

Tonalidad y compás son campos opcionales explícitos. No se deduce una tónica de «mayor» ni se inventa un compás. El adaptador los transmite en los campos upstream correspondientes. Transportar el idioma estructurado al LM y controlar el presupuesto de tokens pertenecen a T-19.

## Consecuencias

El usuario puede revisar la preparación antes de gastar GPU y comparar una toma con sus instrucciones de origen. Los textos y diferencias quedan dentro de datos privados; los recibos públicos de pruebas usan cifras, hashes y fixtures sintéticos. M1 podrá reutilizar el módulo y formato sin duplicar el algoritmo.

Una preparación válida no acredita que el motor acepte su presupuesto ni que cumpla musicalmente las instrucciones. Hasta T-19 ese presupuesto se señala como pendiente. La obediencia y naturalidad siguen requiriendo las pruebas musicales de T-08/T-12/T-13; no se elige un modelo ni se aprueba calidad por pruebas CPU.

La generación vincula además una ejecución a un recibo nuevo: base de semilla resuelta y cantidad de salidas. La petición de origen conserva su semilla, incluso cuando era nula. Cada manifiesto guarda el índice de variante y el verificador exige la igualdad exacta entre semilla publicada y base más índice, no solo pertenencia a un rango. Un hash declarado de letra debe coincidir con los bytes fuente; BOM y finales de línea forman parte de esos bytes. El descriptor conserva los valores de `key` aceptados antes de esta ampliación.

## Referencias

- [Ledger M0, T-18 y T-19](../roadmap/2026-09-28-m0-entorno-y-motor/tasks.md).
- [Pipeline y CLI](../arquitectura/pipeline-audio.md).
- [Constitución](../CONSTITUTION.md), procedencia, inmutabilidad y privacidad.
