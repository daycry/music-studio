import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture
def tmp_path():
    base = (
        Path(os.environ["STUDIO_TEST_TMP_DIR"])
        if "STUDIO_TEST_TMP_DIR" in os.environ
        else Path(__file__).resolve().parents[1] / ".cache" / "pytest"
    )
    path = base / uuid4().hex
    path.mkdir(parents=True)
    return path
