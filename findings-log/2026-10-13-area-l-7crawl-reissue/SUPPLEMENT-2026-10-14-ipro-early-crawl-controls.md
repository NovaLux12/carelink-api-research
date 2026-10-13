# Area L — supplemental independent control, 2026-10-14

**Status:** supplement to `findings-log/2026-10-13-area-l-7crawl-reissue/`. The verifier flagged
three of those seven crawls (`CC-MAIN-2013-48`, `CC-MAIN-2021-04`, `CC-MAIN-2022-05`) as
lacking an independent live control in the verifier's pass. This pass re-runs, for those
three crawls only: one positive control that returned records on that exact crawl, then
`minimed.eu` at `matchType=domain` and `carelink.minimed.eu` at `matchType=host`. GET only.
No Medtronic host is requested — `index.commoncrawl.org` only.

## Accounting

- Requests: **12 of a 12 cap** (self-imposed supplement cap; cap enforced by `req.sh`).
- Hosts contacted: `index.commoncrawl.org` only. Requests to any Medtronic host: **0**.
- Method: GET only. Inter-request delay ≥ 3 s (3.5 s), held inside `flock` on
  `.../.loop/host-index.commoncrawl.org.lock`.
- Raw ledger: `findings-log/2026-10-14-area-l-ipro-early-crawl-supplement/results.jsonl`
  (12 rows). Headers under `.../headers/`, bodies outside the repo.

## Results

| crawl | control (seq) | control result | domain probe (seq) | domain result | host probe (seq) | host result | verdict behind control |
|---|---|---|---|---|---|---|---|
| `CC-MAIN-2013-48` | google.com (seq 1) | 200, 5 records | minimed.eu (seq 2) | **404**, 0 | carelink.minimed.eu (seq 3) | **502**, 0 | **readable absence on domain scope** (control succeeded). Host-scope 502 is a probe failure; the domain `404` subsumes it. |
| `CC-MAIN-2021-04` | commoncrawl.org (seq 4) | 200, 5 records | minimed.eu (seq 5) | **404**, 0 | carelink.minimed.eu (seq 6) | **404**, 0 | **readable absence** (control succeeded; both probes 404). |
| `CC-MAIN-2022-05` | commoncrawl.org (seq 7) | **504**, 0 | minimed.eu (seq 8) | 404, 0 | carelink.minimed.eu (seq 9) | 404, 0 | **uncontrolled in this pass** — see discrepancy. |
| `CC-MAIN-2022-05` | google.com (seq 10) | **504**, 0 | minimed.eu (seq 11) | 404, 0 | carelink.minimed.eu (seq 12) | 404, 0 | **uncontrolled in this pass** — second independent control also failed. |

## Discrepancies against the worker ledger

Both are recorded rather than resolved silently.

1. **`CC-MAIN-2013-48` host probe differs.** Worker ledger seq 16 recorded `404` on
   `carelink.minimed.eu`; this supplement recorded `502` (seq 3) on the same path.
   The worker's *domain* control (`404`, seq 15) is reproduced here (seq 2), so the
   readable-absence verdict on the domain scope is unchanged. The host-scope cell is
   a 502 probe failure in this pass. **No claim that the prior `404` was wrong;**
   the crawl-dependent failure mode documented in
   `findings-log/2026-10-13-area-l-ipro-hcp/FINDINGS.md` (§4) holds.

2. **`CC-MAIN-2022-05` control could not be established in this pass.** Worker
   ledger seq 37 recorded `commoncrawl.org` returning `200`, 5 records on this crawl
   and therefore treated seq 38/39/40 as a readable absence. In this supplement both
   `commoncrawl.org` (seq 7) and `google.com` (seq 10) returned `504` on the same
   crawl, so the `404`s at seq 8/9 and seq 11/12 carry **no** control in this pass
   and are **not** reported as readable absences here. The original reading stands
   as the worker's observation; this supplement records it as **unresolved by
   independent replication** rather than as confirmed. Budget exhausted (12/12); no
   further probe attempted under this supplement's cap.

3. `CC-MAIN-2021-04` **reproduces exactly**: commoncrawl.org control `200`/5, both
   minimed probes `404`. No discrepancy.

## What does not change

- No document's prose is altered by this supplement; area L's close condition still
  requires one member per host/date.
- The earliest `/ipro/hcp/*` capture in the Common Crawl record remains
  `2014-03-10` (`carelink.minimed.eu` `/ipro/hcp/login.jsf` 200, `CC-MAIN-2014-10`),
  per worker seq 19; see the doc update in the same change set.
- `CC-MAIN-2013-48` and `CC-MAIN-2021-04` readable-absence verdicts on the *domain*
  scope are supported by a controlled replication in this supplement (2 of the 3).
  `CC-MAIN-2022-05` is not.
