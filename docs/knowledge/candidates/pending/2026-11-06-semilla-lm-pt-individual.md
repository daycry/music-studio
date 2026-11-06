---
category: GOTCHA
evidencia: validated_case
fuentes:
  - apps/engines/acestep/adapter.py
  - apps/engines/acestep/tests/test_lm_seed.py
  - .cache/dev-cycle/20261106-m0-t16/gpu-pairs/qa/summary.json
  - .cache/dev-cycle/20261106-m0-t16/gpu-pairs/diagnosis-seeding/report.md
  - .cache/dev-cycle/20261106-m0-t16/gpu-pairs/diagnosis-seeding/probe-result.json
  - .cache/dev-cycle/20261106-m0-t16/gpu-pairs/diagnosis-seeding/pinned-source/source.json
  - .cache/dev-cycle/20261106-m0-t16/gpu-pairs/seed-fix/evidence.md
tags:
  - "area:generacion-musical"
  - "componente:acestep"
  - "tema:semilla-lm"
  - "backend:pt"
---

# La ruta PT individual puede recibir semillas sin aplicarlas al muestreo LM

Propuesta pendiente de curación por `knowledge-curator`. `GOTCHA` y
`validated_case` son propuestas de clasificación. La evidencia causal es
CPU/AST/mock; no constituye aprobación ni autorización de exportación.

## Síntoma

La QA GPU conservó seis audios válidos y ninguna de tres parejas certificadas.
Las huellas de códigos LM diferían en las tres parejas, con códigos no vacíos.
Coincidían semillas transportadas, argumentos y prompts LM, metadata y tokens
observados; los pasos y CFG eran las diferencias DiT previstas.
Estos resultados negativos permanecen intactos.

## Causa probada en el control

La fuente exportada de la imagen
`sha256:761384424101a4b7c24994d124bed352594c230f6a50bec59327a3ef6916de56`
descarta `seeds` en la ruta single antes de `_run_pt_single`.
`_sample_tokens` usa `torch.multinomial` sin generador explícito.
La ruta lista de `_run_pt` sí reinicia el RNG por semilla.

El probe extrae funciones por AST y usa logits y Torch simulados.
Demuestra que la ruta individual depende del RNG previo y que la ruta lista
aplica la semilla. No reproduce la numérica del modelo ni demuestra la causa
única de las diferencias GPU. `probe-result.json` contrasta la exportación
con el perfil y la imagen de QA. SHA-256 de `llm_inference.py`:
`afe1baf01d8a594bd06148bf9c79a0f66f84072b5158ae598340b34cc215b9c6`.
SHA-256 de `inference.py`:
`2395a1e6340af075d3f9d2fad293a389beb61f0a11e1db79a5ad120f6d0ce9a2`.

## Qué hacer

[`lm_seed`](../../../../apps/engines/acestep/adapter.py) envuelve temporalmente
`_run_pt_single` por variante y llama a `runtime.torch.manual_seed` antes del
muestreo, una vez por secuencia. Restituye el método en `finally`.
Usa la semilla efectiva existente, incluida `seed+i`, independientemente de
`input_capture`. Conserva entradas LM, controles DiT y contrato público.
Al cambiar el runtime fijado, revisar esta frontera interna y sus pruebas.

## Evidencia de regresión y límites

[`test_lm_seed.py`](../../../../apps/engines/acestep/tests/test_lm_seed.py)
integra `AceStepAdapter.generate` con runtime y Torch falsos.
`test_same_effective_seed_ignores_prior_rng_and_checkpoint` y
`test_variants_use_effective_seed_without_changing_lm_inputs[0]`
fallaron antes del fix por dependencia del RNG y trayectoria incorrecta.
Las ocho regresiones pasan después; incluyen semillas exactas, variantes,
entradas conservadas y restauración ante error o cancelación.

`seed-fix/evidence.md` conserva RED/GREEN, 180 aprobados y uno omitido en la
selección ampliada, y 41 aprobados en la verificación declarada.
La cobertura del delta es 15/15 sentencias; la del fichero completo es 67,77 %.
Estas pruebas no certifican igualdad bit a bit CUDA/BF16, códigos reales
iguales tras el fix, aceptación musical ni cierre de T-16, M0 o M1.
