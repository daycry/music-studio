# Corrección CPU R09-O4b/B3-01 — T-09

Estado DONE_CPU_WITH_CONCERNS. Delta acotado a benchmark_observation.py y su test; root conserva ledger/docs/Git/usage. El contador de revisión sigue3 y requiere revisión excepcional explícita, no reseteo ni deuda.

RED: scripts/eval/tests/test_benchmark_observation.py::test_pilot_acquisition_respects_external_now[True-True-wsl] falló con DID NOT RAISE ValueError · 2026-10-07T00:04:55.472804+00:00
RED: scripts/eval/tests/test_benchmark_observation.py::test_continuity_starts_after_complete_pilot_acquisition falló con DID NOT RAISE ValueError · 2026-10-07T00:05:08.001999+00:00

Reproducción CPU propia con originales previos/actuales sellados. Windows último sigue131.02→131.03; WSL131.04→132.24/browser132.25→132.26 frente now externo132.1. validate_samples rechazaba pero validate_auto aceptaba provider_verified con continuidad. La guarda nueva exige acquisition_end de CADA muestra original≤reference_now externo ANTES de derivar ventana histórica; no sustituye reloj externo ni vuelve a Windows+1ms. Sin continuidad también rechaza. Con now posterior y continuidad posterior válidas, acepta. Los8 casos nuevos cubren WSL/browser, con/sin continuidad y futuros/completados.

Segundo RED prueba continuidad iniciada132 antes de terminar browser132.26 con now133. El inicio se contrasta ahora con final completo del piloto, manteniendo900s intactos. Es continuidad de adquisición, consistente con clocks directos/no usar timestamp general como simultaneidad del diseño ADR0036; no introduce política nueva. La segmentación y el contraste dedicado Windows permanecen; la recursión histórica conserva el máximo exacto de cuatro consultas. O1/O2/O3/O5/O4a preservados.

GREEN dirigido19pass (nuevos9+O4a10, solapados con suite). ÚNICA suite pertinente final:104passed in10.44s sobre cuatro archivos observación/CLI/integraciónCPU/observers. No rerun ni suma de95/138/144 históricos. Cobertura OFICIAL del único módulo completo de producción cambiado:261/304=85.85526316%; gate80exit0. Ruff All checks passed! Formato2files already formatted; ambosexit0. Logs/JUnit/JSON oficial y argv/UTC/exits originales guardados por comando.

Custodia64preimágenes exactas,62fuentes ajenas y12docs protegidos intactos. Fuentes after/diff aislado; manifiestos previos verificadosRO83/84/37, recibos y rootacceptance preservados. No GPU/Docker/WSL/UI/red/install/models/knowledge/memory, Git ni usage. scripts/env.ps1 cargado; uv frozen/no-sync/all-packages, plugin CPU copiadofix2, noconftest y caches/tmp/coverage/Ruff privados. No tocar conftest raíz ni escribir coverage raíz.

Incidentes originales:
- RED overlap produjo dos PytestCacheWarning WinError5 en cache privada, no impidió la reproducción conductual; log/JUnit original conservado.
- Primer GREEN:17pass/2fail por auto_collection_timestamp_invalid de FILETIME redondeado en fixture positiva sample132.3; corregido sólo test a live133/now134. No se cuenta como RED. Log/JUnit/argv/exits originales conservados.
- La inspección RO intentó artifact-manifest.json inexistente en fix2/implementation; se usó artifact-seals.json real. Sin escrituras ni repetición de helpers históricos.
- Incidente de preparación del orquestador ya registrado en preparation-incident.json; no se reconstruye ni altera.

Pendientes revisión excepcional, QA independiente, piloto real y matriz160/verificación canónica. T09 abierta; CPU no certifica GPU, spill cero ni RTF.

DONE_CPU_WITH_CONCERNS


Root verificó41sellos/64fuentes/64preimágenes/62ajenas/12docs/.coverage y los tres manifiestos previos. [Recibo](autonomous-observability-fix3-receipt.json).
