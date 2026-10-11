# carelink-bridge — app-emulation research (2026-10-08)

Reverse-engineering what the **official CareLink app** actually does, so the
bridge matches it. Sources: live probing, the official portal's public JS bundle,
Medtronic's own GB Terms of Use / Privacy Notice, and the reference client
sources (xDrip+ CareLinkFollow, ondrej1024 carelink-python-client).

---

## 1. THE headline: the bridge's data endpoint is right, but for a subtle reason

`/patient/countries/settings?countryCode=GB&language=en` returns
**`blePereodicDataEndpoint`**:

```
https://clcloud.minimed.eu.connect/carepartner/v6/display/message
```

(identical for GB, US, DE, FR, AU, NL — every country probed).

The bridge reads that field and POSTs there (`fetchBleDeviceData`), then
`buildEndpointCandidates()` rewrites the version and tries **13 → 11 → 6 → 5**.
So the 780G path is:

```
POST https://clcloud.minimed.eu/connect/carepartner/{6|13|11|5}/display/message
     {"username":…, "role":"patient"|"carepartner", "patientId":…}
```

**Live-verified today:** `/connect/carepartner/{v6,v11,v13}/display/message`
→ **401 `{"message":"Authentication failure"}`** on both `clcloud.minimed.eu`
and `.com`. All three versions live.

The code comment ("the config returns v6 while the app discovery config
advertises v13, so the fallback list spans both directions") is **still accurate
as of 2026-10-08** — 7 weeks on, nothing has moved. That's the single most
important validation result for the November pump.

## 2. The namespace question — ANSWERED, and it's more nuanced than "two"

Live-verified today, unauthenticated (401/403 = endpoint exists):

| Path | `carelink.minimed.eu` | `clcloud.minimed.eu` |
|---|---|---|
| `/patient/users/me` | **401** InvalidToken | 403 Missing Auth Token |
| `/patient/users/me/profile` | **401** | 403 |
| `/patient/monitor/data` | **401** | 403 |
| `/patient/m2m/links/patients` | **401** | 403 |
| `/patient/countries/settings` | **200** (public) | 403 |
| `/patient/configuration/system/…` | **200** (public) | 403 |
| `/patient/dataUpload/recentUploads` | **405** POST-only | 403 |
| `/patient/connect/data?…` | **401** | **401** |
| `/patient/m2m/connect/data/gc/patients/{u}` | **401** | **401** |

**Reading:** the *metadata* endpoints live only on `carelink.*`; the *data*
endpoints are served by **both** hosts. So:

- The bridge's choice of `carelink.minimed.eu` for everything is **valid** —
  nothing it calls is host-wrong.
- But the two data endpoints it calls have a **second live host**. xDrip's
  current code moved `connect/data` and `m2m/…/gc/patients/*` to
  `cloudServer()` (= `clcloud.minimed.eu`) unconditionally, because
  **"the old cloud data endpoint no longer works outside the US"**
  (xDrip PR #3859).

  ⚠️ **November validation item:** for an EU/OUS account, test
  `clcloud.minimed.eu/patient/connect/data` *as well as* `carelink.minimed.eu`.
  The bridge currently only tries the carelink host for the legacy connect
  fallback, and never tries clcloud for it. If the xDrip finding still holds,
  that fallback silently fails in EU.

## 3. What the official app uses (from `carelink_client2.py`)

The reference implementation models the official CareLink Connect app:

```
[1] GET  baseUrlCareLink + "/users/me"          → /api/carepartner/v2/users/me
[2] GET  baseUrlCareLink + "/links/patients"    → /api/carepartner/v2/links/patients
[3] POST baseUrlCumulus   + "/display/message"  → /connect/carepartner/v11/display/message
```

So there are **three** conventions live, all confirmed today:

1. **xDrip / this bridge** — `carelink.minimed.eu/patient/*` (metadata) +
   `clcloud.minimed.eu/connect/carepartner/v6/display/message` (data)
2. **xDrip cloudServer** — `clcloud.minimed.eu/patient/*`
3. **Official app** — `carelink.minimed.eu/api/carepartner/v2/*` (identity) +
   `clcloud.minimed.eu/connect/carepartner/v{N}/display/message` (data)

Our bridge uses #1. The official app uses #3. **Both are live.** They differ only
in the *identity* endpoints (`/patient/users/me` vs
`/api/carepartner/v2/users/me`) — which return the same thing under different
routes. Not a defect, but worth knowing: the README's "the same way the official
app does" is only true of the *data* leg.

## 4. 🎯 The reports API — and it maps to the ROADMAP's deferred items

The `carelinkhp` portal bundle gave six endpoints on
`commoncore.medtronic.{eu,com}`. The GB country-settings response gives the
**vocabulary** those endpoints take — `supportedReports`:

```
ADHERENCE, ASSESSMENT_AND_PROGRESS, BOLUS_WIZARD_FOOD_BOLUS, DAILY_DETAILS,
DASHBOARD, DEVICE_SETTINGS, EPISODE_SUMMARY, LOGBOOK, OVERVIEW,
WEEKLY_REVIEW, INSULIN_ASSESSMENT
```

Against the bridge's v0.2.0 deferred-fixtures list:

| ROADMAP deferred item | Reports API candidate |
|---|---|
| `markers[]` for treatments | **`BOLUS_WIZARD_FOOD_BOLUS`** or **`LOGBOOK`** |
| `therapyAlgorithmState` (auto-mode) | **`ASSESSMENT_AND_PROGRESS`** / `DEVICE_SETTINGS` |
| `limits[]` schedule | **`DEVICE_SETTINGS`** |
| `reservoirLevelPercent` | **`DAILY_DETAILS`** / `DASHBOARD` |
| NGP-tier alarm codes | **`EPISODE_SUMMARY`** |

**This is the single most promising lead for unblocking the pre-pump fixture
work** — a CSV/PDF report generator over the same account would give us
historical bolus/carb/insulin structure that `monitor/data` doesn't carry. Needs
a token to confirm.

Also note `region: "OUS"` in country settings (not "EU" as the discovery doc's
CP entries say) and audience `carepartner.patient.ous`. Two names for the same
non-US tenant — worth a `// note` in `resolveServerName`.

## 5. Account creation — what the actual contract says

I fetched Medtronic's own GB **Terms of Use** and **Privacy Notice** (the URLs
come from `pathDocs` in the country-settings response — no guessing).

**Terms of Use** (5pp, generic website terms). The operative clause:

> "Medtronic reserves the right to discontinue any use that is **abusive,
> illegal, disruptive, or that otherwise fails to conform** to these Terms of
> Use. Accordingly, Medtronic reserves the right to **terminate access** to any
> or all areas of this web site upon a breach."

What is **not** in there:
- ❌ no one-account-per-person clause
- ❌ no prohibition on automated/scripted access
- ❌ no reverse-engineering / decompilation ban
- ❌ no prohibition on a second or care-partner account

The only other relevant line is a copyright one: materials are for "your
personal, non-commercial use" — which this bridge is.

**Privacy Notice** (22pp) — two things worth knowing:
- It explicitly names **"third-party mobile applications to which you have
  subscribed that are compatible"** as a recognised disclosure path. Medtronic
  contemplates third-party clients in its own privacy document.
- Account creation requires `dateOfBirthRequired: true`, `legalAge: 18`,
  `postal` (UK postcode regex is published), and a `password` — MFA is
  `status: OPTIONAL` with `gracePeriod: 5`.

**Practical read:** the contract risk is the catch-all "abusive/disruptive" +
terminate-at-will, not any explicit ban. For one person doing modest-volume
access the real exposure is behavioural, not contractual.

## 6. My recommendation on the account

**Create the real one now** — it's the same account you'll use in November, so
there's no "two accounts" cost, and the thing you actually need from it (live
`npm run login` → OAuth → refresh → data round-trip) is the only way to catch
an Auth0 drift before it becomes a November emergency. Do **not** lean on it
hard: a handful of logins from a residential IP is not "abusive/disruptive"
under any reading.

Skip the dummy patient account — it adds ToS surface and fake health data to a
medical platform, and buys you nothing a real account doesn't.

**Before the pump**, the highest-value authenticated checks are, in order:
1. `npm run login` end-to-end → does the pinned `android/3.6` Auth0 flow still work?
2. `GET /patient/users/me` → and compare with `GET /api/carepartner/v2/users/me`
3. `POST /connect/carepartner/{6,13}/display/message` → which version answers?
4. For an EU account: `clcloud.minimed.eu/patient/connect/data` vs the carelink host
5. `reports-broker`/`reports-metadata` with a `supportedReports` type → the
   fixture unblocker

## 7. Evidence for S1 (the header finding) is now stronger

Country settings also publishes `pathDocs`, including
`ddms.analyticsToolNoticePdf` → `analytics_tool_notice.pdf`, which returned a
**196-byte HTML document instead of a PDF** from
`carelink.minimed.eu/crm/ocl/15.5/media/en/gb/`. So a document Medtronic's own
config points at is served with the wrong content type, with no
`X-Content-Type-Options: nosniff` on that host either. Small, but it's the same
"the carelink.minimed.eu estate is loosely configured" pattern as S1.

---

# Round 2 — the clinician portal's full API surface (2026-10-08)

`carelinkhp.minimed.eu` is not just a patient portal — it's the **HCP/clinic
portal**. Its public JS bundle (`main.fb5f8cb7eb60c4d5.js`, 3.4 MB) contains
Medtronic's authoritative device tables, the report catalogue, and a complete
`hcp/*` endpoint map. All extracted from a **public asset** — no auth.

## 8. The device model table (authoritative)

`PUMP` (with `minValue`/`maxValue` glucose ranges and `webDashboardEnabled`):

| Model codes | Device |
|---|---|
| MMT-1510, MMT-1710 | 620G |
| MMT-1714, MMT-1715 | 630G |
| MMT-1511/1512, MMT-1711/1712 | 640G |
| MMT-1883, MMT-1740/1741/1742, MMT-1780/1781/1782 | 670G |
| MMT-1800/1801/1805 | 700 |
| MMT-1809/1810/1817/1818 | 720G |
| MMT-1811, MMT-1812 | 740G |
| **MMT-1880, MMT-1881, MMT-1882** | **770G** |
| **MMT-1884, MMT-1884XCU, MMT-1885, MMT-1885XCE, MMT-1886, MMT-1886XCE, MMT-1886XCF** | **780G** ← the pump |
| MMT-1900/1902/1904 | PCL F3 |
| MMT-1906/1907/1908 | NMX7 |
| MMT-8162, MMT-8163 | NMX8 (`minValue:50`) |
| **MMT-8062/8063/8082/8083/8084/8085** | **"Minimed Flex"** (`minValue:50`) — previously unseen |

`SENSOR`: MMT-7763/7731 Enlite · MMT-7811/7821/7910/7911 Guardian Sensor 3 ·
**MMT-7841 Guardian 4 Sensor** · **MMT-5120 Simplera Sync™** ·
MMT-5100/5101 Synergy · **MMT-5420 + SKU-78893/78953/78955/78957/78959/78960-01
Instinct™ Sensor** · **SKU-78954/78956/78958-01 Instinct™ Go**

`StandaloneCGM`: CSS-7200/7201, `gm3_snapshot` Guardian Connect ·
**MMT-8200/8201, `gm4_snapshot` Guardian 4 system** ·
**MMT-6500/6501, MMT-8400/8401 Simplera™ system**

`InsulinDelivery`: MMT-105NNBLNA InPen (Novo).

**Two critical details for the bridge:**

1. **The API returns `deviceModel` *and* `sensorModel`, not only a family
   string.** The portal has a resolver:
   ```js
   const sensorModel = a.sensorModel?.trim();
   return a.deviceModel || (sensorModel && "NO_SENSOR" !== sensorModel.toUpperCase() ? sensorModel : "");
   ```
   `NO_SENSOR` is a real sentinel value. Our bridge only ever reads
   `deviceFamily` / `medicalDeviceFamily` and **never looks at `deviceModel` or
   `sensorModel` at all**.

2. **The family value is mixed-case.** The portal defines
   `SIMPLERA_SYSTEM = "Simplera™ system"`. Our `isBleDevice()` does
   `deviceFamily.includes('SIMPLERA')` — and JavaScript `String.includes()` is
   **case-sensitive**. `"Simplera™ system".includes('SIMPLERA')` → `false`.
   If the wire value is the display string rather than the enum key, **BLE
   detection silently fails for Simplera** and the bridge falls back to
   `monitor/data`, which upstream PR #2 established returns `{}` for BLE
   devices. Cannot confirm which shape the API sends without a token — flagged
   as a validation item, but the code should be case-insensitive regardless.

The tables are also mirrored by a runtime config the app fetches:
`deviceModelMapping` and `deviceToFamilyMapping` (seen in the NgRx store as
`appConfig`, `crmConfig`, `localeConfig`, `productContext`, `patientDashboardEndpointsConfig`),
so the static table above is a *fallback* — the live mapping is server-driven.
That is a further reason not to hardcode model numbers into the bridge.

## 9. The report catalogue (14 types, not 11)

Country settings' `supportedReports` lists 11. The portal has **14**:

| id | label | reportType |
|---|---|---|
| 1 | reportPatientDashboard | PatientDashboard |
| 2 | reportAssessmentAndProgress | AssessmentAndProgress |
| 3 | reportWizardFoodBolus | BolusWizardFoodBolus |
| 4 | reportInsulinAssessment | InsulinAssessment |
| 5 | reportWeeklyReview | WeeklyReview |
| 6 | reportDailyDetails | DailyDetails |
| 7 | reportDeviceSettings | DeviceSettings |
| 8 | reportAdherence | Adherence |
| 9 | reportLogbook | Logbook |
| 10 | reportDashBoard | Dashboard |
| 11 | reportEpisodeSummary | EpisodeSummary |
| 12 | reportOverview | SensorAndMeterOverview |
| 13 | reportDataTable | DataTable |
| 14 | reportSettingsHistory | SettingsHistory |

Data sources: **Pump, Sensor, Meter**. Periods: 0/14/30 days, 2/3/4/5/6/9/12 months.
Formats: CSV + PDF.

## 10. The full `hcp/*` endpoint map

Two services, both pointed (in the shipped bundle) at
`https://dev.commoncore.medtronic.eu/{reports-broker,reports-metadata}/v1/ocl`,
both with `x-api-key: <VENDOR-API-KEY-REDACTED>`:

**broker** `generate_report, report_status, report_csv, report_pdf`
**metadata** `report_data_time_lines_range, report_data_time_lines_for_calendar`

Plus a relative `hcp/*` family on the portal origin — extracted verbatim:

- `hcp/reports/{generateReport,getReportStatus,getReportCsv,getReportPdf,
  getSnapshotTimelinesRange,getSnapshotTimelinesForCalendar,
  getAuditLogsTimelinesForCalendar,generateAuditLogs,getAuditLogStatus,getAuditLogCsv}`
  ← **audit-log reports**, a family not in the portal's own catalogue
- `hcp/insights/v1/{userStatus,generateReport,getReportStatus,getReportPdf,
  acceptTerms,generateOneTimeCode,validateOneTimeCode,generateReportWithCode}`
- `hcp/configuration/public/{pow.nutrino.cc.{metadata,broker}.service.config,
  cua.control.codes.settings, user-identifier-settings?countryCode=…,
  system.logbook.entry.validation.config, logbook.supported.entry.types}`
  ← **the last two are the treatments/alarm-code schemas the ROADMAP defers**
- `hcp/patients/{getAllClinicUnarchivedPatients,getAllClinicArchivedPatients,
  addPatient,flagPatient,unFlagPatient,clearPatientsFlags,archivePatient,
  unarchivePatient,care-partner/search}`
- `hcp/patients/((patientId))/{preferences,remote-monitoring/settings,
  long-acting/settings,insights/disable,control-codes,care-partner,
  care-partner/link,care-partner/unlink,send/follow-up}`
- `hcp/clinics/{clinic-outcomes/reference,access-data/disable}`, `hcp/v2/clinics/access-data`
- `hcp/access-data/{,revoke,suspend,activate}`
- `hcp/follow-up/{domains,domains/((domainId)),templates,templates/((templateId))}`
- `hcp/dataUpload/{generateUrl,getRecentUploadInfo,getSnapshot,getTrace,
  getUploaderLogs,getTokenStatus}`
- `hcp/remoteLinking/{isRemoteLinkingAllowed,remoteLinkPatient}`
- `hcp/fastLinking/{isFastLinkingAllowed,fastLinkPatient,getPersonalPatientInfo}`
- `hcp/anonymization/{getCountryAnonymizationSetting,updateClinicAnonymization,
  createUserName,getNewSystemId}`
- `hcp/user/checkUserIdentifier`
- `hcp/settings-calculator/{generateReportPdf,acceptDisclaimer,recommendedValues,recalculate}`
- `hcp/linkedPatient/{username/check,password/rules,password/compliance}`

**Access control (verified live, no credentials used):**
- `GET /hcp/configuration/public/*` → **412**, empty body, and
  `access-control-allow-headers: X-System-ID, Content-Type, authorization`
- Adding `authorization: Bearer none` → **200** with
  `{"field":null,"message":"access.not.allowed"}` — so the endpoint is live and
  the bearer is validated server-side.
- Without the header, `412`. With an invalid bearer, a clean JSON refusal.

**This is correct posture** — the portal API is not anonymously readable. The
`X-System-ID` header belongs to the anonymisation feature
(`getNewSystemId` / `createUserName`), consistent with the portal being a
clinic-facing tool.

## 11. Where unauthenticated RE ends

Everything past this point needs a bearer token issued to a clinic or patient
account. Concretely blocked:
- the `hcp/configuration/public/*` schemas (logbook entry types, control codes)
- `hcp/reports/*` and `reports-broker`/`reports-metadata` bodies
- the shadow-tenant token-confusion question
- the namespace/version answer for real 780G data

The bundle gave us the *shape* of all of it. A single `npm run login` gives us
the *contents*.

---

# Round 3 — the full `RecentData` payload schema (from xDrip's message classes)

The reference client's model classes are the closest thing to a spec the
CareLink cloud API has. Retrieved 2026-10-09 from `NightscoutFoundation/xDrip`
`…/cgm/carelinkfollow/message/`.

## The top-level payload — every field the v0.2.0 note defers is in the schema

| Field | Note |
|---|---|
| `List<Marker> markers` | **treatment/meal/calibration/insulin/auto-mode events** |
| `TherapyAlgorithmState therapyAlgorithmState` | **auto-mode state** |
| `List<Limit> limits` | **pump settings schedule** |
| `Basal basal` | basal schedule |
| `List<PumpBannerState> pumpBannerState` | pump banners / on-screen alerts |
| `NotificationHistory notificationHistory` | notification history |
| `int reservoirLevelPercent` | **percent form of reservoir** |
| `int reservoirAmount` / `float reservoirRemainingUnits` | units form |
| `String pumpModelNumber` | **model number as the cloud reports it** |
| `Long lastConduitUpdateServerDateTime` | annotated *"As of new BLE endpoint v11"* |
| `int pumpBatteryLevelPercent` | **separate from the medical-device one** |
| `int medicalDeviceBatteryLevelPercent` | what this bridge reads |
| `float maxAutoBasalRate`, `float maxBolusAmount` | pump limits |
| `int averageSG`, `float averageSGFloat`, `int timeInRange` | therapy summary |
| `int belowHypoLimit`, `int aboveHyperLimit`, `int sgBelowLimit` | range limits |
| `boolean medicalDeviceSuspended`, `Boolean pumpSuspended` | suspension |
| `int sensorDurationMinutes`, `int timeToNextCalibrationMinutes` | minute-precision |
| `String clientTimeZoneName` | **client timezone** — relevant to the pump-offset issue |
| `Boolean calFreeSensor`, `Boolean finalCalibration` | calibration model |
| `int gstBatteryLevel`, `Boolean gstCommunicationState` | sensor-comms state |
| `Boolean pumpCommunicationState`, `Boolean conduitMedicalDeviceInRange` | comms |
| `String systemStatusMessage` | `BLUETOOTH_OFF`, `PUMP_PAIRING_LOST`, `PUMP_NOT_PAIRED`, `LOST_PUMP_SIGNAL`, `UPDATING` |
| `SensorGlucose lastSG`, `List<SensorGlucose> sgs`, `String lastSGTrend` | what the bridge uses today |
| `ActiveInsulin activeInsulin`, `Alarm lastAlarm`, `String bgUnits`, `String timeFormat` | bridge-relevant, already typed |

### `deviceFamily` values — this is the wire vocabulary
`GUARDIAN`, `NGP`, `CGM`, `CC` — where **`CC` includes Instinct**.
**None of the four contains `BLE` or `SIMPLERA`.** So if the payload's
`medicalDeviceFamily` carries one of these tokens, this bridge's `isBleDevice()`
would return **false for every device including a 780G** — the BLE endpoint would
never fire and everything would route through `monitor/data`.
The upstream PR #2 tests use `BLE_MINIMED`, so *some* value must carry a BLE
token; whether the cloud sends `BLE_…`-style values or these four canonical ones
is **UNVERIFIED and is the single most important thing to confirm with a
token.** Do not assume either.

### `Marker` — the treatments schema (`markers[]`), in full
`type` ∈ {`MEAL`, `CALIBRATION`, `BG_READING`, `BG`, `INSULIN`,
`AUTO_BASAL_DELIVERY`, `AUTO_MODE_STATUS`}; plus `index`, `value`, `kind`,
`version`, `dateTime`, `timestamp`, `displayTime`, `relativeOffset`,
`calibrationSuccess`, `amount`, `programmedExtendedAmount`, `activationType`,
`deliveredExtendedAmount`, `programmedFastAmount`, `programmedDuration`,
`deliveredFastAmount`, `effectiveDuration`, `completed`, `bolusType`,
`autoModeOn`, `bolusAmount`, `MarkerData data`.
`MarkerData.dataValues` carries `maxAutoBasalRate`, `insulinType`,
`insulinUnits`, `programmedFastAmount`, `deliveredFastAmount`, `activationType`,
`completed`, `bolusType`, `amount`.

**`AUTO_BASAL_DELIVERY` + `autoModeOn` + `MarkerDataValues` map almost exactly
onto the deferred auto-mode and `limits[]` items** — the platform reports them as
*markers*, not separate top-level structures. That is a materially different
design than the ROADMAP assumes, and worth knowing before November.

## Two concrete schema gaps in this bridge

1. **Battery level.** Upstream's `getDeviceBatteryLevel()` prefers
   `pumpBatteryLevelPercent`, falling back to `medicalDeviceBatteryLevelPercent`
   *only when the former is 0*. This bridge reads `medicalDeviceBatteryLevelPercent`
   alone, so on a device reporting only `pumpBatteryLevelPercent` it would surface
   **0% battery**. Fix: `pumpBatteryLevelPercent ?? medicalDeviceBatteryLevelPercent`.
2. **Reservoir.** The payload carries `reservoirLevelPercent` (percent) *and*
   `reservoirAmount`/`reservoirRemainingUnits` (units). The bridge types only the
   units fields, and the ROADMAP lists `reservoirLevelPercent` as deferred — but
   it is present in the schema, so it is not blocked on a pump; it is blocked on
   nobody having typed it.

Neither is confirmed to fire on live data, but neither costs anything to make
robust, and both are the kind of thing that only shows up as "battery reads 0%"
or "no reservoir bar" after a pump arrives.

---

# Round 4 — the alarm-code table and the NGP string-code problem

## The authoritative alarm dictionary

`https://carelink.minimed.com/patient/connect/mobile.do` (mirrored as mddub's
gist `a95dc120d9d1414a433d`, already cited by `src/last-alarm.ts` as its source)
contains `errorStrings`, split in two:

- **paradigm alarms — bare numeric keys:** `3` Battery out limit, `4` Delivery
  stopped. Check BG, `5` Pump battery depleted, `6` Auto Off, `16` Pump reset,
  `43` Pump motor error, `50` Bolus stopped, `51` Delivery limit exceeded,
  `55` Pump battery failed, `59` Button error, `61` Check settings,
  `62` Empty reservoir, `66` No reservoir, `74` Finish loading,
  `81` Replace pump battery now, `82` Low Reservoir, `83` Check BG,
  `84` Alarm clock, `85` Max fill reached, `86` Weak battery, `87` Missed bolus,
  `88` Silenced sensor alert, then `101`–`117` for the sensor/CGM tier
  (`101` High SG … `117` SG falling rapidly).
- **NGP alarms — `N`-prefixed string keys:** `N24`, `N35`, `N40`, `N47`, `N48`,
  `N50`, `N55`, `N131` all = *"Critical Pump Error. Stop using pump"*;
  `N22`, `N77`, `N25`, `N1`, `N33`, `N42`, `N63`, `N67`, `N76`, `N130` =
  *"Pump error. Insulin delivery stopped"*; `N6` Pump power loss;
  `N51` Bolus Stopped; `N73` Replace pump battery now; `N117` Active insulin
  cleared; `N789` Change sensor; `N802`/`N805`–`N812` SmartGuard alerts
  (Alert on low / Suspend on low / Suspend before low / Basal delivery resumed).

## Why this matters (issue #84)

`src/last-alarm.ts:31` declares `STOP_USING_PUMP_CODES: ReadonlySet<number>` and
`:85` does `if (typeof code !== 'number') return null;`.

So if a 780G reports `"N24"`:
1. the alarm is **silently dropped** — no annotation, no warn, no text; and
2. even a correctly-populated `Set<number>` could not hold `"N24"`.

The code's comment assumes *"NGP codes that arrive as numeric wire values"* —
an assumption this same cited source contradicts. The NGP priority-1 set was
left empty pending "a sanitized 780G fixture", but the tiering is already in the
source the repo cites; what was missing was noticing the keys are strings.

**UNVERIFIED:** whether the *wire* sends `"N24"` or `24` — the dictionary is
Medtronic's display layer, not necessarily the payload. But the deferral rested
on an assumption rather than a measurement, and the failure mode is a silent
drop, so handling both forms is strictly additive.

## Also from the same dataset (mddub/5e4a585508c93249eb51, 2,961 records)

`lastSGTrend` ∈ {NONE, DOWN, UP, DOWN_DOUBLE, UP_DOUBLE};
`sensorState` ∈ {NORMAL, UNKNOWN, WEAK_SIGNAL, WARM_UP, METER_BG, LOST_SENSOR};
`conduitBatteryStatus` ∈ {FULL, HIGH, …}; `timeFormat` ∈ {HR_24, HR_12};
paradigm-era `lastAlarm.code` values are unquoted integers (`101`, `102`).

Note `medicalDeviceFamily: "GUARDIAN"` in a real EU `connect/data` response
quoted in nightscout/cgm-remote-monitor#5719 — consistent with the
`GUARDIAN`/`NGP`/`CGM`/`CC` vocabulary from Round 3 and therefore with the
concern in #81, though that sample predates the BLE endpoint and 780G.

## Correction (2026-10-11) — attribution

"the bridge" throughout means
**[NovaLux12/carelink-bridge](https://github.com/NovaLux12/carelink-bridge)**. This
document is the most-consumed file in the repo for that client's implementers, so the
attribution is now a link rather than a bare name. No observation changes.
