# Area F — what the timeline and dialog-lite gateways actually are

**Date:** 2026-10-14 · **Pass:** pool worker F, claim issue
[#123](https://github.com/NovaLux12/carelink-api-research/issues/123) ·
**Log dir:** `findings-log/2026-10-14-pool-f-timeline-caller/`

**Verdict in one line: a firm negative, plus a negative it was not looking for.**
No client artefact in either portal build calls `patient-timeline` or
`dialog-lite`, and the reason is structural rather than an absence of evidence —
**neither build reads the patient configuration document at all**, so the config
pointer that carries the timeline host is unreachable from that code. The BLOCK-7
gateway cells that had never run are **no matching route** on all three
`patient-timeline` deployments. `dialog-lite` still 500s on every invocation and
its certainly-absent control is byte-identical to its published root, so the 500
is the stage-wide catch-all's signature and nothing more. The token-blocked half
(the three readings of the 403s) is **unchanged and still blocked** — see §7.

---

## 1. Request accounting

| | |
|---|---|
| Cap | **40** |
| Requests sent | **17** — **17 of a 40 cap** |
| Ledger | `results.jsonl`, **17 rows**, one per request. No retry, no `hurl --test`, no one-off curl was issued, so harness rows and ledger rows are the same 17 and the accounting is exact in both directions. |
| Methods | **GET only.** No POST, no token exchange, no authentication, no `Authorization`, no `Cookie`, no `X-Api-Key`, no `Origin`. No `-X` override. |
| Delay | **≥2.5 s** between requests to the same host, declared and measured (§2). The sleep is **inside** the host lock, so the ledger's `t_sent` column is the send time rather than the queue time. |
| Hosts | 7 — `carelink.medtronic.eu`, `carelink-support.medtronic.com`, and the five `*.execute-api.*.amazonaws.com` gateways named in the claim. No other host was contacted. |
| Files | `probe.sh` (what was sent), `results.jsonl` (the ledger), `run.log` (t_queued / t_sent / t_done), `headers/` (per-request response heads), `grep.sh` + `grep-out.txt` (the offline half, zero requests) |

**Counting rule for the request count**, so it is re-derivable: every row in
`results.jsonl` is one request, numbered `seq` 1–17, in send order. The offline
half (`grep.sh`) makes **zero** requests and so contributes no rows.

### Cells, in send order

| seq | host | path | status | `x-amzn-errortype` | role |
|---:|---|---|---:|---|---|
| 1 | `carelink.medtronic.eu` | `/main.fb5f8cb7eb60c4d5.js` | 200 | — | corpus, clinic build |
| 2 | `carelink-support.medtronic.com` | `/main.759cddab23085086.js` | 200 | — | corpus, support build |
| 3 | `d4mwt26mmi…` (pt EU) | `/prod/patient-timeline/` | 403 | `MissingAuthenticationTokenException` | control, plausible root |
| 4 | `d4mwt26mmi…` | `/prod/patient-timeline/9f3c1d7e-…` | 403 | same | control, certainly absent |
| 5 | `d4mwt26mmi…` | `/prod/patient-timeline/v1/` | 403 | same | BLOCK-7 area, prefix root |
| 6 | `d4mwt26mmi…` | `/prod/patient-timeline/v1/events` | 403 | same | **BLOCK 7** |
| 7 | `d4mwt26mmi…` | `/prod/patient-timeline/logbook` | 403 | same | **BLOCK 7** |
| 8 | `7r9xxd72kk…` (pt US) | `/prod/patient-timeline/` | 403 | same | control, plausible root |
| 9 | `7r9xxd72kk…` | `/prod/patient-timeline/9f3c1d7e-…` | 403 | same | control, certainly absent |
| 10 | `7r9xxd72kk…` | `/prod/patient-timeline/v1/events` | 403 | same | **BLOCK 7** |
| 11 | `oflhmnvbe6…` (pt trials) | `/prod/patient-timeline/` | 403 | same | control, plausible root |
| 12 | `oflhmnvbe6…` | `/prod/patient-timeline/9f3c1d7e-…` | 403 | same | control, certainly absent |
| 13 | `oflhmnvbe6…` | `/prod/patient-timeline/v1/events` | 403 | same | **BLOCK 7** |
| 14 | `0ptoikank6…` (dl EU) | `/prodous/dialog-lite/v1/` | 500 | `InternalServerErrorException` | control, published root |
| 15 | `0ptoikank6…` | `/prodous/9f3c1d7e-…` | 500 | same | control, certainly absent |
| 16 | `r5djbmetbb…` (dl US) | `/prod/dialog-lite/v1/` | 500 | same | control, published root |
| 17 | `r5djbmetbb…` | `/prod/9f3c1d7e-…` | 500 | same | control, certainly absent |

Controls are **first per host**, before any data cell, as the claim requires.

## 2. Measured spacing

**Counting rule:** same-host gaps between consecutive `t_sent` values, per host,
in send order; **10 measurable gaps** (hosts with n ≥ 2), across **17 requests**
of which the two single-request hosts contribute none.

| oracle | floor | gaps under the declared 2.5 s | gaps under the repo's ≥2 s floor |
|---|---:|---:|---:|
| `t_sent` millisecond series in `results.jsonl` | **2.239 s** | 1 of 10 | **0** |
| kernel body-mtime, nanosecond (`stat -c%Y` on the written bodies) | **2.866 s** | **0** of 10 | **0** |

Per host (`t_sent`): EU pt 2.873 / 2.868 / 2.871 / 2.871 · US pt 3.990 / 2.239 ·
trials pt 3.120 / 3.113 · dl EU 2.909 · dl US 3.098.

**Two disclosures, neither smoothed over.**

1. **One gap measures 2.239 s on the `t_sent` series** (US patient-timeline,
   seq 9 → 10) and **one duration is negative** — seq 9's `t_done` is **552 ms
   before** its `t_sent`. That is the known corrupt-`t0` / clock-step class
   `docs/09` §4 records from five prior passes. **No cause is asserted**, and the
   gap is **not** attributed to lock contention or to a stalled clock.
2. **The kernel body-mtime oracle puts the floor at 2.866 s with 0 sub-2.5 s
   gaps**, so **no gap in this pass was actually short**; the 2.239 s reading is
   a property of the harness's own clock, not of the traffic. The two oracles
   span the same window (48.95 s vs 51.57 s), consistent with one series.

⚠ **The mtime figure is not re-derivable from a clean clone** — git does not
preserve mtimes and the bodies live outside the repository (`AGENTS.md` §7: no
raw captures, and a 3.4 MB bundle would also breach the 1 MiB per-file log
limit). **The load-bearing figure is the millisecond `t_sent` series**, which
reproduces from `results.jsonl` alone. Recorded here because two of the repo's
prior passes have now made this exact mistake in the other direction.

## 3. BLOCK 7, which had never run — verdict

[AWS-GATEWAYS.md](../../findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md):240-242 records that BLOCK 7 *"never ran"*: an accidental re-run
consumed the last four budget slots. Those four cells ran here, with the
controls that make them mean something.

**OBSERVED, 11 of 11 `patient-timeline` cells, all byte-identical.** Every cell
below answers `403`, `application/json`, `content-length: 42`,
`x-amzn-errortype: MissingAuthenticationTokenException`, and a body whose
sha256 is `f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16` —
**one** digest across all eleven, on all three deployments.

| path | deployments | cell |
|---|---|---|
| `/prod/patient-timeline/` | 3 | published root, the claim's plausible-path control |
| `/prod/patient-timeline/9f3c1d7e-2b48-4a6c-8e51-0c7d9a2b41f6` | 3 | **certainly-absent control** |
| `/prod/patient-timeline/v1/` | 1 (EU) | BLOCK-7 prefix root |
| `/prod/patient-timeline/v1/events` | 3 | **BLOCK 7** |
| `/prod/patient-timeline/logbook` | 1 (EU) | **BLOCK 7** |

**The oracle, and what it is allowed to say.** Under Oracle A (`docs/09` §2),
`MissingAuthenticationTokenException` means **no matching route**; it can only
ever confirm a negative and never establishes that a route exists. That reading is
admissible *here* because the certainly-absent control is **byte-identical to
every plausible path on every deployment** — the two are indistinguishable, so
the response carries no route-specific information at all.

> **Verdict (OBSERVED): no GET route exists under `/prod/patient-timeline` on
> any of its three deployments, for the published root, the `v1` prefix, the
> `v1/events` path or the `logbook` path.** The BLOCK-7 cells carry the same
> verdict as the cells that had already run: negative.

**Two by-products worth recording because they are re-derivations, not news.**

- The no-route body's **full** sha256 reproduces the digest this repo already
  publishes (`f249b63cb2fc`, [`docs/09`](../../docs/09-methodology-and-oracles.md)
  §2 and `docs/10`), for the first time as a complete value rather than the
  12-character prefix those pages carry. **OBSERVED, 11 of 11.**
- **Zero 404s in 17 requests, and zero in the 15 gateway responses
  specifically** — the "404 is not in this stack's response vocabulary" clause of
  Oracle A, which `docs/10` marks INFERRED-by-analogy from `clcloud.*`, is now
  directly observed on the `execute-api.*` family itself (`docs/10`, "Which of
  three readings…"). One observation does not make it a law; it removes the
  *analogy* from the citation.

### The one cell this pass added beyond the claim, and why

`/prod/patient-timeline/v1/` (seq 5, EU only). **INFERRED justification,
recorded because the cell is not in the claim's list:** the published dialog URL
carries a `/v1` segment (`…/prodous/dialog-lite/v1`), so `v1` is the vendor's
own version-segment convention on this stack and a client reading the published
host would address the service under it. The cell separates *"the `v1` prefix
is unrouted"* from *"everything under `v1` is unrouted"*. Both readings answer
`403` with the control's exact envelope, so it adds one request and one negative,
and it changes no verdict.

**Neither vocabulary was extended.** The claim is explicit that the
`dialog-lite` list must not be extended — [AWS-GATEWAYS.md](../../findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md) §6 records that
enumeration there is *"informationally empty by construction"* — and the seven
`patient-timeline` noun/verb candidates (`events, entries, items, list, query,
range, params`) were all already run on all three regions on 2026-10-10, so
re-running them would have burned budget to reproduce a recorded answer.

## 4. `dialog-lite` — the 500 reproduces, and the control says what it means

**OBSERVED, 4 of 4 cells.** All four answer `500`, `application/json`,
`content-length: 36`, `x-amzn-errortype: InternalServerErrorException`, body
`{"message": "Internal server error"}`, sha256
`660f19c09a36ca1620054261590b73df388b95892469ff17c1caf4e50376aa02` — **one**
digest across both regions, published root and certainly-absent control alike.

| deployment | published root | certainly-absent control |
|---|---|---|
| EU `0ptoikank6…` | `/prodous/dialog-lite/v1/` → 500 | `/prodous/9f3c1d7e-…` → 500 |
| US `r5djbmetbb…` | `/prod/dialog-lite/v1/` → 500 | `/prod/9f3c1d7e-…` → 500 |

**What this establishes, precisely.** The stage-wide `ANY /{proxy+}` catch-all
reproduces: a request to a **certainly-absent** path under `/prodous/` (EU) or
`/prod/` (US) is byte-identical to a request for the published root, so the
`500` **cannot discriminate the path** and is not evidence that any particular
route exists. What it does establish is the same two facts the log recorded on
2026-10-10, re-observed today: **these two deployments route anything with at
least one path segment below the stage root, and the integration raises on every
invocation.**

**The digest is new.** [AWS-GATEWAYS.md](../../findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md) §3 recorded the routed-and-failed body
as 36 B but published no digest for it; `660f19c0…` is this pass's measurement,
so it is offered as a value to re-check against rather than as a reproduction.

**Limit, stated because the claim asked for it.** The control here was sent at
the **stage root level** (`/prodous/<uuid>`), not inside the `dialog-lite/v1`
prefix. That is the correct control for the oracle question — *is an absent path
distinguishable?*, answer no — but it is **not** the same cell as
[AWS-GATEWAYS.md](../../findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md) §10 row 2 (`/prodous/dialog-lite/v1/<uuid>`), so this pass does
not re-derive that one, and says so rather than counting it as reproduced.

**Still unknown, unchanged:** *why* the backend raises (`docs/10`, "Why does
`dialog-lite`'s backend raise on every invocation"). No reading is offered.

## 5. CORS and the response header set — area F's own premise re-measured

**OBSERVED, 15 of 15 gateway responses.** The complete header key set on every
`execute-api.*` response is **six keys and nothing else**: `date`,
`content-type`, `content-length`, `x-amzn-requestid`, `x-amzn-errortype`,
`x-amz-apigw-id`.

**Zero of 15 carry any `access-control-*` header, and zero carry `Server`,
`Via`, `X-Cache`, `X-Amz-Cf-Id`, `Set-Cookie`, `Allow` or `Vary`.** This
reproduces [AWS-GATEWAYS.md](../../findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md) §3 exactly (0 of 90, 2026-10-10) on a different
date, across both families, and it leaves area F's premise — *"Neither is
browser-callable"* — untouched **as an observation about headers**.

⚠ **What it does not say.** The absence of `Access-Control-*` on a `403` is
evidence about **the stage's configuration**, not about a route; and the
`commoncore*` family returns `ACAO: *` **on its no-route `403`** already
([#61](https://github.com/NovaLux12/carelink-api-research/issues/61),
`docs/09` §2). So this row is **not** evidence that the services are
unreachable *as services* — only that no response in this set is
browser-visible. A browser-side caller is ruled out for the two services; a
server-side or native caller is **not** ruled out by any header.

## 6. The caller half — a negative, and a stronger one than the area expected

### 6.1 The corpus, and the two gates that had to pass first

**OBSERVED.** Both bodies reproduce their pinned sha256 anchors in full, so they
*are* the builds this repo has been reasoning about:

| body | status | `content-type` | bytes | sha256 |
|---|---:|---|---:|---|
| `main.fb5f8cb7eb60c4d5.js` on `carelink.medtronic.eu` | 200 | `application/javascript` | 3,397,615 | `2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba` |
| `main.759cddab23085086.js` on `carelink-support.medtronic.com` | 200 | `application/javascript` | 3,410,666 | `a054555a0f22176ecb51d8f6439680a394e2be5e889494bec5004c93be28c954` |

The request went to the **content-hashed asset name**, not to a document path,
because on this host family the catch-all *is* the entry document — asking a
portal host for a document and getting 5 518 bytes of HTML back is the
`carelinkhp` trap ([area A](../../docs/00-summary-the-map.md),
[`docs/00`](../../docs/00-summary-the-map.md)). Both anchors are the values areas
A and G pin; neither has moved.

Two gates, and both are load-bearing:

- **ANCHOR GATE** — a body that does not reproduce its pinned anchor is **not
  analysed**. Both passed.
- **METHOD GATE** — three literals **known** to be present must be reported
  present, *by name*: `hcp/configuration/public/` (15), `hcp/patients` (42),
  `timeline` (66). A named gate, not a threshold, because **two of the tokens
  below are false hits by construction** and a count-based gate can be met by
  false hits alone. This is `AGENTS.md` §6 item 2 run in the direction the repo
  usually applies it: not "a hit proves it", but **"a miss has to be proven to be
  a miss"**.

### 6.2 The result: 0 hits, twice

**OBSERVED, both bodies.** Every one of these literals scores
**zero** in the clinic build *and* in the support build:

`patient-timeline` · `dialog-lite` · `app-patient-timeline` · `patientTimeline`
· `personal.patient.timeline.config` · `personal.patient.timeline.host` ·
`execute-api` · `prodous` · `/patient/` · `clcloud` · `carelink.minimed` ·
and **each of the five 10-character gateway ids** — `0ptoikank6`, `r5djbmetbb`,
`d4mwt26mmi`, `7r9xxd72kk`, `oflhmnvbe6`.

The gateway-id sweep is the sharpest of these, and it is the one this pass adds.
A caller must name a gateway to reach one, the five ids are on record
([`enumeration-scrubbed.txt`](../../findings-log/2026-10-12-published-pointers/enumeration-scrubbed.txt)
— `0ptoikank6` line 83, `d4mwt26mmi` line 121, `r5djbmetbb` line 155, `7r9xxd72kk`
line 187, `oflhmnvbe6` line 245), and **neither build contains any of them**.

`app-patient-timeline` being 0 is the decisive comparison against area V: the
**patient** build carries that Angular component selector 5 times. The portal
builds do not carry it **once**, so neither portal build has a patient-timeline
*component* either — the service is not merely uncalled, it is absent from the
application's own vocabulary.

### 6.3 Why the two literals that did fire are false hits

Counted **per body**, because `grep-out.txt` reports per body and a cross-build
total beside a per-build figure is the unit error this pass's own correction C3
exists to prevent: `m2m` is **1 per body** (2 across both), `baseUrl` is **2 per
body** (4 across both). **Each token's byte offsets are tabulated per build, and the
two tokens come out differently: `m2m` sits at the same byte in both builds, and
`baseUrl` does not.** `m2m` is at **387460 in the clinic build and 387460 in the
support build**; `baseUrl` is at **2422149 / 2422752 in the clinic build and 2422091
/ 2422694 in the support build**, the support build's two sitting **58 bytes
earlier**. **No reason is offered for that difference.**

Hand-checked, not counted (`grep-out.txt` carries the context):

- **`m2m`, 1 hit per body (2 across both), at byte 387460 in each.** Area F's own
  text proposes looking for "a `m2m` / `gc` call pattern"
  ([`docs/11`](../../docs/11-suggested-research-areas.md):222). The single `m2m`
  byte sequence in either build is the **third through fifth characters of
  `cum2me`**, whose own bytes are 387458–387463 — inside a leaked-password
  dictionary, the same blob that holds the `discover` and `pde` hits area V
  documented. The premise carries its own false-positive trap and it fires on the
  first token tried.

  ⚠ **The token is not fictional, and a reader must not take the false hit that way.**
  `/patient/m2m/connect/data/gc/patients/{username}` is a **live, pinned route** on the
  patient plane — [`regression/hurl/04-deep-surface.hurl`](../../regression/hurl/04-deep-surface.hurl):96
  asserts `GET …/patient/m2m/connect/data/gc/patients/probe-user` → `HTTP 401` with
  `$.error.type == "InvalidToken"`, and `:102` asserts the `/last24hours` suffix shape
  → `404`. **So `m2m`/`gc` is a real call pattern on this vendor's surface and this
  pass's corpus finding is about something narrower: `m2m` as a three-character
  *substring* is unusable as a corpus token, because one occurrence in 3.4 MB of
  minified vendor code is a leaked-password word.** The live route is on
  `carelink.minimed.eu`, which is **outside this claim's host set** and was **not
  probed here** — the pinned assertion above is quoted from the suite, not re-derived
  by this pass. **Not a contradiction, a scoping distinction, and worth stating
  because the opposite reading is the obvious one to reach.**
- **`baseUrl`, 2 hits per body (4 across both), at bytes 2422149 and 2422752 in
  the clinic build and 2422091 and 2422694 in the support build.** Every one of
  the four sits in an **embedded Pusher JS SDK** (`baseUrl:"https://pusher.com"`,
  `authenticationEndpoint`, `docs/channel…`). Not a CareLink API base. Area V's
  counterpart finding for the patient build was different and is not repeated
  here: its two `baseUrl` hits are `getBaseCmsUrl()`, a CMS media base.

### 6.4 The negative that is larger than the one asked for

**OBSERVED.** `personal.` occurs **4 times in each build** (8 across both), and
**none of the eight is a key of the patient bulk document**.

**The offsets are NOT the same in the two builds**, so they are tabulated per build.
**Counting rule, so both columns can be re-derived from `grep-out.txt` by hand:** the
committed context dump is `.{0,45}<token>.{0,45}`, so the **left context is a fixed 45
bytes** and **token byte = context offset + 45**, with a window of `45 + len(token) +
45` — **99 bytes for the 9-character `personal.`**, against 93 for the 3-character
`m2m`. Reading the four `personal.` rows out of each body's section of `grep-out.txt`
gives:

| literal | what it is | clinic offset | support offset |
|---|---|---:|---:|
| `pow.personal.link.gdpr.warning` | an **HCP** config key | 2403157 | 2403099 |
| `hcp/configuration/public/pow.invite.to.personal.uri` | an **HCP** config route | 2762844 | 2762882 |
| `patient.liked.to.personal.header` | a UI i18n string, **twice per build** | 3238864 · 3239490 | 3040788 · 3041414 |

**The literals are identical across the two builds; only the offsets move.** The last
two differ most — clinic has them near 3 238 000 and support near 3 040 000, i.e. the
i18n table sits in a different place in each bundle — and **no cause is asserted for
that**, since the bundles are different builds of different lengths. Only the
minifier's own identifiers differ in the surrounding text (`R[…]` vs `j[…]`,
`Oe=` vs `se=`), which is what a reader would expect from two separately minified
builds and is not load-bearing.

**Zero of the 69 published patient config keys appear in either portal build.**
`/patient/` is 0, `carelink.minimed` is 0, `clcloud` is 0, `api/carepartner` is
0. The API surface these builds name is the **clinician** namespace and nothing
else: `hcp/patients` 42 hits, `hcp/configuration/public/` 15 hits, `pow.*` and
`cua.*` config keys.

> **This is the answer to area F's letter question, and it is stronger than a
> bare absence.** A server-side proxy in the portal bundle was one of the two
> readings area F proposed; there cannot be one, because **there is no base URL
> for it to proxy to** — neither build reads the document that names the
> timeline host. The pointer `personal.patient.timeline.config.host` is
> unreachable *from this code*, which is a statement about the code, not about
> the service.

### 6.5 `timeline` scores 196 and `patient-timeline` scores 0 — the whole false-hit class, quantified

A grep on the bare token would report a large integration that is not there.
**OBSERVED, both bodies: 66 `timeline` + 126 `Timeline` + 4 `TIMELINE` = 196
occurrences across 74 distinct signatures, and not one of them is the service.**
Every occurrence falls into exactly one of five classes, and the census in
`grep-out.txt` lets a reader re-derive that:

| class | evidence in the census |
|---|---|
| **GSAP animation library internals** | `this.currentTimeline`, `transformIntoNewTimeline`, `_globalTimelineStyles`, `_elementTimelineStylesLookup`, `timelineSender`, `buildTimelineMessage`, `appendInstructionToTimeline`, `applyStylesToKeyframes` |
| **Pusher SDK internals** | `this.timeline.info(…)`, `this.timeline.error(…)`, `timeline.pong_timed_out` — the SDK that also owns the `baseUrl` hits of §6.3 |
| **Medtronic's own snapshot-timelines **report** service** | `hcp/reports/getSnapshotTimelinesRange`, `getSnapshotTimelinesForCalendar`, `mergeSnapshotTimelinesForCalendar`, `TIMELINE_RANGE`, `report_data_time_line…` — the `commoncore` reports namespace already on record ([`docs/00`](../../docs/00-summary-the-map.md)), **not** the timeline gateway |
| **leaked-password dictionary words** | bare `timeline` and `timelines` inside password-word lists — the same blob as §6.3 |
| **one analytics label** | `"[Patient Details] update snapshot timeline range"` |

**Counting rule for the census**, so the total can be re-derived and the two
readings cannot drift: each occurrence contributes exactly one signature, formed
from ≤ 18 word-characters of **left** context plus the matched token and **no**
right context. A right-context form was tried first and returns **189**, because
greedy right context swallows a following token inside the same identifier —
so 189 is a defect of that pattern, not a count of anything.

**This is `docs/09` §5's failure class, in the direction that produces false
*positives*, on the exact token this area is hunting.** Area V found the same
class on `patient-timeline` itself in the patient build (5 hits, all Angular
component selectors). The portal builds have the class one level up, and it is
bigger: **196 to 0.**

### 6.6 Scope limit: three builds, and only one of them has ever had the timeline in it

| build | host | corpus swept for these tokens? | `patient-timeline` |
|---|---|---|---|
| clinic `pow` | `carelink.medtronic.eu` | **this pass, 2026-10-14** | 0 (and 0 component selectors) |
| support `cua` | `carelink-support.medtronic.com` | **this pass, 2026-10-14** | 0 (and 0 component selectors) |
| patient | `carelink.minimed.eu` | area V, 2026-10-13 | 5 hits, **all Angular component selectors**; `personal.patient.timeline.config` present and read; `personal.patient.timeline.host` present with **zero** readers |

**The patient build is the only one of the three that has ever contained the
timeline at all — and even there, nothing names the service or its host.** The
patient build was **not** re-fetched here: `carelink.minimed.eu` is outside the
host set this claim authorises, so area V's record is cited, not reproduced. Its
own conclusion — *"the consumer is INFERRED to be a mobile app; no mobile
artefact exists on any probed host"* — is unchanged and is the honest limit.

> **Synthesised, and the load-bearing sentence of this pass (INFERRED, from the
> three OBSERVED corpus facts above):** if a caller for `patient-timeline` exists
> in a **web** client, it is in none of the three builds this repo has read.
> That is a statement about the corpus, which is not the same as a statement
> about every client the vendor ships.

## 7. What is **not** closed, and why — stated before the verdict, not after

**The token-blocked half of area F is unchanged and stays blocked.** Which of
the three readings explains `patient-timeline`'s no-route `403`s — *no routes
deployed* / *routes exist for other verbs only* / *the live stage is not `prod`*
— is still undecidable with GET-only probing, because separating them needs an
authentication attempt, which `AGENTS.md` §8 and §11 exclude. This pass ran four
more cells into that same dead end and did **not** move it; `docs/10` already
carries the row with its blocker named, and nothing here supersedes it.

**Also not closed, and not claimed:** whether `dialog-lite`'s backend raises
because of a vendor defect; whether any non-browser client can reach either
service; and whether the raw `personal.patient.timeline.config.host` value is
publishable — **a disclosure judgement that belongs to a maintainer holding the
value, and is not pre-committed here.**

**No regression pin was added for the gateway cells**, and that is a decision
with a precedent rather than an omission: the `execute-api.*` hosts appear in no
`regression/hurl/` suite, and adding them would widen the weekly drift sweep's
~80-request vendor budget from a research pass. Area M's log records the same
decision and the same reasoning. The rot-prone half of this pass is the EU
69-key **count**, which is pinned at **zero extra requests** (§8).

**One side-finding, recorded as confirmation and not as news.** Both builds
still carry the already-published hardcoded `x-api-key` + `dev.commoncore.…`
reports-broker pair ([`docs/08`](../../docs/08-security-findings.md) §S3). **The
value is not reproduced here** and no dev/stage host was contacted, per policy.
Its presence is a confirmation of an existing record, not a new disclosure.

## 8. The pin — one check, zero requests

The claim's step 5, and the only thing in this pass that will be re-run by
something other than a human.

`regression/hurl/05-public-config.check.sh` fetches the **EU** bulk document
once, at its top, into `$BODY`. **`.com` and `-trials` carry a
`keys | length` = 69 assertion** in the area-E block; **EU did not.** This pass
adds the third, so the count a drift sweep already reads on two deployments is
asserted on the third — at **zero additional vendor requests**, because the body
is already on disk at that point in the script.

Stated limits, carried with the pin rather than implied by it:

- it pins the **count**, not the **set** — a deployment that swapped one key for
  another would keep 69 and pass;
- it does **not** re-derive the projection property (123 valued cells, 0
  mismatches), which is 152 requests of work and belongs in the drift sweep;
- per the counting rule in `scripts/research-checks.py`, this is **one new
  `check` site and no new `for` loop** — a second loop would multiply its site by
  `LOOP_FAMILY_SITES` (16) and silently corrupt every derived count in the repo
  (`05-public-config.check.sh`, area-E block header).

⚠ **The new assertion was NOT executed live, and that is a disclosure rather than an
omission.** Executing `05-public-config.check.sh` fetches
`carelink.minimed.eu`, `carelink.minimed.com` and `carelink-trials.minimed.com` —
**five vendor requests to three hosts that are outside this claim's authorised host
set** — so it was not run. What *was* verified, without a request: `bash -n` on the
suite (clean); the `jq` filter and the expected value against the **committed 69-name
list** `findings-log/2026-10-13-area-w-per-key/keys.txt` (69 lines — the value is right);
and `python3 scripts/research-checks.py`, which re-derives the static and runtime
assertion counts from `scripts/measure_assertions.py` and re-derives the new site's
accounting (**217 static / 431 executed**, matching the prose this pass updated). The
assertion's *live* behaviour is for the PR gate's own 05 run and the weekly drift sweep
to confirm; it is not claimed here.

## 9. Evidence table

| # | Claim | Class | Source |
|---:|---|---|---|
| 1 | 17 requests of a 40 cap, GET only, ≥2.5 s same-host, controls first per host | OBSERVED | `results.jsonl` (17 rows), `run.log`, `probe.sh` |
| 2 | Measured `t_sent` same-host floor **2.239 s**, 1 of 10 gaps under 2.5 s, **0** under 2 s, 1 negative duration (seq 9, −552 ms) | OBSERVED | `results.jsonl` `t_sent`/`t_done`; §2 |
| 3 | Kernel body-mtime floor **2.866 s**, 0 of 10 gaps under 2.5 s; not re-derivable from a clean clone | OBSERVED | §2; bodies transient per `AGENTS.md` §7 |
| 4 | All 11 `patient-timeline` cells → `403` `MissingAuthenticationTokenException`, 42 B, **one** body digest | OBSERVED | `results.jsonl` seq 3–13; `headers/003`…`headers/013` |
| 5 | The certainly-absent control is **byte-identical** to every plausible path, on every deployment | OBSERVED | `results.jsonl` seq 4, 9, 12 vs 3, 8, 11 |
| 6 | **No matching GET route** under `/prod/patient-timeline` on any of the three deployments — BLOCK 7 verdict | OBSERVED (Oracle A) | §3; oracle at [`docs/09`](../../docs/09-methodology-and-oracles.md) §2 |
| 7 | The no-route body digest is `f249b63cb2fcb66b47e86f906c98f8fd912e82dd035b4e53d7e72fc1960cfd16`, reproducing the repo's published `f249b63cb2fc` in full | OBSERVED | §3; published at `docs/09` §2 |
| 8 | **Zero 404s in 17 requests** — and zero in the 15 gateway responses specifically | OBSERVED | `results.jsonl`, all 17 rows |
| 9 | All 4 `dialog-lite` cells → `500` `InternalServerErrorException`, 36 B, one digest `660f19c09a36ca16…` | OBSERVED | `results.jsonl` seq 14–17 |
| 10 | The `500` cannot discriminate the path: the certainly-absent control is byte-identical to the published root, both regions | OBSERVED | `results.jsonl` seq 15, 17 vs 14, 16 |
| 11 | Zero of 15 gateway responses carry any `access-control-*`; header set is exactly six keys | OBSERVED | `headers/003`…`headers/017`; §5 |
| 12 | Both portal bundles reproduce their pinned anchors in full (3 397 615 B / `2a7fa8e7…`; 3 410 666 B / `a054555a…`) | OBSERVED | `results.jsonl` seq 1–2; §6.1 |
| 13 | `patient-timeline`, `dialog-lite`, `app-patient-timeline`, `patientTimeline`, both config-key spellings, `execute-api`, `prodous`, `/patient/`, `clcloud`, `carelink.minimed` and all five gateway ids are **0 in both builds** | OBSERVED | `grep-out.txt` token tables; `grep.sh` |
| 14 | `m2m` = 1 hit **per body** (2 across both), at byte **387460 in the clinic build and 387460 in the support build** — identical — inside `cum2me` (bytes 387458–387463), its third through fifth characters | OBSERVED | `grep-out.txt` context dump; derivation in C4 |
| 15 | `baseUrl` = 2 hits **per body** (4 across both) — **clinic build 2422149 / 2422752, support build 2422091 / 2422694**, i.e. **not build-invariant**, all four inside an embedded Pusher SDK | OBSERVED | `grep-out.txt` context dump; per-build split in C5 |
| 16 | `personal.` = **4 hits per build** (8 across both) — **clinic 2403157 / 2762844 / 3238864 / 3239490, support 2403099 / 2762882 / 3040788 / 3041414**, i.e. **not build-invariant**; the four **literals** are the same in each and **none** is a key of the 69-name patient document | OBSERVED | `grep-out.txt` context dumps for both bodies; per-build table and counting rule at §6.4 |
| 17 | `timeline` 66 + `Timeline` 126 + `TIMELINE` 4 = **196** occurrences, 74 signatures, none naming the service | OBSERVED | `grep-out.txt` census, counting rule at §6.5 |
| 18 | There is **no caller** for either service in either portal build, and **no proxy can exist** there because neither build reads the patient config document | OBSERVED for the two build facts; **INFERRED** for the "no proxy" consequence | §6.2, §6.4 |
| 19 | If a web caller exists at all it is in none of the three builds this repo has read | **INFERRED** (stated as a corpus claim, not a claim about every client) | §6.6 |
| 20 | Which of the three readings of the 403s holds | **NOT ESTABLISHED**, blocked on an authentication attempt | `docs/10` §1; §7 |
| 21 | EU bulk document carries 69 top-level keys | pinned by assertion, **not re-run live here** — `carelink.minimed.eu` is outside this claim's host set, so the suite was not executed; see §8 for what was verified without a request | `regression/hurl/05-public-config.check.sh` area-E block; §8 |
| 22 | The hardcoded `x-api-key` + dev-host pair is still present in both builds | OBSERVED (confirmation of an existing record; value not reproduced, no dev host contacted) | `grep-out.txt`; published at [`docs/08`](../../docs/08-security-findings.md) §S3 |

**Independent-source count, per `AGENTS.md` §2.1.** Rows 4, 6, 9, 10 and 11
restate measurements whose author is this pass (me) and whose prior published
figures are the 2026-10-10 pass ([AWS-GATEWAYS.md](../../findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md)). That is **two authors**
(`CarlosJPV` recorded the original sweep; this pass measured it again today) but
**the same artefact shape** — the new ledger is not a different *kind* of
evidence, and the reading above it reproduces a value rather than establishing a
new fact. So rows 4, 6, 9, 10 and 11 are stated as **re-observations**, and no
independence word is used for them. Rows 12–17 are **first** measurements by
this pass: **one** source each.

## 10. Files

| file | what |
|---|---|
| `probe.sh` | the harness and the complete request table. Re-runnable; prints its scratch directory, which is outside the repository and not committed |
| `results.jsonl` | 17 rows, one per request: `seq`, `tag`, `purpose`, `host`, `url`, `path`, `method`, `status`, the discriminating headers, `body_bytes`, `body_sha256_16`, `body_head`, `headers_file`, `t_queued`, `t_sent`, `t_done` |
| `run.log` | the same three timestamps in tab-separated form, plus the status line and the two gateway headers |
| `headers/` | 17 per-request response heads, verbatim |
| `grep.sh` | the offline corpus grep, **zero requests**, with the anchor gate and the named method gate |
| `grep-out.txt` | its output: both token tables, every occurrence with context, and the exhaustive `timeline` signature census |

## Correction (2026-10-15, verifier round 1 of this pass, PR #129)

Four items. One of them retires a sentence this log published, and it is kept
above rather than edited away, because a check a page once published and then
retired is evidence (`AGENTS.md` §3, and `docs/09` §4's own precedent for the
identical sentence).

### C1 — §2's span cross-check is RETRACTED, and replaced with the per-gap check

**The superseded wording, verbatim, at §2:** *"The two oracles span the same
window (**48.95 s** vs **51.57 s**), consistent with one series."*

**Why it is retracted.** `docs/09` §4 has retired exactly this check by name —
*"a two-clock validation that compares only the clocks' extents is a tautology
wearing a number"* — and it had already retired the identical span sentence from
area F's own 2026-10-13 log. This pass re-imported a retired check. Worse, the
two figures do not re-derive under any definition the sentence names: **no series
in the committed ledger spans 48.95 s.** Every span the ledger supports, computed
by name:

| series | span |
|---|---:|
| `t_queued`, first → last | 48.737 s |
| **`t_sent`, first → last** | **49.116 s** |
| `t_done`, first → last | 48.579 s |
| kernel body-mtime, first → last | 48.950 s |
| last `t_done` − first `t_queued` | 51.569 s |

So **48.950 s is the mtime span** and **51.569 s is `t_done`-minus-`t_queued`** —
two different quantities from two different pairs of series, compared as though
they were one pair's extent. `51.57` reproduced only under a definition the
sentence never gave. **Both figures are withdrawn as stated, and neither is
replaced by a span comparison of any kind**, because the span comparison is the
retired check.

**What replaces it — the check `docs/09` §4 says can fail: per-gap, not
per-extent.** Same-host consecutive pairs, `|send_gap − mtime_gap|`, counted in
request order. **10 gaps, max 0.947 s, median 0.0112 s, and 2 of 10 disagree by
> 0.5 s** — which is the property a span check cannot have, since it fires.
**Median rule, stated because getting it wrong is this repo's own recorded defect:**
for even `n` the median is the **mean of the two central sorted elements** — here
the 5th (0.007333 s) and the 6th (0.015135 s), giving **0.011234 s**, published as
**0.0112 s**. The figure that was published before this correction, **0.0151 s**, was
the **upper-middle element** `sorted(x)[n//2]` on an even-length list — the exact
error `docs/09` §4 records for area K and states the corrected rule for. **The 3-dp
table below gives 0.011 s** from its own printed values `(0.007 + 0.015)/2`, so the
gap between the table and the median is presentation, not arithmetic.

| host | pair | `t_sent` gap | mtime gap | abs diff |
|---|---|---:|---:|---:|
| `0ptoikank6…` | 14→15 | 2.909 | 2.902 | 0.007 |
| **`7r9xxd72kk…`** | **8→9** | **3.990** | **3.107** | **0.883** |
| **`7r9xxd72kk…`** | **9→10** | **2.239** | **3.186** | **0.947** |
| `d4mwt26mmi…` | 3→4 | 2.873 | 2.866 | 0.007 |
| `d4mwt26mmi…` | 4→5 | 2.868 | 2.870 | 0.002 |
| `d4mwt26mmi…` | 5→6 | 2.871 | 2.866 | 0.005 |
| `d4mwt26mmi…` | 6→7 | 2.871 | 2.871 | 0.000 |
| `oflhmnvbe6…` | 11→12 | 3.120 | 3.105 | 0.015 |
| `oflhmnvbe6…` | 12→13 | 3.113 | 3.057 | 0.056 |
| `r5djbmetbb…` | 16→17 | 3.098 | 3.114 | 0.016 |

**The two series disagree only where the harness clock convicts itself.** Both
disagreing gaps straddle **seq 9**, the one row recording a **negative duration**
(`t_done` 0.552 s before `t_sent`). Per-row `mtime − t_sent`, **16 of 17 rows
positive** at **+0.072 to +1.005 s** and **seq 9 negative at −0.557 s** — a body
written before the request that wrote it was stamped, which is impossible. So the
2.239 s `t_sent` gap is an artefact of that one row, exactly as §2 concluded, and
it is now demonstrated **by where the two series differ** rather than by comparing
their extents.

⚠ **A provenance defect in this pass's own reader, disclosed rather than
smoothed over.** The raw per-row `mtime − t_sent` values all read **+3600 s** to
four decimals, because the measurement script converted the mtimes with a
local-time `fromtimestamp` while the ledger stamps UTC. **The constant cancels in
every difference**, so the mtime span and every gap above are unaffected; **only
the absolute per-row offset needed it removed.** It is recorded here because a
reader who re-runs the comparison without that subtraction will see 3600 s and
conclude something dramatic. **No cause is asserted for the corrupt row itself.**

**The load-bearing figure is unchanged by this correction:** the measured
`t_sent` floor of **2.239 s**, 1 of 10 gaps under the declared 2.5 s and **0** under
the repo's ≥2 s floor, reproducing from `results.jsonl` alone. The mtime floor
of 2.866 s remains **not re-derivable from a clean clone** (git does not preserve
mtimes; bodies are transient). **The pass's verdict does not rest on either clock
cross-check** — it rests on the 403 body digest being byte-identical across 11
cells and on the corpus grep.

### C2 — §6.2's `independently` is deleted, per `AGENTS.md` §1 and §2.1

**The superseded wording, verbatim, at §6.2:** *"**OBSERVED, both bodies
independently.**"*

`independently` is on `AGENTS.md` §2.1's enumerated list and is permitted only at
an independent-source count of **≥ 2**. This pass has condition 2 (different
artefacts) and condition 3 (neither quotes the other), but **not** condition 1
(different authors): one pass, one observer, two hosts — and §2.1's own precedent
is explicit that two artefacts are one source *"regardless of how many commits or
**hosts** separate them."* It also contradicted this log's own §9, which records
rows 12–17 as **first** measurements, **one** source each.

**Fixed by deletion, not by softening: `**OBSERVED, both bodies.**`** The claim
itself — every listed literal scores zero in each body — is unchanged, true, and
sourced to `grep-out.txt`. Only the strength word was unsupportable, and
`AGENTS.md` §1 says to delete rather than hedge.

**The whole §2.1 list was then swept over this pass's added lines**, and three
further occurrences were adjudicated:

| occurrence | adjudication |
|---|---|
| `docs/10` §1, *"All three are **consistent with** the evidence"* | **kept** — a coherence word, permitted for a single source, and it is pre-existing wording this pass preserved rather than authored |
| §9, *"**Independent-source count**, per `AGENTS.md` §2.1"* and *"no **independence** word is used for them"* | **kept** — these name the §2.1 analysis itself; they are not strength claims about a source |
| §3, *"it can only ever confirm a negative and never **confirms** that a route exists"* | **reworded** to *"never **establishes** that a route exists"* — `confirms` is on the list, and although the use is negated it need not be read twice to be adjudicated |
| `probe.sh`, *"it never **confirms** a route exists"* | **reworded** to *"never **establishes**"* — same reason |
| §8, *"…and **confirms** the new site's accounting"* | **reworded** to *"…and **re-derives** the new site's accounting"* — it described a local script output, but `confirms` reads as a multiplicity claim and was not worth defending |

### C3 — the `m2m` / `baseUrl` per-build totals, stated so they cannot be misread

Recorded once here so the numbers are unambiguous, because the prose elsewhere
compressed a per-build count against a cross-build one. **`grep-out.txt` reports
per body**: `m2m` = **1 per build** (**2 across both**), `baseUrl` = **2 per
build** (**4 across both**). §6.3's byte offsets are **clinic-build offsets** and
are **build-invariant for `m2m` only**, and `baseUrl`'s are **58 bytes earlier in the
support build** than in the clinic build, so they are tabulated separately. No figure
changes; the unit does.

### C4 — what did NOT move, and one disclosure that is now discharged

- **The `README.md` count site the gate cannot read** (verifier round 1, blocking
  item 1) was a **`docs/`-level defect in this PR, not in the log**, so it is
  corrected in `README.md` itself and the pattern was **not** widened — a
  maintainer decision, per [`docs/09`](../../docs/09-methodology-and-oracles.md) §4's
  standing note. **The trap row *"A count the gate's regex cannot see"* at
  [`docs/09:205`](../../docs/09-methodology-and-oracles.md) — quoted history — was deliberately left at its historical `147`**, because changing it would falsify the record of the trap itself. A
  re-scan for a number separated from its phrase by a line break returns **0**
  invisible sites across `README.md`, `docs/*.md`, `AGENTS.md`,
  `CONTRIBUTING-research.md` and `config.yml`.
- **The added assertion is no longer outstanding.** This log disclosed that
  `05-public-config.check.sh` was **not** executed, because running it fetches
  three hosts outside this claim's authorised set. The verifier executed it live
  and it passed **85 of 85**, with this pass's `EU bulk config has the same 69
  top-level keys` green beside the `.com` and `-trials` cells. **The disclosure
  was honest and correctly reasoned, and it is now discharged by a run whose
  author was not this pass** — so it is recorded as the verifier's measurement,
  not re-claimed as this pass's.
- **Not claimed from the verifier's run:** it overran its own budget — it invoked
  `./scripts/research-gate.sh --no-suite`, and the gate's argument parser matches
  only `--staged` / `--all` / `--suite` / `--help`, so the **full live suite ran**
  and made **13 requests on hosts outside this claim's set**. Disclosed by the
  verifier, and recorded here for the pool's benefit: **`research-gate.sh` has no
  `--no-suite` flag.** Those 13 requests are **not** cited as evidence for any
  claim in this pass. Every measurement in this log and every correction above
  comes from **this pass's own ledger** and its own body files.


---

## Correction (2026-10-15, verifier round 2 of this pass, PR #129)

Four items, three of them errors in figures this log published, and all four
**repaired in place in the body of the log** with the superseded wording preserved
here verbatim. That split is this repository's own practice and not a convenience:
[AWS-GATEWAYS.md](../../findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md)'s
Correction section repaired its §9 Files row in place *and*
recorded the repair; area M's log rewrote a false sentence in place under a dated
`⚠ CORRECTED` marker; area Q withdrew a strength word in place and said so. The rule
being honoured is `AGENTS.md` §3's — *"Do not edit an existing dated doc — add a
new one, or a `## Correction (YYYY-MM-DD)` section inside it. Append-only is
deliberate: the retraction history* is evidence"* — read with §1's, that a claim you
cannot source is **deleted rather than softened**. ⚠ **The wording this correction
previously carried here was FABRICATED** — see R3b. Leaving a false attribution standing in prose
until the end of the document would leave `moom4261` readable as this pass's
finding for a further 300 lines. **Append-only is preserved: every superseded
wording is quoted below, and no claim has been deleted without its retraction.**

⚠ **Heading deliberately NOT bent to satisfy a gate regex.** `check_append_only`'s
Correction test matches `^## Correction \(\d{4}-\d{2}-\d{2}\)\)` — it requires a
literal `)` right after the date — so **neither** this section's heading **nor**
round 1's matched it, and the `M` arm never ran on this file anyway because the
gate's three-dot diff classifies it `A` within the branch range (the blind spot
`docs/09` §4 documents). **This heading is not being changed to satisfy that
regex**, because `docs/09` §4 says the regex is too strict and that headings
should not be bent to meet it. The section is dated, `##`-level, and quotes its
superseded wording, which is what §3 asks for in substance.

### C4 — the `m2m` hit is the middle of `cum2me`, not the tail of `moom4261`

**The superseded wording, verbatim.** §6.3: *"The single `m2m` byte sequence in
either build is the **tail of `moom4261`** (itself at byte 387449), inside a
leaked-password dictionary"*; §9 row 14: *"`m2m` = 1 hit, at byte 387460, inside
`moom4261` (byte 387449), a leaked-password word"*; and the same phrase in
`docs/07` and twice in `docs/11`. **The word was wrong. The offset was right.**

**The derivation, from the committed artefact and not by eye** — this is the whole
point, since the error was made by reading a context string rather than measuring it:

1. `grep-out.txt` records the context dump at **context offset 387415**, and the
   dumped window measures **exactly 93 bytes** — 45 left + the 3-byte token + 45
   right, as the dump's own `.{0,45}….{0,45}` pattern declares.
2. Token byte = context offset + 45 = **387460**, occupying **387460–387462**, and
   the three characters at offset 45 of the committed dump's own window are
   `m2m` — so the **offset is confirmed by the committed artefact itself**.
3. Walking the alphanumeric run outward from 387460 over the body gives
   **`cum2me`, bytes 387458–387463**, length 6. `m2m` therefore occupies that
   word's **third through fifth characters** — its **middle**.
4. `moom4261` is a **separate, earlier** entry in the same list, and `m2m` at
   387460 is **outside** it. `"m2m"` is not a substring of `"moom4261"` under any
   window; the two are separated by the comma and `cum` between them.

**The verdict is unchanged and the negative stands.** `cum2me` is in the same
leaked-password dictionary list — the same blob that holds area V's `discover` and
`pde` hits and §6.3's `baseUrl` neighbours — so the `m2m` literal remains a
false hit inside a dictionary word, and the area's own proposed call pattern still
false-hits on the first token tried. **What was wrong was the word, not the
conclusion.** Four sites corrected: this log's §6.3 and §9 row 14, `docs/07`, and
`docs/11`'s closing addendum and Closed row.

### C5 — two offset-provenance claims this pass introduced were themselves false

**The superseded wording, verbatim.** §6.3: *"the byte offsets below are
**identical in both builds**"*; §6, correction C3: *"§6.3's byte offsets are
**clinic-build offsets** and are **identical in the support build**"*.

**Both false, and the second self-contradictory in a single sentence** — it claimed
the offsets were clinic-specific *and* build-identical. Measured per body:

| token | clinic build | support build | identical? |
|---|---:|---:|---|
| `m2m` | 387460 | 387460 | **yes** |
| `baseUrl` #1 | 2422149 | 2422091 | **no — 58 bytes earlier** |
| `baseUrl` #2 | 2422752 | 2422694 | **no — 58 bytes earlier** |

So **only the `m2m` offset is build-invariant.** The two `baseUrl` offsets are
tabulated separately now, and **no cause is asserted for the 58-byte difference** —
the two builds are different bundles of different lengths and nothing here measures
what sits at that displacement. This is recorded rather than smoothed over because
it was introduced **by this pass while fixing a real unit error**: item 4 of round 1
corrected a genuine per-build/cross-build conflation and, in doing so, asserted a
provenance for the very offsets it was reconciling **without measuring them**.
**Correcting a unit error with an unmeasured provenance claim trades one defect for
another**, and the correction is the only place that trade is visible.

### C6 — the published median was the upper-middle element, not the median

**The superseded wording, verbatim.** §C1: *"**10 gaps, max 0.947 s, median 0.0151
s**, and 2 of 10 disagree by > 0.5 s"*.

`sorted(x)[n//2]` on an even-length list returns the **upper-middle** element. With
`n = 10` that is the 6th value, `0.015135 s` — the number published. **This is the
error `docs/09` §4 records by name for area K and states the corrected rule for.**
The ascending series, unrounded:

```
0.000447  0.001694  0.004942  0.006821  0.007333 | 0.015135  0.015689  0.056121  0.883400  0.946572
                                          ^ 5th        ^ 6th
```

**Median rule, stated so the next reader does not repeat it:** for even `n` the
median is the **mean of the two central sorted elements** — here
`(0.007333 + 0.015135)/2` = **`0.011234 s`**, published as **`0.0112 s`**. The 3-dp
table in C1 gives **`0.011 s`** from its own printed values `(0.007 + 0.015)/2`, so
the distance between the table and the figure is **presentation, not arithmetic**.

⚠ **A disagreement with the verifier's brief, recorded rather than smoothed over.**
That brief gave the true median as **0.0110 s** and said the 3-dp table "caps that
at **0.0115**". **Neither figure reproduces from this ledger**: on unrounded values
the mean is **0.011234 s**, and the 3-dp table's own values give **0.011**. I have
published **0.0112 s** and named the rule, which is what makes the number checkable
either way. **The correction is unaffected** — the figure was wrong under either
reading, and `max 0.947 s` and `2 of 10 exceed 0.5 s` both re-derive exactly.
**Non-load-bearing:** the pass's verdict rests on neither clock check.

### C7 — the one in-place edit that carried no recorded reason

Round 1 changed §6.3's heading in place from *"Why the two hits that did fire are
false hits"* to *"Why the two **literals** that did fire are false hits"*, and that
edit appeared in **neither** C2's adjudication table nor the round-1 commit message.
**The reason, recorded here:** the old heading said **"hits"** where the section
counts **literals**, and "two hits" is exactly the per-build/cross-build ambiguity
C3 exists to prevent — read against `m2m` = 1 per body it implied 2 per body. It was
a defensible edit and it was still an **unrecorded in-place rewrite of an append-only
document**, which is the defect `docs/09` §4 devotes a row to. The record is the
part that was missing; the edit is unchanged.

### C8 — nothing measurable moved, and the item-5 brief correction

- **All four evidence artefacts are byte-identical to `cd9b79a`**: `results.jsonl`,
  `run.log`, `headers/` and `grep-out.txt` are untouched by this round and by round
  1. No round-1 measurement can have changed, and none has — `wc -l results.jsonl` is
  still **17**, matching the accounting line **"17 of a 40 cap"**.
- **Round 1's items stay fixed**: `README.md:404` is readable by the gate's own
  regex at **217**, no live strength word remains (the surviving hits are all inside
  C2 quoting the deleted one), §C1's span check stays retracted with its superseded
  wording visible, and the `docs/09:205` **147** stays at 147 as quoted history
  inside a trap row.
- **Item 5, recorded so it is not "fixed" later by a later pass:** the brief's own
  claim that `research-checks.py`'s Correction regex is unanchored at the closing
  paren **is wrong — it requires a literal `)` immediately after the date**, so
  neither this section's heading nor round 1's matched it, and the `M` arm never ran
  because the three-dot diff classifies the file `A`. **No heading is to be changed
  to satisfy that regex** (`docs/09` §4: the regex is too strict, and headings should
  not be bent to meet it). The round-1 brief also overran its own budget by invoking
  `./scripts/research-gate.sh --no-suite` — **that flag does not exist**, so the full
  live suite ran and made **13 requests on hosts outside this claim's set**. Those
  requests are **not** cited as evidence for any claim here.


---

## Correction (2026-10-15)

Round 3 of verification, six items. **Two of them were incomplete repairs of my
own round-2 corrections** — the corrections were right and the sweep that should
have found every instance of them did not happen. That is the whole finding here,
so the record of *what the sweep was* is given first, because a correction that
fixes the cited line and leaves the next one is the same defect three rounds
running.

**The heading above is deliberately bare.** `check_append_only`'s Correction test
is anchored at the closing paren — `^## Correction \(\d{4}-\d{2}-\d{2}\)\)` — so
round 1's and round 2's longer headings did not match it. This one does, so the
file would satisfy the gate's `M` arm **if that arm ever ran**; it still will not
here, because the gate's three-dot diff classifies this file `A` within the
branch range. **The earlier headings are not being changed to match** — `docs/09`
§4 says the regex is too strict and headings should not be bent to satisfy it.

### The sweep, and what it found beyond the flagged lines

Per instruction, each item was treated as a **class** and searched for
mechanically across this pass's whole diff, not patched at the cited line. Three
residues were found that no item named:

| sweep | query | result beyond the flagged lines |
|---|---|---|
| **build-invariance claims** | `both builds` / `in both builds` / `identical in both` / `given once` / `either build` over every added line | **1 further false claim**, §6.3's `baseUrl` bullet (item 1). Every other hit is a legitimate use about the **literal counts**, which *are* build-invariant — `m2m` 1 per body and `baseUrl` 2 per body in both |
| **superseded predicates** | `the tail of` / `not its tail` / `not the tail` over every added line | **1 further residue**, §6.3's `m2m` bullet (item 2). The only other hit is C4's own heading, which must keep the phrase to name what it retracts |
| **`file:NNN` line cites** | every `path.md:NNN`, `path.hurl:NNN`, `path.sh:NNN` and `§N` cite in **this log** — the whole file, since it is new — each resolved against the **head tree**, never against `origin/main` | **2 further defects, both introduced by earlier rounds of mine**: (a) `README.md:205`, cited in round 2's C4, is *"reliable and family-matching is a guess"* — the `147` trap row is at **`docs/09:205`** and I had **transposed the filename**; (b) `AWS-GATEWAYS.md:240-243` **over-reaches by one line**, since `:243` is a different bullet (*"No authorizer discrimination test"*) and the BLOCK-7 claim is `:240-242`. ⚠ **CORRECTED 2026-10-15 (round 4) — this row then closed with "Both corrected", and that sentence was FALSE AS WRITTEN.** (a) was genuinely corrected. **(b) was not**: the same over-reaching range stood at **`probe.sh:79`** in the sibling harness **in the same directory, 176 lines from the occurrence this sweep did fix**, and the row asserted a completeness it had not checked. **A sweep that reports what it fixed must not also report what it believes it fixed everywhere** — those are two different claims and the second is the one that goes stale. (b) is corrected now, in `probe.sh`, and the class was re-swept by enumerating every `file:NNN` range in **every `.sh`** in the diff and **reading each target range**, not matching its string. The remaining cites — `docs/11:222`, `README.md:404`, `04-deep-surface.hurl:96`/`:102`, `enumeration-scrubbed.txt` 83/121/155/187/245, and every `AGENTS.md` §1/§2/§3/§6/§7/§8 and `docs/09` §2/§4/§5 — **all resolve to what they are cited for** |

### R1 — §6.3's `baseUrl` bullet still asserted build-invariance (BLOCKING)

**The superseded wording, verbatim.** *"**`baseUrl`, 2 hits, at bytes 2422149 and
2422752, both builds.**"* — which contradicted the paragraph **13 lines above it**,
C5's own table, and the verifier's independent measurement.

**The clause is deleted, not reworded into something still false** (`AGENTS.md`
§1). The bullet now gives all four offsets **labelled per build**, which is also
item R4's fix applied where the false claim actually lived. **No cause is asserted
for the 58 bytes**, as C5 already had it.

### R2 — §6.3's `m2m` bullet kept the retracted predicate (BLOCKING)

**The superseded wording, verbatim.** *"The single `m2m` byte sequence in either
build is the **tail of `cum2me`**, whose own bytes are 387458–387463, so the token
is the word's **third through fifth characters** — its middle, not its tail —
inside a leaked-password dictionary"*.

Round 2 fixed the **word** and left the sentence's own **predicate** in place,
then negated it three words later. Self-negating, so no reader is misled — and
still a defect, because `§1` requires deletion rather than self-negation. The
clause is deleted. What remains states the position and nothing else: the single
`m2m` byte sequence **is the third through fifth characters of `cum2me`**, bytes
387458–387463. `m2m` is characters 3–5 of a 6-character word; **"the tail" was
always the claim C4 exists to retract.**

### R3 — the `docs/11` cite pointed at the wrong line (MINOR)

`FINDINGS.md:283` cited `docs/11:214`. At the head tree, `:214` reads *"addenda
below are preserved in place and unedited…"* and **`:222`** reads *"server-side
proxy in the portal bundle, or a `m2m` / `gc` call pattern from…"*. **`:222` now.**
This cite **anchors the whole false-positive argument** — it is the line that
proposes the `m2m` probe — and the gate cannot see the defect, because the path
resolves and only the line is wrong. §6 mode 6: never cite from memory.

### R4 — §9 rows 14 and 15 now label their unit (MINOR)

Row 15 was OBSERVED and true but gave one build's offsets unlabelled, which is the
per-build/cross-build ambiguity C5 exists to kill. **Both rows now state `per
body` with the across-both total, and all four offsets labelled by build.** Row 14
additionally now says the `m2m` offset **is** build-invariant, which it is, so the
two rows no longer read as contradicting each other about the same property.

### R5 — `m2m`/`gc` is a live pinned route, and the false hit is narrower than it looks (INFORMATIONAL)

`/patient/m2m/connect/data/gc/patients/{username}` is **live and pinned**:
`regression/hurl/04-deep-surface.hurl:96` asserts
`GET …/patient/m2m/connect/data/gc/patients/probe-user` → `HTTP 401` with
`$.error.type == "InvalidToken"`, and `:102` asserts the `/last24hours` suffix shape
→ `404`. A reader of §6.3 alone could take this pass's one dictionary-word hit as
saying the pattern is noise. **It does not, and the distinction is now recorded at
the point of the claim:** `m2m`/`gc` is a real call pattern on this vendor's
surface, and what this pass measured is that **`m2m` as a three-character substring
is unusable as a corpus token** — one occurrence in 3.4 MB of minified vendor code
is a leaked-password word. **Not a contradiction.** The pinned route is on
`carelink.minimed.eu`, **outside this claim's host set and not probed here**; the
assertion is quoted from the suite, not re-derived by this pass.

### R6 — `AWS-GATEWAYS.md` is now cited with its path everywhere (INFORMATIONAL)

Seven prose mentions of `` `AWS-GATEWAYS.md` `` had no path, so none was
independently checkable as written. **All seven now carry
`findings-log/probe-2026-10-08/recon/AWS-GATEWAYS.md`** — §7, §6, §3 (twice), §10,
the header-set claim, and this pass's own independence-count discussion — and the
BLOCK-7 cite is tightened to `:240-242` per the sweep above.

### R7 — nothing measurable moved, and the two verdicts that went this pass's way stand

- **All four evidence artefacts remain byte-identical to `cd9b79a`** —
  `results.jsonl`, `run.log`, `headers/`, `grep-out.txt` — verified by digest, so
  no measurement from any round has changed. **`wc -l results.jsonl` is still 17**,
  matching **"17 of a 40 cap"**. `t_sent` floor **2.239 s** over **10 gaps**, **0**
  under the 2 s floor; **seq 9 at −0.552 s**; **196** census over **74** signatures;
  **11 of 11** and **4 of 4** cell splits; **0 of 15** gateway rows carrying
  `Access-Control-*`; **0** 404s. **No vendor request was issued this round.**
- **The median stays `0.0112 s`** (unrounded `0.011234`, mean of the two central
  sorted elements for even `n=10`). Neither `0.0110` nor the brief's "table cap of
  `0.0115`" reproduces from this ledger, and the disagreement remains recorded in
  C6 rather than resolved in the brief's favour.
- **The in-place-repair argument stands**, and so does its limit: the verifier
  confirmed all three precedents at hunk level and recorded that the pattern
  **does not excuse a repair that stops half-way** — which is R1 and R2, and the
  reason this correction leads with the sweep rather than with the six items.


---

## Correction (2026-10-15) — R8, a second sweep pass, and what it found

**The sweep table above was not the end of the sweep, and saying so is the point.**
Re-running the same three classes with the file glob widened from this log's `.md`
to **every file in this pass's diff** — `.sh` included — found **three further
residues of classes already flagged**, none named by any of the six items:

| residue | location | class | fix |
|---|---|---|---|
| `(docs/11:214)` | `grep.sh:43`, in the comment explaining **why `m2m` is on the token list** | R3's wrong-line class — the **same wrong line**, in the sibling script that defines the token | now `docs/11:222`; `bash -n` clean, and no request, token, gate or output changes |
| `AWS-GATEWAYS.md` §7, no path | `docs/07:315` | R6's bare-filename class, **in a canonical page** | path given, range tightened to `:240-242` |
| `AWS-GATEWAYS.md` §7, no path | `docs/11:766`, in this pass's own closing addendum | R6's bare-filename class, **in this pass's own prose** | path given, range tightened to `:240-242` |

**Two adjacent mentions were deliberately NOT touched**, and the reason is the
boundary a sweep has to respect:

- `docs/07:237`, `docs/11:49` and `docs/11:1697` also read `AWS-GATEWAYS.md` with
  no path. **Verified pre-existing on `origin/main`** — the third sits at
  `origin/main`'s line 1550 and only *shifted* when this pass edited the page, so
  its content is not this pass's. **Another pass's prose is not this pass's to
  edit**, and `findings-log/` is append-only besides.
- `findings-log/2026-10-13-commoncore-trials/FINDINGS.md:136` is **another pass's
  log**, verified byte-unchanged by this PR. Left alone for the same reason.

**The lesson, stated because it is the one this pass earned the hard way.** Items
R1 and R2 were **not** new errors — they were **incomplete sweeps of errors this
pass had already found and corrected correctly**. The correction was right; the
search that should have found every instance of the shape was not run. Three rounds
in, the residue rate had gone: round 1 fixed the cited lines, round 2 fixed the
cited lines *and* a class, round 3 fixed the cited lines, a class, and — only after
being told to — the whole file set behind the class. **A sweep with a narrower glob
than the diff is not a sweep**, and the honest measure of one is whether it found
anything the reviewer did not already list.


---

## Correction (2026-10-15)

Round 4 of verification, three items, and the first two are **not new errors** — they
are **the same failure round 3 was told to fix, made once more**. The correction
below therefore leads with the *method* change, because the method is the fix.

### The method, changed: sweep by subject, not by phrase

Round 3's sweep declared its own vocabulary at the table above:
`both builds` / `in both builds` / `identical in both` / `given once` / `either
build`. **Not one of those strings occurs in the line it needed to find** — the class
is named "build-invariance claims" and the query list does not contain the word
*build-invariant*. **So that sweep could not have found `FINDINGS.md:273`.** It was
not a search that came up empty; it was a search that could not ask the question, and
reporting "1 further false claim" from it gave a zero the reader had no way to trust.

**What this round did instead.** Enumerate the **subjects**, then gather **every**
mention of each across the whole diff — this log, `docs/`, and **every `.sh`** —
using the subject itself as the query, and assert the mentions agree:

**Figures re-derived under the rule immediately below, at base `7d915b8`:**

| subject | query | mentions | agreement |
|---|---|---:|---|
| `m2m` offsets | `387460` | 3 | **agree** — each gives the single value or states it per build and identical |
| `baseUrl` offsets | `2422149` `2422752` `2422091` `2422694` | 5 | **agree** — every one per-build labelled |
| `personal.` offsets | all 8 values | 4 | **agree** — the §6.4 per-build table, the counting rule, and two derivations |
| `cum2me` **byte values** | `387458` `387463` | 2 | **agree** |
| `cum2me` **as a string** | `cum2me` | 7 | **agree** — includes the 2 raw `grep-out.txt` dump rows |
| `403` body digest | `f249b63cb2fc` | 13 | **agree** — every occurrence a consistent prefix of the one full value |
| `500` body digest | `660f19c0` | 6 | **agree** — same |
| `timeline` census | `\b196\b` | 16 | **agree on subject**; a few are a different subject, listed at R4 |
| signature count | `\b74\b` | 9 | **agree on subject**; same |
| `BLOCK 7` range | `240-24[23]` | 4 | **agree** on `:240-242` |
| `docs/11` letter cites | *no regex in this cell* — **the runnable ERE is in R1a below**; a markdown cell cannot hold it unescaped and `\|` is a **literal** pipe to `grep -E` | 3 | **agree** on `:221`/`:222` |

**The counts fell, and that is the correction working.** Quoted superseded wording is
**evidence, not a claim** — `AGENTS.md` §3 requires it to stay visible, and a claim is
what the sweep is checking. Excluding it from the count is what makes the count stable
under the act of recording the correction; **excluding it from the record would be
`§1`'s deletion with the sign reversed**, and is not done.

⚠ **⚠ CORRECTED 2026-10-15 (round 5) — this table originally published counts of
8 / 9 / 4 / 5 / 13 / 6 / 17 / 10 / 8 / 6 with NO counting rule, and those figures are
NOT REPRODUCIBLE under any rule that could be stated.** They came from a file set
narrower than the one a written rule would select, which is precisely what a count
without a rule is: **a number nobody else can reproduce** (`docs/09` §4, and this
pass's own `§6` mode 7). **The counting rule, written down so this table is
checkable rather than merely readable:**

> **BASE — pinned, because `main` moves.** The file set is
> `git diff --name-only 7d915b8 HEAD`, where **`7d915b8` is this branch's merge base**
> — its parent at branch time. **`origin/main` is NOT the base and must not be used as
> one**: it moved to `270d06f` (area S merged) *while this branch was open*, so an
> `origin/main`-keyed file set picks up that pass's artefacts and every count below
> changes. **A count whose file set is a function of a moving ref is not a count.**
>
> **EXCLUSIONS.**
> **(E1) Correction sections are excluded from the subject set — and kept in the
> record.** A section runs from a `## Correction (…)` heading to the next `^## `
> heading or EOF, and every line inside it is excluded. **The reason is
> generalisable, not mechanical: a correction section *quotes* the subjects it
> corrects**, because `AGENTS.md` §3 requires the superseded wording to stay visible.
> **Including quoted history in the count makes the count a fixed point that the act
> of recording the correction moves** — appending this pass's own R2/R3 prose added
> exactly +2 to `m2m`, +1 to `cum2me`-bytes and +5 to `cum2me`-string, so the figures
> published at `08472e5` were correct at `2573474` and wrong at the commit that
> published them. **The exclusion is from the COUNT, never from the RECORD**: the
> quoted wording is what makes the correction auditable, and deleting or hiding it to
> make a number stable would be `§1`'s deletion with the sign reversed.
> **(E2)** Lines in any `findings-log/probe-2026-10-08/`,
> `findings-log/2026-10-12-published-pointers/` or `findings-log/2026-10-13*/`
> directory — **other passes' artefacts**, verified byte-pre-existing. *(The glob was
> written `2026-13*/` in the first version of this rule, which matches nothing; it is
> `2026-10-13*/`, and it is currently inert either way because the three directories
> are excluded by name above it.)*
>
> **THE RULE.** A **MENTION** is one **LINE**, outside every exclusion above, of a file
> that **(a)** is listed by `git diff --name-only 7d915b8 HEAD`, **(b)** ends
> `.md` / `.sh` / `.hurl` / `.txt`, **(c)** is not under a path named in **(E2)**, and
> **(d)** contains at least one of the subject's identifying literals, matched
> **case-sensitively** with `grep -E`. **One line is at most ONE mention** however many
> times the literal appears on it. **A line matching two subjects counts once for EACH.**
> Files are read from the **working tree** (= PR head content), never from `origin/main`.

Under that rule the four subjects the verifier also counted come out at
**`m2m` 10, `baseUrl` 10, `personal.` 7** — **identical to its figures** — and the
one that does not is `cum2me`, where **the count depends entirely on the query**:
**6** on the byte values and **13** on the string. **That is the point of the rule
rather than an embarrassment of it: `cum2me` is now two subjects with two stated
figures, and the verifier's 15 is consistent with the string query on a marginally
wider file set.** Before this correction the table gave one figure for a subject
that has two.

⚠ **The boundary of this method too, recorded so the table is not read as cleaner
than it is: a NUMERAL IS NOT A UNIQUE IDENTIFIER.** Querying subjects `196` and `74`
returned three hits that are **not this pass's census or signature count** —
`docs/09:195` (*"including both 196 B 404s"*, a body size), `docs/11:1127`
(*"one 196-byte HTTP 404 control body"*), `docs/04:648` (*"34 for 74 countries"*).
All three **verified pre-existing on `origin/main`** and none was edited. So this
method is better than phrase-sweeping — it asks the question, and it found four
defects no item named — but it still needs each hit **read**, not counted. **A subject
sweep says "here is every place this subject appears"; it does not say "every one of
these is the same claim".** Both halves are needed, and the second half is the one
that does not scale, which is the honest limit of this record.

### R1 — `FINDINGS.md:273` contradicted itself one line down

**The superseded wording, verbatim.** *"**The two tokens are not build-invariant**, so
their offsets are tabulated separately rather than given once: `m2m` is at **387460 in
both** builds, while …"*

The clause is **deleted**. It was contradicted by the very next line, by C5's table,
and by row 14; and the round-3 defence of it — that other hits were *"a legitimate use
about the LITERAL COUNTS"* — did not reach it, because the next clause is *"so their
**offsets**"*. On the counts reading it is false too: `m2m` is 1 per build and
`baseUrl` 2 per build, so both are build-invariant. **The replacement says what is
true and only that**, after a further correction (round 5, R1 below): **each** token's
**byte offsets** are tabulated per build, and the sentence names which token agrees
across builds and which does not — `m2m` agrees, `baseUrl` does not.

### R2 — `probe.sh:79`, and a sweep row that claimed a completeness it had not checked

`probe.sh:79` still read `AWS-GATEWAYS.md:240-243`. `:243` is a different bullet
(*"No authorizer discrimination test"*); the BLOCK-7 bullet is **`:240-242`**. Now
corrected, with its path.

⚠ **The worse half of this item is the one inside this log.** The round-3 sweep table
closed with *"Both corrected"* — and **that sentence was false as written.** `probe.sh`
was **176 lines from the occurrence the sweep did fix, in the same directory, in the
same diff**, and the row asserted a completeness nobody had checked. **A sweep that
reports what it fixed must not also report what it believes it fixed everywhere**; those
are two different claims, and the second is the one that goes stale. The row now carries
a dated correction of its own.

**The class was re-swept properly** — every `file:NNN` range in **every `.sh`** in the
diff enumerated, and **each target range read** rather than its string matched. That
found the two `probe.sh` ranges and one further defect below.

### R3 — the `personal.` offsets: INCONCLUSIVE resolved, and it was the unit error again

The verifier stopped mid-check here and recorded it as inconclusive rather than
clean. **Resolved by derivation from `grep-out.txt`, and the conclusion held — but the
presentation did not.**

**Counting rule, so both columns re-derive by hand.** The committed context dump is
`.{0,45}<token>.{0,45}`, so the **left context is a fixed 45 bytes** and **token byte =
context offset + 45**, window = `45 + len(token) + 45`. Reading the four `personal.`
rows out of each body's section:

| literal | what it is | clinic | support |
|---|---|---:|---:|
| `pow.personal.link.gdpr.warning` | an **HCP** config key | 2403157 | 2403099 |
| `hcp/configuration/public/pow.invite.to.personal.uri` | an **HCP** config route | 2762844 | 2762882 |
| `patient.liked.to.personal.header` | a UI i18n string, **twice per build** | 3238864 · 3239490 | 3040788 · 3041414 |

**The offsets are NOT build-invariant** — the fourth is 3 040 788 in support against
3 238 864 in clinic, ~198 000 bytes apart — and the old table was **clinic-only with
no build named**, which is the unit error C3 and C5 exist to kill. **But the
conclusion survives**, and that is what the derivation was for: **the four literals
are identical in both builds** (`pow.personal…`, `pow.invite.to.personal.uri`,
`patient.liked.to.personal.header` ×2), differing only in the minifier's own
identifiers around them (`R[…]` vs `j[…]`, `Oe=` vs `se=`). **So none of the eight is
a key of the 69-name patient document, in either build.** **No cause is asserted** for
the offset difference; the bundles are different builds of different lengths.

**Fixed in six places, all found by the subject sweep and not by any item:**
§6.4 (table rebuilt per build, counting rule stated), §9 row 16, `docs/00`, `docs/04`,
`docs/10` and `docs/11` — the last five all said *"4 hits"* with **no build named**,
which is the same defect one level up from the offsets.

### R4 — one further defect the subject sweep found, in no item

`grep.sh:5` cited `docs/11-suggested-research-areas.md:209` for *"the letter question"*.
`:209` is the **`### F.` heading** — a title, not a question. The question is asked
verbatim at **`:221`** (*"So: how does the portal call them?"*) with its close
condition at **`:227`**. Now cited to `:221`, with `:209` named as the heading. **Same
class as R2** — a cite that resolves and points at the wrong line — found only because
this round enumerated `file:NNN` in the `.sh` files rather than in the log alone.

### R5 — nothing measurable moved

All four evidence artefacts remain **byte-identical to `cd9b79a`**
(`results.jsonl`, `run.log`, `headers/`, `grep-out.txt`). `wc -l results.jsonl` is
**17**, matching **"17 of a 40 cap"**. No vendor request was issued this round.
`regression/hurl/` untouched, so the counting rule is unchanged: **217 / 431**.


---

## Correction (2026-10-15)

Round 5 of verification. **One blocking clause, one bookkeeping gap.** Everything
else was CONFIRMS on independent re-derivation and is not re-litigated here.

### R1 — the plural survived the clause that replaced it

**The superseded wording, verbatim, at §6.3.** *"**Their byte offsets are tabulated per
build, because they do not agree across builds**: `m2m` is at **387460 in the clinic
build and 387460 in the support build** — the same — while …"*

Round 4 deleted *"The two tokens are not build-invariant"* and put a replacement in
its place. **The replacement carried the same defect**: the plural **"they"** covers
both tokens and is false for `m2m`, which round 4's own subject sweep had just
measured as identical in the two builds. **It contradicted `:483`** (row 14,
*"identical"*), **`:636`** (*"build-invariant for `m2m` only"*), **`:744`** and C5's
own table at **`:740`** — **four records in the same file, one clause away.**

> **It is the identical failure to round 3's, in the sentence written to replace round
> 3's instance of it** — `§6` mode 5, derived prose contradicting its own source
> table. **A replacement clause is a new claim and needs the same check as any other,
> not a lighter one for being written by the correcting pass.**

**Now true of both tokens, and it names which is which:** *"**Each token's byte offsets
are tabulated per build, and the two tokens come out differently: `m2m` sits at the
same byte in both builds, and `baseUrl` does not.**"*

**Swept the class before pushing, as instructed, and it is now empty:** every line in
the diff making a claim that sweeps **both** tokens' offsets —
`their byte offsets` / `the two tokens` / `both tokens` on any line also carrying one
of the four offset literals — returns **0 both-token offset claims**. Read as
*"0 claims found under the rule"*, not *"no violations"*: the rule is stated in R2
below, and a sweep that finds nothing must be read as a question asked, not as proof
of cleanliness.

### R2 — the sweep table's counts had no counting rule, and were not reproducible

**The superseded wording.** The round-4 subject-sweep table published counts of
**8 / 9 / 4 / 5 / 13 / 6 / 17 / 10 / 8 / 6** with **no rule recorded anywhere**, and
those figures come from a file set **narrower than any rule that could be stated** —
so **no one, including me, could reproduce them**. A count whose rule is not written
down cannot be checked by anyone else, which is this project's own `§6` mode 7 and
`docs/09` §4's *"a number that cannot fail is not evidence"*.

**The rule is now written down**, in the table itself, so the numbers beside it are
checkable rather than merely readable:

> **A MENTION is one LINE** of a file that **(a)** is listed by
> `git diff --name-only origin/main`, **(b)** ends `.md` / `.sh` / `.hurl` / `.txt`,
> **(c)** is **not** under `findings-log/probe-2026-10-08/`,
> `findings-log/2026-10-12-published-pointers/` or any `findings-log/2026-10-13*/`
> directory — **other passes' artefacts**, verified pre-existing — and **(d)** contains
> at least one of the subject's identifying literals, matched **case-sensitively** with
> `grep -E`. **One line is at most ONE mention** however many times the literal appears
> on it. **A line matching two subjects counts once for EACH.** Files are read from the
> **working tree** (= PR head content), never from `origin/main`.

**Under that rule the counts change**, and the verifier's independent figures
**reproduce exactly on three of four subjects**: `m2m` **10**, `baseUrl` **10**,
`personal.` **7** — matching the verifier's 10 / 10 / 7. The fourth is `cum2me`,
where **the count is a property of the query, not of the subject**: **6** counting the
**byte values** `387458`/`387463`, and **13** counting the **string** `cum2me`. That
is now **two subjects with two stated figures**, where before it was one subject with
one unreproducible figure — and the verifier's **15** is consistent with the string
query on a marginally wider file set. **The rule exists to make exactly this visible,
not to hide it.**

### R3 — R1's own prose described a replacement it did not deliver

Found by the same subject sweep. R1's text read *"The replacement says what is true
and only that: the two tokens' byte offsets do not agree across builds, and which one
agrees is named"* — **the first clause repeats the defect and the second describes
something the replacement did not do.** Corrected in place, with the supersession
stated rather than the sentence quietly rewritten.

### R4 — the PR BODY was never re-audited, and carried two of these

**This is the one that mattered most and no item named it**, because it is not in the
diff: **the PR description is not a tracked file, so no diff-scoped sweep can ever see
it.** It was written at `cd9b79a` and audited at **no** round in between. It still
named **`moom4261`** (wrong since round 2), still gave `baseUrl`'s **clinic-only**
offsets unlabelled (wrong since round 4), and still said the `m2m` hit was *"the
tail"* of a dictionary word. **All three corrected, plus a dated audit note appended
to the body** — and `README.md`'s *"216 → 217"* left as written, because that is a
**delta** statement and it is true.

**The lesson generalises past this PR: anything a reviewer reads but git does not
track — a PR description, a commit message, an issue body — is outside every sweep
this log has run, and has to be audited by hand.** The commit message of round 4
likewise repeats R1's false clause; **it is immutable history** and is not rewritten,
but this commit's message states the correction and the superseded line is identifiable
at `2573474`.

### R5 — the battery this round's audit did not reach, run here instead

The verification step budget ran out, so the following were **not** checked by it and
**were checked here** rather than assumed:

| check | result |
|---|---|
| `measure_assertions.py` | **217 431**, exit 0 |
| `research-checks.py` | **CHECKS PASS**, exit 0 |
| leak scan, all 10 patterns, whole diff | **0 hits** |
| `196` / `74` census re-derived **from `grep-out.txt`**, not from prose | clinic **196 / 74** and support **196 / 74**; per-case `66 + 126 + 4 = 196` in **both** |
| `README.md` 217 readable by **the gate's own regex** | regex matches at **`README.md:404`** and **`:470`**, both **217**; **0** wrapped-across-newline sites |
| §2.1 strength words | 13 hits, **all inside corrections quoting the deleted word**, none live |
| `docs/09:205`'s quoted-history `147` | **untouched** — 0 lines added, row intact |
| `regression/` pin agreement | `git diff cd9b79a -- regression/` is **empty**: the suite has not been touched since the EU pin landed at `cd9b79a`, so **no pin can have moved** |
| PR body | audited and corrected — R4 |

### R6 — nothing measurable moved, and one harness fact worth keeping

All four evidence artefacts remain **byte-identical to `cd9b79a`**. `wc -l
results.jsonl` is **17**, matching **"17 of a 40 cap"**. No vendor request was issued
this round.

⚠ **A harness fact the verifier established, kept here because it will bite the next
reader of `grep-out.txt`:** `grep.sh`'s context-dump block ends in a `||` fallback,
and when `head` closes the pipe early **grep takes SIGPIPE and the fallback emits a
SECOND, bare-offset line set** — so that block is **not** cleanly parseable as *"≤ 12
lines per token"*. **This pass's sweep never counted mentions from that block**: every
count above comes from a `grep -E` over the **working tree**, and every offset from the
committed context dump's `offset + 45` rule with the 45-byte left context asserted
first. **Had the sweep counted that block, its `≤12` figure would have been wrong in
the same direction as a `head`-truncation artefact — which is what the census in §6.5
already documents.**


---

## Correction (2026-10-15)

Round 6. Two findings, both about the counting rule, and the second one is the more
valuable thing in this round because it is **not about this pass at all**.

### R1 — the count was a fixed point the correction moved, and it is now stable

**The superseded wording.** The rule read *"Files are read from the **working tree**
(= PR head content), never from `origin/main`"* and published `m2m` **10**,
`baseUrl` **10**, `cum2me`-bytes **6**, `cum2me`-string **13**. **Every one of those
figures was correct at `2573474` and wrong at `08472e5`** — the commit that published
them. This pass's own R2/R3 prose **quotes** `387460`, `387458`, `387463` and
`cum2me`, because `AGENTS.md` §3 requires superseded wording to stay visible, and
**appending the correction added exactly +2, +1 and +5 to those subjects.** So the
count was a fixed point the act of recording it moved: **narrowed from round 5's
"a count nobody can reproduce" to "a count nobody can reproduce twice".**

**I took the second route the verifier recommended, and the reason is that the first
does not survive contact with the next round.** Restating the figures at HEAD would
publish a correct number that the *next* correction devalues identically. **So the
rule itself is amended**, with the exclusion and the reason both on the record:

> **(E1) Correction sections are excluded from the subject set — and kept in the
> record.** **The reason is generalisable: a correction section *quotes* the subjects
> it corrects, because `AGENTS.md` §3 requires the superseded wording to stay visible.
> Including quoted history in the count makes the count a fixed point that recording the
> correction moves.** **The exclusion is from the COUNT, never from the RECORD** —
> quoted wording is what makes a correction auditable, and hiding it to stabilise a
> number would be `§1`'s deletion with the sign reversed.

**Every figure is re-derived under the amended rule and republished above.** They fall
— `m2m` 10 → **3**, `baseUrl` 10 → **5**, `personal.` 7 → **4**, `cum2me`-bytes 6 → **2**,
`cum2me`-string 13 → **7** — because most of what the old counts were measuring **was
quoted history**.

⚠ **The amendment is PROVEN, not asserted.** A **decoy correction section** dense with
every one of the subject literals was appended and the counts re-run:

```
BEFORE the decoy:  m2m 3   baseUrl 5   personal. 4   cum2me_bytes 2   cum2me_string 7
AFTER  the decoy:  m2m 3   baseUrl 5   personal. 4   cum2me_bytes 2   cum2me_string 7
STABLE UNDER ITS OWN CORRECTION: True
```

The decoy was then removed and the file restored. **A count that cannot be moved by
recording a correction about it is the property round 6 asked for**, and this is the
evidence.

**All 18 surviving mentions were then read, not counted** — the discipline this repo
keeps teaching — and **every one agrees**: `m2m` 387460 in both builds everywhere;
`baseUrl` per-build labelled everywhere; `personal.` in the §6.4 table and row 16;
`cum2me` 387458–387463 and "middle" everywhere; and the two raw `grep-out.txt` rows are
the committed context dump itself, which is evidence and is kept.

### R2 — the base is now pinned, and it is preventative here rather than corrective — stated as such

The rule's file set is `git diff --name-only <base> HEAD`. **`origin/main` moved from
this branch's merge base `7d915b8` to `270d06f` while the branch was open**, so an
`origin/main`-keyed file set is a function of a moving ref: it is **12 files** under
`7d915b8` and **14** under `270d06f`, the two extra being area S's `docs/03` and
`docs/05`. The rule now names **`7d915b8` explicitly**.

**Honest scope of that fix, because the verifier did not ask me to overstate it:** for
these five subjects the counts are **identical under both bases** — area S's files
happen to contain none of the literals. **So pinning the base is preventative, not
corrective here.** The general form is what matters: **a count whose file set is a
function of a moving ref cannot be reproduced at a later date**, and it is `docs/09`
§4's *"a number that cannot fail is not evidence"* in its purest form — a count that
would change if anyone else happened to merge something.

### R3 — the malformed glob, in the rule and in the message

The rule wrote `findings-log/2026-13*/`, which **matches no directory**; the correct
form is **`findings-log/2026-10-13*/`**. It was **inert** — the three directories are
excluded by name above it either way — but a rule containing a glob that matches
nothing is a rule a reader will copy. Corrected in the rule; **this commit's message
carries the correct form**, and the two now agree.

### R4 — two numerals, and the other subject each of them also is

Recording the limits of the method that produced the table, since a table without them
reads cleaner than it is. Under the amended rule `196` has **16** mentions and `74` has
**9**, and **not every one is this pass's subject**: `docs/09`'s gzip row carries
*"196 B 404s"* and `docs/04` carries *"34 for 74 countries"* — **body sizes and a
country count that share a numeral with a census and a signature count.** Both
**verified pre-existing** on `7d915b8`; neither edited. **A subject sweep says "here is
everywhere this subject appears"; it does not say "every one of these is the same
claim", and a numeral is not a unique identifier.**

### R5 — ⚠ THE MERGE HAZARD NOBODY ASKED FOR, MEASURED ON ALL THREE REFS

**`origin/main` moved to `270d06f` (area S merged) and that merge touched three files
this pass also changed** — `docs/09`, `docs/10`, `docs/11`. **No textual conflict to
resolve here, and none is resolved here.** But the arithmetic is the finding:

| ref | open headings | Closed rows | prose | `config.yml` |
|---|---|---:|---|---:|
| `7d915b8` base | F R S K L (5) | 21 | 5 + 21 | 5 |
| `270d06f` main, **area S merged** | **F** R K L (4) | 22 | **4 + 22** | **4** |
| `08472e5` this branch, **area F closed** | R **S** K L (4) | 22 | **4 + 22** | **4** |

**Two independent closures from one base each computed the same count — "4 open plus 22
closed" — by closing a DIFFERENT letter.** Each branch is internally consistent and
correct for its own closure. **The merge of the two yields 3 open and 23 closed**,
because F *and* S are closed — while the merged text will still carry **4 + 22** in
`docs/11`'s prose and **4** in `config.yml`, since only one of two identical edits to
each of those lines can survive.

> **⚠ FOR THE MERGE QUEUE, and deliberately not fixed here.** Reconciling a merge of
> two closures means recomputing **all three sites together** — `docs/11`'s heading
> count, its Closed-table row count, its "N open plus M closed" prose and
> `config.yml` — to **3 open plus 23 closed**. **Taking whichever of the two identical
> prose lines git selects is wrong by one in the same direction on both surfaces**, and
> `research-checks.py`'s `check_prose_counts` will fail the result, which is that check
> working. **The generalisable form: two closures from one base collide on the count,
> not on the text**, so a count is not a merge-safe value the way the row it annotates
> is.

### R6 — nothing measurable moved

All four evidence artefacts remain **byte-identical to `7d915b8`**'s ancestor
`cd9b79a`. `wc -l results.jsonl` is **17**, matching **"17 of a 40 cap"**. No vendor
request this round. `regression/hurl/` untouched since `cd9b79a`, so no pin can have
moved — `git diff cd9b79a -- regression/` is empty.

**Measurement bases used in this round, stated so an auditor can repeat them:** the
subject sweep and the R5 table read `git diff --name-only 7d915b8 HEAD`; the artefact
identity check compares `cd9b79a`; `research-checks.py` and `measure_assertions.py`
read the **working tree**. **`origin/main` was used for nothing.**


---

## Correction (2026-10-15)

Round 7. Verification returned **CLEAN with no blocking findings** and four items
"owed before merge". All four are closed here. **Nothing CLEAN is re-litigated.**

**Base for every diff and sweep in this round: `7d915b8`** — this branch's merge
point. `origin/main` (`270d06f`, area S merged) was used for **nothing**, and the R5
re-derivation reads each ref **from git** rather than from the worktree.

### R1a — the query cell is now runnable, and why that was the route

The `docs/11` cell published `docs/11…:(209|214|221|222)`. **The cell is now
`docs/11(.{0,200}):(209|214|221|222)`** and runs as written:

```
returns 3  ->  FINDINGS.md:284   grep.sh:6   grep.sh:45
```

**Runnable form chosen over marking it schematic, because the schematic form has
three defensible readings and they disagree:**

| reading of `…` | result |
|---|---:|
| `.{0,4}` — the gap bounded to 4 chars | **1** — misses gaps of 28 and 45 |
| `.{0,200}` — bounded above only | **3** ✅ |
| unbounded above (the "real" reading) | **3** ✅ |
| swept against **`git diff` text** instead of the working tree | **8** — diff headers and hunks |

**The bound is not load-bearing and that is stated:** the widest real gap is **45**
chars, so `.{0,45}`, `.{0,200}` and unbounded all return **3**. The cell publishes
**200** because it is a number a reader can trust to be non-clipping, and the claim
does not depend on where the bound sits.

**On the competing 4th hit** (`docs/09:203`): **no mention of it existed when this
sentence was written** — see **R2a**, because this sentence, by naming the string,
**put it in the log**. ⚠ **This claim was written too broadly and is narrowed here.**
*"The log's only `docs/09` line-cite"* was **false**: `docs/09:205` also appears **×4**.
The supportable claim is the exhaustive one, and it is stronger:

> **ZERO `docs/09:NNN` cites in this log are E1-live.** Checked by enumerating
> every occurrence of the pattern `docs/09:<digits>` **in this file only** and resolving
> each occurrence's enclosing `## ` heading.
>
> **No multiplicity figure is published, deliberately.** A previous version of this
> claim carried one, and it was wrong twice over — it mixed **this log's** occurrences
> with **tree-wide** counts of other passes' artefacts (`docs/09:64` ×4 and
> `docs/09:65` ×1 occur in **other passes' files**, which rule **E2** excludes, and in
> this log they appear **only inside the enumeration that asserted them**). And a
> multiplicity here would be **self-referential**: every round's correction restates
> the enumeration, so each restatement adds occurrences of the very tokens being counted.
> **The negative claim is the whole claim**, it is mechanically checkable in one command,
> and **a count would add nothing but a number that moves when I write the next
> correction.**

The nearest neighbour of the kind this round was chasing is **`docs/09:195`** (the gzip
row carrying *"196 B 404s"*), at `FINDINGS.md:1072` — **also** E1-excluded. A sweep that
returns it had E1 off. **Same shape as the round-4 record: a numeral or a filename
that looks like the subject without being it**, which is why R4's own limit note
("a subject sweep says *here is everywhere this subject appears*, not *every one of
these is the same claim*") is the thing that resolves it.

### R3 — the four evidence artefacts, digested against `cd9b79a`

The claim has been "byte-identical" since round 2 and was asserted, never shown.
**Run and pasted**, read from git at both refs:

```
results.jsonl  dba9f9f243f55dfdea4aea85d1b1fb92c73b2b949f08e9aac0da47e6823ff9fa  (both)
run.log        24b2df751d47ef6884b95774bd695a463dbadad1b41655725e28d28b7dd371d2  (both)
grep-out.txt   ae872d12972464db2bcfea2aa790f8fa5644ec514ab9d3811c352fc20473d482  (both)
headers/       tree a1375242809f19f3b5053fe718f040b54a9e3a6d          (both)
               concatenated bytes 61c4c64cc818e731a89a692ef8bd0ea145ae7fb1e174d2907f9289a12eda0f04 (both)
```

`headers/` is 17 files, so it is digested **twice** — as a git **tree hash** and as
the **concatenated bytes** in `git ls-tree | sort` order, because a tree hash alone
proves path-and-blob identity while the concatenation proves the bytes a reader would
reassemble. **Both identical at `cd9b79a` and at this head. The claim stands, and is
now checkable rather than asserted.**

### R5b — the merge-hazard table, re-derived, with the method shown

This was the one arithmetic claim the verifier could not test. **Method, in full, and
every figure read AT THE REF from git rather than from the worktree:**

- `open` = count of `/^### [A-Z]\.\s/` headings — **research-checks.py's own pattern**
- `closed` = count of `/^| [A-Z] — /` rows in the section after `## Closed areas`
- `prose` = the **live (non-blockquoted)** `N open plus M closed` sentence —
  quoted history excluded, as `check_prose_counts` does
- `config` = the `about: N open areas` claim

| ref | open headings | letters | closed rows | live prose | `config.yml` | internally consistent |
|---|---:|---|---:|---|---|---|
| `7d915b8` base | 5 | **F R S K L** | 21 | `5 + 21` (line 1554) | 5 | ✅ |
| `270d06f` main, **area S closed** | 4 | **F R K L** | 22 | `4 + 22` (line 1517) | 4 | ✅ |
| this head, **area F closed** | 4 | **R S K L** | 22 | `4 + 22` (line 1702) | 4 | ✅ |

**All three are internally consistent** — `open == prose == config.yml`, `closed ==
prose`, and `open + closed == 26` at every ref. That is the point: **neither branch is
wrong.**

**The merged state is `3 open` (R K L) and `23 closed`** (`21 + 2`), so the merged
`docs/11` prose and `config.yml` must both read **3 open plus 23 closed**.

> **⚠ UNCHANGED AND STILL THE QUEUE'S TO HANDLE — deliberately not resolved here.**
> Two closures from one base collide on the **count**, not on the text: both branches
> wrote the identical `4 + 22` into the same prose sentence and the same
> `config.yml` value, so a text-level merge keeps whichever git selects and leaves both
> surfaces **one too high**. Reconciling means recomputing **all three sites
> together**. `research-checks.py`'s `check_prose_counts` will fail the merged result,
> which is that check working, not a defect to work around.

### R4b — the 2.866 s oracle is host-local, and the PR body said otherwise

**Confirmed, and the PR body was corrected.** The kernel body-mtime figure was computed
from response bodies that **are not in the repository**: there are **0 `.js` files** in
the tree, and `results.jsonl` keeps an **80-byte** `body_head` per bundle row beside a
16-character digest prefix — never a body. Git does not preserve mtimes either.

So **`FINDINGS.md` was already right** (it says "not re-derivable from a clean clone"
at both §2 and §9), and **the PR description was the surface that implied a checkable
second opinion.** It now says plainly that **2.866 s is a host-local measurement, not a
second opinion a reader can re-derive**, that the 17-row ledger keeps no body, and that
**the load-bearing figure is the `t_sent` series, which reproduces from the committed
ledger alone.** `2.866 s` was also struck from that body's list of "re-checked and still
true" items.

**The generalisable form, recorded because it is the third untracked surface in this
PR to carry a stale claim** (after the PR body's `moom4261` in round 5 and the commit
message in round 6): **an oracle derived from data that is not committed is not
corroboration, it is an unrecorded observation.** It can still be true and still be
useless to a verifier, and the wording has to say which it is.

### R7b — nothing moved, and counts cannot move

`wc -l results.jsonl` = **17**, matching **"17 of a 40 cap"**. No vendor request this
round. All eleven subject counts **re-run after R1a's edit** and are **unchanged** —
the edited cell is inside a `## Correction (…)` section, so **E1 excludes it**, which is
the second proof that the exclusion is doing its job rather than decorating the rule.


---

## Correction (2026-10-15)

Round 8. **One blocking wording defect and one non-blocking overclaim.** Items 2, 3
and 4 of the previous round are **CLEAN** and are not re-litigated — the merge table at
all three refs, all five digests, and the mtime-oracle disclaimer were each reproduced
unaided.

**Base for every diff and sweep this round: `7d915b8`.** `origin/main` used for
nothing.

### R1b — the cell could not run, and the fix is to take the regex OUT of the cell

**The defect, reproduced on raw source.** The cell published
`` `docs/11(.{0,200}):(209\|214\|221\|222)` `` with the pipes **backslash-escaped**,
which is mandatory inside a markdown table cell — and in ERE `\|` is a **literal**
pipe, so the cell's own string demanded the literal text `(209|214|221|222)`:

```
grep -cE 'docs/11(.{0,200}):(209\|214\|221\|222)' FINDINGS.md  ->  0, exit 1
grep -cE 'docs/11(.{0,200}):(209|214|221|222)'   FINDINGS.md  ->  6, exit 0
```

**A probe that silently returns nothing and reads as agreement** — `AGENTS.md` §6
mode 3's exact shape, and **the runnable spelling existed only in the prose at R1a,
never in the cell the finding was about.**

**I took the first of the two offered routes — reword the cell to defer to R1a —
rather than merely dropping the words "runnable, not schematic".** Dropping the label
would leave a cell that still *looks* like a query and is not one, which is the same
trap in softer form: a reader would still paste it. **The cell now carries no regex at
all:**

> | `docs/11` letter cites | *no regex in this cell* — **the runnable ERE is in R1a
> below**; a markdown cell cannot hold it unescaped and `\|` is a **literal** pipe to
> `grep -E` | 3 | **agree** on `:221`/`:222` |

**Checked across the whole table, not just this cell:** every remaining regex cell
(`\b196\b`, `\b74\b`, `240-24[23]`, `387460`, `f249b63cb2fc`, `660f19c0`, `cum2me`,
`387458`, `387463`) carries **no pipe** and therefore **runs as written in raw source**
— verified by executing each cell's own string with `grep -cE` and requiring **exit 0**:
**0 cells fail**. The one escaped pipe left anywhere in a table cell is the `` `\|` ``
inside the sentence *explaining* this defect, which is prose about the trap rather than
a query.

**The published figure is unchanged at `3`, and must not move.** Re-run under the
amended rule: `FINDINGS.md:284`, `grep.sh:6`, `grep.sh:45`.

### R2a — the overclaim, and what checking it properly turned up instead

**The withdrawn wording.** *"The log's only `docs/09` line-cite in that area is
`docs/09:195`"* was **false under the broad reading**: `docs/09:205` also appears
**×4**, at lines 648, 806, 849 and 1271.

**Replaced with the exhaustive claim, which is stronger and is checkable:** **every
`docs/09:NNN` cite in this log sits inside a `## Correction (…)` section** —
`docs/09:195` ×2, `docs/09:203` ×1, `docs/09:205` ×4, `docs/09:64` ×4, `docs/09:65` ×1 —
**so rule E1 excludes all of them and there are ZERO E1-live `docs/09:NNN` cites.**
Verified **per cite, by resolving each one's enclosing `## ` heading**, not by reading
back the sentence that made the claim.

⚠ **And the check surfaced something about the previous round that belongs here rather
than being quietly dropped.** R1a asserted *"there is no such mention"* about
`docs/09:203`. **That was true when written and false the moment it was written** —
**naming a string puts it in the file.** `git log -S'docs/09:203'` dates the
introduction to `ba36c0e`, this pass's own round-7 commit, and a tree-wide
`git grep` now returns the hit **forever**. So:

> **A sentence that DENIES a string supplies that string**, which makes every later
> tree-wide check for its absence **unable to fail** — the mirror image of `docs/09`
> §4's *"a number that cannot fail is not evidence, however small it comes
out."* A grep for `docs/09:203` can no
> longer return zero, so it is no longer a test of anything; **the surviving test is
> E1-exclusion**, which is per-cite and mechanical.

**This is the fourth surface in this pass to have taught me something about how claims
fail** — after the bare count (`§6` mode 7), the fixed point (round 6), and the
markdown-escaped pipe (here). **The common shape: a claim about the record that is
checked by reading the record's own prose.** Every one of them was caught by a verifier
and not by me.


---

## Correction (2026-10-15)

Round 9. **Both items from the last round hold on their load-bearing conclusions** —
the runnable-cell fix CONFIRMS, the E1-exclusion negative CONFIRMS, and the
`git log -S` attribution CONFIRMS. **Two new defects surfaced while checking them, both
in correction prose, and both are the same shape: a claim about the record that was
never compared with the record.**

**Base for every diff and sweep this round: `7d915b8`.** `origin/main` used for
nothing.

### R1c — mixed-scope multiplicity, and the method that missed it

**The withdrawn claim.** It read *"**every** `docs/09:NNN` cite in this log sits inside
a `## Correction (…)` section"* and then enumerated five tokens — `docs/09:195` ×2,
`docs/09:203` ×1, `docs/09:205` ×4, **`docs/09:64` ×4**, **`docs/09:65` ×1**.

**Two of those five belong to a different scope than the sentence states.**
`docs/09:64` and `docs/09:65` occur in this log **only inside the enumeration that
asserted them**; their real occurrences are **tree-wide, in other passes' artefacts**,
which rule **E2** excludes by name. Measured here at this commit: `docs/09:64` appears
**2** times in this log and **both** are the claim's own enumeration line.

> **⚠ THE METHOD MISS, WHICH IS THE PART WORTH KEEPING.** "Verified per cite by
> resolving each one's enclosing `## ` heading" **tests E1-exclusion, not multiplicity.**
> Those are two different claims and they need two different checks: E1-exclusion asks
> *where does each one live*, and multiplicity asks *how many are there*. **The first
> check passed and was reported as though it were the second** — and it cannot fail on
> a token that is not a cite at all. **A claim about how many something exists needs its
> own enumeration over its own stated scope.**

**The fix is to publish no multiplicity at all**, and that is a deliberate narrowing
rather than a re-count: the load-bearing claim is the **negative** — **zero E1-live
`docs/09:NNN` cites** — which is mechanically checkable in one command. **A count would
add nothing**, and would be **self-referential**: every round's correction restates the
enumeration, so each restatement adds occurrences of the very tokens being counted.
**That is the same shape as `docs/09:203` below, caught a second time.**

### R3b — TWO fabricated quotations, not one

The verifier found `:1631` quoting `docs/09` §4 as *"a **check** that cannot fail is not
evidence."* `docs/09:203` reads **"a number that cannot fail is not evidence, however
small it comes out"** — and `grep -c 'cannot fail' docs/09` = **1**, so the word
changed from *number* to *check* and the trailing clause was dropped. **Corrected
verbatim.**

**The sweep the verifier asked for then found a second one I had not been told about,
in the same class.** `:681` quoted `AGENTS.md` §3 as *"Corrections are appended … the
superseded wording stays visible"* — and **`grep -c superseded AGENTS.md` = 0**. The
phrase is **not in `AGENTS.md` at all**; it is from a *brief*, not from the rulebook.
That is **worse than the `docs/09` case**, because the attribution named the
repository's own governing document. **Corrected verbatim** to what §3 actually says:
*"Do not edit an existing dated doc — add a new one, or a `## Correction (YYYY-MM-DD)`
section inside it. Append-only is deliberate: the retraction history is evidence."*

> **The sweep, and what it found.** Every `*"…"*` span in this log whose surrounding
> context **names a committed file** was extracted (36 spans) and probed against that
> file, normalising markdown markers and collapsing whitespace. **17 initially failed**,
> and **reading them — not counting them — left ZERO**:
>
> - **2 were real fabrications**: the two above, both fixed.
> - **1 was a detector gap**: `:202` *"Neither is browser-callable"* **is** in
>   `docs/00-summary-the-map.md`, but split across a **line break**, which is the same
>   trap as this repo's count site — a raw grep cannot see it, a whitespace-collapsing
>   matcher can.
> - **1 resolved to the very log this area was retracted for**: `:524`'s span sentence
>   is verbatim in `findings-log/2026-10-13-area-f-timeline-config/FINDINGS.md`, which
>   is why `docs/09` §4 retired the check.
> - **the rest** are quotations of **this log's own superseded wording**, of a
>   **verifier brief**, or regex artefacts where a span ran across a heading.
>
> ⚠ **The detector's own limits, so the "ZERO" is not read as more than it is:** it keys
> on `*"…"*` only, so a quotation written with different delimiters is **invisible to
> it**, and it attributes by **nearest named file**, which is a heuristic. **This is a
> sweep that reduces 20 candidates to 2 defects; it is not proof that no quotation in
> this log is wrong.** What would be needed for that is the same thing it needed at the
> start: **read every hit.**

### R5c — the verifier's five gaps, run here so the next verifier reads only my changes

| gap | result |
|---|---|
| **eleven subject counts**, end-to-end programmatic, at this commit | **3 / 5 / 4 / 2 / 7 / 13 / 6 / 16 / 9 / 4 / 3** — **all eleven match** the published figures, over a 12-file set at base `7d915b8` |
| **merge-hazard table at all three refs** | `7d915b8` 5 open `FRSKL` / 21 / `5+21` @L1554 / cfg 5 · `270d06f` 4 `FRKL` / 22 / `4+22` @L1517 / cfg 4 · head 4 `RSKL` / 22 / `4+22` @L1702 / cfg 4 — **all three internally consistent** (`open == prose == cfg`, `closed == prose`, `N+M == 26`). Merged truth: **3 open (R K L) / 23 closed** |
| **five artefact digests** at `cd9b79a` and head | `results.jsonl` `dba9f9f243f55dfd` · `run.log` `24b2df751d47ef68` · `grep-out.txt` `ae872d12972464db` · `headers/` tree `a1375242809f19f3` · `headers/` bytes `61c4c64cc818e731` — **all five identical, 17 blobs** |
| **PR body: mtime wording + whole-body stale sweep** | the disclaimer is present; **every** retracted value sweeps clean — `moom4261` ×1 **is the quoted retraction inside the round-5 audit note, not a live claim**; `independently`, `docs/11:214`, `docs/11:209`, `240-243`, `48.95`, `51.57`, `0.0151`, `tail of`, `two tokens are not build-invariant`, `216 assertions` all **0** |
| **trailing byte; setext risks** | trailing byte `0a`. Sweeping **every** `.md`/`.hurl` in the diff for `---` candidates found **29** and **1 real risk** — `docs/11:1794`, **pre-existing at `7d915b8`**, reproduced by my Closed-row insertion. **One blank line inserted; 0 real risks now** |

### R4b — the pre-existing setext risk, and why this file is where it lives

`docs/11`'s Closed table ended with `| P — … |` immediately followed by `---`, with no
blank line. At base `7d915b8` that is line 1645, and it is **not mine** — but **my row
was inserted directly above it and reproduced the shape**, so a reader of my diff sees
the ambiguity at my line. **One blank line, and the render is unambiguous.** Recorded
because the class is the same one that has bitten this pass three times: **a structural
detail that depends on a line break, checked by a human reading the text rather than by a
mechanical test.**

### R9b — nothing measurable moved

`wc -l results.jsonl` = **17**, matching **"17 of a 40 cap"**. No vendor request this
round. All eleven subject counts **unchanged** after these edits, because every edited
site is inside a `## Correction (…)` section and E1 excludes it.
