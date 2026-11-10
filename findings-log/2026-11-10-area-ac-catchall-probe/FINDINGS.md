# Area AC — the catch-all probe (claim #168), 2026-11-10

**The question this log answers, and it is one question:**

> Does `carelink.minimed.eu` run a catch-all on non-existent paths? If it does, every
> archived `404`-vs-`200` reading in this area's crawl record is uninterpretable, and
> *"is `/ipro/hcp/` retired"* is **unanswerable from crawl data at all**.

**Answer: NO at the apex, YES under `/app/`.** The host runs **two different handlers**,
selected by path prefix, and it says so in the `Content-Type`. `carelink.minimed.eu` is
**not** a whole-host catch-all — a fabricated path outside `/app/` gets a real `404` from
Apache, 196 B — but **every path under `/app/` returns the same 1 833-byte SPA shell
regardless of whether it exists**, including a name in no crawl record and no repository
file. So the status code is an oracle at the apex and **worthless** below `/app/`.

---

## 1. The census half was already complete — this log does not re-derive it

**Stated plainly, because re-running it would have been the mistake.** Area AC's
enumeration close-condition — *"enumerated rather than sampled, under a stated
completeness rule, with the nested-asset shapes either explained or recorded as
unexplained"* — **was already met on 2026-10-17**. That pass reached **0 of 44 unread**,
classified every cell, and returned **165 records over 27 distinct host-relative paths and
six hosts** across its 40 record cells; **five of the 44 carry a `/ipro/hcp/` member**, the
last dated **2026-06-10**, archived **404**. The five nested-asset shapes are **recorded as
unexplained** in that log's **F10a**, which is exactly what the close-condition permits
([findings-log/2026-10-17-sl2-outwindow-census/FINDINGS.md] §F2, §F5, §F10a).

**This pass sent zero requests to Common Crawl and read zero crawls.** The ~106-request
census is not repeated here; `docs/11` already cites that log for it, and it still does.

What the 2026-10-17 pass could **not** do is read the bodies — they are outside the tree by
`AGENTS.md` §7 — so whether those archived statuses were *served paths* or *a catch-all's
answers* was not decidable from a ledger, and that log said so in F10c: *"A `200` on this
host is not evidence of a served document … no pass has established which catch-all
`carelink.minimed.eu` runs."* **That gap is what this lane closes.**

## 2. Request accounting — 14 of a 20 cap

| | n |
|---|---|
| **Cap, declared before the first request** | **20** |
| Requests sent | **14** |
| Failures (`000`/5xx/timeout) | **0** |
| Retries | **0** (none needed) |
| Distinct hosts contacted | **1** — `carelink.minimed.eu` |
| Requests to any other vendor host | **0** (two sibling lanes held the other hosts) |
| Requests to Common Crawl | **0** |

The cap was itemised **before** the first request (2 controls + 5 shapes + 1 depth-4
duplicate + 1 fabricated-at-depth + retries + the gate's ~13 requests). Six rows of headroom
were then spent deliberately, and each is named in §5 with the reason it was needed:
one control repair, two `/ipro/hcp/` rows, and one `/app/` root. **Six rows remain unused.**

Method: **GET only**, `--compressed` on every request, a declared **≥ 2.5 s** same-host delay
slept **inside** `flock` on the per-host lock, measured floor **2.579 s between** consecutive
requests (§3). No POST, no OPTIONS, no token, no cookie, no auth, no wordlist
— the candidate list is the five recorded shapes plus the controls, and nothing else.

## 3. Measured spacing floor — 2.579 s, 13 gaps, 0 under the declared delay

`python3 spacing.py` (re-derivable from `results.jsonl` alone, no body file needed):

```
gaps 13   min 2.579 s   max 73.062 s   mean 9.820 s
under the declared 2.5 s: 0
under the repository 2.0 s floor: 0
negative durations: 0
FLOOR ON THIS CLOCK: 2.579 s
```

**OBSERVED: floor 2.579 s, 13 same-host gaps, 0 of 13 under 2.5 s, 0 under the 2 s
repository floor, 0 negative.** This is the first pass in several to record a floor above
its declared delay with no short gap and no backwards clock step — the running count of
those anomalies lives in `docs/09` §4 and this pass adds none to it.

The two long gaps (73.1 s, 26.1 s) are **not** anomalies: they are the boundaries between
`probe.sh` invocations, where the ledger was read and the next queue written. They are
recorded as measured rather than trimmed.

Body-file mtimes (clock B) are not published: `git` does not preserve them, so they are not
re-derivable from a clean clone and would be a promise the tree cannot keep.

## 4. Controls first — and one of the two controls corrected its own premise

Both controls were sent **before** any shape, because a status is not an oracle until it is
shown to discriminate. **Verdicts:**

| # | Control | Status | Content-Type | Bytes | sha256 (first 16) | Verdict |
|---|---|---|---|---|---|---|
| 1 | `/zz-ac-absent-20261110-probe.html` — **fabricated** | **404** | `text/html; charset=iso-8859-1` | 196 | `80c3fe2ae1062abf` | **PASS — the absent control really is absent** |
| 2 | `/robots.txt` — **expected live** | **404** | `text/html; charset=iso-8859-1` | 196 | `80c3fe2ae1062abf` | **FAILED AS DESIGNED — see below** |

**Control 1 is clean and its fabrication is verified, not assumed.** `git grep` over the
worktree for `zz-ac-absent` returns **0 hits** at the base commit — the name is in no crawl
record and no repository file. It answered **404**, so at the apex the status code **is** an
oracle.

**Control 2 refuted its own premise, and the refutation is a finding.** `/robots.txt` was
included because it is *"recorded as a live `200` on this host family"*. **It is not live on
this host**: it answers **`404`, byte-identical to the fabricated path** (same 196 bytes,
same digest `80c3fe2ae1062abf`). The confusion is traceable and worth naming — the census
records **two `/robots.txt` `403`s on `carelink.minimed.eu`** and a **`200` at `/` on
`carelink-stage3.minimed.eu`**, and a `404` at `/robots.txt` on that same host
([findings-log/2026-10-17-sl2-outwindow-census/FINDINGS.md:422-423]). **No crawl record in
this repository has ever recorded a `200` at `/robots.txt` on `carelink.minimed.eu`.** So the
control as specified could not be built from the record, and the corrected reading is:
**`/robots.txt` is NOT a served document on this host, and a `200` for it must never be
cited as one.**

Because the "certainly exists" control did not exist, a **second, stronger** live control was
run — **`/app/`**, the SPA's own root, which must be served for the patient app to work at
all (row 14): **`200` `text/html; charset=UTF-8`, 1 833 B, digest `8dfb96a70999bdb4`**.
That one passes and it is the control that carries weight, because a real document's shape
is what makes the catch-all's identical shape meaningful.

**Consequence for the oracle, stated precisely:** the apex status code discriminates
(`404` real, `200` real), and **the `/app/` status code does not** — see §5.

## 5. The shape table — five recorded shapes, and the discriminator

Every row below is **OBSERVED**, live, this pass. `matches fabricated-path digest` asks the
decisive question: is this response indistinguishable from the one a name that has never
existed gets?

| # | Path | Status | Content-Type | Bytes | sha256 (first 16) | = fabricated-path digest? |
|---|---|---|---|---|---|---|
| 3 | `/assets/javascript-warning.html` (**apex**) | `200` | `text/html; charset=UTF-8` | 1 180 | `11321752d74eea41` | **No** — a distinct body |
| 4 | `/app/assets/javascript-warning.html` (depth 1) | `200` | `text/html; charset=UTF-8` | 1 833 | `8dfb96a70999bdb4` | **Yes** |
| 5 | `/app/assets/assets/javascript-warning.html` (depth 2) | `200` | `text/html; charset=UTF-8` | 1 833 | `8dfb96a70999bdb4` | **Yes** |
| 6 | `/app/assets/assets/assets/javascript-warning.html` (depth 3) | `200` | `text/html; charset=UTF-8` | 1 833 | `8dfb96a70999bdb4` | **Yes** |
| 7 | `/app/assets/assets/assets/assets/javascript-warning.html` (depth 4) | `200` | `text/html; charset=UTF-8` | 1 833 | `8dfb96a70999bdb4` | **Yes** |
| 8 | depth 4, **duplicate request** | `200` | `text/html; charset=UTF-8` | 1 833 | `8dfb96a70999bdb4` | **Yes** — digest stable across two requests |

**The discriminator rows — the ones that settle it:**

| # | Path | Status | Content-Type | Bytes | sha256 (first 16) | Reading |
|---|---|---|---|---|---|---|
| 9 | `/app/assets/zz-ac-absent-20261110-probe.html` — **fabricated, depth 1** | **200** | `text/html; charset=UTF-8` | 1 833 | `8dfb96a70999bdb4` | **A name that never existed returns the same 1 833 bytes as shape 4** |
| 10 | `/app/assets/assets/assets/assets/zz-ac-absent-20261110-probe.html` — **fabricated, depth 4** | **200** | `text/html; charset=UTF-8` | 1 833 | `8dfb96a70999bdb4` | **Same again at the deepest nesting** |
| 11 | `/assets/zz-ac-absent-20261110-probe.html` — **fabricated, apex `/assets/`** | **404** | `text/html; charset=iso-8859-1` | 196 | `80c3fe2ae1062abf` | **Apex `/assets/` is NOT caught** |
| 14 | `/app/` — **known live** | `200` | `text/html; charset=UTF-8` | 1 833 | `8dfb96a70999bdb4` | **The same body as the catch-all** |

**OBSERVED, and this is the finding in one line: one digest, `8dfb96a70999bdb4`, covers a
path that certainly exists (`/app/`), four recorded nesting depths, and two names invented
in this pass. There is no depth at which the fabricated name and the real path differ.**

**Two distinct handlers, selected by prefix.** Rows 1/2/11/12/13 share **one** 196-byte
`iso-8859-1` Apache 404 (`server: Apache/2.4.62`, `x-cache: Error from cloudfront`); rows
3–10 and 14 share **one** `UTF-8` document or its `gzip` twin. The split is not the status
code — it is **path prefix** (`/app/…`) and it is visible in `Content-Type`.

**Row 3 is the informative exception.** The apex `/assets/javascript-warning.html` is a
**distinct 1 180-byte body**, *not* the 1 833-byte shell, and it is a served document: a
`<title>CareLink</title>` no-script warning page that does `location.href = '/'`. So the
apex shape in F10a is **a real asset**, and its four `/app/`-nested siblings are **the SPA
shell under four different prefixes** — which are the same bytes because the shell is
served at every `/app/` prefix by construction.

**The F10a nesting pattern is therefore explained in the one direction the ledger could
not see** (INFERRED, and labelled as such): a crawler following `/app/assets/assets/…`
accumulates real `200`s at each depth **because the `/app/` catch-all serves them**, not
because four documents exist at four depths. **Which came first — the crawler's URLs or the
vendor's rewrite — is not established**, and no crawl record can settle it: once a URL is
under `/app/`, the origin answers `200` whether the path means anything or not.

## 6. Verdict

**`carelink.minimed.eu` runs a catch-all under `/app/` and does not run one anywhere else.**
OBSERVED on 14 GETs, controls first, 0 failures, floor 2.579 s.

- **Not a whole-host catch-all.** `AGENTS.md` §7's warning is written for
  `carelinkhp.minimed.eu`, which answers `200 text/html` for **every** path. This host does
  **not** behave that way: `/zz-ac-absent-…html`, `/assets/zz-ac-absent-…html`,
  `/ipro/hcp/`, `/ipro/hcp/index.html` and `/robots.txt` all answer real **404**s with one
  shared digest. **The two hosts are measurably different and must not be described alike.**
- **But under `/app/` the status code carries no information.** Two never-existent paths,
  at two depths, answered `200` with the byte-identical body a real path gets. So for any
  archived URL under `/app/`, **`200` proves nothing and `404` cannot occur** — and every
  F10a nested shape is under `/app/`.

## 7. What this means for `/ipro/hcp/` — the sentence the area exists for

**The `/ipro/hcp/` rows in this area's record are on the right side of the split, so they
remain readable — and they still do not date a retirement.**

Live, this pass (rows 12, 13): `/ipro/hcp/` → **`404`** `iso-8859-1`, 196 B, digest
`80c3fe2ae1062abf`; `/ipro/hcp/index.html` → **the same 404, same digest**. Both are
**indistinguishable from the fabricated control** — so `/ipro/hcp/` is **not served today**,
and that is a fact the catch-all does **not** contaminate, because `/ipro/hcp/` is outside
`/app/` where the 404 oracle holds.

**What is still not answerable:** *when* it stopped being served, and *whether* the archived
`404`s record retirement or a gate. A live `404` today is consistent with retirement, a
gate, and rewriting, exactly as `docs/11` already says, and **nothing here separates the
three**. What this pass adds is the elimination of a confound the area could not previously
rule out for the nested shapes — not a date.

**The limit, stated plainly and not overstated:** the catch-all is real, but it is
**prefix-scoped**, so the strong form of the warning in the area's own text — that *"every
archived 404 in this area's record is indistinguishable from a served catch-all 404, so
'is `/ipro/hcp/` retired' becomes UNANSWERABLE from crawl data at all"* — **does not hold as
written**. It holds for the **nested `/app/` shapes** and **not** for `/ipro/hcp/`. The
weaker and correct statement is: **crawl data cannot interpret an archived status for any
`/app/…` URL on this host**, and it can still read a `/ipro/hcp/` `404` as a genuine
non-served answer on the day it was fetched. **A measurement limitation, not a disclosure:
the vendor is not shown to be hiding anything, and this is not a security finding.**

## 8. Successor — derived from what was measured, not from what was expected

The successor the brief anticipated ("is the catch-all host-specific or family-wide?") is
**still the right question, and this pass sharpens it**: the catch-all is not a host
property, it is a **prefix** property, so the cross-host probe must ask **which prefixes each
host serves a shell at**, not merely whether a host catches all. `.com` and `-trials` are
untested on `/app/`, and `AGENTS.md` §7 records `carelinkhp.minimed.eu` as catching
**everything** — two different mechanisms under one word, which a family-wide probe would
have to separate. **Needs its own claim and its own cap.**

Not claimed here: that `.com`/`-trials` behave alike (INFERRED and untested, as `docs/11`
already records for the asset paths); that the shell's presence implies an app route behind
it; that the `/app/` rewrite is deliberate vendor behaviour rather than an SPA fallback
default. **No mechanism is asserted.**

## 9. What this pass does **not** say

- **It does not re-derive the census** and makes no new claim about Common Crawl: 0 requests
  to `index.commoncrawl.org` or `data.commoncrawl.org`. The 165-records / 27-paths / six-hosts
  and 5-of-44 `/ipro/hcp/` figures are **cited** from 2026-10-17, not re-measured.
- **It does not say `/ipro/hcp/` is retired.** It says it is **not served today** (live
  `404`, apex oracle holding) and that the archived `404`s do not date the change.
- **It does not call the catch-all a vulnerability, a disclosure, or evidence of hiding.**
  An SPA serving its shell at every prefix is ordinary behaviour. It is recorded as a
  **measurement limitation**.
- **It did not contact any other Medtronic host**, holds no credential, and no `regression/`
  pin was added — an SPA shell and an Apache 404 are not API surfaces, and `AGENTS.md` §11
  bars a research pass from widening the gate's budget.
- **It does not claim `/robots.txt` is absent**; it says this host answered `404` today and
  that no record in this repository has ever shown a `200` for it here.

## 10. Files, and how to re-run

| File | What it holds |
|---|---|
| `probe.sh` | Called `CAP=20` as **one assignment** with the itemisation beside it; GET only, `--compressed`, sleep inside `flock` |
| `queue.tsv`, `queue2.tsv`, `queue3.tsv` | The candidate lists, in the order sent — three files because the cap was read before each top-up |
| `row.py` | One response → one ledger row; commits status / content-type / bytes / sha256 / redacted `body_head` only |
| `results.jsonl` | 14 rows, every attempt its own row |
| `run.log`, `run.log.capped` | Human-readable ledger + the final `DONE — 14 of 20` line |
| `headers/` | Response headers per row (safe: no session value; `jsessionid_redacted: 0` on every row) |
| `spacing.py` → `spacing.txt` | Zero-request re-derivation of the delay series from `results.jsonl` alone |

**Bodies are not in the tree** (`AGENTS.md` §7). Re-run:

```bash
L_LOCK=<pool>/.loop/host-carelink.minimed.eu.lock L_BODIES=<scratch> ./probe.sh queue.tsv
```

**No raw capture, no `.gz`/`.warc`/`.cdx` archive, and no file over 2 KiB is committed.**
