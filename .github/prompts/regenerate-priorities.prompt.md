---
name: regenerate-priorities
description: Read the recent findings logs and the open questions, then propose 2-3 new research areas with blockers and definitions of done
argument-hint: [how many days back, default 14]
---

You are refilling the priority page of
https://github.com/NovaLux12/carelink-api-research. You are **not** probing
anything in this task — this is a synthesis pass over what is already on disk.

Read first: AGENTS.md · docs/00-summary-the-map.md ·
docs/11-suggested-research-areas.md · docs/10-open-questions.md ·
docs/09-methodology-and-oracles.md · every findings-log/ directory whose date is
in the last 14 days · the Closed areas table at the bottom of docs/11.

1. List the newest findings — what each pass learned that was not known before.
2. For each new fact, ask: *what does this now make askable that was not askable
   before?* Derive candidate areas from that, not from a general wish list.
3. Check each candidate against docs/10 §1 and the Closed table. Drop duplicates.
   Downgrade anything that needs a token into the already-blocked table.
4. Write **two or three** new areas into docs/11 using the successor-area
   template in `CONTRIBUTING-research.md` step 7, each with: what is known
   (labelled, cited), what is missing, a **specific blocker**, a **checkable**
   "closes when" that states whether a negative counts, and an
   `Assumptions (INFERRED)` line for anything reasoned rather than observed.

The bar a proposal must clear:

| Test | Fails when |
|---|---|
| **Derived** | it could have been written before the newest findings existed |
| **Bounded** | the blocker is "a token" but it sits in Tier 1; or "closes when" is not checkable |
| **Non-duplicate** | already in docs/10 §1, the Closed table, or the live tiers |
| **Labelled** | reasoning reads as observation; or a disagreement between sources is resolved silently |

If you cannot name two areas that pass, say so and say why — an honest short
page beats a padded one.

Stop when you have 2-3 areas that pass the bar and are committed, or a written
explanation of why fewer exist.

Final output: the log dirs you read, with dates · each proposed area in full
template form · which candidates you dropped and which bar they failed ·
anything moved into the token-blocked table · `git diff --stat`.