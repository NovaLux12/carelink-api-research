# Empty-account baseline: `monitor/data` answers 200 with `BLE_X` (2026-11-15)

**Evidence class: OBSERVED.** Six authenticated requests against a live account
holding a paired 780G with **no sensor and no data**. Captured 00:07 UTC.

**Requests issued by this pass: 6 of a 20 cap** — five `GET`, one `POST`, all
authenticated with a real access token obtained the previous evening. **Delay:**
≥2 s between requests. No credentials are recorded here.

**This is a baseline, not a discovery pass.** The account is in the one state
nobody had ever recorded: authenticated, pump paired, **nothing uploading**. It
is exactly the state the bridge sees on validation day *before* the first
reading arrives, and being able to recognise it is the difference between
"correctly empty" and "silently broken".

---

## 1. `GET /patient/monitor/data` → 200 `{"deviceFamily":"BLE_X"}`

**24 bytes. No sensor, no readings, no pump data — and a device family.**

```json
{"deviceFamily":"BLE_X"}
```

This is the first **observed** value for this endpoint on a 780G. Everything the
corpus held before was third-party-client declarations; `docs/10` §1 has carried
"which field carries `deviceFamily`, and in what casing" as SOURCE-OBSERVED at
best. It is now OBSERVED, lowercase, camelCase key, value `BLE_X`.

**Why `BLE_X` matters:** it is in the bridge's BLE comparison set, so
`isBleDevice()` returns true on this account **before any data exists**. The
bridge will therefore take the BLE branch on validation day rather than falling
through to the legacy endpoint — the exact silent-zero-data failure mode that
issue #81 and upstream PR #2 were about.

**And it is a device-family value outside the 16 published tokens.** `BLE_X` is
one of the client's own comparison strings (`BLE`, `BLE_X`, `SIMPLERA`,
`SIMPLERA_X`, `GUARDIAN`, `NGP`), not one of the marketing family names
(`GUARDIAN`/`NGP`/`CGM`/`CC`). So the two vocabularies really are disjoint, as
`docs/05` suspected — but `isBleDevice()` is matching the right one.

**`deviceModel` is absent.** The response carries the family only; no model
string, no serial. So `isBleDevice(family, model)` is exercised on the family
branch alone here.

## 2. `GET /patient/connect/data?…` → **204 No Content**

```
GET  /patient/connect/data?cpSerialNumber=NONE&msgType=last24hours&requestTime=…
→ 204, empty body
```

**This is #12 §C's "authenticated, nothing to send" case, finally observed on a
known-empty account.** The distinction it enables is exactly the one §C asks
for: this 204 is *correct* for this account, so a 204 on validation day with a
live sensor means something else is wrong — role, `patientId` pairing, or device
family — rather than "no data yet".

A `POST` to the same path returns **403** (`Invalid key=value pair … in
Authorization header`). The bridge `GET`s it, so the 403 is a probe artefact, not
a defect: `GET` with a bearer token is accepted, `POST` is not. Worth recording
only so nobody repeats my mistake and reports a phantom bug.

## 3. `GET /patient/m2m/links/patients` → **403 NoPermission**

```json
{"error":{"type":"NoPermission","group":"AUTH"}}
```

The carepartner path, confirming the previous evening's finding: this is a
**patient** account and the carepartner namespace is closed to it. `403
NoPermission` — not 401, not 204 — is the fingerprint. **`lastDeviceFamily` is
permanently unavailable on this account**, which is why #12 §A is a two-field
capture.

## 4. Metadata endpoints all answer 200

| Endpoint | Status | Bytes |
|---|---|---|
| `/patient/users/me` | 200 | 283 |
| `/patient/monitor/data` | 200 | 24 |
| `/patient/countries/settings` | 200 | 2,616 |

`country-settings` returns the full document including
`blePereodicDataEndpoint`, `defaultDevice`, `uploaderAllowed` — so the BLE
endpoint is resolvable **before any data exists**.

---

## What this baseline buys us on validation day

| Symptom | Previously | Now |
|---|---|---|
| 204 from `connect/data` | indistinguishable from wrong pairing | **known-correct for an empty account**; a 204 later means something changed |
| `deviceFamily` value | third-party declaration | **OBSERVED: `BLE_X`** |
| BLE branch taken? | unknown until data arrives | **yes, determinable pre-data** |
| `links/patients` 403 | unexplained | **`NoPermission` = patient account, expected** |

## What it does not tell us

Everything that needs actual readings: whether `sgs` arrives, whether `kind` is
present, which endpoint generation serves the device once it is delivering, 200
vs 206 with a populated account, timestamp correctness, and whether
`sensorState` / `relativeOffset` / `limits[]` are populated. `monitor/data`
returning only `deviceFamily` is itself the finding that those fields arrive
with data, not with pairing.

**6 requests. Nothing further is probeable until the sensor is live.**
