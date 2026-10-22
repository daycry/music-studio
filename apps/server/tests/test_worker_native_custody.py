"""Pruebas de handles y árboles reales; ejecutables sin conftest del server."""

import asyncio
import ctypes
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
# Aísla el paquete: app.__init__ arranca imports ajenos a esta unidad.
package = types.ModuleType("app")
package.__path__ = [str(ROOT / "apps/server/app")]
sys.modules["app"] = package
from app.worker.custody_windows import KernelGroup

FIXTURE = Path(__file__).with_name("fixtures") / "worker_custody_child.py"
PHASE = Path(os.environ["STUDIO_TEST_ROOT"])
ID = "01ARZ3NDEKTSV4RRFFQ69G5FAV"
GROUPS = []


@pytest.fixture(autouse=True)
def native_dispositions(request):
    sources_before = {
        rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        for rel in (
            "apps/server/app/worker/custody.py",
            "apps/server/app/worker/custody_windows.py",
        )
    }
    assert sources_before == json.loads(os.environ["CUSTODY_SOURCE_SHA256"])
    runner_birth = KernelGroup.creation_time(-1)
    yield
    values = []
    for group in GROUPS:
        values.append(
            {
                "disposition": group.disposition,
                "closed": group.closed,
                "handles": [
                    {"value": h.value, "escrow": h.escrow, "closed": h.closed}
                    for h in group.handles
                ],
            }
        )
    (
        PHASE / (request.node.name.replace("[", "-").replace("]", "") + "-native.json")
    ).write_text(
        json.dumps(
            {
                "run_uuid": os.environ.get("CUSTODY_RUN_UUID"),
                "groups": values,
                "runner_pid": os.getpid(),
                "runner_birth": runner_birth,
                "sources_before_native_spawn": sources_before,
            },
            indent=2,
        )
    )


def area(name):
    path = PHASE / name
    path.mkdir(exist_ok=False)
    return path


def environment(path):
    return {
        "SystemRoot": os.environ["SystemRoot"],
        "TEMP": str(path),
        "TMP": str(path),
        "PYTHONPYCACHEPREFIX": str(path / "pycache"),
    }


def create(path, mode="silent"):
    group = KernelGroup(
        sys._base_executable,
        [sys._base_executable, str(FIXTURE), mode, str(path), ID, "epoch"],
        path,
        environment(path),
    )
    GROUPS.append(group)
    return group


def wait_json(path, timeout=5):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if path.exists():
            try:
                return json.loads(path.read_text())
            except json.JSONDecodeError:
                pass
        threading.Event().wait(0.005)
    raise AssertionError(f"Barrera de nacimiento no alcanzada: {path.name}")


def witness(path):
    out = (path / "witness-stdout.txt").open("wb")
    err = (path / "witness-stderr.txt").open("wb")
    proc = subprocess.Popen(
        [sys._base_executable, str(FIXTURE), "witness", str(path)],
        stdin=subprocess.PIPE,
        stdout=out,
        stderr=err,
        cwd=path,
        env=environment(path),
        creationflags=0x8 | 0x08000000,
    )
    out.close()
    err.close()
    identity = wait_json(path / "witness-born.json")
    assert identity["pid"] == proc.pid
    assert identity["birth"] == KernelGroup.creation_time(int(proc._handle))
    (path / "witness-creation.json").write_text(
        json.dumps(
            {
                "argv": proc.args,
                "pid": proc.pid,
                "birth": identity["birth"],
                "handle": int(proc._handle),
            }
        )
    )
    return proc


def stop_witness(proc):
    if proc.poll() is None:
        proc.terminate()
    proc.wait(timeout=5)
    assert KernelGroup.wait(int(proc._handle), 0)
    proc.stdin.close()


def test_suspended_birth_assign_before_resume_and_tree_cleanup():
    path = area("suspended")
    foreign = witness(path)
    group = create(path)
    try:
        assert group.member(group.process), "El handle real no pertenece al Job propio"
        assert not (path / "leader-born.json").exists(), "Trabajo antes de ResumeThread"
        assert not group.member(int(foreign._handle))
        group.resume()
        info = wait_json(path / "tree.json")
        member = group.register(info["pid"], info["birth"])
        assert group.member(member)
        assert group.wait(member, 0) is False
        group.seal_births()
        from app.worker.custody_windows import k

        buf = ctypes.create_string_buffer(4096)
        assert k.QueryInformationJobObject(group.job.value, 3, buf, len(buf), None)
        count = ctypes.c_uint32.from_buffer(buf, 4).value
        pids = (ctypes.c_size_t * count).from_buffer(buf, 8)
        print("job-live", list(pids), "total", group.accounting().total)
        query = k.QueryFullProcessImageNameW
        query.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_void_p,
            ctypes.c_void_p,
        ]
        query.restype = ctypes.c_int
        for pid in pids:
            handle = k.OpenProcess(0x1000, False, pid)
            text = ctypes.create_unicode_buffer(1024)
            size = ctypes.c_uint32(1024)
            assert query(handle, 0, text, ctypes.byref(size))
            print("job-image", pid, text.value)
            KernelGroup.raw_close(handle)
        assert group.close(5), (
            f"No se confirmaron waits y cierres de todo el árbol: {group.disposition}"
        )
        assert foreign.poll() is None
        assert group.disposition["waited_members"] == 2
    finally:
        group.close(5)
        stop_witness(foreign)


def test_parent_real_death_kills_tree_foreign_witness_survives():
    path = area("parent-death")
    foreign = witness(path)
    parent = subprocess.Popen(
        [sys._base_executable, str(PHASE.parent / "parent.py"), str(path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        cwd=ROOT,
        env={
            **environment(path),
            "PYTHONPATH": os.pathsep.join(
                [str(ROOT / "apps/server"), str(ROOT / ".venv/Lib/site-packages")]
            ),
            "CUSTODY_RUN_UUID": os.environ.get("CUSTODY_RUN_UUID", ""),
            "COVERAGE_FILE": os.environ.get("COVERAGE_FILE", ""),
            "COVERAGE_RCFILE": os.environ.get("COVERAGE_RCFILE", ""),
            "CUSTODY_SOURCE_SHA256": os.environ.get("CUSTODY_SOURCE_SHA256", ""),
        },
        creationflags=0x8 | 0x08000000,
    )
    handles = []
    try:
        identities = wait_json(path / "parent-ready.json")
        # Sólo referencias a procesos; jamás duplicar el Job en el witness.
        handles = [KernelGroup.open_identity(v["pid"], v["birth"]) for v in identities]
        parent.terminate()
        parent.wait(timeout=5)
        assert all(KernelGroup.wait(h, 5000) for h in handles), (
            "Árbol sobrevivió al padre"
        )
        assert foreign.poll() is None
    finally:
        for handle in handles:
            # Cleanup del baseline fallido: autoridad exacta de nacimiento retenida.
            if not KernelGroup.wait(handle, 0):
                KernelGroup.terminate_process(handle)
                assert KernelGroup.wait(handle, 5000)
            KernelGroup.raw_close(handle)
        if parent.poll() is None:
            parent.terminate()
            parent.wait(timeout=5)
        parent.stdin.close()
        (path / "parent-stderr.txt").write_bytes(parent.stderr.read())
        (path / "parent-exit.json").write_text(
            json.dumps(
                {
                    "argv": parent.args,
                    "pid": parent.pid,
                    "exit_code": parent.returncode,
                    "process_handle_signaled": KernelGroup.wait(int(parent._handle), 0),
                }
            )
        )
        parent.stderr.close()
        stop_witness(foreign)


@pytest.mark.parametrize("mode", ["normal", "silent", "blocked", "fullpipe"])
def test_full_custody_normal_deadline_and_blocked_writer(mode):
    from app.worker.custody import Owner, State

    path = area("owner-" + mode)
    foreign = witness(path)
    owner = Owner(create(path, mode), ID, "epoch", deadline=2)
    try:
        owner.start()
        assert owner.ready.wait(5)
        if mode == "blocked":
            owner.send(
                {
                    "version": 1,
                    "execution_id": ID,
                    "epoch": "epoch",
                    "seq": 2,
                    "kind": "stop",
                    "payload": {"padding": ["x" * 8192] * 30},
                }
            )
            assert owner.writer_started.wait(2)
            end = time.monotonic() + 1
            while owner.group.written_bytes < 4096 and time.monotonic() < end:
                threading.Event().wait(0.005)
            assert owner.group.written_bytes >= 4096
            assert owner.group.write_started > owner.group.write_completed
        receipt = owner.join(8)
        assert receipt.state == State.CLOSED_CONFIRMED
        assert receipt.resources_returned and receipt.streams_confirmed
        assert receipt.kernel["waited_members"] == 2
        assert receipt.kernel["writer_waited"]
        assert len(owner.stderr) <= 16384
        if mode == "fullpipe":
            assert len(owner.stderr) == 16384
        assert foreign.poll() is None
        (path / "receipt.json").write_text(
            json.dumps(
                {
                    "state": receipt.state,
                    "resources_returned": receipt.resources_returned,
                    "streams": receipt.streams_confirmed,
                    "reason": receipt.reason,
                    "kernel": receipt.kernel,
                },
                indent=2,
            )
        )
    finally:
        owner.cancel()
        owner.join(8)
        stop_witness(foreign)


def test_explicit_concurrent_and_coroutine_cancel_retains_finalizer():
    from app.worker.custody import Owner, State

    path = area("async-cancel")
    owner = Owner(create(path), ID, "epoch", deadline=10)
    owner.start()
    assert owner.ready.wait(5)

    async def exercise():
        task = asyncio.create_task(owner.wait())
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(exercise())
    threads = [threading.Thread(target=owner.cancel) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    receipt = owner.join(8)
    assert receipt.state == State.CLOSED_CONFIRMED
    assert receipt.resources_returned
    assert owner.join(0) is receipt
    assert not owner.finalizer.is_alive()


@pytest.mark.parametrize(
    "mode", ["eof", "truncated", "invalid", "flood", "backpressure"]
)
def test_bad_transport_unknown_but_owned_tree_terminated(mode):
    from app.worker.custody import Owner, State

    path = area("bad-" + mode)
    owner = Owner(create(path, mode), ID, "epoch", deadline=2)
    owner.start()
    receipt = owner.join(8)
    assert receipt.state == State.UNKNOWN_QUARANTINED
    assert not receipt.resources_returned
    assert receipt.reason == "transport_error"
    assert receipt.kernel["waited_members"] == 2
    assert receipt.kernel["terminated"]
    (path / "receipt.json").write_text(
        json.dumps(
            {
                "state": receipt.state,
                "resources_returned": receipt.resources_returned,
                "streams": receipt.streams_confirmed,
                "reason": receipt.reason,
                "kernel": receipt.kernel,
            },
            indent=2,
        )
    )


def test_reused_handle_never_closes_foreign_object():
    path = area("reused")
    foreign = witness(path)
    group = create(path)
    try:
        original = group.job.value
        KernelGroup.raw_close(original)
        # Sustituir valor por handle REAL ajeno: CompareObjectHandles debe rechazarlo.
        group.job.value = int(foreign._handle)
        assert not group.close(5)
        assert foreign.poll() is None
        assert KernelGroup.wait(int(foreign._handle), 0) is False
        assert group.disposition["unknown"]
    finally:
        group.contain_unknown()
        stop_witness(foreign)


def test_native_numeric_handle_reuse_keeps_foreign_kernel_object_alive():
    from app.worker.custody_windows import H, k

    path = area("numeric-reuse")
    foreign = witness(path)
    group = create(path)
    duplicates = []
    try:
        original = group.job.value
        KernelGroup.raw_close(original)
        current = k.GetCurrentProcess()
        reused = None
        for _ in range(1024):
            out = H()
            assert k.DuplicateHandle(
                current, int(foreign._handle), current, ctypes.byref(out), 0, False, 2
            )
            duplicates.append(out.value)
            if out.value == original:
                reused = out.value
                break
        assert reused == original, (
            "No se obtuvo reutilización numérica real; prueba inconcluyente"
        )
        assert k.CompareObjectHandles(reused, int(foreign._handle))
        assert not k.CompareObjectHandles(reused, group.job.escrow)
        assert not group.close(5)
        assert group.disposition["unknown"] and not group.closed
        assert KernelGroup.wait(reused, 0) is False
        assert foreign.poll() is None
        (path / "numeric-reuse-proof.json").write_text(
            json.dumps(
                {
                    "original_job_value": original,
                    "reused_foreign_value": reused,
                    "same_foreign_kernel_object": True,
                    "different_job_kernel_object": True,
                    "kernel_disposition": group.disposition,
                }
            )
        )
    finally:
        group.contain_unknown()
        for handle in duplicates:
            KernelGroup.raw_close(handle)
        stop_witness(foreign)


def test_supplementary_wrong_escrow_never_terminates_foreign_job_witness():
    from app.worker.custody_windows import k

    path = area("wrong-escrow")
    foreign = witness(path)
    foreign_job = k.CreateJobObjectW(None, None)
    assert foreign_job
    assert k.AssignProcessToJobObject(foreign_job, int(foreign._handle))
    group = create(path)
    old_escrow = group.job.escrow
    try:
        group.job.escrow = foreign_job
        assert not group.close(5)
        assert not KernelGroup.wait(int(foreign._handle), 250), (
            "Se terminó un Job ajeno"
        )
        assert foreign.poll() is None
    finally:
        group.job.escrow = old_escrow
        group.contain_unknown()
        KernelGroup.raw_close(foreign_job)
        stop_witness(foreign)


def test_native_layout_limits_and_handles_not_inheritable():
    from app.worker.custody_windows import (
        Accounting,
        Limits,
        ProcessInfo,
        Security,
        Startup,
        StartupEx,
        k,
    )

    assert ctypes.sizeof(ctypes.c_void_p) == 8  # Esta unidad acredita Win11 x64.
    assert [
        ctypes.sizeof(t)
        for t in (Security, Startup, StartupEx, ProcessInfo, Limits, Accounting)
    ] == [24, 104, 112, 24, 144, 48]
    path = area("layout")
    group = create(path)
    try:
        limits = Limits()
        assert k.QueryInformationJobObject(
            group.job.value, 9, ctypes.byref(limits), ctypes.sizeof(limits), None
        )
        assert limits.basic.flags == 0x2000
        for h in (
            group.job,
            group.process,
            group.thread,
            group.stdin,
            group.stdout,
            group.stderr,
        ):
            for value in (h.value, h.escrow, h._anchor):
                flags = ctypes.c_uint32()
                assert k.GetHandleInformation(value, ctypes.byref(flags))
                assert flags.value & 1 == 0
        group.seal_births()
        assert group.close(5)
    finally:
        group.close(5)


def test_unregistered_birth_is_unknown_and_all_owned_native_handles_signal():
    path = area("unknown-member")
    group = create(path)
    member = None
    try:
        group.resume()
        info = wait_json(path / "tree.json")
        member = KernelGroup.open_identity(info["pid"], info["birth"])
        assert group.member(member)
        group.seal_births()  # Contrato incumplido a propósito: falta registro.
        assert not group.close(5)
        assert KernelGroup.wait(member, 5000)
        assert not group.closed and group.disposition["unknown"]
    finally:
        group.contain_unknown()
        if member:
            KernelGroup.raw_close(member)


@pytest.mark.parametrize(
    "fault", ["query", "close", "assign", "resume", "wait", "register"]
)
def test_supplementary_controlled_fault_unknown_not_native_api_failure_proof(
    monkeypatch, fault
):
    from app.worker import custody_windows as native

    path = area("fault-" + fault)
    if fault == "assign":
        with monkeypatch.context() as patch:
            patch.setattr(native.k, "AssignProcessToJobObject", lambda *_: False)
            with pytest.raises(OSError):
                create(path)
        assert not (path / "leader-born.json").exists()
        group = native.QUARANTINED[-1]
        assert KernelGroup.wait(group.process.escrow, 0)
        return
    group = create(path)
    try:
        if fault == "resume":
            with monkeypatch.context() as patch:
                patch.setattr(native.k, "ResumeThread", lambda *_: 0xFFFFFFFF)
                with pytest.raises(OSError):
                    group.resume()
            assert not (path / "leader-born.json").exists()
            group.contain_unknown()
            assert KernelGroup.wait(group.process.escrow, 0)
            return
        group.resume()
        info = wait_json(path / "tree.json")
        member = group.register(info["pid"], info["birth"])
        group.seal_births()
        if fault == "register":
            with pytest.raises(ValueError):
                group.register(info["pid"], info["birth"])
            assert group.close(5)
            return
        with monkeypatch.context() as patch:
            if fault == "query":
                patch.setattr(native.k, "QueryInformationJobObject", lambda *_: False)
            elif fault == "close":
                real = native.k.CloseHandle
                patch.setattr(
                    native.k,
                    "CloseHandle",
                    lambda h: False if h == group.stdout.value else real(h),
                )
            else:
                patch.setattr(group, "wait", lambda *_: False)
            assert not group.close(1)
        assert not group.closed
        group.contain_unknown()
        assert (
            KernelGroup.wait(member.escrow if member.escrow else member.value, 5000)
            if not member.closed
            else True
        )
    finally:
        group.contain_unknown()


@pytest.mark.parametrize("deadline", [0, -1, float("nan"), True, 3601])
def test_supplementary_deadline_validation(deadline):
    from app.worker.custody import Owner

    with pytest.raises(ValueError):
        Owner(None, ID, "epoch", deadline)


def test_internal_entrypoint_is_fixed_not_request_executable():
    path = area("entrypoint")
    with pytest.raises(ValueError):
        KernelGroup._validate(
            sys._base_executable,
            [
                sys._base_executable,
                str(ROOT / "scripts/init_env.py"),
                "silent",
                str(path),
                ID,
                "epoch",
            ],
            path,
            environment(path),
        )


def test_no_output_deadline_keeps_unknown_births_and_waits_actual_tree():
    from app.worker.custody import Owner, State

    path = area("no-output")
    group = create(path, "no_output")
    owner = Owner(group, ID, "epoch", deadline=1)
    owner.start()
    info = wait_json(path / "tree.json")
    handle = KernelGroup.open_identity(info["pid"], info["birth"])
    try:
        assert group.member(handle)
        receipt = owner.join(8)
        assert receipt.state == State.UNKNOWN_QUARANTINED
        assert not receipt.resources_returned and not owner.ready.is_set()
        assert KernelGroup.wait(handle, 5000)
        assert receipt.kernel["terminated"]
    finally:
        owner.cancel()
        owner.join(8)
        KernelGroup.raw_close(handle)


@pytest.mark.parametrize("fault", ["containment", "disposition"])
def test_fix1_repeated_containment_failure_has_finite_unknown_receipt(fault):
    from app.worker.custody import OWNERS, Owner, Receipt, State

    class InjectedBackend:
        closed = False
        attempts = 0

        @property
        def disposition(self):
            if fault == "disposition":
                raise RuntimeError("controlled disposition query fault")
            return {"injection": "supplementary-memory-repeated-containment"}

        def resume(self):
            raise OSError("controlled resume fault")

        def terminate(self, timeout):
            if fault == "containment":
                self.contain_unknown()
            return False

        def contain_unknown(self):
            self.attempts += 1
            raise OSError("controlled containment fault")

    group = InjectedBackend()
    owner = Owner(group, ID, "epoch", 1)
    owner.start()
    owner.finalizer.join(2)
    assert not owner.finalizer.is_alive()
    if fault == "containment":
        assert group.attempts == 2
    assert owner.done.is_set(), (
        "Exited finalizer omitted done after containment failure"
    )
    assert isinstance(owner.receipt, Receipt)
    assert owner.receipt.state == State.UNKNOWN_QUARANTINED
    assert not owner.receipt.resources_returned
    assert owner in OWNERS and owner.group is group
    assert owner.receipt.kernel["error_code"] == "finalizer_failure"
    assert asyncio.run(asyncio.wait_for(owner.wait(), 1)) is owner.receipt


def test_fix1_done_barrier_waits_actual_thread_exit_without_spurious_timeout():
    from app.worker.custody import OWNERS, Owner, Receipt, State

    owner = Owner(object(), ID, "epoch", 1)
    signaled, release, exited = (threading.Event() for _ in range(3))
    path = area("fix1-thread-barrier")
    stages = []

    def finalizer():
        owner.receipt = Receipt(State.UNKNOWN_QUARANTINED, False, False, {}, "test")
        owner.done.set()
        stages.append("done-set")
        signaled.set()
        assert release.wait(2)
        stages.append("thread-exit")
        exited.set()

    owner.finalizer = threading.Thread(target=finalizer, daemon=False)
    OWNERS.add(owner)
    owner.finalizer.start()
    assert signaled.wait(1)

    async def exercise():
        task = asyncio.create_task(owner.wait())
        # Yield to the real wait while the real finalizer is held after done.set.
        for _ in range(3):
            await asyncio.sleep(0)
        stages.append("caller-yielded-before-release")
        release.set()
        return await asyncio.wait_for(task, 2)

    try:
        assert asyncio.run(exercise()) is owner.receipt
        assert exited.is_set() and not owner.finalizer.is_alive()
        assert owner in OWNERS
    finally:
        release.set()
        owner.finalizer.join(2)
        (path / "barriers.json").write_text(
            json.dumps(
                {
                    "stages": stages,
                    "thread_ident": owner.finalizer.ident,
                    "exited": exited.is_set(),
                    "join_bound_seconds": 2,
                }
            )
        )


@pytest.mark.parametrize("fault", ["get_times", "mismatch_close"])
def test_fix1_actual_openprocess_retained_before_identity_fault(monkeypatch, fault):
    from app.worker import custody_windows as native

    path = area("fix1-open-" + fault)
    foreign = witness(path)
    group = create(path)
    captured, cleanup = [], []
    open_process, get_times, close = (
        native.k.OpenProcess,
        native.k.GetProcessTimes,
        native.k.CloseHandle,
    )
    birth = group.birth

    def capture(*args):
        handle = open_process(*args)
        if handle:
            captured.append(handle)
            cleanup.append(native.Guard(handle))
        return handle

    def fault_times(*args):
        return False if args[0] in captured else get_times(*args)

    def fault_close(handle):
        return False if handle in captured else close(handle)

    try:
        group.resume()
        with monkeypatch.context() as patch:
            patch.setattr(native.k, "OpenProcess", capture)
            if fault == "get_times":
                patch.setattr(native.k, "GetProcessTimes", fault_times)
            else:
                patch.setattr(native.k, "CloseHandle", fault_close)
            with pytest.raises(OSError):
                group.register(group.pid, birth if fault == "get_times" else birth + 1)
        assert captured and cleanup[0].valid()
        retained = [h for h in group.handles if h.value == captured[0]]
        (path / "injection.json").write_text(
            json.dumps(
                {
                    "fault": fault,
                    "controlled_injection_not_spontaneous_winapi_failure": True,
                    "pid": group.pid,
                    "birth": birth,
                    "open_handle": captured[0],
                    "retained_by_group": bool(retained),
                    "cleanup_anchor": cleanup[0]._anchor,
                    "foreign_alive": foreign.poll() is None,
                }
            )
        )
        assert retained, (
            "Actual OpenProcess object lost before owning group registration"
        )
        assert retained[0].valid()
        assert native.k.CompareObjectHandles(retained[0].value, cleanup[0]._anchor)
        assert group.unknown and not group.closed
        assert foreign.poll() is None
    finally:
        group.contain_unknown()
        assert KernelGroup.wait(group.process.escrow, 5000)
        # RED cleanup uses only the actual object retained before fault injection.
        for guard in cleanup:
            if guard.valid():
                assert guard.close()
        assert foreign.poll() is None
        stop_witness(foreign)


def test_supplementary_duplicate_failure_does_not_orphan_suspended_real_child(
    monkeypatch,
):
    from app.worker import custody_windows as native

    path = area("duplicate-failure")
    duplicate, create_process = native.k.DuplicateHandle, native.k.CreateProcessW
    retained = []
    captured_original = []
    count = 0

    def capture(*args):
        result = create_process(*args)
        if result:
            info = ctypes.cast(args[-1], ctypes.POINTER(native.ProcessInfo)).contents
            captured_original.append(info.process)
            ref = native.H()
            current = native.k.GetCurrentProcess()
            assert duplicate(
                current, info.process, current, ctypes.byref(ref), 0, False, 2
            )
            retained.append(ref.value)
        return result

    def fail(*args):
        nonlocal count
        count += 1
        return (
            False
            if captured_original and args[1] == captured_original[0]
            else duplicate(*args)
        )

    try:
        with monkeypatch.context() as patch:
            patch.setattr(native.k, "CreateProcessW", capture)
            patch.setattr(native.k, "DuplicateHandle", fail)
            with pytest.raises(OSError):
                create(path)
        assert retained
        assert KernelGroup.wait(retained[0], 0), (
            "Hijo suspendido huérfano tras fallo de escrow"
        )
        assert not (path / "leader-born.json").exists()
    finally:
        for handle in retained:
            if not KernelGroup.wait(handle, 0):
                KernelGroup.terminate_process(handle)
                assert KernelGroup.wait(handle, 5000)
            KernelGroup.raw_close(handle)


@pytest.mark.parametrize("mode", ["truncated", "invalid", "normal"])
def test_real_wire_held_until_draining_retains_owner(mode):
    """Entrega controlada de bytes leídos del pipe real, sin falsificar transporte."""
    from app.worker.custody import OWNERS, Owner, State
    from app.worker.pipe_protocol import Decoder, Session

    path = area("drain-" + mode)
    group = create(path, mode)
    owner = Owner(group, ID, "epoch", 4)
    original_read, original_write = group.read_available, group.write
    held, captured = bytearray(), threading.Event()
    timeline = []
    foreign = witness(path)
    preview = Decoder(Session(ID, "epoch", "child"))
    strong_refs = list(group.handles)
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
        if held and (mode != "normal" or captured.is_set()):
            if owner.state != State.DRAINING:
                return b""
            wire = bytes(held)
            held.clear()
            event("drain_delivery", wire_hex=wire.hex())
            return wire
        chunk = original_read(fd)
        if mode == "normal" and chunk:
            for message in preview.feed(chunk):
                if message["kind"] == "closed":
                    captured.set()
        if chunk and owner.ready.is_set() and owner.state != State.DRAINING:
            held.extend(chunk)
            event("native_read_held", wire_hex=chunk.hex())
            if mode != "normal":
                captured.set()
            return b""
        if chunk is None and held and owner.state != State.DRAINING:
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
        native_waits = []
        proof = {
            "authorities": authorities,
            "native_waits": native_waits,
            "foreign_alive_before_decision": foreign.poll() is None,
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
            "handles": [
                {"value": h.value, "escrow": h.escrow, "closed": h.closed}
                for h in strong_refs
            ],
        }
        (
            Path(os.environ.get("STUDIO_TEST_ROOT", "/proof"))
            / ("drain-" + mode + ".json")
        ).write_text(json.dumps(proof, indent=2))
        deliveries = [v for v in timeline if v["event"] == "drain_delivery"]
        assert proof["foreign_alive_before_decision"]
        assert deliveries and deliveries[0]["stop"]
        if mode != "normal":
            assert deliveries[0]["wire_hex"] == (
                "000000107b" if mode == "truncated" else "000000027b7d"
            )
        assert owner.stdout_eof and owner.stderr_eof
        assert owner.messages.empty() and not owner.saw_closed
        if mode == "normal":
            assert owner.decoder.session.frames == 3
            assert receipt.release_gate and receipt.reason == "cancelled"
            return
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
            alive_before_cleanup = foreign.poll() is None
            stop_witness(foreign)
            (path / "foreign-cleanup.json").write_text(
                json.dumps(
                    {
                        "alive_before_cleanup": alive_before_cleanup,
                        "actual_exit": foreign.returncode,
                        "waited": KernelGroup.wait(int(foreign._handle), 0),
                    }
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
def test_stopping_native_pipe_validates_without_effects(case):
    """Physical private pipe checks decoder boundaries; no closure certificate."""
    import importlib

    from app.worker.custody import Owner, State

    protocol = importlib.import_module("app.worker.pipe_protocol")
    backend = importlib.import_module("app.worker.custody_windows")
    path = area("pipe-drain-" + case)
    group = create(path)
    reader, writer = group._pipe(True)
    saved = group.stdout
    group.stdout = reader
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
        count = backend.W.DWORD()
        backend.checked(
            backend.k.WriteFile(
                writer.value, data, len(data), ctypes.byref(count), None
            )
        )
        assert count.value == len(data)
        owner._read(parsing=False)

    try:
        ready = wire("ready", 1)
        if case == "valid":
            feed(ready + wire("result", 2) + wire("closed", 3))
            assert writer.close()
            writer = None
            owner._read(parsing=False)
            assert owner.stdout_eof and owner.decoder.session.frames == 3
        elif case == "truncated":
            feed(b"\x00\x00\x00\x10{")
            assert writer.close()
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
        group.stdout = saved
        try:
            group.contain_unknown()
        finally:
            reader.close()
            if writer is not None:
                assert writer.close()
