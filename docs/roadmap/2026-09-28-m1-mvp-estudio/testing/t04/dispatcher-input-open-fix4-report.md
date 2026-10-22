# B4-01 corregido; entrega para revisión componente5 y QA U1 independiente

Se normaliza únicamente `FileNotFoundError` de `source.open("rb")` como `inputs.ResolutionError`, conservando la causa. La apertura exclusiva del destino queda fuera del catch. Admission conserva su traducción existente a `PreclaimResolutionError`; dispatcher/resolver/admission no se modifican.

RED nativo antes de producción: `red-auto` y `red-explicit`, exit1 por `FileNotFoundError` real tras borrar exclusivamente el origen ya validado por `confined_path`. SQLite en archivo migrada0005, Dispatcher/Admission/Resolver reales, Catalog sintético. El automático corta antes del tail; el explícito no obtiene el tipo esperado. Comandos, UTC, stdout/stderr, JUnit únicos y fuentes/runner ejecutados congelados antes de cada RED en sus carpetas. El staging conocido queda vacío en los recibos nativos.

RED: test_native_source_disappears_after_staging_confinement[False] falló con FileNotFoundError · 2026-10-08T00:35:33.180210+00:00.
RED: test_native_source_disappears_after_staging_confinement[True] falló con FileNotFoundError · 2026-10-08T00:35:39.144392+00:00.

GREEN dirigido: 9 passed. Siete controles baseline ya pasaban antes del fix y siguen pasando: source-open PermissionError, source-read FileNotFoundError, destination-open/write FileNotFoundError, fsync, parent mkdir y cleanup. Todos propagan el mismo objeto de excepción, sin visitar el tail ni crear intentos. El explícito comprueba la cadena completa de causas y no visita otros jobs. El automático despacha sólo el tail y no reserva el head inválido.

Verificación final misma fuente: **215 passed = 206 previos + 9 nuevos**. Se conservan los archivos completos previos y los vecinos privados idénticos al predecesor. AST de las 39+17 parametrizaciones previas intacto; 26 protegidos exactos, además de los siete guardados por root. Helper global terminal T08 ya finalizado antes de ejecutar y copiado en el freeze final. Ninguna traza anterior combinada.

Cobertura oficial whole `inputs.py`: **116/134 = 86.57%**, cero exclusiones. Datos originales `.coverage` y copia `coverage-original-data`, JSON oficial y fuente congelada. Admission/dispatcher/resolver permanecen intactos; sus cifras de esta corrida se califican como evidencia sobre fuente vigente, sin gate nuevo para módulos ajenos ni recertificar bytes antiguos. Se mantienen los seis controles de retención postcommit y las guardas de identidad/VRAM/ocupación, staging fuera del writer/event loop y SHA fresco.

Ruff check y format --check: exit0. Inventario completo NONCLI con hash/tamaño; bases nativas y staging durable retenidos como evidencia propia. Ningún borrado ajeno, ledger/docs/Git/contratos/esquema ni infraestructura modificados.

Incidente transparente: primer GREEN dirigido dio 8PASS/1FAIL por expectativa de causa a un solo nivel; Admission ya añadía su causa. Se fortaleció la prueba con los dos tipos y la causa original, sin alterar producción ni asserts previos. Advertencia pytest conocida: cache_dir desconocido al desactivar cacheprovider.

Modelo/tokens/EUR/horas IA reales NULL; sólo asignación estimada root. Sin aceptación de tarea/global/calidad. Review componente5 e independiente U1 QA pendientes del orquestador; no se delega desde esta fase.
