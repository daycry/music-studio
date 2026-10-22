# ADR-0041 — Esquema inicial y snapshots del server

- **Estado:** aceptada; implementación, revisión y QA pendientes
- **Fecha:** 2026-10-07
- **Decisor:** orquestador, bajo delegación autónoma del propietario
- **Ámbito:** M1/T-02, antes de crear la primera base de datos

Un arquitecto fresco comparó SQLAlchemy declarativo tipado con SQL localizado, SQLAlchemy Core y relaciones ORM con automatismos generales. Se elige la primera opción, compatible con el stack aprobado: Alembic para migraciones, SQL explícito para FTS e invariantes, sin cascadas de borrado ni repositorio genérico. [Diseño elegido](../roadmap/2026-09-28-m1-mvp-estudio/database-design.md).

Las23tablas de datos conservan ULID, `owner_id` de usuario, timestamps UTC y borrado lógico. `local` es el nombre del único usuario; su ID es ULID y su propietario es él mismo. La referencia autorreferente se difiere dentro de la transacción inicial. La apertura multiusuario sigue requiriendo decisión posterior.

En `asset`, `subject_type/subject_id` identifican el artefacto y se corresponden con `manifest.subject`; `owner_id` sigue identificando al usuario. Sustituyen los ambiguos campos propios `owner_type/owner_id` antes de existir datos; no se modifica el contrato del manifiesto ni se renombra una columna poblada. Los sujetos internos se validan contra entidades existentes del mismo propietario. `cli_run` y `lora` son sujetos externos al esquema23: no se inventa una FK ni se identifica una LoRA musical con un personaje. La inserción de un sujeto externo exige un validador del server y su manifiesto/catálogo verificable; mientras no exista ese mecanismo se rechaza, sin declarar esa capacidad implementada.

La pertenencia a canción puede ser directa o transitiva por sus entidades. Personajes, presets, colecciones y uploads son bibliotecas globales; la infraestructura `job`, dependencias, configuración y usuario no constituye contenido musical. Los sujetos CLI de M0 conservan su excepción histórica hasta promoción a una canción. Un asset o arista no se convierte en contenido huérfano por omitir una columna redundante si su sujeto o extremos acreditan la pertenencia.

El linaje es DAG: un take original tiene raíz propia; con varios ancestros take se elige el menor ULID entre raíces originales como raíz canónica, conservando todas las aristas. Con padres exclusivamente externos se inicia raíz propia. Se rechazan ciclos, autorreferencias y mezcla de propietarios o canciones; bibliotecas globales del mismo propietario pueden aportar referencias. El borrado lógico de un padre conserva a sus hijos. La purga física no elimina padres todavía referenciados.

FTS indexa canciones activas y exclusivamente su letra vigente, con triggers transaccionales para insert/update/delete, cambio de letra y papelera/restauración. La reconstrucción usa la misma selección. `song.json` es una proyección derivada validada por `song-v1`: primero se confirma SQLite, después se publica un temporal por reemplazo atómico. No hay una transacción común entre BD y filesystem; se serializan escritores por canción y se reconcilian snapshots ausentes, obsoletos o inválidos en arranque. La reconstrucción/importación valida un cierre de referencias, rutas y colisiones antes de una transacción completa.

El backup usa [`sqlite3.Connection.backup()`](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Connection.backup), API nativa de SQLite disponible en el intérprete gestionado, en lugar de instalar la consola para invocar `.backup`. Debe probarse restauración de datos confirmados en WAL y FTS. Publica únicamente una copia íntegra, conserva la última válida si falla y rota archivos propios de14días. Se comprueba al arrancar y diariamente mientras el backend corre, fuera del event loop y sin solapamientos; la parada del backend pospone el trabajo hasta su próximo arranque. No incluye los medios asociados.

SQLite mantiene `foreign_keys=ON` y WAL en runtime. Upgrade/downgrade/upgrade se prueba en bases temporales vacías y pobladas, sin modificar datos reales. Los ciclos se resuelven con referencias diferidas y eliminación transaccional antes de retirar tablas vacías; no se presume que funcione hasta probarlo. Las migraciones y módulos se empaquetan bajo `app`, incluido `0001_initial.py`, y deben funcionar desde la imagen instalada.

No se implementan aquí dispatcher, SSE o rutas de biblioteca. T-01 tiene revisión y QA técnicas conformes; su integración Git y la aceptación final de M1 siguen pendientes. T-02 requiere TDD, revisión A/B/C según el selector y QA independiente, incluidos wheel/Docker y restauración real. Licencias y versiones de dependencias nuevas se verifican antes del uso, preservando versiones anteriores.


**Complemento de snapshots — 2026-10-07:** [ADR-0044](ADR-0044-snapshots-con-dependencias-explicitas.md) elige una raíz completa y dependencias de soporte explícitas, sin expandir otros proyectos completos. Metadatos locales aditivos distinguen soporte e invalidan/publican sólo raíces afectadas; SQL/Core/bulk y globals compartidos deben cubrirse. Contrato v1 con extensión opcional, IDs/propiedad/historia preservados y conflictos explícitos. Implementación/revisión/QA aún pendientes; el baseline23 y su evidencia no se reescriben.


La [QA técnica de T02](../roadmap/2026-09-28-m1-mvp-estudio/testing/t02/qa4-report.md) y la revisión4 son conformes sobre el baseline0004 congelado. Integración Git, verificación global M1 y M-03 real siguen pendientes. El registro de estados permanece en tasks.md.
