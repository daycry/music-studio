> Publicación: las rutas locales se han anonimizado. Los argv y originales exactos se conservan en la evidencia privada.

# QA nativa independiente — pendiente del root

**QA_GREEN_PENDING_ROOT**. Ownership `[]`; sólo salidas privadas. Una única baseline actual, ROOT test byte exact, con --noconftest, config privada y plugins automáticos desactivados: **36 PASS**, exit 0, UUID `f679a219-bda1-4599-bbe4-667097585f60`. UTC 2026-10-08T23:00:36.381639+00:00 → 2026-10-08T23:00:52.121759+00:00; Popen PID 25720. stdout/stderr/JUnit y argv originales en final-official. No repetición ni ampliación de suites históricas.

| Módulo completo | Cubiertas/total | Coverage.py | Excluidas |
|---|---:|---:|---:|
| apps/server/app/worker/custody.py | 191/212 | 90.09433962% | 0 |
| apps/server/app/worker/custody_windows.py | 354/384 | 92.18750000% | 0 |

Dos trazas RAW propias (2 observadas), copiadas y hasheadas antes de combine --keep/export JSON --keep-combined; sólo esta fase. No unión con productor/31 históricos, exclusiones, medias ni extracción de helpers. Source SHA comprobado en los 36 recibos y antes de imports de custodia en el padre efímero, mismo UUID. Checkpoint guardado ANTES de muerte real: no acredita persistencia de instrucciones posteriores a morir. Fixture workload sólo protocolo; el padre importa KernelGroup y aporta cobertura pertinente.

Adjudicación root inspection2 A/B/C/D limpia, B-01/B-02/B-03 root-adjudicados corregidos, freeze3 + fixture cotejados. Fix1 final01 actual36 y originales31 AST subsecuencia exacta comprobados; final04 permanece histórico, sin sustituir inputs. REDs históricos B01 (incluido fortalecido), B02 y B03 con exit1 y fallos de comportamiento inspeccionados, sin repetir. TDD n/a: QA sin nuevos tests ni cambios de producto.

Fuentes causales4 y guards exactos antes/después: True. Contratos privados/protocolo/worker-init y tests aceptados, locks/config protegidos; SQL models/snapshots/migration0006/schemas y sesiones puras ajenas no congelados. Helpers parent.py/run.py actuales copiados byte exact antes de ejecutar, paths parents[4] correctos; bootstrap namespace actual del ROOT test evita app.__init__/main/Settings/.env.

Prueba positiva Windows: nacimiento suspendido, asignación antes de resume, árbol con nacimientos kernel, cierre por OwnJob/handles retenidos, muerte real del padre y witness ajeno propio sobreviviendo, writer realmente bloqueado, cancelación y barreras de hilos. native-observations.json y originales por caso conservan disposiciones, guards, cierres y UNKNOWN. B01 backend de memoria y B03 OpenProcess real con errores inyectados son suplementarios: no fallos espontáneos de WinAPI. B02 usa hilo/barreras reales, sin afirmaciones de rendimiento por reloj falso. Recibo kernel y recursos/stdio completo distintos; referencias negativas retenidas UNKNOWN, no limpieza total inventada ni CPU2 real por slots inertes. Ningún proceso existente/control de servicio/UI tocado; cleanup únicamente referencias propias exactas.

## Ruff de cuatro fuentes actuales, sin mutaciones

- Proyecto check --no-cache: exit 0. Original en lint/.
- Proyecto format --no-cache --check: exit 0. Original en lint/.
- Default aislado check --no-cache: exit 0. Original en lint/.

All checks passed!

4 files already formatted

All checks passed!

No claim Ruff global/strict project equivalente a default aislado. Un fallo del lint requerido bloquea la QA aunque baseline pase; root resuelve después, sin editar fuente/config/noqa aquí. CLI exit0 no sustituye lint verde.

Sin incidentes de ejecución/reintentos del baseline. Lector privado del informe: KeyError por separadores Windows en Coverage.py, original finish-initial-reader-error.py retenido; sólo lector reparado sin ejecutar de nuevo tests/combine. Incidente adicional del registro PowerShell: parser here-string rechazó el comando completo antes de ejecutarlo; ambos registrados en incident-report-reader.json y transcript original, no causal RED. Métricas reales modelo/tokens/EUR/horas IA NULL; originales CLI reservados pertenecen al parent, sin escritura. Inventario NONCLI completo excluye sólo los cuatro nombres reservados exactos del nivel superior y su propio JSON. Root debe cotejar entrega tras terminal CLI y decidir aceptación fresca. Full T05/M1/Linux/CPU2/FFmpeg/audio/SQLite/fs/E2E/derechos/calidad musical UNPROVEN.

Incidente adicional del lector privado: filtro por sufijo incluyó el test en los dos módulos runtime. Original finish-second-reader-error.py y incident-report-reader2.json conservados. Reparación sólo con dos rutas runtime explícitas, antes del primer lint; no baseline/combine/lint repetidos.

El padre efímero terminó con exit1 por terminate() intencional y handle signaled=true; stderr vacío y stdout DEVNULL por receta del test. El pytest oficial terminó exit0. Sus exits acreditan cosas distintas. Los 36 recibos nativos están presentes, con UUID/hash comunes.
