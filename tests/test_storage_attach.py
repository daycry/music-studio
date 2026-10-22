"""Tests for the fail-closed WSL VHDX attach operator."""

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from studio_storage_guard.receipt import StorageReceipt

from scripts import storage_attach, storage_operator
from scripts.storage_attach import AttachError, execute, parse_lsblk, plan
from scripts.storage_windows import CustodyError


def _lsblk(*rows):
    return json.dumps(
        {
            "blockdevices": [
                dict(zip(("name", "fstype", "uuid", "mountpoint"), row, strict=True))
                for row in rows
            ]
        }
    )


def test_parse_real_lsblk_json_with_null_and_swap():
    # Shape observed with: wsl.exe -d Ubuntu -- lsblk --json --paths
    # --output NAME,FSTYPE,UUID,MOUNTPOINT (read-only, 2026-10-10).
    output = """{"blockdevices": [
        {"name": "/dev/sda", "fstype": "ext4", "uuid": null, "mountpoint": null},
        {"name": "/dev/sdc", "fstype": "swap",
         "uuid": "887040b9-64f9-4359-a59c-407823ff1bea", "mountpoint": "[SWAP]"},
        {"name": "/dev/sdf", "fstype": "ext4",
         "uuid": "f7dad7e8-8890-45a1-9e75-bc21dcb90e7b",
         "mountpoint": "/mnt/wslg/distro"}
    ]}"""
    records = parse_lsblk(output)
    assert set(records) == {"/dev/sda", "/dev/sdc", "/dev/sdf"}
    assert records["/dev/sda"].uuid == ""
    assert records["/dev/sda"].mountpoint == ""
    assert records["/dev/sdc"].fstype == "swap"
    assert records["/dev/sdc"].mountpoint == "[SWAP]"
    assert records["/dev/sdf"].mountpoint == "/mnt/wslg/distro"


def _receipt(tmp_path: Path) -> Path:
    final = tmp_path / "data" / "_storage" / "studio-data.vhdx"
    final.parent.mkdir(parents=True)
    final.write_bytes(b"VHDX")
    receipt = (
        StorageReceipt.reserve(
            project_root=tmp_path,
            operation_id="01ARZ3NDEKTSV4RRFFQ69G5FAV",
            size_bytes=4,
        )
        .advance(
            "raw_verified",
            {
                "raw_sha256": hashlib.sha256(b"raw").hexdigest(),
                "raw_size": 3,
                "uuid": "12345678-1234-5678-1234-567812345678",
            },
        )
        .advance(
            "vhdx_verified",
            {"vhdx_sha256": hashlib.sha256(b"VHDX").hexdigest(), "vhdx_size": 4},
        )
        .advance(
            "published",
            {"final_path": final.absolute().as_posix(), "file_id": "1:owned"},
        )
    )
    path = tmp_path / ".cache/dev-cycle/storage-01ARZ3NDEKTSV4RRFFQ69G5FAV/receipt.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(receipt.to_bytes())
    return path


def test_plan_requires_admin_without_commands(tmp_path):
    receipt = _receipt(tmp_path)
    result = plan(tmp_path, receipt, admin=False)
    assert result.status == "NEEDS_ADMIN"
    assert result.commands == ()


def test_plan_contains_vhd_bare_and_uuid_probe(tmp_path):
    receipt = _receipt(tmp_path)
    result = plan(tmp_path, receipt, admin=True)
    assert result.status == "READY_TO_ATTACH"
    assert result.filesystem_uuid == "12345678-1234-5678-1234-567812345678"
    assert result.commands[0][:4] == (
        "wsl.exe",
        "--mount",
        str(result.final_path),
        "--vhd",
    )
    assert result.commands[0][-1] == "--bare"
    assert "lsblk" in result.commands[1]
    assert result.commands[1][-5:] == (
        "lsblk",
        "--json",
        "--paths",
        "--output",
        "NAME,FSTYPE,UUID,MOUNTPOINT",
    )


def test_parse_lsblk_requires_one_new_ext4_uuid():
    before = parse_lsblk(_lsblk(("/dev/sda", "ext4", "other", "/")))
    after = parse_lsblk(
        _lsblk(
            ("/dev/sda", "ext4", "other", "/"),
            ("/dev/sdb", "ext4", "12345678-1234-5678-1234-567812345678", None),
        )
    )
    assert after["/dev/sdb"].fstype == "ext4"
    assert "/dev/sdb" not in before


def test_execute_mounts_and_advances_receipt(tmp_path, cpu_authority):
    receipt = _receipt(tmp_path)
    attach = plan(tmp_path, receipt, admin=True)
    calls = []
    outputs = {
        "lsblk-before": _lsblk(("/dev/sda", "ext4", "other", "/")),
        "lsblk-after": _lsblk(
            ("/dev/sda", "ext4", "other", "/"),
            ("/dev/sdb", "ext4", "12345678-1234-5678-1234-567812345678", None),
        ),
        "findmnt": "/dev/sdb ext4 rw /\n",
        "blkid": "12345678-1234-5678-1234-567812345678\n",
    }

    def runner(argv, **kwargs):
        calls.append(tuple(argv))
        text = ""
        if "lsblk" in argv:
            text = outputs[
                "lsblk-before"
                if len([c for c in calls if "lsblk" in c]) == 1
                else "lsblk-after"
            ]
        elif "findmnt" in argv:
            text = outputs["findmnt"]
        elif "blkid" in argv:
            text = outputs["blkid"]
        return subprocess.CompletedProcess(argv, 0, text, "")

    result = execute(attach, runner=runner)
    assert result.phase == "attached"
    assert result.history[-1]["evidence"] == {
        "device": "/dev/sdb",
        "mountpoint": "/mnt/studio-data",
    }
    assert any("--mount" in c for c in calls)
    assert (receipt).read_bytes() == result.to_bytes()


def test_execute_unmounts_on_mount_validation_failure(tmp_path, cpu_authority):
    receipt = _receipt(tmp_path)
    attach = plan(tmp_path, receipt, admin=True)
    calls = []

    def runner(argv, **kwargs):
        calls.append(tuple(argv))
        if "lsblk" in argv:
            text = (
                _lsblk(("/dev/sda", "ext4", "other", "/"))
                if len(calls) == 1
                else _lsblk(
                    ("/dev/sda", "ext4", "other", "/"),
                    ("/dev/sdb", "ext4", "12345678-1234-5678-1234-567812345678", None),
                )
            )
        elif "findmnt" in argv:
            text = "/dev/sdb ext4 ro /\n"
        elif "blkid" in argv:
            text = attach.filesystem_uuid
        else:
            text = ""
        return subprocess.CompletedProcess(argv, 0, text, "")

    with pytest.raises(AttachError, match="rw"):
        execute(attach, runner=runner)
    assert any(c[:3] == ("wsl.exe", "-d", "Ubuntu") and "umount" in c for c in calls)
    assert any(c[:2] == ("wsl.exe", "--unmount") for c in calls)


def test_plan_rejects_receipt_outside_project(tmp_path):
    outside = tmp_path.parent / "foreign-receipt.json"
    outside.write_bytes(b"{}")
    with pytest.raises(ValueError, match="fuera del proyecto"):
        plan(tmp_path, outside, admin=False)


def test_parse_lsblk_recurses_partitions_and_null_filesystem():
    child = {
        "name": "/dev/sdb1",
        "fstype": "ext4",
        "uuid": "expected",
        "mountpoint": None,
    }
    tree = {
        "blockdevices": [
            {
                "name": "/dev/sdb",
                "fstype": None,
                "uuid": None,
                "mountpoint": None,
                "children": [child],
            }
        ]
    }
    records = parse_lsblk(json.dumps(tree))
    assert records["/dev/sdb"] == storage_attach.BlockRecord("", "", "")
    assert records["/dev/sdb1"] == storage_attach.BlockRecord("ext4", "expected", "")
    assert storage_attach._select_device({}, records, "expected") == "/dev/sdb1"
    assert parse_lsblk('{"blockdevices": []}') == {}


@pytest.mark.parametrize(
    "output",
    [
        "",
        "/dev/sda ext4 other /\n",
        "/dev/sda|ext4|other|/\n",
        "{",
        "null",
        "[]",
        '{"blockdevices": null}',
        '{"blockdevices": [], "extra": true}',
        '{"blockdevices": [], "blockdevices": []}',
        '{"blockdevices": [null]}',
        '{"blockdevices": [{}]}',
        _lsblk((None, "ext4", "id", None)),
        _lsblk(("/dev/sd a", "ext4", "id", None)),
        _lsblk(("sda", "ext4", "id", None)),
        _lsblk(("/dev/../sda", "ext4", "id", None)),
        _lsblk(("/dev/sda", 3, "id", None)),
        _lsblk(("/dev/sda", "ext4", [], None)),
        _lsblk(("/dev/sda", "ext4", "id", False)),
        _lsblk(("/dev/sda", "ext 4", "id", None)),
        _lsblk(("/dev/sda", "ext4", "id other", None)),
        _lsblk(("/dev/sda", "ext4", "id", "/mnt/has space")),
        _lsblk(("/dev/sda", "ext4", "id", "/mnt/../other")),
        _lsblk(("/dev/sda", "ext4", "id", "/mnt//other")),
        _lsblk(("/dev/sda", "ext4", "id", "[SWAP]")),
        _lsblk(("/dev/sda", "ext4", "id", None), ("/dev/sda", "ext4", "id", None)),
        '{"blockdevices": [{"name":"/dev/sda","fstype":null,"uuid":null,"mountpoint":null,"children":null}]}',
        '{"blockdevices": [{"name":"/dev/sda","fstype":null,"uuid":null,"mountpoint":null,"unexpected":1}]}',
        '{"blockdevices": [{"name":"/dev/sda","name":"/dev/sdb","fstype":null,"uuid":null,"mountpoint":null}]}',
    ],
)
def test_parse_lsblk_rejects_malformed_ambiguous_fields(output):
    with pytest.raises(AttachError):
        parse_lsblk(output)


@pytest.mark.parametrize(
    "rows",
    [
        [("/dev/sda", "ext4", "expected", None)],  # pre-existing, never adopted
        [("/dev/sdb", "ext4", "wrong", None)],
        [("/dev/sdb", "xfs", "expected", None)],
        [("/dev/sdb", "ext4", "expected", "/mnt/foreign")],
        [
            ("/dev/sdb", "ext4", "expected", None),
            ("/dev/sdc", "ext4", "expected", None),
        ],
    ],
)
def test_select_device_rejects_foreign_or_multiple_candidates(rows):
    before = parse_lsblk(_lsblk(("/dev/sda", "ext4", "expected", None)))
    after = parse_lsblk(_lsblk(*rows))
    with pytest.raises(AttachError, match="ambiguo o ausente"):
        storage_attach._select_device(before, after, "expected")


@pytest.mark.parametrize(
    "failure", ["before", "after", "ambiguous", "mount", "blkid", "receipt"]
)
def test_execute_failure_preserves_receipt_and_rolls_back_own_attach(
    tmp_path, failure, cpu_authority
):
    receipt = _receipt(tmp_path)
    original = receipt.read_bytes()
    attach = plan(tmp_path, receipt, admin=True)
    calls = []

    def runner(argv, **kwargs):
        calls.append(tuple(argv))
        text = ""
        if "lsblk" in argv:
            probe = sum("lsblk" in c for c in calls)
            if failure == ("before" if probe == 1 else "after"):
                text = "malformed"
            elif probe == 1:
                text = _lsblk(("/dev/sda", "ext4", "foreign", "/"))
            else:
                rows = [
                    ("/dev/sda", "ext4", "foreign", "/"),
                    ("/dev/sdb", "ext4", attach.filesystem_uuid, None),
                ]
                if failure == "ambiguous":
                    rows.append(("/dev/sdc", "ext4", attach.filesystem_uuid, None))
                text = _lsblk(*rows)
        elif "mount" in argv and failure == "mount":
            raise subprocess.CalledProcessError(1, argv)
        elif "findmnt" in argv:
            text = "/dev/sdb ext4 rw /\n"
        elif "blkid" in argv:
            text = (
                "wrong"
                if failure == "blkid" and sum("blkid" in c for c in calls) == 1
                else attach.filesystem_uuid
            )
            if failure == "receipt":
                changed = StorageReceipt.from_bytes(original).advance(
                    "attached", {"device": "/dev/sdz", "mountpoint": "/mnt/elsewhere"}
                )
                receipt.write_bytes(changed.to_bytes())
        return subprocess.CompletedProcess(argv, 0, text, "")

    with pytest.raises(AttachError):
        execute(attach, runner=runner)
    assert not any("mkfs" in " ".join(c) or "--shutdown" in c for c in calls)
    assert any("--unmount" in c for c in calls) == (failure != "before")
    assert any("umount" in c for c in calls) == (failure in {"blkid", "receipt"})
    if failure in {"before", "after", "ambiguous"}:
        assert not any("mount" in c for c in calls)
    if failure != "receipt":
        assert receipt.read_bytes() == original


def test_execute_requires_ready_without_running_commands(tmp_path):
    attach = plan(tmp_path, _receipt(tmp_path), admin=False)
    calls = []
    with pytest.raises(AttachError, match="no listo"):
        execute(attach, runner=lambda *args, **kwargs: calls.append(args))
    assert calls == []


@pytest.mark.parametrize(
    "device,fstype,options,root",
    [
        ("/dev/foreign", "ext4", "rw", "/"),
        ("/dev/sdb", "xfs", "rw", "/"),
        ("/dev/sdb", "ext4", "rw,ro", "/"),
        ("/dev/sdb", "ext4", "rw", "/sub"),
    ],
)
def test_findmnt_rejects_unaccredited_mount(device, fstype, options, root):
    with pytest.raises(AttachError):
        storage_attach._findmnt(
            f"{device} {fstype} {options} {root}", "/dev/sdb", "/mnt/studio-data"
        )


def test_cli_keeps_admin_gate_and_dry_run(tmp_path, monkeypatch, capsys):
    receipt = _receipt(tmp_path)
    argv = ["--project", str(tmp_path), "--receipt", str(receipt)]
    assert storage_attach.main(argv) == 2
    assert "NEEDS_ADMIN" in capsys.readouterr().out
    assert storage_attach.main(argv + ["--admin-observed"]) == 0
    assert "--json" in capsys.readouterr().out
    monkeypatch.setattr(storage_attach, "_is_admin", lambda: False)
    assert storage_attach.main(argv + ["--admin-observed", "--execute"]) == 2
    assert "NEEDS_ADMIN" in capsys.readouterr().out
    monkeypatch.setattr(storage_attach, "_is_admin", lambda: True)

    def fail(_plan):
        raise AttachError("simulated failure")

    monkeypatch.setattr(storage_attach, "execute", fail)
    assert storage_attach.main(argv + ["--execute"]) == 2
    assert "NOT_READY" in capsys.readouterr().out


class FakeBinding:
    def __init__(self, trace, fail_at=None):
        self.trace, self.fail_at, self.count = trace, fail_at, 0
        self.closed = 0

    def revalidate(self):
        self.count += 1
        self.trace.append("revalidate")
        if self.count == self.fail_at:
            raise CustodyError("identity lost")

    def close(self):
        self.closed += 1
        self.trace.append("close")


@pytest.fixture
def cpu_authority(monkeypatch):
    monkeypatch.setattr(storage_attach, "_is_admin", lambda: True)
    monkeypatch.setattr(
        storage_operator.PublishedDiskBinding,
        "open",
        lambda root, receipt: FakeBinding([]),
    )


def _binding_scenario(tmp_path, monkeypatch, *, fail_at=None, mutate=None):
    receipt = _receipt(tmp_path)
    original = receipt.read_bytes()
    prepared = plan(tmp_path, receipt, admin=True)
    trace, calls = [], []
    lease = FakeBinding(trace, fail_at)

    def factory(root, received):
        assert isinstance(received, StorageReceipt)
        assert received.phase == "published"
        trace.append("open")
        return lease

    monkeypatch.setattr(storage_operator.PublishedDiskBinding, "open", factory)
    monkeypatch.setattr(storage_attach, "_is_admin", lambda: True)

    def runner(argv, **kwargs):
        calls.append(tuple(argv))
        trace.append("runner")
        if "lsblk" in argv:
            text = (
                _lsblk()
                if len(calls) == 1
                else _lsblk(("/dev/sdb", "ext4", prepared.filesystem_uuid, None))
            )
        elif "findmnt" in argv:
            text = "/dev/sdb ext4 rw /"
        elif "blkid" in argv:
            text = prepared.filesystem_uuid
            if mutate:
                payload = json.loads(original)
                mutate(payload)
                receipt.write_bytes(json.dumps(payload).encode())
        else:
            text = ""
        return subprocess.CompletedProcess(argv, 0, text, "")

    return prepared, receipt, original, lease, trace, calls, runner


def test_binding_rejects_identity_before_any_runner(tmp_path, monkeypatch):
    prepared, receipt, original, lease, _trace, calls, runner = _binding_scenario(
        tmp_path, monkeypatch, fail_at=1
    )
    with pytest.raises(AttachError, match="identity lost"):
        execute(prepared, runner=runner)
    assert calls == []
    assert receipt.read_bytes() == original
    assert lease.closed == 1


def test_binding_retained_and_checked_at_every_boundary(tmp_path, monkeypatch):
    prepared, _receipt_path, _original, lease, trace, _calls, runner = (
        _binding_scenario(tmp_path, monkeypatch)
    )
    execute(prepared, runner=runner)
    assert trace[0] == "open" and trace[-1] == "close"
    for index, event in enumerate(trace):
        if event == "runner":
            assert trace[index - 1] == trace[index + 1] == "revalidate"
    assert trace[-2] == "revalidate"
    assert lease.closed == 1


@pytest.mark.parametrize("fail_at", [3, 4, 9, 10])
def test_identity_loss_stops_effects_and_reports_uncertainty(
    tmp_path, monkeypatch, fail_at
):
    prepared, receipt, original, lease, _trace, calls, runner = _binding_scenario(
        tmp_path, monkeypatch, fail_at=fail_at
    )
    with pytest.raises(AttachError, match="identity lost") as captured:
        execute(prepared, runner=runner)
    assert not any("umount" in call or "--unmount" in call for call in calls)
    assert receipt.read_bytes() == original
    assert lease.closed == 1
    if fail_at in {4, 9, 10}:
        assert "incertidumbre" in str(captured.value)


@pytest.mark.parametrize("field", ["operation_id", "file_id", "uuid"])
def test_receipt_same_phase_replacement_is_preserved(tmp_path, monkeypatch, field):
    def mutate(payload):
        if field == "operation_id":
            payload[field] = "01ARZ3NDEKTSV4RRFFQ69G5FAW"
        elif field == "file_id":
            payload["history"][-1]["evidence"][field] = "2:foreign"
        else:
            payload["history"][1]["evidence"][field] = (
                "22345678-1234-5678-1234-567812345678"
            )

    prepared, receipt, original, lease, _trace, _calls, runner = _binding_scenario(
        tmp_path, monkeypatch, mutate=mutate
    )
    with pytest.raises(AttachError, match="recibo"):
        execute(prepared, runner=runner)
    assert receipt.read_bytes() != original
    assert json.loads(receipt.read_bytes())["phase"] == "published"
    assert lease.closed == 1


def test_execute_checks_real_admin_even_for_ready_plan(tmp_path, monkeypatch):
    prepared = plan(tmp_path, _receipt(tmp_path), admin=True)
    monkeypatch.setattr(storage_attach, "_is_admin", lambda: False)
    calls = []
    with pytest.raises(AttachError, match="NEEDS_ADMIN"):
        execute(
            prepared,
            runner=lambda *args, **kwargs: (
                calls.append(args),
                subprocess.CompletedProcess(args[0], 0, _lsblk(), ""),
            )[1],
        )
    assert calls == []


@pytest.mark.parametrize(
    "problem", ["foreign-source", "foreign-uuid", "cleanup-command", "close"]
)
def test_rollback_authority_and_cleanup_errors(tmp_path, monkeypatch, problem):
    prepared, receipt, original, lease, trace, calls, normal_runner = _binding_scenario(
        tmp_path, monkeypatch
    )
    probes = 0

    def runner(argv, **kwargs):
        nonlocal probes
        result = normal_runner(argv, **kwargs)
        if "findmnt" in argv:
            probes += 1
            if probes == 1:
                result.stdout = "/dev/sdb ext4 ro /"
            elif problem == "foreign-source":
                result.stdout = "/dev/foreign ext4 rw /"
        if "blkid" in argv and problem == "foreign-uuid":
            result.stdout = "foreign"
        if "umount" in argv and problem == "cleanup-command":
            raise OSError("cleanup failed")
        return result

    if problem == "close":

        def fail_close():
            lease.closed += 1
            raise OSError("close failed")

        lease.close = fail_close
    with pytest.raises(AttachError, match="rw") as captured:
        execute(prepared, runner=runner)
    assert receipt.read_bytes() == original
    assert lease.closed == 1
    if problem != "close":
        assert "incertidumbre" in str(captured.value)
        assert captured.value.cleanup_errors
    else:
        assert any("close failed" in str(e) for e in captured.value.cleanup_errors)
    if problem in {"foreign-source", "foreign-uuid"}:
        assert not any("umount" in c or "--unmount" in c for c in calls)
    for index, event in enumerate(trace):
        if event == "runner":
            assert trace[index - 1] == "revalidate"


def test_default_binding_factory_rejection_closes_without_runner(tmp_path, monkeypatch):
    prepared = plan(tmp_path, _receipt(tmp_path), admin=True)
    monkeypatch.setattr(storage_attach, "_is_admin", lambda: True)
    calls = []

    def reject(root, receipt):
        raise CustodyError("FileID or ancestor rejected")

    monkeypatch.setattr(storage_operator.PublishedDiskBinding, "open", reject)
    with pytest.raises(AttachError, match="FileID or ancestor"):
        execute(prepared, runner=lambda *a, **k: calls.append(a))
    assert calls == []


def test_explicit_binding_factory_is_supported(tmp_path, monkeypatch):
    prepared, _receipt_path, _original, lease, _trace, _calls, runner = (
        _binding_scenario(tmp_path, monkeypatch)
    )

    def reject(root, receipt):
        raise AssertionError("default factory unexpectedly called")

    monkeypatch.setattr(storage_operator.PublishedDiskBinding, "open", reject)
    result = execute(prepared, runner=runner, binding_factory=lambda r, s: lease)
    assert result.phase == "attached" and lease.closed == 1


def test_postcommit_identity_loss_reports_observed_advance(tmp_path, monkeypatch):
    prepared, receipt, original, lease, _trace, calls, runner = _binding_scenario(
        tmp_path, monkeypatch, fail_at=17
    )
    with pytest.raises(AttachError, match="recibo puede haber avanzado") as captured:
        execute(prepared, runner=runner)
    assert StorageReceipt.from_bytes(receipt.read_bytes()).phase == "attached"
    assert receipt.read_bytes() != original
    assert lease.closed == 1
    assert not any("umount" in c or "--unmount" in c for c in calls)
    assert captured.value.receipt_write_attempted is True


def test_close_failure_after_success_reports_commit(tmp_path, monkeypatch):
    prepared, receipt, _original, lease, _trace, _calls, runner = _binding_scenario(
        tmp_path, monkeypatch
    )

    def fail_close():
        lease.closed += 1
        raise CustodyError("close failed")

    lease.close = fail_close
    with pytest.raises(AttachError, match="recibo puede haber avanzado"):
        execute(prepared, runner=runner)
    assert lease.closed == 1
    assert StorageReceipt.from_bytes(receipt.read_bytes()).phase == "attached"


def test_cli_reports_close_failure_beside_primary_after_own_rollback(
    tmp_path, monkeypatch, capsys
):
    import ast

    prepared, receipt, original, lease, _trace, calls, normal_runner = (
        _binding_scenario(tmp_path, monkeypatch)
    )
    probes = 0

    def runner(argv, **kwargs):
        nonlocal probes
        result = normal_runner(argv, **kwargs)
        if "findmnt" in argv:
            probes += 1
            if probes == 1:
                result.stdout = "/dev/sdb ext4 ro /"
        return result

    def fail_close():
        lease.closed += 1
        raise CustodyError("CLOSE_FAILED_HANDLES_RETAINED private detail")

    lease.close = fail_close
    real_execute = storage_attach.execute
    monkeypatch.setattr(
        storage_attach, "execute", lambda plan: real_execute(plan, runner=runner)
    )
    result = storage_attach.main(
        [
            "--project",
            str(prepared.project_root),
            "--receipt",
            str(receipt),
            "--execute",
        ]
    )
    payload = ast.literal_eval(capsys.readouterr().out)
    assert result == 2 and payload["status"] == "NOT_READY"
    assert "rw" in payload["error"]
    assert "BINDING_CLOSE_FAILED" in payload["error"]
    assert "incertidumbre" in payload["error"]
    assert "handles pueden seguir retenidos" in payload["error"]
    assert "attached=True" in payload["error"]
    assert "mounted=True" in payload["error"]
    assert "private detail" not in payload["error"]
    assert lease.closed == 1
    assert any("umount" in call for call in calls)
    assert any("--unmount" in call for call in calls)
    assert receipt.read_bytes() == original
