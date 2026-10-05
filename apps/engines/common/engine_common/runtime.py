"""Primitivas del proceso padre: nunca importan torch ni inicializan CUDA."""

import json
import os
import queue
import subprocess
import sys
import threading
import time


class EngineError(Exception):
    def __init__(self, code, message=None, retryable=False):
        super().__init__(code)
        self.code = code
        self.message = message or code
        self.retryable = retryable


class CancelToken:
    def __init__(self):
        self.flag = threading.Event()

    def cancel(self):
        self.flag.set()

    @property
    def cancelled(self):
        return self.flag.is_set()

    def check(self):
        if self.cancelled:
            raise EngineError("CANCELLED")

    def wait(self, seconds):
        if self.flag.wait(seconds):
            self.check()


class VramGuard:
    def __init__(self, total_mb, free_mb, margin_mb=512):
        self.total_mb = total_mb
        self.cap_mb = max(0, free_mb - margin_mb)
        self.peak_mb = 0
        self.spilled = False

    def observe(self, peak_mb, rtf=None, reference_rtf=None):
        self.peak_mb = max(self.peak_mb, peak_mb)
        self.spilled = (
            self.spilled
            or (self.cap_mb > 0 and self.peak_mb >= self.cap_mb * 0.95)
            or bool(reference_rtf and rtf and rtf > reference_rtf * 1.5)
        )
        if self.peak_mb > self.cap_mb:
            self.spilled = True
            raise EngineError("VRAM_EXCEEDED")


class NvmlGpu:
    def snapshot(self):
        import pynvml

        try:
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            return memory.total / 1024**2, memory.free / 1024**2
        except pynvml.NVMLError as error:
            raise EngineError("INTERNAL", "No se puede consultar NVML") from error
        finally:
            try:
                pynvml.nvmlShutdown()
            except pynvml.NVMLError:
                pass


class CpuGpu:
    def snapshot(self):
        return 0, 0


class ProcessSupervisor:
    def __init__(self, adapter_factory="engine_mock:MockAdapter", adapter_options=None):
        self.factory = adapter_factory
        self.options = adapter_options or {}
        self.process = None
        self.messages = queue.Queue()
        self.writer_lock = threading.Lock()
        self.loaded = None
        self.load_s = 0

    @property
    def pid(self):
        return self.process.pid if self.process else None

    @property
    def alive(self):
        return self.process is not None and self.process.poll() is None

    def _read(self, process, messages):
        for line in process.stdout:
            try:
                messages.put(json.loads(line))
            except ValueError:
                messages.put(
                    {
                        "kind": "error",
                        "code": "INTERNAL",
                        "message": "Respuesta del proceso inválida",
                    }
                )
        messages.put(
            {"kind": "error", "code": "INTERNAL", "message": "Proceso terminado"}
        )

    def send(self, command):
        with self.writer_lock:
            if not self.alive:
                raise EngineError("INTERNAL", "Proceso no disponible")
            self.process.stdin.write(json.dumps(command) + "\n")
            self.process.stdin.flush()

    def receive(self, timeout):
        try:
            return self.messages.get(timeout=timeout)
        except queue.Empty:
            raise EngineError("TIMEOUT") from None

    def load(self, model_id, mode, cap_mb, total_mb, timeout=60):
        deadline = time.monotonic() + timeout
        if self.alive and self.loaded == (model_id, mode):
            return
        self.unload()
        started = time.monotonic()
        self.messages = queue.Queue()
        env = {**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
        self.process = subprocess.Popen(
            [sys.executable, "-m", "engine_common.worker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            env=env,
        )
        threading.Thread(
            target=self._read, args=(self.process, self.messages), daemon=True
        ).start()
        try:
            self.send(
                {
                    "command": "load",
                    "factory": self.factory,
                    "options": self.options,
                    "model_id": model_id,
                    "mode": mode,
                    "cap_mb": cap_mb,
                    "total_mb": total_mb,
                }
            )
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EngineError("TIMEOUT")
            message = self.receive(remaining)
            if message["kind"] != "loaded":
                raise EngineError(
                    message.get("code", "INTERNAL"), message.get("message")
                )
            self.loaded = (model_id, mode)
            self.load_s = time.monotonic() - started
        except Exception:
            self.unload()
            raise

    def unload(self):
        if self.process:
            if self.alive:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=5)
            self.process.stdin.close()
            self.process.stdout.close()
        self.process = None
        self.loaded = None
