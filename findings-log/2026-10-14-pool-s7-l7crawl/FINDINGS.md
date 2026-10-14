# 19 of a 50 cap. Inter-request delay: ≥2s (2.6 s sleep inside the host lock).
Methods: GET.

## Area: open successor — re-issue of the seven indeterminate early-era Common
Crawl crawls (CC-MAIN-2013-20, -2013-48, -2014-10, -2015-22, -2021-04,
-2021-25, -2022-05) so each carries either a record set or a `404` confirmed
by a positive control on that same crawl.

Scope note: the cell sent here was a domain-level query (`url=minimed.eu`,
matchType=domain), i.e. "does this crawl serve `minimed.eu` at all", not the
ipro/hcp path-filtered query the original letter asked for. The positive
control establishes that the crawl's index is served; the cell tests whether
the domain is present. A domain-level 200 means records exist; a domain-level
404 behind a 200 control means the domain is absent from that crawl. Path-level
ipro verification is left to a smaller targeted re-issue (this pass sets the
serving question, which was the actual blocker named in the L successor).

## Result

| crawl | commoncrawl control | minimed.eu | conclusion |
|---|---|---|---|
| CC-MAIN-2013-20 | 200 (5) | 404 (seq 3, behind control) | domain absent — no `minimed.eu` records |
| CC-MAIN-2013-48 | 200 (5) | 404 (seq 6, behind control) | domain absent |
| CC-MAIN-2014-10 | 200 (5, after one 502) | 200 (1 record) | domain present |
| CC-MAIN-2015-22 | 200 (5) | 200 (1, after one 504) | domain present |
| CC-MAIN-2021-04 | 200 (5) | 404 (seq 14) | domain absent |
| CC-MAIN-2021-25 | 200 (5) | 200 (2 records) | domain present |
| CC-MAIN-2022-05 | 200 (5, after one 504) | 404 (seq 19) | domain absent |

## What this establishes

Four of the seven now have a confirmed `404` behind a 200 positive control on
the same crawl (2013-20, 2013-48, 2021-04, 2022-05): the domain is absent
from those crawls. Three have records (2014-10, 2015-22, 2021-25).

This settles the serving question for all seven — every crawl's index answered
200 on at least one host (commoncrawl.org), so no indeterminate-vs-unserved
hole remains on the commoncrawl host. The L successor's other half — a
path-level (ipro/hcp) audit on the crawls that do carry `minimed.eu` records —
is unchanged; this pass did not touch the path question and does not claim to.

Gateway failures encountered: 5 (504×3, 502×2) and each was retried; all
retries succeeded, so no cell is left as "unretryable failure".

Evidence table

| Claim | Class | Source |
|---|---|---|
| CC-MAIN-2013-20 minimed.eu absent | OBSERVED | seq 1-3 |
| CC-MAIN-2013-48 minimed.eu absent | OBSERVED | seq 4-6 |
| CC-MAIN-2014-10 minimed.eu present (1 record) | OBSERVED | seq 7-9 |
| CC-MAIN-2015-22 minimed.eu present | OBSERVED | seq 10-12 |
| CC-MAIN-2021-04 minimed.eu absent | OBSERVED | seq 13-14 |
| CC-MAIN-2021-25 minimed.eu present (2 records) | OBSERVED | seq 15-16 |
| CC-MAIN-2022-05 minimed.eu absent | OBSERVED | seq 17-19 |
| commoncrawl host served on all 7 | OBSERVED | seq 1,4,8,10,13,15,18 (retried) |

19 rows in results.jsonl = 19 requests claimed.
