"""Sockets CPU reales: silencio legítimo y plazo global; sin inferencia GPU."""

import json
import threading
import time
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from engine_contract import Event
from engine_mock import descriptor

from scripts.eval import metrics, run


@pytest.fixture
def tmp_path():
    path = Path(".cache/dev-cycle/t11/review-fix2/fixtures") / uuid4().hex
    path.mkdir(parents=True)
    return path.absolute()


@pytest.mark.parametrize(
    "expires,fragment", [(False, False), (False, True), (True, False)]
)
def test_native_quiet_job(tmp_path, monkeypatch, record_property, expires, fragment):
    model = descriptor().model_dump(mode="json")
    job_id = "01M49HZQ7K5WFE9PA1N3WDN92K"
    clock = time.monotonic
    origin = clock()
    if expires:
        # 60 logical seconds = 0.6 real seconds, never a 60s wall test.
        monkeypatch.setattr(run.time, "monotonic", lambda: (clock() - origin) * 100)
    source = tmp_path / f"data/tmp/{job_id}/result.json"
    source.parent.mkdir(parents=True)
    source.write_text("{}", encoding="utf-8")
    stop = threading.Event()
    posts, deletes, cursors = [], [], []
    state = {"value": "busy", "submitted": None}

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
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            posts.append((self.path, body))
            if self.path == "/v1/jobs":
                state["submitted"] = clock()
            self.reply({"job_id": job_id} if self.path == "/v1/jobs" else {})

        def do_DELETE(self):
            deletes.append(self.path)
            state["value"] = "cancelled"
            self.reply({})

        def do_GET(self):
            if self.path == "/v1/models":
                self.reply([model])
            elif self.path == "/v1/health":
                self.reply(
                    {
                        "engine_id": "private",
                        "engine_version": "1",
                        "image_digest": "fake",
                        "state": "idle",
                        "loaded": None,
                        "job_id": None,
                        "gpu": {"total_mb": 0, "free_mb": 0, "cap_mb": 0},
                    }
                )
            elif "/events" in self.path:
                after = int(self.path.split("after=")[1])
                cursors.append(after)
                self.send_response(200)
                self.end_headers()
                try:
                    if after == 0:
                        event = Event(
                            job_id=job_id,
                            seq=1,
                            type="progress",
                            data={"fraction": 0.1},
                        )
                        self.wfile.write(event.model_dump_json().encode() + b"\n")
                        if fragment:
                            self.wfile.write(b'{"discarded":"espa\xc3')
                        self.wfile.flush()
                    if stop.wait(max(0, state["submitted"] + 2 - clock())):
                        return
                    state["value"] = "done"
                    event = Event(
                        job_id=job_id,
                        seq=2,
                        type="done",
                        data={
                            "artifacts": [
                                {
                                    "output_index": 0,
                                    "path": f"tmp/{job_id}/result.json",
                                    "sha256": metrics.file_hash(source),
                                    "media_type": "application/json",
                                    "meta": {},
                                }
                            ],
                            "telemetry": {
                                "mode": "cpu",
                                "model_revision": model["revision"],
                            },
                        },
                    )
                    self.wfile.write(event.model_dump_json().encode() + b"\n")
                    self.wfile.flush()
                    stop.wait(5)  # Terminal must not wait for EOF.
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    pass
            else:
                self.reply({"job_id": job_id, "state": state["value"], "seq": 2})

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    provider = threading.Thread(target=server.serve_forever, name="t11-quiet-owned")
    foreign = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    control = threading.Thread(target=foreign.serve_forever, name="t11-quiet-control")
    provider.start()
    control.start()
    started = clock()
    try:
        with httpx.Client(trust_env=False) as client:
            transport = run.V1Transport(
                root=tmp_path,
                config={"STUDIO_ENGINE_TOKEN": "synthetic"},
                url=f"http://127.0.0.1:{server.server_port}",
                client=client,
            )
            request = {"task": "audio.clap", "params": {"text": "silencio español"}}
            if expires:
                with pytest.raises(ValueError, match="TIMEOUT"):
                    transport(request, job_id=job_id, descriptor=model)
                assert clock() - started < 1.5
                assert deletes == [f"/v1/jobs/{job_id}"]
            else:
                result = transport(request, job_id=job_id, descriptor=model)
                assert result["job_id"] == job_id and result[
                    "sha256"
                ] == metrics.file_hash(source)
                assert 2 <= clock() - started < 4
                assert deletes == []
                events = json.loads(
                    (source.parent / "controller-events.json").read_text()
                )
                assert [event["seq"] for event in events] == [1, 2]
            assert len([body for path, body in posts if path == "/v1/jobs"]) == 1
            assert all(body["job_id"] == job_id for _, body in posts)
            assert cursors[0] == 0 and all(cursor in {0, 1} for cursor in cursors)
        stop.set()
        server.shutdown()
        provider.join(2)
        server.server_close()
        assert not provider.is_alive() and server.socket.fileno() == -1
        with httpx.Client(trust_env=False) as client:
            assert client.get(
                f"http://127.0.0.1:{foreign.server_port}/v1/models"
            ).json() == [model]
        assert control.is_alive()
        record_property(
            "native_proof",
            json.dumps(
                {
                    "cursors": cursors,
                    "deletes": deletes,
                    "submit_count": sum(path == "/v1/jobs" for path, _ in posts),
                    "real_elapsed_s": clock() - started,
                    "logical_clock_scale": 100 if expires else 1,
                    "owned_joined": not provider.is_alive(),
                    "owned_socket_closed": server.socket.fileno() == -1,
                    "foreign_alive_and_responding": control.is_alive(),
                }
            ),
        )
    finally:
        stop.set()
        server.shutdown()
        provider.join(2)
        server.server_close()
        foreign.shutdown()
        control.join(2)
        foreign.server_close()
        assert not provider.is_alive() and not control.is_alive()


def test_event_bytes_preserve_split_utf8_and_bound_buffer(tmp_path):
    class Stream(httpx.SyncByteStream):
        def __iter__(self):
            yield b'{"message":"espa\xc3'
            yield b'\xb1ol"}\n'

    with httpx.Client(trust_env=False) as client:
        transport = run.V1Transport(
            root=tmp_path,
            config={"STUDIO_ENGINE_TOKEN": "synthetic"},
            url="http://127.0.0.1:8199",
            client=client,
        )
        with closing(httpx.Response(200, stream=Stream())) as response:
            batches = list(transport.event_batches(response, time.monotonic() + 5))
        assert json.loads(batches[0][0][0]) == {"message": "español"}
        assert batches[0][1] is False
        with (
            closing(httpx.Response(200, content=b"x" * (1024 * 1024 + 1))) as response,
            pytest.raises(ValueError, match="ENGINE_EVENT_TOO_LARGE"),
        ):
            list(transport.event_batches(response, time.monotonic() + 5))
