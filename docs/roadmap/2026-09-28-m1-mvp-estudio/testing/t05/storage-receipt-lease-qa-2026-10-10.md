# QA independiente: ReceiptLease actual — 2026-10-10

**Veredicto técnico del componente: PASS. T-05/M1 siguen sin aceptación global.**

Suite nativa Windows actual: **38/38 PASS, 0 fallos, 0 skips**, pytest exit 0. Cobertura oficial Coverage.py 7.16.2 sobre TODO `storage_receipt_store.py`: **146/149 = 97.98657718 %**, 0 exclusiones; gate `--fail-under=80` exit 0. Ruff y format-check exit 0. No es cobertura de ramas; faltan líneas 87, 140 y 177.

Evidencias: [JUnit](../../../../../.cache/dev-cycle/m1/storage-receipt-lease-20261010/qa/junit.xml), [terminal pytest](../../../../../.cache/dev-cycle/m1/storage-receipt-lease-20261010/qa/pytest.stdout.txt), [cobertura oficial](../../../../../.cache/dev-cycle/m1/storage-receipt-lease-20261010/qa/coverage.json), [gate cobertura](../../../../../.cache/dev-cycle/m1/storage-receipt-lease-20261010/qa/coverage-report.stdout.txt), [Ruff](../../../../../.cache/dev-cycle/m1/storage-receipt-lease-20261010/qa/ruff.stdout.txt), [formato](../../../../../.cache/dev-cycle/m1/storage-receipt-lease-20261010/qa/format.stdout.txt), [comandos y UTC](../../../../../.cache/dev-cycle/m1/storage-receipt-lease-20261010/qa/commands.json).

## Alcance probado

Lectura de recibo existente por el mismo HANDLE, snapshot e identidad, exclusión nativa de escritura/truncado/replacement/rename/delete y ancestros; escritor preexistente; lector permitido; recibo obsoleto, inválido o de otro proyecto; adquisición parcial; errores primarios y cleanup incierto. SEEK/READ concurrentes entregan ambos snapshots exactos; close espera lectura nativa y rechaza nuevas lecturas; el context manager permite lectura desde otro hilo.

El ensayo B03 actual acredita `CloseHandle SUCCESS` seguido de interrupción: contador del handle incierto **1 antes / 1 después**, ocho testigos ajenos nativos preservados por identidad y payload. `reuse_observed=False`: no se exige reutilización del allocator y no se afirma haberla observado. El RED/GREEN original que dependía de reutilización queda como historial de review2; no se reutiliza como QA actual.

La suite comprueba restauración del contador tras destruir la lease. Además, [probe independiente actual](../../../../../.cache/dev-cycle/m1/storage-receipt-lease-20261010/qa/probe.stdout.txt) ejecuta 25 ciclos con lectura nativa: handles antes **136**, durante **149**, después de destrucción **136**. Preserva bytes y verifica import paths/SHA de cinco módulos más SHA del sexto input (test). El +1 observado en el ensayo de incertidumbre de la suite ocurre con la lease/RLock aún vivos; el probe después de destrucción restaura el contador. No confundir esa fase con una fuga probada.

## Fuentes y custodia

Snapshot propio de seis fuentes fijadas al CAS root de 21:40:11 UTC, byte exacto; imports privados explícitos, sin writes a fuentes canónicas. [Sello previo](../../../../../.cache/dev-cycle/m1/storage-receipt-lease-20261010/qa/source-pre.json), [sello posterior](../../../../../.cache/dev-cycle/m1/storage-receipt-lease-20261010/qa/source-post.json), [sello final](../../../../../.cache/dev-cycle/m1/storage-receipt-lease-20261010/qa/source-final.json): **SOURCE_SEAL_FINISHED=true**, hashes y tamaños invariantes en canónico y snapshot. [Inventario final](../../../../../.cache/dev-cycle/m1/storage-receipt-lease-20261010/qa/inventory.json) detalla archivos regulares/special, bytes y SHA-256. No modifica ledger, checkpoint ni Git; conserva los lotes históricos 215/119/78 y reviewcopies.

## Límites y puertas

QA técnica nativa local sin UI en este componente: Playwright/qa-gate no aplican; no se fabrica `results.json` ni veredicto E2E. El test-plan global M1 sigue vigente. [Ledger-lint](../../../../../.cache/dev-cycle/m1/storage-receipt-lease-20261010/qa/ledger-lint.stdout.txt) y [coverage-check](../../../../../.cache/dev-cycle/m1/storage-receipt-lease-20261010/qa/coverage-check.stdout.txt) se conservan como puertas documentales, no como sustitutos de la evidencia de aceptación M1.

No prueba creación/adopción, CAS durable de recibos, lifecycle, validated, detach, attach real, WSL/ext4, persistencia ni recuperación. No GPU, servicios ajenos, elevación, datos canónicos o modelo ACE. Producto Docker permanece sin cambios; Windows nativo se usa para esta frontera de custodia.

PDF omitido: dependencias gestionadas de to-pdf ausentes según mandato de esta QA; no se instala ni se usa caché externa (ADR-0005). Capturas UI no aplican. No handoff a documenter ni cierre del hito. Métricas del lote root estimadas, tokens/coste null; sin marcadores nuevos propios.

Avisos documentales reales: ledger-lint **0 incoherencias y 1 aviso de UTF-8 no limpio**; coverage-check **exit 0, 0 referencias rotas, T-00 sin cobertura declarada**. Si T-00 incluye UI, ese criterio huérfano impide verde global; este informe no adjudica su alcance ni lo elimina.

## Verificaciones pendientes para aceptación global

- [ ] Montaje/persistencia real ext4/VHDX, Range, recovery y backup de T-05.
- [ ] Lifecycle completo y CAS durable de recibos.
- [ ] Escucha humana M-01 y manuales M-02/M-03 del plan.
- [ ] Aceptación root del sello, informe e inventario del componente.
