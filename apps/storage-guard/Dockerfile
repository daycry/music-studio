# Helper CPU stdlib exclusivo del dominio de probes (ADR-0071).
FROM python:3.12.14-slim-bookworm@sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e
WORKDIR /studio
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/studio/packages/storage-guard
COPY packages/storage-guard/studio_storage_guard /studio/packages/storage-guard/studio_storage_guard
USER 19000:10001
CMD ["python", "-m", "studio_storage_guard.helper"]
