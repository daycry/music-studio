# Revisión T-10 CPU — intento 1

Lentes A+B frescas terminales. Selector oficialauto C=false/D=false; scopeexit0 sinavisos/info/exclusiones. Diff íntegro103181bytes/SHAb72c13f7e27efff1a7169e77797a1169b6df68d52402df759f3235552f2e63b8. Root cotejó58fuentes porSHA/tamaño intactas. [Recibo](review1-receipt.json).

**0Critical/6Important/0Minor**, todos pendientes de corrección. Timbre A/B deduplicado; instrucción nativa y códigoLM decomplete son causas distintas. El ✓ de mappingcomplete deA no prueba uso efectivo devoz: prevalece la evidencia B1-03. Sin rebates ni deuda aceptada.

| Criterio | Veredicto | Evidencia |
|---|---|---|
| Ocho operaciones/cinco features/dos superficies/522filas | ✓ CPU | Plan completo y tests de matriz; todasverifiedfalse |
| Song/instrumental/perfiles/semillas/batch | ✓ CPU | Mapping y controles presentes; música no evaluada |
| Retake/cover con semántica nativa | ✗ | R10-01 |
| Extend compuesto padding30/repaint60–90 | ✗ | Padding presente; R10-01 |
| Repaint FLOAT/signed-zero/bandas/capturas | ✗ | Comparador CPU conforme, instrucción R10-01; prueba real pendiente |
| Complete acompaña vocals | ✗ | B1-03/R10-06 prevalece sobre el ✓ CPU de mapping A; fuente ignorada por códigos |
| Extract cuatro clases y GT | ✓ CPU | Mapping/comparador presentes; GT y audio reales pendientes |
| Negative_prompt/BPM/key y textos/fronteras LM/DiT | ✗ | Capturas presentes; R10-04 invalida corpus sellado |
| Timbre controles/RNG y petición válida | ✗ | R10-02 |
| LoRA registrado/licenciado/auditado | ✗ | R10-03 |
| Salidas /v1 reales conservadas | ✗ | R10-05 |
| Pendientes/rechazos/doubles/superficies | ✓ CPU | Pruebas de estados; no veredicto musical |
| Hijo/cap libre−512/unload/crudos | ✓ CPU | Lifecycle CPU; GPU real no acreditada |
| Veredictos musicales/bitexact real/descriptorM1 | pendiente | CA sin marcar; tarea en-progreso |
| Alcance/TDD/cobertura | ✓ | Scope0 sinavisos,15RED,media6=85,5084% |
| Verificación de tarea cerrada | no aplica | T10 abierta; no cierre ficticio |
| Interop/OpenAPI/docs-style | no aplica | Diff de código sin esos contratos |

| Gap | Grado | Archivo:línea | Escenario |
|---|---|---|---|
| R10-01 | Important | `scripts/eval/capabilities_native.py:437` | Cuatro mappings nativos conservan el default de GenerationParams en vez de su instrucción específica; AST/templates upstream y repro CPU:4/4 mismatch. |
| R10-02 | Important | `scripts/eval/capabilities_plan.py:138` | data/inputs/reference.wav se transmite intacta y el servidor busca data/data/inputs/reference.wav. Repro A con servidor CPU:422; cambiar sólo a inputs/reference.wav:200, sin iniciar hijo. |
| R10-03 | Important | `scripts/eval/capabilities_native.py:104` | license vacía/commercial_use null, sin models.lock, archivos auto-sellados y marker ajeno a PEFT con approved=true pasan validate_lora y pending=[]. Viola Constitución24 y diseño38/141/188. |
| R10-04 | Important | `scripts/eval/capabilities.py:150` | fixture.update(resources) sustituye style/lyrics/lyrics_declaration tras comprobar fixture==plan.fixture. Root repro CPU exit0 con ambos textos sobrescritos y sello original aceptado. |
| R10-05 | Important | `scripts/eval/capabilities_runtime.py:22` | server común339 emite tmp/<job>/output.wav relativo a data/. copy_outputs interpreta root/tmp y termina failed/output_not_raw_job aunque el job terminó done. |
| R10-06 | Important | `scripts/eval/capabilities_native.py:30` | Complete no está en skip_lm_tasks. thinking=true con LM inicializado genera códigos, y generate_music_request160–161 ignora src_audio con códigos no vacíos. Repro mapping CPU y recorrido estático fijado; no inferencia GPU. |

A ejecutó36tests dirigidos1,66s y repros CPU de instrucciones/LoRA/estimate; B ejecutó6tests dirigidos0,29s y repros de rutas/mapping. Esos tests se solapan y no se suman como42pruebas únicas. Root reprodujo el override del texto con stub explícito CPU. A cotejó15logsRED y cobertura/JUnit del implementador. B no elevó la imposibilidad de reusar un intento pending como gap: la evidencia es inmutable, nueva sesión/fila conserva la anterior.

No huboGPU/Docker/modelos/red/UI/audio/escucha por los revisores. Las pruebas CPU no habilitan capacidades, no prueban ejecución musical ni cierran T10. QA posterior queda pendiente hasta revisión limpia. Jira desactivado; knowledge excluido expresamente por el propietario.
