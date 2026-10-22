# T11 — QA CPU independiente3

**VERDE limitado a la unidad técnica CPU.** qa-gate exit0 sobre adaptador transparente de JUnit backend:130casos distintos pasan,0failed/0flaky/0skipped/0interrumpidos. No representa E2E, canciones reales, T11 completada ni aceptación de M0/M1/Git. Root puede decidir aceptar este subconjunto técnico según ADR-0037. La revisión3 antecedente A/B/D0Critical0Important1Minor permanece independiente.

## Ejecución y custodia

Fuentes actuales6 congeladas antes de suite y cotejadas después y al cierre (`sources-before.json`, `sources-after-suite.json`, `sources-final.json`). Cuatro tests T11 y dos vecinos copiados byte a byte; `sourceparity-before.json`/`sourceparity-final.json`. El bootstrap sólo cambia ROOT de módulos test y fixtures tmp_path hacia esta carpeta. No modifica aserciones, mocks, plazos ni producto. Python3.12.14gestionado via scripts/env.ps1/uv--no-sync--offline, -B; sin instalaciones, descargas, GPU, Docker, WSL, Ollama, UI, navegador, servicios, subagentes ni knowledge. Sin escrituras ledger/Git/docs/locks/tests canónicos. M1/T03 y T09 concurrentes fuera de congelación T11; no se afirma protección global.

Suite única130=48originales+48fix1+4fix2+30vecinos (selecciones exactas en suite.command.json);26,72s de pytest. No sumar subsets repetidos ni cobertura vieja. Cada comando de verificación tiene argv/startUTC/endUTC/exit y stdout/stderr propios. JUnit suite.xml es la evidencia primaria. Tres warnings de record_property/xunit2: las propiedades se emitieron y se cotejaron; no son skips/fallos.

Cobertura oficial **nueva** de los módulos enteros, datos official.coverage y currentcoverage.json: run.py439/483=90,890269%; metrics.py187/190=98,421053%; cero líneas excluidas en ambos. analysis2 contrasta conteos oficiales; no ramas declaradas ni umbral diluido por promedio (`coverage-verification.json`). Sondas extra fuera de esta cobertura, sin combinar para inflarla.

## Resultados y límites

| Área | Evidencia actual | Resultado / límite |
|---|---|---|
| Quiet2s/cursor/replay UTF8/terminal sin EOF | suite.xml native_proof + nativecleanup.jsonl | Dos quiet reales2s: cursores[0,1], un POSTjobs, ningún DELETE;2,563s hasta registro posterior a cierre del provider. Fragmento UTF8 incompleto descartado al reconectar; splitUTF8 válido preservado por test separado. Terminal devuelve antesEOF. |
| Plazo continuo/chunks/blanks/silencio | Ocho regresiones native_socket sin cambios | Reloj100×:60s lógicos=0,6s reales, no ensayo60s pared. Aserciones de transporte<1,1s o quiet expiry<1,5s pasan; elapsed del hook incluye limpieza/joins y puede ser mayor. |
| Recursos nativos | nativecleanup-summary.json |11casos, sockets observados cerrados, hilos de fase ausentes al salir; provider joined y control vivo antes de cierre propio. Control quiet respondió porHTTP. Cierre del control sólo dentro fixture propietario. Sin matar procesos ajenos. No certificado retrospectivo de CLI históricos. |
| Anonimización | Tests cpu/fix1/guards en suite.xml | Códigos aleatorios sin timestamps/ULID; mapa fuera blind; orden público aleatorizado; grupos por brief incluso vacíos/parciales; resume estable y rechazo de cambios. No ganador ni puntuaciones humanas inventadas. |
| Plan/identidad | Tests actuales y vecinos |30slots, semillas101/202/303, estilo/letra/tags **[...]** literales, hashes preparación/catálogo/descriptor; contrato code-first e identidad de primera petición. |
| ACK y cancelación inciertos | Regresión original + extra-probe.xml/uncertainty-proof.json | Un POSTjobs ante ACKunknown; registros durables SUBMIT_ACK_UNKNOWN y CLEANUP_UNCONFIRMED/retry_submitfalse y nota de error. Nueva sonda es MockTransport, no cancelación de GPU real. |
| Pipeline sintético | test_synthetic_thirty_takes_ninety_metric_jobs_and_blind_sheet |30generaciones mock+90métricas=120IDs distintos; integración unitaria, no30canciones. Audio sintético completo, no calidad ni whole_trackCLAP (CLAPventana10s declarada). |
| FFmpeg nativo | ffmpeg-pretest.json; native-audio/*/measurement.json; native-probe.xml | ZIPSHA y binario contrastados con lock antes suite. Seno3s estéreo48kFLOAT completo: ganancia fija+13,5dB,−16,0LUFS/−14,5dBTP,144000frames y canales inalterados; arrays exactamente proporcionales, cero clipping, sin limitador. Transitorio conflictivo: crudo hash intacto, PEAK_CONFLICT/notblindready y sin salida escalada. No audio musical evaluado. |
| Métricas/suelo | Matriz original de valores nulos/string/bool/NaN/Inf + guards | Fallos aislados, sin ceros inventados; suelo PENDING, autodeclaración no acredita derechos/canto real/ASR, PCM inválido rechazado. Hash íntegro y stagingin/job confinados. |
| Symlink real Windows | native-probe.xml; symlink-fixture/platform-skip.json |1skip por privilegio Windows; no evidencia de symlink runtime en esta plataforma, no sustitución Docker. Guards de rutas no symlink pasan. |
| Catálogo real | dry-run.stdout.txt, full-blocked.* y dryblocked-before-http.json | Dry30slotsexit0; comando completoexit2PREREQUISITES_PENDING; sonda independienteHTTPcalls0. Letras/declaración faltantes, sueloWER,descriptor/preflight real pendientes; no GT/derechos/corpus/tomas nuevos. |
| Lint | ruff-check.*,ruff-format.* | Seis fuentes, ambosexit0, sólo lectura/no-cache; sin autofix. |

Sondas adicionales únicas:4pasan+1skip (2FFmpeg,1symlink,1prerrequisitosHTTP,1ACK/cleanup). No se suman las repeticiones históricas a los130. qa-gate aplicado exclusivamente a suite130 con conteos reales; las sondas separadas tienen JUnit y exits.

## Gate del plugin y plan

```json
{
  "verdict": "VERDE",
  "counts": {
    "passed": 130,
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

ℹ️ Sin UI por diseño (`test-plan: n/a (sin UI)`), marcador real en improvement-plan.md:3. coverage-checkexit0 informativo: NO se ejecutó cobertura criterios↔E2E. `eximidos`:T-00…T-20 (21tareas), `eximidos_exigidos`:false, `rutas_ui`:[], `rutas_ui_degradado`:null, `marcador_no_canonico`:null. Salida literal en plan-coverage.stdout.txt. Ledger-lintexit0:0incoherencias/7avisos de Changelog(T09,T10,T11,T12,T13,T16,T20), sin modificar ledger. No Playwright, capturas ni informe E2E/PDF ficticio.

## Fallos del harness preservados

1. Tras suiteexit0, adaptador de cobertura falló KeyError por separadorWindows. `qa_driver.failed-v1.py` reconstruye el prototipo fallido y `harness-failure.txt` conserva el texto observado; traceback tiene rutas abreviadas, no se presenta como captura byte a byte del CLIroot. JSON nativo/coverage/suite no se reescribieron ni reejecutaron. Adaptador corregido sólo en privado.
2. `finish` esperaba equivocadamente exit1 para coverage-check; realexit0 por marcador sinUI. finish.stderr/command/stdout preservados y `harness-failure2.json` explicita corrección de interpretación. No repetir verificaciones ya terminadas.
3. Búsqueda preliminar rg con wildcardWindows produjo error123; contexto conservado en harness-failure.txt. Sólo lectura. No fallos de producto observados.

## Criterios originales pendientes / handoff root

T11 continúa **abierta**: completar10briefs con letras propias y declaración acreditada, prompt literal comparativo; generar30tomas reales (3/brief), igualarlas y anonimizar; medir antes sueloWER de2–3grabaciones cantadas reales; emitir hoja real de métricas/puntuación; staging de sus tomas reales a data/tmp/<job>/in. La unidad prueba estructuras contra síntesis/mocks, no estos resultados reales. EscuchaD1–D5, naturalidad/cumplimiento, selección humana porbrief y autorización musical permanecen pendientes; ni campos humanos ni vencedor rellenados.

R11-06Minor **pendiente explícito**, verificación FFmpeg repetida porfila; no se ha corregido ni bloquea por sí sola el subconjunto. Sin licencias/modelos nuevos. Paquetes anteriores inventariados1397ficheros intactos (`rootoriginalsunchanged.json`), incluido inventarioCLI prematuro histórico: preservado, nunca avalado; helpers exclusivos originales no ejecutados. Root custodia originalCLI activo/terminal: no sellar cli-original.jsonl/cli-stderr-original.txt mientras vivo. Nuestro inventario cerrado sólo nonCLI.

Modelo/tokens/EUR/horasIA reales **NULL**; peso2estimado. UTC/wallclock no equivale horasIA. Entrega privada; root decide ledger/Git/docs/meter y aceptación técnica, sin cierreT11/M0/M1/Git.
