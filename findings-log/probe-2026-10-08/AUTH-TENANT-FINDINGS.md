# Auth0 tenant + SSO-config findings (2026-10-09, unauthenticated)

Round 5 of the research pass. Everything here is read-only, unauthenticated,
publicly-published configuration. No credentials were used. Verbatim bodies are
in `security/` alongside this file.

## 1. Three tenants, one Auth0 org — the shadow hosts are full clones

| Host | `.well-known/openid-configuration` |
|---|---|
| `carelink-login.minimed.eu` (patient, EU) | 200, 2729 B |
| `carelink-login.medtronic.eu` (shadow) | 200, 2753 B |
| `carelink-login-trials.minimed.com` (clinical) | 200 |

Field-by-field comparison across all three: **identical except `issuer`, the
endpoint hostnames derived from it, and `registration_endpoint`**. Same grant
types, same scopes, same claims, same PKCE methods (`S256, plain`), same token
auth methods, same DPoP algs, same response types.

**Consequence:** the clinical/trials tenant needs no separate auth handling.
There is no "clinical login flow" to implement — it is the same tenant with a
different issuer. Worth recording so nobody re-derives it.

## 2. `code_challenge_methods_supported` includes `plain`

Auth0 advertises `S256` **and `plain`** PKCE. The bridge correctly hardcodes
`code_challenge_method: 'S256'` (`src/login.ts`). No change needed — recorded
only so nobody "simplifies" it to the default.

## 3. The bridge authenticates as the official Android app

From the SSO config the discovery document points at
(`carelink_auth0_ous_sso_config_v1.json`, public, no auth):

```
client.client_id    = PeAhkbhQWlQRxJiQxWfcFBiGus1lxfe9   (EU)
client.client_secret =                                  (empty — public client)
client.redirect_uri = com.medtronic.carepartner:/sso    (custom scheme)
client.scope        = profile openid offline_access
client.audience     = carepartner.patient.ous
```

Two things fall out of this:

- **The bridge impersonates the shipped Android client** — its client ID and
  the app's custom-scheme redirect URI. It works only because Auth0's Allowed
  Callback URLs for that client admit that scheme. There is no bridge-owned
  client. If Medtronic ever locks that client's callback list (common hardening
  move: attested app links / package-name binding), the bridge's login breaks
  with an opaque redirect error. This is a structural single point of failure,
  not a bug — but it is worth knowing before a 2 a.m. token failure.
- **`offline_access` IS requested**, so refresh tokens are legitimate and
  `grant_type: refresh_token` (`src/carelink/token.ts`) is the right call.
- **`email` is NOT requested** even though the tenant advertises it in both
  `scopes_supported` and `claims_supported`. So `/userinfo` for this client
  cannot return an email address. Anything that ever wants one must add the
  scope to the *server-side* config, which the bridge does not control.

## 4. Discovery document is byte-identical across all three regions

`GET /connect/carepartner/v13/discover/android/3.6` on `clcloud.minimed.eu`,
`clcloud.minimed.com` and `clcloud-trials.minimed.com` returns three responses
with the **same md5** (20256 B each) — including the CLINICAL region block.

The `CLINICAL` block points at `carelink-trials.minimed.com` for SSO but
**`baseUrlCumulus` and `baseUrlPde` there need checking** — see open questions.

No `x-api-key` header is required for this endpoint. The vendor key recorded in
`SECURITY-FINDINGS.md` is for a different surface.

## 5. Declared-but-unprobed: `/connect/session/status`

The SSO config declares `usersession_status_endpoint_path =
/connect/session/status` on the **login host**. Probed GET and POST with an
empty body: **404 `Not found.` on both.** The bridge never references it either.
So it is either dead config, or it only answers under an authenticated session
with a different method/tenant. Low value — recorded so it is not re-probed.

## Open questions carried forward

- `baseUrlPde` (`/connect/pde/v3`) — 403, deliberately untouched. The NGP alarm
  code vocabulary (#84) probably lives behind it. Needs a real token.
- `baseUrlCms` (`carelink-content.medtronic.com/carepartner`) — never probed.
- `baseUrlAem` (`www.medtronic.com/content/dam/emc`) — marketing content dam,
  almost certainly irrelevant to data but never confirmed.
- Pre-Auth0 `oauth20_sso_carepartner_*_v6.json` — the legacy Layer7 flow the
  bridge deliberately does not implement. Full characterisation pending.
## 6. The `configs/v1` namespace (agent round, 2026-10-09)

Full detail: `recon/CONFIG-NAMESPACE.md`. 22 requests of a stated 30, GET-only,
unauthenticated, ≥2 s apart.

### CLINICAL base URLs — open question CLOSED, at zero request cost

The saved discovery JSON already answered it:

| key | CLINICAL value |
|---|---|
| `baseUrlCumulus` | `https://clcloud-trials.minimed.com/connect/carepartner/v13` |
| `baseUrlPde` | `https://clcloud-trials.minimed.com/connect/pde/v3` |
| `baseUrlCareLink` | `https://carelink-trials.minimed.com/api/carepartner/v2` |

So the trials tenant **splits planes exactly like US and EU**: `carelink-trials`
for the app/API plane, `clcloud-trials` for cumulus + PDE compute. Only
`baseUrlCareLink` uses `carelink-trials`.

*Process note:* this was answerable from data already on disk. Check local
artifacts before spending requests.

### Legacy pre-Auth0 config — a different auth primitive, not a different API

All three `oauth20_sso_carepartner_*_v6.json` are 200 / 8.2 KB, differing only in
`server.hostname` (`mdtlogin` / `mdtlogin-ocl`) and `client_id`. The flow is
**Layer7/CA-gateway OAuth v2 under an `/mmcl` prefix with an opaque token and a
`roles` model — there is no JWT `audience` at all**, and scope is
`profile openid roles country` with **no `offline_access`**.

Two consequences:

1. **The old flow had no refresh token.** So `grant_type: refresh_token` is an
   Auth0-family capability, not something that always worked. Our refresh path
   depends on a capability the legacy track never had — which is a reason the
   Auth0 pin matters, not just a preference.
2. The config carries **no data-plane base URLs**, so it reveals nothing about the
   pre-Auth0 API shape. Only the auth primitive differed.

**Unambiguously dead:** both `mdtlogin*.medtronic.com` hosts resolve publicly but
refuse TCP :443 (errno 111); the pinned leaf certs expired **2026-03-06** (US and
CLINICAL) and **2025-11-19** (EU). The config also pins a cert whose CN
(`mdtsts.medtronic.com`) does not match its own declared hostname.

### `_vN` is a CERTIFICATE-ROLLOVER COUNTER, not an API schema version

`oauth20_sso_carepartner_us_v5.json` → 200, and it is **functionally identical to
v6 in every field** — same `client_id`, same endpoints — differing only in the
pinned leaf cert, one roll older.

This corrects an implicit assumption worth stating explicitly: do not read a
higher `_vN` as a newer API contract. The suffix tracks cert rotation. The other
12 of 13 candidate names returned 403.

### METHODOLOGICAL CORRECTION — 403 is NOT evidence of absence here

This bucket returns **`AccessDenied`, not `NoSuchKey`, for absent keys.** Every 403
is therefore indistinguishable from "exists but unreadable".

This retrospectively undercuts one earlier recorded inference. We had written
"EU config fetched from the `.com` host → 403 AccessDenied → configs are
hostname-scoped." The **conclusion holds** — it rests on the 200s from the correct
host, which are unambiguous. But the 403 was never evidence of *non*-existence,
only of non-readability, so the reasoning as stated was unsound even though the
answer was right. Any future sibling-name sweep must be reported as "no evidence
of existence", never as "confirmed absent".

### Nothing alarming

No credentials in any of the seven configs — every `client_secret` is empty. No
internal hostnames, no debug flags, no PII. The vendor `x-api-key` appears nowhere.
Note that config *filenames* are region-keyed but **client identity is not**: the
CLINICAL region carries its own distinct legacy `client_id` inside a file named
for the **US** region.

## 7. Portal JS bundle — the clinic portal, and what that means (agent, 2026-10-09)

Full detail + 16 evidence artefacts: `recon/JS-API-SURFACE.md`, `recon/js/`.
**Zero network calls** — pure static analysis of the 3.4 MB `hp-main.js` already
on disk. The one `x-api-key` literal inside the bundle is redacted in every
extract.

### The decisive negative — read this before citing the bundle

The bundle contains **zero** occurrences of `/patient/*`, `/connect/carepartner/*`,
`/api/*`, `/pde/*`, `/oauth/*`, `monitor/`, `NGP`, `BLE`, `BLE_MINIMED` or
`medicalDeviceFamily`. And of 13 distinct host literals, **exactly one is
Medtronic's** (`dev.commoncore.medtronic.eu`); the other 12 are Pusher, Mixpanel,
cdnjs, webpjs, w3.org.

So `carelinkhp` is the **clinician portal, not the mobile app**. It is the right
source for `hcp/*` and device tables, and the **wrong** source for #81
(`deviceFamily` vocabulary) or #84 (alarm codes). Those still need a token.

### NEW surface (verbatim, from prior notes)

- **`MMT-8600`, `MMT-8601`** — shipped in the bundle but **absent from the device
  table in the same file**. Used as `S.includes(dM) ? sM : dM`, i.e. for these two
  codes the portal displays the **sensor** model instead of the device model.
  Anyone mapping `deviceModel` → hardware from this table gets these two wrong.
- **`hcp/user/*` — 29 endpoints** (prior notes had 1), incl. `getMfaUserStatus`,
  `verifyMfaCode`, `sendMfaCodeAfterReCaptcha` ⇒ **the portal enforces MFA**; the
  reCAPTCHA site key comes from authenticated `POST hcp/configuration/user`.
- **`hcp/clinics/*` — 40 endpoints** (prior notes had 2), incl. MFA policy,
  security profiles, and **9 unrecorded `toggle/*` kill-switches** (csv,
  patient-dashboard, blinded-cgm, therapy-data, remote-monitoring,
  clinic-outcomes, clinic-user-settings, titr-settings, status).
- **`hcp/patients/{id}/logbook/entries{,/filled,/last}`** — the *read* side of the
  ROADMAP's deferred `markers[]` item. Never recorded before.
- **`hcp/patients/*otc-linking*` — 6 endpoints** + `ext-otc=true&username=` on the
  login redirect. Zero prior mention of `otc`. **Deliberately not guessed at.**
- **`connect/retina`** — an interceptor exempts this one path from the
  `X-System-ID: ProWeb` header every other portal request carries. Its base URL
  is composed from three server-supplied config fields, so the service host is
  reachable only through an authenticated fetch.
- **`hcp/sso/login|logout|reauth` + `hcp/ping/ping`** — a second, **cookie-based**
  session mechanism entirely separate from the mobile `/oauth/*` surface.

### Two code-level observations

- **Pusher channel names are reversible.** `transformedChannelId($){const q=+$;return (q*q+q).toString(16)}`
  — unkeyed, deterministic, invertible. Event `Clinic_Settings_Update` carries
  `{map:{type:"C"|"P", status:…, identifier:<patientId>}}`, so a clinic-scoped
  socket subscriber can derive another clinic's patient identifier. Worth
  recording as a finding against the *portal*, not the bridge.
- **The client discloses its own origin to pick its backend.**
  `loadProductContext(){POST(..., {currentDomainUrl: window.location.origin})}`.

### Device vocabulary — 80 `MMT-*` + 9 `SKU-*`

New vs prior notes: `MMT-8600`, `MMT-8601`, the Paradigm/Revel/Veo batch
(`MMT-515 522 523 551 554 715 722 723 751 754`), and unhyphenated aliases
`MMT5100 MMT5101 CSS7200 CSS7201`.

**The mixed-case trap recurs.** Device-type wire tokens are
`CC="CC" COSMOS="COSMOS" …` but the pairing Map uses `deviceType:"CC"` against
`deviceType:"Cosmos"` — the enum is uppercase, the value is not. Same shape as the
already-known `SIMPLERA_SYSTEM = "Simplera™ system"` problem, so
`isBleDevice()` needs its family match case-insensitive regardless of which
spelling the wire uses.

Also: `retinaEnabled:!1, cuaEnabled:!1` in the shipped build — the Pusher code is
present but the feature **ships off**.

### Coverage limit — the highest-value next step

`hp-runtime.js` holds a **225-entry lazy-chunk manifest** and `main.js`
references 27. Every feature module (dashboard, reports, logbook, CUA, MFA,
uploader) is a lazy chunk, so **`hp-main.js` is the shell, not the features** —
`hcp/settings-calculator/*` has zero call sites in it at all. Fetching those 225
chunks is one `curl` pass and would extend the `hcp/*` map considerably.

## 8. Verification pass (2026-10-09) — subagent claims checked by hand

Three load-bearing claims came from delegated recon. Each was re-derived here by
direct execution rather than accepted.

### ✅ Byte-identical bundle on a second host — CONFIRMED

```
carelink.medtronic.com/main.fb5f8cb7eb60c4d5.js   3397615 B  sha256 2a7fa8e7af519c2b
carelinkhp.minimed.eu/main.fb5f8cb7eb60c4d5.js   3397615 B  sha256 2a7fa8e7af519c2b
cmp: IDENTICAL (byte-for-byte)
```

Not merely equivalent — the same 3.4 MB file to the byte. So the leaked
`x-api-key` and the `dev.commoncore.medtronic.eu` build-config bug (§ S3) ship as
**one artefact on two hosts**, and a remediation conversation naming only
`carelinkhp` would fix half of it.

### ✅ `*.carelink.eu` is wildcard parking — CONFIRMED, with the right control

The proof is a name that **cannot** exist:

```
zqxjkvwmpn987notarehost.carelink.eu  -> 103.224.182.253     <-- resolves!
carelink.eu                          -> 103.224.182.253
NS: ns1.abovedomains.com / ns2.abovedomains.com
https://admin.carelink.eu            -> 302 https://ww38.carelink.eu/
```

A random string resolving is conclusive. **Any host list containing `*.carelink.eu`
names is fabricated and must never reach a disclosure.**

### ✅ Fourth Auth0 tenant — CONFIRMED, and stronger than claimed

All four JWKS documents fetched and compared. **The key sets are completely
disjoint — no `kid` is shared by any two tenants:**

| tenant | JWKS kids |
|---|---|
| `carelink-login.minimed.eu` (patient EU) | `8RqxnMm8vg2Go_y1LAVh9`, `vnTNpK5RvkqVEfQgHRsqv` |
| `carelink-login.minimed.com` (patient US) | `jpv2d2IuydtvKtefd5M8J`, `qjHNmcQOpW_gvHz6zaD8` |
| `carelink-login.medtronic.eu` (shadow) | `jd0EOLxJ8XduYx4lLy3ig`, `gZMBCJcl_t25Es4U_g_ow` |
| `carelink-login.medtronic.com` (shadow) | `cEgK74cyc5LzAVI9VxEz9`, `80YhF8vW25gJ1_rR_lLOJ` |

This **upgrades** the earlier finding rather than just confirming it. The shadow
deployment was noted as having "identical OAuth policy", which left open the
worry that it might share signing keys — a key-reuse risk. It does not: every
tenant signs with its own key pair.

So the token-confusion question is better posed than "would a shadow token be
accepted?" — it becomes: **does any host validate the `kid` against its own JWKS,
or merely decode the token and trust the claims?** A verifier that fetches the
issuer's JWKS is safe here by construction; one that accepts an arbitrary `kid`
and skips issuer/audience checking would not be. Still needs a token to test, but
the configuration is the safe side of the question, and the exposure is a
verifier bug rather than a key leak.

## 9. Archive lead verified: the shadow portal's `hcp/configuration/public/*` (2026-10-09)

The Common Crawl/Wayback sweep recovered a clinician REST namespace on
`carelink.medtronic.eu` archived **200 unauthenticated** in 2020. Archived ≠ live,
so every one was re-requested. Result:

| path | live status |
|---|---|
| `/hcp/configuration/public/pow.crm.settings` | **200 application/octet-stream, 96 B** |
| `/hcp/configuration/public/cms-config.json` | 412 |
| `/hcp/configuration/public/pow.invite.to.personal.uri` | 412 |
| `/hcp/configuration/public/pow.browser.check.configuration` | 412 |
| `/hcp/configuration/public/pow.mmo.config` | 412 |
| `/hcp/configuration/public/pow.udi.number` | 412 |
| `/hcp/configuration/public/pow.udi.certificate` | 412 |
| `/hcp/configuration/public/logbook.supported.entry.types` | 412 |
| `/hcp/configuration/public/cua.control.codes.settings` | 412 |
| `/hcp/configuration/public/system.logbook.entry.validation.config` | 412 |
| `/hcp/configuration/public/pow.crm.settings.version` | 404 |
| `/hcp/configuration/application` · `/user` · `/countries/getAllCountries` | 405 (POST-only) |
| `/hcp/configuration/product/info` | 404 |

**One endpoint answers unauthenticated where all nine of its siblings require a
header** (412 = precondition failed, which is what the portal's `hcp/` family
returns without the client header — `X-System-ID: ProWeb` per the bundle):

```json
{ "base.uri": "https://carelink.medtronic.eu/crm", "product": "pow", "version": "4.5" }
```

Low sensitivity — a CRM base URI and a version string, no PII, no credential. The
finding is the **inconsistency**, not the content: nine siblings are header-gated
and this one is not. Worth reporting as a hygiene nit alongside S3.

Corroborates the archive sweep's second CMS ladder: the shadow deployment's
content namespace is `pow` (product `pow`, version 4.5), where the patient
deployments use `ocl` (versions 14.x → 15.5).

### Standing blind spot

Prod **`commoncore.medtronic.{eu,com}` has never been archived in any crawl** —
only its `dev`/`stage1`/`preprod1` twins exist. The reports backend that #76
depends on is the single largest unarchived surface in the project.
