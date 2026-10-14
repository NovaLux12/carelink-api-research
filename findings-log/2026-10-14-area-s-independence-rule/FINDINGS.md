# Area S — a rule distinguishing one restated source from two independent sources

**Date:** 2026-10-14
**Area:** S (docs/11-suggested-research-areas.md, attached to its addendum bullet Q→S) —
proposing the precise independence rule named by the addendum (2026-10-13).
**Issue:** #105 (claim: pool lane S evidence-class independence rule).
**Branch:** research/s-independence.
**Requests used:** 0 of a 0 cap. No vendor host was contacted; no archive,
no Common Crawl index, and no third-party repo was re-read for this pass. The
work is a contribution rule, not a surface probe.
**Cap:** 0 (stated in the claim; there is no reason to touch Medtronic's
surface for this, and AGENTS.md §11 forbids it in any case).
**Spacing:** 0 s between requests — no requests were sent, so no pair exists to
measure.
**Method:** static analysis of this repository's own wording (AGENTS.md §2–§3,
docs/03 §3a.4, docs/10 §1 row 59, docs/11 §S addendum). 0 requests to any Medtronic host (no GET, POST, or OPTIONS issued).
**Verifier:** up to three rounds as required by the carelink-research skill.

## What this pass did

One thing, and one thing only: it wrote down the rule that §2 of AGENTS.md
(quoted here as found in `origin/main`, 2026-10-14) was missing — what has to be
true before a strength word (`independently`, `corroborated`, `confirms`,
`verifies independently`) is allowed, and in particular the test that
distinguishes **one source, restated** from **two independent sources**.

It does **not** add a normalised evidence-class label. The three classes in
`AGENTS.md` §2 (OBSERVED / PUBLISHED / INFERRED) stand exactly as written.
SOURCE-OBSERVED and SOURCE-PUBLISHED, already used in this repo's prose (e.g.
`docs/03` §3a.1–§3a.4), remain **corroboration descriptors, not ranks**,
per the failure mode §6 items 1 and 2 of AGENTS.md and `docs/11` §S's
standing blocker. This is option (b) of the §S addendum: the labels stay, the
independence rule is written.

## The proposed rule (added to `AGENTS.md` §2)

A source is identified by **the person or organisation that produced the
measurement or observation**, not by the number of artefacts carrying it.

Two sources count as **independent** only where all three of the following hold:

1. **Different authors.** Different person or organisation responsible for the
   measurement or observation. Two files in one repository, or one file and a
   PR comment on it, are one source — they share a single author's
   understanding and a single chain of custody. (Area Q, `docs/03` §3a.4: the
   boundary table in the README and the same table as a comment under PR #4711
   are the same author, `CarlosJPV`.)
2. **Different artefacts.** Neither artefact is a copy of the other, and the
   second was not produced by reading, quoting, summarising, or re-running
   the first.
3. **Neither quoting the other.** Where one is derived from the other — a PR
   comment that quotes a commit, a secondary site that reprints a README,
   a draft PR that re-types a table — it is one source stated twice,
   regardless of how many URLs or commit hashes it passes through.

**Strength words.** Before using any of
`independently`, `corroborated`, `corroborated independently`, `confirms`,
`confirms independently`, `verifies independently`, or `double-sourced`, count
the *independent* sources, not the references. The word is allowed only where
that count is ≥ 2 by the test above; otherwise it is **deleted**, per
AGENTS.md §1, and the claim is restated as
`reported by <author> at <artefact> (one source)`.

**What remains allowed but is not corroboration.** `consistent with`, `supports`,
`agrees with`, and `not contradicted by` describe coherence, not multiplicity;
they are permitted for one source. They must not be upgraded into
"independently corroborated" by later prose.

**Third-party material stays corroboration.** A SOURCE-OBSERVED (`file:line` at
a named commit) or SOURCE-PUBLISHED (README / PR / commit history) claim is
never proof of vendor behaviour, and the non-promotion rule of AGENTS.md §2
(`Never let INFERRED read as OBSERVED`) extends to it: it does not become
OBSERVED because a client prints it, and labelling it `verified` does not move
the independence count.

**Count, then label.** Evidence class labels the *kind* of source (live,
published, inferred). The independence count above is a *property of the
sources*. The two axes are orthogonal; a claim may be PUBLISHED, OBSERVED, or
INFERRED and still rest on one source.

## Examples, drawn from this repository

- **One source stated twice (INCORRECT usage, withdrawn).**
  `docs/03-discovery-and-versions.md` §3a.4: the boundary table recorded as
  "corroborated independently by a xDrip maintainer on PR #4711" — PR #4711
  contains the table (by `CarlosJPV`, also the author of the README repeating it),
  a question from `jamorham`, and an approval from `benceszasz` that restates no
  boundary value. One source. Independence count = 1. The word *independently*
  was withdrawn, and survives in prose as
  `author-reported (one source), mechanism verifiable in code`
  [source: findings-log/2026-10-13-area-q-appversion-axis/FINDINGS.md §7].
- **A premise that survived two verifier rounds without being checked (area Y,
  candidate Y-1, withdrawn).** This pass initially claimed `docs/03:38` was only
  two-host evidenced, then repaired its arithmetic through three rounds before
  checking the premise itself; area X's tracked ledger then refuted the premise
  and **no correction is carried**. Self-contradiction of this kind is the
  failure mode this rule is meant to prevent in the strength-word dimension,
  not a one-source example.
  [source: findings-log/2026-10-12-area-y-three-host-audit/FINDINGS.md
  §"Y-1 … WITHDRAWN"].
- **No second independently-verified example is cited here.** The POOL-5
  bundle's `carelink-trials.minimed.com` case cannot be called a `_counting-sources_`
  failure from the committed excerpts available to this pass, and rather than
  cite it, it is left with no citation — the pass records the gap instead (see
  §Assumptions).
- **PR-body confirmation (a second source, but only for what it confirms).**
  The xDrip PR #4711 merge independently confirms `3.6.0` → `3.8.0` because it
  is an upstream merge event distinct from the table, but it carries no
  boundary value, so "boundary corroborated in PR #4711" was never licensed at
  all, not merely overstated (`docs/03` §3a.4, "still stands").

## Assumptions (INFERRED)

That independence is judged at the level of the person or organisation that
ran the measurement, not at the level of the artefact. Two files in one
repository are one source even if their digests differ. A maintainer may define
this more strictly, and under any definition strict enough to matter the one
confirmed instance (area Q's table) fails. Stated as an assumption precisely
because it is the one judgement the check cannot automate (AGENTS.md §11: a
script decides the method, not the meaning).
