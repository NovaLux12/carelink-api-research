# Area O — is `/patient/reports/*` the reports surface for every region?

Run date: **2026-10-12**. Claim issue:
[#24](https://github.com/NovaLux12/carelink-api-research/issues/24).
Harness: [`probe.sh`](probe.sh). Corpus: [`results.jsonl`](results.jsonl) — one
row per request. Request ledger: [`run.log`](run.log). Every table below is
rendered from the ledger by [`verdict.py`](verdict.py) (output
[`verdict.txt`](verdict.txt), spacing [`verdict-spacing.txt`](verdict-spacing.txt)),
which issues no requests.

**Timing has a second, better oracle**: [`mtime.py`](mtime.py) →
[`mtime.txt`](mtime.txt), built from the kernel mtimes of the capture files that
curl itself wrote. It **supersedes** `run.log` for timing, because `run.log`'s
`t0` is provably corrupt on two rows. `verdict-spacing.txt` is kept and labelled
as the superseded reading so the retraction history stays visible.

This file records **what came back off the wire** and what it does and does not
license anyone to conclude. It assigns evidence classes and marks the one place
where it must be read against a corrected provenance.

---

## 0. Answer in one line

**The reports namespace is on all three patient deployments, not just the EU
one — and the seven recorded status codes reproduce exactly, live, on every one
of them.** The area's own INFERRED premise ("the three patient deployments
expose the same namespace") is **confirmed**, not assumed. The remaining open
question (#76) is therefore no longer *which host* — it is only *what a body
says*, which needs a token.

---

## 1. Request accounting

**24 of a 30 cap.** The cap is the one declared in issue #24. Used: **24**,
all from the harness. Zero hurl pin-validation requests were counted separately
— see **§10** for where the five new pins were validated and why they are not
double-counted here. `wc -l results.jsonl` = **24**; `run.log` holds exactly
**24** request lines with `seq` contiguous 1..24, no gaps and no extras; both
counters were asserted, not eyeballed (`verdict.py` re-checks contiguity).

- Every request was a **GET**. No POST, no `-X`, no `-d`, no token exchange, no
  authentication, no port scan, no DNS. No `Authorization`, no `Cookie`, no
  `x-api-key` was sent. The only header sent beyond a default curl is
  `User-Agent: carelink-bridge-research/1.0` — deliberately the same UA
  `regression/hurl/05-public-config.check.sh` uses, so these rows are comparable
  with the existing corpus.
- `probe.sh` carries a `CAP=30` guard that exits 9 before issuing a request past
  the cap, and refuses to run a second time if `results.jsonl` or `run.log`
  already exists. The harness count cannot silently double.
- **Three hosts × 8 requests** = 24: per host, one certainly-absent control, one
  known-live control (which is simultaneously candidate 1 of the seven), and the
  six remaining candidates.
- The harness's adaptive branch — a third control, spent only if the known-live
  control came back `404` — **never fired**, because `supported` returned `401`
  on all three hosts. It cost 0 requests.
- **Nothing that came back is sensitive.** The two `Set-Cookie` headers on the
  `401`s carry **empty values** with `Max-Age=0` and an epoch `Expires` — they
  are deletions, not grants. The recorded values in full are
  `auth_tmp_token=""` and `c_token_valid_to=""`. The `400` body is a bean
  validation error naming a method argument. No credential, no patient
  identifier, no internal hostname appears anywhere in this directory, and the
  repository's own scrub list was run over every file here (§9).

### 1a. Delay between requests — **a breach, stated plainly**

**Declared delay between requests to the same host: 2.5 s apart**, which is what
`DELAY=2.5` in `probe.sh` sets and what the repository requires as a minimum of
2 s. **It was not applied.** `probe.sh` declares `DELAY=2.5` and the lock section
is commented "sleep + curl" — but **`sleep` was never emitted into `req()`**. All
24 requests therefore went out spaced only by curl's own round trip.

**The pass originally measured that from `run.log`. It should not have: `run.log`
is wrong.** A second oracle exists and is better — the **kernel mtimes of the
`headers/*.b` and `headers/*.h` files**, which curl itself wrote, spanning the
same 24 requests. It is rendered by [`mtime.py`](mtime.py) into
[`mtime.txt`](mtime.txt); it issues no requests.

**The measurement, both ways. The body-mtime column is authoritative; the
`run.log` column is retained so the retraction history stays visible.**

#### `mtime - t0` per row — the arithmetic that convicts `run.log`

| seq | `t0` (run.log, UTC) | body mtime (UTC) | `mtime - t0` | verdict |
|---|---|---|---|---|
| 1 | 18:01:49.22 | 18:01:49.37 | **+0.153 s** | ok |
| 2 | 18:01:49.42 | 18:01:49.47 | **+0.048 s** | ok |
| 3 | 18:01:49.51 | 18:01:49.56 | **+0.049 s** | ok |
| 4 | 18:01:49.61 | 18:01:49.66 | **+0.047 s** | ok |
| 5 | 18:01:49.70 | 18:01:49.75 | **+0.047 s** | ok |
| 6 | 18:01:49.80 | 18:01:49.84 | **+0.046 s** | ok |
| 7 | 18:01:49.89 | 18:01:49.94 | **+0.049 s** | ok |
| 8 | 18:01:49.99 | 18:01:50.03 | **+0.046 s** | ok |
| 9 | 18:01:50.93 | 18:01:50.46 | **-0.463 s** | **IMPOSSIBLE — `t0` is corrupt** |
| 10 | 18:01:50.51 | 18:01:50.63 | **+0.122 s** | ok |
| 11 | 18:01:50.68 | 18:01:50.79 | **+0.114 s** | ok |
| 12 | 18:01:50.84 | 18:01:51.11 | **+0.265 s** | ok |
| 13 | 18:01:51.16 | 18:01:51.42 | **+0.261 s** | ok |
| 14 | 18:01:51.47 | 18:01:51.58 | **+0.112 s** | ok |
| 15 | 18:01:51.63 | 18:01:51.74 | **+0.118 s** | ok |
| 16 | 18:01:51.79 | 18:01:51.94 | **+0.149 s** | ok |
| 17 | 18:01:52.14 | 18:01:52.38 | **+0.239 s** | ok |
| 18 | 18:01:52.46 | 18:01:52.57 | **+0.116 s** | ok |
| 19 | 18:01:52.69 | 18:01:52.96 | **+0.274 s** | ok |
| 20 | 18:01:53.78 | 18:01:53.20 | **-0.587 s** | **IMPOSSIBLE — `t0` is corrupt** |
| 21 | 18:01:53.25 | 18:01:53.51 | **+0.267 s** | ok |
| 22 | 18:01:53.56 | 18:01:53.68 | **+0.114 s** | ok |
| 23 | 18:01:53.74 | 18:01:53.86 | **+0.122 s** | ok |
| 24 | 18:01:53.98 | 18:01:54.10 | **+0.119 s** | ok |

**22 of 24 rows** fall in a tight **+0.046…+0.274 s** band — exactly what
`t0`-then-`curl` predicts. The only rows outside it are **seq 9** (-0.463 s), **seq 20** (-0.587 s).

`t0` is read **before** curl, so `mtime - t0` cannot be negative. On those two
rows it is. Whatever the mechanism, **those two `t0` reads are wrong**, and
they are precisely the two rows that produce the negative gaps in `run.log`.

#### Same-host gaps, measured two ways

| Measure | body mtimes (**authoritative**) | `run.log` `t0` (**superseded**) |
|---|---|---|
| same-host gaps measured | 21 | 21 |
| minimum gap | **+0.092 s** | -0.538 s |
| maximum gap | **+0.387 s** | +1.097 s |
| negative gaps | **0** | 2 |
| gaps >= 2.5 s (declared) | 0 | 0 |
| gaps >= 2.0 s (**AGENTS.md section 8 floor**) | **0** | 0 |
| gaps < 2.0 s — **rule breach** | **21** of 21 | 21 of 21 |

**No overlap.** Every mtime delta is positive and the 24 mtimes are strictly
increasing, so the 24 requests were issued sequentially and never concurrently.
The negative gaps in `run.log` are an artefact of two corrupt `date` reads, not
evidence of concurrent requests.

#### Correction to this pass's own reported figure

| Figure | first reported | corrected | direction |
|---|---|---|---|
| minimum same-host gap | -0.538 s | **+0.092 s** | **understated the breach** |
| maximum same-host gap | +1.097 s | **+0.387 s** | overstated the spread |
| negative gaps | 1 reported | **2** | undercounted |

The corrected minimum is **higher** than the reported one, so the pass
**understated how badly it breached the floor**: no gap here was negative, and
no gap came within 1.6 s of the 2 s requirement.


**Read the two tables together.** They agree that the floor was breached on
**21 of 21** same-host gaps and that **not one** reached either 2.5 s or the 2 s
minimum. They disagree about *how bad*, and the disagreement matters:

1. **The pass understated its own breach.** It reported a minimum of **−0.538 s**
   — which read like requests overlapping. They did not. The physical minimum is
   **+0.092 s**, and the true maximum is **+0.387 s**. The cleanest derivation of
   how far short the run fell needs no per-gap statistic: 24 requests at the
   declared 2.5 s is a **60 s** budget, and the capture spans **4.728 s**, so the
   run was **12.7× short of its own declared pacing** (60 ÷ 4.728). Per-gap, the
   mean gap is 0.184 s (**13.6×** fast) and the median 0.166 s (**15.1×**). An
   earlier draft of this line said "~20×", which no derivation here supports —
   only the single fastest gap (2.5 ÷ 0.092 = 27.2×) reaches that figure — so the
   number is replaced by the derivations above rather than rounded. A negative
   number in that column invited the reader to conclude concurrency and to
   discount the politeness question; the number that should have carried that
   weight was the *positive floor*, not a spurious negative.
2. **There was no overlap, and that is now established rather than assumed.** The
   24 body mtimes are **distinct and strictly increasing by `seq`**, so the 24
   requests were issued sequentially and never concurrently.
3. **The negative gaps are two corrupt `date` reads, not a clock signature worth
   theorising about.** `t0` is taken *before* curl, so `mtime - t0` must be
   positive. On **22 of 24** rows it is, in a tight **+0.046…+0.274 s** band that
   is exactly what `t0`-then-`curl` predicts. On **seq 9** it is **−0.463 s** and
   on **seq 20** it is **−0.587 s** — arithmetically impossible for a correctly
   read `t0`, and precisely the two rows that manufacture the negative gaps in
   `run.log`. **No cause is asserted**, per `docs/09` §4's own instruction not to
   theorise about this artefact.
4. **A third clock agrees, and it is not ours.** The `Date:` response header in
   each captured head is written by **Medtronic's server**, for no timing purpose,
   at 1-second granularity — too coarse to measure sub-second gaps, but enough to
   decide **order**. It is **strictly monotonic across all 24 rows**
   (18:01:49 → 18:01:54 UTC, **zero inversions**), and it orders the requests the
   same way the local kernel mtimes do. Two clocks, on two different machines,
   agree; only `run.log`'s `t0` dissents, and only on seq 9 and seq 20.

**This is a breach of AGENTS.md §8, and it is not smoothed over.** Areas B, X and
Z each recorded same-host gaps a few hundredths under their declared 2.5 s, and
all of those stayed **above** the 2 s floor; this run is a different and worse
class, because no gap here comes within 1.6 s of the floor. The cause is not a
clock artefact and not a measurement artefact: it is the missing `sleep`.

**The negative-gap count was undercounted at one; it is two.** `run.log` contains
**two** backwards steps — **seq 9 → 10 (−0.415 s)** and **seq 20 → 21
(−0.538 s)** — and this section originally reported only the second. That is one
more occurrence of the `docs/09` §4 artefact, which is updated to **4 passes / 9
occurrences** in this PR.

**The run was not repeated.** A clean re-run is 24 further requests on top of the
24 already sent, which would exceed the 30-request cap committed in #24 — fixing
one committed limit by breaking another is not a repair, and it would double the
vendor traffic that has already mis-paced. Six requests of budget remain
unspent.

**Does the breach affect the findings?** The claims below are per-request
observations — a status code, a `Content-Type`, a body digest, a header's
presence. None of those is a function of request rate, and no response here
varied within a path across the three hosts (§5), which is itself weak evidence
against rate-dependent behaviour. What the breach does affect is **the conduct of
the probe against a third party's servers**, and that is the part being reported,
not excused. A reader weighting this pass should discount the politeness of it
entirely and not discount the rows.

### 1b. Post-run edit to `probe.sh` — declared, with the diff

`probe.sh` was edited **after** the run, twice, both times in ways that cannot
touch a request:

1. **`REPO=` was made portable.** The executed version carried an absolute
   machine path for the shared lock directory, which is on the repository's
   scrub list (`machine-specific paths`, `scripts/scrub-patterns.txt`). It now
   reads `REPO="${CARELINK_LOOP_ROOT:-$HOME/.openclaw/workspace/projects/novas-github/carelink-api-research}"`.
   Verified to resolve to the identical directory the run used. The file is a
   record of the harness; the run itself is recorded in `results.jsonl`.
2. **`sleep "$DELAY"` was added** to `req()`, immediately after `flock "$LOCKFD"`
   and before `curl`, so the committed harness is re-runnable at the declared
   pacing. Plus a banner at the top of the file recording the breach, so nobody
   re-runs it believing the committed version is what produced these artefacts.

Neither edit changes a URL, a header, a candidate list, a cap, or the order of
requests. The executed artefacts — `results.jsonl`, `run.log`, `headers/` — are
preserved byte-for-byte and were not regenerated.

---

## 2. The candidate list, and a provenance correction

The seven paths are taken **verbatim** from
[`findings-log/probe-2026-10-08/recon/ARCHIVE-URLS.md:162`](../probe-2026-10-08/recon/ARCHIVE-URLS.md).
The list was not re-derived per host, not expanded, and not guessed.

**Correction — the recorded verdicts are ARCHIVE verdicts, not live ones.** The
same file states the rule at
[`ARCHIVE-URLS.md:302`](../probe-2026-10-08/recon/ARCHIVE-URLS.md):
"status codes as archived, **not** as measured live today", and the family table
at [`ARCHIVE-URLS.md:329`](../probe-2026-10-08/recon/ARCHIVE-URLS.md) gives
the window as **first 2020-09-29, last 2021-03-31**. So the `(401)`, `(405)`,
`(400)`, `(404)` on line 162 are codes from Wayback captures ending **more than
five years ago**.

This matters because the repo presented those codes as a live observation.
[`docs/00-summary-the-map.md`](../../docs/00-summary-the-map.md) — **as it stood
before this pass's edit**, quoted here so the citation stays checkable — read
"`/patient/reports/*` **on `carelink.minimed.eu`** — **Live, gated 401/405**",
citing the 2026-10-10 sweep.

**The 2026-10-10 artefact's own provenance is weaker than a "JS-bundle scan".**
[`DRIFT-AND-NEW-2026-10-10.md:9`](../probe-2026-10-08/recon/DRIFT-AND-NEW-2026-10-10.md)
opens with: *"this file is a **reconstruction from the agent's report**, because
the agent's own file was never written to disk… the command-level evidence table
is **not reproduced here**… **Re-verify before treating any row as OBSERVED**."*
So the row `docs/00` leaned on was never an OBSERVED capture by its own account;
it is a secondhand report with no command-level evidence committed. **An earlier
draft of this section called it "a JS-bundle scan" — that understated how weak
the provenance is, and is corrected here.**

On top of that, the bundle inventory the 2026-10-10 sweep produced
([`JS-API-SURFACE.md`](../probe-2026-10-08/recon/JS-API-SURFACE.md)) carries
**none** of the camelCase names: `snapshotTimelinesRange` and `favoriteReports`
appear nowhere in it, and its `generateReport` / `reportStatus` hits are the
`hcp/reports/*` and `commoncore /reports/*` namespaces, which are different
paths. Searching the whole committed corpus **as it stood before this pass**,
the only file naming `snapshotTimelinesRange` was `ARCHIVE-URLS.md:162` itself.

**So the labels were right about the value and wrong about the evidence class:
there was no live probe behind "Live".** This pass is the first live
measurement of these seven paths on any host. The value is unchanged; the
sourcing is now real. The original reading is left visible in `docs/` alongside
its correction, per AGENTS.md §3 — a correction does not erase the original.

**An ambiguity in the source, resolved.** Line 162 sits under the heading
"Reports (the generation catalogue that `commoncore.medtronic.eu` now serves)",
which invites the reading that those codes describe `commoncore`'s `/reports/*`
rather than `/patient/reports/*`. They cannot: `commoncore.medtronic.{eu,com}`
returns **502** on `/reports-broker/v1/ocl`
([`docs/00`](../../docs/00-summary-the-map.md), the `commoncore` row), and the
codes on line 162 are 401/405/400/404. They are `/patient/reports/*` codes, and
this pass reproduces exactly those numbers on the `/patient/reports/*` paths —
which settles it.

---

## 3. Controls — 6, sent before any candidate on every host

Per the claim issue: a **certainly-absent** path under the same prefix and a
**known-live recorded** path, both sent **first** on every host. The absent path
carries a run-unique suffix (`this-does-not-exist-ocl-probe-<UTC timestamp>`) so
it cannot have been served before by anything, including a parked front door.

| # | Host | Path | Role | Status | `Content-Type` | Bytes | body sha256 | `x-ca-err` | What it establishes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `carelink.minimed.eu` | `/patient/reports/(certainly-absent)` | CONTROL-certainly-absent-same-prefix | **404** | (none) | 0 | `e3b0c44298fc` | (none) | what **dead** looks like on this host |
| 2 | `carelink.minimed.eu` | `/patient/reports/supported` | CONTROL-known-live-and-CANDIDATE-1-of-7 | **401** | application/json | 48 | `247825a42646` | 990 | the namespace is routed here (this row is also candidate 1 of 7) |
| 3 | `carelink.minimed.eu` | `/patient/reports/snapshotTimelinesRange` | CANDIDATE-snapshotTimelinesRange | **401** | application/json | 48 | `247825a42646` | 990 |  |
| 4 | `carelink.minimed.eu` | `/patient/reports/generateReport` | CANDIDATE-generateReport | **405** | (none) | 0 | `e3b0c44298fc` | (none) |  |
| 5 | `carelink.minimed.eu` | `/patient/reports/favoriteReports` | CANDIDATE-favoriteReports | **405** | (none) | 0 | `e3b0c44298fc` | (none) |  |
| 6 | `carelink.minimed.eu` | `/patient/reports/snapshotTimelinesForCalendar` | CANDIDATE-snapshotTimelinesForCalendar | **405** | (none) | 0 | `e3b0c44298fc` | (none) |  |
| 7 | `carelink.minimed.eu` | `/patient/reports/reportStatus` | CANDIDATE-reportStatus | **400** | application/json | 130 | `216c87d78184` | (none) |  |
| 8 | `carelink.minimed.eu` | `/patient/reports/report` | CANDIDATE-report | **404** | (none) | 0 | `e3b0c44298fc` | (none) |  |
| 9 | `carelink.minimed.com` | `/patient/reports/(certainly-absent)` | CONTROL-certainly-absent-same-prefix | **404** | (none) | 0 | `e3b0c44298fc` | (none) | what **dead** looks like on this host |
| 10 | `carelink.minimed.com` | `/patient/reports/supported` | CONTROL-known-live-and-CANDIDATE-1-of-7 | **401** | application/json | 48 | `247825a42646` | 990 | the namespace is routed here (this row is also candidate 1 of 7) |
| 11 | `carelink.minimed.com` | `/patient/reports/snapshotTimelinesRange` | CANDIDATE-snapshotTimelinesRange | **401** | application/json | 48 | `247825a42646` | 990 |  |
| 12 | `carelink.minimed.com` | `/patient/reports/generateReport` | CANDIDATE-generateReport | **405** | (none) | 0 | `e3b0c44298fc` | (none) |  |
| 13 | `carelink.minimed.com` | `/patient/reports/favoriteReports` | CANDIDATE-favoriteReports | **405** | (none) | 0 | `e3b0c44298fc` | (none) |  |
| 14 | `carelink.minimed.com` | `/patient/reports/snapshotTimelinesForCalendar` | CANDIDATE-snapshotTimelinesForCalendar | **405** | (none) | 0 | `e3b0c44298fc` | (none) |  |
| 15 | `carelink.minimed.com` | `/patient/reports/reportStatus` | CANDIDATE-reportStatus | **400** | application/json | 130 | `216c87d78184` | (none) |  |
| 16 | `carelink.minimed.com` | `/patient/reports/report` | CANDIDATE-report | **404** | (none) | 0 | `e3b0c44298fc` | (none) |  |
| 17 | `carelink-trials.minimed.com` | `/patient/reports/(certainly-absent)` | CONTROL-certainly-absent-same-prefix | **404** | (none) | 0 | `e3b0c44298fc` | (none) | what **dead** looks like on this host |
| 18 | `carelink-trials.minimed.com` | `/patient/reports/supported` | CONTROL-known-live-and-CANDIDATE-1-of-7 | **401** | application/json | 48 | `247825a42646` | 990 | the namespace is routed here (this row is also candidate 1 of 7) |
| 19 | `carelink-trials.minimed.com` | `/patient/reports/snapshotTimelinesRange` | CANDIDATE-snapshotTimelinesRange | **401** | application/json | 48 | `247825a42646` | 990 |  |
| 20 | `carelink-trials.minimed.com` | `/patient/reports/generateReport` | CANDIDATE-generateReport | **405** | (none) | 0 | `e3b0c44298fc` | (none) |  |
| 21 | `carelink-trials.minimed.com` | `/patient/reports/favoriteReports` | CANDIDATE-favoriteReports | **405** | (none) | 0 | `e3b0c44298fc` | (none) |  |
| 22 | `carelink-trials.minimed.com` | `/patient/reports/snapshotTimelinesForCalendar` | CANDIDATE-snapshotTimelinesForCalendar | **405** | (none) | 0 | `e3b0c44298fc` | (none) |  |
| 23 | `carelink-trials.minimed.com` | `/patient/reports/reportStatus` | CANDIDATE-reportStatus | **400** | application/json | 130 | `216c87d78184` | (none) |  |
| 24 | `carelink-trials.minimed.com` | `/patient/reports/report` | CANDIDATE-report | **404** | (none) | 0 | `e3b0c44298fc` | (none) |  |

**All 6 controls passed, and the status oracle held on all three hosts.** On
every host the certainly-absent path returned **404** — so `404` on this host
family really is "no route", not a uniform front-door answer, and the
discriminator the area proposed (405 = POST-only and live, 401 = live and
token-gated, 404 = no route) is sound here. That is worth stating because
`docs/09` §2 records that on the `clcloud.*` API-Gateway family the status line
is **uniform and useless** and `x-amzn-errortype` is the real signal; this is
the opposite case and the controls are what make the difference defensible.

The known-live control is `/patient/reports/supported`, which is simultaneously
**candidate 1 of the seven** — one request, two roles, recorded with
`role: CONTROL-known-live-and-CANDIDATE-1-of-7` so the ledger never pretends to
have more rows than it has.

---

## 4. The seven-path row, three hosts

| Path | archive verdict (ARCHIVE-URLS.md:162) | `carelink.minimed.eu` | `carelink.minimed.com` | `carelink-trials.minimed.com` | identical across all 3? |
|---|---|---|---|---|---|
| `/patient/reports/supported` | 401 | 401 | 401 | 401 | **yes** |
| `/patient/reports/snapshotTimelinesRange` | 401 | 401 | 401 | 401 | **yes** |
| `/patient/reports/generateReport` | 405 | 405 | 405 | 405 | **yes** |
| `/patient/reports/favoriteReports` | 405 | 405 | 405 | 405 | **yes** |
| `/patient/reports/snapshotTimelinesForCalendar` | 405 | 405 | 405 | 405 | **yes** |
| `/patient/reports/reportStatus` | 400 | 400 | 400 | 400 | **yes** |
| `/patient/reports/report` | 404 | 404 | 404 | 404 | **yes** |

**Every one of the seven archived codes reproduces exactly, live, on all three
hosts — 21 of 21 cells matching the archive.** Not "approximately": the `401`s
carry the same 48-byte body digest, the `405`s the same 0-byte digest, the `400`
the same 130-byte digest, on every host.

**Verdict: the area's premise is confirmed and its negative arm is confirmed.**
This is not the "404 on both siblings" outcome the area anticipated — it is
strictly better, because the namespace is present everywhere.

---

## 5. Cross-host identity — no region split

| Path | statuses equal | bodies equal (sha256) | byte counts |
|---|---|---|---|
| `/patient/reports/supported` | yes | yes — `247825a42646` | 48/48/48 |
| `/patient/reports/snapshotTimelinesRange` | yes | yes — `247825a42646` | 48/48/48 |
| `/patient/reports/generateReport` | yes | yes — `e3b0c44298fc` | 0/0/0 |
| `/patient/reports/favoriteReports` | yes | yes — `e3b0c44298fc` | 0/0/0 |
| `/patient/reports/snapshotTimelinesForCalendar` | yes | yes — `e3b0c44298fc` | 0/0/0 |
| `/patient/reports/reportStatus` | yes | yes — `216c87d78184` | 130/130/130 |
| `/patient/reports/report` | yes | yes — `e3b0c44298fc` | 0/0/0 |

All seven responses are **byte-identical across the three hosts**, by sha256 of
the decompressed body. Whatever region-aware behaviour this namespace has, it is
**not** in the unauthenticated response. That is the finding: there is no
region split to document.

---

## 6. Four things this pass saw that no prior note records

These are observations from the same 24 responses, not extra requests.

### 6a. `Allow: POST, OPTIONS` on all nine `405`s — and on nothing else

All nine `405` responses carry **`Allow: POST, OPTIONS`**. On the remaining 15 —
the six `401`s, the three `400`s and the six `404`s — the header is **absent**.
So within this namespace `Allow` appears on **9 of 24** responses and correlates
exactly with the `405`.

`Allow` is **not** new to this host family, and this pass does not claim it: the
patient-plane table already records `Allow: HEAD, GET, OPTIONS` on
`/patient/monitor/data` and `Allow: POST, OPTIONS` on
`/patient/dataUpload/recentUploads`
([`docs/06:27,32`](../../docs/06-patient-api-surface.md)), and — recorded in the
same table — **`/patient/connect/data` carries no `Allow` header at all**
([`docs/06:28`](../../docs/06-patient-api-surface.md)). Those are `.eu` rows
from the 2026-10-08 pass on different paths.

What this pass adds is the per-route pattern on a namespace nobody had sampled:
**on `/patient/reports/*`, `Allow` is present on the POST-only routes and absent
everywhere else**, now confirmed across **all three** patient hosts rather than
one. That matters for method authority: [`docs/09` §4](../../docs/09-methodology-and-oracles.md)
records that across all 42 captured `clcloud.*` responses **not one carried
`Allow`**, so on that family the GET probe was the only authority available. On
the `carelink.*` patient plane the header exists and agrees with the `405` — which
means `docs/09` §4's observation is a **property of that family, not of the
vendor's edge**, and a reader must not generalise it. The three `405` paths are
**POST-only and live** — recorded as evidence and **never sent as a POST**, per
AGENTS.md §8.

### 6b. The `405`s are empty; the `401` is the patient-plane auth signature

The `401` body is `{"error":{"type":"InvalidToken","group":"AUTH"}}` — the exact
signature `regression/hurl/03-patient-api.hurl:13-14` already documents for the
rest of `/patient/*`, so the reports namespace sits behind the **same authoriser
as the rest of the patient plane**, and carries `x-ca-err: 990` like the
recorded Layer7 responses. The `400` on `reportStatus` is a Java bean validation
error naming `getReportStatus.arg0` — evidence the route reaches **application
code**, not merely that a route matched. The `404`s and `405`s are 0-byte.

### 6c. The `Content-Security-Policy` is host-aware, and this is the region evidence

This is the one response-level difference between the three hosts, and it is a
real one. `connect-src` names a different data-plane set per host. **The header
is present on all 24 responses**, so it is a property of the namespace rather
than of one status:

| Host | `connect-src` origins naming the vendor's own data plane |
|---|---|
| `carelink.minimed.eu` | `clcloud.minimed.eu`, `commoncore.minimed.eu`, `commoncore.medtronic.eu`, plus `api-eu.mixpanel.com` |
| `carelink.minimed.com` | `clcloud.minimed.com`, `commoncore.minimed.com`, `commoncore.medtronic.com` |
| `carelink-trials.minimed.com` | `clcloud-trials.minimed.com`, `commoncore-trials.minimed.com`, **`commoncore-trials.medtronic.com`** |

> **A caution about method, because this pass nearly got it wrong.** An initial
> comparison filtered the header block down to seven header names and reported
> the three blocks identical. They are not. The `via` / `x-amz-cf-pop` lines
> differ as expected, and the **CSP differs materially**. A narrow grep would
> have carried "byte-identical across all three hosts" into the write-up as an
> OBSERVED claim — which is exactly AGENTS.md §6 item 2. The full-block diff is
> what §5 and §6c rest on.

**`commoncore-trials.medtronic.com` appears in no prior note in this repository.**
The other five are recorded ([`docs/01:70,93`](../../docs/01-hosts-and-estate.md),
[`CONFIG-NAMESPACE-DEEP.md:252`](../probe-2026-10-08/recon/CONFIG-NAMESPACE-DEEP.md),
which has `commoncore-trials.minimed.com` at 502). The **`.medtronic.com` half of
the trials pair is missing from the corpus** while `docs/07:174` writes the
non-trials pair as `commoncore.medtronic.{eu,com}` — a brace that silently
implies a trials sibling was never looked for.

Stated at the strength it was observed and **no stronger**: OBSERVED is that
**the CSP served by `carelink-trials.minimed.com` names that host**. It is
**INFERRED** that the host exists and serves, because a CSP is a client-side
allowlist, not a liveness proof. **It was not probed** — it is not in this
area's committed candidate list, and a pass does not widen its own list.

### 6d. No gzip, and no CORS, anywhere in this namespace

Every one of the 24 responses carried **no `Content-Encoding`** at all. The
unconditional-gzip trap (AGENTS.md §7) is real on this host family but is
confined to `/patient/v2/configuration/public`; `/patient/reports/*` does not
trigger it. `--compressed` was sent anyway, so this is a property of the
namespace, not of the client.

Every one of the 24 responses carried **no `Access-Control-Allow-Origin`** —
consistent with area X's "0 non-2xx responses carrying CORS anywhere" (see the
`X` row in the Closed-areas table of `docs/11`), though this is a different host
family and is offered as corroboration, not as continuation.

---

## 7. Negatives, recorded as first-class results

- **`/patient/reports/report` is `404` on all three hosts**, and its response is
  **byte-identical to the certainly-absent control** (0 bytes, sha256
  `e3b0c44298fc…` — the digest of the empty string). So on every host in this
  area, `/patient/reports/report` is **indistinguishable from a path that does
  not exist at all**. That is a sharper negative than the archive's bare `404`:
  the in-corpus negative control now has a positive twin on all three hosts.
  Whether the route ever existed, or exists under a different name, is not
  established and is not claimed.
- **No new host, path or candidate was found.** All 21 data cells resolved to
  one of four already-recorded codes; nothing outside the recorded set was
  probed, and nothing unexpected came back.
- **No `200` anywhere.** Nothing in this namespace is unauthenticated, on any of
  the three hosts. Every one of the 24 responses is a 4xx.

---

## 8. What this pass does **not** establish

- **No report body.** Every response is an error or a method rejection. What
  `/patient/reports/*` returns to a caller with a valid token is unknown and
  stays unknown — that is #76, and it needs a token.
- **No POST was sent**, so no report was generated and no status was read. The
  three `405` paths are established as *routed and POST-only*; nothing beyond
  that.
- **The namespace beyond these seven paths was not swept.** "The reports
  namespace is live on all three hosts" means **these seven paths answer on all
  three hosts**. It does not mean the namespace is complete, and the archived
  inventory may not be exhaustive — a path that 404s today because it was added
  after 2021 would be invisible to a list drawn from 2021.
- **`.eu` reproduced exactly**, so the stop condition in #24 ("the `.eu` control
  does not reproduce the recorded verdicts") did **not** fire and the sibling
  comparison has a valid baseline. Recorded explicitly because it was the first
  thing checked and the whole pass rests on it.
- **The delay breach in §1a is not repaired**, only disclosed and fixed in the
  committed harness for future runs.

---

## 9. Verification run over this directory

The repository's own scrub list ([`scripts/scrub-patterns.txt`](../../scripts/scrub-patterns.txt))
was run over every file in this directory, **including `headers/`,
`results.jsonl`, `run.log` and the response bodies**, which is a wider surface
than the PR gate scans (it looks at `*.md`, `*.yml`, `*.sh`, `*.hurl`).

All ten patterns: **zero hits** — after the one real hit that scan *did* catch,
the machine-specific path in `probe.sh` described in §1b.

**The net was proved capable of failing before its zero was trusted**, since a
pattern that cannot match is worse than no pattern (the reasoning the
`reCAPTCHA` entry in that file records from 2026-10-12): a known
`AKIA…`-shaped control was confirmed to match. `results.jsonl` is valid JSON on
all 24 lines with `seq` contiguous 1..24, re-asserted by `verdict.py`.

**Two citation errors survived that gate and were caught only on review** — and
an earlier draft of this section flattered the gate while doing it, so the
corrected account is below.

| Was | Is | Kind |
|---|---|---|
| "see **§8** for where the pins were validated" | **§10** | wrong section in this file |
| "`docs/06:26`" for `/patient/monitor/data`'s `Allow` | **`docs/06:27`** | off-by-one line number |

**Correction — the gate verified *nothing* about either.** An earlier draft said
the check "verifies that citation *paths* resolve, not that their *line numbers*
are right", which is still too generous: it implies the check examined these two
citations and passed them. It never saw them. Reading
`scripts/research-gate.sh:138-157` and running its two regexes over this file:

- **It only opens `docs/*.md`, `README.md` and `AGENTS.md` as pages** — 15 files.
  `findings-log/**` is read **only as the set of valid targets**; a findings-log
  file is never scanned *as a citation source*. Both errors are inside this file,
  so neither was in scope at all.
- **Its `findings-log/…\.md` regex stops at `.md`**, so a `:NN` suffix is outside
  the match. Line numbers can never be validated by it.
- **It has no `docs/…` pattern**, so a `docs/06:26` citation is invisible to it
  wherever it appears.
- **Its `recon/…` regex carries a `(?<![\w./-])` lookbehind**, and `/` is in
  that class, so a relative link `](../probe-2026-10-08/recon/X.md)` can never
  match. Only a bare `recon/X.md` is checked.

So the accurate statement is: the check is a **path-existence test over three
page locations**, and for citations written inside a findings-log log it is
**structurally blind**. The practical rule follows: a citation that *looks*
checkable and is not is worse than one that looks loose, because a green gate
tells a reader it was verified. Every line-numbered citation in this log was
re-derived with `grep -n` in the follow-up round rather than trusted because the
gate was happy.

**The same round re-derived the timing from a second source and found the first
one wrong** (§1a) — which is the argument for the general habit rather than for
this one file: `run.log` was the only timing record, it was internally
implausible, and nothing in the pipeline was watching for that.

**A third defect of the same family, found by the same sweep: six relative links
in this file were broken.** They pointed at sibling findings-log directories with
`../../probe-2026-10-08/…`, which from `findings-log/<this-dir>/` resolves to the
**repository root**, where no such directory exists; the correct prefix is `../`.
(`../../docs/…` and `../../scripts/…` are correct, because those targets really
are at the root — which is exactly why the error survived a read-through.) Every
relative link in this file is now resolved by [`citations.py`](citations.py)
(report: [`citations.txt`](citations.txt)), which also prints the **target line**
of every line-numbered citation so a reader can confirm it says what the sentence
claims rather than merely that something is there. That checker has a
`--selftest` that plants three defects — a link to nowhere, an out-of-range line
and a blank line — and asserts all three are caught, so its zero can be trusted
rather than merely observed.

---

## 10. Regression pins

Five assertions were added to
[`regression/hurl/03-patient-api.hurl`](../../regression/hurl/03-patient-api.hurl),
chosen as the **separating cells** rather than all 21, because AGENTS.md §11
gives the drift sweep a request budget and 21 new requests per sweep is not a
drift guard, it is a tax:

| Pinned | Why this one |
|---|---|
| `supported` → `401` on `carelink.minimed.com` | the load-bearing new cell: the US host now positively carries the namespace |
| `supported` → `401` on `carelink-trials.minimed.com` | same, for the third deployment |
| `generateReport` → `405` + `Allow` on `carelink.minimed.com` | the POST-only arm, asserted on a sibling, with the header as method authority |
| `reportStatus` → `400` on `carelink-trials.minimed.com` | the least-covered status, on the least-covered host |
| `report` → `404` on `carelink.minimed.com` | the **negative arm** — if `/patient/reports/report` ever becomes real, that is a finding, and this is what would catch it |

Without the fifth, the in-corpus negative could silently become positive; it is
the pin most worth its single request.

These five were validated by running exactly those five entries through
`hurl --test --delay 2000ms` at the **pinned hurl 8.0.1**, using the suite's own
delay. That is why §1 counts 24 and not 29: the validation traffic was 5
requests at compliant pacing, issued through the suite runner rather than the
probe, and it is accounted here rather than merged into the probe's number so the
breach in §1a cannot hide behind it.

---

## 11. Successor

Recorded as a dated addendum, not a new letter: **every letter A-Z is in use**
and the priorities page's own gate counts open areas by matching `^### [A-Z]. `
(`docs/11` §"Why there is no area AA"). See `docs/11` for where it was attached
and why. The new fact it rests on is §6c's — the host-aware CSP and the
`commoncore-trials.medtronic.com` name that is in no prior note.

## Correction (2026-10-13)

**The check this log documents now also watches this log.** `scripts/research-checks.py`
grew a findings-log citation check that flags any `recon/|work/|recov/` cite resolving
nowhere — and this file contains the string `` `recon/X.md` `` at §10, which resolves
nowhere. **That occurrence is prose about the gate's own regex, not a citation**: it
demonstrates the lookbehind that keeps a `](../probe-2026-10-08/recon/X.md)` link out
of the match, and there is no artefact by that name to commit. No prose changed; the
exemption below is the whole fix.

<!-- allow-unresolved-cites: recon/X.md — prose demonstrating the gate regex's lookbehind, not a citation, and no such artefact exists to commit -->