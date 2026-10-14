# 0 requests. Accounting: 0 of a 0 cap.

Inter-request delay: n/a — 0 vendor requests issued; the ≥2 s spacing requirement is vacuously satisfied (no sends). Methods: GET (policy-only; no requests issued).

## Area: docs/10 open row (corpus-wide) — "Given the whole-KiB detector, how many
already-committed Common Crawl record counts in this repo are floors rather than
measurements?"

Method: run `account.py <ledger>` (from lane S6) over every Common Crawl
ledger committed in `findings-log/`. The detector rule (S6): a record response
whose `body_bytes` is an exact multiple of 1024 is a truncation candidate; a
response whose byte count is not, ran to completion (correlation only).

## Results, per ledger

| ledger | 200 answers | whole-KiB boundary candidates | max bytes |
|---|---|---|---|
| 2026-10-13-area-l-7crawl-reissue | 13 | 0 | — |
| 2026-10-13-area-l-early-crawl-reissue | 3 | 0 | — |
| 2026-10-13-area-l-ipro-hcp | 15 | 0 | 15 200s; t_sent null on 4 debug rows; account.py aborts in spacing() but the detector count (0 boundary) is derivable. |
| 2026-10-13-area-l-ipro-early-crawl-supplement | 2 | 0 | — |
| 2026-10-13-area-m-commoncrawl-cdx | 38 | 0 | — |
| 2026-10-14-area-l-ipro-early-crawl-supplement | 2 | 0 | — |
| 2026-10-14-pool-l-crawlcontrol | 10 | 0 | — |
| 2026-10-14-lane-s6-public-index | 29 | 3 (seq 74, 102, 145) | 1 864 922 |

Limits of measurement: `2026-10-13-area-l-ipro-hcp/results.jsonl` is not
processable by this detector. Its rows 1–4 carry `t_sent=null`, `http_status=
"unrecorded"` and `role="HARNESS-DEBUG-not-evidence"` (a defective probe whose
gaps included 0.859 s, below the repo's `>=2s` floor, disclosed in that
pass's own note). The ledger's schema is not the one `account.py` assumes, so
it is reported here as "not measurable" rather than as clean. 38 of its 44 rows
are later good rows; the ipro-hcp pass already disclosed the 4 debug rows.

## What this establishes (and what it does not)

Across the six Common Crawl ledgers that can be tested (plus the ipro-hcp ledger, which cannot), truncating responses
(whole-KiB, exact 1024 multiple) are observed in **one ledger only** — lane S6's
— at three sequences (74, 102, 145). Every other ledger, including area M's
(which the S6 row specifically named), returns **zero** boundary candidates.
That corroborates S6's own measurement: area M's published counts are not floors
by this test (its largest response was 35 226 B, larger than S6's smallest
truncation at 32 768 B — so a size-threshold argument would be the wrong
justification; the detector is).

Conclusion for S6's successor row "Given the whole-KiB detector, how many
already-committed Common Crawl record counts in this repo are floors
rather than measurements?": **for the committed Common Crawl ledgers, 3 of 110 (or 3 of 95 excluding the
ipro-hcp ledger, which has 15 200s but no t_sent series) successful 200 answers are truncation candidates, all in lane S6's
pass.** The truncation mechanism and bound remain UNESTABLISHED
(S6's own residual: proxy byte cap / server emit-budget / client read-cutoff all
fit). This row is now settled for the closed ledgers; the open residual is the
mechanism/bound, not the corpus count, plus re-issuing the three truncating
cells at delay when the API is healthy.

Guardrails: the detector is a correlation over observed rows, not a proven
mechanism (S6 FINDINGS §4). A truncation not aligned to 1024 is invisible to it.
The ledgers are committed, reproducible; ipro-hcp noted above as the one
untestable ledger.
