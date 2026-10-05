FROM ghcr.io/astral-sh/uv:0.12.19@sha256:04d046b13e60d6bcec73cbc5e1cad25d680dea90c8573340950a0ac2d1aef424 AS uv
FROM nvidia/cuda:12.8.1-runtime-ubuntu22.04@sha256:4a801ef9232d2b05e69df4eb8aa054dbbe2824e5499e1e6e857320bb01ac41a9

SHELL ["/bin/bash", "-euo", "pipefail", "-c"]
COPY --from=uv /uv /uvx /usr/local/bin/
ENV DEBIAN_FRONTEND=noninteractive \
    UV_PYTHON_INSTALL_DIR=/studio/.cache/uv/python \
    UV_CACHE_DIR=/studio/.cache/uv/cache \
    UV_PYTHON_PREFERENCE=only-managed \
    UV_PROJECT_ENVIRONMENT=/opt/acestep/.venv \
    PATH=/opt/acestep/.venv/bin:/opt/ffmpeg/bin:/usr/local/bin:/usr/bin:/bin \
    LD_LIBRARY_PATH=/opt/ffmpeg/lib:/usr/local/cuda/lib64 \
    HF_HOME=/studio/.cache/huggingface \
    TORCH_HOME=/studio/.cache/torch

RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl git xz-utils libsndfile1 libgomp1 \
    && rm -r /var/lib/apt/lists/*
RUN uv python install 3.11.14

# v0.1.8: código y lock de dependencias originales fijados por commit.
RUN --mount=type=cache,target=/studio/.cache/uv/cache \
    git init /opt/acestep && cd /opt/acestep \
    && git remote add origin https://github.com/ace-step/ACE-Step-1.5.git \
    && git fetch --depth 1 origin dce621408bee8c31b4fcf4811682eb9359e1bc94 \
    && git checkout --detach FETCH_HEAD \
    && uv sync --frozen --no-dev --python 3.11.14 \
      --no-install-package flash-attn --no-install-package xformers

RUN curl -fL --retry 3 \
      https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2026-07-31-14-10/ffmpeg-n7.1.5-12-g1fdbca85aa-linux64-lgpl-shared-7.1.tar.xz \
      -o /tmp/ffmpeg.tar.xz \
    && echo 'f5f0ad52c6ee28a222eb10838c231469a10ad325f84063d3bc0aadf08164b3ec  /tmp/ffmpeg.tar.xz' | sha256sum -c - \
    && mkdir /opt/ffmpeg \
    && tar -xJf /tmp/ffmpeg.tar.xz -C /opt/ffmpeg --strip-components=1 \
    && rm /tmp/ffmpeg.tar.xz

COPY packages/engine-contract /studio/packages/engine-contract
COPY packages/contracts /studio/packages/contracts
COPY apps/engines/common /studio/apps/engines/common
COPY apps/engines/acestep /studio/apps/engines/acestep
WORKDIR /studio/apps/engines/acestep
RUN --mount=type=cache,target=/studio/.cache/uv/cache \
    uv sync --frozen --no-dev --inexact --python 3.11.14 \
    && python -c "import importlib.util; assert not any(importlib.util.find_spec(x) for x in ('xformers', 'flash_attn'))"
# Mantiene el entorno upstream: uv run no debe sincronizar ni retirar sus paquetes.
ENV UV_NO_SYNC=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ACESTEP_LM_BACKEND=pt STUDIO_ENGINE_CONTAINER=1
ENV LD_LIBRARY_PATH=/opt/ffmpeg/lib:/usr/local/cuda/lib64:/usr/local/nvidia/lib:/usr/local/nvidia/lib64
RUN /usr/sbin/useradd --uid 10001 --no-create-home --home-dir /studio engine \
    && chown -R engine:engine /studio/apps/engines/acestep \
    && chown -R engine:engine /studio/.cache/uv/cache \
    && mkdir -p /studio/.cache/huggingface /studio/.cache/torch \
    && chown engine:engine /studio/.cache/huggingface /studio/.cache/torch
USER engine
EXPOSE 8101
ENTRYPOINT ["/bin/sh", "/studio/apps/engines/acestep/entrypoint.sh"]
# Factoría /v1; el padre no importa torch ni inicializa CUDA.
CMD ["uvicorn", "engine_acestep:create_app", "--factory", "--host", "0.0.0.0", "--port", "8101"]
