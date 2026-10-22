"""CPU syscall models; these tests do not certify a native ext4 mount."""

import importlib
import stat
from types import SimpleNamespace
from uuid import UUID

import pytest

UUID_TEXT = "12345678-1234-4234-8234-123456789abc"


def module():
    try:
        return importlib.import_module("studio_storage_guard.provision")
    except ModuleNotFoundError:
        # Behavioural RED: absent provisioner accepts invalid inputs and creates nothing.
        return SimpleNamespace(provision_domains=lambda *args, **kwargs: {})


def test_non_linux_cannot_authorize_provision(monkeypatch):
    value = module()
    if hasattr(value, "sys"):
        monkeypatch.setattr(value.sys, "platform", "win32")
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)


class Tree:
    """Deterministic POSIX model with retained descriptors and mutation hooks."""

    def __init__(self, lost_found=False):
        self.nodes = {
            "/": self.node(1, mode=0o755),
            "/studio-data": self.node(2, mode=0o755),
        }
        if lost_found:
            self.nodes["/studio-data/lost+found"] = self.node(3)
        self.fds = {}
        self.next_fd = 10
        self.events = []
        self.hook = lambda event: None
        self.mount_info = "7 1 8:1 / /studio-data rw - ext4 /dev/own rw\n"
        self.info = SimpleNamespace(
            device=12,
            inode=2,
            mount_id=7,
            fs_uuid=UUID(UUID_TEXT),
            fs_type="ext4",
            mount_root="/",
            writable=True,
        )

    @staticmethod
    def node(inode, uid=0, gid=0, mode=0o700):
        return SimpleNamespace(
            st_dev=12,
            st_ino=inode,
            st_uid=uid,
            st_gid=gid,
            st_mode=stat.S_IFDIR | mode,
            st_nlink=2,
            attrs=[],
        )

    def event(self, name, *values):
        event = (name, *values)
        self.events.append(event)
        self.hook(event)

    def path(self, name, dir_fd=None):
        return name if dir_fd is None else self.fds[dir_fd][0] + "/" + name

    def open(self, name, flags, *, dir_fd=None):
        path = self.path(name, dir_fd)
        self.event("open", path, flags)
        node = self.nodes[path]
        if not stat.S_ISDIR(node.st_mode):
            raise OSError("not a directory")
        fd = self.next_fd
        self.next_fd += 1
        self.fds[fd] = (path, node)
        return fd

    def close(self, fd):
        self.event("close", fd)
        del self.fds[fd]

    def fstat(self, fd):
        return self.fds[fd][1]

    def listdir(self, fd):
        prefix = self.fds[fd][0] + "/"
        return [
            p[len(prefix) :]
            for p in self.nodes
            if p.startswith(prefix) and "/" not in p[len(prefix) :]
        ]

    def mkdir(self, name, mode, *, dir_fd):
        path = self.path(name, dir_fd)
        self.event("mkdir", path, mode)
        if path in self.nodes:
            raise FileExistsError(path)
        self.nodes[path] = self.node(100 + len(self.nodes), mode=mode)

    def fchmod(self, fd, mode):
        self.event("chmod", self.fds[fd][0], mode)
        self.fstat(fd).st_mode = stat.S_IFDIR | mode

    def fchown(self, fd, uid, gid):
        self.event("chown", self.fds[fd][0], uid, gid)
        self.fstat(fd).st_uid, self.fstat(fd).st_gid = uid, gid

    def fsync(self, fd):
        self.event("fsync", self.fds[fd][0])

    def backend(self):
        tree = self

        class Backend:
            def open_root(self, path):
                return tree.open(path, 0)

            def inspect(self, fd):
                node = tree.fstat(fd)
                return SimpleNamespace(
                    **(
                        vars(tree.info)
                        | {
                            "device": node.st_dev,
                            "inode": node.st_ino,
                        }
                    )
                )

        return Backend

    def install(self, monkeypatch, value):
        if not hasattr(value, "os"):
            return
        modeled_os = SimpleNamespace(
            getresuid=lambda: (0, 0, 0),
            getresgid=lambda: (0, 0, 0),
            getgroups=lambda: [0],
            open=self.open,
            close=self.close,
            fstat=self.fstat,
            listdir=self.listdir,
            mkdir=self.mkdir,
            fchmod=self.fchmod,
            fchown=self.fchown,
            fsync=self.fsync,
            listxattr=lambda fd: self.fstat(fd).attrs,
            fspath=lambda path: path,
        )
        monkeypatch.setattr(value, "os", modeled_os)
        monkeypatch.setattr(value.sys, "platform", "linux")
        monkeypatch.setattr(value, "LinuxBackend", self.backend())
        monkeypatch.setattr(value, "_mountinfo", lambda: self.mount_info)


def test_fresh_mount_creates_exact_domains_and_publishes_root_last(monkeypatch):
    value, tree = module(), Tree(lost_found=True)
    tree.install(monkeypatch, value)
    result = value.provision_domains("/studio-data", UUID_TEXT)
    expected = {
        "": (0, 10001, 0o1770),
        "tmp": (0, 10001, 0o1770),
        ".storage-probes": (19000, 10001, 0o700),
        "tmp/.storage-probes": (19000, 10001, 0o700),
        ".storage-control": (19000, 10001, 0o750),
    }
    assert result == {
        "status": "provisioned",
        "uuid": UUID_TEXT,
        "device": 12,
        "inode": 2,
        "mount_id": 7,
    }
    for suffix, policy in expected.items():
        node = tree.nodes["/studio-data" + ("/" + suffix if suffix else "")]
        assert (node.st_uid, node.st_gid, stat.S_IMODE(node.st_mode)) == policy
    mutations = [e for e in tree.events if e[0] in {"mkdir", "chmod", "chown"}]
    assert mutations[0] == ("chmod", "/studio-data", 0o700)
    assert mutations[-1] == ("chmod", "/studio-data", 0o1770)
    assert not tree.fds


@pytest.mark.parametrize(
    "field,bad",
    [
        ("fs_uuid", UUID(int=0)),
        ("fs_type", "9p"),
        ("mount_root", "/tmp"),
        ("writable", False),
    ],
)
def test_mount_mismatch_rejected_without_mutation(monkeypatch, field, bad):
    value, tree = module(), Tree()
    setattr(tree.info, field, bad)
    tree.install(monkeypatch, value)
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)
    assert not [e for e in tree.events if e[0] in {"mkdir", "chmod", "chown"}]
    assert not tree.fds


@pytest.mark.parametrize(
    "entry", ["songs", "tmp", ".storage-probes", ".storage-control"]
)
def test_existing_library_or_crash_residue_never_adopted(monkeypatch, entry):
    value, tree = module(), Tree()
    foreign = tree.node(50)
    tree.nodes["/studio-data/" + entry] = foreign
    tree.install(monkeypatch, value)
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)
    assert tree.nodes["/studio-data/" + entry] is foreign
    assert not [e for e in tree.events if e[0] in {"mkdir", "chmod", "chown"}]


@pytest.mark.parametrize("target", ["", "/lost+found"])
@pytest.mark.parametrize(
    "field,bad",
    [
        ("st_uid", 10001),
        ("st_gid", 10001),
        ("st_mode", stat.S_IFDIR | 0o777),
        ("st_mode", stat.S_IFLNK | 0o700),
        ("st_dev", 99),
        ("attrs", ["system.posix_acl_default"]),
        ("attrs", ["system.posix_acl_access"]),
    ],
)
def test_untrusted_initial_directories_fail_closed(monkeypatch, target, field, bad):
    value, tree = module(), Tree(lost_found=True)
    setattr(tree.nodes["/studio-data" + target], field, bad)
    tree.install(monkeypatch, value)
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)
    assert not [e for e in tree.events if e[0] in {"mkdir", "chmod", "chown"}]


def test_nested_mount_rejected_before_mutation(monkeypatch):
    value, tree = module(), Tree()
    tree.mount_info += "8 7 8:2 / /studio-data/hidden rw - ext4 /dev/other rw\n"
    tree.install(monkeypatch, value)
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)
    assert not [e for e in tree.events if e[0] in {"mkdir", "chmod", "chown"}]


def test_partial_failure_preserves_created_directories_and_blocks_retry(monkeypatch):
    value, tree = module(), Tree()
    tree.install(monkeypatch, value)

    def fail(event):
        if event == ("mkdir", "/studio-data/.storage-control", 0o700):
            raise OSError("injected crash")

    tree.hook = fail
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)
    assert "/studio-data/tmp" in tree.nodes
    assert stat.S_IMODE(tree.nodes["/studio-data"].st_mode) == 0o700
    assert not tree.fds
    tree.hook = lambda event: None
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)


def test_retained_root_cannot_be_replaced_at_original_path(monkeypatch):
    value, tree = module(), Tree()
    tree.install(monkeypatch, value)

    def replace(event):
        if event == ("mkdir", "/studio-data/tmp", 0o700):
            tree.nodes["/studio-data"] = tree.node(999)

    tree.hook = replace
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)
    assert not tree.fds


def test_writable_ancestor_rejected_before_provision(monkeypatch):
    value, tree = module(), Tree()
    tree.nodes["/"].st_mode = stat.S_IFDIR | 0o1777
    tree.install(monkeypatch, value)
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)
    assert not [e for e in tree.events if e[0] in {"mkdir", "chmod", "chown"}]


def test_original_ancestor_replacement_blocks_publication(monkeypatch):
    value, tree = module(), Tree()
    tree.install(monkeypatch, value)

    def replace(event):
        if event == ("mkdir", "/studio-data/tmp", 0o700):
            tree.nodes["/"] = tree.node(999, mode=0o755)

    tree.hook = replace
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)
    assert not tree.fds


@pytest.mark.parametrize(
    "path",
    [
        "/",
        "relative",
        "/studio-data/",
        "/studio-data//x",
        "/studio-data/../x",
        "/studio-data/./x",
        12,
    ],
)
def test_noncanonical_mountpoint_rejected(monkeypatch, path):
    value, tree = module(), Tree()
    tree.install(monkeypatch, value)
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains(path, UUID_TEXT)
    assert tree.events == []


@pytest.mark.parametrize("uuid", ["invalid", UUID_TEXT.upper(), str(UUID(int=0)), None])
def test_invalid_controller_uuid_rejected(monkeypatch, uuid):
    value, tree = module(), Tree()
    tree.install(monkeypatch, value)
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", uuid)
    assert tree.events == []


@pytest.mark.parametrize(
    "method,ids",
    [
        ("getresuid", (0, 10001, 0)),
        ("getresuid", (0, 0, 10001)),
        ("getresgid", (0, 10001, 0)),
        ("getresgid", (10001, 0, 0)),
        ("getgroups", [0, 10001]),
    ],
)
def test_controller_requires_all_root_credentials(monkeypatch, method, ids):
    value, tree = module(), Tree()
    tree.install(monkeypatch, value)
    monkeypatch.setattr(value.os, method, lambda: ids)
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)
    assert tree.events == []


def test_empty_root_without_lost_found_is_supported(monkeypatch):
    value, tree = module(), Tree()
    tree.nodes["/studio-data"].st_mode = stat.S_IFDIR | 0o700
    tree.install(monkeypatch, value)
    assert value.provision_domains("/studio-data", UUID_TEXT)["status"] == "provisioned"
    assert not tree.fds


def test_lost_found_with_content_is_never_cleaned(monkeypatch):
    value, tree = module(), Tree(lost_found=True)
    foreign = tree.node(57)
    tree.nodes["/studio-data/lost+found/foreign"] = foreign
    tree.install(monkeypatch, value)
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)
    assert tree.nodes["/studio-data/lost+found/foreign"] is foreign
    assert not tree.fds


def test_unsupported_acl_query_is_not_absence_of_acl(monkeypatch):
    value, tree = module(), Tree()
    tree.install(monkeypatch, value)

    def unsupported(fd):
        raise OSError("unsupported ACL query")

    monkeypatch.setattr(value.os, "listxattr", unsupported)
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)
    assert not tree.fds


@pytest.mark.parametrize(
    "info",
    [
        "7 1 8:1 / /wrong rw - ext4 /dev/own rw\n",
        "7 1 8:1 / /studio-data rw - ext4 /dev/own rw\nbroken\n",
        (
            "7 1 8:1 / /studio-data rw - ext4 /dev/own rw\n"
            "8 1 8:1 / /studio-data rw - ext4 /dev/own rw\n"
        ),
    ],
)
def test_malformed_or_stacked_mountinfo_rejected(monkeypatch, info):
    value, tree = module(), Tree()
    tree.mount_info = info
    tree.install(monkeypatch, value)
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)
    assert not [e for e in tree.events if e[0] in {"mkdir", "chmod", "chown"}]


@pytest.mark.parametrize("failure", ["chmod", "chown", "fsync"])
def test_syscall_failure_cannot_return_success_or_remove_residues(monkeypatch, failure):
    value, tree = module(), Tree()
    tree.install(monkeypatch, value)

    def fail(event):
        if event[0] == failure and event[1] == "/studio-data/.storage-control":
            raise OSError("injected failure")

    tree.hook = fail
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)
    assert "/studio-data/.storage-control" in tree.nodes
    assert not tree.fds


@pytest.mark.parametrize("target", ["/studio-data/tmp", "/studio-data/.storage-probes"])
def test_created_entry_replacement_is_not_adopted(monkeypatch, target):
    value, tree = module(), Tree()
    tree.install(monkeypatch, value)

    def replace(event):
        if event == ("fsync", target):
            tree.nodes[target] = tree.node(999)

    tree.hook = replace
    with pytest.raises(RuntimeError, match="STORAGE_ROOT_INVALID"):
        value.provision_domains("/studio-data", UUID_TEXT)
    assert tree.nodes[target].st_ino == 999
    assert not tree.fds


def test_consumer_cannot_traverse_parent_during_provision(monkeypatch):
    value, tree = module(), Tree()
    tree.install(monkeypatch, value)

    def check(event):
        if event[0] in {"mkdir", "chown"}:
            assert stat.S_IMODE(tree.nodes["/studio-data"].st_mode) == 0o700

    tree.hook = check
    assert value.provision_domains("/studio-data", UUID_TEXT)["status"] == "provisioned"


def test_cli_success_reports_only_provisioned(monkeypatch, capsys):
    value, tree = module(), Tree()
    tree.install(monkeypatch, value)
    assert value.main(["--mountpoint", "/studio-data", "--uuid", UUID_TEXT]) == 0
    output = capsys.readouterr()
    assert '"status": "provisioned"' in output.out
    assert "validated" not in output.out
    assert output.err == ""


def test_cli_failure_reports_code_without_success(monkeypatch, capsys):
    value, tree = module(), Tree()
    tree.install(monkeypatch, value)
    assert value.main(["--mountpoint", "/studio-data", "--uuid", "wrong"]) == 1
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "STORAGE_ROOT_INVALID\n"
