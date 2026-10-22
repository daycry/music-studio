FROM ghcr.io/astral-sh/uv:0.12.19@sha256:04d046b13e60d6bcec73cbc5e1cad25d680dea90c8573340950a0ac2d1aef424 AS uv
FROM pytorch/pytorch:2.14.0-cuda13.0-cudnn9-runtime@sha256:9c99fafa01edfaa3d16da8c209b38b5970bb6fd6e72725ef60efc901489f70c6

SHELL ["/bin/bash", "-euo", "pipefail", "-c"]
COPY --from=uv /uv /uvx /usr/local/bin/
ENV UV_CACHE_DIR=/studio/.cache/uv \
    UV_PROJECT_ENVIRONMENT=/opt/analysis/.venv \
    UV_PYTHON_DOWNLOADS=never \
    PATH=/opt/analysis/.venv/bin:/usr/local/bin:/usr/bin:/bin \
    HF_HOME=/studio/.cache/huggingface \
    TORCH_HOME=/studio/.cache/torch \
    TRITON_CACHE_DIR=/studio/.cache/triton
RUN apt-get update && apt-get install -y --no-install-recommends \
      git=1:2.43.0-1ubuntu7.3 \
      libsndfile1=1.2.2-1ubuntu5.24.04.1 \
      libgomp1=14.2.0-4ubuntu2~24.04.1 \
    && rm -r /var/lib/apt/lists/*
COPY packages/engine-contract /studio/packages/engine-contract
COPY packages/storage-guard /studio/packages/storage-guard
COPY apps/engines/common /studio/apps/engines/common
COPY apps/engines/analysis/pyproject.toml apps/engines/analysis/uv.lock /studio/apps/engines/analysis/
WORKDIR /studio/apps/engines/analysis
# Torch/torchaudio vienen de la base por digest; uv jamás instala sus wheels.
RUN --mount=type=cache,target=/studio/.cache/uv \
    uv venv --python /usr/bin/python --system-site-packages /opt/analysis/.venv \
    && uv sync --frozen --inexact --python /usr/bin/python \
    && python -c "import torch, torchaudio, torchvision; assert torch.__version__ == '2.14.0+cu130'; assert torchaudio.__version__ == '2.11.0+cu130'; assert torchvision.__version__ == '0.29.0+cu130'; assert not torch.cuda.is_initialized(); import qwen_asr, beat_this, audiobox_aesthetics; assert not torch.cuda.is_initialized()"
COPY apps/engines/analysis/engine_analysis /studio/apps/engines/analysis/engine_analysis
COPY apps/engines/analysis/tests /studio/apps/engines/analysis/tests
RUN python -c "import engine_analysis; import sys; assert 'torch' not in sys.modules"
ENV UV_NO_SYNC=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 STUDIO_ENGINE_CONTAINER=1 \
    PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
RUN /usr/sbin/useradd --uid 10001 --no-create-home --home-dir /studio engine \
    && mkdir -p /studio/.cache/huggingface /studio/.cache/torch /studio/.cache/triton \
    && chmod 0755 /studio/.cache/triton \
    && chown -R engine:engine /studio/.cache /studio/apps/engines/analysis
USER engine
EXPOSE 8130
CMD ["uvicorn", "engine_analysis:create_app", "--factory", "--host", "0.0.0.0", "--port", "8130"]
