"""Supervisor stdlib, fuera del PGID; autoridad por hijos propios, no escaneo."""

import ctypes
import json
import os
import selectors
import signal
import socket
import sys
import time
from pathlib import Path


def birth(pid):
    return int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19])


def subreaper():
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int] + [ctypes.c_ulong] * 4
    libc.prctl.restype = ctypes.c_int
    if libc.prctl(36, 1, 0, 0, 0):
        raise OSError(ctypes.get_errno(), "subreaper")
    value = ctypes.c_int()
    if libc.prctl(37, ctypes.addressof(value), 0, 0, 0) or value.value != 1:
        raise OSError("subreaper no confirmado")


def close_except(keep):
    for name in os.listdir("/proc/self/fd"):
        fd = int(name)
        if fd not in keep:
            try:
                os.close(fd)
            except OSError:
                pass  # descriptor temporal de listdir ya cerrado.



def terminal_ack(control, live):
    """Drena stop pendiente hasta ACK; presupuesto finito, sin borrar incertidumbre."""
    control.setblocking(False)
    end = time.monotonic() + 1
    with selectors.DefaultSelector() as selector:
        selector.register(control, selectors.EVENT_READ, "control")
        selector.register(live, selectors.EVENT_READ, "live")
        while time.monotonic() < end:
            for key, _ in selector.select(max(0, end - time.monotonic())):
                if key.data == "live":
                    if not os.read(live, 1):
                        return True  # Padre muerto: ya se hizo reap de hijos propios.
                else:
                    command = control.recv(1024)
                    if command == b"final_ack":
                        return True
                    if command != b"stop":
                        return False
    return False


def main():
    if sys.argv[3] == "audio":
        return audio_supervisor()
    live, control_fd = map(int, sys.argv[1:3])
    mode, root, execution, epoch = sys.argv[3:7]
    root = Path(root)
    control = socket.socket(fileno=control_fd)
    os.set_blocking(live, False)
    registry, workload_registry = socket.socketpair(
        socket.AF_UNIX, socket.SOCK_SEQPACKET
    )
    gate_r, gate_w = os.pipe()
    born_r, born_w = os.pipe()
    subreaper()
    leader = os.fork()
    if leader == 0:
        os.close(gate_w)
        os.setsid()
        close_except({0, 1, 2, gate_r, born_w, workload_registry.fileno()})
        os.write(born_w, b"B")
        os.close(born_w)
        if os.read(gate_r, 1) != b"R":
            os._exit(125)
        os.close(gate_r)
        os.set_inheritable(workload_registry.fileno(), True)
        fixture = (
            Path(__file__).resolve().parents[2]
            / "tests/fixtures/worker_custody_linux_child.py"
        )
        os.execve(
            sys.executable,
            [
                sys.executable,
                "-B",
                str(fixture),
                mode,
                str(root),
                execution,
                epoch,
                str(workload_registry.fileno()),
            ],
            dict(os.environ),
        )
    record = {
        "leader": leader,
        "pgid": leader,
        "supervisor": os.getpid(),
        "supervisor_pgid": os.getpgrp(),
        "subreaper": True,
        "registered": [],
        "waited": [],
        "liveness_writer_inherited": False,
        "confirmed": False,
    }
    refs = {}
    pending_refs = []  # Captura inmediata, aún SIN autoridad de señalización.
    leader_ref = None
    released = sealed = uncertain = False
    reason = "supervisor_exception"

    def journal():
        temp = root / "supervisor-journal.tmp"
        nonlocal uncertain
        try:
            temp.write_text(json.dumps(record))
            temp.replace(root / "supervisor-journal.json")
            return True
        except (OSError, ValueError, TypeError) as error:
            uncertain = True
            record["journal_error_errno"] = getattr(error, "errno", None)
            record["confirmed"] = False
            return False

    def notify(value):
        nonlocal uncertain
        try:
            control.send(json.dumps(value).encode())
        except (OSError, ValueError, TypeError):
            uncertain = True

    def cleanup_pause(references, timeout):
        """Un selector auxiliar nunca puede interrumpir señales ni waits propios."""
        nonlocal uncertain
        try:
            with selectors.DefaultSelector() as waiter:
                for ref in references:
                    waiter.register(ref, selectors.EVENT_READ)
                waiter.select(timeout)
        except (OSError, ValueError, KeyError) as error:
            uncertain = True
            record["cleanup_selector_error_errno"] = getattr(error, "errno", None)
            # No depende de crear otro FD cuando el sistema rechaza el selector.
            time.sleep(min(timeout, 0.005))

    try:
        os.close(gate_r)
        os.close(born_w)
        workload_registry.close()
        leader_ref = os.pidfd_open(leader)
        refs[leader] = leader_ref
        with selectors.DefaultSelector() as born_selector:
            born_selector.register(born_r, selectors.EVENT_READ)
            if not born_selector.select(5) or os.read(born_r, 1) != b"B":
                raise OSError("Nacimiento nativo no confirmado")
        os.close(born_r)
        end = time.monotonic() + 5
        while os.getpgid(leader) != leader and time.monotonic() < end:
            with selectors.DefaultSelector() as poller:
                poller.register(leader_ref, selectors.EVENT_READ)
                if poller.select(0.001):
                    raise OSError("líder terminó antes de gate")
        if os.getpgid(leader) != leader:
            raise OSError("grupo no confirmado")
        record["birth"] = birth(leader)
        record["native_kernel"] = os.uname().release
        record["python"] = sys.version.split()[0]
        record["leader_pidfd_identity"] = [
            os.fstat(leader_ref).st_dev,
            os.fstat(leader_ref).st_ino,
        ]
        record["liveness_read_identity"] = [
            os.fstat(live).st_dev,
            os.fstat(live).st_ino,
        ]
        record["workload_inheritance"] = [0, 1, 2, "birth_registry_only"]

        if not journal():
            raise OSError("Journal inicial no disponible")
        notify(dict(kind="born", **record))
        # Sólo el workload escribe transporte. Estos duplicados del supervisor
        # no deben retrasar EOF físico hasta su salida/flush de instrumentación.
        os.close(0)
        os.close(1)
        os.close(2)
        reason = "deadline"
        with selectors.DefaultSelector() as selector:
            selector.register(live, selectors.EVENT_READ, "live")
            selector.register(control, selectors.EVENT_READ, "control")
            selector.register(registry, selectors.EVENT_READ, "registry")
            selector.register(leader_ref, selectors.EVENT_READ, "leader")
            end = time.monotonic() + 3600
            running = True
            while running and time.monotonic() < end:
                for key, _ in selector.select(0.05):
                    if not running:
                        break
                    if key.data == "live":
                        if not os.read(live, 1):
                            record["liveness_eof_observed"] = True
                            reason, running = "parent_eof", False
                    elif key.data == "leader":
                        reason, running = "leader_exit", False
                    elif key.data == "control":
                        data = control.recv(1024)
                        if data == b"resume" and not released:
                            os.write(gate_w, b"R")
                            os.close(gate_w)
                            released = True
                        elif data == b"seal" and len(refs) == 2:
                            sealed = True
                            notify({"kind": "sealed"})
                        elif data == b"stop":
                            reason, running = "stop", False
                        elif not data:
                            try:
                                eof = not os.read(live, 1)
                            except BlockingIOError:
                                eof = False
                            record["liveness_eof_observed"] = eof
                            reason, running = (
                                "parent_eof" if eof else "control_eof",
                                False,
                            )
                            uncertain |= not eof
                        else:
                            uncertain, running = True, False
                    elif key.data == "registry":
                        data = registry.recv(1024)
                        if not data:
                            selector.unregister(registry)
                            continue
                        member = json.loads(data)
                        pid = member["pid"]
                        candidate = os.pidfd_open(pid)
                        pending_refs.append(candidate)
                        if (
                            sealed
                            or len(refs) != 1
                            or os.getpgid(pid) != leader
                            or birth(pid) != member["birth"]
                        ):
                            uncertain, running = True, False
                            continue
                        refs[pid] = candidate
                        pending_refs.remove(candidate)
                        record["registered"].append(member)
                        if not journal():
                            reason, running = "journal_error", False
                            continue
                        registry.send(b"R")
                        notify(dict(kind="member", **member))
    except (OSError, ValueError, KeyError, TypeError) as error:
        uncertain = True
        record["supervisor_error_type"] = type(error).__name__
    finally:
        uncertain |= sys.exc_info()[0] is not None
        if not released:
            try:
                os.close(gate_w)
            except OSError:
                uncertain = True
        record.update(reason=reason, births_sealed=sealed)
        try:
            identity = os.waitid(
                os.P_PIDFD if leader_ref is not None else os.P_PID,
                leader_ref if leader_ref is not None else leader,
                os.WEXITED | os.WNOHANG | os.WNOWAIT,
            )
            retained = identity is None or identity.si_pid == leader
        except (OSError, ChildProcessError):
            retained = False
        try:
            group_authority = retained and os.getpgid(leader) == leader
        except OSError:
            uncertain = True
            group_authority = False
        record["leader_retained_before_signals"] = retained
        if not record["leader_retained_before_signals"]:
            uncertain = True
        for pid in refs:
            try:
                uncertain |= os.getpgid(pid) != leader
            except OSError:
                uncertain = True
        if group_authority:
            try:
                os.killpg(leader, signal.SIGTERM)
                record["term_sent"] = True
            except OSError:
                uncertain = True
            if leader_ref is not None:
                cleanup_pause([leader_ref], 0.05)
            try:
                os.killpg(leader, signal.SIGKILL)
                record["kill_sent"] = True
            except OSError:
                uncertain = True
        if uncertain or not group_authority:
            for ref in refs.values():
                try:
                    signal.pidfd_send_signal(ref, signal.SIGKILL)
                except OSError:
                    uncertain = True
        end = time.monotonic() + 5
        no_children = False
        while time.monotonic() < end:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                no_children = True
                break
            if pid:
                record["waited"].append({"pid": pid, "status": status})
                if pid not in refs:
                    uncertain = True
            else:
                cleanup_pause(refs.values(), 0.005)
        record["echild"] = no_children
        record["descendants_waited"] = no_children and {
            v["pid"] for v in record["waited"]
        } == set(refs)
        record["confirmed"] = (
            record["descendants_waited"]
            and not uncertain
            and (not released or len(refs) == 2)
        )
        journal()
        record["confirmed"] &= not uncertain
        notify(dict(kind="final", **record))
        record["confirmed"] &= not uncertain
        acknowledged = not record["confirmed"] or terminal_ack(control, live)
        for ref in refs.values():
            os.close(ref)
        for ref in pending_refs:
            os.close(ref)
        registry.close()
        control.close()
        os.close(live)
        if not acknowledged:
            raise OSError("Terminal sin ACK del padre vivo")


def audio_supervisor():
    """Altas y reap secuenciales: pidfd retenido hasta confirmación de kernel."""
    live, control_fd = map(int, sys.argv[1:3])
    (
        _,
        root,
        execution,
        epoch,
        project,
        plan_sha256,
        plan_bytes,
        context_sha256,
        context_bytes,
    ) = sys.argv[3:12]
    control = socket.socket(fileno=control_fd)
    registry, workload = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    gate_r, gate_w = os.pipe()
    born_r, born_w = os.pipe()
    subreaper()
    leader = os.fork()
    if leader == 0:
        os.close(gate_w)
        os.close(born_r)
        os.setsid()
        close_except({0, 1, 2, gate_r, born_w, workload.fileno()})
        os.write(born_w, b"B")
        os.close(born_w)
        if os.read(gate_r, 1) != b"R":
            os._exit(125)
        os.close(gate_r)
        os.set_inheritable(workload.fileno(), True)
        entry = Path(__file__).with_name("audio_child.py")
        os.execve(
            sys.executable,
            [
                sys.executable,
                "-B",
                str(entry),
                root,
                project,
                execution,
                epoch,
                str(workload.fileno()),
                plan_sha256,
                plan_bytes,
                context_sha256,
                context_bytes,
            ],
            dict(os.environ),
        )
    workload.close()
    os.close(gate_r)
    os.close(born_w)
    leader_fd = os.pidfd_open(leader)
    active = None
    record = {
        "kind": "final",
        "leader": leader,
        "pgid": leader,
        "supervisor": os.getpid(),
        "subreaper": True,
        "scope": "linux_audio_sequential_pidfd_reap",
        "registered_count": 0,
        "reaped_count": 0,
        "confirmed": False,
        "descendants_waited": False,
    }
    released = sealed = uncertain = False
    reason = "supervisor_exception"
    try:
        if os.read(born_r, 1) != b"B" or os.getpgid(leader) != leader:
            raise OSError("Nacimiento audio no confirmado")
        os.close(born_r)
        born_r = None
        record["birth"] = birth(leader)
        control.send(json.dumps(dict(record, kind="born")).encode())
        os.close(0)
        os.close(1)
        os.close(2)
        os.set_blocking(live, False)
        with selectors.DefaultSelector() as selector:
            for fd, kind in (
                (live, "live"),
                (control, "control"),
                (registry, "registry"),
                (leader_fd, "leader"),
            ):
                selector.register(fd, selectors.EVENT_READ, kind)
            end = time.monotonic() + 3600
            running = True
            while running and time.monotonic() < end:
                for event, _ in selector.select(0.05):
                    if event.data == "live":
                        if not os.read(live, 1):
                            reason, running = "parent_eof", False
                    elif event.data == "leader":
                        reason, running = "leader_exit", False
                    elif event.data == "control":
                        command = control.recv(1024)
                        if command == b"resume" and not released:
                            os.write(gate_w, b"R")
                            os.close(gate_w)
                            gate_w = None
                            released = True
                        elif command == b"seal" and sealed:
                            control.send(b'{"kind":"sealed"}')
                        elif command == b"stop":
                            reason, running = "stop", False
                        else:
                            raise OSError("Control audio inválido")
                    elif event.data == "registry":
                        wire = registry.recv(1025)
                        if not wire:
                            selector.unregister(registry)
                            continue
                        if len(wire) > 1024:
                            raise OSError("Registry audio excedido")
                        message = json.loads(wire)
                        kind = message.get("kind")
                        if kind == "register" and not sealed and active is None:
                            if (
                                message.keys() != {"kind", "pid", "birth"}
                                or record["registered_count"] >= 2048
                            ):
                                raise OSError("Nacimiento audio excedido")
                            pid = message["pid"]
                            if (
                                type(pid) is not int
                                or type(message["birth"]) is not int
                            ):
                                raise OSError("Identidad audio inválida")
                            fd = os.pidfd_open(pid)
                            active = {
                                "pid": pid,
                                "birth": message["birth"],
                                "fd": fd,
                                "exited": False,
                            }
                            fields = (
                                Path(f"/proc/{pid}/stat")
                                .read_text()
                                .rsplit(")", 1)[1]
                                .split()
                            )
                            if (
                                int(fields[1]) != leader
                                or os.getpgid(pid) != leader
                                or birth(pid) != active["birth"]
                            ):
                                raise OSError("Hijo audio ajeno")
                            record["registered_count"] += 1
                            registry.send(b"R")
                        elif kind in {"exited", "reaped"} and active is not None:
                            if message.keys() != {"kind", "pid", "birth", "status"} or (
                                message["pid"],
                                message["birth"],
                            ) != (active["pid"], active["birth"]):
                                raise OSError("Exit audio ajeno")
                            if kind == "exited":
                                with selectors.DefaultSelector() as poller:
                                    poller.register(active["fd"], selectors.EVENT_READ)
                                    if not poller.select(0):
                                        raise OSError("FFmpeg no terminó")
                                fields = (
                                    Path(f"/proc/{active['pid']}/stat")
                                    .read_text()
                                    .rsplit(")", 1)[1]
                                    .split()
                                )
                                status = os.waitstatus_to_exitcode(int(fields[49]))
                                if (
                                    fields[0] != "Z"
                                    or birth(active["pid"]) != active["birth"]
                                    or status != message["status"]
                                ):
                                    raise OSError("Estado FFmpeg distinto")
                                active.update(exited=True, status=status)
                                registry.send(b"E")
                            else:
                                fdinfo = Path(
                                    f"/proc/self/fdinfo/{active['fd']}"
                                ).read_text()
                                if (
                                    not active["exited"]
                                    or message["status"] != active["status"]
                                    or "Pid:\t-1\n" not in fdinfo
                                ):
                                    raise OSError("Reap FFmpeg no confirmado")
                                os.close(active["fd"])
                                active = None
                                record["reaped_count"] += 1
                                registry.send(b"W")
                        elif (
                            kind == "seal"
                            and message.keys() == {"kind"}
                            and active is None
                            and not sealed
                        ):
                            sealed = True
                            registry.send(b"S")
                        else:
                            raise OSError("Registry audio fuera de secuencia")
    except (OSError, ValueError, KeyError, TypeError) as error:
        uncertain = True
        record["error_type"] = type(error).__name__
    finally:
        uncertain |= sys.exc_info()[0] is not None
        if gate_w is not None:
            os.close(gate_w)
        if born_r is not None:
            os.close(born_r)
        try:
            retained = os.waitid(
                os.P_PIDFD, leader_fd, os.WEXITED | os.WNOHANG | os.WNOWAIT
            )
            if retained is not None and retained.si_pid != leader:
                raise OSError("Líder retenido distinto")
            if os.getpgid(leader) != leader:
                raise OSError("Grupo líder distinto")
            os.killpg(leader, signal.SIGTERM)
            os.killpg(leader, signal.SIGKILL)
        except (OSError, ChildProcessError):
            uncertain = True
            try:
                signal.pidfd_send_signal(leader_fd, signal.SIGKILL)
            except OSError:
                uncertain = True
        if active is not None:
            try:
                signal.pidfd_send_signal(active["fd"], signal.SIGKILL)
            except OSError:
                uncertain = True
        expected = {leader} | ({active["pid"]} if active is not None else set())
        waited = set()
        no_children = False
        end = time.monotonic() + 5
        while time.monotonic() < end:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                no_children = True
                break
            if pid:
                waited.add(pid)
                if pid not in expected:
                    uncertain = True
            else:
                time.sleep(0.005)
        record.update(
            reason=reason,
            births_sealed=sealed,
            echild=no_children,
            descendants_waited=no_children and waited == expected,
        )
        record["confirmed"] = record["descendants_waited"] and not uncertain
        Path(root, "supervisor-journal.json").write_text(json.dumps(record))
        control.send(json.dumps(record).encode())
        acknowledged = not record["confirmed"] or terminal_ack(control, live)
        if active is not None:
            os.close(active["fd"])
        os.close(leader_fd)
        registry.close()
        control.close()
        os.close(live)
        if not acknowledged:
            raise OSError("Terminal audio sin ACK del padre vivo")


if __name__ == "__main__":
    main()
