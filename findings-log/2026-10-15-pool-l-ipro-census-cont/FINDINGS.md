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
