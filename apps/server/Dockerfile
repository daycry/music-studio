FROM ghcr.io/astral-sh/uv:0.12.19@sha256:04d046b13e60d6bcec73cbc5e1cad25d680dea90c8573340950a0ac2d1aef424 AS uv
FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e AS workspace
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /studio
ENV UV_CACHE_DIR=/studio/.cache/uv \
    UV_PROJECT_ENVIRONMENT=/studio/.venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON_PREFERENCE=only-system \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    PATH=/studio/.venv/bin:/usr/local/bin:/usr/bin:/bin
COPY pyproject.toml uv.lock ./
COPY packages/engine-contract /studio/packages/engine-contract
COPY packages/audio-post/pyproject.toml /studio/packages/audio-post/pyproject.toml
COPY packages/weights/pyproject.toml /studio/packages/weights/pyproject.toml
COPY packages/storage-guard /studio/packages/storage-guard
COPY apps/server/pyproject.toml /studio/apps/server/pyproject.toml
COPY apps/engines/common/pyproject.toml /studio/apps/engines/common/pyproject.toml
COPY apps/engines/mock/pyproject.toml /studio/apps/engines/mock/pyproject.toml

FROM workspace AS mock
COPY apps/engines/common/engine_common /studio/apps/engines/common/engine_common
COPY apps/engines/mock/engine_mock /studio/apps/engines/mock/engine_mock
RUN uv sync --frozen --package engine-mock --no-dev --python /usr/local/bin/python
CMD ["uvicorn", "engine_mock:create_mock_app", "--factory", "--host", "0.0.0.0", "--port", "8199", "--no-access-log"]

FROM workspace AS server
COPY apps/server/app /studio/apps/server/app
COPY packages/audio-post/audio_post /studio/packages/audio-post/audio_post
COPY tools/ffmpeg-linux.lock.json /studio/tools/ffmpeg-linux.lock.json
COPY tools/ffmpeg-linux/n9.0.2-17-g2a571b6068/.archive.tar.xz /studio/.cache/ffmpeg-linux.tar.xz
RUN uv sync --frozen --package server --no-dev --python /usr/local/bin/python
RUN python - <<'PY'
import hashlib, json, pathlib, shutil, tarfile
root = pathlib.Path('/studio')
pin = json.loads((root / 'tools/ffmpeg-linux.lock.json').read_text())
archive = root / '.cache/ffmpeg-linux.tar.xz'
with archive.open('rb') as source:
    assert hashlib.file_digest(source, 'sha256').hexdigest() == pin['candidate']['sha256']
destination = root / pin['dest']
prefix = pin['candidate']['asset'].removesuffix('.tar.xz') + '/'
with tarfile.open(archive) as source:
    for member in source:
        assert member.name.startswith(prefix) or member.name == prefix[:-1]
        name = member.name.removeprefix(prefix)
        if name not in ('bin/ffmpeg', 'bin/ffprobe', 'LICENSE.txt') and not name.startswith('doc/'):
            continue
        assert not member.issym() and not member.islnk()
        if not member.isfile():
            continue
        assert '..' not in pathlib.PurePosixPath(name).parts
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.extractfile(member) as stream, target.open('xb') as output:
            shutil.copyfileobj(stream, output)
        target.chmod(0o755 if name.startswith('bin/') else 0o644)
assert (destination / 'bin/ffmpeg').is_file()
assert (destination / 'LICENSE.txt').is_file()
with (destination / 'bin/ffmpeg').open('rb') as source:
    ffmpeg_sha256 = hashlib.file_digest(source, 'sha256').hexdigest()
(destination / '.installed.json').write_text(json.dumps({'archive_sha256': pin['candidate']['sha256'], 'ffmpeg_sha256': ffmpeg_sha256}))
archive.unlink()
PY
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--no-access-log", "--log-level", "warning"]
