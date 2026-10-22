"""Entrada Linux fija; sólo audio/archivos propios, sin SQLite ni credenciales."""

import hashlib
import json
import os
import selectors
import socket
import subprocess
import sys
import time
from pathlib import Path

# Entrada de archivo propia, no un módulo/entrypoint recibido del plan.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from audio_post.manifest import safe_path
from audio_post.pipeline import process_audio
from audio_post.private_context import PreparedContext, prepare_context
from soundfile import SoundFileError

from app.worker.contracts import PostPlan, TakeFailure, TakeSuccess, canonical_sha256
from app.worker.packages import (
    MAX_PLAN_BYTES,
    TOOL_PIN,
    create_package,
    read_file,
    stage,
    tool,
)
from app.worker.pipe_protocol import Decoder, Session, encode


def birth(pid):
    return int(Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19])


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("PROVENANCE_MISMATCH")
        result[key] = value
    return result


class FfmpegLauncher:
    def __init__(self, registry, binary):
        self.registry, self.binary = registry, binary

    def exchange(self, value, response):
        wire = json.dumps(value, separators=(",", ":")).encode()
        if len(wire) > 1024:
            raise ValueError("PROVENANCE_MISMATCH")
        self.registry.send(wire)
        if self.registry.recv(2) != response:
            raise ValueError("PROVENANCE_MISMATCH")

    def __call__(self, binary, args):
        if Path(binary) != self.binary:
            raise ValueError("PROVENANCE_MISMATCH")
        stdout_r, stdout_w = os.pipe()
        stderr_r, stderr_w = os.pipe()
        gate_r, gate_w = os.pipe()
        pid = os.fork()
        if pid == 0:
            try:
                os.close(gate_w)
                if os.read(gate_r, 1) != b"R":
                    os._exit(125)
                os.dup2(stdout_w, 1)
                os.dup2(stderr_w, 2)
                null = os.open("/dev/null", os.O_RDONLY)
                os.dup2(null, 0)
                for name in os.listdir("/proc/self/fd"):
                    fd = int(name)
                    if fd > 2:
                        try:
                            os.close(fd)
                        except OSError:
                            pass
                argv = [str(self.binary), "-nostdin", "-hide_banner", *args]
                os.execve(self.binary, argv, {"LANG": "C", "LC_ALL": "C"})
            except BaseException:  # noqa: BLE001 -- un fork fallido nunca vuelve al padre Python.
                os._exit(126)
        os.close(gate_r)
        os.close(stdout_w)
        os.close(stderr_w)
        member = {"pid": pid, "birth": birth(pid)}
        self.exchange({"kind": "register", **member}, b"R")
        os.write(gate_w, b"R")
        os.close(gate_w)
        buffers = {stdout_r: bytearray(), stderr_r: bytearray()}
        end = time.monotonic() + 300
        with selectors.DefaultSelector() as selector:
            for fd in buffers:
                os.set_blocking(fd, False)
                selector.register(fd, selectors.EVENT_READ)
            while selector.get_map():
                if time.monotonic() >= end:
                    raise ValueError("AUDIO_TRANSCODE_FAILED")
                for event, _ in selector.select(0.05):
                    chunk = os.read(event.fd, 65536)
                    if not chunk:
                        selector.unregister(event.fd)
                        os.close(event.fd)
                    else:
                        buffers[event.fd].extend(chunk)
                        if len(buffers[event.fd]) > 4194304:
                            raise ValueError("AUDIO_TRANSCODE_FAILED")
        while True:
            result = os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            if result is not None:
                break
            if time.monotonic() >= end:
                raise ValueError("AUDIO_TRANSCODE_FAILED")
            time.sleep(0.005)
        code = (
            result.si_status if result.si_code == os.CLD_EXITED else -result.si_status
        )
        self.exchange({"kind": "exited", **member, "status": code}, b"E")
        waited, status = os.waitpid(pid, 0)
        if waited != pid or os.waitstatus_to_exitcode(status) != code:
            raise ValueError("PROVENANCE_MISMATCH")
        self.exchange({"kind": "reaped", **member, "status": code}, b"W")
        return subprocess.CompletedProcess(
            [str(binary), *args],
            code,
            bytes(buffers[stdout_r]),
            bytes(buffers[stderr_r]),
        )


def main():
    (
        directory,
        root,
        execution,
        epoch,
        registry_fd,
        expected_sha,
        expected_bytes,
        context_sha256,
        context_bytes,
    ) = sys.argv[1:10]
    directory, root = Path(directory), Path(root)
    payload = read_file(directory / "post-plan.json", limit=MAX_PLAN_BYTES)
    if (
        len(payload) != int(expected_bytes)
        or hashlib.sha256(payload).hexdigest() != expected_sha
    ):
        raise ValueError("PROVENANCE_MISMATCH")
    plan = PostPlan.model_validate_json(
        json.dumps(json.loads(payload, object_pairs_hook=pairs), ensure_ascii=False)
    )
    if canonical_sha256(plan) != expected_sha:
        raise ValueError("PROVENANCE_MISMATCH")
    context_raw = read_file(
        safe_path(root, f"data/private-contexts/{context_sha256}.json"),
        limit=MAX_PLAN_BYTES,
    )
    if (
        len(payload) + len(context_raw) > MAX_PLAN_BYTES
        or len(context_raw) != int(context_bytes)
        or hashlib.sha256(context_raw).hexdigest() != context_sha256
    ):
        raise ValueError("PROVENANCE_MISMATCH")
    context = json.loads(context_raw, object_pairs_hook=pairs)
    validated, receipt_sha = prepare_context(context)
    if (
        validated != context_raw
        or receipt_sha != context_sha256
        or set(context["takes"]) != {entry.authority.take_id for entry in plan.takes}
    ):
        raise ValueError("PROVENANCE_MISMATCH")
    prepared_context = PreparedContext(
        value=context, payload=validated, digest=receipt_sha
    )
    pin = json.loads(read_file(TOOL_PIN, limit=65536))
    binary = TOOL_PIN.parent.parent / pin["dest"] / "bin/ffmpeg"
    tool(binary, plan)
    registry = socket.socket(fileno=int(registry_fd))
    registry.settimeout(5)
    launcher = FfmpegLauncher(registry, binary)
    outgoing = Session(execution, epoch, "child")
    seq = 0

    def send(kind, value):
        nonlocal seq
        seq += 1
        message = {
            "version": 1,
            "execution_id": execution,
            "epoch": epoch,
            "seq": seq,
            "kind": kind,
            "payload": value,
        }
        wire = encode(message)
        outgoing.accept(message, len(wire))
        while wire:
            wire = wire[os.write(1, wire) :]

    send(
        "ready",
        {
            "member": {"pid": os.getpid(), "birth": birth(os.getpid())},
            "births_sealed": False,
        },
    )
    decoder = Decoder(Session(execution, epoch, "parent"))
    requested = False
    while not requested:
        data = os.read(0, 4096)
        if not data:
            raise ValueError("CANCELLED")
        for message in decoder.feed(data):
            if message["kind"] != "request" or message["payload"] != {}:
                raise ValueError("CANCELLED")
            requested = True
    successes = 0
    for entry in plan.takes:
        destination = stage(root, execution, entry)
        destination.parent.mkdir(parents=True, exist_ok=True)
        source = safe_path(root, entry.copied_source.path)
        try:
            data = read_file(source)
            if (
                len(data) != entry.copied_source.bytes
                or hashlib.sha256(data).hexdigest() != entry.copied_source.sha256
            ):
                raise ValueError("PROVENANCE_MISMATCH")
            processed = process_audio(
                source,
                destination,
                expected_duration_s=entry.source.duration_s,
                ffmpeg=binary,
                root=root,
                launch=launcher,
            )
            package = create_package(
                plan,
                entry,
                destination,
                processed,
                pin,
                context,
                data_root=root / "data",
                prepared_context=prepared_context,
            )
            result = TakeSuccess(
                status="success",
                take_id=entry.authority.take_id,
                output_index=entry.authority.output_index,
                package=package,
                duration_s=entry.source.duration_s,
                integrated_lufs=processed["post"]["lufs_out"],
                true_peak_dbtp=processed["post"]["true_peak_dbtp"],
            )
            successes += 1
        except (ValueError, SoundFileError) as error:
            code = str(error)
            codes = {
                "UNSAFE_PATH",
                "AUDIO_TRANSCODE_FAILED",
                "AUDIO_MEASUREMENT_FAILED",
                "AUDIO_TARGET_UNREACHABLE",
                "AUDIO_INVALID",
                "PROVENANCE_MISSING",
                "PROVENANCE_MISMATCH",
            }
            if code not in codes:
                code = "AUDIO_INVALID"
            result = TakeFailure(
                status="failure",
                take_id=entry.authority.take_id,
                output_index=entry.authority.output_index,
                code=code,
            )
        send("take_result", result.model_dump(mode="json"))
    launcher.exchange({"kind": "seal"}, b"S")
    send("result", {"takes": len(plan.takes), "successes": successes})
    send("closed", {})
    registry.close()


if __name__ == "__main__":
    main()
