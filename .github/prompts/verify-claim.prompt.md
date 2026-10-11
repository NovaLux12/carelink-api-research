---
name: verify-claim
description: Try to break one existing claim — verdict confirms / contradicts / inconclusive
argument-hint: [the claim, or file:line]
---

You are independently verifying **one** claim in
https://github.com/NovaLux12/carelink-api-research. Your job is to try to break
it, not to agree with it. A verification that only reads back the intended
target is worth nothing — that failure is on the record here.

Read first: AGENTS.md · CONTRIBUTING-research.md ·
docs/09-methodology-and-oracles.md · the docs page carrying the claim · the
findings-log file it cites.

**Method**

1. Take the claim's cited source and open it. **Assert you resolved the right
   thing** — the file exists and the line says what the claim says it says. A
   lookup that silently returned null is how two different values once hashed to
   the same digest and looked like agreement.
2. Re-derive it from the artefact or the live surface — not from the prose
   summary of it. Values quoted in prose notes are not evidence here; the pinned
   assertion and the raw log are.
3. If the claim rests on a hash, assert the resolved *type* before comparing, and
   treat an all-zero digest as a failure, not a comparison.
4. If it rests on a status code, re-establish the oracle with controls first —
   one plausible path, one certainly-absent path.

**Verdict — exactly one**

| Verdict | Means |
|---|---|
| **confirms** | you re-derived the same value by a route that does not pass through the claim's own wording |
| **contradicts** | you derived a different value — paste both, and the command that produced yours |
| **inconclusive** | the artefacts cannot settle it — say precisely what is missing, and what would settle it |

If the sources disagree with each other, **give both**. Never pick one silently.

Stop at the verdict. One claim per run. Do not exceed 10 requests; if you cannot
settle it inside 10, the verdict is inconclusive and the missing request is the
finding.

Final output: the claim verbatim and where it lives (file:line) · the verdict ·
the evidence (command and response head, or document and line) · if it
contradicts, the original claim kept visible with the correction attached, never
deleted · whether the regression suite pins this value, and whether it agrees.