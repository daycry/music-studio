import importlib
import importlib.util

import numpy as np


def module():
    name = "scripts.eval.capabilities_evidence"
    if importlib.util.find_spec(name) is None:
        return type(
            "Missing",
            (),
            {
                "compare_pcm": staticmethod(lambda *a, **k: {"outside_bitexact": True}),
                "eligible": staticmethod(lambda r: True),
            },
        )()
    return importlib.import_module(name)


def test_signed_zero_outside_is_not_bitexact():
    source = np.zeros((2, 100), dtype=np.float32)
    output = source.copy()
    output[0, 0] = -0.0
    result = module().compare_pcm(source, output, 20, 30, crossfade_frames=2)
    assert not result["outside_bitexact"]
    assert result["prefix"]["different_samples"] == [1, 0]
    assert result["prefix"]["max_abs_error"] == [0.0, 0.0]


def test_native_success_cannot_enable_verified():
    assert not module().eligible(
        {
            "surface": "native_lab",
            "execution_status": "executed",
            "verdict": "funciona",
            "musical_acceptance": {"accepted": True},
            "audio_output": "real.wav",
        }
    )
