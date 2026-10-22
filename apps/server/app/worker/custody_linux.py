"""Backend Linux interno con referencias retenidas y transporte no bloqueante."""

import json
import os
import selectors
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

LINUX_GROUPS = set()


class FD:
    """Duplicado inmediato; un número reutilizado no autoriza cerrar otro objeto."""

    def __init__(self, value):
        self.value = value
        self.anchor = os.dup(value)
        self.identity = self._identity(self.anchor)
        self.closed = False
        os.set_inheritable(self.anchor, False)

    @staticmethod
    def _identity(value):
        stat = os.fstat(value)
        return stat.st_dev, stat.st_ino, stat.st_mode

    def valid(self):
        try:
            return (
                not self.closed
                and self._identity(self.value) == self.identity
                and self._identity(self.anchor) == self.identity
            )
        except OSError:
            return False

    def close(self):
        if self.closed:
            return True
        if not self.valid():
            return False
        os.close(self.value)
        os.close(self.anchor)
        self.closed = True
        return True


class WriterReference:
    """Hilo Python Linux retenido; no representa un hThread Windows."""

    def __init__(self, group):
        self.thread = threading.current_thread()
        self.stopping = threading.Event()
        read, write = os.pipe()
        self.wake_read, self.wake_write = FD(read), FD(write)
        group.fds.extend((self.wake_read, self.wake_write))
        os.set_blocking(self.wake_read.anchor, False)
        os.set_blocking(self.wake_write.anchor, False)

    def valid(self):
        return self.thread.ident is not None


class LinuxGroup:
    scope = "linux_subreaper_kernel_and_private_transport"
    MODES = frozenset(
        {
            "normal",
            "silent",
            "blocked",
            "no_output",
            "truncated",
            "invalid",
            "nonfinite",
            "seq",
            "eof",
            "flood",
            "fullpipe",
            "backpressure",
            "foreign_birth",
        }
    )

    def __init__(
        self,
        mode,
        root,
        execution_id,
        epoch,
        *,
        audio_root=None,
        plan_sha256=None,
        plan_bytes=None,
        context_sha256=None,
        context_bytes=None,
    ):
        from .pipe_protocol import Session

        Session(execution_id, epoch, "parent")
        self.audio_policy = mode == "audio" and audio_root is not None
        if mode not in self.MODES and not self.audio_policy:
            raise ValueError("Fixture interna desconocida")
        extra = []
        if self.audio_policy:
            if (
                type(plan_bytes) is not int
                or not 1 <= plan_bytes <= 16777216
                or type(plan_sha256) is not str
                or len(plan_sha256) != 64
                or any(c not in "0123456789abcdef" for c in plan_sha256)
            ):
                raise ValueError("Referencia de plan inválida")
            if (
                type(context_bytes) is not int
                or not 1 <= context_bytes
                or plan_bytes + context_bytes > 16777216
                or type(context_sha256) is not str
                or len(context_sha256) != 64
                or any(c not in "0123456789abcdef" for c in context_sha256)
            ):
                raise ValueError("Referencia de contexto inválida")
            extra = [
                str(Path(audio_root).resolve(strict=True)),
                plan_sha256,
                str(plan_bytes),
                context_sha256,
                str(context_bytes),
            ]
        self.root = Path(root).resolve(strict=True)
        LINUX_GROUPS.add(self)
        self.closed = self.unknown = self.sealed = False
        self.disposition = {"scope": self.scope, "descendants_waited": False}
        self.lock = threading.RLock()
        self.members = {}
        self.events = []
        self.fds = []
        self.writer_local = threading.local()
        parent, child = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        live_r, live_w = os.pipe()
        self.control = parent
        self.liveness = FD(live_w)
        self.fds.append(self.liveness)
        script = Path(__file__).with_name("custody_linux_supervisor.py")
        env = {"PYTHONDONTWRITEBYTECODE": "1"}
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-B",
                str(script),
                str(live_r),
                str(child.fileno()),
                mode,
                str(self.root),
                execution_id,
                epoch,
                *extra,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            pass_fds=(live_r, child.fileno()),
            close_fds=True,
            cwd=self.root,
            env=env,
        )
        try:
            self.streams = (
                self.process.stdin,
                self.process.stdout,
                self.process.stderr,
            )
            self.stream_refs = []
            for stream in self.streams:
                ref = FD(stream.fileno())
                self.stream_refs.append(ref)
                self.fds.append(ref)
            self.supervisor_ref = FD(os.pidfd_open(self.process.pid))
            self.fds.append(self.supervisor_ref)
            os.close(live_r)
            live_r = None
            child.close()
            self.control_ref = FD(parent.fileno())
            self.fds.append(self.control_ref)
            for name, stream in zip(
                ("stdin", "stdout", "stderr"), self.streams, strict=True
            ):
                value = os.dup(stream.fileno())
                try:
                    ref = FD(value)
                except BaseException:
                    os.close(value)  # duplicado propio, aún no publicado
                    raise
                setattr(self, name + "_ref", ref)
                self.fds.append(ref)
            self.stdin, self.stdout, self.stderr = (
                v.value for v in (self.stdin_ref, self.stdout_ref, self.stderr_ref)
            )
            for ref in (self.stdin_ref, self.stdout_ref, self.stderr_ref):
                os.set_blocking(ref.anchor, False)
            parent.setblocking(False)
            self._await("born", 5)
        except BaseException:
            # No se publica un grupo parcial. Se retiene como UNKNOWN y se
            # retira liveness aun sin referencias completas de stdio/control.
            self.unknown = True
            if self.liveness.valid():
                self.liveness.close()
            if live_r is not None:
                os.close(live_r)  # extremo propio no expuesto desde su creación
            child.close()
            try:
                self.disposition["supervisor_exit"] = self.process.wait(timeout=7)
                self.disposition["supervisor_waited"] = True
            except (OSError, subprocess.TimeoutExpired):
                self.disposition["supervisor_waited"] = False
            raise

    def _events(self):
        if not self.control_ref.valid():
            raise OSError("Control perdido")
        while True:
            try:
                data = self.control.recv(4096)
            except BlockingIOError:
                return
            if not data:
                return
            value = json.loads(data)
            if value["kind"] == "member":
                ref = FD(os.pidfd_open(value["pid"]))
                self.fds.append(ref)
                self.members[value["pid"]] = (value["birth"], ref)
            elif value["kind"] in ("born", "final"):
                if value["kind"] == "born":
                    self.leader_ref = FD(os.pidfd_open(value["leader"]))
                    self.fds.append(self.leader_ref)
                self.disposition.update(value)
            self.events.append(value["kind"])
            if len(self.events) > 8:
                raise OSError("Control excedido")
            if value["kind"] == "final" and value.get("confirmed") is True:
                # Final recibido antes del ACK: ningún reset equivale a certificado.
                self._command(b"final_ack")
                return

    def _await(self, kind, timeout):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            self._events()
            if kind in self.events:
                return True
            with selectors.DefaultSelector() as selector:
                selector.register(self.control_ref.anchor, selectors.EVENT_READ)
                selector.select(min(0.02, max(0, end - time.monotonic())))
        raise OSError("Supervisor sin confirmación")

    def _command(self, message):
        if not self.control_ref.valid():
            raise OSError("Control perdido")
        self.control.send(message)

    def resume(self):
        self._command(b"resume")

    def register(self, pid, birth):
        if self.audio_policy:
            if (pid, birth) != (self.disposition["leader"], self.disposition["birth"]):
                raise OSError("Líder de audio distinto")
            if not self.leader_ref.valid():
                raise OSError("Referencia líder perdida")
            return
        self._await("member", 5)
        if type(pid) is not int or type(birth) is not int or pid not in self.members:
            raise OSError("Miembro desconocido")
        expected, ref = self.members[pid]
        if birth != expected or not ref.valid():
            raise OSError("Identidad de miembro perdida")

    def seal_births(self):
        self._command(b"seal")
        self._await("sealed", 5)
        self.sealed = True

    def read_available(self, value):
        ref = {self.stdout: self.stdout_ref, self.stderr: self.stderr_ref}[value]
        if not ref.valid():
            raise OSError("Reader perdido")
        try:
            return os.read(ref.anchor, 16384) or None
        except BlockingIOError:
            return b""

    def retain_writer(self):
        reference = WriterReference(self)
        self.writer_local.reference = reference
        return reference

    def cancel_writer(self, reference):
        reference.stopping.set()
        if not reference.wake_write.valid():
            raise OSError("Referencia de wake perdida")
        try:
            os.write(reference.wake_write.anchor, b"S")
        except BlockingIOError:
            pass

    @staticmethod
    def wait(reference, milliseconds):
        reference.thread.join(milliseconds / 1000)
        return not reference.thread.is_alive()

    def write(self, wire, stop):
        reference = self.stdin_ref
        writer = getattr(self.writer_local, "reference", None)
        offset = 0
        while (
            offset < len(wire)
            and not stop.is_set()
            and not (writer and writer.stopping.is_set())
        ):
            if not reference.valid():
                raise OSError("Writer perdido")
            try:
                offset += os.write(reference.anchor, wire[offset:])
            except BlockingIOError:
                with selectors.DefaultSelector() as selector:
                    selector.register(reference.anchor, selectors.EVENT_WRITE)
                    if writer:
                        selector.register(writer.wake_read.anchor, selectors.EVENT_READ)
                    selector.select(0.01)

    def terminate(self, timeout):
        with self.lock:
            if self.closed:
                return True
            try:
                self._events()
                if "final" not in self.events:
                    self._command(b"stop")
                    self._await("final", timeout)
                if not self.supervisor_ref.valid():
                    raise OSError("Referencia supervisor perdida")
                with selectors.DefaultSelector() as selector:
                    selector.register(self.supervisor_ref.anchor, selectors.EVENT_READ)
                    if not selector.select(timeout):
                        raise OSError("Supervisor no terminado")
                self.disposition["supervisor_exit"] = self.process.wait(timeout=timeout)
                self.disposition["supervisor_waited"] = True
                for ref in [self.leader_ref] + [v[1] for v in self.members.values()]:
                    if not ref.valid():
                        raise OSError("Referencia de proceso perdida")
                    with selectors.DefaultSelector() as selector:
                        selector.register(ref.anchor, selectors.EVENT_READ)
                        if not selector.select(0):
                            raise OSError("Proceso propio sin señal de salida")
                self.disposition["native_process_refs_waited"] = True
                return (
                    self.disposition.get("confirmed") is True
                    and self.disposition["supervisor_exit"] == 0
                    and not self.unknown
                )
            except (OSError, ValueError, subprocess.TimeoutExpired):
                self.unknown = True
                return False

    def contain_unknown(self):
        self.unknown = True
        if self.liveness.valid():
            self.liveness.close()
        self.terminate(5)

    def close(self, timeout):
        with self.lock:
            if self.closed:
                return True
            if (
                self.unknown
                or not self.terminate(timeout)
                or not all(ref.valid() or ref.closed for ref in self.fds)
            ):
                self.unknown = True
                return False
            for stream, ref in zip(self.streams, self.stream_refs, strict=True):
                if not ref.valid():
                    self.unknown = True
                    return False
                stream.close()
                os.close(ref.anchor)
                ref.closed = True
            self.control.detach()
            for ref in self.fds:
                if not ref.close():
                    self.unknown = True
                    return False
            self.closed = True
            LINUX_GROUPS.discard(self)
            return True
