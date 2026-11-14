# The discovery pin and Strategy 2 work; Strategy 1 cannot work at all (2026-11-14)

**Evidence class: OBSERVED.** Authenticated requests against a live CareLink
account, plus one unauthenticated `npm run login` run on macOS.

**Requests issued by this pass: 11 of a 20 cap** — 6 unauthenticated (discovery,
SSO config, `/authorize`, the `/u/login` page) and 5 authenticated
(`/patient/users/me` twice, `/api/carepartner/v2/users/me`, and the two
token-bearing probes). **One `POST`** to `/oauth/token` as part of the PKCE
exchange. **Delay:** ≥2 s between requests. **Credential:** a real account token,
obtained during this pass and never recorded here; the password was read from
1Password at run time and never written to disk or printed.

**Scope limit — read this before citing anything below.** The pump was paired to
the operator's phone but **not delivering**, and no sensor was active. **No pump
data was fetched.** Everything about payload shape, endpoints, `markers[]`,
`sgs` and timestamps remains unknown. This pass settles auth and identity only.

---

## 0. Why this area exists

Issue #12 has carried two "cheapest authenticated checks" since October, and the
README's own framing says the identity path is "unverified — it is the first
authenticated check in ROADMAP.md". Both are now answerable because a real
account logged in for the first time.

It also produced two defects in carelink-bridge, one of which had been silently
shipping since v0.2.0.

---

## 1. The discovery pin still works — CLOSED

```
GET https://clcloud.minimed.eu/connect/carepartner/v13/discover/android/3.6
→ HTTP 200
```

SSO config: `https://carelink.minimed.eu/configs/v1/carepartner_auth0_ous_sso_config_v1.json`

The pin is `android/3.6` (`DISCOVERY_APP_VERSION`). This was last demonstrated
by a third party in September 2026 on v0.2.0 using terminal-paste; it is now
demonstrated directly.

**A measurement worth keeping:** `ssoConfig.server.hostname` is
**`carelink-login.minimed.eu`** — a *different host* from the config file that
describes it (`carelink.minimed.eu`). `baseUrl` must be built from the former.
A probe that uses the config file's own origin gets `404` on `/authorize`, which
is a convincing-looking and completely wrong "finding" — I made exactly this
mistake first and it cost a diagnostic round.

## 2. Strategy 2 (browser login) works — CLOSED, first recorded success

```
Opening browser window...
Log in to CareLink in the browser window...
Got authorization code
Exchanging code for tokens...
Got tokens
Saved to logindata.json
```

`logindata.json` written with mode `0600`.

**MFA did not appear**, and the reason is recorded server-side rather than
guessed: `GET /patient/users/me` returns `mfaRequired: false, mfaEnabled: false`
for this account. The roadmap's assumption that strategy 2 is needed *because*
MFA blocks strategy 1 is therefore wrong twice over — see §4.

## 3. The identity namespace question — CLOSED (both answer)

Issue #12 asked which of these returns data with a valid token:

```
GET https://carelink.minimed.eu/patient/users/me            → 200, 349 B, role PATIENT_OUS
GET https://carelink.minimed.eu/api/carepartner/v2/users/me  → 200, 384 B, role PATIENT_OUS
```

**Both answer, with the same role.** So the namespace distinction the bridge was
built around is real on the wire but does not gate data for this account, and
the bridge's choice of `/patient/*` is correct rather than merely untested.

`/patient/users/me` (identifiers redacted):

```json
{
  "loginDateUTC": "2026-11-11T23:46:05+0000",
  "country": "GB", "language": "en",
  "role": "PATIENT_OUS",
  "cpRegistrationStatus": null,
  "accountSuspended": null,
  "needToReconsent": false,
  "mfaRequired": false, "mfaEnabled": false
}
```

**This is a PATIENT account.** Consequence, and it is load-bearing for #12 §A:
`getConnectData()` branches to `fetchAsCarepartner()` only on `CARE_PARTNER*`, so
`PATIENT_OUS` falls through to `fetchAsPatient()`. The carepartner path —
`fetchAsCarepartner`, `/patient/m2m/links/patients` — **cannot be exercised on
this account**, which means the `lastDeviceFamily` capture in #12 §A is
unreachable here. Only two of the three device-family fields can be captured:
`deviceFamily` from `monitor/data` and `medicalDeviceFamily` from
`display/message`.

## 4. Strategy 1 cannot work, and ARCHITECTURE.md said it did — FALSIFIED

The doc claimed the automated path *"works for most accounts without CAPTCHA"*.
Measured:

```
GET  https://carelink-login.minimed.eu/authorize?…  → 302 /u/login?state=…
GET  /u/login?state=…                              → 200, 95,520 bytes
     <title>Sign in to CareLink™ Personal</title>
     hidden inputs: ['state', 'captcha']
     password input: yes
     username input: yes
     <form> element:  NONE
```

**Auth0's Universal Login renders its form in JavaScript.** The served HTML
contains no `<form>` element and no `<form action>` attribute. `loginAutomated()`
scrapes `type="hidden"` inputs and POSTs to the form action; with no form there
is nothing to scrape and nowhere to POST, so it throws *"Could not extract
authorization code from redirect chain"* — a message that points at redirects
and not at the real cause.

This is not account-specific and not a CAPTCHA gate: it fails **before** MFA is
reached, and would fail identically for any account. Making it work means
executing Auth0's client bundle or reimplementing Universal Login — a much
larger job than an HTTP scrape, against a moving target.

## 5. Token shape — CONFIRMED

| Field | Value |
|---|---|
| access lifetime | 179 min (≈3 h) |
| claims | `token_details, iss, sub, aud, iat, exp, scope, azp` |
| `token_details.roles` | `["patient_ous"]` |
| `token_details.country` | `GB` |
| audience | `carepartner.patient.ous` |
| client_id | `PeAhkbhQWlQRxJiQxWfcFBiGus1lxfe9` |
| scope | `openid profile offline_access` (refresh token present) |

## 6. Defect found in carelink-bridge: the token could not be saved on macOS

The first OAuth run succeeded end-to-end and then failed on the write:

```
Got tokens
[error] Login failed — ENOENT: no such file or directory,
        open '.../logindata.json.tmp'
```

Writable directory, no tmp file present. Reproduced in isolation:

```
openSync(path, 0o100|0o1|0o200, 0o600)  → ENOENT
openSync(path, 'w', 0o600)              → OK
openSync(path, 'wx', 0o600)             → OK
```

`writeLoginDataAtomic` hardcoded Linux numeric flags, with a comment asserting
*"Node does not expose a numeric constants export for these flags"* — false;
`fs.constants` exists. Measured constants:

| | Linux | macOS |
|---|---|---|
| `O_CREAT` | 64 | **512** |
| `O_WRONLY` | 1 | 1 |
| `O_EXCL` | 128 | **2048** |

The Linux bitmask on macOS gives `open()` no valid create flag, so it returns
`ENOENT` — which reads as a permissions problem and is not one. Fixed in
carelink-bridge `9141357`.

**Why the test suite missed it:** every test runs on Linux, where the hardcoded
values are correct. A test added alongside the fix also passes on Linux *with
the bug present*. This class is only catchable by running on the platform, which
is the argument for a macOS job in CI rather than another unit test.

## 7. Defect found: login opened a throwaway browser profile

`puppeteer.launch()` without `userDataDir` mints a fresh temp profile each run —
no saved passwords, no password-manager extension. The operator hand-copied a
25-character password from 1Password every attempt. Fixed in carelink-bridge
`(PR #152)`: honours `CARELINK_BROWSER_PROFILE`, opt-in.

**Caveat recorded with the fix:** a reused profile means a successful browser run
is not proof the credential step executed, because a retained session can carry
it. Anyone reproducing §2 should use a clean profile if they mean to prove
authentication rather than just obtaining a token.

---

## What this pass does NOT settle

Everything requiring the pump to be delivering. A 780G with a battery in and no
sensor uploads nothing, and CareLink shows an empty account while looking
perfectly healthy:

- which data endpoint serves an Instinct-era 780G
- whether `sgs` arrives under `patientData`, and whether `kind` is present
- 204 vs 200 vs 206 with a real device
- timestamp correctness (`relativeOffset`, the quarter-hour offset guess)
- whether `sensorState`, `limits[]`, `markers[]` are populated at all
- the device-family values — and note §3 above has *reduced* what §A can capture
  to two fields, not three

**Requests: 11.** No further probing is warranted until the pump is delivering;
every remaining question needs data that does not yet exist.
