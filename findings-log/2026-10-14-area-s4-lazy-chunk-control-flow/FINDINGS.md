# Area S4 — lazy-chunk control-flow recovery of request shapes (zero requests)

**Pass date:** 2026-10-14 · **Claim issue:** #93 · **Branch:** `research/s4-headliner`
**Cap:** 0 requests (static only). **Requests made: 0 of 0.**

**Corpus:** the retained patient-app body set — 211 lazy chunk bodies listed in
[source: findings-log/2026-10-13-area-k-patient-chunks/chunks-swept.txt] plus four
further bodies (§2). Bodies total 6,300,855 B across 215 files.

**This document supersedes an earlier draft of the same pass** (commits `b68af1d`,
`66fdf26`). The re-measurement found the draft's central negative was wrong and its
counts were not reproducible. Both the wrong claims and the corrections are preserved
below; see §11.

---

## 1. Verdict

**One genuine positive that contradicts a published negative, one correction to a
second published negative, and a reproducible endpoint inventory.**

1. **`markers[]` is NOT absent.** The patient client reads `markers` off a response
   object and maps it to `unfilteredEventMarkers`, from which it reads four fields
   and dispatches on an 11-token type enum. This is the first **positive** client-side
   marker-schema evidence in the repo, and it **retracts** the negative that area P
   recorded and the earlier draft of this pass repeated. §5. OBSERVED.
2. **The two marker vocabularies diverge by `connectType`** — the BLE branch matches a
   literal `BG_READING`, the non-BLE branch matches an enum `BG`. A consumer that
   switches on one spelling silently drops the other. §5.3. OBSERVED.
3. **`deviceFamily` and `medicalDeviceFamily` are one axis, not two.** The client
   assigns `n.deviceFamily = i.medicalDeviceFamily`. Any analysis treating them as
   independent discriminators over-counts the evidence. §6. OBSERVED.
4. **144 distinct `(method, path)` call-site shapes**, by a counting rule recorded in
   `extract-call-sites.py` and restated in §7 — 72 GET, 49 POST, 14 PUT, 9 DELETE,
   0 PATCH. Two earlier figures for this same corpus (141 and 146) are retracted, and
   the rule **reproduces 17 of the 19 `/patient/csr` shapes** `docs/06` published
   independently, which is the cross-check that it is the right rule. §7.
5. **The logbook submission control flow is recovered**, including three behaviours the
   earlier draft attributed to area P without saying so: the `attributes` nulling for
   7 entry types, the decimal-comma coercion for two entry types, and the conditional
   child-question emission. §4. OBSERVED.

---

## 2. Corpus identity, and what "215 chunks" actually is

Every figure below is a local substring scan over bytes whose identity is pinned here.

**Identity oracle.** sha256 over the sorted `sha256  filename` manifest of all 215
bodies: `3f0830115d428e023fe2362118e4c4a6d385329fd4ffbd927e8de3886869ed87`.

| artefact | bytes | sha256 | verifies |
|---|---|---|---|
| patient bundle | 3,417,255 | `0fb4fbd483b5f5d21320ffc595e1befad999eac170d1e7d484fd1c9b09c8ebaa` | yes |
| clinic hp bundle | 3,397,615 | `2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba` | yes |
| chunk `k-9799-ae484032a07c9d4f-js.b` | 176,766 | `713cd95f8371f7b21a63b5d76f035bd03fb94205aa7aa04a5fe8f41550ba8880` | yes |

**Composition — "215 lazy chunks" is imprecise.** The 211-entry
`chunks-swept.txt` maps 1:1 onto 211 lazy chunk bodies. The four further bodies are:

| body | bytes | what it is |
|---|---|---|
| `k-main.b` | 3,417,255 | the eager **main** bundle (= the patient bundle above) |
| `k-runtime.b` | 8,268 | the runtime |
| `k-fu-_common-206e355a4a593fbd-js.b` | 21,157 | the `id`→**name** variant of chunk 2076 (`f.u` emits `common`) |
| `k-negative-twin.b` | **196** | an HTML **404 page** — a control body, not source |

So the scan runs over **211 lazy chunks + main + runtime + 1 name-variant + 1 HTTP
error page**. The 404 page contributes no call site; its presence is a control that
the sweep distinguishes "fetched" from "is source". A count that treats all 215 as
"lazy chunks" is wrong in the same way as a count that treats all `.get(` as HTTP.

---

## 3. Bundle byte offsets re-checked

The earlier draft asserted a local digest re-check without saying where the bytes
were. They are retained, and both offsets verify:

- byte 1,723,245 of the patient bundle — the device-family enum (§6.1).
- byte 2,964,121 of the patient bundle — the `startsWith` routing matcher (§6.2).

Both are quoted verbatim in §6. **OBSERVED.**

---

## 4. Logbook submission control flow

**Source:** `k-9799-ae484032a07c9d4f-js.b`, sha256 as §2.
**Statement extent: bytes 80,919 → 84,159** (3,240 B), located by brace-matching from
`if(this.form.valid){`.

> **Correction to the citation, not to the claim.** The earlier draft cited
> 80,919 → 81,960. That window ends mid-`physicalDisturbanceType` and contains **none**
> of the insertion / removal / medication / adhesive branches its own table described.
> The claims were true; the cite pointed at a window that could not support them.

Sequence, verbatim:

- `entryTs`, `type` (`this.entryType`), `id` (`0` when `isEmpty`, else `this.data.id`)
  and `comment` are set for every entry type.
- `attributes` is initialised to `{}` and then **set to `null`** for exactly 7 entry
  types — `INFUSION_SET_CHANGE, OTHER, SENSOR_PHYSICAL_DISTURBANCE, MEDICATION,
  ADHESIVE_AND_TAPE, SENSOR_INSERTION, SENSOR_REMOVAL` — so those types carry **no**
  `attributes` bag at all. For every other type it is filled dynamically as
  `attributes[<form-control-name>]`, skipping `entryTs`, `additionalTime`,
  `minutesTime`, `comment`.
- `BLOOD_KETONES` and `HBA1C` coerce their measurement field with
  `.toString().replace(",", ".")` — a decimal-comma → decimal-point re-encoding on the
  wire.
- State-dependent branches:

| entry type | wire object | fields (form control → wire key) |
|---|---|---|
| `SENSOR_INSERTION` | `sensorInsertionInfo` | `sensorInsertionLocation`→`sensorLocation`; `sensorInsertionLocationOther`→`otherSensorLocation` (nulled when empty); `capUnscrewDateConversion()`→`timeCapUnscrewed` |
| `SENSOR_REMOVAL` | `removalInfo` | `sensorRemovalLocation`→`sensorLocation`; `sensorRemovalLocationOther`→`otherSensorLocation`; `removalType`; `removalReason` (nulled); `removalDescription` (nulled) |
| `SENSOR_PHYSICAL_DISTURBANCE` | `physicalDisturbanceInfo` | `sensorPdLocationOther`→`otherSensorLocation`; `sensorPdDescription`→`physicalDisturbanceDescription`; `sensorPdType`→`physicalDisturbanceType`; `sensorPdLocation`→`sensorLocation` |
| `MEDICATION` | `medicationInfo` | `medicationName`; `medicationDose`→`dose`; `medicationDoseUnit`→`doseUnit`; `medicationOther`→`otherUnit` |
| `ADHESIVE_AND_TAPE` | `adhesiveAndTapeInfo` | `adhesivetapeLocation`→`sensorLocation`; `adhesivetapeLocationOther`→`otherSensorLocation`; `questions[]` |

`ADHESIVE_AND_TAPE.questions` is **built conditionally** (the control-flow gap
`docs/11` §K predicted): for each configured question it emits
`{answer, question, otherAnswer, children[]}`; a child question is emitted only where
`y.children.findIndex(S => S.conditionValue === answer) !== -1`, `otherAnswer` is read
from a `freeText_*` control only when the matched child declares exactly one free-text
slot, and `children` is then filtered to drop null answers. This is the
"picking one removal reason triggers a free-text field" behaviour, recovered as
control flow rather than inferred from field names. **OBSERVED.**

### 4.1 `timecapUnscrewed` vs `timeCapUnscrewed` — both are correct, for different things

The two casings both occur in the corpus, 42 and 5 times respectively, and reading the
contexts separates them cleanly:

| token | occurrences | role | example site |
|---|---|---|---|
| `timecapUnscrewed` | 42 | **form-control name** | `this.form.addControl("timecapUnscrewed", …)`, `isShowControlError("timecapUnscrewed","required")` |
| `timeCapUnscrewed` | 5 | **wire field** | `timeCapUnscrewed: this.capUnscrewDateConversion()` |

There are also `timecapUnscrewed_minutesTime` and `timecapUnscrewed_additionalTime`
controls. **OBSERVED.**

So the casing correction recorded by area P stands — but stated correctly: the
lowercase form is **not wrong**, it is the control name. What was wrong was reading it
as the wire field. `docs/10` row 46 lists the lowercase token among "call-site fields",
which is accurate; the wire casing is `timeCapUnscrewed`.

> **Scope limit, stated rather than smoothed.** `docs/07` and `docs/00` list
> `sensorInsertionLocation`, `adhesivetapeLocation` and `timecapUnscrewed` as field
> names "at HTTP call-sites", citing
> [source: findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md]. That file mines the
> **clinic portal** corpus, which is not retained here and which contains **neither**
> casing. The control-name / wire-field distinction above is therefore stated for the
> **patient** app only. The clinic wording is left unchanged: correcting it from a
> different corpus would be the AGENTS.md §6 item-5 failure.

---

## 5. `markers[]` — the negative is retracted

The earlier draft recorded "the token `markers` occurs **zero** times as a wire
property" and classified every surviving hit as an SVG asset name, a charting marker,
or a wordlist entry. Re-measured per-hit, that is **wrong on the one hit that matters**.

`markers` occurs **4** times in the corpus. Classified:

| # | context | classification |
|---|---|---|
| 1 | `n.unfilteredEventMarkers=i.markers` | **wire property read** |
| 2 | `oe.markerGroup=oe.plotGroup("markerGroup","markers",…)` | SVG element-group name |
| 3 | `…,biomarkers,…` | password wordlist |
| 4 | `…,markers,reconciliation,…` | password wordlist |

Hit 1 is at byte 77,962 of `k-6746-c6795ff7e9ff468d-js.b`. It is the assignment of a
response field onto the client's view model. `unfilteredEventMarkers` occurs **7**
times in total, all in that chunk.

### 5.1 Marker item schema — OBSERVED

```js
n.unfilteredEventMarkers = i.markers;
…
for (const ue in i.unfilteredEventMarkers) {
  const ie = i.unfilteredEventMarkers[ue],
        De = O - 3e5 * (287 - ie.index);
  …
  "LOW_GLUCOSE_SUSPENDED" != ie.type ||
    (ie.value = ie.deliverySuspended ? 400 : 0,
     i.lowGlucoseSuspends.push([ae, ie.index, ie.value, ie.type]))
}
```

| field | type / use | evidence |
|---|---|---|
| `index` | integer slot; timestamp is `anchor − (287 − index) × 300000 ms` | OBSERVED |
| `type` | string, dispatched on | OBSERVED |
| `value` | numeric, clamped by the consumer (§5.2) | OBSERVED |
| `deliverySuspended` | boolean; the corpus reads it exactly **once**, at byte 70,908 | OBSERVED |

`index > 287` is dropped **except** for `LOW_GLUCOSE_SUSPENDED`, which is retained past
the window.

### 5.2 Marker type vocabulary — 11 tokens, OBSERVED

Webpack module **56358** at byte 65,622 of the same chunk:

```
CALIBRATION, AUTO_BASAL_DELIVERY, AUTO_MODE_STATUS, TIME_CHANGE,
BG_READING, BG, INSULIN, MEAL, LOW_GLUCOSE_SUSPENDED, EXERCISE, OTHER
```

`getMarkersBasedOnType` (byte 80,428) switches on **9** of the 11. `AUTO_BASAL_DELIVERY`
and `AUTO_MODE_STATUS` occur exactly twice each in the corpus — the declaration itself —
so they are **declared but never handled** and fall to `default`, which contributes a
value of `0`. That is an honest distinction: the enum is an 11-token superset of the
9-token set the renderer acts on.

### 5.3 The two vocabularies diverge — OBSERVED, and the most actionable item here

`getMarkersBasedOnType` has two branches selected by `connectType`:

| marker meaning | BLE branch (literal) | non-BLE branch (enum) |
|---|---|---|
| food / uncategorised | `"OTHER"`, `"MEAL"` → 67 | `OTHER`, `MEAL` → `sgBelowLimit` |
| low-glucose suspend | `"LOW_GLUCOSE_SUSPENDED"` → skipped | `LOW_GLUCOSE_SUSPENDED` → skipped |
| exercise / insulin | `"EXERCISE"`, `"INSULIN"` → 385.2 | `EXERCISE`, `INSULIN` → 385.2 |
| **glucose reading** | **`"BG_READING"`** | **`BG`** |
| calibration | `"CALIBRATION"` → clamp 41–385.2 | `CALIBRATION` → clamp to `sgBelowLimit`–385.2 |
| **time change** | (in the insulin/385.2 group) | **`TIME_CHANGE` → 400** |

A consumer switching on `BG_READING` alone silently drops every Guardian/legacy marker;
switching on `BG` alone drops every BLE one. This is a **client-side** divergence in
what the app will recognise, and it is exactly the kind of thing a consumer pinning a
marker vocabulary needs to know. **OBSERVED.**

### 5.4 What this does and does not settle

- **Settled, client-side:** the marker item shape, the index arithmetic, and the type
  vocabulary (with the BLE/non-BLE split).
- **Not settled:** whether the **logbook entries** endpoint carries `markers[]`.
  The site above reads the **periodic connect-data** response
  (`…connect/data…?cpSerialNumber=NONE&msgType=last24hours&requestTime=…`). That is a
  different surface from the one `docs/10` row 46 is blocked on. Row 46 stays open;
  what changes is that its blocker is no longer "nothing is known".
- **Retracted:** the claim that no `markers` wire property exists anywhere in the
  patient corpus.

---

## 6. `deviceFamily` — one axis, not two

### 6.1 What was already on the record

The patient bundle's client enum at byte 1,723,245:

```js
const e = { BLE:"BLE", BLE_X:"BLE_X", SIMPLERA:"SIMPLERA",
            SIMPLERA_X:"SIMPLERA_X", GUARDIAN:"GUARDIAN" };
```

and the routing matcher at byte 2,964,121:

```js
({deviceFamily: p}) => {
  const F = p == null ? void 0 : p.startsWith(o.G.BLE);
  const T = p == null ? void 0 : p.startsWith(o.G.SIMPLERA);
  const v = p == null ? void 0 : p.startsWith(o.G.GUARDIAN);
  return F || T || v ? this.userService.getUploadDeviceInfo(A) : of(null)
}
```

Both of these are already recorded in
[source: findings-log/2026-10-13-area-p-static-schema/FINDINGS.md] §4, which the
earlier draft of this pass reproduced without attributing.

### 6.2 The correction — the two "axes" are one

`parseJsonData` in `k-6746-c6795ff7e9ff468d-js.b` (definition at byte 74,236; the
assignment itself at byte 74,268) opens:

```js
parseJsonData(i, v) { const n = {};
  n.deviceFamily = i.medicalDeviceFamily,
  n.isGuardian = "GUARDIAN" === n.deviceFamily,
  …
```

**The client derives the routing discriminator from the reported field.** `deviceFamily`
is not an independent axis with a partially-overlapping vocabulary; on the wire it is
the value of `medicalDeviceFamily` under a second name. The earlier draft's table —
which presented the two as separate properties overlapping only on `GUARDIAN`, and
counted "two unrelated code paths and three unrelated clients agree" — therefore
**over-counts its own evidence**. **OBSERVED**, and it is a correction to the reasoning
in the earlier draft, not to area P (which only ever claimed a casing candidate).

### 6.3 `NGP` is a `deviceFamily` value the draft missed

Two sites in the same chunk compare it directly (`k-6746-c6795ff7e9ff468d-js.b`,
bytes 87,559 and 78,361):

```js
this.isNGP = "NGP" === K.deviceFamily;
…
if (n.connectType === I.v.BLE && "NGP" === n.deviceFamily) { … sLastAlarmCode … }
```

So the routing discriminator's observed value set is at least
`BLE, BLE_X, SIMPLERA, SIMPLERA_X, GUARDIAN, NGP`. This bears on the NGP rows
(`docs/10` #38, #39) — as a **client-side** value only; the server's own vocabulary is
still token-gated. **OBSERVED.**

### 6.4 Persistence, for completeness

The app round-trips the value through `sessionStorage.getItem("deviceFamily")` and
injects it into later responses. **OBSERVED.** Stated because it explains why a
`deviceFamily` seen in a client-side artefact may reflect a *previous* session's
response rather than the one being read.

---

## 7. Endpoint inventory — 144 shapes, counting rule recorded

**Counting rule** (AGENTS.md §6 item 7: the rule lives in a script, not in prose).
Implementation: `extract-call-sites.py`, committed in this directory. Run it with the
corpus directory as `$S4_CORPUS` and an output directory as `$S4_OUT`; it writes
`pairs.tsv`, `unresolved.tsv`, `resolved-constants.tsv` and `counters.json`. All four
outputs are committed here, so the inventory is inspectable without the corpus.
**Zero requests — pure string analysis over bytes on disk.** Four decisions, each of
which moves the number:

**D1 — receiver.** A call site counts only when the receiver is `http`, `_httpClient`
or `httpClient` (the injected Angular `HttpClient`). The corpus holds **1,139**
`.get(/.post(/.put(/.delete(` occurrences; **233** are HTTP. The rest share those five
method names as collection lookups — `form.get` 161, `this.get` 37, `Vt.get` 27,
`headers.get` 15, `cookieService.get` 14, `injector.get` 11, `map.get` 10,
`cookieService.delete` 5. Counting `.get(` without D1 is the AGENTS.md §6 item-2 trap,
and is how the earlier drafts produced figures reproducible under no stated rule at all.

**D2 — the first argument is a literal**, in any of three forms, all of which count:

| form | example | pairs |
|---|---|---|
| leading slash | `"/patient/users/me"` | 110 |
| **no leading slash** | `"patient/logbookEntry"` | 34 |
| template, may interpolate | `` `patient/logbookEntry/${w}` `` | (counted above) |

34 shapes carry **no leading slash** — the client sends them relative and an interceptor
prefixes the base URL. Any rule that requires a leading `/` drops them silently; the
earlier drafts' rule did exactly that.

**Conditional paths.** A ternary in first-argument position contributes **both**
branches, each labelled, because the client selects at runtime. Three sites:

| method | then-branch | else-branch |
|---|---|---|
| POST | `/patient/users/me/validate/password/compliance` | `/patient/validate/password/compliance` |
| POST | `` /patient/m2m/sms/sendTestSms/${encodeURIComponent(A)} `` | `/patient/sms/sendTestSms` |
| GET | `` /patient/csr/users/me/notifications/history/patients/${encodeURIComponent(a)} `` | `/patient/csr/users/me/notifications/history` |

The first is a flag-dependent choice between a patient-scoped and a legacy path — a
client-side routing fact that reading either route would never reveal.

**D3 — `${this.baseUrl}` is resolved only within its own chunk, and only when that
chunk holds exactly one `this.baseUrl="literal"` assignment.** The guard is the point.
`this.baseUrl` is an instance property meaning different things in different builds
(`"/patient/csr"` in a service vs a CMS media base `getBaseCmsUrl()` in the eager
bundle), so resolving it by leaf name returns whichever entry was indexed first and
*looks* like agreement — AGENTS.md §6 item 3. Four chunks carry such templates and each
has exactly one assignment, so 20 sites resolve under the guard.

**D4 — slot names are minifier artefacts, so slots are renumbered by position.**
`${t}/users`, `${o}/users` and `${c}/users` are the same template in three chunk builds.
This is the rule `docs/06` already states for its own sweep; reusing it keeps **one**
notion of "distinct shape" in this repository rather than two. The verbatim, un-normalised
literal is still emitted alongside in `pairs.tsv`, so nothing is lost by normalising.

### 7.1 Measured result

```
232 http call sites → 155 literal-path + 20 resolved-variable + 57 UNRESOLVED
144 distinct (method, path) shapes = 72 GET + 49 POST + 14 PUT + 9 DELETE + 0 PATCH
```

**Method arithmetic is stated so it can be checked: 72 + 49 + 14 + 9 = 144.**

| metric | value |
|---|---|
| HTTP call sites (D1 receiver-matched) | 232 |
| sites with a literal first-argument path | 155 |
| sites resolved from a variable under D3 | 20 |
| sites whose path is a variable — **not guessed** | 57 |
| **distinct shapes** | **144** |
| shapes with / without a leading slash | 110 / 34 |
| shapes with / without interpolation | 44 / 100 |
| PATCH | 0 — no `http.patch` call site exists anywhere in the corpus |

The single enum-constant resolution is `POST T.S.PATIENT_REPORTS_SENSOR_HISTORY` →
`patient/reports/sensor-history`, defined at byte 1,532,586 of the main bundle and used
at byte 2,211,303 of the same file — so that path came from the **eager** bundle, not
from any lazy chunk. Constant resolution is allowed only for a dotted constant whose
leaf name is defined exactly once in the corpus.

### 7.2 The rule reproduces `docs/06`'s independent `/patient/csr` measurement

This is the cross-check that D1–D4 are the right decisions rather than a rule fitted to
this corpus. `docs/06` published **19** `/patient/csr` method × path shapes on
2026-10-13 from its own sweep. Applying D1–D4 to the whole corpus:

| relation | count |
|---|---|
| `docs/06` shapes reproduced **exactly** | **17** |
| `docs/06` shapes my rule leaves **unresolved** | 2 |
| shapes my rule finds that `docs/06`'s table does not list | 9 |
| **total `/patient/csr` shapes under D1–D4** | **26** |

The two not reproduced are the **bare-base** rows — `GET` and `POST` on
`/patient/csr/safety/notice/definitions` with no suffix. Those calls pass
`this.baseUrl` itself as the first argument, an identifier rather than a literal, so D2
does not admit them and they fall into the unresolved 57. `docs/06` resolved them by a
deliberate decision this rule does not make: *"a bare `this.baseUrl` is a shape, not an
exclusion."* **Both rules are recorded; neither is withdrawn.**

The nine additional shapes are `/patient/csr/admin/info`, `/patient/csr/users/me/account`
(GET and PUT `…/reactivate`), `/patient/csr/users/me/profile`,
`/patient/csr/users/reset/password/link`, `patient/csr/snapshot`,
`patient/csr/getTrace`, and `patient/csr/v2/control/codes` (GET and POST). The
difference is scope, not contradiction: `docs/06`'s sweep was confined to the CSR
namespace by one receiver style, whereas D1–D4 sweep every `http.*` receiver in the
whole corpus and so reach CSR call sites sitting in unrelated chunks. `docs/06`'s own
caveat — *literal ≠ live* — applies unchanged to all nine: none was probed.

### 7.3 The 57 unresolved sites are a finding, not a gap in the work

They are dominated by a report URL builder (`this.createUrlForReport(…)`), the bare-base
calls above, and constants (`g._m`, `Ke.B2`, `fp.rx`, `S.No`, `fp.YV`) whose definitions
are **not in the retained corpus**. One apparent resolution is a false positive and is
called out so nobody re-derives it: `SI:"31234567"` is an Angular internal, not an
endpoint.

---

## 8. Evidence classes used

| class | used for |
|---|---|
| **OBSERVED** | every §2–§7 fact: literals read from bytes whose digests re-matched in §2/§3 |
| **PUBLISHED** | the two bundle digests, as recorded in area K and area P |
| **INFERRED** | nothing in §4–§7 is inferred. The two places inference would normally live are stated as open instead: the server's GET echo of a logbook entry, and the server's own marker/device-family vocabulary |

No claim in this pass reads as OBSERVED unless it was read from a body whose digest
re-matched here.

---

## 9. What this pass does not settle

1. The server's **GET echo** of a logbook entry — §4 is the client's *submission*
   payload; the read side stays token-gated (`docs/10` row 46).
2. Whether `markers[]` appears on the **logbook entries** response. §5 settles the
   periodic connect-data surface only.
3. The server's **NGP** vocabulary. §6.3 is a client-side comparison value only.
4. The 57 variable-path call sites (§7.2).

---

## 10. Request accounting

**0 of a 0 cap.** Cap for this pass: **0 requests**. Requests issued: **0**.

| item | value |
|---|---|
| accounting | **0 of a 0 cap** |
| HTTP methods used | none — no `GET`, `POST`, `PUT`, `DELETE` or `OPTIONS` |
| DNS lookups | none |
| hosts contacted | none — not the vendor estate, not Common Crawl, not Wayback |
| inter-request delay | **≥2 s** floor declared per AGENTS.md §8, and **vacuous**: there were no requests to space out |

Every figure in §2–§7 is a local substring scan over bytes already on disk, re-identified
against the manifest digest in §2. The corpus was read; nothing was fetched. The one
artefact that looks like a fetch is not one: `k-negative-twin.b` is a **196-byte HTTP
404 body retained as a control**, which is how this pass proves it can tell a fetched
page from a source file (§2).

---

## 11. Correction (2026-10-14) — the earlier draft of this pass

Preserved per AGENTS.md §3. The earlier draft of this pass is commits `b68af1d` and
`66fdf26`. A continuation pass re-measured each of its claims from source. Seven
defects were found; none was a vendor-surface change, all were analysis defects.

| # | draft claim | status on re-measurement |
|---|---|---|
| 1 | citation window 80,919 → 81,960 is "one uninterrupted statement" | **cite wrong** — true extent 80,919 → 84,159; the cited window holds none of the branches the section described |
| 2 | `markers` occurs zero times as a wire property | **false** — `i.markers` is read at byte 77,962; negative retracted (§5) |
| 3 | 146 pairs, 90 GET / 50 POST / 21 PUT / 9 DELETE | **not reproducible and internally inconsistent** — the parts sum to 170, not 146. Measured 144 under a recorded rule (§7) |
| 4 | (first commit) 141 pairs, 90/47/6/7/1 | **not reproducible**, and its parts sum to 151, not 141 |
| 5 | routing `deviceFamily` and reported `medicalDeviceFamily` are two axes overlapping on `GUARDIAN` | **wrong** — the client assigns one from the other (§6.2) |
| 6 | "chunk `k-connect-*`" as the equality site | **not a real filename** — the site is `k-6746-c6795ff7e9ff468d-js.b` |
| 7 | §3 field table and §4 bundle enum/matcher presented as this pass's finding | **duplicate of merged area P** §3/§4, unattributed |

Also corrected, in the direction of area P: the draft's §2 stated a local digest
re-check without naming the retained bytes. The digests **do** verify (§2), so the
claim stands once the bytes are named.

Two defects in this pass's own tooling, recorded because both were the documented
traps:

- The first extractor cut a call's first argument at the first `(`, which truncated
  template literals containing `${encodeURIComponent(…)}` and silently dropped 3
  ternary sites. Replaced with an exact quote-aware scanner, which moved the count from
  144 to 155. AGENTS.md §6 item 2, self-inflicted.
- Resolving `this.baseUrl` by leaf name would have produced a confident wrong path;
  §7 D3 records the per-chunk guard instead, and resolving under it moved the count
  back down as the `${this.baseUrl}` templates became real paths rather than
  `${this.baseUrl}`-prefixed strings.
- D4 then removed 11 further shapes by renumbering minifier slot names. The final
  count is 144, and it is the number that survives all four decisions — which is the
  only reason to trust it: each was adopted because it removed a *demonstrated*
  duplication, not because it moved the number in a convenient direction.

One line of tooling debris was removed from this file: a stray heredoc terminator
(`PY`) and an echoed `wc -l` command that a failed shell write had appended. It is
not a claim, and it is noted here rather than deleted silently.

**Where area P is wrong**, for the record, since it is merged and append-only: area P's
"verbatim" snippet renders one branch as `p.PHYSICAL_DISTURBANCE`. The token in the
chunk is **`p.SENSOR_PHYSICAL_DISTURBANCE`** (byte 81,679 of chunk 9799), as §4's table
uses it. Area P's own recovery is otherwise confirmed.

---

## 12. Sources cited

- [source: findings-log/2026-10-13-area-k-patient-chunks/chunks-swept.txt] — the 211-entry chunk list
- [source: findings-log/2026-10-13-area-k-patient-chunks/FINDINGS.md] — corpus retention and digests
- [source: findings-log/2026-10-13-area-p-static-schema/FINDINGS.md] — §3 field recovery, §4 bundle enum
- [source: findings-log/2026-10-13-area-p-static-schema-recovery/FINDINGS.md] — prior `markers` negative
- [source: findings-log/2026-10-11-third-party-client-sources/FINDINGS.md] — reported `medicalDeviceFamily` values
- [source: findings-log/probe-2026-10-08/CHUNK-CORPUS-FINDINGS.md] — clinic-portal call-site field names
- `extract-call-sites.py` — the counting rule, same directory
- bundles: patient `0fb4fbd4…` (3,417,255 B), clinic hp `2a7fa8e7…` (3,397,615 B)
- docs pages updated by this pass: `docs/05`, `docs/10`, `docs/11`

Evidence classes: OBSERVED, PUBLISHED, INFERRED as defined in AGENTS.md §2.
