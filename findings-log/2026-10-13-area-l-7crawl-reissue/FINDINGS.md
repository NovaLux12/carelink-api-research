# Area L — re-issue of the seven indeterminate crawls, 2026-10-13 (claim #79)

**Status:** complete for all seven crawls named in claim #79. Each of the seven now
produces either a record set or a `404 No Captures found` that is confirmed behind
a per-crawl positive control that returned records on that same crawl. The
"indeterminate" column of `findings-log/2026-10-13-area-l-ipro-hcp/FINDINGS.md` §6 is
therefore partly closed: **four of the seven were readable absences** (2013-20,
2013-48, 2021-04, 2022-05) and **three returned records** (2014-10, 2015-22,
2021-25). The earliest `/ipro/hcp/*` capture in this corpus is now
**2014-03-10**, not 2020-05-25.

## Accounting
- Requests: **40 of a 60 cap** (20 unspent).
- Hosts contacted: `index.commoncrawl.org` only. `data.commoncrawl.org` was not
  used. **Number of requests to any Medtronic host: 0.**
- Method: GET only. No POST, no authentication, no token exchange.
- Inter-request delay: ≥ 3 s (3.5 s used), held inside `flock` on
  `…/.loop/host-index.commoncrawl.org.lock`. Host-tagged paths only. Bodies
  stored outside the repository (per §7 hygiene; >1 MiB would fail the check).
- Rows 1–6 of `results.jsonl` used the older `/cdx-server/cdx` path; rows 7–8 used
  the canonical `…-index` path on a sanity probe; rows 9+ used the canonical path
  consistently (`collinfo.json`'s `cdx-api` form). The switch is recorded: the
  older path returned 404/504 on every probe and produced no data. See §5.
- The CDX absence response on this host is `HTTP 404 … Content-Type:
  application/json {"message": "No Captures found for: <url>"}`; projection
  counts a row as a record only when it carries both `url` and `timestamp`, so
  the 404 message is not mis-counted (corrected in-flight on seq 12).

## Controls — per crawl, sent before the minimed probe

Each control returned `200` with records on that exact crawl. A failure or `404`
on any control below is recorded as **nothing** — it is not evidence that the
crawl is unserved, and it was retried until one host returned records.

| crawl | control host (matchType=domain, limit=5) | seq | status | records |
|---|---|---|---|---|
| CC-MAIN-2013-20 | commoncrawl.org | 10 | 200 | 5 |
| CC-MAIN-2013-48 | google.com | 14 | 200 | 5 |
| CC-MAIN-2014-10 | google.com (commoncrawl.org failed, seq 17) | 18 | 200 | 5 |
| CC-MAIN-2015-22 | commoncrawl.org | 23 | 200 | 5 |
| CC-MAIN-2021-04 | commoncrawl.org (medtronic.eu failed, seq 27) | 28 | 200 | 5 |
| CC-MAIN-2021-25 | google.com (commoncrawl.org failed, seq 31) | 32 | 200 | 5 |
| CC-MAIN-2022-05 | commoncrawl.org | 37 | 200 | 5 |

## Probes — minimed.eu, domain and host scope

`matchType=domain` on `minimed.eu` covers every host under it; `matchType=host`
on `carelink.minimed.eu` is the exact-host cross-check. A re-issue that changed
the answer (502/504 → a final answer) is retained as separate ledger rows.

| crawl | domain probe (seq) | answer | records | host probe (seq) | answer | records | /ipro/hcp/ members | verdict behind control |
|---|---|---|---|---|---|---|---|---|
| CC-MAIN-2013-20 | 11 502, 12 404 | **404** | 0 | 13 404 | **404** | 0 | 0 | **readable absence** |
| CC-MAIN-2013-48 | 15 404 | **404** | 0 | 16 404 | **404** | 0 | 0 | **readable absence** |
| CC-MAIN-2014-10 | 19 504, 20 502, 21 200 | **200** | 1 | 22 200 | **200** | 1 | 1 (`/ipro/hcp/login.jsf`, 2014-03-10, status 200) | **capture** |
| CC-MAIN-2015-22 | 24 502, 25 200 | **200** | 1 | 26 200 | **200** | 1 | 0 (`carelink.minimed.eu` `/`, 2015-05-29, no ipro) | capture, root only |
| CC-MAIN-2021-04 | 29 404 | **404** | 0 | 30 404 | **404** | 0 | 0 | **readable absence** |
| CC-MAIN-2021-25 | 33 504, 34 502, 35 200 | **200** | 2 | 36 200 | **200** | 2 | 0 (`/patient/entry.jsp` 403, `/robots.txt` 403) | capture, no ipro |
| CC-MAIN-2022-05 | 38 404 | **404** | 0 | 39 504, 40 404 | **404** (host, behind domain control) | 0 | 0 | **readable absence** (domain scope) |

## Findings

**F1 — The 2013 end resolves on the domain scope: absence, not a hole.**
`CC-MAIN-2013-20` and `CC-MAIN-2013-48` now return `404 No Captures found for: minimed.eu`
behind positive controls on the same crawl (commoncrawl.org / google.com, `200`,
5 records). Under the counting rule of `findings-log/2026-10-13-area-l-ipro-hcp`
§6 ("a cell reads as an absence only if some row for that crawl answered 200"),
these two counts are readable absences, and so is the adjacent
`CC-MAIN-2021-04` (commoncrawl.org control, `404`) and `CC-MAIN-2022-05`
(commoncrawl.org control, domain `404`). **OBSERVED.**

**F2 — The family extends into 2014, nine months before the previously recorded
earliest member.** `CC-MAIN-2014-10` returns one record: `carelink.minimed.eu`
`/ipro/hcp/login.jsf` at 2014-03-10 (HTTP 200), confirmed by `matchType=host`
on the same crawl (`seq 22`, identical record). The prior corpus started the
family at 2020-05-25. The `CC-MAIN-2014-10` crawl was previously one of the seven
"indeterminate" holes. Its status is now a capture, and the 2013/2014 gap in
`ARCHIVE-URLS §3` is closed on the capture side (no `/ipro/hcp/*` in 2013, one
in 2014). **OBSERVED.**

**F3 — `carelink.minimed.eu` root was served in 2015; no `/ipro/hcp/*`.**
`CC-MAIN-2015-22` returns one record (`carelink.minimed.eu` `/`, 2015-05-29
HTTP 200) and no `/ipro/hcp/*` member. **OBSERVED.**

**F4 — The 2021 crawl captured the patient portal and robots, not ipro.**
`CC-MAIN-2021-25` returns two records on `carelink.minimed.eu`:
`/patient/entry.jsp` (403) and `/robots.txt` (403), both 2021-06-12. No
`/ipro/hcp/*`. **OBSERVED.** (This is a path-level observation; no claim is made
about the patient surface itself.)

**F5 — The 2022 end holds; the family is a bounded 2014 → 2020 deployment in
Common Crawl.** With `CC-MAIN-2022-05` now a readable `404` on the domain scope
(commoncrawl.org control, `200`, 5) and `CC-MAIN-2022-21` showing
`carelink.minimed.eu` serving only `/robots.txt` 403 and nothing under `/ipro/hcp/`,
the family does not reach 2022 in this corpus. Reported observation runs
2014-03-10 → 2020-12-02. **OBSERVED.**

**F6 — The 2014 control survived a gateway retry.** `commoncrawl.org` on
`CC-MAIN-2014-10` returned 504 (`seq 17`) before `google.com` returned 200
(`seq 18`). The 504 is a query failure on that host, not a statement about the
crawl, and is recorded as such per `findings-log/2026-10-13-area-l-ipro-hcp`
§5-C2. **OBSERVED.**

## What does not change

- No `/patient/` or `/connect/` data-plane endpoint claim is altered; the 2021
  capture is a portal route and a robots 403 only, which is consistent with the
  prior `docs/08` line about data-plane paths never appearing. **INFERRED.**
- The 2013 host-scope cell for `carelink.minimed.eu` on `CC-MAIN-2013-20` and
  `CC-MAIN-2021-04` is recorded as `404` (readable absence at host scope, since
  the domain `404` subsumes the host); no upgrade is claimed for the host-scope
  verdicts that were already indeterminate. **INFERRED.**
- The three gateway-failed 2013/2014 probes that never produced a `200` remain,
  in their own right, failures of the probe and not of the crawl. The crawl-level
  serving status of those rows is not re-asserted here.

## Reproduction

- Ledger: `findings-log/2026-10-13-area-l-7crawl-reissue/results.jsonl` (40 rows).
- Request script: `…/req.sh` (cap 60, 3.5 s delay inside flock).
- Response headers: `…/headers/XX-*.h`; bodies stored outside the repository
  under `/home/jack/.tmp/l79-bodies/` (not committed, per policy).
- Re-derive record counts and `ipro_hcp` members from `results.jsonl`; the
  projection rules are in `req.sh`.

## References
- [findings-log/2026-10-13-area-l-ipro-hcp/FINDINGS.md] — §6 "seven cells are INDETERMINATE"; §5-C2 one-directional control rule; §3 family enumeration.
- [findings-log/2026-10-13-area-l-early-crawl-reissue/FINDINGS.md] — successor three-crawl re-issue, host-scope indeterminacy.
- [docs/09-methodology-and-oracles.md] §4 — oracle and spacing rules.
- [docs/11-suggested-research-areas.md] §L — close conditions.
