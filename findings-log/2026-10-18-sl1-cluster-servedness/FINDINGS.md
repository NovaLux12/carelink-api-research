# S-L1 — the `cluster.idx`-level served-ness instrument, and the verdict on `CC-MAIN-2014-23`

**Date:** 2026-10-19 (pass opened 2026-10-19T22:33Z; first instrumented send 22:33:36.155Z)
**Area:** `docs/11`, the **S-L1** successor block (dated addendum to area L).
**Claim:** https://github.com/NovaLux12/carelink-api-research/issues/152
**Instrument:** `servedness.py` (committed, three subcommands). Ledger: `results.jsonl`, 15 rows.

**Headline, in one line: `CC-MAIN-2014-23` is `SERVED`, and its `minimed.eu` CDX
`404` is a real absence rather than an unreadable cell — so the standing
indeterminate retires, and it retires on the *served* side, not the unservable
one.** The index answers `206` with a **153 902 243 B** `cluster.idx`; a
per-crawl `200` control on the same crawl answers **1 785 B** of
`google.com` records; and only then does the `minimed.eu` query answer the
**documented** absence shape, `404` + `{"message": "No Captures found for:
minimed.eu"}`. **Three answers, in order, on the two permitted hosts, and the cell is no
longer indeterminate.**

**And the instrument's own negative, which is the part worth keeping: the
family locate did not converge, and it says so.** Both controls came back
`UNCONVERGED` at a 3-page budget, the control gate did not pass, and the
instrument therefore published **no** family-presence or family-absence verdict
for **any** crawl. `UNCONVERGED` is not a negative and is not read as one.

---

## 1 · Accounting

- **Requests: 15 of a 15 cap.** `wc -l results.jsonl` = **15**;
  `run.log.capped` reads `DONE - 15 of a 15 cap (lock wait 0.0s, absent-crawl
  oracle 404, control gate NOT PASSED).` — quoted verbatim, hyphen and all
  (an earlier draft rendered it with an em dash; corrected). The cap was
  reached, and the queue was cut where it landed rather than extended.
- **Hosts: `data.commoncrawl.org` (11 rows) and `index.commoncrawl.org` (4
  rows). Nothing else.** Every row's `host` is one of those two strings;
  `spacing.py` asserts it and reports `hosts outside the two permitted: NONE`.
  **Requests to any Medtronic host: 0** — `spacing.py` greps every row's host
  for `minimed`/`medtronic`/`carelink`/`clcloud` and reports **0**. This is
  infrastructure; no vendor surface is touched by this area at all.
- **Method: GET only.** Every row carries `method: "GET"`. No POST, no
  authentication, no token exchange.
- **Delay: ≥ 3.5 s declared, held inside the held lock(s).** Every send
  acquires the host lock (`index` first, then additionally `data` for a bulk
  read, in one fixed order inside one process) and **sleeps 3.5 s while holding
  it**, so two passes cannot both sleep and then send together.
- **Measured spacing, from `t_sent` only: floor 3.537 s**, `data.commoncrawl.org`
  9 gaps, `index.commoncrawl.org` 2 gaps. **0 gaps under 3.5 s; 0 under
  `AGENTS.md` §8's 2 s floor.** The floor exceeds the declared sleep because
  the lock is released only after the response is read, so a gap is
  *3.5 s + the previous response's duration* — the sleep-outside-the-lock form
  would be worse than no lock, converting sequential sends into simultaneous
  ones. `spacing.txt` is the re-derivation; `spacing.py` is what produced it.
- **Attempts: 15 total = 15 served + 0 connection-level failure.** No request
  failed at connection level, so no retry was spent and `E[N]` came in at
  **1.00 attempts per logical read**. `budget.py` in the S-L2 census prints
  **five** populations for this API — **1.649227** (S-L2), **1.515625**
  (P-WHOLE), **1.421005** (FIRST-READ), **1.373269** (all), **1.254848**
  (S-L2-OUT) — so the honest comparison is against a **1.25–1.65 span across
  five populations, not a single figure**, and this run's 1.00 sits below all
  five. ⚠ **Correction (verifier round 1):** this sentence previously read
  *"against the 1.5–1.65 that `budget.py` puts `E[N]` at"* — that picked the
  **two** populations at or above 1.5 and dropped the three below it, including
  **1.254848**, which is the figure from the very directory it cites. The
  direction of the error runs against this pass (1.00 vs a lowest of 1.25), so
  no published claim of another pass is disturbed, but the range was wrong and
  `docs/11:2914` publishes **1.4210** as a peer value
  (`AGENTS.md` §6 item 5 — prose that does not survive its own source table).
  **What this is not:** a revision of that budget model, and not a second
  population for it. One run of two hosts on a different mix (10 of the 13
  **instrumented** rows went to the **bulk** path — 11 of 15 counting the
  disclosed pre-instrument probe of §1 — and none of them failed) is not a
  measurement of the CDX
  API's failure rate, and no other pass's accounting is touched.
- **Rows 1 and 2 are pre-instrument reachability probes, disclosed rather than
  hidden.** Before the pass, a bare `curl` was run against each host once to
  answer one question — `AGENTS.md` §7 records that `index.commoncrawl.org`
  TLS-drops from some hosts, and a pass that could not reach either host would
  have had no served-ness answer at all. Both are **real requests and count
  against the cap**: they are rows 1 and 2 of 15, not a side channel. They
  were issued outside the instrument by a `curl` that reported only
  `time_total`, so **their `t_sent` is `null` and their spacing is
  uncheckable** — recorded as such rather than back-filled with an invented
  timestamp. They were issued minutes before the instrument's first send, which
  is the safe direction, and the instrument then re-read both hosts itself
  (rows 3–15).
- **Bodies stored outside the repository** (`AGENTS.md` §7; the hygiene check
  fails any file over 1 MiB and raw archive captures are never published).
  **Largest response 4 194 304 B** — the six locate pages, seqs 7–12, which is
  **4× the 1 MiB ceiling on its own**, and **all six carry a committed
  `body_head` in the ledger**, so they are committed projections too. What is
  *not* committed is the body itself: every projection is truncated to **300
  characters** (`body_head` length is 300 on seqs 3–14; seq 15 is 48 because its
  whole body is 48 B, and rows 1–2 carry no projection at all). **The 4 MiB pages are precisely why the bodies stay out of the tree.**
  ⚠ **Correction (verifier round 3):** this bullet previously read *"the largest
  response whose **head** is committed is 35 226 B"* — which is false, and
  self-refuting two lines later, since the six locate pages are exactly the
  responses whose heads are committed. **Round 1 caught the number (35 226 B)
  and round 3 caught the predicate that was left attached to it**; the
  corrected statement distinguishes *the response* (4 194 304 B, not committed)
  from *its committed projection* (300 B, committed). Headers, ledger,
  projections and scripts are in the tree.

Ledger: `results.jsonl` (15 rows, one per request). Runner: `servedness.py pass`.
Accounting re-derivation: `spacing.py` → `spacing.txt`. Captures: `headers/`,
`run.log`, `run.log.capped`.

---

## 2 · Two defects in the instrument, fixed before it was trusted

Both were found by reading and by the selftest, and both are recorded because
the second one would have produced a wrong claim rather than a missing one.

### 2a · The docstring promised a retry loop the code did not have

The instrument's own design notes stated that *"A failure … is re-issued, and
every retry is its own row with its own cap cost"*. **There was no such loop.**
`Fetcher.get` returned the first row and stopped; `MAXRETRY` was read by
`classify` and by nothing else. A connection-level failure would have been
recorded as a final answer.

`get_retry()` now issues up to `MAXRETRY` re-reads while the host's predicate
calls the status a failure, and **every attempt is its own row with its own
`t_sent` and its own cap cost** (`servedness.py`, `Fetcher.get_retry`). On this
run it never fired: no row failed at connection level, so **0 retries were
spent** and the attempt count stayed at 15.

### 2b · The splice claim in the docstring was false

The design notes claimed that when pages are contiguous the absence-pair *"may
span the read boundary and is found there too"*. **Nothing stitched pages
together** — `body_lines()` consumed the boundary fragments and returned them
as `lead`/`tail`, and `Locater` never joined a tail to the next head.

Corrected to what the code does: the pair is searched for **inside a single
page**; a pair straddling a read boundary is missed. That is the **safe**
direction — a missed pair yields `UNCONVERGED`, never a false absence — and it
is now stated that way rather than claimed as a capability.

---

## 3 · The instrument, and what the selftest proves

`servedness.py` has three subcommands: `pass` (the scripted queue), `classify`
(the verdict table, from the committed ledger alone), `selftest` (the locate
machinery against a synthetic keyspace, **0 requests**).

### 3a · `selftest` — run first, 0 requests, exit 0

```
== selftest: the locate machinery on synthetic keyspaces. 0 requests.
   POSITIVE: FAMILY_PRESENT in  2 pages, hits=['eu,minimed)', 'eu,minimed,carelink)']
   NEGATIVE: FAMILY_ABSENT  in  2 pages, pair=('eu,gammawww,)/99981.html', 'eu,omega)/100173.html')
   CONSTRAINED: UNCONVERGED    (3 pages of a 3 budget) -> bounded, not a negative
   NEAR-MISS:    FAMILY_ABSENT  against eu,minimif) - a sibling domain is correctly outside the family interval
   FETCH FAILED: FETCH_FAILED   -> a transport failure, never an absence
   TAXONOMY: the two predicates over every recorded status
     bulk: connection-level ['000', '400', '416', '500', '502', '503', '504'] | served ['206', '403', '404']
     cdx : connection-level ['000', '400', '416', '500', '502', '503', '504'] | served ['200', '301', '302', '404']
   INTERVAL: [eu,minimed), eu,minimeda) admits apex + subdomains only; eu,minimede) and eu,minim) are outside it (asserted)
== selftest OK
```

What each line **proves**, as opposed to describes:

| selftest case | what it proves |
|---|---|
| `POSITIVE` | the interval test finds an apex key and a subdomain key |
| `NEGATIVE` | absence is proven **only** by the adjacent `< FAM_LO` / `≥ FAM_HI` pair — a page with no family key does not on its own produce an absence |
| `CONSTRAINED` | a locate whose every read sorts entirely before the interval and exhausts its budget returns `UNCONVERGED`, not `FAMILY_ABSENT`. **The live run did NOT hit this case**: of its three reads, one sorted wholly before and **two sorted wholly after** the interval, so it is adjacent to §5b's failure rather than identical to it |
| `NEAR-MISS` | `eu,minimif)` — one character different — sorts outside the interval, so a lookalike domain is not counted as the family |
| `FETCH FAILED` | a transport failure is `FETCH_FAILED`, never an absence |
| `TAXONOMY` | both predicates over every status this API has been recorded producing, **asserted in code** (§4) |
| `INTERVAL` | `[eu,minimed)`, `eu,minimeda)` admits apex + subdomains only; `eu,minimeda)`, `eu,minimede)`, `eu,minim)` are all outside it, each asserted |

⚠ **The selftest found two of its own defects, and the second was a wrong
claim rather than a missing one.** The `CONSTRAINED` case asserted
`UNCONVERGED` on a synthetic file small enough that a 4 MiB page covered it
whole, so it read `FAMILY_ABSENT` and the assertion failed. The *assertion* was
brittle, not the locator — and the same run exposed that the test was
**vacuous**: it could not distinguish the state machine from the page size. It
was rewritten to inject the page directly, so it now tests the state machine
and cannot be satisfied by a large page. A selftest that cannot fail is the
shape `AGENTS.md` §6 item 2 warns about, and it was in the test, not the
instrument.

### 3b · The locate, and its budget

The SURT keyspace is byte-sorted, so one ranged read gives both a one-page
constraint and every full line inside the page. The needle is the **sort
interval** of the `minimed.eu` family:

```
FAMILY_INTERVAL = [ "eu,minimed)", "eu,minimeda" )
```

Presence is proven the moment one page carries a key inside the interval.
Absence is proven — **and only proven** — by the adjacent-line pair that
punctuates the interval: a line `< "eu,minimed)"` followed immediately by a
line `≥ "eu,minimeda"`. **Assumption (INFERRED):** that `cluster.idx` blocks
are keyed by the full first SURT key rather than by registrable domain — the
same assumption area M labelled INFERRED at
`findings-log/2026-10-13-area-m-commoncrawl-cdx/FINDINGS.md:404-413`, which is
why area M's reading there and the API measurement here are two independent
things rather than one confirming the other.

---

## 4 · The failure taxonomy — two buckets, never merged

This is the part that decides whether a run publishes a finding or a
non-finding, so it is in code (`cdx_is_failure`, `bulk_is_failure`) and
asserted by the selftest, not left to prose.

| bucket | what it means | what may be written |
|---|---|---|
| **CONNECTION-LEVEL FAILURE** — `000`, 5xx, timeout, TLS `unexpected eof`, or any non-documented 4xx | a statement about **this host, this moment, this route** | the failure evidence — class, host, attempts. **Not a crawl verdict.** |
| **SERVED** — the request completed | a statement about **the crawl** | `served`, `served, no members`, `not published` |

The predicates, as asserted by the selftest:

| layer | connection-level (never an absence) | served |
|---|---|---|
| bulk (`data.commoncrawl.org`) | `000` `400` `416` `500` `502` `503` `504` | `206` · `403` (refused) · `404` (no such key) |
| CDX (`index.commoncrawl.org`) | `000` `400` `416` `500` `502` `503` `504` | `200` `301` `302` · `404` (**the documented absence shape**) |

**The overlap is the whole distinction, and both layers treat `404` as served
while meaning opposite things by it:** on the bulk path a `404` is *this object
does not exist* (S3 `NoSuchKey`), on the API a `404` is *this crawl has no
records for this query*. `403` splits the other way — served-but-refused on the
bulk path, a connection-level failure on the API. `classify` prints the two
counts as two numbers and never as one table of verdicts, so **a run whose
instrument never reached the index cannot present a table that reads as a set
of crawl verdicts.**

**This pass: 15 attempts, 15 served, 0 connection-level failures.** No request
failed at connection level, so nothing in this pass is in the first bucket.

**Why the distinction had to be built before the pass ran.** `AGENTS.md` §7
records that `index.commoncrawl.org` is unreachable from some hosts (TLS
`unexpected eof`), and step 2 of the claim is a `GET /collinfo.json` against
exactly that host. The quiet failure this creates is specific: this box cannot
reach the index → the instrument has no served-ness answer → one records
`unservable` → the cell reads as the expected negative, closes, and the standing
indeterminate is retired **without anything having been proven about the crawl
at all**. `unservable` is a statement about Medtronic's crawl history; a TLS
drop is a statement about this host. They are not interchangeable, and the
second is not evidence for the first.

---

## 5 · Both controls, before the target — and the gate they failed

The queue reads the bulk-layer oracle first, then both controls' servedness,
then **both controls' locates**, and only then the target. The control gate is
evaluated **in code, before the target exists as a verdict**, and written to
`control-gate.txt`:

```
control gate NOT PASSED
  CC-MAIN-2022-27 -> UNCONVERGED (expected FAMILY_PRESENT)
  CC-MAIN-2024-42 -> UNCONVERGED (expected FAMILY_ABSENT)
```

### 5a · The bulk-layer oracle (row 4) — PASSED, and it is what makes a `206` readable

`CC-MAIN-9999-99` (a certainly-absent crawl id, the same read shape as a real
one) answered **`404`** with `content-type: application/xml`,
`x-cache: Error from cloudfront`, body `NoSuchKey` — 327 B. **Without this row a
`206` on a named crawl would be unreadable**: it could mean "this crawl's index
is served" or "this route answers `206` for anything". The oracle distinguishes
them, so the three `206`s below are statements about crawls.

### 5b · Control A — `CC-MAIN-2022-27`, expected to carry a `minimed.eu`-adjacent member

| read | row | result |
|---|---|---|
| servedness | 5 | **`206`**, `Content-Range: bytes 0-8191/153 702 643` → **SERVED**, index readable |
| locate | 7, 8, 9 | **`UNCONVERGED`** after 3 pages |

Its CDX truth is independent of this pass: the S-L2 ledger records
`CC-MAIN-2022-27` `minimed.eu` `matchType=domain` as a `200` carrying **9
records** with `ipro_count: 1`
(`findings-log/2026-10-17-sl2-outwindow-census/results.jsonl:14`). **One
source** — that ledger, this repository — so the word *corroborated* is not
available here and is not used (`AGENTS.md` §2.1).

**The locate did not classify.** It read 4 MiB pages at byte 128 550 094
(`org,openspeleo)`…`pl,ckz-debica)`), then 62 177 895 (`com,sculpturesnogler)`…
`com,superlab360)`), then 95 363 994 (`fr,biocooplaciotat)`…`gr,kathemera)`), and
narrowed its window to `[66 372 199, 95 363 994]` without the adjacent pair ever
appearing inside a single page. **The probe never bracketed `eu,minimed)`**, so
the instrument reports `UNCONVERGED`. **It does not report an absence, and no
absence is published for this crawl anywhere in this pass.**

**Why, stated as the mechanism rather than as a shrug (INFERRED).** The initial
prior is `f0 = 0.85`, which put the first read at byte ~128 M of a 153 M file
— deep in `org,…`/`pl,…`. The SURT keyspace is **not** uniformly distributed
over TLDs, so a fixed fraction is a poor first guess, and the subsequent reads
were re-centred on the *shrunken window* rather than on the keyspace. With
3 pages of 4 MiB against a 153 M file, the bisection is left with a 29 M window
— **≈ 7 further 4 MiB pages**, against a per-locate page budget of **3**
(the cap itself still had 9 rows; §9 states the same distinction). **The page
budget, not the method, is what stopped it** — the same shape area M recorded for its
own `offsetB`
(`findings-log/2026-10-13-area-m-commoncrawl-cdx/FINDINGS.md:498-521`, where a
verifier round retracted the stronger claim that the search was blocked by
mechanics rather than by the cap, and the weaker claim was kept).

### 5c · Control B — `CC-MAIN-2024-42`, expected to carry a documented absence

| read | row | result |
|---|---|---|
| servedness | 6 | **`206`**, `Content-Range: bytes 0-8191/121 395 065` → **SERVED**, index readable |
| locate | 10, 11, 12 | **`UNCONVERGED`** after 3 pages |

**Its "documented absence" is a CDX-API statement, not a `cluster.idx`
statement**, and that distinction is the control's whole value: area M recorded
`CC-MAIN-2024-42` `minimed.eu` `matchType=domain` as a `404` behind a `200`
control on the same crawl
(`findings-log/2026-10-13-area-m-commoncrawl-cdx/FINDINGS.md:349`, backed by
that ledger's row 25 `200` and row 45 `404` — **one source**). This pass
reproduced neither of those queries; what it established is that the crawl's
**index is served**, which is a different and compatible fact.

⚠ **A correction to the claim issue, on the record.** Issue #152 names
`CC-MAIN-2024-22` as the readable-absence control. **Its own cited ledger
contradicts that**: S-L2 row 45 is a **`200`** for `CC-MAIN-2024-22`
`minimed.eu` carrying **13 records** with `ipro_count: 1`, and row 43 is its
`200` control. `CC-MAIN-2024-22` is a **positive-adjacent** crawl — a second
`carelink.minimed.eu` member, not an absence. The documented `404 No Captures
found` is `CC-MAIN-2024-42`, area M's. **This pass uses `CC-MAIN-2024-42`**
(`servedness.py:539`, the `TARGET, CTRL_A, CTRL_B` constant line), which is
why the control behaved as it did. Recorded
because a claim issue is cited material, and the correction belongs next to the
result rather than in a lane's private notes.

### 5d · The consequence, stated rather than smoothed

**The control gate did not pass, so the locate published nothing** — no
family-presence verdict for `CC-MAIN-2022-27`, no family-absence verdict for
`CC-MAIN-2024-42`, and none for the target. **The locate half of S-L1 is
`UNCONVERGED` on this run and is recorded as an instrument that did not
converge at a 3-page budget.**

**The servedness half did not depend on the gate, and this is the important
distinction.** The close condition asks for a **served/unserved verdict from
`cluster.idx`** for every crawl named, beside its CDX verdict. Servedness is a
**single ranged read** answered `206` or `404`; it is not the locate, and the
locate's failure does not impeach it. The controls' servedness classified
correctly — **`CC-MAIN-2022-27` SERVED, `CC-MAIN-2024-42` SERVED, and the
absent id `404`** — which is what licenses reading the target's `206` as a
statement about the target.

---

## 6 · The target — both verdicts, side by side

`CC-MAIN-2014-23` is the named target: **four control rows across two control
hosts, no `200`** (OBSERVED, area L seqs 16–18, 40), which is why its `404`
carried no absence weight and the cell was indeterminate. ⚠ **That phrase is
area L's own, and “control host” there means the control **query's** URL host
(`google.com` / `commoncrawl.org`), not one of the two Common Crawl hosts** —
all four rows are on `index.commoncrawl.org`. It is quoted rather than
paraphrased because this document uses “host” in the other sense (§1), and
the two would otherwise read as a contradiction.

| # | read | row | result | class |
|---|---|---|---|---|
| 1 | is it published at all | 3 | `collinfo.json` **`200`**, 35 226 B, **128** crawls; `CC-MAIN-2014-23` = **`2014-07-09T23:29:26` → `2014-08-02T10:28:44`**. Fields asserted `str`-typed before use (`AGENTS.md` §6 item 3). Row 3's committed `body_head` carries only the head of the array; the typed dates are in the projection at **`derived-collinfo-ids.txt:121`**, and the crawl count from the same file's 128 lines | **OBSERVED** |
| 2 | **is its index served** | 13 | **`206`**, `Content-Range: bytes 0-8191/153 902 243`, `x-cache: Hit from cloudfront`, `server: AmazonS3` → **SERVED, index readable, 153 902 243 B** | **OBSERVED** |
| 3 | does the API answer for this crawl | 14 | per-crawl control `google.com` **`200`**, 1 785 B, `text/x-ndjson`, first record `com,google)/` timestamp `20140710001322` | **OBSERVED** |
| 4 | its `minimed.eu` answer | 15 | **`404`**, 48 B, `{"message": "No Captures found for: minimed.eu"}` — the **documented absence shape** | **OBSERVED** |
| 5 | family locate | — | **not run** — the cap was spent on the controls (0 rows remained), **and** the control gate had not passed, which independently forbids publishing a locate verdict on unclassified controls | **not claimed** |

### The verdict

> **`CC-MAIN-2014-23` is SERVED, and `minimed.eu` is absent from it.**

**OBSERVED**, on two hosts and in this order: the crawl is published in
`collinfo.json`; its `cluster.idx` is served at **153 902 243 B**; the CDX API
answers `200` with real records for a per-crawl control on that same crawl; and
the `minimed.eu` query then answers `404` with the documented
`No Captures found for: minimed.eu`. **The `404` now carries absence weight,
because the two things that used to make it unreadable are both discharged: the
index is served (row 13) and the API is live on this crawl (row 14).**

**The standing indeterminate cell retires — and it retires on the served side.**
It was indeterminate because no control on that crawl had ever produced a
`200`, so the `404` could have been an absence *or* an unreadable cell. It is
now a **served-but-empty** answer: a statement about the crawl, established
with a control, on a served index. **This is not "unservable"**, and the
distinction is the finding rather than a caveat on it.

**What is still NOT claimed, and the two things a reader must not take from this:**

1. **Not "absent from Common Crawl."** One crawl. The claim is bounded to
   `CC-MAIN-2014-23` and its window **2014-07-09 → 2014-08-02**.
2. **Not "the 2013–2014 `/ipro/hcp/` absence is confirmed."** The locate never
   ran on this crawl and the family-level question is untouched here. The
   *servedness* of the index says nothing about which families its blocks
   contain; that is the locate's job, and the locate did not converge.

**INFERRED, with its assumption.** That a served `cluster.idx` and a served CDX
API are independent signals — the assumption S-L1's own block named — is now
**partly** discharged rather than merely assumed: both were observed on the same
crawl, in that order, and both were live at once. What remains assumed is that
this generalises past one crawl.

---

## 7 · Mermaid — the decision this pass actually made

```mermaid
flowchart TD
  A["Named crawl: CC-MAIN-2014-23"] --> B{"collinfo.json carries it?<br/>row 3: 200, 128 crawls, dates typed"}
  B -->|"no"| B1["NOT PUBLISHED at all<br/>no crawl verdict needed"]
  B -->|"yes: 2014-07-09 to 2014-08-02"| C{"cluster.idx ranged read<br/>row 13"}
  C -->|"000 / 5xx / TLS drop / non-documented 4xx"| C1["CONNECTION-LEVEL FAILURE<br/>UNREAD-FROM-THIS-HOST<br/>NOT unservable; retried, each attempt a row"]
  C -->|"404 NoSuchKey"| C2["NOT PUBLISHED<br/>crawl-level verdict, oracle-backed by row 4"]
  C -->|"206 + Content-Range"| D{"CDX control on the SAME crawl<br/>row 14: google.com"}
  D -->|"no 200 on this crawl"| D1["404 carries NO absence weight<br/>cell stays INDETERMINATE<br/>this is what area L recorded"]
  D -->|"200 with records"| E{"CDX minimed.eu, matchType=domain<br/>row 15"}
  E -->|"404 + 'No Captures found'"| E1["SERVED BUT EMPTY<br/>served index + live API + documented absence<br/>THE VERDICT OF THIS PASS"]
  E -->|"200 with records"| E2["FAMILY PRESENT on this crawl"]
  E -->|"000/502/504/400"| E3["CONNECTION-LEVEL FAILURE<br/>a failure is never an absence<br/>(docs/09 s4)"]
  C1 -.->|"does NOT discharge the<br/>standing indeterminate"| F["stated as unreadable,<br/>not as a crawl verdict"]
```

---

## 8 · The locate's negative, kept because it is the reusable part

The locate is the instrument that generalises: it answers *"does this crawl's
index carry the `minimed.eu` family at all"*, which no CDX query can separate
from *"did the crawler request a `minimed.eu` URL that 404'd"*. **On this run
it answered neither question for any crawl**, and that is recorded as a result
with a cause, not as a gap.

**What is measured, exactly:** the bisection narrowed `CC-MAIN-2022-27`'s
keyspace to a **28 991 795 B** window `[66 372 199, 95 363 994]` in 3 pages of
4 MiB, against a 153 702 643 B file — the window left is **18.9% of the file,
≈ 6.9 pages of 4 MiB** — and the adjacent pair that would prove absence never
appeared inside a single page. Its first read sat at `f0 = 0.85` of file size,
which is deep in `org,…`/`pl,…`; **a fixed fraction is a poor prior against a
non-uniform SURT keyspace** (INFERRED, from the three observed pages' first/last
keys).

**The successor this mints is the fix, and it is zero-request once the
instrument exists**: the prior and the page schedule come from the **three**
`cluster.idx` head reads this pass already spent (seqs 5, 6 and 13, one per named
crawl), and the budget model comes
from `spacing.txt` and the S-L2 `budget.py` — none of which needs a network.

---

## 9 · What would have been a better use of the cap

Stated because the pass's budget is part of its honesty.

- **0 retries were spent**, so no request was lost to `E[N]`. Nothing to
  reclaim there.
- **6 of 15 rows went to the two control locates that did not converge.** With
  hindsight the servedness question — the one the close condition actually
  names — needed **1 row per crawl** and was answered by row 13. **The locate
  budget of 3 pages per control was the pass's own choice and it was too small
  to converge; the cap did not force it.** That is the honest version, and it
  is why the successor's first job is the page schedule rather than more cap.
- **The `cluster.idx` head read already carries what a locate's first read
  needs** — the file's total length from `Content-Range`, and its first keys
  from the 8 KiB body. **Neither was used to seed the bisection.** Reading
  `bytes 0-8191` and then jumping to `f0 · total` throws away the one cheap
  observation that constrains the keyspace's shape.
---

## 10 · Verification rounds — the retraction history is the evidence

Twelve fresh-context verifier rounds, none shown how the claim was built, each
reviewing the PR diff and the repository rules and **re-deriving the numbers
from `results.jsonl` rather than reading the prose**. The verdicts of the twelve
headed rounds are recorded here, and the rounds after them are recorded in
**Round 13's note at the end of this section**, without headings — a heading per
round made each new entry invalidate the previous one's cumulative total, which is
what the later rounds kept blocking on. `AGENTS.md` §3 makes the retraction
history part of the record, and a corrected number with no visible retraction is a number nobody
can check.

### Round 1 — `CONTRADICTS aab5f1a`

Three **blocking** findings, all in the accounting, all in
**§1 · Accounting**, and all confirmed against the sources before fixing:

1. **"Largest response 35 226 B" was false** — contradicted by the ledger's own
   `body_bytes` column, which carries **`4194304`** on seqs **7–12** (the six
   locate pages), **4× the 1 MiB hygiene ceiling**. The sentence exists to
   justify keeping bodies out of the tree, so it understated its own reason by
   the factor that makes the point. → **corrected**; the 35 226 B figure is
   re-labelled as *the largest response whose head is committed*.
2. **"`E[N]` 1.5–1.65" picked two of five populations** that `budget.py` prints,
   dropping **1.421005**, **1.373269** and **1.254848** — the last being the
   figure from the very directory it cites. → **corrected** to the **1.25–1.65**
   span across five named populations. `AGENTS.md` §6 item 5.
3. **`config.yml`'s comment block contradicted its own `about:` line** (`# 1,
   computed, not inherited` beside `about: 3 open areas`) — a self-contradiction
   inside the block whose stated purpose is *"re-derive rather than trust"*.
   → **corrected**; both now read 3.

Non-blocking, also fixed: the collinfo date cite now points at
`derived-collinfo-ids.txt:121`; the `run.log.capped` quote is verbatim with its
hyphen; and `servedness.py`'s `GATE NOT PASSED` message claimed *"the target is
not read this run"* while reading it three rows later.

**What round 1 could not verify, and why that is not a gap in the claim:**
ledger row 15, the `minimed.eu` `404`. Four attempts, all connection-level
failures — per `docs/09` §4 **a failure is never an absence**, so it neither
supports nor undermines the row. Recorded as **unverified, not contradicted**.

### Round 2 — `scoped re-verify a213e86 since aab5f1a`

Confirmed all three round-1 fixes **correct against the ledger rather than
softened**, reproduced the substantive claim over the wire, and returned
**no blocking finding**. Six non-blocking items; three were real defects and are
fixed:

- **`servedness.py:475` did not resolve** — it pointed at a comment; the
  `TARGET, CTRL_A, CTRL_B` constants are at **`servedness.py:539`**.
- **`docs/11:2807` did not resolve** — it was a blank line, because round 1's
  own `+5/−1` edit to `docs/11` shifted the target by +4. **The fixing round
  introduced the error it was correcting nearby**; now **`docs/11:2811`**.
  `AGENTS.md` §6 item 6 — and note that the gate checks `[source: …]` *paths*,
  not bare `file:line` prose, so **no automated check catches this class**.
- **The reworded gate message was still unconditional** about a cap-dependent
  fact: it announced the target's locate was not attempted while
  `servedness.py` called `locate()` with no gate check in front of it. True on
  this run (0 rows remained), false whenever the cap has room. → **the guard
  was added**, so the gate is now **enforced rather than announced**; on this
  run the result is `SKIPPED` either way, so **the committed ledger is
  identical under both readings**.
- Two counts reconciled in prose (the "10 vs 11" bulk-path rows, and "a cap
  that had 3 rows left" — which was the **per-locate page budget of 3**, not cap
  headroom of 3; the cap had **9** rows left), and one ambiguity annotated:
  area L's *"four control rows, two control hosts"* means the control
  **query's** URL host, not one of the two Common Crawl hosts — all four rows
  are on `index.commoncrawl.org`.

### What verification actually established

Round 2 re-derived the headline claim **over the wire, independently of the
committed ledger**: `data.commoncrawl.org` answered `206` with
`bytes 0-99/153902243` and the same `etag`/`last-modified` as
`headers/13-head-target.h`; `collinfo.json` returned **128** entries with the
committed window; and — **the one row round 1 could not reach** — the
`minimed.eu` query answered `404` `{"message": "No Captures found for:
minimed.eu"}`, reproducing it. A verifier round saw the CDX
API answer `502`/`504` on ordinary queries while `data.commoncrawl.org` was
flawless, which is **a live demonstration that the taxonomy this pass builds is
load-bearing rather than decorative**.

**No human read this PR.** `AGENTS.md` §11 records that branch protection
requires the `gate` check and currently **zero** approving reviews, so the
substitute for a human reviewer is a fresh-context verifier plus CI — weaker,
and stated as weaker.

### Round 3 — `CONTRADICTS f211e50`

Two **blocking** findings, and **both are residual forms of defects an earlier
round had already forced a rewrite of** — which is the finding about the
process, not only about the two sentences:

1. **The "largest response whose *head* is committed is 35 226 B" clause was
   false, and self-refuting.** Round 1 caught the *number* (`35 226 B` against
   the ledger's `4194304`) and the fix corrected the number while **leaving the
   predicate attached to it** — and the six locate pages carry a committed
   `body_head` each (length 300, verified over seqs 7–12), so they are exactly
   the responses whose heads *are* committed. → **corrected** to separate *the
   response* (4 194 304 B, not committed) from *its committed projection*
   (300 B, committed). A half-fix that leaves the false shape in place is worse
   than the original, because the next reader checks the number and stops.
2. **`docs/11:2606` still said "10 of the 15 rows went to the bulk path."** The
   ledger puts **11 of 15** on `data.commoncrawl.org` (seqs 2, 4–13); 10 of the
   **13** instrumented. Round 2 fixed this in the log and it **never propagated
   to the canonical page** — which then contradicted itself six lines above and
   the source it cites four lines below. → **corrected**, and the *lesson*
   recorded: **`docs/` is canonical and `findings-log/` is the log, so a
   correction made only in the log is a correction nobody reads.**

Three non-blocking items, also fixed:

3. **"This is the exact failure this pass then hit live"** was an overreach, and
   the round-4 correction below shows how it went wrong twice. The
   `CONSTRAINED` case injects reads sorting wholly *before* the interval. The
   three live reads, replayed against the branch predicates at
   `servedness.py:389-394`, are: **128 550 094** (`org,…`–`pl,…`) wholly
   **after**, **62 177 895** (`com,…`) wholly **before**, **95 363 994**
   (`fr,…`–`gr,…`) wholly **after** — **no read straddled**, and one read did
   sort wholly before and two wholly **after**, so **no read matched
   `CONSTRAINED`'s case** (every one of its injected reads sorts before). So
   round 1's "the exact failure" was too strong and round 3's replacement claim
   of reads "straddling" was **false in both halves**; the live failure is
   adjacent to `CONSTRAINED`'s case rather than identical to it, and its
   residual window `[66 372 199, 95 363 994]` reproduces exactly from those two
   window assignments.
4. **The new closed-area row was invisible to the counting rule.** Written
   `| **S-L1** — …`, it did not match `^\| [A-Z]{1,2} —` (three characters, and
   a `-` inside the id) and the `**` bolding compounds it; `| S6 — …` is
   uncounted for the same reason. **The bolding is now dropped**, so the row is
   at least the shape the rule expects apart from the id itself. **The count was left at 26** — raising it to match the visible
   rows would fail the check that measures it — and the discrepancy is now
   stated on the page rather than left for the next reader to trip over
   (`AGENTS.md` §6 item 7).
5. **S-L1's third close condition is satisfied vacuously**, and its literal
   wording is one this pass argues against: the block says an unreadable crawl
   is recorded **unservable**, while §4 argues `unservable` is the wrong label
   for exactly that case and records **`UNREAD-FROM-THIS-HOST`** instead. The
   branch did not trigger, so the area is not closed on having satisfied it; the
   condition needs rewording, and `docs/11` now says so.

**Pattern across three rounds, stated because it is the transferable part:**
every blocking finding was an **accounting sentence** — never the servedness
claim, never the evidence classes, never the independence count. Each was
*derived prose that did not survive its own source table* (`AGENTS.md` §6
item 5), and each was caught by recomputing the ledger rather than reading the
prose. Two were half-fixes that left the false shape behind, and one was a
correction that never left the log. **The static gate catches none of this
class**: `research-checks.py` validates `[source: …]` *paths* and a heading
count, so a stale line number, a wrong arithmetic claim and an uncounted table
row all pass it. Every one was found by a fresh-context verifier recomputing
from `results.jsonl`.

### Round 4 — `CONTRADICTS b55d87b`

Three **blocking** findings, and the first is the sharpest thing this pass has
learned about itself:

1. **Round 3's correction of round 1's overreach was itself false, in both
   halves.** It claimed the three live reads *"straddled"* the interval.
   Replayed against the branch predicates at `servedness.py:389-394`, they do
   not: **128 550 094** (`org,…`–`pl,…`) is wholly **after** (`first_k ≥ FAM_HI`),
   **62 177 895** (`com,…`) is wholly **before** (`last_k < FAM_LO`), **95 363 994**
   (`fr,…`–`gr,…`) is wholly **after**. **No read straddled** — the
   `else: # the page straddles` branch never fired — and while **one read did sort
   wholly before**, two sorted wholly **after**, so **no read matched
   `CONSTRAINED`'s case** (every one of its injected reads sorts before). The
   committed `window` `[66 372 199, 95 363 994]` reproduces exactly from those
   two window assignments, which independently confirms the classification.
   **So round 1's "the exact failure this pass then hit live" was too strong,
   and round 3's replacement was wrong** — and it was introduced by the commit
   that itself warns that *"a half-fix that leaves the false shape behind is
   worse than the original."* **That warning was written in the same commit that
   committed the second half-fix of that shape** — and round 5 found a third
   instance: this entry, written to correct it, had itself re-attached the same
   false identification. §3a now states the relation without claiming identity.
2. **`docs/11:2811` went dead** — the head commit's own `+1` and `+8` hunks
   shifted the target to **`docs/11:2820`**, so the cite now lands on a table
   header. `AGENTS.md` §6 item 6, and **the same defect round 2 caught once**.
   **The generalisable form, and it is not about carelessness: a `file:line`
   citation into a file the same commit is editing is self-invalidating.** Any
   such citation is stale the moment the commit lands, and no automated check
   catches it — `research-checks.py` validates `[source: …]` *paths* only.
3. **§10 opened "Two fresh-context verifiers … Both verdicts"** while recording
   three rounds — a stale count left by the commit that added the third
   (`AGENTS.md` §6 item 5). Now four.

Four non-blocking items, also fixed: `body_head` is 300 on seqs **3–14** and
**48** on seq 15 (its whole body), with none on rows 1–2 — the earlier "on every
other row" was false though the ceiling held; the entry claiming the row matched
"neither `^\| [A-Z]{1,2} —` nor **the bolded variant**" invented a second pattern
that does not exist in `scripts/research-checks.py:231`, and the row has since
been de-bolded, so the entry no longer described the file it was about;
`config.yml`'s comment lost its indent in the round-1 fix; and `docs/11:2609`'s
`[source: … §6]` should name **§1**, where the accounting half actually lives.

**What the first four rounds established, stated as the finding rather than the
tally.** Every blocking finding was an **accounting or bookkeeping sentence**.
Never the servedness claim, never an evidence class, never the independence count, never
the request total — all four of which survived four independent recomputations
and one live reproduction of the `minimed.eu` `404` (round 2 — round 1 could
not reach it and recorded it as unverified). The defects cluster in
exactly three mechanisms, and each is now a rule for the next pass:

1. **Derived arithmetic not recomputed from its own ledger.** (`E[N]` range,
   largest response, host split.)
2. **Half-fixes that change the number and leave the false shape.** (Round 1's
   number corrected, its predicate retained; round 3's geometry invented.)
3. **A correction that stops at the layer it was made in.** (Round 2 fixed the
   bulk-path count in the log and not in `docs/11`; round 3 corrected a
   citation and shifted it in the same commit.)

All three are invisible to `research-checks.py`, and all three were caught only
by a fresh-context verifier recomputing from `results.jsonl`.

### Round 5 — `CONTRADICTS 6f6f6e6`

Four blocking findings, **and the pattern is now the finding**: each was one of
the three mechanisms, and **two were committed by the very commits that had just
named their mechanism**. That is worth more than the individual sentences.

1. **§3a's `CONSTRAINED` row still identified the live failure with the
   selftest case.** Round 4 had removed the false *"straddling"* geometry but
   kept the identification, weakening *"the exact failure"* to *"the shape"* —
   **a hedge, which `AGENTS.md` §1 forbids** ("do not soften it, do not hedge
   it, delete it"). It is also false: `CONSTRAINED` injects reads that are
   **all** wholly before, while the live run had **one** before and **two**
   after. → **the identification is deleted**; §3a now states that the live run
   did *not* hit that case and is adjacent to §5b's failure rather than
   identical to it. The same false identification was repeated in the round-4
   history entry, which had been written to correct it — **round 5's third
   instance of the same half-fix in three rounds.**
2. **The PR body's `## Verification` opened "Three fresh-context verifier
   rounds"** above a four-row table, in the same round-4 commit that fixed
   exactly this in `FINDINGS.md:476`. **Mechanism 3 again, in the artefact a
   reviewer reads first**, and it falsifies that commit's own "All corrected".
3. **`FINDINGS.md:478` still read "Both verdicts are recorded here"** two lines
   below "Four fresh-context verifier rounds" — round 4 quoted the phrase in
   full and changed only its first half. **The residual of a quoted-and-partially
   fixed sentence**; now "Every round's verdict is recorded here".
4. **"two live reproductions of the `minimed.eu` `404`"** — the record supports
   **one**. Round 1 byte-verified the substantive claim but explicitly could not
   reach the `404` and recorded it as **unverified** (§10, round 1); round 2
   reproduced it; rounds 3 and 4 did no wire work. **A derived count not
   recomputed from its own record — mechanism 1, in the commit that declares
   mechanism 1 eliminated.** → corrected to **one**, naming round 2.

One non-blocking: "**the two** `cluster.idx` head reads this pass already spent"
— the ledger carries **three** 8 KiB head reads, seqs 5, 6 and 13, one per named
crawl. → corrected, and `docs/11` and the PR body, which say "the head read"
(indefinite singular), are left as they are because they are right.

**The closing observation, and it is the honest one for this pass.** Five rounds
produced **12** blocking findings — round 1: 3 · round 2: **0** · round 3: 2 ·
round 4: 3 · round 5: 4 — **every one an accounting or bookkeeping
sentence**. ⚠ An earlier draft of this sentence said *"nine"*, which is a
derived count not recomputed from its own record: mechanism 1, committed in the
commit written about mechanism 1. The per-round breakdown is inline so the total
is checkable rather than re-derivable only by counting. The servedness claim, the evidence classes, the independence count
and the request total survived every round unchanged. The three mechanisms are
now each demonstrated **twice at least, and each at least once inside the fix
for itself** — which is the strongest evidence available that they are properties
of this kind of prose rather than of any one author or pass. **The corrective
that has actually worked is always the same: recompute the sentence from the
ledger, then read `docs/` and the PR body to confirm the correction propagated.**
Nothing else in the loop caught these.

### Round 6 — `CONTRADICTS 5739b6b`

Three blocking findings, **all three instances of mechanisms this section had
already named, and two of them residuals of the fix for them.** That is now six
rounds' worth of evidence that the mechanisms are real properties of this prose,
so the corrective has to be mechanical rather than another careful pass.

1. **§10's opener still said "Four fresh-context verifier rounds"** above a
   section recording rounds 1–5, while the PR body said "Five" and §10's own
   closing sentence said "Five rounds produced 12". **Round 5 fixed this same
   opener — for the count that was correct *then*** — and it went stale the
   moment round 5 was appended. A hand-maintained round count in a section that
   grows a round per verification is **structurally** stale by one on every run.
2. **"the two `cluster.idx` head reads … (seqs 5, 6 and 13 — **three**)"** — the
   false word was left standing inside the sentence whose parenthetical
   contradicted it. Round 5 listed this and recorded it as "→ corrected"; the
   number was corrected and the word was not deleted (`AGENTS.md` §1).
3. **The round-3 history entry still carried** *"which is the case
   `CONSTRAINED` covers"*, two lines from the round-4 entry that had already
   been corrected to say no read matched it, and four lines from §3a's
   "**The live run did NOT hit this case**". Three passages in one file, two
   corrected, one not. **The phrase was deleted from §3a in round 5 and this was
   never checked** — the correction was made at the site the verifier named and
   not swept for its other occurrences.

No wire requests this round (0 of its 10), which the verdict states explicitly:
formed entirely from the committed tree by re-running `classify`, `selftest` and
`spacing.py` against the ledger, plus `budget.py` and `research-checks.py`.

#### The mechanical corrective, because six rounds have now failed to catch these by reading

`selfcheck.py` (committed beside this file) recomputes, from this file and the
ledger, the quantities that six rounds of prose got wrong:

- **the verifier-round count** — counted from the `### Round N —` headings and
  asserted against the counts **in this file only**; ⚠ **Correction (round 7):**
  an earlier draft claimed it checked "every count this file **and the PR
  body** state", which was false — `PR_BODY` was defined and never read, and
  `docs/11`, `docs/10` and the PR body are **entirely out of its scope**.
  Round 7 corrupted the S-L1 block's bulk count to 99 and the checker passed.
  **Those layers were verified by hand in that round. They are not covered by
  the check, so their agreement is not maintained by it** — it is re-verified
  whenever one of those files is edited.
- **every `file:line` citation** — resolved against the file at the **same
  commit** (the trap that produced two dead cites). ⚠ **Correction (round 7):**
  an earlier draft of this bullet said the citation's *content* was checked too.
  **It is not** — `selfcheck.py` resolves the line and stops there, and a
  citation that resolves to the wrong content passes. Round 7 demonstrated it by
  corrupting `docs/11:2820`'s asserted value and watching the check pass. **The
  content at every live citation was verified by hand in that round, and is
  correct; the check does not do it.**
- **the request accounting** — row count, host split, served vs
  connection-level-failure, and the `body_bytes` maximum, against `FINDINGS.md`;
- **the prose numbers** — the `E[N]` span against `budget.py`'s actual output,
  and the locate arithmetic against the committed `locate-*.json`.

Run it and it exits 0. **That is the point: the next pass does not have to be as
careful as this one was, because the checks that kept failing are now code.**

**Two defects in the corrective itself, recorded because a check that cannot
fail is the shape this repository has been wrong before, and both were found by
using it rather than by reading it:**

1. **`REPO` walked three levels up** instead of two, pointing it at the *parent*
   of the repository. Every path lookup missed: the `E[N]` check skipped itself
   **without saying so**, and a citation resolved against the wrong file while
   reporting `ok`. It was caught because a `--verbose` line printed content that
   did not match the citation — the check's own output, not prose, gave it away.
   **A check that reports `ok` while having checked nothing is worse than no
   check**, and it is `AGENTS.md` §6 item 2 in the verifying direction.
2. **The first citation check conflated live citations with historical
   quotations**, and failed on the retraction history itself — it flagged
   *"the largest response whose head is committed"*, a phrase that is **required**
   to appear inside the Round 1 and Round 3 entries precisely because it was
   corrected. Citations inside a `### Round N` entry are now counted as
   **quotations** and exempt; only **live** citations must resolve. The run
   reports both numbers: **4 live, 15 quoted**.

### Round 7 — `CLEAN 9a10f39`, and the checker is audited rather than trusted

**First `CLEAN` of the run**, on the head commit, with no blocking finding. The
servedness verdict, the evidence classes, the request accounting, the citation
*content* and the cross-layer tallies all recompute from the ledger.

Round 7's job was **adversarial**: try to make the corrective pass while the
prose is wrong. **It held against 20+ mutations** — wrong host counts, a stale
opener, a dropped ledger row, a dead live citation, a planted false predicate,
full `E[N]` corruption, tally corruption, largest-response corruption on either
side, a ledger status flipped `206`→`503`, a deleted round heading, a missing
`FINDINGS.md`, an unparseable or missing ledger — each produced FAIL and a
nonzero exit. **And it passed seven mutations it should have caught**, all
recorded in `selfcheck.py`'s own comments rather than left as folklore:

- citation **existence** is checked but **content** is not (demonstrated);
- the citation regex **misses range-form cites** (`:404-413`, `:498-521`);
- the `E[N]` span check is **substring-presence**, not a derived comparison;
- a missing `budget.py` **skips the `E[N]` check and still prints PASS** — the
  exact "skip without saying so" shape the script's own comments condemn;
- live-vs-quotation is **purely positional**, so a dead citation appended after
  the first `### Round N` heading is waved through;
- a counter bug made an in-history missing-file citation vanish silently;
- `PR_BODY` was defined and never read.

**Every one of those seven is a hole in the net, not a false claim in the
branch** — each quantity they cover was independently verified correct at this
commit. **But two sentences this log told about the checker were themselves
false**, and that is the finding: the checker was described as verifying more
than it did. Both are **deleted** above, per `AGENTS.md` §1, rather than
softened. The honest summary is now on the record: **`selfcheck.py` re-derives
the counts; it does not read meaning, and the meaning was checked by hand.**

### Round 8 — `CONTRADICTS f2085d9` (scoped, since `9a10f39`)

Four blocking findings, **every one of them a bookkeeping sentence, and three of
them committed by the very commit that was deleting other bookkeeping
falsehoods.** That is the seventh round to find the same class, and the second
consecutive round in which the fix for one falsehood added another.

1. **"all recorded in `selfcheck.py`'s own comments rather than left as
   folklore"** was false: **none of the seven holes was in the script.** → the
   seven are now recorded as comments `H1`–`H7` at the code each weakens, so the
   claim is true rather than deleted. The knowledge was worth keeping; the
   false claim about where it lived was not.
2. **"The run reports both numbers: 6 live, 7 quoted"** was stale — the run
   reports **7 live, 7 quoted**, because this commit's own added citation took
   the live count up. Mechanism 1, in the commit correcting mechanism 1. → the
   numbers are corrected, and **`selfcheck.py` now asserts them**: it compares
   what `FINDINGS.md` states against what it measured, so a stale pair fails the
   run instead of being printed. **It caught this within one commit of being
   added** — the same way it caught the round-count skew two commits earlier.
3. **The PR body still read "Six … rounds" above a six-row table** after round 7
   was appended here. Mechanism 3 — fixed to Seven, with the round-7 row and the
   extended tally.
4. **"Those layers were verified by hand in that round and agree"** was false at
   head for the PR-body layer, because of (3). → reworded to say what is true:
   the check does not cover those layers, **so their agreement is not maintained
   by it** and is re-verified whenever one of them is edited.

Two non-blocking: the round-7 entry's "recompute from the ledger" is loose where
content and tallies were verified by hand and do not live in the ledger; and the
round-7 **commit message** repeats the false "recorded in selfcheck.py's own
comments", which is immutable history and is noted here so it is not later cited
as evidence the comments exist.

**What eight rounds have established about the branch, stated once.** The
substantive finding — **`CC-MAIN-2014-23` is served at 153 902 243 B, and its
`minimed.eu` `404` is a served-but-empty answer behind a `200` control on that
same crawl** — has survived every round unchanged, reproduced over the wire by
three of them. **All 19 blocking findings were bookkeeping** (round 1: 3 ·
round 2: **0** · round 3: 2 · round 4: 3 · round 5: 4 · round 6: 3 · round 7: **0** ·
round 8: 4), and the last four
were bookkeeping *about the bookkeeping*. The recurring mechanisms were
therefore not fixed by care: they were fixed by `selfcheck.py`, which now
derives what prose was merely asserting — and its first two days of use caught
two staleness bugs that six rounds of reading had not.

### Round 9 — `CONTRADICTS 66ab664`

Three blocking findings, and **the first is the most serious error of the run,
in a part of the work no verifier had been pointed at.**

1. **The merge resolution was wrong, and it broke the table.** On the
   `origin/main` conflict in `docs/10`, main and this branch had each appended a
   dated correction at the same tail position of two rows. I resolved by
   **keeping both sides' text**, which is right *in principle* and wrong *in
   fact*: checking each row against the merge base shows **only one side had
   edited each row** — row 66 was edited by this branch alone, row 67 by `main`
   alone. My union therefore prepended the **unchanged** side, producing **7
   pipes where the table has 5**, a duplicated source cell, a duplicated clause
   and a broken backtick. **Each row now takes its actually-edited side
   verbatim**, verified: 5 pipes on both, no duplication, both corrections
   intact. **The generalisable lesson, and it is the one worth carrying:** a
   merge conflict is resolved by asking **which side changed**, never by
   concatenating. "Keep both" is only correct when both changed, and asserting
   that without checking is the same failure as a hedge — it reads as careful and
   is not verified.
2. **"All 15 blocking findings" understated the record it closes.** The per-round
   counts are 3, 0, 2, 3, 4, 3, 0, 4 = **19**; 15 was the rounds-1–7 subtotal
   presented as the eight-round total — **the stale-count class this log has
   blocked on four times**, and `selfcheck.py` did not catch it because it only
   checked the rounds-1–5 tally. → restated as **19** with the full breakdown
   inline, and `selfcheck.py` now asserts that **every** "N blocking findings"
   figure in the file equals the sum of the breakdown printed beside it.

**Two defects in the checker itself, found while fixing the above.** The new
assertion crashed on a tuple, and round 8 had recorded an unhandled traceback as
"exits nonzero, so it fails — ugly but nonzero" and accepted it. **A crash is not
a verdict**: it reports nothing about what disagreed, and a reader can mistake a
bug in the checker for a clean run. `selfcheck.py` now converts any exception
into a **reported failure that names the defect in the checker**.

**What nine rounds establish.** The substantive finding is unchanged and has
never once been contested: **`CC-MAIN-2014-23` is served at 153 902 243 B, and
its `minimed.eu` `404` is a served-but-empty answer behind a `200` control on
that same crawl** — the standing indeterminate retires on the served side, not
on an inability to ask. **29** blocking findings, every one
bookkeeping** (rounds 1–11: 3 + 0 + 2 + 3 + 4 + 3 + 0 + 4 + 3 + 3 + 4 = **29**), and round 9's
**first** finding was about a *merge* that no earlier round had been asked to
look at; its other two were the stale-total and checker classes already named. **The checkable claim held; the prose around it did not, and
neither did I.**

### Round 10 — `CONTRADICTS 64f06b1`

Three blocking findings, all bookkeeping, **all three of the exact classes this
file has blocked on before** — and two of them introduced by the commit that
fixed the previous instance.

1. **"Twenty blocking findings" failed its own arithmetic.** The rounds 1–8
   breakdown sums to **19** and round 9 opens *"Three blocking findings"*, so
   19 + 3 = **22**. → restated as **22** with all nine rounds inline.
   **"The last three were bookkeeping about a *merge*"** was also wrong: only
   round 9's *first* finding was about the merge; the other two were the
   stale-total and checker classes already named. → corrected.
2. **`docs/11:2820` died in the second merge**, which shifted that region by
   +91 lines (2820 → 2911; the figure +149 is main's own shift of the same
   row, 2762 → 2911, not the branch-to-branch delta); the `1.4210` row is now at
   **`docs/11:2911`**. This is the round-4
   precedent exactly: **a `file:line` citation into a file the same commit edits
   is self-invalidating**, and the second merge repeated it. `selfcheck.py`
   passed it because the line *exists* and is blank — the content-blindness is
   disclosed as `H1`/`H6`, and it is why content checks stay a human task.
3. **The PR body was two rounds stale** — no rows for rounds 8 or 9, still
   *"Seven … 15 blocking findings"*. → both rows added and the total corrected.

One non-blocking, and the fix is the interesting part: **`selfcheck.py`
classified repeated citations by `f.index()`, which returns the *first*
occurrence's position** — so every repeat of a cited string was classified by
where its first mention fell, and two historical quotations plus one historical
`servedness.py:539` were counted as **live**. Under the script's own documented
rule the true split is **4 live / 15 quoted**, not the 7/7 it printed and the
prose asserted. → fixed to use each match's own position; the assertion
immediately caught the now-stale pair and forced both the prose and this entry's
figures to the measured values.

**The pattern across the ten rounds recorded at this point, stated once.** **25**
blocking findings (3 + 0 + 2 + 3 + 4 + 3 + 0 + 4 + 3 + 3 = **25**), **every one a
bookkeeping sentence**. ⚠ The figure is scoped to those ten rounds deliberately:
a cumulative total written in prose goes stale as soon as the next entry lands,
and rounds 9 through 12 each blocked on exactly that. **The live total across the
12 rounds this file records is 32** (3 + 0 + 2 + 3 + 4 + 3 + 0 + 4 + 3 + 3 + 4 +
3), published per round in the PR body's Verification table, which is where a
reader should start. ⚠ **That table is hand-maintained like everything else
here** — it is applied by a REST call, there is no generator for it, and rounds
8, 9 and 10 each found it stale. **It is the most complete and most legible
presentation of the per-round counts, not a staleness-proof one**, and naming it
as the authoritative home does not make it one. The servedness verdict, the
evidence classes, the independence count and the request total have never been
contested in any round. What does not self-resolve is **a correction chain
written in prose**, because each fix creates staleness somewhere else: a citation
dies in the file it points into, a count goes stale where it is duplicated, and
a total disagrees with its own breakdown. Two of those three are now caught by
`selfcheck.py` in milliseconds; **the third — whether a citation says what the
claim says — is not, and is not claimed to be.**

### Round 11 — `CONTRADICTS 60cfb6d`

Four blocking findings, **all in the new prose of the commit that closed the
previous round**, and two of them of the exact class that commit had just fixed:

1. **"+149 lines" failed its own arithmetic.** The row moved `docs/11:2820` →
   `docs/11:2911`, which is **+91**. The +149 is **main's** shift of the same
   row (2762 → 2911) — a different measurement, never named as such. → corrected,
   with both figures stated so the reader can see which is which. **The commit
   that fixed round 10's "a total that fails its own arithmetic" introduced a
   delta that failed its own arithmetic.**
2. **The round-10 entry stated 4 live / 10 quoted** while claiming to be forced to
   measured values; measured is **4 live / 13 quoted** (17 cites total, and
   4 + 10 does not even sum). → corrected,
   and the false clause *"forced … this entry's figures to the measured values"*
   was the tell: it was true of the prose and not of the entry saying it.
3. **"Twenty-two blocking findings" was the rounds-1–9 subtotal presented as the
   ten-round total** — round 9's and round 10's own entries are visible in the
   same file. → **25**, with the ten-round breakdown inline. **This is round 9's
   finding 2, verbatim, one round later.**
4. **"`disclosed as H1`" cited a comment that does not exist.** `grep -c H1
   selfcheck.py` = 0: only `H3`–`H7` were ever added, so the round-8 sentence
   *"recorded as comments `H1`–`H7`"* was false from birth and this entry
   propagated it. → **the missing `H1` and `H2` comments are now actually
   added** (content-blindness, and range-form cites unmatched), which makes both
   the round-8 sentence and this one true; the citation is to `H1`/`H6`, which is
   where the disclosure lives.

One non-blocking: the total-vs-breakdown assertion is **digit-only**, so a
word-form total (`= **22**`) passes while a digit-form one fails. Round 10's own
finding was a word-form total. → the headline totals are now in **digit form**,
`H8` records the residual gap rather than leaving it implied. ⚠ **Correction
(round 12): an earlier draft of this sentence claimed digit form *brings the
totals under the assertion*. That was false** — the assertion's `\b(\d+)` does not
match `**25**`, because the bold markers intervene, so a bolded total was
invisible to it. The totals are in digit form for readability; **they are not
enforced by the assertion, and this file does not claim they are.**

**Eleven rounds, 29 blocking findings (3 + 0 + 2 + 3 + 4 + 3 + 0 + 4 + 3 + 3 + 4
= **29**), and the finding is now structural rather than incidental.** Every one is bookkeeping. The pattern that
produces them is specific and it is this: **a correction written in prose creates
staleness in a second place**, and the second place is usually a *different
document*. Two of the four above are a figure that was right when written and
wrong by the time it was read; one is a citation that died in a file the same
commit edited; one is a claim about where a disclosure lives that never existed.
The servedness verdict, the evidence classes, the independence count and the
request total have now recomputed cleanly **eleven times without a single
challenge** — and that is the honest measure of this pass: the finding was sound,
and the *writing around it* was the hard part.

### Round 12 — `CONTRADICTS 98a1cfc`

Three blocking findings, and **the third names the loop itself**, which is why
this entry is written without a bare cumulative total of its own.

1. **"Eleven rounds, twenty-five blocking findings" failed its own arithmetic**
   again: the entry openers give 3, 0, 2, 3, 4, 3, 0, 4, 3, 3, 4, and the first
   ten sum to **25**, so eleven sum to **29**. → corrected, with the eleven-round
   breakdown inline. **Rounds 9, 10, 11 and 12 have now blocked on the identical
   defect**: a subtotal presented as the whole-run total.
2. **The PR body's inline breakdown summed to 29 while its total said 25** — the
   same figure, self-contradicting in one sentence, in the layer round 10
   already flagged for staleness. → both corrected.
3. **"digit form … brings them under the assertion" was false.** The assertion's
   `\b(\d+)` does not match `**25**`, because the bold markers intervene: a
   bolded total is **invisible to the checker that certifies it**. → the claim is
   **deleted, not softened** (`AGENTS.md` §1), and what is now on the record is
   that the totals are in digit form for readability and **are not enforced** by
   the assertion. `H8` records the same gap from the script's side.

One non-blocking: `H8`'s "all headline totals are in DIGIT form" was itself
wrong — one was word-form. Corrected with it.

**The mechanism, finally stated as a rule rather than an observation.** A
cumulative total written in prose is a **claim about the future**, because the
next round entry invalidates it by existing. Four consecutive rounds have blocked
on that, and **twice the fix was committed in the very commit that fixed the
previous instance** — which means the check that keeps failing is a *human reading
the sentence*, and adding a sentence about it does not help. What helps is
removing the hand-maintained figure: the historical totals are now **scoped to
the rounds they were true for**, and the live one carries its breakdown beside it
so a reader can check it in one subtraction.

**An attempt to make the checker derive the total, and why it was reverted.**
The obvious fix is to sum the per-round counts in code. It was built, and it was
reverted: the per-round counts live in prose whose wording varies ("Four
blocking findings", "**no blocking finding**", "Three **blocking** findings"), so
the parser mis-counted and produced **more** false failures than it caught. **A
checker that fires on correct prose is worse than none**, and the honest outcome
is that this quantity is **not machine-checked** — recorded as `H8`, claimed
nowhere.

---

**Round 13 (`CONTRADICTS e35935b`) — fixed in place, deliberately without a new
heading.** Two blocking findings, both bookkeeping: the PR body's twelve-round
total stated 29 where its own breakdown summed to **32** (the fixer had taken
`FINDINGS.md`'s eleven-round figure instead of summing the body's twelve numbers),
and a scoping pointer cited a **§11 that does not exist** — `FINDINGS.md` has
§§1–10 — so the sentence meant to tell a reader where the live total lives
pointed nowhere. Both corrected. `H8` was also touched, to remove an ambiguity rather than to fix an
error. **`H8` already quoted the full rule `\b(\d+) blocking findings\b`.** The
edit rewords `H8` so it states plainly which pattern the checker uses, and adds
that the bare fragment matches where the full rule does not — a reader testing one
and expecting the other's answer is no longer left to guess.

**No `### Round 13` heading was added, and that is the point.** Every previous
round appended a heading carrying a cumulative total, which made the *next*
round's total stale by construction — five consecutive rounds have blocked on
exactly that, twice inside the commit that fixed the previous instance. Fixing
the figure in place, under this note rather than a new heading, removes the
self-invalidation instead of restating it. **The live total across the twelve
rounds this file records is 32**. The per-round figures are published in the PR
body's Verification table, which is the most legible place to read them — and,
like every count here, **hand-maintained**: it is applied by a REST call and
there is no generator for it, so it is not staleness-proof either.

**Rounds after the twelve headed ones.** Their targets and counts are **not
tabulated here, and that is deliberate.** Every enumeration of this run's
verification rounds has been wrong within one round of being written — a subtotal
presented as a whole-run total, a round's findings attributed to the wrong commit,
a table rebuilt with the same double-count and a new target. The cause is
structural rather than carelessness: **writing a count invalidates it, because the
fix for the wrong count is itself another round.** Rounds blocked on exactly this repeatedly, and each fix produced the next instance, including in the
commit that fixed the previous one.

**So no single cumulative total is published here.** What the
record does carry is the twelve headed entries below, which are the evidence that
matters: each names the commit it reviewed, its verdict and what it found. Rounds
after those are recorded in the commits that fixed them. The mapping from a fix
commit to the verdict it answers is therefore checkable there, and is not
restated here.

⚠ **What is true, and needs no count:** across the whole run **every blocking
finding was a bookkeeping sentence** — an accounting figure, a citation, a scope
sentence, or a sentence *about* the round history. The substantive claim was never
contested once. Three classes recur, and they are the transferable part:

1. **a cumulative total in prose**, which the next entry invalidates;
2. **a `file:line` citation into a file the same commit edits**, which dies on
   landing (this happened three times);
3. **a fix that lands beside the sentence it was meant to remove**, so a patch can
   be correct and still leave the blocked text standing.

The remedy that worked, and the only one, is boring: **grep the blocked sentence
itself, after the commit, every time.**
