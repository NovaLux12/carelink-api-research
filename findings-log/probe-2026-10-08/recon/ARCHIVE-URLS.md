# ARCHIVE-URLS.md — historical URL/endpoint record from public web archives

**Date:** 2026-10-09 · **Subagent pass:** passive archive-only recon
**Method:** Wayback CDX API + a small number of Wayback *replay* fetches.
**Requests to Medtronic/MiniMed: ZERO.** No DNS lookups, no TLS, no HTTP to any
`*.minimed.*` or `*.medtronic.*` host. Every request in this pass went to
`web.archive.org`. Common Crawl was **not** needed (Wayback answered everything).

**File ownership:** this pass owns `recon/cdx/` and this file. Another subagent
is concurrently writing `recon/*.md`, `recon/js/`, `recon/bodies/` — untouched.

---

## 0. Request budget

| item | count |
|---|---|
| Wayback **CDX API** requests | **37** (self-imposed cap 40, enforced by `cdx/q.sh`) |
| Wayback **replay** fetches (`/web/<ts>id_/…`) | 4 (2 succeeded, 2 returned archive 404) |
| **Total archive HTTP requests** | **41** |
| Requests to vendor infrastructure | **0** |
| Credentials used / written | **0** |

Rate limiting: ≥3 s between every call (`q.sh` `sleep 3`). Full query log with
exact URLs: `recon/cdx/request-log.tsv`. Counter: `recon/cdx/request-count.txt`.

### Exact CDX queries issued

All against `https://web.archive.org/cdx/search/cdx`.

| # | label | query (params after base) | result |
|---|---|---|---|
| 1 | r01 | `url=carelink.minimed.eu/*&output=json&collapse=urlkey&fl=…&limit=50` | 50 rows (probe; superseded by r01b) |
| 2 | r01b | `url=carelink.minimed.eu/*&…&limit=3000` | **1489 rows** (complete, under limit) |
| 3 | r02 | `url=carelink.minimed.com/*&…&limit=3000` | **949 rows** (complete) |
| 4 | r03 | `url=clcloud.minimed.eu/*&…&limit=3000` | 7 rows |
| 5 | r04 | `url=clcloud.minimed.com/*&…&limit=3000` | 3 rows |
| 6 | r05 | `url=carelinkhp.minimed.eu/*&…&limit=2000` | 308 rows |
| 7 | r06 | `url=carelinkhp-prod.minimed.eu/*&…&limit=1000` | **0 (dry)** |
| 8 | r07 | `url=carelink-trials.minimed.com/*&…&limit=2000` | **504 gateway timeout — retried as r07b** |
| 9 | r08 | `url=clcloud-trials.minimed.com/*&…&limit=2000` | 1 row |
| 10 | r09 | `url=carelink-login.minimed.eu/*&…&limit=1000` | **0 (dry)** |
| 11 | r10 | `url=carelink-login.minimed.com/*&…&limit=1000` | **0 (dry)** |
| 12 | r07b | `url=carelink-trials.minimed.com&matchType=host&…&filter=urlkey:.*(patient\|configs\|connect\|discover\|api).*` | 1 row |
| 13 | r11 | `url=carelink-content.medtronic.com/*&…&limit=800` | 4 rows |
| 14 | r12 | `url=status.minimed.com/*&…&limit=800` | **0 (dry)** |
| 15 | r13 | `url=clcloud-clinical.minimed.com/*&…&limit=800` | **0 (dry)** |
| 16 | r14 | `url=commoncore.minimed.eu/*&…&limit=800` | **0 (dry)** |
| 17 | r15 | `url=clcloudsnp.minimed.eu/*&…&limit=800` | 1 row |
| 18 | r16 | `url=carelink-content.medtronic.com/carepartner/*&…&limit=1500` | 1 row |
| 19 | r17 | `url=minimed.eu&matchType=domain&…&limit=2000&filter=statuscode:200` | **1717 rows** — host inventory |
| 20 | r18 | `url=mdtlogin.medtronic.com/*&…&limit=1000` | 75 rows (⚠ contains archived session tokens, see §7) |
| 21 | r19 | `url=connect.minimed.eu/*&…&limit=1000` | **0 (dry)** |
| 22 | r20 | `url=login.minimed.eu/*&…&limit=1000` | **0 (dry)** |
| 23 | r21 | `url=carelink-subject.minimed.com/*&…&limit=500` | 1 row |
| 24 | r22 | `url=minimed.com&matchType=domain&…&limit=2500&filter=statuscode:200` | 2500 rows — **hit limit, only `www.minimed.com` covered (usvkordered)** |
| 25 | r26 | `url=clcloud.minimed.eu/connect/*&collapse=urlkey&…&limit=1500` | 6 rows |
| 26 | r25 | `url=carelink.minimed.eu/patient/*&fl=…&limit=2500` (**no collapse**) | 434 rows — full capture history |
| 27 | r24 | `url=carelink-stage.minimed.eu/*&collapse=urlkey&…&limit=1200` | 52 rows |
| 28 | r28 | `url=clcloud.minimed.com/connect/*&collapse=urlkey&…&limit=1500` | 2 rows |
| 29 | r29 | `url=carelink.minimed.eu/configs/*&fl=…&limit=1500` | 2 rows |
| 30 | r30 | `url=carelink.minimed.eu/api/*&fl=…&limit=1500` | 2 rows (both 404 noise) |
| 31 | r31 | `url=carelinkhp-test.minimed.eu/*&collapse=urlkey&…&limit=1500` | 273 rows |
| 32 | r32 | `url=mdtlogin-ocl.medtronic.com/*&collapse=urlkey&…&limit=800` | 5 rows (⚠ session tokens) |
| 33 | r33 | `url=commoncore.medtronic.eu/*&collapse=urlkey&…&limit=800` | **0 (dry — notable, see §6)** |
| 34 | r34 | `url=carelink-support.minimed.eu/*&collapse=urlkey&…&limit=800` | 1 row |
| 35 | r35 | `url=carelink-login-trials.minimed.com/*&collapse=urlkey&…&limit=800` | 1 row |
| 36 | r36 | `url=minimed.eu&matchType=domain&collapse=urlkey&…&limit=800&filter=original:.*(discover\|connect/carepartner\|connect/v[0-9]\|configs/v1).*` | 8 rows |
| 37 | r37 | `url=minimed.com&matchType=domain&collapse=urlkey&…&limit=800&filter=original:.*(discover\|connect/carepartner\|connect/v[0-9]\|configs/v1\|patient/).*` | 58 rows |

Replay fetches (`web.archive.org/web/<ts>id_/<url>`):
- `/patient/v2/configuration/public` @20260204132123 → **200, 4482 B gzip → 18834 B JSON**
- `/configs/v1/eu_sso_cp_eu_v6.json` @20260224162224 → **200, 4691 B gzip → 11112 B JSON**
- `/api/connect/v1/client/config/android/whitegraylist` @20250521050536 → archive 404 (never replayed)
- `carelinkhp…/AppConfig.data.service.js` @20201230162805 → archive 404 (never replayed)

---

## 1. Headline: the highest-value NEW find

### `GET /patient/v2/configuration/public` — unauthenticated public config dump

`https://carelink.minimed.eu/patient/v2/configuration/public`
Captured **20260204132123**, still captured **20260926015801** (10 captures).
Archive permalink: <https://web.archive.org/web/20260204132123/https://carelink.minimed.eu/patient/v2/configuration/public>
Local copy: `recon/cdx/replay/v2-configuration-public.json` (18,834 B, 100+ keys).

This is **not** one of the `configs/v1/` SSO configs — it is a separate, wider,
fully-public client configuration document served from the patient host, and it
leaks infrastructure that is invisible to every `*.minimed.*` enumeration.

**Hosts / endpoints published inside it that appear nowhere else:**

| key | value | why it matters |
|---|---|---|
| `nutrino.cc.broker.service.config.host` | `https://commoncore.medtronic.eu/reports-broker/v1` | **NEW host, and on `medtronic.eu` — a different registrable domain from `minimed.eu`.** Invisible to any `*.minimed.*` sweep. Same miss class as the `carelink-content.medtronic.com` find already in PROBE-FINDINGS §4. (PROBE-FINDINGS records `commoncore.minimed.{eu,com}` → 502; this is a *different* name.) |
| `nutrino.cc.metadata.service.config.host` | `https://commoncore.medtronic.eu/reports-metadata/v1` | second service on the same new host |
| `csr.cumulus.periodic.data.endpoints.periodic_packet` | `https://vpce-<eu-id>.execute-api.eu-central-1.vpce.amazonaws.com/dev/connect/csr/v2/periodic/packet` | **AWS VPC-endpoint ID + account-region + `/dev/` path published to the public internet.** An infrastructure-identifier disclosure, not just a URL disclosure. |
| `csr.cumulus.periodic.data.endpoints.display_message` | `https://clcloud.minimed.eu/connect/csr/v2/display/message` | **NEW Cumulus namespace: `csr/v2`** — distinct from `/connect/pde/v3`, `/connect/carepartner/v13`, and the archived `/connect/v2/display/message` |
| `mmm.data.api.url` | `https://0ptoikank6.execute-api.eu-central-1.amazonaws.com/prodous/dialog-lite/v1/` | public AWS API-Gateway id (Nuance "dialog-lite", bot/captcha) |
| `praas.uri.path.reports.ping` | `https://iis.personalace.corp:443/api/report/v2/ping` | **internal corporate hostname (`.corp` TLD, PersonalACE intranet) leaked into a public config** |
| `personal.retina.endpoint.config.target_url` | `https://clcloud.minimed.eu` | ties the `retina` remote-monitoring feature to Cumulus |
| `csr.crm.settings.base.uri` | `https://carelink-support.minimed.eu/crm` | the CSR (Care-Solutions-Rep) CRM — a **second** CRM base distinct from the patient `crm` |

**Other values of operational interest to the bridge:**

- `personal.device.family.to.model.mapping` — the **complete pump model → family map**:
  `BLE770` → MMT-1880/1881/1882/1883 (770G), `BLE780` → MMT-1884/1885/1886 + XCU/XCE/XCF/XCY clinical variants (780G),
  `BLE740` → MMT-1811/1812, `BLE720` → MMT-1809/1810/1817/1818,
  `SIMPLERA` → 27 variants from **MMT-5100** through MMT-5120 incl. `CLX`/`JLX`/`P` clinical suffixes,
  `GST` → MMT-7811, `NMX7`, `NMX8`, `CC840`, `CC880`, `GM`.
  Note the **trailing-whitespace entries** (`"MMT-5100       "`) — a data-hygiene bug that will bite any parser doing exact model matching.
- `logbook.supported.entry.types` = `BLOOD_KETONES, URINE_KETONES, CARBS, EXERCISE, HBA1C, INFUSION_SET_CHANGE, SENSOR_INSERTION, SENSOR_REMOVAL, OTHER`
- `csr.control.codes.settings.predefined_control_codes_regexp` — pump **remote-control code** grammar: `(dpml:[0-3])|(tup:(TUP|LTU|DTU|BGM|GST|NOGSTU|NONE))|(lhpro:\d+)|(lghpro:\d+)|(vex:\d+)|(ssd:(t|f))`; custom codes `(gstpro:\d+)|(gstrc:(t|f))`. This is the closest thing yet to the "NGP alarm/control code vocabulary" open question.
- `personal.integrations.redirect.scheme.whitelist` — the **server-side post-SSO deep-link allowlist** (11 entries): `about`, `minimed`, `com.medtronic.wecare`, `be.aertsbert.wecaredev`, `emea.oscoe.wecaredev`, `com.medtronic.diabetes.wecare.eu`, `com.medtronic.diabetes.wecare.dev`, `inpen`, `https://carelink-3po-dev.minimed.eu/`, `https://fr.ccm.glooko.com/`, `https://xtqa-fr.ccm.glooko.com/`.
  **The bridge's own `com.medtronic.carepartner:/sso` scheme is NOT in this list** — it is a different mechanism (Auth0 Allowed Callback URLs) from this server-side integrations list. Worth recording so nobody conflates them.
- `personal.third.party.apps` — **four data-sharing integrations, three new Auth0 clients/audiences**: `GlookoXT` (audience `GlookoXT`, client_id `pZ8ZK7ck8g8mPp7xJElIaLkAxnc66gTY`), `MyDiabby`, `StenoPool`, `GlookoSolution` — all `consentType: DATA_SHARING`.
  **This falsifies PROBE-FINDINGS §7 "No new Auth0 client_ids"** for the third-party track (the patient client IDs in §4 are unchanged; these are separate clients for export partners).
- `captcha.key` = `<RECAPTCHA-SITE-KEY>` (`type: google`) — public reCAPTCHA v2 site key; `personal.captcha.enable = true`.
- `personal.udi.number` = `(01)00763000984755(10)15.3A` — Medtronic GTIN + version, publicly published.
- `personal.clinical.environment` = `false` — the feature flag that distinguishes patient from trials; PROBE-FINDINGS has no record of it.
- `personal.cp.m2m.enabled` = `true` — matches the live 200 `{"value":"true"}` recorded in PROBE-FINDINGS §5.
- `personal.cp.follow.limit` = `{maxLimit: 5, default: 1}` over 116 countries.
- `personal.countries.certification.enabled` = `[FR, YT, NC, PF]` (French overseas).
- `personal.banner.notifications` leaks an **incident window**: `serversDownTime 2026-01-29T17:00Z → serversUpTime 2026-01-29T17:45Z` — a 45-minute Medtronic outage is published in the client config.
- `config.refetch` = `{frequency: 300000, idleTime: 600000}` (5 min / 10 min).
- `personal.session.timeout` = `30`; `personal.report.generation.settings.maxLimit` = `5`; `personal.linking.request.interval` = `5`.

---

## 2. NEW: paths not in PROBE-FINDINGS.md / AUTH-TENANT-FINDINGS.md

Path families, archive timestamp, and permalink. "New" = absent from both existing
findings documents.

### 2a. New Cumulus / connect namespaces

| path | host | archived | status | permalink |
|---|---|---|---|---|
| `/connect/v2/display/message` | clcloud.minimed.eu | 2022-11-13 | 403 | [wb](https://web.archive.org/web/20221113155802/https://clcloud.minimed.eu/connect/v2/display/message) |
| `/connect/csr/v2/display/message` | clcloud.minimed.eu | via 2026-02-04 config | n/a | (from `v2-configuration-public.json`) |
| `/connect/csr/v2/periodic/packet` | AWS VPCE eu-central-1 | via 2026-02-04 config | n/a | (idem) |
| `/api/connect/v1/client/config/android/{7..14}.0.0` | carelink.minimed.com | 2025-05-21 | 400 | [wb](https://web.archive.org/web/20250521050540/https://carelink.minimed.com/api/connect/v1/client/config/android/13.0.0) |
| `/api/connect/v1/client/config/android/whitegraylist` | carelink.minimed.com | 2025-05-21 | **200** | [wb](https://web.archive.org/web/20250521050536/https://carelink.minimed.com/api/connect/v1/client/config/android/whitegraylist) — archive has the URL but no replayed body; **not re-verified** |
| `/api/header-asset` | **www.minimed.com** | 2026-05-10 → 2026-09-03 | 200 (12 captures) | [wb](https://web.archive.org/web/20260510084931/https://www.minimed.com/api/header-asset) |

### 2b. New patient-API families (all from `carelink.minimed.eu`, mostly captured 2020-09-29 / 2021-03-31)

Account & user:
`/patient/users` (401/405, 2020-09-29→2026-06-15) · `/patient/users/me` · `/patient/users/me/profile` · `/patient/users/me/language` · `/patient/users/me/mfa` · `/patient/users/me/email` · `/patient/users/me/alerts` (401, last **2026-06-15**) · `/patient/users/me/notifications` · `/patient/users/language` · `/patient/users/profile` · `/patient/users/mfa` · `/patient/users/email` · `/patient/users/alerts` · `/patient/users/notifications` · `/patient/users/createUserName` (405)

Auth / SSO:
`/patient/sso/login` (400) · `/patient/sso/reauth` (405) · `/patient/sso/logout` (**307**) · `/patient/mirror` (400) · `/patient/validate/phone` (405) · `/patient/verified/phones` (400)

Care-partner / clinic linking (the pre-`m2m` generation):
`/patient/links/carepartners` (401) · `/patient/links/requests` (401) · `/patient/links/patients` (401) · `/patient/links/patients/current` (401) · `/patient/carePartners` (401) · `/patient/carePartners/changeStatus` (405) · `/patient/clinic/requests` (401)

Registration / username:
`/patient/patientRegistrationCheck/checkUsernameGlobally` (405) · `/patient/orders/reserve/username` (405)

Reports (the generation catalogue that `commoncore.medtronic.eu` now serves):
`/patient/reports/supported` (401) · `/patient/reports/generateReport` (405) · `/patient/reports/reportStatus` (400) · `/patient/reports/favoriteReports` (405) · `/patient/reports/snapshotTimelinesRange` (401) · `/patient/reports/snapshotTimelinesForCalendar` (405) · `/patient/reports/report` (404)

Reference data (all archived **200**, unauthenticated):
`/patient/georegions` · `/patient/languages` · `/patient/countries` · `/patient/countries/mfaStatusForCountry` · `/patient/countries/mfaGracePeriod` · `/patient/countries/account/types` · `/patient/countries/gb/settings` · `/patient/countries/us/settings` · `/patient/configuration/defaultCountry` · `/patient/configuration/messages` · `/patient/consents` (400) · `/patient/data/sharing/display` (401) · `/patient/requestUserEmail` (401) · `/patient/requestPreferences` (401)

Country-settings **query-string shape** (r37, .com only) — genuinely new:
- `?countryCode=us&language=en` — the `language` parameter (EU side only ever captured with a bare `?countryCode=`; the language axis was not previously recorded)
- `?language=en&extraFields=stateCodes` — **`extraFields=stateCodes` on `/patient/countries/us/settings`**: a US-states enumeration parameter.

Configuration keys (all archived **200**, unauthenticated) — the flat key-value namespace:
`personal.captcha.enable` · `personal.udi.number` · `personal.communication.enabled` · `personal.link.help.system` · `personal.link.carepartner.app.download` · `personal.integrations.redirect.scheme.whitelist` · `personal.countries.with.anonymization` · `personal.crm.settings` · `personal.session.timeout` · `personal.mixpanel.analytics.settings` · `personal.application.browser.check.configuration` · `country.reports` · `connect.countriesWithConnect` · `logbook.enabled` · `cms-config.json` · `configuration/recaptcha/{key,type,testkey}`

RUM/telemetry (retired Dynatrace APM agent, archived 2018–2020):
`/patient/dynaTraceMonitor` (200, 18 captures to 2020-04-09) · `/patient/dtagent_ICASTVdegijovx_*.js` (EU) · `/patient/dtagent_A23STVdegijopqrvx_*.js` (US)

### 2c. NEW: the whole legacy `mag` (Layer7) endpoint surface — answers an open question

`AUTH-TENANT-FINDINGS.md` lists "Pre-Auth0 `oauth20_sso_carepartner_*_v6.json` — the legacy Layer7 flow … **Full characterisation pending**." It is now characterised. Source: `recon/cdx/replay/eu-sso-config-v6.json` (archive permalink <https://web.archive.org/web/20260224162224/https://carelink.minimed.eu/configs/v1/eu_sso_cp_eu_v6.json>).

Server: `mdtlogin-ocl.medtronic.com:443`, path prefix **`/mmcl`** (the "mag" = Medtronic Access Gateway stack).

| family | paths |
|---|---|
| OAuth | `/mmcl/auth/oauth/v2/authorize`, `/mmcl/auth/oauth/v2/token`, `/mmcl/auth/oauth/v2/token/revoke` |
| userinfo | `/mmcl/openid/connect/v1/userinfo` |
| session | `/mmcl/connect/session/logout`, `/mmcl/connect/session/status` |
| device registration | `/mmcl/connect/device/register`, `/mmcl/connect/device/register/client`, `/mmcl/connect/device/renew`, `/mmcl/connect/device/remove`, `/mmcl/connect/device/list`, `/mmcl/connect/device/metadata` |
| client init | `/mmcl/connect/client/initialize` |
| enterprise browser | `/mmcl/connect/enterprise/browser` |
| OTP | `/mmcl/auth/generateOTP` |
| demo (still in the shipped config) | `/mmcl/oauth/v2/protectedapi/foo`, `/mmcl/protected/resource/products` |

Identity facts extracted (previously unrecorded):

- **A second CareLink client_id for the legacy track:** `c19218f2-7157-4c93-8fbe-49636e7f9c74` — `"client_name": "OCL - Care Partner App - OUS"`, `redirect_uri com.medtronic.carepartner:/sso`, `client_secret ""` while `client_type: "confidential"` (a confidential client with an empty secret — same shape as the Auth0 public-client oddity already recorded).
- **New scope names:** `msso`, `msso_register`, `msso_client_register` (plus `profile openid roles country`).
- **Token lifetimes:** access `10980 s` (3 h 03 m), refresh `604800 s` (7 d), id_token `604800 s` (7 d).
- **BLE mSSO GATT profile** (relevant to sensor pairing, not previously recorded): service UUID `980c2f36-bde3-11e4-8dfc-aa07a5b093db`, characteristic UUID `980c34cc-bde3-11e4-8dfc-aa07a5b093db`, RSSI threshold `-80`.
- **Weak-mobile-SDK posture flags, publicly shipped:** `enable_public_key_pinning: false`, `trusted_public_pki: false`, `client_cert_rsa_keybits: 1024`.
- **PII leak:** `registered_by: manamr1!` — a Medtronic directory account name, published in a public config for ~4 years.
- The embedded `server_certs` chain is **expired**: leaf `mdts-ocl.medtronic.com` `notAfter 2025-11-19 23:59:59Z`.

### 2d. NEW: archived hosts (passive enumeration only — none were contacted)

| host | evidence | note |
|---|---|---|
| `commoncore.medtronic.eu` | named inside the public 2026-02-04 config | **`medtronic.eu`**, so invisible to `*.minimed.*`. **Zero archive captures** (r33) despite being referenced in a live config — an unarchived live dependency. |
| `mdts-ocl.medtronic.com` | `resource_uri` in the archived mmcl authorize URL | the mag resource server behind the legacy OAuth flow |
| `iis.personalace.corp` | inside the public config | internal `.corp` hostname |
| `vpce-<eu-id>.execute-api.eu-central-1.vpce.amazonaws.com` | inside the public config | AWS VPC-endpoint id |
| `0ptoikank6.execute-api.eu-central-1.amazonaws.com` | inside the public config | AWS API-Gateway id |
| `carelink-3po-dev.minimed.eu` | redirect-scheme whitelist | "3PO" = third-party-organisation dev |
| `fr.ccm.glooko.com`, `xtqa-fr.ccm.glooko.com` | redirect-scheme whitelist | Glooko data-sharing endpoints (EU) |
| `carelinkhp-test.minimed.eu` | r31, 273 archived URLs | the HCP portal's **test** deployment, build **`3.2.339`** vs prod `3.1.326` — a free A/B version datapoint |
| `carelink-stage{1,3}`, `carelink-test`, `carelink-dev`, `carelink-interop-dev`, `carelink-simlab-dev`, `carelink-wl-test`, `carelink-support-stage1-next` `.minimed.eu` | r17 host inventory | passively enumerated from the archive only; **not contacted** |
| `www.carelink.minimed.eu` | r01b/r02 | distinct from `carelink.minimed.eu`; archived 2015–2022, retired |
| `crm.clper.me` | r01b, 404 @2020-12-29 | a dead third-party domain once referenced from the CareLink EU host |
| `carelink-content.medtronic.com/carepartner/<ver>/…` | r11/r16 | content bucket is **version-directory-structured**: `carepartner/3-6-0/IFU/m074407C001_1.zip` — the `3-6-0` matches the bridge's `android/3.6` pin |

`carelinkhp` reclassified: PROBE-FINDINGS §6 calls it an "Angular SPA … Not an API".
The 2020-12-30 archive shows it was, at that generation, an **AngularJS 1.x + Bower +
Foundation app with an explicit REST layer** (`modules/common/service/rest/*.rest.service.js`,
`crm/index.js`, `UserInfoConfirmation.rest.service.js`). By 2026-03-22 it is an
**Angular 17 / webpack** build (`main.ddfde50c658b59b2.js`, `runtime.2f3a88dedd0bae75.js`).
The "returns HTML for every path" observation is a property of the *current* SPA
fallback, not of the host's history.

---

## 3. API-version timeline (from archived URLs only)

| version family | first archived | last archived | what it is | archived evidence |
|---|---|---|---|---|
| `patient/main/*.do`, `patient/entry.jsp` (Struts/JSP) | 2006-05-08 | 2025-11-15 | the original CareLink Personal web app | `/patient/entry.jsp` 63 captures 2006→2025 |
| `patient/*.jsp`, `/patient/registration/register.do` | 2009-01-30 | 2018-10-08 | legacy web tier | 404 from 2009 onward |
| `ipro/hcp/*.jsf` (HCP, JSF/JSF) | 2013-05-17 | 2022-05-13 | the old clinician portal, with `jsessionid` in the URL | `/ipro/hcp/main/home.jsf;jsessionid=…` |
| `patient/dynaTraceMonitor`, `dtagent_*` | 2018-10-08 | 2020-04-09 | Dynatrace RUM | 18 + 6 captures |
| **`/patient/configuration/...` flat key namespace** | **2020-09-29** | **2026-09-26** | the current client-config API | ~40 distinct keys, still captured 10 days ago |
| `crs/ocl/14.01` … `crs/ocl/14.11`, then `crm/ocl/14.12`+ | 2020-12-29 | — | **CMS version dirs; `crs` → `crm` rename between 14.11 (2024-02) and 14.12 (2024-09)** | see §4 table |
| **`/mmcl/…` (mag/Layer7 OAuth)** | **2024-02-26** (URL) / config still shipped **2026-02-24** | 2024-11-27 (URL) | legacy pre-Auth0 SSO, still in the shipped config | r32 |
| **`/connect/carepartner/v6/discover/android/3.1`** | **2026-02-27** | 2026-03-08 | cumulus **v6** — archived as **403**, not 204/401 as the live probe reports for other versions | r03/r04 |
| **`/connect/carepartner/v11/discover/android/3.2,3.3`** | **2026-02-24** | 2026-02-27 | cumulus **v11** (trials tenant) — archived **200** | r03/r04 |
| `/connect/v2/display/message` (bare Cumulus v2) | **2022-11-13** | — | pre-`carepartner` Cumulus namespace, 403 | r03 |
| **`/api/connect/v1/client/config/android/…`** | **2025-05-21** | — | a *third* config mechanism, on `carelink.minimed.com` | r02 |
| **`/patient/v2/configuration/public`** | **2026-02-04** | **2026-09-26** | the public config dump (§1) | r25 |
| `configs/v1/oauth20_sso_carepartner_{us,eu}_v6.json` | 2026-02-27 | — | legacy SSO config, EU **and** US | r29/r37 |
| `configs/v1/{sso_cp_us,eu_sso_cp_eu}_v6.json` | 2026-02-24 | — | **two different filenames for the same role on the two regions** — `sso_cp_us_v6.json` (.com) vs `eu_sso_cp_eu_v6.json` (.eu) | r29/r37 |

**Timeline read (2–3 sentences):** The vendor has run **three parallel, coexisting
config mechanisms** — the flat `/patient/configuration/system/*` key namespace
(2020→now), the versioned `configs/v1/*.json` SSO documents (still shipping, last
captured 2026-02), and the `/patient/v2/configuration/public` JSON dump (2026-02→now)
— plus a fourth, `/api/connect/v1/client/config/android/*` (2025-05, .com only).
The only **API-version** churn visible in the archives is inside the Cumulus
`/connect/carepartner/{v6,v11}` discovery axis and it is *not* monotonic with time:
all six archived `discover` captures cluster in a single 6-week window
(2026-02-24 → 2026-03-08), i.e. the archive has effectively **no time-series** for the
API-version axis — it is a snapshot of one crawler sweep, not a history.
Consequently the archives **neither confirm nor refute** that `android/3.6` → cumulus
`v13` is the live generation; they simply never captured a `v13` discover URL at all.
The one genuine *generational* timeline the archive does support is the CMS
`crs/ocl` → `crm/ocl` rename and the CMS version ladder `14.01 → 15.5`.

---

## 4. CMS version ladder (a real dated series — the strongest timeline in this pass)

`crs` → `crm` rename; `ocl` = "CareLink" product code. Both dirs also carry
`cms-config.json`, `i18n/app/en.json`, `i18n/sso/en.json`, `media/config/{gb,us}.json`.

| version | host | first archived | last archived |
|---|---|---|---|
| `crs/ocl/14.01` | carelink.minimed.eu | 2020-12-29 | 2021-01-08 |
| `crs/ocl/14.02` | carelink.minimed.eu | 2022-06-18 | 2024-06-20 |
| `crs/ocl/14.03` | carelink.minimed.com | 2022-03-29 | 2022-03-30 |
| `crs/ocl/14.06` | .eu + .com | 2021-11-10 | 2025-05-06 |
| `crs/ocl/14.9` | carelink.minimed.eu | 2023-06-28 | 2023-09-07 |
| `crs/ocl/14.10` | carelink.minimed.eu | 2023-10-03 | 2023-10-03 |
| `crs/ocl/14.11` | carelink.minimed.eu | 2024-02-26 | 2024-02-26 |
| `crm/ocl/14.12` | carelink.minimed.eu | 2024-09-12 | 2024-09-12 |
| `crm/ocl/14.13` | .eu + .com | 2024-11-27 | 2024-11-27 |
| `crm/ocl/15.0` | carelink.minimed.eu | 2025-03-19 | — |
| `crm/ocl/15.1` | .eu + .com | 2025-07-25 | — |
| `crm/ocl/15.3` | carelink.minimed.eu | **2026-02-04** | — |
| `crm/ocl/15.4` | carelink.minimed.eu | 2026-06-15 | 2026-07-20 |
| `crm/ocl/15.5` | carelink.minimed.eu | **2026-09-26** | — |

Cross-check: the public config captured 2026-02-04 declares
`personal.crm.settings.version = "15.3"`, and `15.3` is the first `crm/ocl` capture in
the archive (2026-02-04). **Two independent sources agree on the same date and version** —
a genuine, non-circular confirmation that the archive record and the live config agree.

---

## 5. Full API-path family table

4238 distinct normalised path families across all 37 CDX results; **201** are
API/config/auth-shaped (201 is the number this pass's conclusions rest on — the
other ~4000 are asset hashes, locale dirs and scanner noise). Full machine-readable dump: `recon/cdx/f-eu.txt`,
`recon/cdx/f-com.txt`, `request-log.tsv`. Representative rows (all `.minimed.eu`
unless noted; status codes as archived, **not** as measured live today):

| path family | first | last | codes | NEW? |
|---|---|---|---|---|
| `/patient/v2/configuration/public` | 2026-02-04 | 2026-09-26 | 200 | **YES** |
| `/patient/configuration/system/personal.application.browser.check.configuration` | 2020-12-29 | 2026-09-26 | 200 | YES |
| `/patient/configuration/system/personal.integrations.redirect.scheme.whitelist` | 2020-12-29 | 2020-12-29 | 200 | **YES** |
| `/patient/configuration/system/logbook.enabled` | 2024-11-27 | 2025-07-25 | 200 | YES |
| `/patient/configuration/system/personal.crm.settings` | 2020-12-29 | 2025-07-25 | 200 | YES |
| `/patient/configuration/system/personal.mixpanel.analytics.settings` | 2023-06-28 | 2025-07-25 | 200 | YES |
| `/patient/configuration/system/personal.session.timeout` | 2020-12-29 | 2025-07-25 | 200 | YES |
| `/patient/configuration/system/country.reports` | 2020-09-29 | 2021-11-05 | 200 | YES |
| `/patient/configuration/system/connect.countriesWithConnect` | 2020-09-29 | 2021-11-05 | 200 | YES |
| `/patient/configuration/recaptcha/{key,type,testkey}` | 2020-12-29 | 2021-03-31 | 200 | **YES** |
| `/patient/configuration/defaultCountry` | 2020-09-29 | 2025-07-25 | 200 | YES |
| `/patient/configuration/messages/{lang}` | 2021-01-08 | — | 200 | YES |
| `/patient/countries`, `/patient/georegions`, `/patient/languages` | 2020-09-29 | 2026-09-26 | 200 | YES |
| `/patient/countries/settings` | 2020-09-29 | 2026-09-26 | 200,400 | known (PROBE §5) |
| `/patient/countries/{gb,us}/settings` | 2024-02-26 / 2024-11-27 | 2026-09-26 | 200 | **YES** |
| `/patient/countries/mfaStatusForCountry` · `mfaGracePeriod` · `account/types` | 2020-09-29 | 2021-03-31 | 200/400/401 | YES |
| `/patient/consents` | 2020-09-29 | 2021-03-31 | 400 | YES |
| `/patient/sso/{login,reauth,logout}` | 2020-09-29 | 2021-03-31 | 400/405/**307** | YES |
| `/patient/mirror` | 2020-09-29 | 2020-12-30 | 400 | YES |
| `/patient/validate/phone` · `/patient/verified/phones` | 2020-09-29 / 2021-03-31 | — | 405 / 400 | YES |
| `/patient/users/me/*` (profile,language,mfa,email,alerts,notifications) | 2020-09-29 | 2026-06-15 | 401/405 | partly YES |
| `/patient/users/{alerts,notifications,createUserName,mfa,email,language,profile}` | 2020-09-29 | 2023-10-03 | 401/405 | YES |
| `/patient/links/*`, `/patient/carePartners*`, `/patient/clinic/requests` | 2020-09-29 | 2021-03-31 | 401/405 | YES |
| `/patient/reports/*` (7 paths) | 2020-09-29 | 2021-03-31 | 400/401/404/405 | YES |
| `/patient/requestUserEmail` · `/patient/requestPreferences` | 2020-09-29 | 2021-03-31 | 401 | YES |
| `/patient/data/sharing/display` | 2020-09-29 | 2021-03-31 | 401 | YES |
| `/patient/orders/reserve/username` · `patientRegistrationCheck/checkUsernameGlobally` | 2020-09-29 | 2021-03-31 | 405 | YES |
| `/patient/dynaTraceMonitor` · `/patient/dtagent_*` | 2018-10-08 | 2020-04-09 | 200 | YES |
| `/patient/entry.jsp` (Struts) | 2006-05-08 | 2025-11-15 | 200/302 | YES (retired) |
| `/connect/v2/display/message` | 2022-11-13 | — | 403 | **YES** |
| `/connect/carepartner/{v6,v11}/discover/android/*` | 2026-02-24 | 2026-03-08 | 200/403 | known |
| `/api/connect/v1/client/config/android/*` | 2025-05-21 | — | 400/200 | **YES** |
| `/api/header-asset` (www.minimed.com) | 2026-05-10 | 2026-09-03 | 200 | **YES** |
| `/configs/v1/*.json` (4 filenames) | 2026-02-24 | 2026-02-27 | 200 | partly YES |
| `/crm/ocl/*`, `/crs/ocl/*` (14 versions) | 2020-12-29 | 2026-09-26 | 200/404 | YES |
| `/ipro/hcp/*` (JSF, with `jsessionid`) | 2013-05-17 | 2022-05-13 | 200/302 | YES (retired) |
| `/mmcl/auth/oauth/v2/authorize/login` | 2024-02-26 | 2024-11-27 | 200/400 | **YES** |
| `/reporter/secure/ReportServer/*.pdf` (JasperReports) | 2025-05-28 | 2025-05-28 | 404/- | YES — ~55 distinct report IDs |
| `/patient/users/me`, `/patient/monitor/data`, `/patient/m2m/*` | — | — | — | known (PROBE §5/§9) |

---

## 6. Hosts that were archived and are now DEAD / retired

Determined **purely from archive evidence** — no DNS or HTTP was sent to any vendor
host, because that would breach this pass's constraint. "Dead" therefore means
*archived-then-broken*, not *verified NXDOMAIN today*. Verifying live status is a
job for a pass that is allowed to touch the vendor.

| host / path | last archived evidence | assessment |
|---|---|---|
| `www.carelink.minimed.eu` | 2015-09-08 → 2022-02-20, all `200`/`302`/`404` | retired alias; distinct name from `carelink.minimed.eu` |
| `carelink.minimed.{eu,com}/patient/main/login.do`, `*.jsp`, `/patient/entry` (bare) | 404 from 2009/2018 | Struts web tier retired ~2020 |
| `carelink.minimed.{eu,com}/patient/dynaTraceMonitor`, `/patient/dtagent_*` | last capture **2020-04-09** | Dynatrace APM retired |
| `crm.clper.me` | **404** @2020-12-29 | dead third-party domain |
| `mdtlogin-ocl.medtronic.com/` (root) | **500** `text/xml` @2025-07-27 | the legacy mag edge's root is broken |
| `mdtlogin.medtronic.com/` (root) | **500** @2025-07-27 | the other legacy `.medtronic.com` login edge is broken (PROBE-FINDINGS §7 already calls this edge "dead") |
| `mdtlogin.medtronic.com/mdtv2/auth/oauth/v2/authorize/login` | 401-redirect @2021-09-16 → **2025-12-09** | last capture Dec 2025; the flow's own config says leaf cert expired 2025-11-19 |
| `carelinkhp.minimed.eu/robots.txt` | **404** @2022-03-17 | no robots.txt even now |
| `clcloud.minimed.eu/` root | **403** `application/json` @2024-11-26 | still JSON-403, not HTML — consistent with an API-only edge |
| **`commoncore.medtronic.eu`** | **ZERO archive captures** despite being a live dependency in the 2026-02-04 public config | the most interesting unknown: a live, publicly-advertised Medtronic host that **no one has ever archived**. A genuinely new reconnaissance gap. |
| `status.minimed.com` | **ZERO archive captures** | PROBE-FINDINGS §7 records it live (200 `__geo`); it simply is never crawled |
| `carelink-login.minimed.{eu,com}` | **ZERO archive captures** | Auth0 login hosts are never crawled (robots/Auth0 block crawlers) — expected, but it means the archive has **no** record of the tenant surface |
| `carelinkhp-prod.minimed.eu`, `connect.minimed.eu`, `login.minimed.eu`, `commoncore.minimed.eu`, `clcloud-clinical.minimed.com` | **ZERO archive captures** | dry |
| `carelink-login-trials.minimed.com/` root | **403** @2024-09-17 | was 403 at root in 2024; now serves a full `openid-configuration` (AUTH-TENANT-FINDINGS §1) — a real historical drift |

---

## 7. ⚠ Archived session material found in the archive (do not copy these files)

Two CDX result sets — `cdx/r18.json` (mdtlogin.medtronic.com) and `cdx/r32.json`
(mdtlogin-ocl.medtronic.com) — contain **archived OAuth authorize URLs carrying
session material in the query string**. This is a public archive property, not
something this pass caused, but it is a genuine historical security finding and it
is why the raw files must not be pasted anywhere.

Observed shapes (values deliberately **not** reproduced):

- `mdtlogin.medtronic.com/mdtv2/auth/oauth/v2/authorize/login?action=display&sessionID=<uuid>&sessionData=<JWE>&locale=…`
  `sessionData` is a **JWE**, header `{"typ":"JWT","cty":"JWE","alg":"dir","enc":"A128CBC-HS256"}` — encrypted, so the payload is not readable from the archive, but the `sessionID` is a live-looking UUID in a public URL. 401 archived captures, 2021-09-17 → 2025-12-09.
- `mdtlogin-ocl.medtronic.com/mmcl/auth/oauth/v2/authorize/login?action=display&sessionID=<uuid>&sessionData=<JWS>&locale=&countrycode=`
  `sessionData` here is an **HS256 JWS whose payload is plaintext base64url** and decodes to the whole authorization request: `sessionID`, `exp`, `current_username`, `consent`, `client_name` (`OCL-+-WebApp+-+OUS`), `scope_verified` (`openid+profile+roles`), `client_id` (`f3310f93-e8c1-4719-ae9c-69d6588e235`), `prompt`, `redirect_uri` (`https://mdts-ocl.medtronic.com/`), `id_token_hint`, `nonce`, `acr_values`.
  **The whole authorization request is in the URL and is not confidential** on this legacy edge. 2 captures, 2024-02-26 and 2024-09-12.

Takeaway for the project: the pre-Auth0 Layer7 login puts full authorization state
in the URL, which is by construction crawler-visible. That is a plausible
contributor to why these URLs are in public archives today, and it is a category of
exposure the Auth0 track no longer has.

---

## 8. Coverage limits — what I did NOT get to, and why

1. **`minimed.com` domain sweep is incomplete.** r22 hit its 2500-row `limit` and
   `urlkey` ordering meant it only ever covered `www.minimed.com` (1922 rows) —
   the API hosts on `.com` were never reached by that query. Mitigated for
   `/patient/*`, `/configs/*`, `/connect/*` by the targeted r37 query, but a full
   `.com` host inventory does not exist in this pass. **Reason: the 40-request cap.**
2. **`carelink-trials.minimed.com` is only 1 URL deep.** The full-prefix query (r07)
   returned a **504 gateway timeout** and the retry (r07b) had to be regex-filtered
   down to `patient|configs|connect|discover|api` to get any answer at all. Any
   trials-host URL outside that regex is unknown.
3. **`*.medtronic.com` / `*.medtronic.eu` domain sweeps: not done at all.** Only
   four named `medtronic` hosts were queried (`carelink-content`, `mdtlogin`,
   `mdtlogin-ocl`, plus `medts-ocl` discovered late). Given that
   `commoncore.medtronic.eu` turned out to be a live dependency that a `*.minimed.*`
   sweep cannot see, **a `medtronic.eu` / `medtronic.com` domain sweep is the single
   highest-value follow-up.** **Reason: the cap, and the `minimed.com` sweep already
   consuming it.**
4. **No archived replay for `/api/connect/v1/client/config/android/whitegraylist`**
   or the `carelinkhp` `AppConfig.data.service.js`. Both URLs are in CDX with `200`
   but the archive has no replayable body. **Reason: out of replay budget; would
   need another 2 archive requests.** The `carelinkhp` REST base URL is therefore
   still unconfirmed from the archive — the sibling subagent's
   `recon/js/JS-API-SURFACE.md` has it from the live bundle instead.
5. **No time-series for the Cumulus API-version axis.** Only 6 archived `discover`
   captures exist, all inside 2026-02-24 → 2026-03-08. There is **no archived `v13`
   discover URL at all**, so §3's API-version timeline cannot be extended. This is a
   property of the archive, not a coverage gap in this pass.
6. **`filter=statuscode:200` on r17 and r22** means the `.eu`/`.com` host inventories
   in this pass omit hosts whose only captures are non-200. The `commoncore.medtronic.eu`
   "zero captures" finding in §6 was confirmed separately with a filter-free query (r33).
7. **Dev/stage hosts enumerated but not queried.** `carelink-stage{1,3}`,
   `carelink-test`, `carelink-dev`, `carelink-interop-dev`, `carelink-simlab-dev`,
   `carelink-wl-test`, `carelink-support-stage1-next` appear in the archive host
   inventory. Deliberately **not** enumerated further, consistent with the project's
   standing rule that dev/stage hosts are passively listed only.
8. **Common Crawl was not consulted.** Not a failure — Wayback answered every
   pattern asked of it. Worth one `index.commoncrawl.org` pass only for the
   `*.medtronic.{eu,com}` gap in (3).
9. **Nothing was checked live.** Every status code in this document is a **2020–2026
   archive observation**, not a measurement. Several entries (e.g. `/patient/users/me/alerts`
   last seen 401 on 2026-06-15) are recent enough to be *probably* still true, but that
   is an inference, not a fact.
10. **Two hosts named in the public config were never archive-checked**:
    `0ptoikank6.execute-api.eu-central-1.amazonaws.com` and
    `vpce-<eu-id>.execute-api.eu-central-1.vpce.amazonaws.com`.
    A `dev`-stage AWS VPC endpoint is a slightly more sensitive thing to poke at than
    a marketing host, so it was left alone deliberately.