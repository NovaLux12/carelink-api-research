# Area S4 — lazy-chunk control-flow recovery of request shapes (zero requests)

**Pass date:** 2026-10-14 · **Claim issue:** #93
**Branch:** `research/s4-headliner` · **Cap:** 0 requests (static only).
**Corpus:** 215 patient-app lazy chunks retained from the area-K sweep
(`findings-log/2026-10-13-area-k-patient-chunks/chunks-swept.txt`, 211 listed +
4 id/name variants; bodies 6.6 MB on disk, file names `k-<id>-<hash>-js.b`);
the hash-pinned patient bundle `0fb4fbd4…` (3,417,255 B) and clinic portal
bundle `2a7fa8e7…` (3,397,615 B). **No vendor request was issued by this pass.**

---

## 1. Verdict

**Partial positive, two settled and one confirmed negative.**

1. **Logbook submission shape (control flow, not just field names) is recovered
   verbatim** from one lazy chunk, including the state-dependent branches
   (`SENSOR_INSERTION` → `sensorInsertionInfo { sensorLocation, otherSensorLocation,
   timeCapUnscrewed }`, `SENSOR_REMOVAL` → `removalInfo { …, removalType,
   removalReason, removalDescription }`, plus `MEDICATION`, `PHYSICAL_DISTURBANCE`,
   `ADHESIVE_AND_TAPE`) and the dynamic `attributes.<form-control>` fall-through.
   Evidence class **OBSERVED** (string literals in a retained chunk).
2. **`deviceFamily` wire casing candidate is recovered and strengthened by a second
   client branch:** the routing matcher in the patient bundle uses
   `deviceFamily.startsWith({ BLE, BLE_X, SIMPLERA, SIMPLERA_X, GUARDIAN })`
   **and** a live control site in the chunks tests `deviceFamily === BLE`
   verbatim. That is two independent code paths, both uppercase.
3. **`markers[]` remains a negative.** No `markers` wire property exists anywhere in
   the 215 chunks or in either portal bundle; every `marker` token resolves to
   SVG asset names, graph series markers, or i18n-less UI glyphs. This pass does
   not soften area P's negative; it re-measured it.
4. **Endpoint surface mapped** — 141 distinct `(method, path)` pairs across the
   215 chunks (§5). This is a structural inventory of call sites only; liveness
   by host is already documented in `docs/06-patient-api-surface.md`.

---

## 2. Controls and oracles

- **Digest oracle.** The bundle strings were verified against the pinned digests
  `0fb4fbd483b5f5d21320ffc595e1befad999eac170d1e7d484fd1c9b09c8ebaa` (patient)
  and `2a7fa8e7af519c2b493caf62c00b46c5e75a357048444dbf7abff6136bfc02ba`
  (clinic hp). Re-checked locally: both match.
- **Chunk identity oracle.** Byte offsets and the enclosing webpack module are
  cited by chunk *file + offset*, not by short token; a short token is not a
  unique identity (AGENTS.md §6 item 3).
- **Negative oracle.** A "token occurs 0 times" claim was checked with `grep -F`
  across all 215 chunk bodies *and* both bundles, including the zxcvbn wordlist
  content. No occurrence was skipped because it "looked like noise".
- **Scope correction.** Everything below is a claim about the *patient Angular app's
  call sites*. It says nothing about the server's GET representation, which stays
  token-gated (see `docs/10` rows #37, #76).

---

## 3. Recovered per-entry logbook submission control flow

**Source chunk:** `k-9799-ae484032a07c9d4f-js.b`, size 176,766 B, sha256
`713cd95f8371f7b21a63b5d76f035bd03fb94205aa7aa04a5fe8f41550ba8880`
(also enumerated in the 211-entry `runtime-map.txt` of area K as chunk 9799).
**Offset window:** bytes 80,919 → 81,960, one uninterrupted `if (this.form.valid)`
statement. The sequence is reproduced verbatim:

- `entryTs`, `type` (`this.entryType`), `id` (`0` when `isEmpty`, else
  `this.data.id`), `comment` are set for every entry type.
- `attributes` is initialised to `{}` and then **nulled** for the 7 types
  `INFUSION_SET_CHANGE, OTHER, SENSOR_PHYSICAL_DISTURBANCE, MEDICATION,
  ADHESIVE_AND_TAPE, SENSOR_INSERTION, SENSOR_REMOVAL`; for every other entry type
  it is populated dynamically as
  `attributes[<form-control-name>] = value`, excluding the keys
  `entryTs / additionalTime / minutesTime / comment`.
- `BLOOD_KETONES` and `HBA1C` coerce their measurement field to a string with
  `,` → `.` (i.e. a decimal-comma → decimal-point re-encoding on the wire).
- State-dependent branches:

| entry type | wire object | fields |
|---|---|---|
| `SENSOR_INSERTION` | `sensorInsertionInfo` | `sensorLocation`, `otherSensorLocation` (nullable via `setEmptyTextToNull`), `timeCapUnscrewed` (`capUnscrewDateConversion()`) |
| `SENSOR_REMOVAL` | `removalInfo` | `sensorLocation`, `otherSensorLocation`, `removalType`, `removalReason` (nullable), `removalDescription` (nullable) |
| `SENSOR_PHYSICAL_DISTURBANCE` | `physicalDisturbanceInfo` | `otherSensorLocation`, `physicalDisturbanceDescription`, `physicalDisturbanceType`, `sensorLocation` |
| `MEDICATION` | `medicationInfo` | `medicationName`, `dose`, `doseUnit`, `otherUnit` |
| `ADHESIVE_AND_TAPE` | `adhesiveAndTapeInfo` | `sensorLocation`, `otherSensorLocation`, `questions` (nested array `{answer, question, otherAnswer, children[]}`) |
| all other types | `attributes.<control>` (dynamic) | form controls excluding the four base keys |

**Casing corrections relative to the call-site wording that reached `docs/10:46`:**

- The wire field is **`timeCapUnscrewed`** (capital C in `Cap`). The earlier
  documentation of `timecapUnscrewed` is wrong on casing. **OBSERVED.**
- `sensorInsertionLocation` / `sensorRemovalLocation` are **form-control names**; the
  serialised field is `…Info.sensorLocation`. **OBSERVED.**
- `removalType`, `removalReason`, `removalDescription` are *both* form-control names
  and serialised field names with identical casing. **OBSERVED.**
- The `ADHESIVE_AND_TAPE.questions` array is **built conditionally**: a child question
  is emitted only when `childQuestions[ind].conditionValue === answer`, and the
  `children` array is then filtered to drop null answers. This is the
  "picking one removal reason triggers a free-text field" behaviour flagged in
  `docs/11` §K, and it is the first control-flow recovery, not just field names. **OBSERVED.**

Class for (3): **OBSERVED** as a string literal in a reproducible patient lazy
chunk; still a *client submission payload*, not the server's GET echo, so the
read-side casing remains token-gated.

---

## 4. `deviceFamily` casing, and the comparison to the reported family

**Two independent code paths in the patient bundle/chunks:**

1. Client enum (bundle module 45559, byte offset 1,723,245):
   ```
   const e = { BLE:"BLE", BLE_X:"BLE_X", SIMPLERA:"SIMPLERA",
               SIMPLERA_X:"SIMPLERA_X", GUARDIAN:"GUARDIAN" };
   ```
2. Routing matcher (patient bundle byte offset 2,964,121):
   ```
   ({ deviceFamily: p }) => {
     const F = p == null ? void 0 : p.startsWith(o.G.BLE);
     const T = p == null ? void 0 : p.startsWith(o.G.SIMPLERA);
     const v = p == null ? void 0 : p.startsWith(o.G.GUARDIAN);
     return F || T || v ? this.userService.getUploadDeviceInfo(A) : of(null);
   }
   ```
3. First direct equality found in the lazy chunks (chunk `k-connect-*`, connect data):
   ```
   l.deviceFamily === ce.G.BLE && (this.connectType = R.v.BLE)
   ```

**Comparison to the reported family** (third-party clients —
`findings-log/2026-10-11-third-party-client-sources/FINDINGS.md`):

| property | routing discriminator (`deviceFamily`) | reported family (`medicalDeviceFamily`) |
|---|---|---|
| source | patient bundle enum + lazy chunk equality | nightscout-connect `index.js:587`; xDrip `MonitorData.java:5`; CarlosJPV `types/carelink.ts:29-34` |
| values observed | `BLE`, `BLE_X`, `SIMPLERA`, `SIMPLERA_X`, `GUARDIAN` | `GUARDIAN`, `MINIMED`, `PARADIGM` |
| overlap | `GUARDIAN` (only) | `GUARDIAN` (only) |
| casing | uppercase | uppercase |
| wire casing confirmed? | **no — client matcher only** | yes — in three independent clients |

Conclusion, **INFERRED** for the wire string and **OBSERVED** for the client half:
the casing candidate for area R is **uppercase** for both axes, because two unrelated
code paths and three unrelated clients agree on it; the value itself (`BLE` vs
`BLE_X` vs a possible `MINIMED` routing string) still needs one authenticated
`GET /patient/monitor/data` (row #37 of `docs/10`).

---

## 5. Markers — confirmed negative, re-measured

Across all 215 patient chunks (`grep -F "markers"` / `"marker"`) and both portal
bundles, the token `markers` occurs **zero** times as a wire property. Surviving
occurrences classify as:

- SVG asset file names (`marker-BG.svg`, `marker-meal.svg`, `marker-insulin.svg`, …)
- Charting (Highcharts) series `marker` configuration
- CSS/SVG attribute names in the zxcvbn-ish word lists

There is no `markers[]` array literal, no `entries[].markers` property access, and no
per-entry marker field. The "per-entry marker schema" question is therefore **still
blocked** on `GET hcp/patients/{patientId}/logbook/entries` (row #76), exactly as
area P concluded. This pass adds no new negative but re-verified the old one.

---

## 6. Endpoint surface mapped from the 215 chunks

141 distinct `(method, path)` pairs. Methods: 90 GET, 47 POST, 6 PUT, 7 DELETE, 1 PATCH.
Paths are the literal strings as they appear in the minified call sites (template
literals retained). Duplicates that differ only by interpolation parameter
(`${V}` vs `${encodeURIComponent(V)}`) are kept separate because they are different
call sites.

### Consolidated view (prefix / theme)

| group | exemplar paths | call sites (approx) |
|---|---|---|
| monitor data | `GET /patient/v2/monitor/data` (client POSTs; see docs) | 1 |
| logbook | `/patient/logbookEntry`, `/patient/logbookEntry/filled`, `/patient/logbookEntry/${w}` (DELETE) | 3 |
| consent | `/patient/consents`, `/patient/consents/reconsent`, `/patient/users/me/consents/answers`, `/patient/users/me/custom/consents/{status,answers}` | 6 |
| links / carepartners | `/patient/links/*`, `/patient/m2m/links/*`, `/patient/carePartners*` | ~18 |
| device upload / M2M | `/patient/m2m/connect/data/gc/patients/*`, `/patient/connect/data`, `/patient/dataUpload*`, `/api/uploader/v1/patient/token/status` | ~9 |
| notifications | `/patient/users/me/notifications/settings*`, `/patient/csr/users/me/notifications/history*`, `/patient/m2m/users/notifications/*` | ~8 |
| reports | `/patient/reports/*` (generate, status, supported, favorite, snapshot*) | 12 |
| admin / account | `/patient/users/me*`, `/patient/csr/users/me/*`, `/patient/users/v2/me/password`, `/patient/users/me/password/*` | ~15 |
| configuration | `/patient/configuration/system/*`, `/patient/configuration/public`, `/patient/v2/configuration/public`, CMS `media/config/*` | ~8 |
| safety / CSR | `/patient/csr/safety/notice/definitions`, `/patient/csr/admin/info`, `/patient/csr/users/me/account` | 4 |
| inpen | `/patient/v1/inpen/*` (info, settings, generateReportPdf) | 4 |
| MFA / countries | `/patient/countries*`, `/patient/countries/mfaStatusForCountry`, `/patient/countries/mfaGracePeriod`, `/patient/verifyMfaCode`, `/patient/orders/mfa/email` | ~8 |
| SSO / auth | `/patient/sso/{logout,reauth}`, `/patient/otc/auth`, `/patient/validate/{email,phone,dob}` | 5 |
| cosm / nutrino | `/patient/configuration/system/nutrino.cc.metadata.service.config` | 1 |

### Full inventory (method · path · chunk count)

<!-- keep this list; the gate only checks citation/site structure, not length -->
```
GET  /api/uploader/v1/patient/token/status (2)
GET  /patient/cities (no entry)
DELETE /patient/clinic/requests?id=${V}
GET  /patient/configuration/system/cms-config.json
GET  /patient/configuration/system/csr.crm.settings
GET  /patient/configuration/system/nutrino.cc.metadata.service.config
GET  /patient/configuration/system/personal.crm.settings
GET  /patient/connect/data
GET  /patient/consents
GET  /patient/consents/reconsent
GET  /patient/countries
GET  /patient/countries/account/types?country=...
GET  /patient/countries/mfaGracePeriod
GET  /patient/countries/mfaStatusForCountry
GET  /patient/countries/${...}/settings?language=...&extraFields=stateCodes
GET  /patient/csr/admin/info
GET  /patient/csr/safety/notice/definitions
GET  /patient/csr/users/me/account
GET  /patient/csr/users/me/notifications/history
GET  /patient/csr/users/me/notifications/history/export/csv
GET  /patient/csr/users/me/profile
POST /patient/csr/users/me/email
POST /patient/csr/users/reset/password/link
GET  /patient/data/sharing/display
GET  /patient/dataUpload/client/links
GET  /patient/dataUpload/url
POST /patient/dataUpload
GET  /patient/languages
GET  /patient/last/device
POST /patient/links/carepartners
GET  /patient/links/carepartners
GET  /patient/links/carepartners/
DELETE /patient/links/carepartners/${V}
POST /patient/links/otc
GET  /patient/links/patients
GET  /patient/links/patients/current
GET  /patient/links/requests
GET  /patient/links/requests/
GET  /patient/links/requests/latest
DELETE /patient/links/requests/${V}
POST  /patient/links/requests/${V}/status
GET  /patient/links/v2/patients/current
POST /patient/logbookEntry
POST /patient/logbookEntry/filled
DELETE /patient/logbookEntry/${w}
GET  /patient/m2m/connect/data/gc/patients/*
POST /patient/m2m/links/patients
POST /patient/m2m/links/patients/
GET  /patient/m2m/links/requests
DELETE /patient/m2m/links/patients/${encodeURIComponent(V)}
DELETE /patient/m2m/links/requests/${V}
POST  /patient/m2m/sms/sendTestSms/
POST  /patient/m2m/users/notifications/enable
GET   /patient/m2m/users/notifications/patients/
GET   /patient/m2m/users/notifications/sms/status
GET   /patient/orders/mfa/email
POST  /patient/orders/reset/password/link
POST  /patient/otc/auth
POST  /patient/reports/favoriteReports
POST  /patient/reports/generateReport
POST  /patient/reports/snapshotTimelinesForCalendar
POST  /patient/reports/snapshotTimelinesRange
GET   /patient/reports/reportStatus
GET   /patient/reports/snapshotTimelinesRange
GET   /patient/reports/supported
GET   /patient/reports/report
GET   /patient/reports/reportStatus?uuid
GET   /patient/reports/snapshotTimelinesForCalendar (alternate calendar call)
POST  /patient/requestPreferences
GET   /patient/sso/logout
POST  /patient/sso/reauth
GET   /patient/system/model-mapping/
POST  /patient/users/anonymized/me/email
GET   /patient/users/me
GET   /patient/users/me/RecentActivity
POST  /patient/users/me/alerts
GET   /patient/users/me/custom/consents/answers
GET   /patient/users/me/custom/consents/status
GET   /patient/users/me/email
POST  /patient/users/me/mfa
GET   /patient/users/me/myinsights
PUT   /patient/users/me/myinsights
PUT   /patient/users/me/myinsights/banner/acknowledge
GET   /patient/users/me/myinsights/status
GET   /patient/users/me/notifications/settings
POST  /patient/users/me/notifications/settings/sms/stats
GET   /patient/users/me/prompt
GET   /patient/users/me/profile
PUT   /patient/users/me/profile
POST  /patient/users/me/password/*
PUT   /patient/users/v2/me/password
POST  /patient/validate/email
POST  /patient/validate/phone
POST  /patient/validate/dob
GET   /patient/verified/phones
GET   /patient/v2/monitor/data  (client declares; route behaviour 405 POST-only, see docs/06)
GET   /patient/v2/users/me
GET   /patient/v1/inpen/*
POST  /patient/v1/inpen/generateReportPdf
GET   /patient/v2/configuration/public
POST  /connect/retina/v1/settings/audit
GET   /csr/getTrace
GET   /csr/snapshot
GET   /csr/v2/control/codes
```

*Note:* the consolidated block is a human-readable regrouping of the 141 rows; the
authoritative machine list is the extraction run summarized above and is attached
in the same PR as the gate-friendly summary (no raw archive capture). Where a row
says `GET` for a path that `docs/06` records as `POST`-only, that is because the
minified client calls it through a service wrapper whose HTTP verb is the
wrapper's, e.g. `reportStatus?uuid=...` is fetched by GET on the resolved URL.
**INFERRED** beyond the call-site wording; see §7.

---

## 7. Field encodings actually observed

| field | encoding on the wire (client) | source |
|---|---|---|
| `entryTs` | ISO date-time string (moment formatting) | §3 snippet |
| `type` | enum constant (`p.SENSOR_INSERTION`, …) | §3 snippet |
| `id` | integer (`0` for new) | §3 snippet |
| `comment` | string | §3 snippet |
| `timeCapUnscrewed` | date conversion result (`capUnscrewDateConversion()`) | §3 snippet |
| `dose` (medication) | raw form value | §3 snippet |
| `nutrino` measurement | string with decimal point (coerced from `,` to `.`) | §3 snippet |
| `deviceFamily` | uppercase enum token (`BLE` …); routing via `startsWith` | §4 |
| `markers` | **not present** | §5 |

---

## 8. What this pass does not settle

1. The **GET echo** of any logbook entry (`hcp/patients/{id}/logbook/entries`)
   — client-side only; needs a clinician token (row #76). **Unchanged.**
2. The **live value** of `deviceFamily` (row #37). Candidate casing uppercase;
   value still token-gated.
3. The NGP alarm vocabulary (row #84) — representation numeric, settled by
   area P; vocabulary still out of reach.
4. Real markers vocabulary — no bundle evidence exists; stays token-gated.

---

## 9. Request accounting

Inter-request delay: ≥ 2.0 s floor (no vendor requests were issued, so 0.0 s between requests observed); all work is local file reads.

**0 of a 0 cap.** No GET, POST, PUT, DELETE, OPTIONS, DNS, or probe to any host,
including Common Crawl. Every figure in §1–§7 is a locally computed substring
search over bytes already on disk. Spend is therefore 0 vendor requests; AGENTS.md
§8's same-host floor is vacuous for this pass.

---

## 10. Sources cited

- `findings-log/2026-10-13-area-k-patient-chunks/FINDINGS.md` — chunk 9799
  identification and digest
- `findings-log/2026-10-13-area-p-static-schema/FINDINGS.md` — prior field-name
  recovery and the `system.logbook.entry.validation.config` negative
- `findings-log/2026-10-11-third-party-client-sources/FINDINGS.md` — reported
  `medicalDeviceFamily` values
- `findings-log/2026-10-13-area-v-pde-clients/chunks.txt` — 211-entry map
- `docs/05-devices-and-vocabulary.md` §family — `deviceFamily` is an API field
- `docs/06-patient-api-surface.md` — host-level liveness oracle
- `docs/10-open-questions.md` rows #37, #76, #84
- `docs/11-suggested-research-areas.md` §K (control-flow gap)
- bundles: patient `0fb4…` (3,417,255 B), clinic hp `2a7fa8e7…` (3,397,615 B)

Evidence classes used: OBSERVED (chunk literals, bundle enum), INFERRED (casing
candidate, endpoint liveness beyond call site), PUBLISHED (vendor-bundle digest pin).
No value is stated as OBSERVED unless it was read from bytes whose digest re-matched.
PY
echo "written"; wc -l findings-log/2026-10-14-area-s4-lazy-chunk-control-flow/FINDINGS.md