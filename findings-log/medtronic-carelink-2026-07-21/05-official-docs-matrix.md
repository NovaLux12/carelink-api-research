# CareLink + 780G public-docs fact table (observed 2026-07-21)

Primary sources:
- 738634065 (Nov 2024) — CareLink Personal software guide for MiniMed 780G
- FAQ-CLP-CA-EN-002 (Rev. 08/2022) — CareLink Personal Canada FAQ
- CA-DIB-0079-E (Rev. 08/2022) — CareLink Connect getting-started
- M012839C001_1 — CareLink Connect Quick Reference Guide
- minimed.com 780G/MiniMed Mobile pages
- Store listings (Google Play, Apple iOS lookup)

## A. Max care partners per patient

- 780G CareLink Personal guide 738634065 p.5: "Note you can have up to five Care Partners per device user."
- CareLink Connect getting-started guide: "CareLink™ Connect app users can follow up to 5 people using the MiniMed™ mobile app."
- CareLink Connect Google Play (UK/ROW, updated 15 Jun 2026): "Now you can follow up to five people simultaneously."
- 24-hour acceptance window: "Each link will require Notifications to be set up. They must accept your connection request in their CareLink™ Personal account within 24 hrs."
- Confidence: HIGH. Authoritative.

Engineering implications: the bridge has no direct role in care-partner linking. The cap is account-level, not API-level. No rate-limit or partner-count work needed in v0.2.0.

## B. CSV / report export

- CareLink System User Guide: "To export data, go to Reports and then click Data export (CSV) (both in CareLink System and CareLink Personal), or Export data (in CareLink Pro). The CSV file contains the name and Patient ID for the patient, the reporting period, and identifies each device included in the report."
- 780G CareLink Personal guide 738634065 pp.12-20 lists: Assessment & Progress (780G-specific; SmartGuard exits, % time in SmartGuard), Weekly Review, Daily Review, Meal Summary, Log Book, Adherence, Device Settings Snapshot.
- Generate Reports page: "Reports are displayed in PDF format. They can be viewed online, saved, printed, or emailed."
- CareLink US help v5547015.htm reiterates PDF format.
- 2014 decoding-carelink sample shows v1.0.1 CSV field set ("Index,Date,Time,Timestamp,New Device Time,BG Reading (mg/dL),Linked BG Meter ID,…"). Medtronic has not published a current authoritative CSV field list.

Engineering implications: bridge does NOT generate CSV exports. For users who want a CSV: log into carelink.minimed.eu → Reports → Data export (CSV) → choose date range. Bridge is not in this path. A future bridge feature could parse the CSV format and back-fill gaps; not a v0.2.0 target.

## C. Units (mg/dL vs mmol/L) and timezone

- "Using CareLink Personal software" (Medtronic, dated Nov 28 2023): "In 'Preferences' you can customize the way your reports display your data. You can adjust glucose information, carb information and time format."
- 780G CareLink Personal guide 738634065 p.14: report screenshots captioned "Representative patient profile – mmol/L."
- CareLink Pro User Guide: "Glucose Units: mg/dL or mmol/L. Carbohydrate Units: grams or Exchanges."
- Timezone: Using the CareLink Connect App page (Nov 27 2023): "A time change icon appears on the graph if the time has been changed on the connected insulin pump or CGM device. This includes daylight saving time and traveling across time zones. The time shown after the time change icon matches the actual time on the connected insulin pump or CGM device."
- CareLink does not appear to offer a separate timezone preference. Event timestamps reflect what the pump clock said at event time.

Engineering implications: bridge should detect from the API payload whether SG values are mg/dL or mmol/L and either convert to Nightscout's expected mg/dL (canonical) or preserve and tag. Timezone: bridge must treat pump-clock as the authoritative timestamp and convert to UTC.

## D. Official data-freshness / polling guarantee

- 780G CareLink Personal guide 738634065 p.5: "Ensure this is switched on to automatically update your sensor history every five minutes (needed to send Care Partner alerts) and a full upload of your pump every 24 hours to create reports in CareLink™ Personal."
- CareLink Connect Google Play (UK/ROW, updated 15 Jun 2026): "IMPORTANT NOTE: For real-time updates, the app must consistently receive data from the CareLink™ server, while the insulin pump or CGM system must continually upload data to the CareLink™ server."
- CareLink Connect app-side refresh cadence: "Allow at least 20 seconds for data to refresh when bringing the app to the foreground." "The notification sound can be personalised and will sound for 30 seconds and repeat every 60 seconds until the app is viewed."

What Medtronic does NOT guarantee (gap in primary docs):
- No published SLA for the clcloud.minimed.com/connect/carepartner/v13/... API response freshness.
- No published rate-limit on /patient/connect/data or /patient/monitor/data.
- No contractual statement that third-party (non-MiniMed Mobile) clients will get 5-minute freshness. The data that *does* appear in the /connect/data response is whatever the server most recently has from the Mobile app.

Engineering implications: bridge's 5-min default is the natural choice because it matches Medtronic's own push cadence. Anything faster is wasteful; slower risks stale SG to Nightscout. The 24h lag on bolus/basal events is a Medtronic constraint, not a bridge bug.

## E. Confidence summary

| Fact | Source | Date | Confidence |
|---|---|---|---|
| MiniMed Mobile sync ≈ every 5 minutes (sensor) | 738634065 p.5 | 2024-11 | HIGH |
| MiniMed Mobile full upload every 24 hours | 738634065 p.5 | 2024-11 | HIGH |
| Max 5 Care Partners per device user | 738634065 p.5 | 2024-11 | HIGH |
| Care Partner can follow up to 5 patients | CA-DIB-0079-E | 2022-08 | HIGH |
| 24h follow-request acceptance window | CA-DIB-0079-E | 2022-08 | HIGH |
| 20s foreground refresh for CareLink Connect app | CA-DIB-0079-E | 2022-08 | HIGH |
| 30s/60s repeat notification cadence | CA-DIB-0079-E | 2022-08 | HIGH |
| CareLink Personal Reports = PDF | Generate Reports page | 2026-07-21 | HIGH |
| Data export (CSV) per date range | CareLink System User Guide | current | HIGH |
| Glucose units user-set in Preferences (mg/dL or mmol/L) | Using CareLink Personal page | 2023-11-28 | HIGH |
| CareLink uses pump clock time for events | Using the CareLink Connect App | 2023-11-27 | HIGH |
| 4-6 weeks manual upload recommendation | CareLink Personal AU FAQ | 2022-08 | HIGH |
| 780G CareLink upload requires MiniMed Mobile or Blue Adapter | CareLink Personal EU FAQ p.3 | 2022-08 | HIGH |
| Bridge 5-min default = community choice, not Medtronic SLA | [INFERENCE from absence of SLA] | — | MEDIUM |

## F. Items NOT supported by current public docs

1. API rate limits on /patient/connect/data and /patient/monitor/data — no published limit.
2. CSV field schema — the only known public CSV schema sample is from 2014 (Bewest's decoding-carelink). Medtronic has not published a current schema.
3. Timezone semantics in the JSON /connect/data payload — not documented. The bridge's existing `data.sgs[].Timestamp` usage needs code-level verification against actual payload to confirm UTC vs device-local vs server-local.
4. Real-time alert push from CareLink cloud — CareLink Connect gets alerts via the mobile push notification path (APNs/FCM), not via the same REST API the bridge hits. The bridge has no equivalent of push alerts.

## G. Engineering implications summary

1. No code changes needed for care-partner cap. The 5-partner limit is account-level, not API-level.
2. No CSV export work in the bridge. That's a CareLink-Personal-web-UI feature. Bridge users wanting CSV go to the website.
3. Units handling needs code-level verification. Read a real /connect/data payload to confirm whether SG values come in mg/dL or mmol/L, and whether there's a `units` field. Bridge should normalize to Nightscout-canonical mg/dL or document the units in devicestatus.
4. Timezone handling needs code-level verification. Bridge should normalize all timestamps to UTC ISO-8601 for Nightscout, regardless of pump clock.
5. Polling cadence is already optimal. 5-min default matches Medtronic's own push cadence. The 24h full-upload lag on bolus/basal is a Medtronic constraint.
6. The bridge should document the "real-time update requires continuous phone+pump+server chain" caveat in user-facing docs, mirroring Medtronic's Play Store disclaimer.
7. Simplera Sync + Guardian 4 sensor compatibility is post-software-update. Patients must have completed the 780G software upgrade before the bridge's `deviceFamily === 'BLE_X'` detection works for newer sensors.
8. CareLink Personal account unlink does NOT retroactively remove shared data from clinics.
