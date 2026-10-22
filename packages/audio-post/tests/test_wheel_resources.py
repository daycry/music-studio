import hashlib
import json
import shutil
import subprocess
import sys
import sysconfig
import tarfile
import zipfile
from importlib.resources import files
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def distributions(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    shutil.copy2(ROOT / "packages/audio-post/pyproject.toml", source / "pyproject.toml")
    shutil.copytree(
        ROOT / "packages/audio-post/audio_post",
        source / "audio_post",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    paths = []
    for name in ("hatchling", "packaging", "pathspec", "pluggy", "trove_classifiers"):
        candidates = [
            p.parent
            for p in (ROOT / ".cache/uv/archive-v0").glob("*/" + name)
            if p.is_dir()
        ]
        assert candidates, f"managed cached build dependency unavailable: {name}"
        paths.append(str(candidates[0]))
    dist = tmp_path / "dist"
    dist.mkdir()
    build = """
import sys,json
sys.path[:0] = json.loads(sys.argv[1])
from hatchling.build import build_wheel, build_sdist
print(build_wheel(sys.argv[2]))
print(build_sdist(sys.argv[2]))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", build, json.dumps(paths), str(dist)],
        cwd=source,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return dist


def test_installed_manifest_without_checkout(distributions, tmp_path, ffmpeg_path):
    target = tmp_path / "installed"
    result = subprocess.run(
        [
            shutil.which("uv"),
            "pip",
            "install",
            "--python",
            sys.executable,
            "--no-deps",
            "--offline",
            "--no-cache",
            "--target",
            str(target),
            str(next(distributions.glob("*.whl"))),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    valid = json.loads((ROOT / "packages/contracts/examples/cli_run.json").read_text())
    probe = r"""
import sys,json,hashlib
from pathlib import Path
sys.path.insert(0,sys.argv[1])
sys.path.append(sys.argv[2])
import audio_post
from audio_post.manifest import _validate
from audio_post.private_context import prepare_context
assert Path(audio_post.__file__).is_relative_to(Path(sys.argv[1]))
try:
    prepare_context({})
except ValueError as error:
    assert str(error) == 'PRIVATE_CONTEXT_INVALID'
else:
    raise AssertionError('invalid private receipt accepted')
_validate(json.loads(sys.argv[3]))
data = Path('data')
data.mkdir()
(data / 'fixture.txt').write_bytes(b'music-studio fixture\n')
audio_post.write_manifest(data / 'manifest.json', json.loads(sys.argv[3]))
assert audio_post.verify_manifest(data / 'manifest.json', data) == {'valid': True, 'outputs': 1}
import numpy as np
import soundfile as sf
t = np.arange(48000) / 48000
source = data / 'raw.wav'
sf.write(source, 0.12 * np.sin(2 * np.pi * 440 * t), 48000, subtype='FLOAT')
before = source.read_bytes()
result = audio_post.process_audio(source.absolute(), (data / 'take').absolute(),
    root=data.absolute(), expected_duration_s=1, ffmpeg=sys.argv[4])
assert {o['role'] for o in result['outputs']} == {'master','listen','peaks'}
assert abs(result['post']['lufs_out'] + 14) <= 0.5
assert source.read_bytes() == before
try:
    _validate({})
except ValueError as error:
    assert 'MANIFEST_SCHEMA' in str(error)
else:
    raise AssertionError('invalid manifest accepted')
assert 'torch' not in sys.modules
print('installed valid accepted; invalid rejected; torch absent')
"""
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-c",
            probe,
            str(target),
            sysconfig.get_path("purelib"),
            json.dumps(valid),
            str(ffmpeg_path),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_built_distributions_include_exact_schema(distributions):
    expected = (ROOT / "packages/contracts/manifest-v1.schema.json").read_bytes()
    wheel = next(distributions.glob("*.whl"))
    with zipfile.ZipFile(wheel) as archive:
        assert archive.read("audio_post/manifest-v1.schema.json") == expected
        assert (
            archive.read("audio_post/private_context.py")
            == (ROOT / "packages/audio-post/audio_post/private_context.py").read_bytes()
        )
    sdist = next(distributions.glob("*.tar.gz"))
    with tarfile.open(sdist) as archive:
        members = [
            m
            for m in archive.getmembers()
            if m.name.endswith("/audio_post/manifest-v1.schema.json")
        ]
        assert len(members) == 1
        assert archive.extractfile(members[0]).read() == expected


def test_schema_resource_matches_canonical():
    canonical = (
        Path(__file__).resolve().parents[3]
        / "packages/contracts/manifest-v1.schema.json"
    )
    resource = files("audio_post").joinpath("manifest-v1.schema.json")
    assert resource.is_file(), "schema is absent from package resources"
    assert resource.read_bytes() == canonical.read_bytes()
    assert (
        hashlib.sha256(resource.read_bytes()).hexdigest()
        == "13d837fe3ecae22a6b3b3bdea66de8599e0b5fe2ce49fc08ec05457f5f9b9224"
    )
