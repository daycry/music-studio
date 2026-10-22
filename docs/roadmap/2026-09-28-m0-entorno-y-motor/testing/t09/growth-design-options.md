---
estado: borrador
opcion_elegida: pendiente
decisor: root, bajo delegación autónoma explícita
adr: pendiente de decisión de root
---

# Opciones de crecimiento T09, antes de implementación

## 1. Contexto y restricciones

Diseño privado sobre las 16 copias congeladas de esta fase. Revisión3 A/B/D completa: 0 Critical y 6 Important distintos; R09-T10/B3-01 y R09-T13/D-04 son este alcance. R09-T08/A-05/B3-04 y D-01/02 requieren migración de pruebas bajo la frontera live decidida por root. El actor paralelo corrige otros gaps; este diseño no certifica sus cambios. No se ha releído producción viva ni ejecutado pruebas de producto.

ADR-0042 y ADR-0045, spec M0 aprobada y T09 siguen obligando a 160 outcomes, diez baseline/diez loaded/diez unloaded, frescura 900 s, anclas externas, hashes de fuentes, lifecycle y lectura FINAL independiente del RAW completo. Permanecen 64 Mi caracteres por segmento, 1200 por fragmento, 256 KiB por JSON pequeño y frame, 2 s por episodio y cadencia 2,5 s. No habrá flags de confianza legacy ni rutas elegidas por el caller. El manual `task_manager_v1` sigue permitido; V1/V2 live se rechazan incondicionalmente, incluso con `observer_factory`.

## 2. Criterios de decisión

1. Semántica canónica idéntica, incluidos rechazos/interrupciones y todas las operaciones/RAW/progresos.
2. Validar una vez los bytes nuevos y sus anclas auténticas; invalidar cuando se pierde la inmutabilidad/custodia. Un hash cacheado o mtime no acreditan inmutabilidad.
3. Respuestas y prerequisites constantes respecto a historia; sólo referencias opacas a artefactos propios, nunca un trusted root suministrado por RPC.
4. Sampler y deadline independientes durante bootstrap, reanudación, auditoría y empaquetado.
5. Coste total O(bytes originales + entradas), excluida la pasada FINAL obligatoria; no O(N²).
6. Migración auditable: preservar assertions/RED antiguos y mantener lectores offline válidos en la suite actual.

## 3. Opciones

| Opción | Descripción | Complejidad | Riesgo | Coste relativo | Reversibilidad |
|---|---|---|---|---|---|
| O1 | Estado canónico incremental sobre los ficheros actuales, con custodia inmutable real de todos los bytes e inventarios de directorio | Alta | Alto: protección de namespace y muchos handles | M en código, L en recursos | Alta: formato RAW igual; quitar caché devuelve relectura |
| O2 | Estado canónico incremental sobre cápsulas canónicas propias de bytes originales, reunidas en packs inmutables acotados; sidecars actuales conservados y cotejados en FINAL | Alta | Medio-alto: nueva frontera de almacenamiento/custodia debe quedar explícita | L | Media: formato aditivo, lectores anteriores y originales conservados |

**O1.** El validador conserva estado de transición canónico y mantiene abiertos los ficheros originales con denegación de escritura/borrado y exclusión efectiva de adiciones/reemplazos en el namespace del episodio publicado. No basta abrir el directorio con share-delete desactivado: eso no prohíbe crear hijos. La implementación necesita un broker de almacenamiento que cierre el namespace o protección efectiva equivalente, probada frente a modificación, rename, unlink, nuevo RAW y symlink/reparse. Sin ella, una petición no puede usar caché: invalida y bloquea aceptación hasta rebootstrap independiente. Es la menor alteración de formato, pero para N=48.000 y seis ficheros mínimos por episodio serían ≥288.000 identidades/handles protegidos si se pinna cada fichero. No se recomienda presumir que esa cardinalidad es operativamente viable en Windows.

**O2.** El supervisor crea una cápsula cerrada que contiene los bytes exactos de request, prepared, commit, RAW y progresos, inventario completo, recibo/attempt y ancla externa. El artefacto canónico online pasa a ser esa cápsula propia, no un resumen ni una ruta ajena. Los packs contienen hasta 32 intentos y respetan el límite existente; se cierran antes de anunciarse y se pinna su identidad con deny-write/delete. Cada pack tiene índice cerrado: no existe una operación de añadir un RAW a un pack publicado. Cualquier cápsula demasiado grande se fragmenta conforme al transporte actual sin ampliar límites; un intento indivisible que exceda el límite se rechaza, no se trocea silenciosamente su semántica. El índice/manifest aporta offsets y longitudes con límites comprobados, sin extracción de rutas.

La cápsula se verifica y obtiene aceptación dentro del deadline original; el empaquetado por lotes, posterior y fuera del episodio, sólo transporta cápsulas ya custodiadas, no fabrica aceptación tardía. No desplaza la comprobación de bytes/publicación al instante de exportar el pack. Los originales sueltos siguen preservados. FINAL relee todos esos originales, más cápsulas/packs y anclas, compara bytes y recompone sin caché. Cambios en un sidecar no acreditan cambios en la autoridad online inmutable; impiden FINAL. **Esta distinción de autoridad es una frontera documentada nueva que root debe aprobar mediante ADR antes de implementación.** Si root exige que cualquier mutación del sidecar invalide aceptación online inmediatamente, O2 necesita también la protección de namespace de O1; no sirve un watcher con entrega eventual.

## 4. Recomendación y decisión pendiente

Recomiendo **O2**, sujeto a aprobar explícitamente la cápsula como original canónico online y demostrar su custodia real. Reduce el coste de protección a O(N/32) packs cerrados (aprox. 1.500 en el ejemplo lógico), en lugar de cientos de miles de ficheros abiertos. Preserva interpretación y FINAL; hace verificable qué bytes se aceptaron. No existe una solución segura O(delta) sobre ficheros arbitrariamente mutables usando sólo hashes antiguos: comprobar toda mutación exige releer, protección inmutable o un canal fiable de invalidación con orden atómico.

No se fija opción. Root elige tras esta entrega; no se escribe ADR aquí. Si no se aprueba ninguna frontera inmutable, D-04 permanece abierto y el benchmark no está listo. Mantener relectura completa es un fallback honesto, con el coste y el bloqueo declarados, no una tercera opción que resuelva el requisito.

## 5. Impacto real

| Ruta propuesta | Responsabilidad y frontera |
|---|---|
| `scripts/eval/benchmark_episode.py` | Extraer transición canónica compartida; `read_publications` FINAL instancia estado vacío y carga todos los bytes originales; captura canónica dentro de deadline para O2 |
| `scripts/eval/benchmark_canonical.py` (nuevo) | Tipos `CanonicalState`, `VerifiedAttempt`, `VerifiedWindow`; transición pura idéntica para online y offline, sin I/O ni autoridad del caller |
| `scripts/eval/benchmark_custody.py` (nuevo) | `OwnedArtifactBinding`, `PublicationCursor`, `ImmutableCanonicalStore`; lectura limitada, identidad/inmutabilidad y anclas externas autenticadas; no resolver rutas RPC |
| `scripts/eval/benchmark_audit.py` | `AuditPrefix.commit` prepara sólo delta, verifica contra estado anterior y hace commit atómico de posiciones/hash/estado |
| `scripts/eval/benchmark_coordinator.py` | Custodia/export de nuevos intentos; indexado por ordinal; historial accesible por cursores; sampler sin lock largo de I/O |
| `scripts/eval/benchmark_runtime.py` | `validate_delta`, `audit_validate`, `refresh_accreditation`, `calibration_export`, `row`: consumir store propio/ventanas verificadas, respuesta sólo referencia bounded |
| `scripts/eval/benchmark_observation.py` | Ruta online interna sobre `VerifiedWindow`; lectores públicos offline `validate_auto`/`read_acquisitions` siguen revalidando política histórica |
| `scripts/eval/benchmark_runner.py` | Métricas seleccionadas por rango del store, sin llamar `accepted_samples` sobre todo el prefijo en cada fila |
| `scripts/eval/benchmark.py` | Guardar referencia de prerequisites; bootstrap/restart y FINAL explícitos; guarda legacy pertenece al otro actor |
| `scripts/eval/tests/test_benchmark_canonical_growth.py` y `test_benchmark_legacy_boundary.py` (nuevos) | RED de interfaces/custodia/coste y frontera legacy; migración concreta en manifest privado |

Los nombres nuevos son propuestas de diseño, no ficheros existentes ni implementación. Contrato `/v1`, imagen, pesos, BD y server no cambian.

## 6. Riesgos y mitigación

Estado resumido insuficiente: conservar último predecesor completo y estado de rechazos, ambos relojes, ordinal, stream/contexto; pruebas diferenciales online/offline. Custodia falsa: rechazar escrituras/reemplazos realmente y probar identidad nativa; ni watcher eventual ni mtime. Ancla firmada por caller: clave/authority bootstrap fuera del payload y del almacén no confiable. Saturación de CPU: auditar en worker independiente, controlar backlog con fail-closed y medir cadencia real; no garantizar prioridades de SO. Cambio de fuentes: nuevo epoch/plan, no recertificar anterior. Pérdida de ACK: transacción idempotente de consulta, no nueva adquisición/inferencia. Caché de una acreditación vieja: freshness se evalúa contra reloj externo actual, no se cachea un booleano `valid`.

## 7. Preguntas abiertas resueltas o delegadas

Resueltas: legacy live no está soportado; manual sí; política offline vieja intacta; no adaptar sólo la etiqueta del método; FINAL siempre independiente; root decide, sin preguntas al propietario ausente. Pendiente de root: O1/O2 y autoridad canónica de cápsulas. Pendiente de prueba del implementer: custodia nativa efectiva y coste real de captura dentro de 2 s, backlog/cadencia bajo volumen canónico. No se inventan resultados de esas pruebas ni coste económico.
