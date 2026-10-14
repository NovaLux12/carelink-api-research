# Area S — exercising `AGENTS.md` §2.1 over every strength-word claim in `docs/` and `README.md`

**Date:** 2026-10-14
**Area:** S — Two more evidence classes for third-party source material
(`docs/11-suggested-research-areas.md:912`, with area Q's addendum at `:931` and
the 2026-10-14 rule addendum at `:1016`).
**Claim issue:** [#125](https://github.com/NovaLux12/carelink-api-research/issues/125)
**Branch:** `research/s-independence-audit`

## Accounting

**Requests used: 0 of a 0 cap.** No vendor host was contacted, and no
third-party host, archive or repository was contacted either. The cap is zero
because every artefact this pass reads is already on disk in this repository.

**Method:** `GET` — policy statement only, taken from `AGENTS.md` §8. **No `GET`
was issued.** The pass reads committed text with `grep`/`python3`.

**Inter-request delay:** ≥2 s between requests to the same host. **Vacuous at 0
requests** — there is no pair of requests to measure, and `run.log` says so
rather than printing a spacing figure it cannot support.

**Ledger:** `results.jsonl` carries **0 rows**; `wc -l results.jsonl` = 0, which
equals the 0 in the `0 of a 0 cap` line above.
`headers/` holds no capture, because no capture exists.

### Network traffic outside the probe ledger — stated, not hidden

`0 of a 0 cap` describes **research/probe traffic against vendor and
third-party hosts**. This pass made four `gh` API calls against
`github.com/NovaLux12/carelink-api-research` itself: `git fetch`, `gh issue view
125`, `git push`, and the PR creation. Those are harness mechanics for the
claim and the review, not measurements, and none of them can bear on whether a
claim is true. They are listed here rather than left out so the ledger is not
mistaken for a claim that the process touched no network at all.

### Oracle

**None, and none was manufactured.** `AGENTS.md` §2.1's three-part test is the
rule being *applied*, not an observation, and a rule cannot be its own evidence.
Under `AGENTS.md` §2's definitions, every conclusion in this log is
**INFERRED** (or SOURCE-OBSERVED / SOURCE-PUBLISHED where it reads a named
`file:line` in a third-party repo at a named commit), and INFERRED reads as
INFERRED throughout.

## §0 — The counting rule, recorded **before** the count

`AGENTS.md` §6 item 7: *"A count generalised from a subset (44 published as 93),
with no counting rule recorded. → The counting rule lives in
`scripts/measure_assertions.py`; prose states the measured static count,
nothing else."* This pass writes its rule here, in prose, and commits it
**before** taking the count — the rule is the first commit on this branch and
the numbers land in the next one, so `git log` proves the order.

### V — the vocabulary (taken from the rule, not chosen by the audit)

The eleven phrases `AGENTS.md` §2.1 names, verbatim, and nothing else:

- **strength:** `independently` · `corroborated` · `corroborated independently` ·
  `confirms` · `confirms independently` · `verifies independently` ·
  `double-sourced`
- **coherence:** `consistent with` · `supports` · `agrees with` ·
  `not contradicted by`

`independently` is in the list because §2.1 names it; a rule that permits the
word only in defined circumstances has to name the word. `independence` /
`independent` are **not** in the list and are not matched.

### M — the match

Case-insensitive. Longest-alternative-first alternation, scanned left to right,
non-overlapping, so `corroborated independently` is **one** occurrence and not
`corroborated` + `independently`, and `not contradicted by` is **one**
occurrence and not three. The order of alternatives is load-bearing — Perl
alternation is first-match-wins — and `probe.sh` writes them in that order with
a comment saying why. The exact pattern is committed at
`probe.sh`, so a reader re-derives the denominator rather than trusting the
prose.

### S — the subjects

**In scope:** `docs/*.md` (13 files) and `README.md`. These are the canonical,
synthesised, reader-facing pages — `AGENTS.md` §3's "`docs/` — canonical,
synthesised, cites the log" — and they are what a reader of this repo is
actually sold a claim by.

**Out of scope, each for a stated reason rather than by silence:**

| Excluded | Why |
|---|---|
| `findings-log/**` | `AGENTS.md` §3: append-only, dated, **verbatim**. Editing a raw pass to relabel a strength word would destroy the retraction history that §3 and `CONTRIBUTING` step 6 say *is* the evidence. A prior pass (#120) already edited nothing here and filed a fix list; this pass adopts that posture. Hits there are audited (§5) but **not rewritten**. |
| `AGENTS.md` | Its §2.1 hits are **the rule text itself**. Counting them as claims would inflate the denominator with the very vocabulary being audited. Reported separately as D2. |
| `CONTRIBUTING-research.md`, `SECURITY.md`, `docs/RESEARCH-SESSION.md`, `regression/**`, `scripts/**`, `.github/**`, `PR.md` | Not canonical research prose. `PR.md` is a stray working file from another lane and is out of this audit's path either way. |

**A third exclusion is recorded because it is the one that could have
generalised a subset into a claim about the whole repo (§6 item 7):** hits that
are *not claims*. Four kinds, each visible in the hit list:

1. **Rule text** — `docs/09` and `docs/11` describing §2.1 itself.
2. **The audit's own subject matter** — a sentence *about* corroborated claims.
3. **Superseded wording kept visible under a correction** — `AGENTS.md` §3 and
   `CONTRIBUTING` step 6 require the original to stay readable, so a
   preservation block is evidence, not a live claim.
4. **The word used of *this repository's own* observations** — two passes by
   this repo reading the same byte. §2.1 does not exempt these: the *producer*
   is one author either way. They are audited on the same test and most of them
   fail it.

### Two denominators, stated because they are not the same number

- **D1 — matching lines per file**, by `grep -cE`. This is the denominator the
  brief asks to be re-derivable, and the one `probe.sh` §A prints.
- **D2 — occurrences**, matched left to right, non-overlapping (`probe.sh` §C).

They differ wherever one line carries two phrases, and quoting only one of them
is how a denominator stops being re-derivable. Both are committed.

### C — the audit unit

`AGENTS.md` §2.1 asks *"how many **independent sources** produced this claim"*,
which is a property of a **claim**, not of a phrase. So occurrences are grouped
into claims; a claim may be carried by two lines in one page and is audited
once. The per-claim table is §3. A count of phrases is **not** a count of
claims and is never presented as one.

---

*Sections 1–6 are written after the count; this rule section was committed first
and is unchanged by them.*
