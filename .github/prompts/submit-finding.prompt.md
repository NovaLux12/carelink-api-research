---
name: submit-finding
description: Standard path for submitting a verified finding to this repo as a pull request.
mode: agent
---

I have a research finding to submit to this repo. Walk me through it and help me
produce a PR that matches the house standard.

**Read first:** `AGENTS.md` (the rules), `CONTRIBUTING-research.md` (this flow),
and `.github/PULL_REQUEST_TEMPLATE.md`.

## The standard

A finding is submittable when a reader can answer four questions without
re-deriving anything:

| Question | Where it must be answered |
|---|---|
| **What did you observe?** | verbatim evidence — the command and the response head |
| **How do I know it's true?** | an evidence label: **OBSERVED** / **PUBLISHED** / **INFERRED** |
| **Where did it come from?** | a `[source: findings-log/…]` path that resolves |
| **Could it be wrong, and how would I know?** | the limitations and the control that bounds it |

If any of the four is missing, the finding is not ready. That is the whole
standard.

## Before you write anything

1. **Check it is not already recorded.** Grep `docs/` and `findings-log/`. A
   re-derivation is still useful — say so explicitly and add what changed — but a
   duplicate presented as new is noise.
2. **Decide the evidence class honestly.** OBSERVED means you saw it in a live
   response. PUBLISHED means it is in a vendor document served without a login.
   INFERRED means you reasoned it and can show the assumptions. **A negative
   result is OBSERVED** — "I probed 73 paths and this does not exist" is one of
   the most valuable things anyone can contribute here.
3. **Never write a credential, internal hostname, machine path, or live session
   value into the diff.** If your finding *is* that such a thing exists, describe
   it without the value. The gate enforces this; do not work around it.

## Then

1. **Raw pass** → `findings-log/<YYYY-MM-DD>-<area>/`. Append-only. Include your
   request count, your cap, your delay, and any negative results.
2. **Synthesised finding** → the relevant `docs/` page, citing the log. Do not
   duplicate the log; link it.
3. **Pin it** if it is a value someone will rely on → an assertion in
   `regression/hurl/`. A claim that isn't pinned will quietly go stale; that has
   happened here repeatedly.
4. **Run the gate:**
   ```bash
   ./scripts/research-gate.sh
   ```
   Exit 0 or don't open the PR. It scans the diff for credentials and internal
   hostnames, validates every citation, and re-runs the vendor suite. CI runs the
   identical script, so a red gate blocks the merge anyway.
5. **Open the PR** using the template. Fill the evidence table honestly,
   including the request count. If you are correcting something already
   published, keep the original claim visible with the correction attached —
   **never delete a retraction.** That history is the evidence.

## What gets a PR merged

- Gate passes.
- Every claim labelled and cited.
- Corrections preserved, not smoothed over.
- Diagrams are Mermaid, every branch labelled.
- Honest about limits. "This does not prove X" is worth more than a confident
  sentence that implies it.

## If you are not sure

Open an issue using the *New finding* form and say what you have and what you
cannot yet establish. Partial findings are welcome and get labelled partial.
A finding held back for a disclosure decision is also fine — say that, and say
why, rather than publishing it and hoping.