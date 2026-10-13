# Area L addendum — the `/ipro/hcp/*` family, enumerated with a host and a date per member

**Date:** 2026-10-13 · **Claim issue:** [#57](https://github.com/NovaLux12/carelink-api-research/issues/57)
**Area:** `docs/11` Tier 3, **L — Recovery of the retired `ipro/hcp` JSF surface** (addendum from area M)

This is an **addendum**. It does **not** close area L; see §8.

## Accounting

| item | value |
|---|---|
| **Requests sent** | **44 of a 45 cap** — **1 recorded as UNSPENT** |
| Method | **GET only** — no POST, no OPTIONS, no token exchange, no authentication |
| Declared delay | **3.5 s apart**, held **inside** a per-host `flock`, with `sleep 3.5` before the `curl` in the locked region |
| Measured same-host gap floor | **4.275 s** (kernel body-mtime oracle), cross-checked at **4.102 s** from the harness `t_sent` series — see §7 |
| Hosts contacted | `index.commoncrawl.org` (**44**), `data.commoncrawl.org` (**0**) — **nothing else** |
| **Requests to any Medtronic host** | **0**. No vendor traffic of any kind, no DNS, no TLS, no HTTP |
| Ledger rows | `results.jsonl` = **44 rows**, one per request. **40** carry `t_queued`/`t_sent`/`t_done` at millisecond UTC ISO-8601; rows **1–4** carry **`null` in all three** because the harness that sent them wrote no timestamps — the series is **absent** there, not zero-duration (§8 Defect 1) |
| Responses committed | **none.** Bodies live under `.loop/probe-bodies-area-l/`, **outside the repository**; only headers, byte counts, sha256 digests and a projected record tuple are committed |

`wc -l results.jsonl` = 44, and the cap line above says 44 of a 45 cap. Both
directions agree; there is no shortfall to reconcile.

**Why the bodies live outside the tree, which is not where a reader expects
them.** `scripts/research-checks.py`'s hygiene check globs `findings-log/**/*`
**on the filesystem**, not the tracked set, and fails on any file over
**1 MiB**. The `CC-MAIN-2026-39 / medtronic.com` response that answered the §4a
truncation cell is **1 280 724 B**, so a body kept inside `findings-log/` —
**gitignored or not** — turns the check red while nothing is actually committed.
The bodies were therefore moved to `.loop/probe-bodies-area-l/`, outside the
repository, rather than weakening a check this pass does not own (`docs/09` §4
records the precedent: relaxing a check is a maintainer's decision, not a
research pass's side effect). Their facts — byte count and sha256 per row — stay
in `results.jsonl`, so every capture stays re-fetchable, and the mtimes that
produce the §7 spacing series are untouched.

**Why the delay is 3.5 s and not the 2.5 s the claim issue states.** `docs/09` §1
("Low rate") reads "≥1.2 s spacing on probe rounds; ≥2 s per host enforced
in-harness; … **≥3 s on archive calls**", citing
`findings-log/probe-2026-10-08/recon/ARCHIVE-URLS.md` §0, whose own line reads
"Rate limiting: **≥3 s between every call** (`q.sh` `sleep 3`)".
`index.commoncrawl.org` is an archive service, so the repository asks for **≥3 s**
and BRIEF.md's own precedence rule says the repository wins over the brief.
3.5 s was used.

`AGENTS.md` §7: Common Crawl records carry Java session identifiers in URL
paths, so **no response body is committed anywhere in this directory.**
`derive.py` reduces each response in code to `{record_count, distinct_hosts,
members[], first/last_urlkey, ipro_hcp_count}`, redacting any `jsessionid_…` to
the marker plus a count, and the ledger stores that plus the withheld-body
marker, the full-response byte count and its sha256. **Measured result: this
family's Common Crawl records carry zero `jsessionid` markers**
(`jsession_markers: 0` on every record query) — unlike the Wayback captures of
the same paths, which `ARCHIVE-URLS §3` records as
`/ipro/hcp/main/home.jsf;jsessionid=…`.

---

## 1. Controls — sent first, before any candidate, all four

The finding rests on **zeros**, so no instrument was used to measure an absence
until it had returned data on a target it is known to cover. Controls were sent
at `seq` **5, 6, 7, 8** — before any candidate cell — and nothing was read as a
zero before they had passed.

| # | seq | query (after the base) | answer | verdict |
|---|---|---|---|---|
| **A** positive, record form | 5 | `index=CC-MAIN-2020-50&url=carelink.minimed.eu&output=json&matchType=domain&limit=100` | **200**, `content-type: text/x-ndjson`, **6 records**, 1 host (`carelink.minimed.eu`) | **passed** |
| **B** absence, record form | 6 | `index=CC-MAIN-2020-50&url=zz-area-l-absent-20261013.minimed.eu&output=json&matchType=host` | **404** `application/json` `{"message": "No Captures found for: zz-area-l-absent-20261013.minimed.eu"}` | **passed** |
| **C** absence, count form | 7 | `index=CC-MAIN-2020-50&url=zz-area-l-absent-20261013.minimed.eu&output=json&showNumPages=true&matchType=host` | **200** `{"pages": 0, "pageSize": 5, "blocks": 0}` | **passed** |
| **D** positive, count instrument | 8 | `index=CC-MAIN-2020-50&url=carelink.minimed.eu&output=json&showNumPages=true&matchType=domain` | **200** `{"pages": 1, "pageSize": 5, "blocks": 1}` | **passed** |

**Control A's host/crawl pair is not a guess.** Area M's committed ledger answers
**200** for `carelink.minimed.eu` on `CC-MAIN-2020-50` at its `seq 60`
(`matchType=host`), and this pass re-issued it in the `matchType=domain` shape.

**Control D also fills a hole area M left open.** Area M's matching cell — its
`seq 33` — answered **504**, which is why its `FINDINGS.md §3b` carries the `†`
footnote marking `CC-MAIN-2020-50 / minimed.eu` **not observed**. It is observed
here (`seq 8`), and §5 re-reads it.

### The two absence oracles, as established on this pass

| you want to know | the answer that means *absent* | the answer that means *failed* |
|---|---|---|
| absence, record form | **404** + `No Captures found for: <url>` (control B, `seq 6`) | 502 / 504 / 503, and 400 |
| absence, count form | **200** + `{"pages": 0, "blocks": 0}` (control C, `seq 7`) | 502 / 504 / 503 |
| presence, either form | **200** + ≥1 record, or `blocks` ≥ 1 (controls A, D) | — |

**This API failed 18 of the 44 requests (41%)** — `502` ×6, `504` ×8, `400` ×4.
Higher than area M's 28%. **None of the 18 was read as a zero.** §6 lists the
cells that were still unresolved when the budget ran out.

**Not every failure was re-issued, and the first draft of this sentence claimed
otherwise.** Re-issuing is the rule area M's correction binds on this API, and it
was followed for every *cell* that mattered — but two individual rows were
dropped after one attempt:

| row | crawl | what it was | why it was dropped |
|---|---|---|---|
| `seq 25` | `CC-MAIN-2014-10` | the crawl-scoped `example.com` **control** for that crawl | the crawl's three `minimed.eu` attempts had already failed 504/504/502; the control's purpose was to say why, and a fourth request on a crawl that had answered nothing was not bought |
| `seq 41` | `CC-MAIN-2013-48` | `minimed.eu` domain, one attempt, **400** | the budget went to `CC-MAIN-2015-06` instead |

**What that cost, stated rather than absorbed.** `CC-MAIN-2013-48` is one of the
three 2013-era crawls, so it sits in §6's indeterminate column for a reason this
pass **chose** rather than one it hit: the crawl was given one attempt where
`CC-MAIN-2013-20` was given two and `CC-MAIN-2014-10` three. Its verdict is
`indeterminate` either way, but the evidence behind that verdict is thinner than
its neighbours', and a reader weighing the 2013 end should know the difference was
one request wide. **Correct statement of the rule as applied here: every
`*minimed.eu*` cell was attempted at least twice except `CC-MAIN-2013-48`, and
the 2014-10 control was sent once; both failures prove nothing in either
direction.**

---

## 2. The finding — the family is **four members in two crawls**, not three in one

Area M anchored the family on three captures in `CC-MAIN-2020-50`, all at
2020-12-02, and `docs/11`'s addendum calls it "three captures". **That is one
crawl's worth.** A second crawl holds the same family six months earlier and
carries a **fourth member the `.jsf` framing does not name**:

| capture timestamp | code | host | path | crawl |
|---|---|---|---|---|
| **2020-05-27 21:29:18** | **302** | `carelink.minimed.eu` | **`/ipro/hcp/index.jsp`** ← **new** | `CC-MAIN-2020-24` |
| **2020-05-27 21:29:19** | **200** | `carelink.minimed.eu` | **`/ipro/hcp/login.jsf`** | `CC-MAIN-2020-24` |
| **2020-05-27 21:29:19** | **302** | `carelink.minimed.eu` | **`/ipro/hcp/main/home.jsf`** | `CC-MAIN-2020-24` |
| 2020-12-02 03:07:17 | 302 | `carelink.minimed.eu` | `/ipro/hcp/` | `CC-MAIN-2020-50` |
| 2020-12-02 03:07:17 | 200 | `carelink.minimed.eu` | `/ipro/hcp/login.jsf` | `CC-MAIN-2020-50` |
| 2020-12-02 03:07:17 | 302 | `carelink.minimed.eu` | `/ipro/hcp/main/home.jsf` | `CC-MAIN-2020-50` |

**Four distinct paths · one host · two crawls · two capture dates spanning
2020-05-25 → 2020-12-02.** All OBSERVED.

Three things follow, and they carry different weight, so they are kept apart:

1. **The family is `/ipro/hcp/*`; the `.jsf` glob is too narrow.** `index.jsp`
   is a `.jsp`. **Narrower than first stated here:** the repository already
   carries the wider glob once. `ARCHIVE-URLS §5` writes the family row as
   **`/ipro/hcp/*`** (`recon/ARCHIVE-URLS.md:341`), and it is the **§3 timeline**
   row (`recon/ARCHIVE-URLS.md:237`) that writes `ipro/hcp/*.jsf` — so the
   narrow form is one line in one table, not the repository's only spelling.
   The consequence is correspondingly narrower: the **§3 timeline row** omits
   the fourth member, and `docs/11`'s addendum repeats that row's narrower glob.
   **`ARCHIVE-URLS` was not modified** — area M's convention, and that log
   belongs to the 2026-10-08 pass.
2. **It is not a single three-capture entry.** Area L's close condition named
   "one three-capture entry with no siblings" as the negative that would close
   it. There is a sibling crawl and a sibling member.
3. **The migration fact area L exists to recover is confirmed and strengthened:**
   the retired clinician surface ran **on `carelink.minimed.eu`, the live patient
   API host**, and was still being captured seven months into 2020 — not a
   2013–2022 relic that had already gone.

**Two query shapes agree on the new member**, the way area M established its
anchor: `matchType=domain` (`seq 34`) and `matchType=host` (`seq 38`) each
return the identical 7-record set, `index.jsp` included.

**A delta to area M's path table, not a refutation.** Area M's §3a lists five
paths for `CC-MAIN-2020-50`; the record set has **six**. The sixth is
`/robots.txt` **404** at `20201202030717`. Area M did not claim exhaustiveness
for that table and did not list this path; it is recorded here so the next
reader counts six, not five. Area M's own `seq 44` independently recorded
**6 records** for the same crawl and domain, so the count agrees across passes
and only the prose list was short.

---

## 3. The two ends — the 2022 end answered, the 2013 end **withdrawn as unanswerable**

`ARCHIVE-URLS §3` dates the family **2013-05-17 → 2022-05-13** and names no host.
The anchors are therefore chosen from the **published crawl inventory**, not
guessed: `GET /collinfo.json` (`seq 9`) → **200**, `application/json`,
**128 crawl indexes**, newest `CC-MAIN-2026-39`. **84** of them have a window
overlapping 2013-05-17 → 2022-05-13.

**Neither end date falls inside any crawl window.** Checked against the
inventory: no crawl contains 2013-05-17, and no crawl contains 2022-05-13.

### 3a. The 2013 end — **INDETERMINATE**, and the instrument cannot settle it

The crawl after 2013-05-17 is **`CC-MAIN-2013-20`** (2013-05-18 → 2013-06-20) —
**one day after** the date `ARCHIVE-URLS` records. The crawl before it is
`CC-MAIN-2012` (2012-01-27 → 2012-06-05).

| seq | crawl | query | answer |
|---|---|---|---|
| 39 | `CC-MAIN-2013-20` | `minimed.eu` domain | **404** `No Captures found` |
| 40 | `CC-MAIN-2013-20` | `example.com` domain (crawl-scoped control) | **404** `No Captures found` |
| 41 | `CC-MAIN-2013-48` | `minimed.eu` domain | **400** |
| 42 | `CC-MAIN-2013-48` | `example.com` domain (crawl-scoped control) | **404** |
| 17, 20, 23 | `CC-MAIN-2014-10` | `minimed.eu` domain ×3 | **504, 504, 502** |
| 25 | `CC-MAIN-2014-10` | `example.com` domain (crawl-scoped control) | **504** |

> **Verdict, 2013 end: INDETERMINATE.** Not "absent" and not "absent from Common
> Crawl" — **unanswerable through the index API at this date**. Four requests
> were spent reaching it and it did not yield an answer.

The `400` at `seq 41` is a failure and is **never** read as an absence. The
`404` at `seq 39` is the API's absence answer, and §4 explains why it still
cannot be read as a negative here.

### 3b. The 2022 end — the family is **already gone from the corpus**

The crawl after 2022-05-13 is **`CC-MAIN-2022-21`** (2022-05-16 → 2022-05-29),
**three days after** the date; the crawl before it is **`CC-MAIN-2022-05`**
(2022-01-16 → 2022-01-29).

| seq | query | answer |
|---|---|---|
| 19, 22 | `minimed.eu` domain, `CC-MAIN-2022-05` | 504, then 404 `No Captures found` — **no 200 on this crawl, so not evidence** |
| 18, 21, 24 | `minimed.eu` domain, `CC-MAIN-2022-21` | 502, 502, then **200, 4 records** |
| 26 | `example.com` domain, `CC-MAIN-2022-21` — crawl-scoped control | **200, 5 records** |

**This end is answered by `CC-MAIN-2022-21` alone.** `seq 26` returns **200 with
5 records on that crawl**, so the crawl is served and the query shape returns
data there; that is what makes `seq 24` a real answer rather than a lucky escape
from the failure class.

**`seq 22` carries no weight, and the first draft of this section said
otherwise — it called that `404` a "readable absence … on a crawl whose sibling
cell answered 200". There is no `200` anywhere on `CC-MAIN-2022-05`: its only
two rows are `seq 19` (504) and `seq 22` (404).** The `200`s at `seq 24`/`26`
belong to `CC-MAIN-2022-21`, a different crawl. A `404` whose control returned
nothing on that same crawl raises the question; a `404` with **no** control at
all has zero crawl-level evidence. By this pass's own rule — `docs/09` §4, never
let a `404` carry a negative until a positive control has returned records **on
that crawl** — `CC-MAIN-2022-05` is **indeterminate**, not empty, and it is
counted as such in §6.

**`CC-MAIN-2022-21`, `minimed.eu`, all four records:**

| capture timestamp | code | host | path |
|---|---|---|---|
| 2022-05-20 07:32:58 | 403 | `carelink.minimed.eu` | `/robots.txt` |
| 2022-05-21 15:58:22 | 403 | `carelink.minimed.eu` | `/robots.txt` |
| 2022-05-17 04:42:35 | 200 | **`carelink-stage3.minimed.eu`** | `/` |
| 2022-05-17 04:42:35 | 404 | `carelink-stage3.minimed.eu` | `/robots.txt` |

**Not one `/ipro/hcp/` record.** Three days after `ARCHIVE-URLS` records the
family's last archived capture, the nearest crawl shows `carelink.minimed.eu`
serving `/robots.txt` **403** twice and nothing else.

> **Verdict, 2022 end: the family is a bounded 2020 deployment in the Common
> Crawl record** — observed **2020-05-25 → 2020-12-02** across two crawls, and
> **absent from `CC-MAIN-2022-21`, the crawl nearest the 2022 date**, which is
> served and returned records. Area L's second close condition is met **for the
> 2022 end on that one crawl**. It is **not** met on `CC-MAIN-2022-05`, the
> crawl before the date, which is **indeterminate** rather than empty: a `404`
> there has no positive control behind it, because that crawl returned no `200`
> on any of its two rows.

**A host name neither this pass nor area M had seen:**
**`carelink-stage3.minimed.eu`**, recorded 2022-05-17. It comes from a
*successful* `minimed.eu` domain enumeration, not from a guess and not from the
parked `*.carelink.eu` space (`AGENTS.md` §7 — this name is under `minimed.eu`
and was served back to us). Area M's enumerated host set was
`{carelink.minimed.eu, carelink-stage.minimed.eu, minimed.eu,
www.carelink.minimed.eu}`; this is a fifth. **Recorded, not probed** — no DNS or
HTTP was sent to it.

### 3c. One more readable cell, at the 2015 end

`CC-MAIN-2015-06` (2015-01-25 → 2015-02-02) is served and readable: `minimed.eu`
domain → **200, 1 record** — `carelink.minimed.eu` `/` at **2015-01-28
04:10:35**, `ipro_hcp` count **0** (`seq 43`).

**That record carries no archived HTTP status.** Its CDX keys are `digest`,
`filename`, `length`, `offset`, `timestamp`, `url`, `urlkey` — **no `status` and
no `original`**, so there is no code to report and none is reported. It is
listed as a capture with a date and a host, not as a capture with a code.

---

## 4. `docs/10` §1's open row — **is a `matchType=domain` set truncated? — SETTLED**

Area M left this open and it is the load-bearing assumption under every
`minimed.eu` negative in this repo. Four measurements settle it.

### 4a. The count instrument is **not** a record count, and cannot detect truncation

| seq | cell | `pages`/`pageSize`/`blocks` | records actually returned |
|---|---|---|---|
| 8 | `carelink.minimed.eu` domain, `CC-MAIN-2020-50` | `pages 1, pageSize 5, blocks 1` | **6** (`seq 5`, `seq 10`) |
| 16 | `medtronic.com` domain, `CC-MAIN-2026-39` | `pages 1, pageSize 5, blocks 5` | **≥2000** — `limit=2000` returned exactly 2000 (`seq 13`) |

`pages × pageSize` is **5** in both rows. The second row's set is at least
**400× larger**. **`showNumPages` under-reports and must not be used to reason
about completeness in either direction.** Area M's §3b was careful to mark its
`blocks` column as a block count and not a record count; this is the measurement
that shows *how far* the two diverge.

### 4b. `limit` truncates from the **tail**; the **head** is kept

`seq 11` — the same cell with `limit=2` — returns `/` and `/app/login`, the
**first two** in SURT order, dropping the four that follow. A `limit` silently
keeps the head of the SURT range and can drop any host whose key sorts late.
**This is the failure mode a truncated set would hide**, and it is now named.

### 4c. With **no** `limit`, page 0 is the whole set — and the API says so itself

| seq | cell | answer |
|---|---|---|
| 10 | no `limit` | **200, 6 records** — the same six as `seq 5`'s `limit=100` |
| 12 | `page=1` | **400** |
| 15 | `page=1`, verbatim re-issue | **400**, body: **`"Page 1 invalid: First Page is 0, Last Page is 0"`** |

The API's **own page accounting** says the result is a single page, page 0, and
the un-limited page-0 query returned all of it. The `400` is reproduced
identically on two attempts, so it is **a stable answer, not a transient
failure** — it is the API declining a page it has just said does not exist.

> **Verdict: a `matchType=domain` record query carrying **no `limit`** is not
> truncated at these sizes, and the API's `Last Page = 0` corroborates that
> without trusting the record set itself. **A negative (no truncation at these
> sizes) counts** — which is what `docs/10` §1 asked.

### 4d. Area M's negatives therefore stand — for a reason that was never stated

Area M's `clcloud.minimed.eu` / `carelinkhp.minimed.eu` verdict rests on those
names being **absent from the enumerated `minimed.eu` host sets**. That follows
only if the enumerations were not truncated — and it holds, for a reason area M
never had to write down: **every one of area M's 14 record-form `minimed.eu`
queries carried no `limit`**, checked against its committed ledger
(`findings-log/2026-10-13-area-m-commoncrawl-cdx/results.jsonl`, `seq` 40–45,
49–53, 57, 58, 60).

**INFERRED, and the assumption is stated rather than hidden.** That the absence
of a `limit` is what makes those sets complete, rather than the sets happening
to be small enough that it did not matter. Supporting observation: the largest
is 8 records (`seq 42`) against a `limit`-capped 2000 elsewhere, so no cell was
near any cap. **Not demonstrated** — only four cells in this pass could be tested
for `Last Page`, and none was area M's.

---

## 5. Correction (2026-10-13) — an anchor I named wrongly, and a control I over-read

Recorded here rather than smoothed over, because both were mine and both were
caught inside the same pass.

### C1 — the 2013-end anchor was the wrong crawl, and the first answer to §3a was wrong twice

A first draft of §3a named **`CC-MAIN-2014-10`** as "the first published crawl
at or after 2013-05-17" and stated the preceding crawl was `CC-MAIN-2012`.
**The first half was false.** The inventory says the crawl after 2013-05-17 is
**`CC-MAIN-2013-20`** (2013-05-18 → 2013-06-20), one day after the date; 2014-10
is the *third* crawl after it. The second half was right.

The cause is mechanical and worth naming: I compared the inventory's `from`/`to`
strings against a `YYYYMMDD` literal, but the API returns **ISO-8601**
(`2013-05-18T00:00:00`), so every comparison was lexicographic against the wrong
format and `CC-MAIN-2014-10` sorted first. The corrected figures were re-derived
in code with a real date parse, and the corrected crawl was then probed.

### C2 — "the crawl is not served" was **not established**, and is retracted

The first draft of §3a concluded that `CC-MAIN-2014-10` was "a crawl the API is
not serving", on the strength of `seq 25`: a crawl-scoped control for
`example.com` on that crawl answering **504**.

**That conclusion does not follow, and it is retracted.** The control rests on
`example.com` being captured in *every* crawl, which is false:

| seq | crawl | `example.com` control | `minimed.eu` | the crawl is served? |
|---|---|---|---|---|
| 44 | `CC-MAIN-2015-06` | **404** | **200, 1 record** | **yes** — and `example.com` is absent from it |
| 40 | `CC-MAIN-2013-20` | 404 | 404 | unknown |
| 42 | `CC-MAIN-2013-48` | 404 | 400 | unknown |
| 25 | `CC-MAIN-2014-10` | 504 | 502/504/504 | unknown |
| 26 | `CC-MAIN-2022-21` | **200** | **200, 4 records** | **yes** |

**The crawl-scoped control is one-directional.** A control **success** proves the
crawl is served; a control **failure or 404 proves nothing** — the crawl may be
served and simply lack that host. `seq 44` is the row that proves it: a crawl
where `example.com` 404s while `minimed.eu` returns records.

So the honest reading of the 2013-end crawls is narrower than the first draft:
**`minimed.eu` could not be read on them**, for reasons this pass does not
separate. No mechanism is asserted.

**And the sharper point, which survives the retraction:** the same three 2013/
2014-era crawls each failed the `minimed.eu` query in a **different** way —
`404`, `400`, `502`/`504`. **The API's failure mode is crawl-dependent, so a
status code is not an oracle across crawls.** This is `docs/09` §8's
"discriminate on Content-Type, never on status" arriving in a new place: here
even the *absence* answer (`404 No Captures found`) is produced for a cell whose
crawl was never shown to serve anything.

---

## 6. The sweep, and the cells the budget did not settle

Thirteen crawls in the sweep below, each queried with the same domain record
query as every other cell, plus `CC-MAIN-2026-39` for the §4 cells — **fourteen
crawls in all**:

| crawl | window | seq | answer | records | `/ipro/hcp/` |
|---|---|---|---|---|---|
| `CC-MAIN-2013-20` | 2013-05-18 → 2013-06-20 | 39, 40 | 404 (+ control 404) | 0 | **indeterminate** |
| `CC-MAIN-2013-48` | 2013-12-04 → 2013-12-22 | 41, 42 | 400 (+ control 404) | — | **indeterminate** |
| `CC-MAIN-2014-10` | 2014-03-07 → 2014-03-17 | 17, 20, 23, 25 | 504, 504, 502 (+ control 504) | — | **indeterminate** |
| `CC-MAIN-2015-06` | 2015-01-25 → 2015-02-02 | 43, 44 | **200** (+ control 404) | 1 | **0** |
| `CC-MAIN-2015-22` | 2015-05-22 → 2015-06-04 | 27, 33, 36 | 504, 504, 502 | — | **indeterminate** |
| `CC-MAIN-2017-04` | 2017-01-16 → 2017-01-25 | 28 | **200** | 5 | **0** |
| `CC-MAIN-2019-51` | 2019-12-05 → 2019-12-16 | 29 | **200** | 3 | **0** |
| `CC-MAIN-2020-24` | 2020-05-24 → 2020-06-07 | 30, 34, 38 | 504, **200**, **200** | 7 | **3** |
| `CC-MAIN-2020-50` | 2020-11-23 → 2020-12-06 | 5, 10 | **200** | 6 | **3** |
| `CC-MAIN-2021-04` | 2021-01-15 → 2021-01-28 | 31 | 404 | — | **indeterminate** — no `200` on this crawl |
| `CC-MAIN-2021-25` | 2021-06-12 → 2021-06-25 | 32, 35, 37 | 504, 400, 502 | — | **indeterminate** |
| `CC-MAIN-2022-05` | 2022-01-16 → 2022-01-29 | 19, 22 | 504, 404 | — | **indeterminate** — no `200` on this crawl |
| `CC-MAIN-2022-21` | 2022-05-16 → 2022-05-29 | 18, 21, 24, 26 | 502, 502, **200**, **200** | 4 | **0** |

Area M separately covered `CC-MAIN-2018-39`, `CC-MAIN-2022-40`, `CC-MAIN-2024-42`,
`CC-MAIN-2025-30` and `CC-MAIN-2026-39`, none of which holds a family member.

**Seven cells are INDETERMINATE and are recorded as holes, not as absences** —
every crawl on which no row returned `200`: `CC-MAIN-2013-20`, `CC-MAIN-2013-48`,
`CC-MAIN-2014-10`, `CC-MAIN-2015-22`, `CC-MAIN-2021-04`, `CC-MAIN-2021-25`,
`CC-MAIN-2022-05`. **One request of the cap is unspent.**

Two of those seven (`CC-MAIN-2021-04`, `CC-MAIN-2022-05`) were mislabelled
**readable absences** in the first draft of this table, on the reasoning that a
`404` in the record form is the absence answer. That reasoning ignores the
control requirement this pass states at `docs/09` §4 and applies to `seq 39`
above: a `404` means *absent* only once a positive control has returned records
**on that same crawl**, and on both of these crawls nothing returned `200` at
all. **Counting rule, so the next reader can re-derive the column:** a cell is
readable as an absence only if some row for **that crawl** answered `200`. Seven
of the fourteen crawls this pass touched fail that test; the other seven passed
it, and they are the only cells whose answers carry weight.

### A `/patient/` prefix caveat on area M's §3c

Area M §3c states that across every capture recovered for `minimed.eu` in **all
six** crawls, "**not one path begins `/patient/` or `/connect/`**". **In the
crawls area M queried, that is true and stands as written.** In the crawls this
pass added, it is not:

| crawl | paths beginning `/patient/` |
|---|---|
| `CC-MAIN-2017-04` (`seq 28`) | `/patient/entry.jsp` **302**, `/patient/main/login.do` **302** |
| `CC-MAIN-2019-51` (`seq 29`) | `/patient/entry.jsp` **302**, `/patient/main/login.do` **302** |
| `CC-MAIN-2020-24` (`seq 34`, `seq 38`) | `/patient/entry.jsp` **302**, `/patient/main/login.do` **302** |

**Both readings, neither picked.** Area M's claim is scoped to six crawls and is
accurate inside that scope; the generalisation behind `docs/08`'s "zero captures
of the API surface" does **not** survive the prefix test once more crawls are
read. What does survive is narrower and more useful: these are **portal routes**
— an entry page and a Struts login, all **302** redirects — and **no
`/patient/monitor/data`-style data-plane endpoint appears in any crawl either
pass read.** That is a claim about the paths, not about the prefix, and it is
the one worth keeping.

---

## 7. Spacing — measured on both oracles, neither rounded

Counting rule (`docs/09` §4): one gap per consecutive pair **in request order**,
from `results.jsonl`; N bodies give N−1 gaps.

> **Read this before the floor, because the floor is not measured over all 44
> requests.** Rows **1–4** — the four a debug harness sent before the send path
> was fixed — carry **no timestamps at all** and are **excluded from both series**
> (§8 Defect 1). The 39 gaps below are measured over the **40** rows that have a
> series; the other **4 of the 44 requests sit outside both series entirely**,
> and their own sub-floor gap is disclosed in §8 rather than being folded into
> these numbers.

| series | rows measured | gaps | **floor** | max | under 2.5 s | under 2.0 s | span |
|---|---|---|---|---|---|---|---|
| harness `t_sent` | **40 of 44** | 39 | **4.102 s** | 79.318 s | **0** | **0** | 556.858 s |
| **kernel body-mtime** | **40 of 44** | 39 | **4.275 s** | 79.029 s | **0** | **0** | 560.496 s |

**The series agree**: the spans differ by 3.638 s over 557 s, which is the
validation `docs/09` §4 asks for before trusting the mtime series. Requests whose
`t_done` **precedes** `t_sent` (impossible): **0**; requests whose `t_done`
**equals** `t_sent`, a zero-duration request and equally impossible: **0**; rows
with an **absent** timestamp series: **4** (rows 1–4, as above). So this pass's
`date` readings are internally consistent over the 40 rows that have them,
unlike areas B, D, X and Z. `spacing.py` prints all three counts separately so
a zero-duration row cannot pass silently again.

Both floors exceed the **3.5 s** declared and the **≥3 s** `docs/09` §1 asks
for on archive calls. Full output: `spacing.txt`, produced by `spacing.py`.

`git` does not preserve mtimes, so the kernel series is valid only on the machine
that ran the probe and is **not re-derivable from a clean clone**. Both series
are committed as numbers; the bodies are not.

---

## 8. Defects of this pass, recorded rather than smoothed over

### Defect 1 — four requests went out at the wrong delay, from a debug harness

**Sequence, in order.**

1. The first `req()` revision nested the `curl` inside the `flock -c` string.
   The nested quoting broke, the command aborted, and **no request left the
   machine** on four invocations. Each aborted run wrote a ledger row with
   status `000`. Those four rows were removed and the ledger reset, because they
   recorded no request — and that reset is stated here rather than left as a
   silent deletion.
2. While diagnosing it, a **debug harness did send four real requests** against
   `index.commoncrawl.org` with a `sleep 0.2`. Its `-D` was dropped, so **no
   `Content-Type` and no HTTP status survived**, and the responses were not read
   before the pass reset. **They are recorded as ledger rows 1–4**, tagged
   `HARNESS-DEBUG-not-evidence`, because they happened and `wc -l results.jsonl`
   must equal the number of requests sent.

**The cost, stated exactly.** Four requests of the cap went to a discarded
harness, at **0.2 s instead of the declared 3.5 s**. The gaps between those four
sends were measured at the time from kernel body-mtimes: **4.063 s, 7.592 s,
0.859 s**. **The 0.859 s gap is below the repository's `≥2 s` floor.** It is a
real breach of this pass's own rate discipline, it happened before the send path
was fixed, and **no cause is asserted for it.**

**Their timestamps are now `null`, and that is the honest form.** The first
version of rows 1–4 carried a `t_queued`/`t_sent`/`t_done` reconstructed from
those body-mtimes and emitted as though the harness had written them. It had
not, and the reconstruction was wrong in a way that would have read as a real
series: it was stamped **2025** rather than 2026, and it put
**`t_sent == t_done` on all four rows**, which is a **zero-duration request** —
as impossible as a negative one, and invisible to a check that only tests
`t_done < t_sent`. The three fields are now **`null`**, a `timestamp_series` field
records why, and `spacing.py` reports **zero-duration and negative-duration rows
separately** so neither can pass silently again. The bodies for these four
requests were not retained, so on this machine the send times are no longer
re-derivable; **the three mtime gaps above are the record of what was measured
at the time**, and they are the only spacing evidence for these rows.

**What was done.** Rows 1–4 are **excluded from the §7 spacing measurement**;
`spacing.py` prints the excluded count in its own output rather than dropping
them silently. They are **not used as evidence** anywhere: control A was
re-issued clean at `seq 5` with status and `Content-Type` intact, and the four
controls this pass relies on are `seq` **5, 6, 7, 8** — all post-fix.

The send path was then rewritten so the `curl` goes to its own `%q`-quoted file
and `flock` is given `sh <file>` instead of `-c "<string>"`. That form has no
nested quoting to get wrong. `probe.sh` is committed as sent.

### Defect 2 — seven crawls remain holes

`CC-MAIN-2013-20`, `CC-MAIN-2013-48`, `CC-MAIN-2014-10`, `CC-MAIN-2015-22`,
`CC-MAIN-2021-04`, `CC-MAIN-2021-25` and `CC-MAIN-2022-05` are **indeterminate**
— the seven of the fourteen crawls touched here on which no row returned `200`.
§6 marks them and no claim rests on them. In particular **the 2013 end is not
answered** (§3a, §5-C2), and the 2022 end rests on `CC-MAIN-2022-21` alone
(§3b).

### Defect 3 — the sweep is a spread, not a census

Fourteen crawls were read, not 128, and the seven holes mean even those are not
a systematic sweep of the 2013–2022 window. **"Absent from every other crawl
this pass could read"** is the claim; "absent from Common Crawl" is **not**
claimed and cannot be.

---

## 9. What this pass does **not** establish

- **The 2013 end.** Indeterminate, for reasons of instrument failure this pass
  does not fully separate (§3a, §5-C1, §5-C2).
- **That the family is dead today.** Common Crawl is a crawl record, not the
  live surface. Every statement here is about what a crawler recorded, on a
  date, in a named crawl.
- **Which host served the family in 2013**, or whether the 2013 → 2020 captures
  `ARCHIVE-URLS` records are the same deployment. **INFERRED, and unchanged from
  area M's addendum:** that `/ipro/hcp/*` names one surface over time. This pass
  adds a fourth member in a second crawl, which is consistent with it and does
  not prove it — `index.jsp` could equally be a second portal sharing the prefix.
- **Whether `carelink-stage3.minimed.eu` is a real vendor host.** It is a name
  Common Crawl recorded under `minimed.eu` in 2022. No DNS, no HTTP, no claim.

---

## 10. Reproducing this

```bash
cd findings-log/2026-10-13-area-l-ipro-hcp
./probe.sh stage1      # the four controls, in order
./probe.sh stage2      # /collinfo.json — the crawl inventory
./probe.sh stage3      # the truncation cells
./probe.sh stage4      # re-issues of seq 12 (400) and seq 14 (502)
./probe.sh stage5      # the two ends (first attempt; see §5-C1)
./probe.sh stage6      # the spread
./probe.sh stage7      # re-issues of the three failed anchors
./probe.sh stage8      # third attempts + crawl-scoped reachability controls
./probe.sh stage9      # re-issues of the failed spread cells
./probe.sh stage10     # last re-issues + the host-shape cross-check
./probe.sh stage11     # the 2013 end, correctly anchored (2013-20)
./probe.sh stage12     # the last 2013 crawl (2013-48)
./probe.sh stage13     # bounding the unserved region (2015-06)
python3 spacing.py     # both oracles
```

`probe.sh` resumes its `seq` from `results.jsonl`, so a re-run continues the
sequence rather than restarting underneath the hand-written debug rows. **Stage 1
is the only stage that must run first**: it establishes the zero-oracle every
later zero depends on.
