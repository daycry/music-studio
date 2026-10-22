"""ABI y unión del collector con bibliotecas falsas; ninguna llamada UI/GPU real."""

from types import SimpleNamespace

import pytest


class Function:
    def __init__(self, call):
        self.call = call

    def __call__(self, *args):
        return self.call(*args)


def test_dxgi_enumerates_exact_luid_and_releases_com(harness_module, monkeypatch):
    windows = harness_module("benchmark_windows")
    releases = []

    def factory(iid, output):
        assert iid._obj.Data1 == 0x770AAE78
        output._obj.value = 1
        return 0

    monkeypatch.setattr(
        windows.ctypes,
        "WinDLL",
        lambda name: SimpleNamespace(CreateDXGIFactory1=Function(factory)),
    )

    def method(pointer, index, *types):
        if index == 12:

            def enum(factory, index, output):
                if index:
                    return 0x887A0002
                output._obj.value = 2
                return 0

            return enum
        if index == 10:

            def description(adapter, output):
                output._obj.Description = "NVIDIA GeForce RTX 5070"
                output._obj.VendorId = 0x10DE
                output._obj.DeviceId = 0x123
                output._obj.AdapterLuid.LowPart = 0x1234
                output._obj.AdapterLuid.HighPart = -1
                output._obj.DedicatedVideoMemory = 12 * 1024**3
                return 0

            return description
        return lambda pointer: releases.append(pointer.value)

    monkeypatch.setattr(windows, "com_method", method)
    adapters = windows.enumerate_adapters()
    assert adapters[0]["luid_high"] == 0xFFFFFFFF and adapters[0]["luid_low"] == 0x1234
    assert releases == [2, 1]


def test_pdh_localizes_expands_and_samples_only_exact_adapter(
    harness_module, monkeypatch
):
    windows = harness_module("benchmark_windows")
    import winreg

    names = {1: "Memoria del adaptador GPU", 2: "Uso compartido", 3: "Uso dedicado"}

    class Key:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(winreg, "OpenKey", lambda *args: Key())
    monkeypatch.setattr(
        winreg,
        "QueryValueEx",
        lambda *args: (
            ["1", "GPU Adapter Memory", "2", "Shared Usage", "3", "Dedicated Usage"],
            7,
        ),
    )

    def local(machine, index, buffer, size):
        size._obj.value = len(names[index]) + 1
        if buffer is not None:
            buffer.value = names[index]
        return 0

    instance = "luid_0x00000000_0x00001234_phys_0"

    def expand(machine, path, buffer, size, flags):
        assert "Memoria del adaptador GPU" in path
        text = f"\\Memoria del adaptador GPU({instance})\\Uso compartido\0"
        size._obj.value = len(text) + 1
        if buffer is not None:
            for i, char in enumerate(text):
                buffer[i] = char
        return 0

    def query(source, data, handle):
        handle._obj.value = 9
        return 0

    def counter(query, path, data, handle):
        handle._obj.value = 1 if "compartido" in path else 2
        return 0

    def value(counter, fmt, typeptr, output):
        output._obj.CStatus = 0
        output._obj.doubleValue = (64 if counter.value == 1 else 1000) * 1024**2
        return 0

    closed = []
    pdh = SimpleNamespace(
        PdhLookupPerfNameByIndexW=Function(local),
        PdhExpandWildCardPathW=Function(expand),
        PdhOpenQueryW=Function(query),
        PdhAddCounterW=Function(counter),
        PdhCollectQueryData=Function(lambda query: 0),
        PdhGetFormattedCounterValue=Function(value),
        PdhCloseQuery=Function(lambda query: closed.append(query.value)),
    )
    monkeypatch.setattr(windows.ctypes, "WinDLL", lambda name: pdh)
    monkeypatch.setattr(
        windows,
        "enumerate_adapters",
        lambda: [
            {
                "vendor_id": 0x10DE,
                "description": "NVIDIA GeForce RTX 5070",
                "luid_high": 0,
                "luid_low": 0x1234,
            }
        ],
    )
    collector = windows.WindowsGpuMemory("NVIDIA GeForce RTX 5070")
    sample = collector.sample()
    assert sample["shared_mb"] == 64 and sample["dedicated_mb"] == 1000
    assert sample["instance"] == instance
    assert sample["pdh_status"]["shared_mb"]["cstatus"] == 0
    collector.close()
    assert closed == [9]
    collector.close()
    assert closed == [9]


def test_browser_heartbeat_requires_visible_hwnd_exact_pid_and_executable(
    harness_module, monkeypatch
):
    windows = harness_module("benchmark_windows")
    pid = 123
    executable = "msedge.exe"

    def process(hwnd, result):
        result._obj.value = pid
        return 1

    def image(handle, flags, buffer, size):
        buffer.value = "C:\\private\\" + executable
        return 1

    user = SimpleNamespace(
        IsWindow=Function(lambda hwnd: 1),
        IsWindowVisible=Function(lambda hwnd: 1),
        GetWindowThreadProcessId=Function(process),
    )
    kernel = SimpleNamespace(
        OpenProcess=Function(lambda *args: 1),
        QueryFullProcessImageNameW=Function(image),
        CloseHandle=Function(lambda handle: None),
    )
    monkeypatch.setattr(
        windows.ctypes, "WinDLL", lambda name: user if name == "user32" else kernel
    )
    browser = {"pid": pid, "hwnd": 321}
    result = windows.WindowsGpuMemory.browser_heartbeat(browser)
    assert result["visible"] and result["executable"] == "msedge.exe"
    assert "private" not in str(result)
    assert not windows.WindowsGpuMemory.browser_heartbeat({**browser, "pid": 99})[
        "visible"
    ]
    executable = "python.exe"
    assert not windows.WindowsGpuMemory.browser_heartbeat(browser)["visible"]


def test_localized_counter_absent_is_not_silently_english(harness_module, monkeypatch):
    windows = harness_module("benchmark_windows")
    import winreg

    class Key:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(winreg, "OpenKey", lambda *args: Key())
    monkeypatch.setattr(winreg, "QueryValueEx", lambda *args: (["1", "unrelated"], 7))
    collector = windows.WindowsGpuMemory.__new__(windows.WindowsGpuMemory)
    with pytest.raises(ValueError, match="unresolved"):
        collector.localized("GPU Adapter Memory")


def test_registry_multisz_trailing_empty_terminator_is_supported(
    harness_module, monkeypatch
):
    windows = harness_module("benchmark_windows")
    import winreg

    class Key:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(winreg, "OpenKey", lambda *args: Key())
    monkeypatch.setattr(
        winreg, "QueryValueEx", lambda *args: (["7", "GPU Adapter Memory", ""], 7)
    )

    def localized(machine, index, buffer, size):
        assert index == 7
        size._obj.value = 6
        if buffer is not None:
            buffer.value = "Local"
        return 0

    collector = windows.WindowsGpuMemory.__new__(windows.WindowsGpuMemory)
    collector.pdh = SimpleNamespace(PdhLookupPerfNameByIndexW=Function(localized))
    assert collector.localized("GPU Adapter Memory") == "Local"


def test_duplicate_counter_indices_accept_only_unique_localized_name(
    harness_module, monkeypatch
):
    windows = harness_module("benchmark_windows")
    import winreg

    class Key:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(winreg, "OpenKey", lambda *args: Key())
    monkeypatch.setattr(
        winreg,
        "QueryValueEx",
        lambda *args: (["5818", "Shared Usage", "5826", "Shared Usage", ""], 7),
    )
    translated = {5818: "Compartida", 5826: "Compartida"}

    def localized(machine, index, buffer, size):
        size._obj.value = len(translated[index]) + 1
        if buffer is not None:
            buffer.value = translated[index]
        return 0

    collector = windows.WindowsGpuMemory.__new__(windows.WindowsGpuMemory)
    collector.pdh = SimpleNamespace(PdhLookupPerfNameByIndexW=Function(localized))
    assert collector.localized("Shared Usage") == "Compartida"
    translated[5826] = "Distinta"
    with pytest.raises(ValueError, match="unresolved"):
        collector.localized("Shared Usage")


def test_operation_utc_preserves_native_clock_tick_without_microsecond_rounding(
    harness_module, monkeypatch
):
    windows = harness_module("benchmark_windows")
    ticks = iter([134358072800888323, 134358072800888325])

    def read(output):
        tick = next(ticks)
        output._obj.dwLowDateTime = tick & 0xFFFFFFFF
        output._obj.dwHighDateTime = tick >> 32

    kernel = SimpleNamespace(GetSystemTimeAsFileTime=Function(read))
    monkeypatch.setattr(windows.ctypes, "windll", SimpleNamespace(kernel32=kernel))
    value = windows.operation_finish(windows.operation_start())
    assert value["started_utc"] == "2026-10-07T00:41:20.0888323+00:00"
    assert value["finished_utc"] == "2026-10-07T00:41:20.0888325+00:00"
    assert value["finished_monotonic_ns"] >= value["started_monotonic_ns"]


@pytest.mark.parametrize(
    "case", ["ok", "zone_change", "conversion_error", "query_offset", "counter_offset"]
)
def test_native_pdh_conversion_preserves_originals_and_fails_closed(
    harness_module, monkeypatch, case
):
    import copy
    import ctypes

    windows = harness_module("benchmark_windows")
    local_tick = 134358120000088324
    utc_tick = local_tick - 72000000000
    collector = windows.WindowsGpuMemory.__new__(windows.WindowsGpuMemory)
    collector.instance = "luid_0x00000000_0x00001234_phys_0"
    collector.adapters = [
        {
            "description": "NVIDIA GeForce RTX 5070",
            "vendor_id": 0x10DE,
            "luid_high": 0,
            "luid_low": 4660,
        }
    ]
    collector.paths = {name: name for name in ("shared_mb", "dedicated_mb")}
    collector.query = ctypes.c_void_p(9)
    collector.counters = {
        name: ctypes.c_void_p(i) for i, name in enumerate(collector.paths, 1)
    }

    def collect(query, out):
        out._obj.value = local_tick
        return 0

    def raw(counter, kind, out):
        kind._obj.value = 0x10100
        out._obj.FirstValue = 40 * 2**20
        out._obj.TimeStamp.dwLowDateTime = local_tick & 0xFFFFFFFF
        out._obj.TimeStamp.dwHighDateTime = local_tick >> 32
        return 0

    def formatted(counter, flags, kind, out):
        kind._obj.value = 0x10100
        out._obj.doubleValue = 40 * 2**20
        return 0

    def info(counter, explain, size, output):
        size._obj.value = 512
        if output is not None:
            data = ctypes.cast(output, ctypes.POINTER(windows.CounterInfo)).contents
            data.dwType = 0x10100
        return 0

    collector.pdh = SimpleNamespace(
        PdhCollectQueryDataWithTime=collect,
        PdhGetRawCounterValue=raw,
        PdhGetFormattedCounterValue=formatted,
        PdhGetCounterInfoW=info,
    )
    zone = {
        "id": 2,
        "bias_minutes": -60,
        "standard_bias_minutes": 0,
        "daylight_bias_minutes": -60,
        "standard_name": "CPU standard",
        "daylight_name": "CPU daylight",
        "standard_date": [0, 10, 0, 5, 2, 0, 0, 0],
        "daylight_date": [0, 3, 0, 5, 2, 0, 0, 0],
    }
    reads = [0]

    def snapshot():
        reads[0] += 1
        result = copy.deepcopy(zone)
        if case == "zone_change" and reads[0] >= 2:
            result["id"] = 1
        return result

    conversions = []

    def convert(tick):
        conversions.append(tick)
        if case == "conversion_error":
            raise ValueError("filetime_conversion_failed")
        if case == "query_offset" or (
            case == "counter_offset" and len(conversions) > 1
        ):
            return utc_tick + 1
        return utc_tick

    monkeypatch.setattr(windows, "timezone_snapshot", snapshot)
    monkeypatch.setattr(windows, "local_filetime_to_utc", convert)
    monkeypatch.setattr(windows, "utc_now", lambda: "2026-10-07T00:00:00.0088324+00:00")
    if case != "ok":
        with pytest.raises(
            ValueError, match="filetime_(clock_changed|conversion_failed)"
        ):
            collector.sample()
        return
    result = collector.sample()
    assert result["query_filetime"] == local_tick
    assert result["query_utc_filetime"] == utc_tick
    assert conversions == [local_tick] * 3 and reads == [3]
    assert result["filetime_clock"]["timezone_before"] == zone
    assert result["filetime_clock"]["timezone_after"] == zone
    for counter in result["counters"].values():
        assert counter["raw_filetime"] == local_tick
        assert counter["raw_utc_filetime"] == utc_tick
