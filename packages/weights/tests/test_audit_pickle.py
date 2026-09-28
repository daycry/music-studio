import pytest
from weights.audit_pickle import PickleSecurityError, load_restricted, scan_opcodes

from .pickle_fixtures import (
    build_malicious_builtins_eval_pickle,
    build_malicious_pickle,
    build_single_tensor_pickle,
)


def test_scan_opcodes_accepts_allowlisted_tensor_pickle():
    data = build_single_tensor_pickle("0", "cpu", numel=6, size=(2, 3), stride=(3, 1))
    globals_found = scan_opcodes(data)
    assert ("torch._utils", "_rebuild_tensor_v2") in globals_found
    assert ("torch", "FloatStorage") in globals_found
    assert ("collections", "OrderedDict") in globals_found


def test_scan_opcodes_rejects_os_system():
    data = build_malicious_pickle()
    with pytest.raises(PickleSecurityError, match=r"os\.system"):
        scan_opcodes(data)


def test_scan_opcodes_rejects_builtins_eval():
    data = build_malicious_builtins_eval_pickle()
    with pytest.raises(PickleSecurityError, match=r"builtins\.eval"):
        scan_opcodes(data)


def test_load_restricted_never_executes_malicious_payload():
    """El auditor rechaza el pickle SIN ejecutar `os.system`: si lo hubiera
    ejecutado, este test dejaría un rastro (crearía un fichero). No debe
    existir.
    """
    import pathlib
    import tempfile

    marker = pathlib.Path(tempfile.gettempdir()) / "music-studio-pwned-marker.txt"
    marker.unlink(missing_ok=True)

    data = build_malicious_pickle()  # os.system('echo pwned') si se ejecutase

    def storage_reader(dtype_name, key, numel, location):  # pragma: no cover
        raise AssertionError("no debería llamarse: el pickle no tiene tensores")

    with pytest.raises(PickleSecurityError):
        load_restricted(data, storage_reader)

    assert not marker.exists()


def test_load_restricted_reconstructs_tensor_ref_without_torch():
    values_numel = 6
    data = build_single_tensor_pickle("0", "cpu", numel=values_numel, size=(2, 3), stride=(3, 1))

    captured = {}

    def storage_reader(dtype_name, key, numel, location):
        captured["dtype_name"] = dtype_name
        captured["key"] = key
        captured["numel"] = numel
        captured["location"] = location
        import struct

        raw = struct.pack("<6f", 1.0, 2.0, 3.0, 4.0, 5.0, 6.0)
        from weights.audit_pickle import _StorageRef

        return _StorageRef(key=key, location=location, numel=numel, dtype_name=dtype_name, data=raw)

    ref = load_restricted(data, storage_reader)
    assert captured["dtype_name"] == "FloatStorage"
    assert captured["key"] == "0"
    assert captured["numel"] == values_numel
    assert captured["location"] == "cpu"
    assert ref.size == (2, 3)
    assert ref.stride == (3, 1)
    assert ref.storage.data is not None
