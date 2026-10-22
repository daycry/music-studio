"""Árbol benigno fijo para custodia Linux; no ejecuta comandos recibidos."""

import datetime
import importlib
import json
import os
import signal
import socket
import struct
import sys
import types
from pathlib import Path

package = types.ModuleType("app")
package.__path__ = [str(Path(__file__).resolve().parents[2] / "app")]
sys.modules["app"] = package
protocol = importlib.import_module("app.worker.pipe_protocol")
Decoder, Session, encode = protocol.Decoder, protocol.Session, protocol.encode


def birth(pid):
    return int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19])


def main():
    mode, root, execution, epoch = sys.argv[1:5]
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    Path(root, "native-leader.json").write_text(
        json.dumps(
            {
                "pid": os.getpid(),
                "ppid": os.getppid(),
                "pgid": os.getpgrp(),
                "birth": birth(os.getpid()),
                "argv": sys.argv,
                "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            }
        )
    )
    registry = socket.socket(fileno=int(sys.argv[5])) if len(sys.argv) == 6 else None
    barrier_r, barrier_w = os.pipe()
    child = os.fork()
    if child == 0:
        Path(root, "native-grandchild.json").write_text(
            json.dumps(
                {
                    "pid": os.getpid(),
                    "ppid": os.getppid(),
                    "pgid": os.getpgrp(),
                    "birth": birth(os.getpid()),
                    "argv": sys.argv,
                    "origin": "fork",
                    "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }
            )
        )
        os.close(barrier_w)
        os.close(0)
        os.close(1)
        os.close(2)
        if registry:
            registry.close()
        os.read(barrier_r, 1)
        os.close(barrier_r)
        while True:
            signal.pause()
    os.close(barrier_r)
    member = {"pid": child, "birth": birth(child)}
    if mode == "foreign_birth":
        Path(root, "tree.json").write_text(
            json.dumps({"leader": os.getpid(), **member})
        )
    if registry:
        reported = (
            {"pid": os.getppid(), "birth": birth(os.getppid())}
            if mode == "foreign_birth"
            else member
        )
        registry.sendall(json.dumps(reported).encode())
        if registry.recv(1) != b"R":
            return
        registry.close()
    os.write(barrier_w, b"R")
    os.close(barrier_w)
    Path(root, "tree.json").write_text(json.dumps({"leader": os.getpid(), **member}))
    seq = 0

    def send(kind, payload):
        nonlocal seq
        seq += 1
        wire = encode(
            {
                "version": 1,
                "execution_id": execution,
                "epoch": epoch,
                "seq": seq,
                "kind": kind,
                "payload": payload,
            }
        )
        if kind == "ready" and mode == "flood":
            # Ready y primer bloque de flood en una escritura <= PIPE_BUF:
            # el lector observa el fallo antes de revisar su deadline.
            wire += b"x" * 256
        while wire:
            wire = wire[os.write(1, wire) :]

    if mode == "no_output":
        while True:
            signal.pause()
    send("ready", {"member": member, "births_sealed": True})
    decoder = Decoder(Session(execution, epoch, "parent"))
    requested = False
    while not requested:
        data = os.read(0, 4096)
        if not data:
            return
        for message in decoder.feed(data):
            requested |= message["kind"] == "request"
    if mode == "truncated":
        os.write(1, b"\x00\x00\x00\x10{")
        return
    if mode == "invalid":
        os.write(1, b"\x00\x00\x00\x02{}")
        return
    if mode == "nonfinite":
        body = b'{"value":NaN}'
        os.write(1, struct.pack("!I", len(body)) + body)
        return
    if mode == "seq":
        seq += 1
        send("result", {})
        return
    if mode == "eof":
        os.close(1)
        os.close(2)
        while True:
            signal.pause()
    if mode == "flood":
        while True:
            os.write(1, b"x" * 4096)
            os.write(2, b"d" * 4096)
    if mode == "fullpipe":
        while True:
            os.write(2, b"d" * 4096)
    if mode == "backpressure":
        for _ in range(20):
            send("progress", {"text": "x"})
    if mode in ("silent", "blocked", "backpressure"):
        Path(root, "blocked").write_text("ready")
        while True:
            signal.pause()
    send("result", {"ok": True})
    send("closed", {})


if __name__ == "__main__":
    main()
