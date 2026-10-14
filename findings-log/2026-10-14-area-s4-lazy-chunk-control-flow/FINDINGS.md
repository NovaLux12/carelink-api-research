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

**Byte-offset convention, declared because it was previously left implicit:** offsets
are **0-indexed and start-inclusive**, and point at the **start of the token or
statement named**. The one exception is marked where it occurs: §4's statement extent is
given as a **half-open range** `[80919, 84159)`, because it is an extent rather than a
token position. An earlier draft mixed the two without saying so.

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
**Statement extent: bytes 80,919 → 84,159**, a **half-open range `[80919, 84159)`**
(3,240 B), located by brace-matching from `if(this.form.valid){`.

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

⚠ **The §4 window does not contain this evidence.** The 42 lowercase occurrences span
bytes **30,424–98,733** of the chunk — the control is declared in a *different* module
from the one that serialises it — and **0 of them** fall inside §4's statement extent
`[80919, 84159)`. Of the 5 capital-C occurrences (65,606 / 76,826 / 82,579 / 127,510 /
127,580) only **one** (82,579) is inside that window. An earlier draft cited the window
for the casing distinction; it does not support it, and the wider spans are given here
instead. **OBSERVED.**

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

Hit 1 is the right-hand side `i.markers` at byte **77,985** of
`k-6746-c6795ff7e9ff468d-js.b` (the left-hand `n.unfilteredEventMarkers` begins at
77,960). It is the assignment of a
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
| `deliverySuspended` | boolean; the corpus reads it exactly **once**, at byte 71,063 | OBSERVED |

`index > 287` is dropped in the **BLE branch** of `getMarkersBasedOnType`, **except**
for `LOW_GLUCOSE_SUSPENDED`, which is retained past the window. The non-BLE branch has
no such guard. Stated per-branch because the earlier phrasing made it unconditional.
**OBSERVED.**

### 5.2 Marker type vocabulary — 11 tokens, OBSERVED

Webpack module **56358** at byte 65,423 of the same chunk:

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
| calibration | `"CALIBRATION"` → clamp 41–385.2 | `CALIBRATION` → clamp to **`sgBelowLimit + 1`**–385.2 |
| **time change** | (in the insulin/385.2 group) | **`TIME_CHANGE` → 400** |

The non-BLE calibration floor is `sgBelowLimit + 1`, not `sgBelowLimit`
(`W=C.value>385.2?385.2:C.value<O+1?O+1:C.value`, byte 81,344, where `O=c.sgBelowLimit||40`).

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
assignment itself, `n.deviceFamily=i.medicalDeviceFamily`, at byte 74,266) opens:

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

**Four** `NGP` comparison sites exist in `k-6746-c6795ff7e9ff468d-js.b`, all
0-indexed byte offsets:

| byte | code | notes |
|---|---|---|
| 76,305 | `"NGP"===n.deviceFamily){… n.sLastAlarmCode = …` | gates alarm-code formatting |
| 78,360 | `"NGP"==n.deviceFamily){const y=i.lastBolus; … n.sLastBolusDate/Time` | gates **last-bolus** fields, not alarm codes |
| 83,894 | `"NGP"==i.medicalDeviceFamily && (h("activeInsulin") || …)` | compares the **reported** field name directly — independent corroboration of §6.2 |
| 87,565 | `this.isNGP="NGP"===K.deviceFamily;` | sets the `isNGP` flag; 87,559 is the `isNGP` identifier itself |

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
`.get(/.post(/.put(/.delete(` occurrences; **233** are HTTP. The leading ones share those
five method names as collection lookups — `form.get` 161, `this.get` 37, `Vt.get` 27,
`headers.get` 15, `cookieService.get` 14, `map.get` 10, `injector.get` 11,
`cookieService.delete` 5, `_injector.get` 9, `paramMap.get` 4 — and the list continues
past those ten; the figure is a floor, not a total, and is labelled as such here rather
than presented as "the rest". Counting `.get(` without D1 is the AGENTS.md §6 item-2
trap, and is how the earlier drafts produced figures reproducible under no stated rule at
all.

> **D1 had a real bug, found by the independent verifier and now fixed.** The first
> version of the receiver pattern was `(?:_?http|HttpClient|httpClient)`, in which the
> `_?http` branch is followed by `\.` and therefore **cannot** match `_httpClient.` One
> real call site (`k-main.b`, `this._httpClient.get(…)`) was silently dropped, giving 232
> where there are 233. It is now `(?:_?http(?:Client)?|HttpClient)`. The 144 headline was
> unaffected — that site's first argument is a variable, so it lands in the unresolved
> column — but the site total was wrong and the prose had been written to match the bug.

**D2 — the first argument is a literal**, in any of three forms, all of which count:

| form | example | pairs |
|---|---|---|
| leading slash | `"/patient/users/me"` | 99 |
| **no leading slash** | `"patient/logbookEntry"` | 45 |
| template, may interpolate | `` `patient/logbookEntry/${w}` `` | (counted above) |

45 shapes carry **no leading slash** — the client sends them relative and an interceptor
prefixes the base URL. Any rule that requires a leading `/` drops them silently; the
earlier drafts' rule did exactly that.

**Conditional paths.** A ternary in first-argument position contributes **both**
branches, each labelled, because the client selects at runtime. **Four** sites, which
contribute 8 branch rows to `pairs.tsv`:

| method | then-branch | else-branch |
|---|---|---|
| POST | `/patient/users/me/validate/password/compliance` | `/patient/validate/password/compliance` |
| POST | `` /patient/m2m/sms/sendTestSms/${encodeURIComponent(A)} `` | `/patient/sms/sendTestSms` |
| GET | `` /patient/csr/users/me/notifications/history/patients/${encodeURIComponent(a)} `` | `/patient/csr/users/me/notifications/history` |
| GET | `` …/patients/${encodeURIComponent(a)}/export/csv `` | `…/notifications/history/export/csv` |

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
233 http call sites → 154 literal + 20 baseUrl-resolved + 1 constant-resolved + 58 UNRESOLVED
144 distinct (method, path) shapes = 72 GET + 49 POST + 14 PUT + 9 DELETE + 0 PATCH
```

**Method arithmetic is stated so it can be checked: 72 + 49 + 14 + 9 = 144.**

| metric | value | source |
|---|---|---|
| HTTP call sites (D1 receiver-matched) | 233 | `counters.json` |
| sites with a literal first-argument path | 154 | `counters.json` |
| sites resolved under D3 (`${this.baseUrl}`, within-chunk guard) | 20 | `resolved-constants.tsv` |
| sites resolved from a uniquely-defined enum constant | 1 | `resolved-constants.tsv` |
| sites whose path is a variable — **not guessed** | 58 | `counters.json` |
| rows in `resolved-constants.tsv` | 21 | `counters.json` |
| **distinct shapes** | **144** | `pairs.tsv`, `counters.json` |
| shapes with / without a leading slash | 99 / 45 | `counters.json` |
| ternary sites / branch rows | 4 / 8 | `counters.json` |
| `/patient/csr` shapes (§7.2) | 26 | `counters.json` |
| shapes with / without interpolation | 44 / 100 | `counters.json` |
| PATCH | 0 — no `http.patch` call site exists anywhere in the corpus | `counters.json` |

> **Every figure in that table is read out of the committed `counters.json`, which
> `extract-call-sites.py` writes.** An earlier draft of this pass carried
> 110/34 by hand against a committed output that said 99/45 — AGENTS.md §6 item 5, in
> the one section whose thesis is that the rule lives in a script. The counters that feed
> this table were added to the script in response, so the number cannot drift from the
> prose again.

`resolved-constants.tsv` has **21 data rows** — 20 from the D3 `this.baseUrl` family,
all resolving to `/patient/csr/incidents` or `/patient/csr/safety/notice/definitions`,
and 1 from an enum constant. The constant is `POST T.S.PATIENT_REPORTS_SENSOR_HISTORY` →
`patient/reports/sensor-history`, defined at byte 1,532,586 of the main bundle and used
at byte 2,211,303 of the same file — so that path came from the **eager** bundle, not
from any lazy chunk. Constant resolution is allowed only for a dotted constant whose
leaf name is defined exactly once in the corpus.

**A label that was wrong and is now right.** An earlier version counted the
constant-resolved site inside `sites_with_literal_path`, because the counter was keyed on
"did the harvester produce something" rather than on *how*. The constant has its own
column now, which is why the literal count is **154** and the four columns sum exactly:

```
154 literal  +  20 baseUrl-resolved  +  1 constant-resolved  +  58 unresolved  =  233
```

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
does not admit them and they fall into the unresolved **58**. `docs/06` resolved them by a
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

### 7.3 The 58 unresolved sites are a finding, not a gap in the work

Composed exactly as `unresolved.tsv` records them — this breakdown is read off the
committed file, not from memory:

| class | count | examples |
|---|---|---|
| bare-base calls (`this.baseUrl`) | 6 | the two rows `docs/06` counts as shapes |
| dotted constant refs | 8 | `e.SI` ×3, `fp.rx`, `g._m`, `Ke.B2`, `S.B2`, `S.No`, `w.Bp` |
| `this.url` / `this.createUrlForReport(...)` | 3 | a report URL builder |
| bare local identifiers (minified params) | 41 | `j`, `p`, `V`, `t`, … |

None of the eight constants resolves. `e.SI` never resolves **structurally**: the
constant pattern requires a leading `.`, and the corpus writes `,SI:"31234567",`. An
earlier draft called that string "an Angular internal" — that attribution was an
unlabelled INFERRED guess and is **deleted** here, because nothing in the corpus
identifies what `SI` is. The other seven are absent from the retained corpus.

An earlier draft also listed `fp.YV` here. It is not unresolved: the site is
`` `${m}${fp.YV}` ``, a template literal, so it is counted in `pairs.tsv` as shape
`{1}{2}` with the constant left unexpanded. Corrected.

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
4. The 58 variable-path call sites (§7.3).

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
| 2 | `markers` occurs zero times as a wire property | **false** — `i.markers` is read at byte 77,985; negative retracted (§5) |
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
chunk is **`p.SENSOR_PHYSICAL_DISTURBANCE`** (`p.` at byte 81,679; the bare
`SENSOR_PHYSICAL_DISTURBANCE` token at 81,681; the enclosing `if(` at 81,668), as §4's
table uses it. Area P's own recovery is otherwise confirmed.

## 11a. Correction (2026-10-14) — first verifier round, on this document's own draft

An independent `carelink-verifier` reviewed the draft of this document at SHA
`7f4a5babd902a0c3242a8c180a4ca912ca4fa207` and returned **NOT CLEAN** with nine
blocking findings. It used **0 of its 10-request budget** — every finding came from
re-deriving against the corpus on disk, not from the network, and none passed through
this document's wording. All nine were re-derived independently before being accepted;
all nine held. They are fixed above, and they were all defects of this pass's analysis
and citation, not of the vendor surface.

| # | verifier finding | status |
|---|---|---|
| 1 | "34 shapes carry no leading slash" — the committed `pairs.tsv` says **45**, and the script's own docstring already said 45 | fixed; the figure is now read from `counters.json`, which gained the leading-slash counters so the prose cannot drift from the output again |
| 2 | `markers` is at byte 77,987, not 77,962 | fixed in two steps — §11b records the second: `77,984` was the `=`, the `i.markers` expression is at **77,985**, and the left-hand `n.unfilteredEventMarkers` at **77,960** |
| 3 | §6.3 quoted the text at byte 76,306 under a citation of 78,361, which holds last-bolus fields; and `docs/05` propagated it | fixed — all four `NGP` sites are now tabulated with what each actually gates, and `docs/05` corrected |
| 4 | "232 vs 233" was a **regex bug**, not a scope note: `(?:_?http\|HttpClient\|httpClient)` cannot match `_httpClient.` | fixed — `(?:_?http(?:Client)?\|HttpClient)`; site total is **233**, and the prose had been written to match the bug |
| 5 | "all four outputs are committed" — three were | fixed — `resolved-constants.tsv` is now committed |
| 6 | "three sites" for ternaries — there are **4** (8 branch rows) | fixed, and the count is now emitted by the script |
| 7 | offsets 65,622→**65,423**, 70,908→**71,063**, 81,679→**81,668** | first two fixed; the third is a **disagreement, not an error** — 81,679 is the `p.` token this document cites and the enclosing `if(` is at **81,676** (§11b corrects 81,668, which was the verifier's own error carried into this sentence). The byte convention is now declared in §2 so the two cannot be confused again |
| 8 | minor: non-BLE calibration clamps to **`sgBelowLimit + 1`** not `sgBelowLimit`; `index > 287` is a **BLE-branch-only** guard; the §4 window holds **0 of the 42** lowercase casing occurrences | all three fixed |
| 9 | gate exit 0 — INCONCLUSIVE **by abstention** | not a defect in this pass. The gate runs `05-public-config.check.sh`, which makes live vendor requests; the verifier declined to spend them. The offline half (`scripts/research-checks.py`) was run and passes. Recorded as the verifier left it, rather than answered in its place |

The verifier's seven-failure-modes audit returned HITs on modes 1, 2, 5 and 7 — claims
without evidence, a grep that hit without proving, derived prose contradicting its own
source table, and a count presented as a total when it was a partial list. Every one of
those is the same category as the seven in the table above, which is the point: the pass
that corrected the inherited draft then reproduced four of the same failure modes itself.
The most useful thing it said was that the retraction itself is sound —
`markers` really was a wire read, the enum analysis is exact, `deviceFamily =
medicalDeviceFamily` is exact at both offsets, and the 17-of-19 `/patient/csr`
cross-check is a genuine independent validation of the counting rule.

## 11b. Correction (2026-10-14) — second verifier round, and what it cost

Round 2 reviewed `57b0288444633761b397a2f608237dec7da2f059` and returned **NOT CLEAN**
again, with five blocking findings. It **conceded one of its own round-1 findings** (the
`81,679` offset — the verifier was wrong; this document's value is the `p.` token) and
**resolved** the round-1 abstention on the gate by spending 3 of its 10 requests
(`./scripts/research-gate.sh` → GATE PASS, 84 passed / 0 failed).

That is the honest shape of two rounds: the builder was right once, wrong eight times,
and the failures moved rather than disappeared.

| # | round-2 finding | status |
|---|---|---|
| B1 | the **PR body** at the new head was stale — 34, 232, 57, and the old offsets in five evidence rows | fixed; the body is regenerated from the same counters |
| B2 | `resolved-constants.tsv` has **21** rows but was cited for 20, and "the other 19" against 20 baseUrl entries; `sites_with_literal_path` counted the constant site as a literal | fixed — the constant now has its own counter column, so **154 + 20 + 1 + 58 = 233** sums exactly, and `resolved_sites_rows` is emitted by the script |
| B3 | §7.2 still said "unresolved **57**" — the pre-fix figure | fixed → 58 |
| B4 | the ternary table listed **three** sites directly beneath the words "**Four** sites" | fixed — the fourth row (`…/patients/{id}/export/csv`, `k-5750-d7bef840102da905-js.b` byte 763, the
`http.get(a?` call) is now in the table, and the script's docstring said 3 too |
| B5 | the §2 byte convention was **violated by seven of this document's own offsets**, two of them introduced while recording the round-1 fix | fixed — every offset below now points at the start of the token it names |

**Offsets corrected in this round**, each re-measured:

| token | was | now |
|---|---|---|
| `i.markers` | 77,984 (the `=`) | **77,985** |
| `n.unfilteredEventMarkers` (LHS) | 77,962 | **77,960** |
| `"NGP"` site 1 / 2 / 3 | 76,306 / 78,361 / 83,895 | **76,305 / 78,360 / 83,894** |
| clamp ternary `W=C.value>…` | 81,366 | **81,344** |
| `n.deviceFamily=i.medicalDeviceFamily` | 74,268 | **74,266** |
| enclosing `if(` for the disturbance branch | 81,668 *(verifier's own error, carried in)* | **81,676** |

The lesson recorded here, because it recurred: **adding a number to `counters.json` is
not the same as making the prose read from it.** Round 1's fix moved the leading-slash
figure into a counter; round 2 found three figures still hand-carried — a TSV row count,
a table row count, and a stale `57` — in the same sections. Every figure in §7 is now
either read from `counters.json` or enumerated in full beside it.

**Non-blocking, also fixed:** `fp.YV` removed from §7.3 (it is not unresolved — it is
counted as shape `{1}{2}`); the "Angular internal" attribution for `SI` deleted as an
unlabelled INFERRED guess, with the reason it never resolves given instead; and the
half-open range convention for §4's statement extent, which the verifier called a genuine
improvement worth keeping.

**On the substance there is nothing further outstanding.** The verifier's own summary of
what it could not break: the retraction, the 11-token enum and its 9 handled members, the
BLE/non-BLE divergence, `deviceFamily = medicalDeviceFamily`, the 7-type nulled list, the
comma coercion, the conditional-children logic, the 42/5 casing split, the corpus identity
chain, and the 17-of-19 `/patient/csr` cross-check — all re-derived independently and all
holding.

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
