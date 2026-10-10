# Medtronic CareLink URL probe — 2026-10-08

**Scope:** every host/path the project touches or might touch, plus the host
families found passively since the 2026-08-22 baseline.
**Method:** read-only, unauthenticated, low-rate (~1.2s between requests).
No credentials used. Nothing written to Medtronic. No dev/stage/QA hosts
actively probed (enumerated passively only).
**Delta vs baseline:** +7 weeks.

Checks that reproduce this live in `hurl/` (`./hurl/run.sh`, 19 assertions,
exit 0 = surface unchanged).

---

## 1. Host inventory (passive: crt.sh CT logs)

476 certs for `%.minimed.eu`, 1192 for `%.minimed.com` → **345 unique names**.

Four families are **new since August** and had never been probed:

| Family | What it turned out to be |
|---|---|
| `carelinkhp*.minimed.eu` | Angular SPA **health portal** — returns HTML for every path, not an API |
| `commoncore*.minimed.{eu,com}` | **502** — backend not serving |
| `clcloudsnp*.minimed.{eu,com}` | **Static-resource server** (Spring-style), 500 `No static resource ...` |
| `carelink-support*.minimed.{eu,com}` | 404 on the discovery path — not the patient API |

**Not publicly reachable** (so out of scope):
- `carelinkhp.minimed.com`, `carelinkhp-prod.minimed.com`, `clcloud-clinical.minimed.com` → NXDOMAIN (DNS absent; cert-only names)
- `carelink-prod.minimed.com` (144.15.206.166), `carelink-clinical.minimed.com` (144.15.206.180) → Medtronic-internal IPs, TLS handshake hangs

Everything else in the CT logs is dev/stage/test/uat/qa/loadlab — deliberately
**not** actively probed.

## 2. TLS posture (tlsx)

- All live prod hosts: **TLS 1.3, key exchange `X25519MLKEM768`** — a
  post-quantum hybrid KEM. New observation; August noted only the cipher.
- Issuer: DigiCert Global G2 TLS RSA SHA256 2020 CA1.
- **Mass cert rotation happened today (nbf 2026-10-08):** `clcloud.{eu,com}`,
  `carelink.{eu,com}`, `clcloudsnp.{eu,com}`, `carelink-trials-support`.
- **Renewal watch:** `clcloud-trials.minimed.com` expires **2026-10-28** (20 days);
  `status.minimed.com` expires 2026-12-02.

## 3. Discovery matrix

Both `clcloud.minimed.eu` and `clcloud.minimed.com` **and `clcloud-trials.minimed.com`
serve a byte-identical document** (sha256 `f8488626…`). The hostname does not
select the region — the doc is global and carries all three `CP` entries;
`src/login.ts` picks by `region`. So `buildDiscoveryUrl(isUS)`'s eu/com split
is **cosmetic**.

`CP[]` order is `US, EU, CLINICAL`.

| android/ | cumulus | `UseSSOConfiguration` | regions |
|---|---|---|---|
| 3.4 | v11 | *absent* | US+EU+CLINICAL |
| **3.5** | **v11** | **Auth0SSOConfiguration** | US+EU+CLINICAL |
| 3.6 | v13 | Auth0SSOConfiguration | US+EU+CLINICAL |
| 3.7 | v13 | Auth0SSOConfiguration | US+EU+CLINICAL |
| 3.8 | v13 | Auth0SSOConfiguration | US+EU+CLINICAL |
| **3.9** *(new cell)* | v2 | *absent* | US+EU |
| 4.0–4.2, 5.0 | v2 | *absent* | US+EU |

**Deltas vs 2026-08-22:**
- **`android/3.5` now returns `UseSSOConfiguration=Auth0SSOConfiguration`.**
  August recorded the Auth0 family as 3.6/3.7/3.8. 3.5 is a *near miss*: it
  selects the Auth0 config but points at **cumulus v11**, so it is still not a
  usable fallback. Pin stays `android/3.6`.
- **`android/3.9` is a new cell** — cumulus v2, no Auth0 track.

### ⚠️ Code finding: the ADR 0002 pin guard no longer holds

`selectAuth0ConfigUrl()` does `const key = cpEntry.UseSSOConfiguration ?? 'Auth0SSOConfiguration'`.
The `Auth0SSOConfiguration` **key now exists on every version** 3.4→5.0,
including the cumulus-v2 no-Auth0 cells, even where `UseSSOConfiguration` is absent.

So bumping `DISCOVERY_APP_VERSION` to `android/4.0` would **not** throw
`NoAuth0SSOConfigurationError` — it would resolve the same Auth0 config URL and
fail later at the data call, with no named error. The runtime guard the ADR
relies on is currently inert; the pin is protected only by the ADR text and the
discovery test.

Suggested fix (not applied — repo change, needs your call): gate on
`baseUrlCumulus` containing `/v13` too, not just on the presence of the key.

## 4. Auth0 / OIDC surface

| Tenant | Login host | client_id | audience |
|---|---|---|---|
| US | carelink-login.minimed.com | `0FGoNwY0SP8ZmESYSfEOgMw03c58c1hk` | `carepartner.patient.us` |
| EU | carelink-login.minimed.eu | `PeAhkbhQWlQRxJiQxWfcFBiGus1lxfe9` | `carepartner.patient.ous` |
| **CLINICAL** | carelink-login-trials.minimed.com | — | **`carepartner.patient.cl`** *(newly recorded)* |

Identical `.com`/`.eu` OIDC docs modulo host. Advertised:

- **Grants:** `client_credentials, authorization_code, refresh_token, password,
  implicit, device_code, token-exchange, password-realm, passwordless/otp,
  mfa-oob, mfa-otp, mfa-recovery-code, jwt-bearer`
- **PKCE:** `S256, plain` · **token endpoint auth:** incl. `none`
- **DPoP:** `ES256` · **backchannel logout:** `true`
- **JWKS:** `/.well-known/jwks.json` → 200, two RSA RS256 keys per region,
  *different* kids for `.com` vs `.eu`. (Plain `/jwks.json` is 404 — that is
  simply the wrong path, not a drift.)
- **New endpoints advertised:** `/bc-authorize`, `/mfa/challenge`,
  `/oidc/register`, `/oauth/global-token-revocation/connection/{connectionName}`
- Legacy `oauth20_sso_carepartner_us_v6.json` still 200 but names
  `mdtlogin.medtronic.com` (dead edge, expired embedded cert). Fetching it via
  the `.eu` host → 403 S3 AccessDenied: configs remain hostname-scoped.

## 5. Patient data API — **four** live surfaces, not two

| Surface | Unauth response |
|---|---|
| `carelink.minimed.{eu,com}/patient/*` | 401 `{"error":{"type":"InvalidToken","group":"AUTH"}}` — **what the bridge uses** |
| `carelink.minimed.{eu,com}/api/carepartner/v2/*` | 401 InvalidToken — **what the discovery doc's `baseUrlCareLink` actually declares** |
| `clcloud.minimed.{eu,com}/connect/carepartner/v13/*` | 401 `{"message":"Authentication failure"}` — cumulus namespace |
| `clcloud.minimed.{eu,com}/connect/pde/v3/*` | **403** `{"message":"Missing Authentication Token"}` — PDE v3, untouched by us |

> **CORRECTED 2026-10-09.** The live probe in this session returned
> **403**, and this note recorded it as **401**. Two re-probes since (same
> session, same UA, low rate) returned **403** with the identical body,
> both times. The published doc was "corrected" from 403 to 401 off the
> back of this note, so the wrong number is this file's and it propagated
> downstream from here. The 403 is a **gateway-level** rejection — on
> `clcloud.*` that body means the host does not route the path to a
> CareLink-app auth check at all — and is distinct from the
> `401 {"error":{"type":"InvalidToken"}}` the bridge's own endpoints
> return. `/patient/users/me` on clcloud behaves the same way.
> See `audit/CLAIM-AUDIT-2026-10-09.md` for the re-probe record.

1 and 2 have **different base paths** and both are live. Only the hybrid
`/api/carepartner/v2/patient/*` 404s (as in August).

Endpoint-by-endpoint:

| Path | Status | Note |
|---|---|---|
| `/patient/users/me` | 401 | **drift corrected** — August recorded 404; back to the documented 401 |
| `/patient/monitor/data` | 401 | `Allow: HEAD, GET, OPTIONS` — GET works, bridge POSTs |
| `/patient/connect/data` | 401 | no `Allow` header |
| `/patient/m2m/links/patients` | 401 | |
| `/patient/users/me/profile` | 401 | **newly confirmed live** (from the xDrip teardown list) |
| `/patient/dataUpload/recentUploads` | 405 | **newly confirmed live**, `Allow: POST, OPTIONS` |
| `/patient/configuration/system/personal.cp.m2m.enabled` | **200** | **NEW public unauthenticated endpoint** → `{"value":"true"}` |
| `/patient/configuration/system/{mobileEnabled,ble.enabled,uploaderAllowed}` | 404 | only the first key exists |
| `/patient/countries/settings?countryCode=GB` | 200 | unchanged |

## 6. Open question for November validation

The bridge calls bare `/patient/*`, but the discovery doc declares
`baseUrlCareLink = https://carelink.minimed.{eu,com}/api/carepartner/v2`.
Both return 401 unauthenticated. **Which one actually returns data with a valid
token?** Cannot be answered without credentials — top item for authenticated
validation, ideally via a mitmproxy capture of the real app.

Other validation items: whether `monitor/data` GET vs POST changes the payload;
whether `/patient/users/me/profile` and `/patient/dataUpload/recentUploads`
carry anything the bridge wants; whether PDE v3 is where the Instinct/Cumulus-v2
data path lives.

## 7. What did NOT change

`status.minimed.com/__geo` → 200 `{"country":"GB"}` (its `/` is now a full
Angular SPA rather than a bare JS shell). The legacy-OAuth edge stays dead.
No new Auth0 client_ids. The three-region structure is unchanged.

---

# Deep pass — second round, 2026-10-08 (later same day)

Still read-only, unauthenticated, low-rate. Assertions from this round were
promoted into `hurl/04-deep-surface.hurl`; the full suite is now **36
assertions across 4 files, all green**.

## 1. device_code grant: DEFINITIVELY REJECTED ← answered an open question

August flagged this as "advertised in OIDC metadata, reportedly rejected by the
CareLink client_id — untested". Tested with `oauth2c` against both tenants using
the public client_ids and no secret:

```
POST /oauth/device/code   (EU client PeAhkbhQWlQRxJiQxWfcFBiGus1lxfe9)
403 {"error":"unauthorized_client",
     "error_description":"Grant type 'urn:ietf:params:oauth:grant-type:device_code' not allowed for the client."}
POST /oauth/device/code   (US client 0FGoNwY0SP8ZmESYSfEOgMw03c58c1hk)
403  same
```

No device code was created — rejected server-side. **The grant is advertised but
not enabled for this client, on both tenants.** Confirms the community report.
Implication: a CareLink client must use the authorization_code + refresh_token
pair; there's no simpler headless path.

## 2. Discovery has TWO independent axes

The URL `/connect/carepartner/{basePath}/discover/android/{version}` varies on
two orthogonal things:

- **Base path = which deployment/tenant.** `v13` → the patient API.
  `v11` → a **trials deployment**: *all three* regions (US, EU, CLINICAL) are
  returned the **trials** tenant (`carelink-trials` / `clcloud-trials`), not
  the patient one. So "v11" doesn't mean "older API" — it's a different tenant.
  `v10` → 204 (exists, empty). `v12` → 401 `Authentication failure`.
  `v14/v15/v16/v20` → 403 `Missing Authentication Token`.
- **App version = which cumulus the returned doc references.**

| basePath | who it serves |
|---|---|
| `v10` | 204, empty body |
| `v11` | **trials tenant, all regions** |
| `v12` | 401 (auth-gated) |
| `v13` | **the patient API** (what we use) |
| `v14`+ | 403 (gateway-gated) |

## 3. Full discovery version matrix (23 cells, all HTTP 200)

| android/ | cumulus | UseSSOConfiguration | regions |
|---|---|---|---|
| 1.0, 2.0, 2.5, 3.0 | v2 | — | 2 |
| 3.1 | **v6** | — | 2 |
| 3.2 | v11 | — | 2 |
| 3.3, 3.4 | v11 | — | 3 |
| **3.5** | **v11** | **Auth0SSOConfiguration** | 3 |
| **3.6, 3.7, 3.8** | **v13** | **Auth0SSOConfiguration** | 3 |
| 3.9, 3.10, 4.0, 4.1, 4.2, 4.3, 4.5, 4.8, 5.0, 6.0, 10.0 | v2 | — | 2 |

**`3.6/3.7/3.8` are the only Auth0+cumulus-v13 cells, full stop.** 3.5 is Auth0
but v11. New cells vs August: 1.0, 2.0, 2.5, 3.0, 3.1 (cumulus **v6** — a track
nobody had recorded), 3.2, 3.3, 3.10, 4.3, 4.5, 4.8, 6.0, 10.0. The enum is
open-ended (10.0 still 200).

## 4. `baseUrlCms` is a different domain entirely — on `medtronic.com`

The discovery doc's `baseUrlCms` is `https://carelink-content.medtronic.com/carepartner`
— note **`.com` with no `minimed`**, so it was invisible to every `*.minimed.*`
enumeration. It's an S3 bucket: `/carepartner` → **403 AccessDenied**,
`/carepartner/configs/v1/*.json` → 403 AccessDenied, `/` → 200 HTML.
The config JSONs the bridge actually fetches are served by
`carelink.minimed.eu/configs/v1/…` (200) — that host fronts them, not this one.

Also confirmed again: `carelink.minimed.com` serving the **EU** config
(`carepartner_auth0_ous_sso_config_v1.json`) → **403**. Configs are
hostname-scoped. And the v11 doc revealed a **second** legacy config name
(`oauth20_sso_carepartner_eu_v6.json`) alongside the `_us_` one.

## 5. Endpoints that are POST-only (a GET-only probe reads them as dead)

This matters methodologically — I initially recorded `/oauth/revoke` as 404.

| Path | GET | POST | Verdict |
|---|---|---|---|
| `/oauth/revoke` | 404 | **401 `invalid_client`** | **live, POST-only** |
| `/oidc/logout` | 200 HTML | 200 HTML | live |
| `/userinfo` | 401 `Unauthorized` | — | live |
| `/connect/session/status` | 404 | 404 | **advertised in the SSO config but genuinely absent** |
| `/oauth/global-token-revocation/connection/Auth0` | 404 | — | advertised in OIDC doc, absent |
| `/oidc/register` | 404 | — | absent |
| `/bc-authorize` | 404 | — | absent |

## 6. `carelinkhp` / `commoncore` / `clcloudsnp` — classified

- `carelinkhp.minimed.eu` → Angular **SPA** ("health portal"), returns HTML for
  every path. Not an API. `carelinkhp.minimed.com` is NXDOMAIN.
- `commoncore.minimed.{eu,com}` → **502** on every path.
- `clcloudsnp.minimed.{eu,com}` → static-resource server, 500
  `No static resource carepartner/v13/discover/…`.

## 7. Host enumeration widened a lot

`subfinder` (passive, multi-source) found **599 names** vs crt.sh's 345; **240
resolve** publicly. Most new ones are dev/stage/test noise, and I did **not**
probe them. Two new *classes* worth recording:

- **Internal infrastructure** (resolvable but not for us): `grafana.<internal>.minimed.com`,
  `k8s.<internal>.minimed.com`, `gitlab.<internal>.minimed.eu`, `prometheus.<internal>.minimed.eu`,
  `<internal>.minimed.com.*`, `other internal hosts`, `other internal hosts`. Recorded, deliberately untouched.
- **Medtronic-internal IPs that hang on TLS** (not publicly reachable):
  `carelink-prod.minimed.com` (144.15.206.166), `carelink-clinical` (.180),
  `carelink-support-prod` (.165), `origin.carelink.minimed.eu` (144.15.107.20),
  `www.minimed.eu` (144.15.107.20). These are the **real origins behind
  CloudFront** — worth a future look only if the public path is ever wrong.

`carelink-subject.minimed.com` is a **301 redirect to `carelink-trials.minimed.com`**
("Data management for people living with diabetes") — a marketing alias, not an API.
CloudFront edge is **LHR95-P3** (London).

## 8. Country settings — all 109 entries swept, properly this time

The earlier sweep conflated "key absent" with "value false" (jq `//` swallows
`false`). Re-derived with `has()`:

- `cpMobileAppAvailable` **present in 72 / 109** entries; **only AU is `true`**.
  The other 71 are explicitly `false`.
- **37 entries have no such key at all**: AD AL AM AW BO **CLINICAL** CW EC
  **GB GE IE IN** JM KE KR KZ MD ME MK MT MU MY NI **NZ** PE PH PK PY **SA**
  SG TH TT UY UZ VN XK YT. So GB isn't "not yet available" — it's *unconfigured*.
- `defaultDevice` is **`GM` in all 108 real countries** — no Simplera/780G
  device family anywhere yet.
- `uploaderAllowed` is **`true`** in all 108.
- One of the 109 "countries" is **`CLINICAL`** — a pseudo-region in
  `supportedCountries`, with no device/language data. Don't count it as a country.
- Languages per country: 1–4 (6 countries have 3, two have 4).

**Bottom line for the pre-pump watch: nothing has changed.** No country has
flipped to `cpMobileAppAvailable=true` besides AU, and no country has a
non-`GM` default device.

## 9. New live patient-API paths

`/patient/m2m/connect/data/gc/patients/{username}` → **401 InvalidToken (live)**.
This is the guardian-connect data surface from the xDrip teardown, never probed
before. The `/{username}/last24hours` suffix shape is 404.

## 10. Cumulative request budget

Two probe rounds today, ~500 requests total to Medtronic, all GET-or-empty-POST,
all unauthenticated, all ≥1.2s apart. No credentials, no writes, no dev/stage
hosts touched.

## 7. Discovery version axis consolidated (2026-10-09)

Probed 10 further cells with no prior record — `android/` 3.11, 3.12, 4.9, 5.1,
6.1, 7.0, 8.0, 9.0, 11.0, 12.0. **All 200. All legacy: no `Auth0SSOConfiguration`,
`baseUrlCumulus` = `/connect/carepartner/v2`, and the `CP[]` array has only
`US,EU` — no `CLINICAL` entry at all** (contrast: 3.6–3.8 carry `US,EU,CLINICAL`).

**The axis serves exactly TWO documents.** After normalising, every legacy cell
(3.11 … 12.0) is byte-identical to every other; the only differing key is the
echoed request string:

```
"config": "android,3.11"   vs   "config": "android,12.0"
```

So the "enum is open-ended" note is now bounded: the version axis is not a
meaningful dial past 3.8. Probing a new version number only re-derives one of
two known documents. **No new Auth0+v13 fallback exists** — 3.6/3.7/3.8 remain
the only cells on the track the bridge uses.

### Third legacy config filename variant

The legacy EU block names a config we had not recorded:

```
"SSOConfiguration": "https://carelink.minimed.eu/configs/v1/eu_sso_cp_eu_v6.json"
```

with `baseUrlCareLink` on **CareLink API v1** and `baseUrlPde` on **PDE v1**
(both a major version below what the bridge uses). This is a third naming
variant alongside `oauth20_sso_carepartner_{us,eu}_v6.json` and the previously
recorded `sso_cp_us_v6.json`. The legacy EU block also carries **no `baseUrlCms`**
— that key is Auth0-family-only.

### Consolidated matrix

| Cells | Auth0 | Cumulus | CLINICAL | Doc |
|---|---|---|---|---|
| 3.6, 3.7, 3.8 | yes | v13 | yes | auth0 doc (what the bridge uses) |
| 3.5 | yes | **v11** | yes | auth0 doc, wrong cumulus |
| 3.9–12.0 (and ≤3.4) | no | v2 | **no** | legacy doc |

## 8. Subdomain expansion (agent, 2026-10-09) — and a poisoned namespace

Full detail: `recon/RECON-SUBDOMAINS.md` + `recon/known-names.json`.
subfinder passive, 7 seeds, 4028 names collected, 21 HTTP GETs, 3 TLS
handshakes, one request per host, low rate.

### ⚠️ `*.carelink.eu` is a POISONED namespace — do not report names from it

`carelink.eu` is **wildcard DNS on a domain-parking operator**
(`ns1.abovedomains.com`). *Every* name under it resolves — including randomly
generated, definitely-unregistered strings — and all of them 302 to the same
parking target:

```
superset.carelink.eu  → 103.224.182.253 → ww38.carelink.eu
admin.carelink.eu     → 103.224.182.253 → ww38.carelink.eu
```

`clcloud.eu` is likewise a parked, unrelated Dutch company. **All 49 names under
`carelink.eu` / `carelink.com` / `clcloud.eu` in the collected set are false
positives.**

This matters beyond tidiness: these two seeds were in the original brief as
Medtronic domains. Reporting anything from them in a disclosure would be a
demonstrably false positive against a named vendor. Treat the whole
`*.carelink.{eu,com}` and `*.clcloud.eu` space as unusable for attribution.

### A FOURTH Auth0 tenant

`carelink-login.medtronic.com` serves a live OIDC document with **identical
OAuth policy** to the three known tenants but **different JWKS kids**
(`cEgK74…`, `80YhF8…`). The `.medtronic.com` half of the shadow deployment was
never enumerated — an earlier `crtsh-medtronic.com` query had returned a
150-byte error page and was recorded as a dead end.

This **updates an open question**: SECURITY-FINDINGS asks whether a shadow-tenant
token would be accepted by the patient host. That question now has **four**
candidate issuers, not two:

```
carelink-login.minimed.eu      (patient, EU)
carelink-login.minimed.com     (patient, US)
carelink-login.medtronic.eu    (shadow)
carelink-login.medtronic.com   (shadow)
```

Separate issuers + separate keys say no; loose `kid`/`aud` validation at the
patient host would say yes. Still needs a token to answer, and the open question
is now larger than when it was written.

### The leaked-key bundle is served from a second host

`carelink.medtronic.com` is a health-portal SPA serving **byte-identical**
content to `carelinkhp.minimed.eu` (same sha256, same
`main.fb5f8cb7eb60c4d5.js`). `carelink-support.medtronic.com` serves the same
document.

So the bundle analysed in `SECURITY-FINDINGS.md` S3 — the one carrying the
hardcoded `x-api-key` and the `dev.commoncore.medtronic.eu` build-config bug —
is reachable on **two** hosts, and the `.medtronic.com` one was outside the
scope that originally found it. A finding that reads as one host's mistake is
in fact replicated across the shadow deployment.

### New host family: Minimed Outcomes

`usminimedoutcomes`, `ousminimedoutcomes`, `minimedoutcomes-usapi` — never
mentioned in any prior file. All on `144.15.x.x`, all `http=000` from the public
net (consistent with every other internal-looking name already recorded). Logged,
not probed.

### Honest negatives

- **`*.minimed.eu`, `*.minimed.com`, `*.medtronic.eu`: nothing new.** 213 + 385 +
  129 names collected, 0 new. Saturated for passive CT enumeration — do not
  re-run this technique expecting more.
- Cert SAN recursion gained nothing; all three `.medtronic.com` certs are
  single-SAN.
- **No RFC1918 exposure and no unauthenticated data.** Zero of 260 focus names
  resolved to a private address; every API-shaped request returned 401/403 or
  SPA HTML.

### Correction to the brief's own baseline

The task brief said "~345 names already known". That figure is stale — a second
probe round the same day recorded **599**, and those artefacts are still on disk.
The baseline was rebuilt from every pre-existing file (**678** names, with
per-name provenance in `known-names.json`). Diffing against the stale 345 would
have inflated ~254 already-known names as "new".
