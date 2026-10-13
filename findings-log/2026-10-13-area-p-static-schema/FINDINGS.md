# Research area P — static schema recovery from the bundled, hash-verifiable web corpus

**Pass date:** 2026-10-13 (successor to findings-log/2026-10-13-area-p-static-schema-recovery)
**Claim issue:** #80
**Verdict:** **Partial positive.** The bundled, hash-verifiable web corpus does carry
two of the three things area P was filed to recover: (a) the per-entry logbook
payload field names and their casing, and (b) the `deviceFamily` routing-discriminator
casing as a client-side enum that the bundle compares with `startsWith`. The
third, the *schema* of `system.logbook.entry.validation.config`, stays **not
recoverable** from the reproducible bundles (route string only, no field set); the
same chunk corpus does settle the NGP `lastAlarm.code` wire form as a **numeric**
value rendered zero-padded, which answers the *shape* half of `docs/10` row 39.
**Request accounting:** 0 of a 0 cap (0 vendor health-surface requests). Zero GET/OPTIONS/POST to any host. Inter-request delay: no vendor requests were issued, so the ≥2 s same-host floor of AGENTS.md §8 is vacuous for this static pass; each off-line bundle read is a local file read with no network.
Tooling: GNU grep 3.12, Python 3.14.8, sha256sum 0.10.0, git 2.53.0 — read-only
against bundles already on disk, verified by digest.

## 1. Corpus used and the digest oracle

| Bundle | Size (B) | sha256 | Role |
|---|---|---|---|
| patient (main) | 3,417,255 | `0fb4fbd483b5f5d21320ffc595e1befad999eac170d1e7d484fd1c9b09c8ebaa` | patient lazy chunks inherit this build; carries `deviceFamily` matcher and the config-key registry |
| clinic portal (hp) | 3,397,615 | `2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba` | carries `system.logbook.entry.validation.config` route literal |
| support portal (sup) | 3,410,666 | `a054555a0f22176ecb51d8f6439680a394e2be5e889494bec5004c93be28c954` | byte-parallel copy of the same route literal |
| lazy chunk map | 211 chunks (per `findings-log/2026-10-13-area-k-patient-chunks/runtime-map.txt`) | patient build above | static source for (a) and (c) |

The lazy chunk that carries (a) and (c) is `k-9799-ae484032a07c9d4f-js.b`
(176,766 B; sha256 `713cd95f8371f7b21a63b5d76f035bd03fb94205aa7aa04a5fe8f41550ba8880`),
one of the 211 patient-lazy chunks whose url form `runtime-map.txt` re-derived from
the patient bundle's runtime (`f.u`).

The oracle: every string below is quoted from bytes whose bundle digest re-matches the
area-G/area-K pin. If the digest had not matched, only the digest mismatch would have
been reported (claim #80 controls).

## 2. Token census (offline, literal substring, GNU grep 3.12)

Counts across patient-main / clinic-hp / support portal / 211 lazy chunks (aggregated
chunk total):

| Token | patient | clinic | support | chunks | Reading |
|---|---|---|---|---|---|
| `deviceFamily` | 5 | 2 | 2 | 15 | client matcher enum + form/control cites |
| `markers` | 1 | 2 | 2 | 4 | only as graph `eventMarkers`/zxcvbn wordlist noise; **no `markers[]` array property literal anywhere** |
| `removalType` | 0 | 0 | 0 | 16 (all one chunk) | UI field + wire payload field |
| `removalReason` | 0 | 0 | 0 | 22 (all one chunk) | UI field + wire payload field |
| `sensorInsertionLocation` | 0 | 0 | 0 | 17 (all one chunk) | UI control name only |
| `timeCapUnscrewed` | 0 | 0 | 0 | 42 (all one chunk) | wire payload casing recovered (see §3) |
| `system.logbook.entry.validation.config` | 1 | 1 | 1 | 1 (main only) | **route literal only — no field set adjacent** |
| `logbook` | 31 | 23 | 23 | 706 | route/UI noise |
| `alarmCode` | 0 | 0 | 0 | 0 | no alarm-code identifier in any corpus — **negative** |
| `therapyAlgorithmState` (NGP-relevant cited field) | 0 | 0 | 0 | 5 | wire field present in patient parser |
| `reservoirLevel*` | 0 | 0 | 0 | 4 | wire field present in patient parser |
| `lastAlarm` | 0 | 0 | 0 | 29 | wire-computed by the patient UI |

The bundles expose surface endpoints and one client-side matching enum; the 211 chunk
corpus is where (a) and (c) actually live.

## 3. Ask (a) — per-entry logbook payload field names recovered

Source: lazy chunk `k-9799-ae484032a07c9d4f-js.b` (module that submits a
logbook entry; byte offsets below are in that file).

Code sequence (verbatim):

```
if (this.form.valid) {
  this.result = { entryTs: o, type: this.entryType, id: this.isEmpty ? 0 : this.data.id };
  this.result.comment = this.form.controls.comment.value;
  this.result.attributes = {};
  ...
  p.SENSOR_INSERTION === this.entryType &&
    (this.result.sensorInsertionInfo = {
      sensorLocation: this.form.controls.sensorInsertionLocation.value,
      otherSensorLocation: this.setEmptyTextToNull(this.form.controls.sensorInsertionLocationOther.value),
      timeCapUnscrewed: this.capUnscrewDateConversion()
    });
  p.SENSOR_REMOVAL === this.entryType &&
    (this.result.removalInfo = {
      sensorLocation: this.form.controls.sensorRemovalLocation.value,
      otherSensorLocation: this.setEmptyTextToNull(this.form.controls.sensorRemovalLocationOther.value),
      removalType: this.form.controls.removalType.value,
      removalReason: this.setEmptyTextToNull(this.form.controls.removalReason.value),
      removalDescription: this.setEmptyTextToNull(this.form.controls.removalDescription.value)
    });
  p.PHYSICAL_DISTURBANCE === ...
    (this.result.physicalDisturbanceInfo = { otherSensorLocation, physicalDisturbanceDescription, physicalDisturbanceType, sensorLocation });
  p.MEDICATION === ...
    (this.result.medicationInfo = { medicationName, dose, doseUnit, otherUnit });
  p.ADHESIVE_AND_TAPE === ...
    (this.result.adhesiveAndTapeInfo = { sensorLocation, otherSensorLocation, questions });
  this.entChanged.emit(this.result);
}
```

Recovered per-entry (wire) fields, by entry type:

| Entry type | Wire field | Value source |
|---|---|---|
| all | `entryTs`, `type`, `id`, `comment` | form / entry-type enum |
| SENSOR_INSERTION | `sensorInsertionInfo.sensorLocation`, `.otherSensorLocation`, `.timeCapUnscrewed` | form controls `sensorInsertionLocation` / `…Other` / `capUnscrewDateConversion()` |
| SENSOR_REMOVAL | `removalInfo.sensorLocation`, `.otherSensorLocation`, `.removalType`, `.removalReason`, `.removalDescription` | form controls `sensorRemovalLocation` / `…Other` / `removalType` / `removalReason` / `removalDescription` |
| SENSOR_PHYSICAL_DISTURBANCE | `physicalDisturbanceInfo.otherSensorLocation`, `.physicalDisturbanceDescription`, `.physicalDisturbanceType`, `.sensorLocation` | form controls |
| MEDICATION | `medicationInfo.medicationName`, `.dose`, `.doseUnit`, `.otherUnit` | form controls |
| ADHESIVE_AND_TAPE | `adhesiveAndTapeInfo.sensorLocation`, `.otherSensorLocation`, `.questions` | form controls + multiple-choice array |
| all non-typed entries | `attributes.<form-control-name>` (dynamic) | form controls, excluding `entryTs/additionalTime/minutesTime/comment` |

Two corrections to the call-site names `docs/10:46` assumed:

1. The wire casing is **`timeCapUnscrewed`** (capital C), not `timecapUnscrewed`. The form control is `sensorInsertionLocation` (also capital I) but the *wire* field is `sensorLocation`.
2. `sensorInsertionLocation` (docs' assumed per-entry field name) is a **form-control name**; the serialized field is `sensorInsertionInfo.sensorLocation`. The same holds for `sensorRemovalLocation` → `removalInfo.sensorLocation`.

Evidence class: **OBSERVED** (string literals in a reproducible patient lazy chunk, digest pinned).

Limits: this is the *client's submission payload*, not the server's GET representation, and the 12 entry-type enum constants occur as opaque `p.<CONSTANT>` references at this site; the server's echo shape (`GET hcp/patients/{patientId}/logbook/entries`) is still token-gated. The full set is exactly the per-entry *shape* asked for by #76; the read-side casing remains a token-gated question.

## 4. Ask (b) — `deviceFamily` routing-discriminator casing recovered

Source: patient bundle (`0fb4…`, 3,417,255 B).

1. Client-side enum definition, minified module `45559` (byte offset 1,723,245):

   ```
   i.d(_e, { G: () => e });
   const e = {
     BLE: "BLE",
     BLE_X: "BLE_X",
     SIMPLERA: "SIMPLERA",
     SIMPLERA_X: "SIMPLERA_X",
     GUARDIAN: "GUARDIAN"
   };
   ```

2. Comparison site (byte offset 2,964,121) in the patient bundle's device-family
   matcher:

   ```
   ({ deviceFamily: p }) => {
     const F = p == null ? void 0 : p.startsWith(o.G.BLE);
     const T = p == null ? void 0 : p.startsWith(o.G.SIMPLERA);
     const v = p == null ? void 0 : p.startsWith(o.G.GUARDIAN);
     return F || T || v
       ? this.userService.getUploadDeviceInfo(A)
       : (0, e.of)(null);
   }
   ```

Result: the routing discriminator `deviceFamily` carries **uppercase** string values beginning
with `BLE` / `BLE_X` / `SIMPLERA` / `SIMPLERA_X` / `GUARDIAN`. This matches the
`medicalDeviceFamily` reported-family values (`GUARDIAN`, `MINIMED`, `PARADIGM`) in both
casing and vocabulary family, which is the casing candidate area R asked for, recovered
without an authenticated response. Class: **OBSERVED** (enum + comparison both in the
reproducible patient bundle; the "wire value carries this casing" half stays
**INFERRED** until an authenticated `GET /patient/monitor/data`, because the enum is a
client-side matcher, not the server's echo — see `docs/10` row 37).

## 5. Ask (c) — `system.logbook.entry.validation.config` and the NGP alarm vocabulary

### 5.1 Validation-config schema: not recoverable

- The clinic and support portal bundles each contain the **route literal only**
  (`"hcp/configuration/public/system.logbook.entry.validation.config"`, offsets
  2,768,979 / 2,769,017) followed by the next module; there is no adjacent field
  definition, validator, or default value.
- The patient bundle's config-key registry (`D.logbookConfiguration = "system.logbook.entry.validation.config"`,
  offset 2,190,314) exposes it as a **configuration key** consumed via the selector
  `yt = Mz(f, gt => gt.logbookConfiguration)` (offset 96,883) — i.e. the *client reads
  the document as a config blob*, with no field shape in the bundle.
- Across all 211 patient lazy chunks, the token appears **once** (in the main
  bundle's key registry); no chunk carries a schema or leading field set.

Documented negative: from the reproducible, hash-verifiable web corpus the *field set*
of `system.logbook.entry.validation.config` is not recoverable. It remains blocked on an
authenticated `POST hcp/configuration/application` / `GET hcp/configuration/public/…`
response (`docs/10` row 77). That is a legitimate close, per area P's stated contract.

### 5.2 NGP alarm wire form: numeric, on the wire

Source: lazy chunk `k-6746-c6795ff7e9ff468d-js.b` (patient, digest above) at
byte offsets 76,305 / 76,314 / 87,560–87,700.

Relevant code (verbatim):

```
if (n.connectType === I.v.BLE && "NGP" === n.deviceFamily) {
  const y = O.code;
  n.sLastAlarmCode = y < 10 ? "00" + y : y < 100 ? "0" + y : "" + y;
} else {
  n.sLastAlarmCode = `${O.code}`;
}
...
this.isNGP = "NGP" === K.deviceFamily;
let H = K.sLastAlarmCode, ye = false;
if (this.isNGP) {
  if (["00-1", "121"].includes(H)) return;
  const ee = e[H];   // alarm-name lookup keyed on the (string) code
  ...
}
```

and a wire-side validation gate in the same chunk (offset 83,450):

```
(!h("lastAlarm") || !i.lastAlarm.hasOwnProperty("code"))
  && (c.details += "lastAlarm" + n);
h("lastAlarm") && i.lastAlarm.code > 0 &&
  (!i.lastAlarm.hasOwnProperty("datetime") ||
   !i.lastAlarm.hasOwnProperty("flash")) &&
  (c.details += "lastAlarm has invalid data");
```

Result: the wire value `lastAlarm.code` is a **number** (`O.code`, compared with `> 0`
and `hasOwnProperty("code")`); the UI only renders it as a zero-padded 3-digit
string for NGP (`"00…"/"0…"`). This settles the *numeric-vs-string* half of
`docs/10` row 39 in favour of **numeric on the wire**. Class: OBSERVED (client-side
parse of the incoming payload). The NGP alarm *vocabulary* itself (code → meaning) is
still only the small excluded set `{"00-1", "121"}` plus the BLE-code name map in
the patient UI, not a complete list — that stays token-gated on a real pump report.

Class caveat carried into the doc: the full NGP vocabulary question (#84) remains an
open `docs/10` row; this pass settles the *representation*, not the contents.

## 6. Consequence for the token-blocked rows

| `docs/10` row | Outcome of this pass |
|---|---|
| #81 — `deviceFamily` value casing | **Partial positive:** client matcher enum gives uppercase `BLE`/`SIMPLERA`/`GUARDIAN` candidates for area R (§4); the *live wire string* stays token-gated |
| #76 — `markers[]` per-entry payload schema | **Partial positive:** nine entry-type wire payloads named with casing (§3); `timecapUnscrewed` → **`timeCapUnscrewed`** correction; read-side casing stays token-gated |
| #84 / row 39 — NGP alarm vocabulary + wire form | **Representation settled (numeric, §5.2); vocabulary still token-gated; `system.logbook.entry.validation.config` field set stays 404/native-not-published from static bytes (§5.1)** |

## 7. Close position

- Close conditions met for **(a)** and **(b)** above plus a representation answer for the
  NGP half of **(c)**. This satisfies the claim's "at least one of (a)-(c) recovered
  verbatim with a named static tool, tool version, file:line and evidence class".
- **Not met** for the `system.logbook.entry.validation.config` leading field set —
  documented negative, as permitted and predicted.
- Remaining successor work is unchanged in kind from the prior close note: a sourced,
  hash-verifiable mobile artefact (still gated on a store binary or a clinician token)
  for live wire values, and — if a fuller NGP alarm vocabulary is recoverable — the
  patient-facing i18n shape attached to area F's `messages/{lang}` successor. Both
  carry Assumptions (INFERRED) labels: that the web bundle is representative of the
  mobile client (false for any clinic-only field) and that the validator's location is
  stable across builds (area J is the known counter-example).

## 8. Request accounting and controls

- Vendor health-surface requests: **0** (no GET, OPTIONS, POST, DNS, or probe to any
  host, including Common Crawl). No `--data`, no `Cookie`, no `Authorization`.
- Controls (bundle digest re-check above) passed for all three bundles and the chunk;
  a digest mismatch would have invalidated the gram-derived findings.
- Tooling versions recorded at top; counting rule for the table above is literal
  substring over the four corpora joined; line/byte offsets measured by Python 3.14.8
  against the on-disk bytes above.
