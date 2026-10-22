"""Factoría HTTP ligera: modelos y CUDA exclusivamente en el hijo."""

from engine_common import EngineError
from engine_common import create_app as common_app

from .descriptor import descriptors, validate_language


def preflight(request):
    if request.get("task") in {"audio.transcribe", "audio.align_lyrics"}:
        validate_language(request.get("params", {}).get("language"))
    if (
        request.get("n_outputs", 1) != 1
        or len(request["inputs"]) != 1
        or request["inputs"][0]["role"] != "audio"
    ):
        raise EngineError(
            "INVALID_PARAMS", "Se requiere una entrada de audio y una salida"
        )


def create_app(**kwargs):
    return common_app(
        descriptors(),
        "engine_analysis:AnalysisAdapter",
        engine_id="analysis",
        preflight=preflight,
        **kwargs,
    )
