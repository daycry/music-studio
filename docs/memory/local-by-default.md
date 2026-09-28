---
name: local-by-default
description: Every feature must default to a local model; APIs/subscriptions are only optional, opt-in alternatives
metadata:
  type: feedback
---

Default to local models for everything (music, lyrics LLM, image, video, analysis). External APIs/subscriptions (Claude API, video APIs, cloud GPU) are only optional alternatives, disabled by default, enabled per feature with a key in `.env`, visible in the UI and recorded in the manifest. Music generation is always local.

**Why:** the user corrected my first proposal (Claude API as default for lyrics) on 2026-09-28: "la api/subscripción sea alternativa, el modelo local es el que debería de ser por defecto".
**How to apply:** when choosing a model/provider for any feature, pick the best local option that fits the RTX 5070 12 GB as default and list APIs as opt-in. Recorded as ADR-0014. See [[project-context]].
