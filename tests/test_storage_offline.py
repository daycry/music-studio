import importlib.util
import sys
from pathlib import Path

import pytest


def storage_offline():
    path = Path(__file__).parents[1] / "scripts/storage_offline.py"
    spec = importlib.util.spec_from_file_location("studio_storage_offline", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_plan_is_confined_and_never_targets_final_disk(tmp_path):
    module = storage_offline()
    plan = module.plan(
        tmp_path,
        size_bytes=64 * 1024 * 1024,
        operation_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        filesystem_uuid="12345678-1234-5678-1234-567812345678",
        image="storage-tools:test",
    )

    assert (
        plan.workspace
        == tmp_path / ".cache/dev-cycle/storage-01ARZ3NDEKTSV4RRFFQ69G5FAV"
    )
    assert plan.raw_path.parent == plan.workspace
    assert plan.vhdx_path.parent == plan.workspace
    assert plan.final_path == tmp_path / "data/_storage/studio-data.vhdx"
    assert all(
        str(plan.final_path) not in " ".join(command) for command in plan.commands
    )
    assert [command[-1] for command in plan.commands[:2]] == [
        "/work/raw.ext4",
        "/work/raw.ext4",
    ]
    assert "-n" in plan.commands[3]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"size_bytes": 0},
        {"size_bytes": 64, "operation_id": "bad"},
        {"size_bytes": 64, "filesystem_uuid": "bad"},
        {"size_bytes": 64, "image": ""},
    ],
)
def test_plan_rejects_invalid_inputs(tmp_path, kwargs):
    module = storage_offline()
    with pytest.raises(ValueError):
        module.plan(tmp_path, image=kwargs.pop("image", "storage-tools:test"), **kwargs)


def test_plan_refuses_existing_reservation_or_final_disk(tmp_path):
    module = storage_offline()
    workspace = tmp_path / ".cache/dev-cycle/storage-01ARZ3NDEKTSV4RRFFQ69G5FAV"
    workspace.mkdir(parents=True)
    with pytest.raises(ValueError, match="reserva"):
        module.plan(
            tmp_path,
            size_bytes=64,
            operation_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
            filesystem_uuid="12345678-1234-5678-1234-567812345678",
            image="storage-tools:test",
        )

    other = tmp_path / "other"
    other.mkdir()
    (other / "data/_storage").mkdir(parents=True)
    (other / "data/_storage/studio-data.vhdx").write_bytes(b"foreign")
    with pytest.raises(ValueError, match="final"):
        module.plan(
            other,
            size_bytes=64,
            operation_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
            filesystem_uuid="12345678-1234-5678-1234-567812345678",
            image="storage-tools:test",
        )


def test_execute_keeps_reservation_and_records_verified_phases(tmp_path):
    module = storage_offline()
    plan = module.plan(
        tmp_path,
        size_bytes=64,
        operation_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        filesystem_uuid="12345678-1234-5678-1234-567812345678",
        image="storage-tools:test",
    )
    calls = []

    def runner(command, **kwargs):
        calls.append(command)
        if (
            any(value.endswith("/qemu-img") for value in command)
            and "create" in command
        ):
            plan.vhdx_path.write_bytes(b"VHDX")

    receipt = module.execute(plan, runner=runner)
    assert receipt.phase == "vhdx_verified"
    assert len(calls) == 5
    assert (plan.workspace / "receipt.json").exists()
    assert not plan.final_path.exists()


def test_execute_preserves_partial_reservation_after_tool_failure(tmp_path):
    module = storage_offline()
    plan = module.plan(
        tmp_path,
        size_bytes=64,
        operation_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        filesystem_uuid="12345678-1234-5678-1234-567812345678",
        image="storage-tools:test",
    )

    def runner(command, **kwargs):
        raise RuntimeError("tool failed")

    with pytest.raises(RuntimeError, match="tool failed"):
        module.execute(plan, runner=runner)
    assert plan.workspace.exists()
    assert plan.raw_path.exists()
    assert not (plan.workspace / "receipt.json").exists()
