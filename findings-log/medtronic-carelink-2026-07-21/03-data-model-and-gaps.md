# Data-model / Nightscout-mapping gap memo (observed 2026-07-21, public sources only)

Anchor sources:
- mddub field-analysis gist: https://gist.github.com/5e4a585508c93249eb51 (last updated 2017-12-10, paradigm-era)
- mddub alarm code gist: https://gist.github.com/a95dc120d9d1414a433d (paradigm + NGP table, 2015-10-19)
- ondrej1024/carelink-python-client doc/carelink.md: paraphrased 780G-era field notes
- nightscout/nightscout-connect `lib/sources/minimedcarelink/index.js`: `markers_to_treatment`, `deviceStatusEntry`, `trend-map`, `modDefaults`
- Tidepool deprecated data model: https://github.com/tidepool-org/deprecated-data-model/wiki/Carelink-Files (39-column CSV shape; pre-7xxG)

## P0 — safety: do FIRST even before real pump arrives

### P0.1 — mmol/L passthrough is a correctness AND safety bug

- Observed in repo: `src/types/carelink.ts:48-49` declares `bgUnits?: string; bgunits?: string;` and `src/transform/index.ts:64-86` sends `sgv: sgv.sg` straight through with no unit normalization. `test/fixtures.ts:44`, `test/samples.ts:4,46` hardcode `bgUnits: 'MGDL', bgunits: 'MGDL'`.
- Observed in public evidence: mddub field-analysis 5e4a585508c93249eb51 (mentions `MMOL_L` as the other value). ondrej1024 doc/carelink.md lists bgUnits as MGDL/MMOL.
- Impact: if a mmol/L CareLink account flows through, Nightscout receives mmol/L numbers but Nightscout is mg/dL-native. AAPS, Loop, xDrip, Loop-based rigs will treat them as mg/dL readings and over-deliver insulin (or produce nonsensical highs).
- Fix shape (scope only): detect `data.bgUnits === 'MMOL_L'` (or `data.bgunits === 'MMOL_L'`) at transform; convert sg -> mg/dL by `mgdl = round(mmol * 18.0182)`; set entries[].sgv (mg/dL) and a devicestatus annotation so downstream looping clients see "the bridge did the conversion".
- Sanitized-fixture need: one mmol/L fixture that exercises the path. Can be hand-constructed by scaling an mg/dL fixture by 1/18.

### P0.2 — lastAlarm is modeled but never reaches Nightscout

- Observed: `src/types/carelink.ts:16-24` defines full `CareLinkAlarm { type, version, flash, datetime, kind, code }`. `src/transform/index.ts` does not reference `lastAlarm`. No alarm upload endpoint in `src/main.ts`.
- Observed in public evidence: nightscout-connect `lib/sources/minimedcarelink/index.js` `deviceStatusEntry()` contains an explicit `// TODO: add last alarm from data['lastAlarm']['code'] and data['lastAlarm']['datetime']` comment with the mddub alarm gist URL. mddub 5e4a585508c93249eb51 "Last alarm" section: `lastAlarm.type` always 'ALARM', `lastAlarm.code` ∈ {101,102}. mddub a95dc120d9d1414a433d ships paradigm numeric codes 3-117 + NGP "N"-prefixed 1-870.
- SAFETY CONSTRAINT (must precede any auto-relay feature): the mddub table has clear "Critical Pump Error. Stop using pump" codes (N24, N35, N40, N47, N48, N50, N55, N131) and many "Insulin delivery stopped" codes (paradigm 4/5/6/16/43/61 + NGP N2/N3/N4/N13/N14/N15/N16/N18/N20/N22/N27/N29/N33/N42/N45/N46/N53/N54/N60/N63/N67/N76/N77/N130). Several NGP N-codes include action guidance ("Insulin flow blocked. Check BG", "Auto Suspend. Insulin delivery stopped"). Auto-relaying these as Nightscout treatments/announcements without operator review is unsafe.
- Recommendation: do NOT implement an "alarm relay" feature blindly. Minimum path: emit a Nightscout devicestatus annotation `last_alarm = { code, datetime, text }` (purely informational); log at INFO/WARN with the human-readable text from a code→text table kept in-repo. For the priority-1 "stop using pump" and "Insulin delivery stopped" subset, log only with a hard-coded WARN banner; never auto-publish to Nightscout without operator gating.
- Sanitized-fixture need: a real 780G account's full alarm payload to validate code→text table coverage.

### P0.3 — pump-clock offsets work for ±quarter-hour timezones, but parsing is naive

- Observed: `src/transform/pump-offset.ts:24` rounds pump/server-clock delta to 15-minute steps and emits a signed-HHMM string. CHANGELOG.md 0.1.3 credits this fix (#15, #20).
- Not modeled: DST transitions (pump clocks don't auto-DST-adjust). A spring-forward pump timestamp can produce ±1h offsets rounded to a wrong quarter-hour until the next fetch.
- Implementation gap: emit a Nightscout devicestatus annotation `clock_drift_minutes` so an operator dashboard can detect drift early.

## P1 — feature, implementable from public evidence after P0 lands

### P1.1 — treatments (markers) upload is the single largest "available but unused" gap

- Observed: nightscout-connect `lib/sources/minimedcarelink/index.js` has a working `markers_to_treatment()` mapping. Observed CareLink `markers` shape: entries with `type ∈ {'MEAL', 'INSULIN', 'CALIBRATION', 'BG READING' / 'BG'}`, `index`, `dateTime`, `amount` (carbs for MEAL), `bolusType` (e.g. 'FAST'), `deliveredFastAmount`, `programmedFastAmount`, `effectiveDuration`, `activationType`.
- Translated outputs:
  - MEAL + paired-INSULIN (same index) -> { eventType:'Meal Bolus', carbs, insulin (with FAST duration/amount/programmed metadata) }
  - INSULIN not paired -> { eventType:'Correction Bolus', insulin: deliveredFastAmount }
  - CALIBRATION or BG READING -> { eventType:'BG CHECK', glucose, glucoseType:'Finger', created_at }
- Repo gap: `src/types/carelink.ts:51` has `[key: string]: unknown`, so `markers` passes through untyped and is silently ignored. No treatments upload endpoint (`src/main.ts` only uploads to `/api/v1/entries.json` and `/api/v1/devicestatus.json`). Nightscout has a separate `/api/v1/treatments.json` endpoint the bridge doesn't hit.
- Implementation: add a `treatment` / treatments type in `src/types/carelink.ts`; map markers->Nightscout treatments in `src/transform/index.ts` (or new `src/transform/treatments.ts`); POST to `${nsBase}/api/v1/treatments.json` in `src/nightscout/upload.ts` and `src/main.ts`.
- Sanitized-fixture need: a markers array from a real account (7xxG produces these; the 2015 mddub sample did not include markers, so it is unobserved in older references). A redacted copy from the operator's pump after arrival closes the gap.

### P1.2 — Medtronic 780G auto-mode fields likely available but currently unmodeled

- Observed in ondrej1024 doc/carelink.md "Data fields" table:
  - `therapyAlgorithmState/autoModeState`: "FEATURE_OFF","AUTO_BASAL","SAFE_BASAL" (SAFE_BASAL indicates "waiting for calibration")
  - `therapyAlgorithmState/safeBasalDuration` (minutes until exit from auto)
- Repo gap: `src/types/carelink.ts` does not declare these fields. Currently caught by the catch-all `[key: string]: unknown` and discarded.
- Implementation: add optional `therapyAlgorithmState?: { autoModeShieldState?: string; safeBasalDuration?: number; ... }` (field names from ondrej1024). Surface as Nightscout devicestatus pump.annotations. The "SAFE_BASAL" label is itself a clinically interesting signal — when present, the pump is in a degraded auto mode and the operator should know.
- Sanitized-fixture need: only obtain from a real 780G account.

### P1.3 — BG-target schedule (`limits` array)

- Observed in mddub 5e4a585508c93249eb51: a sample `limits` array of four `{kind:'Limits', version:1, highLimit, lowLimit, index}` entries with index values 0/60/126/228 (half-hour offsets; 24×15min slots = 360). User commentary: "12 am 70-200, 5:30am 70-180, 2pm 70-200".
- Repo gap: not declared in `src/types/carelink.ts`; passes through `[key: string]: unknown` and is dropped by `src/transform/index.ts`.
- Implementation: surface as Nightscout devicestatus pump.annotations.bgTargets (array of {startMin, low, high}); useful for clients that auto-adjust alarms.
- Sanitized-fixture need: a real connect/data payload containing `limits`.

## P2 — feature, requires real-data fixtures

### P2.1 — reservoir-level percentage mapping

- Observed: `reservoirLevelPercent` is observed on every record but the values are snap-points: 0, 25, 50, 75, 100. Current repo uses `reservoirAmount` (decimals, full units), which mddub didn't include. `src/types/carelink.ts:41` declares both `reservoirAmount?: number` and `reservoirRemainingUnits?: number`.
- Implementation: prefer `reservoirLevelPercent` for low-reservoir alerting (only 5 buckets); fall back to `reservoirRemainingUnits` for precision when present. Add `pump.reservoirPercent` to Nightscout devicestatus.

### P2.2 — multi-patient / caregiver mode

- Observed: `src/carelink/client.ts` implements `fetchAsCarepartner`. It calls `/patient/m2m/links/patients` (line aligned with nightscout-connect `modDefaults.patient_list_url`). `src/config.ts` has `CARELINK_PATIENT` env. `doctor.ts` and `main.ts` support multi-account.
- Gap: only ONE patient is auto-selected (`patientsResp.data[0].username`). No round-robin / multi-patient fan-out. ROADMAP.md v0.6.0+ lists this as a future item.
- Implementation: emit devicestatus per-patient when `CARELINK_PATIENT` is empty and there are multiple linked patients.
- Sanitized-fixture need: a carepartner account with 2+ linked patients. Not generally publicly available.

### P2.3 — additional CareLink endpoints the fork never hits

Cross-referenced from nightscout-connect `lib/sources/minimedcarelink/index.js` `modDefaults` block:
- (a) `/patient/users/me/profile` — more fields than `/users/me`
- (b) `/patient/dataUpload/recentUploads` — pump direct-upload history
- (c) `/patient/configuration/system/personal.cp.m2m.enabled` — feature flag check (m2m standing)
- (d) `/patient/m2m/connect/data/gc/patients/...` — grand-child data path under a care partner
- Implementation: optional but useful; only worth wiring once a real account can confirm the auth scopes work.

## P3 — trend-map quirk

- Observed: `src/transform/trend-map.ts` maps `NONE → {trend:0, direction:'NONE'}`. Nightscout convention for "no-change" is `trend:4, direction:'Flat'`. nightscout-connect maps the same key to `{trend:4, direction:'Flat'}`. Other six keys are identical.
- Impact: only matters for clients that key on `trend` numeric (Loop, AAPS). `NONE` arrows render correctly via the `direction` string but the numeric `trend=0` does not match what every other CGM source emits for flat.
- Implementation: change NONE to `{trend:4, direction:'Flat'}`. One-line edit + one line in the existing trend tests.
- Upstream domien-f uses the same `NONE → 0` so this is inherited, not a regression.

## P4 — version / device family quirks

- `src/carelink/client.ts:283` matches by `includes('BLE') || includes('SIMPLERA')`. Matches 780G / Guardian 4 / Simplera family per CHANGELOG.md 0.1.0.
- `src/transform/index.ts:23` branches on `data.medicalDeviceFamily === 'GUARDIAN'`. mddub sample is PARADIGM-era; the ondrej1024 README 770G works (not tested); 780G is the supported-device target.
- Unobserved: exact deviceFamily strings 780G accounts return. The fork's `isBleDevice` match-by-substring is conservative but will NOT match device families Medtronic might introduce without those substrings.

## Confidence / recency

- mddub 5e4a585508c93249eb51: last updated 2017-12-10 (paradigm-era, pre-7xxG). HIGH on enum value lists and field-presence claims that have since held across paradigm/NGP generations. LOW when extrapolating to 780G-specific NEW fields.
- mddub a95dc120d9d1414a433d: 2015-10-19. HIGH on the alarm code→text table for codes that predate the gist. MEDIUM-LOW on completeness for codes newer than 2015.
- nightscout-connect master: actively maintained 2026-vintage. HIGH on treatment/marker shapes, endpoint list, trend-map convention.
- ondrej1024/carelink-python-client: 2024-2026 era. HIGH on schema notes; the EXACT property paths are inferred from the table, not from JSON samples.
- Fork-local CHANGELOG.md v0.1.0-v0.1.6 (2026-07-19): HIGH for the current model.

## Recommended order of operations

1. P0.1 mmol/L safety fix + regression test ASAP, even before real pump. Fixture can be synthesized.
2. P0.2 lastAlarm plumbing + devicestatus.annotation.last_alarm + WARN log only for stop-using-pump subset. NO Nightscout alarm relay.
3. Post-pump (Nov 2026): capture sanitized fixtures for items 1-6 below and revisit for P0.2 safety hardening.
4. P1.1 markers/treatments: dependent on fixture 3.
5. P1.2 therapyAlgorithmState: dependent on fixture 1.
6. P1.3 limits[] schedule: medium-confidence shape from mddub; can implement speculatively, low blast radius.
7. P3 trend map NONE→Flat: trivial, ship with P0.1.
8. P2.1 reservoirLevelPercent: trivial alongside P1.1 once a real low-fill fixture lands.
9. P2.2 / P2.3: defer until P0 real-data pass.

Most of the P0/P1 work is implementable from public evidence alone. The safety-calibration items (P0.1, the un-explored half of P0.2) are the only ones that genuinely need a real account to validate end-to-end. Everything in P2+ requires real-auth fixtures and should be sequenced after the operator's 780G lands.

## Items requiring authenticated real-account fixtures

1. 780G raw device payload — deviceFamily string casing, therapyAlgorithmState object shape, reservoirLevelPercent boundaries, presence of any 780G-specific fields Medtronic added after the 2015 paradigm sample.
2. mmol/L account JSON once — confirm casing/key (`bgUnits` vs `bgunits`, `MMOL_L` vs `MMOL`).
3. `markers[]` from a 7xxG/780G account — treatment-event field set evolution; `bolusType` values, `effectiveDuration` semantics.
4. Alarm codes observed in 780G specifically — mddub's table is paradigm + NGP-era.
5. Carepartner account with >1 linked patients — to exercise P2.2 fan-out.
6. country-settings `blePereodicDataEndpoint` URL/version observed for a 780G EU account.

For each, a redacted JSON fixture inside test/fixtures-real/ would let us write proper regression tests today; the fork already has the placeholder pipeline (test/fixtures.ts + test/samples.ts) for paradigm-era shapes.
