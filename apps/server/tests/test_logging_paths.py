import os

import app
import pytest
from test_settings import settings


@pytest.mark.skipif(
    os.name == "nt", reason="Windows exige privilegio symlink; probado en Docker Linux"
)
@pytest.mark.parametrize("sink", ["directory", "file"])
def test_logging_confines_symlink_sink(tmp_path, sink):
    data = tmp_path / "data"
    outside = tmp_path / "outside"
    data.mkdir()
    outside.mkdir()
    if sink == "directory":
        (data / "logs").symlink_to(outside, target_is_directory=True)
    else:
        (data / "logs").mkdir()
        (data / "logs/server.log").symlink_to(outside / "escaped.log")
    with pytest.raises(ValueError, match="inside configured data directory"):
        app.configure_logging(settings(data_dir=data))
