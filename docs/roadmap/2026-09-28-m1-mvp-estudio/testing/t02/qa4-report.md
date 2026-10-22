# QA independiente M1/T02 — unidad técnica de base de datos

Aceptación técnica propuesta: conforme, limitada a T02. M1 completo, M-03 real, aceptación humana, Git y cierre del ledger siguen pendientes y pertenecen a raíz.

Suite actual: **327 pass, 3 skips Windows, 330 casos distintos**; Linux verifica los mismos tres casos symlink, sin sumarlos otra vez. Selección exacta original: **30 pass/300 deselected**, incluida en los330. Ruff actual: exit0. No tests/producción/locks canónicos modificados. Copias privadas sólo bootstrap/rutas; assertions AST idénticas. ONE0003 y TWO0002 históricos intactos.

Cinco criterios originales conservados íntegros en unit-fixture/tasks.md y spec.md; backend-mapping.json vincula evidencia. Esquema23/usuario local/WAL/FK/FTS, regeneración/round-trip/restauración, backup diario cancelable/rotación14días/última válida/restore WAL FTS, linaje/multipadres/papelera verificados por tests actuales. Regresiones SQL/Core/ORM/bulk, promoción de soporte, globals/dependencias dirigidas, invalidación, conflictos/rollback y concurrencia incluidos en suite330.

CLI real gestionada:18operaciones, vacío y poblado, head0004→0003/0002/0001/base→head, con revisiones/FK/datos verificados. Wheel construido nuevo:28recursos iguales a fuente; instalación privada host y Docker sin dependencias/red y paridad exacta. DockerCPU runc/.5CPU/512MiB/sinDeviceRequests/sinprivileged/sinTorch, imagen existente fijada; primer runtime completo, symlink Linux, backup/FTS/importación/promoción/eventos seguros conformes. Reinicio real docker restart en restart-fixed-current con wait0, datos persistidos y regeneración de JSON dañado/backupFTS; logs e inspect conservados. Uso de [create](https://docs.docker.com/reference/cli/docker/container/create/) y [restart](https://docs.docker.com/reference/cli/docker/container/restart/) contrastado con contrato oficial.

Limpieza: todos los contenedores propios removidos tras comprobar labelowner. Nueve controles preexistentes sobreviven primera limpieza; inventario terminal actual incluido. Sin GPU/WSL/Ollama/navegador/descargas/modelos/build de imagen/Git/ledger/knowledge. Sólo escrituras privadas; intérprete gestionado con env.ps1, uv --no-sync y Python-B. No afirmar protegidos run.py/metrics/benchmark intactos: son actores externos ajenos al freeze32.

Fallos retenidos: descubrimiento inicial qa-gate en shared inexistente y rg glob Windows inválido; primer fullserver326pass/1fail/3skip por profundidad extra de fixture privada. Corregir sólo salida conservó assertions y repeticiónfull330 justificadamente verificó327/3. Primer restart wait1 no guardó traceback antes de limpieza; causa de ese proceso individual desconocida. Reproducciones privadas identificaron eliminaciónapp+uv omite reinstalar, y destino restore reutilizado; --reinstall y destino único sólo en runner resuelven. Linux inicial no tenía pytest, luego faltaba py.py: discovery parcial retenida, prueba final trespass con libs existentes copiadas offline. Fallos de quoting/preparación privados retenidos en cli-original/transcripción; no atribuirlos a producción ni borrar evidencia. No reejecutados helpers exclusivos históricos.

Puertas: ledger-lint y coverage-check original salidas intactas. Unit qa-gate usa adapter transparente desde JUnit real backend, no fabrica ejecuciónPlaywright. Estado globalM1 NO-VERDE por ausencia resultadosE2E; M1 tieneUI y M-03 real continúa pendiente. T03 factory/API/red futuro fuera de esta unidad y sin adjudicarlos como bugs nuevosDB.

Cobertura oficial actual completa de los tres módulos cambiados, no líneasdiff ni media diluida: {"apps/server/app/snapshots.py": {"covered_lines": 351, "num_statements": 380, "percent_covered": 92.36842105263158, "percent_covered_display": "92", "missing_lines": 29, "excluded_lines": 0, "percent_statements_covered": 92.36842105263158, "percent_statements_covered_display": "92"}, "apps/server/app/migrations/fix3_invariants.py": {"covered_lines": 4, "num_statements": 4, "percent_covered": 100.0, "percent_covered_display": "100", "missing_lines": 0, "excluded_lines": 0, "percent_statements_covered": 100.0, "percent_statements_covered_display": "100"}, "apps/server/app/migrations/versions/0004_snapshot_promotion.py": {"covered_lines": 10, "num_statements": 10, "percent_covered": 100.0, "percent_covered_display": "100", "missing_lines": 0, "excluded_lines": 0, "percent_statements_covered": 100.0, "percent_statements_covered_display": "100"}}. Ceroexclusiones, cada uno≥80. Fuente32revalidada antes/después; recibos tienen argv/inicio/finUTC/exit nativos, stdout/stderr/JUnit exactos. Conteos de SELECT actuales quedan en test-output; no inferir latencia.

Gate unidad (exit0):
```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 327,
    "failed": 0,
    "flaky": 0,
    "skipped": 3,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}

```
Gate originalM1 (exit1):
```json
{
  "verdict": "NO-VERDE",
  "reason": "sin resultados: results.json no existe (la ausencia de evidencia es rojo)"
}

```

Modelo real/tokens/EUR/horasIA: NULL; peso estimado3 dado por raíz. No sellar CLI viva: cli-original.jsonl y cli-stderr-original.txt excluidos del inventario cerrado; raíz certificará terminal de este CLI tras retorno. Los procesos de comandos creados aquí terminaron; sin contenedores propios vivos.

Puerta de cobertura y protección terminal: official-whole-module-gate-final.receipt.json exit0, parser oficial parsear_pytest sobre JSON actual, umbral≥80 por cada módulo completo. canonical-test-protected-diff.json coteja todas las fuentes de tests copiadas con hash inicial. Fallo privado de finalización por nombre parse_pytest inexistente conservado en transcripción; corregido a parsear_pytest, sin repetir tests/gates ya terminados. Sin PDF en este alcance privado autorizado.

El primer wrapper terminal de cobertura falló por KeyError al usar la ruta normalizada del parser contra las claves Windows del JSON; recibo exit1 preservado. Corrección privada del lookup; wrapper final exit0. No cambios/exclusiones en cobertura ni repetición de suite.


**Aclaración de custodia root:** el recibo correcto del gate final de cobertura es `official-whole-module-gate-final.receipt.json`, exit0. El primer `official-whole-module-gate.receipt.json` tiene exit1 por separadores Windows en el parser privado y se conserva. La mención anterior a ese nombre como exit0 es un error del informe original, no de los tests ni de la cobertura. Root verificó ambos recibos y el JSON oficial actual.
