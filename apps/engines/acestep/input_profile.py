"""Política operativa del backend PT auditado; no es la ventana arquitectónica."""

import math


def inference_controls(params, *, sft=False):
    """Valores efectivos; validación también para llamadas fuera de HTTP."""
    steps = params.get("inference_steps", 50 if sft else 8)
    guidance = params.get("guidance_scale", 7.0)
    if (
        type(steps) is not int
        or not 1 <= steps <= (200 if sft else 8)
        or (not sft and "guidance_scale" in params)
        or type(guidance) not in {int, float}
        or not 1 <= guidance <= 20
        or not math.isfinite(guidance)
    ):
        raise ValueError("INVALID_PARAMS")
    return {"inference_steps": steps, "guidance_scale": guidance}


LM_CONTEXT = 4096
DIT_TEXT_LIMIT = 256
DIT_LYRICS_LIMIT = 2048
MAX_DURATION = 480
UPSTREAM_REVISION = "dce621408bee8c31b4fcf4811682eb9359e1bc94"
SOURCE_HASHES = {
    "gpu_config.py": "50e9ca449d2c328b348a73975bcee81ba378ec610072196b8f6cfa8e23b54afa",
    "inference.py": "2395a1e6340af075d3f9d2fad293a389beb61f0a11e1db79a5ad120f6d0ce9a2",
    "llm_inference.py": "afe1baf01d8a594bd06148bf9c79a0f66f84072b5158ae598340b34cc215b9c6",
    "constants.py": "7b8d4ce49649c819d1b3be87a434be2d90768308768d4620639328f906209b22",
    "core/generation/handler/conditioning_text.py": "0313ef5fc5ade1baa5a806f3748e5c853961768d057045e040fcb28a33a153b6",
    "core/generation/handler/prompt_utils.py": "242835ae29cc1bfcc40aadf1c46d8156230349d6e2f05436b2c85b3491484fae",
    "core/generation/handler/metadata_utils.py": "b8485fe9c3a8ffdf0ee0147df68366770abfe6b68e6cd286dd4722d9379cdc5b",
}
VALID_LANGUAGES = frozenset(
    [
        "ar",
        "az",
        "bg",
        "bn",
        "ca",
        "cs",
        "da",
        "de",
        "el",
        "en",
        "es",
        "fa",
        "fi",
        "fr",
        "he",
        "hi",
        "hr",
        "ht",
        "hu",
        "id",
        "is",
        "it",
        "ja",
        "ko",
        "la",
        "lt",
        "ms",
        "ne",
        "nl",
        "no",
        "pa",
        "pl",
        "pt",
        "ro",
        "ru",
        "sa",
        "sk",
        "sr",
        "sv",
        "sw",
        "ta",
        "te",
        "th",
        "tl",
        "tr",
        "uk",
        "ur",
        "vi",
        "yue",
        "zh",
        "unknown",
    ]
)
