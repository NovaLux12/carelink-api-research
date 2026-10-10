# Config-namespace recon — 2026-10-09

Subagent pass on the public `configs/v1/` namespace of the Medtronic CareLink
surface, plus the CLINICAL region block. Read-only, unauthenticated, GET-only,
no POST, no auth headers, no writes to the vendor.

**Request cap: 30. Used: 22. Stayed under cap — 8 unused.**
≥2 s between consecutive requests to the same host. No brute force, no wordlist,
no fuzzing: 13 explicitly-justified sibling filenames, each requested once.

Machine-readable matrix: `recon/matrix.jsonl` (22 rows).
Raw bodies: `recon/bodies/` (only 200s and the interesting negatives are kept).
Scripts: `recon/probe.sh` (rate limiter + cap), `phase-ab.sh`, `phase-cd.sh`, `phase-e.sh`.

> **File ownership note.** `recon/` is being written to concurrently by another
> subagent doing passive CT-log/subfinder hostname enumeration. Everything from
> *this* pass is: `CONFIG-NAMESPACE.md`, `probe.sh`, `phase-ab.sh`, `phase-cd.sh`,
> `phase-e.sh`, `matrix.jsonl`, `bodies/`. The files `build-known.py`, `diff.py`,
> `resolve.py`, `known-names.*`, `sf-*.txt`, `cdx/`, `js/`, `raw/` are **not** mine —
> I left them untouched. Request counts in this document cover only this pass.

> Credential hygiene: no `x-api-key` value appears in any body captured in this
> pass, so nothing had to be redacted. Every `client_secret` in both config
> families is the empty string. Nothing in this directory is a credential.

---

# ANSWER TO TARGET 1 — the CLINICAL base URL question

**Answered from the already-saved discovery document — zero requests needed.**
`recon/bodies/A1-clcloudtrials-disc` and the three pre-existing captures are all
md5 `403220ced1a7837372b777fa97ecbb2b`, and all contain the CLINICAL block.

Verbatim CLINICAL entry:

```json
{
  "region": "CLINICAL",
  "SSOConfiguration": "https://carelink-trials.minimed.com/configs/v1/oauth20_sso_carepartner_us_v6.json",
  "Layer7SSOConfiguration": "https://carelink-trials.minimed.com/configs/v1/oauth20_sso_carepartner_us_v6.json",
  "Auth0SSOConfiguration": "https://carelink-trials.minimed.com/configs/v1/carepartner_auth0_cl_sso_config_v1.json",
  "UseSSOConfiguration": "Auth0SSOConfiguration",
  "baseUrlCms": "https://carelink-content.medtronic.com/carepartner",
  "baseUrlCareLink": "https://carelink-trials.minimed.com/api/carepartner/v2",
  "baseUrlCumulus": "https://clcloud-trials.minimed.com/connect/carepartner/v13",
  "baseUrlPde": "https://clcloud-trials.minimed.com/connect/pde/v3",
  "baseUrlAem": "https://www.medtronic.com/content/dam/emc"
}
```

### The question: `carelink-trials.minimed.com` or `clcloud-trials.minimed.com`?

**It depends on which service — and the split is by service, not by tenant.**

| key | CLINICAL host | note |
|---|---|---|
| `baseUrlCareLink` | `carelink-trials.minimed.com` | the patient app API |
| `baseUrlCumulus` | **`clcloud-trials.minimed.com`** | ← the answer for Cumulus |
| `baseUrlPde` | **`clcloud-trials.minimed.com`** | ← the answer for Pde |
| `baseUrlCms` | `carelink-content.medtronic.com` | global, identical in all 3 regions |
| `baseUrlAem` | `www.medtronic.com` | global, identical in all 3 regions |

So for the two keys asked about: **both `baseUrlCumulus` and `baseUrlPde` are
`clcloud-trials.minimed.com`, not `carelink-trials.minimed.com`.** The trials
tenant is `carelink-trials` for the app/API plane and `clcloud-trials` for the
cumulus/PDE compute plane — exactly mirroring the US (`carelink.minimed.com` /
`clcloud.minimed.com`) and EU (`carelink.minimed.eu` / `clcloud.minimed.eu`) pairs.
The naming is consistent across all three regions; only the region code differs.

This is the same `carelink-*` (app) / `clcloud-*` (compute) pattern the
`AUTH-TENANT-FINDINGS.md` CLINICAL open question was asking about. It is now closed.

### Discovery path on the CLINICAL host family

| host | path | result |
|---|---|---|
| `clcloud-trials.minimed.com` | `/connect/carepartner/v13/discover/android/3.6` | **200**, 20256 B, `application/json`, md5 identical to `.eu`/`.com` |
| `carelink-trials.minimed.com` | same path | **404**, 196 B, `text/html`, Apache/2.4.62 (RHEL) behind CloudFront |

So the discovery document is served only by the `clcloud-*` hosts, exactly as for
US and EU. `carelink-trials` hosts configs only, not the discovery document.
The 404 body is a stock Apache page:

```html
<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>404 Not Found</title>
</head><body>
<h1>Not Found</h1>
<p>The requested URL was not found on this server.</p>
</body></html>
```

---

# TARGET 2 — the legacy pre-Auth0 `oauth20_sso_carepartner_*_v6.json` family

All three URLs the discovery document declares for `SSOConfiguration` /
`Layer7SSOConfiguration` return **200 JSON** (8.2 KB each). Fully characterised.

| field | US | EU | CLINICAL |
|---|---|---|---|
| `server.hostname` | `mdtlogin.medtronic.com` | `mdtlogin-ocl.medtronic.com` | `mdtlogin.medtronic.com` |
| `server.port` | 443 | 443 | 443 |
| `server.prefix` | `mmcl` | `mmcl` | `mmcl` |
| `client.client_id` | `d596e4ae-b713-4f6d-913a-b39dc3e23acf` | `4fb211b8-f130-4398-b51e-28900bf68527` | `0afb9353-e2d4-4f9a-9425-0f7634e6ecde` |
| `client.client_secret` | `""` | `""` | `""` |
| `client.scope` | `profile openid roles country` | same | same |
| `client.redirect_uri` | `com.medtronic.carepartner:/sso` | same | same |
| `client.audience` | **absent** | **absent** | **absent** |

```json
"system_endpoints": {
  "authorization_endpoint_path":   "/auth/oauth/v2/authorize",
  "token_endpoint_path":           "/auth/oauth/v2/token",
  "token_revocation_endpoint_path":"/auth/oauth/v2/token/revoke",
  "usersession_logout_endpoint_path": "/connect/session/logout",
  "usersession_status_endpoint_path": "/connect/session/status"
},
"oauth_protected_endpoints": {
  "userinfo_endpoint_path": "/openid/connect/v1/userinfo"
}
```

The three regions are identical **except** `server.hostname` and
`client.client_id`. `server_certs[1]` and `[2]` (the DigiCert chain) are
byte-identical across all three; `server_certs[0]` is the pinned leaf and differs
only between the US/CL pair and the EU one.

### Auth0 vs legacy, field by field — this is the interesting comparison

| | legacy `oauth20_…_v6` | current `carepartner_auth0_…_v1` |
|---|---|---|
| `server.prefix` | `mmcl` | `""` |
| `client_id` shape | **UUID** (`d596e4ae-…`) | 32-char Auth0 id (`PeAhkb…`) |
| `client_secret` | `""` (public) | `""` (public) |
| `client.scope` | `profile openid **`roles`** **`country**` | `profile openid **`offline_access`** |
| `client.audience` | **absent** | `carepartner.patient.{us,ous,cl}` |
| `configuration_endpoint_path` | **absent** (no `.well-known`) | `/.well-known/openid-configuration` |
| authorize | `/auth/oauth/v2/authorize` | `/authorize` |
| token | `/auth/oauth/v2/token` | `/oauth/token` |
| revoke | `/auth/oauth/v2/token/revoke` | `/oauth/revoke` |
| logout | `/connect/session/logout` | `/oidc/logout` |
| session status | `/connect/session/status` | `/connect/session/status` |
| userinfo | `/openid/connect/v1/userinfo` | `/userinfo` |

### What this implies

1. **No different data-plane base URLs.** The legacy config contains *only* auth-server
   coordinates — no `baseUrlCumulus`/`baseUrlCareLink`/`baseUrlPde`. Those live only in the
   discovery document, which is region- and version-selected independently of the SSO
   config. So the legacy config says **nothing** about the pre-Auth0 *API/data* shape.
   Anyone expecting an older endpoint list here will not find one.
2. **The pre-Auth0 auth model genuinely was different** — and differently in kind, not
   degree. It is Layer7/CA-gateway OAuth v2 under an `/mmcl` prefix with an
   **opaque-token + `roles`/RBAC** model: no JWT `audience` anywhere, and `roles`/`country`
   explicitly in scope. The current flow is a JWT-`audience` model. That is a different
   authorisation primitive, not a renamed endpoint — which is the substantive reason the
   bridge implements only Auth0. Note also the legacy scope **lacks `offline_access`**:
   the old flow appears to have had no refresh token, so it would have meant re-login
   per session. `src/carelink/token.ts`'s use of `grant_type: refresh_token` depends on a
   capability the legacy flow did not have.
3. **CLINICAL reuses the *US* legacy config filename**, not a `_cl_` one — and that is
   deliberate, not a gap: the CLINICAL legacy body has its **own distinct client_id**
   (`0afb9353-…`) despite carrying the `_us_` filename and the US `server.hostname`.
   Confirmed independently: `oauth20_sso_carepartner_cl_v6.json` → **403** (C1 below).

### Is it stale? Yes, and measurably so

- **Both declared auth hosts refuse TCP connections.** `mdtlogin.medtronic.com`
  (144.15.232.38) and `mdtlogin-ocl.medtronic.com` (144.15.111.12) both resolve publicly
  but `connect:errno=111` — **connection refused on :443**. The legacy flow cannot work
  at all today. The bridge implementing only Auth0 is not a preference; it is forced.
  *(This is more precise than `PROBE-FINDINGS.md` §4's "dead edge, expired embedded
  cert" — nothing is listening; there is no TLS handshake to fail.)*
- **The pinned leaf certificates are long expired:**

  | config | leaf CN | notBefore | notAfter | expired for |
  |---|---|---|---|---|
  | v6 US + CLINICAL | `mdtsts.medtronic.com` | 2025-02-19 | **2026-03-06** | 217 days |
  | v6 EU | `mdtsts-ocl.medtronic.com` | 2024-11-07 | **2025-11-19** | 325 days |
  | v5 US (new, see below) | `mdtsts.medtronic.com` | 2024-02-15 | **2025-03-06** | 590 days |

- **The pinned leaf CN does not match the declared hostname.** Config says
  `server.hostname: mdtlogin.medtronic.com`; the pinned leaf says
  `CN=mdtsts.medtronic.com`. Cert pinning as shipped would fail on hostname grounds
  even if the cert were current.
- **There is no version or date field anywhere in the JSON.** No schema version, no
  `updatedAt`, no etag in the body. The embedded cert dates are the *only* staleness
  signal available. Best bound derivable: last touched at the March 2026 cert roll at
  the very latest; the EU copy looks frozen since November 2025.

---

# TARGET 3 — bounded sibling filenames

13 candidates, each requested once, each derived from a token observed in an
already-known filename. Observed vocabulary:

- service prefixes: `oauth20_sso_carepartner`, `carepartner_auth0`
- region keys: `us`, `eu` (legacy family) · `us`, `ous`, `cl` (auth0 family)
- version tokens: `_v6` (legacy) · `_sso_config_v1` (auth0)

| # | candidate | justification from observed convention |
|---|---|---|
| C1 | `oauth20_sso_carepartner_cl_v6.json` | legacy family + auth0's `cl` region key; discovery points legacy@CL at `_us_`, so does `_cl_` exist anyway? |
| C2 | `oauth20_sso_carepartner_ous_v6.json` | legacy family + auth0's `ous` key (does EU legacy use `eu` or `ous`?) |
| C3 | `oauth20_sso_carepartner_us_v7.json` | next legacy version |
| C4 | `oauth20_sso_carepartner_eu_v7.json` | next legacy version |
| C5 | `oauth20_sso_carepartner_us_v5.json` | previous legacy version (v6 ↔ cumulus v6 in the discovery matrix) |
| C6 | `carepartner_auth0_eu_sso_config_v1.json` | auth0 family carrying legacy's `eu` key instead of `ous` |
| C7 | `carepartner_auth0_us_sso_config_v2.json` | next auth0 version |
| C8 | `carepartner_auth0_ous_sso_config_v2.json` | next auth0 version |
| C9 | `carepartner_auth0_cl_sso_config_v2.json` | next auth0 version |
| C10 | `carepartner_sso_config_v1.json` | bare auth0 form, no region token |
| C11 | `oauth20_sso_carepartner_v6.json` | bare legacy form, no region token |
| C12 | `carepartner_config_v1.json` | third service prefix, bare |
| C13 | `carepartner_auth0_us_sso_config.json` | auth0 family, versionless |

**Result: 1 of 13 exists beyond the known 3.**

### The one hit: `oauth20_sso_carepartner_us_v5.json` → 200, 8259 B, JSON

This is a **genuine finding**. Diffed against `…_v6.json` (US):

```
diff <(jq -S 'del(.server.server_certs)' v6) <(jq -S 'del(.server.server_certs)' v5)
  (no differences)
```

**Every functional field is identical** — `server.hostname`/`port`/`prefix`,
`client_id`, `client_secret`, `scope`, `redirect_uri`, all five `system_endpoints`,
the userinfo path. The *only* difference between v5 and v6 is `server_certs[0]`:

| | v5 | v6 |
|---|---|---|
| leaf CN | `mdtsts.medtronic.com` | `mdtsts.medtronic.com` |
| notBefore | 2024-02-15 | 2025-02-19 |
| notAfter | 2025-03-06 | 2026-03-06 |

**Conclusion: the `_vN` suffix in `oauth20_sso_carepartner_*_vN.json` is a
certificate-rollover generation counter, not an API schema version.** v5 and v6 are
the same configuration one certificate roll apart. Anyone reading `_v6` as "OAuth
v6" or "API v6" is wrong; the auth0 family's `_v1` suffix is probably a
different axis (first generation of that family) and the two suffixes should not
be compared.

### The other 12, and an important caveat

All 12 returned **403 `AccessDenied`, 111 B, `application/xml`**, `server: AmazonS3`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Error><Code>AccessDenied</Code><Message>Access Denied</Message></Error>
```

**This bucket returns `AccessDenied`, not `NoSuchKey`, for keys that do not exist.**
So a 403 here is **indistinguishable from "absent"** and from "present but not
readable". I am reporting these as "no evidence of existence", **not** as
"confirmed non-existent". This matters retrospectively: the recorded observation
that `carelink.minimed.com` returns 403 for the *EU* config was never evidence
that the key is missing from that bucket — it is just what S3 does. The
hostname-scoping conclusion in `PROBE-FINDINGS.md` §4 stands, but the reasoning
underneath it was never actually testing what it appeared to be testing.

---

# TARGET 4 — `baseUrlCms` and `baseUrlAem`

| URL | status | bytes | verdict |
|---|---|---|---|
| `https://carelink-content.medtronic.com/carepartner` | **403** | 111 | `AmazonS3` behind CloudFront, `application/xml` |
| `https://www.medtronic.com/content/dam/emc` | **200** | 1105 | `AkamaiGHost`, `text/html` — but not AEM content |

`baseUrlCms` is a **private S3 bucket**. Verbatim body:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Error><Code>AccessDenied</Code><Message>Access Denied</Message></Error>
```

Confirms `PROBE-FINDINGS.md` §4 and closes the "never probed" open question in
`AUTH-TENANT-FINDINGS.md`. Note `.com` with no `minimed` — which is why it was
invisible to every `*.minimed.*` enumeration.

`baseUrlAem` serves an **Akamai bot-manager interstitial**, not content:

```html
<title>Incorrect Browser</title>
<h1>Oops! It looks like there's an error. Please switch to a different browser and try again. </h1>
<p>Reference ID: 0.471e1202.1791550943.4149e866</p>
```

Marketing AEM dam behind a bot manager. Irrelevant to any data path — this closes
the second "never probed" open question. (It also incidentally publishes a support
mailbox, `DLAEMSUPPORTHELP@medtronic.onmicrosoft.com`, in a public error page.
Not a finding, just noted.)

---

# Full request matrix

22 requests, all GET, all unauthenticated, all ≥2 s apart per host.

| # | label | URL | status | bytes | content-type | verdict |
|---|---|---|---|---|---|---|
| A1 | clcloud-trials discovery | `clcloud-trials.minimed.com/connect/carepartner/v13/discover/android/3.6` | 200 | 20256 | `application/json;charset=utf-8` | byte-identical to `.eu`/`.com` |
| A2 | carelink-trials discovery | `carelink-trials.minimed.com/connect/carepartner/v13/discover/android/3.6` | 404 | 196 | `text/html` | Apache catch-all; not served here |
| B1 | legacy US | `carelink.minimed.com/configs/v1/oauth20_sso_carepartner_us_v6.json` | 200 | 8255 | `application/json` | **new** full characterisation |
| B2 | legacy EU | `carelink.minimed.eu/configs/v1/oauth20_sso_carepartner_eu_v6.json` | 200 | 8279 | `application/json` | **new** full characterisation |
| B3 | legacy CLINICAL | `carelink-trials.minimed.com/configs/v1/oauth20_sso_carepartner_us_v6.json` | 200 | 8255 | `application/json` | **new** full characterisation |
| C1 | legacy cl v6 | `carelink-trials.minimed.com/…/oauth20_sso_carepartner_cl_v6.json` | 403 | 111 | `application/xml` | no evidence of existence |
| C2 | legacy ous v6 | `carelink.minimed.eu/…/oauth20_sso_carepartner_ous_v6.json` | 403 | 111 | `application/xml` | no evidence of existence |
| C3 | legacy us v7 | `carelink.minimed.com/…/oauth20_sso_carepartner_us_v7.json` | 403 | 111 | `application/xml` | no evidence of existence |
| C4 | legacy eu v7 | `carelink.minimed.eu/…/oauth20_sso_carepartner_eu_v7.json` | 403 | 111 | `application/xml` | no evidence of existence |
| C5 | **legacy us v5** | `carelink.minimed.com/…/oauth20_sso_carepartner_us_v5.json` | **200** | **8259** | `application/json` | **EXISTS — genuine finding** |
| C6 | auth0 eu v1 | `carelink.minimed.eu/…/carepartner_auth0_eu_sso_config_v1.json` | 403 | 111 | `application/xml` | no evidence of existence |
| C7 | auth0 us v2 | `carelink.minimed.com/…/carepartner_auth0_us_sso_config_v2.json` | 403 | 111 | `application/xml` | no evidence of existence |
| C8 | auth0 ous v2 | `carelink.minimed.eu/…/carepartner_auth0_ous_sso_config_v2.json` | 403 | 111 | `application/xml` | no evidence of existence |
| C9 | auth0 cl v2 | `carelink-trials.minimed.com/…/carepartner_auth0_cl_sso_config_v2.json` | 403 | 111 | `application/xml` | no evidence of existence |
| C10 | auth0 bare v1 | `carelink.minimed.eu/…/carepartner_sso_config_v1.json` | 403 | 111 | `application/xml` | namespace is region-keyed |
| C11 | legacy bare v6 | `carelink.minimed.com/…/oauth20_sso_carepartner_v6.json` | 403 | 111 | `application/xml` | namespace is region-keyed |
| C12 | carepartner_config_v1 | `carelink.minimed.eu/…/carepartner_config_v1.json` | 403 | 111 | `application/xml` | no evidence of existence |
| C13 | auth0 us no-version | `carelink.minimed.com/…/carepartner_auth0_us_sso_config.json` | 403 | 111 | `application/xml` | no evidence of existence |
| D1 | baseUrlCms | `carelink-content.medtronic.com/carepartner` | 403 | 111 | `application/xml` | private S3 bucket |
| D2 | baseUrlAem | `www.medtronic.com/content/dam/emc` | 200 | 1105 | `text/html` | Akamai bot interstitial, not content |
| E1 | Layer7 US edge | `mdtlogin.medtronic.com/` | 000 | 0 | — | TCP **connection refused** |
| E2 | Layer7 EU edge | `mdtlogin-ocl.medtronic.com/` | 000 | 0 | — | TCP **connection refused** |

Plus non-HTTP: 4 DNS lookups (`mdtlogin*`, `mdtsts*`) and 2 TLS handshakes
against the Layer7 hosts, which do not reach the HTTP layer.

---

# NEW FINDINGS

1. **CLINICAL base URLs resolved.** `baseUrlCumulus` and `baseUrlPde` are both
   `clcloud-trials.minimed.com`; `baseUrlCareLink` is `carelink-trials.minimed.com`.
   Closes the `AUTH-TENANT-FINDINGS.md` open question. Answerable with zero requests
   from the saved discovery doc — it should not have needed a probe.
2. **CLINICAL Auth0 `client_id` recorded: `pfAI1ecGsXWXcAWMQxCP5IU0ChhypH6B`**
   (audience `carepartner.patient.cl`, host `carelink-login-trials.minimed.com`).
   This fills the `—` in `PROBE-FINDINGS.md` §4's table and corrects §7's
   "No new Auth0 client_ids". It was already captured in
   `sso-carepartner_auth0_cl_sso_config_v1.json` on 2026-10-08 but never written up.
3. **`oauth20_sso_carepartner_us_v5.json` exists** (200, 8259 B) and is
   functionally identical to v6 apart from a one-roll-older pinned leaf cert.
   ⇒ **`_vN` = certificate generation, not API version.** The three known configs
   are therefore part of a small ladder, and v4/v3 plausibly exist (not probed —
   out of cap).
4. **The legacy Layer7 auth hosts refuse TCP :443.** `mdtlogin.medtronic.com` and
   `mdtlogin-ocl.medtronic.com` both resolve (144.15.232.38 / 144.15.111.12) but
   nothing is listening. More precise than the recorded "expired embedded cert",
   and it means the legacy flow is structurally dead, not merely misconfigured.
5. **The legacy family has no JWT `audience` and no `offline_access`,** but does
   request `roles` and `country`. The pre-Auth0 model was opaque-token/RBAC under a
   `/mmcl` Layer7 prefix — a different authorisation primitive, not a renamed API.
   Only a login-detail difference; it says nothing about the data plane.
6. **CLINICAL carries its own legacy Layer7 `client_id`** (`0afb9353-…`) inside the
   *US*-named config file, on the *US* `server.hostname`. Filename region key and
   client region are independent.
7. **Methodological correction — S3 returns `AccessDenied`, not `NoSuchKey`,** for
   absent keys on these config buckets. Every 403 in the previous rounds'
   hostname-scoping argument was therefore never distinguishing "absent" from
   "present but not readable". The conclusion (configs are hostname-scoped) still
   holds because it rests on the 200s, not the 403s.
8. **`carelink-trials.minimed.com` serves configs but not the discovery document**
   (404, stock Apache/2.4.62 behind CloudFront). `clcloud-*` serves the discovery
   document. Consistent with US/EU.
9. `baseUrlCms` is a private S3 bucket (403) and `baseUrlAem` is an Akamai-gated
   marketing dam returning an "Incorrect Browser" page (200). Both open questions closed.

---

# ⚠️ NEEDS A MAINTAINER DECISION — do not act on these unilaterally

**Nothing here is exploitable, and nothing new is alarming.** I want to be
explicit rather than manufacture concern. Specifically checked and **clean**:

- no `x-api-key` in any body; **no credentials of any kind** in either config family
- `client_secret` is `""` in **all seven** configs across both families
- no internal hostnames, no `.internal`/`.local` names, no RFC1918 addresses
- no debug flags, no feature toggles, no environment markers
- no PII of any kind

Four items are judgement calls for a human:

1. **`_vN` semantics correction is a documentation fix, not a code fix.** If any
   comment, ADR, or test in `src/` or `docs/` describes `_v6` as an API or OAuth
   version, it is wrong and should be reworded. I have not touched any source —
   repo changes are out of scope for this pass.
2. **The pinned `server_certs[]` are still ignored by the bridge** (`SECURITY-FINDINGS.md`
   S4). Now that the legacy family is characterised, S4 has a sharper edge: the
   `_vN` ladder exists *precisely because* Medtronic rolls the pinned leaf cert,
   so those pins are load-bearing upstream and worthless downstream. Worth weighing
   in the existing S4 discussion; no change proposed here.
3. **Medtronic-side config hygiene (not ours to fix, disclosure-adjacent):**
   the legacy config pins a leaf cert whose CN (`mdtsts.medtronic.com`) does not match
   its own declared `server.hostname` (`mdtlogin.medtronic.com`), and ships expired
   pins. Dead config, so severity is informational at most. Recording it so it is not
   rediscovered; I am **not** recommending disclosure — that is a maintainer call and
   S6 already notes there is no `security.txt` to disclose through.
4. **Whether to spend more of the sibling ladder.** v4/v3 were not probed (cap).
   Given C5 proved v5 exists, probing `…_us_v4.json` and `…_us_v3.json` would test the
   "one roll per version" theory directly. Two requests, near-zero marginal value
   now that the semantic is established. I would **not** bother unless the config
   history itself becomes interesting. Flagging rather than assuming.

---

# Negatives, stated plainly

- 12 of 13 sibling candidates returned 403. I **cannot** distinguish "does not exist"
  from "exists but unreadable" on this bucket, so the honest claim is *no evidence of
  existence*, not *confirmed absent*.
- I did **not** probe v4/v3/v1, other service prefixes beyond one guess
  (`carepartner_config_v1`), or any non-`medtronic.com`/`.eu` TLD. Those are outside
  the stated convention and outside the cap.
- The legacy config gave **no** information about the pre-Auth0 data/API shape. Anyone
  hoping for an older endpoint list from it will be disappointed; that data lives in the
  discovery document, which is selected by app version, not by auth family.
- No conclusion about whether `baseUrlPde` (`/connect/pde/v3`, still 403, untouched)
  is reachable from the CLINICAL tenant. It would now be `clcloud-trials.minimed.com`
  rather than `carelink-trials`, which is the only thing this pass changes about it —
  and it remains a needs-a-real-token question.
