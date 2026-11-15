# The BLE data path: endpoint is v6, and it 400s on a data-less account

**Evidence class: OBSERVED.** Nine authenticated requests, 2026-11-15 00:1x UTC,
against a live patient account with a paired 780G, **no sensor, no data**.

**Requests: 9 of a 20 cap** (this pass; 15 total tonight against the tenant).
**Delay:** ≥2.5 s between BLE attempts. Bearer token only.

---

## 1. Country settings advertises a **v6** BLE endpoint

```
GET /patient/countries/settings?countryCode=GB&language=en
→ blePereodicDataEndpoint:
  https://clcloud.minimed.eu/connect/carepartner/v6/display/message
```

**v6.** That is directly at odds with the corpus's own conclusion, recorded in
`docs/10` and in the bridge's `buildEndpointCandidates()` comment: *devices are
v13-era, and `blePereodicDataEndpoint` returns **v6** everywhere while legacy
backends answer 200 with stale records* — which is exactly why the candidate
list leads with v13.

So `fetchBleDeviceData()` POSTs to the endpoint the server advertises, and the
server advertises the generation the research says is wrong. Both facts can be
true — the advertised endpoint may be a legacy fallback — but they have never
been reconciled in one place. **On validation day this is the branch that will
run** (`isBleDevice('BLE_X')` is true), so it is now the highest-value unknown.

## 2. That endpoint returns `400 {"message":"Bad Request"}` for every body tried

Six variants, all identical:

| Body | Status | Response |
|---|---|---|
| `{username, role:'patient', patientId}` (the bridge's shape) | 400 | `{"message":"Bad Request"}` |
| `{username, role:'patient'}` | 400 | same |
| `{username, role, patientId, appVersion:'3.8.0'}` | 400 | same |
| `{username}` only | 400 | same |
| **v13** `…/v13/display/message` with the bridge's shape | 400 | same |
| **v13** with `appVersion` | 400 | same |

**A 400 that is identical for a minimal body and for the full one is not a
body-shape rejection.** If a required field were missing the message would name
it; if a field were wrong the message would differ between variants. It is the
same 25 bytes every time, on both v6 and v13.

**Most likely reading:** the endpoint refuses because the account has no device
data to serve — a 400 used where a 204 would be more honest. That cannot be
confirmed without a live sensor, and it means **this 400 is not a bug**. It is
now the recorded baseline: on validation day, a 400 from here means the request
regressed; a 200 with `patientData` means it works.

## 3. `/patient/users/me` has **no `username` field**

```
keys: loginDateUTC, id, country, language, lastName, firstName,
      accountId, role, cpRegistrationStatus, accountSuspended,
      needToReconsent, mfaRequired, mfaEnabled
```

`accountUsername()` is `this.currentUser?.username || this.options.username`.
Since `/users/me` carries **no `username` key at all**, that first term is
*always* undefined on this account, and the fallback to the configured
`CARELINK_USERNAME` is what actually supplies the identifier on every data
request.

**This is not a defect — `CARELINK_USERNAME` is required.** `loadConfig()` throws
`Missing CARELINK_USERNAME` before the client is ever constructed
(`src/config.ts:41`), so the `"unknown"` placeholder my probe sent came from
calling the endpoint outside config validation, not from the bridge. Recorded
here only because the *implication* is worth keeping: the code comment calls
this a preference for the "server-reported username", and on this account the
server reports none — so the configured value is the sole source, by necessity
rather than by preference.

---

## What this changes for validation day

| Question | Before | Now |
|---|---|---|
| Which endpoint serves data? | `display/message` v13, or BLE — unknown | **BLE branch is taken**, because `BLE_X` matches; it POSTs to the **v6** advertised endpoint |
| What does that endpoint return when empty? | never observed | **400 `{"message":"Bad Request"}`** |
| Is the bridge's BLE body shape wrong? | suspected | **no evidence of that** — six shapes including minimal all 400 identically |
| Username source | "server-reported, falling back to configured" | **server never reports it**; the configured value is the sole source (and is required) |

## Open, and only validation day can close it

- Does the v6 advertised endpoint serve data at all, or does the bridge fall
  through to `display/message` v13?
- On a delivering pump, does the BLE POST 200 with `patientData`, or still 400?
- Is `buildEndpointCandidates()`' v13-first ordering ever reached on a
  patient-account BLE device, given the BLE branch pre-empts it?

**9 requests. No further probing is meaningful without a sensor.**
