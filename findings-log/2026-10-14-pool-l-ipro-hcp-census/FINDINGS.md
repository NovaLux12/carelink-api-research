# Pool L — area L (claim #126): the `ipro/hcp` census over the 2013→2022 Common Crawl window

**Date:** 2026-10-15 (pass opened 2026-10-14T22:54Z UTC)
**Area:** L — Recovery of the retired `ipro/hcp` JSF surface.
**Claim:** https://github.com/NovaLux12/carelink-api-research/issues/126

## Accounting

- **Requests: 40 of a 40 cap.** Cap reached exactly; the harness stopped on its
  own cap check and abandoned the rest of the queue rather than overrunning.
- **Host contacted: `index.commoncrawl.org` only. Requests to any Medtronic
  host: 0.** `data.commoncrawl.org` was not used.
- **Method: GET only.** No POST, no authentication, no token exchange.
- **Inter-request delay: ≥ 3.5 s**, held *inside* `flock` on the shared host
  lock `<pool-root>/.loop/host-index.commoncrawl.org.lock` — passed in as
  `$L_LOCK`, never written as a literal path (no home path may be committed,
  `AGENTS.md` §7).
- Measured same-host spacing floor from `t_sent`: **4.272 s** over **39** gaps
  (max 29.625 s), **0 under 3.5 s, 0 under the repo's `>=2 s` floor**,
  **0 negative durations**. Cross-checked on the kernel body-mtime oracle
  (`docs/09` §4): **40** bodies, min gap **4.035 s**, **0 under 3.5 s**. The two
  series agree, so this pass carries neither the sub-declared-gap nor the
  corrupt-`t0` signature.
- Bodies stored **outside** the repository; headers, ledger and scripts committed.
  Largest response **35 226 B** (`collinfo.json`), far below the 1 MiB hygiene bar.
- **Failures: 15 of 40 (38%)** — `502` ×10, `504` ×3, `400` ×2 — inside the
  repo's recorded 28–41% band for this API. **A retry is a request** and each
  one has its own row: **12** of the 40 rows are retries.
- `jsessionid` redaction was applied **in code** (`project-row.py`) as a marker
  plus a count. **0 occurrences** were found in any of the 40 responses
  (OBSERVED) — the Common Crawl records for this family carry bare URLs, unlike
  the Wayback archive the family was first seen in.

Ledger: `results.jsonl` (40 rows, one per request). Runner: `probe.sh`, queue
files `q-0*.tsv`, row projector `project-row.py`, captures `headers/`,
`run.log`. All 40 rows are re-derivable from these files; `derive.py` re-prints
every table below.

## Method and the rule that governs every cell

**There is no Oracle A/B/C for the CDX API, and this pass borrows none.**

- absence, record form → `404` + `{"message": "No Captures found for: …"}`
- absence, count form → `200` + `{"pages": 0, "blocks": 0}` (not exercised here)
- `502` / `504` / `503` / `400` → **a failure, never an absence**, and re-issued

**Counting rule (unchanged, and it is what decides every verdict below):**

> a cell is readable as an absence **only if some row for that crawl answered 200**.

A row is counted as a *record* only when it parses as a JSON object carrying both
`url` and `timestamp`, so a `404` body never inflates a count.

## Controls, and their order

Per crawl, **control first, probe immediately after** — the ordering the claim
names and the ordering the disputed cell needed.

| control | shape | rows |
|---|---|---|
| positive, per crawl | `url=<commoncrawl.org\|google.com>&matchType=domain&limit=5` on that exact crawl | seq 3, 8, 10, 12, 20, 22, 24, 26, 30, 32 |
| positive, host-scoped | `url=carelink.minimed.eu&matchType=host&limit=5` on `CC-MAIN-2020-50` | seq 7 |
| certainly-absent | `url=zz-area-l-absent-20261013.minimed.eu&matchType=host` on `CC-MAIN-2020-50` | seq 5 → **404** |

**`example.com` was not used as a control** — it was measured absent from
`CC-MAIN-2015-06` (`2026-10-13-area-l-ipro-hcp` §5-C2), and a control failure or
404 proves nothing.

**The certainly-absent sibling 404s on a crawl whose real host returns records**
(seq 5 against seq 7, same crawl, same scope, minutes apart). That is the
absence oracle, established directly in this pass rather than inherited.

## F1 — the one contradictory cell is settled, and the disagreement was a control-ordering artefact

`CC-MAIN-2022-05`, `url=minimed.eu&matchType=domain`:

| seq | role | answer |
|---|---|---|
| 2 | control, `commoncrawl.org` `limit=5` | **504** Gateway Time-out |
| 3 | control, same query, retry | **200, 5 records** |
| 4 | `minimed.eu` domain, no `limit` | **404** `{"message": "No Captures found for: minimed.eu"}` |

**Verdict: a readable absence** (OBSERVED, seqs 2–4). A row for that crawl
answered `200` at seq 3; the probe at seq 4 returned the API's absence shape; the
control was sent **immediately before** it, in the same pass. This is the exact
pairing `2026-10-13-area-l-7crawl-reissue/FINDINGS.md:155-156` names as the thing
that would settle it.

**Both prior readings were true of their own ledgers and neither was true of the
crawl, and neither is retracted:**

- The 7crawl pass's **Correction (2026-10-14)** says no independent positive
  control exists on that crawl. What it records is that **its own two re-issued
  controls returned `504`** — a statement about those two requests.
- Pool-L (#104) ran a control on `-2022-05` (seq 7 there, `200`, 134 records) and
  **sent no minimed probe**, then read the standing absence verdicts as now
  covered. That reading is right about its control and wrong to carry it across
  to a probe it never sent.

What moved the cell is neither ledger alone: it is a control and a probe **on one
crawl, in one pass, in that order**. **OBSERVED.**

## F2 — `/ipro/hcp/*` reaches **2022-07-03**, past the recorded 2022 end

`CC-MAIN-2022-27` (window 2022-06 → 2022-07), `url=minimed.eu&matchType=domain`:

| seq | answer |
|---|---|
| 34, 35, 36 | control `google.com` → **502 ×3** |
| 37 | probe → **502** · seq 38 → **400** (`RemoteDisconnected`) · seq 39 → **200, 9 records** |

The 9 records include
`https://carelink.minimed.eu/ipro/hcp/index.jsp @ 20220703140927` **HTTP 200**
(OBSERVED, seq 39).

**This refutes the "bounded 2020 deployment in the Common Crawl record" reading**
carried as F5 in `2026-10-13-area-l-7crawl-reissue/FINDINGS.md` and, until this
pass, at `docs/11`'s area-L 2022-end paragraph — which the closure addendum in
`docs/11` now replaces. **The 2022 end is now carried by a
capture, not by an absence**, and it lands **51 days after** the 2022-05-13 date
`ARCHIVE-URLS §3` records. The earlier reading rested on `CC-MAIN-2022-21`, whose
window (2022-05-16 → 2022-05-29) **precedes** the 2022-07 capture; nothing was
wrong with that crawl's reading, and it was simply not the nearest crawl that
carries the family.

**The control caveat, stated rather than smoothed:** the `google.com` control
gateway-failed **3×** on this crawl, so this cell is a **record behind no
succeeded control**. That does not weaken it — a record needs no absence oracle,
and seq 39 is a `200` **on that exact crawl**, which is the same thing the
counting rule asks for. It does mean the reverse statement ("`CC-MAIN-2022-27`
holds no other `minimed.eu` record") is not available from this pass. A gateway
failure on one control host carries no information about the crawl
(`2026-10-13-area-l-ipro-hcp` §4; `2026-10-14-pool-l-crawlcontrol/FINDINGS.md`
"what remains open").

## F3 — `CC-MAIN-2014-15` holds **four** `/ipro/hcp/login.jsf` captures, all April 2014

| seq | answer |
|---|---|
| 12 | control `commoncrawl.org` `limit=5` → **200, 5 records** |
| 13 | probe → **502** · seq 14 → **504** · seq 15 → **200, 4 records** |

All four records are `https://carelink.minimed.eu/ipro/hcp/login.jsf`, **HTTP
200**, at four distinct timestamps (**OBSERVED**, seq 15):

| timestamp | path | status |
|---|---|---|
| `20140417041651` | `/ipro/hcp/login.jsf` | 200 |
| `20140423143329` | `/ipro/hcp/login.jsf` | 200 |
| `20140424054803` | `/ipro/hcp/login.jsf` | 200 |
| `20140424231208` | `/ipro/hcp/login.jsf` | 200 |

**This is the densest cell in the corpus for this family and the only one holding
repeated captures of a single path on a single crawl.** The prior corpus had one
record per crawl. Four captures of the login page inside eight days is what a
surface served repeatedly looks like to a crawler, and it is the first direct
evidence *within* the Common Crawl corpus that this family was captured more than
once — the records are OBSERVED, that reading is **INFERRED**.

**It does not move the family's earliest member.** `CC-MAIN-2014-15`'s window
opens in April 2014, *after* the `CC-MAIN-2014-10` capture of 2014-03-10, so the
Common Crawl lower bound stays **2014-03-10** and these four records extend the
family's *density*, not its span.

## F4 — the host-scope fills are readable absences

Claim step 2: `carelink.minimed.eu` `matchType=host` behind its own per-crawl
control on the two crawls whose host-scope cell `early-crawl-reissue` recorded as
unpromoted.

| crawl | control | host probe | verdict |
|---|---|---|---|
| `CC-MAIN-2013-20` | seq 8 **200, 5 records** | seq 9 **404** | **readable absence** |
| `CC-MAIN-2021-04` | seq 10 **200, 5 records** | seq 11 **404** | **readable absence** |

**OBSERVED.** This discharges `2026-10-13-area-l-early-crawl-reissue/FINDINGS.md:107-111`
("the host-scoped cell itself is not promoted to a verdict").

## F5 — `CC-MAIN-2014-23` stays a hole, and five rows is what that cost

| seq | control host | answer |
|---|---|---|
| 16 | `google.com` | **400** `Error: ('Connection aborted.', ConnectionResetError(104, 'Connection reset by peer'))` |
| 17 | `google.com` | **502** |
| 18 | `google.com` | **502** |
| 40 | `commoncrawl.org` | **502** |
| 19 | *(probe, `minimed.eu` domain)* | **404** |

**No row for `CC-MAIN-2014-23` answered `200`, so its `404` carries no absence
weight: the cell is INDETERMINATE** (OBSERVED, the counting rule). Two control
hosts, four control rows, no `200` — and the probe's own `404` is the only
`minimed.eu` answer this crawl ever gave.

**A failure body not previously on record joins the ones that are.** Area M
recorded this API failing as an nginx `502`, an nginx `504`, an S3 `503 SlowDown`
and a Python `400` carrying `RemoteDisconnected`. This pass adds a **Python `400`
carrying `ConnectionResetError`** — at seq 16, on a different crawl, in the same
run as the `RemoteDisconnected` at seq 38. Every one of the 15 failures in this
pass is a **failure**, and none was read as an absence.

## F6 — the census arithmetic, and what this pass can and cannot say

**Inventory (seq 1, `GET /collinfo.json` → 200, 35 226 B): 128 crawl indexes.**
**Counting rule:** a crawl is *in the window* when its published `from` ≤
2022-05-13T00:00:00 and its `to` ≥ 2013-05-17T00:00:00, full-timestamp,
endpoints inclusive.

| quantity | this pass |
|---|---|
| published crawl indexes | **128** |
| overlapping 2013-05-17 → 2022-05-13 | **84** |
| already read by a prior area-L pass (in window) | 12 |
| **unread at the time of this pass** | **72** |
| attempted by this pass, all newly read | **9** |
| — of those, cells classified (record or readable absence) | 8 |
| — of those, left **indeterminate** | 1 (`CC-MAIN-2014-23`) |
| selected but never sent — queue abandoned on the cap | 1 (`CC-MAIN-2018-05`) |
| **still unread after this pass** | **63** |

**The 84 agrees with the prior pass, and the 87 this log first computed was wrong.**
`2026-10-13-area-l-ipro-hcp/FINDINGS.md:313-317` records "**84** of them have a
window overlapping 2013-05-17 → 2022-05-13"; this pass measures **84** from its own
`collinfo.json` (seq 1 — **35 226 B, byte-size identical to the figure area M
records** for the same fetch). **The prior number stands; this log's first
arithmetic is retracted.** See the Correction section at the foot of this file —
the mechanism is a string comparison that silently returned the wrong set, which
is `AGENTS.md` §6 item 3 — a comparison over a lookup that silently returns the
wrong value.

**The 10 crawls were chosen by a rule fixed before the sweep, not by a guess:**
*the earliest unread crawl in each of 2014–2022 (nine crawls), plus the
second-earliest unread 2014 crawl* — double density at the 2014 end, which is the
area's one named hole. Every name came from seq 1's published inventory. Control
host was varied per crawl (`commoncrawl.org` / `google.com` alternating), because
pool-L measured `commoncrawl.org` first-attempt-failing on 4 of 7 crawls and
`google.com` covering all four. **The selection is unaffected by the arithmetic
error below**: all nine selected ids sit well inside the window either way, and
`CC-MAIN-2018-05` — the tenth — was never sent.

### The census table — 13 crawls, every cell classified

| crawl | control (seq · status · records) | probe (seq · status · records) | `/ipro/hcp/` members | **verdict** |
|---|---|---|---|---|
| `CC-MAIN-2013-20` | 8 · 200 · 5 | 9 · 404 · 0 | 0 | **readable absence** (host scope) |
| `CC-MAIN-2014-15` | 12 · 200 · 5 | 15 · 200 · 4 | **4** | **record** |
| `CC-MAIN-2014-23` | 16 · 400 · 17 · 502 · 18 · 502 · 40 · 502 | 19 · 404 · 0 | 0 | **INDETERMINATE** |
| `CC-MAIN-2015-11` | 20 · 200 · 5 | 21 · 200 · 1 | 0 | record, no ipro |
| `CC-MAIN-2016-07` | 22 · 200 · 5 | 23 · 200 · 1 | 0 | record, no ipro |
| `CC-MAIN-2017-09` | 24 · 200 · 5 | 25 · 200 · 6 | 0 | record, no ipro |
| `CC-MAIN-2019-04` | 26 · 200 · 5 | 28 · 200 · 12 | 0 | record, no ipro |
| `CC-MAIN-2020-05` | 29 · 504 · 30 · 200 · 5 | 31 · 200 · 3 | 0 | record, no ipro |
| `CC-MAIN-2020-50` | 6 · 502 · **7 · 200 · 5** | 7 · 200 · 5 | **3** | **record** (area M's anchor, reproduced) |
| `CC-MAIN-2021-04` | 10 · 200 · 5 | 11 · 404 · 0 | 0 | **readable absence** (host scope) |
| `CC-MAIN-2021-10` | 32 · 200 · 5 | 33 · 200 · 3 | 0 | record, no ipro |
| `CC-MAIN-2022-05` | 2 · 504 · **3 · 200 · 5** | 4 · 404 · 0 | 0 | **readable absence** |
| `CC-MAIN-2022-27` | 34 · 502 · 35 · 502 · 36 · 502 | 39 · 200 · 9 | **1** | **record** (control failed) |

**`CC-MAIN-2020-50` reproduced area M's anchor in this pass** (seq 7, three
records, all `@20201202030717`, statuses 302 / 200 / 302) — the same
`findings-log/2026-10-13-area-m-commoncrawl-cdx/FINDINGS.md §3a` set. One source
restating another, **not** independent corroboration (`AGENTS.md` §2.1): this is
the same corpus read by a different pass, and the value here is reproduction, not
a second author.

## F7 — the family, as this pass's corpus now reads it

Every `/ipro/hcp/*` record in the corpus, one host and one date per member. **The
crawl column says which of these are this pass's rows and which are inherited.**

| timestamp | host | path | status | crawl | source |
|---|---|---|---|---|---|
| 2014-03-10 | `carelink.minimed.eu` | `/ipro/hcp/login.jsf` | 200 | `CC-MAIN-2014-10` | prior pass |
| **2014-04-17 04:16:51** | `carelink.minimed.eu` | `/ipro/hcp/login.jsf` | **200** | `CC-MAIN-2014-15` | **seq 15** |
| **2014-04-23 14:33:29** | `carelink.minimed.eu` | `/ipro/hcp/login.jsf` | **200** | `CC-MAIN-2014-15` | **seq 15** |
| **2014-04-24 05:48:03** | `carelink.minimed.eu` | `/ipro/hcp/login.jsf` | **200** | `CC-MAIN-2014-15` | **seq 15** |
| **2014-04-24 23:12:08** | `carelink.minimed.eu` | `/ipro/hcp/login.jsf` | **200** | `CC-MAIN-2014-15` | **seq 15** |
| 2020-05-27 21:29:18–19 | `carelink.minimed.eu` | `/ipro/hcp/index.jsp`, `/ipro/hcp/login.jsf`, `/ipro/hcp/main/home.jsf` | 302 / 200 / 302 | `CC-MAIN-2020-24` | prior pass |
| 2020-12-02 03:07:17 | `carelink.minimed.eu` | `/ipro/hcp/`, `/ipro/hcp/login.jsf`, `/ipro/hcp/main/home.jsf` | 302 / 200 / 302 | `CC-MAIN-2020-50` | prior pass, **reproduced seq 7** |
| **2022-07-03 14:09:27** | `carelink.minimed.eu` | `/ipro/hcp/index.jsp` | **200** | `CC-MAIN-2022-27` | **seq 39** |

**Four paths · one host · five crawls · an observed span of 2014-03-10 →
2022-07-03** (OBSERVED for the two new ends, this pass; the 2020 rows are prior
passes, one of them reproduced here).

**Two ends, and both are captures now.** The area's close condition asked for the
`carelink.minimed.eu` anchor to be "confirmed across the 2013 and 2022 ends or
explicitly shown to be a single-period deployment". It is confirmed at the 2022
end by a capture rather than an absence (F2). **The 2013 end is still an absence
and stays an absence** — `CC-MAIN-2013-20` and `CC-MAIN-2013-48` are readable
absences, and nothing observed contradicts them; the family simply is not in
Common Crawl before 2014-03-10 in the crawls read.

**The standing INFERRED assumption is unchanged and is repeated here because the
2022 capture makes it load-bearing.** That `/ipro/hcp/*` names **one** surface
over time is **still not demonstrated**. The 2022 member is a **`.jsp`** and the
2014 members are **`.jsf`**; the 2020-05 member is a `.jsp` and it sits on the same
host as the `.jsf` members, so the shape does not split the family — but a single
path prefix across eight years, two server-side technologies (JSF and JSP) and a
host that also serves the
patient portal is exactly the kind of claim that two corpora agreeing on a string
does not establish. **Assumption:** that a shared path prefix implies a shared
deployment. **Nothing observed in this pass demonstrates it, and the 2022 capture
makes it more, not less, load-bearing.**

**A side-finding recorded and left alone.** `CC-MAIN-2022-27`'s 9 records include
five `javascript-warning.html` captures at **nested asset paths**
(`/assets/javascript-warning.html`, `/app/assets/javascript-warning.html`,
`/app/assets/assets/javascript-warning.html`, and two deeper), **all HTTP 200**,
all within sixteen minutes of each other (OBSERVED, seq 39). This pass does not
interpret it — it is a question about the patient plane's asset handling, not
about `/ipro/hcp/`, and it belongs to whoever owns that axis. Recorded so the
next reader does not read those five 200s as five files.

## What this pass does **not** say

- **It does not say "absent from Common Crawl."** It says: absent from every crawl
  **this pass could read**. **9 of the 72** unread in-window crawls were attempted
  here, one of those is still indeterminate, one selected crawl was never sent,
  and **63 remain unread**. The census is **not complete at one pass** and this
  log does not pretend otherwise.
- It does not claim anything about what `/ipro/hcp/index.jsp` served. The record
  carries an HTTP **status** from the crawl, not a body; no body was fetched.
- It makes **no** claim about `data.commoncrawl.org`, the `cluster.idx` bulk path,
  or whether `CC-MAIN-2014-23` is served at all. That question is untouched here
  and is the first successor below.
- **No `regression/hurl/` pin was added.** Nothing under `ipro`/`jsf` is pinned
  today, these suites are vendor surfaces, and `AGENTS.md` §11 bars one research
  pass from widening the gate's budget; the rot-prone halves are recorded as
  `docs/09` §4 trap rows instead.

## Evidence map

| claim | class | source |
|---|---|---|
| `CC-MAIN-2022-05` is a readable absence | OBSERVED | `results.jsonl` seqs 2, 3, 4 |
| `/ipro/hcp/index.jsp` @ 2022-07-03, 200, `CC-MAIN-2022-27` | OBSERVED | `results.jsonl` seq 39 |
| four `/ipro/hcp/login.jsf` captures @ April 2014, `CC-MAIN-2014-15` | OBSERVED | `results.jsonl` seq 15 (control seq 12) |
| `CC-MAIN-2013-20` / `-2021-04` host-scope absences | OBSERVED | `results.jsonl` seqs 8–9, 10–11 |
| `CC-MAIN-2014-23` indeterminate | OBSERVED | `results.jsonl` seqs 16–18, 40 (probe 19) |
| 128 published crawl indexes; 84 in window; 72 unread before this pass; 63 after | OBSERVED | `results.jsonl` seq 1 + `derive.py` |
| prior pass's "84 in window" | PUBLISHED (this repo) | `2026-10-13-area-l-ipro-hcp/FINDINGS.md:313-317` — **reproduced exactly** (see Correction) |
| failure rate 15/40 (38%) | OBSERVED | `results.jsonl`, all rows |
| `/ipro/hcp/*` is one surface over time | **INFERRED**, undemonstrated | assumption stated in F7 |
| repeated captures ⇒ a live surface to a crawler | **INFERRED** | reasoning on seq 15, assumption stated in F3 |
| `commoncrawl.org` / `google.com` differ in per-crawl reliability | INFERRED | pool-L observed 4 of 7; this pass observed both fail (§F5) |

## Reproduction

```bash
cd findings-log/2026-10-14-pool-l-ipro-hcp-census
python3 derive.py          # re-prints the census table, the per-member list and the spacing floor
wc -l results.jsonl        # 40 — must equal the "40 of a 40 cap" line above
```

`probe.sh` is the exact record of what was sent, queue file by queue file, with
the delay inside `flock` and the cap checked before each attempt. Bodies are
outside the tree by policy (`AGENTS.md` §7); `project-row.py` is what projected
them, and it is the reason the `jsessionid` rule was enforced in code rather than
by reading.

## Correction (2026-10-15) — this log's own crawl-window count was wrong, and the prior pass was right

**Found while writing `derive.py`, zero requests, after the sweep was finished
and its ledger complete.** The pass is unchanged; only the arithmetic is.

**What this log first published:** "**87** of the 128 crawls overlap
2013-05-17 → 2022-05-13", and a table built on it (**76** unread). It also told
the reader that the prior pass's **84** was a counting-rule disagreement with the
rule stated here, left open.

**Both are retracted.** Re-derived from the same seq-1 body under the rule now
stated — *compare `from`/`to` against the same ISO-8601 shape `collinfo.json`
publishes* — the answer is **84**, agreeing with
`2026-10-13-area-l-ipro-hcp/FINDINGS.md:313-317` exactly. **72** crawls were
unread at the start of this pass, not 76; **63** remain unread, not 67.

**The mechanism, which is the transferable half.** `collinfo.json` publishes
`"from": "2013-05-18T04:54:09"` — dashes. The comparison that produced 87 sliced
the leading eight characters (`c['from'][0:8]` → `'2013-05-1'`) against a
**dashless** bound (`'20220513'`), and the `to` test against a dashless
`'20130517'`. On that form `'2013-06-20T13:36:32' >= '20130517000000'` is
**false**, because `-` is `0x2D` and `0` is `0x30` and the separator sorts below
the digit: **every 2013 crawl silently dropped itself out of the window** —
`CC-MAIN-2013-20` and `CC-MAIN-2013-48`, the exact two crawls the 2013-end
question turns on. Those two are the 87-versus-84 gap.

**Nothing raised an error.** The comparison returned a plausible integer, the
crawl names it selected were all genuinely in the window, and the sweep it chose
would have been identical. This is `AGENTS.md` §6 item 3 — *a comparison over a
lookup that silently returns the wrong value* — recorded here rather than fixed
quietly, because **the number a census publishes is the number everything else is
read against.**

**What is not retracted:** every probe, every control, every census-table cell,
every `/ipro/hcp/` member and every verdict. None of them reads the crawl
inventory; they read CDX responses. Only the denominator moved, and it moved
**toward** the prior pass's figure rather than away from it.

## Correction (2026-10-15) — verification round 1: nine arithmetic items, and a second correction to the first correction

Round-1 verification returned **NOT CLEAN** on `5738a16`. The spine held — the
spacing floors, the 40-row ledger with every retry carrying its own row, both
positives read from the bodies, the `CC-MAIN-2022-05` ordering, the 2022 capture
refuting "bounded 2020", `CC-MAIN-2014-23` held indeterminate, and "absent from
Common Crawl" disclaimed. **What did not hold was arithmetic that had escaped
into prose** — this log's own §6 item 5. Everything below is derived in code
(`derive.py`, now reading only committed files) and is re-checkable on a clean
clone.

`findings-log/` is append-only, so nothing above is edited. Line numbers refer to
`5738a16`.

### C1 — "8 of the 9" was wrong; the negative is **7 of the 9**

`FINDINGS.md:217` counts `cells classified | 8`, and prose above carried that
number forward as "8 without ipro". Re-derived per crawl from the ledger
(`derive.py` §4): `/ipro/hcp/` was absent in **7 of the 9** newly-read crawls.
Two of those eight classified cells — `CC-MAIN-2014-15` (4 members) and
`CC-MAIN-2022-27` (1 member) — **do** carry ipro records, so the table cell and
the prose disagreed. **Corrected: 7 of 9.**

**The denominator is stated explicitly, because two are defensible:**

| denominator | figure | reading |
|---|---|---|
| all 9 crawls this pass first read (**published**) | **7 of 9** | the indeterminate cell counts in the denominator and is not in the numerator |
| the 8 classified cells only | **6 of 8** | a `404` behind no control cannot carry an absence in either direction |

The two differ by exactly the one indeterminate cell (`CC-MAIN-2014-23`). Both
are stated; neither is a rounding. `docs/11` carries both.

### C2 — the census table's row labels conflated two things

`FINDINGS.md:214-216`. The nine newly-read crawls are **8 record cells + 1
indeterminate** — **zero** readable absences among them. The three readable
absences (`-2013-20`, `-2021-04`, `-2022-05`) are on crawls a prior pass had
**already read**; this pass re-probed them with its own control+probe pair. The
row labelled "cells classified (record or readable absence) | 8" is right on the
number and wrong on the label. **Corrected in `docs/11`; the eight are record
cells, not "record or absence" cells.**

### C3 — `CC-MAIN-2018-05` was never queued; the cap blocked a **retry**

`FINDINGS.md:217` said "selected but never sent — queue abandoned on the cap".
`grep -rn '2018-05' q-0*.tsv probe.sh results.jsonl run.log` returns **0 hits** —
it was never enqueued. And `run.log.capped`'s `CAP REACHED at 40 of 40` did not
abandon a queued line: `q-05-last.tsv` holds exactly one entry, which **was**
sent as seq 40; that row answered `502`, `is_failure` was true, `attempt 0 <
MAXRETRY 2`, so the loop went round again and the cap check at `probe.sh:60-62`
stopped it before the retry. **Corrected: the crawl was never queued, and the
cap instead blocked the retry of seq 40.** The bare fact "was never sent" at
`FINDINGS.md:238` is true and stands.

### C4 — "all 40 rows are re-derivable from these files" was false

`FINDINGS.md:36`. Two of `derive.py`'s blocks were gated on `$L_BODIES` and
silently disabled when unset: the **mtime oracle** and the **84-crawl
denominator**. `results.jsonl` carries a 400-character `body_head` and no mtime
field, so neither was re-derivable from the tree — `docs/09` §4's own lesson,
which this pass reproduced in reverse.

**Fixed by committing the data, not by weakening the claim.** Two new files:

- **`spacing.txt`** — the per-gap series on **both** clocks, 39 gaps, with the
  counting rule and the floor for each: clock A (`t_sent`) **4.272 s**, clock B
  (kernel body mtime) **4.035 s**, 0 under 3.5 s and 0 under the `>=2 s` floor
  on either. It states plainly that **the mtime series is machine-local and is
  not re-derivable from a clean clone** (git does not preserve mtimes), which is
  the repo's own convention for that oracle.
- **`crawl-window.txt`** — all 128 published `id`/`from`/`to` rows plus the
  window decision and the read-by tag, so the 84 is re-derivable from the tree.

`derive.py` now reads only committed files, and prints the `L_BODIES` blocks as
an explicit *optional cross-check that says so when absent*, instead of printing
nothing.

### C5 — "roughly 1.6 requests per crawl" had no derivation; the real figure is **2.4–3.2**

Published at `docs/11:1389` as **S-L2's blocker figure**, which is the number a
third party would budget from. It matched nothing on disk. Derived from this
pass's own ledger, counting rule: *requests per newly-read crawl = every
`results.jsonl` row whose crawl is one of the nine ÷ 9.*

| | figure | rule |
|---|---|---|
| **measured** | **3.22** (29 rows ÷ 9 crawls) | rows on the nine newly-read crawls: 15 control + 14 probe |
| **derived** | **2.36** | row failure rate on those rows `p = 0.448`; `E[attempts/query]` at `MAXRETRY=2` is `(1−p)(1+p+p²) + 3p³ = 1.180`; two queries per crawl → `2.36` |

The measured figure exceeds the derived one because **two of the nine crawls
exhausted a control host** (`-2014-23` across two hosts, `-2022-27` across three
attempts). **Publish 2.4–3.2, not 2 and not 1.6.** `1.6` is withdrawn; it had no
derivation and the nearest committed figure is area M's "roughly 1.3 N" at 28%.

### C6 — "within sixteen minutes" was wrong by about sixfold

`FINDINGS.md:309`, labelled OBSERVED. The five `javascript-warning.html` records
in the `CC-MAIN-2022-27` body run **`20220703140102` → `20220703154254`**:
**span 1 h 41 m 52 s, maximum consecutive gap 0:52:07.** Five records and all
HTTP 200 are correct; the interval was not. Relative to the `index.jsp` capture
at `14:09:27`, only 2 of 5 fall inside sixteen minutes, so no subset of the data
gives the figure that was published. **Corrected to 1:41:52 with the rule stated
("span = last timestamp − first timestamp").** The side-finding is still not
interpreted.

### C7 — the `docs/09` trap rows are not this pass's artefact

`FINDINGS.md:326-329` said the rot-prone halves are "recorded as `docs/09` §4
trap rows instead", which reads as though this pass produced them. **`docs/09` is
not in this diff and cites nothing from this pass.** The two rows that already
cover both halves are **`docs/09:186`** (host reachability is a fact about a host
at a time, not a property) and **`docs/09:187`** (~28% failure rate, and a
covered host is not a shield). **Restated: "already carried by the rows at
`docs/09:186-187`."**

### C8 — the control host was "varied per crawl", not "alternating"

`FINDINGS.md:234`. The ledger's control hosts run
`cc, google, google, cc, google, cc, google, cc, cc, google, cc, google` —
**two `commoncrawl.org` in a row** at `-2014-15` → `-2015-11`, and a third at
`-2019-04` → `-2020-05`. "Varied per crawl" is the true claim; "alternating" is
not.

### C9 — this log's own first Correction was incomplete: the 87 was **two** errors, not one

The Correction above attributes the whole 87 → 84 gap to the two 2013 crawls
dropping out. Re-derived against the committed inventory, that is **half** the
story, and the half it named is not the half that mattered:

| variant | rule | count |
|---|---|---|
| **correct** | `from`/`to` compared against the **same** ISO shape, endpoints inclusive | **84** |
| correct, day precision | `from[:10]` / `to[:10]`, dashes kept on both sides | **84** |
| the one that printed 87 | `from[:8]` / `to[:8]` — **dashes kept** — against a **dashless** bound | **87** |

The buggy variant makes **two** opposite mistakes, because `-` is `0x2D`, which
sorts below both `0` (`0x30`) and `2` (`0x32`):

- **drops 2** — the `to` test fails for every 2013 crawl (`'2013-06-20…' >=
  '20130517'` is false);
- **wrongly includes 5** — the `from` test *passes* for every post-window 2022
  crawl (`'2022-06-24…' <= '20220513'` is true), so `CC-MAIN-2022-21`, `-2022-27`,
  `-2022-33`, `-2022-40` and `-2022-49` all entered the window.

84 − 2 + 5 = **87**. **Two consequences that change published claims:**

1. **The rule was stated too narrowly.** Full ISO-8601 precision is *not*
   required — comparing `YYYY-MM-DD` on both sides gives the same **84**. What is
   forbidden is comparing two **different shapes**. The rule above and in
   `crawl-window.txt` is corrected accordingly.
2. **`CC-MAIN-2022-27` is outside the window.** Its window is
   `2022-06-24 → 2022-07-07`. So of the nine crawls this pass first read, **8 are
   in the 2013-05-17 → 2022-05-13 window and 1 is not** — it was read precisely
   because the 2022-end question needed the crawl after the window. **The window
   census therefore reads 84 in window, 12 read before, 8 read new, 64 still
   unread** — not the **63** published above. The 2022 *capture* is unaffected;
   only the census denominator moves.

**What is not retracted.** Every probe, control, census-table cell, `/ipro/hcp/`
member and verdict. The spine round 1 confirmed is confirmed: the 2022 capture
on `CC-MAIN-2022-27` is a record on an out-of-window crawl, which is exactly why
no in-window 2022 crawl had carried it. The counting-rule table, the
`CC-MAIN-2022-05` ordering, `CC-MAIN-2014-23`'s indeterminacy, the host-scope
fills, both spacing floors and the 40-row ledger are untouched.

### C10 — the append-only guard **cannot see this file**, and that is worth stating rather than banking

`scripts/research-checks.py`'s `check_append_only` arms on status `D` and `M`
(`scripts/research-checks.py:471` and `:474`). The diff it reads is three-dot
(`origin/main...HEAD`), and every file in this directory is added on this branch,
so `git diff --name-status origin/main...HEAD -- findings-log/` reports **`A`** for
`FINDINGS.md` — and `A` matches neither arm, so the check prints `ok`
**without ever reading the file.**

**Proved, not assumed.** A negative control: renaming this very section's heading
from `## Correction (2026-10-15) — verification round 1…` to an undated one and
re-running the check **still printed `ok findings-log changes are append-only`**.
The heading form the repo's own gate screens for is
`^## Correction \(\d{4}-\d{2}-\d{2}\)` and both sections here match it, but that
is a fact about this file's text, not something the gate confirmed.

**So the append-only discipline on this log is mine, not the gate's**, and the
green line above should be read for what it is: `D` and `M` are clean. This is the
defect `docs/09` §4 already records at length — *an append-only guard that never
sees a new document* — reproduced here on a pass that had every intention of
complying. **Not fixed here:** widening the gate's own patterns is a maintainer
decision (`docs/09` §4, and `AGENTS.md` §11 on a pass not extending the gate).
Recorded so the next reader does not take that `ok` as evidence about this file.


## Correction (2026-10-15) — verification round 2: the expectation formula was wrong and inverted its own conclusion, and the in-window characterisation was never swept

Round 2 returned **NOT CLEAN** on `078dd38`. It re-derived the census, the
12/8/64 split, the two-opposite-error correction, the out-of-window finding,
`spacing.txt`, `crawl-window.txt` and the C10 finding exactly, and called C10 the
most valuable thing in the diff. Six items. **Two of them are corrections to the
corrections**, which is the failure mode `docs/09` §4 names: *derived prose
contradicting its own source table, then propagating*. Zero requests so far in
this section; the budget this area now holds is spent by the continuation pass
whose log is `findings-log/2026-10-15-pool-l-ipro-census-cont/`.

### C1 — the expectation formula was wrong, and it inverted the sentence attached to it

`FINDINGS.md:487` and `derive.py` §5 both printed

> `E[attempts/query]` at `MAXRETRY=2` is `(1−p)(1+p+p²) + 3p³ = 1.180`

**`probe.sh:81` sends `N = min(Geom(p), MAXRETRY+1) = min(Geom(p), 3)`, so by the
tail-sum rule `E[N] = 1 + p + p²`.** The inner polynomial must be `1 + 2p + 3p²`;
`(1−p)(1+2p+3p²) + 3p³` is the same value. **The published form expands to
`1 + 2p³` — an expectation that FALLS as the failure rate rises, which cannot be
right**, and it was carried into `docs/11` as successor **S-L2's blocker figure**,
the number a third party budgets from.

| | figure | how |
|---|---|---|
| **measured** | **3.22** | 29 rows on the nine first-read crawls ÷ 9 |
| **derived (corrected)** | **3.30** | `p = 13/29 = 0.448`; `E[N] = 1 + p + p² = 1.649`; × 2 queries |
| published (broken) | 2.36 | from `1 + 2p³` |

**And the sentence attached to it was backwards.** `FINDINGS.md:489` /
`docs/11:1410` read *"the measured figure exceeds the derived one because two of
the nine crawls exhausted a control host"*. Under the corrected algebra the
**derived 3.30 exceeds the measured 3.22 by 2.4%** — the exact opposite.
Cross-check: the observed mean attempts per query over the whole 40-row ledger is
**1.43** against the **1.65** the model predicts, so the model is the
conservative one.

**Three figures are withdrawn in turn: "roughly 1.6" (no derivation), "2.4–3.2"
(a floor produced by the broken formula), and the sentence explaining why the
measured number was higher.** What survives is **3.3 requests per crawl**,
budgeted conservatively. `derive.py` §5 is **corrected at source** rather than
left wrong in a shipped script; every figure is computed by
`findings-log/2026-10-15-pool-l-ipro-census-cont/budget.py` so prose quoting it
cannot drift again.

**One mechanism is worth recording.** `check_append_only` screens **every** file
under `findings-log/` — `scripts/research-checks.py:471-480` branches on diff
status, not extension — so a Python file can only be modified by carrying a
`^## Correction \(\d{4}-\d{2}-\d{2}\)` marker, which in Python means a markdown
heading inside a docstring. That is a workaround, not an endorsement; the check
arguably wants scoping to `.md`, which is a maintainer decision (`docs/09` §4)
and is **not** taken here.

### C2 — `docs/10` row 64 still said "63", two clauses after its own correction

Round 1 fixed the arithmetic in that cell's middle clause and left the successor
count live and unmarked further along the same cell: *"…the remaining **63**
crawls (S-L2)"*, while the clause before it read **64 unread**. Corrected to
"**64 in-window** crawls (S-L2) — **not 63**", with the staleness named in the
sentence rather than quietly overwritten. **The lesson is the one this log has now
paid twice:** a correction that fixes a number and does not then re-read the whole
sentence it sits in leaves the error adjacent, not removed.

### C3 — S-L2's headline described 9 in-window crawls five lines before saying 64

`docs/11:1400` read **"the census read 9 of the 72 unread in-window crawls"**,
five lines from "continuing with the **64** unread in-window crawls". Only **8**
were in window: `CC-MAIN-2022-27` is not, which is the fact this log's own C9
introduced. **It is a fourth instance of the same error**, in the successor this
pass wrote to fix it, and it is recorded here as such rather than as a new defect.

### C4 — the full list of stale in-window / out-of-window characterisations

C9 above names line numbers generically. **Here is every one**, so the next reader
can check rather than search. Pass-1 log, body (pre-correction):

| line | what it said | correct value |
|---|---|---|
| 218 | `still unread after this pass \| 63` | **64** |
| 237 | "all nine selected ids sit well inside the window either way" | **eight** do; `CC-MAIN-2022-27` does not |
| 317 | "**9 of the 72** unread in-window crawls were attempted" | **8 of the 72** in window, plus 1 out |
| 319 | "**63 remain unread**" | **64** |
| 340 | evidence map: "72 unread before this pass; 63 after" | "…; **64** after" |

And two **inside the round-1 corrections themselves**:

| line | what it said | correct value |
|---|---|---|
| 375 | "**63** remain unread, not 67" (stated as the corrected figure) | **64** |
| 388 | "crawl names it selected were all genuinely in the window" | **eight** of the nine were |

**Line 237 and line 388 are the same false claim stated twice**, in a body and
then in the correction that was supposed to have caught it — which is `AGENTS.md`
§2.1's *one source, stated twice* arriving through a different door, and §6 item 5
again. **Corrected in `docs/11` and `docs/10` in place; corrected here because this
file is append-only.**

### C5 — C6's replacement figures rested on timestamps committed nowhere

C6 replaced an OBSERVED claim — *"within sixteen minutes"* —
with *"span 1 h 41 m 52 s, max consecutive gap 0:52:07"* — derived from five
timestamps that **existed nowhere in the tree**: seq 39's `body_head` is 300
characters and carries only `20220703140102`, and the other four appeared **only
inside the correction text**. `derive.py` §8 said so in as many words.

**Fixed by committing the data**, the same move that fixed C4's substantive half:
`findings-log/2026-10-15-pool-l-ipro-census-cont/seq39-timestamps.txt` carries the
five `timestamp` values and their host-relative paths, plus the span and the
maximum gap recomputed from them by a stated counting rule. **No record bodies, no
headers, no full URLs** — nothing that could carry a session value.

### C6 — line 36 overclaimed, exactly as C4's did

`FINDINGS.md:36` reads *"All 40 rows are re-derivable from these files; `derive.py`
re-prints every table below."* After C4 the **ledger** claims are true, but §8 of
`derive.py` prints a **notice**, not a table, when `$L_BODIES` is unset. Narrowed
in the correction that C4 already made for the substantive half; recorded here so
the line is not read as a blanket guarantee. **The gap between what a re-derivation
tool prints and what a sentence about it promises is the same gap `docs/09` §4
records as "a check that cannot fail"** — a green line about the wrong thing.

### C7 — the continuation pass ran, and it closes the census this pass left open

The 200-request budget authorised in round 2 was spent as
`findings-log/2026-10-15-pool-l-ipro-census-cont/`: **188 requests** of the 200,
GET only, `index.commoncrawl.org` alone, **zero Medtronic requests**, 54 retries
each with its own row and header capture, `t_sent` floor **3.536 s** and kernel
mtime floor **4.156 s**, both series committed in that pass's `spacing.txt`.

**It read all 64 crawls the queue held, and the window census is now complete:
0 of the 84 in-window crawls are unread.** Eight of them carry `/ipro/hcp/*` —
**28 members spanning 2017-06-26 → 2021-09-28**, dates this area had nothing for,
including `/ipro/hcp/privacy.jsf` and `/ipro/hcp/login.jsf?bhcp=1`, two paths new
to every corpus. **`CC-MAIN-2018-05`, the selection this pass left unenqueued, is
in that queue and answered.**

Two consequences for the figures this log published, both already corrected in
`docs/11` and `docs/10`:

- **The family is not a 2014-and-2020 artifact.** With 2017, 2019 (twice), 2020
  and 2021 (four times) all carrying captures, the "bounded 2020 deployment"
  reading this log helped refute was wrong in the same way — it read a *sparse*
  sweep as a *bounded* one. **The stronger statement the sweep now supports is the
  negative: `/ipro/hcp/` is absent from 65 of the 84 in-window crawls.**
- **The hole stays open and is now stated differently.** 41 of the 128 published
  indexes lie outside the window; this area has read exactly **one** of them, and
  that one — `CC-MAIN-2022-27` — carried a member. **A member outside the window
  has already refuted the window's sufficiency once.**

**Not restated here:** the family member table now lives in the continuation's
`census-84.txt` and `derive.py`, which read both this pass's ledger and that one.

### C8 — round 3: the same three figures, restated from the scripts rather than from memory

Round 3 confirmed this log's measurement and found the *publishing layer* broken.
Two of the three fixes touch figures this log published, so they are recorded here
as well as in the continuation's correction. **Zero new requests.**

**The budget figure.** This log's C1 corrected the algebra to `E[N] = 1 + p + p²`
and published **3.30** citing `budget.py` — but `budget.py` was computing `p` over
the **whole 40-row ledger** and printing **3.0312**, and had no way to be given the
29-row population the published figure used. **`budget.py` now takes a named
population** (`--population s-l2`: every row whose crawl is one of the **nine**
crawls this pass FIRST READ) and emits **3.2985**, which is the published 3.30
rounded. **`derive.py` §5 now prints the same number with its population rule**, so
the two cannot drift again.

**A correction to this log's C1 that round 3 forced.** C1 said the corrected model
is "conservative". It is conservative **only** at the failure rate it was fitted on:

| population | p | derived | measured | direction |
|---|---|---|---|---|
| S-L2 (29 rows) | 0.4483 | 3.2985 | 3.2222 | derived **ABOVE** by 2.4% |
| the continuation (188) | 0.3191 | 2.8420 | 2.9375 | derived **BELOW** by 3.3% |
| both ledgers (228) | 0.3289 | 2.8743 | 2.9610 | derived **BELOW** by 2.9% |

**A single population cannot license a claim about the error's sign.** No prose in
this repo asserts one now.

**The re-derivation over an empty set.** This log's `derive.py` §6 filtered
`crawl-window.txt` rows on `len(r) == 5`; that file's rows are **5** fields, so it
worked here. **The continuation's §6 had the same class of bug** against
`census-84.txt`, whose rows are **8** fields — it re-derived over an empty set and
printed `0` whatever the census said. Fixed there, and recorded here because it is
the same defect recurring in the script that inherited this log's method.

**The `## Correction` heading in this file's `derive.py`.** This log's C1 said the
dated heading was "the mechanism by which the file could be edited at all". **That
was false**: `check_append_only` does screen every file under `findings-log/` with
no extension filter, but the diff it reads is three-dot and every file here is
status `A`, which matches neither arm — **so the check never read the file and the
regex was never evaluated.** The gate did not force a Python file to contain
markdown; a person put it there. Corrected in the docstring, along with a
`SyntaxWarning` the non-raw `\(\d{4}` emitted on every run.

**Not corrected here, and unchanged:** the ledger (40 rows), the census cells, the
spacing floors, `CC-MAIN-2022-05`'s readable absence, `CC-MAIN-2014-23`'s
indeterminacy, the two-opposite-error account of the 87 → 84, and the claim that
`/ipro/hcp/*` is one surface over time — still **INFERRED and undemonstrated**.
