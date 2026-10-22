"""Fixture benigna Windows; sin imports del server ni acceso a datos del estudio."""

import ctypes
import json
import os
import struct
import subprocess
import sys
import types
from ctypes import wintypes as W
from pathlib import Path

package = types.ModuleType("app")
package.__path__ = [str(Path(__file__).resolve().parents[2] / "app")]
sys.modules["app"] = package
from app.worker.pipe_protocol import Decoder, Session


def birth(handle):
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.GetProcessTimes.argtypes = [W.HANDLE] + [ctypes.POINTER(W.FILETIME)] * 4
    values = [W.FILETIME() for _ in range(4)]
    if not k.GetProcessTimes(handle, *(ctypes.byref(v) for v in values)):
        raise ctypes.WinError(ctypes.get_last_error())
    return (values[0].dwHighDateTime << 32) | values[0].dwLowDateTime


def send(kind, payload, seq, fragmented=False):
    value = {
        "version": 1,
        "execution_id": sys.argv[3],
        "epoch": sys.argv[4],
        "seq": seq,
        "kind": kind,
        "payload": payload,
    }
    body = json.dumps(value, separators=(",", ":")).encode()
    wire = struct.pack("!I", len(body)) + body
    for pos in range(0, len(wire), 3 if fragmented else len(wire)):
        os.write(1, wire[pos : pos + (3 if fragmented else len(wire))])


def main():
    mode, root = sys.argv[1:3]
    root = Path(root)
    # Sólo canales propios; stdin bloquea sin consumir CPU y sirve de barrera.
    if mode in ("grandchild", "witness"):
        (root / f"{mode}-born.json").write_text(
            json.dumps({"pid": os.getpid(), "birth": birth(-1)})
        )
        os.read(0, 1)
        return
    (root / "leader-born.json").write_text(
        json.dumps(
            {"pid": os.getpid(), "birth": birth(-1), "environment": sorted(os.environ)}
        )
    )
    # Nieto inmediato al primer código Python; Popen conserva su handle real.
    child = subprocess.Popen(
        [sys.executable, __file__, "grandchild", str(root)],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=dict(os.environ),
        cwd=root,
        creationflags=0x8 | 0x08000000,
    )
    (root / "tree.json").write_text(
        json.dumps({"pid": child.pid, "birth": birth(int(child._handle))})
    )
    if mode == "no_output":
        ctypes.WinDLL("kernel32").Sleep(0xFFFFFFFF)
    send(
        "ready",
        {
            "member": {"pid": child.pid, "birth": birth(int(child._handle))},
            "births_sealed": True,
        },
        1,
        True,
    )
    # Padre reconoce el nacimiento antes de autorizar más salida o terminación.
    decoder = Decoder(Session(sys.argv[3], sys.argv[4], "parent"))
    received = False
    while not received:
        data = os.read(0, 4096)
        if not data:
            return
        for message in decoder.feed(data):
            received |= message["kind"] == "request"
    if mode == "truncated":
        os.write(1, b"\x00\x00\x00\x10{")
        return
    if mode == "invalid":
        os.write(1, b"\x00\x00\x00\x02{}")
        return
    if mode == "eof":
        return
    if mode == "flood":
        while True:
            os.write(2, b"d" * 4096)
            os.write(1, b"x" * 4096)
    if mode == "fullpipe":
        while True:
            os.write(2, b"d" * 4096)
    if mode == "backpressure":
        for seq in range(2, 20):
            send("progress", {"text": "x" * 8192}, seq)
        ctypes.WinDLL("kernel32").Sleep(0xFFFFFFFF)
    if mode == "silent" or mode == "blocked":
        (root / "work-blocked.json").write_text("{}")
        # No lee stdin otra vez: permite un writer verdaderamente bloqueado.
        ctypes.WinDLL("kernel32").Sleep(0xFFFFFFFF)
    send("result", {"ok": True}, 2, True)
    send("closed", {}, 3, True)
    child.terminate()
    child.wait(timeout=5)


if __name__ == "__main__":
    main()
