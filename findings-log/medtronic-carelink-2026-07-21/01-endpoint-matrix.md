# Endpoint matrix (CareLink public surface, observed 2026-07-21)

Probes: 14 unauthenticated GETs against the surface the repo actually uses (`src/carelink/urls.ts`, `src/login.ts:17-23`, `src/doctor.ts:69-72`). All credential-free, no Auth0 redirect-following, no brute force, no mutation. Tool returned only Content-Type and body, not Date / cache / security headers.

## Discovery surface (status 200 for all 8 cells)

| Host | App version | Cumulus | Auth0 | Clinical region? |
|---|---|---|---|---|
| clcloud.minimed.com | android/3.4 | v11 | absent (legacy) | yes |
| clcloud.minimed.com | android/3.6 | v13 | Auth0SSOConfiguration | yes |
| clcloud.minimed.com | android/3.7 | v13 | Auth0SSOConfiguration | yes |
| clcloud.minimed.com | android/4.0 | v2 | absent (legacy) | NO |
| clcloud.minimed.eu | android/3.4 | v11 | absent | yes |
| clcloud.minimed.eu | android/3.6 | v13 | Auth0SSOConfiguration | yes |
| clcloud.minimed.eu | android/3.7 | v13 | Auth0SSOConfiguration | yes |
| clcloud.minimed.eu | android/4.0 | v2 | absent | NO |

Shape: `{ config, supportedCountries: [...], CP: [{region, SSOConfiguration, Layer7SSOConfiguration?, Auth0SSOConfiguration?, UseSSOConfiguration, baseUrlCms, baseUrlCareLink, baseUrlCumulus, baseUrlPde, baseUrlAem}], certificates: [{host, cert}] }`. `certificates[].cert` is a base64 X.509 (DigiCert Global Root G2). Same RSA modulus across all hosts — they pin the same CA cert, not leaf cert.

## Auth0 SSO config (200, no creds)

| URL | hostname | endpoint paths | scope | audience |
|---|---|---|---|---|
| carelink.minimed.com/configs/v1/carepartner_auth0_us_sso_config_v1.json | carelink-login.minimed.com | /authorize, /oauth/token, /oauth/revoke, /oidc/logout, /connect/session/status, /.well-known/openid-configuration | profile openid offline_access | carepartner.patient.us |
| carelink.minimed.eu/configs/v1/carepartner_auth0_ous_sso_config_v1.json | carelink-login.minimed.eu | same shape, plus /.well-known/openid-configuration | profile openid offline_access | carepartner.patient.ous |

Both ship `redirect_uri: "com.medtronic.carepartner:/sso"` and empty `client_secret` (public client, PKCE only).

## Legacy OAuth SSO config (3.4 / 4.0 paths)

| URL | hostname | shape |
|---|---|---|
| carelink.minimed.com/configs/v1/oauth20_sso_carepartner_us_v6.json | mdtlogin.medtronic.com | OAuth2 paths /auth/oauth/v2/{authorize,token,token/revoke}, no configuration_endpoint_path, no audience, scope profile openid roles country |
| carelink.minimed.eu/configs/v1/oauth20_sso_carepartner_eu_v6.json | mdtlogin-ocl.medtronic.com | same |

Different Auth0 tenant. v3.4 and v4.0 won't work with the current Auth0-aware login flow.

## OIDC metadata (200)

| URL | issuer | jwks | code_challenge_methods |
|---|---|---|---|
| carelink-login.minimed.com/.well-known/openid-configuration | https://carelink-login.minimed.com/ | /.well-known/jwks.json | S256, plain |
| carelink-login.minimed.eu/.well-known/openid-configuration | https://carelink-login.minimed.eu/ | /.well-known/jwks.json | S256, plain |

## Web roots

- carelink.minimed.com/ and carelink.minimed.eu/ both serve the same SPA. EU page sets `<link rel=canonical href=https://carelink.minimed.com/>` (no HTTP redirect, just HTML canonical).

## Auth boundary (no token)

- carelink.minimed.eu/patient/users/me -> 401 (empty body)
- carelink.minimed.eu/patient/connect/data?...msgType=last24hours -> 401 (empty body)

The 401 has no JSON body. The bridge must rely on status code only — it already does.

## Corrections to v3.4/v3.6/v3.7/v4.0 table

1. EU SPA canonical is HTML, not HTTP redirect.
2. baseUrlCareLink version: v3.4/3.6/3.7 all advertise `/api/carepartner/v2`; v4.0 advertises `/api/carepartner/v1`. So a `4.0` downgrade would also drop the carelink API version, not just the cumulus version. The current bridge calls `/patient/*` on the bare hostname and is unaffected.
3. Legacy v6 configs do NOT include `configuration_endpoint_path` and do NOT advertise an OIDC metadata URL — anyone assuming v6 configs are OIDC-compliant is wrong.
4. v4.0 discovery omits the CLINICAL region entirely (US + EU only). v3.4/3.6/3.7 all include it. Confirmed observation.

## Not probed

- HEAD response headers (Date/Cache-Control/HSTS/X-Content-Type-Options).
- /.well-known/jwks.json body.
- CORS preflight behaviour for *.minimed.com origins against Auth0 hosts.
- baseUrlCumulus v11/v2 tracks; baseUrlPde v2/v3; /api/carepartner/v2 (used by nightscout-connect and the upstream CareLink app, not the current bridge).
- Rate-limit / X-RateLimit-* headers.

## Compatibility implications for the bridge

1. `DISCOVERY_APP_VERSION='android/3.6'` is the correct current choice; `4.0` would silently break login. Matches the in-repo comment.
2. Region selection is load-bearing: US and EU live on different Auth0 tenants with different `client_id` and `audience`. Operators must keep `MMCONNECT_SERVER` in sync.
3. EU discovery returns the `carepartner_auth0_ous_sso_config_v1.json` URL (with `_ous_` slug, no `eu`). The bridge doesn't parse the filename, only the contents.
4. `baseUrlCareLink` in v3.6/3.7 is `carelink.minimed.{com,eu}/api/carepartner/v2`. The v2 path is what `nightscout-connect` and the upstream CareLink app use for some endpoints; the bridge currently calls `/patient/*` instead. Worth a follow-up issue to consider switching to the discovery-derived family.
5. `baseUrlCumulus` is `v13` in 3.6/3.7 but `v11` in 3.4 and `v2` in 4.0. The bridge only ever calls the discovery endpoint over v13.
6. The bridge's 401-recovery path cannot depend on a body shape — must rely on status code only. Current code already does this.
7. Both Auth0 SSO configs ship `client_secret: ""`. The bridge's PKCE + state implementation is correct for this tenant shape. Any fallback to `client_secret_post` would break, since the server publishes `client_secret_post` as supported but the bridge's secret is empty.

---

## Re-probe 2026-08-05 (diff vs 07-21 baseline)

All credential-free GETs, same tooling discipline. Findings:

### 1. New app-version tracks exist: `android/3.8` and `android/4.1`

Both now resolve HTTP 200 on clcloud.minimed.com (baseline only mapped 3.4/3.6/3.7/4.0).

- `android/3.8` → **Auth0 track**: `UseSSO=Auth0SSOConfiguration`, cumulus v13, CLINICAL region present, for both com and eu hosts. Same shape as 3.6/3.7. **Useful new fact: the Auth0 track is a family (3.6, 3.7, 3.8), not a single fragile version.** If Medtronic were to deprecate one of them, the others are verified fallbacks with identical cumulus/Auth0 behaviour — de-risks `DISCOVERY_APP_VERSION`.
- `android/4.1` → **legacy track**: `UseSSO` absent, cumulus v2, no CLINICAL, same as 4.0. Confirms 4.x is a distinct legacy product track (no Auth0) all the way up to 4.1; bumping onto 4.x would still break Auth0 login.
- Pattern: `3.x` (except 3.4) = Auth0 v13 track · `4.x` = legacy no-Auth0 v2 track · `3.4` = v11 legacy. `DISCOVERY_APP_VERSION=android/3.6` remains correct.

### 2. CLINICAL / trials surface is a full third Auth0 tenant (untouched by the bridge)

All 3.6-3.8 tracks advertise a CLINICAL region pointing at dedicated infra:
- `clcloud-trials.minimed.com/connect/carepartner/v13` (cumulus)
- `carelink-trials.minimed.com/api/carepartner/v2` + `/configs/v1/carepartner_auth0_cl_sso_config_v1.json`
- `carelink-login-trials.minimed.com` (Auth0 tenant; leaf cert CN `carelink-login-trials.minimed.com`, valid to 2026-09-16)

This is an entire parallel deployment (trials/clinical studies) the bridge doesn't touch. Same config shape, same Auth0 model, separate hostnames + audience. Candidate for a future clinical-data note; not needed for patient use.

### 3. EU tenant live health (no drift)

- Discovery 3.6 → `UseSSO=Auth0SSOConfiguration` → `carepartner_auth0_ous_sso_config_v1.json` resolves (proprietary Medtronic shape `{server:{hostname,port,prefix,server_certs}}`, root→intermediate→leaf; EU leaf cert CN `carelink-login.minimed.eu`, valid to 2026-09-16, normal rotation).
- OIDC metadata live: issuer `https://carelink-login.minimed.eu/`, `code_challenge_methods_supported: [S256, plain]`, token auth methods include `none` (public client) — consistent with the bridge's PKCE approach.
- jwks has 2 keys.

### 4. Conclusion

Core pinned surface unchanged and healthy → the bridge's login/data path is not at risk. Only genuinely new info is the 3.8/4.1 tracks and the confirmed trials third-tenant. No code action required; optionally note 3.8 as a verified fallback in the `DISCOVERY_APP_VERSION` comment (keeps the "keep it verified" rule intact).
