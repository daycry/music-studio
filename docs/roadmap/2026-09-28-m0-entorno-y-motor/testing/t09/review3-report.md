# Revisión adversarial T-09 CPU — intento 3

Resultado: **0 Critical, 1 Important pendiente, 0 Minor**. R09-04a/b y las guardas derivadas pasan; la corrección de cadencia introduce una regresión de observación cuando el sensor consume todo el periodo. T-09 permanece en-progreso, sin QA ni ejecución del benchmark GPU.

Cuatro contextos frescos A/B/C/D, solo lectura. Delta íntegro de cuatro archivos,22590bytes,SHA `760a07337fb4ca1a92bbc284808b46461e4cbefc6c62a515e263d86b23ba8e68`. Las33fuentes congeladas permanecen intactas; scope-check exit0, sin archivos ajenos, avisos ni exclusiones. Diff completo aislado227678bytes/SHA `049391410cf3fbf4835de8dbc428d622a9e2074cc5751d1d312c64ad3efb20ca`.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Deadline HTTP en conexión/envío/cabeceras/chunk/extensión/body | ✓ | D reproduce límite40ms y cierre; A/B regresiones conformes |
| Cadencia con sensor500ms | ✓ | Muestras0/1/2/3s; stream500ms, observación4s |
| Deadline original, terminal tardío, límiteNDJSON | ✓ | Regresiones dirigidas conformes |
| Job observable si sensor consume el periodo | ✗ | R09-08: ambos canales se omiten permanentemente |
| Seguridad del transporte | ✓ | C verifica tokenloopback, HTTP400/cierre y302 sin redirección |
| Coste añadido del transporte/sampler | ✓ con límite | D no identifica degradación significativa nueva; sensores reales pendientes |
| TDD, diagnóstico, cobertura y alcance | ✓ | CincoRED; suite267; mediaoficial15archivos87,45%, mínimo67,96%; scope0 |
| Aprobados anteriores/rebate parcialR09-07 | ✓ preservados | Sin evidencia nueva que reabra los casos previos |
| GPU/XL/RTF/calidad musical/calibraciónGUI | Pendiente | CPU no acredita estos resultados |

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| R09-08 | Important | Sensor lento causa inanición de consultas del job | T-09 | pendiente | B3-01; benchmark_runner.py123/136. Sensor1,5s/periodo1s/horizonte4s/done disponible: fix1done1,51s; fix2timeout4,5s, ceroevents/status. A y D observan el mismo caso fuera de sus lentes. |

Ejecuciones: A50passed/1,56s; B50passed/1,32s; C29passed/5deselected/0,50s más trescasosHTTPsimulados; D27passed/0,49s. Son conjuntos solapados, no se suman como tests distintos. Sin GPU, Docker, red, modelos, audio ni conocimiento ajeno. La reproducción de B compara contra preimagenfix1; no exige una cadencia exacta ni atribuye1,5s de latencia al sensor real.

Arbitraje: se conserva R09-07 SHA64hex descartado(rebatido) por falta de preimagen de kwargs dinámicos/códigosLM. Las guardas reales del adapter y los campos CFG/metadatos/formato disponibles se mantienen. R09-04a/b quedan corregidos en soporteCPU; R09-08 es una regresión nueva, no una reapertura sin evidencia.

La regla del dev-cycle de tres intentos está alcanzada. Root elige **seguir con una corrección concreta y una revisión adicional** bajo la instrucción vigente del propietario «implementar todo el roadmap, y toma las mejores deciciones en caso de que haya alternativas». Esta es una decisión delegada del orquestador, no una aprobación puntual nueva del propietario. Se conserva el historial1/2/3 y la próxima revisión será4; no se acepta el defecto como deuda ni se declaraQA/GPU. La nueva corrección queda acotada a garantizar alguna consulta con plazo global restante cuando el sensor agota el periodo, sin añadir espera si también agota el horizonte ni romper el caso500ms/deadline/cierre/seq.

El control del equipo fue detenido por el propietario con Escape. No se reinicia por una continuación automática del objetivo; no hay captura del panelGPU ni calibración acreditada. La preparaciónGUI previa sólo verificó un heartbeat nativo de Edge en blanco; no es una captura. Ninguna consulta de8768 se repite. TDDn/a: publicación del informe.
