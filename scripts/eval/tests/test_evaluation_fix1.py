"""Regresiones CPU adversariales; ningún fixture acredita corpus o calidad real."""

import json
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from uuid import uuid4

import httpx
import numpy as np
import pytest
import soundfile as sf

from scripts.eval import metrics, run


@pytest.fixture
def tmp_path():
    path = run.ROOT / ".cache/dev-cycle/t11/review-fix1/fixtures" / uuid4().hex
    path.mkdir(parents=True)
    return path


def wav(path):
    sf.write(path, np.full((480, 2), 0.1, dtype=np.float32), 48000, subtype="FLOAT")
    return path


def takes(root):
    source = wav(root / "synthetic.wav")
    return [
        {
            "identity": f"{brief}:{seed}",
            "brief_id": brief,
            "candidate": "mock",
            "seed": seed,
            "source": str(source),
            "sha256": metrics.file_hash(source),
        }
        for brief in ("B-01", "B-02")
        for seed in run.SEEDS
    ]


def test_r11_01_filename_has_no_ulid_timestamp(tmp_path, monkeypatch):
    # Actual ULID implementation with known, distinct creation times.
    clocks = iter([1700000000 + i for i in range(20)])
    monkeypatch.setattr(run.generate.time, "time", lambda: next(clocks))
    mapping = run.anonymize(takes(tmp_path), tmp_path / "collection", root=tmp_path)
    assert all(re.fullmatch(r"N[0-9a-f]{32}", row["code"]) for row in mapping)
    assert all(
        not re.fullmatch(r"[0-7][0-9A-HJKMNP-TV-Z]{25}", p.stem)
        for p in (tmp_path / "collection/blind").glob("*.wav")
    )
    folder = tmp_path / "collection"
    before = (folder / "private.map.json").read_bytes()
    assert run.anonymize(takes(tmp_path), folder, root=tmp_path) == mapping
    assert (folder / "private.map.json").read_bytes() == before


def test_partial_actual_execution_retains_ten_planned_groups(tmp_path):
    from engine_mock import descriptor
    from test_evaluation_cpu import catalog

    from scripts import input_preparation

    catalog(tmp_path)
    model = descriptor().model_dump(mode="json")
    plan = run.build_plan("mock", root=tmp_path, descriptors=[model])
    for row in plan["rows"]:
        row["request"]["params"]["duration_s"] = 0.01
        row["preparation"] = input_preparation.prepare(row["request"])
    plan = run.seal_plan(plan)
    counter = iter(range(30))

    def transport(request, *, job_id, **kwargs):
        index = next(counter)
        output = tmp_path / f"data/tmp/{job_id}/synthetic.wav"
        output.parent.mkdir(parents=True)
        if index not in {0, 6, 7, 8}:
            sf.write(
                output,
                np.full((480, 2), 1.1 if index == 3 else 0.1, dtype=np.float32),
                48000,
                subtype="FLOAT",
            )
        return {
            "source": str(output),
            "sha256": metrics.file_hash(output) if output.exists() else "missing",
            "job_id": job_id,
            "model_id": "mock",
            "synthetic": True,
        }

    def normalization(raw, scaled, **kwargs):
        index = int(raw.stem.split("-")[-1])
        if index == 1:
            return {"blind_ready": False, "gain": {"status": "PEAK_CONFLICT"}}
        scaled.write_bytes(raw.read_bytes())
        return {"blind_ready": True}

    def metric_runner(raw, request, **kwargs):
        if raw.stem == "raw-02":
            raise ValueError("SYNTHETIC_METRIC_FAILURE")
        return {"audio.clap": {"status": "ERROR"}}

    report = run.execute(
        plan,
        root=tmp_path,
        transport=transport,
        allow_synthetic=True,
        normalization=normalization,
        metric_runner=metric_runner,
    )
    assert len(report["takes"]) == 30 and report["acceptance"] is None
    folder = tmp_path / "eval/takes" / report["session_id"] / "collection"
    mapping = json.loads((folder / "private.map.json").read_text())
    groups = json.loads((folder / "selection-pending.json").read_text())["groups"]
    by_code = {r["code"]: r for r in mapping}
    assert len(groups) == 10
    assert sorted(len(g["codes"]) for g in groups) == [0, 1, 2] + [3] * 7
    for group in groups:
        assert len({by_code[c]["brief_id"] for c in group["codes"]}) <= 1
    assert report["takes"][2]["status"] == "ERROR" and report["takes"][2]["blind_ready"]
    assert not report["takes"][3]["blind_ready"]
    sheet = (folder / "blind/sheet.md").read_text(encoding="utf-8")
    assert "incompleto: faltan 3" in sheet and "B-01" not in sheet
    assert (folder.parent / "report.json").is_file()


def test_r11_02_partial_groups_never_cross_briefs(tmp_path):
    rows = takes(tmp_path)[1:]
    folder = tmp_path / "collection"
    run.anonymize(rows, folder, root=tmp_path)
    private = json.loads((folder / "private.map.json").read_text())
    by_code = {r["code"]: r for r in private}
    selection = json.loads((folder / "selection-pending.json").read_text())
    assert sorted(len(g["codes"]) for g in selection["groups"]) == [2, 3]
    for group in selection["groups"]:
        assert len({by_code[c]["brief_id"] for c in group["codes"]}) == 1
        assert group["complete"] == (len(group["codes"]) == 3)
        assert re.fullmatch(r"N[0-9a-f]{32}", group["group"])
    assert "B-01" not in json.dumps(selection) and "mock" not in json.dumps(selection)
    before = {p.name: p.read_bytes() for p in folder.rglob("*.json")}
    run.anonymize(rows, folder, root=tmp_path)
    assert before == {p.name: p.read_bytes() for p in folder.rglob("*.json")}


def test_group_plan_keeps_empty_brief_and_failed_slots(tmp_path):
    planned = takes(tmp_path)
    ready = planned[1:3]  # remaining brief has no playable audio
    folder = tmp_path / "collection"
    run.anonymize(ready, folder, root=tmp_path, planned_takes=planned)
    selection = json.loads((folder / "selection-pending.json").read_text())
    assert sorted(len(g["codes"]) for g in selection["groups"]) == [0, 2]
    assert sorted(g["missing_count"] for g in selection["groups"]) == [1, 3]
    assert all(not g["complete"] for g in selection["groups"])
    changed = [dict(t) for t in planned]
    changed[-1]["seed"] = 999
    with pytest.raises(ValueError, match="BLIND_RESUME_MISMATCH"):
        run.anonymize(ready, folder, root=tmp_path, planned_takes=changed)


def test_codes_collision_retry_and_exhaustion(tmp_path, monkeypatch):
    codes = iter(["0" * 32, "0" * 32, "1" * 32, "1" * 32, "2" * 32])
    monkeypatch.setattr(run.secrets, "token_hex", lambda _: next(codes))
    mapping = run.anonymize(takes(tmp_path)[:2], tmp_path / "collection", root=tmp_path)
    assert len({m["code"] for m in mapping}) == 2
    monkeypatch.setattr(run.secrets, "token_hex", lambda _: "0" * 32)
    with pytest.raises(ValueError, match="BLIND_CODE_COLLISION"):
        run.anonymize(takes(tmp_path), tmp_path / "collision", root=tmp_path)


def floor_rows(root):
    rows = []
    for i in range(2):
        audio = wav(root / f"structural-synthetic-{i}.wav")
        # Distinct PCM bytes, explicitly synthetic fixture falsely claiming real.
        sf.write(
            audio,
            np.full((480, 2), 0.1 + i * 0.1, dtype=np.float32),
            48000,
            subtype="FLOAT",
        )
        gt, transcript = root / f"gt-{i}.txt", root / f"transcript-{i}.txt"
        gt.write_text("Árbol canta", encoding="utf-8")
        transcript.write_text("árbol", encoding="utf-8")
        rows.append(
            dict(
                synthetic=False,
                sung=True,
                rights="own",
                gt_declared=True,
                model_id="asr",
                profile="profile",
                coverage="whole_recording",
                language="es",
                **{
                    k: {"path": p.name, "sha256": metrics.file_hash(p)}
                    for k, p in [
                        ("audio", audio),
                        ("ground_truth", gt),
                        ("transcript", transcript),
                    ]
                },
            )
        )
    return rows


@pytest.mark.parametrize(
    "case",
    [
        "nominal",
        "model",
        "profile",
        "partial",
        "synthetic",
        "input",
        "output",
        "invalid_pcm",
        "duplicate",
    ],
)
def test_floor_structural_fixtures_never_authorize_rebate(tmp_path, case):
    rows = floor_rows(tmp_path)
    if case == "model":
        rows[0]["model_id"] = "other"
    if case == "profile":
        rows[0]["profile"] = "other"
    if case == "partial":
        rows[0]["coverage"] = "first_window"
    if case == "synthetic":
        rows[0]["synthetic"] = True
    if case in {"input", "output"}:
        field = "audio" if case == "input" else "transcript"
        (tmp_path / rows[0][field]["path"]).write_bytes(b"replaced")
    if case == "invalid_pcm":
        audio = tmp_path / rows[0]["audio"]["path"]
        sf.write(audio, np.full((480, 2), np.nan), 48000, subtype="FLOAT")
        rows[0]["audio"]["sha256"] = metrics.file_hash(audio)
    if case == "duplicate":
        rows[1]["audio"] = rows[0]["audio"]
    if case == "nominal":
        before = (tmp_path / rows[0]["transcript"]["path"]).read_bytes()
        result = metrics.measure_floor(
            rows, root=tmp_path, model_id="asr", profile="profile"
        )
        assert result["status"] == "PENDING" and result["mean"] is None
        assert result["normalization"] == metrics.NORMALIZATION
        assert result["per_recording"] == [0.5, 0.5]
        assert (tmp_path / rows[0]["transcript"]["path"]).read_bytes() == before
    else:
        with pytest.raises(ValueError):
            metrics.measure_floor(
                rows, root=tmp_path, model_id="asr", profile="profile"
            )


def test_r11_03_hashes_cannot_attest_real_asr(tmp_path):
    rows = []
    for i in range(2):
        audio = tmp_path / f"fake-audio-{i}"
        audio.write_text(f"not audio {i}")
        gt, transcript = tmp_path / f"gt-{i}", tmp_path / f"transcript-{i}"
        gt.write_text("uno dos")
        transcript.write_text("uno")
        rows.append(
            dict(
                synthetic=False,
                sung=True,
                rights="own",
                gt_declared=True,
                model_id="asr",
                profile="profile",
                coverage="whole_recording",
                language="es",
                **{
                    k: {
                        "path": str(p.relative_to(tmp_path)),
                        "sha256": metrics.file_hash(p),
                    }
                    for k, p in [
                        ("audio", audio),
                        ("ground_truth", gt),
                        ("transcript", transcript),
                    ]
                },
            )
        )
    try:
        result = metrics.measure_floor(
            rows, root=tmp_path, model_id="asr", profile="profile"
        )
    except (ValueError, sf.LibsndfileError):
        return
    assert result["status"] == "PENDING" and result.get("mean") is None


@pytest.mark.parametrize("bad", [None, "0.5", True, float("nan"), float("inf")])
@pytest.mark.parametrize("axis", ["PQ", "PC", "CE", "CU"])
def test_r11_04_invalid_outputs_isolated(tmp_path, bad, axis):
    from engine_mock import descriptor

    model = descriptor().model_dump(mode="json")
    calls = []

    def transport(request, *, job_id, **kwargs):
        task = request["task"]
        calls.append(task)
        analysis = {
            "audio.transcribe": {"text": "uno", "language": "Spanish"},
            "audio.clap": {"score": bad, "text_truncated": False, "audio_window_s": 10},
            "audio.aesthetics": dict(
                {"PQ": 1, "PC": 2, "CE": 3, "CU": 4}, **{axis: bad}
            ),
        }[task]
        path = tmp_path / f"data/tmp/{job_id}/analysis.json"
        path.write_text(
            json.dumps(
                {
                    "task": task,
                    "analysis": analysis,
                    "stages": [
                        {"task": task, "model_id": "mock", "revision": "synthetic-v1"}
                    ],
                }
            )
        )
        return {
            "source": str(path),
            "sha256": metrics.file_hash(path),
            "job_id": job_id,
            "model_id": "mock",
            "synthetic": True,
        }

    result = run.measure_take(
        wav(tmp_path / "input.wav"),
        {"params": {"lyrics": "uno dos", "language": "es", "style": "synthetic"}},
        root=tmp_path,
        transport=transport,
        descriptors=[model],
        bindings={
            t: "mock" for t in ("audio.transcribe", "audio.clap", "audio.aesthetics")
        },
    )
    assert len(calls) == 3
    assert result["audio.transcribe"]["status"] == "MEASURED"
    assert result["audio.transcribe"]["value"]["wer"]["adjusted"] is None
    assert (
        result["audio.clap"]["status"]
        == result["audio.aesthetics"]["status"]
        == "ERROR"
    )


@pytest.mark.parametrize("payload", [None, [], {"analysis": None}, {"analysis": []}])
def test_metric_output_shape_errors_are_typed(payload):
    with pytest.raises(ValueError, match="METRIC_OUTPUT_INVALID"):
        metrics.native_metric("audio.clap", payload, reference="uno", language="es")


def test_matching_caller_floor_cannot_authorize_adjustment(tmp_path):
    from engine_mock import descriptor

    from scripts import input_preparation

    model = descriptor().model_dump(mode="json")
    stages = [
        {"task": "audio.transcribe", "model_id": "mock", "revision": "synthetic-v1"}
    ]
    profile = input_preparation.digest(
        input_preparation.encode(
            {
                "descriptor": model,
                "stages": stages,
                "coverage": "whole_recording",
                "normalization": metrics.NORMALIZATION,
            }
        )
    )

    def transport(request, *, job_id, **kwargs):
        output = tmp_path / f"data/tmp/{job_id}/analysis.json"
        output.write_text(
            json.dumps(
                {
                    "task": request["task"],
                    "stages": stages,
                    "analysis": {"text": "uno", "language": "Spanish"},
                }
            )
        )
        return {
            "source": str(output),
            "sha256": metrics.file_hash(output),
            "job_id": job_id,
            "model_id": "mock",
            "synthetic": True,
        }

    result = run.measure_take(
        wav(tmp_path / "input.wav"),
        {"params": {"lyrics": "uno dos", "language": "es", "style": "synthetic"}},
        root=tmp_path,
        transport=transport,
        descriptors=[model],
        bindings={
            t: "mock" for t in ("audio.transcribe", "audio.clap", "audio.aesthetics")
        },
        floor={
            "status": "MEASURED",
            "model_id": "mock",
            "profile": profile,
            "mean": 0.9,
            "normalization": metrics.NORMALIZATION,
            "bindings": [{"caller_receipt": "invented"}],
        },
    )
    assert result["audio.transcribe"]["error"] == "FLOOR_CONTROLLED_EXECUTION_PENDING"
    assert "value" not in result["audio.transcribe"]


@pytest.mark.parametrize(
    "stream_kind",
    [
        "lines",
        "partial",
        "blank",
        "stall",
        "terminal_keepalive",
        "multiple",
        "submit_partial",
        "estimate_partial",
    ],
)
def test_r11_05_native_socket_stream_deadline(tmp_path, monkeypatch, stream_kind):
    from engine_contract import Event
    from engine_mock import descriptor

    model = descriptor().model_dump(mode="json")
    job_id = "01M49HZQ7K5WFE9PA1N3WDN92K"
    real_clock = time.monotonic
    origin = real_clock()
    # Sixty logical seconds in 0.6 real seconds; socket and threads remain native.
    monkeypatch.setattr(run.time, "monotonic", lambda: (real_clock() - origin) * 100)
    stop = threading.Event()
    posts = []
    cleanup = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, value):
            body = json.dumps(value).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            self.rfile.read(int(self.headers.get("Content-Length", 0)))
            posts.append(self.path)
            if (stream_kind == "submit_partial" and self.path == "/v1/jobs") or (
                stream_kind == "estimate_partial" and self.path == "/v1/estimate"
            ):
                self.send_response(200)
                self.end_headers()
                try:
                    end = real_clock() + 1.3
                    while real_clock() < end and not stop.is_set():
                        self.wfile.write(b" ")
                        self.wfile.flush()
                        stop.wait(0.01)
                    self.wfile.write(json.dumps({"job_id": job_id}).encode())
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass
                return
            self.reply({"job_id": job_id} if self.path == "/v1/jobs" else {})

        def do_GET(self):
            if self.path == "/v1/models":
                self.reply([model])
            elif self.path == "/v1/health":
                self.reply(
                    {
                        "engine_id": "private-fake",
                        "engine_version": "1",
                        "image_digest": "fake",
                        "state": "idle",
                        "loaded": None,
                        "job_id": None,
                        "gpu": {"total_mb": 0, "free_mb": 0, "cap_mb": 0},
                    }
                )
            elif "/events" in self.path:
                self.send_response(200)
                self.end_headers()
                end = real_clock() + 1.3
                seq = 0
                try:
                    if stream_kind in {"terminal_keepalive", "multiple"}:
                        first = Event(
                            job_id=job_id,
                            seq=1,
                            type="error",
                            data={
                                "code": "INTERNAL",
                                "message": "synthetic",
                                "retryable": False,
                            },
                        )
                        block = first.model_dump_json().encode() + b"\n"
                        if stream_kind == "multiple":
                            block += (
                                first.model_copy(update={"seq": 2})
                                .model_dump_json()
                                .encode()
                                + b"\n"
                            )
                        self.wfile.write(block)
                        self.wfile.flush()
                        stop.wait(1.3)
                        return
                    if stream_kind == "stall":
                        stop.wait(1.3)
                        return
                    while real_clock() < end and not stop.is_set():
                        seq += 1
                        chunk = (
                            Event(
                                job_id=job_id,
                                seq=seq,
                                type="progress",
                                data={"fraction": 0.1},
                            )
                            .model_dump_json()
                            .encode()
                            + b"\n"
                        )
                        if stream_kind == "partial":
                            chunk = b" "
                        if stream_kind == "blank":
                            chunk = b"\n"
                        self.wfile.write(chunk)
                        self.wfile.flush()
                        stop.wait(0.01)
                    terminal = Event(
                        job_id=job_id,
                        seq=seq + 1,
                        type="error",
                        data={
                            "code": "INTERNAL",
                            "message": "synthetic late terminal",
                            "retryable": False,
                        },
                    )
                    self.wfile.write(terminal.model_dump_json().encode() + b"\n")
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass
            else:
                cleanup.append(self.path)
                self.reply({"job_id": job_id, "state": "error", "seq": 0})

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = False
    provider = threading.Thread(target=server.serve_forever, name="t11-owned-provider")
    foreign_stop = threading.Event()
    foreign = threading.Thread(
        target=lambda: foreign_stop.wait(10), name="t11-foreign-sentinel"
    )
    provider.start()
    foreign.start()
    started = real_clock()
    try:
        with httpx.Client(trust_env=False, timeout=2) as client:
            transport = run.V1Transport(
                root=tmp_path,
                config={"STUDIO_ENGINE_TOKEN": "synthetic"},
                url=f"http://127.0.0.1:{server.server_port}",
                client=client,
            )
            expected = {
                "terminal_keepalive": "INTERNAL",
                "multiple": "ENGINE_EVENT_INVALID",
                "submit_partial": "SUBMIT_ACK_UNKNOWN",
            }.get(stream_kind, "TIMEOUT")
            with pytest.raises(ValueError, match=expected):
                transport(
                    {"task": "music.song", "params": {"duration_s": 0.01}, "seed": 101},
                    job_id=job_id,
                    descriptor=model,
                )
        assert real_clock() - started < 1.1
        assert posts.count("/v1/jobs") == (
            0 if stream_kind == "estimate_partial" else 1
        )
        assert (cleanup or stream_kind == "estimate_partial") and foreign.is_alive()
    finally:
        stop.set()
        server.shutdown()
        provider.join(2)
        server.server_close()
        assert not provider.is_alive() and foreign.is_alive()
        foreign_stop.set()
        foreign.join(2)
