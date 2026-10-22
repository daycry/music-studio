import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest


def test_replay_rejects_partial_reserved_history_before_returning_receipt(
    monkeypatch, tmp_path
):
    """A committed sibling must not hide a second take still reserved."""
    from app.worker import publications

    first_authority = SimpleNamespace(take_id="take-1", authority_id="a1")
    second_authority = SimpleNamespace(take_id="take-2", authority_id="a2")
    first = SimpleNamespace(authority=first_authority)
    second = SimpleNamespace(authority=second_authority)
    plan = SimpleNamespace(takes=[first, second], song_id="song-1")

    manifest = b'{"private_context":{"sha256":"' + b"a" * 64 + b'"}}'
    receipt = b"{}"
    package = SimpleNamespace(
        authority=first_authority,
        manifest=SimpleNamespace(
            bytes=len(manifest), sha256=hashlib.sha256(manifest).hexdigest()
        ),
    )

    class Result:
        def __init__(self, row):
            self.row = row

        def mappings(self):
            return self

        def one(self):
            return self.row

    class Connection:
        def __init__(self):
            self.revision = None

        def execute(self, _statement):
            return Result(self.revision)

    connection = Connection()

    class ConnectionContext:
        def __enter__(self):
            return connection

        def __exit__(self, *_args):
            return False

    class Engine:
        def connect(self):
            return ConnectionContext()

    publisher = publications.Publisher(Engine(), tmp_path, None, None)
    intents = {
        "take-1": {"active_revision_id": "rev-1", "state": "committed"},
        "take-2": {"active_revision_id": "rev-2", "state": "reserved"},
    }
    revisions = {
        "rev-1": {"package": package, "package_sha256": "package-sha"},
        "rev-2": {"package": None, "package_sha256": None},
    }
    monkeypatch.setattr(
        publisher,
        "intent",
        lambda _connection, entry: intents[entry.authority.take_id],
    )

    def execute(statement):
        # The statement carries the revision id in its bound parameters; using
        # the call order keeps this test independent of SQLAlchemy internals.
        connection.revision = (
            revisions["rev-1"] if connection.revision is None else revisions["rev-2"]
        )
        return Result(connection.revision)

    connection.execute = execute
    monkeypatch.setattr(publications, "canonical_sha256", lambda _value: "package-sha")
    monkeypatch.setattr(publications, "stage", lambda *_args: tmp_path / "pending")
    monkeypatch.setattr(
        publications, "safe_path", lambda root, relative: Path(root) / relative
    )
    monkeypatch.setattr(
        publications,
        "read_file",
        lambda path, **_kwargs: (
            manifest if Path(path).name == "manifest.json" else receipt
        ),
    )
    monkeypatch.setattr(
        publications, "prepare_context", lambda _value: (receipt, "a" * 64)
    )

    with pytest.raises(ValueError, match="^CPU_EXECUTION_REQUIRES_RECOVERY$"):
        publisher.receipt_from_history(plan, "execution", receipt)


def test_prepared_context_reuses_authenticated_material(monkeypatch):
    from app.worker import packages
    from audio_post.private_context import PreparedContext

    context = {"marker": "same-object"}
    prepared = PreparedContext(context, b"canonical", "a" * 64)
    monkeypatch.setattr(
        packages,
        "prepare_context",
        lambda _value: pytest.fail("no se debe serializar otra vez"),
    )

    assert packages._context_material(context, prepared) == (
        b"canonical",
        "a" * 64,
    )


def test_replay_reconstructs_durable_failed_and_cancelled_takes(tmp_path):
    """A mixed historical outcome must retain every durable failure result."""
    from app.worker.contracts import TakeFailure
    from app.worker.execution import CpuAudioService
    from test_worker_publication_invariants import EXECUTION, OTHER, SONG, TAKE

    first_authority = SimpleNamespace(take_id=TAKE, output_index=0, song_id=SONG)
    second_authority = SimpleNamespace(take_id=OTHER, output_index=1, song_id=SONG)
    entries = [
        SimpleNamespace(authority=first_authority),
        SimpleNamespace(authority=second_authority),
    ]
    plan = SimpleNamespace(takes=entries, song_id=SONG)
    intents = {
        TAKE: {"state": "failed", "active_revision_id": "rev-1", "error_code": None},
        OTHER: {
            "state": "cancelled",
            "active_revision_id": "rev-2",
            "error_code": None,
        },
    }
    revisions = {
        "rev-1": {"error_code": "AUDIO_INVALID"},
        "rev-2": {"error_code": "CANCELLED"},
    }

    class Result:
        def __init__(self, row):
            self.row = row

        def mappings(self):
            return self

        def one(self):
            return self.row

    class Connection:
        def __init__(self):
            self.index = 0

        def execute(self, _statement):
            self.index += 1
            return Result(revisions[f"rev-{self.index}"])

    connection = Connection()

    class ConnectionContext:
        def __enter__(self):
            return connection

        def __exit__(self, *_args):
            return False

    class Engine:
        def connect(self):
            return ConnectionContext()

    service = object.__new__(CpuAudioService)
    service.engine = Engine()
    service.root = tmp_path
    service.publisher = SimpleNamespace(
        intent=lambda _connection, entry: intents[entry.authority.take_id]
    )

    results = service._stored_results(plan, EXECUTION)

    assert results == (
        TakeFailure(
            status="failure", take_id=TAKE, output_index=0, code="AUDIO_INVALID"
        ),
        TakeFailure(status="failure", take_id=OTHER, output_index=1, code="CANCELLED"),
    )
