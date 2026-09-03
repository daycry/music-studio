# Tests del runner (Fase 0)

Suite pytest del runner. Corre **sin GPU** (todo en CPU), pero **no corre entera sin torch**:
la revisión del 2026-09-03 destapó que el README anterior decía «sin torch» mientras el
68 % de los tests (423 de 624 en aquel momento, contados con `--collect-only`) dependían de
`torch`, `numpy` y `scipy` vía `importorskip`, y un `-q` sin `-rs` lo escondía. Ahora `conftest.py` aborta la sesión si faltan esas dependencias, salvo
que se pida `--permitir-saltos` a propósito.

## Ejecución

Desde la raíz del repo:

```
python -m pytest apps/runner/tests -q -rs
```

- `-rs` muestra los saltos con su motivo. Úsalo siempre: un recuento en verde con medio suite
  saltado no es un recuento en verde.
- Sin torch/numpy/scipy: `python -m pytest apps/runner/tests -q -rs --permitir-saltos` corre
  solo la parte de biblioteca estándar (contratos, D-14, D-17, `_timing`, hashes del vendor).
- Dependencias: `pip install pytest numpy scipy torch` (la rueda de torch para CPU basta;
  ninguna prueba toca CUDA). Versiones de referencia en la máquina del propietario: torch
  2.13.0+cpu, numpy 2.5.2, scipy 1.18.1.

## Qué cubre cada fichero

| Fichero | Necesita | Qué prueba |
|---|---|---|
| `test_contracts.py` | stdlib | Puerta anti-RCE de D-14 (`assert_safetensors`), presupuesto D-17, validación de peticiones |
| `test_adapter.py` | stdlib | Camino mock del adapter, `_slug`, contrato M-3 de `gpu_seconds`, **integridad de pesos** (provenance hermano, variable, salto explícito) |
| `test_timing.py` | stdlib | Estadísticas e informes atómicos de `_timing.py` |
| `test_vram_profile.py` | stdlib | Protección C1 contra degradación silenciosa al mock (se salta si hay CUDA) |
| `test_gpu_tiers.py` | stdlib | Tabla de niveles por VRAM |
| `test_vram_floor.py` | stdlib | Suelo de 8 GB con tolerancia de 64 MB (CS-51) |
| `test_g1_generar.py` | stdlib | Kit de G1: briefs del protocolo real, cegado, mapa sellado, `--sin-lm` ausente |
| `test_vendor_hashes.py` | stdlib | Cada fichero de `adapters/*/vendor/**` coincide con la fila de su README y ninguno se ejecuta sin fila. Descubre los adapters, no los lleva escritos |
| `test_model_cards.py` | stdlib | Inventario de fichas `.model.json`: la ficha es evidencia y nunca autoridad, lista blanca de variables de entorno, estados y encaje de VRAM |
| `test_esquema_artefacto.py` | torch | Puerta de `artifact_schema_version`: versión mayor aborta, ausente avisa y sigue, y los artefactos en disco declaran la soportada |
| `test_matriz_ab.py` | stdlib | La matriz 2×2 del A/B está cruzada de verdad y cada par comparte semilla |
| `test_limitador.py` | torch, numpy | Limitador de picos: señal intacta lejos del transitorio, sin fundido, ganancia común a los canales, sin saltos de ganancia, coste lineal, punto de llamada `_a_pcm16` |
| `test_carga_contigua.py` | torch, safetensors | Lectura contigua contra `load_file`, cabeceras, respaldo solo ante `ArtefactoIlegible`, guardarraíl de subida, SHA-256 de paso en la carga |
| `test_shim_planificador.py` | torch | Perilla `usar_lm` en sus seis casos, aritmética 25 Hz/5 Hz, `render()` no reentrante y `release()` que espera al render |
| `test_residual_fp32.py` | torch | Promoción fp32 del residual: reproduce el desbordamiento y la cura |
| `test_diffusion_guia.py` | torch | Guía APG contra el bucle de upstream, drift documentado |
| `test_scheduler_variantes.py` | torch | Planificador de pasos por variante (`turbo`/`sft`) |
| `test_medir_ab.py` | numpy, scipy | Descriptores contra valores teóricos; contrastes 2×2 con `efecto_relativo_pct` |
| `test_pulso.py` | numpy, scipy | Métrica de ritmo contra señales de tempo conocido, **y sus limitaciones escritas** (transitorio ancho, ruido de fondo) |

Recuento a 2026-09-03: 695 tests, unos 19 s en CPU.

## Fuera de la suite: qué hay instalado

`python apps/runner/model_cards.py <directorio-de-pesos> --vram-mb N` lista los modelos
instalados y su estado. No es un test, pero responde a la pregunta que ningún test responde:
cuál de los `.safetensors` que hay en disco es el de producción. Turbo y sft traen las mismas
claves con las mismas formas, así que el artefacto no lo dice; la ficha `.model.json` sí. Unos 200 son una sola propiedad parametrizada sobre
`range(1, 200)` en `test_shim_planificador.py`; el número de comportamientos distintos es
bastante menor que el de tests recogidos.
