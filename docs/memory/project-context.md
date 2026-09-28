---
name: project-context
description: music-studio = personal Suno-like AI music app; restarted from zero (2026-09-28) on RTX 5070 12 GB, everything inside the project folder, docs reorganized
metadata:
  type: project
---

Personal, solo project (possible future commercialization): self-hosted Suno-like app (lyrics + style → full song).

Decisions of 2026-09-28:
- **Development restarts from zero**; old code (repo `suno-sondo-clone`, `apps/runner/`) is not reused.
- **Everything lives inside `C:\Users\daycr\Development\music-studio`** — no other drives (old docs' `D:\srv\ace-step\...` no longer applies).
- **GPU: RTX 5070, 12 GB, Blackwell sm_120** (driver 616.92, Docker 29.8 on WSL2). Old Pascal/GTX 1070 decisions are obsolete.
- **Docs reorganized** (hybrid layout, user's choice): permanent docs in `docs/producto|arquitectura|decisiones|calidad|legal`, one plugin-compatible initiative per milestone in `docs/roadmap/` (M0 entorno-y-motor, M1 mvp-estudio; both specs `borrador`), old docs archived in `docs/archive/roadmap-2026-07-27/`. No € budgets or corporate gates.
- **Models (ADR-0011, to be confirmed by M0 listening test):** ACE-Step 1.5 (MIT weights) 2B turbo + LM 0.6B primary (5070 = ACE-Step tier 4); HeartMuLa-oss-3B 4-bit alternative; non-commercial models only as "lab". Lyrics assistant: Gemma 4 12B local default, Claude API optional (ADR-0012). **Song = project** (ADR-0013). **Sondo.ai-style music video** added (ADR-0015 tiers N0–N3, ADR-0016 ComfyUI headless engine; Wan 2.2, InfiniteTalk, Qwen-Image-Edit/FLUX.2 klein 4B; protagonist from uploaded photos with consent declaration). Roadmap: M3 cover art + lyric video, M4 music video, M5 LoRAs. Machine has 32 GB RAM (tight for 14B video offload).

**Why:** leaner fresh start with better hardware; keep commercialization possible.
**Docs reviewed 2026-09-28** by 3 independent reviewers (consistency, rework-risk, fact-check); all findings applied: generic task-based `/v1` engine contract (contrato-engines.md), full schema in first migration (job/asset/upload/lineage_edge…), manifest v1 for all artefacts, post-processing in server (ADR-0017), job queue (ADR-0018), code-first contracts (ADR-0019), local security (ADR-0020), weights incl. GGUF + pickle conversion (ADR-0006), CONSTITUTION.md. M0/M1 ledgers pass plugin `ledger-lint` (0 warnings) and `coverage-check`; valid task states are only borrador/en-progreso/en-revision/completado/cancelado.

**How to apply:** follow `docs/README.md`; task state only in each milestone's `tasks.md`; keep paths relative to the project folder. See [[memory-location]].
