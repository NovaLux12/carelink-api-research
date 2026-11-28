# Alarm semantics on a live 780G + Instinct: the published time is the CLEAR time, and two fields are dead

**Evidence class: OBSERVED.** 2026-11-28. Analysis of eight `display/message`
payloads from one live GB account (780G, MMT-1885, Instinct sensor), spanning
**24.2 h** — 2026-11-27T15:22Z to 2026-11-28T15:34Z.

**Requests: 2 of a 20 cap** (ledger: `results.jsonl`). Two new requests were made
this pass: one `GET /patient/users/me` to resolve the `patientId` the data-leg body
requires, and one `POST …/v6/display/message` to capture a current payload. The
other seven captures predate this pass and were already on disk.
**≥2 s between requests** — in this case ~60 s apart; the bridge's own 5-minute
polling is independent of this pass. Methods used: `GET` and `POST`.

**Account:** a live GB patient account, role `PATIENT_OUS`. The numeric `patientId` is
redacted here — it is PII and is not needed to reproduce anything below.

**Endpoint:** `https://clcloud.minimed.eu/connect/carepartner/v6/display/message`
— the **v6 BLE** route, not v13. See the correction issue for the 2026-11-15
baseline that recorded this endpoint as permanently 400-ing.

---

## 1. `lastAlarm.datetime` is the moment the alarm was CLEARED, not raised

The payload carries **both** `lastAlarm` (the current alarm only) and
`notificationHistory` (a retained list). Cross-referencing them by
`referenceGUID` gives a one-to-one match, and on every match:

```
lastAlarm.datetime === notification.dateTime
```

`notification.dateTime` is the **clear** moment. The alarm moment is a separate,
different field: **`triggeredDateTime`**.

| payload | code | `lastAlarm.datetime` (= clear) | `triggeredDateTime` (the alarm) | lag |
|---|---|---|---|---|
| `cl_ble.json` | 802 | 09:35:12 | 09:26:01 | **+551 s** |
| `cl_ble_LIVE.json` | 810 | 14:30:42 | 14:24:42 | **+360 s** |
| `cl_ble_now.json` | 810 | 17:40:49 | 17:40:43 | +6 s |
| `cl_ble_now2.json` | 810 | 17:40:49 | 17:40:43 | +6 s |
| `cl_ble_raw.json` | 100 | 13:29:15 | 13:29:06 | +9 s |

Across the full retained history the lag ranges **3 s to 36 m 27 s** (median
133.5 s, n=10), with one further outlier of **12 d 20 m 32 s**.

**Why this matters clinically:** an alarm timestamped at its clear moment can
report an event as having happened up to half an hour late, and in the outlier
case nearly two weeks late. A hypo suspend that was cleared quickly reads as
"now"; one cleared after a long recovery reads as having started when it ended.

**Which is right, and evidenced internally:** on event 31 the `triggeredDateTime`
lands exactly on the same payload's `markers[]` `LOW_GLUCOSE_SUSPENDED` entry —
two independent parts of the payload agreeing. (OBSERVED for that event; the
general rule is INFERRED from it plus the lag distribution.)

⚠ **`lastAlarm` does not carry `triggeredDateTime` at all**, so a client reading
only `lastAlarm` cannot recover the true alarm time. `notificationHistory` must be
read to get it.

## 2. `notificationHistory` retains roughly 24 hours and is the only source of the true alarm time

- `activeNotifications` was `[]` in **4/4** payloads — an active→cleared transition
  was never observed. (UNKNOWN, not disproven.)
- Retention is bracketed tightly: instance 8 was present at age **9 h 08 m** and
  gone at **24 h 57 m**; instance 20 was still present at **22 h 01 m**. Cutoff is
  therefore in **(22.0 h, 25.0 h)** — consistent with 24 h, not proven as exactly 24.
- `clearedNotifications` held **9–10** events in the captures examined.

## 3. `referenceGUID` decodes to a struct — it is not opaque

Bytes are **little-endian**:

| bytes | contents | verified |
|---|---|---|
| `[0:4]` | `instanceId` | 11/11 GUIDs |
| `[4:6]` | `faultId` (= the alarm code) | 11/11 |
| `[8:12]` | Unix seconds − **978307200** (Apple epoch), i.e. the trigger instant | matches `triggeredDateTime` on 9/11 |

It is **stable 1:1 across all eight payloads** (12 re-occurrences, zero field
disagreements), which makes it a sound idempotency key for writing alarms
downstream. Untested: behaviour at counter wrap, and whether a GUID is reused when
an event moves active→cleared (never observed). Both UNKNOWN.

**`relativeOffset` must never be persisted.** For one unchanged event it took four
different values across four payloads — it is a per-fetch relative value.

## 4. `faultId` IS the alarm code — so messageIds map to codes directly

Because `notificationHistory[].faultId` and `lastAlarm.code` are the same integer
for the same event, every `messageId` in the payload has a **direct**, non-inferred
numeric code. Seven codes are present across the captures:

| code | messageId |
|---|---|
| 100 | `BC_SID_BOLUS_ENTRY_TIMED_OUT` |
| 117 | (timed-out-class event) |
| 802 | `BC_SID_LOW_SD_CHECK_BG` |
| 803 | `BC_SID_LOW_SG_INSULIN_DELIVERY_SUSPENDED_SINCE_X_CHECK_BG` |
| 808 | `BC_SID_MAXIMUM_2_HOUR_SUSPEND_TIME_REACHED_CHECK_BG` |
| 810 | `BC_MESSAGE_DELIVERY_STOPPED_SG_APPROACHILG_LOW_LIMIT_CHECK_BG` |
| 827 | `BC_MESSAGE_SG_UNDER_50_MG_DL` |

This is the mapping that clients have been missing. It should be pinned as a
fixture so it cannot silently drift.

## 5. `pumpDeliverySuspendState` is dead on this pump generation

`false` on **every** event in **every** payload — including events whose messageId
literally reads `INSULIN_DELIVERY_SUSPENDED`.

The two plausible readings are **refuted, not merely unsupported**:

- **Not "state at clear":** six events have trigger and clear times squarely inside
  suspend windows that the *same payload's* `markers[] LOW_GLUCOSE_SUSPENDED`
  records with `deliverySuspended: true`.
- **Not "state at trigger":** the decisive case is `cl_ble_now.json`, which in one
  response reports `medicalDeviceSuspended: true`,
  `pumpBannerState: [SUSPENDED_BEFORE_LOW]` and `plgmLgsState: SUSPEND_FIRED_PLGM`
  — and `false` on every alarm event in that same response.

Only PLGM suspends appear in this corpus, so whether it ever goes true for a
user-initiated or fault suspend is **UNKNOWN**. Treat it as unpopulated and read
`medicalDeviceSuspended` / `pumpBannerState` instead.

## 6. `secondaryTime` is the suspend instant

Present on exactly the two `…SUSPENDED SINCE X…` events, as `"00:34"`, and it
matches the `LOW_GLUCOSE_SUSPENDED true` marker at `00:34:43` in the same payload.
Local-vs-UTC cannot be determined from this account, which is `GMT+00:00`. Format
is a bare `HH:MM` with no date.

## 7. `lastConduitUpdateServerDateTime` is absent; the real field breaks `clock_drift`

A separate and independent finding, recorded because it produces a **wrong number
on a live dashboard**.

`src/transform/pump-offset.ts` prefers the conduit clock pair
`lastConduitDateTime` / `lastConduitUpdateServerDateTime`, on the strength of
xDrip's `correctTimeInDisplayMessage()`. On this pump
**`lastConduitUpdateServerDateTime` is absent from 8/8 payloads**, so the pair
silently falls through to the device pair — which is why this never surfaced as an
error.

The field that *is* sent is **`lastConduitUpdateServerTime`** (epoch ms). Substituting
it makes the reported drift collapse:

| payload | `sMedicalDeviceTime` | `lastMedicalDeviceDataUpdateServerTime` | residual |
|---|---|---|---|
| `cl_ble.json` | 10:24:03 | 10:24:04 | **+0.022 min** |
| `cl_ble_LIVE.json` | 15:32:01 | 15:32:02 | **+0.023 min** |
| `cl_ble_now.json` | 18:04:48 | 18:04:50 | +0.023 min |
| `cl_ble_now2.json` | 18:34:46 | 18:34:48 | +0.027 min |
| `cl_ble_raw.json` | 15:23:02 | 15:22:04 | −0.966 min |

**The pump's clock is clean to within a couple of seconds.** The `+1.4 s` offset is
conduit transit time, not clock error. The bridge reports it to Nightscout as
`clock_drift_minutes`, rounded to a quarter hour — so what reaches the record is
`(rawMs − roundedOffset)/60000`, i.e. **essentially the upload latency mislabelled
as clock drift**.

Measured on the live database: **226 of 227 devicestatus rows** carry a
`clock_drift_minutes` in the range **0.1–4.7**, 24 distinct values. Every one of
those is an artefact.

⚠ **Caveat on the mechanism.** The +0.022 min residual technically rounds to a
zero quarter-hour offset, which would make drift ≈0.02, not 1–3 min. So the exact
path producing the observed 0.2–4.7 figures is **INFERRED, not traced end to end**.
What is OBSERVED is: (a) the preferred conduit pair is absent, (b) substituting
`lastConduitUpdateServerTime` gives sub-second agreement, and (c) the live database
shows non-zero "drift" on 226/227 rows. The inference is that the fallback path is
producing it; the trace should be confirmed before the fix is claimed complete.

## 8. What this pass did not establish

| Question | Status |
|---|---|
| Exact retention window | bracketed (22 h, 25 h), not proven |
| Whether `pumpDeliverySuspendState` ever goes true (user/fault suspend) | UNKNOWN |
| `secondaryTime` timezone | UNKNOWN — account is GMT+00:00 |
| `referenceGUID` at counter wrap, or across active→cleared | UNKNOWN |
| The exact source of the 0.2–4.7 `clock_drift_minutes` values | INFERRED, not traced |

[source: findings-log/2026-11-28-alarm-semantics/FINDINGS.md]
