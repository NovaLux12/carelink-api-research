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
happens before any lookup, and the two views are asserted to agree.

## 3. Controls

- **The method is the control.** Grep the corpus for the path, read the host column, compare
  against the claim's wording. A claim naming three hosts that resolves to one row is a defect
  **whether or not the underlying fact is true** — the defect is the evidence, not the world.
- **The schema guard is the second control.** `corpus-audit.py` must exit 0 before any count in
  this audit is believed, and its six guards (3 conventions, 5 ledgers, [2,2,1], 17 rows,
  12 cells, 2 short-key cells) must hold. A single-convention query sees 2 ACAO cells where the
  true figure is 12 — that is area Z's own retracted error, and re-running it here would
  reproduce it.
- **The two views must agree.** The index's report and its `--coverage` lookup are the same
  corpus by construction after §2.3. A disagreement between them is a bug, not a finding.

## 4. What the audit found

**29 claims in scope** (`docs/03` and `docs/06`, the area's stated scope) plus **3 added by dated
addendum** (`docs/02`, `docs/08`, and the gitignored-captures note).

**26 of 29 are confirmed by row.** The `clcloud.*` route claims in `docs/06` are three-host
evidenced for every cell they name — v6/v11/v13 `display/message`, `csr/v2`, bare `v2`, v12,
`v13/discover/android/3.6` — because areas B, X, N, U and Z each swept all three hosts on
2026-10-12. **This is the negative result the area allows, and it is the likelier one.**

**Three claims are not evidenced as written.** None is a *false* claim; two are count/label
defects and one is a presentation risk.

### Y-1 · `docs/03:38` — "All three hosts return the same document"

> **OBSERVED** and hash-verified. All three hosts return the **same document** — sha256
> `f8488626…`, md5 `403220ced1a7837372b777fa97ecbb2b` — re-verified byte-identical to the
> on-disk capture `disc-eu.json`

The cited evidence is the 2026-10-12 discovery sweep, and its own table
([`2026-10-12-published-pointers/FINDINGS.md` §1](../2026-10-12-published-pointers/FINDINGS.md))
carries **two** `v13/discover/android/3.6` rows — `clcloud.minimed.eu` and `clcloud.minimed.com`,
both 20256 B / `f84886265667`. That pass's **only** `-trials` row is the **legacy** `v6` document
(10053 B, `1aab9bb1e721`). `requests.tsv` confirms it: one `-trials` line, and it is `v6`.

That pass's own prose says "the **two** `v13` documents are byte-identical" — two.

**So the document-identity claim is two-host evidenced and says three.** The *route* is
three-host evidenced (`v13/discover/android/3.6` returns 200 on all three, areas B and X), which
is a different and weaker fact than "the same document".

This is `AGENTS.md` §6 item 1 in its purest form: the claim is very likely **true**, and it was
still not evidenced.

### Y-2 · `docs/08:37` — "replicated across five hosts", labelled OBSERVED

> | F2 | Hardcoded `x-api-key` in a public bundle, replicated across **five hosts** (drift-swept); prod API base points at a `dev.` host | **OBSERVED** | low — verified not live [SECURITY-FINDINGS S3] |

Two defects, independent of each other:

1. **The count is inflated.** The cited `SECURITY-FINDINGS.md` §S3 says it in a section titled
   "**S3 is replicated across a second host**": *"S3 was recorded as a property of one host. It
   is a property of the bundle, and the bundle is deployed **at least twice** — including on the
   `.medtronic.com` shadow."* The source says **two**; the page says **five**.
2. **The evidence class is the one the source forbids.** The corroborating drift file opens:
   *"**Provenance:** this file is a **reconstruction from the agent's report** … Re-verify
   before treating any row as **OBSERVED**."* `docs/08:37` labels the row **OBSERVED** and cites
   it.

Neither is a disclosure risk — the key is redacted and the finding is "verified not live". Both
are evidence defects, and the second is the more serious: a page tells the reader to trust a
label that its own source forbids.

### Y-3 · `docs/02` — the trials tenant inside a "compared field-by-field" subgraph

The mermaid subgraph is titled *"OAuth policy compared field-by-field — identical but for
`issuer`, the endpoint hostnames derived from it, and `registration_endpoint`"*, and contains
**five** tenant nodes. Four are wired solid to the comparison node; the fifth
(`carelink-login-trials.minimed.com`) is wired **dashed** to "no kid recorded" and labelled
*"never fetched — kids Unknown, not in any source"*.

**The fact is stated correctly.** `AUTH-TENANT-FINDINGS.md` compared **three** tenants in §1 and
**four** in §8 — EU, US and the two shadows. The trials tenant is in neither. `docs/02` does not
claim otherwise.

**The risk is visual.** A reader scanning the diagram sees a five-node subgraph whose title says
field-by-field comparison. The dashed edge and label are the mitigation, and they work — but a
reader who reads titles rather than edges gets the wrong count. This is a restatement, not a
retraction: the corrected reading is that the comparison covered **four of the five**, and the
page already says so in words two lines away.

### Y-4 (addendum) — the evidence for some of this is not in a clean clone

`findings-log/2026-10-12-published-pointers/.gitignore` lists `docs/`. A fresh clone therefore
does **not** hold the discovery/country/config bodies those pages rest on, so Y-1 cannot be
re-derived from a clean checkout — only the finding's own `FINDINGS.md` and `requests.tsv` are
tracked. Several pages depend on untracked captures. This is recorded rather than fixed: it is a
maintainer decision whether those bodies can be committed scrubbed.

## 5. Assumptions

1. **The claim set is `all three hosts | on all three | three hosts | all 3 hosts | 3 of 3 | five
   hosts | spans five`.** A claim phrased as "both regions", "each deployment" or a bare host
   list is out of scope. This is a lexical sweep, and it under-reports claims that imply
   multi-host coverage without saying so.
2. **Host coverage is the test, not truth.** This audit asks whether a claim has a row per host.
   It does not ask whether the vendor behaves the same way on all three — that is a different
   question, and Y-1's underlying fact may well be true.
3. **The two-source corpus is complete enough.** `results.jsonl` plus `ORACLE-PROBE-MATRIX.md`
   cover the cells this repo has probed, but other markdown files carry host evidence too
   (`VERSION-AXIS.md`, `AWS-GATEWAYS.md`). A cell marked under-evidenced here may be evidenced in
   a file this index does not read. **No claim was marked defective on the strength of this index
   alone** — each was checked against the page's own cited source.

## 6. What "closed" would mean

Every one of the 29 claims marked **confirmed-by-row** or restated with its actual coverage, and
Y-1/Y-2/Y-3 carried into `docs/` as corrections with their retractions preserved. The 26 clean
claims **are** that result — proving the rest are correctly evidenced retires the audit, and
that is the outcome here.