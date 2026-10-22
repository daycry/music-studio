"""DXGI/PDH/heartbeat Windows, sólo lectura, biblioteca estándar."""

import ctypes
import math
import os
import sys
import time
from ctypes import wintypes
from pathlib import PureWindowsPath

from benchmark_clock import (
    local_filetime_to_utc,
    timezone_offset_ticks,
    timezone_snapshot,
    utc_now,
)
from benchmark_observers import counter_paths, map_5070


class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", ctypes.c_uint32),
        ("Data2", ctypes.c_uint16),
        ("Data3", ctypes.c_uint16),
        ("Data4", ctypes.c_ubyte * 8),
    ]


class LUID(ctypes.Structure):
    _fields_ = [("LowPart", ctypes.c_uint32), ("HighPart", ctypes.c_int32)]


class AdapterDesc(ctypes.Structure):
    _fields_ = [
        ("Description", ctypes.c_wchar * 128),
        ("VendorId", ctypes.c_uint32),
        ("DeviceId", ctypes.c_uint32),
        ("SubSysId", ctypes.c_uint32),
        ("Revision", ctypes.c_uint32),
        ("DedicatedVideoMemory", ctypes.c_size_t),
        ("DedicatedSystemMemory", ctypes.c_size_t),
        ("SharedSystemMemory", ctypes.c_size_t),
        ("AdapterLuid", LUID),
        ("Flags", ctypes.c_uint32),
    ]


def com_method(pointer, index, restype, *argtypes):
    vtable = ctypes.cast(
        pointer, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))
    ).contents
    return ctypes.WINFUNCTYPE(restype, ctypes.c_void_p, *argtypes)(vtable[index])


def enumerate_adapters():
    if os.name != "nt":
        raise ValueError("windows_required")
    dxgi = ctypes.WinDLL("dxgi")
    factory = ctypes.c_void_p()
    iid = GUID(
        0x770AAE78,
        0xF26F,
        0x4DBA,
        (ctypes.c_ubyte * 8)(0xA8, 0x29, 0x25, 0x3C, 0x83, 0xD1, 0xB3, 0x87),
    )
    dxgi.CreateDXGIFactory1.argtypes = [
        ctypes.POINTER(GUID),
        ctypes.POINTER(ctypes.c_void_p),
    ]
    dxgi.CreateDXGIFactory1.restype = ctypes.c_int32
    if dxgi.CreateDXGIFactory1(ctypes.byref(iid), ctypes.byref(factory)):
        raise ValueError("dxgi_factory_failed")
    adapters = []
    try:
        enum = com_method(
            factory,
            12,
            ctypes.c_int32,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_void_p),
        )
        index = 0
        while True:
            adapter = ctypes.c_void_p()
            result = enum(factory, index, ctypes.byref(adapter))
            if result & 0xFFFFFFFF == 0x887A0002:
                break
            if result:
                raise ValueError("dxgi_enumeration_failed")
            try:
                desc = AdapterDesc()
                if com_method(adapter, 10, ctypes.c_int32, ctypes.POINTER(AdapterDesc))(
                    adapter, ctypes.byref(desc)
                ):
                    raise ValueError("dxgi_description_failed")
                adapters.append(
                    {
                        "description": desc.Description,
                        "vendor_id": desc.VendorId,
                        "device_id": desc.DeviceId,
                        "luid_high": desc.AdapterLuid.HighPart & 0xFFFFFFFF,
                        "luid_low": desc.AdapterLuid.LowPart,
                        "dedicated_video_bytes": desc.DedicatedVideoMemory,
                    }
                )
            finally:
                com_method(adapter, 2, ctypes.c_uint32)(adapter)
            index += 1
    finally:
        com_method(factory, 2, ctypes.c_uint32)(factory)
    return adapters


class CounterValue(ctypes.Structure):
    _fields_ = [("CStatus", ctypes.c_uint32), ("doubleValue", ctypes.c_double)]


class RawCounter(ctypes.Structure):
    _fields_ = [
        ("CStatus", ctypes.c_uint32),
        ("TimeStamp", wintypes.FILETIME),
        ("FirstValue", ctypes.c_int64),
        ("SecondValue", ctypes.c_int64),
        ("MultiCount", ctypes.c_uint32),
    ]


class CounterInfo(ctypes.Structure):
    # Public PDH_COUNTER_INFO_W prefix, before its string/union fields.
    _fields_ = [
        ("dwLength", ctypes.c_uint32),
        ("dwType", ctypes.c_uint32),
        ("CVersion", ctypes.c_uint32),
        ("CStatus", ctypes.c_uint32),
        ("lScale", ctypes.c_int32),
        ("lDefaultScale", ctypes.c_int32),
        ("dwUserData", ctypes.c_size_t),
        ("dwQueryUserData", ctypes.c_size_t),
    ]


def operation_start():
    return {
        "started_utc": utc_now(),
        "started_monotonic_ns": time.perf_counter_ns(),
    }


def operation_finish(value):
    return {
        **value,
        "finished_utc": utc_now(),
        "finished_monotonic_ns": time.perf_counter_ns(),
    }


class IncompleteWindowsSample(ValueError):
    """A later failure never discards values already returned by native calls."""

    def __init__(self, error, partial_sample):
        super().__init__(str(error))
        self.partial_sample = partial_sample


class WindowsGpuMemory:
    def __init__(self, nvidia_name, *, progress_callback=None):
        self.progress_callback = progress_callback
        if os.name != "nt":
            raise ValueError("windows_required")
        self.pdh = ctypes.WinDLL("pdh")
        self.pdh.PdhLookupPerfNameByIndexW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self.pdh.PdhExpandWildCardPathW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.LPCWSTR,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.DWORD,
        ]
        self.pdh.PdhOpenQueryW.argtypes = [
            wintypes.LPCWSTR,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self.pdh.PdhAddCounterW.argtypes = [
            ctypes.c_void_p,
            wintypes.LPCWSTR,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        self.pdh.PdhCollectQueryData.argtypes = [ctypes.c_void_p]
        self.pdh.PdhGetFormattedCounterValue.argtypes = [
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            ctypes.POINTER(CounterValue),
        ]
        for name, args in (
            (
                "PdhCollectQueryDataWithTime",
                [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int64)],
            ),
            (
                "PdhGetRawCounterValue",
                [
                    ctypes.c_void_p,
                    ctypes.POINTER(wintypes.DWORD),
                    ctypes.POINTER(RawCounter),
                ],
            ),
            (
                "PdhGetCounterInfoW",
                [
                    ctypes.c_void_p,
                    wintypes.BOOL,
                    ctypes.POINTER(wintypes.DWORD),
                    ctypes.c_void_p,
                ],
            ),
        ):
            if hasattr(self.pdh, name):
                getattr(self.pdh, name).argtypes = args
        self.pdh.PdhCloseQuery.argtypes = [ctypes.c_void_p]
        self.object_name = self.localized("GPU Adapter Memory")
        shared_name, dedicated_name = (
            self.localized("Shared Usage"),
            self.localized("Dedicated Usage"),
        )
        expanded = self.expand(counter_paths(self.object_name, shared_name, "*"))
        instances = [path.split("(", 1)[1].split(")", 1)[0] for path in expanded]
        self.adapters = enumerate_adapters()
        self.instance = map_5070(self.adapters, instances, nvidia_name)
        self.paths = {
            "shared_mb": counter_paths(self.object_name, shared_name, self.instance),
            "dedicated_mb": counter_paths(
                self.object_name, dedicated_name, self.instance
            ),
        }
        self.query = ctypes.c_void_p()
        if self.pdh.PdhOpenQueryW(None, 0, ctypes.byref(self.query)):
            raise ValueError("pdh_query_failed")
        self.counters = {}
        try:
            for name, path in self.paths.items():
                counter = ctypes.c_void_p()
                if self.pdh.PdhAddCounterW(self.query, path, 0, ctypes.byref(counter)):
                    raise ValueError("pdh_counter_failed")
                self.counters[name] = counter
        except Exception:
            self.close()
            raise

    def localized(self, english):
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Perflib\009",
        ) as key:
            names, _ = winreg.QueryValueEx(key, "Counter")
        if len(names) % 2:
            if names[-1] != "":
                raise ValueError("localized_counter_catalog_invalid")
            names = names[:-1]
        indices = [
            int(names[i]) for i in range(0, len(names), 2) if names[i + 1] == english
        ]
        if not indices:
            raise ValueError("localized_counter_unresolved")
        translated = set()
        for index in indices:
            size = wintypes.DWORD(0)
            self.pdh.PdhLookupPerfNameByIndexW(None, index, None, ctypes.byref(size))
            if not size.value:
                raise ValueError("localized_counter_unresolved")
            buffer = ctypes.create_unicode_buffer(size.value)
            if (
                self.pdh.PdhLookupPerfNameByIndexW(
                    None, index, buffer, ctypes.byref(size)
                )
                or not buffer.value
            ):
                raise ValueError("localized_counter_unresolved")
            translated.add(buffer.value)
        if len(translated) != 1:
            raise ValueError("localized_counter_unresolved")
        return translated.pop()

    def expand(self, path):
        size = wintypes.DWORD(0)
        self.pdh.PdhExpandWildCardPathW(None, path, None, ctypes.byref(size), 0)
        if not size.value:
            raise ValueError("counter_instances_unavailable")
        buffer = ctypes.create_unicode_buffer(size.value)
        if self.pdh.PdhExpandWildCardPathW(None, path, buffer, ctypes.byref(size), 0):
            raise ValueError("counter_instances_unavailable")
        return [p for p in buffer[:].split("\0") if p]

    def sample(self):
        self.partial_sample = None
        try:
            return self._sample()
        except (OSError, ValueError, RuntimeError) as error:
            if self.partial_sample is None:
                raise
            self.partial_sample["status"] = "incomplete_invalid"
            self.partial_sample["error"] = str(error)
            raise IncompleteWindowsSample(error, self.partial_sample) from error

    def _emit_progress(self, value):
        callback = getattr(self, "progress_callback", None)
        if callback is not None:
            callback(value)

    def _sample(self):
        result = {
            "windows_build": ".".join(
                map(str, sys.getwindowsversion().platform_version)
            ),
            "scope": "adapter_aggregate",
            "gpu_mapping_status": "resolved",
            "instance": self.instance,
            "paths": self.paths,
            "shared_mb": None,
            "dedicated_mb": None,
            "pdh_status": {},
        }
        self.partial_sample = result
        native = all(
            hasattr(self.pdh, name)
            for name in (
                "PdhCollectQueryDataWithTime",
                "PdhGetRawCounterValue",
                "PdhGetCounterInfoW",
            )
        )
        zone_before = timezone_snapshot() if native else None
        collection = operation_start()
        query_time = ctypes.c_int64()
        collected = (
            self.pdh.PdhCollectQueryDataWithTime(self.query, ctypes.byref(query_time))
            if native
            else self.pdh.PdhCollectQueryData(self.query)
        )
        result["collection"] = operation_finish(collection)
        result["query_filetime"] = query_time.value if native else None
        result["collect_return"] = collected & 0xFFFFFFFF
        self._emit_progress(result)
        if native:
            result["query_utc_filetime"] = local_filetime_to_utc(query_time.value)
        adapter = next(
            a
            for a in self.adapters
            if a["description"] == "NVIDIA GeForce RTX 5070"
            and a["vendor_id"] == 0x10DE
        )
        result["adapter_luid"] = [
            adapter["luid_high"] & 0xFFFFFFFF,
            adapter["luid_low"],
        ]
        result["dxgi_inventory"] = self.adapters
        result["counters"] = {}
        self._emit_progress(result)
        for name, counter in self.counters.items():
            value, kind = CounterValue(), wintypes.DWORD()
            status = self.pdh.PdhGetFormattedCounterValue(
                counter,
                0x1200 if native else 0x200,
                ctypes.byref(kind) if native else None,
                ctypes.byref(value),
            )
            result["pdh_status"][name] = {
                "collect": collected & 0xFFFFFFFF,
                "return": status & 0xFFFFFFFF,
                "cstatus": value.CStatus,
            }
            if (
                not collected
                and not status
                and value.CStatus in {0, 1}
                and math.isfinite(value.doubleValue)
                and value.doubleValue >= 0
            ):
                result[name] = value.doubleValue / 1024**2
            self._emit_progress(result)
            if native:
                raw, raw_kind = RawCounter(), wintypes.DWORD()
                raw_status = self.pdh.PdhGetRawCounterValue(
                    counter, ctypes.byref(raw_kind), ctypes.byref(raw)
                )
                result["counters"][name] = {
                    "counter_type": kind.value,
                    "raw_counter_type": raw_kind.value,
                    "info_counter_type": None,
                    "info_return": None,
                    "scale": None,
                    "default_scale": None,
                    "raw_unit": "unknown",
                    "format_flags": 0x1200,
                    "conversion": "bytes/2**20",
                    "path": self.paths[name],
                    "raw_return": raw_status & 0xFFFFFFFF,
                    "format_return": status & 0xFFFFFFFF,
                    "raw_cstatus": raw.CStatus,
                    "formatted_cstatus": value.CStatus,
                    "raw_value": raw.FirstValue,
                    "raw_second_value": raw.SecondValue,
                    "raw_multi_count": raw.MultiCount,
                    "raw_filetime": (raw.TimeStamp.dwHighDateTime << 32)
                    | raw.TimeStamp.dwLowDateTime,
                    "formatted_value": value.doubleValue
                    if math.isfinite(value.doubleValue)
                    else None,
                    "formatted_nonfinite": None
                    if math.isfinite(value.doubleValue)
                    else str(value.doubleValue),
                }
                self._emit_progress(result)
                size = wintypes.DWORD(0)
                self.pdh.PdhGetCounterInfoW(counter, False, ctypes.byref(size), None)
                if size.value < ctypes.sizeof(CounterInfo):
                    raise ValueError("pdh_metadata_unavailable")
                buffer = ctypes.create_string_buffer(size.value)
                info_status = self.pdh.PdhGetCounterInfoW(
                    counter, False, ctypes.byref(size), buffer
                )
                info = ctypes.cast(buffer, ctypes.POINTER(CounterInfo)).contents
                result["counters"][name] = {
                    "counter_type": kind.value,
                    "raw_counter_type": raw_kind.value,
                    "info_counter_type": info.dwType,
                    "info_return": info_status & 0xFFFFFFFF,
                    "scale": info.lScale,
                    "default_scale": info.lDefaultScale,
                    "raw_unit": "bytes"
                    if kind.value == raw_kind.value == info.dwType == 0x10100
                    else "unknown",
                    "format_flags": 0x1200,
                    "conversion": "bytes/2**20",
                    "path": self.paths[name],
                    "raw_return": raw_status & 0xFFFFFFFF,
                    "format_return": status & 0xFFFFFFFF,
                    "raw_cstatus": raw.CStatus,
                    "formatted_cstatus": value.CStatus,
                    "raw_value": raw.FirstValue,
                    "raw_second_value": raw.SecondValue,
                    "raw_multi_count": raw.MultiCount,
                    "raw_filetime": (raw.TimeStamp.dwHighDateTime << 32)
                    | raw.TimeStamp.dwLowDateTime,
                    "formatted_value": value.doubleValue
                    if math.isfinite(value.doubleValue)
                    else None,
                    "formatted_nonfinite": None
                    if math.isfinite(value.doubleValue)
                    else str(value.doubleValue),
                }
            self._emit_progress(result)
        if native:
            zone_after = timezone_snapshot()
            offset = timezone_offset_ticks(zone_before)
            if (
                zone_after != zone_before
                or result["query_filetime"] - result["query_utc_filetime"] != offset
            ):
                raise ValueError("pdh_filetime_clock_changed")
            for counter in result["counters"].values():
                counter["raw_utc_filetime"] = local_filetime_to_utc(
                    counter["raw_filetime"]
                )
                if counter["raw_filetime"] - counter["raw_utc_filetime"] != offset:
                    raise ValueError("pdh_filetime_clock_changed")
            if timezone_snapshot() != zone_before:
                raise ValueError("pdh_filetime_clock_changed")
            result["filetime_clock"] = {
                "basis": "local",
                "conversion": "LocalFileTimeToFileTime",
                "timezone_before": zone_before,
                "timezone_after": zone_after,
            }
        self._emit_progress(result)
        return result

    @staticmethod
    def browser_heartbeat(browser):
        user32, kernel32 = ctypes.WinDLL("user32"), ctypes.WinDLL("kernel32")
        user32.IsWindow.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        native = all(
            hasattr(user32, name) for name in ("GetWindowRect", "IsIconic")
        ) and hasattr(kernel32, "GetProcessTimes")
        if native:
            user32.GetWindowRect.argtypes = [
                wintypes.HWND,
                ctypes.POINTER(wintypes.RECT),
            ]
            user32.IsIconic.argtypes = [wintypes.HWND]
            kernel32.GetProcessTimes.argtypes = [wintypes.HANDLE] + [
                ctypes.POINTER(wintypes.FILETIME)
            ] * 4
        hwnd = int(browser["hwnd"])
        pid = wintypes.DWORD()
        visible = bool(user32.IsWindow(hwnd) and user32.IsWindowVisible(hwnd))
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value != browser["pid"]:
            visible = False
        executable = None
        creation_time = None
        rect = None
        iconic = None
        handle = kernel32.OpenProcess(0x1000, False, pid.value)
        if handle:
            try:
                size = wintypes.DWORD(32768)
                buffer = ctypes.create_unicode_buffer(size.value)
                if kernel32.QueryFullProcessImageNameW(
                    handle, 0, buffer, ctypes.byref(size)
                ):
                    executable = PureWindowsPath(buffer.value).name.lower()
                if native:
                    created, exited, kernel, user = (
                        wintypes.FILETIME() for _ in range(4)
                    )
                    if kernel32.GetProcessTimes(
                        handle,
                        ctypes.byref(created),
                        ctypes.byref(exited),
                        ctypes.byref(kernel),
                        ctypes.byref(user),
                    ):
                        creation_time = (
                            created.dwHighDateTime << 32
                        ) | created.dwLowDateTime
            finally:
                kernel32.CloseHandle(handle)
        visible = visible and executable in {"chrome.exe", "msedge.exe", "firefox.exe"}
        if native:
            area = wintypes.RECT()
            if user32.GetWindowRect(hwnd, ctypes.byref(area)):
                rect = [area.left, area.top, area.right, area.bottom]
            iconic = bool(user32.IsIconic(hwnd))
            visible = bool(
                visible
                and not iconic
                and rect
                and rect[2] > rect[0]
                and rect[3] > rect[1]
                and creation_time
                and (
                    "creation_time" not in browser
                    or creation_time == browser["creation_time"]
                )
                and ("executable" not in browser or executable == browser["executable"])
            )
        return {
            "creation_time": creation_time,
            "rect": rect,
            "iconic": iconic,
            "hwnd": hwnd,
            "pid": pid.value,
            "visible": visible,
            "executable": executable,
        }

    def close(self):
        if getattr(self, "query", None):
            self.pdh.PdhCloseQuery(self.query)
            self.query = None
