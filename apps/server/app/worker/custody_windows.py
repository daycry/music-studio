"""Custodia Win32 propia (ADR-0057); API interna, nunca comandos de usuario.

El cierre kernel no acredita transporte, publicación ni reservas CPU2.
"""

from __future__ import annotations

import ctypes as C
import subprocess
import sys
import threading
import time
from ctypes import wintypes as W
from pathlib import Path

H, P, SIZE = W.HANDLE, C.c_void_p, C.c_size_t
k = C.WinDLL("kernel32", use_last_error=True)


class Security(C.Structure):
    _fields_ = [("length", W.DWORD), ("descriptor", P), ("inherit", W.BOOL)]


class Startup(C.Structure):
    _fields_ = (
        [
            ("cb", W.DWORD),
            ("reserved", W.LPWSTR),
            ("desktop", W.LPWSTR),
            ("title", W.LPWSTR),
        ]
        + [(s, W.DWORD) for s in ("x", "y", "xs", "ys", "xc", "yc", "fill", "flags")]
        + [
            ("show", W.WORD),
            ("reserved_size", W.WORD),
            ("reserved_data", P),
            ("stdin", H),
            ("stdout", H),
            ("stderr", H),
        ]
    )


class StartupEx(C.Structure):
    _fields_ = [("startup", Startup), ("attributes", P)]


class ProcessInfo(C.Structure):
    _fields_ = [("process", H), ("thread", H), ("pid", W.DWORD), ("tid", W.DWORD)]


class BasicLimits(C.Structure):
    _fields_ = [
        ("process_time", C.c_int64),
        ("job_time", C.c_int64),
        ("flags", W.DWORD),
        ("minimum", SIZE),
        ("maximum", SIZE),
        ("active_limit", W.DWORD),
        ("affinity", SIZE),
        ("priority", W.DWORD),
        ("scheduling", W.DWORD),
    ]


class Limits(C.Structure):
    _fields_ = [
        ("basic", BasicLimits),
        ("io", C.c_uint64 * 6),
        ("process_memory", SIZE),
        ("job_memory", SIZE),
        ("peak_process", SIZE),
        ("peak_job", SIZE),
    ]


class Accounting(C.Structure):
    _fields_ = [
        (s, C.c_int64) for s in ("user", "kernel", "period_user", "period_kernel")
    ] + [(s, W.DWORD) for s in ("faults", "total", "active", "terminated")]


def bind(name, result, *args):
    dll = (
        C.WinDLL("kernelbase", use_last_error=True)
        if name == "CompareObjectHandles"
        else k
    )
    fn = getattr(dll, name)
    fn.restype, fn.argtypes = result, list(args)
    setattr(k, name, fn)


bind("CreateJobObjectW", H, P, W.LPCWSTR)
bind("SetInformationJobObject", W.BOOL, H, C.c_int, P, W.DWORD)
bind("QueryInformationJobObject", W.BOOL, H, C.c_int, P, W.DWORD, P)
bind("CreatePipe", W.BOOL, C.POINTER(H), C.POINTER(H), P, W.DWORD)
bind("SetHandleInformation", W.BOOL, H, W.DWORD, W.DWORD)
bind("GetHandleInformation", W.BOOL, H, C.POINTER(W.DWORD))
bind("InitializeProcThreadAttributeList", W.BOOL, P, W.DWORD, W.DWORD, C.POINTER(SIZE))
bind("UpdateProcThreadAttribute", W.BOOL, P, W.DWORD, SIZE, P, SIZE, P, P)
bind("DeleteProcThreadAttributeList", None, P)
bind(
    "CreateProcessW",
    W.BOOL,
    W.LPCWSTR,
    W.LPWSTR,
    P,
    P,
    W.BOOL,
    W.DWORD,
    P,
    W.LPCWSTR,
    P,
    C.POINTER(ProcessInfo),
)
bind("AssignProcessToJobObject", W.BOOL, H, H)
bind("IsProcessInJob", W.BOOL, H, H, C.POINTER(W.BOOL))
bind("GetProcessId", W.DWORD, H)
bind("GetProcessTimes", W.BOOL, H, *([C.POINTER(W.FILETIME)] * 4))
bind("ResumeThread", W.DWORD, H)
bind("GetCurrentProcess", H)
bind("GetCurrentThread", H)
bind("DuplicateHandle", W.BOOL, H, H, H, C.POINTER(H), W.DWORD, W.BOOL, W.DWORD)
bind("CompareObjectHandles", W.BOOL, H, H)
bind("CloseHandle", W.BOOL, H)
bind("TerminateJobObject", W.BOOL, H, W.UINT)
bind("TerminateProcess", W.BOOL, H, W.UINT)
bind("WaitForSingleObject", W.DWORD, H, W.DWORD)
bind("OpenProcess", H, W.DWORD, W.BOOL, W.DWORD)
bind("PeekNamedPipe", W.BOOL, H, P, W.DWORD, P, C.POINTER(W.DWORD), P)
bind("ReadFile", W.BOOL, H, P, W.DWORD, C.POINTER(W.DWORD), P)
bind("WriteFile", W.BOOL, H, P, W.DWORD, C.POINTER(W.DWORD), P)
bind("OpenThread", H, W.DWORD, W.BOOL, W.DWORD)
bind("CancelSynchronousIo", W.BOOL, H)


def checked(ok):
    if not ok:
        raise C.WinError(C.get_last_error())
    return ok


def raw(handle):
    return handle.value if isinstance(handle, Guard) else int(handle)


class Guard:
    """Referencias no heredables con anclaje independiente; un número no autoriza."""

    def __init__(self, value):
        self.value, self.escrow, self.closed = int(value), None, False
        self._anchor = None
        out = H()
        current = k.GetCurrentProcess()
        checked(
            k.DuplicateHandle(current, self.value, current, C.byref(out), 0, False, 2)
        )
        self.escrow = out.value
        anchor = H()
        checked(
            k.DuplicateHandle(
                current, self.value, current, C.byref(anchor), 0, False, 2
            )
        )
        self._anchor = anchor.value

    def authority(self):
        """Referencia comparada contra anclaje retenido independiente, o ninguna."""
        if self.closed or self._anchor is None:
            return None
        for value in (self.escrow, self.value):
            if value is not None and k.CompareObjectHandles(value, self._anchor):
                return value
        return None

    def valid(self):
        return (
            not self.closed
            and self._anchor is not None
            and bool(k.CompareObjectHandles(self.escrow, self._anchor))
            and bool(k.CompareObjectHandles(self.value, self._anchor))
        )

    def close(self):
        if self.closed:
            return True
        if not self.valid():
            return False
        if not k.CloseHandle(self.value):
            return False
        self.value = None
        if not k.CloseHandle(self.escrow):
            return False
        self.escrow = None
        if not k.CloseHandle(self._anchor):
            return False
        self._anchor = None
        self.escrow, self.closed = None, True
        return True


QUARANTINED = []
IDENTITY_REFERENCES = []


class KernelGroup:
    """Registro interno confiable de nacimientos + handles retenidos.

    seal_births exige que el lanzador no creará más hijos y ha registrado todos.
    Accounting.total es sólo una comprobación adicional, no prueba de completitud.
    """

    def __init__(self, application, argv, cwd, env):
        self.lock = threading.RLock()
        self.handles, self.members = [], []
        self.unwrapped, self.new_process = [], None
        self.partial_guards = []
        self.write_started = self.write_completed = self.written_bytes = 0
        self.job = self.process = self.thread = None
        self.sealed = self.assigned = self.resumed = self.closed = False
        self.unknown = False
        self.disposition = {
            "scope": "windows_kernel_group_handles",
            "terminated": False,
            "waited_members": 0,
            "unknown": False,
            "births": [],
        }
        self._validate(application, argv, cwd, env)
        self.cwd = Path(cwd).resolve()
        try:
            self.job = self._own(checked(k.CreateJobObjectW(None, None)))
            limits = Limits()
            limits.basic.flags = 0x2000  # KILL_ON_JOB_CLOSE, sin BREAKAWAY.
            checked(
                k.SetInformationJobObject(
                    self.job.value, 9, C.byref(limits), C.sizeof(limits)
                )
            )
            self.stdin_child, self.stdin = self._pipe(False)
            self.stdout, self.stdout_child = self._pipe(True)
            self.stderr, self.stderr_child = self._pipe(True)
            self._spawn(application, argv, env)
            checked(k.AssignProcessToJobObject(self.job.value, self.process.value))
            self.assigned = True
            if not self.member(self.process):
                raise OSError("Pertenencia no acreditada")
            self._record(self.process)
            self.disposition["assigned_before_resume"] = True
        except BaseException:
            self.contain_unknown()
            raise

    @staticmethod
    def _validate(application, argv, cwd, env):
        project = Path(__file__).resolve().parents[4]
        for path in (application, cwd):
            if not Path(path).resolve(strict=True).is_relative_to(project):
                raise ValueError("Ruta interna fuera del proyecto")
        if (
            not argv
            or argv[0] != application
            or any(type(v) is not str or "\0" in v for v in argv)
        ):
            raise ValueError("argv interno inválido")
        fixture = project / "apps/server/tests/fixtures/worker_custody_child.py"
        modes = {
            "normal",
            "silent",
            "blocked",
            "fullpipe",
            "backpressure",
            "truncated",
            "invalid",
            "eof",
            "flood",
            "no_output",
        }
        if (
            Path(application).resolve() != Path(sys._base_executable).resolve()
            or len(argv) != 6
            or Path(argv[1]).resolve() != fixture.resolve()
            or argv[2] not in modes
            or Path(argv[3]).resolve() != Path(cwd).resolve()
        ):
            raise ValueError("Entrypoint interno no autorizado")
        allowed = {"SYSTEMROOT", "TEMP", "TMP", "PYTHONPYCACHEPREFIX"}
        if any(
            type(key) is not str
            or key.upper() not in allowed
            or type(value) is not str
            or "\0" in value
            for key, value in env.items()
        ):
            raise ValueError("Entorno interno inválido")
        for key, value in env.items():
            if key.upper() != "SYSTEMROOT" and not Path(value).resolve().is_relative_to(
                project
            ):
                raise ValueError("Temporal fuera del proyecto")

    def _own(self, value):
        handle = Guard.__new__(Guard)
        try:
            handle.__init__(value)
        except BaseException:
            self.partial_guards.append(handle)
            # Conservar la creación propia incluso si falla DuplicateHandle.
            if value not in self.unwrapped:
                self.unwrapped.append(value)
            raise
        self.handles.append(handle)
        if value in self.unwrapped:
            self.unwrapped.remove(value)
        return handle

    def _pipe(self, parent_reads):
        read, write = H(), H()
        security = Security(C.sizeof(Security), None, True)
        checked(k.CreatePipe(C.byref(read), C.byref(write), C.byref(security), 4096))
        self.unwrapped.extend((read.value, write.value))
        read, write = self._own(read.value), self._own(write.value)
        checked(k.SetHandleInformation((read if parent_reads else write).value, 1, 0))
        return read, write

    def _spawn(self, application, argv, env):
        size = SIZE()
        k.InitializeProcThreadAttributeList(None, 1, 0, C.byref(size))
        if not size.value or C.get_last_error() != 122:
            raise OSError("Tamaño de atributos desconocido")
        storage = C.create_string_buffer(size.value)
        checked(k.InitializeProcThreadAttributeList(storage, 1, 0, C.byref(size)))
        try:
            inherit = (H * 3)(
                self.stdin_child.value, self.stdout_child.value, self.stderr_child.value
            )
            checked(
                k.UpdateProcThreadAttribute(
                    storage, 0, 0x00020002, inherit, C.sizeof(inherit), None, None
                )
            )
            startup = StartupEx()
            startup.startup.cb, startup.startup.flags = C.sizeof(startup), 0x101
            startup.startup.stdin, startup.startup.stdout, startup.startup.stderr = (
                inherit
            )
            startup.attributes = C.cast(storage, P)
            command = C.create_unicode_buffer(subprocess.list2cmdline(argv))
            block = C.create_unicode_buffer(
                "\0".join(
                    f"{key}={value}"
                    for key, value in sorted(
                        env.items(), key=lambda item: item[0].upper()
                    )
                )
                + "\0\0"
            )
            info = ProcessInfo()
            checked(
                k.CreateProcessW(
                    application,
                    command,
                    None,
                    None,
                    True,
                    0x4 | 0x8 | 0x80000 | 0x400 | 0x08000000,
                    block,
                    str(self.cwd),
                    C.byref(startup),
                    C.byref(info),
                )
            )
            self.new_process = info.process
            self.unwrapped.extend((info.process, info.thread))
            self.process = self._own(info.process)
            self.thread = self._own(info.thread)
            if k.GetProcessId(self.process.value) != info.pid:
                raise OSError("Identidad de creación distinta")
            self.pid, self.birth = info.pid, self.creation_time(self.process)
            self.disposition["creation"] = {
                "application": application,
                "argv": list(argv),
                "pid": info.pid,
                "thread_id": info.tid,
                "birth": self.birth,
                "process_handle": self.process.value,
                "thread_handle": self.thread.value,
                "flags": 0x4 | 0x8 | 0x80000 | 0x400 | 0x08000000,
            }
            for pipe in (self.stdin_child, self.stdout_child, self.stderr_child):
                if not pipe.close():
                    raise OSError("Extremo heredado sin cierre confirmado")
        finally:
            k.DeleteProcThreadAttributeList(storage)

    @staticmethod
    def creation_time(handle):
        values = [W.FILETIME() for _ in range(4)]
        checked(k.GetProcessTimes(raw(handle), *(C.byref(v) for v in values)))
        return (values[0].dwHighDateTime << 32) | values[0].dwLowDateTime

    @staticmethod
    def open_identity(pid, birth, custodian=None):
        if type(pid) is not int or type(birth) is not int or pid <= 0 or birth <= 0:
            raise ValueError("Nacimiento inválido")
        value = checked(k.OpenProcess(0x100000 | 0x1000 | 1, False, pid))
        # Capture the returned object before any fallible identity query. Failed
        # guards keep their partial anchors too; numeric PID is never authority.
        try:
            if custodian is not None:
                handle = custodian._own(value)
            else:
                handle = Guard.__new__(Guard)
                IDENTITY_REFERENCES.append(handle)
                handle.__init__(value)
            if (
                not handle.valid()
                or k.GetProcessId(handle.value) != pid
                or KernelGroup.creation_time(handle) != birth
            ):
                raise OSError("Nacimiento no coincide")
            if custodian is not None:
                return handle
            # Preserve the successful standalone raw-handle contract. Release
            # only compared duplicates; on failure the journal retains authority.
            for attr in ("escrow", "_anchor"):
                duplicate = getattr(handle, attr)
                if not k.CompareObjectHandles(duplicate, handle.value):
                    raise OSError("Referencia de identidad perdida")
                checked(k.CloseHandle(duplicate))
                setattr(handle, attr, None)
            handle.value, handle.closed = None, True
            IDENTITY_REFERENCES.remove(handle)
            return value
        except Exception:
            if custodian is not None:
                custodian.unknown = custodian.disposition["unknown"] = True
                if custodian not in QUARANTINED:
                    QUARANTINED.append(custodian)
            raise

    def _record(self, handle):
        self.members.append(handle)
        self.disposition["births"].append(
            {"pid": k.GetProcessId(handle.value), "birth": self.creation_time(handle)}
        )

    def member(self, handle):
        if not self.job.valid():
            raise OSError("Referencia de Job perdida")
        result = W.BOOL()
        checked(k.IsProcessInJob(raw(handle), self.job.value, C.byref(result)))
        return bool(result.value)

    def register(self, pid, birth):
        with self.lock:
            if self.sealed or self.closed or not self.resumed:
                raise ValueError("Registro fuera del nacimiento")
            handle = self.open_identity(pid, birth, self)
            if not self.member(handle) or any(
                k.CompareObjectHandles(handle.value, old.value) for old in self.members
            ):
                self.unknown = True
                raise OSError("Miembro ajeno o repetido")
            self._record(handle)
            return handle

    def seal_births(self):
        with self.lock:
            self.sealed = True

    def resume(self):
        with self.lock:
            if (
                self.resumed
                or not self.assigned
                or not self.process.valid()
                or not self.thread.valid()
            ):
                raise OSError("Nacimiento no autorizado")
            if (
                not self.member(self.process)
                or self.creation_time(self.process) != self.birth
            ):
                raise OSError("Identidad no acreditada")
            if k.ResumeThread(self.thread.value) != 1:
                self.unknown = True
                raise OSError("ResumeThread no confirmado")
            self.resumed = True
            self.disposition["resumed"] = True
            checked(self.thread.close())

    @staticmethod
    def wait(handle, milliseconds):
        result = k.WaitForSingleObject(raw(handle), milliseconds)
        if result not in (0, 258):
            raise OSError("Wait de objeto desconocido")
        return result == 0

    @staticmethod
    def terminate_process(handle):
        checked(k.TerminateProcess(raw(handle), 125))

    @staticmethod
    def raw_close(handle):
        checked(k.CloseHandle(raw(handle)))

    def accounting(self):
        if not self.job.valid():
            raise OSError("Job no acreditado")
        info = Accounting()
        checked(
            k.QueryInformationJobObject(
                self.job.value, 1, C.byref(info), C.sizeof(info), None
            )
        )
        return info

    def terminate(self, timeout=5):
        with self.lock:
            if self.disposition["terminated"]:
                return not self.unknown
            if not self.job.valid() or any(not h.valid() for h in self.members):
                self.unknown = True
                return False
            checked(k.TerminateJobObject(self.job.value, 125))
            end = time.monotonic() + timeout
            for handle in self.members:
                signaled = self.wait(
                    handle, max(0, int((end - time.monotonic()) * 1000))
                )
                self.disposition.setdefault("waits", []).append(
                    {
                        "handle": handle.value,
                        "birth": self.creation_time(handle),
                        "signaled": signaled,
                    }
                )
                if not signaled:
                    self.unknown = True
                    return False
            info = self.accounting()
            self.disposition["accounting"] = {
                "total": info.total,
                "active": info.active,
            }
            self.disposition.update(
                terminated=info.active == 0, waited_members=len(self.members)
            )
            if info.active or info.total != len(self.members) or not self.sealed:
                self.unknown = True
            return not self.unknown

    def close(self, timeout=5):
        with self.lock:
            if self.closed:
                return True
            try:
                if not self.terminate(timeout):
                    self.contain_unknown()
                    return False
                for handle in self.handles:
                    old = handle.value
                    closed = handle.close()
                    self.disposition.setdefault("closes", []).append(
                        {"handle": old, "confirmed": closed}
                    )
                    if not closed:
                        self.unknown = True
                        self.contain_unknown()
                        return False
                self.closed = True
                return True
            except OSError as error:
                self.disposition["error_code"] = getattr(error, "winerror", None)
                self.contain_unknown()
                return False

    def contain_unknown(self):
        """Escrows propios para contención; ninguna operación sobre valor ajeno."""
        self.unknown = self.disposition["unknown"] = True
        if self not in QUARANTINED:
            QUARANTINED.append(self)
        job_authority = self.job.authority() if self.job is not None else None
        if job_authority is not None:
            k.TerminateJobObject(job_authority, 125)
        process_authority = (
            self.process.authority() if self.process is not None else None
        )
        if process_authority is not None:
            k.TerminateProcess(process_authority, 125)
            self.wait(process_authority, 5000)
        elif self.process is None and self.new_process is not None:
            # Sólo durante constructor fallido: referencia de CreateProcessW aún
            # retenida, no publicada, jamás cerrada ni obtenida desde un PID.
            k.TerminateProcess(self.new_process, 125)
            self.disposition["unwrapped_leader_waited"] = self.wait(
                self.new_process, 5000
            )

    def read_available(self, handle):
        if not handle.valid():
            raise OSError("Pipe no acreditada")
        size = W.DWORD()
        if not k.PeekNamedPipe(handle.value, None, 0, None, C.byref(size), None):
            if C.get_last_error() == 109:
                return None
            raise C.WinError(C.get_last_error())
        if not size.value:
            return b""
        buffer = C.create_string_buffer(min(size.value, 4096))
        count = W.DWORD()
        checked(k.ReadFile(handle.value, buffer, len(buffer), C.byref(count), None))
        return buffer.raw[: count.value]

    def write(self, data, stop):
        for offset in range(0, len(data), 4096):
            if stop.is_set():
                return
            if not self.stdin.valid():
                raise OSError("Writer sin referencia")
            part, count = data[offset : offset + 4096], W.DWORD()
            self.write_started += 1
            checked(
                k.WriteFile(self.stdin.value, part, len(part), C.byref(count), None)
            )
            self.write_completed += 1
            self.written_bytes += count.value
            if count.value != len(part):
                raise OSError("Escritura parcial")

    def retain_writer(self):
        """Se llama DENTRO del writer; duplica su objeto real, nunca busca TID."""
        current, out = k.GetCurrentProcess(), H()
        checked(
            k.DuplicateHandle(
                current, k.GetCurrentThread(), current, C.byref(out), 0, False, 2
            )
        )
        with self.lock:
            return self._own(out.value)

    @staticmethod
    def cancel_writer(thread):
        if not thread.valid():
            raise OSError("Writer sin identidad retenida")
        if not k.CancelSynchronousIo(thread.value) and C.get_last_error() != 1168:
            raise C.WinError(C.get_last_error())
