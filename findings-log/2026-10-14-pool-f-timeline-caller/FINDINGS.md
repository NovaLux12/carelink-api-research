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

`AWS-GATEWAYS.md` §7 records that BLOCK 7 *"never ran"*: an accidental re-run
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
`dialog-lite` list must not be extended — `AWS-GATEWAYS.md` §6 records that
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

**The digest is new.** `AWS-GATEWAYS.md` §3 recorded the routed-and-failed body
as 36 B but published no digest for it; `660f19c0…` is this pass's measurement,
so it is offered as a value to re-check against rather than as a reproduction.

**Limit, stated because the claim asked for it.** The control here was sent at
the **stage root level** (`/prodous/<uuid>`), not inside the `dialog-lite/v1`
prefix. That is the correct control for the oracle question — *is an absent path
distinguishable?*, answer no — but it is **not** the same cell as
`AWS-GATEWAYS.md` §10 row 2 (`/prodous/dialog-lite/v1/<uuid>`), so this pass does
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
reproduces `AWS-GATEWAYS.md` §3 exactly (0 of 90, 2026-10-10) on a different
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
body** (4 across both), and the byte offsets below are identical in both builds.

Hand-checked, not counted (`grep-out.txt` carries the context):

- **`m2m`, 1 hit, at byte 387460.** Area F's own text proposes looking for "a
  `m2m` / `gc` call pattern" ([`docs/11`](../../docs/11-suggested-research-areas.md)
  :214). The single `m2m` byte sequence in either build is the **tail of
  `moom4261`** (itself at byte 387449), inside a leaked-password dictionary — the
  same blob that holds the `discover` and `pde` hits area V documented. The
  premise carries its own false-positive trap and it fires on the first token
  tried.
- **`baseUrl`, 2 hits, at bytes 2422149 and 2422752, both builds.** Both sit in
  an **embedded Pusher JS SDK** (`baseUrl:"https://pusher.com"`,
  `authenticationEndpoint`, `docs/channel…`). Not a CareLink API base. Area V's
  counterpart finding for the patient build was different and is not repeated
  here: its two `baseUrl` hits are `getBaseCmsUrl()`, a CMS media base.

### 6.4 The negative that is larger than the one asked for

**OBSERVED.** `personal.` occurs **4 times** in each build, and **none of the
four is a key of the patient bulk document**:

| offset | literal | what it is |
|---:|---|---|
| 2403157 | `pow.personal.link.gdpr.warning` | an **HCP** config key |
| 2762844 | `hcp/configuration/public/pow.invite.to.personal.uri` | an **HCP** config route |
| 3238864, 3239490 | `patient.liked.to.personal.header` | a UI i18n string, twice |

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
| 14 | `m2m` = 1 hit, at byte 387460, inside `moom4261` (byte 387449), a leaked-password word | OBSERVED | `grep-out.txt` context dump |
| 15 | `baseUrl` = 2 hits at bytes 2422149 / 2422752, both inside an embedded Pusher SDK | OBSERVED | `grep-out.txt` context dump |
| 16 | `personal.` = 4 hits at bytes 2403157 / 2762844 / 3238864 / 3239490, **none** a key of the 69-name patient document | OBSERVED | `grep-out.txt`; offsets tabulated at §6.4 |
| 17 | `timeline` 66 + `Timeline` 126 + `TIMELINE` 4 = **196** occurrences, 74 signatures, none naming the service | OBSERVED | `grep-out.txt` census, counting rule at §6.5 |
| 18 | There is **no caller** for either service in either portal build, and **no proxy can exist** there because neither build reads the patient config document | OBSERVED for the two build facts; **INFERRED** for the "no proxy" consequence | §6.2, §6.4 |
| 19 | If a web caller exists at all it is in none of the three builds this repo has read | **INFERRED** (stated as a corpus claim, not a claim about every client) | §6.6 |
| 20 | Which of the three readings of the 403s holds | **NOT ESTABLISHED**, blocked on an authentication attempt | `docs/10` §1; §7 |
| 21 | EU bulk document carries 69 top-level keys | pinned by assertion, **not re-run live here** — `carelink.minimed.eu` is outside this claim's host set, so the suite was not executed; see §8 for what was verified without a request | `regression/hurl/05-public-config.check.sh` area-E block; §8 |
| 22 | The hardcoded `x-api-key` + dev-host pair is still present in both builds | OBSERVED (confirmation of an existing record; value not reproduced, no dev host contacted) | `grep-out.txt`; published at [`docs/08`](../../docs/08-security-findings.md) §S3 |

**Independent-source count, per `AGENTS.md` §2.1.** Rows 4, 6, 9, 10 and 11
restate measurements whose author is this pass (me) and whose prior published
figures are the 2026-10-10 pass (`AWS-GATEWAYS.md`). That is **two authors**
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
request order. **10 gaps, max 0.947 s, median 0.0151 s, and 2 of 10 disagree by
> 0.5 s** — which is the property a span check cannot have, since it fires.

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
are identical in the support build, which is why they are given once. No figure
changes; the unit does.

### C4 — what did NOT move, and one disclosure that is now discharged

- **The `README.md` count site the gate cannot read** (verifier round 1, blocking
  item 1) was a **`docs/`-level defect in this PR, not in the log**, so it is
  corrected in `README.md` itself and the pattern was **not** widened — a
  maintainer decision, per `docs/09` §4's standing note. `README.md:205`-style
  **quoted history inside a trap row was deliberately left at its historical
  value**, because changing it would falsify the record of the trap itself. A
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
