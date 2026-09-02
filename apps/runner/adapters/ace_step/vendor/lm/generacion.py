# ---------------------------------------------------------------------------
# NOTA DE MODIFICACION
# ---------------------------------------------------------------------------
# ESTE FICHERO HA SIDO MODIFICADO respecto del original.
#
# Obra derivada de `acestep/llm_inference.py` (metodos `_apply_top_k_filter`,
# `_apply_top_p_filter`, `_sample_tokens`, `_check_eos_token`, `_forward_pass`,
# `_compute_max_new_tokens`, `_generate_with_constrained_decoding` y
# `_generate_with_cfg_custom` de la clase `LLMHandler`).
#
#   Origen          : github.com/ace-step/ACE-Step-1.5, ruta `acestep/llm_inference.py`
#   Revision fijada : ca1e85fe9430179831e6bc6be790c332190a3866  (2026-08-29)
#   Bytes origen    : 192383
#   SHA-256 origen  : afe1baf01d8a594bd06148bf9c79a0f66f84072b5158ae598340b34cc215b9c6
#   blob SHA-1      : 3690af56d8fe5c6a51844917e8e56c54fc088953
#   Copiado el      : 2026-09-02
#   Licencia        : MIT (LICENSE de la raiz del repositorio, blob SHA-1
#                     600451d484a555c1273baa2602f32a37fdd0d0ab)
#
# Cada cambio va marcado con "MODIFICADO respecto a upstream".
# ---------------------------------------------------------------------------
"""Bucle de generacion del planificador de 5 Hz.

Por que hay bucle propio y no `model.generate()`
------------------------------------------------
Porque la decodificacion restringida necesita que **despues** de muestrear cada
token alguien llame a `procesador.actualizar_estado(token)`. `generate()` aplica
los `LogitsProcessor` pero no ofrece ese enganche de vuelta, asi que el automata
se quedaria congelado en el primer estado y el contador de codigos a cero: el
EOS no se forzaria nunca y la duracion volveria a ser libre. Upstream llega a la
misma conclusion y escribe su propio bucle; esto es ese bucle.

Dos bucles, no uno
------------------
- `generar` — sin CFG, lote 1. Una pasada por paso.
- `generar_con_cfg` — con CFG, lote 2 (condicional + incondicional con relleno a
  la izquierda). Dos pasadas por paso. La mezcla se hace **solo sobre los tokens
  permitidos** cuando el automata esta emitiendo codigos: si se mezclase sobre
  el vocabulario entero, los 153.204 tokens de texto (ya a -inf en las dos
  ramas) producirian `-inf - -inf = NaN`, y ademas se estaria gastando computo
  en 153.204 columnas que van a acabar descartadas.

El defecto de upstream para el LM es `cfg_scale = 2.0` (`GenerationParams` de
`acestep/inference.py`), es decir: **la ruta normal es la de CFG**.

Que se ha quitado
-----------------
- Las barras de `tqdm`. En su lugar hay un callback `on_token(paso, total)`, que
  es el mismo patron que ya usa `vendor/pipeline/diffusion.py` con `on_step` y
  el punto donde el adapter puede aplicar su tope de segundos (D-17): una
  excepcion levantada desde el callback aborta el bucle y se propaga.
- Los `streamer`. No hay consumidor.
- Los caminos vLLM / nano-vllm / MLX. Ni estan en la imagen ni tienen sentido en
  una GTX 1070.
"""

from __future__ import annotations

from typing import Any, Callable, List, Optional

import torch

from .constants import (
    DURATION_MAX,
    DURATION_MIN,
    MARGEN_TOKENS_CODIGOS,
    MARGEN_TOKENS_COT,
    codigos_para_duracion,
)

__all__ = [
    "calcular_max_tokens_nuevos",
    "filtrar_top_k",
    "filtrar_top_p",
    "generar",
    "generar_con_cfg",
    "muestrear",
]

#: Firma del callback de progreso: `(paso, total)`, 1-indexado.
CallbackToken = Callable[[int, int], None]


# --------------------------------------------------------------------------- #
# Filtros y muestreo
# --------------------------------------------------------------------------- #

def filtrar_top_k(logits: torch.Tensor, top_k: Optional[int]) -> torch.Tensor:
    """Deja solo los `top_k` logits mas altos. `None` o 0 = sin filtro."""
    if top_k is not None and top_k > 0:
        fuera = logits < torch.topk(logits, top_k)[0][..., -1, None]
        logits[fuera] = float("-inf")
    return logits


def filtrar_top_p(logits: torch.Tensor, top_p: Optional[float]) -> torch.Tensor:
    """Nucleo de probabilidad acumulada `top_p`. `None` o >=1,0 = sin filtro."""
    if top_p is not None and 0.0 < top_p < 1.0:
        ordenados, indices = torch.sort(logits, descending=True)
        # El `.float()` es de upstream y no es decorativo: en float16 el
        # `softmax`+`cumsum` de un vocabulario de 217.204 columnas pierde el
        # nucleo entero.
        acumulada = torch.cumsum(torch.softmax(ordenados.float(), dim=-1), dim=-1)
        quitar_ordenados = acumulada > top_p
        quitar_ordenados[..., 1:] = quitar_ordenados[..., :-1].clone()
        quitar_ordenados[..., 0] = 0
        quitar = quitar_ordenados.scatter(1, indices, quitar_ordenados)
        logits[quitar] = float("-inf")
    return logits


def muestrear(logits: torch.Tensor, temperatura: float) -> torch.Tensor:
    """Muestrea un token por fila. Temperatura 0 = `argmax` (determinista)."""
    if temperatura > 0:
        probabilidades = torch.softmax(logits.float() / temperatura, dim=-1)
        return torch.multinomial(probabilidades, num_samples=1).squeeze(1)
    return torch.argmax(logits, dim=-1)


def calcular_max_tokens_nuevos(
    duracion_objetivo: Optional[float],
    fase: str,
    tope_modelo: int = 4096,
    duracion_maxima: int = DURATION_MAX,
) -> int:
    """Cuantos tokens como mucho puede emitir el LM en esta fase.

    En la fase de codigos basta con `objetivo + 10`: la decodificacion
    restringida fuerza el EOS exactamente en el codigo objetivo, asi que el
    margen solo existe para que el contador no mienta. En la fase de
    razonamiento el margen es de 500 tokens para los metadatos.
    """
    if duracion_objetivo is not None and duracion_objetivo > 0:
        tope = max(DURATION_MIN, min(min(duracion_maxima, DURATION_MAX), duracion_objetivo))
        objetivo = codigos_para_duracion(tope)
        if fase == "codes":
            maximo = objetivo + MARGEN_TOKENS_CODIGOS
        else:
            maximo = objetivo + MARGEN_TOKENS_COT
    else:
        maximo = min(tope_modelo - 64, DURATION_MAX * 5 + MARGEN_TOKENS_COT)
    return max(1, min(maximo, tope_modelo - 64))


# --------------------------------------------------------------------------- #
# Internos
# --------------------------------------------------------------------------- #

def _penalizador(repeticion: float):
    """Penalizacion de repeticion de `transformers`, solo si se pide.

    Se importa dentro de la funcion a proposito: con el valor por defecto (1,0)
    no se toca `transformers.generation`, que es la parte de la API que mas se
    mueve entre versiones mayores.
    """
    if repeticion == 1.0:
        return None
    from transformers.generation.logits_process import RepetitionPenaltyLogitsProcessor

    return RepetitionPenaltyLogitsProcessor(penalty=repeticion)


def _pasada(model, secuencia: torch.Tensor, mascara: torch.Tensor, cache, usar_cache: bool):
    """Una pasada hacia delante, con o sin cache de claves/valores."""
    if cache is None:
        return model(input_ids=secuencia, attention_mask=mascara, use_cache=usar_cache)
    return model(
        input_ids=secuencia[:, -1:],
        attention_mask=mascara,
        past_key_values=cache,
        use_cache=usar_cache,
    )


def _es_final(tokens: torch.Tensor, eos: int, pad: Optional[int]) -> bool:
    if bool(torch.any(tokens == eos)):
        return True
    if pad is not None and pad != eos and bool(torch.any(tokens == pad)):
        return True
    return False


def _usar_cache(model) -> bool:
    configuracion = getattr(model, "generation_config", None)
    return bool(getattr(configuracion, "use_cache", True)) if configuracion is not None else True


# --------------------------------------------------------------------------- #
# Bucles
# --------------------------------------------------------------------------- #

def generar(
    model,
    input_ids: torch.Tensor,
    attention_mask: Optional[torch.Tensor],
    max_tokens_nuevos: int,
    temperatura: float,
    eos_token_id: int,
    pad_token_id: Optional[int] = None,
    top_k: Optional[int] = None,
    top_p: Optional[float] = None,
    repeticion: float = 1.0,
    procesador: Optional[Any] = None,
    on_token: Optional[CallbackToken] = None,
) -> List[int]:
    """Bucle sin CFG. Devuelve **solo** los tokens nuevos, en orden.

    `procesador` es un :class:`ProcesadorRestringido` ya reiniciado y
    configurado. Puede ser `None`, pero entonces no hay contrato de duracion ni
    lista blanca de vocabulario: eso NO es una configuracion valida para
    producir audio, solo para experimentar.
    """
    dispositivo = input_ids.device
    secuencia = input_ids.clone()
    mascara = attention_mask.clone() if attention_mask is not None else torch.ones_like(input_ids)
    largo_prompt = secuencia.shape[1]

    cache = None
    usar_cache = _usar_cache(model)
    penalizador = _penalizador(repeticion)

    with torch.inference_mode():
        for paso in range(max_tokens_nuevos):
            salida = _pasada(model, secuencia, mascara, cache, usar_cache)
            logits = salida.logits[:, -1, :]

            if procesador is not None:
                logits = procesador(secuencia, logits)
            if penalizador is not None:
                logits = penalizador(secuencia, logits)

            logits = filtrar_top_k(logits, top_k)
            logits = filtrar_top_p(logits, top_p)
            tokens = muestrear(logits, temperatura)

            if procesador is not None:
                for b in range(tokens.shape[0]):
                    procesador.actualizar_estado(int(tokens[b].item()))

            parar = _es_final(tokens, eos_token_id, pad_token_id)

            secuencia = torch.cat([secuencia, tokens.unsqueeze(1)], dim=1)
            mascara = torch.cat(
                [mascara, torch.ones((secuencia.shape[0], 1), device=dispositivo, dtype=mascara.dtype)],
                dim=1,
            )
            if usar_cache:
                cache = getattr(salida, "past_key_values", None)

            # MODIFICADO respecto a upstream: punto de control. Upstream pinta
            # una barra de `tqdm` aqui; una excepcion levantada desde este
            # callback aborta el bucle y se propaga, que es como el adapter
            # aplica su tope de segundos.
            if on_token is not None:
                on_token(paso + 1, max_tokens_nuevos)

            if parar:
                break

    del cache
    return secuencia[0, largo_prompt:].tolist()


def generar_con_cfg(
    model,
    input_ids: torch.Tensor,
    attention_mask: Optional[torch.Tensor],
    max_tokens_nuevos: int,
    temperatura: float,
    escala_cfg: float,
    eos_token_id: int,
    pad_token_id: Optional[int] = None,
    top_k: Optional[int] = None,
    top_p: Optional[float] = None,
    repeticion: float = 1.0,
    procesador: Optional[Any] = None,
    on_token: Optional[CallbackToken] = None,
) -> List[int]:
    """Bucle con CFG. `input_ids` es `[2, L]`: fila 0 condicional, fila 1 no.

    Las dos filas tienen que venir con **relleno a la izquierda** y la misma
    longitud (el llamante las tokeniza juntas con `padding_side="left"`).
    Devuelve solo los tokens nuevos de la rama condicional.
    """
    from .decodificacion_restringida import EstadoFSM

    if input_ids.shape[0] != 2:
        raise ValueError(f"generar_con_cfg espera un lote de 2 filas, no {input_ids.shape[0]}.")

    dispositivo = input_ids.device
    secuencia = input_ids.clone()
    mascara = attention_mask.clone() if attention_mask is not None else torch.ones_like(input_ids)
    largo_prompt = secuencia.shape[1]

    cache = None
    usar_cache = _usar_cache(model)
    penalizador = _penalizador(repeticion)
    terminado = False

    with torch.inference_mode():
        for paso in range(max_tokens_nuevos):
            salida = _pasada(model, secuencia, mascara, cache, usar_cache)
            logits = salida.logits[:, -1, :]
            cond = logits[0:1]
            uncond = logits[1:2]

            en_codigos = (
                procesador is not None
                and procesador.estado == EstadoFSM.CODES_GENERATION
                and procesador.mascara_solo_codigos is not None
            )
            if en_codigos:
                # Mezcla restringida a las columnas permitidas: evita el NaN de
                # `-inf - -inf` y no gasta computo en el texto.
                bruta = procesador.mascara_solo_codigos
                if bruta.device != dispositivo or bruta.dtype != torch.float32:
                    bruta = bruta.to(device=dispositivo, dtype=torch.float32)
                validos = (bruta[0] == 0).nonzero(as_tuple=False).squeeze(1)
                mezcla_validos = uncond[:, validos].float() + escala_cfg * (
                    cond[:, validos].float() - uncond[:, validos].float()
                )
                mezcla = torch.full(
                    (1, cond.shape[1]), float("-inf"), device=dispositivo, dtype=torch.float32
                )
                mezcla[:, validos] = mezcla_validos
            else:
                mezcla = uncond.float() + escala_cfg * (cond.float() - uncond.float())
                # `-inf + escala * (-inf - -inf)` da NaN; se convierte en -inf
                # para que esos tokens queden simplemente fuera del muestreo.
                mezcla = torch.nan_to_num(mezcla, nan=float("-inf"))

            entrada_cond = secuencia[0:1]
            if procesador is not None:
                mezcla = procesador(entrada_cond, mezcla)
            if penalizador is not None:
                mezcla = penalizador(entrada_cond, mezcla)

            mezcla = filtrar_top_k(mezcla, top_k)
            mezcla = filtrar_top_p(mezcla, top_p)

            if terminado:
                mezcla[0, :] = float("-inf")
                mezcla[0, eos_token_id] = 0.0

            tokens = muestrear(mezcla, temperatura)

            if procesador is not None:
                procesador.actualizar_estado(int(tokens[0].item()))

            terminado = terminado or _es_final(tokens, eos_token_id, pad_token_id)

            # El mismo token se anade a las dos ramas: la incondicional tiene
            # que ver el mismo historial para que la diferencia de logits mida
            # solo la condicion.
            secuencia = torch.cat([secuencia, tokens.unsqueeze(1).repeat(2, 1)], dim=1)
            mascara = torch.cat(
                [mascara, torch.ones((2, 1), device=dispositivo, dtype=mascara.dtype)], dim=1
            )
            if usar_cache:
                cache = getattr(salida, "past_key_values", None)

            if on_token is not None:
                on_token(paso + 1, max_tokens_nuevos)

            if terminado:
                break

    del cache
    return secuencia[0, largo_prompt:].tolist()
