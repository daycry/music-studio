"""Semilla LM en la frontera PT individual, con RNG falso y sin Torch."""

import random
from contextlib import nullcontext
from types import SimpleNamespace

import adapter
import pytest
from engine_common import CancelToken, EngineError


class FakeTorch:
    def __init__(self, previous):
        self.cpu_rng = random.Random(previous)
        self.cuda_rng = random.Random(previous + 1)
        self.cuda = SimpleNamespace(max_memory_allocated=lambda: 0)

    def manual_seed(self, seed):
        # Torch manual_seed applies the seed to CPU and all device generators.
        self.cpu_rng.seed(seed)
        self.cuda_rng.seed(seed)

    def multinomial(self):
        return (self.cpu_rng.randrange(2**31), self.cuda_rng.randrange(2**31))


def exercise(
    monkeypatch,
    tmp_path,
    *,
    previous=100,
    seed=1,
    checkpoint="turbo",
    n_outputs=1,
    failure=None,
):
    torch = FakeTorch(previous)
    observed = []
    lm = SimpleNamespace(llm_backend="pt")

    def single(formatted_prompt, **kwargs):
        observed.append(
            {
                "prompt": formatted_prompt,
                "kwargs": kwargs,
                "codes": [torch.multinomial() for _ in range(4)],
            }
        )
        if failure is not None:
            raise failure
        return observed[-1]["codes"]

    lm._run_pt_single = single

    def generate_with_stop_condition(**kwargs):
        # The diagnosed upstream single path discards seeds. Formatting or
        # preprocessing can consume RNG before reaching the actual PT boundary.
        torch.multinomial()
        return lm._run_pt_single(
            "formatted caption + lyrics",
            temperature=0.85,
            user_metadata=kwargs["user_metadata"],
            top_k=0,
        )

    lm.generate_with_stop_condition = generate_with_stop_condition

    def generate_music(dit, lm, params, config, **kwargs):
        torch.multinomial()  # load/preprocessing state must not control LM codes
        lm.generate_with_stop_condition(
            caption=params.caption,
            lyrics=params.lyrics,
            seeds=config["seeds"],
            batch_size=1,
            user_metadata={"bpm": 94},
        )
        return SimpleNamespace(
            success=True, audios=[{"tensor": None, "sample_rate": 48000}]
        )

    monkeypatch.setattr(adapter, "preflight", lambda *a, **k: {})
    monkeypatch.setattr(adapter, "step_hooks", lambda *a: nullcontext())
    monkeypatch.setattr(
        adapter, "timed_generation", lambda rt, call: (call(), {"inference_s": 1})
    )
    monkeypatch.setattr(adapter, "write_wav", lambda *a: None)
    import soundfile

    monkeypatch.setattr(
        soundfile, "info", lambda *a: SimpleNamespace(frames=48000, samplerate=48000)
    )
    model = adapter.AceStepAdapter(checkpoint=f"acestep-v15-{checkpoint}")
    model.runtime = SimpleNamespace(
        torch=torch,
        lm=lm,
        dit=None,
        GenerationParams=lambda **kw: SimpleNamespace(**kw),
        GenerationConfig=lambda **kw: kw,
        generate_music=generate_music,
    )
    req = {
        "task": "music.song",
        "params": {
            "style": "caption",
            "lyrics": "lyrics",
            "language": "es",
            "duration_s": 30,
        },
        "seed": seed,
        "n_outputs": n_outputs,
    }
    try:
        result = model.generate(req, tmp_path, lambda e: None, CancelToken())
    finally:
        assert lm._run_pt_single is single, "La frontera LM no se restituyó"
    return observed, result


def test_same_effective_seed_ignores_prior_rng_and_checkpoint(monkeypatch, tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    turbo, _ = exercise(monkeypatch, first, previous=100, checkpoint="turbo")
    sft, _ = exercise(monkeypatch, second, previous=900, checkpoint="sft")
    assert turbo == sft, "La ruta LM individual sigue dependiendo del RNG anterior"


@pytest.mark.parametrize("seed", [0, 1, 2**64 - 3, None])
def test_variants_use_effective_seed_without_changing_lm_inputs(
    monkeypatch, tmp_path, seed
):
    random_seeds = iter([71, 72, 73])
    monkeypatch.setattr(adapter.secrets, "randbelow", lambda limit: next(random_seeds))
    observed, result = exercise(monkeypatch, tmp_path, seed=seed, n_outputs=3)
    seeds = [item["meta"]["seed"] for item in result["artifacts"]]
    assert seeds == ([71, 72, 73] if seed is None else [seed + i for i in range(3)])
    for item, effective in zip(observed, seeds, strict=True):
        expected = FakeTorch(999)
        expected.manual_seed(effective)
        assert item == {
            "prompt": "formatted caption + lyrics",
            "kwargs": {
                "temperature": 0.85,
                "user_metadata": {"bpm": 94, "language": "es"},
                "top_k": 0,
            },
            "codes": [expected.multinomial() for _ in range(4)],
        }
    if seed is not None:
        assert len({str(item["codes"]) for item in observed}) == 3


@pytest.mark.parametrize(
    "failure",
    [
        RuntimeError("sample error"),
        EngineError("CANCELLED", "cancel"),
        KeyboardInterrupt(),
    ],
)
def test_lm_method_is_restored_on_errors_and_cancellation(
    monkeypatch, tmp_path, failure
):
    expected = (
        KeyboardInterrupt if isinstance(failure, KeyboardInterrupt) else EngineError
    )
    with pytest.raises(expected):
        exercise(monkeypatch, tmp_path, failure=failure)
