---
name: research-area
description: Run one bounded read-only research session on the CareLink API and submit it as a PR
argument-hint: [area id, or "pick for me"]
---

You are contributing to https://github.com/NovaLux12/carelink-api-research — a
public, read-only map of Medtronic's undocumented CareLink API. A wrong claim
here misleads someone building a medical-data integration, so accuracy is worth
more than coverage.

Read these first, over HTTPS, before you touch the network (clone the repo if you
can — prefer that):
  AGENTS.md · CONTRIBUTING-research.md · docs/00-summary-the-map.md
  docs/11-suggested-research-areas.md · docs/09-methodology-and-oracles.md
  docs/10-open-questions.md

Then follow CONTRIBUTING-research.md §"Run a research session" in order, ending
at step 7.

1. Pick ONE area from docs/11 that is not already claimed in an open issue. State
   why it is the highest-value one you can do, your request cap, your delay, and
   what "closed" means — including whether a negative counts.
2. Probe. Controls first: one plausible path, one certainly-absent path.
3. Raw pass → findings-log/<YYYY-MM-DD>-<area>/. Synthesised → docs/, citing the
   log. Pin anything someone will rely on into regression/hurl/.
4. **Refill the priority page (step 7):** close the area into the dated Closed
   table, and add at least one successor area with a blocker, a definition of
   done, and INFERRED labels where they belong. If you genuinely cannot name
   one, say why in the PR.
5. Run the gate. Then open the PR.

Stop when the gate exits 0 and the PR is open, OR when you hit your stated
request cap, OR when you can state a specific blocker that stops the session — in
which case record it as the area's blocker and still write up what you have. Do
not silently exceed the cap.

Final output, in this order: one line per request (method, path, status,
discriminating header) · the evidence table (claim | OBSERVED/PUBLISHED/INFERRED |
source file:line) · the paths you created or changed · the gate exit code · the
successor area(s) you added to docs/11, or the reason you could not.