---
name: reencauce-2026-10-22
description: After the Codex stage (Oct 5–12) the project was re-scoped — one active milestone, M1 trimmed, M2/M3 frozen, Windows storage journal parked, lean ledgers (ADR-0089)
metadata:
  type: project
---

On 2026-10-22 the user asked to clean up after a Codex stage. That stage had opened M0 to M3 at once and produced:
- 88 ADRs;
- 600 KB ledgers;
- ~11k lines of Windows NT storage journal;
- no end-to-end song in the web yet.

What was done (ADR-0089):
- Full prior state frozen in commit `36d4e99` on branch `rescue/2026-10-22-codex`, with personal paths scrubbed. It is local; the push was blocked and is left to the user.
- Old ledgers, M2/M3 and storage designs moved to `docs/archive/codex-2026-10/`.
- M0 is closed with what works: T-10, T-11 and T-12 cancelled, T-09 reduced to a basic benchmark, and T-13 needs the user's listening.
- M1 trimmed to the minimal end-to-end path. The first blocker is M1/T-05: `renameat2(NOREPLACE)` fails on the Docker Desktop 9p bind, so it is replaced by unique-id directories, plain rename and SQLite as the authority.

**Why:** the process had outgrown the product. The user approved cutting scope («haz lo que tengas que hacer para dejarlo limpio»).

**How to apply:**
- Keep one milestone active.
- Ledgers hold state, criteria and verification output only, with no attempt diary.
- Write an ADR only for real decisions.
- Keep `CONTINUE-HERE.md` to one screen.
- Do not reintroduce the VHDX/journal approach without a new ADR.

See [[project-context]], [[use-custom-agents-plugin]].
