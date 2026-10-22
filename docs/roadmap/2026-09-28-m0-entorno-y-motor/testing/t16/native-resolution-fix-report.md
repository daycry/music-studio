# T-16 — corrección de resolución DiT, entrega CPU

2026-10-06. Alcance: fase 4 de la causa probada en `native30-diagnosis/report.md` y ADR-0032. Producto y tests congelados; pendiente revisión fresca, QA independiente y prueba GPU del orquestador. T-16/M0 y sus criterios musicales siguen abiertos.

## Resultado

El preflight ejecuta los dos métodos puros originales del resolver fijado, sin importar torch en el padre ni copiar instrucciones. `SOURCE_HASHES` incorpora `generate_music_request.py` con SHA-256 `2761ac8afd0d55877ca1a83913cff35213f334417577baab26df5fbf12204a43`. Planifica y aplica los presupuestos originales a ambas ramas: sin códigos (`text2music`) y con códigos no vacíos (`cover`). Se conserva reserva LM, contexto4096, tier4, duración, controles SFT/Turbo y la prohibición de truncar.

Los recibos nuevos son v2. La fuente canónica de candidatos es `planned.dit.candidates`; `dit.receipt_version` permite que el resumen HTTP existente transporte el formato y las dos alternativas, sin modificar common, Compose o el contrato `/v1`. Los alias `dit.text/lyrics` conservan la rama sin códigos y el validador exige igualdad con ese candidato. No existe copia de candidatos top-level.

La frontera nueva `dit_resolution` acredita `initial_task`, `has_audio_codes` booleano estricto, `resolved_task` e `instruction_sha256`. El adaptador valida la instrucción inicial, la instrucción efectiva (posicional1 o keyword `instructions`) y después conteo/SHA exactos de IDs contra la rama resuelta. No se guarda el contenido de códigos en la frontera. Captions/letras siguen solo en los recibos privados existentes; resumen HTTP/informe no contienen estos textos.

El lector CLI/manifiesto exige los cinco stages, enlace SHA al planned, índice/semilla/request efectivos, instrucción y perfil completo fijados, candidatos válidos y presupuesto también de la rama no usada. Una resolución legítima rehasheada con los tokens de la otra rama se rechaza. El worker actual exige v2; el lector sigue admitiendo v1 con su política histórica, sin fingir una captura de resolución nueva. `scripts/generate.py` no requiere cambios: utiliza el mismo validador antes de CAS/publicación.

## TDD y regresiones

Salidas completas en esta carpeta, sin reinterpretar fallos auxiliares como RED:

- RED: `test_plan_accounts_for_both_native_resolutions` falló v1 frente a v2 en Turbo/SFT, 2026-10-06 (`red-plan.txt`).
- RED: `test_capture_binds_native_resolution_and_instructions` falló por frontera ausente en12casos; `test_instruction_mutation_is_rejected_even_with_identical_token_ids` falló DID NOT RAISE en2casos (`red-capture.txt`).
- RED: `test_native_v2_receipt_resolution_and_publication` falló INPUT_RECEIPT_INVALID con v2 válidas (`red-manifest.txt`).
- RED: `test_resolver_rejects_unknown_initial_instruction` falló DID NOT RAISE (`red-initial-instruction.txt`).
- RED: HTTP real `test_real_http_estimate_transports_both_candidates` falló KeyError receipt_version en el summary (`red-http-summary.txt`). Se deshizo la adición previa del summary antes de este RED; reestructuración posterior hacia candidato canónico único.
- RED: `test_native_v2_resolution_rejects_rehashed_contradictions` para profile/source falló DID NOT RAISE en4casos (`red-profile.txt`).
- RED: `test_worker_success_checks_receipt_and_policy[1]` falló DID NOT RAISE al aceptar formato histórico de un worker actual (`red-current-worker-version.txt`).

Tests cubren string/lista/vacío/whitespace; Turbo/SFT; instrucciones desconocidas/alteradas; presupuesto ambas ramas al borde/+1; fallos de caption/letra/tokens y recibos incompatibles, booleanos, perfil/source, índice/semilla/version/stages/alias. Los dobles de conteo se identifican explícitamente; no se presentan como inferencia o tokenizadores reales.

## Verificación final y límites exactos

Entorno host siempre `. ./scripts/env.ps1`, `uv run --no-sync --all-packages`; sin instalación ni torch host.

1. Verificación CPU declarada: `pytest tests/test_generate_inference.py apps/engines/acestep/tests/test_inference_controls.py -q`: **41 passed in0,55s** (`declared-cpu.txt`).
2. Colección predeterminada del workspace, sinGPU: **326 passed/5warnings**; excluye ACE-Step por testpaths (`workspace-cpu-corrected.txt`). Complemento engine **152 passed/5skipped/1deselected** (`engine-cpu.txt`). No se suman como una suite final única ni se cuentan skips como ejecución.
3. Tras las últimas guardas de perfil/version y formato, delta final fresco: `pytest apps/engines/acestep/tests packages/audio-post/tests tests/test_generate_preparation.py tests/test_generate_inference.py -m 'not gpu' --cov=apps/engines/acestep --cov=packages/audio-post/audio_post --cov-report=json:.../coverage-final.json --cov-report=term -q`: **314 passed/5skipped/1deselected in8,21s**. Medición SIN append: no mezcla posiciones de líneas antiguas (`production-delta-measured-final.txt`).
4. Cobertura oficial pytest-cov, delta difflib contra fuentes de la imagen9e4fc86 y manifest suministrado por root desde HEAD8663287: **64/68=94,12%**, mínimo cambiado por archivo **92,31%**. Adapter27/28; preflight12/13; manifest25/27. Input_profile añade metadata SHA al dict existente, cero líneas ejecutables nuevas, archivo completo100%. Archivos completos: adapter92,90%, preflight90,63%, manifest92,37%. `coverage-summary-final.json` guarda numeradores y líneas no cubiertas. Root puede contrastar su diff Git real; este worker no usó Git.
5. Ruff: **All checks passed!**; formato **8 files already formatted** (`ruff-sealed.txt`, `format-sealed.txt`). Contratos: **engine-v1.json up to date** (`contracts.txt`).
6. Imagen final, namespace/tag exacto **music-studio-acestep:m0-t16-native-resolution**, ID inmutable **sha256:18d94fd4b377016a895e5cd89ee446b64c872421b0d401987f58b0583b16da2d**. Docker run sin --gpus, CUDA_VISIBLE_DEVICES vacío y network none. Suite CPU imagen: **158 passed/1deselected/5warnings in20,80s** (`container-tests-sealed.txt`). Checkpoints/config montados RO; datos del fixture solo en esta caché. Import de la factoría sin torch y seis SHA copiados iguales al host (`image-source-sha.json`).

## Integración CPU nativa

`native-probe.py` usa resolver, batch y conditioning originales +16archivos tokenizer verificados:24combinaciones admitidas/6mutaciones rechazadas; ejecutado en imagen intermedia1a13321 antes de la última guarda de formato del worker. No se atribuye esa ejecución al ID final.

En la imagen FINAL se ejecutaron `integrated-native.py` y `integrated-original.py`: cuatro casos sintéticos y cuatro con los inputs originales RO,30s, Turbo/SFT × con/sin códigos. Orquestación upstream `inference.generate_music`, LM/PT tokenization, batch, resolver y conditioning reales; forwards de inferencia LM y generación musical/DiT sustituidos por dobles CPU explícitos, sin modelos/VRAM/audio. Para el fallback, el doble genera un token normal no musical: el parser nativo produce códigos vacíos; el primer doble que generaba cero tokens fue rechazado legítimamente por LM y se corrigió solo el probe.

Inputs originales acreditan cover150/text2music151, letra256, LM397/33/reserva160. Los registros LM completos coinciden por conteo/SHA con la captura real previa de30s; no se presentan estos IDs/counts DiT CPU como medición de aquel GPU fallido. Los8recibos v2 pasan el lector y la publicación CAS real del CLI en caché;8resoluciones rehasheadas con tokens de rama incompatible se rechazan.13recibos v1 históricos siguen válidos y su fichero conserva SHA. Evidencia: `integrated-*-private.json` privada, `integrated-*-public.json` sin inputs, `validation-receipt.json`.

## Conservación, incidencias y pendiente

Se verifican32archivos del inventario histórico T-17 y27evidencias congeladas del diagnóstico nativo, sin modificación. No se sobrescribe tagcontrol9e4fc86 ni tomas/manifiestos/valoraciones. No se tocaron analysis, common, Compose, locks, pesos, dependencias, docs/knowledge, documentación root, ledger ni Git.

Incidencias preservadas: primera coverage por nombres de módulos provocó import eager NumPy durante colección; se corrigió la invocación a directorios. Primera suite imagen146passed/11fallos fue configurada sin mount models/envruntime; un intento de mount anidado falló125 por faltar tmp. Solo se corrigieron args/mounts privados. Primeros helpers de freeze/validación requirieron sys.path y utf-8 explícitos. Ruff import-order se corrigió antes del freeze; builds intermedios5d32c853/1a13321 y final18d94fd están justificados por fuentes distintas, no por reintentar GPU.

Revisión fresca y QA independiente corresponden a root. La prueba GPU30s, seis tomas90s, escucha y CA3/4 permanecen pendientes; esta entrega no acredita VRAM suficiente ni calidad musical. La verificación de generación completa del brief no se ejecuta bajo este despacho CPU ONLY.

Estado del alcance delegado: **CPU_FIX_READY**, con la validación GPU pendiente del orquestador.
