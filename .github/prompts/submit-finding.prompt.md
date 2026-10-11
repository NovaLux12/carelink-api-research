---
name: submit-finding
description: Submit a finding you already have as a pull request — no session, no probing
argument-hint: [what you observed]
---

You already have a finding for
https://github.com/NovaLux12/carelink-api-research — a public, read-only map of
Medtronic's undocumented CareLink API. Do NOT run a research session; help write
up what you have, correctly, as a pull request.

Read over HTTPS (clone the repo if you can — prefer that):
  AGENTS.md · CONTRIBUTING-research.md §"Submit a finding" ·
  docs/09-methodology-and-oracles.md

1. **Check it isn't already recorded.** Grep `docs/` and `findings-log/`. A
   re-derivation is welcome if you say so and add what changed.
2. **Label the evidence honestly.** OBSERVED = you saw it in a live response;
   PUBLISHED = it is in a vendor document served without a login; INFERRED = you
   reasoned it, and you must show the reasoning and its assumptions. If you
   cannot classify something as OBSERVED, it is INFERRED. If you cannot point at
   the line a claim came from, delete the claim.
3. **Raw pass → `findings-log/<YYYY-MM-DD>-<name>/`** with your request count,
   cap, delay, methods, and any negative results. **Synthesised → the relevant
   `docs/` page**, citing the log with a `[source: findings-log/…]` path.
4. **Never write a credential, internal hostname, machine path, or live session
   value into the diff** — even to describe one. Describe it without the value.
5. **Pin anything that must not rot** as an assertion in `regression/hurl/`, and
   say whether a negative result closes your finding.
6. Run `./scripts/research-gate.sh` — it must exit 0 — then open the PR with
   `.github/PULL_REQUEST_TEMPLATE.md`.

If your finding corrects something already published, say so plainly and keep the
original claim visible with the correction attached. **Never delete a
retraction** — that history is the evidence.

Final output: the evidence table (claim | class | source) · the paths you
created or changed · the gate exit code · whether the value is pinned, and where.