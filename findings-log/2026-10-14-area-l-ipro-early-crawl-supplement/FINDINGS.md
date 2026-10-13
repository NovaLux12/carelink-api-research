# Area L — supplemental independent control of three crawls, 2026-10-14

**Status:** supplement to `findings-log/2026-10-13-area-l-7crawl-reissue/`. Scope limited to three
crawls the verifier did not control: `CC-MAIN-2013-48`, `CC-MAIN-2021-04`, `CC-MAIN-2022-05`.
Full accounting, results table and discrepancy record:
`findings-log/2026-10-13-area-l-7crawl-reissue/SUPPLEMENT-2026-10-14-ipro-early-crawl-controls.md`.

## Accounting
- Requests: **12 of a 12 cap**.
- Hosts contacted: `index.commoncrawl.org` only. Requests to any Medtronic host: **0**.
- Method: GET only. Inter-request delay: ≥ 3 s (3.5 s) inside `flock` on
  `.../.loop/host-index.commoncrawl.org.lock`.
- Ledger: `results.jsonl` (12 rows). Bodies stored outside the repository.
- Outcome: two of the three crawls (2013-48, 2021-04) are readable absences on the domain
  scope behind an independent positive control. `CC-MAIN-2022-05` could not be controlled in
  this pass (both candidate controls returned 504); its `404`s are recorded as unresolved, not
  as absences.

[details: same directory `results.jsonl` and `headers/`.]
