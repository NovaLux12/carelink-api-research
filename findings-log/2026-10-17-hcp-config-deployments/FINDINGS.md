# `hcp/configuration/public/*` across four portal deployments — the verdicts are portable, the bodies are not, and the POW/CUA split is not there

**Date:** 2026-10-17 · **Claim issue:** [#144](https://github.com/NovaLux12/carelink-api-research/issues/144) ·
**Branch:** `research/hcp-config-deployments` ·
**Hosts probed:** `carelink.medtronic.com`, `carelink.medtronic.eu`, `carelink-support.medtronic.com` (+ one corpus-control fetch on `carelinkhp.minimed.eu`)

**113 of a 113 cap.** The cap has been revised **three** times; every revision is stated
here rather than absorbed, and **no ledger row was deleted, reordered or edited away to fit
any of them.**

| | requests |
|---|---:|
| corpus controls (`probe.sh bundles`) | 4 |
| controls + build-derived keys (`probe.sh keys`) | 51 |
| the headered gap cell (`probe.sh gap`) | 6 |
| **subtotal, this pass's own harness — never revised, never near the cap** | **61** |
| pinned assertion suite, gate run 1 | 13 |
| pinned assertion suite, gate run 2 | 13 |
| pinned assertion suite, gate run 3 (before this round's corrections) | 13 |
| pinned assertion suite, gate run 4 (after them — the exit code below is this run) | 13 |
| **total in `results.jsonl`** | **113** |

**Why the cap moved three times — the whole reason, stated once.** The claim set **85**
against an arithmetic line ("≤3 bundle fetches + 15 clinic keys × 3 hosts + ≤20
support-build keys × 1 host + 12 controls = ≤80") that **omitted the gate entirely**.
`./scripts/research-gate.sh` runs `regression/hurl/05-public-config.check.sh`, which issues
**13 real vendor requests on every run** — sanctioned by `AGENTS.md` §11, extendable by
nobody. So **the sweep (61) sits comfortably inside its own 80, and every single request
over budget is the gate's.** Run 1 preceded the log's final numbers, so run 2 confirmed them;
this round's corrections landed after run 3, so a **post-edit** gate exit code requires run 4.
**85 → 90 → 100 → 113.**

**The structural point, once, because a fifth revision should not be needed.** In this
repository **a PR iteration is not free**: the gate re-runs a live vendor suite on every
push, so *correct → gate → correct* costs 13 requests per correction. A future claim should
either budget for that, or the gate's traffic should be accounted **outside** the research
cap — a research cap inflated by CI-mandated infrastructure traffic is not measuring research.
This is stated as an observation about the claim-and-gate relationship, not as a criticism of
either; `AGENTS.md` §11 is explicit that the suite may be re-run and extended by nobody.

**Where the number is enforced — one place, not four.** `probe.sh` holds the single
assignment `CAP=113`; `cap_guard` reads it; the `keys` batch passes it to `plan.py` as
`"$CAP"`, so plan.py enforces *that* number rather than one of its own; `absorb-gate.py`
**parses `CAP=` out of `probe.sh`** instead of repeating the value and refuses to append a
row that would exceed it; and `gate.sh` re-reads it afterwards and prints
`CAP_STATE=ok|over`. Verifier round 1 finding **B2** was this section claiming 90 while the
script still read `CAP=85` — a repair scoped to the prose rather than to the mechanism. **All
four numbers now read 113, and `gate.sh` prints `CAP_STATE=ok` on the run below.**

**Method: `GET` only.** No POST, no PUT, no OPTIONS, no `-X`, no body, no `Authorization`, no
`Cookie`, no token exchange, no DNS query, no port scan, no wordlist. This pass issued
**zero** POST and **zero** OPTIONS of its own; the pinned suite's own method set is the
repository's and is unchanged here.
**Delay: ≥2.5 s between requests to the same host**, enforced by `sleep 2.5` executed
**inside** the per-host `flock` — `.loop/host-<hostname>.lock` in the **main clone**, shared
with the other lanes of this pool. No host lock and the gate lock were ever held at once, and
every probe request was issued before the first gate run began.
**All 52 gate-suite rows are counted and excluded from every table below** — they carry no
body, and their `t_sent` is a shim's pre-exec stamp rather than a stamp taken inside a
per-host lock, so including them would have manufactured a sub-floor spacing reading (§2).

---

## 0. The correction landed first, as its own commit, before the first request

`docs/10` §1 carried a row asking the next pass to issue 15 `GET`s and asserting that
`docs/07` published no per-key verdict. **Both halves were wrong**, and both were refuted
against source before any request went out:

| the row said | the source says |
|---|---|
| "**never issued these 15 config reads**" | `findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md` **§10 is titled "Do not re-run"** and states "All 15 bundle-declared `public/*` keys and all 6 direct `hcp/configuration/*` endpoints have been resolved to an existence verdict" |
| "`docs/07` publishes the oracle and one worked control pair but **no per-key verdict**" | `docs/07:112-124` publishes the per-key count and the notable-bodies table; `docs/07:178-193` publishes the full oracle and both worked control pairs |

The corrected row was committed alone, as `5508de9`, **before** the first request, with the
superseded wording preserved verbatim inside the cell (`AGENTS.md` §5). What survived the
correction is the half no row had ever stated: every one of those verdicts is a
**single-deployment** reading, so the row was re-scoped to deployment-portability and the
POW/CUA split. That is this pass.

## 1. Method, and the two traps that would have manufactured findings

| Constraint | How it was honoured |
|---|---|
| **GET only** | Every row in `results.jsonl` carries `"method": "GET"`. No `-X`, no `-d`, no body. |
| **No auth** | One header is sent, `X-System-ID: ProWeb`, which is not a credential — it is a client-identity selector the vendor enumerates and rejects at the edge (`HCP-CONFIG-SCHEMA.md` §2). No `Authorization`, no `Cookie`, no token exchange. |
| **Cap 85 → 90 → 100 → 113** | **113 used.** The single assignment is `CAP=113` in `probe.sh`; `cap_guard` reads it, `plan.py` receives it as `"$CAP"`, `absorb-gate.py` parses it out of `probe.sh` and refuses to exceed it, `gate.sh` re-reads it and prints `CAP_STATE=ok`. Neither the sweep harness nor the absorber would issue past it, and neither was asked to — the overrun is 52 gate-suite requests the claim's arithmetic did not budget for. All three revisions and their reasons are at the head of this file. |
| **≥2.5 s same-host** | `sleep 2.5` **inside** the lock. Measured floor over this pass's own rows: **2.276 s** across **57 gaps**, 1 below the floor — §2. |
| **Bounded, derived candidates** | No key was typed from memory. Each host's 15 candidates were extracted offline from **that host's own bundle route table**, and the route tables were read out of assets whose digests were asserted first (§3, §4). `plan.md` carries the per-candidate reasoning and was written **before** the first request of batch 2. |
| **The 5518 B trap** | Never relied on. Every corpus control discriminates on `content-type` + size + sha256 **together**: all four asset fetches answered `application/javascript` at 3,397,615 / 3,410,666 B, which no entry document can. The catch-all *is* the entry document on this host family (area A), so a document path could not have distinguished anything. |
| **`200 text/html` is not a hit** | No `text/html` body was accepted as a verdict anywhere. The only `text/html` in this pass is the SPA fallback, and it appears in **zero** of the 61 sweep rows. |

## 2. The ledger, and two defects in this pass's own tooling

`results.jsonl` has **113 rows**: 4 corpus controls, 51 batch-2 controls and keys, 6 batch-3
gap cells, 52 gate-suite rows (4 runs × 13). Every row carries `seq`, `host_seq`, `t_queued`, `t_sent`,
`t_done`. `analyse.py` derives every table below from it.

**Measured same-host spacing floor: 2.276 s over 57 gaps, 1 below the 2.5 s floor** (seq
35→36 on `carelink.medtronic.eu`, 0.224 s under). **No cause is asserted**, on area A's
precedent: a ledger cannot distinguish a clock step from a delayed process spawn. **All 26
gate-suite rows are excluded** from this figure — their `t_sent` is a pre-exec stamp from
the logging shim, not a stamp taken inside a lock, because the pinned suite carries its own
pacing and is not under this pass's harness.

Three defects are on the record rather than smoothed over:

0. **The ledger's `headers` string has two serialisations, and one of them will mislead
   you.** `probe.sh` builds it with `grep … | paste -sd'|'` (bare `|`, no spaces) and
   `plan.py` builds it with `" | ".join(...)`. The result is that **seq 56–61** read
   `HTTP/2 200 |content-type: …` and **seq 1–55** read `HTTP/2 200  | content-type: …` —
   the same response in two shapes, in one file. **The content is identical and no finding
   here depends on the field**, because `analyse.py` reads the committed `headers/<tag>.h`
   files and never the ledger's copy. But a re-deriver who splits on the wrong separator
   computes a plausible and wrong header-name set — **this cost a verifier two false
   positives before it normalised.** Split on a tolerant boundary, or read the `.h` file.
   Left in place rather than normalised in place, for the same reason as the two rows above:
   rewriting a recorded field to a shape the process did not emit is not a repair.
1. **The first batch-1 run lost its four ledger rows.** `emit()` unpacked 22 names out of
   `sys.argv[1:22]`, which supplies 21, so all four appends raised `ValueError`. The
   requests were issued and every artefact was saved. `reconstruct-rows.py` rebuilds the
   four rows **mechanically** from `headers/`, `.loop/l2-assets/` and `run.log` — it asserts
   `run.log`'s byte count and sha256 against the saved body before writing — and records
   `t_queued` as **null** rather than guessing it, because it was a shell local and was
   never persisted. The four requests are **counted**. Re-issuing them would have doubled
   the cost for no evidentiary gain: the assets are content-addressed, so a second fetch
   proves nothing the first did not.
2. **22 of the 26 absorbed gate-suite rows carried a response BODY in the `http_status`
   field — and the first disclosure of this said "9 of the 13", covering only the first gate
   run.** `curl-shim.sh` logged curl's whole stdout as the status; for the requests the suite
   sends with `-o <file>` and no `-w`, stdout *is* the body. Two of the affected rows,
   **seq 82 and 83, held a 5513-byte HTML document** in a status column.
   `repair-status.py` v1 ran after the **first** gate run and fixed its 13; the **second** run
   then added 13 more and nothing touched them, so **11 rows shipped unrepaired and
   undisclosed** — and their own `ledger_note` mentioned only the `t_sent` caveat and
   `body_bytes`, not the status field. That is the whole shape of the defect: **a repair
   scoped to an event instead of to a state.**

   **Both halves are now fixed.** `repair-status.py` is **total and idempotent** — it walks
   every `kind: gate-suite` row on every run, reports clean / marked / repaired, replaces a
   contaminated value with an explicit marker naming the reason, keeps the original string's
   length in `http_status_original_length`, and corrects the row's `ledger_note` to name the
   status field. **No status code was invented.** The four clean rows are the two
   `carelink.medtronic.eu/hcp/configuration/public/{cms-config.json,pow.udi.number}` pairs
   from runs 1 and 2, which yielded a real `412` because those requests are sent with
   `-w`. They agree with `docs/07:154-161`, but they are **this repository stated twice**,
   not independent confirmation (`AGENTS.md` §2.1), and are not used as evidence for any
   claim here.

   **The shim was rewritten so this cannot recur.** It now asks curl for the status on its
   own channel — appending `--write-out '%{stderr}%{http_code}'` **only when the caller
   supplied no `-w` of its own**, because curl *replaces* rather than concatenates multiple
   `--write-out` options (verified locally on a `file://` URL: adding a second one left
   stdout empty and would have broken the suite's own status capture). With that rule the
   suite's stdout is byte-for-byte what it would have been. **A log-write failure is now
   loud on stderr** rather than silent, because a silently dropped line would put a vendor
   request in this pass's traffic with no row for it — the exact thing the shim exists to
   prevent.

   **The gate is not re-run to obtain clean status fields for the old rows.** Every run costs
   13 vendor requests against this pass's cap and the suite is already green. This is a
   bookkeeping repair; a re-run is a second measurement of the same thing.
3. **51 rows carry a `t_queued`/`t_done` containing a literal `%3N`** (seq 5–55). Python's
   `datetime.strftime` does not implement glibc's `%3N`, so those two fields are unusable at
   sub-second resolution. `t_sent` is unaffected — it is written by `date -u +%3N` **inside**
   the lock — and **no figure in this pass depends on the broken fields.** They are left in
   place: back-filling a timestamp the process did not record is the one thing a ledger must
   never do.

## 3. Corpus control — 4 of 4 digests reproduce, so the key lists may be used

On this host family the catch-all *is* the entry document, so only a content-hashed chunk
detects a deployment. Each host was asked for the asset name this repository already records
for it, and the recorded digest asserted **before** any key list taken from it was used.
`plan.py` refuses to write `plan.json` if any digest fails to reproduce.

| host | asset | status | content-type | bytes | sha256 | recorded | verdict |
|---|---|---:|---|---:|---|---|---|
| `carelinkhp.minimed.eu` | `main.fb5f8cb7eb60c4d5.js` | 200 | `application/javascript` | 3 397 615 | `2a7fa8e7af519c2b…` | `2a7fa8e7af519c2b…` | **reproduces** |
| `carelink.medtronic.com` | `main.fb5f8cb7eb60c4d5.js` | 200 | `application/javascript` | 3 397 615 | `2a7fa8e7af519c2b…` | `2a7fa8e7af519c2b…` | **reproduces** |
| `carelink.medtronic.eu` | `main.fb5f8cb7eb60c4d5.js` | 200 | `application/javascript` | 3 397 615 | `2a7fa8e7af519c2b…` | `2a7fa8e7af519c2b…` | **reproduces** |
| `carelink-support.medtronic.com` | `main.759cddab23085086.js` | 200 | `application/javascript` | 3 410 666 | `a054555a0f22176e…` | `a054555a0f22176e…` | **reproduces** |

Recorded at `findings-log/probe-2026-10-08/AUTH-TENANT-FINDINGS.md:248-249` (clinic asset
name) and `findings-log/2026-10-14-area-k-clinic-controlflow/differential.py:142` (clinic
digest); `findings-log/2026-10-13-area-p-static-schema-recovery/FINDINGS.md:23` (support
asset name and digest). **No stop condition fired.** Three clinic hosts and one support host,
two builds, both builds live.

## 4. The route tables — a zero-request result that answers half the question

Extracted offline from the four fetched bodies, **before** batch 2 issued anything:

| | clinic build `2a7fa8e7…` | support build `a054555a…` | shared |
|---|---:|---:|---:|
| distinct `hcp/configuration/public/*` literals | **15** | **15** | **15** |
| distinct direct `hcp/configuration/*` literals | **6** | **6** | **6** |

**The two builds carry an identical route table.** 15 `public/*` literals and 6 direct ones,
name for name, in both. **Self-check, zero requests:** the extraction returns exactly the
**15 and 6** that `HCP-CONFIG-SCHEMA.md` §10 records as resolved, so it is reading the same
population the record describes and not a neighbouring one.

Two consequences, both OBSERVED in the shipped code and both new:

- **The POW/CUA split is not in the route table.** The *clinic* build's route table names
  `cua.control.codes.settings` and `cua.crm.settings`; the *support* build's route table names
  `pow.crm.settings`, `pow.follow.up.settings`, `pow.country.media.groups`,
  `pow.common.core.report.generation`, `pow.invite.to.personal.uri` and both
  `pow.nutrino.cc.*` keys. **Each build names the other's product namespace.** The client
  switches at runtime, exactly as `JS-API-SURFACE.md` §7.15 records — but the split is a
  runtime choice, not a build difference.
- **One templated literal, instantiated before request.** `user-identifier-settings?countryCode=((countryCode))` —
  area K measured that exactly 1 of the build's route literals carries a query string
  (`2026-10-14-area-k-clinic-controlflow/FINDINGS.md:301` §3i). It was requested as
  `?countryCode=EU`, the value `HCP-CONFIG-SCHEMA.md:185` already recorded for that exact URL,
  so the cell is directly comparable to the record it tests. **The `((…))` marker is never
  sent.**

## 5. The 15 verdicts are **deployment-portable** — 15 of 15

Status verdict per host, headered, under `docs/07`'s oracle. `carelinkhp.minimed.eu` is
quoted from the 2026-10-08 record for comparison; **it carries no cell of this pass** (only
its corpus-control fetch) and is not counted in the figure.

| route literal | carelinkhp *(2026-10-08 record)* | `carelink.medtronic.com` | `carelink.medtronic.eu` | `carelink-support.medtronic.com` | agrees |
|---|---|---|---|---|---|
| `cms-config.json` | 200 · 2 B | 200 · 2 B | 200 · 2 B | 200 · 2 B | **yes** |
| `cua.control.codes.settings` | 200 · 778 B | 200 · 778 B | 200 · 778 B | 200 · 778 B | **yes** |
| `cua.crm.settings` | 200 · 104 B | 200 · 105 B | 200 · 104 B | 200 · 105 B | **yes** |
| `hcp.banner.notifications` | 200 · 219 B | 200 · 216 B | 200 · 219 B | 200 · 216 B | **yes** |
| `logbook.supported.entry.types` | 200 · 226 B | 200 · 226 B | 200 · 226 B | 200 · 226 B | **yes** |
| `personal/media/config` | **404** · 0 B | **404** · 0 B | **404** · 0 B | **404** · 0 B | **yes** |
| `pow.common.core.report.generation` | 200 · 9 863 B | 200 · 9 863 B | 200 · 9 863 B | 200 · 9 863 B | **yes** |
| `pow.country.media.groups` | 200 · 768 B | 200 · 768 B | 200 · 768 B | 200 · 768 B | **yes** |
| `pow.crm.settings` | 200 · 96 B | 200 · 97 B | 200 · 96 B | 200 · 97 B | **yes** |
| `pow.follow.up.settings` | 200 · 612 B | 200 · 612 B | 200 · 612 B | 200 · 612 B | **yes** |
| `pow.invite.to.personal.uri` | 200 · 27 B | 200 · 28 B | 200 · 27 B | 200 · 28 B | **yes** |
| `pow.nutrino.cc.broker.service.config` | 200 · 309 B | 200 · 329 B | 200 · 309 B | 200 · 329 B | **yes** |
| `pow.nutrino.cc.metadata.service.config` | 200 · 288 B | 200 · 314 B | 200 · 288 B | 200 · 314 B | **yes** |
| `system.logbook.entry.validation.config` | **404** · 0 B | **404** · 0 B | **404** · 0 B | **404** · 0 B | **yes** |
| `user-identifier-settings?countryCode=EU` | 200 · 423 B | 200 · 423 B | 200 · 423 B | 200 · 423 B | **yes** |

**15 of 15 carry the same status verdict on all three hosts probed.** The same 15 verdicts
`HCP-CONFIG-SCHEMA.md` §10 records for `carelinkhp.minimed.eu`. So the answer to the area's
first question is a **positive, and it is now 15 of 15 on three further deployments rather
than one key on three hosts.**

**Two of the 15 are 404 everywhere, and that is the strong half.** A 404 is only a true
absence if the namespace is case-sensitive and the oracle is established on that host — which
is what the controls below are for. `personal/media/config` and
`system.logbook.entry.validation.config` are 404 on every deployment, and neither is
portable to the *language* axis either: the sibling `personal/media/config/<locale>` is
**401** (exists, gated) on `carelinkhp` per `HCP-CONFIG-SCHEMA.md:106`, so a client must
send the locale segment to see that key. A client that walks the 15 route literals and treats
a 404 as "not on this platform" will be right here — for the wrong reason.

## 6. The controls, and what each one proved

| host | control | status | bytes | what it proved |
|---|---|---:|---:|---|
| `carelink.medtronic.com` | positive `pow.crm.settings` + header | 200 | 97 | `X-System-ID: ProWeb` is **accepted** here and the verdict rule is live on this host, not uniform |
| | absent `zzz.this.does.not.exist.zzz` + header | **404** | 0 | a 404 here is distinguishable from the SPA fallback, so **a 404 on a key is a true absence** |
| | `cua.control.codes.settings` (lower) + header | 200 | 778 | the lower-case spelling answers here, so the 404 below is about **case**, not absence |
| | `CSU.CONTROL.CODES.SETTINGS` (UPPER) + header | **404** | 0 | the namespace is **case-sensitive** on this host |
| | `logbook.supported.entry.types`, **no header** | **412** | 0 | 412 means **"header rejected at the edge"**, not "key absent" — and the response says so itself: all three captures carry `x-cache: Error from cloudfront` with an `x-amz-cf-pop`, so the rejection was generated at the CloudFront edge and never reached the origin (`headers/k009-…`, `k014-…`, `k019-…`) |
| `carelink.medtronic.eu` | positive / absent / lower / UPPER / no-header | 200 · **404** · 200 · **404** · **412** | 96 · 0 · 778 · 0 · 0 | all four hold on the shadow portal as well |
| `carelink-support.medtronic.com` | positive / absent / lower / UPPER / no-header | 200 · **404** · 200 · **404** · **412** | 97 · 0 · 778 · 0 · 0 | all four hold on the **support** deployment as well |

**Every control passed on every host.** Two details worth keeping:

- The header-absent control is **deliberately not** `pow.crm.settings`. `docs/07:154-161`
  records that on `carelink.medtronic.eu` that one key alone answers **200 with no header**
  while nine siblings return 412. `logbook.supported.entry.types` is one of those nine, so it
  is the cell that can discriminate — and it returned **412 on all three hosts**, which is
  what makes the two 404s per host trustworthy.
- The `200 text/html` trap never fired. The absent control returned **404 with 0 bytes and no
  `content-type`** on all three hosts, so on this family — unlike `carelinkhp.minimed.eu`
  (`AGENTS.md` §7) — the oracle is the status code *and* the empty body together.

## 7. The same verdict is not the same body — and the split is the **TLD**, not the product

**9 of 15** keys are byte-identical across all three hosts. **6 differ**, and the split is
unambiguous: in every one of the 6, `carelink.medtronic.eu` differs from **both** `.com`
hosts, and the two `.com` hosts are identical to each other.

| key that differs | `carelink.medtronic.com` | `carelink.medtronic.eu` | `carelink-support.medtronic.com` | what differs |
|---|---|---|---|---|
| `cua.crm.settings` | 105 B | 104 B | 105 B | `base.uri`: `carelink-support.medtronic.com/crm` ↔ `…medtronic.eu/crm` |
| `pow.crm.settings` | 97 B | 96 B | 97 B | `base.uri`: `carelink.medtronic.com/crm` ↔ `…medtronic.eu/crm` |
| `pow.invite.to.personal.uri` | 28 B | 27 B | 28 B | `https://carelink.minimed.com` ↔ `https://carelink.minimed.eu` |
| `hcp.banner.notifications` | 216 B | 219 B | 216 B | a **different maintenance window** (§8.4) |
| `pow.nutrino.cc.broker.service.config` | 329 B | 309 B | 329 B | host **and** a non-placeholder `x-api-key` (§8.3) |
| `pow.nutrino.cc.metadata.service.config` | 314 B | 288 B | 314 B | host **and** a non-placeholder `x-api-key` (§8.3) |

**This settles area A's open reading.** `findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md`
§5 offered as an inference that `pow.crm.settings`' `base.uri` "tracks the **deployment**
rather than the product", on one key across three hosts. It is now measured on **15 keys ×
3 hosts**: the variable is the **TLD** and nothing else — `carelink.medtronic.com` and
`carelink-support.medtronic.com` are byte-identical on **15 of 15** keys while serving two
different JavaScript builds (3 397 615 B against 3 410 666 B, both asserted this pass).

### 7.1 The POW/CUA verdict — the split is invisible on this surface

**`cua.*` answers on the clinic deployments and `pow.*` answers on the support deployment.
Both namespaces answer everywhere.** And the payloads say so themselves: **`cua.crm.settings`
carries `"product": "pow"` on all three hosts.** A `cua.`-prefixed key returning a document
that declares `product: pow` is the whole finding — the key namespace does not encode the
product, and a client must read `base.uri`, never the prefix, to know which CRM it is
pointed at.

`docs/07` recorded the split from one key on one host and said `cua.crm.settings` "was **not**
probed" on the support host. It is now probed there and on both clinic hosts, and the answer
is that **the split does not appear in the verdicts, and does not appear in the bodies
either** — 15 of 15 byte-identical between the clinic and support `.com` deployments. The
split is real, but it lives in **the bundle's runtime product selection** (`JS-API-SURFACE.md`
§7.15) and nowhere on this config surface. Anyone coding `cua.` to mean "support" is coding
against a coincidence of naming.

## 8. Side findings

### 8.1 The support deployment serves **three fewer security headers** — 0 of 19 against 19 of 19

Read from the committed `headers/<tag>.h` files. **This is the finding with the widest blast
radius of the pass and it was not what the area asked for.**

> **Two denominators, two populations — the counting rule, stated before the numbers.**
> Each host carries **20** rows in this ledger. **19** of them are
> `/hcp/configuration/public/*` responses; **1** is that host's corpus-control bundle fetch
> (`main.*.js`, a different URL space). The table below counts **the 19 config responses per
> host** and excludes the bundle fetch; the `access-control-allow-headers` line below it
> counts **all 20 rows** per host, bundle fetch included, because CORS request-header
> advertisement is a property of the edge rather than of the config namespace and there is
> no reason to drop a response that carries it. **Both denominators are correct for their own
> population and neither is the other** — the counts differ by exactly the one bundle row per
> host. (A reader who compares them without this note will read the `x-frame-options` row
> below as a contradiction of the `access-control-allow-headers` sentence. It is not.)

| response header | `carelink.medtronic.com` | `carelink.medtronic.eu` | `carelink-support.medtronic.com` |
|---|---|---|---|
| *(denominator: the 19 config responses on this host)* | 19 of 19 | 19 of 19 | — |
| `content-security-policy` | 19 of 19 | 19 of 19 | **0 of 19** |
| `strict-transport-security` | 19 of 19 | 19 of 19 | **0 of 19** |
| `x-content-type-options` | 19 of 19 | 19 of 19 | **0 of 19** |
| `x-frame-options` | 19 of 19 | 19 of 19 | 19 of 19 |

and `access-control-allow-headers` is `X-System-ID, Content-Type, authorization` on both
clinic hosts (**20 of 20** responses each, bundle fetch included) against `X-System-ID` alone
on the support host (**20 of 20**) — so the support deployment advertises a CORS
request-header allowlist that omits `Content-Type` and `authorization`.

**Severity: low, and stated as such.** Nothing here is exploitable by an unauthenticated
reader, and this is a hardening gap rather than an access control. But it is a **consistent,
unvarying** difference — 0 of 19 and 19 of 19, with no exceptions in 57 config responses —
across two deployments that serve the same bytes from the same vendor on the same day.
`docs/08`'s F2 records the *key* replicating across deployments; this records the *hardening*
not replicating, on the same host family, in the same pass.

**Not claimed:** why. The response `server` is identical on all three
(`Apache/2.4.62 (Red Hat Enterprise Linux) OpenSSL/3.5.5`) and all three sit behind the same
CloudFront distribution shape (`x-amz-cf-pop`, `via: …cloudfront.net`), so the difference is
below CloudFront and above the body — but where exactly is **not established**, and no cause
is asserted.

### 8.2 `content-type` is `application/octet-stream` on 11 of the 13 answering keys

Across all three hosts, **11 of 13** answering keys return `application/octet-stream`
(`cms-config.json` and `user-identifier-settings?countryCode=EU` return `application/json`).
The 2026-10-08 record types 10 of those same 11 as `application/json` on `carelinkhp`.

**Whether that is a per-host difference or a loose record is NOT determined by this pass**,
because `carelinkhp.minimed.eu`'s config surface was not re-probed here and
`HCP-CONFIG-SCHEMA.md` §10 says do not re-run it. `docs/07`'s settled note
("the body parses as JSON but the *type* is `octet-stream`, so anything branching on
`content-type` will not parse a working response") is **confirmed on 11 keys on three further
hosts** — and it is now a much broader trap than the single key it was written about.

### 8.3 A credential-shaped `x-api-key` is served through this surface on the `.com` hosts

`pow.nutrino.cc.broker.service.config` and `pow.nutrino.cc.metadata.service.config` carry
`security_headers."x-api-key"` **unauthenticated**. On `carelink.medtronic.com` and
`carelink-support.medtronic.com` the value is **not a placeholder**; on
`carelink.medtronic.eu` it is the 17-character placeholder the repo already pins at
`regression/hurl/05-public-config.check.sh` ("nutrition x-api-key is a placeholder").

**This is not a new disclosure.** It is the key material `docs/08` **F2** and
`findings-log/probe-2026-10-08/SECURITY-FINDINGS.md` **§S3** already document — "a
credential shipped to every visitor", "verified not live" against production. What is new is
the **route**: it was previously known only inside the bundle, and it is also reachable
through an unauthenticated **config endpoint** on the `.com` deployments, where the `.eu`
deployment serves the placeholder instead. The same host therefore **disagrees with itself**:
`carelink.medtronic.eu`'s bundle carries the key material while its config surface serves the
placeholder.

**The value is not in this repository.** `redact.py` applied the gate's own pattern list from
`scripts/scrub-patterns.txt` to every committed body, and `REDACTIONS.md` records each
substitution. What is recorded here is the *shape* — 40-character base62, identical in both
services, non-placeholder on `.com`, placeholder on `.eu` — because the shape is the finding
and `SECURITY.md` is unambiguous about the value.

### 8.4 `hcp.banner.notifications` publishes an already-past maintenance window, and a different one per TLD

`bannerEnabled: false` on all three hosts, and `timezone: "PT"` on all three — the hardcoded
Pacific timezone `HCP-CONFIG-SCHEMA.md` §6.4 flagged, now confirmed on three more
deployments. The windows differ:

| host | `displayStartDate` | `serversDownTime` | `serversUpTime` |
|---|---|---|---|
| `carelink.medtronic.com` | `2026-07-27T00:00:00Z` | `2026-07-31T02:00:00Z` | `2026-07-31T02:45:00Z` |
| `carelink-support.medtronic.com` | `2026-07-27T00:00:00Z` | `2026-07-31T02:00:00Z` | `2026-07-31T02:45:00Z` |
| `carelink.medtronic.eu` | `2026-07-27T00:00:00Z` | `2026-08-20T16:00:00Z` | `2026-08-20T16:45:00Z` |

Both windows are **in the past** as of this pass (2026-10-17), and both deployments publish
them with `bannerEnabled: false`. The `.eu` values are exactly the ones
`HCP-CONFIG-SCHEMA.md` §6.4 recorded for `carelinkhp`; the `.com` values are a **different,
earlier** window. A client that displays this window without checking `bannerEnabled` shows a
two-month-old maintenance notice.

### 8.5 The route accepts a doubled slash, and it is the same cell

Three requests (seq 56–58) went out as `/hcp/configuration/public//logbook.supported.entry.types`
— a doubled slash from a trailing slash in a shell variable. All three answered **200 · 226 B
· sha256 `44eabb0f401d…`**, identical to the canonical path's body and identical in the full
response-head set.

Recorded for two reasons. **First, the three rows are left on the ledger and counted, not
edited**, and the canonical cells were issued separately (seq 59–61) — because a 200 that
answers a URL you did not mean to send is `AGENTS.md` §6.2 in its purest form. **Second**, the
observation itself is mildly useful: the route normalises a doubled slash rather than 404ing,
so a path-construction bug in a client is invisible here.

## 9. What this closes, and what it does not

**Closed.** The existence verdicts are deployment-portable: **15 of 15** on three further
deployments. The POW/CUA question is answered: the split is **not** in the verdicts, **not**
in the bodies, and **not** in the route table — each build names the other's namespace, and
`cua.crm.settings` ships `"product": "pow"` everywhere. The TLD, not the product, is the axis
that moves content.

**Not claimed, deliberately.**

- **`carelink-support.medtronic.eu` was not swept.** Four of the five deployments named in
  area A are now measured; the fifth carries the same two build digests, so its *verdicts* are
  INFERRED from the corpus control and its *bodies* are unmeasured. It is excluded from every
  figure in §5 and §7 rather than inferred into them.
- **`carelinkhp.minimed.eu`'s config surface was not re-probed**, per its own
  `HCP-CONFIG-SCHEMA.md` §10. It is quoted as the 2026-10-08 record, never as this pass's
  evidence.
- **The 6 direct `hcp/configuration/*` endpoints were not requested.** `plan.md` names all
  six for both builds; 3 are POST-only (`405`) and 3 token-gated (`401`) on the recorded host,
  and this is a GET-only, no-auth pass (`AGENTS.md` §8). That is area AB.
- **No cause is asserted** for the sub-floor spacing reading, for the three missing security
  headers, or for the `content-type` difference against the 2026-10-08 record.

## 10. Successor — area AB

**`AB` is minted in `docs/11` in this same PR.** It took `AB` rather than `AA`
because lane l3 minted `AA` in PR #148 on the same day; a two-letter id is only a namespace
if it is allocated once. Derived: the six direct literals are now
enumerated for both builds with a digest assertion on each. Bounded: 6 candidates × 3 hosts +
4 controls per host. Non-duplicate: `HCP-CONFIG-SCHEMA.md` §10 says those six were *resolved*
on one host on 2026-10-08, so AB asks the deployment-portability question for them, not their
existence. Labelled: every cell gets a status + content-type + digest under `docs/07`'s
oracle.

## 11. Reproducing

```bash
# batch 1 — the 4 corpus controls (4 requests)
bash findings-log/2026-10-17-hcp-config-deployments/probe.sh bundles
# zero requests — digest assertions, route-table extraction, the per-candidate reasoning
python3 findings-log/2026-10-17-hcp-config-deployments/plan.py        # -> plan.md, plan.json
# batch 2 — 5 controls per host, then that host's own 15-key list (51 requests)
bash findings-log/2026-10-17-hcp-config-deployments/probe.sh keys
# batch 3 — the one cell batch 2 spent on the header-absent control (6 requests, 3 wasted)
bash findings-log/2026-10-17-hcp-config-deployments/probe.sh gap
# the gate, with the pinned suite's own requests logged into this pass's ledger
bash findings-log/2026-10-17-hcp-config-deployments/gate.sh
# zero requests — every table above, and the credential redaction
python3 findings-log/2026-10-17-hcp-config-deployments/redact.py
python3 findings-log/2026-10-17-hcp-config-deployments/analyse.py     # -> analysis.md
```

The two 3.4 MB bundle assets are **not committed** (`scripts/research-checks.py` fails any
file over 1 MiB under `findings-log/`); they are held in `.loop/l2-assets/` and their digests
are reproducible only by re-fetching, which is what the corpus control is for. Response heads
for the 61 sweep rows are under `headers/`; the 52 gate-suite rows have no committed head
(the shim does not intercept bodies).

## 12. Evidence table

| Claim | Class | Source |
|---|---|---|
| The `docs/10` §1 row was wrong on both halves, corrected before any request | SOURCE-OBSERVED | commit `5508de9`; `findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md` §10; `docs/07:112-124`, `:178-193` |
| All four bundle digests reproduce their recorded values | OBSERVED | `results.jsonl` seq 1–4; `plan.md` §Corpus control |
| Both builds carry an identical `hcp/configuration` route table — 15 `public/*` + 6 direct | OBSERVED (shipped code) | `plan.md` §The two route tables; extraction in `plan.py` |
| The extraction reads the same population `HCP-CONFIG-SCHEMA.md` §10 records (15 and 6) | OBSERVED | `plan.md` self-check line |
| Each build names the **other** product's namespace | OBSERVED (shipped code) | `plan.md` clinic-only / support-only literals (both empty) |
| **15 of 15** route literals carry the same status verdict on all three hosts | OBSERVED | `analysis.md` §3; `results.jsonl` seq 5–61 |
| `personal/media/config` and `system.logbook.entry.validation.config` are 404 on all three | OBSERVED | `results.jsonl` seq 23/35/47, 30/42/54 |
| All 4 controls passed on all 3 hosts; 412 = header rejected; namespace case-sensitive | OBSERVED | `analysis.md` §6 |
| **9 of 15** keys byte-identical across all three hosts; **6** differ, and only by TLD | OBSERVED | `analysis.md` §4 |
| **15 of 15** byte-identical between clinic `.com` and support `.com` | OBSERVED | `analysis.md` §5 |
| `cua.crm.settings` ships `"product": "pow"` on all three hosts | OBSERVED | `headers/k021-…`, `k033-…`, `k045-…` |
| The support host serves **no** CSP, HSTS or `x-content-type-options` — 0 of 19 vs 19 of 19 | OBSERVED | `analysis.md` §7; `headers/*.h` |
| `access-control-allow-headers` omits `Content-Type, authorization` on the support host | OBSERVED | `analysis.md` §7 |
| No cause for the security-header difference | — | asserted nowhere; `server` and CloudFront shape identical across all three |
| A non-placeholder `x-api-key` is served by this surface on `.com`, a placeholder on `.eu` | OBSERVED, value redacted | `headers/k028-…`, `k029-…`, `k052-…`, `k053-…`; `REDACTIONS.md`; `docs/08` F2; `SECURITY-FINDINGS` §S3 |
| Already known, not a new disclosure — the key does not authenticate against production | SOURCE-OBSERVED | `docs/08-security-findings.md` §F2; `findings-log/probe-2026-10-08/SECURITY-FINDINGS.md` §S3 |
| `hcp.banner.notifications` publishes a past window, different per TLD, `bannerEnabled: false`, `timezone: "PT"` | OBSERVED | `headers/k022-…`, `k034-…`, `k046-…` |
| `application/octet-stream` on 11 of 13 answering keys on all three hosts | OBSERVED | `analysis.md` §8.2 derivation; `headers/*.h` |
| The 2026-10-08 record types 10 of those keys `application/json` on `carelinkhp` | SOURCE-OBSERVED | `findings-log/probe-2026-10-08/recon/HCP-CONFIG-SCHEMA.md` §5 |
| Whether that is per-host or a loose record | **not determined** | `carelinkhp` config surface not re-probed; §10 says do not re-run |
| The route answers a doubled slash with the identical body and header set | OBSERVED | `results.jsonl` seq 56–58 vs 59–61; `analysis.md` §8 |
| Area A's "the base tracks the deployment, not the product" reading | now OBSERVED, 15 keys × 3 hosts | `findings-log/2026-10-12-area-a-clinic-portal-region/FINDINGS.md` §5 vs `analysis.md` §4 |
| `carelink-support.medtronic.eu`'s verdicts | **INFERRED**, excluded from every figure | same build digests asserted on its `.com` pair; body never requested |
| The sub-floor spacing reading (2.276 s, 1 of 57) | OBSERVED; **no cause asserted** | `analysis.md` §2 |