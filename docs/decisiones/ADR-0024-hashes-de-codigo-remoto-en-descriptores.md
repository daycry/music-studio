# ADR-0024 · Hashes de código remoto en el descriptor del modelo

- **Estado:** aceptada · **Fecha:** 2026-10-05

## Contexto

T-06 exige que el descriptor ACE-Step incluya los hashes del código cargado con
`trust_remote_code`. ADR-0006 ya exige fijarlo y verificarlo, y el manifiesto dispone de
`pipeline.remote_code`. El contrato Python de `ModelDescriptor` todavía no tenía un campo
para conservar esa información: `extra="ignore"` descartaba un `remote_code` añadido por el engine.

## Decisión

Se añade a `ModelDescriptor` el campo opcional `remote_code`, una lista vacía por defecto.
Cada entrada contiene `path`, relativo a `models/`, y `sha256`, con 64 caracteres hexadecimales
en minúsculas. La validación de rutas reutiliza la regla de `Weight`; no admite rutas absolutas
ni recorridos que salgan de su raíz.

El engine obtiene las entradas de `models.lock.json` y verifica los archivos antes de cargar
código remoto. Publicar un hash en el descriptor no sustituye esa verificación en runtime.
El consumidor puede copiar la procedencia al manifiesto sin buscar información fuera del catálogo.

El cambio es aditivo y mantiene la versión `/v1` y `CONTRACT_VERSION = "1"`. Los descriptores
anteriores sin el campo siguen validando; los clientes antiguos ignoran el campo nuevo.
Los campos existentes conservan sus tipos y su obligatoriedad. Se regenera `engine-v1.json`
desde el modelo Python, con pruebas de conservación del campo, compatibilidad y rechazo de
rutas o hashes inválidos.

## Consecuencias

- El catálogo conserva los hashes exigidos por T-06 y permite trasladarlos al manifiesto.
- Los engines sin código remoto emiten una lista vacía; no se les exige una migración.
- El descriptor no acredita capacidades ni la integridad real de archivos por sí solo.
- No se cambia el esquema de la BD ni el formato del manifiesto.

## Referencias

- [Contrato de engines](../arquitectura/contrato-engines.md).
- [Datos y manifiestos](../arquitectura/datos.md).
- [ADR-0006](ADR-0006-seguridad-de-pesos.md).
- [Ledger de M0, T-06](../roadmap/2026-09-28-m0-entorno-y-motor/tasks.md).
