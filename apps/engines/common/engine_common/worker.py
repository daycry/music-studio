"""Proceso hijo. IPC JSON, sin deserialización pickle."""

import importlib
import json
import sys
import threading
from pathlib import Path

from .runtime import CancelToken, EngineError

writer_lock = threading.Lock()


def send(message):
    with writer_lock:
        sys.stdout.write(json.dumps(message) + "\n")
        sys.stdout.flush()


def run(adapter, request, output_dir, token):
    try:
        result = adapter.generate(
            request,
            Path(output_dir),
            lambda event: send({"kind": "event", "type": event[0], "data": event[1]}),
            token,
        )
        token.check()
        send({"kind": "result", **result})
    except EngineError as error:
        send(
            {
                "kind": "error",
                "code": error.code,
                "message": error.message,
                "retryable": error.retryable,
            }
        )
    except Exception:  # noqa: BLE001 - frontera del adapter: error interno sin detalles privados
        send(
            {
                "kind": "error",
                "code": "INTERNAL",
                "message": "Fallo interno del adapter",
                "retryable": False,
            }
        )


def main():
    adapter = None
    token = None
    worker = None
    for line in sys.stdin:
        command = json.loads(line)
        if command["command"] == "load":
            try:
                module, name = command["factory"].split(":")
                adapter = getattr(importlib.import_module(module), name)(
                    **command["options"]
                )
                adapter.load(
                    command["model_id"],
                    command["mode"],
                    command["cap_mb"],
                    command["total_mb"],
                )
                send({"kind": "loaded"})
            except EngineError as error:
                send({"kind": "error", "code": error.code, "message": error.message})
            except Exception:  # noqa: BLE001 - frontera del adapter: error interno sin detalles privados
                send(
                    {
                        "kind": "error",
                        "code": "INTERNAL",
                        "message": "No se pudo cargar el modelo",
                    }
                )
        elif command["command"] == "generate":
            if worker and worker.is_alive():
                send({"kind": "error", "code": "BUSY", "message": "Proceso ocupado"})
                continue
            token = CancelToken()
            worker = threading.Thread(
                target=run,
                args=(adapter, command["request"], command["output_dir"], token),
                daemon=True,
            )
            worker.start()
        elif command["command"] == "cancel" and token:
            token.cancel()


if __name__ == "__main__":
    main()
