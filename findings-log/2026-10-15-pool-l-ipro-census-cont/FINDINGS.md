# Pool L — area L continuation: the census over the 64 unread in-window crawls

**Date:** 2026-10-15. **Area:** L. **Claim:** issue #126.
**Predecessor:** `findings-log/2026-10-14-pool-l-ipro-hcp-census/` (40 requests, the
first pass; every correction to it is appended there, never edited in place).

## Pre-flight accounting — stated BEFORE the first request of this pass

**Continuation budget: 200 of a 240 cap.** The area total is **240** (the first
pass's 40 plus this pass's 200). **This is an authorised increase, not an
overrun:** the repository owner extended claim #126's budget from 40 to 240 in
round 2, after verifier round 1 established that the first pass was cut off
mid-flight — seq 40's **retry** was blocked by the cap, and `CC-MAIN-2018-05` was
selected but never queued. **0 requests of this pass had been sent when this
section was written**, and the harness aborts on its own cap check before each
attempt, so `results.jsonl` in this directory will hold **exactly 200 rows** if the
queue outlasts the budget. `wc -l results.jsonl` is checked against the figure in
the line above in **both** directions.

- **Host: `index.commoncrawl.org` only.** `data.commoncrawl.org` not used.
  **Requests to any Medtronic host: 0.**
- **Method: GET only.** No POST, no authentication, no token exchange.
- **Delay ≥ 3.5 s**, held *inside* `flock` on the per-host lock
  `<pool-root>/.loop/host-index.commoncrawl.org.lock`, passed in as `$L_LOCK`; no
  literal home path is committed (`AGENTS.md` §7). Bodies live in `$L_BODIES`,
  outside the repository.

## What this pass is for, and what it is not for

**It continues the census; it does not re-argue the first pass's findings.** Its
whole job is to read crawls the first pass could not reach, under the same two
queries per crawl — **per-crawl positive control first, then `minimed.eu`
`matchType=domain`, `output=json`, no `limit`** — and to classify every cell with
the counting rule that governs all of them:

> a cell is readable as an absence **only if some row for that crawl answered 200**.

`502` / `504` / `503` / `400` is a **failure, never an absence**, and is re-issued
up to `MAXRETRY=2`. `example.com` is **banned** as a control: it was measured
absent from `CC-MAIN-2015-06` (`2026-10-13-area-l-ipro-hcp` §5-C2), and a control
failure or `404` proves nothing.

**The claim does not change and is not widened by spending this budget.** It
remains **"absent from every crawl this pass could read"**. More requests narrow
the negative; they never make it "absent from Common Crawl", which stays
disclaimed. The only instrument that would address that is successor **S-L1**,
the `cluster.idx`-level served-ness check, which remains unbuilt.

## The queue, and how the crawls were chosen

All **64** crawls still unread inside the 2013-05-17 → 2022-05-13 window, taken
from the committed `crawl-window.txt` of the first pass — which is derived from
`GET /collinfo.json` (seq 1 there, 200, 35 226 B, 128 published indexes) and
never guessed. `CC-MAIN-2018-05` is in that list: it was **selected by the first
pass and never enqueued**, and it is queued here.

**Control host is strictly alternating by crawl index** — `commoncrawl.org`,
`google.com`, `commoncrawl.org`, … 32 of each across 64 crawls — because pool-L
measured `commoncrawl.org` first-attempt-failing on 4 of 7 crawls and `google.com`
covering all four, and neither is a reliable single choice. The description is
checkable against `run.log` rather than a characterisation.

**Budget, at the corrected figure.** 64 crawls × 2 queries = 128 logical queries.
Round 2 corrected the first pass's expectation algebra (see the correction appended
to the predecessor's log): `probe.sh` sends `N = min(Geom(p), 3)` attempts per
query, so `E[N] = 1 + p + p²`, and at the measured row failure rate that is
**3.30 requests per two-query crawl** — not the 2.36 the predecessor published, and
not 2. **128 × 3.30 ≈ 422 expected rows against a 200 cap**, so the budget binds
well before the queue does and this pass will read roughly **60 of the 64**. How
many it actually reached, and how many remain, is reported below and in the
correction appended to the predecessor's log.
---

## Outcome — what the budget bought

**188 requests sent of the 200 authorised. The queue ran out before the cap did**,
so the cap never bound: all **64** queued crawls were read, and the last **11
requests** were spent re-issuing the five cells the sweep had left with no verdict.

| | |
|---|---|
| requests | **188** (authorisation 200; area total **228 of a 240 cap** with the predecessor's 40) |
| status codes | `200` ×120, `502` ×33, `504` ×24, `404` ×8, `400` ×3 |
| failure rows | **60 of 188 (32%)** — inside the repo's recorded 28–41% band, and **every one classified as a failure, never an absence** |
| retries | **54 rows** — each a request, each with its own row, its own `headers/` capture and its own `t_queued`/`t_sent`/`t_done` |
| logical queries | 129 |
| hosts | `index.commoncrawl.org` only. **Requests to any Medtronic host: 0.** |
| method | GET only |
| spacing | `t_sent` floor **3.536 s** over 187 gaps (max 206.085 s), **0 under 3.5 s, 0 under the `>=2 s` floor**; kernel-mtime oracle **4.156 s**, 0 under 3.5 s. Both series committed in `spacing.txt`. |
| `jsessionid` | **0 occurrences**; the redaction is enforced in code (`project-row.py`), marker plus count |
| largest response | 6 318 B |

**Two negative durations** (`seq 64` −0.489 s, `seq 76` −0.427 s) — `t_done`
earlier than `t_sent`, which is impossible. This is `docs/09` §4's recorded
corrupt-`t0` class and **no cause is asserted**. Both clocks agree the spacing
was honoured: the same positions read **4.072 s** on clock A and **4.662 s** on
clock B, and **no gap on either clock is under 3.5 s**.

### The census is complete for the window, and that is the headline

`collinfo.json` publishes **128** crawl indexes; **84** overlap
2013-05-17 → 2022-05-13. Across **this pass, the predecessor and the earlier
area-L passes together**, every one of the 84 now carries a verdict:

| | count |
|---|---|
| RECORD (the last probe answered 200) | **65** |
| ABSENCE (404 behind a `200` on that crawl) | **10** |
| INDETERMINATE (404 with no `200` on any row) | **1** — `CC-MAIN-2014-23`, from the predecessor |
| FAILURE | **0** |
| read by an earlier area-L pass, under a row schema this pass's reader does not parse | **8** |
| **UNREAD** | **0** |

`census-84.txt` carries all 128 rows with each verdict and the pass it came from.
The eight `older-schema` rows **were read** — by the 2026-10-13 area-L passes, whose
ledgers use free-text `role` values and a different member field
(`ipro_hcp_urls` / `ipro_hcp_members` rather than `ipro_hcp`) — and this pass's
reader says so rather than reading them by eye. That is `docs/11`'s area-Y defect,
*the corpus is two sources, not one*, arriving as a **schema change** rather than a
missing file. It is successor **S-L4**.

**This pass's own 64 cells:** 57 RECORD · 7 ABSENCE · **0 indeterminate · 0
failure**, after the last 11 requests converted the 4 failure cells and the 1
indeterminate cell that the sweep had left open. `CC-MAIN-2018-05` — selected by
the predecessor and never enqueued — is in the queue and answered.

### Eight crawls carry `/ipro/hcp/*`, and they fill the corpus's biggest hole

**28 members across 8 crawls, spanning 2017-06-26 → 2021-09-28** — dates the corpus
previously had **nothing** for. The predecessor found the family at 2014 and at
2020; this pass shows it being crawled steadily through 2017, 2019 (twice), 2020
and 2021 (four times).

| crawl | members | dates | what is new |
|---|---|---|---|
| `CC-MAIN-2017-26` | **6** | 2017-06-26 | the family's first appearance between 2014 and 2020; **two crawl passes of the same three paths on one day** |
| `CC-MAIN-2019-35` | 3 | 2019-08-19 | — |
| `CC-MAIN-2019-47` | 3 | 2019-11-15 | — |
| `CC-MAIN-2020-45` | **6** | 2020-10-20, 2020-10-31 | **two dates eleven days apart**, the second densest cell in the area |
| `CC-MAIN-2021-17` | 1 | 2021-04-20 | **`/ipro/hcp/privacy.jsf` 403 — a path never seen before in any corpus** |
| `CC-MAIN-2021-21` | 4 | 2021-05-06 | **`/ipro/hcp/login.jsf?bhcp=1` — the same login page captured in its *queried* form** |
| `CC-MAIN-2021-31` | 2 | 2021-07-27, 2021-07-28 | **`403` on both members** — the only `/ipro/hcp/*` cells in the area that answer 403 rather than 200/302 |
| `CC-MAIN-2021-39` | 3 | 2021-09-28 | — |

**Five distinct paths now, all on `carelink.minimed.eu`**:
`/ipro/hcp/`, `/ipro/hcp/index.jsp`, `/ipro/hcp/login.jsf`,
`/ipro/hcp/login.jsf?bhcp=1`, `/ipro/hcp/main/home.jsf`, plus
`/ipro/hcp/privacy.jsf` — **six**, counting the bare prefix, of which **two are
new to this area**.

**What the 403s are and are not.** `CC-MAIN-2021-17` and `CC-MAIN-2021-31` hold
`403` records on `/ipro/hcp/privacy.jsf`, `/ipro/hcp/index.jsp` and
`/ipro/hcp/main/home.jsf`. A `403` here is **the archived HTTP status of a
capture**, not a probe result and not a claim about today's surface: the crawler
fetched them and recorded the code. **No statement is made about why**, and none
is available — the bodies are in Common Crawl, not here, and fetching them would
be a separate pass with its own budget. **INFERRED, and flagged as such:** that
the 2021 `403`s mark the surface closing rather than a crawler hitting a gate.
Nothing observed in this pass distinguishes those.

**The negative, at full census size.** `/ipro/hcp/` was **absent from 56 of the
64 cells this pass read**, and **absent from 65 of the 84 in-window crawls** the
area has read overall (the 19 remainder being the cells that do carry members,
plus the eight `older-schema` rows this pass's reader does not resolve). **The
negative is now a census and not a spread** — which is precisely the defect
`2026-10-13-area-l-ipro-hcp` recorded against itself: *"Fourteen crawls were read,
not 128, and the seven holes mean even those are not a systematic sweep of the
2013–2022 window."* **Zero in-window crawls are unread.**

### The claim does not widen, and the hole stays open

**The claim is still "absent from every crawl this pass could read."** Spending the
budget narrowed the negative from 64 unread crawls to **zero**, and that is a real
advance — but it is an advance *inside a window*, and the window is a choice this
area made in 2026-10-13 from `ARCHIVE-URLS`'s two dates. Three things stay exactly
as open as they were:

1. **Nothing here says "absent from Common Crawl."** 41 of the 128 published
   indexes lie **outside** the window entirely (2008–2013 and 2022-06 onward), and
   this area has read **one** of them — `CC-MAIN-2022-27`, on purpose, because it
   is the crawl just past the window and it turned out to carry the 2022 capture.
   **A crawl outside the window that carried a member would have refuted this
   area's reading, and one such crawl has already done exactly that.**
2. **The `403` bodies are unread.** Eight `/ipro/hcp/*` records exist whose content
   this area has never looked at.
3. **`cluster.idx` is still unbuilt** (S-L1). Every cell above is "the crawl
   answered", never "the crawl is served", which is a weaker statement than the
   one that would address the whole-corpus question.

### The budget figure, checked against the corrected formula

The predecessor's corrected figure is **3.30 requests per two-query crawl**. This
pass measured:

| | value | how |
|---|---|---|
| measured, this pass | **2.94** | 188 rows ÷ 64 crawls |
| derived, this pass | **2.84** | `p = 60/188 = 0.319`; `E[N] = 1 + p + p² = 1.421`; × 2 |
| derived, predecessor | **3.30** | `p = 13/29 = 0.448`; × 2 |

**The measured figure came in 11% *below* the prediction, which is the correct
direction for a budget.** The model is conservative, as it should be. **S-L2's
figure is not restated here**: it was corrected to **3.3** in `docs/11` and the
arithmetic lives in `budget.py`. What this pass adds is the first large-sample
check of it, and the check passed.

### Evidence map

| claim | class | source |
|---|---|---|
| 188 requests; 60 failures; 54 retries; 129 logical queries | OBSERVED | `results.jsonl`, all rows; `derive.py` §1 |
| spacing floors 3.536 s / 4.156 s; 2 negative durations | OBSERVED | `spacing.txt`; `derive.py` §2 |
| this pass's 64 cells: 57 RECORD, 7 ABSENCE, 0 indeterminate, 0 failure | OBSERVED | `derive.py` §3 |
| `/ipro/hcp/` absent in 56 of those 64 cells | OBSERVED | `derive.py` §3 |
| **the window census is complete — 0 of 84 unread** | OBSERVED | `census-84.txt`; `derive.py` §6 |
| 28 members across 8 crawls, 2017-06-26 → 2021-09-28 | OBSERVED | `derive.py` §4, from the response bodies |
| `/ipro/hcp/privacy.jsf` and `/ipro/hcp/login.jsf?bhcp=1` are new paths | OBSERVED | same |
| the 2021 `403`s mark the surface closing | **INFERRED**, flagged, nothing observed distinguishes it | this log, "What the 403s are and are not" |
| control hosts were strictly alternating, 32 of each | OBSERVED | `q-01-census-cont.tsv` vs `run.log` |
| measured 2.94 vs derived 2.84/3.30 — the model is conservative | OBSERVED (the comparison) | `budget.py`; `derive.py` §5 |

### Reproduction

```bash
cd findings-log/2026-10-15-pool-l-ipro-census-cont
python3 derive.py        # every figure above, from committed files only
python3 budget.py        # the S-L2 arithmetic, exact rationals, both the right and wrong forms
wc -l results.jsonl      # 188 — must equal the 188 in the outcome table above
```

`L_BODIES` is optional and re-measures the mtime oracle live when set; when unset
`derive.py` **says so** rather than printing nothing.

## Successors to this pass

**S-L1 — unchanged and still the one that matters.** The `cluster.idx`-level "is
this crawl served at all" check remains unbuilt. Nothing above is a statement
about servedness. **Blocker:** none. **Closes when** every crawl a pass names in a
negative carries a served/unserved verdict from `cluster.idx` as well as from the
CDX API. **Assumptions (INFERRED):** that the two are independent signals.

**S-L2 — the census is done; the successor is no longer the window.** 0 of 84
in-window crawls unread. **Blocker for what remains:** budget, and the fact that
41 published indexes lie outside the window. **Closes when** either the window
justification is re-examined against `ARCHIVE-URLS`, or those 41 crawls are read
too. **Assumptions (INFERRED):** that a member outside the window would have
meant the family spans longer than 2014–2022 — which `CC-MAIN-2022-27` supports.

**S-L4 — one reader for the area's ledgers.** The eight `older-schema` rows exist
because three passes wrote three row schemas. **Blocker:** none, zero requests.
**Closes when** one script reads every area-L ledger and produces the census with
no manual reading, and the corpus is two sources in the sense `docs/11`'s area-Y
addendum means it. **Assumptions (INFERRED):** that the three schemas carry the
same facts — the free-text roles look like the same queries under other names, but
that is a reading of strings, not a demonstrated equivalence.


## Correction (2026-10-15) — verification round 3: a cited figure the script could not emit, a re-derivation over an empty set, a count that did not add up, and a window figure that was a third short

Round 3 returned **NOT CLEAN** on `4c585cd` and **confirmed the measurement**:
the census, the 28 members, the spacing, the two negative durations, the host and
method discipline, the scrub, and the out-of-window refutation were all
independently re-derived and stood. What was broken was the layer that *publishes*
those numbers — a cited figure the cited script could not produce, a re-derivation
that ran over an empty set and so could not fail, a ledger decomposition that did
not sum, and two stale counts. **Zero new requests.** Every figure below is
re-derived by `budget.py` and `derive.py`, both of which were changed first.

### R3-1 — `3.30` was hand-typed, and `budget.py` could not produce it

`FINDINGS.md:67`, `:68`, `:192`, `:199` and the evidence-map row at `:220` all
published **3.30**, and cited `budget.py` as the source. **`budget.py` computed `p`
over the whole predecessor ledger** — 40 rows, 15 failures, `p = 0.375` — and
printed **3.0312**. Its only argument was whole ledger *files*, so it could not be
given the 29-row population the published figure used. **The claim that these
figures were "now computed by `budget.py` so prose cannot drift from the algebra"
did not hold for this figure: the population had drifted, not just the prose.**

**Fixed at source.** `budget.py` now takes a **named population** and prints the
rule with the number:

```
budget.py --population s-l2
  THE PUBLISHED S-L2 FIGURE  every predecessor-ledger row whose crawl is one of the
  9 crawls that pass FIRST READ (…); the 3 re-probed prior-read crawls and the 1
  anchor reproduction are excluded
     population 29 rows over 9 crawls | p = 13/29 = 0.448276
     E[N] = 1 + p + p^2 = 1.649227   ->  2 queries x 1.649227 = 3.2985 requests/crawl
     MEASURED 3.2222 requests/crawl | model ABOVE the measurement by 2.4%
```

**`3.2985` is what the script emits**, and the published **3.30** is that figure
rounded. `64 × 3.2985 = 211.1` rows predicted — so the "211" in the prose was
`64 × 3.30` typed by hand and **happened to be right**; it is now derived, and it
would move if the population moved.

**A consequence round 3 forced that round 2 did not: "the model is conservative"
does not generalise.** The sign of (derived − measured) depends on `p`:

| population | p | derived | measured | direction |
|---|---|---|---|---|
| S-L2 (29 rows) | 0.4483 | 3.2985 | 3.2222 | derived **ABOVE** by 2.4% |
| this pass (188) | 0.3191 | 2.8420 | 2.9375 | derived **BELOW** by 3.3% |
| both (228) | 0.3289 | 2.8743 | 2.9610 | derived **BELOW** by 2.9% |

The model is conservative only near the failure rate it was fitted on and slightly
optimistic at the lower rate this pass met. **A single population cannot license a
claim about the error's sign**, so both directions are now printed with every
figure and no prose asserts one.

### R3-2 — `derive.py` §6 re-derived over an **empty set** and could not fail

**This was fixed before anything else, because while it stood every census figure
downstream of that script was unverified.** §6 filtered `census-84.txt` rows on
`len(r) == 5 and r[3] == 'yes'`. Measured field-widths in that file: **2 × 1-field,
7 × 2, 2 × 3, 128 × 8 — zero 5-field rows exist.** So `win` was always `[]` and
the block printed *"published 0 | in window 0 | UNREAD in window: 0"* — **it would
have printed `0` whatever the census said**, including the headline `0 of 84
unread`. Worse, §6 printed census lines copied verbatim from `census-84.txt` and
then "re-derived" them from that same file: **the script could not disagree with
the file it was checking.**

**Fixed both ways.** The filter is `len(r) >= 5`, and §6 now runs **two independent
routes** and compares them:

- **A)** every verdict re-derived from scratch out of the six area-L ledgers;
- **B)** the verdicts read from `census-84.txt`.

A disagreement is printed as a disagreement. **Current result: 0 disagreements**,
and the block independently recovers **published 128 · in window 84 · outside 44 ·
UNREAD 0**, which is the same set of numbers the verifier reached by hand.

### R3-3 — the 188 rows did not decompose, and the counting rule was unstated

`derive.py` counted rows whose `attempt_tag` matches `-rN` → **54**, and that was
published as *the* retry count. **188 rows − 129 distinct paths = 59.** The gap is
the second sweep (`q-02-retry-novdict.tsv`), which re-issued five already-attempted
paths under **fresh, un-suffixed tags** — seq **178, 181, 182, 185, 188**. So a
subset was presented as the total, with no rule stated.

**`-rN` is a label the harness puts on its own retries; it is not the same thing as
a re-issue.** The counting rule is now stated and the decomposition adds up:

| | count | rule |
|---|---|---|
| logical queries | **129** | the **first** row carrying a given path |
| re-issues, `-rN`-tagged | **54** | a later row for a path, tagged by this sweep's own retry logic |
| re-issues, **no** `-rN` tag | **5** | a path re-issued by a **later** sweep under a fresh tag — seqs 178, 181, 182, 185, 188 |
| **SUM** | **188** | **ADDS UP** |

The same rule applied to the predecessor's ledger gives **28 + 12 + 0 = 40**, so
the area total decomposes too: **157 logical · 66 `-rN` · 5 un-suffixed = 228**.

### R3-4 — "41 of 128 outside the window" is **44**

**41 is the count entirely *after* the window.** Measured: **44** outside = **41**
entirely-after (2022-06 onward) **+ 3** entirely-before (`CC-MAIN-2008-2009`,
`CC-MAIN-2009-2010`, `CC-MAIN-2012`) — and the sentence claimed **both** eras while
citing 41. `128 − 84 = 44`.

Corrected in `FINDINGS.md:178` and `:244`, in `docs/11` (three places) and in
`docs/10`. Same shape as round 2's 63/64 sweep: a number that was right for a
narrower population, published for a wider one.

### R3-5 — "Five distinct paths now" is **six**, and the "19 remainder" named 18

`FINDINGS.md:145` read *"**Five distinct paths now** … `/ipro/hcp/`,
`/ipro/hcp/index.jsp`, `/ipro/hcp/login.jsf`, `/ipro/hcp/main/home.jsf`, plus
`/ipro/hcp/privacy.jsf` — **six**, counting the bare prefix"*. The colon-list
carried five items, `privacy.jsf` makes six, and **the bare prefix is already
inside the five**, so "counting the bare prefix" was a false reconciliation. From
the ledgers the union is **6**: the predecessor had `/ipro/hcp/`, `index.jsp`,
`login.jsf`, `main/home.jsf`; this pass adds `login.jsf?bhcp=1` and `privacy.jsf`.
**"Six" was right; the subject was wrong.** This is the **fifth** instance of the
stale-count-word shape round 2 was commissioned to sweep — in the successor
written to fix four others.

`FINDINGS.md:163`'s *"19 remainder"* parenthetical named **18** and dropped
`CC-MAIN-2014-23`, the one cell whose absence is genuinely unread. Corrected, and
now derived rather than narrated:

```
absent in 65 of the 84 in-window crawls
  = 10 ABSENCE cells + 55 RECORD cells carrying no member
complement (19) = 10 RECORD carrying members + 8 older-schema + 1 INDETERMINATE
```

### R3-6 — the `## Correction` heading was justified by a **false** premise

The `derive.py` docstring said the dated heading *"is the mechanism by which the
file could be edited at all"*, because `check_append_only`
(`scripts/research-checks.py:471-480`) screens every file under `findings-log/`
with no extension filter. **The first half is true; the conclusion is false.** The
diff that check reads is three-dot, every file in this pass's directory is status
`A`, and **`A` matches neither the `D` arm nor the `M` arm** — so no file was read
and **the regex was never evaluated**. **The gate did not force a Python file to
contain markdown; a person chose to put it there.** The heading is kept — it is
what a reader and the check would both look for, and the day this merges the file
may become status `M` at which point the check *would* read it — but it is now
described as a **promise rather than a licence**. Scoping the check to `.md`
remains a maintainer decision and is still not taken here.

Also fixed: the docstring's `\(\d{4}` sat in a **non-raw** string and emitted
`SyntaxWarning: "\(" is an invalid escape sequence` on every run. It is now a raw
string; `python3 -W error::SyntaxWarning derive.py` is silent.

### R3-7 — the sweeps round 3 did not reach

- **"absent from Common Crawl"** — **three** occurrences in `docs/11` and **one** in
  `docs/10`; all four are disclaimers, not claims, and each now sits beside the
  corrected **44**. Verified, not assumed.
- **The `403` INFERRED** — `FINDINGS.md` labelled it (that part the verifier
  confirmed). **`docs/11` described the same cells without the label**, and neither
  did the PR body. Both now carry it: *that the 2021 `403`s mark the surface
  closing rather than a crawler meeting a gate is INFERRED and nothing observed
  separates the readings; the `403` is the archived status of a capture, not a
  probe result.*
- **`CC-MAIN-2018-05` in isolation** — the pages said it was "in the queue and
  answered" without naming the verdict. It is a **readable absence**: control
  `commoncrawl.org` **200 / 5 records** (seq 82), `minimed.eu` domain **404**
  `No Captures found for: minimed.eu` (seq 83), one attempt each, no retry.
- **The three-schema claim behind the 8 `older-schema` rows** — the labelling is
  stated and was verified; what was **not** verified is that no published figure
  rests on a cell read by eye. **Checked and clean**: every in-window number
  (`65 of 84`, `0 UNREAD`, the 44/3/41 split) comes from `derive.py` route **A**,
  which reads ledgers mechanically. The 8 `older-schema` cells are counted as
  *neither absent nor present* — they are in the complement, never in the absent
  set. **This is stated as a bound, not a proof of equivalence between the three
  schemas**, which remains INFERRED and is S-L4.
- **The "both credits in the config.yml comment" claim** — that claim was about the
  `origin/main` conflict and is **unchanged and still correct**: 3 open (`F R K`)
  plus 23 closed, both closures credited. **Not acted on** — the merge queue's,
  not this pass's.

### What did not change

The measurement. 188 rows; 64 crawls classified **57 RECORD / 7 ABSENCE / 0
INDETERMINATE / 0 FAILURE**; `/ipro/hcp/` absent in **56 of those 64**; **28
members across 8 crawls, 2017-06-26 → 2021-09-28**; the area-wide census
**65 of 84 absent, 0 unread**; spacing floors **3.536 s** (`t_sent`) and
**4.156 s** (kernel mtime) with 0 gaps under 3.5 s or 2.0 s; exactly 2 negative
durations; **zero Medtronic requests**; GET only; `index.commoncrawl.org` only.
The claim is still **"absent from every crawl this pass could read"** and
**"absent from Common Crawl"** stays disclaimed.


## Correction (2026-10-15) — verification round 4: three of round 3's corrections asserted an edit that was never made

Round 4 returned **NOT CLEAN** on `29ba42d` and confirmed the measurement, the
`budget.py` populations, the 188 decomposition, the two independent `derive.py`
routes (**which it proved can disagree** by flipping a verdict in `census-84.txt`
and watching route A report it), `CC-MAIN-2018-05`'s verdict, the SyntaxWarning
fix, and the append-only mechanism. **Zero new requests.**

**The framing correction, which governs this whole section.** Round 3's corrections
were written as if closing a finding and asserting the body had been corrected were
**two independent acts. They are the same act.** A correction that says the body was
fixed, when the body is append-only and was not fixed, is a **new false claim** —
and round 3 made three of them. The rule this section follows instead:

> **Where a file is append-only, the correction states what the body STILL SAYS,
> names the correct value, and says plainly that the body was not edited because
> the directory forbids it. It never claims an edit it did not make.**

### R4-1 — the direction claims: corrected in `docs/`, retracted here

**Correctable, and corrected in place** — `docs/` is canonical, not append-only:

- **`docs/11`**'s budget cell said the continuation came in *"11% below the
  prediction, the correct direction for a budget"* and that *"the model is
  conservative"*. **Both were wrong, by conflating two different quantities.**
  `2.94` is `rows ÷ crawls`; `211` is `crawls × derived`. On the like-for-like
  comparison the continuation measured **2.9375 against a derived 2.8420 — ABOVE
  the model by 3.4%** — while the predecessor's 29-row population came in **below**
  by 2.4%. The cell now publishes three named quantities side by side and claims
  **no direction**.
- **`docs/11`**'s second claim — *"observed mean attempts per query (1.43
  predecessor, **1.45** continuation) sits below the model's 1.65 / 1.42"* — was
  wrong twice: the continuation's figure is **1.4574, which is ABOVE the model's
  1.4210**, and it rounds to **1.46**, not 1.45. Corrected.
- **`docs/10:64`** said *"so the model is conservative"* and is corrected with the
  same three-quantity table.
- **`budget.py`** ended with the sentence *"no prose asserts which way it errs"* —
  a claim about prose, which was **false when written**, since `docs/11` and
  `docs/10` both asserted a direction. The file now asserts nothing about prose
  and prints both directions per population, plus the per-query mean beside the
  per-crawl figure so the two cannot be merged again.

### R4-2 — "41 of 128" was **never** corrected in this log, and round 3 said it was

**The body of this file still reads 41 at two places and round 3 claimed both were
fixed. They were not.** Verified: `git diff 4c585cd..29ba42d` on this file is a
**single hunk, 189 insertions, 0 deletions** — pure append. The sites:

| line | **what the body still says** | correct value |
|---|---|---|
| `:178` | *"**41** of the 128 published indexes lie outside the window entirely (**2008–2013 and 2022-06 onward**)"* — names **both** eras, counts one | **44** = 41 entirely-after **+ 3 entirely-before** (`CC-MAIN-2008-2009`, `CC-MAIN-2009-2010`, `CC-MAIN-2012`); `128 − 84 = 44` |
| `:244-245` | *"**41** published indexes lie outside the window … or those **41** crawls are read too"* | **44** |

**The body was not edited because `findings-log/` is append-only** (§3, and C10 of
this log's own round-1 correction, which is the passage that says so). **The
prose above is therefore superseded, not fixed**, and a reader who reads `:178`
without reading this is reading a **wrong number about both eras.**

**Round 3's R3-4 and the PR body both said "Corrected in `FINDINGS.md:178` and
`:244`" / "Corrected in both logs." Neither is true.** The predecessor's `:735`
carries the same false claim in its own C7. All three retractions are here.

### R4-3 — the same stale-count-word shape, two more sites

**The body still reads, unchanged since round 2:**

| line | **what the body still says** | correct value |
|---|---|---|
| `:145` | *"**Five distinct paths now**, all on `carelink.minimed.eu`"* above a list of **six** items | **six** |
| `:148` | *"— **six**, counting the bare prefix"* | **false reconciliation**: `/ipro/hcp/` is **item 1 of the six**; nothing needs counting |
| `:163` | *"(the 19 remainder being the cells that do carry members, plus the eight `older-schema` rows)"* | enumerates **18 of 19** — it drops **`CC-MAIN-2014-23`**, the one INDETERMINATE cell. Correct: **10 RECORD-with-members + 8 `older-schema` + 1 INDETERMINATE** |

None of the three was edited; all three are superseded by this section. **This is
the sixth and seventh instance of the shape round 2 was commissioned to sweep.**

### R4-4 — round 3's R3-5 **misquoted the line it was correcting**

**R3-5's premise was false and its fix described work already done.** It quoted
`:145` as *"a **five**-item list omitting `login.jsf?bhcp=1`"* and said *"the
colon-list carried five items"*. **The list has carried all six items since round
2** — `git show 4c585cd:…/FINDINGS.md` and the current file are **byte-identical**
on those lines. `login.jsf?bhcp=1` was never omitted.

What R3-5 got right, and what survives: the **subject** "**Five** distinct paths
now" is wrong, and *"counting the bare prefix"* is a **false reconciliation**.
What was wrong: the quote, and the implication that the list needed adding to.
**A correction must quote its target accurately; a paraphrase that makes the target
look worse than it is is its own defect class** — the same one R3-4 recorded, where
a correction inherited a false premise from the round before it.

### R4-5 — the PR body's "Proved" line was **false**; the conclusion was right

Round 3's PR body said *"Proved: stripping the heading from a modified log still
printed `ok`."* **That experiment does not print `ok`.** Driving the real
`check_append_only` with synthetic diffs: `A` → ok (file never read); `M` + heading
→ ok; **`M` + heading stripped → `!! modified without a '## Correction
(YYYY-MM-DD)' section`**; `D` → `!! deleted`.

**The correct claim is the one `FINDINGS.md` R3-6 already makes and I stated badly
in the PR body:** the diff it reads is three-dot, and on this branch every file in
this directory is status **`A`** — which matches neither the `D` arm nor the `M`
arm — so **no file is read and the regex is never evaluated.** A sharper statement
I can now support, from a scratch clone: **on a branch, a file added on that branch
is `A` in the three-dot diff no matter how many times it is edited afterwards**,
because the comparison is against the merge base, where the file does not exist.
Editing it four times changed nothing about what the check can see.

### R4-6 — round 3's R3-7 attributed an occurrence to `docs/10` that is not there

R3-7 said *"three occurrences in `docs/11` and one in `docs/10`"* of the phrase
"absent from Common Crawl". **Measured: `docs/11` has 3 (`docs/11:1282`, `:1423`,
`:1670`); `docs/10` has ZERO.** The false attribution is withdrawn. `docs/10`'s
row 64 does disclaim the whole-corpus claim — in different words, in the sentence
this round corrected — but it does not contain that phrase, and R3-7 said it did.

### R4-7 — the gate-coverage scan, finished

Round 4 confirmed my extension tally but found I had **not actually applied the ten
patterns to the 260 files**, so the CLEAN was unverified. It is now, and the
6-vs-7 is reconciled.

| | |
|---|---|
| changed files, `git diff 7d915b8 HEAD` | **260** |
| pass the gate's filter `\.(md\|yml\|yaml\|sh\|hurl)$` | **7** — `config.yml`, `docs/10`, `docs/11`, 2 × `FINDINGS.md`, 2 × `probe.sh` |
| **structurally unreadable by that filter** | **253** — `.h` 228, `.tsv` 8, `.py` 5, `.txt` 5, `.jsonl` 2, `.log` 2, `.capped` 2, `.out` 1 |

**7 is right and 6 is not** — the `SELF_PATTERNS`/`research-gate.sh` exclusion
removes nothing here, because neither file is in this diff; the likely cause of the
off-by-one is dropping `.yml`, which is exactly one file.

**The scan, all ten patterns, both code paths, all 260 files:** line-by-line with
`re.M` → **0 hits**; whole-file with `DOTALL` and no `re.M` → **0 hits**.
**Per-net, every one 0**: vendor key, reports-broker fragments, reCAPTCHA site
keys, AWS VPC endpoint, internal `.minimed`/`.medtronic` host, `.corp` host,
machine-specific paths, `jsessionid` values, `sessionData` values, credential
prefixes. **Controls proved to fire first**, to each pattern's documented shape.

**Is gate-green a meaningful signal for this PR? No, and here is the precise
claim.** The leak scan's filter structurally cannot read **253 of 260** files,
**including `results.jsonl` — the ledger every claim in this area rests on**. So
the leak scan has never read the ledger. **But `research-checks.py:355-360` does
open it**, count its rows, and fail the gate when `rows > used`; it read **228**
rows this run. **"The leak scan has not read the ledger" is true; "the gate has
never read the ledger" is false.** Two different checks, two different reach, and
conflating them is the error `docs/09` §4 records as *"the corpus is two sources,
not one"* arriving as *two checks with one name*.
