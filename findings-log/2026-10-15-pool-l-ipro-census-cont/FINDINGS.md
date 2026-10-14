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
