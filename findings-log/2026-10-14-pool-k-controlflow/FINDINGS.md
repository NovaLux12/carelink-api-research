# Pool K — control-flow request schema recovery (static, 0 vendor requests)

**Date:** 2026-10-14
**Claim issue:** #103 — "pool lane K control-flow request schema recovery (static, 0 requests)"
**Area:** K proper, successor residual of `docs/11-suggested-research-areas.md` §K
("control-flow mining of the call-sites and the state-dependent shape of
`system.logbook.entry.validation.config`").
**Verdict:** **Partial positive, no requests.** The shipped client corpus (patient
bundle `0fb4fbd4…` 3,417,255 B and its 211 lazy chunks) already contains both
halves of the requested artefact: (a) the client-side call sites and their HTTP
request shapes, and (b) the state-dependent write-side logbook entry payload,
including the conditional field construction that depends on `entryType`. Verified
byte-for-byte against bundle digests. The *read-side* echo shape
(`GET /patient/logbookEntry`) and the *schema* of
`system.logbook.entry.validation.config` remain token-gated, consistent with the
area-P boundary and the surviving `docs/10` open question.

**Tooling (read-only):** `grep` 3.12, Python 3.14.8, `sha256sum` 0.10.0,
`git` 2.53.0. Analysis performed against client chunk bodies retained locally;
no vendor GET/OPTIONS/POST, no token exchange, no authentication. **Requests used:
0 of a 0 cap.** Inter-request delay: no vendor requests were made, so the ≥2 s
same-host floor of `AGENTS.md` §8 is vacuous for this static pass.

## 1. Corpus used and the digest oracle

| Bundle | Size (B) | sha256 | Role |
|---|---|---|---|
| patient main (`k-main.b`) | 3,417,255 | `0fb4fbd483b5f5d21320ffc595e1befad999eac170d1e7d484fd1c9b09c8ebaa` | carries `logbookService` call sites and URL builders |
| lazy chunk `k-9799-ae484032a07c9d4f-js.b` | 176,766 | `713cd95f8371f7b21a63b5d76f035bd03fb94205aa7aa04a5fe8f41550ba8880` | builds the per-entry write payload conditionally on `entryType` |

These are the same digests pinned by
`findings-log/2026-10-13-area-p-static-schema/FINDINGS.md` §1; they re-match on
this pass (no new digest pin is introduced, so no new oracle is claimed).

## 2. Call-site request shapes (patient corpus)

Source: `k-main.b`, bytes **2,999,785–3,000,295** (offsets 0-based). The call
sites are concentrated in one consecutive run of the minified `logbookService`
implementation:

```
/patient/logbookEntry/filled?from=${from}&to=${to}&zoneOffset=${zoneOffset}
/patient/logbookEntry?from=${from}&to=${to}&start=${start}&zoneOffset=${zoneOffset}[&type=${type}…]
http.post("patient/logbookEntry", w)
http.put("patient/logbookEntry", w)
http.delete("patient/logbookEntry/${id}")
/patient/logbookEntry/last?date=${date}&type=${type}&zoneOffset=${zoneOffset}
```

Recovered request shapes (OBSERVED from the same bytes):

| Method | Path / template | Body | Notes |
|---|---|---|---|
| GET | `/patient/logbookEntry/filled?from=&to=&zoneOffset=` | none | filled-day range read |
| GET | `/patient/logbookEntry?from=&to=&start=&zoneOffset=[&type=]` | none | paginated list; `type` is a repeated query parameter (`&type=${A}` per element of the passed array) |
| POST | `/patient/logbookEntry` | the `result` object built in §3 | `addEntry(w)` passes `w` straight to `http.post` without reshaping |
| PUT | `/patient/logbookEntry` | the same `result` object | `editEntry(w)` passes `w` straight to `http.put` |
| DELETE | `/patient/logbookEntry/${id}` | none | `deleteEntry(w)` interpolates the passed value (the entry's `id`) into the path |
| GET | `/patient/logbookEntry/last?date=&type=&zoneOffset=` | none | last-entry read for a date + entry type |

Offsets in `k-main.b`:
- `logbookEntry` literal block begins at **2,999,785**;
- `addEntry(w)` POST literal at **3,000,146**;
- `editEntry(w)` PUT literal at **3,000,207**;
- `deleteEntry(w)` DELETE template at **3,000,269**;
- preceding GET builders end at **3,000,145** (the index immediately before `http.post`,
  which starts at byte 3,000,146).

Evidence class: **OBSERVED** — string literals in a reproducible, digest-pinned
bundle, compared against the same literals already reported by the 2026-10-08
recon pass (`findings-log/probe-2026-10-08/recon/JS-API-SURFACE.md` §7.8) and
the per-key sweep (area E, area W per-key projection, `docs/04-configuration.md`).
No live request was sent.

## 3. State-dependent write payload (client submission shape)

Source: lazy chunk `k-9799-ae484032a07c9d4f-js.b`, bytes **80,914–84,074**
(0-based). The construction is gated on `this.form.valid` and branches on
`entryType`:

```js
if (this.form.valid) {
  this.result = { entryTs: o, type: this.entryType, id: this.isEmpty ? 0 : this.data.id };
  this.result.comment = this.form.controls.comment.value;
  this.result.attributes = {};
  // for these 7 types attributes is reported as null; otherwise every form
  // control (except entryTs / additionalTime / minutesTime / comment) is
  // copied verbatim into attributes[control-name].
  [INFUSION_SET_CHANGE, OTHER, SENSOR_PHYSICAL_DISTURBANCE, MEDICATION,
   ADHESIVE_AND_TAPE, SENSOR_INSERTION, SENSOR_REMOVAL].includes(this.result.type)
    ? this.result.attributes = null
    : Object.keys(this.form.controls).forEach(h => {
        ["entryTs","additionalTime","minutesTime","comment"].includes(h) ||
        this.result.attributes && (this.result.attributes[h] = this.form.controls[h].value);
      });
  // HbA1c / blood-ketone coerce a single attribute field's decimal comma → dot.
  [BLOOD_KETONES, HBA1C].includes(this.entryType) && { ... }
  // type-specific nested objects are added ONLY for their own type:
  SENSOR_PHYSICAL_DISTURBANCE -> physicalDisturbanceInfo
  MEDICATION -> medicationInfo
  SENSOR_INSERTION -> sensorInsertionInfo { sensorLocation, otherSensorLocation, timeCapUnscrewed }
  SENSOR_REMOVAL -> removalInfo { sensorLocation, otherSensorLocation, removalType, removalReason, removalDescription }
  ADHESIVE_AND_TAPE -> adhesiveAndTapeInfo { sensorLocation, otherSensorLocation, questions[] }
  this.entChanged.emit(this.result);
}
```

Recovered wire fields, by entry type (already recorded in area P §3; re-anchored
here to its submission call site):

| Baseline (all types) | `entryTs`, `type`, `id`, `comment`, plus `attributes` when non-typed |
|---|---|
| typed entries (INFUSION_SET_CHANGE, OTHER, and the 5 named below) | `attributes = null` — the nested object carries the data instead of the generic `attributes` bag |
| SENSOR_INSERTION | `sensorInsertionInfo.sensorLocation`, `.otherSensorLocation`, `.timeCapUnscrewed` |
| SENSOR_REMOVAL | `removalInfo.sensorLocation`, `.otherSensorLocation`, `.removalType`, `.removalReason`, `.removalDescription` |
| SENSOR_PHYSICAL_DISTURBANCE | `physicalDisturbanceInfo.otherSensorLocation`, `.physicalDisturbanceDescription`, `.physicalDisturbanceType`, `.sensorLocation` |
| MEDICATION | `medicationInfo.medicationName`, `.dose`, `.doseUnit`, `.otherUnit` |
| ADHESIVE_AND_TAPE | `adhesiveAndTapeInfo.sensorLocation`, `.otherSensorLocation`, `.questions[]` (each: `answer`, `question`, `otherAnswer`, `children[]`) |

Two casing corrections to the names `docs/10` row 46 assumed (from the same
chunk, already recorded by area P, re-anchored here as the submission payload
rather than the published schema): `timecapUnscrewed` → **`timeCapUnscrewed`**,
and `sensorInsertionLocation` is a *form control* name whose serialized field is
`sensorInsertionInfo.sensorLocation` (same for removal).

Evidence class: **OBSERVED** — string literals and control flow in a reproducible
patient lazy chunk, digest pinned above, compared verbatim against the
transcription in
`findings-log/2026-10-13-area-p-static-schema/FINDINGS.md` §3.

## 4. Control-flow points genuinely recovered

The point of this pass, as distinct from area P's field-name recovery, is that
the control flow of construction is knowable from these bytes:

1. **Write side is conditional on type, but the HTTP body is one shape.**
   `addEntry(w)` / `editEntry(w)` receive whatever `w = this.result` evaluates
   to, and POST/PUT it verbatim (`http.post("patient/logbookEntry", w)`). The
   server therefore sees *either* a generic `attributes` bag *or* a
   type-specific nested object, never both, because `attributes` is set to
   `null` before the type-specific object is added. The two are mutually
   exclusive on the wire.
2. **`id` distinguishes create vs. update on the client.** `id: this.isEmpty
   ? 0 : this.data.id`, with `editEntry` PUT for the populated case and
   `addEntry` POST at this site receiving the same object. The verb, not `id`, is
   what the client uses to distinguish create (POST) from update (PUT).
3. **DELETE carries no body** — the entry's id travels in the path.
4. **Read side is query-shaped, not body-shaped** — `from`, `to`, `start`,
   `zoneOffset`, and repeated `type` query parameters; `filled` (day range) and
   `last` (date + type + zone offset) are separate templates.

## 5. What remains token-gated (negative, documented)

- **Read-side echo casing** — `GET /patient/logbookEntry` with a clinician or
  patient token is still required to confirm the server's returned shape casing
  (`timeCapUnscrewed` vs. `timecapUnscrewed`, `sensorLocation` vs.
  `sensorInsertionLocation`). The client-side write shape recorded here does not
  establish the server's echo shape.
- **`system.logbook.entry.validation.config` field set** — still only a route
  literal in the clinic bundle (`/hcp/configuration/public/` form), and
  `null`/404 on the unauthenticated projection. Area P §4 documents the
  negative; this pass does not change it. No call site in the corpus reads
  `config` beyond resolving the key (offset 2,190,314 in the patient bundle:
  `D.logbookConfiguration = "system.logbook.entry.validation.config"`, selector
  `yt` at byte 96,846).
- **Whether `entryTs` is submitted in the server's timezone or the client's
  local offset string** is observable in the builder (`zoneOffset` encoding in
  the read URLs) but the timezone conversion is not pinned by this pass.

## 6. Safe successor

Per the successor block on claim issue #103, the next owner task is:

- **L positive control (0–2 GETs)** — a host known present in each crawl returns
  200 for its query shape. This is the acknowledged blocker; 0–2 GETs, no POST.
  Owner decision for scope/identity; documented in
  `docs/11-suggested-research-areas.md` §L.

Additional, non-blocking follow-ups (no vendor requests until a token exists):
  unauthenticated cannot settle them; record as `docs/10` row 46 remainders.

## 7. Request accounting

- **Vendor health-surface requests: 0** (no GET, OPTIONS, POST, DNS, probe).
- **Local reads only:** two bundle files (digests re-verified above) and their
  byte offsets. Re-verifying the digests required reading the files; no network.
- Cap on issue #103 ("0 requests, GET only not needed") — not exceeded; trivially
  met.

## Evidence map

| Claim | Class | Source |
|---|---|---|
| `addEntry` POSTs `patient/logbookEntry` with the built `result` | OBSERVED | this log §2; `k-main.b` (sha256 `0fb4fbd4…`) byte 3,000,146 |
| `editEntry` PUTs the same path/body | OBSERVED | this log §2; `k-main.b` byte 3,000,207 |
| `deleteEntry` deletes `patient/logbookEntry/{id}` with no body | OBSERVED | this log §2; `k-main.b` byte 3,000,269 |
| GET read shapes (`filled`, paginated list incl. repeated `type`, `last`) | OBSERVED | this log §2; `k-main.b` bytes 2,999,785–3,000,145 |
| State-dependent write payload field names/casing | OBSERVED | this log §3; `k-9799-ae484032a07c9d4f-js.b` (sha256 `713cd95f…`) bytes 80,914–84,074 |
| Mutual exclusivity of `attributes` vs. nested type object | INFERRED (derived from the conditional construction in §3) | the chunk itself says `attributes = null` for typed entries and only afterwards adds the nested object; bytes 80,926–81,010 |
| `timecapUnscrewed` → `timeCapUnscrewed` casing | OBSERVED (literal `timeCapUnscrewed` in the client serializer) | `k-9799-ae484032a07c9d4f-js.b` byte 82,579 |
| Read-side echo casing / validation-config schema | INFERRED-as-remaining-negative (no evidence either way) | no read-side data in the corpus |
| Service uses the verb (not `id`) to distinguish create vs. update | INFERRED (from `id: this.isEmpty ? 0 : this.data.id` plus distinct POST/PUT call sites) | `k-9799…` bytes 80,926–80,945 and `k-main.b` bytes 3,000,146–3,000,206 |
