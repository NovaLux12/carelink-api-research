# Area M — Common Crawl through the CDX index API, not through computed byte offsets

**Date:** 2026-10-13 · **Claim issue:** [#44](https://github.com/NovaLux12/carelink-api-research/issues/44)
**Area:** `docs/11` Tier 3, **M — Common Crawl, properly**
Closes `docs/11` area M.

## Accounting

| item | value |
|---|---|
| **Requests sent** | **61 of a 64 cap** — 60 under the original claim cap, **1 more under the owner-authorised extension** (dated addendum on issue #44, 2026-10-13), spent on the `cdx-00101.gz` overshoot re-read and on nothing else. **3 of the 4 authorised requests are recorded as UNSPENT.** |
| Method | **GET only** — no POST, no OPTIONS, no token exchange, no authentication |
| Declared delay | **2.5 s apart**, held **inside** a per-host `flock`, with `sleep 2.5` before the `curl` in the locked region |
| Measured same-host gap floor | **2.873 s** (kernel body-mtime oracle), cross-checked at **2.736 s** from the harness `t_sent` series — see §7 |
| Hosts contacted | `index.commoncrawl.org` (56), `data.commoncrawl.org` (5) — **nothing else** |
| **Requests to any Medtronic host** | **0**. No vendor traffic of any kind, no DNS, no TLS, no HTTP |
| Ledger rows | `results.jsonl` = **61 rows**, one per request, `t_queued`/`t_sent`/`t_done` at millisecond UTC ISO-8601 |
| Responses committed | **none.** Bodies live under `bodies/` (this directory's `.gitignore`); only headers, byte counts, sha256 digests and a host-only projection are committed |

`wc -l results.jsonl` = 61, and the cap line above says 61 of a 64 cap. Both
directions agree; there is no shortfall to reconcile.

`AGENTS.md` §7: Common Crawl captures carry Java session identifiers in URL
paths, so **no response body is committed anywhere in this directory.**
`derive.py` reduces each response in code to `{record_count, distinct_hosts,
shape}` and the ledger stores that, plus the withheld-body marker, plus the
full-response byte count and sha256 so the capture stays reproducible.

---

## 1. Reachability — OBSERVED, at this host, on this date, and no further

`GET https://index.commoncrawl.org/collinfo.json` → **200**,
`content-type: application/json`, **35 226 B**, **128 crawl indexes** published,
newest `CC-MAIN-2026-39` (2026-09-04 → 2026-09-17). Ledger seq 1 and seq 2 —
**the same request was sent twice**, see §6.

This **contradicts** `COMMONCRAWL §0`'s "host unreachable" **as of 2026-10-13 and
from this host**. It is recorded at that scope and is **not generalised**:
`docs/09` §4 already carries "unreachable *from some hosts*", and a pass that
turns one machine's reachability into a general fact is the same error as the
one this area was opened to correct. The earlier observation stands as an
observation about the host that made it.

## 2. Controls — sent before any candidate, all four

The whole finding is a claim about a **zero**, so no instrument was used to
measure an absence until it had returned data on a target it is known to cover.

| # | ledger seq | query | answer | verdict |
|---|---|---|---|---|
| **A** positive, universal | 3 | `url=example.com&matchType=domain&limit=5` on `CC-MAIN-2026-39` | **200**, 5 records, 2 hosts (`example.com`, `www.example.com`) | **passed** |
| **B** positive, same crawl, same shape, **on the namespace under test** | 4 | `url=medtronic.com&matchType=domain&limit=5` on `CC-MAIN-2026-39` | **200**, 5 records, 1 host (`www.medtronic.com`) | **passed** |
| **C** absent, fabricated host under a covered domain | 5, then 7 | `url=zz-area-m-absent-20261013.medtronic.com&matchType=host` | **504** first, then **404** `{"message": "No Captures found for: …"}` | **passed on re-issue** |
| **D** positive, the count instrument | 10, 15 | `url=example.com&output=json&showNumPages=true&matchType=domain` | **200** `{"pages": 1, "pageSize": 5, "blocks": 1}` | **passed** |

Control B's response is **byte-identical across three separate requests**
(seq 4, 6, 11 — one sha256), so the instrument is also reproducible, not merely
alive.

**Control C is the one that nearly ended the pass**, and it is reported at the
top of §3 rather than smoothed over: its first answer was a gateway timeout,
not an absence.

### Control-set resolution — what a zero on this API actually looks like

Control C's `504` meant the zero-oracle was unknown, so no candidate was sent
until it was resolved. Ledger seq 6–16:

| seq | query | answer |
|---|---|---|
| 6 | `matchType=host` on **`www.medtronic.com`** (known-covered) | **200**, 5 records — *the host shape returns data, and the API was healthy at this moment* |
| 7 | absent host, `matchType=host`, re-issued | **404** `{"message": "No Captures found for: …"}` |
| 12 | same, re-issued again | **504** |
| 8, 13 | absent host under `example.com` | **502**, then **404** |
| 9, 14 | absent host via `showNumPages=true` | **502**, then **200** `{"pages": 0, "pageSize": 5, "blocks": 0}` |
| 16 | second fabricated host, same domain | **504** |
| 11 | control B shape, re-issued | **200**, byte-identical to seq 4 |

**The oracle, established with a positive control for each shape:**

| you want to know | the answer that means *absent* | the answer that means *failed* |
|---|---|---|
| absence, record query (`output=json`) | **404** + `{"message": "No Captures found for: <url>"}` | 502 / 504 / 503, and 400 |
| absence, count query (`showNumPages=true`) | **200** + `{"pages": 0, "blocks": 0}` | 502 / 504 / 503 |
| presence, either shape | **200** + ≥1 record, or `blocks` ≥ 1 | — |

**This API fails often.** Across the whole pass, **17 of 60 requests (28%)**
*(the original 60-request figures below are kept as first written; the pass ends
at 61 rows and **⚠ the last paragraph of this subsection is retracted — see the
"Correction (2026-10-13) — verifier round 1" section below, item C1")*
answered 502 ×6, 504 ×7, 400 ×2 or 503 ×2 — nginx `text/html` gateway pages, an
S3 `SlowDown` ("Please reduce your request rate") from `data.commoncrawl.org`,
and a **400 leaking a Python `RemoteDisconnected` as its body**. Every one of
the 17 was re-issued or left as a recorded hole; **not one was read as a zero.**

## Correction (2026-10-13) — verifier round 3

Round 2 returned INCONCLUSIVE — out of steps, not blocked — with six of eight
items fully confirmed and two small outstanding. The substance stands; these are
the two edits, and the first one is a false claim of my own.

### R3-1 — a mechanism claim in `derive.py` was false, and the self-test now proves the replacement

`derive.py` justified binary detection by the gzip magic with: *"a NUL-sniff
misses short payloads **and would have let this pass's own two gzip fetches
through as text**."* **The second clause was false and is deleted.** Every gzip
member carries `FLG=0x00` at byte offset 3, so a NUL-sniff *does* catch a gzip
payload — verified on this pass's own `seq 55` body (632 173 B): gzip magic at
offset 0, **first NUL at index 3**, inside the 4096-byte window. The first
clause (a NUL-sniff misses short payloads) stands.

**Two things bound the damage, and both are recorded rather than assumed.** The
false clause **did not propagate**: `FINDINGS.md` carried only the weaker,
true "short payloads" wording, so no published sentence was wrong. And **no
published number moves** — removing the magic branch entirely leaves
`--selftest` green and every figure identical.

So what does the magic check buy? On the real bodies, nothing measurable. It is
kept because a control now exercises it: **control (6)** feeds a payload
carrying the magic but **no NUL byte** in the sniff window, which the signature
catches and the sniff misses. **Demonstrated**: deleting the
`body[:2] == "\x1f\x8b"` branch makes `--selftest` **exit 1**. That converts
an unsupported mechanism claim into a claim a test holds up — which is the only
kind worth keeping.

This is §6 items 1 and 2 in miniature: a claim stated without evidence, and a
mechanism asserted past what its own artefact shows.

### R3-2 — "each of the five files' headers" was true of three

`FINDINGS.md` said **each** of the five query files names its own dropped line.
That held for `queries-04`, `-05`, `-06` and **failed for `queries-01` and
`queries-03`** — the two files whose dropped-line evidence I had myself masked
(§5 and §6 record that the newline was appended before the first commit).

**I chose to fix the files rather than narrow the sentence**, because the header
is the useful artefact and "the three files whose evidence survived" would have
been a sentence about which files happen to be honest — a property of my
bookkeeping, not of the reader's problem. Both files now carry the same
dropped-line header as the other three, plus an explicit note that they are the
two whose repair erased the evidence. `dropped-lines.py` still reports the same
five tags, and **the file set and the published count are unchanged**.

### R3-3 — main has moved once; not merged, count unaffected

`origin/main` is now `77b2c8e` (PR #51, machine-path redaction), which touched
`docs/09`, one `findings-log/` directory and **no `regression/hurl/` file**. This
branch is **behind `main` and not stale**: measured **209 / 423**,
`git diff 77b2c8e HEAD -- regression/` is empty, and nothing in those commits
touches this pass's log directory. **Not merged** — a re-merge would only
manufacture a fresh `docs/11` conflict for no benefit.

⚠ **The brief for this round said "behind by one commit"; the measurement is
five**, and the five are PR #51's own: `8a4ac41`, `2a1255b`, `9390715`,
`f3da0b2`, and the merge `77b2c8e`. The brief counted the *merge* and not the
commits it brought. The conclusion is unaffected — none of the five touches
`regression/hurl/` or this log directory, so the assertion count cannot have
moved — but the number is stated as measured rather than as received.

---

## Correction (2026-10-13) — verifier rounds 1 and 2

Round 1's three blocking findings and the non-blocking ones, then round 2's
four. Each is attached at the site it changes; the original wording stays
readable at every one of them, and nothing below is a rewrite in place.

### ⚠ Correction (2026-10-13) — verifier round 2: the self-test's strength was overstated, and measuring it found a bug

`failclass.py`'s docstring claimed the self-test asserted that "a
`showNumPages` cell does not mark its own domain absent". **That assertion was
vacuous**: the fixture gave the cell an empty `distinct_hosts`, so it could not
discriminate, and two mutants passed with exit 0 — `record_form = True`
(ignores `showNumPages`) and dropping the `and r["distinct_hosts"]` guard
(reads an empty host set as "no captures"). **The claim overstated coverage by
one assertion.**

[`failclass-mutants.py`](failclass-mutants.py) now measures that strength
instead of asserting it, and [`failclass-mutants.txt`](failclass-mutants.txt)
is the committed matrix:

| mutant | mutation | result |
|---|---|---|
| **A** | ignores `showNumPages` | **killed** |
| **C** | empty host set read as "no captures" | **SURVIVES** |
| **D** | enumeration inference scoped to the crawl, not the registrable domain | **killed** |
| **S** | re-introduces sibling inheritance | **killed** |

**C survives, and the suite does not claim otherwise.** It survives because
`covered` is consulted before `absent`, so a C-mutant's damage to the absent-set
never shows up in a classification. That is a measured limit, not a statement
that C is harmless — it would matter the moment the check order changed, and
**nothing in the published 2 / 0 / 13 / 2 split depends on it.**

Two fixtures were added to close the gap, and **writing one of them found a real
bug in this pass's own classifier**: `complete` was keyed by crawl alone, so a
completed enumeration of `minimed.eu` marked **`medtronic.eu`** absent —
inference leaking across registrable domains. It is now keyed
`(crawl, registrable domain)`. **The fix does not move the published split**:
the 17 failures re-classify to the same 2 covered / 0 absent / 13 indeterminate
/ 2 n/a, because no affected cell was a `matchType=domain` query about a domain
its own enumeration never touched.

### C1 — the "covered hosts never fail" claim was false

This section originally read: *"17 of 17 failures are on absent-host or
`data.commoncrawl.org` requests, and **0 of the 20 requests against hosts known
to be covered ever failed**."* **That is false, and the ledger refutes it from
inside this pass.** `seq 50` and `seq 53` query `carelink.minimed.eu` on
`CC-MAIN-2018-39` — a host `seq 42` had already returned **200** for, with
`carelink.minimed.eu` among its 8 records, **32.6 s earlier**. Both failed (504).
The claim was load-bearing: it was the reassurance that made the 28% failure
rate survivable, and it was republished **unlabelled** in `docs/09` §4, the
`docs/11` M row and the PR body.

**The counting rule, stated before the number** (`failclass.py`, which computes
it; `AGENTS.md` §6 item 7):

> Only a **record-form** query returns a host list, so only a record-form query
> can prove anything about a specific host — a `showNumPages` cell answers
> `{"pages": N, "blocks": M}` and names no host. For each row, ask what the
> ledger had established about that host **on that crawl before the row was
> sent**:
> **covered** — an earlier record-form query in the same crawl returned 200 and
> its host set contains this host · **absent** — an earlier query returned the
> definitive absence form (404 `No Captures found`, `{"pages": 0}`, or a complete
> domain enumeration not naming it) · **indeterminate** — neither, which covers
> every host no enumeration named, every `showNumPages` cell, and every
> fabricated name, *including a fabricated sibling of a covered host* · **n/a** —
> not an index-API query at all.

**Result — 17 gateway errors:**

| class | failures | rows |
|---|---|---|
| **covered** | **2** | 50, 53 |
| absent | 0 | — |
| indeterminate | 13 | 5, 8, 9, 12, 16, 21, 32, 33, 37, 51, 52, 57, 58 |
| n/a (`data.commoncrawl.org` ranged fetch) | 2 | 56, 59 |

**What replaces the false sentence, and it is narrower and more useful than
either the original or "ten covered-host failures":**

> **A gateway error on a host whose coverage was never established carries no
> information in either direction, and must be re-issued rather than read as an
> absence.** And the corollary the other direction points at: **coverage does
> not protect you either** — 2 of 2 queries for `carelink.minimed.eu` on
> `CC-MAIN-2018-39` failed, on a host this same ledger had just proven covered.

`seq 51`/`52`/`57`/`58` (`clcloud.minimed.eu`, `carelinkhp.minimed.eu`) are the
case the class distinction exists for. They are **neither** coverage failures
nor absences: nothing in the ledger establishes coverage of those names, and the
repo's own recorded finding is that CC covers essentially zero CareLink hosts.
§3c's verdict on them comes from **enumerating** the successful `minimed.eu`
domain responses, not from these four failures.

**The INFERRED reading, restated and still only a hypothesis.** Gateway failures
concentrate on queries whose result set is small or absent, i.e. on the backend
doing work the index does not shortcut. **This does not explain `seq 50`/`53`**,
which is exactly why it stays a hypothesis: a hypothesis that cannot account for
the case that prompted the correction is not one to publish as a mechanism.
**No cause is asserted**, and nothing in this pass depends on the reading. What
survives of the original claim is the weaker and true one: **not one** of the
17 gateway errors was read as a zero anywhere in this pass.

## 3. The finding — `docs/10` §2's closed negative is REFUTED in part

`docs/10` §2 currently reads:

> Does Common Crawl cover the API surface? — **Essentially zero** — not one
> record for any `carelink*`/`clcloud*`/`carelinkhp*` host in either of two
> crawls; Wayback is the only usable archive. `[COMMONCRAWL §0–§1]`

Queried through the API, across six named crawls with their dates:

### 3a. `minimed.eu` — record query, `matchType=domain` (apex + every subdomain)

| crawl | crawl window | records | distinct hosts |
|---|---|---|---|
| `CC-MAIN-2018-39` | 2018-09-18 → 2018-09-26 | **8** | `carelink.minimed.eu`, `minimed.eu`, `www.carelink.minimed.eu` |
| `CC-MAIN-2020-50` | 2020-11-23 → 2020-12-06 | **6** | `carelink.minimed.eu` |
| `CC-MAIN-2022-40` | 2022-09-24 → 2022-10-08 | **5** | `carelink-stage.minimed.eu` |
| `CC-MAIN-2024-42` | 2024-10-03 → 2024-10-16 | **0** | — **404 `No Captures found`** |
| `CC-MAIN-2025-30` | 2025-07-07 → 2025-07-20 | **2** | `carelink.minimed.eu` |
| `CC-MAIN-2026-39` | 2026-09-04 → 2026-09-17 | **3** | `carelink.minimed.eu` |

**24 records across 5 of 6 crawls, on the live patient API host.** Host-level
confirmation on two different crawls and two different query shapes: seq 49
(`matchType=host`, `CC-MAIN-2026-39`) and seq 60 (`matchType=host`,
`CC-MAIN-2020-50`) both **200**, returning the same record sets as the domain
queries.

**The paths recovered, with their archive status** (the load-bearing detail —
these are portal captures, not API captures):

| capture timestamp | code | path |
|---|---|---|
| 2026-09-07 | 200 | `/assets/javascript-warning.html` |
| 2026-09-07 | 404 | `/html/en/popUpFeatureReports.html` |
| 2026-09-07 | 404 | `/robots.txt` |
| 2025-07-14 | 200 | `/assets/javascript-warning.html` |
| 2020-12-02 | 200 | `/` |
| 2020-12-02 | 200 | `/app/login` |
| **2020-12-02** | **302** | **`/ipro/hcp/`** |
| **2020-12-02** | **200** | **`/ipro/hcp/login.jsf`** |
| **2020-12-02** | **302** | **`/ipro/hcp/main/home.jsf`** |
| 2022-09-24/25 | 302/200 | `/`, `/robots.txt`, `/assets/javascript-warning.html` on **`carelink-stage.minimed.eu`** |
| 2018-09-18/26 | 302/200 | `/` on `minimed.eu`, `carelink.minimed.eu`, `www.carelink.minimed.eu` |

### 3b. The count sweep, `showNumPages=true&matchType=domain`, all four domains

`blocks` per cell. **All six crawls, all four domains, 24 cells:**

| crawl | `minimed.eu` | `minimed.com` | `medtronic.eu` | `medtronic.com` |
|---|---|---|---|---|
| `CC-MAIN-2018-39` | 1 | 1 | **1** | 3 |
| `CC-MAIN-2020-50` | 1 † ‡ | 1 | **1** | 13 |
| `CC-MAIN-2022-40` | 1 | 1 | **1** | 14 ‡ |
| `CC-MAIN-2024-42` | **0** | 1 | **1** | 9 |
| `CC-MAIN-2025-30` | 1 † | 1 | **1** | 9 |
| `CC-MAIN-2026-39` | 1 | 2 | **1** | 5 |

† the `showNumPages` cell failed (504 / 502); the value shown is **not observed**
— it is **INFERRED** as "non-zero" from the record query that replaced it (seq 44
returned 6 records, seq 43 returned 2). `blocks` is a block count and the two are
not the same quantity, so **these two cells are the only ones in the table that
were not measured as a block count**, and they are marked rather than smoothed.
‡ the first cell failed (504) and was re-issued (seq 46); the `medtronic.eu`
figure for 2022-40 and the `minimed.eu` figures for 2020-50 and 2025-30 are the
only three cells whose value comes from a different query shape than the one the
column names.

**`medtronic.eu` is non-empty in all six**, against `COMMONCRAWL §1`'s table
recording `eu,medtronic)` = **0 blocks** in both crawls it used — including
`CC-MAIN-2026-39` and `CC-MAIN-2024-42`, which are two of the six cells above.

**INFERRED — the likely mechanism of the earlier pass's error, and the reason
the correction is to the method and not only to the count.** A `cluster.idx`
key prefix of the form `eu,medtronic)` names **one** block: the one whose first
key is exactly the registrable domain. A subdomain's block is keyed
`eu,medtronic,carelink)/…`, a *different* prefix. The repo's own table shows the
pass aware of the distinction where it mattered — it annotates `com,medtronic)`
as "4 blocks **+ `com,medtronicdiabetes,origin)`**" and, for 2024-42, "2 blocks
**+ 6 `com,medtronic,wwwp)`**" — and reports `eu,medtronic)` as a bare 0 with no
such annotation. **Assumption:** that `cluster.idx` blocks are keyed by the full
first SURT key rather than by registrable domain. This pass never read a
`cluster.idx` (§4 explains why), so the reading is labelled INFERRED and the
API measurement in §3b stands on its own.

### 3c. What the correction does **not** say

Stated explicitly so the refutation is not over-read:

- **The API-surface half of the old verdict survives.** Across **every** capture
  recovered for `minimed.eu` in **all six** crawls, **not one path begins
  `/patient/` or `/connect/`.** The paths are `/`, `/robots.txt`,
  `/assets/javascript-warning.html`, `/html/en/popUpFeatureReports.html`,
  `/app/login` and `/ipro/hcp/*`. Common Crawl still holds nothing of the
  patient data plane — which is why Wayback remains the usable archive, exactly
  as `docs/10` §2 concluded for a different reason.
- **`clcloud.minimed.eu` and `carelinkhp.minimed.eu` hold zero captures** in all
  six crawls. This is **not** concluded from their own host queries, which
  failed (§4); it follows from **enumerating** the successful `minimed.eu`
  domain responses above, whose combined host set is `{carelink.minimed.eu,
  carelink-stage.minimed.eu, minimed.eu, www.carelink.minimed.eu}` and does not
  contain either name. Enumeration of a successful query is the stronger
  instrument, and it is what the verdict rests on.
- **INFERRED, and it is the assumption that negative rests on:** that the
  `minimed.eu` domain responses are complete rather than truncated. Supporting
  observation: `showNumPages` reports `blocks: 1` in every non-zero `minimed.eu`
  cell and the record counts are 2–8. Assumption: a Common Crawl index block
  holds on the order of thousands of records, so 2–8 cannot be a page cut. **Not
  established by this pass**, and named as an open question in `docs/10` §1
  rather than left inside a negative.

## 4. The byte offsets — re-derived independently, and one of the three is wrong

The claim issue puts this in scope because *"the offsets are the mechanism"*.
`COMMONCRAWL §1` records three computed ranges. Each was fetched verbatim and
its own boundary keys read — a correct range begins on its recorded lower bound.

| recorded range | reproduced? | first key in the fetched span | last key in the fetched span | records |
|---|---|---|---|---|
| `cdx-00101.gz` 45 560 954–47 031 753 (2026-39) | **206**, 1 470 800 B | `com,medtronic)/covidien/de-de/clinical-solutions/lung-health-solutions/resources.html` — **matches the recorded lower bound** | `com,medtryck)/piketrojor/prima-polo` — **does not match the recorded upper bound** `com,medtronicdiabetes,origin)` | **15 000** |
| `cdx-00102.gz` 741 698 501–742 330 673 (2026-39) | **206**, 632 173 B | `com,minimed)/en-us/support/product-support/sensors/sensor-replacement` — **matches** | `com,minimicroled)/nationstar-new-micro-led-nstar-iii` — **matches** | **6 000** |
| `cdx-00097.gz` 26 751 110–27 650 507 (2024-42) | **503 `SlowDown` twice** | — | — | — |

**Settled 2026-10-13 (verifier round 1) under the owner-authorised extension of
the cap from 60 to 64, spent on this row only.** Ledger **seq 61**: the same
ranged fetch, **206**, 1 470 800 B, **sha256 identical to seq 54's recorded
digest**. Decompressed: **15 000 records**, first key
`com,medtronic)/covidien/de-de/clinical-solutions/lung-health-solutions/resources.html`,
last key `com,medtryck)/piketrojor/prima-polo` — both verbatim, so the earlier
reading was right and is now **re-derivable from the repo**. The overshoot is
also quantified, against a range labelled for one registrable domain: it holds
**53 distinct registrable domains** spanning all 15 000 records, derivable from
the 53-row table in
[`offset-boundaries.txt`](offset-boundaries.txt) — whose counts sum to exactly
the span total, so the list is complete. ⚠ **Corrected 2026-10-13 (verifier
round 2): this paragraph previously said "109 distinct hosts across 49
registrable domains".** The table has 53 rows; **49 appears nowhere in the
artefact** except as the record count beside `medtronicinteract.com`, and the
artefact also labelled its own 53-row per-domain table "109 hosts" while
stating a rule ("one host per distinct SURT authority") that it did not follow
— the artefact's own header is now corrected, and it carries an explicit
counting rule (one row per distinct registrable domain, last two labels, no
public-suffix list). The generation run did also count **109 distinct
hostnames**; that figure is **not re-derivable from the committed artefact**,
which is per-domain, so it is recorded here as a note and **nothing else in
this document rests on it**. Boundary keys, the digest and the
host breakdown are committed in
[`offset-boundaries.txt`](offset-boundaries.txt), because the original body had
to be deleted under `research-checks.py`'s 1 MiB ceiling and without that file
the finding rested on prose alone. **No URL, path or status code from that range
is published** — `AGENTS.md` §7.

**Verdict on the method, stated at the mechanism and not only at the count:**

1. **One of the three recorded ranges reproduces exactly at both ends.**
2. **One reproduces at its start and overshoots its recorded end.** The span
   runs past `com,medtronicdiabetes,origin)` and continues into
   `com,medtryck)`, so the 15 000-record artefact contains records for domains
   beyond the family it is labelled with. Its start being exact means this is
   **not** the "alphabetical neighbours" failure `COMMONCRAWL §1` describes for
   the earlier pass — it is the opposite failure, a span that reaches too far.
   The overshoot is in the safe direction (it cannot hide a record of the target
   family), but it does mean the artefact is not what its label says it is.
3. **One could not be fetched at all** and is recorded as a failure, not a
   verdict.
4. ⚠ **Correction (2026-10-13, verifier round 2): `offsetB` is blocked by the
   cap, not by mechanics.** This item previously added that the independent
   `cluster.idx` binary search "could not be sent by the command in §9
   **regardless of the cap**". **That was false and is withdrawn** — the
   hardened read loop now dispatches it (verified: under the old loop it was
   dropped; under the guarded loop it is dispatched). With 61 rows against
   `probe.sh`'s `CAP=64`, a re-run of `queries-06` sends its first three lines
   as `seq 62/63/64` and **aborts before `offsetB`**. So the conclusion is
   unchanged — the offsets rest on one instrument — but the blocker is the
   ordinary cap and is recorded as such.

   Verified both ways, and the detail matters. Against **`queries-06` as it
   stood at the run's head** (ending `…true|` with no `\n`): the old loop
   dispatched `offsetA-r1/r2/r3` and **dropped `offsetB`**; the guarded loop
   dispatched all four. Against the **current** file (newline added in round 1)
   **both** loops dispatch all four — so the newline, not the guard, is what
   makes it sendable now. That is the same evidence-masking the verifier caught
   in §5, and it is why the check above is stated against a named revision.
5. **The first pass's ranges cannot be re-derived, and that is a gap in the
   record.** `COMMONCRAWL §1` reports that those ranges "landed on alphabetical
   neighbours" and names the neighbours, but **records no byte offsets and no
   block keys**. There is nothing in the repo to check them against, so the
   claim is neither confirmed nor refuted here — it is **unverifiable from the
   committed record**, and that is said rather than passed over.

`offsetB` (an independent binary search of `cluster.idx`) was prepared and
**not sent**: the cap was reached first. It is named as the blocker on the
successor, so the gap is visible rather than quietly absent.

## 5. What would have been a better use of the cap

Stated because the pass's own budget is part of its honesty. ⚠ **Corrected
2026-10-13 (verifier round 1): this section originally claimed "22 of 60
requests" on recoverable instrument defects. That over-counted, because it
charged the pass for work the method legitimately does.**

The honest split, with the ledger rows named:

| what | requests | rows |
|---|---|---|
| **pure duplicates** — a re-issue whose response was **byte-identical** to an earlier successful row, so it added nothing | **3** | 2 (dup of 1), 11 (dup of 6), 15 (dup of 10) |
| **re-issues of a dropped line** — the newline defect below, re-sent as their own file | **2** | 47, 60 |
| **re-issues of a failed cell that produced new information** — the method, not waste: these are how the absence oracles were established and how a repeat-failure rate was measured | **7** | 7, 13, 14, 43, 44, 46, 48 |
| **re-issues of a failed cell that failed again** — also the method: they are the evidence that failures repeat | **6** | 12, 16, 53, 57, 58, 59 |
| everything else — distinct information | 42 | — |

**So 5 of 60 requests were spent on the harness defects, not 22.** The original
"22" counted the 13 legitimate re-issue rounds as waste; they are not.

### ⚠ Correction (2026-10-13) — verifier round 2: FIVE lines were dropped, not three

The paragraph above previously said **three**, named three, and attributed all
three to the trailing-newline defect. **All three counts were wrong.**
[`dropped-lines.py`](dropped-lines.py) derives the answer mechanically by
comparing every committed query line against every `host_tag` in
`results.jsonl`; `dropped-lines.txt` is its output.

**60 committed query lines · 61 ledger rows · 55 distinct host_tags · 5 query
lines never sent**, across **five** files:

| never sent | file | cost |
|---|---|---|
| `control-D-positive-showNumPages-count-instrument` | queries-01 | nothing — but **this is where the Control D mis-transcription came from**: the table row was written from the query file rather than from the ledger, and the file's line was never sent |
| `sweep-2018-39-medtronic-com` | queries-03 | re-issued as `seq 47`, which succeeded |
| `host-carelink-minimed-eu-2022-40` | queries-04 | nothing — no row, no finding rests on it |
| `rec-2026-34-minimed-eu-records` | queries-05 | nothing — `CC-MAIN-2026-34` appears **zero** times in the ledger. This line was previously listed under "cost", which was a safe-direction over-count: it cost nothing |
| `offsetB-cluster-idx-2026-39` | queries-06 | nothing — see §4 for why the offsets rest on one instrument |

⚠ **On the cause, which was also mis-attributed.** `sweep-2018-39-medtronic-com`
is the last line of a file that **ends in `\n` at every committed head** — so on
the committed record it looks like a different defect. It is not. The newline
was appended to `queries-03` **after** the run and **before** the first commit,
without that being recorded anywhere, so the repair masked the evidence. What
survives is `run.log`: the file's run stopped at `seq 39`, one line short of the
24 the file now holds. **The same masking applies to `queries-01`'s
`control-D`.** A repair that hides the defect it repairs is not a repair, and
`dropped-lines.py` now exists because a reader of the committed files cannot
derive this without it.

`probe.sh`'s own header carried the same error in a third form — *"Four of this
pass's query files had no trailing newline, so four queries were never sent and
three of them have no ledger row at all"* — while §5 said three and §6 said four.
All three are corrected here and in `probe.sh`; the count is now computed, not
recalled.

**Each of the five files' headers now names its own dropped line**, and
`probe.sh` warns to `run.log` when a query file lacks a trailing newline.
⚠ (Added by verifier round 3.) That sentence was true for three of the five
when it was written — `queries-04`, `-05` and `-06`, the files repaired before
the run's first commit — and **false for `queries-01` and `queries-03`**, the
two whose repair erased the evidence before anything was committed. Rather than
narrow the sentence, the two missing headers were added, and both now carry an
extra note saying they are the files whose evidence the fix destroyed. The
asymmetry is preserved deliberately rather than tidied away: it is the same
defect as the one it describes, one level up.

## 6. Three defects of this pass, recorded rather than smoothed over

1. **A trailing newline silently dropped the last query line of four files.**
   ⚠ **Fixed 2026-10-13 (verifier round 1, BLOCKING 2) — this defect was still
   live in the committed artefacts, not merely described in prose.**
   `probe.sh` was `while IFS='|' read -r …`, and `read` returns non-zero at
   EOF-without-newline, so the loop exits before dispatching the final line.
   **FIVE query lines across FIVE files were lost to it** — `control-D…`
   (queries-01), `sweep-2018-39-medtronic-com` (queries-03),
   `host-carelink-minimed-eu-2022-40` (queries-04),
   `rec-2026-34-minimed-eu-records` (queries-05) and
   `offsetB-cluster-idx-2026-39` (queries-06); see §5's correction for why
   two of those are invisible in the committed files, and
   [`dropped-lines.py`](dropped-lines.py) for the mechanical derivation. This
   paragraph previously said "four files … three of them", which was wrong.

   Fixed four ways: the newline is on every query file; the loop carries the
   standard `|| [ -n "${tag}${role}${host}${path}" ]` guard; `probe.sh`
   **warns to `run.log`** when a query file has no trailing newline, so the
   next pass is told rather than silently shortchanged; and each affected file
   carries a header naming its dropped line. Verified: all nine files dispatch
   every one of their query lines under the hardened loop.

   ⚠ **And the honest limitation of that fix**, added by verifier round 2:
   repairing the newline in the committed files **erased the evidence** for two
   of the five losses. `queries-01` and `queries-03` now end in `\n` and look
   clean; a reader of the committed tree cannot see that they once did not. The
   guard means a re-run would now send those lines — which is the correct
   behaviour and is **not** evidence that this pass sent them.

   The first occurrence of this defect is visible in `run.log` as a
   `seq=2 REFUSED` line — the harness's host allowlist refused a malformed line
   rather than guessing at it, which is the one time it surfaced loudly.
2. **Six `host_tag`s were reused across re-issued requests**, so six body files
   hold one response instead of two and the kernel mtime oracle reads the same
   file twice. `spacing.py` detects and reports this rather than printing a
   `0.000 s` gap that looks like a rule breach. **The harness body is named by
   tag, not by sequence number, and a re-issued request must get a fresh tag.**
3. ⚠ **`record_count` was meaningless for binary bodies** (added by verifier
   round 1). `derive.py` decoded the two ranged gzip fetches as UTF-8 and counted
   *byte* lines: ledger `seq 54` recorded **38 112** "records" and `seq 55`
   **16 284**, against true counts of **15 000** and **6 000** — a reader summing
   that column would add ~54 000 phantom records to a corpus. The `shape` field
   did say `"text"`, but the field is *named* `record_count`. Fixed three ways:
   binary is now detected by the **gzip magic `\x1f\x8b`** rather than a NUL
   sniff (which would have let short payloads through as text), the body is
   decompressed and re-derived so a binary body still yields its **true** count,
   and the phantom byte-line count is quarantined in a separate
   `bytes_read_as_lines` field instead of being presented as a count. A binary
   control was added to `--selftest`, which had none. **The three ledger rows
   already written (54, 55, 61) are not edited** — a ledger row is a record of
   what happened, and hand-correcting one would destroy that. Their true values
   are in `offset-boundaries.txt` and in §4.

4. **`spacing.py` divided seconds by 1000 on its first run** and printed a
   `0.003 s` floor with 58 of 58 gaps "under the 2 s floor" — a total rule breach
   that never happened. Caught because the per-gap mean did not reconcile with
   the run's span. Fixed; the unit constant and the reason are in the file.

## 7. Spacing — measured, both series, neither rounded

Counting rule, in `spacing.py` rather than in prose: one gap per consecutive
pair **in run order**, per host, since the rule is "≥ 2 s between requests to
the **same** host".

| oracle | gaps | min | max | under 2.5 s | under 2.0 s |
|---|---|---|---|---|---|
| **kernel body-file mtimes** (independent of the harness clock) | 45 | **2.873 s** | 152.906 s † | **0** | **0** |
| harness `t_sent` | 59 | **2.736 s** | 1806.735 s ‡ | **0** | **0** |

† inflated by the excluded duplicate-tag bodies, which join two otherwise
adjacent requests into one long gap. ‡ the authorised `seq 61` went out in a
later session, so the longest `t_sent` gap spans the interval between the two
harness invocations rather than any in-run spacing. Neither figure is a spacing
claim; the minimum is.

Re-measured over all 61 rows on 2026-10-13. The floor is **unchanged** by the
extra request: `seq 61`'s body was deleted under the 1 MiB ceiling, so the
kernel series now covers 45 gaps rather than 47, and the minimum it reports is
the same 2.873 s — the deleted bodies were never the minimum.

**Measured floor: 2.873 s, from the kernel mtime series**, because
`docs/09` §4 establishes that series as the independent one; the harness series
agrees to within 0.14 s. **No gap in this pass was below the declared 2.5 s, and
none below the repo's `>= 2 s` floor**, on either oracle. Zero requests recorded
a negative duration (`t_done` before `t_sent`), which is the corruption
signature `docs/09` §4 uses to distrust the harness series — its absence is why
this pass's harness series is reportable at all.

Git does not preserve mtimes, so **the kernel series is valid only on the
machine that ran this probe** and is not re-derivable from a clean clone. Both
series are recorded in `spacing.txt`.

The bodies those numbers were measured from are not all still on disk: **two**
1 470 800-byte ranged CDX fetches (`seq 54` and `seq 61`, byte-identical) were
deleted after each run because `scripts/research-checks.py` enforces a **1 MiB
ceiling over every file under `findings-log/`**, which it applies to the working
tree and not only to committed files. `spacing.py` reports them as missing rather
than skipping them silently. Their byte counts and sha256 remain in
`results.jsonl`, the boundary keys are committed in `offset-boundaries.txt`, and
`spacing.txt` is the committed record of the measurement the bodies supported.

## 8. Scope and limits, stated before anyone relies on this

- **128 crawls are published; 6 were queried.** This is a sample with a stated
  rationale (§ `queries-03-crawl-sweep.txt`), not a census. "CC holds no
  `/patient/` capture" is scoped to **those six crawls**, and the row in
  `docs/10` §2 now says so.
- **The `medtronic.eu` positive was never resolved to a host.** All six cells
  are non-zero, and the cap was reached before a record query could name the
  host. That is a recorded gap, not an implied one.
- **Two host-level cells stayed unresolved**: `clcloud.minimed.eu` (502 ×2) and
  `carelinkhp.minimed.eu` (400, then 502 ×2). §3c explains why that does not
  leave a hole — the enumeration does the work — but the cells themselves are
  failures and are labelled as such.
- **No CC record body is published**, only hostnames, counts, statuses and
  timestamps (`AGENTS.md` §7).
- **No vendor request of any kind was made**, so nothing here changes what the
  bridge pins. No `downstream-bridge` label applies.
- **Nothing was added to `regression/hurl/`.** The pinned suites are vendor
  surfaces, and `AGENTS.md` §11 limits scheduled work to patterns already in
  `regression/hurl/` — adding Common Crawl requests to the PR gate would extend
  the gate's vendor budget on the strength of one research pass, which is not
  this pass's decision to make. What *would* rot — the zero-oracle and the
  failure modes — is pinned in `docs/09` §4 as traps, which is the repo's
  existing anti-rot mechanism for methodology, and is machine-checked here by
  `derive.py --selftest` (falsifiable: it caught a wrong control expectation on
  its own first run) and `spacing.py`.

## 9. Reproducing this

```bash
python3 derive.py --selftest     # the host projection, proven falsifiable
python3 spacing.py               # both spacing series, counting rule in code
./probe.sh queries-01-reachability-and-controls.txt   # reachability + all four controls
./probe.sh queries-02-zero-oracle.txt                # resolve the zero oracle
./probe.sh queries-03-crawl-sweep.txt                # 6 crawls x 4 domains
./probe.sh queries-04-follow-the-positive.txt        # records behind the positive + retries
./probe.sh queries-05-other-named-hosts.txt          # the other two named hosts
./probe.sh queries-06-offsets.txt                    # offset reproduction
./probe.sh queries-07-retries.txt                    # failure cells, re-issued
./probe.sh queries-08-final.txt                      # the host-shape cross-check
./probe.sh queries-09-overshoot-reread.txt                # authorised overshoot re-read
```

⚠ **Read the loop before re-running this.** `probe.sh` now guards its read loop
and warns when a query file lacks a trailing newline, but several of these files
re-request queries this pass already made, and **re-running them against a live
API is not a reproduction of this run** — it is new traffic. To re-derive the
numbers in this document without any request, run the three scripts, which read
only what is committed: `spacing.py`, `failclass.py` and `derive.py --selftest`.

Every query file names its own justification. The harness refuses any host
outside `index.commoncrawl.org` / `data.commoncrawl.org` and aborts at the cap.