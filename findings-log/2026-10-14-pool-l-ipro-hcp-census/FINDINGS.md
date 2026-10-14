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