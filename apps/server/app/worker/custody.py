"""Propietario portable de custodia; gate de lease/staging sólo inerte.

Backends nativos internos Windows y Linux. El dueño
de servicio conserva OWNERS hasta join; una CancelledError nunca libera nada.
"""

from __future__ import annotations

import asyncio
import math
import threading
import time
from dataclasses import dataclass
from enum import StrEnum
from queue import Empty, Full, Queue

from .pipe_protocol import Decoder, ProtocolError, Session, encode


class State(StrEnum):
    STARTING = "STARTING"
    OWNED = "OWNED"
    DRAINING = "DRAINING"
    CLOSED_CONFIRMED = "CLOSED_CONFIRMED"
    UNKNOWN_QUARANTINED = "UNKNOWN_QUARANTINED"


@dataclass(frozen=True)
class Receipt:
    state: State
    resources_returned: bool
    streams_confirmed: bool
    kernel: dict
    reason: str
    scope: str = "windows_kernel_and_private_transport"

    @property
    def release_gate(self):
        return self.state == State.CLOSED_CONFIRMED and self.resources_returned


OWNERS = set()
_registry_lock = threading.Lock()


class Owner:
    """Pasar sólo un backend interno confiable y correlación local del padre.

    Reader exclusivo usa PeekNamedPipe + ReadFile sólo con bytes disponibles:
    ninguna lectura bloqueada puede impedir deadline/cancel. Writer separado,
    cola4, cancelación por handle real de hilo y joins conocidos antes de close.
    Payload recibido no autoriza SQL, archivos ni publicación.
    """

    def __init__(self, group, execution_id, epoch, deadline):
        if (
            type(deadline) not in (float, int)
            or not math.isfinite(deadline)
            or not 0 < deadline <= 3600
        ):
            raise ValueError("Deadline interno inválido")
        self.group, self.deadline = group, float(deadline)
        try:
            self.scope = getattr(group, "scope", "windows_kernel_and_private_transport")
            if type(self.scope) is not str:
                raise ValueError("Scope interno inválido")
            self.scope_unknown = False
        except (
            OSError,
            ValueError,
            RuntimeError,
            TypeError,
            AttributeError,
            LookupError,
        ):
            self.scope = "unknown_kernel_and_private_transport"
            self.scope_unknown = True
        self.decoder = Decoder(Session(execution_id, epoch, "child"))
        self.outgoing = Session(execution_id, epoch, "parent")
        self.execution_id, self.epoch = execution_id, epoch
        self.state = State.STARTING
        self.ready, self.stop, self.writer_started, self.done = (
            threading.Event() for _ in range(4)
        )
        self.stderr, self.stdout = bytearray(), bytearray()
        self.messages, self.writes = Queue(maxsize=4), Queue(maxsize=4)
        self.lock = threading.RLock()
        self.receipt, self.writer_error = None, False
        self.writer_ref = None
        self.bad = self.scope_unknown
        self.saw_closed = self.stdout_eof = self.stderr_eof = False
        self.finalizer = threading.Thread(
            target=self._run, name="custody-finalizer", daemon=False
        )
        self.writer = threading.Thread(
            target=self._write_loop, name="custody-writer", daemon=False
        )
        self.end = None

    def start(self):
        with self.lock:
            if self.state != State.STARTING or self.finalizer.ident is not None:
                raise ValueError("Owner ya iniciado")
            self.end = time.monotonic() + self.deadline
            with _registry_lock:
                OWNERS.add(self)
            self.finalizer.start()

    def send(self, message):
        with self.lock:
            if self.stop.is_set() or self.state != State.OWNED:
                raise ValueError("Writer revocado")
            wire = encode(message)
            if self.writes.full():
                raise ValueError("Writer sin capacidad")
            self.outgoing.accept(message, len(wire))
            self.writes.put_nowait(wire)

    def _write_loop(self):
        try:
            self.writer_ref = self.group.retain_writer()
        except OSError:
            self.writer_error = True
            self.stop.set()
            return
        while not self.stop.is_set():
            try:
                wire = self.writes.get(timeout=0.01)
            except Empty:
                continue
            try:
                self.writer_started.set()
                self.group.write(wire, self.stop)
            except OSError:
                if not self.stop.is_set():
                    self.writer_error = True
                    self.stop.set()
                return

    def _message(self, message):
        if message["kind"] == "ready":
            payload = message["payload"]
            real = getattr(self.group, "audio_policy", False) is True
            if payload.keys() != {"member", "births_sealed"} or payload[
                "births_sealed"
            ] is not (not real):
                raise ProtocolError("Handshake de nacimientos inválido")
            member = payload["member"]
            if type(member) is not dict or member.keys() != {"pid", "birth"}:
                raise ProtocolError("Nacimiento inválido")
            self.group.register(member["pid"], member["birth"])
            if not real:
                self.group.seal_births()
            self.send(
                {
                    "version": 1,
                    "execution_id": self.execution_id,
                    "epoch": self.epoch,
                    "seq": 1,
                    "kind": "request",
                    "payload": {},
                }
            )
            self.ready.set()
            return
        if message["kind"] == "closed":
            if getattr(self.group, "audio_policy", False) is True:
                self.group.seal_births()
            self.saw_closed = True
        while True:
            try:
                self.messages.put(message, timeout=0.01)
                return
            except Full:
                if self.stop.is_set() or time.monotonic() >= self.end:
                    raise ProtocolError("Backpressure agotó el plazo")

    def receive(self, timeout=0):
        return self.messages.get(timeout=timeout)

    def _read(self, parsing=True):
        if not self.stdout_eof:
            chunk = self.group.read_available(self.group.stdout)
            if chunk is None:
                self.stdout_eof = True
                self.decoder.finish()
                if not self.saw_closed and not self.stop.is_set():
                    raise ProtocolError("EOF prematuro")
            elif chunk:
                self.stdout.extend(chunk[: max(0, 16384 - len(self.stdout))])
                if not self.bad:
                    for message in self.decoder.feed(chunk):
                        # Drain validates every frame, including errors after a yield.
                        # Stopping revokes effects, never transport validation.
                        if parsing and not self.stop.is_set():
                            self._message(message)
        if not self.stderr_eof:
            chunk = self.group.read_available(self.group.stderr)
            if chunk is None:
                self.stderr_eof = True
            elif chunk:
                self.stderr.extend(chunk[: max(0, 16384 - len(self.stderr))])

    def _run(self):
        try:
            reason = "completed"
            try:
                self.group.resume()
                self.state = State.OWNED
                self.writer.start()
                while not self.stop.is_set():
                    self._read()
                    if self.stdout_eof and self.stderr_eof:
                        break
                    if time.monotonic() >= self.end:
                        reason = "deadline"
                        self.cancel()
                        break
                    self.stop.wait(0.005)
                if self.stop.is_set() and reason == "completed":
                    reason = "cancelled"
            except (OSError, ValueError, ProtocolError):
                self.bad, reason = True, "transport_error"
            finally:
                self.state = State.DRAINING
                self.stop.set()
                self.decoder.session.mark_stopping("liveness")
                streams, kernel = False, False
                try:
                    # Deadline independiente del writer que pueda estar dentro de WriteFile.
                    if self.writer_ref is not None and self.writer.is_alive():
                        try:
                            self.group.cancel_writer(self.writer_ref)
                        except OSError:
                            if self.writer.is_alive():
                                self.bad = True
                    kernel = self.group.terminate(5)
                    if self.writer.ident is not None:
                        self.writer.join(2)
                    if self.writer.is_alive():
                        self.bad = True
                    writer_waited = (
                        self.writer_ref is not None
                        and self.writer_ref.valid()
                        and self.group.wait(self.writer_ref, 2000)
                    )
                    self.group.disposition["writer_waited"] = writer_waited
                    if not writer_waited:
                        self.bad = True
                    drain_end = time.monotonic() + 2
                    while (
                        not (self.stdout_eof and self.stderr_eof)
                        and time.monotonic() < drain_end
                    ):
                        try:
                            self._read(parsing=False)
                        except ProtocolError:
                            self.bad = True
                            # Reader físicamente terminó; frontera inválida permanece sticky.
                        self.done.wait(0.001)
                    streams = (
                        self.stdout_eof
                        and self.stderr_eof
                        and not self.writer.is_alive()
                    )
                    self.bad |= self.writer_error
                    if kernel and streams and not self.bad:
                        kernel = self.group.close(5)
                    else:
                        self.group.contain_unknown()
                except (OSError, ValueError):
                    self.bad = True
                    self.group.contain_unknown()
                confirmed = kernel and streams and not self.bad and self.group.closed
                self.state = (
                    State.CLOSED_CONFIRMED if confirmed else State.UNKNOWN_QUARANTINED
                )
                self.receipt = Receipt(
                    self.state,
                    confirmed,
                    streams,
                    dict(self.group.disposition),
                    "transport_error" if self.bad else reason,
                    scope=self.scope,
                )
        except (
            OSError,
            ValueError,
            RuntimeError,
            TypeError,
            AttributeError,
            LookupError,
        ):
            # A secondary containment/query failure must not orphan this owner.
            # No backend query here: disposition itself may be unavailable.
            self.bad = True
            self.stop.set()
            self.state = State.UNKNOWN_QUARANTINED
            self.receipt = Receipt(
                self.state,
                False,
                False,
                {"unknown": True, "error_code": "finalizer_failure"},
                "transport_error",
                scope=self.scope,
            )
        finally:
            # Receipt readiness is not proof that the native/thread resources returned.
            self.done.set()

    def cancel(self):
        self.stop.set()

    def join(self, timeout):
        if self.finalizer.ident is None:
            raise ValueError("Owner no iniciado")
        self.finalizer.join(timeout)
        if self.finalizer.is_alive():
            raise TimeoutError("Finalizador retenido todavía activo")
        if self.receipt is None:
            raise RuntimeError(
                "Custodia UNKNOWN: finalizador sin recibo; referencias retenidas"
            )
        if self.receipt.resources_returned:
            with _registry_lock:
                OWNERS.discard(self)
        return self.receipt

    async def wait(self):
        try:
            # Join the actual retained thread in a worker, with a finite cleanup
            # budget. done can be set while the finalizer is still returning.
            end = self.end if self.end is not None else time.monotonic() + self.deadline
            return await asyncio.to_thread(
                self.join, max(0, end + 20 - time.monotonic())
            )
        except asyncio.CancelledError:
            self.cancel()
            raise
