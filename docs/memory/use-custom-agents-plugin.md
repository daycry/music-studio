---
name: use-custom-agents-plugin
description: All product/code work must go through the custom-agents plugin (dev-cycle, quick-implement, agents, skills) — never implement outside it
metadata:
  type: feedback
---

Always use the custom-agents plugin: `/custom-agents:dev-cycle` for planned milestones, the `quick-implement` skill for small changes, `pm-cycle`/`analyst`/`architect` for new ideas, `adversarial-review`, `tdd`, `debug-root-cause`, `nemesis`, `retro`, `changelog-sync`, `documenter`/`knowledge-curator`. Dispatch agents by name; the orchestrator (not subagents) updates the ledger.

**Why:** the user stated on 2026-09-28 "siempre se ha de usar el plugin de custom-agents".
**How to apply:** before doing any implementation or doc/product change, pick the matching plugin command/skill/agent from the table in `AGENTS.md` §2; don't hand-roll work that the plugin covers, even small changes (use the quick path). See [[project-context]].
