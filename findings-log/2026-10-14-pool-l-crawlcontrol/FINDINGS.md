# Pool L — per-crawl positive control over Common Crawl index (#104)

**Date:** 2026-10-14
**Area:** L successor — per-crawl control that returned records on each named crawl.
**Host probed:** `index.commoncrawl.org` only. No Medtronic host was requested.
**Probe mode:** read-only GET. No vendor host touched.

## Request accounting

- **GET requests used: 20 of a 20 cap.** Cap not exceeded.
- Host contacted: `index.commoncrawl.org` only. Requests to any Medtronic host: 0.
- Inter-request delay: ≥ 3.5 s, held inside `flock` on
  the shared host lock `.loop/host-index.commoncrawl.org.lock`. Measured `t_sent` gaps
  all ≥ 3 s floor.
- Methods: GET only. No POST, authentication, or token exchange.
- Bodies: stored outside the repository; only digests and counts committed.
  (bodies in the shared scratch dir, outside the repo.)

## Result of the controls-first pass

All **seven** named indeterminate crawls (`CC-MAIN-2013-20`, `-2013-48`, `-2014-10`,
`-2015-22`, `-2021-04`, `-2021-25`, `-2022-05`) now carry a positive control that
returned `200` with records on that exact crawl, ahead of any absence conclusion:

| crawl | control (seq) | host / shape | status | records | notes |
|---|---|---|---|---|---|
| CC-MAIN-2013-20 | 8 (retry 15) | google.com (limit=5); cc (no limit) | 200 | 5 (9 cc) | cc first attempt 504 (seq 1) |
| CC-MAIN-2013-48 | 9 (retry 16) | google.com (limit=5); cc (no limit) | 200 | 5 (465 cc) | cc first attempt 502 (seq 2) |
| CC-MAIN-2014-10 | 3 | commoncrawl.org (no limit) | 200 | 37 | accounting seq 12 |
| CC-MAIN-2015-22 | 4 | commoncrawl.org (no limit) | 200 | 24 | accounting seq 13 |
| CC-MAIN-2021-04 | 10 (retry 17) | google.com (limit=5); cc (no limit) | 200 | 5 (71 cc) | cc first attempt 504 (seq 5) |
| CC-MAIN-2021-25 | 11 | google.com (limit=5) | 200 | 5 | cc both attempts 504 (seq 6, 18) |
| CC-MAIN-2022-05 | 7 | commoncrawl.org (no limit) | 200 | 134 | accounting seq 14 (status 200/301/404) |

A control host varied by crawl (commoncrawl.org alone was absent or gateway-failed on
four of seven first attempts; google.com returned records on all four). Consistent
with the crawl-dependent failure mode documented in `findings-log/2026-10-13-area-l-ipro-hcp`
§4: a `502`/`504` on one host is not a statement about the crawl.

## CDX accounting (no-limit commoncrawl.org queries)

For the three crawls whose control used a no-limit `commoncrawl.org` query, the API's
own paging accounting confirms the query shape returns a single page:

| crawl | no-limit records | `page=1` response (seq) | message |
|---|---|---|---|
| CC-MAIN-2014-10 | 37 | 400 (12) | `Page 1 invalid: First Page is 0, Last Page is 0` |
| CC-MAIN-2015-22 | 24 | 400 (13) | `Page 1 invalid: First Page is 0, Last Page is 0` |
| CC-MAIN-2022-05 | 134 | 400 (14) | `Page 1 invalid: First Page is 0, Last Page is 0` |
| CC-MAIN-2013-20 | 9 | 400 (19) | `Page 1 invalid: First Page is 0, Last Page is 0` |
| CC-MAIN-2013-48 | 465 | 400 (20) | `Page 1 invalid: First Page is 0, Last Page is 0` |

So `pages × pageSize` under-reports by ≥400× at these sizes is corroborated for five
crawls, and an un-limited query on this API is not tail-truncated (per
`docs/10` §1 row and `findings-log/2026-10-13-area-l-ipro-hcp` §4). `CC-MAIN-2021-04`'s
no-limit commoncrawl.org capture (71 records, seq 17) is a direct reading of its
response without a `page=1` accounting call — the cap was exhausted; its Last Page
claim is therefore not separately demonstrated this pass.

`CC-MAIN-2021-25` never returned a commoncrawl.org row across two attempts; its only
control this pass is google.com (limit=5, seq 11).

## What this settles

- The blocker named in `docs/11` §L-successor ("a per-crawl control that is
  known-covered *for that crawl*") is now **built for all seven crawls**: every
  crawl named in a negative carries a `200`-with-records positive control on that
  crawl. Absences previously recorded for `CC-MAIN-2013-20`, `-2013-48`,
  `-2021-04` and `-2022-05` on the minimed.eu domain scope stand, each now behind
  an independent served-crawl control.
- The 2021-25 commoncrawl.org 504 across two independent attempts is recorded as an
  observation about that host on that crawl; it does **not** imply the crawl is
  unserved (google.com returned 200, seq 11).
- This pass makes **no** new absence claim about minimed.eu: no minimed.eu probe
  was sent. The existing readable-absence verdicts transfer unchanged.

## What remains open

- Per-crawl `Last Page` accounting was not exercised for `CC-MAIN-2021-04`'s no-limit
  commoncrawl.org query (cap) and not at all for the google.com limited controls
  (which by construction carry no completeness claim).
- Whether a universal control host exists is still **INFERRED** (no: commoncrawl.org
  failed on at least one crawl, and google.com is untested for an absence; one crawl's
  absence of one host does not demonstrate it). The weaker, sufficient claim stands:
  the controls actually used (`commoncrawl.org`, `google.com`) each returned records
  on the crawls named above.

## Evidence map

| claim | class | source |
|---|---|---|
| positive controls 200 w/ records on all 7 crawls | OBSERVED | this log, seqs 3/4/7/8/9/10/11 (15/16/17) |
| commoncrawl.org gateway failures on 4 crawls | OBSERVED | this log, seqs 1/2/5/6 (18) |
| CDX `page=1` "Last Page is 0" on 5 no-limit queries | OBSERVED | this log, seqs 12/13/14/19/20 |
| crawl-dependent failure mode | INFERRED | `findings-log/2026-10-13-area-l-ipro-hcp/FINDINGS.md` §4 |
| universal-control-host impossibility | INFERRED | `docs/11` §L-successor; not demonstrated here |

## Next successor

Per-crawl control is now available; the remaining gap in area L is on the **absence**
side of the minimed.eu domain records (re-issuing the known-minimed cells with the
now-established controls lands as citation updates, not a new area). Successor:
**none required from this pass** — the successor named in `docs/11` §L (per-crawl
control) is delivered here. If a future pass needs a "known-covered handle" for a
named crawl, run the commoncrawl.org no-limit control first (9 records on
`CC-MAIN-2013-20`, 465 on `-2013-48`, 71 on `-2021-04`) and treat any gateway
failure on a *different* host as carrying no information.
