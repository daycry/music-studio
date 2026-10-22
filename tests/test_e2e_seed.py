from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "apps" / "server" / "scripts" / "seed_e2e.py"
SPEC = importlib.util.spec_from_file_location("seed_e2e", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def test_first_named_requires_exact_match_and_preserves_order():
    items = [
        {"id": "later", "title": "E2E · Canción semilla"},
        {"id": "first", "title": "E2E · Canción semilla"},
        {"id": "partial", "title": "E2E · Canción semilla (copia)"},
    ]
    assert MODULE.first_named(items, "title", MODULE.SONG_TITLE) == items[0]
    assert MODULE.first_named(items, "title", "E2E") is None


def test_seed_constants_are_stable_and_scoped():
    assert MODULE.SEED_VERSION == "m1-e2e-v1"
    assert MODULE.COLLECTION_NAME.startswith("E2E")
    assert MODULE.SONG_TITLE.startswith("E2E")


def test_bootstrap_uses_the_browser_origin_contract():
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"session_token":"token"}'

    seen = {}

    def opener(request, timeout):
        seen["headers"] = dict(request.header_items())
        seen["timeout"] = timeout
        return Response()

    assert MODULE.SeedClient("http://server", opener).bootstrap() == "token"
    assert seen["headers"]["Origin"] == "http://127.0.0.1:3000"
    assert seen["headers"]["X-studio-session-bootstrap"] == "1"
