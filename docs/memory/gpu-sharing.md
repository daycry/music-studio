---
name: gpu-sharing
description: The owner's knowledge-graphs Docker stack (Ollama qwen3.5:9b ~8.9 GB) shares the RTX 5070; free VRAM before any GPU work
metadata:
  type: project
---

The owner runs a separate Docker stack `knowledge-graphs` (Kwipu bridge :8765, Kwipu MCP stdio, Graphiti MCP :8001 on FalkorDB, Ollama with qwen3.5:9b + nomic-embed-text, open-webui). Ollama keeps ~8.9 GB of the 12 GB VRAM loaded while Kwipu works. Kwipu (markdown-export) and Graphiti (mode shadow, group_id `music-studio`) are enabled in the plugin and registered as local-scope MCP servers (2026-09-28, ADR-0022).

**Why:** on 2026-09-28 the GPU showed 11,621/12,227 MiB used by that stack; ACE-Step needs ~8–10 GB and WSL2 spills silently to RAM.
**How to apply:** before GPU measurements/generation (M0 T-05+, especially T-09 benchmark) run `wsl -d Ubuntu -e ollama ps`, then `wsl -d Ubuntu -e ollama stop <model>` (currently `mimo:9b-q5`) and check `nvidia-smi` ≤ ~1.6 GB used; afterwards reload with `ollama run <model>`. The owner explicitly asked (2026-09-28) NOT to stop the systemd service or delete models — only unload with `ollama stop`. Don't run knowledge-sync during GPU jobs. See [[project-context]].
