---
name: push-authorized
description: Claude may push main (and task/rescue branches) to origin itself after a task is merged
metadata:
  type: feedback
---

After merging a closed task into `main` (fast-forward, ADR-0021), push it to `origin` yourself; don't hand the `git push` back to the owner.

**Why:** on 2026-10-23, after running `git push origin main rescue/2026-10-22-codex` by hand, the owner asked «¿puedes hacerlo tú?».
**How to apply:** push `main` right after each merge, and any branch the owner wants published. Never force-push, and never push anything from `.env`, `data/` or `models/` (except the locks), or personal paths (AGENTS.md §4.10). If the auto-mode classifier blocks the push, tell the owner and give them the exact command. See [[use-custom-agents-plugin]].
