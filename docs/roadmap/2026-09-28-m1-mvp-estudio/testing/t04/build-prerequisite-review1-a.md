**Lente A: 0 Critical / 0 Important / 0 Minor**, exclusivamente para el prerrequisito de build T04.

| Tarea → criterio revisado | Resultado | Evidencia fichero:línea |
|---|---|---|
| T-04 → seis versiones y licencias exactas registradas | ✓ | `docs/legal/licencias.md:167–172`: hatchling MIT; pathspec MPL-2.0; trove-classifiers Apache-2.0; packaging Apache-2.0 OR BSD-2-Clause, elección BSD; pluggy y tomlkit MIT. Coinciden con metadatos y avisos conservados de las ruedas. |
| T-04 → origen y pin privado verificables | ✓ | `.cache/dev-cycle/m1/t04-build-prerequisite/build-backend.lock.json:1722`: allowlist con seis versiones, URL y SHA-256. Cotejo independiente de JSON, ZIP, **179 miembros**, metadatos, avisos y fuentes: exit **0**. |
| T-04 → comparación exacta del código existente | ✓ | `report.md:7–9`: tres árboles históricos coincidentes; packaging/pluggy coincidentes salvo RECORD de instalación y extras INSTALLER/REQUESTED explícitos. Comprobado por miembros; no se equipara hash ZIP con hash de directorio. |
| T-04 → tomlkit identificado como candidato pendiente | ✓ | `docs/legal/licencias.md:163`; `receipt.json:6–8`: cierre importable incompleto, tomlkit ausente, seis ruedas verificadas. No se reclama instalación ni ejecución. |
| T-04 → alcance y `Archivos` conformes | ✓ | `tasks.md:177`: registro legal del toolchain QA declarado. El diff completo contiene únicamente las seis filas y su contexto; encaja en el prerrequisito documentado en `tasks.md:634`. |
| T-04 → principios explícitos de constitución | ✓ | Sin contradicción con `docs/CONSTITUTION.md:25` — ubicación dentro del proyecto— ni `:33` —estado y cierre en ledger—. |
| T-04 → evidencia de verificaciones | ✓ | `cli-original.jsonl:29`: finalización ejecutada, exit **0**, salida «Evidence sealed; existing closure incomplete: tomlkit absent; root review pending». T04 continúa `en-progreso` (`tasks.md:171`); no procede exigir evidencia de cierre ni ejecutar su Verificación para suplirla. |
| T-04 → tests, TDD y cobertura del diff | N/A | Cambio documental y de procedencia; no código ni criterios de aceptación cerrados. No corresponde porcentaje de cobertura. |
| T-04 → generados/descriptores E2–E3 | N/A | El diff no toca `commands/`, `agents/` ni `hooks/`; no corresponde ejecutar exportador interop. |

Los ocho criterios funcionales de T04 (`tasks.md:183–190`) permanecen abiertos: carriles, EngineBackend, cadenas, resolver, descarga/VRAM, NDJSON, reintentos y recuperación. **No se evalúan ni aceptan en este despacho.**

Limitaciones: revisión local de evidencia conservada, sin red ni ejecución del backend, instalación, build o QA. El resultado acredita este prerrequisito documental y su pin candidato; no acredita cierre importable actual, conformidad histórica ni autorización comercial integral.