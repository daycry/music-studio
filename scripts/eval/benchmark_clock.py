"""UTC del reloj nativo PDH, conservando sus ticks de 100 ns sin float."""

import ctypes
import os
from ctypes import wintypes
from datetime import datetime, timedelta, timezone


def utc_now():
    # PDH uses the coarse Windows system clock, not the precise QPC-based clock.
    if os.name != "nt":
        return datetime.now(timezone.utc).isoformat()
    read = ctypes.windll.kernel32.GetSystemTimeAsFileTime
    read.argtypes = [ctypes.POINTER(wintypes.FILETIME)]
    read.restype = None
    value = wintypes.FILETIME()
    read(ctypes.byref(value))
    ticks = (value.dwHighDateTime << 32) | value.dwLowDateTime
    seconds, fraction = divmod(ticks - 116444736000000000, 10000000)
    date = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=seconds)
    return date.strftime("%Y-%m-%dT%H:%M:%S") + f".{fraction:07d}+00:00"


class SystemTime(ctypes.Structure):
    _fields_ = [
        (name, wintypes.WORD)
        for name in (
            "year",
            "month",
            "weekday",
            "day",
            "hour",
            "minute",
            "second",
            "millisecond",
        )
    ]


class TimeZoneInformation(ctypes.Structure):
    _fields_ = [
        ("Bias", wintypes.LONG),
        ("StandardName", wintypes.WCHAR * 32),
        ("StandardDate", SystemTime),
        ("StandardBias", wintypes.LONG),
        ("DaylightName", wintypes.WCHAR * 32),
        ("DaylightDate", SystemTime),
        ("DaylightBias", wintypes.LONG),
    ]


def timezone_snapshot():
    read = ctypes.windll.kernel32.GetTimeZoneInformation
    read.argtypes = [ctypes.POINTER(TimeZoneInformation)]
    read.restype = wintypes.DWORD
    value = TimeZoneInformation()
    state = read(ctypes.byref(value))
    if state not in {0, 1, 2}:
        raise ValueError("timezone_unavailable")
    return {
        "id": state,
        "bias_minutes": value.Bias,
        "standard_bias_minutes": value.StandardBias,
        "daylight_bias_minutes": value.DaylightBias,
        "standard_name": value.StandardName,
        "daylight_name": value.DaylightName,
        "standard_date": [
            getattr(value.StandardDate, k) for k, _ in SystemTime._fields_
        ],
        "daylight_date": [
            getattr(value.DaylightDate, k) for k, _ in SystemTime._fields_
        ],
    }


def local_filetime_to_utc(raw):
    # Only at live acquisition: Windows applies CURRENT zone/DST, not historical rules.
    if type(raw) is not int or not 0 < raw < 2**64:
        raise ValueError("filetime_conversion_failed")
    convert = ctypes.windll.kernel32.LocalFileTimeToFileTime
    convert.argtypes = [ctypes.POINTER(wintypes.FILETIME)] * 2
    convert.restype = wintypes.BOOL
    local = wintypes.FILETIME(raw & 0xFFFFFFFF, raw >> 32)
    utc = wintypes.FILETIME()
    if not convert(ctypes.byref(local), ctypes.byref(utc)):
        raise ValueError("filetime_conversion_failed")
    return (utc.dwHighDateTime << 32) | utc.dwLowDateTime


def timezone_offset_ticks(zone):
    required = {
        "id",
        "bias_minutes",
        "standard_bias_minutes",
        "daylight_bias_minutes",
        "standard_name",
        "daylight_name",
        "standard_date",
        "daylight_date",
    }
    if (
        not isinstance(zone, dict)
        or set(zone) != required
        or type(zone["id"]) is not int
        or zone["id"] not in {0, 1, 2}
        or any(
            type(zone[k]) is not int
            for k in ("bias_minutes", "standard_bias_minutes", "daylight_bias_minutes")
        )
        or any(not isinstance(zone[k], str) for k in ("standard_name", "daylight_name"))
        or any(
            not isinstance(zone[k], list)
            or len(zone[k]) != 8
            or any(type(v) is not int or not 0 <= v <= 65535 for v in zone[k])
            for k in ("standard_date", "daylight_date")
        )
    ):
        raise ValueError("filetime_timezone_invalid")
    season = "daylight" if zone["id"] == 2 else "standard"
    bias = zone["bias_minutes"]
    if zone[f"{season}_date"][1]:
        bias += zone[f"{season}_bias_minutes"]
    return -bias * 60 * 10000000
