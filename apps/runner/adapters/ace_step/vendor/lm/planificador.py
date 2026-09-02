# ---------------------------------------------------------------------------
# NOTA DE MODIFICACION
# ---------------------------------------------------------------------------
# ESTE FICHERO HA SIDO MODIFICADO respecto del original.
#
# Obra derivada de dos ficheros de github.com/ace-step/ACE-Step-1.5,
# revision fijada ca1e85fe9430179831e6bc6be790c332190a3866 (2026-08-29):
#
#   1) `acestep/llm_inference.py`  (192.383 bytes)
#      SHA-256 afe1baf01d8a594bd06148bf9c79a0f66f84072b5158ae598340b34cc215b9c6
#      blob SHA-1 3690af56d8fe5c6a51844917e8e56c54fc088953
#      -> `LLMHandler.generate_with_stop_condition` (orquestacion en dos fases),
#         `has_all_metas`, `_setup_constrained_processor`, `_run_pt_single`.
#
#   2) `acestep/core/generation/handler/audio_codes.py`  (4.456 bytes)
#      SHA-256 7dec268778c6c6d493aafc8253ae1374bff43459bbd62fb3c16fcd47fefb747a
#      blob SHA-1 31d6835c9b79104a8ebae0425d9b9055f75c37b1
#      -> `AudioCodesMixin._parse_audio_code_string`,
#         `AudioCodesMixin._decode_audio_codes_to_latents`.
#
#   Copiado el : 2026-09-02
#   Licencia   : MIT (LICENSE de la raiz del repositorio, blob SHA-1
#                600451d484a555c1273baa2602f32a37fdd0d0ab)
#
# Cada cambio va marcado con "MODIFICADO respecto a upstream". Lo que no procede
# de upstream va marcado con "ANADIDO (no procede de upstream)".
# ---------------------------------------------------------------------------
"""El planificador de 5 Hz: de (estilo, letra, duracion) a codigos de audio.

Las dos fases
-------------
1. **Razonamiento.** El LM escribe un bloque `<think>` con bpm, caption,
   duracion, tonalidad, idioma y compas, y para ahi. Si el llamante ya conoce
   esos valores, se inyectan token a token en vez de generarse; y si conoce los
   cuatro que upstream considera suficientes (bpm, tonalidad, compas y
   duracion), la fase 1 **no se ejecuta**.
2. **Codigos.** El razonamiento se reserializa en YAML, se mete en el prompt con
   el turno de asistente abierto, y el LM emite exactamente `duracion * 5`
   codigos de audio. Esta fase si usa CFG (por defecto 2,0 en upstream).

Que hace el DiT con esos codigos, y por que hoy no hace nada
-------------------------------------------------------------
El camino de upstream, verificado en el codigo y no supuesto:

    codigos (5 Hz)
      -> model.tokenizer.quantizer.get_output_from_indices(indices)  [1, N, 64]
      -> model.detokenizer(...)                                      [1, N*5, 64]
      -> = lm_hints_25Hz

y en `prepare_condition` del modelo (linea 1646 de
`vendor/modeling_acestep_v15_turbo.py`)::

    src_latents = torch.where(is_covers.unsqueeze(-1).unsqueeze(-1) > 0,
                              lm_hints_25Hz, src_latents)

**Ojo con el sentido de esa condicion.** Los hints entran cuando `is_covers` es
CIERTO, no cuando es falso. Lo que hace que entren en una generacion normal es
que upstream marca el elemento como "cover" en cuanto hay codigos, en
`acestep/core/generation/handler/conditioning_masks.py` linea 70::

    is_cover = (task_type == "cover") or has_code_hint

Es decir: `is_covers` no significa "el usuario ha pedido una version"; significa
"el latente de origen viene de fuera del ruido". Con el planificador conectado,
viene del planificador. Y ademas upstream mete esos mismos hints como
`target_latents` (`conditioning_target.py` linea 79), asi que `src_latents` y
`lm_hints_25Hz` acaban siendo la misma cosa.

Consecuencia practica para quien escriba el shim, y es la parte que se puede
hacer mal sin que nada falle: **no basta con pasar los codigos; hay que poner
`is_covers = True`**. Si se pasan los hints con `is_covers = False`, el
`torch.where` los tira y el DiT sigue componiendo sobre el latente de silencio,
exactamente igual que hoy. No habria error, ni aviso, ni diferencia en el log:
solo el mismo audio de antes.

Que se ha quitado
-----------------
- Lote (`batch_size > 1`), `infer_type="dit"` (solo metadatos), la fase de
  comprension de audio, las rutas vLLM / nano-vllm / MLX, la descarga de pesos
  desde el hub, el catalogo de modelos por nivel de GPU y la gestion de descarga
  a CPU por presion de VRAM.
- `trust_remote_code=True`, que es lo que usa `_load_pytorch_model` de upstream.
  Aqui la clase se importa por nombre y se comprueba que el `config.json` no
  trae `auto_map`.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import torch

from .constants import (
    DURATION_MAX,
    MAX_AUDIO_CODE,
    VENTANA_AGRUPACION,
    codigos_para_duracion,
    duracion_de_codigos,
)
from .decodificacion_restringida import ProcesadorRestringido
from .generacion import calcular_max_tokens_nuevos, generar, generar_con_cfg
from .prompt import (
    SIN_ENTRADA_USUARIO,
    metadatos_a_cot,
    parsear_salida,
    prompt_codigos,
    prompt_codigos_uncond,
    prompt_cot,
)

__all__ = [
    "CAMPOS_SUFICIENTES",
    "PlanDeAudio",
    "PlanificadorLM",
    "codigos_de_texto",
    "hints_25Hz",
    "indices_de_codigos",
    "resumen_rango_dinamico",
]

#: Campos que, si vienen dados, hacen innecesaria la fase de razonamiento.
CAMPOS_SUFICIENTES = ("bpm", "keyscale", "timesignature", "duration")

_PATRON_CODIGO = re.compile(r"<\|audio_code_(\d+)\|>")


# --------------------------------------------------------------------------- #
# Codigos -> tensores
# --------------------------------------------------------------------------- #

def codigos_de_texto(cadena: str) -> List[int]:
    """Extrae los enteros de una cadena de tokens `<|audio_code_N|>`.

    Los valores fuera de `[0, 63999]` se recortan al rango, como upstream. Con
    la decodificacion restringida activada esto no deberia disparar nunca; si
    dispara, es que la lista blanca no se aplico.
    """
    if not cadena:
        return []
    return [max(0, min(int(x), MAX_AUDIO_CODE)) for x in _PATRON_CODIGO.findall(cadena)]


def indices_de_codigos(codigos: List[int], device: Any = "cpu") -> torch.Tensor:
    """Codigos -> tensor `[1, N, 1]` de enteros, la forma que espera el FSQ.

    La ultima dimension es el numero de cuantizadores residuales, que en este
    checkpoint es 1 (`config.fsq_input_num_quantizers`).
    """
    if not codigos:
        raise ValueError("No hay codigos que convertir.")
    return torch.tensor(codigos, device=device, dtype=torch.long).unsqueeze(0).unsqueeze(-1)


def hints_25Hz(
    model: Any,
    codigos: List[int],
    device: Any = None,
    dtype: Optional[torch.dtype] = None,
) -> torch.Tensor:
    """Codigos de 5 Hz -> `lm_hints_25Hz` `[1, N*5, 64]`, listos para el DiT.

    `model` es el `AceStepConditionGenerationModel` ya construido: se usan
    `model.tokenizer.quantizer` y `model.detokenizer`, nada mas.

    OJO al detalle de `vendor/pipeline/README.md`: los cinco bufferes NO
    persistentes del cuantizador FSQ (`_levels`, `_basis`, `implicit_codebook`,
    `scales`, `soft_clamp_input_value`) NO viajan en el `state_dict`. Hasta hoy
    daba igual porque `text2music` no llamaba ni a `tokenize` ni a `detokenize`;
    en cuanto se conecta el planificador, **si** se llama, y un `to_empty()` sin
    reinicializarlos produce hints basura sin levantar ningun error.
    """
    if device is None:
        device = next(model.parameters()).device
    indices = indices_de_codigos(codigos, device=device)
    cuantizado = model.tokenizer.quantizer.get_output_from_indices(indices)
    if dtype is not None and cuantizado.dtype != dtype:
        cuantizado = cuantizado.to(dtype)
    return model.detokenizer(cuantizado)


def resumen_rango_dinamico(ruta_safetensors: str) -> Dict[str, Any]:
    """ANADIDO (no procede de upstream): rango dinamico de los pesos del LM.

    El checkpoint viene en BF16 y Pascal no tiene BF16, asi que hay que decidir
    entre FP16 (rapido, con riesgo de desbordar) y FP32 (seguro, en CPU). Esta
    funcion mide en vez de suponer: recorre los tensores con `safetensors` (sin
    `pickle`, sin `torch.load`) y devuelve el maximo absoluto, cuantos valores
    caen fuera del rango normal de FP16 y cuantos se volverian cero.
    """
    from safetensors import safe_open

    maximo = 0.0
    minimo_no_nulo = float("inf")
    desbordan = 0
    subdesbordan = 0
    total = 0
    peor_tensor = ""

    with safe_open(ruta_safetensors, framework="pt", device="cpu") as fichero:
        for clave in fichero.keys():
            t = fichero.get_tensor(clave).float().abs()
            total += t.numel()
            local = float(t.max().item())
            if local > maximo:
                maximo = local
                peor_tensor = clave
            desbordan += int((t > 65504.0).sum().item())
            no_nulos = t[t > 0]
            if no_nulos.numel():
                minimo_no_nulo = min(minimo_no_nulo, float(no_nulos.min().item()))
                subdesbordan += int((no_nulos < 6.0e-8).sum().item())

    return {
        "max_abs": maximo,
        "tensor_max": peor_tensor,
        "min_abs_no_nulo": None if minimo_no_nulo == float("inf") else minimo_no_nulo,
        "valores": total,
        "fuera_de_fp16_por_arriba": desbordan,
        "fuera_de_fp16_por_abajo": subdesbordan,
        "cabe_en_fp16": desbordan == 0,
    }


# --------------------------------------------------------------------------- #
# Resultado
# --------------------------------------------------------------------------- #

@dataclass
class PlanDeAudio:
    """Lo que devuelve el planificador."""

    #: Metadatos del razonamiento (bpm, caption, duration, keyscale, language,
    #: timesignature). Los que el llamante impuso salen tal cual.
    metadatos: Dict[str, Any]
    #: Codigos de 5 Hz, ya como enteros del rango [0, 63999].
    codigos: List[int]
    #: El bloque `<think>` reserializado que se uso en la fase 2.
    texto_cot: str
    #: Segundos de audio que representan los codigos (`len(codigos) / 5`).
    segundos: float
    #: Fotogramas latentes de 25 Hz que produciran (`len(codigos) * 5`).
    fotogramas_25Hz: int
    #: Tiempos por fase, en segundos.
    tiempos: Dict[str, float] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Planificador
# --------------------------------------------------------------------------- #

class PlanificadorLM:
    """Carga el LM de 5 Hz y produce planes de audio.

    No instancia nada del DiT ni sabe de latentes: devuelve codigos. Quien los
    convierte en hints es :func:`hints_25Hz`, y quien decide donde vive cada
    componente es el shim.
    """

    def __init__(self, model: Any, tokenizer: Any, duracion_maxima: int = DURATION_MAX) -> None:
        self.model = model
        self.tokenizer = tokenizer
        self.dispositivo = next(model.parameters()).device
        self.procesador = ProcesadorRestringido(tokenizer, duracion_maxima=duracion_maxima)
        self.duracion_maxima = duracion_maxima

    # -- carga ----------------------------------------------------------- #

    @staticmethod
    def _comprobar_sin_codigo_remoto(ruta: str) -> None:
        """Aborta si algun JSON del checkpoint pide cargar codigo de terceros.

        ANADIDO (no procede de upstream): upstream carga con
        `trust_remote_code=True` sin mirar. `CLAUDE.md` lo prohibe, y una
        comprobacion explicita es mejor que confiar en el valor por defecto de
        una libreria que puede cambiarlo.
        """
        for nombre in ("config.json", "tokenizer_config.json"):
            camino = os.path.join(ruta, nombre)
            if not os.path.exists(camino):
                continue
            with open(camino, "r", encoding="utf-8") as fichero:
                datos = json.load(fichero)
            if "auto_map" in datos:
                raise ValueError(
                    f"{camino} declara 'auto_map': cargarlo ejecutaria codigo de terceros "
                    "descargado en tiempo de ejecucion. Prohibido por CLAUDE.md."
                )

    @classmethod
    def cargar(
        cls,
        ruta: str,
        device: Any = "cpu",
        dtype: torch.dtype = torch.float32,
        duracion_maxima: int = DURATION_MAX,
    ) -> "PlanificadorLM":
        """Carga el checkpoint desde un directorio local.

        `dtype` por defecto es **float32 en CPU**, no bfloat16: el checkpoint
        viene en BF16 y la GPU objetivo (GP104, sm_61) no tiene BF16. Ver
        :func:`resumen_rango_dinamico` antes de bajar a FP16.
        """
        from transformers import AutoTokenizer, Qwen3ForCausalLM

        cls._comprobar_sin_codigo_remoto(ruta)

        with open(os.path.join(ruta, "config.json"), "r", encoding="utf-8") as fichero:
            configuracion = json.load(fichero)
        arquitecturas = configuracion.get("architectures") or []
        if arquitecturas != ["Qwen3ForCausalLM"]:
            raise ValueError(
                f"El checkpoint declara architectures={arquitecturas!r} y este cargador solo "
                "acepta ['Qwen3ForCausalLM']."
            )

        tokenizer = AutoTokenizer.from_pretrained(ruta)
        # MODIFICADO respecto a upstream: `AutoModelForCausalLM` +
        # `trust_remote_code=True` se sustituye por la clase concreta, importada
        # por nombre, y `use_safetensors=True` para que ni siquiera considere un
        # `.bin` con `pickle` dentro.
        model = Qwen3ForCausalLM.from_pretrained(ruta, dtype=dtype, use_safetensors=True)
        model = model.to(device)
        model.eval()
        return cls(model, tokenizer, duracion_maxima=duracion_maxima)

    # -- planificacion ---------------------------------------------------- #

    @staticmethod
    def tiene_metas_suficientes(metadatos: Optional[Dict[str, Any]]) -> bool:
        """True si estan los cuatro campos que permiten saltarse la fase 1.

        MODIFICADO respecto a upstream: `has_all_metas` comprueba
        `'bpm' in user_metadata`, o sea la PRESENCIA DE LA CLAVE, no que tenga
        valor. Un diccionario `{"bpm": None, "keyscale": None, ...}` —que es
        justo lo que produce un formulario con campos vacios— le da True, se
        salta el razonamiento y el modelo se queda sin metadatos. Aqui se exige
        valor no nulo.
        """
        if not metadatos:
            return False
        return all(metadatos.get(campo) is not None for campo in CAMPOS_SUFICIENTES)

    def planificar(
        self,
        estilo: str,
        letra: str = "",
        duracion_s: Optional[float] = None,
        metadatos_usuario: Optional[Dict[str, Any]] = None,
        temperatura: float = 0.85,
        escala_cfg: float = 2.0,
        top_k: Optional[int] = None,
        top_p: Optional[float] = 0.9,
        repeticion: float = 1.0,
        prompt_negativo: str = SIN_ENTRADA_USUARIO,
        generar_caption: bool = True,
        generar_idioma: bool = True,
        semilla: Optional[int] = None,
        on_token: Optional[Any] = None,
    ) -> PlanDeAudio:
        """Ejecuta las dos fases y devuelve el plan.

        Los valores por defecto de muestreo son los de `GenerationParams` de
        upstream: `lm_temperature=0.85`, `lm_cfg_scale=2.0`, `lm_top_k=0`
        (desactivado), `lm_top_p=0.9`.
        """
        # MODIFICADO respecto a upstream: semilla explicita. El camino PyTorch de
        # upstream no siembra nada en modo individual, asi que dos ejecuciones
        # con los mismos parametros dan codigos distintos y no hay forma de
        # comparar una version del pipeline con otra.
        if semilla is not None:
            torch.manual_seed(int(semilla))

        metadatos_usuario = dict(metadatos_usuario or {})
        if duracion_s is not None and metadatos_usuario.get("duration") is None:
            metadatos_usuario["duration"] = str(int(duracion_s))

        tiempos: Dict[str, float] = {}
        metadatos: Dict[str, Any] = {}

        # ---------------- Fase 1: razonamiento ---------------- #
        if not self.tiene_metas_suficientes(metadatos_usuario):
            inicio = time.time()
            entrada = self.tokenizer(prompt_cot(self.tokenizer, estilo, letra), return_tensors="pt")
            entrada = {clave: valor.to(self.dispositivo) for clave, valor in entrada.items()}

            self.procesador.reiniciar()
            self.procesador.habilitado = True
            self.procesador.fijar_fase("cot")
            self.procesador.fijar_parar_en_razonamiento(True)
            # Upstream NO restringe la duracion en la fase 1: el valor entra por
            # inyeccion de metadatos si el llamante lo dio.
            self.procesador.fijar_duracion_objetivo(None)
            self.procesador.fijar_metadatos_usuario(metadatos_usuario)
            self.procesador.fijar_omitir_caption(not generar_caption)
            self.procesador.fijar_omitir_idioma(not generar_idioma)
            self.procesador.temperatura_metadatos = None
            self.procesador.temperatura_codigos = None

            nuevos = generar(
                self.model,
                entrada["input_ids"],
                entrada.get("attention_mask"),
                max_tokens_nuevos=calcular_max_tokens_nuevos(
                    None, "cot", self._tope_modelo(), self.duracion_maxima
                ),
                temperatura=temperatura,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.pad_token_id,
                top_k=top_k,
                top_p=top_p,
                repeticion=repeticion,
                procesador=self.procesador,
                on_token=on_token,
                # Sin CFG: upstream fuerza cfg_scale=1.0 en el razonamiento
                # porque escalar logits de texto trunca los captions.
            )
            texto = self.tokenizer.decode(nuevos, skip_special_tokens=False)
            metadatos, _ = parsear_salida(texto)
            tiempos["fase1"] = time.time() - inicio
        else:
            metadatos = {c: v for c, v in metadatos_usuario.items() if v is not None}
            tiempos["fase1"] = 0.0

        # La duracion efectiva: la pedida manda; si no hay, la del razonamiento.
        if duracion_s is None or duracion_s <= 0:
            try:
                duracion_s = float(metadatos.get("duration"))
            except (TypeError, ValueError):
                duracion_s = None
        if duracion_s is None or duracion_s <= 0:
            raise ValueError(
                "No hay duracion: ni la pidio el llamante ni la produjo el razonamiento. "
                "Sin duracion no hay contrato de longitud."
            )

        # ---------------- Fase 2: codigos ---------------- #
        inicio = time.time()
        cot = metadatos_a_cot(metadatos)
        texto_cond = prompt_codigos(self.tokenizer, estilo, letra, cot)

        self.procesador.reiniciar()
        self.procesador.habilitado = True
        self.procesador.fijar_fase("codes")
        self.procesador.fijar_parar_en_razonamiento(False)
        self.procesador.fijar_duracion_objetivo(duracion_s)
        self.procesador.fijar_metadatos_usuario(None)
        self.procesador.fijar_omitir_caption(True)
        self.procesador.fijar_omitir_idioma(True)

        maximo = calcular_max_tokens_nuevos(
            duracion_s, "codes", self._tope_modelo(), self.duracion_maxima
        )

        if escala_cfg > 1.0:
            texto_uncond = prompt_codigos_uncond(self.tokenizer, prompt_negativo)
            lado = self.tokenizer.padding_side
            self.tokenizer.padding_side = "left"
            try:
                lote = self.tokenizer([texto_cond, texto_uncond], return_tensors="pt", padding=True)
            finally:
                self.tokenizer.padding_side = lado
            lote = {clave: valor.to(self.dispositivo) for clave, valor in lote.items()}
            nuevos = generar_con_cfg(
                self.model,
                lote["input_ids"],
                lote.get("attention_mask"),
                max_tokens_nuevos=maximo,
                temperatura=temperatura,
                escala_cfg=escala_cfg,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.pad_token_id,
                top_k=top_k,
                top_p=top_p,
                repeticion=repeticion,
                procesador=self.procesador,
                on_token=on_token,
            )
        else:
            entrada = self.tokenizer(texto_cond, return_tensors="pt")
            entrada = {clave: valor.to(self.dispositivo) for clave, valor in entrada.items()}
            nuevos = generar(
                self.model,
                entrada["input_ids"],
                entrada.get("attention_mask"),
                max_tokens_nuevos=maximo,
                temperatura=temperatura,
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.pad_token_id,
                top_k=top_k,
                top_p=top_p,
                repeticion=repeticion,
                procesador=self.procesador,
                on_token=on_token,
            )

        texto = self.tokenizer.decode(nuevos, skip_special_tokens=False)
        _, cadena_codigos = parsear_salida(texto)
        codigos = codigos_de_texto(cadena_codigos)
        tiempos["fase2"] = time.time() - inicio
        tiempos["total"] = tiempos["fase1"] + tiempos["fase2"]

        # ANADIDO (no procede de upstream): el contrato, comprobado. Upstream se
        # limita a registrar cuantos codigos salieron; si la restriccion no se
        # aplico, el fallo aparece 20 minutos despues como un audio de la
        # duracion equivocada.
        esperados = codigos_para_duracion(duracion_s)
        if len(codigos) != esperados:
            raise ValueError(
                f"El planificador emitio {len(codigos)} codigos y la duracion pedida "
                f"({duracion_s} s) exige exactamente {esperados}. La decodificacion "
                "restringida no se aplico."
            )

        return PlanDeAudio(
            metadatos=metadatos,
            codigos=codigos,
            texto_cot=cot,
            segundos=duracion_de_codigos(len(codigos)),
            fotogramas_25Hz=len(codigos) * VENTANA_AGRUPACION,
            tiempos=tiempos,
        )

    def _tope_modelo(self) -> int:
        """Longitud maxima de contexto que se usa para acotar `max_new_tokens`."""
        # Upstream usa `self.max_model_len = 4096` fijo, no la del checkpoint
        # (40.960). Se conserva su valor: subirlo cambiaria el numero de codigos
        # que se pueden pedir de una vez y no es lo que se esta midiendo.
        return 4096
