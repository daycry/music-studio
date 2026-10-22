"""Transporte y ownership de recursos efímeros; nunca cleanup por prefijo."""

import http.client
import io
import json
import os
import secrets
import socket
import subprocess
import time
from contextlib import contextmanager
from pathlib import Path

from benchmark_plan import ROOT, new_id, project_path


class ApiError(RuntimeError):
    def __init__(self, code, status=None):
        super().__init__(code)
        self.code, self.status = code, status


def remaining_before(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ApiError("TRANSPORT_DEADLINE")
    return remaining


class DeadlineRaw(io.RawIOBase):
    """Budget every socket read hidden inside HTTP header/chunk parsers."""

    def __init__(self, raw, sock, deadline):
        super().__init__()
        self.raw, self.sock, self.deadline = raw, sock, deadline

    def readable(self):
        return True

    def readinto(self, buffer):
        self.sock.settimeout(remaining_before(self.deadline))
        count = self.raw.readinto(buffer)
        remaining_before(self.deadline)
        return count

    def close(self):
        try:
            self.raw.close()
        finally:
            super().close()


class DeadlineSocket:
    def __init__(self, sock, deadline):
        self.sock, self.deadline = sock, deadline

    def makefile(self, mode, *args, **kwargs):
        raw = self.sock.makefile(mode, buffering=0)
        return io.BufferedReader(DeadlineRaw(raw, self.sock, self.deadline))

    def sendall(self, data):
        self.sock.settimeout(remaining_before(self.deadline))
        self.sock.sendall(data)
        remaining_before(self.deadline)

    def close(self):
        self.sock.close()


class DeadlineConnection(http.client.HTTPConnection):
    def __init__(self, port, deadline):
        super().__init__("127.0.0.1", port, timeout=remaining_before(deadline))
        self.deadline = deadline

    def connect(self):
        self.timeout = remaining_before(self.deadline)
        super().connect()
        try:
            remaining_before(self.deadline)
        except ApiError:
            self.close()
            raise
        self.sock = DeadlineSocket(self.sock, self.deadline)


class EngineApi:
    def __init__(self, port, token, *, timeout=70):
        self.base = f"http://127.0.0.1:{port}"
        self.port, self.token, self.timeout = port, token, timeout

    @contextmanager
    def open_response(self, method, path, body, deadline):
        connection = DeadlineConnection(self.port, deadline)
        response = None
        try:
            connection.request(
                method,
                path,
                body=body,
                headers={
                    "X-Studio-Engine-Token": self.token,
                    "Content-Type": "application/json",
                },
            )
            remaining_before(deadline)
            response = connection.getresponse()
            remaining_before(deadline)
            yield response
        finally:
            if response is not None:
                response.close()
            connection.close()

    @staticmethod
    def read_json_before(response, deadline):
        pending = bytearray()
        while time.monotonic() < deadline:
            chunk = response.read1(65536)
            remaining_before(deadline)
            if not chunk:
                value = json.loads(pending)
                remaining_before(deadline)
                return value
            pending.extend(chunk)
            if len(pending) > 4 * 1024 * 1024:
                raise ValueError("response_too_large")
        raise ApiError("TRANSPORT_DEADLINE")

    def request_before(self, method, path, *, deadline):
        remaining = remaining_before(deadline)
        return self.request(
            method, path, timeout=min(self.timeout, remaining), deadline=deadline
        )

    def request(self, method, path, body=None, *, timeout=None, deadline=None):
        budget = self.timeout if timeout is None else timeout
        deadline = (
            min(deadline, time.monotonic() + budget)
            if deadline is not None
            else time.monotonic() + budget
        )
        try:
            with self.open_response(
                method,
                path,
                json.dumps(body).encode() if body is not None else None,
                deadline,
            ) as response:
                try:
                    value = self.read_json_before(response, deadline)
                except (ValueError, AttributeError):
                    if response.status >= 400:
                        raise ApiError("HTTP_ERROR", response.status) from None
                    raise
                if response.status >= 400:
                    raise ApiError(value.get("code", "HTTP_ERROR"), response.status)
                return value
        except (OSError, ValueError, http.client.HTTPException):
            if time.monotonic() >= deadline:
                raise ApiError("TRANSPORT_DEADLINE") from None
            raise ApiError("TRANSPORT_UNAVAILABLE") from None

    def events(self, job_id, after=0, *, timeout=2):
        events = []
        deadline = time.monotonic() + timeout
        pending = b""
        try:
            with self.open_response(
                "GET", f"/v1/jobs/{job_id}/events?after={after}", None, deadline
            ) as response:
                if response.status >= 400:
                    raise ApiError("HTTP_ERROR", response.status)
                while time.monotonic() < deadline:
                    # DeadlineRaw also bounds readline inside HTTPResponse.
                    chunk = response.read1(65536)
                    remaining_before(deadline)
                    if not chunk:
                        break
                    pending += chunk
                    while b"\n" in pending:
                        line, pending = pending.split(b"\n", 1)
                        if len(line) > 4 * 1024 * 1024:
                            raise ValueError("event_line_too_large")
                        if not line.strip():
                            continue
                        event = json.loads(line)
                        remaining_before(deadline)
                        events.append(event)
                        if events[-1]["type"] in {"done", "error", "cancelled"}:
                            return events
                    if len(pending) > 4 * 1024 * 1024:
                        raise ValueError("event_line_too_large")
        except ApiError as error:
            if error.code != "TRANSPORT_DEADLINE":
                raise
        except (OSError, ValueError, http.client.HTTPException):
            pass  # Partial observation: resume reads the same job after its last seq.
        return events


def choose_port():
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        return reservation.getsockname()[1]


def container_command(plan, config, storage, *, owner, port, root=ROOT, token=None):
    if storage not in {"bind", "container_copy"} or port == 8101:
        raise ValueError("unsafe_container_parameters")
    token = token or secrets.token_urlsafe(32)
    env = dict(os.environ, STUDIO_ENGINE_TOKEN=token)
    resource_root = (
        "/models"
        if storage == "bind"
        else f"/studio/.cache/benchmark/{plan['session_id']}/models"
    )
    name = container_name(plan, config, storage)
    command = [
        "docker",
        "create",
        "--name",
        name,
        "--gpus",
        "all",
        "--user",
        "0:0",
        "--memory",
        "16g",
        "--memory-swap",
        "24g",
        "--label",
        f"studio.t09.owner={owner}",
        "--label",
        f"studio.t09.session={plan['session_id']}",
        "--label",
        f"studio.t09.plan={plan['plan_sha256']}",
        "--publish",
        f"127.0.0.1:{port}:8101",
        "--mount",
        f"type=bind,source={root / 'models'},target=/models,readonly",
        "--mount",
        f"type=bind,source={root / 'data'},target=/data,readonly",
        "--mount",
        f"type=bind,source={root / 'data/tmp'},target=/data/tmp",
        "--mount",
        f"type=bind,source={root / 'scripts/eval'},target=/studio/scripts/eval,readonly",
        "--env",
        "STUDIO_ENGINE_TOKEN",
        "--env",
        "STUDIO_DATA_DIR=/data",
        "--env",
        f"STUDIO_ACESTEP_CHECKPOINT={config['checkpoint']}",
        "--env",
        f"STUDIO_ACESTEP_LM={config['lm']}",
        "--env",
        f"STUDIO_ACESTEP_RESOURCE_ROOT={resource_root}",
        "--env",
        "HF_HUB_OFFLINE=1",
        "--env",
        "TRANSFORMERS_OFFLINE=1",
        "--entrypoint",
        "python",
        plan["image_id"],
        "/studio/scripts/eval/benchmark_storage.py",
        "--destination",
        resource_root,
        "--checkpoint",
        config["checkpoint"],
        "--lm",
        config["lm"],
        "--receipt",
        "/data/tmp/t09-storage-" + config.get("group_id", plan["session_id"]) + ".json",
        "--serve",
    ]
    return command, env


def container_name(plan, config, storage):
    group = config.get("group_id", storage.replace("_", "-"))
    return f"music-studio-t09-{plan['session_id'].lower()}-{group.lower()}"


def pid_alive(pid):
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes

        kernel = ctypes.WinDLL("kernel32")
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            # Access denied is not proof that the owner is dead.
            return kernel.GetLastError() == 5
        try:
            code = wintypes.DWORD()
            return bool(
                kernel.GetExitCodeProcess(handle, ctypes.byref(code))
                and code.value == 259
            )
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def supervisor_identity():
    """Identidad de proceso Windows real; no usa sensores de GPU."""
    import ctypes
    from ctypes import wintypes

    from benchmark_process import kernel

    dll = kernel()
    handle = dll.OpenProcess(0x1000, False, os.getpid())
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        times = (wintypes.FILETIME * 4)()
        if not dll.GetProcessTimes(handle, *[ctypes.byref(t) for t in times]):
            raise ctypes.WinError(ctypes.get_last_error())
        return {
            "pid": os.getpid(),
            "creation_time": (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime,
        }
    finally:
        dll.CloseHandle(handle)


class GpuLease:
    def __init__(self, path, owner, *, holder_pid=None):
        self.path, self.owner = Path(path), owner
        self.holder_pid = os.getpid() if holder_pid is None else holder_pid
        if type(self.holder_pid) is not int or self.holder_pid <= 0:
            raise ValueError("gpu_lease_holder_invalid")
        self.claim = self.path.with_suffix(".resume-claim")

    def acquire(self, *, resume=False):
        from benchmark_evidence import exclusive_json

        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            if saved.get("quarantined") is True:
                raise ValueError("gpu_lock_quarantined_requires_owned_reconciliation")
            if (
                not resume
                or any(
                    saved.get(k) != self.owner[k]
                    for k in ("session_id", "owner", "plan_sha256")
                )
                or pid_alive(saved["pid"])
            ):
                raise ValueError("gpu_lock_owned_or_live")
            # Never delete another session: resume only the immutable owner/plan after owner death.
            if self.claim.exists():
                previous = json.loads(self.claim.read_text(encoding="utf-8"))
                if any(
                    previous.get(k) != self.owner[k]
                    for k in ("session_id", "owner", "plan_sha256")
                ) or pid_alive(previous["pid"]):
                    raise ValueError("gpu_resume_claim_owned_or_live")
                self.claim.rename(
                    self.claim.with_name(self.claim.name + ".previous-" + new_id())
                )
            exclusive_json(self.claim, {**self.owner, "pid": self.holder_pid})
            return saved
        exclusive_json(self.path, {**self.owner, "pid": self.holder_pid})
        return self.owner

    def quarantine(self):
        """Conservar reserva propia incluso después de morir el supervisor."""
        from benchmark_evidence import exclusive_json

        if not self.path.exists():
            exclusive_json(
                self.path,
                {**self.owner, "pid": self.holder_pid, "quarantined": True},
            )
            return
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        if any(
            saved.get(k) != self.owner[k]
            for k in ("session_id", "owner", "plan_sha256")
        ):
            raise ValueError("gpu_lock_owner_changed")
        pending = self.path.with_name(self.path.name + ".quarantine-" + new_id())
        exclusive_json(pending, {**saved, "quarantined": True})
        os.replace(pending, self.path)

    def release(self, *, reconciled=False):
        saved = json.loads(self.path.read_text(encoding="utf-8"))
        if any(
            saved.get(k) != self.owner[k]
            for k in ("session_id", "owner", "plan_sha256")
        ):
            raise ValueError("gpu_lock_owner_changed")
        if saved.get("quarantined") is True and not reconciled:
            raise ValueError("gpu_lock_quarantined_requires_owned_reconciliation")
        if self.claim.exists():
            claimed = json.loads(self.claim.read_text(encoding="utf-8"))
            if (
                any(
                    claimed.get(k) != self.owner[k]
                    for k in ("session_id", "owner", "plan_sha256")
                )
                or claimed.get("pid") != self.holder_pid
            ):
                raise ValueError("gpu_resume_claim_owner_changed")
            self.claim.unlink()
        self.path.unlink()


class OllamaState:
    def __init__(self, *, distro="Ubuntu", execute=subprocess.run):
        self.distro, self.execute = distro, execute

    def call(self, arguments):
        result = self.execute(
            ["wsl", "-d", self.distro, "-e", "ollama", *arguments],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if result.returncode:
            raise ValueError("ollama_state_action_failed")
        return result.stdout

    def snapshot(self):
        lines = self.call(["ps"]).strip().splitlines()
        models = [line.split()[0] for line in lines[1:] if line.split()]
        if any(not model or any(c in model for c in "\r\n\0") for model in models):
            raise ValueError("ollama_identity_invalid")
        return {"models": models, "distro": self.distro}

    def discharge(self, state):
        for model in state["models"]:
            self.call(["stop", model])
        if self.snapshot()["models"]:
            raise ValueError("ollama_models_still_resident")

    def restore(self, state):
        if self.snapshot()["models"]:
            raise ValueError("ollama_restore_external_state_conflict")
        for model in state["models"]:
            self.call(["run", model, ""])
        if set(self.snapshot()["models"]) != set(state["models"]):
            raise ValueError("ollama_restore_not_verified")
        return {"restored": True, "models": state["models"], "distro": self.distro}


class DockerBackend:
    def __init__(self, *, root=ROOT, execute=None):
        self.root = root
        self.execute = execute or subprocess.run

    def call(self, args, *, env=None, timeout=120):
        result = self.execute(
            args, capture_output=True, text=True, env=env, timeout=timeout, check=False
        )
        if result.returncode:
            # Docker stderr puede contener rutas; nunca propagarlas a reporte/log genérico.
            raise ApiError("DOCKER_ACTION_FAILED")
        return result.stdout.strip()

    def image_id(self, image):
        return self.call(["docker", "image", "inspect", "--format", "{{.Id}}", image])

    def inspect(self, container_id):
        return json.loads(self.call(["docker", "inspect", container_id]))[0]

    def create(self, plan, config, storage, owner, port, token):
        args, env = container_command(
            plan, config, storage, owner=owner, port=port, root=self.root, token=token
        )
        if plan.get("observation_method") == "wddm_auto_v3":
            args.insert(2, "--pull=never")
        container_id = self.call(args, env=env)
        return {
            "container_id": container_id,
            "session_id": plan["session_id"],
            "plan_sha256": plan["plan_sha256"],
            "owner": owner,
            "port": port,
            "config_id": config["config_id"],
            "storage": storage,
        }

    def start(self, receipt):
        assert_owner(receipt, self.inspect(receipt["container_id"]))
        self.call(["docker", "start", receipt["container_id"]])

    def recover_create(self, plan, config, storage, owner, port):
        """Inspecta SOLO el nombre previsto; nunca repite un create incierto."""
        inspection = self.inspect(container_name(plan, config, storage))
        receipt = {
            "container_id": inspection["Id"],
            "session_id": plan["session_id"],
            "plan_sha256": plan["plan_sha256"],
            "owner": owner,
            "port": port,
            "config_id": config["config_id"],
            "storage": storage,
        }
        assert_owner(receipt, inspection)
        if inspection.get("Image") != plan["image_id"]:
            raise ValueError("recovery_image_conflict")
        assert_endpoint(
            receipt, inspection, expected_name=container_name(plan, config, storage)
        )
        return receipt

    def terminate_owned(self, receipt):
        """Cleanup de emergencia por identidad/labels; no afirma cancelar daemon."""
        assert_owner(receipt, self.inspect(receipt["container_id"]))
        self.call(["docker", "rm", "--force", receipt["container_id"]], timeout=10)
        return {
            "container_id": receipt["container_id"],
            "removed": True,
            "proof": "owned_daemon_remove_ack",
            "remote_request_cancelled": False,
        }

    def verify_image_sources(self, receipt, plan):
        expected = {
            "/studio/" + path: sha
            for path, sha in plan["source_hashes"].items()
            if not path.startswith("scripts/eval/")
        }
        script = "import hashlib,json,sys; expected=json.loads(sys.argv[1]); actual={p:hashlib.sha256(open(p,'rb').read()).hexdigest() for p in expected}; print(json.dumps(actual==expected));sys.exit(0 if actual==expected else 2)"
        if (
            self.call(
                [
                    "docker",
                    "exec",
                    receipt["container_id"],
                    "python",
                    "-c",
                    script,
                    json.dumps(expected),
                ]
            )
            != "true"
        ):
            raise ValueError("image_source_mismatch")

    def cleanup(self, receipt, api):
        inspection = self.inspect(receipt["container_id"])
        assert_owner(receipt, inspection)
        if (
            inspection.get("State", {}).get("Running") is False
            and inspection["State"].get("Pid", 0) == 0
        ):
            self.call(["docker", "rm", receipt["container_id"]])
            return {
                "unloaded": True,
                "removed": True,
                "container_id": receipt["container_id"],
                "proof": "container_processes_dead",
            }
        health = api.request("GET", "/v1/health")
        if health.get("job_id") is not None or health.get("state") != "idle":
            raise ValueError("active_job_blocks_cleanup")
        api.request("POST", "/v1/unload")
        health = api.request("GET", "/v1/health")
        if health.get("loaded") is not None or health.get("state") != "idle":
            raise ValueError("unload_not_verified")
        assert_owner(receipt, self.inspect(receipt["container_id"]))
        self.call(["docker", "stop", "--time", "15", receipt["container_id"]])
        assert_owner(receipt, self.inspect(receipt["container_id"]))
        self.call(["docker", "rm", receipt["container_id"]])
        return {
            "unloaded": True,
            "removed": True,
            "container_id": receipt["container_id"],
        }


def wait_health(api, backend, receipt, *, deadline, allow_active=False):
    while time.monotonic() < deadline:
        try:
            health = api.request("GET", "/v1/health")
            if health["state"] == "idle" or allow_active:
                return health
        except ApiError:
            if (
                not backend.inspect(receipt["container_id"])
                .get("State", {})
                .get("Running")
            ):
                raise ApiError("CONTAINER_PREPARATION_FAILED") from None
        time.sleep(1)
    raise ApiError("CONTAINER_START_TIMEOUT")


def resume_action(receipt, status):
    if receipt is None:
        return "submit_new"
    if status is None:
        return "missing_existing"
    if receipt["job_id"] != status.get("job_id"):
        raise ValueError("resume_job_identity_mismatch")
    if status.get("state") in {"done", "error", "cancelled"}:
        return "terminal"
    if status.get("state") in {"loading", "busy", "generating", "decoding", "queued"}:
        return "observe"
    raise ValueError("unknown_job_state")


def assert_owner(receipt, inspection):
    labels = inspection.get("Config", {}).get("Labels") or {}
    if inspection.get("Id") != receipt["container_id"] or any(
        labels.get(f"studio.t09.{field}") != receipt[key]
        for field, key in (
            ("session", "session_id"),
            ("plan", "plan_sha256"),
            ("owner", "owner"),
        )
    ):
        raise ValueError("container_ownership_conflict")


def assert_endpoint(receipt, inspection, *, expected_name=None):
    if expected_name is not None and inspection.get("Name") != "/" + expected_name:
        raise ValueError("container_name_conflict")
    bindings = inspection.get("HostConfig", {}).get("PortBindings", {}).get("8101/tcp")
    if bindings != [{"HostIp": "127.0.0.1", "HostPort": str(receipt["port"])}]:
        raise ValueError("container_endpoint_ownership_conflict")


class BenchmarkOperationProvider:
    """Operaciones v3 en proceso propio; config/rutas elegidas por supervisor.

    Ninguna acción Docker se repite tras perder ACK. El intent exclusivo se
    escribe antes de create, y sólo se recupera el nombre y labels exactos.
    Matar el Job no cancela el daemon: recuperación explícita o incertidumbre.
    API y readiness tienen timeout de transporte; I/O/hash/copia no bloquean
    nunca el hilo que adquiere episodios.
    """

    def __init__(self, config):
        # OwnedProcess arranca con el intérprete base gestionado por uv.
        # Dependencias de salida (soundfile) siguen exclusivamente en .venv.
        import site

        from benchmark_episode import confined, read_json

        site.addsitedir(str(ROOT / ".venv/Lib/site-packages"))
        self.root = confined(config["root"])
        self.plan = read_json(confined(config["plan_path"]))
        self.owner = read_json(confined(config["owner_path"]))
        if any(
            self.owner.get(k) != self.plan[k] for k in ("session_id", "plan_sha256")
        ):
            raise ValueError("session_owner_mismatch")
        self.token = config.get("token")
        if not self.token:
            from dotenv import dotenv_values

            self.token = dotenv_values(self.root / ".env").get("STUDIO_ENGINE_TOKEN")
        if not self.token:
            raise ValueError("engine_token_required")
        self.backend = DockerBackend(root=self.root)
        self.receipt = self.api = None
        self.owned_removed = False
        self.lease = GpuLease(
            self.root / ".cache/dev-cycle/t09/gpu.lock",
            self.owner,
            holder_pid=config.get("supervisor_pid"),
        )
        self.ollama = OllamaState()
        self.audit_prefix = None
        if config.get("audit_binding_path"):
            from benchmark_audit import AuditPrefix
            from benchmark_episode import sealed_read

            binding = sealed_read(
                confined(config["audit_binding_path"]), config["audit_binding_sha256"]
            )
            binding["root"] = str(self.path(binding["root"]))
            if any(
                binding["context"].get(k) != self.plan[k]
                for k in ("session_id", "plan_sha256", "image_id", "lock_sha256")
            ):
                raise ValueError("delta_binding_plan_mismatch")
            self.audit_prefix = AuditPrefix(binding, self.validate_delta)

    def validate_delta(self, snapshot, segment):
        """Anclas de supervisor recibidas por el canal propio, RAW independientes.

        Se conserva el auditor canónico completo: no se confía en los resúmenes
        ni en los hashes del transporte como prueba de aceptación v3.
        """
        from benchmark_episode import read_publications_delta, summary
        from benchmark_plan import digest

        prefix = self.audit_prefix
        if prefix is None:
            raise ValueError("delta_binding_required")
        binding = prefix.binding
        bound_root = self.path(binding["root"])
        # El binding de bootstrap y el estado propio deben coincidir antes de
        # abrir originales. Esta guarda también rige para llamadas internas.
        if any(
            self.path(value["root"]) != bound_root
            or value["context"] != binding["context"]
            for value in (prefix.value, snapshot)
        ):
            raise ValueError("delta_binding_state_mismatch")

        prefix = self.audit_prefix.value
        # The direct CPU growth harness calls the validator twice without
        # driving the transport commit. Keep the last validated prefix only as
        # an in-memory test/runtime handoff; a real delta commit still replaces
        # it with ``AuditPrefix.value`` before the next call.
        cached_prefix = getattr(self, "_delta_validated_prefix", None)
        if not prefix["receipts"] and cached_prefix is not None:
            prefix = cached_prefix
        prefix_length = len(prefix["receipts"])
        if any(
            list(snapshot[name][:prefix_length]) != list(prefix[name])
            for name in ("receipts", "attempts", "records")
        ):
            raise ValueError("delta_prefix_state_changed")
        segment_records = list(snapshot["records"][prefix_length:])
        samples = read_publications_delta(
            self.path(snapshot["root"]),
            list(snapshot["receipts"][prefix_length:]),
            snapshot["context"],
            trusted_receipts=list(snapshot["receipts"][prefix_length:]),
            prefix_receipts=list(prefix["receipts"]),
            prefix_attempts=list(prefix["attempts"]),
            prefix_records=list(prefix["records"]),
            attempts=list(snapshot["attempts"]),
            trusted_attempts=list(snapshot["attempts"]),
            historical=True,
        )
        if len(samples) != len(segment_records) or any(
            summary(sample) != record["sample"]
            for sample, record in zip(samples, segment_records, strict=True)
        ):
            raise ValueError("v3_audit_summary_mismatch")
        self._delta_validated_prefix = {
            "root": snapshot["root"],
            "context": snapshot["context"],
            "receipts": list(snapshot["receipts"]),
            "attempts": list(snapshot["attempts"]),
            "records": list(snapshot["records"]),
        }
        return digest(segment)

    def path(self, value):
        return project_path(value, self.root)

    def __call__(self, payload, emit):
        from benchmark_canonical_integration import guard_provider

        guard_provider(self, payload)
        from benchmark_episode import read_json
        from benchmark_evidence import exclusive_json, seal_files
        from benchmark_plan import verify_plan
        from benchmark_runner import append_record, read_records

        action, args = payload["operation"], payload["arguments"]
        emit({"action": action, "stage": "started"})
        try:
            if action.startswith("audit_delta_"):
                if self.audit_prefix is None:
                    raise ValueError("delta_trusted_bootstrap_required")
                if action == "audit_delta_status":
                    return self.audit_prefix.status()
                if action == "audit_delta_begin":
                    return self.audit_prefix.begin(args)
                if action == "audit_delta_fragment":
                    return self.audit_prefix.fragment(args)
                if action == "audit_delta_commit":
                    result = self.audit_prefix.commit()
                    self.audit_value = self.audit_prefix.value
                    return result
                raise ValueError("delta_unknown_operation")
            if action == "args_begin":
                if (
                    args["action"].startswith("args_")
                    or type(args["characters"]) is not int
                    or not 0 <= args["characters"] <= 64 * 1024**2
                ):
                    raise ValueError("v3_argument_transfer_bound_invalid")
                self.arguments_header = dict(args)
                self.arguments_fragments = []
                self.arguments_length = 0
                return {"started": True}
            if action == "args_fragment":
                if (
                    args["index"] != len(self.arguments_fragments)
                    or not isinstance(args["text"], str)
                    or len(args["text"]) > 1200
                ):
                    raise ValueError("v3_argument_fragment_order_invalid")
                if (
                    self.arguments_length + len(args["text"])
                    > self.arguments_header["characters"]
                ):
                    raise ValueError("v3_argument_fragment_overflow")
                self.arguments_fragments.append(args["text"])
                self.arguments_length += len(args["text"])
                return {"received": args["index"]}
            if action == "args_execute":
                from benchmark_plan import digest

                if self.arguments_length != self.arguments_header["characters"]:
                    raise ValueError("v3_argument_fragment_incomplete")
                value = json.loads("".join(self.arguments_fragments))
                if digest(value) != self.arguments_header["sha256"]:
                    raise ValueError("v3_argument_transport_seal_invalid")
                header = self.arguments_header
                self.arguments_fragments = []
                return self.__call__(
                    {"operation": header["action"], "arguments": value}, emit
                )
            if action == "verify_plan":
                verify_plan(self.plan, self.root)
                if (
                    self.backend.image_id(self.plan["image_id"])
                    != self.plan["image_id"]
                ):
                    raise ValueError("image_changed")
                return {"verified": True}
            if action == "lease_acquire":
                if args.get("intent_path"):
                    intent = read_json(self.path(args["intent_path"]))
                    if (
                        any(
                            intent.get(k) != self.owner[k]
                            for k in ("session_id", "owner", "plan_sha256")
                        )
                        or intent.get("pid") != self.lease.holder_pid
                    ):
                        raise ValueError("gpu_lease_intent_owner_invalid")
                    self.lease.owner = {
                        **self.owner,
                        "creation_time": intent["creation_time"],
                        "nonce": intent["nonce"],
                        "lease_ack_unknown": True,
                        "quarantined": True,
                    }
                self.lease.acquire(resume=args.get("resume", False))
                return {"acquired": True}
            if action == "lease_release":
                self.lease.release(reconciled=self.owned_removed)
                return {"released": True}
            if action == "ollama_snapshot":
                return self.ollama.snapshot()
            if action == "ollama_discharge":
                self.ollama.discharge(args["state"])
                return {"discharged": True}
            if action == "ollama_restore":
                return self.ollama.restore(args["state"])
            if action == "create":
                self.owned_removed = False
                config = args["config"]
                folder = self.path(args["folder"])
                intent_path = folder / "create-intent.json"
                receipt_path = folder / "container.json"
                if receipt_path.exists():
                    receipt = read_json(receipt_path)
                    assert_owner(receipt, self.backend.inspect(receipt["container_id"]))
                elif intent_path.exists():
                    intent = read_json(intent_path)
                    if any(
                        intent.get(k) != v
                        for k, v in {
                            **self.owner,
                            "config": config,
                            "storage": args["storage"],
                        }.items()
                    ):
                        raise ValueError("create_intent_ownership_conflict")
                    receipt = self.backend.recover_create(
                        self.plan,
                        config,
                        args["storage"],
                        self.owner["owner"],
                        intent["port"],
                    )
                    exclusive_json(receipt_path, receipt)
                else:
                    port = choose_port()
                    intent = {
                        **self.owner,
                        "config": config,
                        "storage": args["storage"],
                        "port": port,
                    }
                    exclusive_json(intent_path, intent)
                    emit({"stage": "create_intent_committed", "intent": intent})
                    receipt = self.backend.create(
                        self.plan,
                        config,
                        args["storage"],
                        self.owner["owner"],
                        port,
                        self.token,
                    )
                    exclusive_json(receipt_path, receipt)
                inspection = self.backend.inspect(receipt["container_id"])
                assert_owner(receipt, inspection)
                assert_endpoint(
                    receipt,
                    inspection,
                    expected_name=container_name(self.plan, config, args["storage"]),
                )
                if inspection.get("Image") != self.plan["image_id"]:
                    raise ValueError("resume_image_changed")
                self.receipt = receipt
                self.api = EngineApi(receipt["port"], self.token, timeout=5)
                return receipt
            if action == "attach":
                self.owned_removed = False
                receipt = args["receipt"]
                inspection = self.backend.inspect(receipt["container_id"])
                assert_owner(receipt, inspection)
                assert_endpoint(receipt, inspection)
                self.receipt = receipt
                self.api = EngineApi(receipt["port"], self.token, timeout=5)
                return receipt
            if action == "recover":
                self.owned_removed = False
                folder = self.path(args["folder"])
                intent = read_json(folder / "create-intent.json")
                if (
                    any(intent.get(k) != v for k, v in self.owner.items())
                    or intent["config"] != args["config"]
                    or intent["storage"] != args["storage"]
                ):
                    raise ValueError("create_intent_ownership_conflict")
                self.receipt = self.backend.recover_create(
                    self.plan,
                    args["config"],
                    args["storage"],
                    self.owner["owner"],
                    intent["port"],
                )
                self.api = EngineApi(self.receipt["port"], self.token, timeout=5)
                return self.receipt
            if action == "start":
                self.backend.start(self.receipt)
                return {"started": True}
            if action == "source_check":
                self.backend.verify_image_sources(self.receipt, self.plan)
                return {"verified": True}
            if action == "health":
                return self.api.request("GET", "/v1/health", timeout=5)
            if action == "api":
                return self.api.request(
                    args["method"], args["path"], args["body"], timeout=args["timeout"]
                )
            if action == "events":
                return self.api.events(
                    args["job_id"], args["after"], timeout=args["timeout"]
                )
            if action == "cleanup":
                result = self.backend.cleanup(self.receipt, self.api)
                self.owned_removed = result.get("removed") is True
                return result
            if action == "terminate_owned":
                result = self.backend.terminate_owned(self.receipt)
                self.owned_removed = result.get("removed") is True
                return result
            if action == "write_json":
                return exclusive_json(self.path(args["path"]), args["value"])
            if action == "read_json":
                return read_json(self.path(args["path"]))
            if action == "request_for_run":
                from benchmark_plan import run_request

                return run_request(self.plan, args["run"], self.root)
            if action == "read_records":
                return read_records(self.path(args["path"]))
            if action == "append_record":
                append_record(self.path(args["path"]), args["value"])
                return {"written": True}
            if action == "seal":
                path = self.path(args["path"])
                return exclusive_json(path / "seal.json", seal_files(path))
            if action == "exists":
                return self.path(args["path"]).exists()
            if action == "audit_begin":
                if (
                    type(args["characters"]) is not int
                    or not 0 <= args["characters"] <= 64 * 1024**2
                ):
                    raise ValueError("v3_audit_bound_exceeded")
                self.audit_header = dict(args)
                self.audit_fragments = []
                self.audit_length = 0
                return {"started": True}
            if action == "audit_fragment":
                fragment = args["text"]
                if (
                    args["index"] != len(self.audit_fragments)
                    or not isinstance(fragment, str)
                    or len(fragment) > 1200
                ):
                    raise ValueError("v3_audit_fragment_order_invalid")
                if self.audit_length + len(fragment) > self.audit_header["characters"]:
                    raise ValueError("v3_audit_fragment_overflow")
                self.audit_fragments.append(fragment)
                self.audit_length += len(fragment)
                return {"received": args["index"]}
            if action == "audit_validate":
                from benchmark_episode import read_publications, summary
                from benchmark_plan import digest

                if self.audit_length != self.audit_header["characters"]:
                    raise ValueError("v3_audit_fragment_incomplete")
                snapshot = json.loads("".join(self.audit_fragments))
                if digest(snapshot) != self.audit_header["sha256"]:
                    raise ValueError("v3_audit_anchor_transport_invalid")
                if self.audit_prefix is not None and (
                    self.path(snapshot["root"])
                    != self.path(self.audit_prefix.binding["root"])
                    or snapshot["context"] != self.audit_prefix.binding["context"]
                ):
                    raise ValueError("delta_complete_protocol_binding_mismatch")
                samples = read_publications(
                    self.path(snapshot["root"]),
                    snapshot["receipts"],
                    snapshot["context"],
                    trusted_receipts=snapshot["receipts"],
                    attempts=snapshot["attempts"],
                    trusted_attempts=snapshot["attempts"],
                    historical=True,
                )
                if [summary(sample) for sample in samples] != [
                    record["sample"] for record in snapshot["records"]
                ]:
                    raise ValueError("v3_audit_summary_mismatch")
                self.audit_value = snapshot
                self.audit_fragments = []
                return {
                    "validated": len(samples),
                    "supervisor_anchor_sha256": digest(snapshot),
                    "audit_only": True,
                }
            if action == "calibration_export":
                from benchmark_observation import validate_calibration
                from benchmark_plan import digest

                snapshot = self.audit_value
                inventory = {
                    receipt["ordinal"]: receipt for receipt in snapshot["receipts"]
                }
                phases = {
                    phase: [
                        {
                            "episode_id": inventory[ordinal]["episode_id"],
                            "receipt_sha256": digest(inventory[ordinal]),
                        }
                        for ordinal in ordinals
                    ]
                    for phase, ordinals in args["phase_ordinals"].items()
                }
                envelope = {
                    "root": self.path(snapshot["root"]),
                    "receipts": snapshot["receipts"],
                    "attempts": snapshot["attempts"],
                    "phases": phases,
                }
                result = validate_calibration(
                    envelope,
                    args["lifecycle"],
                    snapshot["context"],
                    method="wddm_auto_v3",
                    trusted_receipts=snapshot["receipts"],
                    trusted_attempts=snapshot["attempts"],
                )
                folder = self.path(args["folder"])
                originals = {}
                for name, value in {
                    **phases,
                    "lifecycle": args["lifecycle"],
                    "publications": {
                        "root": self.path(snapshot["root"])
                        .relative_to(self.root)
                        .as_posix(),
                        "receipts": snapshot["receipts"],
                        "attempts": snapshot["attempts"],
                    },
                }.items():
                    path = folder / (name + ".json")
                    exclusive_json(path, value)
                    originals[name] = path.relative_to(self.root).as_posix()
                return {
                    "calibration": result,
                    "originals": originals,
                    "receipt_count": len(snapshot["receipts"]),
                    "attempt_count": len(snapshot["attempts"]),
                }
            if action == "accreditation":
                from benchmark_observation import build_auto_prerequisites

                snapshot = self.audit_value
                return build_auto_prerequisites(
                    self.plan,
                    snapshot["context"],
                    args["originals"],
                    args["viewport_path"],
                    root=self.root,
                    exclusive_gpu_authorized=args["exclusive_gpu_authorized"],
                    trusted_receipts=snapshot["receipts"],
                    trusted_attempts=snapshot["attempts"],
                )
            if action == "refresh_accreditation":
                from benchmark_observation import validate_auto

                snapshot = self.audit_value
                observation = dict(
                    read_json(self.path(args["observation_path"]))["observation"]
                )
                observation["evidence"] = dict(observation["evidence"])
                publication = {
                    "root": self.path(snapshot["root"])
                    .relative_to(self.root)
                    .as_posix(),
                    "receipts": snapshot["receipts"],
                    "attempts": snapshot["attempts"],
                }
                path = self.path(args["path"])
                seal = exclusive_json(path, publication)
                observation["evidence"]["publications"] = {
                    **seal,
                    "path": path.relative_to(self.root).as_posix(),
                }
                result = validate_auto(
                    observation,
                    self.root,
                    plan=self.plan,
                    continued_samples=snapshot["receipts"],
                    trusted_receipts=snapshot["receipts"],
                    trusted_attempts=snapshot["attempts"],
                )
                return {"observation": observation, "accreditation": result}
            if action == "row":
                from benchmark_runner import summarize_run, verify_outputs

                snapshot = self.audit_value
                records = [
                    {
                        "supervisor_receipt": r["supervisor_receipt"],
                        "sample": r["sample"],
                    }
                    for r in snapshot["records"]
                ]
                selected = [
                    record
                    for record in records
                    if args["first_ordinal"]
                    <= record["supervisor_receipt"]["ordinal"]
                    <= args["last_ordinal"]
                ]
                baseline = [
                    record
                    for record in records
                    if record["supervisor_receipt"]["ordinal"]
                    in args["baseline_ordinals"]
                ]
                folder = self.path(args["folder"])
                terminal = read_json(folder / "terminal.json")
                request = read_json(folder / "request.json")
                estimate = read_json(folder / "estimate.json")
                valid, fidelity, output = verify_outputs(
                    self.root,
                    request,
                    terminal,
                    config=args["config"],
                    resource_root=args["resource_root"],
                    estimate=estimate,
                )
                row = summarize_run(
                    args["run"],
                    terminal,
                    selected,
                    baseline,
                    output_valid=valid,
                    fidelity_valid=fidelity,
                    observation_context=snapshot["context"],
                    v3_evidence={
                        "records": records,
                        "publication_root": snapshot["root"],
                        "trusted_receipts": snapshot["receipts"],
                        "attempts": snapshot["attempts"],
                        "trusted_attempts": snapshot["attempts"],
                    },
                )
                row.update(output)
                row.update(args["storage_fields"])
                if (
                    args["config"]["config_id"] == "xl-turbo-lm06-int8"
                    and row.get("error_code") == "VRAM_EXCEEDED"
                ):
                    cap = (
                        self.api.request("GET", "/v1/health", timeout=5)
                        .get("gpu", {})
                        .get("cap_mb")
                    )
                    if type(cap) in {int, float} and cap > 0:
                        from benchmark_plan import file_hash

                        row.update(
                            status="hardware_not_feasible",
                            vram_cap_mb=cap,
                            hardware_evidence_sha256=file_hash(
                                folder / "terminal.json"
                            ),
                        )
                exclusive_json(folder / "row.json", row)
                exclusive_json(folder / "seal.json", seal_files(folder))
                return row
            raise ValueError("v3_unknown_owned_operation")
        except ApiError as error:
            return {"api_error": error.code, "status": error.status}

    def close(self):
        # El cierre no recrea el runtime ni repite operaciones.
        pass


def recover_owned_runtime(
    config, active_group, before, *, release_lease=False, runtime_factory=None
):
    """Recuperación de ownership fuera de la cadena aceptada si falló el sampler.

    Inspección obligatoria por nombre, labels e imagen; conserva create y POST.
    La intención queda en cuarentena si no se puede reconciliar el daemon.
    """
    from benchmark_process import OwnedProcess

    result = {
        "kind": "ownership_recovery_not_observation_acceptance",
        "remote_request_cancelled": False,
        "uncertain": True,
        "disposition": "unknown_quarantined",
        "reservation_retained": release_lease,
    }
    intent_path = config.get("lease_intent_path")
    if intent_path and not config.get("lease_acknowledged", False):
        result["reservation_retained"] = False
        try:
            intent = json.loads(Path(intent_path).read_text(encoding="utf-8"))
            owner = json.loads(Path(config["owner_path"]).read_text(encoding="utf-8"))
            if any(
                intent.get(k) != owner[k]
                for k in ("session_id", "owner", "plan_sha256")
            ):
                raise ValueError("gpu_lease_intent_owner_invalid")
            lease = GpuLease(
                config.get(
                    "lease_path", Path(config["root"]) / ".cache/dev-cycle/t09/gpu.lock"
                ),
                owner,
                holder_pid=intent["pid"],
            )
            result["lease_intent"] = intent
            if lease.path.exists():
                saved = json.loads(lease.path.read_text(encoding="utf-8"))
                if any(
                    saved.get(k) != owner[k]
                    for k in ("session_id", "owner", "plan_sha256")
                ):
                    result["reservation_state"] = "foreign_untouched"
                elif saved.get("pid") != intent["pid"] or any(
                    saved.get(k) is not None and saved[k] != intent[k]
                    for k in ("creation_time", "nonce")
                ):
                    result["reservation_state"] = "identity_unknown_untouched"
                else:
                    result["reservation_retained"] = True
                    lease.quarantine()
                    result["quarantine_reserved"] = True
                    result["reservation_state"] = "owned_ack_unknown"
            else:
                result["reservation_state"] = "absent_at_recovery"
        except (OSError, ValueError, KeyError, TypeError) as error:
            result["quarantine_error"] = str(error)
        # No capacity acquisition or release is permitted by this uncertain ACK.
        # Still attempt the existing resource reconciliation only when needed.
        if active_group is None and before is None:
            result["action"] = "quarantine_intent_reconcile_owned_identity_no_replay"
            return result
        release_lease = False

    worker = None
    try:
        worker = (
            runtime_factory(config)
            if runtime_factory
            else OwnedProcess(config, "benchmark_runtime:BenchmarkOperationProvider")
        )

        def call(action, args, seconds=12):
            value = worker.call(
                {"operation": action, "arguments": args},
                deadline_ns=time.perf_counter_ns() + int(seconds * 1e9),
            )["value"]
            if isinstance(value, dict) and "api_error" in value:
                raise ApiError(value["api_error"], value.get("status"))
            return value

        if active_group is not None:
            result["recovered_receipt"] = call("recover", active_group)
            result["cleanup"] = call("terminate_owned", {})
            if result["cleanup"].get("removed") is not True:
                raise ValueError("v3_owned_cleanup_not_verified")
        result["disposition"] = "removed"
        if before is not None:
            result["restore"] = call("ollama_restore", {"state": before}, 120)
        if release_lease:
            result["lease"] = call("lease_release", {})
            result["reservation_retained"] = False
        result["uncertain"] = False
    except (OSError, ValueError, RuntimeError, KeyError, TypeError) as error:
        result["error"] = str(error)
        result["action"] = "quarantine_intent_reconcile_owned_identity_no_replay"
    finally:
        if result["reservation_retained"] and config.get("owner_path"):
            try:
                owner = json.loads(
                    Path(config["owner_path"]).read_text(encoding="utf-8")
                )
                lease = GpuLease(
                    Path(
                        config.get(
                            "lease_path",
                            Path(config["root"]) / ".cache/dev-cycle/t09/gpu.lock",
                        )
                    ),
                    owner,
                    holder_pid=config.get("supervisor_pid"),
                )
                lease.quarantine()
                result["quarantine_reserved"] = True
            except (OSError, ValueError, KeyError, TypeError) as error:
                result["quarantine_error"] = str(error)
        if worker is not None:
            try:
                worker.close()
                result["worker_cleanup"] = worker.close_evidence
            except (OSError, RuntimeError, ValueError) as error:
                result["worker_cleanup_error"] = str(error)
    return result
