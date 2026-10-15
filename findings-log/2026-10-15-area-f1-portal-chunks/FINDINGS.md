# Area F successor 1 — the portal **lazy-chunk** corpus

**Date:** 2026-10-15 · **Pool:** lane A · **Claim issue:**
[#131](https://github.com/NovaLux12/carelink-api-research/issues/131) ·
**Branch:** `research/A-portal-chunk-corpus` ·
**Log dir:** `findings-log/2026-10-15-area-f1-portal-chunks/`

**Verdict in one line: a negative on the clinic build, complete — and a negative
on the support build only where it can be had inside the cap.** Area F's scoped
negative is now unqualified for the **clinic** portal build: all 225 of its lazy
chunks, re-derived from that build's own live runtime `f.u` and fetched under
the names it emits, carry **0** occurrences of every service-identifying token on
area F's list — including `patient-timeline`, `dialog-lite`, `execute-api`, and
all five gateway ids. The **support** build's corpus was **not** swept in full
(15 of its 225 cells, plus its 2076 cell as the positive control = 16 of 225)
and that remainder is named exactly in §6. The headline number is **never** a
pooled total.

There is also a positive, and it is the reason §5 matters: **the two portal
builds are one codebase.** 221 of 225 chunk ids carry an identical content hash
across the builds, the 4 that differ differ by **exactly five bytes** (one
webpack module id, `37254` → `21981`), and 12 of 12 sampled shared-hash cells
came back **byte-identical** from the two different hosts.

---

## 1. Request accounting

| | |
|---|---|
| **Requests used** | **252 of a 260 cap** — 8 unspent |
| Ledger | `results.jsonl`, **252 rows**, one per request. `wc -l results.jsonl` = 252. |
| **Methods** | **GET only.** 252 of 252 rows carry `"method": "GET"`. **No POST**, no **OPTIONS**, no `-X` override, no `-d`/`--data`, no token exchange, no authentication, no `Authorization`, no `Cookie`, no `X-Api-Key`, no `Origin`. |
| **Delay** | declared **≥2.5 s** between requests to the same host, `sleep 2.5` held **inside** the per-host `flock` and `t_sent` stamped inside the lock immediately before `curl`. **Measured, both series, in §2** — and the `t_sent` series reads 9 gaps under the repo's 2 s floor, which is reported as a breach of the floor, not smoothed. |
| Hosts | **2.** `carelinkhp.minimed.eu` (231 rows, clinic `pow`) and `carelink-support.medtronic.eu` (21 rows, support `cua`). |
| Bodies | transient, written outside the repository and **not committed** (`AGENTS.md` §7: no raw captures; these total 5.2 MB). The token census is therefore computed **inside the harness while each body was on disk** and recorded per row, so the negative is re-derivable from the committed ledger alone. |
| Composition | 12 controls / map-derivation rows + 240 chunk cells, one row each. |

**Counting rule for the request count**, so it is re-derivable: every non-empty
line of `results.jsonl` is one request, numbered `seq` 1–252 in send order, and
each `seq` names the `role` that issued it. The offline half (`derive-map.py`,
`plan-cells.py`, `sweep.py`, `spacing.py`, `diff-distinct.py`, `runlog.py`,
`scrub-check.sh`) makes **zero** requests and contributes no rows.

### 1a. One redundant request, named rather than hidden

`seq 4` (the clinic **positive control**, `common.a62bb847b4ea289e.js`) and
`seq 151` (the clinic **sweep cell** for chunk id 2076) request the same URL,
because `plan-cells.py` generates the sweep from `chunk-map.tsv` and does not
de-duplicate against the control list. The two bodies are byte-identical
(`b3de036cb88c5f4c…`, 20 731 B both), so no result is affected. It is **1
redundant request out of 252** and it is inside the cap rather than over it.
The control went first, as the rules require; the sweep cell is a duplicate, not
a substitution.

---

## 2. Measured spacing — both series, and the one number that is a breach

Recomputed by `spacing.py` from `results.jsonl`, offline, zero requests. **One
gap per consecutive pair in request order within one host.**

### 2a. `t_sent` — the harness clock, millisecond resolution

| host | requests | gaps | min | max | under declared 2.5 s | under repo's 2.0 s floor |
|---|---:|---:|---:|---:|---:|---:|
| `carelinkhp.minimed.eu` | 231 | 230 | **1.801 s** | 101.048 s | **29** | **9** |
| `carelink-support.medtronic.eu` | 21 | 20 | **2.213 s** | 602.961 s | **1** | **0** |

The nine sub-floor gaps on the clinic host, shortest first:
**1.801, 1.805, 1.824, 1.827, 1.849, 1.915** s (and three more under 2 s).
**Stated as a breach, not smoothed:** by the `t_sent` series this pass sent
requests to `carelinkhp.minimed.eu` **9 times under the repo's `>= 2 s` floor**,
the shortest at 1.801 s. That is the number a reader should hold.

**Three** gaps exceed 11.892 s, and **each has its own cause** — measured, not
narrated. **Counting rule:** every same-host gap > 11.892 s, of which there are 3.

| gap | host | value | cause |
|---|---|---:|---|
| seq 5 → 9 | clinic | 101.048 s | **phase-1 → phase-2 boundary.** `cells.txt` is 8 data rows (seq 1–8) and `cells-phase2.txt` is 244 (seq 9–252); the clinic rows of phase 1 are seq 1–5 and phase 2 opens at seq 9, where `probe.sh` was re-invoked and the chunk map derived, planned and diffed in between |
| seq 8 → 10 | support | 95.997 s | **the same boundary on the other host.** The phase boundary falls between global seq 8 and seq 9, so it opens a same-host gap on **both** hosts, not on one — support's phase 1 is seq 6–8 and its phase 2 opens at seq 10 |
| seq 12 → 238 | support | 602.961 s | **not a phase boundary — the support host was idle while the clinic sweep ran.** Both rows are phase 2. Between them the harness sent the 225 clinic cells, seq 13 → 237, whose `t_sent` span is **597.040 s** (mean 2.665 s/request). The support host was not asked during that window because the harness was busy on the clinic host |

Every other gap on either host is ≤ **11.892 s** (the largest is clinic seq 9 → 13;
support's largest after the three above is 3.136 s). The kernel `body_mtime`
series corroborates all three independently — its only large values are **102 s**
(clinic) and **97 s / 603 s** (support), against 2 s and 3 s everywhere else.

⚠ **Corrected 2026-10-15 after verification round 1.** This paragraph previously
named **two** of these gaps and called both "phase-1 → phase-2 boundaries",
closing *"Every other gap on either host is ≤ 11.892 s."* **All three halves were
wrong**: the support seq 8 → 10 gap (95.997 s) was not named at all, and
seq 12 → 238 is not a phase boundary — attributing it to a harness pause would
tell a reader the run stalled for ten minutes when it was fully occupied 225
rows away. The wrong sentence is kept in git history rather than deleted
(`AGENTS.md` §3), and the numbers above replace it. **No vendor request changed;
every figure re-derives from the same `results.jsonl`** by `spacing.py` and,
independently, by a second implementation.

### 2b. `body_mtime` — the kernel clock, independent of the harness

| host | requests | gaps | min | under declared 2.5 s | under repo's 2.0 s floor |
|---|---:|---:|---:|---:|---:|
| `carelinkhp.minimed.eu` | 231 | 230 | **2.0 s** | 77 | **0** |
| `carelink-support.medtronic.eu` | 21 | 20 | **2.0 s** | 6 | **0** |

`curl -o` makes the kernel set each body's mtime, so this series does not depend
on the harness's clock. It is at **1-second resolution**, which is stated next to
the number and is load-bearing: it **cannot resolve 2.5 s** (that is why 77 gaps
read "under 2.5 s" — they quantise onto 2.000 and can be anything in
[2.0, 3.0)). What it does say is that **no gap on either host was shorter than
2.0 s**.

### 2c. The timestamps are not wholly faithful, and that is stated here

**28 rows record a `t_done` earlier than their own `t_sent`** — a negative
duration, which is impossible (seq 4 −0.075 s, seq 7 −0.378 s, seq 13 −0.491 s,
… seq 224 −0.026 s; the full list is in `spacing.json`). This is the exact
signature `docs/09` §4 records for areas B, X, Z, D, the CORS-method pass and
area K: **the `date` series is the suspect, the kernel series is not.** This pass
exhibits the signature. **No cause is asserted** — `run.log` cannot distinguish
truncation from a clock step from a post-hoc edit, and neither can
`results.jsonl`.

**So the two readings stand side by side and neither is promoted.** The
`t_sent` series says 9 gaps were under the 2 s floor; the kernel series says 0
were. Both are reproducible from this directory. A reader who wants the floor
should take **1.801 s** as the conservative figure from the harness clock and
know that the independent series puts every gap at ≥ 2.0 s. This pass therefore
contributes **1 more occurrence** to the `docs/09` §4 "a gap below the harness's
own declared sleep" row, and the merge queue reconciles that row's `n`, not this
log.

### 2d. The arithmetic behind 26 of the 30 short gaps — published so a reader does not have to derive it

**This explains a gap. It does not explain the impossible duration, so no cause
is asserted and nothing below promotes a guess.** The harness sleeps inside the
lock and stamps `t_sent` immediately pre-`curl` (`probe.sh:150-153`), so for two
consecutive same-host rows **A → B**:

```
t_sent[B] - t_sent[A]  =  LOCKD (2.5)  +  dur[A]  +  overhead
dur[A]                   = t_done[A] - t_sent[A]
overhead                  = gap - 2.5 - dur[A]
```

A negative `dur[A]` therefore *shortens* the following gap. **All 30 gaps under
the declared 2.5 s are tested against that identity** — clinic 29, support 1.

**26 of the 30 fit, and the residual is a constant to within 13 ms** across gaps
spanning 0.70 s of range. **Every one of the 26 has a negative predecessor
duration.** Representative rows, shortest first:

| seq A → B | host | `dur[A]` | predicted `2.5 + dur[A]` | observed gap | overhead |
|---|---|---:|---:|---:|---:|
| 182 → 183 | clinic | −0.792 | 1.708 | **1.801** | +0.093 |
| 164 → 165 | clinic | −0.782 | 1.718 | **1.805** | +0.087 |
| 134 → 135 | clinic | −0.764 | 1.736 | **1.824** | +0.088 |
| 137 → 138 | clinic | −0.759 | 1.741 | **1.827** | +0.086 |
| 236 → 237 | clinic | +0.089 | 2.589 | **1.849** | −0.740 ⚠ |
| 155 → 156 | clinic | −0.673 | 1.827 | **1.915** | +0.088 |
| 16 → 17 | clinic | −0.655 | 1.845 | **1.932** | +0.087 |
| 230 → 231 | clinic | +0.051 | 2.551 | **1.969** | −0.582 ⚠ |
| 215 → 216 | clinic | −0.641 | 1.859 | **1.950** | +0.091 |
| 128 → 129 | clinic | −0.539 | 1.961 | **2.049** | +0.088 |
| 116 → 117 | clinic | −0.094 | 2.406 | **2.499** | +0.093 |
| **7 → 8** | **support** | −0.378 | 2.122 | **2.213** | +0.091 |

`overhead` over all **26** conforming rows: **min +0.086 s, max +0.099 s.**

**The four that do NOT fit** are named rather than folded in, and **all four have
a *positive* predecessor duration** — the one thing every conforming row lacks:

| seq A → B | host | `dur[A]` | predicted | observed gap | overhead |
|---|---|---:|---:|---:|---:|
| 236 → 237 | clinic | +0.089 | 2.589 | **1.849** | −0.740 |
| 230 → 231 | clinic | +0.051 | 2.551 | **1.969** | −0.582 |
| 221 → 222 | clinic | +0.548 | 3.048 | **2.299** | −0.749 |
| 22 → 23 | clinic | +0.561 | 3.061 | **2.347** | −0.714 |

So, against the headline: **seven of the nine clinic sub-floor gaps and the one
support sub-2.5 s gap are arithmetically accounted for by the preceding row's
impossible duration. Two of the nine — seq 230 → 231 (1.969 s) and
seq 236 → 237 (1.849 s) — are not, and neither is any other mechanism this
directory can test.** The kernel series, which never saw a negative duration,
reports **0** under 2.0 s on both hosts. **That is the reading that counts**, and
it is unchanged by this section; the arithmetic explains the *size* of the short
readings, not their existence.

**What this does and does not license.** It is consistent with the clock fault
`docs/09` §4 already records, and equally consistent with a post-hoc edit to
`run.log` followed by a regeneration of `results.jsonl`, since the ledger is
downstream of the same clock. **No cause is asserted.** What is asserted is the
arithmetic, which is re-derivable: `verify-derivable.py` recomputes all 30 rows
of both tables from `results.jsonl`, zero requests, and prints the overhead
range so the 13 ms spread is checkable rather than taken on trust.

---

## 3. Controls — numbered as they were actually sent, all before the data cells they judge

| # | seq | host | path | status | content-type | bytes | sha256_16 | what it PROVES |
|---|---:|---|---|---:|---|---:|---|---|
| **C1** | 1 | clinic | `zzzz.0000000000000000.js` | 200 | `text/html; charset=UTF-8` | 5 518 | `0f2c5f62…` | **The oracle is `Content-Type`, never status.** A name no build emits answers `200` on this host. A status-only read would score it as a live asset. |
| **C2** | 2 | clinic | `/` | 200 | `text/html; charset=UTF-8` | 5 518 | `0f2c5f62…` | **The entry document IS the SPA shell on this host family** — byte-identical to C1. Re-pins the clinic entry-document digest this repo publishes. |
| **C3** | 3 | clinic | `runtime.a752bb828cca4b2c.js` | 200 | `application/javascript` | 8 597 | `47939ec8…` | **The chunk map is re-derived from the build's own live `f.u`, not from a committed list** (§4). Also the corpus is *current*. |
| **C4** | 4 | clinic | `common.a62bb847b4ea289e.js` | 200 | `application/javascript` | 20 731 | `b3de036c…` | **The positive control, and the emitted-name form is live.** Body begins `"use strict";(self.webpackChunkpow=…).push([[2076]`. Reproduces the committed measurement byte-for-byte. |
| **C5** | 5 | clinic | `2076.a62bb847b4ea289e.js` | 200 | `text/html; charset=UTF-8` | 5 518 | `0f2c5f62…` | **The form-defect control.** The **id** form of the same hash is byte-identical to C1: the id form does not exist on this host, the emitted name does. The two forms are distinguishable, not assumed to be. |
| **C6** | 6 | support | `zzzz.0000000000000000.js` | 200 | `text/html; charset=UTF-8` | 5 518 | `f637c8d0…` | Same oracle, **the support host's own** fallback — and a **different digest from the clinic host's**. Per-build, never pooled. |
| **C7** | 7 | support | `/` | 200 | `text/html; charset=UTF-8` | 5 518 | `f637c8d0…` | The support entry document is byte-identical to its own fallback, as on the clinic host. |
| **C8** | 8 | support | `runtime.0c0212e340fbafc0.js` | 200 | `application/javascript` | 8 597 | `319efc19…` | **The support build's own runtime**, a different name and a different digest from the clinic one (C3). |
| **C9** | 9 | clinic | `main.fb5f8cb7eb60c4d5.js` | 200 | `application/javascript` | 3 397 615 | `2a7fa8e7…` | **ANCHOR GATE, clinic — PASS.** The build the corpus belongs to is the build this repo pins. **METHOD GATE** fires here too (§4). |
| **C10** | 10 | support | `main.759cddab23085086.js` | 200 | `application/javascript` | 3 410 666 | `a054555a…` | **ANCHOR GATE, support — PASS.** |
| **C11** | 11 | support | `common.f55548f9efbc71ce.js` | 200 | `application/javascript` | 20 731 | `39c7795a…` | **Positive control on the support host, in its emitted name form — and the same substitution state holds there.** Matched out of the support runtime body (C8), not inherited from the clinic build. Doubles as support's chunk-2076 sweep cell (§1a). |
| **C12** | 12 | support | `2076.f55548f9efbc71ce.js` | 200 | `text/html; charset=UTF-8` | 5 518 | `f637c8d0…` | **Form-defect control on the support host** — byte-identical to C6. |

All 252 rows are `200`. Every row that scored 5518 B `text/html` is a fallback:
6 in total (C1, C2, C5, C6, C7, C12) and **0 sweep cells**. `sweep.py` refuses to
classify any cell whose content-type is not `application/javascript`.

---

## 4. The gates, and why the zeros are zeros

### Gate 1 — content type, never status

| build | sweep rows | returned a chunk | returned the SPA fallback | distinct body digests | duplicate digests | empty bodies | decoded bytes |
|---|---:|---:|---:|---:|---|---|---:|
| clinic | 225 | **225** | **0** | **225** | 0 | 0 | 4 374 660 |
| support | 15 | **15** | **0** | **15** | 0 | 0 | 861 735 |

Plus the support 2076 cell carried by C11. **0 of 240 sweep cells returned the
shell**, so no cell in either denominator carries a false verdict — which is the
failure the 5518 B trap exists to cause ("Nearly stored 225 copies of
`index.html` in the chunk sweep", `docs/09` §4).

### Gate 2 — the anchor, per build

| build | measured sha256_16 | bytes | pinned | verdict |
|---|---|---:|---|---|
| clinic `pow` | `2a7fa8e7af519c2b` | 3 397 615 | `2a7fa8e7af519c2b` | **PASS** |
| support `cua` | `a054555a0f22176e` | 3 410 666 | `a054555a0f22176e` | **PASS** |

### Gate 3 — the method gate, or a zero is a broken grep

Area F's `grep.sh` requires three literals **known to be present** to be reported
present; without that, "0 hits" is indistinguishable from a matcher that cannot
see anything (`AGENTS.md` §6 item 2, run in the other direction). Both main
bundles carry all three:

| build | `hcp/configuration/public/` | `hcp/patients` | `timeline` | `Timeline` | `TIMELINE` |
|---|---:|---:|---:|---:|---:|
| clinic main (seq 9) | **15** | **42** | 66 | 126 | 4 |
| support main (seq 10) | **15** | **42** | 66 | 126 | 4 |

The three case forms total **196** on both, which is the total area F's own
`grep.sh` asserts ("The census total must equal 66 + 126 + 4 = 196"). Reported as
a reproduction of a figure committed in **this** repository, which under
`AGENTS.md` §2.1 rule 1 is **one source**, not two.

### 4a. The map, re-derived from each build's own runtime, and diffed by hash

`derive-map.py`, offline, from the two runtime bodies this ledger fetched (C3,
C8). The `f.u` ternary is **matched out of the source**, not assumed, and the
answer is recorded either way:

```
f.u = e => (2076===e ? "common" : e) + "." + { 225 entries }[e] + ".js"
```

| | clinic `pow` | support `cua` |
|---|---|---|
| runtime name | `runtime.a752bb828cca4b2c.js` | `runtime.0c0212e340fbafc0.js` |
| runtime sha256_16 | `47939ec8…` | `319efc19…` |
| runtime bytes | 8 597 | 8 597 |
| entries in `f.u` | **225** | **225** |
| duplicate ids | 0 | 0 |
| distinct hashes | 225 | 225 |
| `f.u` special case | id `2076` → name **`common`** | id `2076` → name **`common`** |

⚠ **`chunk-map.json`'s `f_u_expression_first_400_chars` is a display prefix and
nothing else.** It is the first 400 characters of the matched expression, and it
is **identical for the two builds by truncation, not by identity** — id 2076 sorts
near the end of the table and falls outside the cut, which is exactly the entry
that differs between the builds. The field is renamed and carries
`f_u_expression_note` and `f_u_expression_truncated_at` in the JSON itself (fixed
2026-10-15, verification round 1, where the field was called `f_u_expression` and
said nothing about being cut). **`entries` (225 ids each) and `chunk-map.tsv` are
the complete artefact**; the expression string is a human-readable echo of them and
is not evidence on its own.

**Against the committed clinic list** (`findings-log/2026-10-14-area-k-clinic-controlflow/committed-map.txt`,
copied there from the 2026-10-13 pass), joined **by hash**:

| re-derived vs committed | result |
|---|---|
| entries | 225 vs 225 |
| shared hashes | **225 of 225** |
| hashes only in re-derived | **0** |
| hashes only in committed | **0** |
| **name differences** | **0** |
| **id differences** | **0** |

So the committed list was already correct, including the `common` substitution
for 2076. **That is a fact about the clinic build only** — it is not evidence
about the support build, whose map had never been derived before this pass.

---

## 5. The result — per build, never pooled

Token list: area F's, **verbatim and unmodified**, from
`findings-log/2026-10-14-pool-f-timeline-caller/grep.sh`. This pass asks area F's
question of a corpus area F never read; changing the list would make the two
passes incomparable. 24 tokens, byte-exact `count()` per body.

### 5a. Clinic build `pow` — 225 of 225 chunk cells, **complete**

| token | occurrences | | token | occurrences |
|---|---:|---|---|---:|
| `patient-timeline` | **0** | | `execute-api` | **0** |
| `dialog-lite` | **0** | | `0ptoikank6` | **0** |
| `app-patient-timeline` | **0** | | `r5djbmetbb` | **0** |
| `patientTimeline` | **0** | | `d4mwt26mmi` | **0** |
| `personal.patient.timeline.config` | **0** | | `7r9xxd72kk` | **0** |
| `personal.patient.timeline.host` | **0** | | `oflhmnvbe6` | **0** |
| `prodous` | **0** | | `/patient/` | **0** |
| `hcp/configuration/public/` | **0** | | `clcloud` | **0** |
| `carelink.minimed` | **0** | | `m2m` | **0** |
| `baseUrl` | **0** | | `TIMELINE` | **0** |
| `timeline` | 44 | | `Timeline` | 104 |
| `personal.` | 23 | | `hcp/patients` | 1 |

**Every service-identifying token is 0 across all 225 bodies.** The four that
score are read below — all four are code, not pointers.

### 5b. Support build `cua` — 16 of 225 chunk cells, **partial, remainder named**

| token | occurrences | | token | occurrences |
|---|---:|---|---|---:|
| `patient-timeline` | **0** | | `prodous` | **0** |
| `dialog-lite` | **0** | | `/patient/` | **0** |
| `app-patient-timeline` | **0** | | `clcloud` | **0** |
| `patientTimeline` | **0** | | `carelink.minimed` | **0** |
| `personal.patient.timeline.config` | **0** | | `m2m` | **0** |
| `personal.patient.timeline.host` | **0** | | `TIMELINE` | **0** |
| `execute-api` | **0** | | `timeline` | **0** |
| all five gateway ids | **0** | | `Timeline` | 4 |
| `hcp/configuration/public/` | **0** | | `personal.` | 14 |
| `baseUrl` | **0** | | `hcp/patients` | 1 |

**This is 16 of 225 cells and it does not close the support build.** §6 names the
remainder and §6b states what would carry it.

### 5c. Every non-zero token, read to literal-vs-code

**`timeline` / `Timeline` — 148 clinic + 4 support occurrences, all code.**
Not one is a path segment. Every occurrence read at its byte offset
(`sweep.py`, ±45 bytes of context) is an Angular state property, a service
method name, or a CSS class:

| shape | example (byte offset, clinic chunk) |
|---|---|
| state object literal | `allTimelinePeriod:null,currentTimelinePeriod:null` (seq 36 @ 17 858) |
| `select()` on state | `this.currentTimelinePeriod$=this.select(p=>p.currentTimelinePeriod)` (seq 36 @ 21 341) |
| derived stream | `this.noUploadedData$=this.select(this.allTimelinePeriod$,p=>!p)` (seq 36 @ 21 745) |
| service method | `getAuditLogTimelineForCalendar(o){return this.http.get(l.K7s,{pa…` (seq 61 @ 344) |
| method call + dispatch | `getSnapshotTimelinesRange(F.id.toString()).pipe(…snapshotTimelinesRange:et…)` (seq 120 @ 133 278) |
| Angular selector | `[1,"timeline-chart"],[1,"timeline-actions"]` (seq 36 @ 95 026) |
| **CSS class names** | `["timeline-element",3,"click","disabled"]` (seq 36 @ 94 955) |

**Case-sensitivity control** (the class of false hit this repo has been bitten by
three times): in seq 36, `Timeline` = 84, lowercase `timeline` = 44, `TIMELINE` =
**0**. The score is not a case-blind match, and it is not a zxcvbn dictionary
substring — the false-hit words this corpus is full of (`discover`, `pde`,
`dropdead`, `helpdesk`, `herpderp`, `topdevice`, `hampden`) did not fire on any
token in the list: **`m2m`, which area F included precisely because it is
expected to false-hit, is 0 across all 240 chunk bodies** (and 1 in each main
bundle, where area F recorded it).

**`personal.` — 23 clinic + 14 support occurrences, all i18n translation keys.**
Every one read: `personal.termsOfUse` (seq 120 @ 20 866 — the only one that is a
*value* rather than a UI string), `patient.invite.to.personal.message`,
`patient.link.to.personal.message`, `patient.liked.to.personal.header`,
`profile.carelink.personal.login.info`, `hsp.patient.link.personal.paragraph.1.new`.
**Zero are patient-configuration document keys** — which is exactly why
`personal.patient.timeline.config` and `personal.patient.timeline.host` are 0
while `personal.` scores. A prefix that scores tells you nothing about a
configuration key unless you read each occurrence, and each one was read.

**`hcp/patients` — 1 occurrence per build, and it is a real call.** Seq 120
(clinic chunk `6831.8323d65e48e01a28.js` @ 259 411) and seq 239 (support
`6831.e0b3f8bffa1bf0e0.js` @ 259 411 — **the identical offset in both**):

```js
validatePhoneNumber(i,d){return this.http.post("hcp/patients/checkPhoneNumber",{phone:i,country:d})}
```

`POST hcp/patients/checkPhoneNumber` is a documented HCP route; the lazy corpus
reaches the `hcp/patients` namespace exactly once and not at the patient-facing
one. `/patient/` is **0** in every body on both builds.

### 5d. ⚠ The one thing this negative does **not** say

**A zero on a path-literal token list is a statement about literals, not about
reachability — and this pass demonstrates the difference in its own ledger.**

Seq 105, clinic chunk `9481.6977c1a7bd7461f8.js`, 188 467 B, scores **0 on all
24 tokens**. It nevertheless carries, at these byte offsets:

| offset | bytes |
|---:|---|
| 6 756 | `getLogBookConfig(){return this.http.get($.C40).pipe(` |
| 6 798 | the constant reference `$.C40` |
| 6 883 | `getLogBookEntryConfig(){return this.http.get($.df4)` |
| **— 1** | **`hcp/configuration/public/` — absent** |

The two `$.C*` / `$.df4` constants are **imported from the eager main bundle**,
which is where the route literals live (15 of them, seq 9). So the namespace
literal count of **0 across all 225 clinic chunks** and the presence of a
working config-document client in one of those same chunks are both true, and
they are not in tension: **a lazy chunk can call the `hcp/configuration/public/*`
namespace while carrying none of its strings.**

So `hcp/configuration/public/` = 0 in the lazy corpus must be read as *"the lazy
corpus adds no new route literals"*, **not** as *"the lazy corpus does not read
the configuration namespace"*. The same bound applies, with more force, to every
service-identifying token that reads 0: a lazy chunk could reach
`patient-timeline` through a base URL and a path assembled at run time and leave
no literal of it in the bundle. **This is why the negative is a negative about
literals, and why the area's close condition asks for the corpus to be swept
rather than for the question to be settled.**

---

## 6. What remains — named, not vague

**Support build `cua`: 209 of its 225 lazy chunks were never requested.** The 16
that were: id **2076** (seq 11, as positive control), ids **2873** (seq 238),
**6831** (seq 239), **8285** (seq 240) — the four build-distinctive ids — and 12
bridge cells at a fixed stride of 18 from index 9 of the 221 shared-hash ids
(sorted ascending by hash), seq 241–252.

**The remainder is exactly:** every support-host cell for the 221 shared-hash ids
except those 12 — i.e. `209` cells, reachable in one further pass at 2.5 s
(≈ 9 min, ≈ 209 requests). The cell list is regenerable with **zero** requests by
running `plan-cells.py` with `BRIDGE_N` set to cover the remainder, against the
same `chunk-map.tsv` this pass commits. `probe.sh` is resumable from the ledger's
highest `seq`, so the remainder continues at 253 without re-sending anything.

### 6a. The bridge, measured rather than assumed

A shared contenthash *is* evidence of a shared body, but it is an inference about
bytes and this repo does not promote inferences. So 12 support-host cells were
drawn from the 221 shared-hash ids and fetched:

| | |
|---|---|
| sampled | **12 of 221**, stride 18 from index 9 of the hash-sorted ids |
| came back `application/javascript` | **12 of 12** |
| **byte-identical to the clinic build's cell at the same hash** | **12 of 12** |

**OBSERVED for those 12. INFERRED for the other 209**, with the inference and its
assumption stated: *a webpack contenthash that is equal across two builds
denotes the same emitted chunk*. Nothing in this pass tests that for the other
209, and §6 keeps them as an open remainder rather than banking them.

### 6b. What the remainder would add, honestly assessed

If the bridge holds for the remaining 209 — which §6a samples but does not prove
— the support negative becomes complete **by arithmetic, not by fetch**: the same
221 chunk bodies, swept with the same 24 tokens, scored the same. If it does not
hold, the support negative is wrong and only a fetch would say so. **That is the
whole value of the remainder and also its cost**, and the honest statement today
is *INFERRED, one 12-of-221 sample in support*.

---

## 7. The positive: the two portal builds are one codebase

This is why the brief's "the two builds are two corpora" instruction was followed
literally rather than pooled, and it turned out to be worth its own finding.

| measured | value |
|---|---|
| chunk ids per build | **225 and 225, the identical id set** |
| ids whose contenthash is the same on both builds | **221** |
| ids whose contenthash differs | **4** — ids `2076`, `2873`, `6831`, `8285` |
| sampled shared-hash cells fetched on both hosts | **12 of 12 byte-identical** |

And the 4 that differ, read byte-for-byte (`diff-distinct.py`, offline):

| id | clinic bytes | support bytes | length delta | common prefix | common suffix | **divergent middle** |
|---|---:|---:|---:|---:|---:|---:|
| `2076` (`common`) | 20 731 | 20 731 | 0 | 2 237 | 18 489 | **5 B** |
| `2873` | 22 430 | 22 430 | 0 | 13 810 | 8 615 | **5 B** |
| `6831` | 316 979 | 316 979 | 0 | 244 250 | 72 724 | **5 B** |
| `8285` | 148 969 | 148 969 | 0 | 118 549 | 30 415 | **5 B** |

**All four differ by exactly five bytes, and the five bytes are the same five
bytes in all four: the webpack module id `37254` on the clinic build and `21981`
on the support build.** Read at the byte:

```
seq   4 / seq  11  common.f55548f9…  @   2 237:  '37254);function n(c,s=o.E,p){…'  vs  '21981);function n(c,s=o.E,p){…'
seq 225 / seq 238  2873.cd4baaf5…    @  13 810:  '37254),w=a(47073),S=a(67370)…'  vs  '21981),w=a(47073),S=a(67370)…'
seq 120 / seq 239  6831.e0b3f8bf…    @ 244 250:  '37254),g=e(23007),E=e(79668)…'  vs  '21981),g=e(23007),E=e(79668)…'
seq 185 / seq 240  8285.79616a0d…    @ 118 549:  '37254),oe=l(71144),le=l(82086)…' vs  '21981),oe=l(71144),le=l(82086)…'
```

**Consequence, and it is the useful part:** the 4 cells are the **only** places
where a support-host fetch can carry information a clinic-host fetch cannot, and
they turn out to carry **none** — the token censuses of all four pairs are
identical (`6831` scores `Timeline`=4, `personal.`=14, `hcp/patients`=1 on both;
the other three score all-zero on both). So the support remainder in §6 is a
question about *coverage*, not about content: it cannot change the answer to
"does a portal build call `patient-timeline`", because the only chunks that could
have differed between the builds did not differ in any token.

---

## 8. What this does not settle

- **It does not extend area F's negative to the support build.** 16 of 225
  cells, with a 12-of-221 bridge sample, is not 225. §6 names the remainder.
- **It does not convert area F's negative from a literal negative into a
  behavioural one.** §5d is the demonstration: a chunk can call a namespace it
  does not spell.
- **It does not cover the `carelink.medtronic.{eu,com}` and
  `carelink-support.medtronic.com` deployments.** Those hosts serve the same two
  builds byte-for-byte as far as this repo has measured, so a sweep there would
  be a re-read; but this pass did not probe them and does not claim anything
  about their **chunk** URLs specifically. That is a narrower claim than
  "the same page" and it was not tested here.
- **No source maps were sought or found**, and this pass says nothing about
  them. Chunk 9481's call sites were read from the minified body, which is why
  §5d quotes minified bytes.
- **It says nothing about a browser executing the bundle.** Every claim here is
  about bytes served over GET.
- **The `Timeline` census total of 196 on the main bundles reproduces area F's
  committed figure from this same repository** — one source under `AGENTS.md`
  §2.1 rule 1, reported as a reproduction and not as corroboration.

---

## 8a. ⚠ The 224 this repo already published is 225 − 1, and the missing one has a name

**This settles a denominator that two other pages still carry, and it closes a
successor area K left open.** `docs/10`'s open-questions row for
`personal.patient.timeline.config.host` still reads *"The one thing a web sweep
could still add is the portal **lazy-chunk** corpus (**224 chunks**, never swept
for these tokens)"*, and `docs/11`'s own text repeats "224 lazy chunks" — found by
`grep -nF '224 lazy chunks are mined for endpoints' docs/11-suggested-research-areas.md`,
1 hit. Both trace to `findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md`,
whose own heading reads **"Lazy-chunk corpus (224 files)"**.

That record is not wrong about the map. It says, at `:9-10`:

> `hp-runtime.js` holds a **225-entry** webpack chunk map, `{12:"cfb28faf…", …}`, and
> chunks resolve against the portal root (`.p=""`), so the filenames are
> `<id>.<hash>.js`.

and at `:13`: **"224 fetched, 4.4 MB. One entry returned the SPA fallback."**

**225 entries in the map, 224 real chunks, 1 SPA fallback.** This pass measured
**225 entries** in the clinic build's `f.u` (OBSERVED, `chunk-map.json`) and
fetched **225 of 225** under the names `f.u` emits, with **0 fallbacks**
(OBSERVED, `results.jsonl` seq 13–237). So the arithmetic closes exactly: the
missing 224th chunk is the entry whose **id form is not the name `f.u` emits**.

**Which entry that is: INFERRED, with the assumption named.** The 2026-10-08
record says "One entry returned the SPA fallback" and **does not name it**. The
attribution to id **2076** rests on three OBSERVED facts and one assumption:

| | fact | class | where |
|---|---|---|---|
| 1 | that pass built filenames as `<id>.<hash>.js` — the **id** form | SOURCE-OBSERVED | `CHUNK-CORPUS-FINDINGS.md:9-10` |
| 2 | `f.u` in this build emits `common` for id 2076 and for **no other id** | OBSERVED | `chunk-map.json` `special_case_id_to_name`; `derive-map.py` |
| 3 | `2076.<hash>.js` answers `200 text/html` 5 518 B while `common.<hash>.js` answers `200 application/javascript`, on **both** builds | OBSERVED | this ledger, C5/C12 vs C4/C11, seq 4/5/11/12 |
| *assumption* | the unnamed fallback entry in the 2026-10-08 run **is** that one, rather than a fetch error or a different defect | **INFERRED — not tested** | — |

**Not claimed:** that the 2026-10-08 pass erred. It recorded the fallback
explicitly rather than hiding it, and `docs/09` §4's trap row — *"A committed
filename list is not a URL list … the defect is invisible to any control that
does not compare the list against its generator"* — was written from that class
of event. **The trap reproduced in the repo's own 2026-10-08 record, and this
pass's `derive-map.py` is the fix it asks for.**

**What this closes.** Area K's `FINDINGS.md:246-249` names the open item: *"`CHUNK-CORPUS-FINDINGS.md:13` records that the 224-chunk clinic sweep had **'One entry returned the SPA fallback'** — never explained. That is the successor (§8)."* **This is the named cause for that entry**, conditional on the assumption above. Area K's §8 is **not** in this pass's lane to close, and this log does not close it — it supplies the explanation and points at the two pages that still publish 224.

**The denominator a reader should use: 225 per portal build**, OBSERVED here and
re-derivable from `chunk-map.tsv`. The 224 is a different measurement of the same
corpus with one entry lost to a name form, not a separate population.

---

## 8b. What is re-derivable from a clean clone, and what is not

Stated because a stranger must not have to guess which half of this log they can
check. **The response bodies are not committed** (`AGENTS.md` §7), and this pass
went further: they were written to `SCRATCH=$(mktemp -d)` and are **gone from the
machine as well**, so they cannot be recovered even by re-running anything offline.

**RE-DERIVABLE from this directory, zero requests — `verify-derivable.py` runs
all of it and exits non-zero on any mismatch:**

| claim | checked against |
|---|---|
| 252 ledger rows, seq 1–252 contiguous and unique; 252 of 252 `GET`; hosts 231/21; all `200` | `results.jsonl` |
| 12 controls + 240 sweep cells; **0 of 240** returned the 5 518 B shell | `results.jsonl`, by content-type |
| the redundant request is present and counted: seq 4 ≡ seq 151, same URL, same `body_sha256` | `results.jsonl` |
| the per-build token census, every one of the 24 tokens, including `m2m` = 0 across all 240 bodies | `results.jsonl` `tokens` |
| the method gate: 15 / 42 / 66+126+4 = 196 on **both** main bundles | `results.jsonl` seq 9, 10 |
| the case control: seq 36 `Timeline`=84 / `timeline`=44 / `TIMELINE`=0 | `results.jsonl` seq 36 |
| **all of §2** — both spacing series, the 28 negative durations, the three >11.892 s gaps, and the §2d arithmetic with its overhead range | `results.jsonl` |
| 225 ids per build, identical id sets, **221** shared hashes, **4** differing (2076/2873/6831/8285), 0 duplicate ids, 225 distinct hashes each | `chunk-map.tsv` |
| the by-hash diff against area K's committed map: 225 shared, 0 either side, **0 name / 0 id differences** | `chunk-map.tsv` + `committed-map.txt` |
| the 12-cell bridge selection (stride 18 from index 9) and **12 of 12** byte-identity | `chunk-map.tsv`, `results.jsonl` |
| `distinct-diff.json` is internally consistent: `prefix + 5 + suffix == body_bytes` in all four | `distinct-diff.json` |
| `run.log` regenerates byte-identically from `results.jsonl` | `results.jsonl` |
| **0 scrub hits** over all 271 committed artefacts, all 10 patterns | `scrub-check.sh` |

**LOG-LEVEL, NOT RE-DERIVABLE from a clean clone.** Named rather than left for a
reader to assume:

| claim | why | class it actually is |
|---|---|---|
| §5c's per-hit **byte offsets** and the quoted minified source for the `timeline`/`Timeline`/`personal.` reads | bodies gone; `sweep.py` printed contexts to stdout and persisted only `n_hit_contexts: 87` | OBSERVED **when made**; unverifiable now |
| `hcp/patients/checkPhoneNumber` at offset **259 411** "in both" | same | same |
| `$.C40` at **6 798**, `getLogBookConfig` at **6 756**, `hcp/configuration/public/` absent from that body | same | same |
| the **shape** signatures behind "all code, not pointers" | same | same |
| **"exactly five bytes"** — specifically that **no other divergence exists** between each distinct pair | needs both full bodies | the `37254`→`21981` **excerpt** at each offset IS committed (90 B, `distinct-diff.json`); the *exhaustiveness* is not |

**What survives of the 5-byte claim, precisely.** Committed and checkable: both
members of each pair have **equal `body_bytes`** and **different `body_sha256`**
(OBSERVED, `results.jsonl`); the 90-byte excerpts at each first-divergence offset
show `37254` against `21981`; and `prefix + 5 + suffix` equals the body length
exactly in all four. Not checkable: that the five bytes are the *only* difference.
**The claim is therefore published at its evidence class and not above it** —
`docs/11` states "differing by exactly five bytes", which is what
`distinct-diff.json` measures, and this section is the receipt for that.

**The fix, named rather than left open:** a future sweep should commit a small
per-cell evidence index at capture time — an offset list plus a ~160-byte excerpt
per non-zero hit, and a fixed-width window per distinct pair. Roughly 30 KB, no
vendor secret, and it makes §5c and the 5-byte claim checkable from a clone. It
**cannot** be back-filled for this pass without re-fetching 240 bodies, which
would break the closed request accounting in §1. Filed as the successor in
`docs/11` §1b.

## 9. Not pinned, and why

**No `regression/hurl/` pin was added.** The only pin this finding could support
is the presence of the two build anchors, and `regression/hurl/05-public-config.check.sh:329–330`
**already pins both**, at zero extra vendor requests, by reading the build name
out of each host's entry document. Pinning the *anchor* is done. Pinning the
*corpus* would mean 225 chunk GETs inside the weekly drift sweep, against a
budget that pass describes as ~80 requests in total
(`AGENTS.md` §11), to protect a value nobody has agreed to rely on — a negative
over literals, which §5d shows is not the behavioural question. Area F and area K
reached the same judgement on the same grounds (their logs §6 and §6
respectively). **Proposing a pin is a maintainer's decision, not this pass's
side effect** (`docs/09` §4, "a count the gate's regex cannot see").

## 10. A one-cell note on content encoding

Across 252 responses on two hosts in this run: **224 `br` (brotli), 26 with no
`content-encoding` at all, 2 `gzip`.** Area K recorded 206 `br` / 1 `gzip` / 24
identity across 231 responses on `carelinkhp.minimed.eu` alone. `curl
--compressed` is what made every body parse here, which is why `docs/09` §4's
instruction stays a general one rather than a brotli-specific one. **One run, two
hosts, one request shape; not generalised in either direction.**

---

## 11. Evidence map

| claim | class | source |
|---|---|---|
| the clinic build's lazy-chunk corpus is 225 cells, all `application/javascript`, 0 SPA fallbacks, 225 distinct body digests, 4 374 660 B | OBSERVED | `results.jsonl` seq 13–237; `verdicts.json` `corpus.clinic` |
| **every service-identifying token is 0 across all 225 clinic chunk bodies** | OBSERVED | `results.jsonl` seq 13–237 `tokens`; `sweep.py` §TOKEN CENSUS |
| all 148 clinic + 4 support `timeline`/`Timeline` hits are Angular identifiers, CSS classes or service method names | OBSERVED | `sweep.py` §EVERY NON-ZERO TOKEN, every occurrence with byte offset and ±45 B of context |
| `Timeline`=84 / `timeline`=44 / `TIMELINE`=0 in seq 36 | OBSERVED | `sweep.py` §CASE-SENSITIVITY CONTROL |
| `m2m` — the token area F included expecting a false hit — is **0** across all 240 chunk bodies | OBSERVED | `results.jsonl` `tokens` |
| all `personal.` hits are i18n translation keys; `personal.patient.timeline.*` is 0 | OBSERVED | `sweep.py` contexts at seq 74, 91, 120, 143, 193 |
| the single `hcp/patients` hit is `POST hcp/patients/checkPhoneNumber`, at the identical byte offset on both builds | OBSERVED | `results.jsonl` seq 120 @ 259 411 and seq 239 @ 259 411 |
| **a lazy chunk can call `hcp/configuration/public/*` while carrying none of its literals** (seq 105: all 24 tokens 0, `getLogBookConfig` at 6 756, `$.C40` at 6 798, literal absent) | OBSERVED | `results.jsonl` seq 105; body read at the byte in this pass |
| both builds' anchor gates pass at the repo's pinned digests | OBSERVED | `results.jsonl` seq 9, seq 10 |
| both main bundles carry all three known-present literals, `timeline` census total 196 | OBSERVED (and a reproduction of a figure committed in **this** repo — one source, `AGENTS.md` §2.1 rule 1) | `results.jsonl` seq 9, seq 10; area F's total from [findings-log/2026-10-14-pool-f-timeline-caller/FINDINGS.md] |
| both builds' `f.u` carry 225 entries, 0 duplicate ids, and the `2076 → common` special case | OBSERVED | `chunk-map.json`; `derive-map.py` reading the seq 3 and seq 8 bodies |
| the re-derived clinic map matches the committed clinic map on **all 225 hashes, ids and names** | OBSERVED | `chunk-map.json` `vs_committed_clinic_map` |
| both builds expose the **same 225 chunk ids**; **221** share a contenthash | OBSERVED | `chunk-map.tsv`, joined by id |
| the 4 differing chunks differ by **exactly 5 bytes**, the module id `37254` vs `21981`, with identical lengths | OBSERVED | `distinct-diff.json`; `diff-distinct.py` |
| 12 of 12 sampled shared-hash cells are byte-identical across the two hosts | OBSERVED | `results.jsonl` seq 241–252 vs the clinic cells at the same hash; `sweep.py` §BRIDGE |
| a shared contenthash denotes the same emitted chunk, so the support remainder carries no content difference | **INFERRED** — supported by 12 of 221, not tested on the other 209 | §6a; assumption stated there |
| the support build's remaining 209 chunks carry no service-identifying token | **NOT CLAIMED** — the remainder is open | §6 |
| `carelinkhp.minimed.com` is NXDOMAIN, so the claim's second host does not exist and the support build was read from its own pinned host | SOURCE-OBSERVED (this repo) | [findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md] (`:379-380`, and its summary at `:10`); the Closed-table row restating it is `docs/11-suggested-research-areas.md`, **found by grep not by line number** — `grep -nF '| A — is \`carelinkhp\` really the clinician portal for every region?' docs/11-suggested-research-areas.md` (1 hit); the host pair is pinned at `regression/hurl/05-public-config.check.sh:329–330`, read as the `for spec in` pair, **stable because `regression/hurl/` is not edited by this PR** |
| `t_sent` floor 1.801 s, 29 gaps under the declared 2.5 s, **9 under the repo's 2 s floor**; kernel-mtime series 0 under 2.0 s; 28 negative durations | OBSERVED (both series), no cause asserted | `spacing.json`; `spacing.py` |
| a `200` on this host family means nothing without the content-type discriminator | OBSERVED | seq 1, 5, 6, 12 — each fallback byte-identical to its host's entry document |
| the declared 2.5 s delay | SOURCE-OBSERVED (the harness) | `probe.sh`, `sleep $LOCKD` inside the `flock` |

---

## 12. Files

| file | what it is |
|---|---|
| `probe.sh` | what was sent. The cell list it reads **is** the probe; nothing is generated or re-ordered at request time. Cap 260, enforced. Resumable from the ledger's highest `seq`. |
| `cells.txt` | phase 1 — 8 rows: controls and map derivation, both builds. |
| `cells-phase2.txt` | phase 2 — 244 rows, emitted by `plan-cells.py` **before** any of them was sent. |
| `plan-cells.py` | the allocation rule, declared before the data cells, and the generator. |
| `plan.json` | the plan as sent: 252 of a 260 cap, 8 unspent. |
| `derive-map.py` | re-derives both `f.u` maps from this ledger's own runtime bodies; the by-hash diff against the committed clinic list. |
| `chunk-map.json` · `chunk-map.tsv` | the two maps and the diff. 225 ids per build. |
| `sweep.py` | the four gates, the per-build census, the case-sensitivity control, every non-zero hit with context, the bridge. |
| `spacing.py` · `spacing.json` | both spacing series and the negative-duration count. |
| `verify-derivable.py` | **the receipt for §8b.** Re-derives, offline and zero requests, every figure this pass says is re-derivable from its committed artefacts — ledger shape, the content-type gate, the token census, both spacing series, the §2d arithmetic, the chunk map and its by-hash diff, the bridge, `distinct-diff.json`'s internal arithmetic, and `run.log`'s regeneration. **101 checks; exits non-zero on any mismatch.** It also prints, on exit, the two claims it deliberately does **not** check and why. |
| `diff-distinct.py` · `distinct-diff.json` | what the 4 build-distinctive chunks differ by. |
| `runlog.py` · `run.log` | `run.log` is **generated from `results.jsonl`**. The harness's own `run.log` printf had one conversion too few for its argument list, and bash `printf` reuses the format string when arguments outnumber conversions, so it emitted extra lines instead of failing. Found by reading the file; the ledger was never affected (one `python3` row per request) and is the record. |
| `scrub-check.sh` | every pattern in `scripts/scrub-patterns.txt` against **all 271 files this pass adds** — the 20 top-level artefacts plus **all 252 `.h` header captures** — because the gate reads no `.txt`, `.jsonl`, `.tsv`, `.json`, `.log` or `.h` file in any mode, `--all` included (`docs/09` §4, "a leak scan that cannot see the file it was written for"). Measured: **271 files, 10 patterns, 0 hits, 0 `Set-Cookie`**. It also **fails closed** — unreadable pattern list, fewer than 5 parsed patterns, or zero subject files each exit 1. ⚠ **Corrected 2026-10-15 (verification round 1): the first version of this script screened 19 of 271 files** — its `for f in "$DIR"/*` loop did not recurse into `headers/`, so every one of the 252 captures went unread — **and printed PASS having iterated zero patterns** when run from a partial tree. The verifier screened `headers/` by hand: **0 hits**, so nothing had escaped and no published claim was affected; the *sentence* was the defect. Both are fixed; the wrong claim is kept here rather than deleted (`AGENTS.md` §3). |
| `results.jsonl` | 252 rows, millisecond `t_queued`/`t_sent`/`t_done` plus the kernel `body_mtime`. |
| `headers/` | 252 response heads. |
---

## 13. Corrections (2026-10-15, verification round 1)

Kept rather than silently edited (`AGENTS.md` §3). **None of these changed a vendor
request, a body, a digest or a headline figure** — the request accounting in §1 is
unchanged at 252 of a 260 cap and the token census in §5 re-derives identically.
Each is a prose or tooling defect, fixed against the same committed artefacts.

| # | where | what was wrong | class | now |
|---|---|---|---|---|
| 1 | §2a | named **two** gaps above 11.892 s, called both "phase-1 → phase-2 boundaries", and closed "every other gap on either host is ≤ 11.892 s". There are **three**: support seq 8 → 10 (95.997 s) was unnamed, and seq 12 → 238 is not a phase boundary — the support host was idle while the 225-row clinic sweep (597.040 s) ran | **disagreement** — contradicted by this pass's own ledger | §2a rewritten with all three, each with its own measured cause; both wrong sentences kept in git history |
| 2 | §12 | claimed `scrub-check.sh` screened "every file here". It screened **19 of 271** — `"$DIR"/*` does not recurse into `headers/` — and **printed PASS having iterated 0 patterns** from a partial tree | **disagreement** — the sentence, not the corpus; verifier screened `headers/` by hand, 0 hits | script rewritten to `find -type f` incl. `.h`, with three fail-closed guards; now 271 files / 10 patterns / 0 hits; sentence narrowed to the measured coverage |
| 3 | §11 | cited `docs/11-suggested-research-areas.md:2082` for the NXDOMAIN source row. Correct against `origin/main`; **on this branch line 2082 is the area-Y addendum** and the row is at 2198, because this PR inserted 116 lines above it | **disagreement** — §6 item 6 in line-number form | replaced with a grep that hits exactly one line, plus the `committed-map.txt` / area-A `file:line` forms. **The `05-public-config.check.sh:329–330` half was always correct** — `regression/hurl/` is not edited here. The verifier's report named a second site at `docs/11:906`; **that file carries no such citation** and its existing cite is correct, so nothing was changed there |
| 4 | `docs/11` §1a | no recorded grep-first duplicate test, which `CONTRIBUTING-research.md:195-200` requires ("grep both first") | **absence** of a check, not a disagreement — the successor is substantively non-duplicate | test run and recorded in `docs/11` with its commands and hit counts |
| 5 | §5c, `distinct-diff.json` | per-hit byte offsets, the quoted minified source, `checkPhoneNumber` at 259 411, `$.C40` at 6 798, and the exhaustiveness of "exactly five bytes" are **not re-derivable from a clean clone**: bodies were written to a `mktemp -d` and are gone from the machine | **absence** of the artefact | `verify-derivable.py` added (101 checks, zero requests) so the re-derivable half is machine-checked; **§8b names, per claim, what remains log-level** and why; the fix is filed as a successor |
| 6 | §2a/§2c | under-claimed: `gap = 2.5 + dur[prev] + overhead` accounts for **26 of the 30** sub-2.5 s gaps at a constant **+0.086…+0.099 s**, and every one of the 4 it does not fit has a *positive* predecessor duration | **addition**, not a defect | §2d added. **No cause is still asserted** — the identity explains the size of a short reading, not the impossible duration it rests on |
| 7 | `chunk-map.json` | `f_u_expression` was a 400-char prefix with nothing saying so, and is identical across builds **by truncation, not by identity** — id 2076 falls outside the cut, which is the entry that differs | **disagreement** — the field invited a false reading | renamed `f_u_expression_first_400_chars` with `f_u_expression_truncated_at` and `f_u_expression_note` in the JSON, and `derive-map.py` updated to emit the same keys so a regeneration cannot lose them |
| 8 | `docs/10` | still publishes "**224 chunks**, never swept for these tokens" for this corpus; our denominator is **225** | **disagreement**, but **not this PR's file** | resolved and published as **§8a**: 224 = 225 − 1, the lost entry being the `f.u` `2076 → common` id-vs-name form, which closes the explanation area K left open. `docs/10` is not this pass's lane; it is named as a successor in `docs/11` |

**On finding 5, stated plainly rather than dressed up.** The instruction was to
commit a per-cell evidence index so §5c becomes checkable from a clone. **That
cannot be done for this pass**: the bodies no longer exist on the machine, so
producing 30 KB of excerpts would mean re-fetching 240 chunks, which breaks the
closed request accounting in §1 and would be a different pass with a different
ledger. **The honest resolution is the one taken here** — machine-check the half
that is checkable, and label the other half by claim. The 148+4
`timeline`/`Timeline` hits, the byte offsets, and the exhaustiveness of the 5-byte
claim are **OBSERVED when made and unverifiable now**, and this log says so.
