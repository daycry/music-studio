"""ABI acotada del guardián de almacenamiento."""

import json
import os
import re
import socket
import struct
import time
from uuid import UUID

from .preflight import StorageGuardError


class Deadline:
    def __init__(self, connection):
        self.connection = connection
        self.end = time.monotonic() + 2.0

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def recvmsg(self, *args):
        self._remaining()
        return self.connection.recvmsg(*args)

    def sendall(self, *args):
        self._remaining()
        return self.connection.sendall(*args)

    def sendmsg(self, *args):
        self._remaining()
        return self.connection.sendmsg(*args)

    def connect(self, *args):
        self._remaining()
        return self.connection.connect(*args)

    def _remaining(self):
        remaining = self.end - time.monotonic()
        if remaining <= 0:
            raise StorageGuardError()
        self.connection.settimeout(remaining)


def decode(data, *, response=False):
    try:
        if type(data) is not bytes or not 0 < len(data) <= 4096:
            raise ValueError()

        def unique(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError()
                result[key] = value
            return result

        value = json.loads(data.decode("ascii"), object_pairs_hook=unique)
        fields = {"version", "role", "challenge"}
        if response:
            fields |= {"uuid", "device", "inode"}
        valid = type(value) is dict and set(value) == fields
        if response and valid:
            valid = (
                type(value["uuid"]) is str
                and str(UUID(value["uuid"])) == value["uuid"]
                and type(value["device"]) is int
                and value["device"] >= 0
                and type(value["inode"]) is int
                and value["inode"] > 0
            )
    except (ValueError, TypeError, UnicodeError):
        raise StorageGuardError() from None
    if (
        not valid
        or type(value["version"]) is not int
        or value["version"] != 1
        or type(value["role"]) is not str
        or value["role"] not in ("server", "raw")
        or type(value["challenge"]) is not str
        or re.fullmatch("[0-9a-f]{64}", value["challenge"]) is None
    ):
        raise StorageGuardError()
    return value


def encode(message, *, response=False):
    return json.dumps(message, sort_keys=True, separators=(",", ":")).encode("ascii")


def authenticate(connection, uid):
    try:
        value = struct.unpack(
            "3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
        )
        if value[1:] != (uid, 10001):
            raise StorageGuardError()
        return value
    except (OSError, ValueError, struct.error, AttributeError):
        raise StorageGuardError() from None


def receive(connection, *, response=False):
    import array

    fds = []

    def collect(ancillary):
        valid = True
        for level, kind, raw in ancillary:
            if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
                values = array.array("i")
                complete = len(raw) - len(raw) % values.itemsize
                values.frombytes(raw[:complete])
                fds.extend(values)
                valid &= complete == len(raw)
            else:
                valid = False
        return valid

    try:
        data, ancillary, flags, _ = connection.recvmsg(
            4096, socket.CMSG_SPACE(256), socket.MSG_CMSG_CLOEXEC
        )
        valid = collect(ancillary)
        if (
            not valid
            or flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC)
            or len(fds) != (0 if response else 1)
            or len(ancillary) != (0 if response else 1)
        ):
            raise StorageGuardError()
        value = decode(data, response=response)
        tail, controls, flags, _ = connection.recvmsg(
            1, socket.CMSG_SPACE(256), socket.MSG_CMSG_CLOEXEC
        )
        collect(controls)
        if tail or controls or flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
            raise StorageGuardError()
        return value, (None if response else fds.pop())
    except (OSError, ValueError, TypeError, AttributeError):
        raise StorageGuardError() from None
    finally:
        for fd in fds:
            os.close(fd)
