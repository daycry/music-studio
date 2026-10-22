import array
import json
import os
import socket
import struct
import sys

import pytest
from studio_storage_guard import protocol
from studio_storage_guard.preflight import StorageGuardError

REQUEST = {"version": 1, "role": "server", "challenge": "ab" * 32}


@pytest.mark.parametrize(
    "change",
    [
        {"version": True},
        {"version": 2},
        {"role": "library"},
        {"challenge": "AB" * 32},
        {"challenge": "ab" * 31},
        {"path": "/data"},
    ],
)
def test_closed_request_rejects_noncanonical_values(change):
    value = REQUEST | change
    assert protocol.decode(protocol.encode(REQUEST)) == REQUEST
    with pytest.raises(StorageGuardError):
        protocol.decode(json.dumps(value).encode())


@pytest.mark.parametrize(
    "data",
    [
        b"{",
        b"[]",
        b"null",
        b"\xff",
        b" " * 4097,
        b'{"version":2,"version":1,"role":"server","challenge":"' + b"ab" * 32 + b'"}',
        b'{"version":1,"role":[],"challenge":"' + b"ab" * 32 + b'"}',
    ],
)
def test_malformed_is_closed_error(data):
    with pytest.raises(StorageGuardError):
        protocol.decode(data)


RESPONSE = REQUEST | {
    "uuid": "bda4915f-04df-4e3c-94d6-39817d60185e",
    "device": 23,
    "inode": 1,
}


def test_response_has_canonical_object_identity():
    assert protocol.decode(protocol.encode(RESPONSE), response=True) == RESPONSE


@pytest.mark.parametrize(
    "change",
    [
        {"device": True},
        {"inode": 0},
        {"device": -1},
        {"uuid": "BDa4915f-04df-4e3c-94d6-39817d60185e"},
        {"ok": True},
    ],
)
def test_response_rejects_wrong_identity(change):
    with pytest.raises(StorageGuardError):
        protocol.decode(json.dumps(RESPONSE | change).encode(), response=True)


class Peer:
    def __init__(self, uid, gid, pid=0):
        self.value = struct.pack("3i", pid, uid, gid)

    def getsockopt(self, *args):
        return self.value


@pytest.mark.parametrize("uid,gid", [(10001, 10001), (19000, 0), (0, 10001)])
def test_peer_uid_and_gid_are_required(uid, gid, monkeypatch):
    monkeypatch.setattr(socket, "SO_PEERCRED", 17, raising=False)
    assert protocol.authenticate(Peer(19000, 10001, 0), 19000)[1:] == (19000, 10001)
    with pytest.raises(StorageGuardError):
        protocol.authenticate(Peer(uid, gid), 19000)


class Frame:
    def __init__(self, ancillary, flags=0, data=None):
        self.frame = (
            protocol.encode(REQUEST) if data is None else data,
            ancillary,
            flags,
            None,
        )

    def recvmsg(self, *args):
        return self.frame


@pytest.mark.parametrize(
    "case", ["extra", "none", "truncated", "control-truncated", "unknown", "malformed"]
)
def test_invalid_frame_closes_every_received_fd(case, monkeypatch):
    monkeypatch.setattr(socket, "CMSG_SPACE", lambda n: n + 16, raising=False)
    monkeypatch.setattr(socket, "MSG_CMSG_CLOEXEC", 0x40000000, raising=False)
    monkeypatch.setattr(socket, "SCM_RIGHTS", 1, raising=False)
    monkeypatch.setattr(socket, "MSG_TRUNC", 32, raising=False)
    monkeypatch.setattr(socket, "MSG_CTRUNC", 8, raising=False)
    descriptors = [
        os.open(__file__, os.O_RDONLY) for _ in range(2 if case == "extra" else 1)
    ]
    try:
        rights = [
            (
                socket.SOL_SOCKET,
                socket.SCM_RIGHTS,
                array.array("i", descriptors).tobytes(),
            )
        ]
        flags, data = 0, None
        if case == "none":
            rights = []
        elif case == "truncated":
            flags = socket.MSG_TRUNC
        elif case == "control-truncated":
            flags = socket.MSG_CTRUNC
        elif case == "unknown":
            rights.append((socket.SOL_SOCKET, 999, b""))
        elif case == "malformed":
            data = b"{"
        with pytest.raises(StorageGuardError):
            protocol.receive(Frame(rights, flags, data))
        if case != "none":
            for fd in descriptors:
                with pytest.raises(OSError):
                    os.fstat(fd)
    finally:
        for fd in descriptors:
            try:
                os.close(fd)
            except OSError:
                pass


@pytest.mark.skipif(sys.platform != "linux", reason="native AF_UNIX and SCM_RIGHTS")
def test_native_one_fd_cloexec_and_tail_rejection():
    first, second = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    original = os.open("/scratch/data", os.O_RDONLY | os.O_DIRECTORY)
    try:
        first.sendmsg(
            [protocol.encode(REQUEST)],
            [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [original]))],
        )
        first.shutdown(socket.SHUT_WR)
        value, fd = protocol.receive(second)
        try:
            assert value == REQUEST
            assert not os.get_inheritable(fd)
            assert os.fstat(fd).st_ino == os.fstat(original).st_ino
        finally:
            os.close(fd)
    finally:
        os.close(original)
        first.close()
        second.close()


@pytest.mark.parametrize("method", ["recvmsg", "sendmsg", "sendall", "connect"])
def test_absolute_deadline_is_installed_before_each_operation(method, monkeypatch):
    class Connection:
        timeout = None

        def settimeout(self, value):
            self.timeout = value

        def action(self, *args):
            assert self.timeout == 1.0
            return "called"

        recvmsg = sendmsg = sendall = connect = action

    connection = Connection()
    monkeypatch.setattr(protocol.time, "monotonic", lambda: 10.0)
    wrapper = protocol.Deadline(connection)
    monkeypatch.setattr(protocol.time, "monotonic", lambda: 11.0)
    assert getattr(wrapper, method)() == "called"
    monkeypatch.setattr(protocol.time, "monotonic", lambda: 12.0)
    with pytest.raises(StorageGuardError):
        getattr(wrapper, method)()


@pytest.mark.skipif(
    sys.platform != "linux", reason="native truncation and descriptor ownership"
)
@pytest.mark.parametrize(
    "variant",
    [
        "extra",
        "control-truncated",
        "data-truncated",
        "tail-fd",
        "response-fd",
        "malformed",
        "disconnect",
    ],
)
def test_native_invalid_frame_has_no_descriptor_leak(variant):
    first, second = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    first.settimeout(1)
    second.settimeout(1)
    original = os.open("/scratch/data", os.O_RDONLY | os.O_DIRECTORY)
    before = len(os.listdir("/proc/self/fd"))
    try:
        count = (
            100 if variant == "control-truncated" else 2 if variant == "extra" else 1
        )
        rights = [
            (socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [original] * count))
        ]
        data = (
            b"x" * 4097
            if variant == "data-truncated"
            else b"{"
            if variant == "malformed"
            else protocol.encode(RESPONSE if variant == "response-fd" else REQUEST)
        )
        if variant != "disconnect":
            first.sendmsg([data], rights)
            if variant == "tail-fd":
                first.sendmsg([b"x"], rights)
        first.shutdown(socket.SHUT_WR)
        with pytest.raises(StorageGuardError):
            protocol.receive(second, response=variant == "response-fd")
        assert len(os.listdir("/proc/self/fd")) == before
    finally:
        os.close(original)
        first.close()
        second.close()
