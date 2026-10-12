# Area Y — "all three hosts" claims, audited

Run date: 2026-10-12. Harness: **none — this pass issued ZERO vendor requests.** It is a
corpus audit.

Artefacts, all in this directory:
- [`audit-index.py`](audit-index.py) — builds the host-coverage index from the raw corpus
- [`host-coverage.txt`](host-coverage.txt) — the index, printed
- [`audit-verdicts.md`](audit-verdicts.md) — the per-claim table

This file records what the audit found and **assigns no evidence class to the claims it
checks** — that is the corpus's job, not this pass's. Where the audit disagrees with a page,
the disagreement is stated as a location and a count, and the page's own text is quoted so a
reader can check it without opening this file.

---

## 1. Request accounting

- **0 of a 0 cap.** No request was issued by `audit-index.py`, by this file, or by any step of
  the pass. `audit-index.py` reads `findings-log/**/results.jsonl` and
  `findings-log/probe-2026-10-08/recon/ORACLE-PROBE-MATRIX.md` from disk and prints.
- The claim issue ([#19](https://github.com/NovaLux12/carelink-api-research/issues/19)) declared
  `ZERO` requests and named the two controls. Both are in §3.

### Delay between requests

**None was needed, because no request was made.** The repository's `≥2 s` floor between requests
to the same host is **vacuous** for this pass — there is no second request to space from, and
neither `audit-index.py` nor any step of the audit opens a socket. The floor is stated here so
the accounting is complete rather than because it applied.

## 2. Method, and the two ways this audit nearly returned a wrong answer

The audit resolves each claim to its raw row(s) and records the **host coverage actually
present** — not the coverage asserted. Three things had to be right, and each was wrong on the
first attempt. All three are recorded because the failures are the point.

### 2.1 The ledgers are not the whole corpus

`audit-index.py` reads the JSONL ledgers under all three storage conventions area Z identified.
On that basis `connect/carepartner/v6/display/message` has **zero** `GET` rows on any host — so
`docs/03:256` ("**403 on GET** … on all three hosts") looked like an unevidenced claim.

It is not. `ORACLE-PROBE-MATRIX.md` carries that cell on three hosts and no `results.jsonl`
carries it at all. **An audit that read only the machine-readable ledgers would have marked a
correctly-evidenced claim false.** The index now merges both sources, and the source is named
on every row.

### 2.2 The matrix's columns do not assemble the way they look

The matrix records `namespace`, a `ver` column and a path *tail*. Reading it naively produces
`connect/connect/carepartner/…` (namespace already includes `connect/`) and drops the version on
the rows that carry it in the `ver` column rather than the tail. Both make real 3-host cells
look single-host. The loader now emits **both** readings where the row is ambiguous, rather
than guessing one — a claim must never be marked unevidenced because the parser guessed.

### 2.3 The lookup answered from a smaller corpus than the report beside it

`--coverage` returned **before** the matrix was merged into the index, while the full report was
printed **after**. So the two views of the same script disagreed, and the coverage lookup — the
one the audit actually queries — was matrix-blind. It reported `v11`/`v12` `discover` as
single-host when they are three-host.

This was caught only because a spot-check disagreed with the table beside it. **A lookup path
that silently answers from a smaller corpus than the report printed next to it is a check that
cannot fail**, and this repository already holds corrections for that shape. The merge now
happens before any lookup, and `audit-index.py --selftest` asserts it: it probes a
matrix-only cell and exits non-zero unless the lookup reports three hosts.

## 3. Controls

- **The method is the control.** Grep the corpus for the path, read the host column, compare
  against the claim's wording. A claim naming three hosts that resolves to one row is a defect
  **whether or not the underlying fact is true** — the defect is the evidence, not the world.
- **The schema guard is the second control.** `corpus-audit.py` must exit 0 before any count in
  this audit is believed, and its six guards (3 conventions, 5 ledgers, [2,2,1], 17 rows,
  12 cells, 2 short-key cells) must hold. A single-convention query sees 2 ACAO cells where the
  true figure is 12 — that is area Z's own retracted error, and re-running it here would
  reproduce it.
- **The two views must agree.** The index's report and its `--coverage` lookup must read the
  same corpus. `audit-index.py --selftest` asserts it against a cell that exists **only** in the
  matrix, so the assertion fails if the merge ever moves after the lookup again.

## 4. What the audit found

**29 claims in scope** (`docs/03` and `docs/06`, the area's stated scope) plus **3 added by dated
addendum** (`docs/02`, `docs/08`, and the gitignored-captures note).

**All 29 in-scope claims are confirmed by row. None is defective.**

**Counting rule, so the split can be reproduced:** in scope means the area's stated scope,
`docs/03` + `docs/06`, matched against the seven multi-host phrases (enumerated in
`audit-verdicts.md` § Counting rule) → **29 lines**. **All 29 are confirmed-by-row.** The
`clcloud.*` route claims in `docs/06` are three-host evidenced for every cell they name — v6/v11/v13
`display/message`, `csr/v2`, bare `v2`, v12, `v13/discover/android/3.6` — because areas B, X, N, U
and Z each swept all three hosts on 2026-10-12.

**This is the negative result the area allows, and it is the likelier one.** It is also, on the
evidence, the whole in-scope result: the audit's three candidate findings are one correction
(A1, outside scope), one withdrawal (A2, outside scope) and one withdrawal (Y-1, **inside** scope,
which returned the line it had marked defective to the clean set).

**Three addendum rows, outside that scope, are counted separately**: A1 corrected, A2 withdrawn,
A3 recorded-not-fixed. **Folding them into the 29 would not reproduce the table.** Two earlier
drafts of this file did exactly that and reported "26 of 29" and then "27 and 2" — both wrong,
and both repaired without first checking whether the premise they were repairing was true.

### Y-1 · `docs/03:38` — **WITHDRAWN. The claim was correct and three-host evidenced.**

This pass claimed `docs/03:38` ("All three hosts return the same document — sha256 `f8488626…`")
was only two-host evidenced, edited the page to say "2 of 3", and — because `01-discovery-pin.hurl`
carried the same claim — edited that pin file too.

**All of that was wrong, and both edits have been reverted byte-identically to `origin/main`.**

The refutation is a **tracked** ledger this audit was citing: area X's
[`results.jsonl`](../2026-10-12-area-x-cors-separation/results.jsonl) records
`GET connect/carepartner/v13/discover/android/3.6` on **all three** cumulus hosts as
`data-public-200-GET-bare`, each **20256 B**, each **sha256
`f84886265667b1b685ad0d362793c0478354f2ec30d7c81e30a52ca86a3b1609`** — one distinct digest across
three hosts. Area X's own prose says it: *"The 36-byte, 42-byte and 20256-byte bodies each
returned a byte-identical payload on all three hosts"*
([`FINDINGS.md` §5](../2026-10-12-area-x-cors-separation/FINDINGS.md)).

**How the error happened, because it is the same error as §2.1.** The 2026-10-12 discovery sweep
(`published-pointers`) genuinely does carry only **two** `v13` rows, and its only `-trials` row is
the legacy `v6` document. That part of the reasoning was correct — and I then treated **one
pass's ledger as the whole corpus**. This is precisely what area Z's addendum warns about
(*"any audit that counts, like Y, is working from a corpus whose shape is not uniform"*), written
by the pass immediately before this one, about this very mistake.

**Three rounds went into repairing the arithmetic built on that premise** before anyone checked
the premise. `§6 item 1`: a claim asserted instead of searched for. The audit's own subject was
the shape of the corpus, and it read one file.

**No correction is carried for Y-1, and `docs/03:38` and `01-discovery-pin.hurl` are unchanged
from `origin/main`.**

### Y-2 · `docs/08:37` — "replicated across five hosts", labelled OBSERVED

> | F2 | Hardcoded `x-api-key` in a public bundle, replicated across **five hosts** (drift-swept); prod API base points at a `dev.` host | **OBSERVED** | low — verified not live [SECURITY-FINDINGS S3] |

Two defects, each sufficient alone:

1. **The count outruns its own citation.** This row cites `SECURITY-FINDINGS.md` §S3, a section
   titled *"S3 is replicated across a second host"*: *"S3 was recorded as a property of one host.
   It is a property of the bundle, and the bundle is deployed **at least twice** — including on
   the `.medtronic.com` shadow."* **Two, not five.**
2. **The evidence class is the one the source forbids.** The corroborating drift file opens:
   *"**Provenance:** this file is a **reconstruction from the agent's report** … Re-verify
   before treating any row as **OBSERVED**"*. `docs/08:37` labels the row **OBSERVED**.

Neither is a disclosure risk — the key is redacted, the finding is "verified not live", and no new
host is named. Both are evidence defects, and the second is the more serious.

> **⚠ Corrected after review round 1: the `docs/08` paragraph carrying the same count — the one
> beginning *"so the finding spans **five hosts** — recorded as reported"* — is NOT part of this
> finding, and this pass originally said it was.** It carries the same "five hosts" count but **cites a different
> source** — `[source: DRIFT-AND-NEW; docs/00-summary-the-map.md]` — and `DRIFT-AND-NEW` has a
> section headed *"Five hosts, not two — the leaked bundle replicates wider"*. So that paragraph's count
> came from its own citation, and the paragraph **already carried the caveat**: *"recorded as
> reported; the sweep's own caveat is that its evidence table was never written to disk and must
> be re-verified before being treated as OBSERVED"*.
>
> **That paragraph was correct as written and has been reverted to byte-identical with
> `origin/main`.**
> This pass conflated two lines with different citations, which is §6 item 5 — derived prose
> contradicting the sources it cites. The retraction is recorded rather than deleted.
>
> **What survives for that paragraph, and is weaker than what this pass first claimed:** the drift file
> *asserts* five and **enumerates no five-host list anywhere in the corpus** — the
> "Five hosts, not two" section names two hosts and the file as a whole contains nine distinct
> names, neither of which is a five-host list. The count is unverified rather than wrong, which is
> what the paragraph already said. *(An earlier draft put a precise "three host names" figure
> here. It could not be reproduced and is withdrawn.)*

### Y-3 · `docs/02` — **WITHDRAWN. There is no defect here.**

This pass originally claimed that `docs/02`'s mermaid puts five tenants inside a subgraph titled
"compared field-by-field" when the comparison covered **four**, and it edited the subgraph title
to say so.

**That was wrong, and the edit made the page contradict itself.** `AUTH-TENANT-FINDINGS.md` §1 is
titled *"Three tenants, one Auth0 org"* and its own table names them:

| Host | `.well-known/openid-configuration` |
|---|---|
| `carelink-login.minimed.eu` (patient, EU) | 200, 2729 B |
| `carelink-login.medtronic.eu` (shadow) | 200, 2753 B |
| **`carelink-login-trials.minimed.com` (clinical)** | 200 |

**The trials tenant is in the policy comparison.** §8's *four*-tenant comparison is a different
one — it compares **JWKS `kid` sets** across EU, US and the two shadows, and trials is correctly
absent from *that*, which is exactly what the diagram's dashed edge and "no kid recorded" label
already said. `docs/02:58-60` states the three-tenant policy comparison in prose, and it is right.

The subgraph title has been **reverted to byte-identical with `origin/main`**. The error was
reading "§8 compares four" as the only comparison and glossing §1's three as "EU, US and the two
shadows" — four names for a section that calls itself three, silently dropping the tenant the
section actually compared. §6 item 5, and §6 item 1: I asserted a characterisation instead of
reading the table.

**No correction is carried for this finding, and none should be.**

### Y-4 (addendum) — the evidence for some of this is not in a clean clone

`findings-log/2026-10-12-published-pointers/.gitignore` lists `docs/`. A fresh clone therefore
does **not** hold the discovery/country/config bodies those pages rest on, so Y-1 cannot be
re-derived from a clean checkout — 10 files in that directory are tracked (`git ls-files`), none of
them a `docs/*.json` capture. Several pages depend on untracked captures. This is recorded rather than fixed: it is a
maintainer decision whether those bodies can be committed scrubbed.

## 5. Assumptions

1. **The claim set is `all three hosts | on all three | three hosts | all 3 hosts | 3 of 3 | five
   hosts | spans five`.** A claim phrased as "both regions", "each deployment" or a bare host
   list is out of scope. This is a lexical sweep, and it under-reports claims that imply
   multi-host coverage without saying so.
2. **Host coverage is the test, not truth.** This audit asks whether a claim has a row per host.
   It does not ask whether the vendor behaves the same way on all three — that is a different
   question, and Y-1's underlying fact may well be true.
3. **The two-source corpus is NOT complete, and three claims rest on files this index does not
   read.** `audit-index.py` reads `results.jsonl` and `ORACLE-PROBE-MATRIX.md` and nothing else.
   Verified after review round 1: claims `docs/03:347`, `docs/06:354` and `docs/06:467` resolve
   through `2026-10-12-published-pointers/requests.tsv:5-7` (three `carelink.*/patient/v2/
   configuration/public` rows) and `CHUNK-CORPUS-FINDINGS.md:131-141` (three named hosts).
   `--coverage` returns nothing for those paths. **"3 hosts" in `audit-verdicts.md` therefore is
   not re-derivable from the shipped index for those three lines**, and the table should not imply
   it is. **No claim was marked defective on the strength of the index alone** — each was checked
   against the page's own cited source.

## 6. What "closed" would mean

**All 29 in-scope claims are confirmed by row**, so there is nothing left to restate and no
correction to carry from the in-scope set. Outside that scope, **Y-2** (`docs/08:37`) is carried
into `docs/` as a correction with its retraction preserved; **Y-3** and **Y-1** are withdrawn and
change nothing, both files byte-identical to `origin/main`; **Y-4** is recorded, not fixed.

The 29 clean claims **are** that result — proving the rest are correctly evidenced retires the
audit, and that is the outcome here. The record's most useful half is the two withdrawals: both
were produced by reading **one file as the corpus**, and both are kept with the mechanism named.