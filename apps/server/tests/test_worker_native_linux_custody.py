"""Custodia nativa en contenedor propio; sin conftest ni imports de BD."""

import array
import asyncio
import importlib
import json
import os
import selectors
import shutil
import signal
import sys
import threading
import time
import types
from pathlib import Path

import pytest

fcntl = pytest.importorskip("fcntl")
termios = pytest.importorskip("termios")

ROOT = Path(__file__).resolve().parents[3]
package = types.ModuleType("app")
package.__path__ = [str(ROOT / "apps/server/app")]
sys.modules["app"] = package
LinuxGroup = importlib.import_module("app.worker.custody_linux").LinuxGroup
custody = importlib.import_module("app.worker.custody")
Owner, State, OWNERS = custody.Owner, custody.State, custody.OWNERS

ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
GROUPS = []
original_init = LinuxGroup.__init__


def captured_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    GROUPS.append(self)


LinuxGroup.__init__ = captured_init


@pytest.fixture(autouse=True)
def native_receipts(request):
    yield
    output = Path(os.environ.get("STUDIO_TEST_ROOT", "/proof"))
    output.mkdir(exist_ok=True)
    for group in GROUPS:
        for name in ("tree.json", "supervisor-journal.json"):
            if (group.root / name).exists():
                shutil.copyfile(
                    group.root / name,
                    output
                    / (
                        request.node.name.replace("[", "-").replace("]", "")
                        + "-"
                        + name
                    ),
                )
    (
        output / (request.node.name.replace("[", "-").replace("]", "") + ".json")
    ).write_text(
        json.dumps(
            [
                {
                    "disposition": g.disposition,
                    "closed": g.closed,
                    "unknown": g.unknown,
                    "fds": [
                        {
                            "value": f.value,
                            "anchor": f.anchor,
                            "identity": f.identity,
                            "closed": f.closed,
                        }
                        for f in g.fds
                    ],
                }
                for g in GROUPS
            ],
            indent=2,
        )
    )
    GROUPS.clear()


def signalled(fd, timeout):
    with selectors.DefaultSelector() as selector:
        selector.register(fd, selectors.EVENT_READ)
        return bool(selector.select(timeout))


def tree(group):
    end = time.monotonic() + 5
    while time.monotonic() < end:
        try:
            return json.loads((group.root / "tree.json").read_text())
        except (FileNotFoundError, ValueError):
            group.read_available(group.stdout)
    raise AssertionError("El árbol no alcanzó la barrera de nacimiento")


def test_term_ignored_tree_waited_before_release(tmp_path):
    group = LinuxGroup("silent", tmp_path, ID, "epoch")
    group.resume()
    record = tree(group)
    reference = os.pidfd_open(record["pid"])
    try:
        group.register(record["pid"], record["birth"])
        group.seal_births()
        group.terminate(2)
        assert signalled(reference, 0), "Nieto propio sigue vivo tras terminar custodia"
        assert group.disposition["descendants_waited"] is True
    finally:
        if not signalled(reference, 0):
            signal.pidfd_send_signal(reference, signal.SIGKILL)
            assert signalled(reference, 2)
        os.close(reference)
        group.contain_unknown()


@pytest.mark.parametrize(
    "mode", ["normal", "silent", "no_output", "fullpipe", "blocked"]
)
def test_owner_deadline_and_normal(tmp_path, mode):
    group = LinuxGroup(mode, tmp_path, ID, "epoch")
    assert group.disposition["pgid"] != group.disposition["supervisor_pgid"]
    assert not (tmp_path / "tree.json").exists()
    owner = Owner(group, ID, "epoch", 5)
    if mode == "no_output":
        actual_resume = group.resume
        birth_observed = []

        def resume_after_birth():
            actual_resume()
            end = time.monotonic() + 5
            while not (tmp_path / "tree.json").exists() and time.monotonic() < end:
                time.sleep(0.001)
            assert (tmp_path / "tree.json").exists(), "Nacimiento nativo no establecido"
            birth_observed.append(time.monotonic_ns())
            owner.end = time.monotonic() + 0.35

        group.resume = resume_after_birth
        stimulus = []
    else:
        stimulus = native_stimulus_budget(owner, group, observation=0.35)
    owner.start()
    receipt = owner.join(10)
    if mode == "no_output":
        assert birth_observed and not owner.ready.is_set()
    else:
        assert owner.ready.is_set() and any(e["event"] == "request_written" for e in stimulus), stimulus
    if mode != "normal":
        assert receipt.reason == "deadline", receipt
    assert receipt.state == State.CLOSED_CONFIRMED, (receipt, bytes(owner.stderr))
    assert receipt.resources_returned
    assert receipt.scope == group.scope
    assert group.disposition["supervisor_waited"]
    assert group.disposition["echild"]
    assert owner not in OWNERS



def native_stimulus_budget(owner, group, observation=0.25):
    """Arranque <=5s del fixture; 0.25s de observación tras request nativo propio."""
    actual_write, actual_read = group.write, group.read_available
    events = []

    def write(wire, stop):
        result = actual_write(wire, stop)
        if not stop.is_set():
            owner.end = time.monotonic() + observation
            events.append({"event": "request_written", "ns": time.monotonic_ns()})
        return result

    def read(fd):
        result = actual_read(fd)
        if result is None:
            events.append({"event": "native_eof", "fd": fd,
                           "stopping": owner.stop.is_set(), "ns": time.monotonic_ns()})
        return result

    group.write, group.read_available = write, read
    return events


@pytest.mark.parametrize(
    "mode", ["truncated", "invalid", "eof", "flood", "nonfinite", "seq", "backpressure"]
)
def test_invalid_transport_retains_owner(tmp_path, mode):
    group = LinuxGroup(mode, tmp_path, ID, "epoch")
    stimulated = mode in {"eof", "backpressure"}
    owner = Owner(group, ID, "epoch", 5 if stimulated else 0.25)
    events = native_stimulus_budget(owner, group) if stimulated else []
    owner.start()
    receipt = owner.join(10)
    if stimulated:
        assert owner.ready.is_set() and any(e["event"] == "request_written" for e in events), (
            "Estímulo no establecido dentro del presupuesto de arranque", events
        )
    if mode == "eof":
        assert any(e["event"] == "native_eof" and e["fd"] == group.stdout
                   and not e["stopping"] for e in events), events
    assert receipt.state == State.UNKNOWN_QUARANTINED
    assert not receipt.release_gate
    assert owner in OWNERS
    assert group.disposition["supervisor_waited"]
    assert len(owner.stdout) <= 16384 and len(owner.stderr) <= 16384


def test_full_write_cancel_concurrent_join(tmp_path):
    group = LinuxGroup("blocked", tmp_path, ID, "epoch")
    owner = Owner(group, ID, "epoch", 4)
    owner.start()
    assert owner.ready.wait(5)
    barrier_end = time.monotonic() + 2
    while not (tmp_path / "blocked").exists() and time.monotonic() < barrier_end:
        assert not owner.done.wait(0.001)
    assert (tmp_path / "blocked").exists()
    stopped = threading.Event()
    writer = threading.Thread(target=group.write, args=(b"x" * 1048576, stopped))
    writer.start()
    end = time.monotonic() + 2
    occupancy = array.array("i", [0])
    blocked = False
    while time.monotonic() < end:
        fcntl.ioctl(group.stdin, termios.FIONREAD, occupancy, True)
        with selectors.DefaultSelector() as selector:
            selector.register(group.stdin, selectors.EVENT_WRITE)
            blocked = occupancy[0] > 0 and not selector.select(0)
        if blocked:
            break
        stopped.wait(0.001)
    assert blocked and writer.is_alive()
    stopped.set()
    writer.join(1)
    assert not writer.is_alive()
    owner.cancel()
    receipts = []
    threads = [
        threading.Thread(target=lambda: receipts.append(owner.join(10)))
        for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(11)
    assert len(receipts) == 2 and all(r.release_gate for r in receipts)


def test_coroutine_cancel_retains_finalizer(tmp_path):
    group = LinuxGroup("silent", tmp_path, ID, "epoch")
    owner = Owner(group, ID, "epoch", 4)
    owner.start()
    assert owner.ready.wait(5)

    async def cancel():
        task = asyncio.create_task(owner.wait())
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel())
    assert owner.join(10).release_gate


def test_reused_pipe_fd_does_not_close_foreign(tmp_path):
    group = LinuxGroup("silent", tmp_path, ID, "epoch")
    group.resume()
    record = tree(group)
    group.register(record["pid"], record["birth"])
    group.seal_births()
    read, write = os.pipe()
    os.dup2(read, group.stdout)
    os.close(read)
    try:
        assert not group.stdout_ref.valid()
        assert not group.close(2)
        os.write(write, b"witness")
        assert os.read(group.stdout, 7) == b"witness"
    finally:
        group.contain_unknown()
        os.close(write)


def test_parent_death_liveness_and_foreign_witness(tmp_path):
    parent = os.fork()
    if parent == 0:
        group = LinuxGroup("silent", tmp_path, ID, "epoch")
        group.resume()
        record = tree(group)
        group.register(record["pid"], record["birth"])
        group.seal_births()
        if os.environ.get("COVERAGE_PROCESS_START"):
            import coverage

            coverage.Coverage.current().save()
        (tmp_path / "parent-ready").write_text("ready")
        while True:
            signal.pause()
    parent_ref = os.pidfd_open(parent)
    witness_r, witness_w = os.pipe()
    witness = os.fork()
    if witness == 0:
        os.close(witness_w)
        os.setsid()
        os.read(witness_r, 1)
        os._exit(0)
    os.close(witness_r)
    witness_ref = os.pidfd_open(witness)
    try:
        end = time.monotonic() + 5
        while not (tmp_path / "parent-ready").exists() and time.monotonic() < end:
            assert not signalled(parent_ref, 0.005)
        assert (tmp_path / "parent-ready").exists()
        journal = json.loads((tmp_path / "supervisor-journal.json").read_text())
        leader_ref = os.pidfd_open(journal["leader"])
        child_ref = os.pidfd_open(journal["registered"][0]["pid"])
        supervisor_ref = os.pidfd_open(journal["supervisor"])
        signal.pidfd_send_signal(parent_ref, signal.SIGKILL)
        assert signalled(parent_ref, 2)
        os.waitpid(parent, 0)
        assert signalled(supervisor_ref, 5)
        assert signalled(leader_ref, 0) and signalled(child_ref, 0)
        final = json.loads((tmp_path / "supervisor-journal.json").read_text())
        assert final["reason"] == "parent_eof"
        assert final["liveness_eof_observed"] is True
        assert final["confirmed"] and final["echild"]
        assert final["kill_sent"] and final["descendants_waited"]
        assert not signalled(witness_ref, 0)
        for ref in (leader_ref, child_ref, supervisor_ref):
            os.close(ref)
    finally:
        os.close(witness_w)
        assert signalled(witness_ref, 2)
        os.waitpid(witness, 0)
        os.close(witness_ref)
        os.close(parent_ref)


def test_scope_query_failure_finite_unknown(tmp_path, monkeypatch):
    group = LinuxGroup("silent", tmp_path, ID, "epoch")
    calls = []

    def fail_scope(self):
        calls.append(1)
        raise OSError("controlled scope query")

    monkeypatch.setattr(LinuxGroup, "scope", property(fail_scope))
    owner = Owner(group, ID, "epoch", 0.2)
    owner.start()
    receipt = owner.join(10)
    assert receipt.state == State.UNKNOWN_QUARANTINED
    assert receipt.scope == "unknown_kernel_and_private_transport"
    assert not receipt.resources_returned and len(calls) == 1
    assert owner in OWNERS


def test_controlled_close_failure_retained(tmp_path, monkeypatch):
    group = LinuxGroup("silent", tmp_path, ID, "epoch")
    monkeypatch.setattr(group.stdout_ref, "close", lambda: False)
    owner = Owner(group, ID, "epoch", 0.2)
    owner.start()
    receipt = owner.join(10)
    assert not receipt.release_gate and owner in OWNERS
    assert group.unknown and not group.closed


def test_supervisor_real_death_quarantines(tmp_path):
    group = LinuxGroup("silent", tmp_path, ID, "epoch")
    group.resume()
    record = tree(group)
    group.register(record["pid"], record["birth"])
    group.seal_births()
    leader_ref = os.pidfd_open(record["leader"])
    child_ref = os.pidfd_open(record["pid"])
    try:
        signal.pidfd_send_signal(group.supervisor_ref.anchor, signal.SIGKILL)
        assert signalled(group.supervisor_ref.anchor, 2)
        assert not group.terminate(0.1)
        assert group.unknown and not group.close(0.1)
        assert not signalled(leader_ref, 0) and not signalled(child_ref, 0)
    finally:
        for ref in (leader_ref, child_ref):
            signal.pidfd_send_signal(ref, signal.SIGKILL)
            assert signalled(ref, 2)
            os.close(ref)


def test_reject_unknown_member_and_invalid_mode(tmp_path):
    with pytest.raises(ValueError):
        LinuxGroup("arbitrary", tmp_path, ID, "epoch")
    group = LinuxGroup("silent", tmp_path, ID, "epoch")
    group.resume()
    record = tree(group)
    with pytest.raises(OSError):
        group.register(os.getpid(), record["birth"])
    with pytest.raises(OSError):
        group.register(record["pid"], record["birth"] + 1)
    group.contain_unknown()
    assert not group.close(1)


def test_reused_original_stdio_does_not_close_foreign(tmp_path):
    group = LinuxGroup("silent", tmp_path, ID, "epoch")
    group.resume()
    record = tree(group)
    group.register(record["pid"], record["birth"])
    group.seal_births()
    read, write = os.pipe()
    original = group.process.stdout.fileno()
    os.dup2(read, original)
    os.close(read)
    try:
        assert not group.close(2), (
            "Cierre de stdio original reutilizado no puede retornar recursos"
        )
        os.write(write, b"witness")
        assert os.read(original, 7) == b"witness"
    finally:
        group.contain_unknown()
        os.close(write)


def test_foreign_birth_reference_never_signal_authority(tmp_path):
    group = LinuxGroup("foreign_birth", tmp_path, ID, "epoch")
    group.resume()
    record = tree(group)
    leader = os.pidfd_open(record["leader"])
    child = os.pidfd_open(record["pid"])
    try:
        assert signalled(group.supervisor_ref.anchor, 8)
        actual_exit = group.process.wait(1)
        assert actual_exit == 0, (
            "Registro ajeno provocó señal al supervisor fuera del PGID"
        )
        assert not group.terminate(1)
        assert not group.close(1)
    finally:
        for ref in (leader, child):
            if not signalled(ref, 0):
                signal.pidfd_send_signal(ref, signal.SIGKILL)
                assert signalled(ref, 2)
            os.close(ref)


def fault_witness():
    """Testigo propio ajeno al grupo: cierre deliberado sólo tras las assertions."""
    read, write = os.pipe()
    pid = os.fork()
    if pid == 0:
        os.close(write)
        os.setsid()
        os.read(read, 1)
        os._exit(0)
    os.close(read)
    import datetime

    stat = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    (Path("/proof") / ("foreign-witness-" + str(pid) + ".json")).write_text(
        json.dumps(
            {
                "pid": pid,
                "birth": int(stat[19]),
                "parent": os.getpid(),
                "argv": sys.argv,
                "origin": "fork",
                "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
        )
    )
    return pid, os.pidfd_open(pid), write


def fault_capture(root, name, record, refs):
    output = Path(os.environ.get("STUDIO_TEST_ROOT", "/proof"))
    output.mkdir(exist_ok=True)
    for artifact in (
        "native-leader.json",
        "native-grandchild.json",
        "supervisor-journal.json",
    ):
        if (root / artifact).exists():
            shutil.copyfile(root / artifact, output / (name + "-" + artifact))
    (output / (name + "-before.json")).write_text(
        json.dumps(
            {
                "record": record,
                "refs": [
                    {
                        "fd": fd,
                        "identity": list(os.fstat(fd)[:3]),
                        "exited": signalled(fd, 0),
                    }
                    for fd in refs
                ],
                "utc": time.time(),
                "pid": os.getpid(),
                "argv": sys.argv,
                "root": str(root),
            },
            indent=2,
        )
    )


@pytest.fixture(autouse=True)
def extended_native_receipts(native_receipts, request):
    yield
    output = Path(os.environ.get("STUDIO_TEST_ROOT", "/proof"))
    for group in GROUPS:
        for name in ("native-leader.json", "native-grandchild.json"):
            if (group.root / name).exists():
                shutil.copyfile(
                    group.root / name, output / (request.node.name + "-" + name)
                )


def test_construction_emfile_after_native_popen_contains_tree(tmp_path, monkeypatch):
    import errno
    import subprocess

    backend = importlib.import_module("app.worker.custody_linux")
    original_popen, original_dup = subprocess.Popen, os.dup
    captured = {}
    witness, witness_ref, witness_write = fault_witness()

    class FaultPopen(original_popen):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            captured["process"] = self
            partial = next(g for g in backend.LINUX_GROUPS if g.root == tmp_path)
            captured["partial"] = partial
            partial.control.settimeout(5)
            born = json.loads(partial.control.recv(4096))
            partial.control.send(b"resume")
            member = json.loads(partial.control.recv(4096))
            assert born["kind"] == "born" and member["kind"] == "member"
            refs = [
                os.pidfd_open(pid) for pid in (self.pid, born["leader"], member["pid"])
            ]
            captured.update(refs=refs, born=born, member=member, armed=True)
            fault_capture(
                tmp_path,
                "emfile",
                {"born": born, "member": member, "witness": witness},
                refs,
            )

    def fail_dup(value):
        if captured.get("armed"):
            captured["armed"] = False
            captured["fault_fd"] = value
            raise OSError(errno.EMFILE, "controlled dup after native Popen")
        return original_dup(value)

    monkeypatch.setattr(subprocess, "Popen", FaultPopen)
    monkeypatch.setattr(os, "dup", fail_dup)
    start = time.monotonic()
    result = {}
    try:
        with pytest.raises(OSError) as failure:
            LinuxGroup("silent", tmp_path, ID, "epoch")
        assert failure.value.errno == errno.EMFILE
        refs = captured["refs"]
        result["native_exits"] = [
            signalled(fd, 7 if index == 0 else 0) for index, fd in enumerate(refs)
        ]
        result["duration"] = time.monotonic() - start
        result["foreign_alive"] = not signalled(witness_ref, 0)
        assert result["foreign_alive"]
        assert all(result["native_exits"]), (
            "EMFILE dejó supervisor/líder/nieto propios vivos"
        )
        assert result["duration"] < 8
        assert captured["process"].wait(timeout=1) == 0
        journal = json.loads((tmp_path / "supervisor-journal.json").read_text())
        assert journal["echild"] and journal["term_sent"] and journal["kill_sent"]
        assert {entry["pid"] for entry in journal["waited"]} == {
            captured["born"]["leader"],
            captured["member"]["pid"],
        }
        assert captured["partial"].unknown and not captured["partial"].closed
    finally:
        partial = captured.get("partial")
        if partial:
            partial.liveness.close()
        process = captured.get("process")
        if process:
            try:
                process.wait(timeout=7)
            except subprocess.TimeoutExpired:
                signal.pidfd_send_signal(captured["refs"][0], signal.SIGKILL)
                process.wait(timeout=2)
            result["supervisor_wait_returncode"] = process.returncode
        if (tmp_path / "supervisor-journal.json").exists():
            result["journal_after"] = json.loads(
                (tmp_path / "supervisor-journal.json").read_text()
            )
        if partial:
            result["partial_disposition"] = partial.disposition
            result["unknown"] = partial.unknown
            result["closed"] = partial.closed
        for fd in captured.get("refs", []):
            if not signalled(fd, 0):
                signal.pidfd_send_signal(fd, signal.SIGKILL)
                assert signalled(fd, 2)
            os.close(fd)
        os.close(witness_write)
        assert signalled(witness_ref, 2)
        os.waitpid(witness, 0)
        result["foreign_waited_after_assertions"] = True
        os.close(witness_ref)
        (Path("/proof") / "emfile-after.json").write_text(json.dumps(result, indent=2))


@pytest.mark.parametrize("fault", ["ENOSPC", "EIO"])
def test_journal_fault_after_native_registration_still_reaps(
    tmp_path, monkeypatch, fault
):
    import subprocess

    original_popen = subprocess.Popen
    witness, witness_ref, witness_write = fault_witness()

    class JournalPopen(original_popen):
        def __init__(self, *args, **kwargs):
            env = dict(kwargs["env"])
            env["CUSTODY_TEST_JOURNAL_ERRNO"] = fault
            kwargs["env"] = env
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", JournalPopen)
    group = LinuxGroup("silent", tmp_path, ID, "epoch")
    group.resume()
    refs = []
    result = {}
    try:
        end = time.monotonic() + 5
        while (
            not (tmp_path / "journal-fault-before.json").exists()
            and time.monotonic() < end
        ):
            assert not signalled(group.supervisor_ref.anchor, 0.001)
        record = json.loads((tmp_path / "journal-fault-before.json").read_text())[
            "record"
        ]
        refs = [
            os.pidfd_open(pid)
            for pid in (record["leader"], record["registered"][0]["pid"])
        ]
        assert record["pgid"] != record["supervisor_pgid"]
        assert all(not signalled(fd, 0) for fd in refs)
        fault_capture(
            tmp_path,
            "journal-" + fault,
            {"record": record, "witness": witness},
            [group.supervisor_ref.anchor] + refs,
        )
        (tmp_path / "release-journal-fault").write_text("release")
        assert signalled(group.supervisor_ref.anchor, 7)
        result["native_exits"] = [signalled(fd, 0) for fd in refs]
        result["foreign_alive"] = not signalled(witness_ref, 0)
        result["supervisor_exit"] = group.process.wait(timeout=1)
        assert result["foreign_alive"]
        assert all(result["native_exits"]), (
            "Journal roto omitió TERM/KILL o wait de descendientes"
        )
        group._events()
        result["native_cleanup_record"] = group.disposition.copy()
        assert group.disposition["term_sent"] and group.disposition["kill_sent"]
        assert group.disposition["echild"] and group.disposition["descendants_waited"]
        assert {entry["pid"] for entry in group.disposition["waited"]} == {
            record["leader"],
            record["registered"][0]["pid"],
        }
        assert not group.terminate(1) and not group.close(1)
        assert group.unknown and not group.closed
    finally:
        (tmp_path / "release-journal-fault").write_text("release")
        for fd in refs:
            if not signalled(fd, 0):
                signal.pidfd_send_signal(fd, signal.SIGKILL)
                assert signalled(fd, 2)
            os.close(fd)
        group.contain_unknown()
        os.close(witness_write)
        assert signalled(witness_ref, 2)
        os.waitpid(witness, 0)
        result["foreign_waited_after_assertions"] = True
        os.close(witness_ref)
        (Path("/proof") / ("journal-" + fault + "-after.json")).write_text(
            json.dumps(result, indent=2)
        )


@pytest.mark.parametrize("stage", ["create", "register", "select", "close"])
def test_grace_selector_enfile_after_actual_term_contains_owned_tree(
    tmp_path, monkeypatch, stage
):
    import subprocess

    original_popen = subprocess.Popen
    witness, witness_ref, witness_write = fault_witness()

    class GraceFaultPopen(original_popen):
        def __init__(self, *args, **kwargs):
            env = dict(kwargs["env"])
            env["CUSTODY_TEST_GRACE_ENFILE"] = stage
            kwargs["env"] = env
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", GraceFaultPopen)
    group = LinuxGroup("silent", tmp_path, ID, "epoch")
    refs = []
    result = {}
    try:
        group.resume()
        record = tree(group)
        group.register(record["pid"], record["birth"])
        group.seal_births()
        refs = [os.pidfd_open(pid) for pid in (record["leader"], record["pid"])]
        assert all(not signalled(fd, 0) for fd in refs)
        fault_capture(
            tmp_path,
            "grace-" + stage,
            {"tree": record, "disposition": group.disposition, "witness": witness},
            [group.supervisor_ref.anchor] + refs,
        )
        group._command(b"stop")
        assert signalled(group.supervisor_ref.anchor, 7)
        result["supervisor_exit"] = group.process.wait(timeout=1)
        result["native_exits_before_rescue"] = [signalled(fd, 0) for fd in refs]
        result["foreign_alive_before_rescue"] = not signalled(witness_ref, 0)
        fault = json.loads((tmp_path / "grace-fault.json").read_text())
        result["fault"] = fault
        assert fault["stage"] == stage and fault["errno"] == 23
        assert fault["actual_term_returned"] and fault["record"]["term_sent"]
        assert fault["record"]["leader_retained_before_signals"]
        assert fault["record"]["pgid"] != fault["record"]["supervisor_pgid"]
        assert result["foreign_alive_before_rescue"]
        assert all(result["native_exits_before_rescue"]), (
            "ENFILE tras TERM omitió SIGKILL/waits: descendientes propios vivos"
        )
        assert result["supervisor_exit"] == 0
        group._events()
        final = group.disposition.copy()
        result["final"] = final
        assert final["term_sent"] and final["kill_sent"]
        assert final["echild"] and final["descendants_waited"]
        assert {entry["pid"] for entry in final["waited"]} == {
            record["leader"],
            record["pid"],
        }
        assert all(os.WIFSIGNALED(entry["status"]) for entry in final["waited"])
        assert all(
            os.WTERMSIG(entry["status"]) == signal.SIGKILL for entry in final["waited"]
        )
        assert not final["confirmed"]
        assert not group.terminate(1) and not group.close(1)
        assert group.unknown and not group.closed
    finally:
        # Rescate propio DESPUÉS de las assertions; nunca convierte RED en PASS.
        for fd in refs:
            if not signalled(fd, 0):
                signal.pidfd_send_signal(fd, signal.SIGKILL)
                assert signalled(fd, 2)
            os.close(fd)
        group.contain_unknown()
        for artifact in ("grace-fault.json", "supervisor-journal.json"):
            if (tmp_path / artifact).exists():
                shutil.copyfile(
                    tmp_path / artifact,
                    Path("/proof") / ("grace-" + stage + "-" + artifact),
                )
        os.close(witness_write)
        assert signalled(witness_ref, 2)
        result["foreign_wait_status_after_assertions"] = os.waitpid(witness, 0)
        os.close(witness_ref)
        (Path("/proof") / ("grace-" + stage + "-after.json")).write_text(
            json.dumps(result, indent=2)
        )


def test_secondary_final_notify_error_retains_unknown_after_native_waits(
    tmp_path, monkeypatch
):
    import subprocess

    original_popen = subprocess.Popen
    witness, witness_ref, witness_write = fault_witness()

    class NotifyFaultPopen(original_popen):
        def __init__(self, *args, **kwargs):
            env = dict(kwargs["env"])
            env["CUSTODY_TEST_FINAL_NOTIFY_ERROR"] = "ValueError"
            kwargs["env"] = env
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", NotifyFaultPopen)
    group = LinuxGroup("silent", tmp_path, ID, "epoch")
    refs = []
    result = {}
    try:
        group.resume()
        record = tree(group)
        group.register(record["pid"], record["birth"])
        group.seal_births()
        refs = [os.pidfd_open(pid) for pid in (record["leader"], record["pid"])]
        assert all(not signalled(fd, 0) for fd in refs)
        fault_capture(
            tmp_path,
            "notify-secondary",
            {"tree": record, "witness": witness},
            [group.supervisor_ref.anchor] + refs,
        )
        group._command(b"stop")
        assert signalled(group.supervisor_ref.anchor, 7)
        result["supervisor_exit"] = group.process.wait(timeout=1)
        result["native_exits_before_rescue"] = [signalled(fd, 0) for fd in refs]
        result["foreign_alive_before_rescue"] = not signalled(witness_ref, 0)
        result["notify_attempt"] = json.loads(
            (tmp_path / "notify-fault.json").read_text()
        )
        final = result["notify_attempt"]["record"]
        assert all(result["native_exits_before_rescue"])
        assert result["foreign_alive_before_rescue"]
        assert final["term_sent"] and final["kill_sent"] and final["echild"]
        assert final["descendants_waited"]
        assert {entry["pid"] for entry in final["waited"]} == {
            record["leader"],
            record["pid"],
        }
        assert all(entry["status"] == signal.SIGKILL for entry in final["waited"])
        assert result["supervisor_exit"] == 0, (
            "Metadatos secundarios escaparon de la finalización nativa"
        )
        group._events()
        assert "final" not in group.events
        assert not group.terminate(0.1) and not group.close(0.1)
        assert group.unknown and not group.closed
    finally:
        for fd in refs:
            if not signalled(fd, 0):
                signal.pidfd_send_signal(fd, signal.SIGKILL)
                assert signalled(fd, 2)
            os.close(fd)
        group.contain_unknown()
        if (tmp_path / "notify-fault.json").exists():
            shutil.copyfile(
                tmp_path / "notify-fault.json", Path("/proof") / "notify-fault.json"
            )
        os.close(witness_write)
        assert signalled(witness_ref, 2)
        result["foreign_wait_status_after_assertions"] = os.waitpid(witness, 0)
        os.close(witness_ref)
        (Path("/proof") / "notify-secondary-after.json").write_text(
            json.dumps(result, indent=2)
        )


def test_final_group_query_error_uses_owned_pidfds_and_retains_unknown(
    tmp_path, monkeypatch
):
    import subprocess

    original_popen = subprocess.Popen
    witness, witness_ref, witness_write = fault_witness()

    class QueryFaultPopen(original_popen):
        def __init__(self, *args, **kwargs):
            env = dict(kwargs["env"])
            env["CUSTODY_TEST_FINAL_GROUP_QUERY_ERROR"] = "EIO"
            kwargs["env"] = env
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", QueryFaultPopen)
    group = LinuxGroup("silent", tmp_path, ID, "epoch")
    refs = []
    result = {}
    try:
        group.resume()
        record = tree(group)
        group.register(record["pid"], record["birth"])
        group.seal_births()
        refs = [os.pidfd_open(pid) for pid in (record["leader"], record["pid"])]
        assert all(not signalled(fd, 0) for fd in refs)
        fault_capture(
            tmp_path,
            "group-query",
            {"tree": record, "witness": witness},
            [group.supervisor_ref.anchor] + refs,
        )
        group._command(b"stop")
        assert signalled(group.supervisor_ref.anchor, 7)
        result["supervisor_exit"] = group.process.wait(timeout=1)
        result["native_exits_before_rescue"] = [signalled(fd, 0) for fd in refs]
        result["foreign_alive_before_rescue"] = not signalled(witness_ref, 0)
        result["query_fault"] = json.loads(
            (tmp_path / "group-query-fault.json").read_text()
        )
        assert result["query_fault"]["retained_before_query"]
        assert result["foreign_alive_before_rescue"]
        assert all(result["native_exits_before_rescue"]), (
            "Fallo secundario PGID omitió SIGKILL por pidfds propios y waits"
        )
        assert result["supervisor_exit"] == 0
        group._events()
        final = group.disposition.copy()
        result["final"] = final
        assert final["echild"] and final["descendants_waited"]
        assert not final.get("term_sent") and not final.get("kill_sent")
        assert {entry["pid"] for entry in final["waited"]} == {
            record["leader"],
            record["pid"],
        }
        assert all(entry["status"] == signal.SIGKILL for entry in final["waited"])
        assert not final["confirmed"], "PGID incierto no puede confirmar recursos"
        assert not group.terminate(0.1) and not group.close(0.1)
        assert group.unknown and not group.closed
    finally:
        for fd in refs:
            if not signalled(fd, 0):
                signal.pidfd_send_signal(fd, signal.SIGKILL)
                assert signalled(fd, 2)
            os.close(fd)
        group.contain_unknown()
        if (tmp_path / "group-query-fault.json").exists():
            shutil.copyfile(
                tmp_path / "group-query-fault.json",
                Path("/proof") / "group-query-fault.json",
            )
        os.close(witness_write)
        assert signalled(witness_ref, 2)
        result["foreign_wait_status_after_assertions"] = os.waitpid(witness, 0)
        os.close(witness_ref)
        (Path("/proof") / "group-query-after.json").write_text(
            json.dumps(result, indent=2)
        )


@pytest.mark.parametrize("mode", ["truncated", "invalid"])
def test_real_wire_held_until_draining_retains_owner(tmp_path, mode):
    """Entrega controlada de bytes leídos del pipe real, sin falsificar transporte."""
    group = LinuxGroup(mode, tmp_path, ID, "epoch")
    owner = Owner(group, ID, "epoch", 4)
    original_read, original_write = group.read_available, group.write
    held, captured = bytearray(), threading.Event()
    timeline = []
    witness, witness_ref, witness_write = fault_witness()
    strong_refs = list(group.fds)
    authorities = []
    for name in ("terminate", "close"):
        actual = getattr(group, name)

        def observed(*args, _actual=actual, _name=name, **kwargs):
            value = _actual(*args, **kwargs)
            authorities.append(
                {
                    "method": _name,
                    "actual_return": value,
                    "monotonic_ns": time.monotonic_ns(),
                }
            )
            return value

        setattr(group, name, observed)

    def event(kind, **values):
        timeline.append(
            {
                "event": kind,
                "monotonic_ns": time.monotonic_ns(),
                "state": owner.state,
                "stop": owner.stop.is_set(),
                **values,
            }
        )

    def write(wire, stop):
        result = original_write(wire, stop)
        event("native_write_return", wire_hex=wire.hex())
        return result

    def read(fd):
        if fd != group.stdout:
            return original_read(fd)
        if held:
            if owner.state != State.DRAINING:
                return b""
            wire = bytes(held)
            held.clear()
            event("drain_delivery", wire_hex=wire.hex())
            return wire
        chunk = original_read(fd)
        if chunk and owner.ready.is_set() and owner.state != State.DRAINING:
            held.extend(chunk)
            event("native_read_held", wire_hex=chunk.hex())
            captured.set()
            return b""
        if chunk is None:
            event("native_stdout_eof")
        elif chunk:
            event("native_read_delivered", wire_hex=chunk.hex())
        return chunk

    group.read_available, group.write = read, write
    owner.start()
    try:
        assert owner.ready.wait(5)
        assert captured.wait(2), "No llegaron bytes malformados reales"
        event("cancel_requested")
        owner.cancel()
        receipt = owner.join(10)
        event("joined", receipt_state=receipt.state, reason=receipt.reason)
        process_refs = [group.supervisor_ref, group.leader_ref] + [
            v[1] for v in group.members.values()
        ]
        strong_refs.extend(f for f in group.fds if f not in strong_refs)
        native_waits = [
            {
                "anchor": f.anchor,
                "valid": f.valid(),
                "waited": signalled(f.anchor, 0) if f.valid() else None,
            }
            for f in process_refs
        ]
        proof = {
            "authorities": authorities,
            "native_waits": native_waits,
            "foreign_alive_before_decision": not signalled(witness_ref, 0),
            "owner_retained": owner in OWNERS,
            "controlled_delivery": True,
            "spontaneous_os_failure": False,
            "timeline": timeline,
            "receipt": {
                "state": receipt.state,
                "reason": receipt.reason,
                "release_gate": receipt.release_gate,
            },
            "disposition": dict(group.disposition),
            "closed": group.closed,
            "writer_alive": owner.writer.is_alive(),
            "finalizer_alive": owner.finalizer.is_alive(),
            "stdout_eof": owner.stdout_eof,
            "stderr_eof": owner.stderr_eof,
            "stdout_hex": bytes(owner.stdout).hex(),
            "fds": [
                {
                    "value": f.value,
                    "anchor": f.anchor,
                    "identity": f.identity,
                    "closed": f.closed,
                }
                for f in group.fds
            ],
        }
        (
            Path(os.environ.get("STUDIO_TEST_ROOT", "/proof"))
            / ("drain-" + mode + ".json")
        ).write_text(json.dumps(proof, indent=2))
        deliveries = [v for v in timeline if v["event"] == "drain_delivery"]
        assert proof["foreign_alive_before_decision"]
        assert deliveries and deliveries[0]["stop"]
        assert deliveries[0]["wire_hex"] == (
            "000000107b" if mode == "truncated" else "000000027b7d"
        )
        assert owner.stdout_eof and owner.stderr_eof
        assert receipt.state == State.UNKNOWN_QUARANTINED, receipt
        assert receipt.reason == "transport_error"
        assert not receipt.release_gate and owner in OWNERS
        assert not group.closed
    finally:
        owner.cancel()
        try:
            try:
                if owner.finalizer.is_alive():
                    owner.join(10)
            finally:
                group.contain_unknown()
        finally:
            os.close(witness_write)
            exited = signalled(witness_ref, 2)
            waited = os.waitpid(witness, 0)
            os.close(witness_ref)
            (
                Path(os.environ.get("STUDIO_TEST_ROOT", "/proof"))
                / ("drain-" + mode + "-cleanup.json")
            ).write_text(
                json.dumps(
                    {
                        "witness_exited": exited,
                        "actual_waitpid": waited,
                        "authorities": authorities,
                    },
                    indent=2,
                )
            )


@pytest.mark.parametrize(
    "case",
    [
        "valid",
        "schema",
        "valid_before_bad",
        "truncated",
        "quota",
        "final_eos",
        "length",
    ],
)
def test_stopping_native_pipe_validates_without_effects(tmp_path, case):
    """Physical private pipe checks decoder boundaries; no closure certificate."""
    protocol = importlib.import_module("app.worker.pipe_protocol")
    backend = importlib.import_module("app.worker.custody_linux")
    group = LinuxGroup("silent", tmp_path, ID, "epoch")
    reader, writer = os.pipe()
    os.set_blocking(reader, False)
    reference = backend.FD(reader)
    saved = group.stdout, group.stdout_ref
    group.stdout, group.stdout_ref = reader, reference
    owner = Owner(group, ID, "epoch", 4)
    owner.state = State.DRAINING
    owner.stop.set()
    owner.decoder.session.mark_stopping("liveness")
    owner.stderr_eof = True

    def wire(kind, seq):
        return protocol.encode(
            {
                "version": 1,
                "execution_id": ID,
                "epoch": "epoch",
                "seq": seq,
                "kind": kind,
                "payload": {},
            }
        )

    def feed(data):
        assert os.write(writer, data) == len(data)
        owner._read(parsing=False)

    try:
        ready = wire("ready", 1)
        if case == "valid":
            feed(ready + wire("result", 2) + wire("closed", 3))
            os.close(writer)
            writer = None
            owner._read(parsing=False)
            assert owner.stdout_eof and owner.decoder.session.frames == 3
        elif case == "truncated":
            feed(b"\x00\x00\x00\x10{")
            os.close(writer)
            writer = None
            with pytest.raises(protocol.ProtocolError, match="incompleto"):
                owner._read(parsing=False)
            assert owner.stdout_eof
        elif case == "quota":
            feed(ready)
            for seq in range(2, 66):
                feed(wire("progress", seq))
            with pytest.raises(protocol.ProtocolError, match="progress"):
                feed(wire("progress", 66))
            assert owner.decoder.session.progress_count == 64
            assert owner.decoder.session.frames == 65
        else:
            data = {
                "schema": b"\x00\x00\x00\x02{}",
                "valid_before_bad": ready + b"\x00\x00\x00\x02{}",
                "final_eos": ready + wire("closed", 2) + wire("progress", 3),
                "length": b"\x00\x00\x00\x00",
            }[case]
            with pytest.raises(protocol.ProtocolError):
                feed(data)
            if case == "valid_before_bad":
                assert owner.decoder.session.frames == 1
            if case == "final_eos":
                assert owner.decoder.session.frames == 2
        assert owner.messages.empty() and not owner.ready.is_set()
        assert not owner.saw_closed and owner.writes.empty()
        assert len(owner.stdout) <= 16384
        if case != "valid":
            with pytest.raises(protocol.ProtocolError):
                list(owner.decoder.feed(wire("closed", 1)))
    finally:
        group.stdout, group.stdout_ref = saved
        try:
            group.contain_unknown()
        finally:
            reference.close()
            if writer is not None:
                os.close(writer)


def test_backpressure_fixture_really_saturates_queue(tmp_path):
    """El estímulo nativo debe producir Full real antes de probar la retención."""
    from queue import Full

    group = LinuxGroup("backpressure", tmp_path, ID, "epoch")
    owner = Owner(group, ID, "epoch", 5)
    stimulus = native_stimulus_budget(owner, group)
    actual_put = owner.messages.put
    attempts = []
    strong_refs = list(group.fds)

    def observed_put(item, *args, **kwargs):
        event = {"monotonic_ns": time.monotonic_ns(), "kind": item["kind"],
                 "stopping": owner.stop.is_set()}
        try:
            result = actual_put(item, *args, **kwargs)
        except Full:
            event["actual_full"] = True
            event["stopping_at_full"] = owner.stop.is_set()
            attempts.append(event)
            raise
        else:
            event["actual_full"] = False
            attempts.append(event)
            return result

    owner.messages.put = observed_put
    owner.start()
    receipt = owner.join(10)
    strong_refs.extend(f for f in group.fds if f not in strong_refs)
    proof = {
        "utc": __import__("datetime")
        .datetime.now(__import__("datetime").timezone.utc)
        .isoformat(),
        "observer_pid": os.getpid(),
        "attempts": attempts,
        "stimulus": stimulus,
        "queue_size": owner.messages.qsize(),
        "queue_capacity": owner.messages.maxsize,
        "receipt": {
            "state": receipt.state,
            "reason": receipt.reason,
            "release_gate": receipt.release_gate,
        },
        "owner_retained": owner in OWNERS,
        "disposition": dict(group.disposition),
        "fds_after_legitimate_close_before_assertions": [
            {
                "value": f.value,
                "anchor": f.anchor,
                "identity": f.identity,
                "closed": f.closed,
                "valid": f.valid(),
            }
            for f in strong_refs
        ],
        "native_records": {
            name: json.loads((tmp_path / name).read_text())
            for name in (
                "native-leader.json",
                "native-grandchild.json",
                "tree.json",
                "supervisor-journal.json",
            )
            if (tmp_path / name).exists()
        },
    }
    (
        Path(os.environ.get("STUDIO_TEST_ROOT", "/proof"))
        / "backpressure-before-assertions.json"
    ).write_text(json.dumps(proof, indent=2))
    assert owner.ready.is_set() and any(e["event"] == "request_written" for e in stimulus), proof
    assert any(event["actual_full"] and not event["stopping_at_full"] for event in attempts), proof
    assert receipt.state == State.UNKNOWN_QUARANTINED, receipt
    assert not receipt.release_gate
    assert owner in OWNERS


def test_native_terminal_stop_after_final_journal_confirms(tmp_path, monkeypatch):
    """Pausa de planificación; final, stop, pidfds y waits siguen siendo nativos."""
    import subprocess

    private = tmp_path / "source"
    shutil.copytree(ROOT / "apps", private / "apps")
    supervisor = private / "apps/server/app/worker/custody_linux_supervisor.py"
    source = supervisor.read_text()
    needle = '        record["confirmed"] &= not uncertain\n        notify(dict(kind="final", **record))'
    assert source.count(needle) == 1
    supervisor.write_text(source.replace(needle, needle.replace(
        '        notify(',
        '        (root / "terminal-pause").write_text("ready")\n'
        '        time.sleep(0.05)  # scheduling only, no synthetic final\n'
        '        notify(',
    )))
    actual_popen = subprocess.Popen

    def private_popen(argv, **kwargs):
        argv = list(argv)
        argv[2] = str(supervisor)
        return actual_popen(argv, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", private_popen)
    group = LinuxGroup("normal", tmp_path, ID, "epoch")
    actual_terminate = group.terminate
    actual_events = group._events
    observations = []
    errors = []

    def observed_events():
        try:
            return actual_events()
        except OSError as error:
            errors.append({"type": type(error).__name__, "errno": error.errno})
            raise

    group._events = observed_events

    def stop_in_terminal_window(timeout):
        end = time.monotonic() + 5
        while not (tmp_path / "terminal-pause").exists() and time.monotonic() < end:
            time.sleep(0.001)
        assert (tmp_path / "terminal-pause").exists(), "Ventana terminal no alcanzada"
        observations.append({"final_received_before_stop": "final" in group.events})
        return actual_terminate(timeout)

    group.terminate = stop_in_terminal_window
    owner = Owner(group, ID, "epoch", 4)
    owner.start()
    try:
        receipt = owner.join(12)
        assert observations and not observations[0]["final_received_before_stop"]
        journal = json.loads((tmp_path / "supervisor-journal.json").read_text())
        assert journal["reason"] == "leader_exit" and journal["confirmed"]
        assert journal["echild"] and journal["descendants_waited"]
        (Path(os.environ.get("STUDIO_TEST_ROOT", "/proof")) / "terminal-race.json").write_text(
            json.dumps({"errors": errors, "observations": observations,
                        "disposition": group.disposition, "journal": journal,
                        "receipt_state": receipt.state}, indent=2)
        )
        assert receipt.state == State.CLOSED_CONFIRMED, (receipt, errors)
        assert receipt.resources_returned and receipt.release_gate
        assert group.disposition["native_process_refs_waited"]
        assert group.disposition["supervisor_waited"]
        assert group.disposition["writer_waited"]
        assert all(ref.closed for ref in group.fds)
        assert owner not in OWNERS
    finally:
        owner.cancel()
        if owner.finalizer.is_alive():
            owner.join(12)
        if not group.closed:
            group.contain_unknown()


@pytest.mark.parametrize("mode", ["eof", "backpressure"])
def test_cancel_before_native_request_stimulus_confirms_custody(tmp_path, mode):
    """Cancelación antes del request: no se atribuye EOF/Full a estímulo inexistente."""
    group = LinuxGroup(mode, tmp_path, ID, "epoch")
    owner = Owner(group, ID, "epoch", 5)
    actual_write = group.write
    entered, release = threading.Event(), threading.Event()
    writes = []

    def held_write(wire, stop):
        entered.set()
        assert release.wait(5), "Barrera de request no liberada"
        writes.append({"stopping_before_write": stop.is_set()})
        return actual_write(wire, stop)

    group.write = held_write
    owner.start()
    try:
        assert owner.ready.wait(5) and entered.wait(5)
        assert not owner.stdout_eof and owner.messages.empty()
        owner.cancel()
        release.set()
        receipt = owner.join(12)
        assert writes == [{"stopping_before_write": True}]
        assert receipt.state == State.CLOSED_CONFIRMED, receipt
        assert receipt.release_gate and receipt.reason == "cancelled"
        assert owner not in OWNERS and group.closed
        assert group.disposition["native_process_refs_waited"]
        assert group.disposition["writer_waited"]
    finally:
        owner.cancel()
        release.set()
        if owner.finalizer.is_alive():
            owner.join(12)
        if not group.closed:
            group.contain_unknown()


@pytest.mark.parametrize("mode", ["normal", "eof", "backpressure"])
def test_native_cancellation_before_birth_has_no_fixture_stimulus(tmp_path, mode):
    """El líder está nacido en gate, pero el fixture aún no pudo ejecutarse."""
    group = LinuxGroup(mode, tmp_path, ID, "epoch")
    assert not (tmp_path / "tree.json").exists()
    assert "born" in group.events and "member" not in group.events
    try:
        assert group.terminate(2)
        assert group.disposition["reason"] == "stop"
        assert not group.disposition["births_sealed"]
        assert group.disposition["descendants_waited"] and group.disposition["echild"]
        assert not (tmp_path / "tree.json").exists()
        assert group.close(2)
        assert all(ref.closed for ref in group.fds)
    finally:
        if not group.closed:
            group.contain_unknown()


@pytest.fixture(autouse=True)
def explicit_native_fault_bootstrap(request, monkeypatch):
    """Activate only the four named parametrized syscall/metadata negatives."""
    names = {
        "test_journal_fault_after_native_registration_still_reaps",
        "test_grace_selector_enfile_after_actual_term_contains_owned_tree",
        "test_secondary_final_notify_error_retains_unknown_after_native_waits",
        "test_final_group_query_error_uses_owned_pidfds_and_retains_unknown",
    }
    if request.node.originalname not in names:
        return
    import runpy
    import subprocess

    fixture = Path(__file__).with_name("fixtures") / "native_custody_fault_bootstrap.py"
    configure = runpy.run_path(str(fixture))["invocation"]
    actual = subprocess.Popen

    class TestOwnedFaultPopen(actual):
        def __init__(self, argv, **kwargs):
            argv, kwargs["env"] = configure(argv, kwargs["env"])
            super().__init__(argv, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", TestOwnedFaultPopen)


def test_fault_bootstrap_uses_real_children_without_inherited_configuration(tmp_path, monkeypatch):
    """Harness regression: configured fault exists, real descendants inherit no hooks."""
    import runpy
    import subprocess

    fixture = Path(__file__).with_name("fixtures") / "native_custody_fault_bootstrap.py"
    configure = runpy.run_path(str(fixture))["invocation"]
    actual = subprocess.Popen

    class IsolatedFaultPopen(actual):
        def __init__(self, argv, **kwargs):
            environment = dict(kwargs["env"], CUSTODY_TEST_JOURNAL_ERRNO="ENOSPC")
            argv, kwargs["env"] = configure(argv, environment)
            super().__init__(argv, **kwargs)

    monkeypatch.setattr(subprocess, "Popen", IsolatedFaultPopen)
    group = LinuxGroup("silent", tmp_path, ID, "epoch")
    refs = []
    try:
        group.resume()
        end = time.monotonic() + 5
        artifact = tmp_path / "journal-fault-before.json"
        while not artifact.exists() and time.monotonic() < end:
            assert not signalled(group.supervisor_ref.anchor, 0.001)
        assert artifact.exists(), "Configured fault was not injected in real supervisor"
        observed = json.loads(artifact.read_text())
        assert observed["injected"] and not observed["kernel_errno_claimed"]
        record = observed["record"]
        pids = [record["leader"], record["registered"][0]["pid"]]
        refs = [os.pidfd_open(pid) for pid in pids]
        assert all(not signalled(fd, 0) for fd in refs)
        for pid in pids:
            environment = Path(f"/proc/{pid}/environ").read_bytes().split(b"\0")
            assert not any(value.startswith(b"CUSTODY_TEST_") for value in environment)
            command = Path(f"/proc/{pid}/cmdline").read_bytes()
            assert b"native_custody_fault_bootstrap.py" not in command
        (tmp_path / "release-journal-fault").write_text("release")
        assert signalled(group.supervisor_ref.anchor, 7)
        assert group.process.wait(timeout=1) == 0
        assert all(signalled(fd, 0) for fd in refs)
        group._events()
        assert group.disposition["echild"] and group.disposition["descendants_waited"]
        assert not group.terminate(0.1) and not group.close(0.1)
        assert group.unknown and not group.closed
    finally:
        (tmp_path / "release-journal-fault").write_text("release")
        for fd in refs:
            if not signalled(fd, 0):
                signal.pidfd_send_signal(fd, signal.SIGKILL)
                assert signalled(fd, 2)
            os.close(fd)
        group.contain_unknown()


def audio_before_resume_stimulus(group, action):
    """Deliver real control or revoke the real liveness pipe before resume."""
    if action == "stop":
        group.terminate(3)
    elif action == "invalid_control":
        group._command(b"not-a-command")
        group.terminate(3)
    elif action == "cancel":
        group.contain_unknown()
    else:
        raise ValueError("Unknown audio-before-resume stimulus")


@pytest.mark.parametrize("action", ["stop", "invalid_control", "cancel"])
def test_audio_before_resume_real_control_and_cancellation(tmp_path, action):
    """Gated audio must reap the real leader; uncertain control cannot release."""
    import hashlib

    project = tmp_path / "project"
    project.mkdir()
    opaque = b"{}"
    (project / "plan-before-resume.json").write_bytes(opaque)
    (project / "context-before-resume.json").write_bytes(opaque)
    digest = hashlib.sha256(opaque).hexdigest()
    witness, witness_ref, witness_write = fault_witness()
    group = LinuxGroup(
        "audio", tmp_path, ID, "epoch", audio_root=project,
        plan_sha256=digest, plan_bytes=len(opaque),
        context_sha256=digest, context_bytes=len(opaque),
    )
    leader = group.disposition["leader"]
    refs = [os.pidfd_open(pid) for pid in (group.process.pid, leader)]
    result = {"action": action, "leader": leader, "witness": witness}
    try:
        assert group.audio_policy and "born" in group.events
        assert not group.disposition["registered_count"]
        assert all(not signalled(fd, 0) for fd in refs)
        command = Path(f"/proc/{leader}/cmdline").read_bytes()
        assert b"audio_child.py" not in command
        audio_before_resume_stimulus(group, action)
        # An uncertain control return is not process completion: observe retained
        # native refs with the same finite cleanup budget before any rescue.
        assert all(signalled(fd, 3) for fd in refs)
        result["native_exits_before_rescue"] = [signalled(fd, 0) for fd in refs]
        result["foreign_alive_before_rescue"] = not signalled(witness_ref, 0)
        assert all(result["native_exits_before_rescue"]), "New audio stimulus did not terminate the gated native tree"
        assert result["foreign_alive_before_rescue"]
        result["supervisor_exit"] = group.process.wait(timeout=1)
        assert result["supervisor_exit"] == 0
        final = json.loads((tmp_path / "supervisor-journal.json").read_text())
        result["final"] = final
        assert final["leader"] == leader
        assert final["registered_count"] == final["reaped_count"] == 0
        assert final["echild"] and final["descendants_waited"]
        assert not final["births_sealed"]
        for fd in refs:
            assert "Pid:\t-1\n" in Path(f"/proc/self/fdinfo/{fd}").read_text()
        if action == "stop":
            assert final["reason"] == "stop" and final["confirmed"]
            assert group.close(2)
            assert all(ref.closed for ref in group.fds)
        else:
            assert not group.close(0.1)
            assert group.unknown and not group.closed
            if action == "invalid_control":
                assert final["error_type"] == "OSError" and not final["confirmed"]
            else:
                assert final["reason"] in {"stop", "parent_eof"}
    finally:
        for fd in refs:
            if not signalled(fd, 0):
                signal.pidfd_send_signal(fd, signal.SIGKILL)
                assert signalled(fd, 2)
            os.close(fd)
        if not group.closed:
            group.contain_unknown()
        os.close(witness_write)
        assert signalled(witness_ref, 2)
        os.waitpid(witness, 0)
        os.close(witness_ref)
        output = Path(os.environ.get("STUDIO_TEST_ROOT", "/proof"))
        (output / ("audio-before-resume-" + action + ".json")).write_text(json.dumps(result, indent=2))
