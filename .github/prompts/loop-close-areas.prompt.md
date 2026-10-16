---
name: loop-close-areas
description: Close the highest-value open research area, or prove it blocked, then refill the priority page — one loop iteration
argument-hint: [iteration number]
---

You are one iteration of a research loop on
https://github.com/NovaLux12/carelink-api-research.

Read first: AGENTS.md · CONTRIBUTING-research.md · docs/00-summary-the-map.md ·
docs/11-suggested-research-areas.md · docs/09-methodology-and-oracles.md ·
docs/10-open-questions.md

Your goal for this iteration: **close the single highest-value still-open area in
docs/11, or prove it blocked.** Cheapest-and-highest-value first, per the page's
own ordering; token-gated areas are at the bottom and are not yours to start.

1. Read docs/11. Choose one area. Check it is not claimed in an open issue.
2. Claim it with the exact request cap, the delay, and the specific result that
   would let you file it as done — including whether a negative counts. A vague
   bound is a failed iteration.
3. Probe. Controls first — one plausible path, one certainly-absent path — so
   the oracle verdict is not contaminated by the data it judges.
4. Write it up: raw pass → findings-log/<date>-<area>/; synthesised → docs/; pin
   any value someone will rely on → regression/hurl/.
5. **Refill the priority page (step 7):** move the closed area into the dated
   Closed table with its evidence, and add at least one successor area with a
   stated blocker, a definition of done, and INFERRED labels on any assumption
   behind it — minting the next free id (`AA`, `AB`, …) when `A`–`Z` is spent.
   If you genuinely cannot name one, write the reason in the PR.
6. Run `./scripts/research-gate.sh`. Open the PR.
7. Flip your area's line in `.loop/worklist.md` from `- [ ]` to `- [x]`, and
   append a Loop report to `.loop/last-report.md`:

   ## Loop report
   ITERATION: <n>
   REQUESTS_USED: <requests you made this iteration, not the running total>
   AREAS_OPEN: <count of - [ ] lines still in the worklist>
   STOP: no-unclaimed-areas | budget-exhausted | needs-human | none
   NOTES: <one line>

Stop when any of: the gate exits 0 and the PR is open; your request cap is
reached; you hit a blocker you can name precisely (record it as the area's
blocker and still submit what you have); or the area is already claimed. Do not
open a PR if the gate is red.

Final output: area letter and one-line verdict · requests used, of what cap, at
what spacing · the evidence table · paths changed and the gate exit code · the
successor area(s) added · the Loop report block verbatim.