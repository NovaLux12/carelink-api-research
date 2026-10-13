# Area L — early-crawl fill-in: three un-reissued indeterminate crawls, re-issued

**Status:** fills the gap named in
`findings-log/2026-10-13-area-l-ipro-hcp/FINDINGS.md` §6 and
`docs/11-suggested-research-areas.md` area L addendum: the three
indeterminate crawls that were asked **once** (`CC-MAIN-2013-20`,
`CC-MAIN-2013-48`, `CC-MAIN-2021-04`). Each is re-issued here with a
**per-crawl positive control that returned records on that same crawl**, and
with **both `matchType=domain` and `matchType=host`**. Result: for all three,
the domain-level `minimed.eu` query is now a **readable absence** (404 behind a
live control) rather than an indeterminate cell.

## Accounting
- Requests: **17 of a 45 cap** (28 unspent).
- Hosts: `index.commoncrawl.org` only.
- Method: GET only. No POST, no token exchange, no authentication.
- Delay: 2.5 s, inside a per-host `flock` on
  `carelink-api-research/.loop/host-index.commoncrawl.org.lock`.
- Spacing floor on body mtimes: **6.907 s** minimum (≥ 2.5 s; all 17 within
  the same host, zero gaps below the declared delay).
- No vendor host was contacted. No `data.commoncrawl.org` (body) fetch was
  made; only CDX-index JSON is read.
- Negative results are first-class and are recorded (see §3).

## 1. Per-crawl positive controls (sent first per crawl, all returned 200 with records)

| seq | crawl | control query | answer | records |
|---|---|---|---|---|
| 1 | CC-MAIN-2013-20 | `commoncrawl.org` domain | 200 | 5 |
| 6 | CC-MAIN-2013-48 | `google.com` domain | 200 | 5 |
| 5 | CC-MAIN-2021-04 | `medtronic.eu` domain | 200 | 5 |

These establish, independently of any `minimed.eu` answer, that the CDX index
for each named crawl is served and that the domain record-query shape returns
data there. A control **success** proves the crawl is served; a control
failure proves nothing. Under that rule the three crawls above are served, and
the two earlier controls that failed on a *different* host while another host
succeeded on the same crawl (commoncrawl.org 504 where google.com 200 on
2013-48) are correctly discarded as query failures, not as servability
verdicts.

No `example.com` control was used: it is absent from at least one crawl already
measured (`CC-MAIN-2015-06`, area L §5 C2) and is therefore not universal.

## 2. Both match types, both domains of the retired surface

Query set per crawl, identical in shape to area L's prior cells (no `limit`-truncation
concern at these record counts; `limit=200` applied, and no cell exceeded 8 records
anywhere in the 2020 cells, so 200 is not a truncating cap here):

| seq | crawl | matchType | url | answer | note |
|---|---|---|---|---|---|
| 8 | CC-MAIN-2013-20 | domain | `minimed.eu` | **404** `No Captures found` | behind seq 1 |
| 9 | CC-MAIN-2013-20 | host | `carelink.minimed.eu` | 504 (×2) | **failure, not absence** (seq 9 + seq 14) |
| 10 | CC-MAIN-2013-48 | domain | `minimed.eu` | 504 (×2) then **404** | re-issued; behind seq 6 |
| 11 | CC-MAIN-2013-48 | host | `carelink.minimed.eu` | **404** `No Captures found` | behind seq 6 |
| 12 | CC-MAIN-2021-04 | domain | `minimed.eu` | 502 (×2) then **404** | re-issued; behind seq 5 |
| 13 | CC-MAIN-2021-04 | host | `carelink.minimed.eu` | 502 (×2) | **failure, not absence** (seq 13 + seq 17) |

Raw re-issue cells:
- seq 14 `CC-MAIN-2013-20` host `carelink.minimed.eu`: 504 (second 504).
- seq 15 `CC-MAIN-2013-48` domain `minimed.eu`: 404 (second query) — confirms absence.
- seq 16 `CC-MAIN-2021-04` domain `minimed.eu`: 404 — confirms absence.
- seq 17 `CC-MAIN-2021-04` host `carelink.minimed.eu`: 502 (second 502) — remains a query failure.

## 3. Verdict — the 2013 end, answered for the domain scope

**Domain level (all hosts under `minimed.eu`).** For all three previously
indeterminate crawls, `minimed.eu` with `matchType=domain` now returns
`404 No Captures found` behind a positive control that returned records on
that same crawl:
- CC-MAIN-2013-20 — 404, control seq 1 (commoncrawl.org, 200, 5 records).
- CC-MAIN-2013-48 — 404 (after one 504 that was a query failure), control seq 6 (google.com, 200, 5 records).
- CC-MAIN-2021-04 — 404 (after one 502 that was a query failure), control seq 5 (medtronic.eu, 200, 5 records).

**Therefore, on the domain scope that covers every host name the
`/ipro/hcp/*` family could have lived on, all three are readable absences:
no `minimed.eu` capture of any kind exists in any of the three crawls.** That
includes `/ipro/hcp/index.jsp`, `/ipro/hcp/login.jsf`, and
`/ipro/hcp/main/home.jsf`, none of which are recorded for 2013 or 2014 in
Common Crawl. The earliest `/ipro/hcp/*` capture in this corpus remains
**2020-05-25** (`CC-MAIN-2020-24`, seq 3 of area L).

**The 2013 end of `ARCHIVE-URLS §3` (2013-05-17) is therefore no longer a
hole on the domain scope for the two closest crawls above it**
(`CC-MAIN-2013-20`, 2013-05-18, one day after the date, and
`CC-MAIN-2013-48`). `CC-MAIN-2021-04` is a 2021 crawl and was in the
indeterminate set for scheduling reasons only; it too is now a readable
absence.

**Host level (exact host `carelink.minimed.eu`).** This is *not* settled by
this pass: `carelink.minimed.eu` with `matchType=host` returned 504 and 502 on
two crawls and 404 on one. The 404 (CC-MAIN-2013-48, seq 11, behind the
google.com control) is a **readable absence for that exact host**. The 504/502
pairs (CC-MAIN-2013-20 and CC-MAIN-2021-04) are query failures on the
query *shape*, not absences — a domain-level 404 already implies the host is
absent (the domain set is the union over hosts), so nothing changes, but the
host-scoped cell itself is not promoted to a verdict. It is recorded here as
indeterminate at the host scope, consistent with area L's rule.

## 4. What remains open (not touched by this pass, by design)

The four other indeterminate crawls from area L §6 are **unchanged** and
still indeterminate: `CC-MAIN-2014-10`, `CC-MAIN-2015-22`,
`CC-MAIN-2021-25`, `CC-MAIN-2022-05`. The three un-reissued ones (asked
once) are the ones this pass closed, as the task scoped it. Their gaps were
partly budget artefacts and are now partly closed. A future pass that wants
the host-scope verdict for `carelink.minimed.eu` on `CC-MAIN-2013-20` and
`CC-MAIN-2021-04` needs either a served crawl or a query shape the index
accepts for that host on that crawl; neither is available inside this pass, and
re-running the same shape a third time is not evidence.

## 5. Reproduction

Harness and ledger committed alongside this file:
- `findings-log/2026-10-13-area-l-early-crawl-reissue/req.sh`
- `findings-log/2026-10-13-area-l-early-crawl-reissue/results.jsonl`
- `findings-log/2026-10-13-area-l-early-crawl-reissue/run.log`
- `findings-log/2026-10-13-area-l-early-crawl-reissue/headers/`
- Response bodies are stored outside the repository (not committed, per policy)
  and are not part of this commit.

Re-derive spacing and record counts from `results.jsonl` and the body mtimes;
do not trust the harness's own span check (retired, per `docs/09` §4).

## References
- [findings-log/2026-10-13-area-l-ipro-hcp/FINDINGS.md] (area L, pass #57) — §6 "seven cells are INDETERMINATE", §5 C2 "`example.com` is not universal".
- [findings-log/2026-10-13-area-m-commoncrawl-cdx/FINDINGS.md] — §2 "a gateway error carries no information", §3a control pairing.
- [docs/09-methodology-and-oracles.md] §4 — oracle rules, 2.5 s floor, mtime validation.
- [docs/11-suggested-research-areas.md] §L — close conditions and the successor addendum.
