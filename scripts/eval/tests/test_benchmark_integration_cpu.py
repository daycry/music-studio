"""Le lot completo con dobles CPU: prueba orchestration, no rendimiento GPU."""

import json

import pytest


def prepared_plan(planner, root):
    (root / "models").mkdir(parents=True)
    (root / "models/models.lock.json").write_text('{"models": {}}')
    (root / "data/tmp").mkdir(parents=True)
    fixtures = {}
    for duration in planner.DURATIONS:
        path = root / f"fixture-{duration}.json"
        path.write_text(
            json.dumps(
                {
                    "task": "music.song",
                    "authorship": {"declared": True, "basis": "original"},
                    "params": {
                        "lyrics": "fixture CPU",
                        "style": "test",
                        "language": "es",
                        "duration_s": duration,
                    },
                }
            )
        )
        fixtures[str(duration)] = {"path": path.name, "sha256": planner.file_hash(path)}
    plan = planner.build_plan(
        {"fixtures_by_duration": fixtures},
        image_id="sha256:image",
        prerequisites_sha256="manual",
        observation_method="task_manager_v1",
        root=root,
    )
    plan["observer_policy"]["interval_s"] = 0
    plan["plan_sha256"] = planner.digest(
        {k: v for k, v in plan.items() if k != "plan_sha256"}
    )
    return plan


@pytest.mark.parametrize("start_failure", [False, True])
def test_full_160_error_attempts_keep_rows_and_cleanup_without_reuse(
    harness_module, tmp_path, monkeypatch, start_failure
):
    planner = harness_module("benchmark_plan")
    cli = harness_module("benchmark")
    evidence = harness_module("benchmark_evidence")
    plan = prepared_plan(planner, tmp_path)
    planner.verify_plan(plan, tmp_path)
    folder = tmp_path / ".cache/session"
    folder.mkdir(parents=True)
    calls = []
    api_by_port = {}

    class Sensor:
        def nvidia(self):
            return {"name": "NVIDIA GeForce RTX 5070", "used_mb": 1300}

        def sample(self):
            return {
                "errors": [],
                "browser": {"visible": True},
                "nvml": self.nvidia(),
                "windows": {"shared_mb": 100, "gpu_mapping_status": "resolved"},
                "wsl": {"mem_available_mb": 12000, "swap_used_mb": 0},
            }

    class Api:
        def __init__(self, port, token):
            api_by_port[port] = self
            self.jobs = {}

        def request(self, method, path, body=None):
            calls.append((method, path))
            if path == "/v1/health":
                return {
                    "state": "idle",
                    "job_id": None,
                    "loaded": None,
                    "gpu": {"cap_mb": 10000},
                }
            if path == "/v1/estimate":
                assert (
                    body["seed"] == 1
                    and body["n_outputs"] == 1
                    and body["timeout_s"] == 3600
                )
                return {"input_budget": {"effective_sha256": "test"}}
            if path == "/v1/jobs":
                assert body["job_id"] not in self.jobs
                self.jobs[body["job_id"]] = body
                return {"job_id": body["job_id"]}
            return {}

        def events(self, job, after, **kwargs):
            return [
                {
                    "job_id": job,
                    "seq": 1,
                    "type": "error",
                    "data": {"code": "VRAM_EXCEEDED"},
                }
            ]

    class Backend:
        def create(self, plan, config, storage, owner, port, token):
            resource = (
                "/models"
                if storage == "bind"
                else f"/studio/.cache/benchmark/{plan['session_id']}/models"
            )
            evidence.exclusive_json(
                tmp_path / "data/tmp" / f"t09-storage-{config['group_id']}.json",
                {
                    "resource_root": resource,
                    "destination_lock_sha256": plan["lock_sha256"],
                    "source_lock_sha256": plan["lock_sha256"],
                    "copy_s": 3 if storage == "container_copy" else 0,
                },
            )
            return {
                "container_id": planner.new_id(),
                "session_id": plan["session_id"],
                "plan_sha256": plan["plan_sha256"],
                "owner": owner,
                "port": port,
                "config_id": config["config_id"],
                "storage": storage,
            }

        def start(self, receipt):
            if start_failure:
                raise ValueError("start_acknowledgement_lost")
            calls.append(("start", receipt["container_id"]))

        def verify_image_sources(self, receipt, plan):
            calls.append(("sources", receipt["container_id"]))

        def cleanup(self, receipt, api):
            calls.append(("cleanup", receipt["container_id"]))
            return {"unloaded": True, "removed": True}

    class Ollama:
        def snapshot(self):
            return {"models": []}

        def discharge(self, state):
            calls.append(("discharge", "empty"))

        def restore(self, state):
            calls.append(("restore", "empty"))
            return {"restored": True}

    original = cli.observed_baseline
    monkeypatch.setattr(
        cli,
        "observed_baseline",
        lambda sensors, folder: original(
            sensors, folder, interval=0, sleep=lambda seconds: None
        ),
    )
    if start_failure:
        with pytest.raises(ValueError, match="start_acknowledgement_lost"):
            cli.run_session(
                plan,
                folder,
                {"browser": {}},
                root=tmp_path,
                backend=Backend(),
                observer_factory=lambda windows: Sensor(),
                api_factory=Api,
                ollama=Ollama(),
                token="CPU-private",
            )
        assert (tmp_path / ".cache/dev-cycle/t09/gpu.lock").exists()
        assert list(folder.glob("resume-required-*.json"))
        assert not any(method == "restore" for method, _ in calls)
        return
    rows = cli.run_session(
        plan,
        folder,
        {"browser": {}},
        root=tmp_path,
        backend=Backend(),
        observer_factory=lambda windows: Sensor(),
        api_factory=Api,
        ollama=Ollama(),
        token="CPU-private",
    )
    assert len(rows) == 160 and len({row["job_id"] for row in rows}) == 160
    assert sum(method == "POST" and path == "/v1/jobs" for method, path in calls) == 160
    assert sum(method == "cleanup" for method, _ in calls) == 40
    assert sum(row["status"] == "hardware_not_feasible" for row in rows) == 32
    assert all(row["inference_s"] is None for row in rows)
    assert evidence.complete_matrix(plan, rows) is False
    assert "pendiente" in evidence.recommendations(plan, rows)
    assert not (tmp_path / ".cache/dev-cycle/t09/gpu.lock").exists()
    # Replay completions from immutable seals without resubmitting or fresh containers.
    calls.clear()
    replay = cli.run_session(
        plan,
        folder,
        {"browser": {}},
        root=tmp_path,
        backend=Backend(),
        observer_factory=lambda windows: Sensor(),
        api_factory=Api,
        ollama=Ollama(),
        token="CPU-private",
        resume=True,
    )
    assert replay == rows
    assert not any(path == "/v1/jobs" for _, path in calls)


def test_plan_and_seals_detect_mutation(harness_module, tmp_path):
    planner = harness_module("benchmark_plan")
    evidence = harness_module("benchmark_evidence")
    plan = prepared_plan(planner, tmp_path)
    path = tmp_path / "evidence.json"
    evidence.exclusive_json(path, {"event": "real"})
    seal = evidence.seal_files(tmp_path)
    evidence.validate_seal(tmp_path, seal)
    path.write_text("altered")
    with pytest.raises(ValueError, match="evidence_changed"):
        evidence.validate_seal(tmp_path, seal)
    plan["seed"] = 2
    with pytest.raises(ValueError, match="plan_or_lock_changed"):
        planner.verify_plan(plan, tmp_path)


def test_reference_and_recommendation_require_all_rows_and_valid_sensors(
    harness_module,
):
    planner = harness_module("benchmark_plan")
    evidence = harness_module("benchmark_evidence")
    plan = {
        "runs": planner.matrix_runs(),
        "configs": planner.configurations(),
        "durations_s": list(planner.DURATIONS),
    }
    rows = [
        {
            **r,
            "valid": True,
            "status": "done",
            "rtf": 0.1 + r["repetition"] * 0.01,
            "shared_gpu_observed": False,
            "fixture_sha256": str(r["duration_s"]),
            "load_s": 31 if r["storage"] == "bind" else 0,
            "vram_peak_mb": 7000,
        }
        for r in plan["runs"]
    ]
    enriched = evidence.enrich_rows(rows)
    assert evidence.complete_matrix(plan, rows)
    recommendation = evidence.recommendations(plan, enriched)
    assert (
        "Default operativo" in recommendation
        and "sft-lm06" in recommendation
        and "pendiente de escucha" in recommendation
    )
    assert "requiere ADR" in evidence.render_report({**plan, "session_id": "CPU"}, rows)
    rows[0]["valid"] = False
    assert "pendiente" in evidence.recommendations(plan, evidence.enrich_rows(rows))


@pytest.mark.parametrize("failure_stage", ["before_post", "after_post", "after_rows"])
def test_cleanup_error_receipt_and_resume_never_inspect_dead_container_or_duplicate(
    harness_module, tmp_path, monkeypatch, failure_stage
):
    planner = harness_module("benchmark_plan")
    cli = harness_module("benchmark")
    runtime = harness_module("benchmark_runtime")
    plan = prepared_plan(planner, tmp_path)
    plan["runs"] = plan["runs"][:4]
    folder = tmp_path / ".cache/session"
    folder.mkdir(parents=True)
    created = []
    removed = set()
    submitted = []
    first = [True]
    health_calls = [0]

    class Sensors:
        def nvidia(self):
            return {"name": "NVIDIA GeForce RTX 5070", "used_mb": 1300}

        def sample(self):
            return {
                "errors": [],
                "browser": {"visible": True},
                "nvml": self.nvidia(),
                "windows": {"shared_mb": 0, "gpu_mapping_status": "resolved"},
                "wsl": {"mem_available_mb": 12000, "swap_used_mb": 0},
            }

    class Backend:
        def create(self, plan, config, storage, owner, port, token):
            receipt = {
                "container_id": planner.new_id(),
                "session_id": plan["session_id"],
                "plan_sha256": plan["plan_sha256"],
                "owner": owner,
                "port": port,
            }
            created.append(receipt)
            (
                tmp_path / "data/tmp" / f"t09-storage-{config['group_id']}.json"
            ).write_text(
                json.dumps(
                    {
                        "resource_root": "/models",
                        "source_lock_sha256": plan["lock_sha256"],
                        "destination_lock_sha256": plan["lock_sha256"],
                        "copy_s": 0,
                    }
                )
            )
            return receipt

        def start(self, receipt):
            pass

        def inspect(self, identity):
            assert identity not in removed, "resume inspected removed container"
            receipt = next(r for r in created if r["container_id"] == identity)
            return {
                "Id": identity,
                "Image": plan["image_id"],
                "Config": {
                    "Labels": {
                        "studio.t09.session": receipt["session_id"],
                        "studio.t09.plan": receipt["plan_sha256"],
                        "studio.t09.owner": receipt["owner"],
                    }
                },
            }

        def verify_image_sources(self, *args):
            pass

        def cleanup(self, receipt, api):
            removed.add(receipt["container_id"])
            return {
                "container_id": receipt["container_id"],
                "unloaded": True,
                "removed": True,
            }

    class Api:
        def __init__(self, *args):
            pass

        def request(self, method, path, body=None):
            if path == "/v1/health":
                return {"state": "idle", "job_id": None, "loaded": None}
            if path == "/v1/estimate":
                return {"input_budget": {}}
            if path == "/v1/jobs":
                submitted.append(body["job_id"])
                if failure_stage == "after_post" and first[0]:
                    first[0] = False
                    raise runtime.ApiError("TRANSPORT_UNAVAILABLE")
                return {"job_id": body["job_id"]}
            return {"job_id": path.rsplit("/", 1)[-1], "state": "cancelled"}

        def events(self, job, after, **kwargs):
            return (
                [{"seq": 1, "job_id": job, "type": "cancelled", "data": {}}]
                if after == 0
                else []
            )

    class Ollama:
        def snapshot(self):
            return {"models": []}

        def discharge(self, state):
            pass

        def restore(self, state):
            return {"restored": True}

    def health(*args, **kwargs):
        health_calls[0] += 1
        if failure_stage == "after_rows" and health_calls[0] == 2:
            raise runtime.ApiError("TRANSPORT_UNAVAILABLE")
        if failure_stage == "before_post" and first[0]:
            first[0] = False
            raise runtime.ApiError("TRANSPORT_UNAVAILABLE")
        return {"state": "idle", "loaded": None}

    monkeypatch.setattr(cli, "wait_health", health)
    original = cli.observed_baseline
    monkeypatch.setattr(
        cli,
        "observed_baseline",
        lambda sensors, path: original(sensors, path, interval=0, sleep=lambda _: None),
    )
    kwargs = {
        "root": tmp_path,
        "backend": Backend(),
        "observer_factory": lambda _: Sensors(),
        "api_factory": Api,
        "ollama": Ollama(),
        "token": "CPU",
    }
    with pytest.raises(runtime.ApiError, match="TRANSPORT_UNAVAILABLE"):
        cli.run_session(plan, folder, {"browser": {}}, **kwargs)
    cleanup = list(folder.glob("groups/**/cleanup-after-error-*.json"))
    assert cleanup, "durable cleanup receipt missing"
    assert json.loads(cleanup[0].read_text())["removed"] is True
    if failure_stage == "before_post":
        rows = cli.run_session(plan, folder, {"browser": {}}, resume=True, **kwargs)
        assert len(rows) == 4 and len(created) == 2
        assert len(set(submitted)) == 4
        assert not set(submitted) & {r["job_id"] for r in plan["runs"]}
        assert all(row["actual_job_id"] in submitted for row in rows)
    elif failure_stage == "after_rows":
        rows = cli.run_session(plan, folder, {"browser": {}}, resume=True, **kwargs)
        assert len(rows) == 4 and len(created) == 1 and len(submitted) == 4
    else:
        with pytest.raises(
            ValueError, match="removed_container_has_submitted_job_requires_inspection"
        ):
            cli.run_session(plan, folder, {"browser": {}}, resume=True, **kwargs)
        assert len(submitted) == 1 and len(created) == 1
