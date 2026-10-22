"""Custodia Windows real; no acredita semántica ni autenticación del proveedor."""

import hashlib
import importlib
import importlib.util
import os
import shutil
import struct
import time
import uuid
from pathlib import Path

import pytest


def api():
    assert importlib.util.find_spec("benchmark_custody"), (
        "Falta captura funcional de bytes originales con custodia nativa"
    )
    return importlib.import_module("benchmark_custody")


def source(m, root, name="raw.bin", data=b"RAW\r\n\x00exact\xff"):
    path = root / name
    path.write_bytes(data)
    return m.SourceEntry(name, path, len(data), hashlib.sha256(data).hexdigest())


def deadline():
    return time.monotonic() + 20


@pytest.fixture
def tmp_path():
    # STUDIO_CUSTODY_TEST_ROOT permite al orquestador aislar cada ejecución.
    # Sin variable, la fixture permanece en la caché normal del repositorio.
    cache = (Path(__file__).resolve().parents[3] / ".cache").resolve()
    root = Path(os.environ.get("STUDIO_CUSTODY_TEST_ROOT", str(cache / "pytest-tmp")))
    root = root.resolve()
    if not root.is_relative_to(cache):
        raise ValueError("STUDIO_CUSTODY_TEST_ROOT debe permanecer dentro de .cache")
    root.mkdir(parents=True, exist_ok=True)
    path = root / uuid.uuid4().hex
    path.mkdir()
    try:
        yield path
    finally:
        assert path.parent == root and path.name.isalnum()
        shutil.rmtree(path)


@pytest.fixture
def native_root(tmp_path):
    if os.name != "nt":
        pytest.skip("Prueba real de pins CreateFileW requiere Windows")
    return tmp_path


def test_exact_bytes_and_bounded_offsets(native_root):
    m = api()
    entry = source(m, native_root)
    with m.CustodyStore(native_root) as store:
        ref = store.capture([entry], deadline=deadline())
        assert (
            store.read(ref, "raw.bin", offset=3, length=5, deadline=deadline())
            == b"\r\n\x00ex"
        )
        assert (
            store.read(
                ref, "raw.bin", offset=0, length=entry.length, deadline=deadline()
            )
            == entry.path.read_bytes()
        )
        entry.path.write_bytes(b"changed loose original")
        assert (
            store.read(ref, "raw.bin", offset=3, length=5, deadline=deadline())
            == b"\r\n\x00ex"
        )


@pytest.mark.parametrize(
    "operation", ["write", "truncate", "rename", "unlink", "hardlink"]
)
def test_native_mutation_denied_and_foreign_control(
    native_root, operation, monkeypatch
):
    m = api()
    entry = source(m, native_root)
    foreign = native_root / "foreign.bin"
    foreign.write_bytes(b"foreign")
    with m.CustodyStore(native_root) as store:
        ref = store.capture([entry], deadline=deadline())
        capsule = next(store._directory.glob("*.cap"))
        target = capsule
        with pytest.raises(OSError):
            if operation == "hardlink":
                target = native_root / "alias.bin"
                os.link(capsule, target)
            if operation in ("write", "hardlink"):
                with target.open("r+b") as file:
                    file.write(b"evil")
            elif operation == "truncate":
                with target.open("wb"):
                    pass
            elif operation == "rename":
                target.rename(native_root / "replaced.cap")
            else:
                target.unlink()
        foreign.write_bytes(b"control writable")
        assert foreign.read_bytes() == b"control writable"
        assert (
            store.read(
                ref, entry.name, offset=0, length=entry.length, deadline=deadline()
            )
            == b"RAW\r\n\x00exact\xff"
        )
    capsule.write_bytes(b"released")
    capsule.unlink()
    assert foreign.read_bytes() == b"control writable"


def test_preexisting_native_writer_rejected(native_root):
    m = api()
    entry = source(m, native_root)
    with entry.path.open("r+b") as writer, m.CustodyStore(native_root) as store:
        with pytest.raises(m.CustodyError):
            store.capture([entry], deadline=deadline())
        assert list(store._directory.glob("*.cap")) == []
        writer.seek(0)
        writer.write(b"own")
    assert entry.path.read_bytes().startswith(b"own")


@pytest.mark.parametrize(
    "case",
    [
        "seal",
        "truncated",
        "duplicate",
        "name",
        "integer",
        "total",
        "count",
        "seal_format",
    ],
)
def test_capture_rejects_invalid_closed_input(native_root, case):
    m = api()
    entry = source(m, native_root)
    args = [entry]
    if case == "seal":
        args = [m.SourceEntry(entry.name, entry.path, entry.length, "0" * 64)]
    elif case == "truncated":
        entry.path.write_bytes(b"x")
    elif case == "duplicate":
        args *= 2
    elif case == "name":
        args = [m.SourceEntry("../raw", entry.path, entry.length, entry.seal)]
    elif case == "integer":
        args = [m.SourceEntry(entry.name, entry.path, True, entry.seal)]
    elif case == "total":
        args = [m.SourceEntry(entry.name, entry.path, 64 * 1024 * 1024, entry.seal)]
    elif case == "count":
        args *= 129
    else:
        args = [m.SourceEntry(entry.name, entry.path, entry.length, "A" * 64)]
    with m.CustodyStore(native_root) as store:
        with pytest.raises(m.CustodyError):
            store.capture(args, deadline=deadline())
        assert store._capsules == {}
        assert list(store._directory.glob("*.cap")) == []


@pytest.mark.parametrize(
    "case",
    [
        "foreign",
        "unknown",
        "name",
        "overflow",
        "negative",
        "bool",
        "large",
        "closed",
        "expired",
    ],
)
def test_read_rejects_unbound_or_unbounded_request(native_root, case):
    m = api()
    entry = source(m, native_root)
    with m.CustodyStore(native_root) as store, m.CustodyStore(native_root) as other:
        ref = store.capture([entry], deadline=deadline())
        name, offset, length, limit = entry.name, 0, 1, deadline()
        if case == "foreign":
            store = other
        elif case == "unknown":
            ref = m.CapsuleRef(ref.store_id, "missing")
        elif case == "name":
            name = str(entry.path)
        elif case == "overflow":
            offset = 2**64
        elif case == "negative":
            offset = -1
        elif case == "bool":
            length = True
        elif case == "large":
            length = 256 * 1024 + 1
        elif case == "closed":
            store.close()
        else:
            limit = time.monotonic() - 1
        with pytest.raises(m.CustodyError):
            store.read(ref, name, offset=offset, length=length, deadline=limit)


def test_native_pin_loss_invalidates_all_future_reads(native_root):
    m = api()
    entry = source(m, native_root)
    with m.CustodyStore(native_root) as store:
        ref = store.capture([entry], deadline=deadline())
        capsule = store._capsules[ref.capsule_id]
        assert m._native().CloseHandle(capsule.pin.handle)
        with pytest.raises(m.CustodyError):
            store.read(ref, entry.name, offset=0, length=1, deadline=deadline())
        with pytest.raises(m.CustodyError):
            store.read(ref, entry.name, offset=0, length=1, deadline=deadline())


def test_expired_capture_has_no_announced_or_partial_capsule(native_root):
    m = api()
    entry = source(m, native_root)
    with m.CustodyStore(native_root) as store:
        with pytest.raises(m.CustodyError):
            store.capture([entry], deadline=time.monotonic() - 1)
        assert store._capsules == {}
        assert list(store._directory.glob("*.cap")) == []


def test_namespace_rename_is_denied(native_root):
    m = api()
    with m.CustodyStore(native_root) as store, pytest.raises(OSError):
        store._directory.rename(native_root / "substitution")
    assert store._directory.is_dir()


def test_reparse_source_rejected_when_supported(native_root):
    m = api()
    entry = source(m, native_root)
    alias = native_root / "reparse.bin"
    try:
        alias.symlink_to(entry.path)
    except OSError as error:
        pytest.skip(f"Windows symlink privilege unavailable: {error}")
    with m.CustodyStore(native_root) as store:
        with pytest.raises(m.CustodyError):
            store.capture(
                [m.SourceEntry(entry.name, alias, entry.length, entry.seal)],
                deadline=deadline(),
            )
        assert store._capsules == {}


def test_linux_fails_closed_without_files(monkeypatch, tmp_path):
    m = api()
    monkeypatch.setattr(m, "_platform", lambda: "posix")
    with pytest.raises(m.UnsupportedPlatform):
        m.CustodyStore(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_failure_preserves_substituted_foreign_file_in_owned_namespace(
    native_root, monkeypatch
):
    """Inyección en el traspaso; sustitución real de Windows denegada."""
    m = api()
    entry = source(m, native_root)
    original_pin = m._Pin
    attempted = []

    def substitute(path, **kwargs):
        if Path(path).suffix == ".cap" and not attempted:
            attempted.append(Path(path))
            with pytest.raises(OSError):
                Path(path).rename(Path(path).with_suffix(".own-original"))
            raise m.CustodyError("Inyección: fallo de pin posterior al ataque")
        return original_pin(path, **kwargs)

    monkeypatch.setattr(m, "_Pin", substitute)
    with m.CustodyStore(native_root) as store:
        with pytest.raises(m.CustodyError):
            store.capture([entry], deadline=deadline())
        assert store._capsules == {}
        assert len(attempted) == 1
        assert entry.path.read_bytes() == b"RAW\r\n\x00exact\xff"
        assert list(store._directory.glob("*.cap")) == []


def test_close_preserves_reused_foreign_native_handle(native_root):
    """Pérdida real del handle y reutilización real del slot por Windows."""
    m = api()
    entry = source(m, native_root)
    foreign = source(m, native_root, "foreign.bin", b"foreign")
    store = m.CustodyStore(native_root)
    ref = store.capture([entry], deadline=deadline())
    pin = store._capsules[ref.capsule_id].pin
    lost_handle = pin.handle
    assert m._native().CloseHandle(lost_handle)
    foreign_pins = []
    try:
        for _ in range(4096):
            handle = m._native().CreateFileW(
                str(foreign.path), 0x80000000, 7, None, 3, 0x00200000, None
            )
            foreign_pins.append(handle)
            if handle == lost_handle:
                break
        assert handle == lost_handle, (
            "Kernel no reutilizó slot dentro de 4096 aperturas"
        )
        store.close()
        information = m._FileInformation()
        assert m._native().GetFileInformationByHandle(
            handle, m.ctypes.byref(information)
        )
        assert information.size_low == 7
    finally:
        for resource in foreign_pins:
            m._native().CloseHandle(resource)
        store.close()


def test_reopened_same_file_is_not_original_native_pin(native_root):
    m = api()
    entry = source(m, native_root)
    store = m.CustodyStore(native_root)
    ref = store.capture([entry], deadline=deadline())
    pin = store._capsules[ref.capsule_id].pin
    lost_handle = pin.handle
    path = pin.path
    assert m._native().CloseHandle(lost_handle)
    handles = []
    try:
        for _ in range(4096):
            handle = m._native().CreateFileW(
                str(path), 0x80000000, 7, None, 3, 0x00200000, None
            )
            handles.append(handle)
            if handle == lost_handle:
                break
        assert handle == lost_handle, (
            "Kernel no reutilizó slot dentro de 4096 aperturas"
        )
        with pytest.raises(m.CustodyError):
            store.read(ref, entry.name, offset=0, length=1, deadline=deadline())
    finally:
        store.close()
        for handle in handles:
            m._native().CloseHandle(handle)


def test_capture_deadline_includes_release_before_exposure(native_root, monkeypatch):
    """Inyección de IO lento; plazo monotónico real que nunca se reinicia."""
    m = api()
    entry = source(m, native_root)
    limit = time.monotonic() + 0.1
    original_close = m._Pin.close
    delayed = []

    def close_with_delay(pin):
        if pin.path == entry.path and pin.handle is not None and not delayed:
            delayed.append(True)
            time.sleep(max(0, limit - time.monotonic()) + 0.015)
        original_close(pin)

    monkeypatch.setattr(m._Pin, "close", close_with_delay)
    with m.CustodyStore(native_root) as store:
        with pytest.raises(m.CustodyError):
            store.capture([entry], deadline=limit)
        assert delayed == [True]
        assert store._capsules == {}
        assert list(store._directory.glob("*.cap")) == []


@pytest.mark.parametrize(
    "case",
    [
        "magic",
        "count",
        "truncated",
        "offsetoverflow",
        "lengthoverflow",
        "duplicate",
        "name",
        "seal",
        "payload",
        "trailing",
        "offsetgap",
        "padding",
    ],
)
def test_corrupted_closed_capsule_rejected_before_exposure(
    native_root, monkeypatch, case
):
    """Inyección de bytes antes del pin; Write/ReadFile y protección reales."""
    m = api()
    assert callable(getattr(m.CustodyStore, "_verify_capsule", None)), (
        "Falta verificación funcional del contenedor pinned y su índice cerrado"
    )
    first = source(m, native_root)
    second = source(m, native_root, "receipt.json", b'{"done":true}\r\n')
    original_pin = m._Pin
    corrupted = []

    def corrupt(path, **kwargs):
        if Path(path).suffix == ".cap" and not corrupted:
            data = bytearray(Path(path).read_bytes())
            header = m._HEADER.size
            if case == "magic":
                data[0] ^= 1
            elif case == "count":
                data[8:12] = (129).to_bytes(4, "little")
            elif case == "truncated":
                del data[-1:]
            elif case == "offsetoverflow":
                data[header + 64 : header + 72] = (2**64 - 1).to_bytes(8, "little")
            elif case == "lengthoverflow":
                data[header + 72 : header + 80] = (2**64 - 1).to_bytes(8, "little")
            elif case == "duplicate":
                data[header + m._ENTRY.size : header + m._ENTRY.size + 64] = data[
                    header : header + 64
                ]
            elif case == "name":
                data[header] = 0xFF
            elif case == "seal":
                data[header + 80] ^= 1
            elif case == "payload":
                data[-1] ^= 1
            elif case == "trailing":
                data += b"foreign trailing bytes"
            elif case == "offsetgap":
                data[header + 64 : header + 72] = (
                    header + 2 * m._ENTRY.size + 1
                ).to_bytes(8, "little")
            else:
                data[header + len(first.name) + 1] = 1
            Path(path).write_bytes(data)
            corrupted.append(case)
        return original_pin(path, **kwargs)

    monkeypatch.setattr(m, "_Pin", corrupt)
    with m.CustodyStore(native_root) as store:
        with pytest.raises(m.CustodyError):
            store.capture([first, second], deadline=deadline())
        assert corrupted == [case]
        assert store._capsules == {}
        assert list(store._directory.glob("*.cap")) == []
        assert first.path.read_bytes() == b"RAW\r\n\x00exact\xff"


def test_source_seal_verified_before_any_capsule_recording(native_root, monkeypatch):
    m = api()
    entry = source(m, native_root)
    bad = m.SourceEntry(entry.name, entry.path, entry.length, "0" * 64)
    recordings = []
    original_open = Path.open

    def record_open(path, mode="r", *args, **kwargs):
        if path.suffix == ".cap" and "x" in mode:
            recordings.append(path)
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", record_open)
    with m.CustodyStore(native_root) as store:
        with pytest.raises(m.CustodyError):
            store.capture([bad], deadline=deadline())
        assert recordings == [], (
            "Se grabó cápsula antes de verificar el sello de la fuente"
        )
        assert store._capsules == {}


def test_opaque_ref_rejects_nonstring_identifiers(native_root):
    m = api()
    entry = source(m, native_root)
    with m.CustodyStore(native_root) as store:
        ref = store.capture([entry], deadline=deadline())
        with pytest.raises(m.CustodyError):
            store.read(
                m.CapsuleRef(ref.store_id, []),
                entry.name,
                offset=0,
                length=1,
                deadline=deadline(),
            )


def test_read_io_does_not_visit_other_historical_capsules(native_root, monkeypatch):
    m = api()
    entry = source(m, native_root)
    with m.CustodyStore(native_root) as store:
        refs = [store.capture([entry], deadline=deadline()) for _ in range(6)]
        target = store._capsules[refs[-1].capsule_id].pin.path
        visited = []
        original_verify = m._Pin.verify

        def track(pin):
            if pin.path.suffix == ".cap":
                visited.append(pin.path)
            return original_verify(pin)

        monkeypatch.setattr(m._Pin, "verify", track)
        assert (
            store.read(refs[-1], entry.name, offset=4, length=2, deadline=deadline())
            == b"\n\x00"
        )
        assert visited and set(visited) == {target}, (
            "Read visita otros contenedores del historial"
        )


def test_native_junction_alias_rejected_for_sources_and_namespace(native_root):
    """Reparse mount-point real sin depender del privilegio de symlinks."""
    m = api()
    target = native_root / "target"
    target.mkdir()
    entry = source(m, target)
    alias = native_root / "junction"
    alias.mkdir()
    dll = m._native()
    handle = dll.CreateFileW(str(alias), 0x40000000, 7, None, 3, 0x02200000, None)
    assert handle != m.ctypes.c_void_p(-1).value
    control = m.ctypes.WinDLL("kernel32", use_last_error=True).DeviceIoControl
    control.argtypes = [
        m.wintypes.HANDLE,
        m.wintypes.DWORD,
        m.ctypes.c_void_p,
        m.wintypes.DWORD,
        m.ctypes.c_void_p,
        m.wintypes.DWORD,
        m.ctypes.POINTER(m.wintypes.DWORD),
        m.ctypes.c_void_p,
    ]
    control.restype = m.wintypes.BOOL
    substitute = ("\\??\\" + str(target)).encode("utf-16-le")
    display = str(target).encode("utf-16-le")
    payload = (
        struct.pack("<HHHH", 0, len(substitute), len(substitute) + 2, len(display))
        + substitute
        + b"\0\0"
        + display
        + b"\0\0"
    )
    buffer = struct.pack("<IHH", 0xA0000003, len(payload), 0) + payload
    count = m.wintypes.DWORD()
    try:
        success = control(
            handle,
            0x000900A4,
            buffer,
            len(buffer),
            None,
            0,
            m.ctypes.byref(count),
            None,
        )
        if not success:
            pytest.skip(
                f"FSCTL_SET_REPARSE_POINT no soportado aquí: {m.ctypes.get_last_error()}"
            )
    finally:
        dll.CloseHandle(handle)
    try:
        assert (alias / entry.name).read_bytes() == b"RAW\r\n\x00exact\xff"
        with pytest.raises(m.CustodyError):
            m.CustodyStore(alias)
        with m.CustodyStore(native_root) as store:
            with pytest.raises(m.CustodyError):
                store.capture(
                    [
                        m.SourceEntry(
                            entry.name, alias / entry.name, entry.length, entry.seal
                        )
                    ],
                    deadline=deadline(),
                )
            assert store._capsules == {}
    finally:
        alias.rmdir()
    assert entry.path.read_bytes() == b"RAW\r\n\x00exact\xff"


def test_native_preexisting_hardlink_writer_denied(native_root):
    """Hardlink preexistente: el mismo pin nativo protege la cápsula."""
    m = api()
    entry = source(m, native_root)
    alias = native_root / "hardlink.bin"
    os.link(entry.path, alias)
    pin = m._Pin(entry.path)
    try:
        with pytest.raises(OSError), alias.open("r+b"):
            pytest.fail("Hardlink writer abierto con pin activo")
        assert pin.read(0, entry.length, deadline()) == b"RAW\r\n\x00exact\xff"
    finally:
        pin.close()
    alias.write_bytes(b"released")
    assert entry.path.read_bytes() == b"released"


@pytest.mark.parametrize(
    "stage", ["source_hash", "source_pin", "capsule_index", "capsule_hash"]
)
def test_real_deadline_expires_during_each_capture_stage(
    native_root, monkeypatch, stage
):
    """Inyección de latencia real; operaciones y bytes siguen siendo nativos."""
    m = api()
    entry = source(m, native_root)
    limit = time.monotonic() + 0.1
    delayed = []
    if stage == "source_pin":
        original = m._Pin.__init__

        def slow_pin(pin, path, **kwargs):
            original(pin, path, **kwargs)
            if pin.path == entry.path:
                delayed.append(stage)
                time.sleep(max(0, limit - time.monotonic()) + 0.01)

        monkeypatch.setattr(m._Pin, "__init__", slow_pin)
    else:
        original = m._Pin.read

        def slow_read(pin, offset, length, end):
            chosen = (
                (stage == "source_hash" and pin.path == entry.path)
                or (
                    stage == "capsule_index"
                    and pin.path.suffix == ".cap"
                    and offset == m._HEADER.size
                )
                or (
                    stage == "capsule_hash"
                    and pin.path.suffix == ".cap"
                    and length > m._ENTRY.size
                )
            )
            if chosen and not delayed:
                delayed.append(stage)
                time.sleep(max(0, limit - time.monotonic()) + 0.01)
            return original(pin, offset, length, end)

        monkeypatch.setattr(m._Pin, "read", slow_read)
    with m.CustodyStore(native_root) as store:
        with pytest.raises(m.CustodyError):
            store.capture([entry], deadline=limit)
        assert delayed == [stage]
        assert store._capsules == {}
        assert list(store._directory.glob("*.cap")) == []


def test_exact_64_mib_container_and_chunked_native_read(native_root):
    m = api()
    path = native_root / "large.bin"
    length = m.MAX_CAPSULE - m._HEADER.size - m._ENTRY.size
    chunk = b"a\r\n\0" * (m.MAX_READ // 4)
    digest = hashlib.sha256()
    with path.open("wb") as output:
        for offset in range(0, length, len(chunk)):
            data = chunk[: min(len(chunk), length - offset)]
            output.write(data)
            digest.update(data)
    entry = m.SourceEntry("large.bin", path, length, digest.hexdigest())
    with m.CustodyStore(native_root) as store:
        ref = store.capture([entry], deadline=deadline())
        capsule = store._capsules[ref.capsule_id]
        assert capsule.pin.identity[3] == 64 * 1024 * 1024
        assert (
            store.read(
                ref, entry.name, offset=0, length=m.MAX_READ, deadline=deadline()
            )
            == chunk
        )
        assert (
            store.read(
                ref, entry.name, offset=length - 4, length=4, deadline=deadline()
            )
            == b"a\r\n\0"
        )
        assert (
            store.read(ref, entry.name, offset=length, length=0, deadline=deadline())
            == b""
        )


def test_native_closed_index_accepts_128_entries_and_empty_bytes(native_root):
    m = api()
    entry = source(m, native_root, data=b"")
    entries = [
        m.SourceEntry(f"entry{i:03}.bin", entry.path, 0, entry.seal) for i in range(128)
    ]
    with m.CustodyStore(native_root) as store:
        ref = store.capture(entries, deadline=deadline())
        assert len(store._capsules[ref.capsule_id].entries) == 128
        assert (
            store.read(ref, entries[-1].name, offset=0, length=0, deadline=deadline())
            == b""
        )


def test_capture_freezes_caller_list_before_native_io(native_root, monkeypatch):
    """Caller modifica su lista durante IO; los sellos iniciales siguen mandando."""
    m = api()
    first = source(m, native_root)
    original = source(m, native_root, "receipt.bin", b"oldbytes")
    replacement = source(m, native_root, "other.bin", b"newbytes")
    entries = [first, original]
    original_pin = m._Pin
    mutated = []

    def mutate_list(path, **kwargs):
        if Path(path) == first.path and not mutated:
            entries[1] = m.SourceEntry(
                original.name, replacement.path, replacement.length, replacement.seal
            )
            mutated.append(True)
        return original_pin(path, **kwargs)

    monkeypatch.setattr(m, "_Pin", mutate_list)
    with m.CustodyStore(native_root) as store:
        ref = store.capture(entries, deadline=deadline())
        assert mutated == [True]
        assert (
            store.read(ref, original.name, offset=0, length=8, deadline=deadline())
            == b"oldbytes"
        )


@pytest.mark.parametrize("value", [None, 4, b"C:/invalid"])
def test_source_paths_reject_nonpath_types(native_root, value):
    m = api()
    entry = m.SourceEntry("raw.bin", value, 0, hashlib.sha256(b"").hexdigest())
    with m.CustodyStore(native_root) as store:
        with pytest.raises(m.CustodyError):
            store.capture([entry], deadline=deadline())
        assert store._capsules == {}


def custody_handle_flags(m):
    """APIs reales independientes del wrapper del producto, también en RED."""
    dll = m.ctypes.WinDLL("kernel32", use_last_error=True)
    dll.SetHandleInformation.argtypes = [
        m.wintypes.HANDLE,
        m.wintypes.DWORD,
        m.wintypes.DWORD,
    ]
    dll.SetHandleInformation.restype = m.wintypes.BOOL
    dll.GetHandleInformation.argtypes = [
        m.wintypes.HANDLE,
        m.ctypes.POINTER(m.wintypes.DWORD),
    ]
    dll.GetHandleInformation.restype = m.wintypes.BOOL
    return dll


def custody_alive(m, handle):
    info = m._FileInformation()
    return bool(m._native().GetFileInformationByHandle(handle, m.ctypes.byref(info)))


def custody_reuse(m, path, slot, handles):
    for _ in range(4096):
        handle = m._native().CreateFileW(
            str(path), 0x80000000, 7, None, 3, 0x00200000, None
        )
        assert handle != m.ctypes.c_void_p(-1).value
        handles.append(handle)
        if handle == slot:
            return handle
    pytest.fail("Windows no reutilizó el slot en 4096 aperturas reales")


@pytest.mark.parametrize("same_file", [False, True])
def test_recycled_guard_preserves_foreign_and_principal_disposition(
    native_root, same_file
):
    m = api()
    entry = source(m, native_root)
    other = source(m, native_root, "foreign.bin", b"foreign")
    pin = m._Pin(entry.path)
    main, guard = pin.handle, pin._guard
    flags = custody_handle_flags(m)
    handles = []
    try:
        assert flags.SetHandleInformation(guard, 2, 0)
        assert m._native().CloseHandle(guard)
        foreign = custody_reuse(
            m, entry.path if same_file else other.path, guard, handles
        )
        assert custody_alive(m, foreign) and custody_alive(m, main)
        assert not m._native().CompareObjectHandles(main, foreign)
        with pytest.raises(m.CustodyError):
            pin.verify()
        try:
            pin.close()
        except m.CustodyError as error:
            assert "unknown_quarantined" in str(error)
        assert custody_alive(m, foreign), "close destruyó el handle ajeno reciclado"
        assert not custody_alive(m, main) or (
            pin.handle == main and pin.disposition == "unknown_quarantined"
        ), "Principal propio abierto y referencia descartada"
    finally:
        for handle in {main, guard, *handles}:
            flags.SetHandleInformation(handle, 2, 0)
            m._native().CloseHandle(handle)
        if hasattr(m, "_QUARANTINED_PINS") and pin in m._QUARANTINED_PINS:
            m._QUARANTINED_PINS.remove(pin)


def test_owned_witness_blocks_ordinary_native_close(native_root):
    m = api()
    entry = source(m, native_root)
    pin = m._Pin(entry.path)
    main, guard = pin.handle, pin._guard
    flags = custody_handle_flags(m)
    try:
        assert not m._native().CloseHandle(guard), (
            "El witness propio permite cierre externo y reciclaje"
        )
        value = m.wintypes.DWORD()
        assert flags.GetHandleInformation(guard, m.ctypes.byref(value))
        assert value.value & 2
        assert pin.read(0, entry.length, deadline()) == b"RAW\r\n\x00exact\xff"
        pin.close()
        assert not custody_alive(m, main)
        assert not custody_alive(m, guard)
    finally:
        # Limpieza del test con referencias obtenidas directamente, sin nuevos opens.
        flags.SetHandleInformation(guard, 2, 0)
        m._native().CloseHandle(guard)
        m._native().CloseHandle(main)


@pytest.mark.parametrize("main_state", ["intact", "lost", "different", "same"])
@pytest.mark.parametrize("guard_state", ["unprotected", "lost", "different", "same"])
def test_guard_authority_loss_quarantines_without_foreign_close(
    native_root, main_state, guard_state
):
    """Pérdida y reciclaje reales; retirar protección es sabotaje explícito del proceso."""
    m = api()
    entry = source(m, native_root)
    other = source(m, native_root, "foreign.bin", b"foreign")
    pin = m._Pin(entry.path)
    main, guard = pin.handle, pin._guard
    flags = custody_handle_flags(m)
    handles = []
    try:
        if main_state != "intact":
            assert m._native().CloseHandle(main)
            if main_state != "lost":
                custody_reuse(
                    m, entry.path if main_state == "same" else other.path, main, handles
                )
        assert flags.SetHandleInformation(guard, 2, 0)
        if guard_state != "unprotected":
            assert m._native().CloseHandle(guard)
            if guard_state != "lost":
                custody_reuse(
                    m,
                    entry.path if guard_state == "same" else other.path,
                    guard,
                    handles,
                )
        live_before = {h for h in [main, guard, *handles] if custody_alive(m, h)}
        with pytest.raises(m.CustodyError):
            pin.verify()
        with pytest.raises(m.CustodyError, match="unknown_quarantined"):
            pin.close()
        assert pin.handle == main and pin._guard == guard
        assert pin.disposition == "unknown_quarantined"
        assert pin in m._QUARANTINED_PINS
        assert all(custody_alive(m, h) for h in live_before)
        if main_state == "intact":
            assert custody_alive(m, main), (
                "Principal propio perdido sin disposición explícita"
            )
        with pytest.raises(m.CustodyError, match="unknown_quarantined"):
            pin.close()
    finally:
        for handle in {main, guard, *handles}:
            flags.SetHandleInformation(handle, 2, 0)
            m._native().CloseHandle(handle)
        if hasattr(m, "_QUARANTINED_PINS") and pin in m._QUARANTINED_PINS:
            m._QUARANTINED_PINS.remove(pin)


@pytest.mark.parametrize("main_state", ["intact", "lost", "different", "same"])
def test_protected_witness_certifies_native_cleanup(native_root, main_state):
    m = api()
    entry = source(m, native_root)
    other = source(m, native_root, "foreign.bin", b"foreign")
    pin = m._Pin(entry.path)
    main, guard = pin.handle, pin._guard
    handles = []
    try:
        assert not m._native().CloseHandle(guard)
        if main_state != "intact":
            assert m._native().CloseHandle(main)
            if main_state != "lost":
                custody_reuse(
                    m, entry.path if main_state == "same" else other.path, main, handles
                )
            with pytest.raises(m.CustodyError):
                pin.verify()
        pin.close()
        assert pin.handle is None and pin._guard is None
        assert pin.disposition == "released"
        assert not custody_alive(m, guard)
        if main_state in ("intact", "lost"):
            assert not custody_alive(m, main)
        assert all(custody_alive(m, h) for h in handles)
        if main_state != "same":
            entry.path.open("r+b").close()
    finally:
        for handle in {main, guard, *handles}:
            custody_handle_flags(m).SetHandleInformation(handle, 2, 0)
            m._native().CloseHandle(handle)


@pytest.mark.parametrize(
    "operation",
    ["duplicate", "protect", "flags", "main_close", "unprotect", "guard_close"],
)
def test_native_fault_injection_retains_uncertain_resources(
    native_root, monkeypatch, operation
):
    """Fault injection explícita: llamadas no afectadas y handles son Windows reales."""
    m = api()
    entry = source(m, native_root)
    dll = m._native()
    flags = custody_handle_flags(m)
    pins = []
    original_init = m._Pin.__init__

    def remember(pin, *args, **kwargs):
        pins.append(pin)
        original_init(pin, *args, **kwargs)

    monkeypatch.setattr(m._Pin, "__init__", remember)
    pin = None
    if operation in ("main_close", "unprotect", "guard_close"):
        pin = m._Pin(entry.path)
    main = pin.handle if pin else None
    guard = pin._guard if pin else None

    class Fault:
        def __getattr__(self, name):
            return getattr(dll, name)

        def DuplicateHandle(self, *args):
            if operation == "duplicate":
                # Resultado real ERROR_INVALID_HANDLE, sin duplicado creado.
                return dll.DuplicateHandle(args[0], None, *args[2:])
            return dll.DuplicateHandle(*args)

        def SetHandleInformation(self, handle, mask, value):
            if (operation == "protect" and value == 2) or (
                operation == "unprotect" and value == 0
            ):
                return flags.SetHandleInformation(
                    m.ctypes.c_void_p(-1).value, mask, value
                )
            return flags.SetHandleInformation(handle, mask, value)

        def GetHandleInformation(self, handle, output):
            if operation == "flags":
                return flags.GetHandleInformation(m.ctypes.c_void_p(-1).value, output)
            return flags.GetHandleInformation(handle, output)

        def CloseHandle(self, handle):
            if (operation == "main_close" and handle == main) or (
                operation == "guard_close" and handle == guard
            ):
                return dll.CloseHandle(None)
            return dll.CloseHandle(handle)

    monkeypatch.setattr(m, "_native", lambda: Fault())
    try:
        if pin is None:
            with pytest.raises(m.CustodyError) as failure:
                m._Pin(entry.path)
            pin = pins[0]
            if operation in ("duplicate", "protect"):
                assert pin.disposition == "released"
                entry.path.write_bytes(b"released")
            else:
                assert "Witness" in str(failure.value)
                assert any("unknown_quarantined" in n for n in failure.value.__notes__)
                assert pin in m._QUARANTINED_PINS
                assert custody_alive(m, pin.handle) and custody_alive(m, pin._guard)
        else:
            with pytest.raises(m.CustodyError, match="unknown_quarantined"):
                pin.close()
            assert pin.disposition == "unknown_quarantined"
            assert pin in m._QUARANTINED_PINS
            assert custody_alive(m, guard)
            if operation == "main_close":
                assert pin.handle == main and custody_alive(m, main)
            else:
                assert pin.handle is None and not custody_alive(m, main)
            with pytest.raises(m.CustodyError, match="unknown_quarantined"):
                pin.close()
    finally:
        monkeypatch.setattr(m, "_native", lambda: dll)
        for resource in {main, guard, pin.handle, pin._guard} if pin else ():
            if resource is not None:
                flags.SetHandleInformation(resource, 2, 0)
                dll.CloseHandle(resource)
        if pin in m._QUARANTINED_PINS:
            m._QUARANTINED_PINS.remove(pin)


def test_duplicate_close_source_guard_loss_is_not_clean(native_root):
    """DUPLICATE_CLOSE_SOURCE real; no asumir que todos los cierres son CloseHandle."""
    m = api()
    entry = source(m, native_root)
    pin = m._Pin(entry.path)
    main, guard = pin.handle, pin._guard
    dll = m._native()
    duplicate = m.wintypes.HANDLE()
    process = dll.GetCurrentProcess()
    flags = custody_handle_flags(m)
    try:
        result = dll.DuplicateHandle(
            process, guard, process, m.ctypes.byref(duplicate), 0, False, 3
        )
        if custody_alive(m, guard):
            value = m.wintypes.DWORD()
            assert (
                flags.GetHandleInformation(guard, m.ctypes.byref(value))
                and value.value & 2
            )
            pin.verify()
            pin.close()
            assert not custody_alive(m, main) and not custody_alive(m, guard)
        else:
            assert result and custody_alive(m, duplicate.value)
            with pytest.raises(m.CustodyError):
                pin.verify()
            with pytest.raises(m.CustodyError, match="unknown_quarantined"):
                pin.close()
            assert custody_alive(m, main) and pin.handle == main
            assert custody_alive(m, duplicate.value)
            assert pin in m._QUARANTINED_PINS
    finally:
        for handle in {main, guard, duplicate.value} - {None}:
            flags.SetHandleInformation(handle, 2, 0)
            dll.CloseHandle(handle)
        if pin in m._QUARANTINED_PINS:
            m._QUARANTINED_PINS.remove(pin)


def test_store_cleanup_preserves_primary_and_retries_fail_closed(native_root):
    m = api()
    entry = source(m, native_root)
    store = m.CustodyStore(native_root)
    ref = store.capture([entry], deadline=deadline())
    pin = store._capsules[ref.capsule_id].pin
    main, guard = pin.handle, pin._guard
    flags = custody_handle_flags(m)
    assert flags.SetHandleInformation(guard, 2, 0)
    try:
        primary = ValueError("primary-original")
        with pytest.raises(ValueError) as caught, store:
            raise primary
        assert caught.value is primary
        assert any("unknown_quarantined" in n for n in primary.__notes__)
        assert custody_alive(m, main) and custody_alive(m, guard)
        assert all(p.disposition == "released" for p in store._pins)
        with pytest.raises(m.CustodyError, match="unknown_quarantined"):
            store.close()
        with pytest.raises(m.CustodyError):
            store.read(ref, entry.name, offset=0, length=1, deadline=deadline())
    finally:
        for handle in (main, guard):
            flags.SetHandleInformation(handle, 2, 0)
            m._native().CloseHandle(handle)
        m._QUARANTINED_PINS.remove(pin)


def test_real_protected_principal_close_failure_is_quarantined(native_root):
    m = api()
    entry = source(m, native_root)
    pin = m._Pin(entry.path)
    main, guard = pin.handle, pin._guard
    flags = custody_handle_flags(m)
    try:
        assert flags.SetHandleInformation(main, 2, 2)
        with pytest.raises(m.CustodyError, match="unknown_quarantined"):
            pin.close()
        assert custody_alive(m, main) and custody_alive(m, guard)
        assert pin.handle == main and pin._guard == guard
        assert pin in m._QUARANTINED_PINS
    finally:
        for handle in (main, guard):
            flags.SetHandleInformation(handle, 2, 0)
            m._native().CloseHandle(handle)
        m._QUARANTINED_PINS.remove(pin)


def test_capture_primary_error_retains_lost_source_witness(native_root, monkeypatch):
    m = api()
    entry = source(m, native_root)
    bad = m.SourceEntry(entry.name, entry.path, entry.length, "0" * 64)
    original_read = m._Pin.read
    sabotaged = []
    flags = custody_handle_flags(m)

    def read(pin, *args):
        result = original_read(pin, *args)
        if pin.path == entry.path and not sabotaged:
            assert flags.SetHandleInformation(pin._guard, 2, 0)
            sabotaged.append(pin)
        return result

    monkeypatch.setattr(m._Pin, "read", read)
    try:
        with m.CustodyStore(native_root) as store:
            with pytest.raises(m.CustodyError, match="Fuente no verificada") as primary:
                store.capture([bad], deadline=deadline())
            assert any("unknown_quarantined" in n for n in primary.value.__notes__)
            assert store._capsules == {}
            pin = sabotaged[0]
            assert pin in m._QUARANTINED_PINS
            assert custody_alive(m, pin.handle) and custody_alive(m, pin._guard)
    finally:
        for pin in sabotaged:
            for handle in (pin.handle, pin._guard):
                flags.SetHandleInformation(handle, 2, 0)
                m._native().CloseHandle(handle)
            m._QUARANTINED_PINS.remove(pin)
