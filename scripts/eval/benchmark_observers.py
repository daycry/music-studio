"""Sensores agregados y separados; datos ausentes permanecen desconocidos."""

import csv
import io
import math
import re
import statistics
import subprocess
import time
from itertools import pairwise

from benchmark_clock import utc_now


def map_5070(adapters, instances, nvidia_name):
    candidates = [
        a
        for a in adapters
        if a.get("vendor_id") == 0x10DE
        and a.get("description") == "NVIDIA GeForce RTX 5070"
        and nvidia_name == a["description"]
    ]
    if len(candidates) != 1:
        raise ValueError("gpu_mapping_unresolved")
    adapter = candidates[0]
    matches = []
    for instance in instances:
        match = re.fullmatch(
            r"luid_0x([0-9a-fA-F]{8})_0x([0-9a-fA-F]{8})_phys_[0-9]+", instance
        )
        if match and (int(match[1], 16), int(match[2], 16)) == (
            adapter["luid_high"] & 0xFFFFFFFF,
            adapter["luid_low"],
        ):
            matches.append(instance)
    if len(matches) != 1:
        raise ValueError("gpu_mapping_unresolved")
    return matches[0]


def shared_assessment(baseline, samples, *, breaks=None):
    if (
        len(baseline) != 10
        or len(samples) < 2
        or any(
            type(v) not in {float, int} or not math.isfinite(v) or v < 0
            for v in baseline + samples
        )
    ):
        return {
            "observed": None,
            "baseline_mb": None,
            "tolerance_mb": None,
            "peak_mb": None,
        }
    level = statistics.mean(baseline)
    tolerance = max(32, 3 * statistics.pstdev(baseline))
    if breaks is None:
        breaks = [False] * len(samples)
    if len(breaks) != len(samples) or any(type(v) is not bool for v in breaks):
        raise ValueError("shared_adjacency_invalid")
    sustained = any(
        not breaks[index] and a > level + tolerance and b > level + tolerance
        for index, (a, b) in enumerate(pairwise(samples), 1)
    )
    return {
        "observed": sustained,
        "baseline_mb": level,
        "tolerance_mb": tolerance,
        "peak_mb": max(samples),
    }


def counter_paths(object_name, counter_name, instance):
    return f"\\{object_name}({instance})\\{counter_name}"


def parse_nvidia(text):
    rows = list(csv.reader(io.StringIO(text.strip()), skipinitialspace=True))
    if len(rows) != 1 or len(rows[0]) not in {5, 6}:
        raise ValueError("gpu_inventory_ambiguous")
    uuid, name, total, used, free = rows[0][:5]
    if any(not math.isfinite(float(v)) or float(v) < 0 for v in (total, used, free)):
        raise ValueError("gpu_sensor_invalid")
    return {
        "driver_version": rows[0][5] if len(rows[0]) == 6 else None,
        "uuid": uuid,
        "name": name,
        "total_mb": float(total),
        "used_mb": float(used),
        "free_mb": float(free),
    }


def parse_meminfo(text):
    data = {}
    for line in text.splitlines():
        match = re.fullmatch(r"(MemAvailable|SwapTotal|SwapFree):\s+([0-9]+) kB", line)
        if match:
            data[match[1]] = int(match[2]) / 1024
    return {
        "mem_available_mb": data.get("MemAvailable"),
        "swap_total_mb": data.get("SwapTotal"),
        "swap_used_mb": data["SwapTotal"] - data["SwapFree"]
        if {"SwapTotal", "SwapFree"} <= data.keys()
        else None,
    }


def command_text(args, *, execute=subprocess.run):
    # El proveedor v3 tiene un episodio absoluto de 2 s. Una consulta hija no
    # puede conservar el timeout genérico de 15 s y arrastrar al observador a
    # un WorkerDeadline cuando WSL/WDDM se atasca.
    result = execute(args, capture_output=True, text=True, timeout=1.25, check=False)
    if result.returncode:
        raise ValueError("sensor_unavailable")
    return result.stdout


class Observers:
    def __init__(
        self,
        windows,
        *,
        browser,
        distro="Ubuntu",
        execute=subprocess.run,
        progress_callback=None,
        parallel_operations=False,
    ):
        self.progress_callback = progress_callback
        self.parallel_operations = parallel_operations
        self.windows, self.browser, self.distro, self.execute = (
            windows,
            browser,
            distro,
            execute,
        )

    def nvidia(self):
        return parse_nvidia(
            command_text(
                [
                    "nvidia-smi",
                    "--query-gpu=uuid,name,memory.total,memory.used,memory.free,driver_version",
                    "--format=csv,noheader,nounits",
                ],
                execute=self.execute,
            )
        )

    def _operations(self):
        return (
            ("nvml", self.nvidia),
            ("windows", self.windows.sample),
            (
                "wsl",
                lambda: parse_meminfo(
                    command_text(
                        ["wsl", "-d", self.distro, "-e", "cat", "/proc/meminfo"],
                        execute=self.execute,
                    )
                ),
            ),
            ("browser", lambda: self.windows.browser_heartbeat(self.browser)),
        )

    def sample(self):
        if self.parallel_operations:
            return self._sample_parallel()
        return self._sample_sequential()

    def _sample_sequential(self):
        from benchmark_observation import acquisition_context

        context = getattr(self, "observation_context", None)
        acquired = (
            acquisition_context(
                context, getattr(self, "observation_method", "wddm_auto_v1")
            )
            if context is not None
            else None
        )
        value = {
            "timestamp": utc_now(),
            "monotonic_ns": time.perf_counter_ns(),
            "nvml": None,
            "windows": None,
            "wsl": None,
            "browser": None,
            "errors": [],
            "operations": {},
        }
        if acquired is not None:
            value["acquisition_context"] = acquired
        callback = getattr(self, "progress_callback", None)
        if callback is not None:
            callback(value)
        for name, operation in self._operations():
            started = {
                "started_utc": utc_now(),
                "started_monotonic_ns": time.perf_counter_ns(),
            }
            # La muestra se ancla al inicio de la primera consulta real. La
            # preparación del contenedor y el callback inicial pueden tardar
            # más de la tolerancia del validador, pero no forman parte de la
            # adquisición de sensores.
            if not value["operations"]:
                value["timestamp"] = started["started_utc"]
                value["monotonic_ns"] = started["started_monotonic_ns"]
            try:
                value[name] = operation()
            except (
                OSError,
                ValueError,
                RuntimeError,
                subprocess.SubprocessError,
            ) as error:
                partial = getattr(error, "partial_sample", None)
                if partial is not None:
                    value[name] = partial
                value["errors"].append(f"{name}_unavailable")
            finally:
                value["operations"][name] = {
                    **started,
                    "finished_utc": utc_now(),
                    "finished_monotonic_ns": time.perf_counter_ns(),
                }
            if callback is not None:
                callback(value)
        return value

    def _sample_parallel(self):
        """Acquire independent sensors concurrently within one sample window.

        The result and callback order stay canonical even though the sensor
        calls overlap. This shortens the absolute deadline path when WSL is
        slow, while preserving the sequential contract used by CPU fixtures.
        """
        from concurrent.futures import ThreadPoolExecutor

        from benchmark_observation import acquisition_context

        context = getattr(self, "observation_context", None)
        acquired = (
            acquisition_context(
                context, getattr(self, "observation_method", "wddm_auto_v1")
            )
            if context is not None
            else None
        )
        value = {
            "timestamp": utc_now(),
            "monotonic_ns": time.perf_counter_ns(),
            "nvml": None,
            "windows": None,
            "wsl": None,
            "browser": None,
            "errors": [],
            "operations": {},
        }
        if acquired is not None:
            value["acquisition_context"] = acquired
        callback = getattr(self, "progress_callback", None)
        if callback is not None:
            callback(value)

        operations = self._operations()
        started = [
            {
                "started_utc": utc_now(),
                "started_monotonic_ns": time.perf_counter_ns(),
            }
            for _name, _operation in operations
        ]
        value["timestamp"] = started[0]["started_utc"]
        value["monotonic_ns"] = started[0]["started_monotonic_ns"]

        def acquire(item):
            name, operation, bracket = item
            try:
                result = operation()
            except (
                OSError,
                ValueError,
                RuntimeError,
                subprocess.SubprocessError,
            ) as error:
                result = getattr(error, "partial_sample", None)
                error_name = f"{name}_unavailable"
            else:
                error_name = None
            return (
                name,
                result,
                error_name,
                {
                    **bracket,
                    "finished_utc": utc_now(),
                    "finished_monotonic_ns": time.perf_counter_ns(),
                },
            )

        items = [
            (name, operation, bracket)
            for (name, operation), bracket in zip(operations, started)
        ]
        with ThreadPoolExecutor(max_workers=len(items)) as executor:
            futures = [executor.submit(acquire, item) for item in items]
            for future in futures:
                name, result, error_name, bracket = future.result()
                if result is not None:
                    value[name] = result
                if error_name is not None:
                    value["errors"].append(error_name)
                value["operations"][name] = bracket
                if callback is not None:
                    callback(value)
        return value
