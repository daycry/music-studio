# QA independiente T04 U1 — Windows nativo

**SCOPED_U1_NATIVE_QA_PASS**. Una batería actual: **215 PASS**, 0 fallos, 0 skips, 70,52 s; 190 U1 + 25 vecinos. T04 y sus ocho CA permanecen abiertos; U2/U3 y aceptación corresponden exclusivamente a root.

## Cobertura oficial fresca de cada módulo completo

| Módulo bajo app.queue | Líneas | Cobertura | Excluidas |
|---|---:|---:|---:|
| __init__.py | 0/0 | n/a | 0 |
| admission.py | 192/203 | 94.58% | 0 |
| backends/__init__.py | 0/0 | n/a | 0 |
| backends/http.py | 157/170 | 92.35% | 0 |
| backends/protocol.py | 32/32 | 100.00% | 0 |
| dispatcher.py | 128/145 | 88.28% | 0 |
| inputs.py | 116/134 | 86.57% | 0 |
| resolver.py | 151/163 | 92.64% | 0 |

Gate individual ≥80 % sobre los seis módulos ejecutables actuales. Los dos init sin sentencias son n/a. `.coverage`, copia original y JSON proceden sólo de esta batería, sin unión histórica, media ni módulos omitidos. `72` fuentes archivadas antes y cotejadas después; `62` protegidas root exactas. Vecinos copiados del argv real fix4 byte/AST exactos, incluyendo funciones, helpers, decoradores, params y asserts. Sólo binding Path del vecino schema se redirige mediante conftest privado a own schema-root; ninguna fixture histórica recibe escrituras.

## Evidencia y límites

SQLite 0005 de archivo y FS Windows nativos. Catalog/política, HTTP Mock/ASGI y monkeypatch de intercalaciones son sintéticos explícitos. Batería verifica GPU1/CPU2 de admisión, prioridades/FIFO, not_before UTC microsegundos, selección explícita/automática, páginas de 400 con 401/2001, snapshot finito, recheck actual y transacción identidad/inputs. Screening duradero: un SELECT ocupación por despacho en 200/400/2001, cero en event loop. Hash/copia preceden al writer y corren fuera del loop; perfil hash-io `[[false,true],[false,true]]`. Los cuatro perfiles busy de 200/400 preservan sólo dos SHA por candidato seleccionado, con inputs WAV nativos de 204 bytes.

Seleccionado conserva resolve completo y preflight fresco de busy/identidad/VRAM antes de reserva. Inputs staged de sólo lectura conservan bytes tras mutar origen. Source-open desaparición real: automático visita cola y envía una vez; explícito propaga PreclaimResolutionError → ResolutionError → FileNotFoundError, no envía. Los siete controles access/read/destination/write/fsync/parent/cleanup propagan el mismo objeto y no crean intento. Commit conocido/desconocido conserva intento y copias, sin POST duplicado. B3-01/D3-01/B4-01 cerrados en la batería actual; adjudicación inspection5 A/B/D limpia leída, contador 5 conservado. 8 RED históricos comprobados contra inventarios/JUnit en lectura, ninguno reejecutado.

Los tiempos y heartbeats son observaciones sintéticas, sin garantía realtime ni rendimiento GPU. Casos de protocolo events/status/cancel presentes en los tests existentes no acreditan integración U2.

Ruff no-cache y format --check: exit 0, 13 ficheros. Ledger lint readonly: 0 incoherencias/0 avisos. Wheel actual real Hatchling 1.32.4: ocho módulos queue byte exactos y nueve imports app/queue desde extracción propia, torch ausente. Se copiaron seis wheels cacheadas con pins verificados; sin instalación ni descargas. Se repitió sólo el import dirigido para completar archivo previo de su runner generado; la primera sonda exit0 permanece cualificada. No Docker: packaging resuelto por wheel/import nativos; no Linux ni clean install certificados. No prueba Linux omitida por privilegio: no se intentó. OpenAPI/Playwright n/a sin cambio contractual/UI. TDD n/a QA independiente.

## Custodia

Todos los comandos usan env.ps1 y .venv Python -B, variables UV/TEMP/TMP/pycache/coverage/test roots y basetemp propias. Receipts contienen argv, tiempos, exit y stdout/stderr reales. Las lecturas iniciales sólo tienen transcript de herramienta; stdout/stderr separados UNKNOWN. Datos SQLite y staging duradero/incierto retenidos para evidencia; teardown engines completado, markers workspace 0. No recursos ajenos borrados ni servicios/contenedores/GPU iniciados.

`receipt.json`, `native-ownership-cleanup.json`, mapas before/after, JUnit, cobertura y command receipts detallan la entrega. Inventario recursivo NONCLI SHA/bytes con exactamente cinco exclusiones top-level: cli-original.jsonl, cli-stderr-original.txt, cli-metadata.json, final-original.md y file-inventory.json. Los nombres homónimos anidados se incluyen. Root cierra logs/metadata/final y meter. Peso estimado 1,5; actual modelo/tokens/EUR/horasIA NULL. Ningún ledger, Git, fuente, test, doc o lock modificado por QA.

Incidentes de entrega privados preservados: finalize1 BOM y finalize2 formato de inventario histórico, corregidos sólo en lector; finalize3 exit0. Primera generación del inventario intentó hash de su stderr abierto y falló por sharing lock Windows; se conserva stderr real, generación directa con streams cerrados exit0. No se repitió baseline ni se tocaron fuentes. Streams separados de la generación directa UNKNOWN; transcript tool autoritativo.

