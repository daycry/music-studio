# QA independiente: componente startup ACE M1/T-05

Resultado: **PASS_COMPONENT**, 3/3 Linux, 0 fallos, 0 skips Linux. Windows: 0 ejecutadas, 3 omitidas por requerir shell POSIX. No cierre de T-05/M1 ni aceptación del hito.

Cambio auditado: `apps/engines/acestep/entrypoint.sh` conserva shebang, `set -eu` y `exec "$@"`; elimina el import de torch anterior a la delegación. Fuentes/test exactos del source-receipt, sin cambios antes/después (source-before.json/source-after.json). No escrituras propias en fuentes, tests, docs ni ledger.

## Conducta verificada

| Prueba real Linux | Resultado | Evidencia |
|---|---|---|
| Delegación antes de cualquier llamada Python por PATH; trampa Python exit97 no activada | PASS | cases.json, linux.xml, linux.stderr.log |
| argv vacío/espacios/metacaracteres/comillas/Unicode conservados; exit23; PID igual al Popen original mediante exec | PASS | cases.json, linux.xml, linux.stderr.log |
| SIGTERM llega al proceso delegado y termina exit42; finally reap completo | PASS | cases.json, linux.xml, linux-cleanup.json |

Runner independiente stdlib unittest carga los tests existentes desde el repo RO. El arnés usa un comando Python de prueba como consumidor; no ejecuta el preflight real ni importa torch/ACE. El gate-input.json es una adaptación explícita de los casos unittest observados al formato aceptado por qa-gate; no evidencia Playwright.

## Entorno y custodia

Contenedor CPU Linux imagen fija `sha256:1c18c0ef8ed31d824452f8f3d449f93700c1f26fabd90c4ca0c7c69190df719d`, USER 19000:10001, repo RO, rootfs RO, red none, caps ALL retiradas, no-new-privileges, sin dispositivos/GPU ni privilegios. Único bind RW propio: esta carpeta /qa; TMPDIR=/qa/tmp existente. docker-create.receipt.json contiene argv; docker-inspect-before/after.stdout.log contiene configuración/estado real. Contenedor `6affa0ca719a13eea5fbf8668daec559f8b13377c4b3fc6e189e1da4a840a054` terminó exit0 y fue eliminado por su ID exacto; docker-remove exit0 y docker-absence exit1/no such object. linux-cleanup.json: cero entradas temporales y cero PID hijo restante.

No instalación, descarga, acceso WSL, reconstrucción ACE, GPU o Playwright/PDF. Env.ps1 cargado y uv managed --no-sync; no Python de máquina.

## Puertas

Ruff check y format --check: exit0. Ledger-lint: exit0, 0 incoherencias, 1 aviso sobre UTF-8 leído con reemplazos (preservado en log). Coverage-check: exit0, broken_refs0; aviso T-00 sin cobertura declarada. Lectura de T-00 líneas40-51 confirma Tipo docs y test DOC-00, fuera de UI y de este componente; el checker enumera solo los bloques E2E/API/M del test-plan. No se infiere aprobación documental de T-00.

Cobertura mínima80%: **n/a porcentaje para esta unidad**. La producción modificada es un script shell de tres líneas; ningún módulo Python producto cambia. No se presenta cobertura de tests Python ni un 100% inventado. La conducta del shell sí se ejercita en Linux real con tres pruebas; no equivale a cobertura instrumentada del shell ni a la suite del hito.

qa-gate terminal exit0 (alcance exclusivamente 3 casos Linux):

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 3,
    "failed": 0,
    "flaky": 0,
    "skipped": 0,
    "interrupted": 0
  },
  "flaky_sin_justificar": [],
  "flaky_justificados": {},
  "threshold": "verde ⟺ 0 failed, 0 flaky sin justificar, 0 interrumpidos y ≥1 test ejecutado"
}

```

## Incidencias de evidencia preservadas

orchestrate.py terminó exit1 únicamente por UnicodeEncodeError cp1252 al imprimir el log del ledger ya terminal0. Pruebas Linux/Windows, lint y cleanup estaban completados y guardados. finish.py terminó exit0 reanudando coverage-check/gate/hashes sin repetir pruebas. El recibo inicial container-cleanup.json marcó absent=false por comparación case-sensitive; container-cleanup-confirmed.json corrige desde stderr original lower-case. Ambos se conservan. Ningún incidente convertido en fallo/pase de producto.

## Límites y pendientes

No valida la imagen ACE construida, torch/SDPA, modelos, GPU, montaje ext4/VHDX, readiness integrado, BD, audio ni E2E-01/E2E-09. No reemplaza los manuales M-01 (GPU/escucha), M-02, M-03 ni los gates de aceptación integral. Los estados canónicos quedan a cargo del orquestador. A/B previa informada por el padre no se reatribuye como QA propia.

Todas las salidas/argv/UTC/terminal se conservan por operación en *.receipt.json y *.stdout.log/*.stderr.log. Inventario sellado propio en inventory.json (incluye todos los ficheros de esta carpeta salvo el inventario mismo, excluido explícitamente para evitar autorreferencia).

## Aceptación del componente por el orquestador

Revisión fresca A y B: sin gaps pendientes. QA independiente: PASS_COMPONENT, tres pruebas Linux reales y tres omisiones Windows explícitas. El orquestador comprobó los 56 artefactos del inventario, dos hashes de fuentes, ocho operaciones terminales, JUnit y limpieza del contenedor; recibo `root-verification.json`, 2026-10-10T19:05:28Z. La imagen ACE vigente no se ha reconstruido: esta aceptación corresponde al código del entrypoint, no a un despliegue actualizado ni al cierre de T-05.