import sys
import uuid
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def tmp_path():
    # Windows sandbox: pytest mktemp(mode=0700) no conserva ACL heredada.
    root = Path(__file__).resolve().parents[1] / ".cache/pytest/t06"
    root.mkdir(parents=True, exist_ok=True)
    path = root / uuid.uuid4().hex
    path.mkdir()
    return path
