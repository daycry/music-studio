---
name: memory-location
description: All persistent memory for this project must live in docs/memory/ inside the repo, never in ~/.claude/projects/.../memory
metadata:
  type: feedback
---

All memory/context files go in `docs/memory/` (index: `docs/memory/MEMORY.md`), same frontmatter format (one fact per file, `[[name]]` links). Do not write to the user-level `~/.claude/projects/<project>/memory/` directory.

**Why:** the user wants the whole project context contained within the project folder (2026-09-28), consistent with "everything lives inside this folder" ([[project-context]]).
**How to apply:** read `docs/memory/MEMORY.md` at session start (it is imported from `CLAUDE.md`); create/update memories there and add a one-line pointer to the index.
