# T-05: QA4 actual de SQL y selección de motores en Windows

Fecha: 2026-10-09. QA independiente del productor y de los revisores.

La pareja Windows y los tres casos Linux pasaron con el código actual.
Root aceptó técnicamente la unidad SQL/identidad; T-05 completa sigue abierta.

## Alcance y resultados

Las 33 suites conservan los 1.056 casos originales y añaden los diez casos
actuales de identidad. No se modificaron las expectativas para obtener verde.

| Fase | Resultado real | Duración |
|---|---|---|
| Funcional sin instrumentación | 1.063 PASS, 3 SKIP, 0 FAIL/ERROR | 368,24 s |
| Cobertura oficial | 1.062 PASS, 3 SKIP, 1 deselectado, 0 FAIL/ERROR | 464,28 s |

Ambos comandos terminaron con exit 0 mediante espera real. La sesión 7354
ha terminado; los procesos 21064 y 28716 no deben reiniciarse ni consultarse
como ejecuciones activas.

El caso original `test_global_busy_gpu_negative_once_and_available_cpu_native[801]`
pasó sin instrumentación en 2,821 s, conservando sus aserciones y su plazo.
Es la única omisión de la fase de cobertura prevista en ADR-0064/0067.
Los diez casos de identidad se ejecutaron en ambas fases. Se conserva la
observación de otros backends y el descarte del seleccionado si cambia su
identidad o su asociación durante una espera de catálogo, sin reservar ni
enviar trabajo al reemplazo.

## Cobertura de módulos completos

Porcentaje combinado de líneas y ramas; cero exclusiones de código.

| Módulo | Cobertura |
|---|---:|
| `app/models/__init__.py` | 99,1525 % |
| `app/snapshots.py` | 91,4463 % |
| `app/migrations/cpu_publication_invariants.py` | 89,7603 % |
| `app/migrations/versions/0006_cpu_publication.py` | 100 % |
| `app/queue/dispatcher.py` | 86,8421 % |
| `app/queue/resolver.py` | 90,0735 % |

El informe oficial incluye también los módulos Alembic 0001–0005 y su
`__init__.py`; no se ocultaron para calcular el gate de los seis módulos.

## Comprobación del orquestador

Root verificó JUnit, orden de colección, skips, deselectado exacto y cálculo
de cobertura. Cotejó los bytes actuales de 117 fuentes, 112 protegidas en
este alcance, 8.126 archivos del entorno gestionado, 136 entradas del espejo,
configuraciones y recursos. Los recibos antes/después coinciden.

SourceGuard se instaló antes de pytest y de cobertura; las fuentes mapeadas
se compilaron con su ubicación original. Se comprobó UTF-8 explícito y
ausencia de trazado previo en la fase funcional. Esto no certifica un cierre
exhaustivo de código nativo/TCB ni retroactivamente el primer RED histórico.

Evidencia local, excluida de Git:
`.cache/dev-cycle/m1/t05-current-sql-independent-qa4/` contiene comandos,
stdout/stderr, JUnit, colecciones, cobertura, custodia y
`root-windows-pair-verification.json`.

## Suplemento Linux y trabajo pendiente

Los skips Windows son exactamente:

- `test_logging_paths.py::test_logging_confines_symlink_sink[directory]`.
- `test_logging_paths.py::test_logging_confines_symlink_sink[file]`.
- `test_persistence_t02.py::test_snapshot_symlink_directory_rejected`.

La ejecución Linux actual, liberada tras preflight separado, terminó con
3 PASS y exit 0. Root verificó JUnit, los tres IDs, 39 cargas guardadas y
139 metadatos, fuentes actuales, paquetes y preservación de recibos Windows.
El contenedor propio se retiró tras comprobar owner e imagen. Se verificaron
705 artefactos finales; tres enlaces de fixtures quedaron inventariados sólo
por metadatos, sin atravesarlos. Los errores de inventario Windows se
conservaron y no requirieron repetir tests. El estado terminal procede de
inspect y del comando start con attach; no se inventa un recibo docker wait.

No se suman resultados históricos a esta pareja. Tampoco se acredita con estas
pruebas la integración real WAV/FFmpeg/publicación, el runtime CPU2, beats,
la imagen server final, E2E, Git ni la aceptación de todo M1.
