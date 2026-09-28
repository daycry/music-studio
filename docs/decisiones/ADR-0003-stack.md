# ADR-0003 · Stack: Next.js + FastAPI + engines GPU en contenedor

- **Estado:** aceptada · **Fecha:** 2026-09-28 · El contrato se concreta en [ADR-0019](ADR-0019-contratos-code-first.md)

## Decisión
- **web:** Next.js (App Router), TypeScript, Tailwind, shadcn/ui, wavesurfer.js y next-intl. Gestor de paquetes: pnpm. Node 22 LTS.
- **server:** Python 3.12 con FastAPI, SQLAlchemy 2, Alembic y Pydantic 2. Gestor de paquetes: uv. **No usa torch.** Se encarga también del post-proceso, el render y los manifiestos ([ADR-0017](ADR-0017-postproceso-y-manifiesto-en-el-server.md)).
- **engines:** un contenedor Docker con `--gpus all` **por familia de modelo**. Todos implementan el mismo contrato `/v1` ([`../arquitectura/contrato-engines.md`](../arquitectura/contrato-engines.md)).
  - Cada uno lleva las versiones que exige su upstream. Ejemplo: ACE-Step 1.5 usa `torch 2.10+cu128` con Python 3.11, instalado con `uv sync --frozen` (su pyproject admite `>=3.11,<3.13`; se usa 3.11, igual que su Dockerfile oficial).
- **Contratos** (code-first, [ADR-0019](ADR-0019-contratos-code-first.md)):
  - `packages/engine-contract` (Pydantic) para los engines;
  - `openapi.json` generado por FastAPI para la API del server;
  - los tipos TypeScript se generan a partir de él.
- **Ejecución:** web y server en nativo (Windows), con recarga en caliente; los engines, en Docker (`docker compose --profile engines`). Un perfil «todo en contenedores» no forma parte de M1 (exigiría ffmpeg Linux en el server, nombres de servicio en `STUDIO_ENGINES` y hosts permitidos configurables).

## Motivo
- Next.js + FastAPI era un requisito original y sigue teniendo sentido: el ecosistema de audio e inferencia vive en Python.
- Hay un contenedor por familia de modelo porque las versiones que fija cada upstream chocan entre sí (`torch<2.11`, `transformers<4.58`, `bitsandbytes==…`, versiones distintas de CUDA). Un entorno común obligaría a parchear los modelos.
- El server no depende de torch y arranca en un segundo.
