import importlib
import importlib.util

from scripts.eval.capabilities_plan import matrix


def module():
    name = "scripts.eval.capabilities_runtime"
    if importlib.util.find_spec(name) is None:
        return type(
            "Missing",
            (),
            {
                "execute_v1": staticmethod(
                    lambda *a, **k: {
                        "execution_status": "planned",
                        "audio_output": "source.wav",
                    }
                )
            },
        )()
    return importlib.import_module(name)


def test_v1_rejection_is_real_422_null_audio_and_unload(tmp_path):
    from scripts.eval.benchmark_runtime import ApiError

    class Api:
        def __init__(self):
            self.calls = []

        def request(self, method, path, body=None, **kwargs):
            self.calls.append((method, path))
            if path == "/v1/jobs":
                raise ApiError("INVALID_PARAMS", 422)
            return {"ok": True}

    api = Api()
    row = next(
        r for r in matrix() if r["case"] == "music.retake" and r["surface"] == "v1"
    )
    result = module().execute_v1(
        row,
        {"style": "own", "lyrics": "own"},
        api,
        tmp_path,
        tmp_path,
        test_double=True,
    )
    assert result["execution_status"] == "rejected"
    assert result["audio_output"] is None
    assert result["error"] == {"code": "INVALID_PARAMS", "status": 422}
    assert api.calls[-1] == ("POST", "/v1/unload")
    assert not result["verified"]


def test_native_lifecycle_uses_nvml_tuple_and_always_unloads(tmp_path):
    from scripts.eval.capabilities_runtime import execute_native

    class GPU:
        def snapshot(self):
            return (12000, 10000)

    class Supervisor:
        alive = False

        def __init__(self):
            self.unloaded = False

        def load(self, *args, **kwargs):
            self.cap = args[2]

        def send(self, message):
            self.message = message

        def receive(self, timeout):
            return {"kind": "error", "code": "INTERNAL"}

        def unload(self):
            self.unloaded = True

    sup = Supervisor()
    row = next(
        r
        for r in matrix()
        if r["case"] == "music.song" and r["surface"] == "native_lab"
    )
    result = execute_native(
        row,
        {"style": "own", "lyrics": "own"},
        sup,
        GPU(),
        tmp_path,
        tmp_path / "evidence",
        test_double=True,
    )
    assert result["execution_status"] == "failed"
    assert sup.unloaded and sup.cap == 9488
    assert result["unload"]["free_recovered"]


def test_timbre_without_captured_consumption_does_not_invent_noop(tmp_path):
    row = next(
        r
        for r in matrix()
        if r["case"] == "timbre_ref"
        and r["surface"] == "v1"
        and r["control"]["reference"] is None
    )
    raw = tmp_path / "data/tmp" / row["job_id"]
    raw.mkdir(parents=True)
    (raw / "output.wav").write_bytes(b"CPU double")

    class API:
        def request(self, *a, **k):
            return {}

        def events(self, job, **k):
            return [
                {
                    "job_id": job,
                    "seq": 1,
                    "type": "done",
                    "data": {
                        "artifacts": [
                            {
                                "path": str(
                                    (raw / "output.wav").relative_to(tmp_path / "data")
                                )
                            }
                        ]
                    },
                }
            ]

    result = module().execute_v1(
        row,
        {"style": "own", "lyrics": "own"},
        API(),
        tmp_path,
        tmp_path / "evidence",
        test_double=True,
    )
    assert result["no_op"] is None
