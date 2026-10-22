"""Proveedor reescrito desde el contrato después del RED funcional.

Sensores persistentes exclusivamente en el hijo. El proxy conserva v1/v2;
la política v3 necesita su propia factoría y esquema explícitos.
"""

import time

from benchmark_process import OwnedProcess, WorkerFailure


class NativeProvider:
    def __init__(self, config):
        if not isinstance(config, dict) or config.keys() - {
            "browser",
            "distro",
            "gpu_name",
        }:
            raise ValueError("provider_config_invalid")
        from benchmark_observers import Observers
        from benchmark_windows import WindowsGpuMemory

        self.windows = WindowsGpuMemory(
            config.get("gpu_name", "NVIDIA GeForce RTX 5070")
        )
        self.observers = Observers(
            self.windows,
            browser=config.get("browser", {}),
            distro=config.get("distro", "Ubuntu"),
            parallel_operations=True,
        )

    def __call__(self, payload, emit):
        if payload.keys() - {"operation", "arguments"}:
            raise ValueError("provider_payload_invalid")
        operation = payload.get("operation")
        if operation not in ("sample", "nvidia", "native_probe"):
            raise ValueError("provider_operation_invalid")
        args = payload.get("arguments", {})
        if not isinstance(args, dict) or args.keys() - {
            "observation_context",
            "observation_method",
        }:
            raise ValueError("provider_arguments_invalid")
        context = args.get("observation_context")
        method = args.get("observation_method", "wddm_auto_v1")
        self.observers.observation_context = context
        self.observers.observation_method = method
        self.observers.progress_callback = lambda raw: emit(
            {"source": "observers_raw", "raw": raw}
        )
        self.windows.progress_callback = lambda raw: emit(
            {
                "source": "windows_raw",
                "raw": raw,
                "observation_context": context,
                "observation_method": method,
            }
        )
        if operation == "native_probe":
            return {
                "status": "partial_native_probe",
                "full_calibration": False,
                "windows": self.windows.sample(),
            }
        return getattr(self.observers, operation)()

    def close(self):
        self.windows.close()


class IsolatedObservers:
    """Deadline absoluto intacto; RAW parcial conservado en WorkerFailure."""

    def __init__(
        self,
        *,
        browser,
        distro="Ubuntu",
        gpu_name="NVIDIA GeForce RTX 5070",
        trusted_handler="benchmark_provider:NativeProvider",
        startup_timeout_s=5,
    ):
        self.observation_context = None
        self.observation_method = "wddm_auto_v1"
        self.last_raw = self.last_result = None
        self.worker = OwnedProcess(
            {"browser": browser, "distro": distro, "gpu_name": gpu_name},
            trusted_handler,
            startup_timeout_s=startup_timeout_s,
        )

    def _call(self, operation, deadline_ns):
        deadline_ns = (
            time.perf_counter_ns() + 2_000_000_000
            if deadline_ns is None
            else deadline_ns
        )
        self.last_raw = self.last_result = None
        request = {
            "operation": operation,
            "arguments": {
                "observation_context": self.observation_context,
                "observation_method": self.observation_method,
            },
        }
        try:
            result = self.worker.call(request, deadline_ns=deadline_ns)
        except WorkerFailure as failure:
            self.last_raw = {
                "status": "incomplete_invalid",
                "progress": failure.progress,
            }
            failure.partial_raw = self.last_raw
            raise
        self.last_result = result
        self.last_raw = result["value"]
        return self.last_raw

    def sample(self, *, deadline_ns=None):
        return self._call("sample", deadline_ns)

    def nvidia(self, *, deadline_ns=None):
        return self._call("nvidia", deadline_ns)

    def native_probe(self, *, deadline_ns=None):
        return self._call("native_probe", deadline_ns)

    def close(self):
        self.worker.close()
